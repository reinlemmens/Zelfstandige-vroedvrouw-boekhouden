# Quickstart: Transaction Categorization

**Feature**: 002-transaction-categorization
**Date**: 2026-01-02
**Updated**: 2026-01-03 (Maatschap support)

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

## Maatschap (Partnership) Accounts

For Maatschap accounts like "Huis van Meraki", transactions between partners require special categorization based on the description field rather than the counterparty name.

### 1. Configure Maatschap Account

Create or update `config/accounts.yaml`:

```yaml
version: "1.0"
accounts:
  - id: goedele
    name: "Vroedvrouw Goedele"
    iban: "BE05 0636 4778 9475"
    account_type: standard

  - id: meraki
    name: "Huis van Meraki"
    iban: "BE98 0689 5286 6793"
    account_type: maatschap
    partners:
      - name: "Vroedvrouw Goedele Deseyn"
        iban: "BE05 0636 4778 9475"
      - name: "HUIS VAN MERAKI - LEILA RCHAIDIA BV"
        iban: "BE27 7370 6541 0173"
```

### 2. Import Maatschap Transactions

```bash
plv import data/meraki/bank/*.csv --year 2025 --account meraki
```

### 3. Categorization Priority

For Maatschap accounts, description-based rules are applied first:

| Description Contains | Category | Example |
|---------------------|----------|---------|
| "Inkomstenverdeling" | `winstverdeling` | Profit distribution to partners |
| "Verkeerde rekening" | `verkeerde-rekening` | Wrong account correction |
| "Google workspace" | `licenties-software` | Software cost reimbursement |
| "Q1", "Q2", "Q3", "Q4" | `contractors` | Partner work payment |
| Invoice number (20XXYYZZZ) | `contractors` | Partner work payment |

### 4. Example Transactions

```
Transaction: -10347.50 EUR to "Vroedvrouw Goedele Deseyn"
Description: "Inkomstenverdeling 2025 Maatschap huis van Meraki"
→ Category: winstverdeling (profit distribution)

Transaction: -1050.00 EUR to "Vroedvrouw Goedele Deseyn"
Description: "Q3 maatschap"
→ Category: contractors (work payment)

Transaction: -125.00 EUR to "HUIS VAN MERAKI - LEILA RCHAIDIA BV"
Description: "Google workspace 2024-2025"
→ Category: licenties-software (cost reimbursement)
```

### 5. Difference: Loon vs Contractors

- **Loon**: Payments to private persons (natural persons) for work done
- **Contractors**: Payments for work to companies (BVs) or independent entities

Partner work payments in a Maatschap use `contractors` because partners typically bill through their BV or as independents.

## File Locations

| Purpose | Location |
|---------|----------|
| Input: Bank CSV | `data/2025/bank/*.csv` |
| Input: Mastercard PDF | `data/2025/mastercard/*.pdf` |
| Config: Categories | `config/categories.yaml` |
| Config: Rules | `config/rules.yaml` |
| Config: Accounts | `config/accounts.yaml` |
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
