# Tasks: Transaction Categorization

**Input**: Design documents from `/specs/002-transaction-categorization/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/cli.md, research.md, quickstart.md
**Base Status**: ✅ Implemented (2026-01-02) - User Stories 1-6 complete
**Enhancement**: ✅ Complete (2026-01-03) - User Story 7 (Maatschap categorization)

**Tests**: Not explicitly requested in spec - test tasks omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/`, `config/` at repository root
- Based on plan.md project structure

---

## Phase 1: Setup (Project Infrastructure)

**Purpose**: Project initialization, dependencies, and basic structure

- [x] T001 Create project structure: `src/models/`, `src/services/`, `src/cli/`, `src/lib/`, `config/`, `tests/`
- [x] T002 Initialize Python project with pyproject.toml (Python 3.11+, dependencies: pandas, openpyxl, pdfplumber, PyYAML, click)
- [x] T003 [P] Create `src/__init__.py` and all module `__init__.py` files
- [x] T004 [P] Create `config/categories.yaml` with 26 predefined Belgian tax categories from data-model.md
- [x] T005 [P] Create `config/rules.yaml` with empty rules structure (version: "1.0", rules: [])
- [x] T006 [P] Create `config/settings.yaml` with default configuration from contracts/cli.md

**Checkpoint**: Project structure ready for implementation

---

## Phase 2: Foundational (Core Models & Utilities)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 [P] Implement Belgian number parser in `src/lib/belgian_numbers.py` (parse_belgian_amount function from research.md)
- [x] T008 [P] Create Transaction dataclass in `src/models/transaction.py` with all 18 fields from data-model.md
- [x] T009 [P] Create Category dataclass in `src/models/category.py` with id, name, type, tax_deductible, description
- [x] T010 [P] Create CategoryRule dataclass in `src/models/rule.py` with pattern, pattern_type, match_field, target_category, priority, is_therapeutic, enabled, source
- [x] T011 [P] Create ImportSession and ImportError dataclasses in `src/models/import_session.py`
- [x] T012 Implement persistence service in `src/services/persistence.py` (load/save transactions.json, rules.yaml, categories.yaml)
- [x] T013 Implement category loader in `src/services/persistence.py` (load categories from YAML)
- [x] T014 Create CLI entry point skeleton in `src/cli/main.py` with Click framework and global options

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Import Bank Transactions (Priority: P1) MVP

**Goal**: Import all Belfius bank statement CSV files with correct parsing of Belgian number format

**Independent Test**: Load a single bank CSV file and verify all transactions are parsed with correct dates, amounts, counterparty names, and descriptions.

### Implementation for User Story 1

- [x] T015 [US1] Implement Belfius CSV parser in `src/services/csv_importer.py` with semicolon delimiter and 15 columns from spec.md
- [x] T016 [US1] Add Belgian date parsing (DD/MM/YYYY format) in `src/services/csv_importer.py`
- [x] T017 [US1] Implement duplicate detection by (statement_number, transaction_number, source_type) in `src/services/csv_importer.py`
- [x] T018 [US1] Add Mastercard settlement exclusion patterns from research.md in `src/services/csv_importer.py`
- [x] T019 [US1] Implement `plv import` command for CSV files in `src/cli/main.py` with --year, --dry-run, --force options
- [x] T020 [US1] Add import summary output (imported, skipped_duplicates, excluded, errors) in `src/cli/main.py`
- [x] T021 [US1] Persist imported transactions to `data/output/transactions.json` via persistence service

**Checkpoint**: Bank CSV import fully functional - can import all 2025 bank statements

---

## Phase 4: User Story 3 - Auto-Categorize Transactions (Priority: P1)

**Goal**: Automatically categorize transactions based on counterparty patterns using configurable rules

**Independent Test**: Import transactions and apply categorization rules; verify that known counterparties are correctly categorized.

**Depends on**: US1 (transactions must be imported first)

### Implementation for User Story 3

- [x] T022 [US3] Implement rule matching engine in `src/services/categorizer.py` with exact, prefix, contains, regex pattern types
- [x] T023 [US3] Add case-insensitive matching for all pattern types in `src/services/categorizer.py`
- [x] T024 [US3] Implement priority-ordered first-match-wins logic in `src/services/categorizer.py`
- [x] T025 [US3] Add match_field support (counterparty_name, description, counterparty_iban) in `src/services/categorizer.py`
- [x] T026 [US3] Set matched_rule_id on categorized transactions in `src/services/categorizer.py`
- [x] T027 [US3] Implement `plv categorize` command in `src/cli/main.py` with --year, --all, --dry-run options
- [x] T028 [US3] Add categorization summary output (categorized count, uncategorized count, rules_applied breakdown)
- [x] T029 [US3] Persist categorized transactions back to `data/output/transactions.json`

