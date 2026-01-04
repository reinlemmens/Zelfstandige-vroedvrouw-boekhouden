# Quickstart: Report Data Quality Warnings

**Feature**: 007-report-warnings
**Date**: 2026-01-04

## Overview

This document provides test scenarios and manual verification steps for the data quality warnings feature.

## Prerequisites

- Python 3.11+ with virtual environment activated
- PLV CLI installed (`pip install -e .`)
- Test data in `data/goedele/` directory

## Test Scenarios

### Scenario 1: No Warnings (Clean Data)

**Setup**: All transactions categorized, verkeerde-rekening balanced

```bash
# Generate report for a year with clean data
plv --company goedele report -y 2025 --pdf /tmp/test-clean.pdf -o /tmp/test-clean.xlsx
```

**Expected PDF Output**:
- No warning banner on page 1
- No Aandachtspunten section at end
- Normal report structure

**Expected Excel Output**:
- No Aandachtspunten sheet
- P&L sheet without warning message

---

### Scenario 2: Uncategorized Transactions Warning

**Setup**: Create test data with uncategorized transactions

```python
# Test data setup (in test fixture)
transactions = [
    Transaction(id="test-1", category=None, amount=Decimal("-100.00"), ...),
    Transaction(id="test-2", category=None, amount=Decimal("-50.00"), ...),
]
```

**Verification Command**:
```bash
plv --company goedele report -y 2025 --pdf /tmp/test-uncat.pdf
```

**Expected PDF Output**:
- Warning banner on page 1 after summary table:
  ```
  ⚠ AANDACHTSPUNTEN: 2 niet-gecategoriseerde transacties (€ -150,00)
  ```
- Aandachtspunten section at end with:
  - Section heading "Aandachtspunten"
  - Subheading "Niet-gecategoriseerde transacties"
  - Table listing all uncategorized transactions with date, amount, counterparty, description
  - Actionable text: "Controleer en categoriseer deze transacties"

**Expected Excel Output**:
- Aandachtspunten sheet with:
  - Row 1: "Aandachtspunten - Boekjaar 2025"
  - Row 3: "Niet-gecategoriseerde transacties: 2 (€ -150,00)"
  - Row 5+: Transaction details table

---

### Scenario 3: Verkeerde-rekening Warning (Unreimbursed)

**Setup**: Private expenses without matching reimbursements

```python
# Test data setup
transactions = [
    # Private expense
    Transaction(id="vr-1", category="verkeerde-rekening", amount=Decimal("-218.70"), ...),
    # Partial reimbursement (leaves balance of -118.70)
    Transaction(id="vr-2", category="verkeerde-rekening", amount=Decimal("100.00"), ...),
]
```

**Expected PDF Output**:
- Warning banner on page 1:
  ```
  ⚠ AANDACHTSPUNTEN: Verkeerde rekening niet in balans (€ -118,70)
  ```
- Aandachtspunten section with:
  - Subheading "Privé-uitgaven (verkeerde rekening)"
  - Net balance displayed
  - Table of all verkeerde-rekening transactions
  - Actionable text: "Voeg ontbrekende terugbetalingen toe of corrigeer categorisatie"

**Expected Excel Output**:
- Aandachtspunten sheet with:
  - "Privé-uitgaven niet in balans: € -118,70"
  - Transaction details for all verkeerde-rekening entries

---

### Scenario 4: Both Warnings

**Setup**: Both uncategorized and unbalanced verkeerde-rekening

**Expected PDF Output**:
- Warning banner with both warnings:
  ```
  ⚠ AANDACHTSPUNTEN:
  • 2 niet-gecategoriseerde transacties (€ -150,00)
  • Verkeerde rekening niet in balans (€ -118,70)
  ```
- Aandachtspunten section with both subsections

**Expected Excel Output**:
- Aandachtspunten sheet with both warning types and transaction details

---

### Scenario 5: Over-reimbursed Verkeerde-rekening

**Setup**: More reimbursements than expenses

```python
transactions = [
    Transaction(id="vr-1", category="verkeerde-rekening", amount=Decimal("-100.00"), ...),
    Transaction(id="vr-2", category="verkeerde-rekening", amount=Decimal("150.00"), ...),
]
```

**Expected Output**:
- Warning shows positive balance:
  ```
  ⚠ AANDACHTSPUNTEN: Verkeerde rekening niet in balans (€ +50,00)
  ```
- Actionable text: "Controleer of alle terugbetalingen correct zijn gecategoriseerd"

---

## Visual Verification Checklist

### PDF Report
- [ ] Warning banner has orange/amber background (#FEF3C7)
- [ ] Warning banner appears immediately after summary table on page 1
- [ ] Aandachtspunten section appears before Conclusie section
- [ ] Section uses consistent heading styles (SectionHeading, SubHeading)
- [ ] Transaction tables are readable with proper column alignment
- [ ] Amounts formatted in EUR (€ X.XXX,XX format)

### Excel Export
- [ ] Aandachtspunten sheet is created when warnings exist
- [ ] Sheet tab name is "Aandachtspunten"
- [ ] Warning summary at top of sheet
- [ ] Transaction details table with headers
- [ ] Currency formatting matches P&L sheet

## Unit Test Coverage

```python
# tests/unit/test_report_warnings.py

def test_report_has_no_warnings_when_clean():
    """Report with all categorized, balanced transactions has no warnings."""

def test_report_detects_uncategorized_transactions():
    """Report tracks uncategorized transactions correctly."""

def test_report_calculates_verkeerde_rekening_balance():
    """Net balance of verkeerde-rekening is calculated correctly."""

def test_report_has_data_quality_warnings_property():
    """has_data_quality_warnings returns True when issues exist."""

def test_verkeerde_rekening_balanced_shows_no_warning():
    """Balanced verkeerde-rekening (net zero) shows no warning."""

def test_pdf_generator_includes_warning_banner():
    """PDF includes warning banner when issues exist."""

def test_excel_export_creates_aandachtspunten_sheet():
    """Excel export includes Aandachtspunten sheet when warnings exist."""
```

## CLI Verification

```bash
# Full workflow test
source .venv/bin/activate

# Import and categorize
plv --company goedele import 2025
plv --company goedele categorize -y 2025

# Generate reports
plv --company goedele report -y 2025 --pdf /tmp/test.pdf -o /tmp/test.xlsx

# Open and verify
open /tmp/test.pdf
open /tmp/test.xlsx
```

## Troubleshooting

| Issue | Possible Cause | Solution |
|-------|----------------|----------|
| No warnings in PDF | All data is clean | Verify uncategorized count in CLI output |
| Warnings in PDF but not Excel | Excel export not updated | Check export_to_excel method |
| Wrong balance shown | Category filter issue | Verify verkeerde-rekening filter in report generator |
| Styling not applied | Style names mismatch | Check PDF generator style definitions |
