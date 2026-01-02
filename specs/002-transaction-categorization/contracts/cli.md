# CLI Contract: Transaction Categorization

**Feature**: 002-transaction-categorization
**Date**: 2026-01-02

## Overview

Command-line interface for importing, categorizing, and managing financial transactions.

**Entry Point**: `python -m src.cli.main` or installed as `plv` command

## Commands

### `import` - Import Transactions

Import transactions from bank CSV files and/or Mastercard PDF statements.

```bash
plv import <files...> [options]
```

**Arguments**:
| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| files | path(s) | Yes | One or more CSV or PDF files to import |

**Options**:
| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| --year | -y | int | current | Fiscal year for imported transactions |
| --dry-run | -n | flag | false | Preview import without saving |
| --force | -f | flag | false | Re-import even if duplicates exist |

**Output** (JSON when `--json` flag used):
```json
{
  "imported": 45,
  "skipped_duplicates": 3,
  "excluded": 1,
  "errors": []
}
```

**Exit Codes**:
| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Partial failure (some files had errors) |
| 2 | Complete failure (no files imported) |

**Examples**:
```bash
# Import single bank CSV
plv import data/2025/bank-statement-dec.csv

# Import multiple files
plv import data/2025/*.csv data/2025/mastercard/*.pdf

# Dry run to preview
plv import data/2025/bank.csv --dry-run
```

---

### `categorize` - Apply Categorization Rules

Run automatic categorization on all uncategorized transactions.

```bash
plv categorize [options]
```

**Options**:
| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| --year | -y | int | current | Fiscal year to process |
| --all | -a | flag | false | Re-categorize all (including already categorized) |
| --dry-run | -n | flag | false | Preview categorization without saving |

**Output**:
```json
{
  "categorized": 42,
  "uncategorized": 5,
  "rules_applied": {
    "rule-001": 15,
    "rule-002": 12,
    "rule-003": 8
  }
}
```

**Exit Codes**:
| Code | Meaning |
|------|---------|
| 0 | All transactions categorized |
| 1 | Some transactions remain uncategorized |

**Examples**:
```bash
# Categorize current year
plv categorize

# Re-categorize all for 2024
plv categorize --year 2024 --all
```

---

### `list` - List Transactions

Display transactions with optional filtering.

```bash
plv list [options]
```

**Options**:
| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| --year | -y | int | current | Fiscal year |
| --category | -c | string | all | Filter by category |
| --uncategorized | -u | flag | false | Show only uncategorized |
| --therapeutic | -t | flag | false | Show only therapeutic |
| --from | | date | year start | Start date (YYYY-MM-DD) |
| --to | | date | year end | End date (YYYY-MM-DD) |
| --format | -o | enum | table | Output format: table, json, csv |
| --limit | -l | int | 50 | Max rows to display |

**Output** (table format):
```
ID          Date        Amount     Category              Counterparty
00012-476   2025-11-28  -2.50      Vervoer               Dott bike bill
00012-477   2025-11-28  -45.00     Huur onroerend goed   Sweele B.V.
00012-478   2025-11-29  +150.00    Omzet                 LCM VP
...
Total: 127 transactions | Showing 1-50
```

**Examples**:
```bash
# List uncategorized
plv list --uncategorized

# Export to CSV
plv list --year 2025 --format csv > transactions.csv

# Filter by category
plv list --category omzet --therapeutic
```

---

### `assign` - Manually Assign Category

Manually assign or override a transaction's category.

```bash
plv assign <transaction-id> <category> [options]
```

**Arguments**:
| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| transaction-id | string | Yes | Transaction ID (e.g., "00012-476") |
| category | string | Yes | Category ID (e.g., "vervoer") |

**Options**:
| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| --therapeutic | -t | flag | false | Mark as therapeutic (only for omzet) |
| --note | | string | | Add note explaining override |

**Exit Codes**:
| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Transaction not found |
| 2 | Invalid category |

