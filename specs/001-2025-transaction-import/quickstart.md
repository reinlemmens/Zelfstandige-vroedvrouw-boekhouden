# Quickstart: 2025 Transaction Import

**Feature**: 001-2025-transaction-import
**Date**: 2026-01-02

## Overview

This feature imports financial transactions from Belfius bank CSV exports and Mastercard PDF statements, deduplicates them, and outputs a consolidated Google Sheet.

## Prerequisites

- Python 3.11+ installed
- Claude Code with Google Drive MCP configured
- Source files in `data/2025/`:
  - Belfius CSV exports (`BE*.csv`)
  - Mastercard PDF statements (`*.pdf`)

## Quick Implementation Path

### Step 1: Parse CSV Files

```python
import pandas as pd
from pathlib import Path

def parse_belfius_csv(file_path: Path) -> pd.DataFrame:
    """Parse Belfius bank CSV export."""
    df = pd.read_csv(
        file_path,
        sep=';',
        decimal=',',
        thousands='.',
        skiprows=12,  # Skip metadata rows
        encoding='utf-8'
    )
    df['source_file'] = file_path.name
    return df
```

### Step 2: Parse PDF Files

```python
import pdfplumber

def parse_mastercard_pdf(file_path: Path) -> dict:
    """Extract transactions from Mastercard PDF."""
    with pdfplumber.open(file_path) as pdf:
        # Extract text and tables from first page
        page = pdf.pages[0]
        tables = page.extract_tables()
        # Parse transaction table (usually second table)
        # Return structured data
```

### Step 3: Deduplicate

```python
def create_dedup_key(row: dict) -> str:
    """Create unique key for deduplication."""
    return f"{row['account']}|{row['date']}|{row['txn_num']}|{row['ref']}"

def deduplicate(transactions: list) -> list:
    """Remove duplicate transactions."""
    seen = set()
    unique = []
    for txn in transactions:
        key = create_dedup_key(txn)
        if key not in seen:
            seen.add(key)
            unique.append(txn)
    return unique
```

### Step 4: Output to Google Sheet

Use the MCP tool directly in Claude Code:

```
mcp__google-drive__createGoogleSheet(
    name="2025 Transactions - Vroedvrouw Goedele",
    data=[
        ["Date", "Account", "Amount", "Counterparty", "Description", "Reference", "Type", "Source"],
        ["2025-01-15", "BE05 0636...", "-50.00", "Example", "Payment", "REF123", "regular", "file.csv"],
        ...
    ],
    parentFolderId="1TJAIGg_RlomBlyPXjnKYH0XJWg2osxdW"
)
```

## Key Files

| File | Purpose |
|------|---------|
| `data/2025/*.csv` | Belfius bank statement exports |
| `data/2025/*.pdf` | Mastercard monthly statements |
| `specs/001-2025-transaction-import/spec.md` | Feature specification |
| `specs/001-2025-transaction-import/data-model.md` | Data model documentation |

## Common Patterns

### European Number Format
```python
# Convert "1.234,56" to 1234.56
amount_str = "1.234,56"
amount = float(amount_str.replace('.', '').replace(',', '.'))
```

### Date Parsing
```python
from datetime import datetime
# Belfius format: DD/MM/YYYY
date = datetime.strptime("15/03/2025", "%d/%m/%Y")
```

### Mastercard Settlement Detection
```python
def is_mastercard_settlement(description: str) -> bool:
    """Check if bank entry is a Mastercard settlement."""
    patterns = ["5440 56", "MASTERCARD", "KREDIETKAART"]
    return any(p in description.upper() for p in patterns)
```

## Verification Steps

1. **Count check**: Total unique transactions should match sum of (CSV transactions - duplicates + PDF transactions - settlements)
2. **Amount check**: Sum of all non-settlement transactions should match expected total
3. **Source check**: Every transaction should have a valid `source_file` value
4. **Date check**: All transactions should be within 2025

## Troubleshooting

| Issue | Solution |
|-------|----------|
| CSV encoding errors | Try `encoding='latin-1'` or `encoding='cp1252'` |
| PDF table not found | Check page number, Mastercard tables may span pages |
| Amount mismatch | Verify settlement linking by date ±1 day |
| Missing transactions | Check date filter boundaries (inclusive) |
