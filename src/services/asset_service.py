"""Asset service for managing depreciable business assets."""

import logging
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Tuple

from src.models.asset import Asset
from src.services.persistence import PersistenceService

logger = logging.getLogger(__name__)


def generate_asset_id() -> str:
    """Generate a unique asset ID.

    Returns:
        Asset ID in format "asset-{8-char-hex}"
    """
    return f"asset-{uuid.uuid4().hex[:8]}"


def calculate_annual_depreciation(asset: Asset) -> Decimal:
    """Calculate annual depreciation using straight-line method.

    Args:
        asset: The asset to calculate depreciation for

    Returns:
        Annual depreciation amount (purchase_amount / depreciation_years)
    """
    return asset.purchase_amount / asset.depreciation_years


def check_duplicate(
    name: str,
    purchase_date: date,
    existing_assets: List[Asset],
) -> Optional[Asset]:
    """Check if an asset with the same name and purchase date already exists.

    Args:
        name: Asset name to check
        purchase_date: Purchase date to check
        existing_assets: List of existing assets

    Returns:
        The duplicate Asset if found, None otherwise
    """
    name_lower = name.lower().strip()
    for asset in existing_assets:
        if asset.name.lower().strip() == name_lower and asset.purchase_date == purchase_date:
            return asset
    return None


def add_asset(
    persistence: PersistenceService,
    name: str,
    purchase_date: date,
    purchase_amount: Decimal,
    depreciation_years: int,
    notes: Optional[str] = None,
    source: str = "manual",
) -> Tuple[Asset, Optional[Asset]]:
    """Add a new depreciable asset.

    Args:
        persistence: Persistence service for loading/saving assets
        name: Asset description
        purchase_date: Date of purchase
        purchase_amount: Original purchase price in EUR
        depreciation_years: Number of years for depreciation
        notes: Optional notes
        source: Origin ("manual" or "excel_import")

    Returns:
        Tuple of (new Asset, duplicate Asset if found or None)

    Raises:
        ValueError: If asset data is invalid
    """
    # Load existing assets
    existing_assets = persistence.load_assets()

    # Check for duplicates
    duplicate = check_duplicate(name, purchase_date, existing_assets)

    # Create new asset
    asset = Asset(
        id=generate_asset_id(),
        name=name.strip(),
        purchase_date=purchase_date,
        purchase_amount=purchase_amount,
        depreciation_years=depreciation_years,
        notes=notes,
        source=source,
        created_at=datetime.now(),
    )

    # Add to list and save
    existing_assets.append(asset)
    persistence.save_assets(existing_assets)

    logger.info(f"Added asset '{asset.id}': {asset.name}")

    return asset, duplicate


def dispose_asset(
    persistence: PersistenceService,
    asset_id: str,
    disposal_date: date,
    notes: Optional[str] = None,
) -> Asset:
    """Mark an asset as disposed.

    Args:
        persistence: Persistence service for loading/saving assets
        asset_id: ID of asset to dispose
        disposal_date: Date of disposal
        notes: Optional notes about disposal

    Returns:
        The updated Asset

    Raises:
        ValueError: If asset not found, already disposed, or disposal date invalid
    """
    # Load existing assets
    assets = persistence.load_assets()

    # Find the asset
    target_asset = None
    for i, asset in enumerate(assets):
        if asset.id == asset_id:
            target_asset = asset
            target_index = i
            break

    if target_asset is None:
        raise ValueError(f"Asset not found: {asset_id}")

    if target_asset.disposal_date is not None:
        raise ValueError(f"Asset already disposed on {target_asset.disposal_date}")

    if disposal_date < target_asset.purchase_date:
        raise ValueError(
            f"Disposal date ({disposal_date}) must be after purchase date ({target_asset.purchase_date})"
        )

    # Update the asset with disposal info
    updated_asset = Asset(
        id=target_asset.id,
        name=target_asset.name,
        purchase_date=target_asset.purchase_date,
        purchase_amount=target_asset.purchase_amount,
        depreciation_years=target_asset.depreciation_years,
        disposal_date=disposal_date,
        notes=notes if notes else target_asset.notes,
        source=target_asset.source,
        created_at=target_asset.created_at,
    )

    # Replace in list and save
    assets[target_index] = updated_asset
    persistence.save_assets(assets)

    logger.info(f"Disposed asset '{asset_id}': {updated_asset.name}")

    return updated_asset
