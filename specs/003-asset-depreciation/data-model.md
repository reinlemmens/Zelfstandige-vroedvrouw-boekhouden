# Data Model: Asset Depreciation Tracking

**Feature**: 003-asset-depreciation
**Date**: 2026-01-02

## Entities

### Asset

A depreciable business purchase tracked for multi-year write-offs.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique identifier (e.g., "asset-a1b2c3d4") |
| name | string | Yes | Asset description (e.g., "Orbea fiets", "iPhone 14 Pro") |
| purchase_date | date | Yes | Date of purchase (YYYY-MM-DD) |
| purchase_amount | Decimal | Yes | Original purchase price in EUR |
| depreciation_years | int | Yes | Number of years for depreciation (1-10) |
| disposal_date | date | No | Date asset was sold/disposed (null if active) |
| notes | string | No | User notes or source documentation reference |
| source | string | Yes | Origin: "manual" or "excel_import" |
| created_at | datetime | Yes | When the asset was registered |

**Validation Rules**:
- `purchase_amount` must be positive
- `depreciation_years` must be 1-10 (Belgian SME typical range)
- `disposal_date` must be >= `purchase_date` if set
- `name` must be non-empty

**Derived Properties**:
- `annual_depreciation`: purchase_amount / depreciation_years
- `status`: "active" | "fully_depreciated" | "disposed"
- `book_value`: purchase_amount - accumulated_depreciation
- `first_depreciation_year`: purchase_date.year
- `last_depreciation_year`: purchase_date.year + depreciation_years - 1

### DepreciationEntry (Computed, not persisted)

Annual depreciation record for reporting.

| Field | Type | Description |
|-------|------|-------------|
| asset_id | string | Reference to Asset.id |
| asset_name | string | Asset name for display |
| fiscal_year | int | Year of depreciation |
| amount | Decimal | Depreciation amount for this year |
| year_number | int | Which year of depreciation (1, 2, 3...) |
| remaining_book_value | Decimal | Book value after this year's depreciation |

### AssetStatus (Enum)

| Value | Description |
|-------|-------------|
| active | Currently depreciating |
| fully_depreciated | Depreciation period complete |
| disposed | Sold or disposed before full depreciation |

## State Transitions

```
                    ┌─────────────────┐
                    │    ACTIVE       │
                    │  (depreciating) │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              │              ▼
    ┌─────────────────┐      │    ┌─────────────────┐
    │ FULLY_DEPRECIATED│      │    │    DISPOSED     │
    │ (years complete) │      │    │ (sold/disposed) │
    └─────────────────┘      │    └─────────────────┘
                             │
                    Disposed before
                    full depreciation
```

**Transition Rules**:
- ACTIVE → FULLY_DEPRECIATED: When current_year > last_depreciation_year
- ACTIVE → DISPOSED: When disposal_date is set
- No reverse transitions (disposed assets cannot be reactivated)

## Relationships

```
Asset 1───────* DepreciationEntry (computed)
  │
  │  An asset generates one depreciation entry
  │  per year for each year in its depreciation period
  │
  └─→ entries = [
        (year: 2023, amount: 1393.02, year_number: 1),
        (year: 2024, amount: 1393.02, year_number: 2),
        (year: 2025, amount: 1393.02, year_number: 3),
      ]
```

## Persistence Format

### assets.json

```json
{
  "version": "1.0",
  "exported_at": "2026-01-02T10:00:00",
  "assets": [
    {
      "id": "asset-a1b2c3d4",
      "name": "Orbea fiets",
      "purchase_date": "2023-01-15",
      "purchase_amount": "4179.05",
      "depreciation_years": 3,
      "disposal_date": null,
      "notes": "Afschrijving fiets 2023, 2024, 2025",
      "source": "excel_import",
      "created_at": "2026-01-02T10:00:00"
    },
    {
      "id": "asset-e5f6g7h8",
      "name": "iPhone 14 Pro",
      "purchase_date": "2023-06-01",
      "purchase_amount": "769.00",
      "depreciation_years": 3,
      "disposal_date": null,
      "notes": "Telefonie - gsm",
      "source": "excel_import",
      "created_at": "2026-01-02T10:00:00"
    }
  ]
}
```

## Calculations

### Annual Depreciation

```python
def calculate_annual_depreciation(asset: Asset) -> Decimal:
    """Straight-line depreciation per year."""
    return asset.purchase_amount / asset.depreciation_years
```

### Depreciation Schedule for Year

```python
def get_depreciation_for_year(assets: List[Asset], year: int) -> List[DepreciationEntry]:
    """Get all depreciation entries for a fiscal year."""
    entries = []
    for asset in assets:
        if is_depreciating_in_year(asset, year):
            year_number = year - asset.purchase_date.year + 1
            remaining = asset.purchase_amount - (year_number * calculate_annual_depreciation(asset))
            entries.append(DepreciationEntry(
                asset_id=asset.id,
                asset_name=asset.name,
                fiscal_year=year,
                amount=calculate_annual_depreciation(asset),
                year_number=year_number,
                remaining_book_value=max(remaining, Decimal('0'))
            ))
    return entries
```

### Is Depreciating in Year

```python
def is_depreciating_in_year(asset: Asset, year: int) -> bool:
    """Check if asset has depreciation for the given year."""
    first_year = asset.purchase_date.year
    last_year = first_year + asset.depreciation_years - 1

    # Not yet purchased
    if year < first_year:
        return False

    # Already fully depreciated
    if year > last_year:
        return False

    # Disposed before this year (disposal year still gets depreciation)
    if asset.disposal_date and asset.disposal_date.year < year:
        return False

    return True
```

### Asset Status

```python
def get_asset_status(asset: Asset, reference_date: date = None) -> AssetStatus:
    """Determine current status of an asset."""
    if reference_date is None:
        reference_date = date.today()

    if asset.disposal_date:
        return AssetStatus.DISPOSED

    last_year = asset.purchase_date.year + asset.depreciation_years - 1
    if reference_date.year > last_year:
        return AssetStatus.FULLY_DEPRECIATED

    return AssetStatus.ACTIVE
```

## Integration Points

### P&L Summary

The depreciation service provides totals for the "afschrijvingen" category:

```python
def get_total_depreciation_for_year(year: int) -> Decimal:
    """Sum of all depreciation for a fiscal year."""
    entries = get_depreciation_for_year(load_assets(), year)
    return sum(e.amount for e in entries)
```

### Excel Import Mapping

| Excel Column | Asset Field | Transformation |
|--------------|-------------|----------------|
| Column 0 (name) | name | Direct mapping |
| Column 1 (amount) | purchase_amount | Absolute value |
| Column 5 (rate) | depreciation_years | round(1 / rate) |
| Column 7 (notes) | notes | Direct mapping |
| - | purchase_date | Parse from notes or default to first year |
| - | source | "excel_import" |

## Data Integrity Rules

1. **Uniqueness**: Asset ID must be unique across all assets
2. **Amount Precision**: Use Decimal with 2 decimal places for EUR amounts
3. **Date Validity**: All dates must be valid and in expected format
4. **Depreciation Period**: Must be positive integer (1-10 years typical)
5. **Disposal Constraint**: disposal_date must be after purchase_date
6. **No Orphans**: Deleted assets are removed from file (no soft delete)
