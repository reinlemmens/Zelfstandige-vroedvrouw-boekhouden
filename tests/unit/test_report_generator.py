"""Unit tests for the report generator service."""

import unittest
from decimal import Decimal
from pathlib import Path
import json

from src.models.transaction import Transaction
from src.models.asset import Asset
from src.services.report_generator import ReportGenerator

class TestReportGenerator(unittest.TestCase):
    """Tests for the ReportGenerator service."""

    def setUp(self):
        """Set up test data."""
        self.transactions = self._load_fixture('sample_transactions.json', Transaction.from_dict)
        self.assets = self._load_fixture('sample_assets.json', Asset.from_dict)
        self.generator = ReportGenerator(self.transactions, self.assets)

    def _load_fixture(self, filename, constructor):
        """Load a JSON fixture file."""
        path = Path(__file__).parent.parent / 'fixtures' / filename
        with open(path, 'r') as f:
            data = json.load(f)
        return [constructor(item) for item in data]

    def test_generate_pnl_report_totals(self):
        """
        Test that the generate_pnl_report service function correctly calculates
        totals for income, expenses, and profit.
        """
        report = self.generator.generate_pnl_report(fiscal_year=2025)

        # Expected income: 800.00
        # Expected expenses: -2.50 (vervoer) + -1755.17 (sociale-bijdragen)
        # Expected depreciation: 300 (laptop) + 700 (bike) = 1000
        # Total expenses with depreciation: -2.50 - 1755.17 - 1000 = -2757.67
        # Expected profit: 800.00 - 2757.67 = -1957.67
        
        # These assertions will now fail until the logic is implemented.
        self.assertEqual(report.total_income, Decimal('800.00'))
        self.assertEqual(report.total_expenses, Decimal('-2757.67'))
        self.assertEqual(report.profit_loss, Decimal('-1957.67'))

    def test_therapeutic_subtotal(self):
        """
        Test that therapeutic and non-therapeutic income are correctly sub-totaled.
        """
        # We need a therapeutic transaction in our fixtures for this.
        # Let's add one to our test-local data.
        self.transactions.append(
            Transaction.from_dict({
                "id": "therapeutic-1", "source_file": "manual.csv", "source_type": "bank_csv",
                "statement_number": "00014", "transaction_number": "001",
                "booking_date": "2025-05-10", "value_date": "2025-05-10",
                "amount": "100.00", "currency": "EUR", "counterparty_name": "Patient X",
                "description": "Consultation", "category": "omzet", "is_therapeutic": True,
                "is_manual_override": False, "is_excluded": False, "exclusion_reason": None,
                "matched_rule_id": None
            })
        )
        generator = ReportGenerator(self.transactions, self.assets)
        report = generator.generate_pnl_report(fiscal_year=2025)

        # Total income should now be 800 + 100 = 900
        self.assertEqual(report.total_income, Decimal('900.00'))

        # Find the 'omzet' line item and check its sub-items
        omzet_item = next((item for item in report.income_items if item.category == 'omzet'), None)
        self.assertIsNotNone(omzet_item)
        
        therapeutic_item = next((item for item in omzet_item.sub_items if item.category == 'Therapeutic'), None)
        non_therapeutic_item = next((item for item in omzet_item.sub_items if item.category == 'Non-therapeutic'), None)

        self.assertIsNotNone(therapeutic_item)
        self.assertIsNotNone(non_therapeutic_item)
        self.assertEqual(therapeutic_item.amount, Decimal('100.00'))
        self.assertEqual(non_therapeutic_item.amount, Decimal('800.00'))


    def test_uncategorized_handling(self):
        """
        Test that uncategorized transactions are handled correctly.
        """
        report = self.generator.generate_pnl_report(fiscal_year=2025)
        
        # Expected uncategorized: -123.45
        self.assertEqual(report.total_uncategorized, Decimal('-123.45'))


if __name__ == '__main__':
    unittest.main()
