# Tasks: Asset Depreciation Tracking

**Input**: Design documents from `/specs/003-asset-depreciation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md

**Tests**: Not explicitly requested in spec - test tasks not included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Verify project structure and data directory

- [x] T001 Verify data/output directory exists for assets.json storage

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 [P] Create Asset dataclass with all fields in src/models/asset.py (id, name, purchase_date, purchase_amount, depreciation_years, disposal_date, notes, source, created_at)
- [x] T003 [P] Create AssetStatus enum (active, fully_depreciated, disposed) in src/models/asset.py
- [x] T004 [P] Create DepreciationEntry dataclass for computed entries in src/models/asset.py
- [x] T005 Add Asset validation (positive amount, years 1-10, disposal after purchase) in src/models/asset.py
- [x] T006 Extend PersistenceService with load_assets() method in src/services/persistence.py
- [x] T007 Extend PersistenceService with save_assets() method in src/services/persistence.py
- [x] T008 Create `plv assets` command group scaffold in src/cli/main.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Register Depreciable Asset (Priority: P1) 🎯 MVP

**Goal**: Allow user to register a new depreciable asset with name, date, amount, and years

**Independent Test**: Run `plv assets add -n "Test Laptop" -d 2025-01-01 -a 1500.00 -y 5` and verify asset appears with correct annual depreciation (€300/year)

### Implementation for User Story 1

- [x] T009 [US1] Create asset_service.py with generate_asset_id() function in src/services/asset_service.py
- [x] T010 [US1] Implement add_asset() function in src/services/asset_service.py
- [x] T011 [US1] Implement calculate_annual_depreciation() function in src/services/asset_service.py
- [x] T012 [US1] Implement `plv assets add` command with --name, --date, --amount, --years, --notes options in src/cli/main.py
- [x] T013 [US1] Add duplicate detection (same name + purchase_date) warning to add_asset() in src/services/asset_service.py
- [x] T014 [US1] Format add command output showing asset ID, purchase info, and annual depreciation amount

**Checkpoint**: User Story 1 complete - can register new assets via CLI

---

## Phase 4: User Story 2 - View Annual Depreciation Schedule (Priority: P1)

**Goal**: Display depreciation amounts for each year so user can include correct write-offs in tax filing

**Independent Test**: After registering assets, run `plv assets depreciation -y 2025` and verify amounts match expected calculations

### Implementation for User Story 2

- [x] T015 [P] [US2] Create depreciation.py service in src/services/depreciation.py
- [x] T016 [US2] Implement is_depreciating_in_year() function per data-model.md in src/services/depreciation.py
- [x] T017 [US2] Implement get_depreciation_for_year() returning list of DepreciationEntry in src/services/depreciation.py
- [x] T018 [US2] Implement get_asset_status() function in src/services/depreciation.py
- [x] T019 [US2] Implement `plv assets list` command with --status, --year, --format options in src/cli/main.py
- [x] T020 [US2] Implement `plv assets depreciation` command with --year, --format, --detail options in src/cli/main.py
- [x] T021 [US2] Format depreciation output showing category (afschrijvingen), asset names, amounts, and year info

**Checkpoint**: User Story 2 complete - can view asset list and depreciation schedules

---

## Phase 5: User Story 3 - Include Depreciation in P&L Report (Priority: P2)

**Goal**: Provide depreciation totals that can be included in P&L summary under "afschrijvingen" category

**Independent Test**: Call get_total_depreciation_for_year(2025) and verify it returns sum of all active asset depreciation

### Implementation for User Story 3

- [x] T022 [US3] Implement get_total_depreciation_for_year() function in src/services/depreciation.py
- [x] T023 [US3] Add category_id field ("afschrijvingen") to DepreciationEntry for P&L integration in src/models/asset.py
- [x] T024 [US3] Document depreciation service interface for future P&L summary command in src/services/depreciation.py docstrings

**Checkpoint**: User Story 3 complete - depreciation service ready for P&L integration

---

## Phase 6: User Story 4 - Import Existing Assets from Excel (Priority: P2)

**Goal**: One-time import of existing assets from Resultaat sheet to avoid manual re-entry

**Independent Test**: Run `plv assets import "data/2025/Resultatenrekening Vroedvrouw Goedele 2025.xlsx" --dry-run` and verify Telefonie and Orbea assets are detected

### Implementation for User Story 4

- [x] T025 [P] [US4] Create asset_importer.py service in src/services/asset_importer.py
- [x] T026 [US4] Implement find_depreciation_rows() to detect rows with fractional rate (0 < rate < 1) in src/services/asset_importer.py
- [x] T027 [US4] Implement parse_depreciation_years() calculating round(1/rate) from fractional rate in src/services/asset_importer.py
- [x] T028 [US4] Implement parse_purchase_year_from_notes() extracting first year from notes like "2023, 2024, 2025" in src/services/asset_importer.py
- [x] T029 [US4] Implement import_assets_from_excel() returning list of Asset objects in src/services/asset_importer.py
- [x] T030 [US4] Implement `plv assets import` command with --sheet, --dry-run, --merge options in src/cli/main.py
- [x] T031 [US4] Add duplicate detection during import (skip assets with same name already in assets.json) in src/services/asset_importer.py

**Checkpoint**: User Story 4 complete - can import assets from Excel

---

## Phase 7: User Story 5 - Edit or Dispose of Asset (Priority: P3)

**Goal**: Mark assets as disposed so depreciation stops from that point forward

**Independent Test**: Dispose an asset with `plv assets dispose <id> -d 2025-06-01` and verify it no longer appears in 2026 depreciation schedule

### Implementation for User Story 5

- [x] T032 [US5] Implement dispose_asset() function setting disposal_date in src/services/asset_service.py
- [x] T033 [US5] Implement `plv assets dispose` command with --date, --notes options in src/cli/main.py
- [x] T034 [US5] Validate disposal_date is after purchase_date in dispose_asset() in src/services/asset_service.py
- [x] T035 [US5] Format dispose output showing final depreciation year and remaining book value

**Checkpoint**: User Story 5 complete - can dispose of assets

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Validation, edge cases, and final testing

- [ ] T036 Validate assets.json schema version handling in load_assets() in src/services/persistence.py
- [ ] T037 [P] Add --json global output format support to all assets subcommands in src/cli/main.py
- [ ] T038 [P] Add helpful error messages for common issues (file not found, invalid date format) in src/cli/main.py
- [ ] T039 Run quickstart.md workflow end-to-end to validate all commands work together
- [ ] T040 Verify depreciation calculations match Excel within €0.01 tolerance (SC-002)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

| Story | Depends On | Can Parallel With |
|-------|------------|-------------------|
| US1 (P1) | Foundational | - |
| US2 (P1) | Foundational | US1 (same priority, may share asset_service) |
| US3 (P2) | US2 (uses depreciation service) | - |
| US4 (P2) | Foundational | US1, US2 (independent Excel import) |
| US5 (P3) | US1 (uses asset_service) | US3, US4 |

### Within Each User Story

- Models/dataclasses before services
- Services before CLI commands
- Core implementation before formatting/output
- Validate each story works independently before next

### Parallel Opportunities

Within Phase 2 (Foundational):
```
T002, T003, T004 - All model definitions can be parallel
T006, T007 - Persistence methods can be parallel
```

Within Phase 4 (US2):
```
T015 - Create depreciation.py (independent file)
```

Within Phase 6 (US4):
```
T025 - Create asset_importer.py (independent file)
```

---

## Parallel Example: Foundational Phase

```bash
# Launch all model tasks together:
Task: "Create Asset dataclass in src/models/asset.py"
Task: "Create AssetStatus enum in src/models/asset.py"
Task: "Create DepreciationEntry dataclass in src/models/asset.py"

