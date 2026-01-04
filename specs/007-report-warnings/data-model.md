# Data Model: Report Data Quality Warnings

**Feature**: 007-report-warnings
**Date**: 2026-01-04

## Overview

This feature extends the existing `Report` model to track verkeerde-rekening (private expense) transactions and their net balance, enabling data quality warnings in both PDF and Excel outputs.

## Existing Model: Report

**Location**: `src/models/report.py`

```python
@dataclass
class Report:
    fiscal_year: int
    income_items: List[ReportLineItem]
    expense_items: List[ReportLineItem]
    depreciation_items: List[ReportLineItem]
    uncategorized_items: List[ReportLineItem]  # Already exists
    disallowed_expenses: List[DisallowedExpenseItem]

    # Existing properties
    total_income: Decimal
    total_expenses: Decimal
    profit_loss: Decimal
    total_uncategorized: Decimal  # Already exists
    total_disallowed: Decimal
```

## Model Extensions

### New Field: verkeerde_rekening_items

**Type**: `List[ReportLineItem]`
**Default**: `[]`
**Purpose**: Store all transactions in the verkeerde-rekening category for the fiscal year

### New Property: verkeerde_rekening_balance

**Type**: `Decimal`
**Calculation**: Sum of all amounts in `verkeerde_rekening_items`
**Purpose**: Net balance of private expenses vs reimbursements
- Negative value: Unreimbursed private expenses (needs attention)
- Positive value: Over-reimbursed (also needs attention)
- Zero: Balanced (no warning needed)

### New Property: has_data_quality_warnings

**Type**: `bool`
**Calculation**: `total_uncategorized != 0 or verkeerde_rekening_balance != 0`
**Purpose**: Quick check for whether any warnings should be displayed

## Updated Model Definition

```python
@dataclass
class Report:
    """Represents a full P&L statement for a fiscal year."""
    fiscal_year: int
    income_items: List[ReportLineItem] = field(default_factory=list)
    expense_items: List[ReportLineItem] = field(default_factory=list)
    depreciation_items: List[ReportLineItem] = field(default_factory=list)
    uncategorized_items: List[ReportLineItem] = field(default_factory=list)
    disallowed_expenses: List[DisallowedExpenseItem] = field(default_factory=list)
    verkeerde_rekening_items: List[ReportLineItem] = field(default_factory=list)  # NEW

    # ... existing properties ...

    @property
    def verkeerde_rekening_balance(self) -> Decimal:
        """Net balance of verkeerde-rekening transactions.

        Zero = balanced (expenses match reimbursements)
        Negative = unreimbursed expenses
        Positive = over-reimbursed
        """
        return sum(item.amount for item in self.verkeerde_rekening_items)

    @property
    def has_data_quality_warnings(self) -> bool:
        """Check if any data quality warnings should be displayed."""
        return self.total_uncategorized != 0 or self.verkeerde_rekening_balance != 0
```

## Entity Relationships

```
Report
├── income_items: List[ReportLineItem]
├── expense_items: List[ReportLineItem]
├── depreciation_items: List[ReportLineItem]
├── uncategorized_items: List[ReportLineItem]
│   └── [existing] Transactions with category=None
├── disallowed_expenses: List[DisallowedExpenseItem]
└── verkeerde_rekening_items: List[ReportLineItem]  [NEW]
    └── Transactions with category='verkeerde-rekening'
```

## Transaction Entity Reference

Existing `Transaction` model (no changes needed):

| Field | Type | Relevant for Warnings |
|-------|------|----------------------|
| id | str | Yes - for detailed listings |
| booking_date | date | Yes - for detailed listings |
| amount | Decimal | Yes - for totals and listings |
| counterparty_name | str | Yes - for detailed listings |
| description | str | Yes - for detailed listings |
| category | Optional[str] | Yes - None = uncategorized, 'verkeerde-rekening' = private expense |

## Data Flow

1. **ReportGenerator.generate_pnl_report()**:
   - Already filters verkeerde-rekening from P&L (excluded category)
   - NEW: Collect verkeerde-rekening transactions into `verkeerde_rekening_items`

2. **PDFReportGenerator.generate()**:
   - NEW: Check `report.has_data_quality_warnings`
   - NEW: If warnings exist, render warning banner after summary
   - NEW: Render Aandachtspunten section with details

3. **ReportGenerator.export_to_excel()**:
   - Existing: Shows uncategorized warning on P&L sheet
   - NEW: Create Aandachtspunten sheet if warnings exist
   - NEW: List uncategorized transactions with details
   - NEW: List verkeerde-rekening transactions with details

## Validation Rules

| Field | Validation | Error Handling |
|-------|------------|----------------|
| verkeerde_rekening_items | List of valid ReportLineItem | Empty list if none found |
| verkeerde_rekening_balance | Decimal (can be negative) | Returns Decimal(0) if empty list |
| has_data_quality_warnings | Boolean, always valid | N/A |

## Migration Notes

- No database migrations needed (JSON file storage)
- Backward compatible: New fields have default values
- Existing reports will have empty `verkeerde_rekening_items` until regenerated
