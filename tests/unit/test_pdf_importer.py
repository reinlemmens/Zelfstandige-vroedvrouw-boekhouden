"""Unit tests for the PDF importer service."""

import unittest
from datetime import date
from decimal import Decimal

from src.services.pdf_importer import PDFImporter


class TestPDFImporterTextParsing(unittest.TestCase):
    """Tests for the PDFImporter text line parsing."""

    def setUp(self):
        """Set up test importer."""
        self.importer = PDFImporter()

    def test_parse_expense_line(self):
        """Test parsing a typical expense transaction line."""
        line = "03/10 06/10 SP TALES.COM PROVO US 38,51 EUR-"

        tx = self.importer._parse_text_line(
            line=line,
            source_file="test.pdf",
            statement_number="6287522061",
            sequence=1,
            statement_year=2025,
        )

        self.assertIsNotNone(tx)
        self.assertEqual(tx.booking_date, date(2025, 10, 3))
        self.assertEqual(tx.value_date, date(2025, 10, 6))
        self.assertEqual(tx.amount, Decimal('-38.51'))
        self.assertEqual(tx.description, "SP TALES.COM PROVO US")
        self.assertEqual(tx.currency, "EUR")
        self.assertEqual(tx.source_type, "mastercard_pdf")

    def test_parse_refund_line(self):
        """Test parsing a refund transaction line (positive amount)."""
        line = "15/10 18/10 SP TWOTHIRDS BARCELONA ES 101,10 EUR+"

        tx = self.importer._parse_text_line(
            line=line,
            source_file="test.pdf",
            statement_number="6287522061",
            sequence=2,
            statement_year=2025,
        )

        self.assertIsNotNone(tx)
        self.assertEqual(tx.booking_date, date(2025, 10, 15))
        self.assertEqual(tx.value_date, date(2025, 10, 18))
        self.assertEqual(tx.amount, Decimal('101.10'))
        self.assertIn("TWOTHIRDS", tx.description)

    def test_parse_large_amount(self):
        """Test parsing a transaction with a larger amount (no thousands separator in Belfius PDFs)."""
        line = "01/11 03/11 AMAZON MKTPL ORDER 234,56 EUR-"

        tx = self.importer._parse_text_line(
            line=line,
            source_file="test.pdf",
            statement_number="TEST",
            sequence=3,
            statement_year=2025,
        )

        self.assertIsNotNone(tx)
        self.assertEqual(tx.amount, Decimal('-234.56'))

    def test_parse_integer_amount(self):
        """Test parsing a transaction with no decimal part."""
        line = "20/09 22/09 SOME VENDOR 50 EUR-"

        tx = self.importer._parse_text_line(
            line=line,
            source_file="test.pdf",
            statement_number="TEST",
            sequence=4,
            statement_year=2025,
        )

        self.assertIsNotNone(tx)
        self.assertEqual(tx.amount, Decimal('-50'))

    def test_skip_non_transaction_lines(self):
        """Test that non-transaction lines return None."""
        non_transaction_lines = [
            "",
            "Transacties van 26/09/2025 tot 25/10/2025",
            "Datum Datum Omschrijving Bedrag",
            "Belfius Mastercard Business",
            "Totaal: 123,45 EUR",
            "Page 1 of 2",
        ]

        for line in non_transaction_lines:
            tx = self.importer._parse_text_line(
                line=line,
                source_file="test.pdf",
                statement_number="TEST",
                sequence=1,
                statement_year=2025,
            )
            self.assertIsNone(tx, f"Expected None for line: {line!r}")

    def test_transaction_id_generation(self):
        """Test that transaction IDs are unique and consistent."""
        line = "03/10 06/10 SP TALES.COM PROVO US 38,51 EUR-"

        tx1 = self.importer._parse_text_line(
            line=line,
            source_file="test.pdf",
            statement_number="6287522061",
            sequence=1,
            statement_year=2025,
        )

        tx2 = self.importer._parse_text_line(
            line=line,
            source_file="test.pdf",
            statement_number="6287522061",
            sequence=1,
            statement_year=2025,
        )

        # Same input should produce same ID
        self.assertEqual(tx1.id, tx2.id)

        # ID should contain statement number and date
        self.assertIn("MC-6287522061", tx1.id)
        self.assertIn("20251003", tx1.id)

    def test_duplicate_detection(self):
        """Test that duplicate transactions are tracked."""
        line = "03/10 06/10 SP TALES.COM PROVO US 38,51 EUR-"

        tx1 = self.importer._parse_text_line(
            line=line,
            source_file="test.pdf",
            statement_number="6287522061",
            sequence=1,
            statement_year=2025,
        )

        # Add ID to existing_ids
        self.importer.existing_ids.add(tx1.id)

        # Second parse should still work (duplicate detection happens at import level)
        tx2 = self.importer._parse_text_line(
            line=line,
            source_file="test.pdf",
            statement_number="6287522061",
            sequence=1,
            statement_year=2025,
        )

        self.assertIsNotNone(tx2)
        self.assertIn(tx2.id, self.importer.existing_ids)


class TestPDFImporterDateParsing(unittest.TestCase):
    """Tests for the PDFImporter date parsing."""

    def setUp(self):
        """Set up test importer."""
        self.importer = PDFImporter()

    def test_parse_date_ddmmyyyy(self):
        """Test parsing date in DD/MM/YYYY format."""
        result = self.importer._parse_date("25/10/2025")
        self.assertEqual(result, date(2025, 10, 25))

    def test_parse_date_ddmmyy(self):
        """Test parsing date in DD/MM/YY format."""
        result = self.importer._parse_date("25/10/25")
        self.assertEqual(result, date(2025, 10, 25))

    def test_parse_date_invalid(self):
        """Test that invalid date raises ValueError."""
        with self.assertRaises(ValueError):
            self.importer._parse_date("invalid")

    def test_parse_date_with_whitespace(self):
        """Test that dates with whitespace are handled."""
        result = self.importer._parse_date("  25/10/2025  ")
        self.assertEqual(result, date(2025, 10, 25))


class TestPDFImporterYearCrossover(unittest.TestCase):
    """Tests for handling year crossover in PDF statements."""

    def setUp(self):
        """Set up test importer."""
        self.importer = PDFImporter()

    def test_december_transaction_in_2025(self):
        """Test that December transactions use correct year."""
        line = "15/12 18/12 DECEMBER PURCHASE 50,00 EUR-"

        tx = self.importer._parse_text_line(
            line=line,
            source_file="test.pdf",
            statement_number="TEST",
            sequence=1,
            statement_year=2025,
        )

        self.assertEqual(tx.booking_date.year, 2025)
        self.assertEqual(tx.booking_date.month, 12)

    def test_january_transaction_in_2025(self):
        """Test that January transactions use correct year."""
        line = "05/01 08/01 NEW YEAR PURCHASE 75,00 EUR-"

        tx = self.importer._parse_text_line(
            line=line,
            source_file="test.pdf",
            statement_number="TEST",
            sequence=1,
            statement_year=2025,
        )

        self.assertEqual(tx.booking_date.year, 2025)
        self.assertEqual(tx.booking_date.month, 1)


if __name__ == '__main__':
    unittest.main()
