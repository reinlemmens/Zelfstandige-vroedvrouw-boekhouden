# Research: Session State Export/Import

**Feature**: 010-session-state-export
**Phase**: 0 (Research)
**Date**: 2026-01-05

## Current Session State Structure

The Streamlit app (`streamlit_app.py`) uses `st.session_state` to store the following:

### Tracked State Variables (lines 184-206)

| Variable | Type | Description | Serializable |
|----------|------|-------------|--------------|
| `transactions` | `List[Transaction]` | Imported financial transactions | Yes (via `to_dict`) |
| `existing_ids` | `Set[str]` | Transaction IDs for duplicate detection | Yes (convert to list) |
| `fiscal_year` | `int` | Selected fiscal year (2024, 2025, etc.) | Yes |
| `categorization_done` | `bool` | Whether auto-categorization has been run | Yes |
| `import_stats` | `dict` | Statistics from last import (imported, skipped, excluded, errors) | Yes |
| `categories` | `List[Category]` | Loaded category definitions | Yes (via `to_dict`) |
| `rules` | `List[CategoryRule]` | Loaded categorization rules | Yes (via `to_dict`) |

### State NOT Currently Tracked (needs addition)

| Variable | Type | Description | Purpose |
|----------|------|-------------|---------|
| `custom_rules_loaded` | `bool` | True if user uploaded rules.yaml | Know whether to include rules.yaml in export |
| `custom_categories_loaded` | `bool` | True if user uploaded categories.yaml | Know whether to include categories.yaml in export |
| `uploaded_files_content` | `Dict[str, bytes]` | Original file content keyed by filename | Enable source file inclusion in export |
| `company_name` | `str` | User-entered company name | For export filename and metadata |

## Model Serialization Analysis

### Transaction Model (`src/models/transaction.py`)

**Serialization**: Has `to_dict()` and `from_dict()` methods.

```python
def to_dict(self) -> dict:
    return {
        'id': self.id,
        'source_file': self.source_file,
        'source_type': self.source_type,
        'statement_number': self.statement_number,
        'transaction_number': self.transaction_number,
        'booking_date': self.booking_date.isoformat(),  # date -> str
        'value_date': self.value_date.isoformat(),      # date -> str
        'amount': str(self.amount),                      # Decimal -> str
        'currency': self.currency,
        # ... all 20+ fields
    }

@classmethod
def from_dict(cls, data: dict) -> 'Transaction':
    return cls(
        booking_date=date.fromisoformat(data['booking_date']),  # str -> date
        amount=Decimal(data['amount']),                          # str -> Decimal
        # ... handles all fields with defaults
    )
```

**Notes**:
- Dates serialized as ISO 8601 strings
- Decimals serialized as strings (preserves precision)
- All 23 fields are covered
- `from_dict` handles missing optional fields with defaults

### Category Model (`src/models/category.py`)

**Serialization**: Has `to_dict()` and `from_dict()` methods.

```python
def to_dict(self) -> dict:
    result = {
        'id': self.id,
        'name': self.name,
        'type': self.type,
        'tax_deductible': self.tax_deductible,
    }
    if self.description:
        result['description'] = self.description
    return result
```

**Issue**: `deductibility_pct` is NOT included in `to_dict()` output but IS read in `from_dict()`.

**Fix Required**: Update `Category.to_dict()` to include `deductibility_pct`:
```python
if self.deductibility_pct != 100:
    result['deductibility_pct'] = self.deductibility_pct
```

### CategoryRule Model (`src/models/rule.py`)

**Serialization**: Has `to_dict()` and `from_dict()` methods.

```python
def to_dict(self) -> dict:
    result = {
        'id': self.id,
        'pattern': self.pattern,
        'pattern_type': self.pattern_type,
        'match_field': self.match_field,
        'target_category': self.target_category,
        'priority': self.priority,
        'enabled': self.enabled,
        'source': self.source,
    }
    if self.is_therapeutic is not None:
        result['is_therapeutic'] = self.is_therapeutic
    if self.notes:
        result['notes'] = self.notes
    return result
```

**Notes**:
- All fields covered
- Optional fields only included when set
- `_compiled_pattern` correctly excluded (not serializable)

## Source File Tracking

### Current Behavior

When files are uploaded via `st.file_uploader`, the content is processed immediately and transactions are extracted. The original file content is **NOT** preserved after processing.

**Location**: `process_uploaded_files()` function (line 909)
```python
for uploaded_file in uploaded_files:
    filename = uploaded_file.name
    file_content = uploaded_file.read()  # Read once, used for import
    # ... processing ...
    # file_content is NOT stored
```

### Required Changes

To support source file inclusion in exports, need to:
1. Add `uploaded_files_content: Dict[str, bytes]` to session state
2. Store content after successful import
3. Provide checkbox UI for inclusion in export

## Configuration Upload Tracking

### Current Behavior (lines 394-424)

When custom configuration files are uploaded:
- Content is parsed into `Category` or `CategoryRule` objects
- Objects replace the default lists in session state
- **No flag is set** to indicate custom config was loaded

