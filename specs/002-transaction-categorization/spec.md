# Feature Specification: Transaction Categorization

**Feature Branch**: `001-transaction-categorization`
**Created**: 2026-01-02
**Status**: Draft
**Input**: User description: "Apply consistent categorization of financial movements from Excel template to all bank and credit card statements"

## Clarifications

### Session 2026-01-02

- Q: How should categorized transactions be persisted between runs? → A: JSON/YAML file
- Q: What uniquely identifies a transaction for duplicate detection? → A: Statement number + Transaction number
- Q: How to handle Mastercard-Bank statement overlap? → A: Import Mastercard details, auto-exclude bank Mastercard settlement line
- Q: How should initial category rules be created? → A: Extract patterns from existing 2024 and 2025 Excel categorizations
- Q: Is P&L report generation part of this feature? → A: No, separate feature (this outputs categorized JSON)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Import Bank Transactions (Priority: P1)

As a midwife preparing tax documents, I want to import all my Belfius bank statement CSV files so that I have a complete record of financial transactions for the year.

**Why this priority**: Without imported transactions, no categorization can occur. This is the foundational data ingestion step.

**Independent Test**: Load a single bank CSV file and verify all transactions are parsed with correct dates, amounts, counterparty names, and descriptions.

**Acceptance Scenarios**:

1. **Given** a Belfius bank CSV file with transactions, **When** I run the import command, **Then** all transactions are loaded with: booking date, amount (positive/negative preserved), counterparty name, counterparty account (IBAN), and transaction description.
2. **Given** multiple CSV files with overlapping date ranges, **When** I import them, **Then** duplicate transactions (identified by statement number + transaction number) are detected and only imported once.
3. **Given** a CSV with Belgian number format (comma as decimal separator), **When** I import it, **Then** amounts are correctly parsed (e.g., "1.234,56" becomes 1234.56).

---

### User Story 2 - Import Mastercard Transactions (Priority: P2)

As a midwife, I want to import transactions from my Belfius Mastercard PDF statements so that credit card expenses are included in my P&L.

**Why this priority**: Mastercard transactions represent a separate expense stream that must be tracked, but bank transactions are the primary source.

**Independent Test**: Load a single Mastercard PDF and verify all transactions are extracted with dates, descriptions, and amounts (including refunds marked with +).

**Acceptance Scenarios**:

1. **Given** a Belfius Mastercard PDF statement, **When** I run the import command, **Then** all transactions in the transaction table are extracted with: transaction date, settlement date, description, and amount.
2. **Given** a Mastercard statement with a refund (positive amount with + suffix), **When** I import it, **Then** the refund is recorded as a positive amount.
3. **Given** multiple monthly Mastercard PDFs, **When** I import them, **Then** all transactions are combined chronologically without duplicates.

---

### User Story 3 - Auto-Categorize Transactions Using Rules (Priority: P1)

As a midwife, I want transactions to be automatically categorized based on counterparty patterns so that I don't have to manually categorize each transaction.

**Why this priority**: Manual categorization of hundreds of transactions is error-prone and time-consuming. Automation is essential for consistency.

**Independent Test**: Import transactions and apply categorization rules; verify that known counterparties are correctly categorized.

**Acceptance Scenarios**:

1. **Given** a transaction from "Sweele B.V." (rent payment), **When** auto-categorization runs, **Then** it is categorized as "Huur onroerend goed".
2. **Given** a transaction from health insurance (e.g., "LCM VP", "SOLIDARIS", "RIZIV", "MUTUALITES"), **When** auto-categorization runs, **Then** it is categorized as "Omzet".
3. **Given** a transaction from "BOL.COM", **When** auto-categorization runs, **Then** it is categorized as "Boeken en tijdschriften".
4. **Given** a transaction with no matching rule, **When** auto-categorization runs, **Then** it remains "Uncategorized" for manual review.

---

### User Story 4 - Configure Category Rules (Priority: P2)

As a midwife, I want to define and modify categorization rules so that I can adapt the system to new vendors or correct miscategorizations.

**Why this priority**: The rule set must be maintainable and extensible as business relationships change.

**Independent Test**: Add a new rule for a vendor, re-run categorization, and verify the vendor's transactions are now categorized correctly.

**Acceptance Scenarios**:

1. **Given** a YAML/JSON configuration file with category rules, **When** I add a new rule pattern, **Then** subsequent categorization runs apply the new rule.
2. **Given** a rule with counterparty pattern "ACTION*", **When** a transaction from "ACTION 2028" is processed, **Then** it matches the rule.
3. **Given** multiple rules that could match a transaction, **When** categorization runs, **Then** the first matching rule (by order in config) is applied.

---

### User Story 5 - Review and Correct Categorizations (Priority: P2)

As a midwife, I want to review uncategorized transactions and manually assign categories so that all transactions are properly classified before generating the P&L.

**Why this priority**: Some transactions will always require human judgment; the system must support manual overrides.

**Independent Test**: List uncategorized transactions, manually assign a category to one, and verify the assignment persists.

**Acceptance Scenarios**:

1. **Given** transactions have been auto-categorized, **When** I request a list of uncategorized items, **Then** I see all transactions without a category.
2. **Given** an uncategorized transaction, **When** I manually assign category "Klein materiaal", **Then** the category is saved and used in reports.
3. **Given** a transaction with an auto-assigned category, **When** I manually override it to a different category, **Then** the manual assignment takes precedence.

---

### User Story 6 - Mark Therapeutic Transactions (Priority: P3)