**Checkpoint**: Auto-categorization working - can categorize imported transactions with existing rules

---

## Phase 5: User Story 2 - Import Mastercard Transactions (Priority: P2)

**Goal**: Extract transactions from Belfius Mastercard PDF statements

**Independent Test**: Load a single Mastercard PDF and verify all transactions are extracted with dates, descriptions, and amounts.

### Implementation for User Story 2

- [x] T030 [P] [US2] Implement Mastercard PDF parser in `src/services/pdf_importer.py` using pdfplumber
- [x] T031 [US2] Extract transaction table from PDF pages in `src/services/pdf_importer.py`
- [x] T032 [US2] Parse transaction rows: date, description, amount (including refunds with + suffix) in `src/services/pdf_importer.py`
- [x] T033 [US2] Generate unique transaction IDs for PDF transactions (MC-{statement}-{sequence}) in `src/services/pdf_importer.py`
- [x] T034 [US2] Add PDF file support to `plv import` command in `src/cli/main.py`
- [x] T035 [US2] Implement duplicate detection for Mastercard transactions in `src/services/pdf_importer.py`

**Checkpoint**: Mastercard PDF import working - can import all credit card statements

---

## Phase 6: User Story 4 - Configure Category Rules (Priority: P2)

**Goal**: Allow user to define, modify, and test categorization rules

**Independent Test**: Add a new rule for a vendor, re-run categorization, and verify the vendor's transactions are now categorized correctly.

### Implementation for User Story 4

- [x] T036 [P] [US4] Implement `plv rules list` subcommand in `src/cli/main.py` with --category and --format options
- [x] T037 [P] [US4] Implement `plv rules add` subcommand in `src/cli/main.py` with --pattern, --category, --type, --field, --priority, --therapeutic options
- [x] T038 [US4] Implement `plv rules disable` subcommand in `src/cli/main.py`
- [x] T039 [US4] Implement `plv rules test` subcommand in `src/cli/main.py` to preview pattern matches without saving
- [x] T040 [US4] Add rule validation (valid category, valid regex if pattern_type=regex) in `src/services/persistence.py`
- [x] T041 [US4] Implement rule extraction from Excel in `src/services/rule_extractor.py` using frequency-based pattern mining from research.md
- [x] T042 [US4] Implement `plv bootstrap` command in `src/cli/main.py` with --sheet, --min-occurrences, --output, --dry-run, --merge options
- [x] T043 [US4] Add ambiguous pattern detection (same counterparty, different categories) in `src/services/rule_extractor.py`

**Checkpoint**: Rule management working - can add, list, test, and bootstrap rules

---

## Phase 7: User Story 5 - Review and Correct Categorizations (Priority: P2)

**Goal**: Allow user to review uncategorized transactions and manually assign categories

**Independent Test**: List uncategorized transactions, manually assign a category to one, and verify the assignment persists.

### Implementation for User Story 5

- [x] T044 [P] [US5] Implement `plv list` command in `src/cli/main.py` with --year, --category, --uncategorized, --from, --to, --format, --limit options
- [x] T045 [US5] Add table formatter for transaction list output in `src/cli/main.py`
- [x] T046 [US5] Add CSV and JSON output formats for `plv list` in `src/cli/main.py`
- [x] T047 [US5] Implement `plv assign` command in `src/cli/main.py` with transaction-id, category arguments
- [x] T048 [US5] Set is_manual_override=true when manually assigning category in `src/services/persistence.py`
- [x] T049 [US5] Add --note option to `plv assign` for documenting override reason in `src/cli/main.py`
- [x] T050 [US5] Implement `plv categories` command in `src/cli/main.py` to list available categories

**Checkpoint**: Review workflow working - can list, filter, and manually categorize transactions

---

## Phase 8: User Story 6 - Mark Therapeutic Transactions (Priority: P3)

**Goal**: Allow marking revenue transactions as therapeutic (direct patient care) for tax tracking

**Independent Test**: Mark a transaction as therapeutic and verify the flag is stored and can be filtered.

### Implementation for User Story 6

