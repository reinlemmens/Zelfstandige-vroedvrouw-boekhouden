<!--
  SYNC IMPACT REPORT
  ====================
  Version change: 1.0.0 → 2.0.0 (MAJOR - Principle V redefined for Streamlit)

  Modified principles:
  - V. Simplicity → V. Simplicity & Accessibility (expanded to include Streamlit web interface)

  Added sections:
  - Principle VI: Stateless Public Operation

  Removed sections: None

  Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ Updated - Constitution Check now includes all 6 principles
  - .specify/templates/spec-template.md: ✅ No changes needed
  - .specify/templates/tasks-template.md: ✅ No changes needed

  Follow-up TODOs: None
-->

# Vroedvrouw Goedele P&L Tool Constitution

## Core Principles

### I. Data Integrity

All financial data MUST be traceable to source documents (bank CSV exports, Mastercard PDF
statements). Every transaction in the final P&L MUST reference its origin file and line/entry.
No manual data entry for transactions that exist in source files. Calculations MUST be
deterministic and reproducible - running the same inputs MUST produce identical outputs.

**Rationale**: Tax filings require audit trails. The Belgian tax authority (FOD Financien) may
request source documentation for any declared amount.

### II. Belgian Tax Compliance

The P&L output MUST conform to Belgian tax requirements for independent professionals
(zelfstandigen/indépendants). Categories MUST align with the standard Belgian
"Resultatenrekening" structure:
- Omzet (Revenue)
- Beroepskosten (Professional expenses) with proper subcategories
- Afschrijvingen (Depreciation/Write-offs)
- Netto belastbaar inkomen (Net taxable income)

All amounts MUST be in EUR. Dates MUST follow Belgian fiscal year (calendar year).

**Rationale**: Non-compliant filings result in penalties or rejection by the tax authority.

### III. Transparency & Auditability

Every categorization decision MUST be explainable. The system MUST generate a detailed
breakdown showing:
- How each transaction was categorized
- Which rules/patterns matched
- Any ambiguous transactions flagged for user review

Uncategorized or ambiguous transactions MUST NOT be silently dropped or auto-assigned.

**Rationale**: The midwife (Goedele) must understand and verify all categorizations before
signing the tax declaration.

### IV. User Control

Users MUST explicitly configure:
- Write-off schedules (afschrijvingen) with asset descriptions, purchase dates, and periods
- Category mappings for recurring counterparties
- Professional vs. private expense ratios for mixed-use items (e.g., phone, car)
- Any manual adjustments with documented justification

The system MUST NOT make assumptions about deductibility without user confirmation.

**Rationale**: Tax liability is personal. The taxpayer must control and understand all inputs.

### V. Simplicity & Accessibility

The tool provides two interfaces:
- **CLI** (primary): Python scripts runnable locally for power users and automation
- **Web** (Streamlit): Browser-based interface for users who prefer not to use command line

Both interfaces MUST use the same core services and produce identical outputs for the same
inputs. Configuration via simple files (YAML/JSON). Output as Excel (matching the existing
format) plus optional CSV/JSON/PDF for analysis.

Dependencies MUST be minimal and well-maintained (pandas, openpyxl, pdfplumber, Streamlit).
The Streamlit app MUST be deployable on Streamlit Community Cloud (free tier).

**Rationale**: This is an annual task. The tool must remain accessible to non-technical users
while still supporting CLI workflows for automation and advanced use cases.

### VI. Stateless Public Operation

The Streamlit web application is public and MUST operate statelessly:
- NO server-side persistence of user data between sessions
- NO user accounts, authentication, or login required
- ALL uploaded files processed in-memory only
- Session data cleared when browser tab closes or session times out
- Users MUST re-upload files to resume work

The application MUST NOT:
- Store financial data on the server filesystem
- Log or transmit transaction details to external services
- Retain any user-identifiable information after session ends

Configuration files (rules, categories) may be bundled with the application or loaded per
company selection, but user-uploaded bank statements MUST NOT persist.

**Rationale**: Financial data is sensitive. A public stateless design ensures users retain
full control of their data while enabling convenient browser-based access without complex
authentication infrastructure.

## Input Data Requirements

### Bank Statements (CSV)
- Source: Belfius bank export
- Format: Semicolon-separated CSV with Belgian locale (comma as decimal separator)
- Required columns: Boekingsdatum, Bedrag, Naam tegenpartij, Mededelingen, Rekening tegenpartij
- Multiple CSV files per year supported (merged by date)

### Mastercard Statements (PDF)
- Source: Belfius Mastercard monthly statements
- Format: PDF with transaction tables
- Required fields: Transaction date, Description, Amount, Currency
- Parser MUST handle refunds (positive amounts marked with +)

### Write-off Configuration
- Format: YAML or JSON file
- Required fields per asset: description, purchase_date, purchase_amount, depreciation_years,
  category
- System calculates annual depreciation automatically

### Category Rules
- Format: YAML or JSON file
- Pattern matching on counterparty name and/or description
- Supports regex patterns
- Fallback to "uncategorized" for review

## Output Requirements

### Legal P&L (Primary)
- Format: Excel (.xlsx) matching structure of previous year's Resultatenrekening
- Sections: Revenue, Expenses by category, Write-offs, Net result
- Summary sheet + detailed transaction list sheet
- Ready for accountant review and tax filing

### Analysis Reports (Secondary)
- Monthly cost breakdown
- Category-wise expense analysis
- Year-over-year comparison (when previous year data available)
- Profitability metrics (revenue vs. costs)
- Format: Excel sheets, CSV, or PDF (Jaarverslag)

## Governance

This constitution establishes the non-negotiable principles for the Vroedvrouw Goedele P&L
tool. All implementation decisions MUST align with these principles.

**Amendment Process**:
1. Propose change with rationale
2. Assess impact on existing functionality and tax compliance
3. Update version number (MAJOR for principle changes, MINOR for additions, PATCH for
   clarifications)
4. Document change in this file's sync impact report

**Compliance Review**:
- Before each annual tax filing, verify tool output against principles
- Any discrepancies must be resolved before submission
- For public web app: periodically verify no data persistence violations

**Version**: 2.0.0 | **Ratified**: 2026-01-02 | **Last Amended**: 2026-01-05
