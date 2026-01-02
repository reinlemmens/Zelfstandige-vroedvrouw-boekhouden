"""Depreciation calculation service for asset tracking.

This module provides functions to calculate depreciation schedules
and determine asset status for any given fiscal year.
"""

import logging
from datetime import date
from decimal import Decimal
from typing import List, Optional

from src.models.asset import Asset, AssetStatus, DepreciationEntry
from src.services.persistence import PersistenceService

logger = logging.getLogger(__name__)


def is_depreciating_in_year(asset: Asset, year: int) -> bool:
    """Check if an asset has depreciation for the given year.

    Full-year depreciation is applied (no pro-rating):
    - First year: Full depreciation from purchase year
    - Last year: Full depreciation even if disposed mid-year
    - After last year: No depreciation

    Args:
        asset: The asset to check
        year: The fiscal year to check

    Returns:
        True if the asset has depreciation in the given year
    """
    first_year = asset.purchase_date.year
    last_year = first_year + asset.depreciation_years - 1

    # Not yet purchased
    if year < first_year:
        return False

    # Already fully depreciated
    if year > last_year:
        return False

    # Disposed before this year (disposal year still gets full depreciation)
    if asset.disposal_date and asset.disposal_date.year < year:
        return False

    return True


def get_asset_status(asset: Asset, reference_date: Optional[date] = None) -> AssetStatus:
    """Determine the current status of an asset.

    Args:
        asset: The asset to check
        reference_date: Date to check status for (defaults to today)

    Returns:
        AssetStatus: ACTIVE, FULLY_DEPRECIATED, or DISPOSED
    """
    if reference_date is None:
        reference_date = date.today()

    # Check if disposed
    if asset.disposal_date:
        return AssetStatus.DISPOSED

    # Check if fully depreciated
    last_year = asset.purchase_date.year + asset.depreciation_years - 1
    if reference_date.year > last_year:
        return AssetStatus.FULLY_DEPRECIATED

    return AssetStatus.ACTIVE


def get_depreciation_for_year(assets: List[Asset], year: int) -> List[DepreciationEntry]:
    """Get all depreciation entries for a fiscal year.

    Args:
        assets: List of assets to calculate depreciation for
        year: The fiscal year

    Returns:
        List of DepreciationEntry objects for assets with depreciation in that year
    """
    entries = []

    for asset in assets:
        if not is_depreciating_in_year(asset, year):
            continue

        annual_depreciation = asset.purchase_amount / asset.depreciation_years
        year_number = year - asset.purchase_date.year + 1

        # Calculate remaining book value after this year's depreciation
        accumulated = year_number * annual_depreciation
        remaining = asset.purchase_amount - accumulated
        remaining = max(remaining, Decimal('0'))

        entry = DepreciationEntry(
            asset_id=asset.id,
            asset_name=asset.name,
            fiscal_year=year,
            amount=annual_depreciation,
            year_number=year_number,
            remaining_book_value=remaining,
            category_id="afschrijvingen",
        )
        entries.append(entry)

    logger.debug(f"Found {len(entries)} depreciation entries for year {year}")
    return entries


def get_total_depreciation_for_year(persistence: PersistenceService, year: int) -> Decimal:
    """Calculate total depreciation for a fiscal year.

    This function is the primary interface for P&L integration.
    Returns the sum of all asset depreciation for the given year.

    Args:
        persistence: Persistence service for loading assets
        year: The fiscal year

    Returns:
        Total depreciation amount for the year
    """
    assets = persistence.load_assets()
    entries = get_depreciation_for_year(assets, year)
    return sum(entry.amount for entry in entries)


def get_book_value(asset: Asset, as_of_year: int) -> Decimal:
    """Calculate the book value of an asset as of a specific year-end.

    Args:
        asset: The asset
        as_of_year: The year to calculate book value for (end of year)

    Returns:
        Book value after depreciation through the given year
    """
    first_year = asset.purchase_date.year
    last_year = first_year + asset.depreciation_years - 1

    # Before purchase
    if as_of_year < first_year:
        return asset.purchase_amount

    # After full depreciation
    if as_of_year >= last_year:
        return Decimal('0')

    # During depreciation period
    years_depreciated = as_of_year - first_year + 1
    annual_depreciation = asset.purchase_amount / asset.depreciation_years
    accumulated = years_depreciated * annual_depreciation

    return max(asset.purchase_amount - accumulated, Decimal('0'))


def get_current_depreciation_year(asset: Asset, as_of_year: int) -> Optional[int]:
    """Get which year of depreciation an asset is in.

    Args:
        asset: The asset
        as_of_year: The reference year

    Returns:
        The depreciation year number (1, 2, 3...) or None if not depreciating
    """
    if not is_depreciating_in_year(asset, as_of_year):
        return None

    return as_of_year - asset.purchase_date.year + 1