- [x] T051 [US6] Add --therapeutic flag to `plv assign` command (only valid for omzet category) in `src/cli/main.py`
- [x] T052 [US6] Add therapeutic flag validation in `src/services/persistence.py` (only omzet transactions can be therapeutic)
- [x] T053 [US6] Add --therapeutic filter to `plv list` command in `src/cli/main.py`
- [x] T054 [US6] Add is_therapeutic support to rule matching (rules can auto-set therapeutic flag) in `src/services/categorizer.py`

**Checkpoint**: Therapeutic marking working - can flag and filter therapeutic revenue

---

## Phase 9: User Story 7 - Maatschap Transaction Categorization (Priority: P1) 🆕

**Goal**: Enable description-based categorization for Maatschap (partnership) accounts where the same counterparty can represent different transaction types (profit distribution vs work payment vs cost reimbursement)

**Independent Test**: Import Meraki transactions from `data/meraki/` and verify:
- "Inkomstenverdeling" → winstverdeling (profit distribution)
- "Q3 maatschap" → contractors (work payment)
- "Google workspace" → licenties-software (cost reimbursement)
- "Verkeerde rekening" → verkeerde-rekening (wrong account correction)

**Functional Requirements**: FR-014 to FR-019

### Setup for User Story 7

- [x] T055 [P] [US7] Create account configuration file at config/accounts.yaml with goedele (standard) and meraki (maatschap) accounts per data-model.md
- [x] T056 [P] [US7] Extend config/categories.yaml with new categories: winstverdeling, contractors

### Model Extensions for User Story 7

- [x] T057 [P] [US7] Create Account and Partner dataclasses in src/models/account.py with fields: id, name, iban, account_type (standard|maatschap), partners list
- [x] T058 [US7] Extend Category definitions in src/models/category.py with WINSTVERDELING and CONTRACTORS constants

### Implementation for User Story 7

- [x] T059 [US7] Add account loading function load_accounts() in src/services/persistence.py to read config/accounts.yaml
- [x] T060 [US7] Add description-based rules to config/rules.yaml with match_field: description for patterns: inkomstenverdeling, verkeerde rekening, google workspace, Q1-Q4, invoice numbers (20XXYYZZZ)
- [x] T061 [US7] Add get_account_type_by_iban() helper function in src/services/persistence.py to determine account type from transaction IBAN
- [x] T062 [US7] Modify categorize_transaction() in src/services/categorizer.py to check account_type and apply two-phase matching for maatschap accounts
- [x] T063 [US7] Implement description-first matching logic in src/services/categorizer.py: if account_type=maatschap, try description rules before counterparty rules
- [x] T064 [US7] Add logging for description-based rule matches in src/services/categorizer.py
- [x] T065 [US7] Ensure standard accounts maintain existing behavior (counterparty-only matching) for backwards compatibility

### Validation for User Story 7

- [x] T066 [US7] Run categorization on data/meraki/ transactions and verify SC-006 (100% keyword-based accuracy for Inkomstenverdeling, Verkeerde rekening, Q1-Q4, invoice numbers)
- [x] T067 [US7] Verify existing Goedele transactions in data/goedele/ still categorize correctly (backwards compatibility test)

**Checkpoint**: Maatschap categorization working - run `plv categorize` on Meraki transactions

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Refinements, validation, and documentation

- [ ] T068 [P] Add verbose logging throughout all services using Python logging
- [ ] T069 [P] Implement --verbose and --quiet global options in `src/cli/main.py`
- [ ] T070 [P] Add --json global option for JSON output in `src/cli/main.py`
- [ ] T071 Add input validation and helpful error messages for all CLI commands
- [ ] T072 Add --version option showing package version in `src/cli/main.py`
- [ ] T073 Validate quickstart.md workflow end-to-end with sample data (including Maatschap section)
- [ ] T074 Update CLAUDE.md with Maatschap account handling notes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - US1 and US3 are both P1 but US3 depends on US1 (need transactions to categorize)
  - US2, US4, US5 (all P2) can proceed after US1
  - US6 (P3) can proceed after US5
- **US7 (Phase 9)**: Maatschap enhancement - depends on US3 categorizer being complete
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies

