# Feature Specification: 2025 Transaction Import & Consolidation

**Feature Branch**: `001-2025-transaction-import`
**Created**: 2026-01-02
**Status**: Draft
**Input**: User description: "Import all CSV files and PDFs in data/2025 and create a list of all transactions in 2025, making sure to not miss out on any and not double count transactions that appear twice. For Mastercard specifically, they are aangezuiverd from the main account, so each mastercard statement is also as a whole in the bank statements."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Import Bank Statement CSVs (Priority: P1)

As a user, I want to import all Belfius bank statement CSV files from the data/2025 folder so that I have all bank transactions available for review.

**Why this priority**: The bank statement CSVs contain the primary transaction data for both accounts (BE05 0636 4778 9475 - Vroedvrouw Goedele business account and BE05 0682 4812 1175 - secondary account). This is the foundation for all transaction tracking.

**Independent Test**: Can be fully tested by importing CSV files and verifying all transactions are captured with correct dates, amounts, and descriptions.

**Acceptance Scenarios**:

1. **Given** CSV files exist in data/2025 folder, **When** the import process runs, **Then** all transactions from all CSV files are imported with their complete details (date, amount, counterparty, description, reference)
2. **Given** multiple CSV files contain overlapping date ranges, **When** the import process runs, **Then** transactions appearing in multiple files are deduplicated based on unique identifiers (account + date + transaction number + reference)
3. **Given** a CSV file uses semicolon delimiters and European number format (comma as decimal separator), **When** the import process runs, **Then** amounts are correctly parsed as numeric values

---

### User Story 2 - Import Mastercard PDF Statements (Priority: P1)

As a user, I want to import all Mastercard statement PDFs from the data/2025 folder so that I have detailed Mastercard transaction information available.

**Why this priority**: The Mastercard PDFs contain individual transaction details that are not visible in the bank statements where only the total settlement amount appears.

**Independent Test**: Can be fully tested by importing PDF files and verifying individual Mastercard transactions are extracted with correct dates, merchants, and amounts.

**Acceptance Scenarios**:

1. **Given** Mastercard PDF statements exist in data/2025 folder, **When** the import process runs, **Then** individual transactions are extracted including transaction date, settlement date, merchant name, location, and amount
2. **Given** a Mastercard PDF contains both debit (-) and credit (+) transactions, **When** the import process runs, **Then** both types are correctly captured with appropriate sign
3. **Given** a Mastercard PDF shows a statement period and total, **When** the import process runs, **Then** the statement metadata (period dates, settlement date, total amount) is also captured

---

### User Story 3 - Prevent Double Counting of Mastercard Transactions (Priority: P1)

As a user, I want the system to recognize that Mastercard statement totals appear as settlement transactions in the bank statements, so that individual Mastercard transactions are not counted twice alongside their aggregated settlement.

**Why this priority**: This is critical for financial accuracy. Each Mastercard statement total is "aangezuiverd" (settled) from the main account, meaning the bank statement contains a single settlement line while the PDF contains the individual transactions making up that total.

**Independent Test**: Can be fully tested by verifying that the sum of all transactions equals the expected total, and that Mastercard settlement lines in bank statements are marked as "summary" entries linked to their detailed PDF transactions.

**Acceptance Scenarios**:

1. **Given** a Mastercard PDF with total 63.00 EUR and a bank statement showing a Mastercard settlement of 63.00 EUR, **When** transactions are consolidated, **Then** the individual Mastercard transactions are included but the settlement line is flagged as a "settlement/summary" entry to avoid double counting
2. **Given** a consolidated transaction list, **When** calculating totals, **Then** settlement entries are excluded from summation since their component transactions are already included
3. **Given** Mastercard card number 5440 56XX XXXX 6159 in a PDF statement, **When** matching to bank settlement entries, **Then** the system links the PDF transactions to their corresponding bank settlement entry

---

### User Story 4 - Deduplicate Transactions Across Files (Priority: P2)

As a user, I want duplicate transactions that appear in multiple CSV files to be automatically deduplicated so that each transaction is only counted once.

**Why this priority**: Bank statement exports may overlap in date ranges, causing the same transaction to appear in multiple files.

**Independent Test**: Can be tested by importing overlapping CSV files and verifying transaction count matches expected unique transactions.

**Acceptance Scenarios**:

1. **Given** two CSV files with overlapping periods containing the same transaction, **When** both files are imported, **Then** the transaction appears only once in the final list
2. **Given** a transaction with identical date, amount, and reference in multiple files, **When** deduplication runs, **Then** the transaction is identified as a duplicate based on the unique combination of: Account + Booking Date + Transaction Number + Reference Number

---

### User Story 5 - Generate Complete Transaction List (Priority: P2)

As a user, I want to see a consolidated list of all 2025 transactions from all sources, properly categorized and without duplicates, so that I have a complete financial overview.

**Why this priority**: This is the end goal of the feature - a clean, accurate transaction list for accounting purposes.

**Independent Test**: Can be tested by comparing the final list total against manual verification of source documents.

**Acceptance Scenarios**:

