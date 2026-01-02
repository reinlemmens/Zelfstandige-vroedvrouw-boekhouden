# Tasks: Financial Report Generation

**Input**: Design documents from `/specs/004-financial-report/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Tests**: Not explicitly requested in the spec, but unit tests for the core reporting logic will be included for robustness, following the existing project pattern.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and service structure that must be in place before report generation can be implemented.

- [x] T001 [P] Create `Report` and `ReportLineItem` data classes in `src/models/report.py` as defined in `data-model.md`.
- [x] T002 [P] Create the basic structure for the report generation service in `src/services/report_generator.py`.
- [x] T003 Create test fixtures in `tests/fixtures/` with sample transactions and assets for 2025 to ensure predictable test outcomes.

**Checkpoint**: Foundation ready - report generation logic can now be built.

---

## Phase 2: User Story 1 - Generate Annual P&L Report (Priority: P1) 🎯 MVP

**Goal**: Generate a complete P&L report for a specific fiscal year, with correct calculations for income, expenses, and profit, displayed in the console.

**Independent Test**: Run `plv report --year 2025` and verify that the console output correctly shows total income, a breakdown of expenses by category, total depreciation, and the final calculated profit.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T004 [US1] Write a unit test in `tests/unit/test_report_generator.py` that uses fixture data and asserts that the `generate_pnl_report` service function correctly calculates totals for income, expenses, and profit.
- [x] T005 [P] [US1] Add a test case to `tests/unit/test_report_generator.py` to verify that therapeutic and non-therapeutic income are correctly sub-totaled.
- [x] T006 [P] [US1] Add a test case to `tests/unit/test_report_generator.py` to ensure uncategorized transactions are handled correctly according to the spec clarification.

### Implementation for User Story 1

- [x] T007 [US1] Implement the main `generate_pnl_report` function in `src/services/report_generator.py` that takes a list of transactions and assets and returns a `Report` object.
- [x] T008 [US1] In `src/services/report_generator.py`, add logic to group transactions by category and sum their amounts using `pandas`.
- [x] T009 [US1] In `src/services/report_generator.py`, integrate with the `DepreciationService` to get the total annual depreciation and include it as an expense line item.
- [x] T010 [US1] In `src/services/report_generator.py`, add logic to calculate the final profit/loss and handle uncategorized transactions.
- [x] T011 [US1] Create a console formatter function in `src/services/report_generator.py` to display the `Report` object in a human-readable table format as shown in `quickstart.md`.
- [x] T012 [US1] Add the `report` command to `src/cli/main.py`, which calls the `report_generator` service and prints the formatted output to the console.

**Checkpoint**: At this point, User Story 1 should be fully functional. The `plv report` command should generate a correct P&L summary in the console.

---

## Phase 3: User Story 2 - Export P&L Report to Excel (Priority: P2)

**Goal**: Export the generated P&L report to a clean, well-formatted Excel file suitable for accountants.

**Independent Test**: Run `plv report --year 2025 --output report.xlsx`. Verify that `report.xlsx` is created and that it contains the correct data, with proper currency formatting and column headers.

### Implementation for User Story 2

- [x] T013 [P] [US2] Create an `export_to_excel` function in `src/services/report_generator.py`.
- [x] T014 [US2] In `src/services/report_generator.py`, use `pandas` to create a DataFrame from the `Report` object, structuring it with sections for Income, Expenses, and Result.
- [x] T015 [US2] Use `openpyxl` within the `export_to_excel` function to apply styling to the exported sheet, including currency formatting, bold headers, and column width adjustments.
- [x] T016 [US2] Add logic to handle existing files by creating a new file with a unique suffix, as per the spec clarification.
- [x] T017 [US2] Update the `report` command in `src/cli/main.py` to accept an `--output` option and call the `export_to_excel` function when the path ends with `.xlsx`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work. The `plv report --output` command should generate a formatted Excel file.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements and validation.

- [x] T018 [P] Add verbose logging to the `report_generator` service to provide insight into the report creation process.
- [x] T019 [P] Review and improve error handling for edge cases, such as missing transaction data or inability to write the output file.
- [x] T020 Run the full workflow described in `quickstart.md` to ensure the end-to-end process is smooth.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: Must be completed before any other phase.
- **User Story 1 (Phase 2)**: Depends on Foundational phase.
- **User Story 2 (Phase 3)**: Depends on User Story 1 (it exports the report generated in US1).
- **Polish (Phase 4)**: Depends on all user stories being complete.

### Implementation Strategy

The implementation will follow the phases sequentially, as each phase builds upon the previous one.

1.  **Phase 1 (Foundational)**: Build the core data structures.
2.  **Phase 2 (User Story 1)**: Implement the core P&L logic and console output. This delivers the MVP.
3.  **Phase 3 (User Story 2)**: Add the Excel export functionality.
4.  **Phase 4 (Polish)**: Finalize logging and error handling.
