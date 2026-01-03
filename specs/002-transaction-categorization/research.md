# Research: Transaction Categorization

**Feature**: 002-transaction-categorization
**Date**: 2026-01-02

## Research Topics

### 1. PDF Parsing Library Selection

**Decision**: pdfplumber

**Rationale**:
- Pure Python, no external dependencies (vs. PyMuPDF which requires system libs)
- Excellent table extraction specifically designed for tabular PDF data
- Active maintenance and good documentation
- Handles the Belfius Mastercard statement format (simple table structure)

**Alternatives Considered**:
| Library | Pros | Cons | Rejected Because |
|---------|------|------|------------------|
| PyPDF2 | Simple, lightweight | Poor table extraction | Mastercard statements are tabular |
| PyMuPDF | Fast, feature-rich | Requires system libraries | Constitution mandates minimal dependencies |
| tabula-py | Excellent tables | Requires Java runtime | Adds significant complexity |
| camelot | Good accuracy | Heavy dependencies (OpenCV) | Over-engineered for simple tables |

### 2. Belgian Number Format Handling

**Decision**: Custom parser using regex + locale-aware conversion

**Rationale**:
- Belgian format: `1.234,56` (period as thousands separator, comma as decimal)
- Python's `locale` module is unreliable across systems
- Simple regex replacement is deterministic and testable

**Implementation Approach**:
```python
def parse_belgian_amount(value: str) -> Decimal:
    """Convert Belgian number format to Decimal."""
    # Remove thousands separator (period)
    # Replace decimal separator (comma) with period
    normalized = value.replace('.', '').replace(',', '.')
    return Decimal(normalized)
```

**Edge Cases Handled**:
- Negative amounts: `-1.234,56` → `-1234.56`
- No thousands separator: `123,45` → `123.45`
- Whole numbers: `1.000` → `1000`

### 3. Rule Matching Strategy

**Decision**: Priority-ordered pattern matching with multiple match types

**Rationale**:
- Counterparty names vary (e.g., "BOL.COM", "BOL. COM", "Bol.com")
- Some vendors need description-based matching (same vendor, different categories)
- First match wins allows explicit priority control

**Pattern Types Supported**:
1. **exact**: Case-insensitive exact match
2. **prefix**: Starts with pattern (e.g., "ACTION*" matches "ACTION 2028")
3. **contains**: Pattern appears anywhere in string
4. **regex**: Full regex support for complex patterns

**Rule Structure** (YAML):
```yaml
rules:
  - pattern: "Sweele B.V."
    pattern_type: contains
    category: "Huur onroerend goed"
    priority: 10

  - pattern: "LCM VP|SOLIDARIS|RIZIV|MUTUALITES"
    pattern_type: regex
    category: "Omzet"
    priority: 20
```

### 4. Data Persistence Format

**Decision**: JSON for transactions, YAML for configuration

**Rationale**:
- **JSON for transactions**: Better handling of large datasets, faster parsing, widely supported
- **YAML for configuration**: Human-readable, supports comments, easier manual editing

**Transaction JSON Schema**:
```json
{
  "version": "1.0",
  "exported_at": "2026-01-02T10:30:00Z",
  "fiscal_year": 2025,
  "transactions": [
    {
      "id": "00012-476",
      "source_file": "BE05 0636 4778 9475 2025-12-05.csv",
      "statement_number": "00012",
      "transaction_number": "476",
      "booking_date": "2025-11-28",
      "value_date": "2025-11-28",
      "amount": -2.50,
      "currency": "EUR",
      "counterparty_name": "Dott bike bill 1 2",
      "counterparty_iban": null,
      "description": "DEBITMASTERCARD-BETALING...",
      "category": "Vervoer",
      "matched_rule": "Dott*",
      "is_therapeutic": false,
      "is_manual_override": false
    }
  ]
}
```

### 5. Mastercard Settlement Exclusion Pattern

**Decision**: Pattern-based exclusion of bank CSV entries

**Rationale**:
- Bank CSV contains monthly Mastercard settlement as single debit
- Mastercard PDFs contain detailed individual transactions
- Must exclude bank settlement to avoid double-counting

**Exclusion Pattern**:
```python
MASTERCARD_SETTLEMENT_PATTERNS = [
    r"MASTERCARD.*AFREKENING",
    r"KREDIETKAART.*AFREKENING",
    r"6287522061",  # Mastercard customer reference from PDF
]
```

### 6. Rule Extraction from Historical Data

**Decision**: Frequency-based pattern mining

**Rationale**:
- 2024/2025 Excel files contain ~500+ categorized transactions each
- Most counterparties appear multiple times with same category
- Extract unique counterparty → category mappings

**Extraction Algorithm**:
1. Load transactions from Excel "Verrichtingen" sheet
2. Group by counterparty name (normalized)
3. For each counterparty with >1 occurrence:
   - If all occurrences have same category → create rule
   - If mixed categories → flag for manual review
