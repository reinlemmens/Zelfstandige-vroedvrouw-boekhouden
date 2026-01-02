# Research: Asset Depreciation Tracking

**Feature**: 003-asset-depreciation
**Date**: 2026-01-02

## Executive Summary

This research documents technical decisions for implementing asset depreciation tracking. No major unknowns existed - the feature extends the existing PLV codebase with consistent patterns.

## Research Topics

### 1. Depreciation Calculation Method

**Decision**: Straight-line depreciation with full-year periods (no pro-rating)

**Rationale**:
- Matches user's current Excel practice (confirmed in clarification session)
- Standard method for Belgian small business assets
- Simplest to implement and audit

**Alternatives Considered**:
- Pro-rated first/last year: Rejected - user confirmed full-year approach matches current practice
- Declining balance method: Rejected - not currently used, adds complexity

**Implementation**:
```python
annual_depreciation = purchase_amount / depreciation_years
# Applied for each year from purchase_year to (purchase_year + depreciation_years - 1)
```

### 2. Asset ID Generation

**Decision**: UUID-based IDs with readable prefix

**Rationale**:
- Unique across all assets
- No collision risk when importing from Excel
- Readable prefix helps with debugging

**Implementation**:
```python
asset_id = f"asset-{uuid.uuid4().hex[:8]}"  # e.g., "asset-a1b2c3d4"
```

### 3. Data Persistence Format

**Decision**: JSON file at `data/output/assets.json`

**Rationale**:
- Consistent with existing `transactions.json` pattern
- Human-readable for debugging
- Easy to version control

**Alternatives Considered**:
- YAML: Rejected - transactions use JSON, consistency is valuable
- SQLite: Rejected - violates Constitution V (Simplicity)

**JSON Structure**:
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
      "source": "excel_import"
    }
  ]
}
```

### 4. Excel Import Strategy

**Decision**: Parse Resultaat sheet rows with fractional depreciation rate (e.g., 0.333333)

**Rationale**:
- Resultaat sheet contains all current assets with their depreciation rates
- Rate indicates depreciation period (1/3 = 3 years, 1/5 = 5 years)
- Column structure is stable (confirmed in spec assumptions)

**Source Data (from Excel)**:
```
Row 28: Telefonie | -769 | 0.333333 | -256.33 | Afschrijving gsm 2023, 2024, 2025
Row 29: Orbea | -4179.05 | 0.333333 | -1393.02 | Afschrijving fiets 2023, 2024, 2025
```

**Parsing Logic**:
1. Find rows with fractional rate (0 < rate < 1)
2. Calculate depreciation_years = round(1 / rate)
3. Extract name, amount, notes
4. Infer purchase_year from notes (parse "2023, 2024, 2025" → first year is purchase year)

### 5. P&L Integration Approach

**Decision**: Depreciation service calculates totals, P&L summary aggregates

**Rationale**:
- Depreciation is a computed value, not a transaction
- Should appear as separate line item under "afschrijvingen" category
- Does not need to be stored as a transaction

**Implementation**:
1. `depreciation.py` provides `get_depreciation_for_year(year)` → returns list of (asset, amount) tuples
2. P&L summary (future feature) calls this service and adds to category totals
3. Category "afschrijvingen" already exists in categories.yaml

### 6. Disposal Handling

**Decision**: Disposal date stops future depreciation, disposal year gets full depreciation

**Rationale**:
- Consistent with "no pro-rating" approach (user confirmed)
- Simpler implementation
- Matches common Belgian practice for small assets

**Implementation**:
```python
def is_depreciating_in_year(asset, year):
    # Check if asset was active at any point in the year
    if asset.purchase_date.year > year:
        return False  # Not yet purchased
    if asset.disposal_date and asset.disposal_date.year < year:
        return False  # Disposed before this year
    # Check if fully depreciated
    last_depreciation_year = asset.purchase_date.year + asset.depreciation_years - 1
    if year > last_depreciation_year:
        return False  # Fully depreciated
    return True
```

### 7. CLI Command Structure

**Decision**: `plv assets` subcommand group with add/list/depreciation/dispose/import

**Rationale**:
- Follows existing pattern (`plv rules` is a command group)
- Clear separation from transaction commands
- Logical grouping of related operations

**Commands**:
- `plv assets add` - Register new asset
- `plv assets list` - Show all assets with status
- `plv assets depreciation` - Show depreciation schedule for a year
- `plv assets dispose` - Mark asset as disposed
- `plv assets import` - One-time Excel import

## Dependencies Analysis

No new dependencies required. Feature uses existing:
- `click` - CLI framework (already in use)
- `openpyxl` - Excel reading (already in use for rule extraction)
- `pandas` - Data processing (already in use)
- Standard library: `uuid`, `datetime`, `json`, `dataclasses`

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Excel format changes | Low | Medium | Validate import with current file before release |
| Rounding errors in depreciation | Low | Low | Use Decimal type, compare against Excel within €0.01 |
| Asset ID collision | Very Low | Low | UUID provides sufficient uniqueness |

## Conclusion

All research topics resolved with clear decisions. Feature is ready for Phase 1 (design artifacts).
