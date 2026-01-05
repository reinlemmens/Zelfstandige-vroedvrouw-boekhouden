# Tasks: Session State Export/Import

**Input**: Design documents from `/specs/010-session-state-export/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Per Constitution Principle VI (Test Coverage), all features MUST include automated tests. Test tasks are MANDATORY for every user story to prevent silent regressions.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Streamlit app: `streamlit_app.py` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Fix existing bugs and prepare session state tracking

- [ ] T001 Fix Category.to_dict() to include deductibility_pct in src/models/category.py
- [ ] T002 [P] Add unit test for Category serialization round-trip in tests/unit/test_category_serialization.py
- [ ] T003 Add new session state variables (company_name, custom_rules_loaded, custom_categories_loaded, uploaded_files_content) to init_session_state() in streamlit_app.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core export/import service that MUST be complete before ANY user story UI can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create SessionState dataclass in src/models/session_state.py with version, company_name, fiscal_year, exported_at, transactions, existing_ids, categorization_done, import_stats, custom_rules_loaded, custom_categories_loaded fields
- [ ] T005 [P] Create StateFile validation functions in src/models/session_state.py (validate_state_dict, validate_version)
- [ ] T006 Create session_to_dict() function in src/services/session_export.py to serialize session state
- [ ] T007 Create dict_to_session() function in src/services/session_export.py to deserialize session state
- [ ] T008 [P] Create sanitize_filename() helper in src/services/session_export.py for company name sanitization
- [ ] T009 Implement version migration framework in src/services/session_export.py (apply_migrations function)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Export Session State (Priority: P1) 🎯 MVP

**Goal**: User can export current session to a downloadable ZIP file

**Independent Test**: Upload files, categorize some transactions, click export, verify ZIP contains valid state.json

### Tests for User Story 1 (REQUIRED per Constitution VI) ✅

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for session_to_dict() serialization in tests/unit/test_session_export.py
- [ ] T011 [P] [US1] Unit test for create_export_zip() function in tests/unit/test_session_export.py
- [ ] T012 [P] [US1] Unit test for sanitize_filename() in tests/unit/test_session_export.py

### Implementation for User Story 1

- [ ] T013 [US1] Implement create_export_zip() in src/services/session_export.py that creates ZIP with state.json
- [ ] T014 [US1] Add custom rules.yaml inclusion to create_export_zip() when custom_rules_loaded is True
- [ ] T015 [US1] Add custom categories.yaml inclusion to create_export_zip() when custom_categories_loaded is True
- [ ] T016 [US1] Add source_files/ directory inclusion to create_export_zip() with optional flag
- [ ] T017 [US1] Update config upload handlers in streamlit_app.py to track custom_rules_content and custom_categories_content
- [ ] T018 [US1] Update process_uploaded_files() in streamlit_app.py to store file content in uploaded_files_content
- [ ] T019 [US1] Add "Exporteer sessie" section to sidebar in streamlit_app.py (visible when transactions exist)
- [ ] T020 [US1] Add "Bronbestanden toevoegen" checkbox to export section in streamlit_app.py
- [ ] T021 [US1] Implement st.download_button for ZIP export in streamlit_app.py

**Checkpoint**: At this point, User Story 1 should be fully functional - users can export their session

---

## Phase 4: User Story 2 - Import Session State (Priority: P1)

**Goal**: User can import a previously exported session to continue work

**Independent Test**: Export session, close browser, reopen, import ZIP, verify transactions restored

### Tests for User Story 2 (REQUIRED per Constitution VI) ✅

- [ ] T022 [P] [US2] Unit test for dict_to_session() deserialization in tests/unit/test_session_export.py
- [ ] T023 [P] [US2] Unit test for validate_import_zip() function in tests/unit/test_session_export.py
- [ ] T024 [P] [US2] Unit test for version migration in tests/unit/test_session_export.py

### Implementation for User Story 2

- [ ] T025 [US2] Implement validate_import_zip() in src/services/session_export.py that checks ZIP structure and state.json validity
- [ ] T026 [US2] Implement import_session_zip() in src/services/session_export.py that restores session state
- [ ] T027 [US2] Add rules.yaml restoration to import_session_zip() when present in ZIP
- [ ] T028 [US2] Add categories.yaml restoration to import_session_zip() when present in ZIP
- [ ] T029 [US2] Add "Importeer sessie" file uploader to sidebar in streamlit_app.py
- [ ] T030 [US2] Implement confirmation dialog when importing would replace existing data in streamlit_app.py
- [ ] T031 [US2] Display success message with transaction count after import in streamlit_app.py
- [ ] T032 [US2] Display clear error messages for invalid/corrupted import files in streamlit_app.py
- [ ] T033 [US2] Display version migration info message when importing older files in streamlit_app.py
- [ ] T034 [US2] Update fiscal year selector to match imported session data in streamlit_app.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - full export/import cycle functional

---

## Phase 5: User Story 3 - Company Name for Export (Priority: P2)

**Goal**: User can enter a company name that appears in export filename and is preserved across sessions

**Independent Test**: Enter company name, export, verify filename contains sanitized name, import, verify name restored

### Tests for User Story 3 (REQUIRED per Constitution VI) ✅

- [ ] T035 [P] [US3] Unit test for company name sanitization edge cases in tests/unit/test_session_export.py
- [ ] T036 [P] [US3] Unit test for company name in export filename in tests/unit/test_session_export.py

### Implementation for User Story 3

- [ ] T037 [US3] Add "Bedrijfsnaam" text input to sidebar in streamlit_app.py
- [ ] T038 [US3] Update export filename generation to use sanitized company name in streamlit_app.py
- [ ] T039 [US3] Use "sessie" as default company name when field is empty in streamlit_app.py
- [ ] T040 [US3] Restore company name from imported session in streamlit_app.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Run all tests and verify 100% pass rate
- [ ] T042 [P] Verify export/import round-trip preserves all transaction data (manual test)
- [ ] T043 [P] Test with large session (500+ transactions) to verify performance within 5 seconds
- [ ] T044 [P] Test ZIP file size is under 1MB for typical sessions
- [ ] T045 Update quickstart.md with actual UI screenshots if needed in specs/010-session-state-export/quickstart.md
- [ ] T046 Update requirements checklist with completed items in specs/010-session-state-export/checklists/requirements.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 (Export) and US2 (Import) both P1 - can proceed in parallel after Foundational
  - US3 (Company Name) is P2 - can run in parallel or after US1/US2
- **Polish (Final Phase)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (Export, P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (Import, P1)**: Can start after Foundational (Phase 2) - Logically pairs with US1 but independently testable
- **User Story 3 (Company Name, P2)**: Can start after Foundational (Phase 2) - Enhances US1/US2 but independently testable

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Service functions before UI components
- Core implementation before enhancements
- Story complete before moving to next priority

### Parallel Opportunities

- T002, T003 can run in parallel (different files)
- T004, T005 can run in parallel (model vs validation)
- T006, T007, T008, T009 can run in parallel (independent functions)
- All tests within a user story marked [P] can run in parallel
- US1, US2, US3 can potentially run in parallel after Foundational phase

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for session_to_dict() serialization in tests/unit/test_session_export.py"
Task: "Unit test for create_export_zip() function in tests/unit/test_session_export.py"
Task: "Unit test for sanitize_filename() in tests/unit/test_session_export.py"
```

