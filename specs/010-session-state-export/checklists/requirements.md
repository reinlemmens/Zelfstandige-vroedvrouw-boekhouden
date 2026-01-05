# Requirements Checklist: Session State Export/Import

**Feature**: 010-session-state-export
**Generated**: 2026-01-05

## Functional Requirements

### Export Functionality
- [ ] **FR-001**: "Exporteer sessie" button in sidebar (visible when transactions exist)
- [ ] **FR-002**: ZIP filename format `plv-{company_name}-{fiscal_year}.zip`
- [ ] **FR-003**: Company name sanitization (lowercase, hyphens, alphanumeric)
- [ ] **FR-004**: state.json contains version, company_name, fiscal_year, transactions, existing_ids, categorization_done, import_stats, exported_at
- [ ] **FR-005**: Include rules.yaml in ZIP if custom rules loaded
- [ ] **FR-006**: Include categories.yaml in ZIP if custom categories loaded

### Import Functionality
- [ ] **FR-007**: "Importeer sessie" file uploader in sidebar (.zip files)
- [ ] **FR-008**: Validate ZIP contains valid state.json
- [ ] **FR-009**: Restore all session state from imported file
- [ ] **FR-010**: Confirmation dialog when replacing existing session
- [ ] **FR-011**: Success message with transaction count after import
- [ ] **FR-012**: Clear error messages for invalid/corrupted files

### Company Name
- [ ] **FR-013**: Optional "Bedrijfsnaam" text input in sidebar
- [ ] **FR-014**: Default company name "sessie" if none entered
- [ ] **FR-015**: Update fiscal year to match imported session

## Non-Functional Requirements

- [ ] **NFR-001**: Export completes within 5 seconds (<500 transactions)
- [ ] **NFR-002**: ZIP file under 1MB for typical sessions
- [ ] **NFR-003**: Cross-browser/computer compatibility
- [ ] **NFR-004**: Schema version in state.json for migrations

## User Stories

### US-1: Export Session State
- [ ] Export button downloads ZIP file
- [ ] Custom rules/categories included in ZIP
- [ ] state.json contains all session data

### US-2: Import Session State
- [ ] Upload ZIP restores session
- [ ] Confirmation before replacing data
- [ ] Error handling for invalid files

### US-3: Company Name
- [ ] Company name input in sidebar
- [ ] Filename reflects company name
- [ ] Company name restored on import

## Edge Cases

- [ ] Missing state.json shows error
- [ ] Invalid JSON shows error
- [ ] Non-ZIP file shows error
- [ ] Empty company name uses default
- [ ] Large sessions (500+ tx) work within limits
