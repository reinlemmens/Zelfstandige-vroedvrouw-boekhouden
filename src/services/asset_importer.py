"""Import assets from Excel Resultaat sheet for one-time migration."""

import logging
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

from src.models.asset import Asset
from src.services.asset_service import generate_asset_id
from src.services.persistence import PersistenceService

logger = logging.getLogger(__name__)


def find_depreciation_rows(df: pd.DataFrame) -> List[int]:
    """Find rows containing depreciation entries.

    Depreciation rows are identified by having a fractional rate (0 < rate < 1)
    in column 5, indicating multi-year depreciation.

    Args:
        df: DataFrame from Resultaat sheet

    Returns:
        List of row indices containing depreciation data
    """
    depreciation_rows = []

    for idx, row in df.iterrows():
        # Check column 5 for fractional rate
        rate = row.iloc[5] if len(row) > 5 else None

        if rate is None or pd.isna(rate):
            continue

        try:
            rate_val = float(rate)
            # Fractional rate indicates depreciation (e.g., 0.333333 = 1/3 = 3 years)
            if 0 < rate_val < 1:
                depreciation_rows.append(idx)
        except (ValueError, TypeError):
            continue

    logger.debug(f"Found {len(depreciation_rows)} depreciation rows")
    return depreciation_rows


def parse_depreciation_years(rate: float) -> int:
    """Calculate depreciation years from fractional rate.

    Args:
        rate: Depreciation rate (e.g., 0.333333 for 3 years)

    Returns:
        Number of depreciation years (rounded to nearest integer)
    """
    if rate <= 0 or rate >= 1:
        raise ValueError(f"Invalid depreciation rate: {rate}")

    years = round(1 / rate)
    # Clamp to valid range
    return max(1, min(10, years))


def parse_purchase_year_from_notes(notes: str) -> Optional[int]:
    """Extract the first (purchase) year from notes.

    Notes typically contain year ranges like "2023, 2024, 2025"
    or "Afschrijving gsm 2023, 2024, 2025"

    Args:
        notes: Notes string from Excel

    Returns:
        The first year found, or None if no year pattern found
    """
    if not notes or pd.isna(notes):
        return None

    notes_str = str(notes)

    # Find all 4-digit years
    years = re.findall(r'\b(20\d{2})\b', notes_str)

    if years:
        # Return the earliest year (first year of depreciation = purchase year)
        return min(int(y) for y in years)

    return None


def import_assets_from_excel(
    file_path: Path,
    sheet_name: str = "Resultaat",
) -> List[Asset]:
    """Import depreciable assets from Excel file.

    Parses the Resultaat sheet to find rows with fractional depreciation rates,
    extracting asset name, purchase amount, depreciation period, and notes.

    Args:
        file_path: Path to Excel file
        sheet_name: Name of sheet to read (default: Resultaat)

    Returns:
        List of Asset objects extracted from the file

    Raises:
        FileNotFoundError: If Excel file doesn't exist
        ValueError: If sheet not found or no assets found
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    # Read sheet without header
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
    except ValueError as e:
        if "Worksheet" in str(e):
            raise ValueError(f"Sheet '{sheet_name}' not found in {file_path}")
        raise

    # Find depreciation rows
    dep_rows = find_depreciation_rows(df)

    if not dep_rows:
        raise ValueError(f"No depreciation entries found in sheet '{sheet_name}'")

    assets = []

    for row_idx in dep_rows:
        row = df.iloc[row_idx]

        # Extract data
        name = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None
        amount = row.iloc[1] if len(row) > 1 and pd.notna(row.iloc[1]) else None
        rate = row.iloc[5] if len(row) > 5 and pd.notna(row.iloc[5]) else None
        notes = str(row.iloc[7]).strip() if len(row) > 7 and pd.notna(row.iloc[7]) else None

        if not name or amount is None or rate is None:
            logger.warning(f"Skipping incomplete row {row_idx}: name={name}, amount={amount}, rate={rate}")
            continue

        try:
            # Parse depreciation years from rate
            years = parse_depreciation_years(float(rate))

            # Parse purchase year from notes
            purchase_year = parse_purchase_year_from_notes(notes)

            # If no year in notes, use current year minus (years - 1)
            if purchase_year is None:
                purchase_year = datetime.now().year - years + 1

            # Create purchase date (January 1st of purchase year)
            purchase_date = date(purchase_year, 1, 1)

            # Convert amount to positive Decimal
            purchase_amount = Decimal(str(abs(float(amount))))

            # Create asset
            asset = Asset(
                id=generate_asset_id(),
                name=name,
                purchase_date=purchase_date,
                purchase_amount=purchase_amount,
                depreciation_years=years,
                notes=notes,
                source="excel_import",
                created_at=datetime.now(),
            )

            assets.append(asset)
            logger.info(f"Parsed asset: {name} (€{purchase_amount}, {years} years)")

        except Exception as e:
            logger.warning(f"Error parsing row {row_idx}: {e}")
            continue

    logger.info(f"Imported {len(assets)} assets from {file_path}")
    return assets


def import_and_save_assets(
    persistence: PersistenceService,
    file_path: Path,
    sheet_name: str = "Resultaat",
    merge: bool = False,
    dry_run: bool = False,
) -> Tuple[List[Asset], List[Asset], List[Asset]]:
    """Import assets from Excel and optionally save to persistence.

    Args:
        persistence: Persistence service for loading/saving
        file_path: Path to Excel file
        sheet_name: Sheet name to read
        merge: If True, add only new assets; if False, replace all
        dry_run: If True, don't actually save

    Returns:
        Tuple of (imported assets, skipped duplicates, final assets list)
    """
    # Parse assets from Excel
    new_assets = import_assets_from_excel(file_path, sheet_name)

    # Load existing assets
    existing_assets = persistence.load_assets()

    # Check for duplicates by name (case-insensitive)
    existing_names = {a.name.lower().strip() for a in existing_assets}

    imported = []
    skipped = []

    for asset in new_assets:
        if asset.name.lower().strip() in existing_names:
            skipped.append(asset)
            logger.info(f"Skipping duplicate: {asset.name}")
        else:
            imported.append(asset)
            existing_names.add(asset.name.lower().strip())

    # Determine final list
    if merge:
        final_assets = existing_assets + imported
    else:
        final_assets = imported

    # Save if not dry run
    if not dry_run and imported:
        persistence.save_assets(final_assets)

    return imported, skipped, final_assets