**Examples**:
```bash
# Assign category
plv assign 00012-476 vervoer

# Mark revenue as therapeutic
plv assign 00012-478 omzet --therapeutic

# Override with note
plv assign 00012-477 klein-materiaal --note "Misclassified by rule"
```

---

### `rules` - Manage Categorization Rules

List, add, or modify categorization rules.

```bash
plv rules <subcommand> [options]
```

**Subcommands**:

#### `rules list`
```bash
plv rules list [--category <cat>] [--format table|json|yaml]
```

#### `rules add`
```bash
plv rules add --pattern <pattern> --category <category> [options]
```

| Option | Short | Type | Required | Description |
|--------|-------|------|----------|-------------|
| --pattern | -p | string | Yes | Match pattern |
| --category | -c | string | Yes | Target category ID |
| --type | -t | enum | No | Pattern type: exact, prefix, contains, regex (default: contains) |
| --field | -f | enum | No | Match field: counterparty_name, description, counterparty_iban (default: counterparty_name) |
| --priority | | int | No | Priority (lower = higher priority) |
| --therapeutic | | flag | No | Also set therapeutic flag on match |

#### `rules disable`
```bash
plv rules disable <rule-id>
```

#### `rules test`
```bash
plv rules test <pattern> [--type contains] [--field counterparty_name]
```
Test a pattern against existing transactions without creating a rule.

**Examples**:
```bash
# List all rules
plv rules list

# Add a new rule
plv rules add --pattern "PROXIMUS" --category telefonie --type contains

# Add regex rule for health insurance revenue
plv rules add --pattern "LCM|SOLIDARIS|RIZIV" --category omzet --type regex --therapeutic

# Test pattern before adding
plv rules test "BOL.COM" --type contains
```

---

### `bootstrap` - Extract Rules from Excel

Extract categorization rules from historical Excel files.

```bash
plv bootstrap <excel-files...> [options]
```

**Arguments**:
| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| excel-files | path(s) | Yes | Excel files with categorized transactions |

**Options**:
| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| --sheet | -s | string | Verrichtingen* | Sheet name pattern |
| --min-occurrences | -m | int | 2 | Minimum occurrences to create rule |
| --output | -o | path | config/rules.yaml | Output rules file |
| --dry-run | -n | flag | false | Preview rules without saving |
| --merge | | flag | false | Merge with existing rules |

**Output**:
```json
{
  "rules_extracted": 67,
  "patterns_ambiguous": 3,
  "coverage_estimate": "92%"
}
```

**Examples**:
```bash
# Bootstrap from 2024 and 2025 data
plv bootstrap data/2024/*.xlsx data/2025/*.xlsx

# Preview extraction
plv bootstrap data/2025/Resultatenrekening*.xlsx --dry-run

# Merge with existing rules
plv bootstrap data/2024/*.xlsx --merge
```

---

### `categories` - List Available Categories

Display all available categories.

```bash
plv categories [--format table|json|yaml]
```

**Output** (table format):
```
ID                                  Name                              Type
omzet                               Omzet                             income
admin-kosten                        Admin kosten                      expense
bankkosten                          Bankkosten                        expense
...
Total: 26 categories
```

---

## Global Options

These options are available on all commands:

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| --help | -h | flag | Show help message |
| --version | -V | flag | Show version |
| --verbose | -v | flag | Verbose output |
| --quiet | -q | flag | Suppress non-error output |
| --json | -j | flag | Output as JSON |
| --config | | path | Custom config file path |
| --data-dir | | path | Custom data directory |

## Configuration File

Default location: `config/settings.yaml`

```yaml
fiscal_year: 2025
data_dir: data/output
rules_file: config/rules.yaml
categories_file: config/categories.yaml

import:
  default_source_type: bank_csv
  exclude_patterns:
    - "MASTERCARD.*AFREKENING"

output:
  default_format: table
  date_format: "%Y-%m-%d"
```
