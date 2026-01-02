# Feature Specification: Financial Report Generation

**Feature Branch**: `004-financial-report`
**Created**: 2026-01-02
**Status**: Draft
**Input**: User description: "in @data/2024/Resultatenrekening Vroedvrouw Goedele 2024.xlsx and @data/2024/Deseyn Goedele_Berekening eenmanszaak PB.pdf you can find the reporting that is built upon the list of transactions (feature 001), categorization (feature 002), depreciations (feature 003) create a similar report"

## Clarifications

### Session 2026-01-02
- Q: How should the system behave if the report output file already exists? → A: Create a new file with a timestamp or number suffix (e.g., `report-2.xlsx`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Annual P&L Report (Priority: P1)

As a self-employed midwife, I want to generate a complete Profit & Loss (P&L) report for a specific fiscal year, so that I can see a summary of my income, expenses, and profit for tax filing purposes.

**Why this priority**: This is the primary goal of the application. It provides the final, aggregated numbers required for the user's annual tax declaration.

**Independent Test**: Can be fully tested by running the report generation for a year with known data (transactions and assets) and verifying that the totals for income, expenses, and profit match a manual calculation.

**Acceptance Scenarios**:

1. **Given** I have categorized transactions and registered assets for 2025, **When** I run the report generation for the year 2025, **Then** the system produces a P&L report showing total income, total expenses, and the final profit/loss.
2. **Given** the generated report, **When** I view the income section, **Then** it shows a total for the 'omzet' category, with a sub-total for therapeutic vs. non-therapeutic income.
3. **Given** the generated report, **When** I view the expenses section, **Then** it shows a list of all expense categories with their respective total amounts, sorted alphabetically.
4. **Given** depreciable assets exist for the fiscal year, **When** I view the report, **Then** a dedicated 'afschrijvingen' (depreciation) expense line is included with the correct total annual depreciation amount.

---

### User Story 2 - Export P&L Report to Excel (Priority: P2)

As a self-employed midwife, I want to export the generated P&L report to an Excel file so that I can easily share it with my accountant or archive it for my records.

**Why this priority**: The user needs a persistent, shareable artifact of the report. Excel is the standard format for financial data exchange with accountants.

**Independent Test**: Can be tested by generating a report and specifying an Excel output file. The test passes if a valid `.xlsx` file is created with the correct P&L data and formatting.

**Acceptance Scenarios**:

1. **Given** a P&L report has been generated, **When** I specify an output path with an `.xlsx` extension, **Then** the system saves the report as a formatted Excel file at that path.
2. **Given** the Excel file is generated, **When** I open it, **Then** the layout is clean and professional, with clear headings for 'Baten' (Income), 'Kosten' (Expenses), and 'Resultaat' (Result).
3. **Given** the Excel file, **When** I inspect the numbers, **Then** they are formatted as currency values, and totals are calculated using Excel formulas where appropriate (e.g., `SUM(...)`).

---

### Edge Cases

- What happens when there are no transactions for the selected fiscal year?
  - The system should generate an empty report with a clear message stating "No data found for the selected year."
- What happens if some transactions are still uncategorized?
  - The report should include an "Uncategorized" line item in the expenses section to highlight that the report is incomplete and requires further action.
- What happens if the specified output file already exists?
  - The system will create a new file with a unique suffix (e.g., `report-1.xlsx`, `report-2.xlsx`) to avoid overwriting existing data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate a Profit & Loss (P&L) report for a given fiscal year.
- **FR-002**: The report MUST calculate total income by summing all transactions in the 'omzet' category.
- **FR-003**: The report MUST calculate total expenses by summing all transactions in expense categories, including a separate total for annual asset depreciation.
- **FR-004**: The report MUST calculate the final result (Profit/Loss) by subtracting total expenses from total income.
- **FR-005**: The report MUST provide a breakdown of income into "Therapeutic" and "Non-therapeutic" sub-totals.
- **FR-006**: The expense section MUST list each expense category alphabetically with its corresponding total.
- **FR-007**: The report MUST include a line item for 'afschrijvingen' (depreciation) calculated from the asset service.
- **FR-008**: System MUST allow exporting the report to a formatted Excel (`.xlsx`) file.
- **FR-009**: If uncategorized transactions exist for the period, they MUST be displayed as a separate line item in the report to ensure financial transparency.

### Key Entities

- **Report**: Represents the generated P&L statement for a fiscal year, containing sections for income, expenses, and the final result.
- **ReportLineItem**: A single line in the report, consisting of a label (e.g., a category name), an amount, and its type (income, expense).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The totals in the generated report MUST match the totals in the reference `Resultatenrekening 2024.xlsx` file when run on the same 2024 dataset, with a tolerance of €0.01 for rounding differences.
- **SC-002**: The report generation process for a full fiscal year with ~500 transactions MUST complete in under 10 seconds.
- **SC-003**: 100% of expense categories present in the transaction data for a given year appear as line items in the report.
- **SC-004**: The exported Excel report is correctly opened by standard spreadsheet applications (MS Excel, Google Sheets) without errors or formatting issues.

## Assumptions

- The user has already imported transactions and run categorization before generating a report.
- The chart of accounts (i.e., the list of categories) is stable and defined in `config/categories.yaml`.
- The fiscal year aligns with the calendar year (January 1 - December 31).
- All financial calculations are performed in EUR.