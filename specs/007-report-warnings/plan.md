# Implementation Plan: Report Data Quality Warnings

**Branch**: `007-report-warnings` | **Date**: 2026-01-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-report-warnings/spec.md`

## Summary

Add explicit data quality warnings to both PDF jaarverslag and Excel export reports. Warnings will appear in two places: (1) a brief banner on page 1/P&L sheet showing counts and totals, and (2) a detailed "Aandachtspunten" section/sheet with full transaction listings. Two warning types: uncategorized transactions and non-reimbursed private expenses (verkeerde-rekening with non-zero balance).

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: reportlab (PDF), openpyxl (Excel), pandas (data processing)
**Storage**: JSON file storage (`data/{company}/output/transactions.json`)
**Testing**: pytest (existing test infrastructure)
**Target Platform**: macOS/Linux CLI
**Project Type**: Single CLI application
**Performance Goals**: N/A (annual batch process)
**Constraints**: No external services, local processing only
**Scale/Scope**: ~500 transactions per year, single user

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Data Integrity | PASS | Warnings are derived from source data, no manual entry |
| II. Belgian Tax Compliance | PASS | Warnings help ensure accurate tax filings |
| III. Transparency & Auditability | PASS | Explicitly surfaces uncategorized/ambiguous transactions |
| IV. User Control | PASS | Warnings are informational, user decides next steps |
| V. Simplicity | PASS | Extends existing PDF/Excel generators, no new dependencies |

**All gates pass. No violations to justify.**

## Project Structure

### Documentation (this feature)

```text
specs/007-report-warnings/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── models/
│   └── report.py              # Extend: add warning data structures
├── services/
│   ├── pdf_report_generator.py # Modify: add warning banner + Aandachtspunten section
│   ├── report_generator.py     # Modify: add verkeerde-rekening balance calculation
│   └── exporter.py             # Extend: add Aandachtspunten sheet to Excel export
├── cli/
│   └── main.py                 # No changes needed (uses existing report command)
└── lib/
    └── report_context.py       # Optional: extend for LLM warning context

tests/
├── unit/
│   └── test_report_warnings.py # New: unit tests for warning logic
└── integration/
    └── test_report_output.py   # Extend: verify warnings in output files
```

**Structure Decision**: Single project structure (existing). Feature extends existing services rather than adding new modules.

## Existing Infrastructure Analysis

### PDF Report Generator (`src/services/pdf_report_generator.py`)
- Uses reportlab for PDF generation
- Has structured sections: summary (page 1), methodology, income, expense, conclusion
- Already counts uncategorized transactions in data quality table (line 338)
- **Integration point**: Add warning banner after summary table, add Aandachtspunten section before conclusion

### Excel Export (`src/services/report_generator.py`)
- Uses openpyxl for Excel generation
- Already shows uncategorized warning on P&L sheet (line 279-282)
- Creates single P&L sheet with transaction details
- **Integration point**: Add Aandachtspunten sheet, enhance existing warning

### Report Model (`src/models/report.py`)
- Has `uncategorized_items` list and `total_uncategorized` property
- **Integration point**: Add verkeerde_rekening_balance property

### Category Handling
- verkeerde-rekening is excluded from P&L (report_generator.py line 41)
- Transactions in this category should net to zero when properly balanced
- **Integration point**: Calculate and expose net balance

## Implementation Approach

### Phase 1: Warning Data Model
1. Add `verkeerde_rekening_transactions` list to Report model
2. Add `verkeerde_rekening_balance` property (net sum)
3. Add helper method to identify unbalanced private expenses

### Phase 2: PDF Warning Integration
1. Add warning banner method `_create_warning_banner()` - called after summary
2. Add Aandachtspunten section method `_create_aandachtspunten_section()` - before conclusion
3. Use distinct styling (orange/yellow background for visibility)

### Phase 3: Excel Warning Integration
1. Extend `export_to_excel()` to create Aandachtspunten sheet
2. Include warning summary at top of sheet
3. List full transaction details for both uncategorized and verkeerde-rekening

### Phase 4: Testing
1. Unit tests for warning calculation logic
2. Integration tests verifying output contains expected warnings
3. Edge case tests (no warnings, both warnings, over-reimbursed)

## Complexity Tracking

> No violations to justify. Feature uses existing patterns and extends existing infrastructure.
