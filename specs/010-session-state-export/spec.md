# Feature Specification: Session State Export/Import

**Feature Branch**: `010-session-state-export`
**Created**: 2026-01-05
**Updated**: 2026-01-05
**Status**: Draft

## Overview

The PLV Streamlit web app is stateless - all session data is lost when the browser tab is closed. This feature adds the ability to export the current session state to a downloadable file and import it later to continue work. This allows users to pause their bookkeeping work and resume it in a future session without losing progress.

**Architecture**: ZIP file containing JSON state and any uploaded configuration files
**File Naming**: `plv-{company_name}-{fiscal_year}.zip` (e.g., `plv-goedele-2025.zip`)

## User Scenarios & Testing

### User Story 1 - Export Session State (Priority: P1)

A user has imported transactions, categorized some manually, and wants to save their progress to continue later.

**Acceptance Scenarios**:

1. **Given** a user has imported transactions and done some categorization work, **When** they click "Exporteer sessie", **Then** a ZIP file downloads to their browser with the filename `plv-{company_name}-{fiscal_year}.zip`.

2. **Given** a user has not entered a company name, **When** they click "Exporteer sessie", **Then** the system prompts them to enter a company name first (or uses "sessie" as default).

3. **Given** a user has uploaded custom rules.yaml or categories.yaml, **When** they export the session, **Then** these files are included in the ZIP alongside the state JSON.

4. **Given** the export completes successfully, **When** the user opens the ZIP file, **Then** it contains:
   - `state.json` with transactions, fiscal year, categorization status
   - `rules.yaml` (if custom rules were uploaded)
   - `categories.yaml` (if custom categories were uploaded)
   - `source_files/` directory with original CSV/PDF files (if "Bronbestanden toevoegen" was checked)

---

### User Story 2 - Import Session State (Priority: P1)

A user wants to continue work from a previously exported session.

**Acceptance Scenarios**:

1. **Given** a user is on the web interface, **When** they upload a valid PLV session ZIP file via "Importeer sessie", **Then** the session state is restored including all transactions, categories, and rules.

2. **Given** a user imports a session file, **When** the import succeeds, **Then** they see a confirmation message with the number of transactions restored and the fiscal year.

3. **Given** a user already has transactions in the current session, **When** they import a session file, **Then** they are asked to confirm replacing the current session data.

4. **Given** a user imports an invalid or corrupted file, **When** the import fails, **Then** they see a clear error message explaining the issue.

5. **Given** a user imports a session file, **When** the fiscal year in the file differs from the current selection, **Then** the fiscal year selector updates to match the imported data.

---

### User Story 3 - Company Name for Export (Priority: P2)

A user wants to identify their exports with a meaningful company name.

**Acceptance Scenarios**:

1. **Given** a user opens the app for the first time, **When** they view the sidebar, **Then** they see an optional "Bedrijfsnaam" (company name) text input.

2. **Given** a user enters a company name, **When** they export the session, **Then** the filename includes their company name (e.g., `plv-mijn-praktijk-2025.zip`).

3. **Given** a user imports a session file, **When** the file contains a company name, **Then** the company name field is populated with the imported value.

---

### Edge Cases

- What happens when the ZIP file is missing state.json? System displays error "Ongeldig sessiebestand: state.json niet gevonden".
- What happens when state.json contains invalid JSON? System displays error "Ongeldig sessiebestand: corrupte data".
- What happens when transactions in the file have incompatible format? System auto-migrates with info message showing version upgrade (e.g., "Upgrading v1.0 → v1.1").
- What happens when the file is not a ZIP? System displays error "Upload een .zip bestand".
- What happens when the user's browser blocks downloads? Standard browser download behavior applies.
- What happens with very large sessions (500+ transactions)? ZIP compression keeps file size manageable (<1MB typically).

## Requirements

### Functional Requirements