```
                    ┌─────────────────────┐
                    │  Phase 2:           │
                    │  Foundational       │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  US1: Import Bank   │ ◄── MVP
                    │  (P1)               │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
     ┌────────▼────────┐ ┌─────▼─────┐ ┌────────▼────────┐
     │ US2: Import MC  │ │ US3: Auto │ │ US4: Configure  │
     │ (P2)            │ │ Categorize│ │ Rules (P2)      │
     └─────────────────┘ │ (P1)      │ └─────────────────┘
                         └─────┬─────┘
                               │
              ┌────────────────┼────────────────┐
              │                                 │
     ┌────────▼────────┐               ┌────────▼────────┐
     │ US5: Review     │               │ US7: Maatschap  │ ◄── 🆕
     │ (P2)            │               │ (P1)            │
     └────────┬────────┘               └─────────────────┘
              │
     ┌────────▼────────┐
     │ US6: Therapeutic│
     │ (P3)            │
     └─────────────────┘
```

### Within Each User Story

- Models before services
- Services before CLI commands
- Core implementation before integrations
- Complete story before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003, T004, T005, T006)
- All Foundational tasks marked [P] can run in parallel (T007, T008, T009, T010, T011)
- US4 and US5 tasks marked [P] can run in parallel within their phases
- After Foundation, US2 and US4 can start in parallel (both only depend on US1 being complete)

---

## Parallel Example: Foundational Phase

```bash
# Launch all model creations together:
Task: "Implement Belgian number parser in src/lib/belgian_numbers.py"
Task: "Create Transaction dataclass in src/models/transaction.py"
Task: "Create Category dataclass in src/models/category.py"
Task: "Create CategoryRule dataclass in src/models/rule.py"
Task: "Create ImportSession and ImportError dataclasses in src/models/import_session.py"
```

## Parallel Example: After US1 Completion

```bash
# These can proceed in parallel after bank import works:
Task: US2 - "Implement Mastercard PDF parser in src/services/pdf_importer.py"
Task: US4 - "Implement plv rules list subcommand in src/cli/main.py"
Task: US5 - "Implement plv list command in src/cli/main.py"
```

---

## Implementation Strategy

### MVP First (Setup + Foundation + US1 + US3)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: US1 - Import Bank Transactions
4. Complete Phase 4: US3 - Auto-Categorize
5. **STOP and VALIDATE**: Can now import and categorize bank transactions
6. This alone provides 80%+ value for the user

### Incremental Delivery

1. MVP: Setup + Foundation + US1 + US3 → Can categorize bank transactions
2. Add US2 → Can also import Mastercard PDFs
3. Add US4 → Can bootstrap and manage rules
4. Add US5 → Can review and manually correct
5. Add US6 → Can track therapeutic revenue
6. Polish → Full feature complete

### Task Count Summary

| Phase | Tasks | Parallel | Status |
|-------|-------|----------|--------|
| Setup | 6 | 4 | ✅ Complete |
| Foundational | 8 | 5 | ✅ Complete |
| US1 (P1) | 7 | 0 | ✅ Complete |
| US3 (P1) | 8 | 0 | ✅ Complete |
| US2 (P2) | 6 | 1 | ✅ Complete |
| US4 (P2) | 8 | 2 | ✅ Complete |
| US5 (P2) | 7 | 1 | ✅ Complete |
| US6 (P3) | 4 | 0 | ✅ Complete |
| US7 (P1) 🆕 | 13 | 3 | ✅ Complete |
| Polish | 7 | 3 | 🔄 Pending |
| **Total** | **74** | **19** | |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently testable after completion
- Commit after each task or logical group
- Stop at any checkpoint to validate progress
- MVP (US1 + US3) covers core categorization workflow
- US7 is a priority enhancement for Maatschap (partnership) accounts

---

## Maatschap Enhancement Reference (US7)

### Description Rules (from research.md)

| Priority | Pattern | Category | Match Field |
|----------|---------|----------|-------------|
| 100 | `inkomstenverdeling` | winstverdeling | description |
| 90 | `verkeerde\s*rekening` | verkeerde-rekening | description |
| 80 | `google\s*workspace\|office\s*365` | licenties-software | description |
| 70 | `Q[1-4]\s+maatschap\|20\d{7}` | contractors | description |

### Account Configuration (from data-model.md)

```yaml
# config/accounts.yaml
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

### Two-Phase Matching Algorithm

```
For each transaction:
  1. Get account config by IBAN
  2. If account_type == "maatschap":
     a. First: Try description-based rules (in priority order)
     b. If match found → return category
     c. If no match → fall through to counterparty rules
  3. If account_type == "standard":
     a. Use counterparty rules only (existing behavior)
  4. Apply counterparty rules (in priority order)
  5. If still no match → mark as uncategorized
```
