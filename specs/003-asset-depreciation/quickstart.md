# Quickstart: Asset Depreciation Tracking

**Feature**: 003-asset-depreciation

This guide walks through the complete asset depreciation workflow.

## Prerequisites

- PLV tool installed and working (`plv --version`)
- Transactions imported (`plv import data/2025/*.csv`)
- For Excel import: Existing Resultatenrekening Excel file

## Workflow Overview

```
┌─────────────────────┐
│  1. Import Assets   │  One-time migration from Excel
│     (or add manually) │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  2. View Schedule   │  Check depreciation for any year
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  3. Include in P&L  │  Depreciation added to tax report
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  4. Manage Assets   │  Add new, dispose old
└─────────────────────┘
```

## Step 1: Import Existing Assets from Excel

If you have assets in your Resultatenrekening Excel file:

```bash
# Preview what will be imported
plv assets import "data/2025/Resultatenrekening Vroedvrouw Goedele 2025.xlsx" --dry-run

# Output:
# Found 2 depreciable assets:
#   Telefonie          €769.00    3 years (2023-2025)
#   Orbea             €4179.05    3 years (2023-2025)

# Perform the import
plv assets import "data/2025/Resultatenrekening Vroedvrouw Goedele 2025.xlsx"

# Output:
# Imported: 2 assets
```

## Step 2: Verify Assets

Check that assets were imported correctly:

```bash
plv assets list

# Output:
# ID              Name                  Purchase      Amount      Years   Status
# ---------------------------------------------------------------------------------
# asset-a1b2c3d4  Orbea fiets          2023-01-15   €4179.05    3       active (2/3)
# asset-e5f6g7h8  iPhone 14 Pro        2023-06-01   €769.00     3       active (2/3)
#
# Total: 2 assets | Book value: €1649.35
```

## Step 3: View Depreciation Schedule

See write-offs for a specific year:

```bash
# Current year depreciation
plv assets depreciation

# Specific year
plv assets depreciation -y 2025

# Output:
# Depreciation Schedule: 2025
# ===========================
#
# Total depreciation: €1649.35
#
# Category: afschrijvingen
#   Orbea fiets:    €1393.02 (year 3 of 3)
#   iPhone 14 Pro:  €256.33  (year 3 of 3)
```

## Step 4: Add New Assets (Manual)

When you buy a new depreciable item:

```bash
# Add a new laptop
plv assets add \
  --name "MacBook Pro 14" \
  --date 2025-03-15 \
  --amount 2499.00 \
  --years 5 \
  --notes "Primary work laptop"

# Output:
# Added asset 'asset-x1y2z3w4': MacBook Pro 14
#   Purchase: €2499.00 on 2025-03-15
#   Depreciation: €499.80/year for 5 years (2025-2029)
```

## Step 5: Dispose of Assets

When you sell or discard an asset:

```bash
# Mark phone as disposed (sold)
plv assets dispose asset-e5f6g7h8 --date 2026-01-15 --notes "Upgraded to new phone"

# Output:
# Disposed asset 'asset-e5f6g7h8': iPhone 14 Pro
#   Disposal date: 2026-01-15
#   Final depreciation year: 2025 (already completed)
```

## Step 6: Use in P&L Summary

View depreciation as part of your P&L:

```bash
# Future command - once P&L summary is implemented
plv summary -y 2025

# The "afschrijvingen" section will show:
#
# AFSCHRIJVINGEN (Depreciation)
#   Orbea fiets:         €1393.02
#   iPhone 14 Pro:       €256.33
#   ─────────────────────────────
#   Subtotal:            €1649.35
```

## Common Scenarios

### Check Next Year's Depreciation

```bash
# See what depreciation will be in 2026
plv assets depreciation -y 2026

# Only new assets will appear (bike and phone are fully depreciated)
```

### Export for Accountant

```bash
# JSON format for data processing
plv assets list -o json > assets_2025.json

# Depreciation schedule as JSON
plv assets depreciation -y 2025 -o json > depreciation_2025.json
```

### Filter by Status

```bash
# Only active assets
plv assets list -s active

# Fully depreciated
plv assets list -s fully_depreciated

# Disposed
plv assets list -s disposed
```

## Typical Annual Workflow

At the start of each year:

1. **Review assets**: `plv assets list` - check what's still active
2. **Check depreciation**: `plv assets depreciation -y 2026` - see this year's write-offs
3. **Add new purchases**: `plv assets add ...` - register any new assets
4. **Dispose old items**: `plv assets dispose ...` - mark sold/discarded items
5. **Generate P&L**: Include depreciation in tax filing

## Troubleshooting

### "No assets found"

```bash
# Check if assets.json exists
ls -la data/output/assets.json

# If missing, import from Excel or add manually
plv assets import "data/2025/Resultatenrekening.xlsx"
```

### Wrong depreciation amount

Verify the asset details:

```bash
plv assets list -o json | grep -A 10 "asset-id"
```

Check that:
- `purchase_amount` is correct
- `depreciation_years` matches expected period
- `purchase_date` year is correct (affects which years get depreciation)

### Duplicate asset warning

If you see a duplicate warning during import:

```bash
# Use --merge to add only new assets
plv assets import file.xlsx --merge
```

## File Locations

| File | Purpose |
|------|---------|
| `data/output/assets.json` | Asset data storage |
| `config/categories.yaml` | Contains "afschrijvingen" category |
| `data/2025/*.xlsx` | Source Excel files for import |
