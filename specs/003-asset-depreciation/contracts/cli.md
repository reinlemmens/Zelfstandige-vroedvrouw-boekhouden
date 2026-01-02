# CLI Contract: Asset Depreciation Commands

**Feature**: 003-asset-depreciation
**Date**: 2026-01-02

## Command Group: `plv assets`

Manage depreciable business assets and their write-off schedules.

---

## `plv assets add`

Register a new depreciable asset.

### Synopsis

```bash
plv assets add --name NAME --date DATE --amount AMOUNT --years YEARS [OPTIONS]
```

### Options

| Option | Short | Type | Required | Default | Description |
|--------|-------|------|----------|---------|-------------|
| `--name` | `-n` | string | Yes | - | Asset description |
| `--date` | `-d` | date | Yes | - | Purchase date (YYYY-MM-DD) |
| `--amount` | `-a` | decimal | Yes | - | Purchase amount in EUR |
| `--years` | `-y` | int | Yes | - | Depreciation period (1-10) |
| `--notes` | | string | No | null | Additional notes |

### Examples

```bash
# Add a new bike
plv assets add -n "Orbea fiets" -d 2023-01-15 -a 4179.05 -y 3

# Add phone with notes
plv assets add -n "iPhone 14 Pro" -d 2023-06-01 -a 769.00 -y 3 --notes "Business phone"
```

### Output

```
Added asset 'asset-a1b2c3d4': Orbea fiets
  Purchase: €4179.05 on 2023-01-15
  Depreciation: €1393.02/year for 3 years (2023-2025)
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Validation error (invalid date, amount, years) |
| 2 | Duplicate warning (same name + date exists) |

---

## `plv assets list`

List all registered assets with their depreciation status.

### Synopsis

```bash
plv assets list [OPTIONS]
```

### Options

| Option | Short | Type | Required | Default | Description |
|--------|-------|------|----------|---------|-------------|
| `--status` | `-s` | choice | No | all | Filter: active, fully_depreciated, disposed |
| `--year` | `-y` | int | No | current | Show status as of year |
| `--format` | `-o` | choice | No | table | Output: table, json, csv |

### Examples

```bash
# List all assets
plv assets list

# List only active assets
plv assets list -s active

# JSON output for 2025
plv assets list -y 2025 -o json
```

### Output (Table)

```
ID              Name                  Purchase      Amount      Years   Status              Book Value
---------------------------------------------------------------------------------------------------------
asset-a1b2c3d4  Orbea fiets          2023-01-15   €4179.05    3       active (2/3)        €1393.02
asset-e5f6g7h8  iPhone 14 Pro        2023-06-01   €769.00     3       active (2/3)        €256.33

Total: 2 assets | Book value: €1649.35
```

### Output (JSON)

```json
[
  {
    "id": "asset-a1b2c3d4",
    "name": "Orbea fiets",
    "purchase_date": "2023-01-15",
    "purchase_amount": 4179.05,
    "depreciation_years": 3,
    "status": "active",
    "current_year": 2,
    "book_value": 1393.02,
    "annual_depreciation": 1393.02
  }
]
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |

---

## `plv assets depreciation`

Show depreciation schedule for a fiscal year.

### Synopsis

```bash
plv assets depreciation [OPTIONS]
```

### Options

| Option | Short | Type | Required | Default | Description |
|--------|-------|------|----------|---------|-------------|
| `--year` | `-y` | int | No | current | Fiscal year |
| `--format` | `-o` | choice | No | table | Output: table, json, csv |
| `--detail` | `-d` | flag | No | false | Show individual assets |

### Examples

```bash
# Show 2025 depreciation summary
plv assets depreciation -y 2025

# Detailed breakdown
plv assets depreciation -y 2025 -d
```

### Output (Summary)

```
Depreciation Schedule: 2025
===========================

Total depreciation: €1649.35

Category: afschrijvingen
  Orbea fiets:    €1393.02 (year 3 of 3)
  iPhone 14 Pro:  €256.33  (year 3 of 3)
```

### Output (Detailed)

