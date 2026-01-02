# Tasks: 2025 Transaction Import & Consolidation

**Input**: Design documents from `/specs/001-2025-transaction-import/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Manual verification against source documents (no automated tests required for this one-time data import)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Execution Context

This is a data processing task executed within Claude Code using MCP tools. Implementation involves:
- Reading and parsing source files from `data/2025/`
- Processing data in memory
- Outputting results via Google Drive MCP to folder `1TJAIGg_RlomBlyPXjnKYH0XJWg2osxdW`

---

## Phase 1: Setup (Data Discovery)

**Purpose**: Verify data files and understand their structure

- [x] T001 List all files in data/2025/ and categorize by type (CSV, PDF, other)
- [x] T002 [P] Sample first CSV file to verify Belfius format and column structure
- [x] T003 [P] Sample first PDF file to verify Mastercard statement format

**Checkpoint**: Data structure understood, ready for parsing

---

## Phase 2: Foundational (Shared Parsing Logic)

**Purpose**: Establish parsing patterns that all user stories depend on

**⚠️ CRITICAL**: No user story work can begin until CSV and PDF parsing is validated

- [x] T004 Define Transaction data structure with all required fields per data-model.md
- [x] T005 Implement European number format parsing (comma decimal, dot thousands)
- [x] T006 Implement date parsing for DD/MM/YYYY format
- [x] T007 Implement reference extraction from transaction description (REF. : pattern)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Import Bank Statement CSVs (Priority: P1) 🎯 MVP

**Goal**: Import all Belfius bank statement CSV files and extract transactions

**Independent Test**: Verify all transactions from CSV files are captured with correct dates, amounts, and descriptions

### Implementation for User Story 1

- [ ] T008 [US1] Read all CSV files matching pattern `BE*.csv` from data/2025/
- [ ] T009 [US1] Parse CSV headers and map to Transaction fields per data-model.md
- [ ] T010 [US1] Extract transactions from first CSV file (BE05 0636 4778 9475 - Vroedvrouw Goedele)
- [ ] T011 [P] [US1] Extract transactions from second account CSV (BE05 0682 4812 1175)
- [ ] T012 [US1] Add source_file tracking to each transaction
- [ ] T013 [US1] Generate dedup_key for each transaction (account|date|txn_num|ref)
- [ ] T014 [US1] Verify transaction count and sample amounts against source files

**Checkpoint**: All CSV transactions imported with source tracking

---

## Phase 4: User Story 2 - Import Mastercard PDF Statements (Priority: P1)

**Goal**: Extract individual transactions from Mastercard PDF statements

**Independent Test**: Verify individual Mastercard transactions are extracted with correct dates, merchants, and amounts

### Implementation for User Story 2

- [ ] T015 [US2] Read all PDF files from data/2025/ (pattern: 6287522061_*.pdf)
- [ ] T016 [US2] Extract statement metadata from first PDF (period dates, settlement date, total)
- [ ] T017 [US2] Extract transaction table from first PDF (date, merchant, location, amount)
- [ ] T018 [P] [US2] Parse remaining PDF statements (repeat T016-T017 pattern)
- [ ] T019 [US2] Handle credit (+) and debit (-) transaction signs correctly
- [ ] T020 [US2] Set transaction type to 'mastercard_detail' for PDF transactions
- [ ] T021 [US2] Verify PDF transaction totals match statement totals

**Checkpoint**: All Mastercard transactions imported from PDFs

---

## Phase 5: User Story 3 - Prevent Double Counting (Priority: P1)

**Goal**: Link Mastercard settlements in bank CSVs to their detailed PDF transactions

**Independent Test**: Verify settlement entries are flagged and linked to PDF transactions

### Implementation for User Story 3

- [ ] T022 [US3] Identify Mastercard settlement entries in CSV transactions (card number pattern or MASTERCARD keyword)
- [ ] T023 [US3] Match each settlement to corresponding PDF statement by date (±1 day) and amount
- [ ] T024 [US3] Flag matched transactions as type 'settlement'
- [ ] T025 [US3] Create settlement links showing which PDF transactions belong to each settlement
- [ ] T026 [US3] Verify settlement amounts match PDF totals (flag discrepancies)

**Checkpoint**: Settlements linked to detail transactions, no double counting possible

---

## Phase 6: User Story 4 - Deduplicate Transactions (Priority: P2)

**Goal**: Remove duplicate transactions that appear in multiple overlapping CSV files

**Independent Test**: Verify transaction count matches expected unique transactions

### Implementation for User Story 4

- [ ] T027 [US4] Combine all CSV transactions into single list
- [ ] T028 [US4] Group transactions by dedup_key
- [ ] T029 [US4] For duplicate groups, keep first occurrence and remove others
- [ ] T030 [US4] Log removed duplicates with source file information
- [ ] T031 [US4] Verify no settlement entries were incorrectly deduplicated against detail entries

**Checkpoint**: All duplicates removed, unique transaction list ready

---

## Phase 7: User Story 5 - Generate Complete Transaction List (Priority: P2)

**Goal**: Create consolidated, filtered, sorted transaction list in Google Sheet

**Independent Test**: Verify final list contains all unique 2025 transactions with correct totals

### Implementation for User Story 5

- [ ] T032 [US5] Merge CSV transactions (deduplicated) with PDF transactions
- [ ] T033 [US5] Filter to only transactions with date between 2025-01-01 and 2025-12-31
- [ ] T034 [US5] Sort transactions by date (ascending), then by account
- [ ] T035 [US5] Prepare data array for Google Sheet (header row + data rows)
- [ ] T036 [US5] Create Google Sheet in folder 1TJAIGg_RlomBlyPXjnKYH0XJWg2osxdW via MCP
- [ ] T037 [US5] Verify row count matches expected unique 2025 transactions

**Checkpoint**: Google Sheet created with complete 2025 transaction list

---

## Phase 8: Polish & Validation

**Purpose**: Final verification and cleanup

- [ ] T038 [P] Verify sum of non-settlement transactions matches expected financial total
- [ ] T039 [P] Verify each transaction has valid source_file reference
- [ ] T040 Verify settlement entries are clearly distinguishable in output (type column)
- [ ] T041 Document any discrepancies or warnings for user review

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1-2 (Phase 3-4)**: Can proceed in parallel after Foundational
- **User Story 3 (Phase 5)**: Depends on both US1 and US2 completion (needs both CSV and PDF data)
- **User Story 4 (Phase 6)**: Depends on US1 completion (CSV data only)
- **User Story 5 (Phase 7)**: Depends on US3 and US4 completion (needs linked, deduplicated data)
- **Polish (Phase 8)**: Depends on US5 completion

### User Story Dependencies

```
US1 (CSV Import) ──────┬──→ US4 (Dedup) ──┬──→ US5 (Output)
                       │                   │
US2 (PDF Import) ──────┴──→ US3 (Link) ────┘
```

### Parallel Opportunities

- T002, T003 can run in parallel (different file types)
- T010, T011 can run in parallel (different accounts)
- T016-T017, T018 can run in parallel (different PDF files)
- T038, T039 can run in parallel (different validations)

---

## Parallel Example: Phase 3 (User Story 1)

```bash
# After T009 completes, these can run in parallel:
Task T010: "Extract transactions from first CSV file (BE05 0636...)"
Task T011: "Extract transactions from second account CSV (BE05 0682...)"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 5 = Basic CSV Import to Sheet)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T007)
3. Complete Phase 3: User Story 1 - CSV Import (T008-T014)
4. Skip directly to Phase 7: User Story 5 - Output (T032-T037)
5. **Result**: Basic transaction list without PDF details or settlement linking

### Full Implementation (Recommended)

1. Complete all phases in order
2. Each phase validates before proceeding
3. Final output includes all sources with proper deduplication and settlement linking

---

## Notes

- This is a one-time data import task executed within Claude Code
- No source code files are created - processing happens in conversation
- Output is via Google Drive MCP createGoogleSheet tool
- Manual verification replaces automated tests
- All amounts are in EUR with European number format
