# Implementation Plan: Session State Export/Import

**Branch**: `010-session-state-export` | **Date**: 2026-01-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-session-state-export/spec.md`

## Summary

Add session state persistence to the stateless Streamlit app by enabling users to export their current work session to a ZIP file and import it later to continue. The ZIP archive contains a versioned `state.json` with all session data, optional configuration files (`rules.yaml`, `categories.yaml`), and optionally the original source files. This allows users to pause bookkeeping work and resume in future sessions without losing progress.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Streamlit 1.x, zipfile (stdlib), json (stdlib), yaml
**Storage**: Browser downloads (export), file upload (import), session state (runtime)
**Testing**: pytest (`tests/unit/`, `tests/integration/`)
**Target Platform**: Streamlit Community Cloud, local browser
**Project Type**: Single project (web application embedded in existing structure)
**Performance Goals**: Export/import <5 seconds for 500 transactions
**Constraints**: ZIP files <1MB for typical sessions, no server-side persistence
**Scale/Scope**: Single user session, ~500 transactions max typical use

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Data Integrity | All data traceable to source documents | [x] Transactions preserve source_type and IDs; optional source file inclusion |
| II. Belgian Tax Compliance | Categories align with Resultatenrekening | [x] No category changes; preserves existing structure |
| III. Transparency | Categorization decisions explainable | [x] Exports category assignments; preservable audit trail |
| IV. User Control | No assumptions without user confirmation | [x] User controls export/import; confirmation before overwriting |
| V. Simplicity | CLI-based, minimal dependencies | [x] Uses stdlib (zipfile, json); no new external dependencies |
| VI. Test Coverage | Automated tests for all features | [x] Unit tests for serialization, import validation, migration |

## Project Structure

### Documentation (this feature)

```text
specs/010-session-state-export/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output (session state structure analysis)
├── data-model.md        # Phase 1 output (StateFile schema)
├── quickstart.md        # Phase 1 output (user guide)
├── checklists/
│   └── requirements.md  # Requirements tracking
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── models/
│   └── session_state.py  # NEW: SessionState, StateFile models
├── services/
│   └── session_export.py # NEW: export_session(), import_session()
├── cli/
│   └── main.py           # Existing (no changes needed)
└── lib/

streamlit_app.py          # MODIFY: Add export/import UI in sidebar

tests/
├── integration/
└── unit/
    └── test_session_export.py  # NEW: Export/import tests
```

**Structure Decision**: Single project structure. New models and services follow existing patterns (`src/models/`, `src/services/`). UI changes in `streamlit_app.py`.

## Implementation Phases

### Phase 0: Research
- Document current session state structure in `streamlit_app.py`
- Analyze Transaction model serialization (to_dict/from_dict)
- Review CategoryRule and Category serialization patterns
- Identify any state not currently tracked (e.g., custom config flags)

### Phase 1: Design
- Define `StateFile` JSON schema with version field
- Design migration strategy for future schema changes
- Create data-model.md with schema documentation
- Create quickstart.md with user instructions

### Phase 2: Implementation (via /speckit.tasks)
- Create session state models
- Implement export functionality
- Implement import functionality with validation
- Add UI components (sidebar buttons, file uploader)
- Add confirmation dialog for overwriting existing data
- Add "Bedrijfsnaam" input field
- Implement source file inclusion checkbox
- Write unit and integration tests

## Key Design Decisions

### StateFile Schema (v1.0)

```json
{
  "version": "1.0",
  "company_name": "goedele",
  "fiscal_year": 2025,
  "exported_at": "2026-01-05T10:30:00Z",
  "transactions": [...],
  "existing_ids": [...],
  "categorization_done": true,
  "import_stats": {...},
  "custom_rules_loaded": false,
  "custom_categories_loaded": false
}
```

### ZIP Archive Structure

```
plv-goedele-2025.zip
├── state.json           # Required: session state
├── rules.yaml           # Optional: if custom rules uploaded
├── categories.yaml      # Optional: if custom categories uploaded
└── source_files/        # Optional: if checkbox checked
    ├── bank_jan.csv
    └── mastercard_jan.pdf
```

### Migration Strategy

When importing older state files:
1. Check `version` field in state.json
2. If older than current (1.0), show info message "Sessiebestand wordt geüpgraded van v{old} naar v{new}"
3. Apply migration transformations (field additions, renames)
4. Continue with import

### State Tracking Additions

Current session state needs additional fields:
- `custom_rules_loaded`: bool - True if user uploaded rules.yaml
- `custom_categories_loaded`: bool - True if user uploaded categories.yaml
- `uploaded_files_content`: Dict[str, bytes] - Store original file content for export
- `company_name`: str - User-entered company name

## Complexity Tracking

No constitution violations. Implementation uses:
- Standard library modules (zipfile, json)
- Existing model patterns (to_dict/from_dict)
- Existing Streamlit UI patterns

## Dependencies

- Python `zipfile` module (standard library)
- Python `json` module (standard library)
- Streamlit `st.download_button` for exports
- Streamlit `st.file_uploader` for imports
- Existing Transaction model serialization
- Existing CategoryRule serialization
- Existing Category serialization
