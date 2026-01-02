"""Asset data model for depreciation tracking."""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class AssetStatus(Enum):
    """Status of a depreciable asset."""
    ACTIVE = "active"
    FULLY_DEPRECIATED = "fully_depreciated"
    DISPOSED = "disposed"


@dataclass
class Asset:
    """Represents a depreciable business asset.

    Attributes:
        id: Unique identifier (e.g., "asset-a1b2c3d4")
        name: Asset description (e.g., "Orbea fiets", "iPhone 14 Pro")
        purchase_date: Date of purchase
        purchase_amount: Original purchase price in EUR
        depreciation_years: Number of years for depreciation (1-10)
        disposal_date: Date asset was sold/disposed (None if active)
        notes: User notes or source documentation reference
        source: Origin: "manual" or "excel_import"
        created_at: When the asset was registered
    """

    # Required fields
    id: str
    name: str
    purchase_date: date
    purchase_amount: Decimal
    depreciation_years: int
    source: str

    # Optional fields
    disposal_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate asset data after initialization."""
        # Validate name is non-empty
        if not self.name or not self.name.strip():
            raise ValueError("Asset name cannot be empty")

        # Validate purchase_amount is positive
        if self.purchase_amount <= Decimal('0'):
            raise ValueError(f"Purchase amount must be positive, got: {self.purchase_amount}")

        # Validate depreciation_years is 1-10
        if not (1 <= self.depreciation_years <= 10):
            raise ValueError(f"Depreciation years must be 1-10, got: {self.depreciation_years}")

        # Validate source
        if self.source not in ('manual', 'excel_import'):
            raise ValueError(f"Invalid source: {self.source}. Must be 'manual' or 'excel_import'")

        # Validate disposal_date is after purchase_date if set
        if self.disposal_date and self.disposal_date < self.purchase_date:
            raise ValueError(
                f"Disposal date ({self.disposal_date}) must be after purchase date ({self.purchase_date})"
            )

    @property
    def annual_depreciation(self) -> Decimal:
        """Calculate annual depreciation amount (straight-line method)."""
        return self.purchase_amount / self.depreciation_years

    @property
    def first_depreciation_year(self) -> int:
        """First year of depreciation."""
        return self.purchase_date.year

    @property
    def last_depreciation_year(self) -> int:
        """Last year of depreciation (before any disposal)."""
        return self.purchase_date.year + self.depreciation_years - 1

    def to_dict(self) -> dict:
        """Convert asset to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'purchase_date': self.purchase_date.isoformat(),
            'purchase_amount': str(self.purchase_amount),
            'depreciation_years': self.depreciation_years,
            'disposal_date': self.disposal_date.isoformat() if self.disposal_date else None,
            'notes': self.notes,
            'source': self.source,
            'created_at': self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Asset':
        """Create asset from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            purchase_date=date.fromisoformat(data['purchase_date']),
            purchase_amount=Decimal(data['purchase_amount']),
            depreciation_years=data['depreciation_years'],
            disposal_date=date.fromisoformat(data['disposal_date']) if data.get('disposal_date') else None,
            notes=data.get('notes'),
            source=data.get('source', 'manual'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
        )


@dataclass
class DepreciationEntry:
    """Annual depreciation record for reporting (computed, not persisted).

    Attributes:
        asset_id: Reference to Asset.id
        asset_name: Asset name for display
        fiscal_year: Year of depreciation
        amount: Depreciation amount for this year
        year_number: Which year of depreciation (1, 2, 3...)
        remaining_book_value: Book value after this year's depreciation
        category_id: Category for P&L integration (always "afschrijvingen")
    """

    asset_id: str
    asset_name: str
    fiscal_year: int
    amount: Decimal
    year_number: int
    remaining_book_value: Decimal
    category_id: str = "afschrijvingen"

    def to_dict(self) -> dict:
        """Convert depreciation entry to dictionary."""
        return {
            'asset_id': self.asset_id,
            'asset_name': self.asset_name,
            'fiscal_year': self.fiscal_year,
            'amount': str(self.amount),
            'year_number': self.year_number,
            'remaining_book_value': str(self.remaining_book_value),
            'category_id': self.category_id,
        }
