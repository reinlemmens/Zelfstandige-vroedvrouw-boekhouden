# Research: 2025 Transaction Import

**Feature**: 001-2025-transaction-import
**Date**: 2026-01-02

## CSV Parsing Strategy

**Decision**: Use pandas with custom parsing for Belfius format

**Rationale**:
- Belfius exports use semicolon delimiter (`;`) and European locale
- Header row starts at line 13 (lines 1-12 contain metadata)
- Amount format: `1.234,56` (dot for thousands, comma for decimal)
- pandas handles this with `sep=';'` and `decimal=','`

**Alternatives Considered**:
- Built-in csv module: More manual parsing needed for European numbers
- openpyxl: Overkill for CSV, better for Excel output

**Implementation Notes**:
```python
# Skip metadata rows, parse with European locale
df = pd.read_csv(file, sep=';', decimal=',', skiprows=12, encoding='utf-8')
```

## PDF Parsing Strategy

**Decision**: Use pdfplumber for Mastercard PDF extraction

**Rationale**:
- pdfplumber excels at table extraction from PDFs
- Mastercard statements have consistent table structure
- Can extract both text and tabular data

**Alternatives Considered**:
- PyPDF2: Good for text but weak on tables
- tabula-py: Requires Java dependency (violates simplicity)
- pdf2image + OCR: Overkill for text-based PDFs

**Implementation Notes**:
- Transaction table starts after "Transacties - Kaartnummer" header
- Columns: DATUM TRANSACTIE, DATUM VERREKENING, OMSCHRIJVING, BEDRAG
- Amount format: `38,51 EUR -` (amount, currency, sign)
- Refunds marked with `+` sign

## Deduplication Strategy

**Decision**: Composite key with fallback matching

**Primary Key**: `{Account}|{BookingDate}|{TransactionNumber}|{Reference}`

**Rationale**:
- Transaction number is unique within a statement
- Reference (REF.) provides additional uniqueness
- Booking date + account scopes to specific statement
- This combination is unique even across overlapping exports

**Edge Cases**:
- Same-day, same-amount transactions to same counterparty: Distinguished by transaction number
- Missing reference: Use description hash as fallback

## Mastercard Settlement Linking

**Decision**: Match by settlement date and total amount

**Rationale**:
- Bank CSV shows settlement as single debit on "Datum van debet" (e.g., 03/11/2025)
- PDF shows same date and total amount
- Card number in description confirms linkage

**Matching Logic**:
1. Find bank entries containing "5440 56" (Mastercard number prefix) or card reference patterns
2. Extract settlement amount from bank entry
3. Match to PDF statement by:
   - Settlement date within ±1 day of bank booking date
   - Total amount matches (accounting for sign)

**Conflict Resolution**:
- If multiple PDFs match same settlement: Flag for manual review
- If settlement has no matching PDF: Include with warning

## Google Sheet Output via MCP

**Decision**: Use `mcp__google-drive__createGoogleSheet` tool

**Rationale**:
- Direct integration with Claude Code environment
- No additional authentication setup needed
- Creates shareable, cloud-based output

**Implementation**:
- Tool: `createGoogleSheet`
- Parent folder: `1TJAIGg_RlomBlyPXjnKYH0XJWg2osxdW`
- Data format: Array of arrays (rows)

**Column Structure**:
| Column | Description |
|--------|-------------|
| Date | Booking date (YYYY-MM-DD) |
| Account | IBAN (BE05...) |
| Amount | Transaction amount (negative for debits) |
| Counterparty | Name of other party |
| Description | Transaction description |
| Reference | Bank reference number |
| Type | "regular" or "settlement" |
| Source File | Original file name |

## Data Volume Analysis

**Input Files** (from data/2025/):
- 5 CSV files (bank statements, ~500+ transactions each based on file sizes)
- 5 PDF files (Mastercard statements, ~5-20 transactions each)
- 1 Excel file (excluded - separate report)

**Expected Output**:
- Estimated 500-1000 unique transactions after deduplication
- Google Sheet can handle this volume easily

## Dependencies

**Required**:
- `pandas>=2.0`: CSV parsing, data manipulation
- `pdfplumber>=0.10`: PDF table extraction

**Already Available**:
- Google Drive MCP tools (in Claude Code environment)

**Not Needed**:
- Database (file-based processing)
- Web framework (CLI only)
- Authentication libraries (MCP handles Google auth)