# After models complete, launch persistence tasks together:
Task: "Extend PersistenceService with load_assets() in src/services/persistence.py"
Task: "Extend PersistenceService with save_assets() in src/services/persistence.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Register Asset)
4. **STOP and VALIDATE**: Test `plv assets add` and verify asset saved
5. Can demo basic asset registration

### Recommended Order

1. **Phase 1 + 2**: Setup + Foundational → Foundation ready
2. **Phase 3 (US1)**: Register Asset → Can add new assets (MVP!)
3. **Phase 4 (US2)**: View Depreciation → Can see schedules and tax amounts
4. **Phase 6 (US4)**: Excel Import → Migrate existing data
5. **Phase 5 (US3)**: P&L Integration → Ready for summary command
6. **Phase 7 (US5)**: Dispose Asset → Full lifecycle management
7. **Phase 8**: Polish → Production ready

### Why This Order?

- US1 + US2 together deliver the core tax filing value
- US4 (Import) is useful early to bring in existing data
- US3 (P&L) can wait until depreciation calculations are solid
- US5 (Dispose) is lowest priority - less common scenario

---

## Notes

- All file paths are relative to repository root
- Existing patterns: CLI uses Click groups (see `rules` command), services are in src/services/
- Use Decimal for all EUR amounts per data-model.md
- UUID-based asset IDs with "asset-" prefix per research.md
- Full-year depreciation (no pro-rating) per spec clarifications