```python
if rules_file is not None:
    rules_content = rules_file.read()
    parsed_rules = parse_rules_yaml(rules_content)
    if parsed_rules and parsed_rules != st.session_state.rules:
        st.session_state.rules = parsed_rules  # Replaces defaults
        # NO FLAG SET - can't distinguish custom from default
```

### Required Changes

Add tracking for custom config:
```python
if rules_file is not None:
    rules_content = rules_file.read()
    parsed_rules = parse_rules_yaml(rules_content)
    if parsed_rules:
        st.session_state.rules = parsed_rules
        st.session_state.custom_rules_loaded = True
        st.session_state.custom_rules_content = rules_content  # For export
```

## Serialization Strategy

### state.json Schema

```json
{
  "version": "1.0",
  "company_name": "goedele",
  "fiscal_year": 2025,
  "exported_at": "2026-01-05T10:30:00+00:00",
  "transactions": [
    { /* Transaction.to_dict() output */ }
  ],
  "existing_ids": ["id1", "id2"],
  "categorization_done": true,
  "import_stats": {
    "imported": 150,
    "skipped": 3,
    "excluded": 5,
    "errors": []
  },
  "custom_rules_loaded": false,
  "custom_categories_loaded": false
}
```

### Conversion Functions Needed

```python
def session_to_dict(session_state) -> dict:
    """Convert session state to serializable dictionary."""
    return {
        'version': '1.0',
        'company_name': session_state.get('company_name', 'sessie'),
        'fiscal_year': session_state.fiscal_year,
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'transactions': [tx.to_dict() for tx in session_state.transactions],
        'existing_ids': list(session_state.existing_ids),
        'categorization_done': session_state.categorization_done,
        'import_stats': session_state.import_stats,
        'custom_rules_loaded': session_state.get('custom_rules_loaded', False),
        'custom_categories_loaded': session_state.get('custom_categories_loaded', False),
    }

def dict_to_session(data: dict) -> dict:
    """Convert dictionary to session state values."""
    return {
        'company_name': data.get('company_name', 'sessie'),
        'fiscal_year': data['fiscal_year'],
        'transactions': [Transaction.from_dict(tx) for tx in data['transactions']],
        'existing_ids': set(data['existing_ids']),
        'categorization_done': data.get('categorization_done', False),
        'import_stats': data.get('import_stats'),
        'custom_rules_loaded': data.get('custom_rules_loaded', False),
        'custom_categories_loaded': data.get('custom_categories_loaded', False),
    }
```

## ZIP Archive Structure

```
plv-goedele-2025.zip
├── state.json              # Always included
├── rules.yaml              # Only if custom_rules_loaded
├── categories.yaml         # Only if custom_categories_loaded
└── source_files/           # Only if checkbox checked
    ├── bankafschrift_jan.csv
    ├── bankafschrift_feb.csv
    └── mastercard_jan.pdf
```

## Version Migration Strategy

### Current Version: 1.0

Fields:
- version, company_name, fiscal_year, exported_at
- transactions, existing_ids, categorization_done, import_stats
- custom_rules_loaded, custom_categories_loaded

### Future Migration Example (1.0 -> 1.1)

```python
def migrate_1_0_to_1_1(data: dict) -> dict:
    """Add new_field introduced in 1.1."""
    data['new_field'] = 'default_value'
    data['version'] = '1.1'
    return data

MIGRATIONS = {
    '1.0': migrate_1_0_to_1_1,
    # Future: '1.1': migrate_1_1_to_1_2,
}

def apply_migrations(data: dict, current_version: str) -> dict:
    """Apply sequential migrations from data version to current."""
    data_version = data.get('version', '1.0')
    while data_version != current_version:
        if data_version not in MIGRATIONS:
            raise ValueError(f"No migration path from {data_version}")
        data = MIGRATIONS[data_version](data)
        data_version = data['version']
    return data
```

## Implementation Risks

### Risk 1: Large Session Export

**Risk**: Sessions with 500+ transactions may produce large JSON files.

**Mitigation**:
- ZIP compression reduces size significantly
- Typical JSON for 500 transactions: ~500KB uncompressed -> ~50KB compressed
- NFR-002 specifies <1MB target

### Risk 2: Browser Memory

**Risk**: Storing source file content in session state increases memory usage.

**Mitigation**:
- Source files are optional (checkbox)
- Typical monthly CSV: 10-50KB
- Typical PDF statement: 100-500KB
- Total for year: ~2-5MB (acceptable for modern browsers)

### Risk 3: Category.to_dict() Bug

**Risk**: `deductibility_pct` not serialized, will lose partial deductibility info.

**Fix**: Update `Category.to_dict()` before implementing export:
```python
# Add to to_dict():
if self.deductibility_pct != 100:
    result['deductibility_pct'] = self.deductibility_pct
```

## Recommendations

1. **Fix Category.to_dict()** first - add `deductibility_pct` to output
2. **Add session state tracking** for custom config and source files
3. **Create service module** `src/services/session_export.py` for export/import logic
4. **Write comprehensive tests** for serialization round-trips
5. **UI changes in sidebar** after core logic is tested