- **FR-001**: System MUST provide a "Exporteer sessie" button in the sidebar when transactions exist.
- **FR-002**: System MUST generate a ZIP file named `plv-{company_name}-{fiscal_year}.zip` on export.
- **FR-003**: System MUST sanitize company names for valid filenames (lowercase, hyphens for spaces, alphanumeric only).
- **FR-004**: System MUST include `state.json` in the ZIP containing:
  - `version`: Schema version for future compatibility (start with "1.0")
  - `company_name`: User-entered company name
  - `fiscal_year`: Selected fiscal year
  - `transactions`: List of transaction dictionaries
  - `existing_ids`: Set of imported transaction IDs (for duplicate detection)
  - `categorization_done`: Boolean flag
  - `import_stats`: Statistics from last import
  - `exported_at`: ISO timestamp of export
- **FR-005**: System MUST include uploaded `rules.yaml` in the ZIP if custom rules were loaded.
- **FR-006**: System MUST include uploaded `categories.yaml` in the ZIP if custom categories were loaded.
- **FR-006a**: System MUST provide a checkbox "Bronbestanden toevoegen" (Include source files) on export. When checked, original uploaded CSV/PDF files are included in the ZIP under a `source_files/` directory.
- **FR-007**: System MUST provide an "Importeer sessie" file uploader in the sidebar accepting .zip files.
- **FR-008**: System MUST validate the ZIP contains a valid `state.json` before importing.
- **FR-008a**: System MUST check the `version` field in state.json. If older than current app version, display info message "Sessiebestand wordt geüpgraded van v{old} naar v{new}" and auto-migrate data to current format.
- **FR-009**: System MUST restore all session state from the imported file.
- **FR-010**: System MUST show confirmation dialog when importing would replace existing session data.
- **FR-011**: System MUST display success message with transaction count after import.
- **FR-012**: System MUST display clear error messages for invalid or corrupted import files.
- **FR-013**: System MUST provide an optional "Bedrijfsnaam" text input in the sidebar.
- **FR-014**: System MUST use "sessie" as default company name if none entered.
- **FR-015**: System MUST update fiscal year selector to match imported session data.

### Non-Functional Requirements

- **NFR-001**: Export should complete within 5 seconds for typical sessions (<500 transactions).
- **NFR-002**: ZIP files should be under 1MB for typical sessions.
- **NFR-003**: Export/import should work across browser sessions and different computers.
- **NFR-004**: Schema version in state.json allows future backward-compatible migrations.

### Key Entities

- **SessionState**: The complete state of a user's work session including transactions, configuration, and metadata.
- **StateFile**: The `state.json` file containing serialized session state with version information.
- **SessionArchive**: The ZIP file containing state.json and optional configuration files.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can export and re-import a session with 100% data fidelity.
- **SC-002**: Export generates a valid ZIP file in under 5 seconds.
- **SC-003**: Import restores session state in under 5 seconds.
- **SC-004**: ZIP file size is under 1MB for 500 transactions.
- **SC-005**: Users can transfer session files between different computers/browsers.

## Assumptions

1. Users have write access to their browser's download folder.
2. ZIP file format is universally supported across operating systems.
3. Transaction data is JSON-serializable without loss.
4. Session files are small enough to not cause memory issues during compression.
5. Users understand the concept of saving and restoring work.

## Out of Scope

- Cloud storage integration (Google Drive, Dropbox).
- Automatic session backup/recovery.
- Session file encryption or password protection.
- Merging sessions (import always replaces).
- Session sharing between users.
- Breaking schema changes that cannot be auto-migrated (future versions will maintain backward compatibility).

## Clarifications

### Session 2026-01-05

- Q: Should the original uploaded CSV/PDF source files be preserved in the export? → A: User choice via checkbox ("Include source files")
- Q: When importing an older version state file, what should happen? → A: Warning + migrate (show message like "Upgrading van v1.0 naar v1.1", then auto-migrate)

## Dependencies

- Python `zipfile` module (standard library).
- Python `json` module (standard library).
- Streamlit `st.download_button` for exports.
- Streamlit `st.file_uploader` for imports.
- Existing Transaction model serialization.
