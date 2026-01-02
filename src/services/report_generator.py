"""Service to generate a Profit & Loss (P&L) financial report."""

import logging
from decimal import Decimal
from pathlib import Path
from typing import List

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows

from src.models.asset import Asset
from src.models.report import Report, ReportLineItem
from src.models.transaction import Transaction
from src.services.depreciation import get_depreciation_for_year

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates a P&L report from transactions and assets."""

    def __init__(self, transactions: List[Transaction], assets: List[Asset]):
        self.transactions = transactions
        self.assets = assets

    def generate_pnl_report(self, fiscal_year: int) -> Report:
        """
        Generates a P&L report for a given fiscal year.
        """
        report = Report(fiscal_year=fiscal_year)
        logger.debug(f"Generating P&L report for fiscal year {fiscal_year} with {len(self.transactions)} transactions and {len(self.assets)} assets.")
        
        # Filter transactions for the fiscal year
        year_transactions = [
            t for t in self.transactions if t.booking_date.year == fiscal_year
        ]
        logger.debug(f"Found {len(year_transactions)} transactions for {fiscal_year}.")

        if not year_transactions:
            return report

        df = pd.DataFrame([t.to_dict() for t in year_transactions])
        df['amount'] = df['amount'].apply(Decimal)
        logger.debug("Transaction DataFrame head:\n%s", df.head().to_string())

        # Handle income
        income_df = df[df['category'] == 'omzet']
        if not income_df.empty:
            total_omzet = income_df['amount'].sum()
            omzet_item = ReportLineItem(category='omzet', amount=total_omzet, item_type='income')
            logger.debug(f"Total income (omzet): {total_omzet}")

            thera_amount = income_df[income_df['is_therapeutic'] == True]['amount'].sum()
            non_thera_amount = income_df[income_df['is_therapeutic'] == False]['amount'].sum()
            logger.debug(f"Therapeutic: {thera_amount}, Non-therapeutic: {non_thera_amount}")

            if thera_amount > 0:
                omzet_item.sub_items.append(ReportLineItem('Therapeutic', thera_amount, 'income'))
            if non_thera_amount > 0:
                omzet_item.sub_items.append(ReportLineItem('Non-therapeutic', non_thera_amount, 'income'))
            
            report.income_items.append(omzet_item)

        # Handle expenses
        expense_df = df[df['category'].notna() & (df['category'] != 'omzet')]
        if not expense_df.empty:
            expense_groups = expense_df.groupby('category')['amount'].sum()
            logger.debug("Expense groups:\n%s", expense_groups.to_string())
            for category, total in expense_groups.items():
                report.expense_items.append(ReportLineItem(category, total, 'expense'))

        # Handle depreciation
        depreciation_entries = get_depreciation_for_year(self.assets, fiscal_year)
        if depreciation_entries:
            total_depreciation = sum(e.amount for e in depreciation_entries)
            logger.debug(f"Total depreciation: {total_depreciation}")
            # Depreciation is an expense, so it should be negative
            report.depreciation_items.append(ReportLineItem('afschrijvingen', -total_depreciation, 'depreciation'))

        # Handle uncategorized
        uncategorized_df = df[df['category'].isna()]
        if not uncategorized_df.empty:
            total_uncategorized = uncategorized_df['amount'].sum()
            logger.debug(f"Total uncategorized: {total_uncategorized}")
            report.uncategorized_items.append(ReportLineItem('Uncategorized', total_uncategorized, 'uncategorized'))
            
        return report

    def export_to_excel(self, report: Report, output_path: Path) -> None:
        """
        Exports the P&L report to a formatted Excel file.
        """
        logger.info(f"Starting Excel export to {output_path}")
        wb = Workbook()
        ws = wb.active
        ws.title = f"P&L {report.fiscal_year}"

        # Define styles
        bold_font = Font(bold=True)
        currency_format = '€ #,##0.00'
        
        # Title
        ws.cell(row=1, column=1, value=f"Profit & Loss Report for {report.fiscal_year}").font = Font(size=16, bold=True)
        ws.merge_cells('A1:C1')
        
        current_row = 3
        logger.debug("Writing income section...")
        # Income
        ws.cell(row=current_row, column=1, value="Baten (Income)").font = bold_font
        current_row += 1
        for item in report.income_items:
            ws.cell(row=current_row, column=1, value=f"  {item.category}")
            cell = ws.cell(row=current_row, column=2, value=float(item.amount))
            cell.number_format = currency_format
            current_row += 1
            for sub_item in item.sub_items:
                ws.cell(row=current_row, column=1, value=f"    - {sub_item.category}")
                cell = ws.cell(row=current_row, column=2, value=float(sub_item.amount))
                cell.number_format = currency_format
                current_row += 1
        
        ws.cell(row=current_row, column=1, value="Totaal Baten").font = bold_font
        cell = ws.cell(row=current_row, column=2, value=float(report.total_income))
        cell.number_format = currency_format
        cell.font = bold_font
        current_row += 2

        # Expenses
        logger.debug("Writing expenses section...")
        ws.cell(row=current_row, column=1, value="Kosten (Expenses)").font = bold_font
        current_row += 1
        all_expenses = sorted(report.expense_items + report.depreciation_items, key=lambda x: x.category)
        for item in all_expenses:
            ws.cell(row=current_row, column=1, value=f"  {item.category.capitalize()}")
            cell = ws.cell(row=current_row, column=2, value=float(-item.amount))
            cell.number_format = currency_format
            current_row += 1

        ws.cell(row=current_row, column=1, value="Totaal Kosten").font = bold_font
        cell = ws.cell(row=current_row, column=2, value=float(-report.total_expenses))
        cell.number_format = currency_format
        cell.font = bold_font
        current_row += 2

        # Result
        logger.debug("Writing result section...")
        ws.cell(row=current_row, column=1, value="Resultaat (Winst/Verlies)").font = bold_font
        cell = ws.cell(row=current_row, column=2, value=float(report.profit_loss))
        cell.number_format = currency_format
        cell.font = bold_font
        current_row += 2

        # Uncategorized warning
        if report.total_uncategorized != 0:
            logger.debug("Adding uncategorized warning.")
            ws.cell(row=current_row, column=1, value=f"Waarschuwing: {report.total_uncategorized:,.2f} aan niet-gecategoriseerde transacties (niet opgenomen in resultaat).").font = Font(color="FF0000")

        # Adjust column widths
        ws.column_dimensions['A'].width = 40
        ws.column_dimensions['B'].width = 15

        # Save workbook
        try:
            wb.save(output_path)
            logger.info(f"Successfully exported report to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save Excel file to {output_path}: {e}")
            raise


    def format_for_console(self, report: Report) -> str:
        """
        Formats the P&L report for display in the console.
        """
        lines = []
        width = 50
        lines.append("=" * width)
        lines.append(f"   Profit & Loss Report for {report.fiscal_year}".center(width))
        lines.append("=" * width)
        lines.append("")

        # Income
        lines.append("Baten (Income)")
        lines.append("-" * width)
        for item in report.income_items:
            lines.append(f"  {item.category:<35} € {item.amount:10,.2f}")
            for sub_item in item.sub_items:
                lines.append(f"    - {sub_item.category:<31} € {sub_item.amount:10,.2f}")
        lines.append("-" * width)
        lines.append(f"{'Totaal Baten':<37} € {report.total_income:10,.2f}")
        lines.append("")

        # Expenses
        lines.append("Kosten (Expenses)")
        lines.append("-" * width)
        
        all_expenses = sorted(report.expense_items + report.depreciation_items, key=lambda x: x.category)
        for item in all_expenses:
            lines.append(f"  {item.category.capitalize():<35} € {-item.amount:10,.2f}")
        lines.append("-" * width)
        lines.append(f"{'Totaal Kosten':<37} € {-report.total_expenses:10,.2f}")
        lines.append("")

        # Result
        lines.append("=" * width)
        profit_label = "Winst" if report.profit_loss >= 0 else "Verlies"
        lines.append(f"Resultaat ({profit_label}){'':<20} € {report.profit_loss:10,.2f}")
        lines.append("=" * width)
        lines.append("")

        # Uncategorized warning
        if report.total_uncategorized != 0:
            lines.append(f"Waarschuwing: Er is € {report.total_uncategorized:,.2f} aan niet-gecategoriseerde transacties.")
            lines.append("Het resultaat is exclusief deze transacties.")

        return "\n".join(lines)
