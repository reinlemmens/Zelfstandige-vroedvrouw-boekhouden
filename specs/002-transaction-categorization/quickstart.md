# Quickstart: Transaction Categorization

**Feature**: 002-transaction-categorization
**Date**: 2026-01-02

## Prerequisites

- Python 3.11+
- Bank statement CSV files from Belfius
- Mastercard PDF statements from Belfius (optional)
- Historical Excel files for rule bootstrap (recommended)

## Installation

```bash
# Clone and setup
cd PLVroedvrouwGoedele
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quick Start (5 minutes)

### 1. Bootstrap Rules from Historical Data

Extract categorization patterns from your existing Excel files:

```bash
plv bootstrap \
  data/2024/Resultatenrekening\ Vroedvrouw\ Goedele\ 2024.xlsx \
  data/2025/Resultatenrekening\ Vroedvrouw\ Goedele\ 2025.xlsx
```

This creates `config/rules.yaml` with ~50-80 rules covering most vendors.

### 2. Import Transactions

Import bank statements and Mastercard PDFs:

```bash
# Import all 2025 data
plv import data/2025/bank/*.csv data/2025/mastercard/*.pdf --year 2025
```

Expected output:
```
Imported: 487 transactions
Skipped duplicates: 0
Excluded (MC settlements): 12
```

### 3. Auto-Categorize

Apply rules to imported transactions:

```bash
plv categorize
```

Expected output:
```
Categorized: 445 (91%)
Uncategorized: 42 (9%)
```

### 4. Review Uncategorized

List transactions that need manual attention:

```bash
plv list --uncategorized
```

### 5. Manually Assign Categories

For each uncategorized transaction:

```bash
# View categories
plv categories

# Assign category
plv assign 00012-476 vervoer
```

### 6. Add New Rules (Optional)

Create rules for recurring vendors:

```bash
plv rules add --pattern "NEW VENDOR" --category klein-materiaal
```

## File Locations

| Purpose | Location |
|---------|----------|
| Input: Bank CSV | `data/2025/bank/*.csv` |
| Input: Mastercard PDF | `data/2025/mastercard/*.pdf` |
| Config: Categories | `config/categories.yaml` |
| Config: Rules | `config/rules.yaml` |
| Output: Transactions | `data/output/transactions.json` |

## Common Tasks

### Check Import Status
```bash
plv list --year 2025 --format json | jq '.total'
```

### Export for Review
```bash
plv list --year 2025 --format csv > review.csv
```

### Mark Therapeutic Revenue
```bash
plv assign 00012-500 omzet --therapeutic
```

### Test a Pattern Before Adding
```bash
plv rules test "PROXIMUS" --type contains
```

## Troubleshooting

### "Amount parsing failed"
Belgian format uses comma as decimal separator. Ensure CSV is in original Belfius format.

### "Duplicate transaction skipped"
Transaction already imported. Use `--force` to re-import if needed.

### "PDF extraction failed"
Ensure PDF is a valid Belfius Mastercard statement. Some password-protected PDFs require unlocking first.

## Next Steps

After all transactions are categorized:
1. Generate P&L report (separate feature)
2. Review therapeutic vs non-therapeutic revenue split
3. Export for tax filing