As a midwife, I want to mark certain revenue transactions as "Therapeutic" (direct patient care) so that I can track billable vs. non-billable income.

**Why this priority**: Belgian tax rules distinguish between therapeutic services and other income; this classification supports tax compliance.

**Independent Test**: Mark a transaction as therapeutic and verify the flag is stored and appears in reports.

**Acceptance Scenarios**:

1. **Given** an "Omzet" transaction, **When** I mark it as therapeutic, **Then** the transaction has a "Therapeutisch" flag set to true.
2. **Given** a list of revenue transactions, **When** I filter by therapeutic flag, **Then** only therapeutic transactions are shown.
3. **Given** a P&L report is generated, **When** I view the revenue section, **Then** therapeutic and non-therapeutic revenue are shown separately.

---

### Edge Cases

- What happens when a transaction description is empty or contains only whitespace? The system uses counterparty name for categorization matching.
- What happens when a CSV file is malformed (wrong number of columns)? The system reports an error with line number and skips malformed rows.
- What happens when amount parsing fails due to unexpected format? The system flags the transaction for manual review with original value preserved.
- What happens when the same vendor has multiple business categories? Multiple rules for the same counterparty with different description patterns are supported.
- What happens when a bank CSV contains a Mastercard settlement line? The system auto-excludes bank transactions matching Mastercard settlement patterns to avoid double-counting with detailed Mastercard PDF transactions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST import Belfius bank CSV files with semicolon delimiters and Belgian number format.
- **FR-002**: System MUST extract transactions from Belfius Mastercard PDF statements.
- **FR-003**: System MUST detect and skip duplicate transactions across multiple import files.
- **FR-004**: System MUST support 26 expense/income categories as defined in the existing Excel template.
- **FR-005**: System MUST apply categorization rules based on counterparty name patterns (exact match, prefix, contains, regex).
- **FR-006**: System MUST preserve original transaction data alongside categorization for audit trail.
- **FR-007**: System MUST allow manual category assignment and override of auto-categorization.
- **FR-008**: System MUST support a "Therapeutisch" flag on revenue transactions.
- **FR-009**: System MUST maintain categorization rules in a human-readable configuration file (YAML or JSON).
- **FR-010**: System MUST report all uncategorized transactions for user review.
- **FR-011**: System MUST persist categorized transactions to a JSON or YAML data file, preserving all categorization decisions and manual overrides between runs.
- **FR-012**: System MUST auto-exclude bank CSV transactions that represent Mastercard monthly settlements (to avoid double-counting with detailed Mastercard PDF transactions).
- **FR-013**: System MUST provide a bootstrap mechanism to extract categorization rules from existing Excel files (Verrichtingen 2024 and 2025 sheets) by mining counterparty-to-category patterns.

### Key Entities

- **Transaction**: Represents a single financial movement with: source_file, statement_number, transaction_number (unique key), booking_date, value_date, amount, currency, counterparty_name, counterparty_iban, description, category, is_therapeutic, is_manual_override.
- **Category**: A predefined expense or income type (e.g., "Omzet", "Huur onroerend goed", "Klein materiaal"). The 26 categories from the Excel template are: Admin kosten, Bankkosten, Boeken en tijdschriften, Bureelbenodigdheden, Drukwerk en publiciteit, Huur onroerend goed, Interne storting, Investeringen over 3 jaar, Klein materiaal, Kosten opleiding en vorming, Licenties software, Loon, Maatschap Huis van Meraki, Medisch materiaal, Omzet, Onthaal, Relatiegeschenken, Restaurant, Sociale bijdragen, Telefonie, Verkeerde rekening, Verzekering beroepsaansprakelijkheid, Vrij Aanvullend Pensioen Zelfstandigen, Vervoer, Mastercard, Sponsoring.
- **CategoryRule**: A pattern-matching rule with: pattern_type (exact/prefix/contains/regex), pattern_value, target_category, priority_order.

## Out of Scope

- P&L report generation (Excel Resultatenrekening output) - separate follow-up feature
- Write-off/depreciation calculations - separate feature
- Year-over-year comparison reports - separate feature
- Multi-user access or authentication - single-user CLI tool

## Assumptions

- All transactions are in EUR (single currency).
- Bank CSV exports follow the standard Belfius export format (columns: Rekening, Boekingsdatum, Rekeninguittrekselnummer, Transactienummer, Rekening tegenpartij, Naam tegenpartij bevat, Straat en nummer, Postcode en plaats, Transactie, Valutadatum, Bedrag, Devies, BIC, Landcode, Mededelingen).
- Mastercard PDFs follow the standard Belfius credit card statement format.
- The 26 categories from the existing Excel file represent the complete category set; new categories can be added via configuration.
- A transaction belongs to exactly one category.
- Fiscal year is the calendar year (January 1 - December 31).
- Historical categorized data is available in `data/2024/Resultatenrekening Vroedvrouw Goedele 2024.xlsx` and `data/2025/Resultatenrekening Vroedvrouw Goedele 2025.xlsx` for rule extraction.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 90% of transactions are auto-categorized correctly without manual intervention (based on existing Excel categorizations as ground truth).
- **SC-002**: All transactions from source files are imported without data loss (100% import accuracy).
- **SC-003**: Users can complete the annual categorization review in under 2 hours (vs. current manual Excel process).
- **SC-004**: Zero miscategorized transactions in the final P&L output (all flagged for review are resolved).
- **SC-005**: Categorization rules are reusable year-over-year with minimal updates (fewer than 10 new rules per year).
