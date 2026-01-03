# Data Model: Transaction Categorization

**Feature**: 002-transaction-categorization
**Date**: 2026-01-02
**Updated**: 2026-01-03 (Maatschap Enhancement)

## Entities

### Transaction

Represents a single financial movement from bank statement or credit card.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique identifier: `{statement_number}-{transaction_number}` |
| source_file | string | Yes | Original file name (for audit trail) |
| source_type | enum | Yes | `bank_csv` or `mastercard_pdf` |
| statement_number | string | Yes | Bank statement number (e.g., "00012") |
| transaction_number | string | Yes | Transaction sequence within statement |
| booking_date | date | Yes | Date transaction was booked |
| value_date | date | Yes | Date transaction was valued |
| amount | decimal | Yes | Transaction amount (negative = expense, positive = income) |
| currency | string | Yes | Always "EUR" |
| counterparty_name | string | No | Name of other party (may be null for fees) |
| counterparty_iban | string | No | IBAN of other party (when available) |
| description | string | No | Full transaction description/communication |
| category | string | No | Assigned category (null = uncategorized) |
| matched_rule_id | string | No | ID of rule that assigned category (null if manual) |
| is_therapeutic | boolean | Yes | True if revenue from direct patient care |
| is_manual_override | boolean | Yes | True if category was manually assigned |
| is_excluded | boolean | Yes | True if excluded (e.g., Mastercard settlement) |
| exclusion_reason | string | No | Reason for exclusion |

**Uniqueness**: `(statement_number, transaction_number)` within same `source_type`

**Validation Rules**:
- `amount` must not be zero
- `currency` must be "EUR"
- `booking_date` must be within fiscal year
- `is_therapeutic` only valid when `category` = "Omzet"

### Category

Predefined expense/income category for Belgian tax filing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique identifier (slug form, e.g., "huur-onroerend-goed") |
| name | string | Yes | Display name (Dutch, e.g., "Huur onroerend goed") |
| type | enum | Yes | `income` or `expense` |
| tax_deductible | boolean | Yes | Whether expense is tax-deductible |
| description | string | No | Help text for user |

**Predefined Categories** (28 total):

| ID | Name | Type | Notes |
|----|------|------|-------|
| omzet | Omzet | income | |
| admin-kosten | Admin kosten | expense | |
| bankkosten | Bankkosten | expense | |
| boeken-en-tijdschriften | Boeken en tijdschriften | expense | |
| bureelbenodigdheden | Bureelbenodigdheden | expense | |
| contractors | Contractors | expense | Payments for work to companies/independent entities (incl. Maatschap partners) |
| drukwerk-en-publiciteit | Drukwerk en publiciteit | expense | |
| huur-onroerend-goed | Huur onroerend goed | expense | |
| interne-storting | Interne storting | expense | |
| investeringen-over-3-jaar | Investeringen over 3 jaar | expense | |
| klein-materiaal | Klein materiaal | expense | |
| kosten-opleiding-en-vorming | Kosten opleiding en vorming | expense | |
| licenties-software | Licenties software | expense | |
| loon | Loon | expense | Payments to private persons only |
| maatschap-huis-van-meraki | Maatschap Huis van Meraki | expense | |
| medisch-materiaal | Medisch materiaal | expense | |
| onthaal | Onthaal | expense | |
| relatiegeschenken | Relatiegeschenken | expense | |
| restaurant | Restaurant | expense | |
| sociale-bijdragen | Sociale bijdragen | expense | |
| telefonie | Telefonie | expense | |
| verkeerde-rekening | Verkeerde rekening | expense | |
| verzekering-beroepsaansprakelijkheid | Verzekering beroepsaansprakelijkheid | expense | |
| vapz | Vrij Aanvullend Pensioen Zelfstandigen | expense | |
| vervoer | Vervoer | expense | |
| mastercard | Mastercard | expense | |
| sponsoring | Sponsoring | expense | |
| winstverdeling | Winstverdeling | expense | Profit distribution to Maatschap partners |

### CategoryRule

Pattern-matching rule for automatic categorization.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique identifier (auto-generated or user-defined) |
| pattern | string | Yes | Match pattern (text or regex) |
| pattern_type | enum | Yes | `exact`, `prefix`, `contains`, `regex` |
| match_field | enum | Yes | `counterparty_name`, `description`, `counterparty_iban` |
| target_category | string | Yes | Category ID to assign on match |
| priority | integer | Yes | Lower = higher priority (first match wins) |
| is_therapeutic | boolean | No | If true, also set `is_therapeutic` flag on match |
| enabled | boolean | Yes | Whether rule is active |
| source | enum | Yes | `extracted` (from Excel) or `manual` |
| notes | string | No | User notes about this rule |

**Validation Rules**:
- `target_category` must reference valid Category
- `pattern` must be valid regex when `pattern_type` = "regex"
- `priority` must be unique within enabled rules

### ImportSession

Tracks a batch import operation for audit purposes.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | UUID |
| timestamp | datetime | Yes | When import was run |
| source_files | list[string] | Yes | Files processed in this session |
| transactions_imported | integer | Yes | Count of new transactions |
| transactions_skipped | integer | Yes | Count of duplicates skipped |
| transactions_excluded | integer | Yes | Count of excluded (e.g., MC settlements) |
| errors | list[ImportError] | No | Any errors encountered |

