# Quickstart: Financial Report Generation

This guide provides the steps to use the financial report generation feature.

## Prerequisites

- Transactions for the desired fiscal year have been imported (`plv import`).
- Transactions have been categorized (`plv categorize`).
- Depreciable assets have been registered (`plv assets add` or `plv assets import`).

## Generating a Report

To generate a financial report for a specific year and display it in the console, use the `plv report` command:

```bash
# Generate and display a report for 2025
plv report --year 2025
```

## Exporting to Excel

To export the report to a formatted Excel file, use the `--output` option:

```bash
# Generate a report for 2025 and save it to an Excel file
plv report --year 2025 --output "Resultatenrekening 2025.xlsx"
```

If the output file already exists, a new file with a numeric suffix will be created automatically (e.g., `Resultatenrekening 2025-1.xlsx`).

## Example Output (Console)

```
========================================
   Profit & Loss Report for 2025
========================================

Baten (Income)
----------------------------------------
  Omzet                               € 50,000.00
    - Therapeutic                     € 45,000.00
    - Non-therapeutic                 €  5,000.00
----------------------------------------
Totaal Baten                        € 50,000.00

Kosten (Expenses)
----------------------------------------
  Huur onroerend goed               €  6,000.00
  Sociale bijdragen                 €  8,000.00
  Verzekering beroepsaansprakelijkheid€    500.00
  ...
  Afschrijvingen                      €  1,500.00
----------------------------------------
Totaal Kosten                       € 20,000.00

========================================
Resultaat (Profit)                  € 30,000.00
========================================

Waarschuwing: Er is € 150.75 aan niet-gecategoriseerde transacties.
Het resultaat is exclusief deze transacties.
```
