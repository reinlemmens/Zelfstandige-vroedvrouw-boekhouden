# Data Model: Financial Report

This document outlines the data structures used to represent the financial report.

## Report

A `Report` object represents the entire P&L statement for a fiscal year.

- **fiscal_year** (int): The year the report is for.
- **income_items** (List[ReportLineItem]): A list of line items representing income.
- **expense_items** (List[ReportLineItem]): A list of line items representing expenses.
- **depreciation_items** (List[ReportLineItem]): A list of line items for depreciation.
- **uncategorized_items** (List[ReportLineItem]): A list of line items for uncategorized transactions.
- **total_income** (Decimal): The sum of all income items.
- **total_expenses** (Decimal): The sum of all expense and depreciation items.
- **profit_loss** (Decimal): The final result (total_income - total_expenses).
- **total_uncategorized** (Decimal): The sum of all uncategorized items.

## ReportLineItem

A `ReportLineItem` represents a single row in the report.

- **category** (str): The name of the category (e.g., "Omzet", "Huur onroerend goed", "Uncategorized").
- **amount** (Decimal): The total amount for this line item.
- **item_type** (str): The type of the line item, one of 'income', 'expense', 'depreciation', or 'uncategorized'.
- **sub_items** (List[ReportLineItem], optional): A list of sub-items for hierarchical display (e.g., for breaking down 'Omzet' into therapeutic and non-therapeutic).

## State Transitions

The data models are stateless and are generated on-the-fly when a report is requested. They do not have a lifecycle beyond the report generation process.
