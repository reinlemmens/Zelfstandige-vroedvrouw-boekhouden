# Data Model: PLV Web Interface

**Feature**: 009-streamlit-web-app
**Date**: 2026-01-04

## Overview

The web interface reuses existing data models from the PLV codebase. No new persistent entities are introduced. This document describes the entities as used in the web context with session state storage.

## Entities

### Transaction (Existing)

**Location**: `src/models/transaction.py`

**Purpose**: Represents a single financial transaction from bank or credit card statement.

| Field | Type | Description |
|-------|------|-------------|
| id | str | Unique identifier (e.g., "MC-123-20250115-a1b2c3d4") |
| source_file | str | Original filename for traceability |
| source_type | str | "belfius_csv" or "mastercard_pdf" |
| statement_number | str | Bank statement reference |
| transaction_number | str | Sequence within statement |
| booking_date | date | When transaction was recorded |
| value_date | date | When transaction took effect |
| amount | Decimal | Amount in EUR (negative = expense) |
| currency | str | Always "EUR" |
| counterparty_name | Optional[str] | Name of other party |
| counterparty_account | Optional[str] | IBAN if available |
| description | Optional[str] | Transaction details |
| category | Optional[str] | Assigned category ID |
| is_therapeutic | Optional[bool] | For revenue categorization |

**Web Context**: Stored in `st.session_state.transactions` as a list. Cleared when session ends.

### Category (Existing)

**Location**: `src/models/category.py`

**Purpose**: Classification for transactions in P&L report.

| Field | Type | Description |
|-------|------|-------------|
| id | str | Unique identifier (e.g., "sociale-bijdragen") |
| name | str | Display name (e.g., "Sociale Bijdragen") |
| parent_id | Optional[str] | Parent category for hierarchy |
| type | str | "income" or "expense" |
| tax_deductible_pct | Decimal | Percentage deductible (100, 69, 50) |
| exclude_from_report | bool | True for internal transfers |

**Web Context**: Loaded from `data/{company}/config/categories.yaml` based on company selection.

### Rule (Existing)

**Location**: `src/models/rule.py`

**Purpose**: Pattern for automatic transaction categorization.

| Field | Type | Description |
|-------|------|-------------|
| id | str | Unique identifier |
| pattern | str | Text pattern to match |
| pattern_type | str | "exact", "prefix", "contains", "regex" |
| match_field | str | "counterparty_name" or "description" |
| target_category | str | Category ID to assign |
| priority | int | Higher = matched first |
| is_therapeutic | Optional[bool] | For revenue transactions |

**Web Context**: Loaded from `data/{company}/config/rules.yaml` based on company selection.

### Report (Existing)

**Location**: `src/models/report.py`

**Purpose**: Generated P&L summary from categorized transactions.

| Field | Type | Description |
|-------|------|-------------|
| fiscal_year | int | Year of report |
| total_income | Decimal | Sum of income transactions |
| total_expenses | Decimal | Sum of expense transactions |
| net_result | Decimal | Income minus expenses |
| income_items | List[LineItem] | Breakdown by income category |
| expense_items | List[LineItem] | Breakdown by expense category |

**Web Context**: Generated on-demand when user views P&L. Not persisted.

### ImportSession (Existing)

**Location**: `src/models/import_session.py`

**Purpose**: Statistics from a file import operation.

| Field | Type | Description |
|-------|------|-------------|
| source_files | List[str] | Files processed |
| transactions_imported | int | Count of new transactions |
| transactions_skipped | int | Count of duplicates skipped |
| errors | List[ImportError] | Any parsing failures |

**Web Context**: Displayed to user after import; not stored.

## Session State Schema

The web application uses Streamlit session state to maintain data across reruns:

```python
st.session_state = {
    # User selections
    'company': str,           # "goedele" or "meraki"
    'fiscal_year': int,       # e.g., 2025

    # Imported data
    'transactions': List[Transaction],  # All imported transactions
    'existing_ids': Set[str],            # For duplicate detection

    # Processing state
    'import_stats': ImportSession,       # Last import statistics
    'categorization_done': bool,         # Has categorization run?

    # Generated outputs (cached)
    'report': Optional[Report],          # P&L summary
    'excel_bytes': Optional[bytes],      # Generated Excel report
    'pdf_bytes': Optional[bytes],        # Generated PDF Jaarverslag
}
```

## Data Flow

```
User Upload → UploadedFile objects
    ↓
Import (csv_importer/pdf_importer) → List[Transaction]
    ↓
Store in session_state.transactions
    ↓
Categorize (categorizer) → Updates transaction.category
    ↓
Generate Report → Report object
    ↓
Export → Excel/PDF/CSV bytes for download
```

## Validation Rules

### Transaction Validation
- `booking_date` must be within selected fiscal year
- `amount` must be non-zero
- `id` must be unique within session (duplicates skipped)

### Categorization Validation
- Transactions with `exclude_from_report=True` category not included in P&L
- Partial deductibility applied per category tax_deductible_pct

### Report Validation
- All transactions must have category assigned (or marked uncategorized)
- Totals must match sum of line items
