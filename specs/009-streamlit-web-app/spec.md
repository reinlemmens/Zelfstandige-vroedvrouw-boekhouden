# Feature Specification: PLV Web Interface

**Feature Branch**: `009-streamlit-web-app`
**Created**: 2026-01-04
**Updated**: 2026-01-05
**Status**: Implemented

## Overview

PLV (Profit & Loss for Vroedvrouw) is a financial reporting tool for Belgian self-employed midwives. This feature provides a web-based interface that allows users to:
- Upload bank statements (CSV) and credit card statements (PDF) through a browser
- Process transactions with automatic categorization using embedded Belgian rules
- View and filter transactions with multi-column search
- Edit categories for individual transactions
- View financial summaries and analytics
- Download generated reports

**Architecture**: Fully stateless - no preloaded companies, no server-side persistence
**Deployment**: Streamlit Community Cloud (free tier) with public URL
**Budget**: Free

## User Scenarios & Testing

### User Story 1 - Upload and Import Financial Files (Priority: P1)

A user wants to upload their monthly bank statements and credit card statements to process them for financial reporting.

**Acceptance Scenarios**:

1. **Given** a user is on the web interface, **When** they upload a CSV bank statement file and click "Importeren", **Then** the system displays the number of transactions imported and shows them in a table.

2. **Given** a user has uploaded a file, **When** the import completes, **Then** any duplicate transactions are skipped and the user sees how many were skipped vs. imported.

3. **Given** a user uploads a PDF credit card statement, **When** the import runs, **Then** transactions are extracted from the PDF and displayed alongside bank transactions.

4. **Given** a user uploads multiple files at once, **When** the import runs, **Then** all files are processed and combined into a single transaction list.

---

### User Story 2 - Select Fiscal Year and Configure Categories (Priority: P1)

A user wants to select the fiscal year they're working on and optionally upload custom categorization rules.

**Acceptance Scenarios**:

