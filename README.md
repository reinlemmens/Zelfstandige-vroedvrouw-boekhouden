# PLV - P&L Tool for Belgian Midwife Tax Filing

A CLI tool to import, categorize, and generate financial reports from bank statements for Belgian self-employed midwives (vroedvrouwen).

## Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install the CLI
pip install -e .
```

## Quick Start

```bash
# Full pipeline in one command (auto-discovers input files)
plv --company goedele run --pdf data/goedele/output/Jaarverslag_2025.pdf

# Or step by step
plv --company goedele import data/goedele/input/2025/*.csv
plv --company goedele categorize
plv --company goedele matches run
plv --company goedele report --pdf data/goedele/output/Jaarverslag_2025.pdf
```

## Commands

### Run Full Pipeline

Run import, categorize, match, and report in one command:

```bash
# With --company: auto-discovers files in data/<company>/input/<year>/
plv --company goedele run
plv --company goedele run -y 2024              # Use specific year

# With explicit files
plv run data/input/*.csv
plv run data/input/*.csv -o report.xlsx
plv run data/input/*.csv --pdf Jaarverslag_2025.pdf

# Both outputs
plv --company goedele run -o report.xlsx --pdf Jaarverslag_2025.pdf

# With AI-generated insights (~$0.05-0.10)
plv --company goedele run --pdf Jaarverslag_2025.pdf --llm

# Dry run (preview without saving)
plv --company goedele run -n
```

The `run` command executes these steps:
1. **Import** - Load transactions from CSV/PDF files
2. **Categorize** - Apply categorization rules
3. **Match** - Auto-match verkeerde-rekening pairs
4. **Report** - Generate P&L report

### Import Transactions

Import bank CSV and Mastercard PDF files:

```bash
# Import CSV files
plv import data/input/*.csv

# Import PDF files (Mastercard statements)
plv import data/input/*.pdf

# Import for specific year
plv import -y 2025 data/input/*.csv

# Dry run (preview without saving)
plv import -n data/input/*.csv

# Force re-import duplicates
plv import -f data/input/*.csv
```

### Categorize Transactions

Apply categorization rules to transactions:

```bash
# Categorize uncategorized transactions
plv categorize

# Re-categorize all transactions
plv categorize --all

# Dry run
plv categorize -n
```

### Match Verkeerde-Rekening Transactions

Match private expenses with their reimbursements:

```bash
# Run auto-matching
plv matches run

# Preview matches without saving
plv matches run --dry-run

# List all matches
plv matches list

# List including rejected matches
plv matches list --all

# Create manual match
plv matches create <expense_tx_id> <reimbursement_tx_id>

# Reject an incorrect match
plv matches reject <match_id>
```

**How matching works:**
- Finds "verkeerde-rekening" expenses (negative) and reimbursements (positive)
- Scores candidates based on:
  - Keywords (+50 pts): "terugbetaling", "verkeerde rekening", "foutieve rekening"
  - Date proximity (0-30 pts): Linear decay over 90 days
  - Vendor similarity (+20 pts): Vendor name appears in reimbursement description
- Auto-matches when score >= 50 and no ambiguity (single candidate)
- Matched pairs are excluded from Aandachtspunten warnings in reports

### Generate Reports

```bash
# Console output
plv report

# Excel export
plv report -o data/output/PL_2025.xlsx

# PDF management report
plv report --pdf data/output/Jaarverslag_2025.pdf

# With AI-generated insights (~$0.05-0.10)
plv report --pdf data/output/Jaarverslag_2025.pdf --llm

# Specific fiscal year
plv report -y 2024
```

### List Transactions

```bash
# List recent transactions
plv list

# Filter by category
plv list -c restaurant

# Show uncategorized only
plv list -u

# Show therapeutic income only
plv list -t

# Date range
plv list --from 2025-01-01 --to 2025-03-31

# Output formats
plv list -o json
plv list -o csv
```

### Assign Category Manually

```bash
# Assign category to a transaction
plv assign <transaction_id> <category>

# Mark as therapeutic income
plv assign <transaction_id> omzet --therapeutic
```

### Manage Rules

```bash
# List all rules
plv rules list

# Filter by category
plv rules list -c restaurant

# Add a new rule
plv rules add -p "COLRUYT" -c bureelbenodigdheden

# Add with regex pattern
plv rules add -p "ALDI.*STORE" -c bureelbenodigdheden -t regex

# Test a pattern
plv rules test "COLRUYT"

# Disable a rule
plv rules disable <rule_id>
```

### Manage Assets (Depreciation)

```bash
# Add a new asset
plv assets add -n "Laptop" -d 2025-01-15 -a 1200 -y 3

# List all assets
plv assets list

# Show depreciation schedule
plv assets depreciation -y 2025

# Import assets from Excel
plv assets import data/input/Boekhouding_2024.xlsx

# Mark asset as disposed
plv assets dispose <asset_id> -d 2025-06-01
```

### Bootstrap Rules from Excel

Extract categorization rules from historical Excel files:

```bash
# Extract rules
plv bootstrap data/input/Boekhouding_*.xlsx

# Merge with existing rules
plv bootstrap --merge data/input/Boekhouding_*.xlsx

# Dry run
plv bootstrap -n data/input/Boekhouding_*.xlsx
```

### Multi-Company Support

```bash
# List configured companies
plv company list

# Initialize new company
plv company init acme

# Copy config from existing company
plv company init acme --copy-from goedele

# Run commands for specific company
plv --company goedele import ...
plv --company goedele report ...
```

## Directory Structure

```
data/
├── goedele/                    # Company directory
│   ├── input/
│   │   └── 2025/              # Bank statements by year
│   │       ├── bank_2025.csv
│   │       └── mastercard_2025.pdf
│   ├── output/
│   │   ├── transactions.json  # Imported transactions
│   │   ├── matches.json       # Reconciliation matches
│   │   └── assets.json        # Depreciable assets
│   └── config/
│       ├── rules.yaml         # Categorization rules
│       ├── categories.yaml    # Category definitions
│       └── settings.yaml      # Company settings
└── output/                    # Default output (no company)
```

## Global Options

```bash
plv --help                    # Show help
plv --version                 # Show version
plv -v ...                    # Verbose output
plv -q ...                    # Quiet mode
plv -j ...                    # JSON output
plv -c goedele ...            # Use company config
```

## Categories

Key expense categories:
- `omzet` - Revenue (therapeutic/non-therapeutic)
- `restaurant` - Restaurant expenses (69% deductible)
- `onthaal` - Entertainment (50% deductible)
- `bureelbenodigdheden` - Office supplies
- `klein-materiaal` - Small equipment
- `afschrijvingen` - Depreciation
- `verkeerde-rekening` - Private expenses (wrong account)
- `contractors` - Subcontractor payments

## Typical Workflow

1. **Setup** (once per company):
   ```bash
   plv company init goedele
   # Copy bank statements to data/goedele/input/2025/
   plv --company goedele bootstrap data/goedele/input/*.xlsx
   ```

2. **Monthly/Quarterly**:
   ```bash
   plv --company goedele import data/goedele/input/2025/*.csv
   plv --company goedele categorize
   plv --company goedele matches run
   plv --company goedele list -u  # Check uncategorized
   ```

3. **Year-end**:
   ```bash
   plv --company goedele report -y 2025 --pdf data/goedele/output/Jaarverslag_2025.pdf
   ```

## License

Private - All rights reserved.
