# Requirements Checklist: Session State Export/Import

**Feature**: 010-session-state-export
**Generated**: 2026-01-05
**Updated**: 2026-01-05

## Functional Requirements

### Export Functionality
- [x] **FR-001**: "Exporteer sessie" button in sidebar (visible when transactions exist)
- [x] **FR-002**: ZIP filename format `plv-{company_name}-{fiscal_year}.zip`
- [x] **FR-003**: Company name sanitization (lowercase, hyphens, alphanumeric)
- [x] **FR-004**: state.json contains version, company_name, fiscal_year, transactions, existing_ids, categorization_done, import_stats, exported_at
- [x] **FR-005**: Include rules.yaml in ZIP if custom rules loaded
- [x] **FR-006**: Include categories.yaml in ZIP if custom categories loaded

### Import Functionality
- [x] **FR-007**: "Importeer sessie" file uploader in sidebar (.zip files)
- [x] **FR-008**: Validate ZIP contains valid state.json
- [x] **FR-009**: Restore all session state from imported file
- [x] **FR-010**: Confirmation dialog when replacing existing session
- [x] **FR-011**: Success message with transaction count after import
- [x] **FR-012**: Clear error messages for invalid/corrupted files

### Company Name
- [x] **FR-013**: Optional "Bedrijfsnaam" text input in sidebar
- [x] **FR-014**: Default company name "sessie" if none entered
- [x] **FR-015**: Update fiscal year to match imported session

## Non-Functional Requirements

- [x] **NFR-001**: Export completes within 5 seconds (<500 transactions) - *Tested: 0.007s for 500 tx*
- [x] **NFR-002**: ZIP file under 1MB for typical sessions - *Tested: 16KB for 500 tx*
- [x] **NFR-003**: Cross-browser/computer compatibility (standard ZIP/JSON formats)
- [x] **NFR-004**: Schema version in state.json for migrations

## User Stories

### US-1: Export Session State
- [x] Export button downloads ZIP file
- [x] Custom rules/categories included in ZIP
- [x] state.json contains all session data

### US-2: Import Session State
- [x] Upload ZIP restores session
- [x] Confirmation before replacing data
- [x] Error handling for invalid files

### US-3: Company Name
- [x] Company name input in sidebar
- [x] Filename reflects company name
- [x] Company name restored on import

## Edge Cases

- [x] Missing state.json shows error
- [x] Invalid JSON shows error
- [x] Non-ZIP file shows error
- [x] Empty company name uses default
- [x] Large sessions (500+ tx) work within limits - *Tested: 500 tx in 0.007s, 16KB ZIP*
