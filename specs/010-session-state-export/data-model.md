# Data Model: Session State Export/Import

**Feature**: 010-session-state-export
**Phase**: 1 (Design)
**Date**: 2026-01-05

## StateFile JSON Schema (v1.0)

The `state.json` file is the core of the session export. It contains all session data needed to restore a user's work.

### Root Schema

```json
{
  "version": "1.0",
  "company_name": "string",
  "fiscal_year": 2025,
  "exported_at": "2026-01-05T10:30:00+00:00",
  "transactions": [],
  "existing_ids": [],
  "categorization_done": false,
  "import_stats": {},
  "custom_rules_loaded": false,
  "custom_categories_loaded": false
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Schema version for migration support. Current: "1.0" |
| `company_name` | string | Yes | User-entered company name (used in filename) |
| `fiscal_year` | integer | Yes | Selected fiscal year (e.g., 2024, 2025) |
| `exported_at` | string (ISO 8601) | Yes | Timestamp when export was created |
| `transactions` | array | Yes | List of Transaction objects (see below) |
| `existing_ids` | array | Yes | List of transaction IDs for duplicate detection |
| `categorization_done` | boolean | Yes | Whether auto-categorization has been run |
| `import_stats` | object | No | Statistics from last file import |
| `custom_rules_loaded` | boolean | Yes | True if custom rules.yaml was uploaded |
| `custom_categories_loaded` | boolean | Yes | True if custom categories.yaml was uploaded |

### Transaction Object Schema

Each transaction in the `transactions` array follows this schema:

```json
{
  "id": "00012-001",
  "source_file": "bankafschrift_jan.csv",
  "source_type": "bank_csv",
  "statement_number": "00012",
  "transaction_number": "001",
  "booking_date": "2025-01-15",
  "value_date": "2025-01-15",
  "amount": "-125.50",
  "currency": "EUR",
  "counterparty_name": "PROXIMUS NV",
  "counterparty_iban": "BE12345678901234",
  "counterparty_street": null,
  "counterparty_postal_city": null,
  "counterparty_bic": null,
  "counterparty_country": null,
  "own_account": "BE98765432109876",
  "communication": "Factuur 2025-001",
  "description": "DOMICILIERING PROXIMUS",
  "category": "telefonie",
  "matched_rule_id": "proximus-tel",
  "is_therapeutic": false,
  "is_manual_override": false,
  "is_excluded": false,
  "exclusion_reason": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier: `{statement_number}-{transaction_number}` |
| `source_file` | string | Yes | Original filename for audit trail |
| `source_type` | string | Yes | `"bank_csv"` or `"mastercard_pdf"` |
| `statement_number` | string | Yes | Bank statement number |
| `transaction_number` | string | Yes | Sequence within statement |
| `booking_date` | string | Yes | ISO 8601 date (YYYY-MM-DD) |
| `value_date` | string | Yes | ISO 8601 date (YYYY-MM-DD) |
| `amount` | string | Yes | Decimal as string (negative = expense) |
| `currency` | string | Yes | Always "EUR" |
| `counterparty_name` | string | No | Name of other party |
| `counterparty_iban` | string | No | IBAN of other party |
| `counterparty_street` | string | No | Street address |
| `counterparty_postal_city` | string | No | Postal code and city |
| `counterparty_bic` | string | No | BIC/SWIFT code |
| `counterparty_country` | string | No | Country code |
| `own_account` | string | No | Own account number |
| `communication` | string | No | Payment communication/reference |
| `description` | string | No | Full transaction description |
| `category` | string | No | Assigned category ID (null if uncategorized) |
| `matched_rule_id` | string | No | ID of rule that assigned category |
| `is_therapeutic` | boolean | Yes | True for direct patient care revenue |
| `is_manual_override` | boolean | Yes | True if manually categorized |
| `is_excluded` | boolean | Yes | True if excluded from P&L |
| `exclusion_reason` | string | No | Reason for exclusion |

### ImportStats Object Schema

```json
{
  "imported": 150,
  "skipped": 3,
  "excluded": 5,
  "errors": [
    {
      "file": "corrupted.csv",
      "message": "Invalid CSV format"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `imported` | integer | Number of transactions successfully imported |
| `skipped` | integer | Number of duplicate transactions skipped |
| `excluded` | integer | Number of transactions excluded (e.g., Mastercard settlements) |
| `errors` | array | List of error objects with `file` and `message` fields |

## ZIP Archive Structure

The exported ZIP file contains:

```
plv-{company_name}-{fiscal_year}.zip
├── state.json                  # Required: session state
├── rules.yaml                  # Optional: if custom_rules_loaded == true
├── categories.yaml             # Optional: if custom_categories_loaded == true
└── source_files/               # Optional: if user checked "Bronbestanden toevoegen"
    ├── bankafschrift_jan.csv
    ├── bankafschrift_feb.csv
    └── mastercard_jan.pdf
```

### Filename Sanitization

Company name is sanitized for use in filename:
- Converted to lowercase
- Spaces replaced with hyphens
- Non-alphanumeric characters removed
- Default: "sessie" if empty

Examples:
- "Vroedvrouw Goedele" → `plv-vroedvrouw-goedele-2025.zip`
- "Mijn Praktijk 123" → `plv-mijn-praktijk-123-2025.zip`
- "" (empty) → `plv-sessie-2025.zip`

## Version Migration

### Schema Versioning

The `version` field uses semantic versioning (MAJOR.MINOR):
- **MAJOR**: Breaking changes requiring user action
- **MINOR**: Backward-compatible additions

### Migration Process

1. Read `state.json` from ZIP
2. Check `version` field
3. If older than current, show info message: "Sessiebestand wordt geüpgraded van v{old} naar v{new}"
4. Apply sequential migrations
5. Continue with import

### Example Migration (1.0 → 1.1)

```python
# Future migration example
def migrate_1_0_to_1_1(data: dict) -> dict:
    """Add hypothetical new field in v1.1."""
    # Add new optional field with default
    data['new_optional_field'] = []
    data['version'] = '1.1'
    return data
```

## Validation Rules

### On Import

1. **ZIP Validation**
   - File must be a valid ZIP archive
   - Error: "Upload een .zip bestand"

2. **state.json Presence**
   - ZIP must contain `state.json` at root
   - Error: "Ongeldig sessiebestand: state.json niet gevonden"

3. **JSON Validity**
   - `state.json` must be valid JSON
   - Error: "Ongeldig sessiebestand: corrupte data"

4. **Schema Validation**
   - Required fields must be present
   - Types must match schema
   - Error: "Ongeldig sessiebestand: [specific field] ontbreekt"

5. **Version Check**
   - Version must be migratable to current
   - Error: "Sessiebestand versie {v} wordt niet ondersteund"

### On Export

1. **Transactions Present**
   - At least one transaction must exist
   - Button disabled if no transactions

2. **Company Name**
   - If empty, use "sessie" as default
   - Sanitize for filename use

## Session State Changes

### New State Variables

Add to `init_session_state()`:

```python
if 'company_name' not in st.session_state:
    st.session_state.company_name = ''

if 'custom_rules_loaded' not in st.session_state:
    st.session_state.custom_rules_loaded = False

if 'custom_categories_loaded' not in st.session_state:
    st.session_state.custom_categories_loaded = False

if 'uploaded_files_content' not in st.session_state:
    st.session_state.uploaded_files_content = {}
```

### Update on Config Upload

```python
# In rules upload handler:
st.session_state.custom_rules_loaded = True
st.session_state.custom_rules_content = rules_content

# In categories upload handler:
st.session_state.custom_categories_loaded = True
st.session_state.custom_categories_content = categories_content
```

### Update on File Import

```python
# In process_uploaded_files():
st.session_state.uploaded_files_content[filename] = file_content
```

## Model Fix Required

The `Category.to_dict()` method is missing `deductibility_pct`. This must be fixed before implementing export:

```python
# In src/models/category.py
def to_dict(self) -> dict:
    result = {
        'id': self.id,
        'name': self.name,
        'type': self.type,
        'tax_deductible': self.tax_deductible,
    }
    if self.deductibility_pct != 100:  # ADD THIS
        result['deductibility_pct'] = self.deductibility_pct
    if self.description:
        result['description'] = self.description
    return result
```

## Example Complete Export

### state.json

```json
{
  "version": "1.0",
  "company_name": "Vroedvrouw Goedele",
  "fiscal_year": 2025,
  "exported_at": "2026-01-05T14:30:00+01:00",
  "transactions": [
    {
      "id": "00001-001",
      "source_file": "belfius_jan_2025.csv",
      "source_type": "bank_csv",
      "statement_number": "00001",
      "transaction_number": "001",
      "booking_date": "2025-01-02",
      "value_date": "2025-01-02",
      "amount": "1250.00",
      "currency": "EUR",
      "counterparty_name": "RIZIV-INAMI",
      "counterparty_iban": null,
      "description": "TERUGBETALING RIZIV",
      "category": "omzet",
      "matched_rule_id": "riziv-niv",
      "is_therapeutic": true,
      "is_manual_override": false,
      "is_excluded": false,
      "exclusion_reason": null
    },
    {
      "id": "00001-002",
      "source_file": "belfius_jan_2025.csv",
      "source_type": "bank_csv",
      "statement_number": "00001",
      "transaction_number": "002",
      "booking_date": "2025-01-05",
      "value_date": "2025-01-05",
      "amount": "-45.99",
      "currency": "EUR",
      "counterparty_name": "PROXIMUS NV",
      "counterparty_iban": "BE12345678901234",
      "description": "DOMICILIERING PROXIMUS",
      "category": "telefonie",
      "matched_rule_id": "proximus",
      "is_therapeutic": false,
      "is_manual_override": false,
      "is_excluded": false,
      "exclusion_reason": null
    }
  ],
  "existing_ids": ["00001-001", "00001-002"],
  "categorization_done": true,
  "import_stats": {
    "imported": 2,
    "skipped": 0,
    "excluded": 0,
    "errors": []
  },
  "custom_rules_loaded": false,
  "custom_categories_loaded": false
}
```