4. Output rules sorted by frequency (most common first)

**Expected Output**: ~50-80 rules covering 90%+ of transactions

---

## Enhancement: Maatschap Categorization (2026-01-03)

### 7. Maatschap Transaction Patterns

**Decision**: Description-based categorization with priority over counterparty matching

**Rationale**:
- In a Maatschap (Belgian partnership), the same counterparty can represent different transaction types
- E.g., "Vroedvrouw Goedele Deseyn" may receive profit distribution OR work payment
- Transaction description (Omschrijving field) contains the distinguishing information

**Key Patterns Identified** (from Huis van Meraki data analysis):

| Description Contains | Category | Example |
|---------------------|----------|---------|
| "Inkomstenverdeling" | `winstverdeling` | "Inkomstenverdeling 2025 Maatschap" |
| Q1, Q2, Q3, Q4 (without "Inkomstenverdeling") | `contractors` | "Q3 maatschap" |
| Invoice number patterns (20XXYYZZZ) | `contractors` | "202510001" |
| "Google workspace", "Office 365" | `licenties-software` | "Google workspace 2025" |
| "Verkeerde rekening" | `verkeerde-rekening` | "Verkeerde rekening la royale" |

**Pattern Priority Order**:
1. "Inkomstenverdeling" → winstverdeling (highest priority)
2. "Verkeerde rekening" → verkeerde-rekening
3. Software names → licenties-software
4. Quarter refs (Q1-Q4) or invoice patterns → contractors
5. "Maatschap" alone → fall through to counterparty rules

### 8. Account-Type Configuration

**Decision**: Per-company account configuration with `account_type` flag

**Rationale**:
- Not all accounts require description-based priority
- Standard accounts (eenmanszaak) use counterparty-first matching
- Maatschap accounts need description-first matching

**Configuration Structure** (accounts.yaml):
```yaml
accounts:
  goedele:
    name: "Vroedvrouw Goedele"
    iban: "BE05 0636 4778 9475"
    account_type: standard

  meraki:
    name: "Huis van Meraki"
    iban: "BE98 0689 5286 6793"
    account_type: maatschap
    partners:
      - name: "Vroedvrouw Goedele Deseyn"
        iban: "BE05 0636 4778 9475"
      - name: "HUIS VAN MERAKI - LEILA RCHAIDIA BV"
        iban: "BE27 7370 6541 0173"
```

### 9. Category Distinction: Loon vs Contractors

**Decision**: Use `contractors` for all partner work payments; reserve `loon` for payments to private persons

**Rationale**:
- Belgian tax law distinguishes between:
  - **Loon**: Payments to natural persons (employees, freelancers as individuals)
  - **Contractors/Diensten**: Payments to companies (BVs, VOFs) or independent professionals
- In a Maatschap, partners are typically paid through their BV or as independents → `contractors`
- "Vergoeding-vennoten" rejected as it implies shareholder compensation, not work payment

**Implementation**:
```python
# Description-based rules for Maatschap accounts
MAATSCHAP_DESCRIPTION_RULES = [
    {"pattern": r"inkomstenverdeling", "category": "winstverdeling", "priority": 100},
    {"pattern": r"verkeerde\s*rekening", "category": "verkeerde-rekening", "priority": 90},
    {"pattern": r"google\s*workspace|office\s*365", "category": "licenties-software", "priority": 80},
    {"pattern": r"Q[1-4]\s+maatschap|20\d{7}", "category": "contractors", "priority": 70},
]
```

### 10. Categorizer Algorithm Update

**Decision**: Two-phase matching for Maatschap accounts

**Algorithm**:
```
For each transaction:
  1. Get account config by IBAN
  2. If account_type == "maatschap":
     a. First: Try description-based rules (in priority order)
     b. If match found → return category
     c. If no match → fall through to counterparty rules
  3. If account_type == "standard":
     a. Use counterparty rules only (existing behavior)
  4. Apply counterparty rules (in priority order)
  5. If still no match → mark as uncategorized
```

**Backwards Compatibility**: Standard accounts behave exactly as before.

## Summary

All technical decisions align with constitution principles:
- ✅ **Simplicity**: Pure Python libraries, no external system dependencies
- ✅ **Data Integrity**: Deterministic parsing, full traceability
- ✅ **Transparency**: Rules are human-readable YAML, match logging supported
- ✅ **User Control**: Manual rule editing, override support, account-type configuration

### Maatschap Enhancement Summary
- ✅ **Simplicity**: Reuses existing pattern-matching infrastructure
- ✅ **Data Integrity**: Same traceability for description-based matches
- ✅ **Transparency**: Rule priority is explicit and logged
- ✅ **User Control**: Account-type and partner config is user-editable

No NEEDS CLARIFICATION items remain - proceed to Phase 1.
