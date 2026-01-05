# Tasks: PLV Web Interface

**Input**: Design documents from `/specs/009-streamlit-web-app/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: Not explicitly requested in spec. Existing unit tests for services remain unchanged. Manual testing checklist provided in quickstart.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and deployment configuration

- [x] T001 Create `requirements.txt` at repository root with Streamlit dependencies (streamlit>=1.28.0, pandas>=2.0.0, openpyxl>=3.1.0, pdfplumber>=0.10.0, PyYAML>=6.0, reportlab>=4.0.0, plotly>=5.18.0)
- [x] T002 [P] Create `.streamlit/config.toml` with theme configuration (primaryColor, backgroundColor, maxUploadSize=50)
- [x] T003 [P] Create `streamlit_app.py` with basic app structure (page config, title, layout="wide")

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Implement session state initialization in `streamlit_app.py` (transactions list, existing_ids set, company, fiscal_year, categorization_done flag)
- [x] T005 Add config loading functions to read `data/{company}/config/categories.yaml` and `data/{company}/config/rules.yaml`
- [x] T006 [P] Add BytesIO wrapper method to `src/services/csv_importer.py` for in-memory file processing (`import_from_bytes(bytes, filename)`)
- [x] T007 [P] Add BytesIO wrapper method to `src/services/pdf_importer.py` for in-memory file processing (`import_from_bytes(bytes, filename)`)
- [x] T008 Create helper function for Belgian number formatting (comma decimal, period thousands) in `streamlit_app.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 + 2 - File Upload & Company Selection (Priority: P1) MVP

**Goal**: Users can select company/year, upload files, and see imported transactions

**Independent Test**: Upload a CSV bank statement, select company "goedele", verify transactions appear in table

### Implementation for User Stories 1 & 2

- [x] T009 [US1+2] Add sidebar with company selector dropdown (goedele, meraki) in `streamlit_app.py`
- [x] T010 [US1+2] Add sidebar with fiscal year selector (2024, 2025, current year) in `streamlit_app.py`
- [x] T011 [US1] Add file uploader component (`st.file_uploader`) accepting CSV and PDF with multi-file support
- [x] T012 [US1] Implement "Import" button that triggers csv_importer and pdf_importer based on file extension
- [x] T013 [US1] Add import statistics display (st.success/st.info) showing imported count and skipped duplicates
- [x] T014 [US1] Add duplicate detection using transaction IDs stored in `st.session_state.existing_ids`
- [x] T015 [US1] Create transaction table display (`st.dataframe`) with sortable columns (date, amount, counterparty, category)
- [x] T016 [US1] Add error handling for invalid files with user-friendly error messages (`st.error`)
- [x] T017 [US1] Handle edge case: empty files with "No transactions found" message
- [x] T018 [US1] Handle edge case: PDF parsing failures with specific file error and continue processing others

**Checkpoint**: Users can upload files, select company/year, and view imported transactions. MVP is functional.

---

## Phase 4: User Story 3 - Automatic Categorization (Priority: P2)

**Goal**: Users can categorize transactions automatically using existing rules

**Independent Test**: Import uncategorized transactions, click "Categorize", verify category column updates

### Implementation for User Story 3

- [x] T019 [US3] Add "Categorize" button in main area below transaction table
- [x] T020 [US3] Implement categorization logic using existing `Categorizer` service with loaded rules
- [x] T021 [US3] Display categorization statistics (st.metric: categorized count, uncategorized count)
- [x] T022 [US3] Add "Recategorize All" checkbox option for re-running categorization on already-categorized transactions
- [x] T023 [US3] Highlight uncategorized transactions in table (conditional formatting or filter option)
- [x] T024 [US3] Update `st.session_state.categorization_done` flag after categorization completes

**Checkpoint**: Users can categorize transactions. Combined with P1, core workflow is complete.

---

## Phase 5: User Story 4 - P&L Summary and Analytics (Priority: P2)

**Goal**: Users can view financial summary with income, expenses, and Mollie analysis

**Independent Test**: With categorized transactions loaded, verify P&L summary shows correct totals

