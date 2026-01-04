# Feature Specification: Report Data Quality Warnings

**Feature Branch**: `007-report-warnings`
**Created**: 2026-01-04
**Status**: Draft
**Input**: User description: "In the jaarverslag and xlsx there should be an explicit mention of uncategorized transactions or non-reimbursed private expenses."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Uncategorized Transaction Warnings (Priority: P1)

As an accountant generating financial reports, I need to see a clear warning when there are uncategorized transactions so that I can address data quality issues before finalizing tax filings.

**Why this priority**: Uncategorized transactions directly affect the accuracy of P&L reports. Missing categorizations can lead to incorrect tax declarations and potential penalties.

**Independent Test**: Generate a report with at least one uncategorized transaction and verify the warning appears in both PDF and Excel outputs with the count and total amount.

**Acceptance Scenarios**:

1. **Given** transactions exist with no category assigned, **When** I generate a PDF jaarverslag, **Then** a visible warning section displays the count and total amount of uncategorized transactions
2. **Given** transactions exist with no category assigned, **When** I export to Excel, **Then** a dedicated sheet or section lists all uncategorized transactions with their details
3. **Given** all transactions are categorized, **When** I generate any report, **Then** no uncategorized warning appears

---

### User Story 2 - View Non-Reimbursed Private Expense Warnings (Priority: P2)

As a self-employed professional, I need to see when private expenses paid from the business account have not been matched with a reimbursement, so I can ensure proper accounting treatment.

**Why this priority**: Private expenses (verkeerde-rekening) that aren't matched with reimbursements indicate either missing reimbursement entries or incorrect categorization, both of which affect the accuracy of financial statements.

**Independent Test**: Generate a report with verkeerde-rekening transactions that don't have matching positive reimbursements and verify the warning appears with specific details.

**Acceptance Scenarios**:

1. **Given** private expenses exist without matching reimbursements, **When** I generate a PDF jaarverslag, **Then** a warning section shows the net unbalanced amount for private expenses
2. **Given** private expenses exist without matching reimbursements, **When** I export to Excel, **Then** the unbalanced private expense transactions are listed with their details
3. **Given** all private expenses have matching reimbursements (net zero), **When** I generate any report, **Then** no private expense warning appears

---

### Edge Cases

- What happens when there are zero transactions in the dataset? No warnings should appear, just empty report
- How does the system handle verkeerde-rekening transactions that have partial reimbursements? Show the net unbalanced amount
- What if both uncategorized and non-reimbursed private expenses exist? Show both warnings separately
- What if verkeerde-rekening has a positive net balance (over-reimbursed)? Show warning indicating excess reimbursement

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a warning in the PDF jaarverslag when uncategorized transactions exist: (a) brief banner on page 1 after summary showing count and total, (b) detailed "Aandachtspunten" section at end with full context
- **FR-002**: System MUST include uncategorized transactions in Excel export: (a) keep existing warning on P&L sheet, (b) new "Aandachtspunten" sheet with warning summary and full transaction details (date, amount, counterparty, description)
- **FR-003**: System MUST calculate the net balance of verkeerde-rekening (private expense) category and warn if non-zero
- **FR-004**: System MUST display the net unbalanced private expense amount in the PDF jaarverslag when applicable: (a) brief banner on page 1 after summary, (b) detailed breakdown in "Aandachtspunten" section at end
- **FR-005**: System MUST include unbalanced private expense details in Excel export: (a) warning on P&L sheet showing net balance, (b) full transaction list in "Aandachtspunten" sheet
- **FR-006**: System MUST suppress warnings when no data quality issues exist (all categorized, private expenses balanced)
- **FR-007**: Warnings MUST include actionable context (e.g., "Review categorization" or "Add missing reimbursement")
- **FR-008**: Warning sections MUST be visually distinct (highlighted) to draw attention to data quality issues

### Key Entities

- **Uncategorized Transaction**: A transaction without an assigned category (category is null, empty, or "uncategorized")
- **Private Expense (verkeerde-rekening)**: Transactions categorized as personal expenses paid from the business account
- **Reimbursement**: Positive transactions in the verkeerde-rekening category representing repayment from personal funds
- **Net Balance**: Sum of all verkeerde-rekening transactions (should be zero when properly balanced)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of reports with uncategorized transactions display a visible warning in both PDF and Excel formats
- **SC-002**: 100% of reports with non-zero verkeerde-rekening balance display a visible warning with the exact unbalanced amount
- **SC-003**: Users can identify all data quality issues within 10 seconds of opening a report
- **SC-004**: Warnings include enough context that users can take corrective action without consulting documentation

## Clarifications

### Session 2026-01-04

- Q: Where should warnings appear in PDF jaarverslag? → A: Both - brief banner on page 1 after summary + detailed "Aandachtspunten" section at end before closing
- Q: How should Excel export display warnings? → A: Keep existing warning on P&L sheet + new "Aandachtspunten" sheet with warning summary and full transaction details

## Assumptions

- Verkeerde-rekening transactions should net to zero when properly balanced (expenses + reimbursements = 0)
- Warnings are informational and do not block report generation
- Excel export already exists via the `-o` option and this feature adds additional warning/detail sections
- The existing categorization system properly marks transactions as uncategorized when no rule matches
- Both PDF (jaarverslag) and Excel outputs should receive these warnings
