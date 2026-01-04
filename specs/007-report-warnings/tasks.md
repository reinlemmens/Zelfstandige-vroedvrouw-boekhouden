# Tasks: Report Data Quality Warnings

**Input**: Design documents from `/specs/007-report-warnings/`
**Prerequisites**: plan.md (✓), spec.md (✓), research.md (✓), data-model.md (✓), quickstart.md (✓)

**Tests**: Not explicitly requested in spec - test tasks omitted.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Exact file paths included in descriptions

---

## Phase 1: Setup

**Purpose**: No new setup required - feature extends existing infrastructure

*No tasks in this phase - existing project structure and dependencies are sufficient.*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extend Report model with warning data structures needed by both user stories

**⚠️ CRITICAL**: Both user stories depend on the model extensions in this phase

- [x] T001 Add `verkeerde_rekening_items` field to Report dataclass in src/models/report.py
- [x] T002 Add `verkeerde_rekening_balance` property to Report class in src/models/report.py
- [x] T003 Add `has_data_quality_warnings` property to Report class in src/models/report.py
- [x] T004 Add warning style constants (HIGHLIGHT_WARNING color) to PDFReportGenerator in src/services/pdf_report_generator.py

**Checkpoint**: Report model now supports warning data - user story implementation can begin

---

## Phase 3: User Story 1 - Uncategorized Transaction Warnings (Priority: P1) 🎯 MVP

**Goal**: Display visible warnings in PDF and Excel when uncategorized transactions exist

**Independent Test**: Generate report with at least one uncategorized transaction, verify warning appears in both PDF and Excel with count and total amount

### Implementation for User Story 1

#### PDF Warning Components

- [x] T005 [US1] Create `_create_warning_banner()` method in src/services/pdf_report_generator.py for page 1 banner (uncategorized only for MVP)
- [x] T006 [US1] Create `_create_aandachtspunten_section()` method in src/services/pdf_report_generator.py for detailed section (uncategorized only for MVP)
- [x] T007 [US1] Create `_create_uncategorized_table()` helper method in src/services/pdf_report_generator.py for transaction listing
- [x] T008 [US1] Integrate warning banner into `_create_summary_section()` after summary table in src/services/pdf_report_generator.py
- [x] T009 [US1] Integrate Aandachtspunten section into `generate()` method before conclusion in src/services/pdf_report_generator.py

#### Excel Warning Components

- [x] T010 [US1] Create `_create_aandachtspunten_sheet()` method in src/services/report_generator.py for new Excel sheet
- [x] T011 [US1] Add uncategorized transaction details to Aandachtspunten sheet in src/services/report_generator.py
- [x] T012 [US1] Integrate Aandachtspunten sheet creation into `export_to_excel()` method in src/services/report_generator.py

**Checkpoint**: US1 complete - reports now show uncategorized warnings in both PDF and Excel

---

## Phase 4: User Story 2 - Verkeerde-rekening Warnings (Priority: P2)

**Goal**: Display visible warnings when private expenses don't balance with reimbursements

**Independent Test**: Generate report with verkeerde-rekening transactions that have non-zero net balance, verify warning appears in both PDF and Excel

### Implementation for User Story 2

#### Report Generator Extension

- [x] T013 [US2] Add verkeerde-rekening transaction collection to `generate_pnl_report()` in src/services/report_generator.py
- [x] T014 [US2] Populate `report.verkeerde_rekening_items` with transactions from category 'verkeerde-rekening' in src/services/report_generator.py

#### PDF Warning Extension

- [x] T015 [US2] Extend `_create_warning_banner()` to include verkeerde-rekening balance warning in src/services/pdf_report_generator.py
- [x] T016 [US2] Create `_create_verkeerde_rekening_table()` helper method in src/services/pdf_report_generator.py for transaction listing
- [x] T017 [US2] Extend `_create_aandachtspunten_section()` to include verkeerde-rekening transactions in src/services/pdf_report_generator.py

#### Excel Warning Extension

- [x] T018 [US2] Add verkeerde-rekening balance warning to P&L sheet in src/services/report_generator.py
- [x] T019 [US2] Add verkeerde-rekening transactions to Aandachtspunten sheet in src/services/report_generator.py

**Checkpoint**: US2 complete - reports now show both uncategorized and verkeerde-rekening warnings

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and edge case handling

- [x] T020 Implement warning suppression when no data quality issues exist (both warnings absent) in src/services/pdf_report_generator.py
- [x] T021 Implement warning suppression for Excel when no issues exist (skip Aandachtspunten sheet) in src/services/report_generator.py
- [x] T022 Add actionable context text to warnings ("Review categorization" / "Add missing reimbursement") in src/services/pdf_report_generator.py
- [x] T023 Run quickstart.md validation scenarios to verify all warning combinations work correctly
- [x] T024 Update CLAUDE.md with report warnings feature documentation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Skipped - existing infrastructure sufficient
- **Foundational (Phase 2)**: No dependencies - can start immediately - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 (T001-T004)
- **User Story 2 (Phase 4)**: Depends on Phase 2 (T001-T004); integrates with US1 components
- **Polish (Phase 5)**: Depends on both user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on US2
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Extends US1 components but is independently testable

### Within Each User Story

- PDF components can be implemented before or after Excel components (parallel OK)
- Integration tasks (T008-T009, T012) depend on their component tasks
- Warning banner before Aandachtspunten section (logical order)

### Parallel Opportunities

Within Phase 2 (Foundational):
- T001, T002, T003 can run sequentially (same file)
- T004 can run in parallel with T001-T003 (different file)

Within User Story 1:
- PDF tasks (T005-T009) and Excel tasks (T010-T012) can run in parallel

Within User Story 2:
- Report generator tasks (T013-T014) should complete before PDF/Excel extensions
- PDF tasks (T015-T017) and Excel tasks (T018-T019) can run in parallel after T013-T014

---

## Parallel Example: User Story 1

```bash
# Launch PDF and Excel components in parallel:
Task: "Create _create_warning_banner() method in src/services/pdf_report_generator.py"
Task: "Create _create_aandachtspunten_sheet() method in src/services/report_generator.py"

# Then integrate:
Task: "Integrate warning banner into _create_summary_section()"
Task: "Integrate Aandachtspunten sheet creation into export_to_excel()"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (T001-T004)
2. Complete Phase 3: User Story 1 (T005-T012)
3. **STOP and VALIDATE**: Test with uncategorized transactions
4. Generates reports with uncategorized warnings - MVP complete!

### Full Feature (Both User Stories)

1. Complete MVP (above)
2. Complete Phase 4: User Story 2 (T013-T019)
3. Complete Phase 5: Polish (T020-T024)
4. **VALIDATE**: Test all scenarios from quickstart.md

---

## Notes

- All paths are relative to repository root
- Report model extensions (T001-T003) are in single file - do sequentially
- PDF and Excel changes can be developed in parallel by different developers
- Each checkpoint allows independent testing and validation
- No new dependencies required - uses existing reportlab and openpyxl