1. **Given** a user opens the web interface, **When** they see the fiscal year selector, **Then** it defaults to the previous year in Jan-Mar (when typically doing last year's books).

2. **Given** a user wants custom categorization rules, **When** they upload a rules.yaml file in the sidebar, **Then** the rules are loaded and used for auto-categorization.

3. **Given** a user wants custom categories, **When** they upload a categories.yaml file, **Then** the categories replace the default Belgian categories.

---

### User Story 3 - Filter and View Transactions (Priority: P1)

A user wants to search, filter, and view details of their transactions.

**Acceptance Scenarios**:

1. **Given** transactions have been imported, **When** the user types in the search box, **Then** transactions are filtered by tegenpartij or omschrijving text.

2. **Given** transactions are displayed, **When** the user sets date range filters, **Then** only transactions within that range are shown.

3. **Given** transactions are displayed, **When** the user sets amount range filters, **Then** only transactions within that amount range are shown.

4. **Given** transactions are displayed, **When** the user selects a category filter, **Then** only transactions with that category are shown.

5. **Given** transactions are displayed, **When** the user checks "Alleen niet-gecategoriseerd", **Then** only uncategorized transactions are shown.

6. **Given** transactions are displayed, **When** the user checks "Alleen inkomsten" or "Alleen uitgaven", **Then** only positive or negative amounts are shown.

---

### User Story 4 - View Transaction Details and Edit Category (Priority: P1)

A user wants to view full details of a transaction and change its category.

**Acceptance Scenarios**:

1. **Given** transactions are displayed, **When** the user checks the "Selecteer" checkbox for a transaction, **Then** full transaction details appear below the table.

2. **Given** transaction details are displayed, **When** the user sees the detail panel, **Then** they see: Transaction ID, Boekingsdatum, Bedrag, Tegenpartij naam, Tegenpartij rekening, Mededeling, Volledige omschrijving, Bron, and Huidige categorie.

3. **Given** transaction details are displayed, **When** the user selects a new category from the dropdown and clicks "Categorie opslaan", **Then** the transaction's category is updated.

4. **Given** the user selects a category, **When** the category has partial deductibility, **Then** a hint shows the deductibility percentage (e.g., "69% fiscaal aftrekbaar" for restaurant).

---

### User Story 5 - Automatic Transaction Categorization (Priority: P2)

A user wants the system to automatically categorize transactions based on embedded rules or uploaded custom rules.

**Acceptance Scenarios**:

1. **Given** transactions have been imported, **When** the user clicks "Automatisch categoriseren", **Then** the system applies categorization rules and displays how many transactions were categorized.

2. **Given** some transactions cannot be categorized (no matching rule), **When** categorization completes, **Then** these transactions remain uncategorized and can be filtered to view.

3. **Given** a transaction was previously categorized, **When** the user checks "Hercategoriseer alle" and re-runs categorization, **Then** the transaction can be reassigned if rules have changed.

---

### User Story 6 - View P&L Summary and Analytics (Priority: P2)

After importing transactions, a user wants to see a profit and loss summary showing total income, total expenses, net profit, and breakdown by category.

**Acceptance Scenarios**:

1. **Given** transactions have been imported and categorized, **When** the user views the P&L summary, **Then** they see total income, total expenses, and net profit with Belgian number formatting.

2. **Given** the P&L summary is displayed, **When** the user views expense breakdown, **Then** they see expenses grouped by category with amounts and percentages.

3. **Given** Mollie payment transactions exist, **When** the user views analytics, **Then** they see a dedicated Mollie analysis section showing online payment volume and percentage of total revenue.

---

### User Story 7 - Download Reports (Priority: P3)

A user wants to download their financial reports in formats suitable for their accountant or tax filing.

**Acceptance Scenarios**:

1. **Given** transactions are imported and categorized, **When** the user clicks "Download Excel Rapport", **Then** an Excel file is downloaded containing the P&L summary and transaction details.

2. **Given** transactions are imported and categorized, **When** the user clicks "Download PDF Jaarverslag", **Then** a PDF management report is downloaded with income analysis, expense breakdown, and Mollie analysis.

3. **Given** the user wants raw transaction data, **When** they click "Exporteer Transacties (CSV)", **Then** a CSV file is downloaded with all transaction details.

---

### Edge Cases

- What happens when a user uploads an invalid file format? System displays clear error message indicating supported formats (CSV, PDF).
- What happens when a user uploads an empty file? System displays "No transactions found in file" message.
- What happens when the session times out? User sees a message explaining data was cleared and needs to re-upload.
- What happens when a PDF cannot be parsed? System displays which file failed and continues processing other files.
- What happens when duplicate files are uploaded? Duplicate transactions are detected by ID and skipped with notification.
- What happens when fiscal year doesn't match data? Transactions outside the fiscal year are filtered out during import.

## Requirements

### Functional Requirements

- **FR-001**: System MUST allow users to select a fiscal year (2024, 2025, current year) with smart default (previous year in Jan-Mar)
- **FR-002**: System MUST accept file uploads for CSV bank statements (Belfius format, semicolon-delimited)
- **FR-003**: System MUST accept file uploads for PDF credit card statements (Belfius Mastercard format)
- **FR-004**: System MUST support uploading multiple files simultaneously
- **FR-005**: System MUST import transactions from uploaded files and display import statistics (imported count, skipped duplicates)
- **FR-006**: System MUST detect and skip duplicate transactions based on transaction ID
- **FR-007**: System MUST embed default Belgian expense categories (30 categories including partial deductibility rules)
- **FR-008**: System MUST embed default categorization rules for Belgian midwives (48 patterns for RIZIV, mutualiteiten, social contributions, etc.)
- **FR-009**: System MUST allow users to optionally upload custom rules.yaml to override default rules
- **FR-010**: System MUST allow users to optionally upload custom categories.yaml to override default categories
- **FR-011**: System MUST apply automatic categorization rules to imported transactions
- **FR-012**: System MUST display a filterable transaction table with:
  - Text search (tegenpartij, omschrijving)
  - Date range filter (van/tot datum)
  - Amount range filter (min/max bedrag)
  - Category filter dropdown
  - Source filter dropdown (CSV/PDF)
  - Quick filters: uncategorized only, income only, expenses only
- **FR-013**: System MUST allow users to select a transaction to view full details
- **FR-014**: System MUST allow users to edit the category of a selected transaction
- **FR-015**: System MUST calculate and display P&L summary (total income, total expenses, net profit)
- **FR-016**: System MUST display expense breakdown by category with amounts and percentages
- **FR-017**: System MUST display Mollie payment analysis when Mollie transactions are present
- **FR-018**: System MUST provide download option for Excel P&L report
- **FR-019**: System MUST provide download option for PDF management report (Jaarverslag)
- **FR-020**: System MUST provide download option for CSV transaction export
- **FR-021**: System MUST display appropriate error messages for invalid files or processing failures
- **FR-022**: System MUST format all monetary values in Belgian format (comma as decimal separator, period as thousands separator)
- **FR-023**: System MUST use Dutch language for labels and report text
- **FR-024**: System MUST be fully stateless - no preloaded company data, no server-side persistence

### Default Categories (Embedded)

The system embeds 30 Belgian expense categories:

**Income**: omzet

**Fully Deductible Expenses**: admin-kosten, bankkosten, boeken-en-tijdschriften, bureelbenodigdheden, drukwerk-en-publiciteit, huur-onroerend-goed, investeringen-over-3-jaar, klein-materiaal, kosten-opleiding-en-vorming, licenties-software, medisch-materiaal, sociale-bijdragen, telefonie, verzekering-beroepsaansprakelijkheid, vapz, vervoer, sponsoring, lidmaatschap, maatschap

**Partially Deductible**: onthaal (50%), relatiegeschenken (50%), restaurant (69%)

**Excluded from P&L**: interne-storting, loon, verkeerde-rekening, verkeerde-rekening-matched, mastercard, prive-opname, voorafbetaling

### Default Rules (Embedded)

The system embeds 48 categorization rules for Belgian midwives:

- **Income patterns**: RIZIV/INAMI, mutualiteiten (CM, Solidaris, Partena, Helan, etc.), hospitals (UZ, AZ, Sint-*), Mollie
- **Social contributions**: Acerta, Liantis, Xerius, UCM, Partena Sociaal
- **VAPZ**: Vivium, VAPZ keyword patterns
- **Insurance**: AMMA, AXA
- **Memberships**: VBOV, Orde van
- **Bank fees**: Beheerskosten, Rekeningkosten, Kaartkosten
- **Telecom**: Proximus, Telenet, Orange, Mobile Vikings
- **Medical supplies**: Medische Wereld, Apotheek/Pharmacie
- **Transport**: NMBS/SNCB, De Lijn, fuel stations
- **Excluded**: Eigen rekening transfers, FOD Financien, Mastercard settlement

### Key Entities

- **Transaction**: A financial record with date, amount, counterparty, description, and category assignment.
- **Category**: A classification for transactions with type (income/expense/excluded) and optional deductibility percentage.
- **Rule**: A pattern-matching definition that automatically assigns categories to transactions.
- **Report**: A generated financial summary containing income items, expense items, and totals.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can upload files and see imported transactions within 30 seconds for typical monthly statements (up to 100 transactions)
- **SC-002**: Users can complete full workflow (upload, categorize, download report) in under 5 minutes
- **SC-003**: Default rules categorize >15% of typical transactions automatically (user-specific rules achieve higher coverage)
- **SC-004**: Generated reports match the accuracy of existing command-line tool output (100% data parity)
- **SC-005**: System handles files up to 500 transactions without timeout or memory errors
- **SC-006**: Users can filter and find specific transactions in under 10 seconds
- **SC-007**: Users can edit a transaction category in under 30 seconds
- **SC-008**: Application remains accessible 99% of the time during business hours

## Assumptions

1. Users have modern web browsers (Chrome, Firefox, Safari, Edge - latest 2 versions)
2. Users have stable internet connection for file uploads and downloads
3. Users bring their own rules.yaml for high auto-categorization coverage, or manually categorize transactions
4. Monthly transaction volume is typically 50-100 transactions
5. Users are comfortable with Dutch-language interface
6. Session-based storage is acceptable (data not persisted between browser sessions)
7. Public URL access is acceptable for this internal bookkeeping tool

## Out of Scope

- User authentication and login (public access is acceptable for v1)
- Persistent data storage between sessions
- Multi-user collaboration features
- Rule editing through the web interface (upload rules.yaml instead)
- Mobile-optimized interface
- Integration with accounting software
- Automatic backup of uploaded data
- Email notifications or scheduled reports
- Preloaded company data (stateless architecture)

## Dependencies

- Existing PLV codebase services (csv_importer, pdf_importer, categorizer, report_generator, pdf_report_generator)
- Streamlit Community Cloud (free tier)
