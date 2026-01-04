# Claude Code Project Guide

## Project Overview

PLV (Profit & Loss for Vroedvrouw) is a financial reporting tool for Belgian self-employed midwives (vroedvrouwen). It processes bank statements and generates P&L reports for tax filing.

## Running Python Code

This project uses macOS with an externally-managed Python environment. To run Python code:

### Option 1: Virtual Environment (Recommended)
```bash
# Create a virtual environment
python3 -m venv /tmp/venv

# Activate and install dependencies
source /tmp/venv/bin/activate
pip install pandas pdfplumber openpyxl click pyyaml

# Run CLI
python3 -m src.cli.main --help
```

### Option 2: Direct CLI usage
```bash
source /tmp/venv/bin/activate
plv --help
```

## CLI Commands

The `plv` CLI tool provides the following commands:

### Import
```bash
plv import data/2025/*.csv data/2025/*.pdf -y 2025
```
- Imports transactions from Belfius CSV files and Mastercard PDF statements
- Automatically detects and excludes Mastercard settlement transactions
- Supports fiscal year filtering

### Categorize
```bash
plv categorize -y 2025 --all
```
- Applies rules from `config/rules.yaml` to categorize transactions
- Use `--all` to re-categorize already categorized transactions

### Report
```bash
plv report -y 2025 -o "data/output/report_2025.xlsx"
```
- Generates P&L report for the specified fiscal year
- Exports to Excel format when output path specified

#### AI-Enhanced Reports (LLM Feature)
```bash
# Generate PDF with AI-generated insights
plv --company goedele report -y 2025 --pdf Jaarverslag_2025.pdf --llm
```

**Setup**: Configure your Anthropic API key:
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

For persistent configuration, add to `~/.zshrc` or `~/.bashrc`.

Get your API key from: https://console.anthropic.com/

**Cost**: ~$0.05-0.10 per report. Falls back to static text if API is unavailable.

### Export
```bash
plv export -y 2025 -o "data/output/transactions_2025.xlsx"
```
- Exports all transactions to Excel or CSV

### Bootstrap (extract rules from Excel)
```bash
plv bootstrap "data/2024/Resultatenrekening 2024.xlsx" --merge
```
- Extracts categorization patterns from a manually categorized Excel file
- Use `--merge` to combine with existing rules

## Project Structure

```
PLVroedvrouwGoedele/
├── config/
│   ├── categories.yaml     # Category definitions
│   ├── rules.yaml          # Categorization rules (204 patterns)
│   └── settings.yaml       # Application settings
├── data/
│   ├── 2025/               # Source financial data
│   │   ├── *.csv           # Belfius bank statements
│   │   └── *.pdf           # Mastercard statements
│   └── output/
│       └── transactions.json  # Imported transactions database
├── src/
│   ├── cli/main.py         # CLI entry point
│   ├── models/             # Data models
│   │   ├── transaction.py
│   │   ├── rule.py
│   │   ├── asset.py
│   │   └── report.py
│   └── services/           # Business logic
│       ├── csv_importer.py
│       ├── pdf_importer.py
│       ├── categorizer.py
│       ├── report_generator.py
│       └── depreciation.py
└── specs/                  # Feature specifications
```

## Belgian Tax Rules

### Partially Deductible Expenses
- **Restaurant**: 69% deductible
- **Onthaal** (reception): 50% deductible
- **Relatiegeschenken** (business gifts): 50% deductible

### Excluded Categories (not in P&L)
- `prive-opname`: Private withdrawals to personal accounts
- `verkeerde-rekening`: Corrections for wrong account
- `interne-storting`: Internal transfers
- `mastercard`: Settlement transactions (details in PDF)

### Income Categories
- `omzet`: Revenue, split into:
  - Therapeutic (RIZIV reimbursed): Lower VAT rate
  - Non-therapeutic: Standard rate

## Categorization Rules

Rules are stored in `config/rules.yaml` and follow this structure:
```yaml
rules:
  - id: "rule-unique-id"
    pattern: "COUNTERPARTY NAME"
    pattern_type: contains  # exact, prefix, contains, regex
    match_field: counterparty_name
    target_category: category-id
    priority: 100
    source: extracted  # or manual
    is_therapeutic: true  # optional, for omzet only
```

### Key Patterns
- `Lemmens R-Deseyn G` → `prive-opname` (private account)
- `Acerta` → `sociale-bijdragen` (social contributions)
- Hospitals and care centers → `omzet` with `is_therapeutic: true`

## Data Processing Notes

- CSV files use semicolon delimiter (`;`) and European number format (comma as decimal)
- PDF Mastercard statements require `pdfplumber` for extraction
- All amounts are in EUR
- Transaction IDs are `{statement_number}-{transaction_number}`

## MCP Integrations

- **Google Drive MCP**: Available for file operations (sheets, docs, etc.)
- **Google Calendar MCP**: Available for calendar operations

## Data Quality Warnings

The report generator automatically detects and displays data quality warnings in both PDF and Excel reports.

### Warning Types

1. **Uncategorized Transactions**: Transactions without an assigned category
   - Displayed as count and total amount
   - Listed in detail in the "Aandachtspunten" section

2. **Verkeerde-rekening (Private Expenses)**: Non-zero balance in private expense category
   - Should net to zero when expenses match reimbursements
   - Negative balance = unreimbursed private expenses
   - Positive balance = over-reimbursed

### PDF Report
- Warning banner appears on page 1 after the summary table
- Detailed "Aandachtspunten" section before conclusion with transaction listings
- Actionable advice for each issue type

### Excel Export
- Warning messages on P&L sheet
- "Aandachtspunten" sheet with full transaction details
- Only created when data quality issues exist

### Model Properties
```python
report.has_data_quality_warnings  # True if any warnings exist
report.total_uncategorized        # Sum of uncategorized transaction amounts
report.verkeerde_rekening_balance # Net balance (should be 0)
report.verkeerde_rekening_items   # List of private expense transactions
```

## Recent Changes

### 2025 Financial Year Processing
- Imported 825 transactions (805 regular, 6 settlements, 14 mastercard details)
- Extracted 204 categorization rules from manually categorized data
- Final P&L: €72,618.50 income, €36,039.95 expenses, €36,578.55 net profit
- Social contributions: €13,557.89

### Active Technologies
- Python 3.11+ with Click (CLI), PyYAML (config), openpyxl (Excel), pandas (data)
- JSON file storage (`data/output/transactions.json`, `data/assets.json`)

## Active Technologies
- Python 3.11+ + reportlab (PDF generation), pandas, openpyxl (005-jaarverslag)
- JSON file storage (`data/{company}/transactions.json`, `data/assets.json`) (005-jaarverslag)