### ImportError

Records an error during import.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | string | Yes | Source file name |
| line | integer | No | Line number (for CSV) |
| message | string | Yes | Error description |
| raw_data | string | No | Original data that caused error |

### Account

Configuration for a bank account, including Maatschap-specific settings.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique identifier (slug form, e.g., "goedele", "meraki") |
| name | string | Yes | Display name (e.g., "Vroedvrouw Goedele") |
| iban | string | Yes | IBAN (e.g., "BE05 0636 4778 9475") |
| account_type | enum | Yes | `standard` or `maatschap` |
| partners | list[Partner] | No | Partner list (required for Maatschap accounts) |

**Validation Rules**:
- `account_type` must be "standard" or "maatschap"
- If `account_type` = "maatschap", `partners` must have at least 2 entries
- `iban` must be a valid Belgian IBAN format

### Partner

Represents a partner in a Maatschap.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Partner name (individual or BV) |
| iban | string | Yes | Partner's bank account IBAN |

**Notes**:
- Partners may be individuals (e.g., "Vroedvrouw Goedele Deseyn") or BVs (e.g., "HUIS VAN MERAKI - LEILA RCHAIDIA BV")
- Partner IBAN is used to identify incoming/outgoing payments between Maatschap and partners

## Relationships

```
Transaction
    └── Category (many-to-one, via category field)
    └── CategoryRule (many-to-one, via matched_rule_id, nullable)
    └── Account (many-to-one, via source IBAN matching)

CategoryRule
    └── Category (many-to-one, via target_category)

Account
    └── Partner (one-to-many, for Maatschap accounts)
```

## State Transitions

### Transaction Lifecycle

```
[New] → [Imported] → [Categorized] → [Reviewed]
                  ↘                  ↗
                    [Uncategorized] → [Manually Assigned]
```

| State | Conditions |
|-------|------------|
| Imported | `category` is null, `is_manual_override` = false |
| Categorized | `category` is set, `matched_rule_id` is set |
| Uncategorized | `category` is null after all rules applied |
| Manually Assigned | `category` is set, `is_manual_override` = true |
| Reviewed | (implicit) User has verified categorization |

### Transaction Exclusion

```
[Imported] → [Excluded]
```

Transactions matching Mastercard settlement patterns are marked `is_excluded` = true with `exclusion_reason` and are not processed further.

## Data Volume Assumptions

| Entity | Expected Volume | Growth Rate |
|--------|-----------------|-------------|
| Transaction | 500-1000/year | +10%/year |
| Category | 28 (fixed) | Rarely changes |
| CategoryRule | 50-100 | +5-10/year |
| ImportSession | 10-20/year | Stable |
| Account | 2-5 | Rarely changes |
| Partner | 2-4 per Maatschap | Rarely changes |

## File Formats

### transactions.json

```json
{
  "version": "1.0",
  "fiscal_year": 2025,
  "exported_at": "2026-01-02T10:30:00Z",
  "transactions": [ /* Transaction objects */ ],
  "import_sessions": [ /* ImportSession objects */ ]
}
```

### rules.yaml

```yaml
version: "1.0"
rules:
  - id: rule-001
    pattern: "Sweele B.V."
    pattern_type: contains
    match_field: counterparty_name
    target_category: huur-onroerend-goed
    priority: 10
    enabled: true
    source: extracted
```

### categories.yaml

```yaml
version: "1.0"
categories:
  - id: omzet
    name: Omzet
    type: income
    tax_deductible: false
  - id: huur-onroerend-goed
    name: Huur onroerend goed
    type: expense
    tax_deductible: true
```

### accounts.yaml

```yaml
version: "1.0"
accounts:
  - id: goedele
    name: "Vroedvrouw Goedele"
    iban: "BE05 0636 4778 9475"
    account_type: standard

  - id: meraki
    name: "Huis van Meraki"
    iban: "BE98 0689 5286 6793"
    account_type: maatschap
    partners:
      - name: "Vroedvrouw Goedele Deseyn"
        iban: "BE05 0636 4778 9475"
      - name: "HUIS VAN MERAKI - LEILA RCHAIDIA BV"
        iban: "BE27 7370 6541 0173"
```

## Categorization Algorithm

### Standard Account Flow

```
For each transaction:
  1. Load rules sorted by priority (lower = higher priority)
  2. For each rule where match_field = "counterparty_name":
     - Apply pattern match to counterparty_name
     - If match found → assign category, record matched_rule_id
  3. If no match → mark as uncategorized
```

### Maatschap Account Flow

```
For each transaction from Maatschap account:
  1. Load description rules sorted by priority
  2. For each rule where match_field = "description":
     - Apply pattern match to description
     - If match found → assign category, record matched_rule_id, return
  3. If no description match → fall through to counterparty rules
  4. For each rule where match_field = "counterparty_name":
     - Apply pattern match to counterparty_name
     - If match found → assign category, record matched_rule_id
  5. If no match → mark as uncategorized
```

### Description Rule Priority (Maatschap)

| Priority | Pattern | Category |
|----------|---------|----------|
| 100 | `inkomstenverdeling` | winstverdeling |
| 90 | `verkeerde\s*rekening` | verkeerde-rekening |
| 80 | `google\s*workspace\|office\s*365` | licenties-software |
| 70 | `Q[1-4]\s+maatschap\|20\d{7}` | contractors |
