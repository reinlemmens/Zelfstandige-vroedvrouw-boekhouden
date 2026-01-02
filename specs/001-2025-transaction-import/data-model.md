# Data Model: 2025 Transaction Import

**Feature**: 001-2025-transaction-import
**Date**: 2026-01-02

## Entity Overview

```
┌─────────────────┐     ┌─────────────────────┐
│  BankStatement  │────▶│    Transaction      │
│     (CSV)       │     │                     │
└─────────────────┘     │  - date             │
                        │  - amount           │
┌─────────────────┐     │  - counterparty     │
│ MastercardStmt  │────▶│  - description      │
│     (PDF)       │     │  - reference        │
└─────────────────┘     │  - type             │
        │               │  - source_file      │
        │               │  - dedup_key        │
        ▼               └─────────────────────┘
┌─────────────────┐              │
│ SettlementLink  │◀─────────────┘
│                 │     (links settlement
│  - pdf_total    │      to detail txns)
│  - bank_entry   │
└─────────────────┘
```

## Entities

### Transaction

The core entity representing a single financial movement.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `date` | date | Booking date of transaction | CSV: Boekingsdatum, PDF: DATUM TRANSACTIE |
| `value_date` | date | Value date (when funds moved) | CSV: Valutadatum, PDF: DATUM VERREKENING |
| `account` | string | Source bank account IBAN | CSV: Rekening |
| `amount` | decimal | Transaction amount (negative=debit) | CSV: Bedrag, PDF: BEDRAG |
| `currency` | string | Currency code (always EUR) | CSV: Devies, PDF: extracted |
| `counterparty_name` | string | Name of other party | CSV: Naam tegenpartij, PDF: OMSCHRIJVING |
| `counterparty_account` | string? | IBAN of other party (if available) | CSV: Rekening tegenpartij |
| `description` | string | Full transaction description | CSV: Mededelingen, PDF: OMSCHRIJVING |
| `reference` | string | Bank reference number | CSV: extracted from Transactie field |
| `transaction_number` | string? | Statement transaction number | CSV: Transactienummer |
| `type` | enum | Transaction type | Derived |
| `source_file` | string | Origin file name | Processing |
| `dedup_key` | string | Unique key for deduplication | Computed |

**Transaction Types**:
- `regular`: Normal transaction
- `settlement`: Mastercard settlement (links to detailed PDF transactions)
- `mastercard_detail`: Individual Mastercard transaction from PDF

**Deduplication Key Format**:
```
{account}|{date:YYYY-MM-DD}|{transaction_number}|{reference_hash}
```

### BankStatement

Represents a parsed CSV file.

| Field | Type | Description |
|-------|------|-------------|
| `file_name` | string | Source file name |
| `account` | string | Bank account IBAN |
| `date_from` | date | Statement start date |
| `date_to` | date | Statement end date |
| `last_balance` | decimal | Closing balance |
| `transactions` | Transaction[] | Extracted transactions |

**CSV Header Mapping**:
| CSV Column | Entity Field |
|------------|--------------|
| Rekening | account |
| Boekingsdatum | date |
| Rekeninguittrekselnummer | (statement metadata) |
| Transactienummer | transaction_number |
| Rekening tegenpartij | counterparty_account |
| Naam tegenpartij bevat | counterparty_name |
| Transactie | description + reference extraction |
| Valutadatum | value_date |
| Bedrag | amount |
| Devies | currency |
| Mededelingen | description (alternate) |

### MastercardStatement

Represents a parsed PDF file.

| Field | Type | Description |
|-------|------|-------------|
| `file_name` | string | Source file name |
| `card_number` | string | Masked card number (5440 56XX XXXX 6159) |
| `cardholder` | string | Cardholder name |
| `period_start` | date | Statement period start |
| `period_end` | date | Statement period end |
| `settlement_date` | date | Date charged to bank account |
| `total_amount` | decimal | Total statement amount |
| `transactions` | Transaction[] | Individual card transactions |

**PDF Field Extraction**:
| PDF Field | Entity Field |
|-----------|--------------|
| Afsluitingsdatum | period_end |
| Datum van debet | settlement_date |
| "Transacties van X tot Y" | period_start, period_end |
| Totaal | total_amount |
| DATUM TRANSACTIE | transaction.date |
| DATUM VERREKENING | transaction.value_date |
| OMSCHRIJVING | transaction.description |
| BEDRAG | transaction.amount |

### SettlementLink

Links a bank settlement entry to its Mastercard statement details.

| Field | Type | Description |
|-------|------|-------------|
| `bank_transaction` | Transaction | The settlement entry from bank CSV |
| `mastercard_statement` | MastercardStatement | The linked PDF statement |
| `amount_match` | boolean | Whether amounts match exactly |
| `date_match` | boolean | Whether dates match (±1 day tolerance) |
| `discrepancy` | decimal? | Amount difference if any |

## Validation Rules

### Transaction Validation
- `date` must be valid date
- `amount` must be non-null decimal
- `account` must match pattern `BE\d{2} \d{4} \d{4} \d{4}`
- `type` must be one of: regular, settlement, mastercard_detail
- `source_file` must be non-empty

### Deduplication Rules
1. Exact key match → duplicate, keep first occurrence
2. Same account + date + amount + counterparty → potential duplicate, verify by reference
3. Settlement entries → never deduplicate against detail entries

### Settlement Matching Rules
1. Bank entry must contain card number pattern OR "MASTERCARD" keyword
2. Settlement amount must match PDF total (±0.01 EUR tolerance for rounding)
3. Bank booking date must be within ±1 day of PDF settlement date
4. One bank entry links to exactly one PDF statement

## State Transitions

Transactions don't have complex state, but processing has phases:

```
[Raw Data] → [Parsed] → [Deduplicated] → [Linked] → [Output]
     ↓           ↓            ↓             ↓          ↓
   CSV/PDF   Transaction   Unique txns   Settlements  Google
   files     objects       only          connected    Sheet
```

## Output Schema (Google Sheet)

Single sheet with columns:

| Column | Type | Example |
|--------|------|---------|
| A: Date | Date | 2025-03-15 |
| B: Account | Text | BE05 0636 4778 9475 |
| C: Amount | Number | -125.50 |
| D: Counterparty | Text | NMBS SNCB |
| E: Description | Text | Train ticket Brussels-Leuven |
| F: Reference | Text | REF. : 0509542610853 |
| G: Type | Text | regular |
| H: Source File | Text | BE05 0636...2025-12-05.csv |

**Sorting**: By Date (ascending), then by Account
**Filtering**: Only transactions where Date is between 2025-01-01 and 2025-12-31
