# Implementation Plan: Transaction Categorization

**Branch**: `002-transaction-categorization` | **Date**: 2026-01-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-transaction-categorization/spec.md`
**Status**: ✅ Base Implemented (2026-01-02) | 🔄 Enhancement Pending (2026-01-03)

**Enhancement**: Added Maatschap (partnership) categorization logic (FR-014 to FR-019)

## Summary

Build a Python CLI tool to import financial transactions from Belfius bank CSV files and Mastercard PDF statements, then automatically categorize them based on configurable rules extracted from historical data. The tool persists categorized transactions to JSON/YAML files for downstream P&L generation.

Key capabilities:
- Import bank CSV (semicolon-delimited, Belgian number format)
- Extract transactions from Mastercard PDF statements
- Auto-categorize using pattern-matching rules
- Support manual overrides and therapeutic transaction flagging
- Bootstrap rules from existing 2024/2025 Excel categorizations
- **NEW**: Description-based categorization for Maatschap (partnership) accounts
- **NEW**: Priority-based rule matching (description rules > counterparty rules for Maatschap)
- **NEW**: Account-type configuration (standard vs. maatschap)

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: pandas (CSV/data handling), openpyxl (Excel read for bootstrap), pdfplumber (PDF extraction), PyYAML (config files)
**Storage**: JSON/YAML files (no database)
**Testing**: pytest with fixtures for sample bank/Mastercard data
**Target Platform**: macOS/Linux CLI (single-user local execution)
**Project Type**: Single project
**Performance Goals**: Process full year (~500-1000 transactions) in <10 seconds
**Constraints**: No cloud services, no web server, minimal dependencies per constitution
**Scale/Scope**: ~500-1000 transactions/year, ~50 category rules, single user

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Data Integrity | ✅ PASS | Transaction entity includes source_file, statement_number, transaction_number for full traceability |
| II. Belgian Tax Compliance | ✅ PASS | 26+ categories align with Resultatenrekening structure; EUR only; calendar year fiscal; Maatschap-specific categories (winstverdeling, contractors) added |
| III. Transparency & Auditability | ✅ PASS | Each transaction records which rule matched; description-based rules logged; uncategorized flagged for review (FR-010) |
| IV. User Control | ✅ PASS | Manual overrides (FR-007), configurable rules (FR-009), therapeutic flag (FR-008), account-type config (FR-019) |
| V. Simplicity | ✅ PASS | Python CLI, file-based storage, minimal dependencies (pandas, openpyxl, pdfplumber); description rules use existing pattern-matching infrastructure |

**Gate Result**: ALL PASS - Proceed to Phase 0

### Maatschap Enhancement Constitution Check (2026-01-03)

| Principle | Status | Enhancement Evidence |
|-----------|--------|----------|
| I. Data Integrity | ✅ PASS | Description-based rules preserve original transaction data; categorization decisions are traceable |
| II. Belgian Tax Compliance | ✅ PASS | Winstverdeling distinct from loon/contractors aligns with Belgian tax treatment of Maatschap partnerships |
| III. Transparency & Auditability | ✅ PASS | Rule priority (description > counterparty) is explicit; all matching logged |
| IV. User Control | ✅ PASS | Account-type configuration per company allows user control over which accounts use Maatschap logic |
| V. Simplicity | ✅ PASS | Reuses existing CategoryRule infrastructure with match_field extension; no new dependencies |

## Project Structure

### Documentation (this feature)

```text
specs/002-transaction-categorization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CLI interface specs)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── models/
│   ├── __init__.py
│   ├── transaction.py       # Transaction dataclass
│   ├── category.py          # Category enum/list (extended with winstverdeling, contractors)
│   ├── rule.py              # CategoryRule dataclass (extended with match_field)
│   └── account.py           # NEW: Account config (iban, name, account_type: standard|maatschap)
├── services/
│   ├── __init__.py
│   ├── csv_importer.py      # Belfius CSV parsing
│   ├── pdf_importer.py      # Mastercard PDF extraction
│   ├── categorizer.py       # Rule matching engine (MODIFIED: priority-based matching for Maatschap)
│   ├── rule_extractor.py    # Bootstrap rules from Excel
│   └── persistence.py       # JSON/YAML read/write
├── cli/
│   ├── __init__.py
│   └── main.py              # Click/argparse CLI entry point
└── lib/
    ├── __init__.py
    └── belgian_numbers.py   # Belgian locale number parsing

config/
├── categories.yaml          # Category definitions (26 base + extended: winstverdeling, contractors)
├── rules.yaml               # Categorization rules (counterparty + description-based)
└── accounts.yaml            # NEW: Account configuration with account_type (standard/maatschap)

data/
├── 2024/                    # Historical data (existing)
├── 2025/                    # Current year data (existing)
└── output/
    └── transactions.json    # Persisted categorized transactions

tests/
├── fixtures/
│   ├── sample_bank.csv      # Test bank CSV
│   ├── sample_mastercard.pdf # Test Mastercard PDF
│   └── sample_excel.xlsx    # Test historical categorizations
├── unit/
│   ├── test_csv_importer.py
│   ├── test_pdf_importer.py
│   ├── test_categorizer.py
│   └── test_belgian_numbers.py
└── integration/
    └── test_full_pipeline.py
```

**Structure Decision**: Single project layout chosen per constitution (V. Simplicity). CLI tool with clear separation: models (data structures), services (business logic), cli (user interface), lib (utilities).

## Complexity Tracking

No violations - design aligns with all constitution principles.