### Implementation for User Story 4

- [x] T025 [US4] Add P&L summary section with `st.metric` cards (Total Income, Total Expenses, Net Profit)
- [x] T026 [US4] Implement report generation using existing `generate_report` function from `src/services/report_generator.py`
- [x] T027 [US4] Add expense breakdown table by category (category name, amount, percentage)
- [x] T028 [US4] Add Plotly pie chart for expense category visualization
- [x] T029 [US4] Add Mollie analysis section (conditionally shown when Mollie transactions present)
- [x] T030 [US4] Display Mollie metrics: transaction count, total volume, percentage of total revenue
- [x] T031 [US4] Apply Belgian number formatting to all monetary displays

**Checkpoint**: Users can view complete financial summary. Full analysis capability is available.

---

## Phase 6: User Story 5 - Report Downloads (Priority: P3)

**Goal**: Users can download Excel, PDF, and CSV reports

**Independent Test**: With transactions imported and categorized, click each download button and verify file downloads correctly

### Implementation for User Story 5

- [x] T032 [US5] Add "Download Excel Report" button using `st.download_button` with in-memory Excel generation
- [x] T033 [US5] Implement Excel report generation using existing `report_generator` with BytesIO output
- [x] T034 [US5] Add "Download PDF Jaarverslag" button for management report download
- [x] T035 [US5] Implement PDF Jaarverslag generation using existing `pdf_report_generator` with BytesIO output
- [x] T036 [US5] Add "Export Transactions CSV" button for raw data export
- [x] T037 [US5] Implement CSV export using pandas DataFrame.to_csv() with Belgian number formatting
- [x] T038 [US5] Group download buttons in an `st.expander` or dedicated section for clean layout

**Checkpoint**: All download options available. Feature is complete.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T039 [P] Add progress indicators (`st.spinner`) for long-running operations (import, categorize, report generation)
- [x] T040 [P] Improve table styling with column width adjustments and number formatting
- [x] T041 Add session timeout message explaining data clearance and re-upload requirement
- [x] T042 [P] Add debug expander in sidebar showing session state (for development troubleshooting)
- [x] T043 Validate app against quickstart.md manual testing checklist
- [x] T044 [P] Update CLAUDE.md with Streamlit app documentation
- [x] T045 Deploy to Streamlit Community Cloud and verify public URL access

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories 1+2 (Phase 3)**: Depends on Foundational - delivers MVP
- **User Story 3 (Phase 4)**: Depends on Phase 3 (needs transactions to categorize)
- **User Story 4 (Phase 5)**: Depends on Phase 4 (needs categorized transactions for P&L)
- **User Story 5 (Phase 6)**: Depends on Phase 5 (needs report data for downloads)
- **Polish (Phase 7)**: Can start after Phase 3 MVP, parallel to later phases

### Within Each Phase

- Tasks marked [P] can run in parallel
- Sequential tasks should complete in order listed
- Commit after each logical task group

### Parallel Opportunities

```bash
# Phase 1: All setup tasks can run in parallel
T001, T002, T003

# Phase 2: Importer modifications can run in parallel
T006, T007

# Phase 7: All polish tasks can run in parallel
T039, T040, T042, T044
```

---

## Implementation Strategy

### MVP First (Phase 1-3)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Stories 1+2
4. **STOP and VALIDATE**: Test file upload and transaction display
5. Deploy MVP to Streamlit Cloud for early feedback

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1+2 (Phase 3) → Test independently → Deploy MVP
3. Add US3 (Phase 4) → Test categorization → Update deployment
4. Add US4 (Phase 5) → Test P&L display → Update deployment
5. Add US5 (Phase 6) → Test downloads → Update deployment
6. Polish (Phase 7) → Final testing → Production ready

---

## Notes

- Existing services in `src/services/` are reused - only BytesIO wrappers needed
- Session state cleared on browser refresh (documented behavior)
- Belgian number formatting applies to all monetary displays
- Dutch language for all UI labels
- Memory budget: ~200MB peak within 1GB Streamlit Cloud limit