---

## Parallel Example: Foundational Phase

```bash
# Launch all model/service tasks together after T004:
Task: "Create StateFile validation functions in src/models/session_state.py"
Task: "Create sanitize_filename() helper in src/services/session_export.py"

# Launch all serialization tasks together:
Task: "Create session_to_dict() function in src/services/session_export.py"
Task: "Create dict_to_session() function in src/services/session_export.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (fix Category bug, add state tracking)
2. Complete Phase 2: Foundational (create service module)
3. Complete Phase 3: User Story 1 (Export)
4. **STOP and VALIDATE**: Test export independently - verify ZIP is valid
5. Deploy/demo if ready - users can now save their work!

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Export) → Test independently → Deploy (MVP!)
3. Add User Story 2 (Import) → Test independently → Deploy (Full cycle!)
4. Add User Story 3 (Company Name) → Test independently → Deploy (Polish!)
5. Each story adds value without breaking previous stories

### Single Developer Strategy

1. Complete Setup (T001-T003)
2. Complete Foundational (T004-T009)
3. Complete US1 tests (T010-T012) - verify they FAIL
4. Complete US1 implementation (T013-T021) - verify tests PASS
5. Continue with US2, then US3
6. Finish with Polish phase

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Key files modified: streamlit_app.py, src/models/category.py
- Key files created: src/models/session_state.py, src/services/session_export.py, tests/unit/test_session_export.py