```
Depreciation Schedule: 2025 (Detailed)
======================================

Asset: Orbea fiets (asset-a1b2c3d4)
  Purchase: €4179.05 on 2023-01-15
  Period: 3 years (2023-2025)

  Year   Depreciation   Book Value
  2023   €1393.02       €2786.03
  2024   €1393.02       €1393.02
  2025   €1393.02       €0.00      ← current year

---

Asset: iPhone 14 Pro (asset-e5f6g7h8)
  Purchase: €769.00 on 2023-06-01
  Period: 3 years (2023-2025)

  Year   Depreciation   Book Value
  2023   €256.33        €512.67
  2024   €256.33        €256.33
  2025   €256.33        €0.00      ← current year

===================================
Total 2025 Depreciation: €1649.35
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |

---

## `plv assets dispose`

Mark an asset as disposed (sold/discarded).

### Synopsis

```bash
plv assets dispose ASSET_ID --date DATE [OPTIONS]
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| ASSET_ID | string | Yes | Asset ID to dispose |

### Options

| Option | Short | Type | Required | Default | Description |
|--------|-------|------|----------|---------|-------------|
| `--date` | `-d` | date | Yes | - | Disposal date (YYYY-MM-DD) |
| `--notes` | | string | No | null | Reason for disposal |

### Examples

```bash
# Dispose an asset
plv assets dispose asset-a1b2c3d4 -d 2025-06-01

# With notes
plv assets dispose asset-a1b2c3d4 -d 2025-06-01 --notes "Sold on Marktplaats"
```

### Output

```
Disposed asset 'asset-a1b2c3d4': Orbea fiets
  Disposal date: 2025-06-01
  Final depreciation year: 2025 (full year applied)
  Remaining book value at disposal: €0.00
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Asset not found |
| 2 | Already disposed |
| 3 | Disposal date before purchase date |

---

## `plv assets import`

Import assets from Excel Resultaat sheet (one-time migration).

### Synopsis

```bash
plv assets import EXCEL_FILE [OPTIONS]
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| EXCEL_FILE | path | Yes | Path to Excel file |

### Options

| Option | Short | Type | Required | Default | Description |
|--------|-------|------|----------|---------|-------------|
| `--sheet` | `-s` | string | No | Resultaat | Sheet name |
| `--dry-run` | `-n` | flag | No | false | Preview without saving |
| `--merge` | | flag | No | false | Merge with existing assets |

### Examples

```bash
# Preview import
plv assets import data/2025/Resultatenrekening.xlsx -n

# Actual import
plv assets import data/2025/Resultatenrekening.xlsx

# Merge with existing
plv assets import data/2025/Resultatenrekening.xlsx --merge
```

### Output

```
Importing from: Resultatenrekening.xlsx (sheet: Resultaat)

Found 2 depreciable assets:

  Telefonie          €769.00    3 years (2023-2025)
  Orbea             €4179.05    3 years (2023-2025)

Imported: 2 assets
Skipped: 0 duplicates

(Use --dry-run to preview without saving)
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | File not found |
| 2 | Sheet not found |
| 3 | No assets found |

---

## Global Options (inherited from `plv`)

| Option | Short | Description |
|--------|-------|-------------|
| `--verbose` | `-v` | Show detailed logging |
| `--quiet` | `-q` | Suppress non-essential output |
| `--json` | | Force JSON output |
| `--config` | | Custom config directory |
| `--data-dir` | | Custom data directory |

---

## Integration with Existing Commands

### P&L Summary (future)

The `plv summary` command (to be implemented) will include depreciation:

```bash
plv summary -y 2025
```

```
P&L Summary: 2025
=================

OMZET (Revenue)
  ...

BEROEPSKOSTEN (Expenses)
  ...

AFSCHRIJVINGEN (Depreciation)
  Orbea fiets:         €1393.02
  iPhone 14 Pro:       €256.33
  ─────────────────────────────
  Subtotal:            €1649.35

NETTO BELASTBAAR INKOMEN
  ...
```

### Category Integration

Depreciation amounts are reported under the existing "afschrijvingen" category from `config/categories.yaml`.