1. **Given** all sources have been imported and deduplicated, **When** the consolidated list is generated, **Then** it includes all unique transactions sorted by date
2. **Given** transactions come from multiple accounts, **When** viewing the consolidated list, **Then** each transaction is clearly labeled with its source account
3. **Given** Mastercard transactions exist, **When** viewing the consolidated list, **Then** they are shown as individual transactions with the settlement entry marked separately

---

### Edge Cases

- What happens when a CSV file is malformed or has encoding issues?
  - System should report the error and continue importing other files
- How does system handle Mastercard PDFs that cannot be parsed?
  - System should flag the file for manual review and continue processing other files
- What happens when a Mastercard settlement amount doesn't match the PDF total?
  - System should flag a discrepancy warning but include both sets of data
- How are transactions in foreign currencies handled?
  - All transactions in the data appear to be in EUR; non-EUR transactions should be flagged for review
- What happens with zero-amount transactions (fees, administrative entries)?
  - These should be included in the transaction list as they represent legitimate banking activity

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST import all CSV files from the data/2025 folder with semicolon-delimited format
- **FR-002**: System MUST parse CSV headers correctly to identify columns: Rekening, Boekingsdatum, Rekeninguittrekselnummer, Transactienummer, Rekening tegenpartij, Naam tegenpartij, Transactie, Valutadatum, Bedrag, Devies, BIC, Landcode, Mededelingen
- **FR-003**: System MUST handle European number format (comma as decimal separator) for amount fields
- **FR-004**: System MUST import all PDF files from the data/2025 folder that are Mastercard statements
- **FR-005**: System MUST extract individual transactions from Mastercard PDFs including: transaction date, settlement date, merchant name, location, amount, and +/- indicator
- **FR-006**: System MUST identify Mastercard settlement entries in bank CSVs (entries referencing card numbers or "MASTERCARD" in the description)
- **FR-007**: System MUST link Mastercard PDF transactions to their corresponding bank settlement entry using statement period and total amount
- **FR-008**: System MUST deduplicate transactions using the combination of: Account Number + Booking Date + Transaction Number + Reference
- **FR-009**: System MUST flag settlement entries as "summary" type to prevent double counting with their detailed transactions
- **FR-010**: System MUST generate a consolidated transaction list with all unique transactions
- **FR-011**: System MUST include source tracking for each transaction (which file it came from)
- **FR-012**: System MUST handle the two identified accounts: BE05 0636 4778 9475 (Vroedvrouw Goedele) and BE05 0682 4812 1175
- **FR-013**: System MUST output the consolidated transaction list as a single Google Sheet with all transactions in one sheet, using an account column to distinguish sources (via MCP integration to folder ID `1TJAIGg_RlomBlyPXjnKYH0XJWg2osxdW`)
- **FR-014**: System MUST filter the final output to include only transactions dated within 2025 (01/01/2025 - 31/12/2025)

### Key Entities

- **Transaction**: A single financial movement with date, amount, counterparty, description, reference, source account, and source file. Has a type indicator (regular/settlement)
- **BankStatement**: A CSV file import containing multiple transactions for a specific account and date range
- **MastercardStatement**: A PDF file containing individual card transactions for a billing period, with statement dates and total amount
- **SettlementLink**: A relationship connecting a bank settlement entry to its corresponding Mastercard statement and detailed transactions
- **Account**: A bank account identified by IBAN (BE05 0636 4778 9475 or BE05 0682 4812 1175) with associated name/description

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of CSV files in data/2025 are successfully imported without data loss
- **SC-002**: 100% of Mastercard PDF statements in data/2025 are successfully parsed and transactions extracted
- **SC-003**: Zero duplicate transactions in the final consolidated list (verified by unique transaction identifiers)
- **SC-004**: Mastercard settlement amounts in bank statements match the totals from corresponding PDF statements (with any discrepancies flagged)
- **SC-005**: The sum of all non-settlement transactions equals the correct financial total for 2025
- **SC-006**: Each transaction in the final list can be traced back to its source file
- **SC-007**: User can distinguish between regular transactions and settlement summary entries in the output

## Clarifications

### Session 2026-01-02

- Q: What format should the consolidated transaction list be output in? → A: Google Sheet (cloud-based, shareable, with MCP integration available)
- Q: Should the output include all transactions from files or filter by date? → A: Import all data from files, but filter final output to only 2025 transactions (01/01/2025 - 31/12/2025)
- Q: How should transactions from multiple accounts be organized in the output? → A: Single sheet with all transactions, using an account column to distinguish
- Q: Where should the Google Sheet be created? → A: Google Drive folder ID `1TJAIGg_RlomBlyPXjnKYH0XJWg2osxdW`

## Assumptions

- All data files for 2025 are located in the data/2025 folder
- CSV files follow the Belfius bank export format with semicolon delimiters
- Mastercard PDFs follow the Belfius Mastercard statement format shown in the samples
- All amounts are in EUR (European number format with comma as decimal separator)
- The Mastercard card number 5440 56XX XXXX 6159 belongs to Goedele Deseyn and is settled from account BE05 0636 4778 9475
- Duplicate files (e.g., files with "(1)" suffix) contain the same data and should be deduplicated
- The Excel file (Resultatenrekening Vroedvrouw Goedele 2025.xlsx) is a separate report and not a source for transaction import
