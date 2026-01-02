<!--
  SYNC IMPACT REPORT
  ====================
  Version change: 0.0.0 → 1.0.0 (MAJOR - initial constitution)

  Modified principles: N/A (new constitution)

  Added sections:
  - Core Principles (5 principles)
  - Input Data Requirements
  - Output Requirements
  - Governance

  Removed sections: N/A

  Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ No changes needed (generic)
  - .specify/templates/spec-template.md: ✅ No changes needed (generic)
  - .specify/templates/tasks-template.md: ✅ No changes needed (generic)

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

### V. Simplicity

Implementation MUST be Python CLI scripts that can be run locally. No web servers, databases,
or cloud services required. Configuration via simple files (YAML/JSON). Output as Excel
(matching the existing format) plus optional CSV/JSON for analysis.

Dependencies MUST be minimal and well-maintained (pandas, openpyxl for Excel, pdfplumber or
similar for PDF parsing).

**Rationale**: This is an annual task. The tool must remain runnable year after year without
complex infrastructure maintenance.

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
- Format: Excel sheets or CSV

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

**Version**: 1.0.0 | **Ratified**: 2026-01-02 | **Last Amended**: 2026-01-02
