"""Belfius Mastercard PDF statement importer."""

import hashlib
import io
import logging
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional, Set, Tuple

import pdfplumber

from src.lib.belgian_numbers import parse_belgian_amount
from src.models.transaction import Transaction
from src.models.import_session import ImportSession, ImportError

logger = logging.getLogger(__name__)


class PDFImporter:
    """Import transactions from Belfius Mastercard PDF statements."""

    def __init__(self, existing_ids: Optional[Set[str]] = None):
        """Initialize PDF importer.

        Args:
            existing_ids: Set of existing transaction IDs for duplicate detection
        """
        self.existing_ids = existing_ids or set()

    def import_file(
        self,
        file_path: Path,
        fiscal_year: Optional[int] = None,
        force: bool = False,
    ) -> Tuple[List[Transaction], ImportSession]:
        """Import transactions from a single PDF file.

        Args:
            file_path: Path to the PDF file
            fiscal_year: Optional fiscal year filter
            force: If True, re-import even if transaction exists

        Returns:
            Tuple of (list of imported transactions, import session with stats)
        """
        file_path = Path(file_path)
        session = ImportSession(source_files=[str(file_path)])
        transactions = []

        try:
            # Extract statement number from filename (e.g., "6287522061_02_01_2026_09_03_17.pdf")
            statement_match = re.search(r'^(\d+)_', file_path.name)
            statement_number = statement_match.group(1) if statement_match else "MC"

            with pdfplumber.open(file_path) as pdf:
                tx_sequence = 1

                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract tables from the page
                    tables = page.extract_tables()

                    for table in tables:
                        if not table:
                            continue

                        for row in table:
                            if not row or len(row) < 4:
                                continue

                            try:
                                tx = self._parse_row(
                                    row,
                                    file_path.name,
                                    statement_number,
                                    tx_sequence,
                                    page_num,
                                )

                                if tx is None:
                                    continue

                                # Filter by fiscal year if specified
                                if fiscal_year and tx.booking_date.year != fiscal_year:
                                    continue

                                # Check for duplicates
                                if tx.id in self.existing_ids and not force:
                                    session.transactions_skipped += 1
                                    continue

                                transactions.append(tx)
                                self.existing_ids.add(tx.id)
                                session.transactions_imported += 1
                                tx_sequence += 1

                            except Exception as e:
                                # Skip header rows and non-transaction rows silently
                                logger.debug(f"Skipping row on page {page_num}: {e}")

        except Exception as e:
            error = ImportError(
                file=file_path.name,
                message=f"Failed to read PDF: {e}",
            )
            session.errors.append(error)
            logger.error(f"Failed to read {file_path}: {e}")

        logger.info(
            f"Imported {session.transactions_imported} transactions from {file_path.name} "
            f"(skipped: {session.transactions_skipped})"
        )

        return transactions, session

    def import_from_bytes(
        self,
        file_bytes: bytes,
        filename: str,
        fiscal_year: Optional[int] = None,
        force: bool = False,
    ) -> Tuple[List[Transaction], ImportSession]:
        """Import transactions from PDF file bytes (for Streamlit uploads).

        Args:
            file_bytes: Raw bytes of the PDF file
            filename: Original filename for error reporting
            fiscal_year: Optional fiscal year filter
            force: If True, re-import even if transaction exists

        Returns:
            Tuple of (list of imported transactions, import session with stats)
        """
        session = ImportSession(source_files=[filename])
        transactions = []

        try:
            # Extract statement number from filename
            statement_match = re.search(r'^(\d+)_', filename)
            statement_number = statement_match.group(1) if statement_match else "MC"

            # Open PDF from bytes and extract text
            pdf_file = io.BytesIO(file_bytes)
            with pdfplumber.open(pdf_file) as pdf:
                tx_sequence = 1
                statement_year = None

                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if not text:
                        continue

                    # Try to extract statement year from text (e.g., "Transacties van 26/09/2025 tot 25/10/2025")
                    if statement_year is None:
                        year_match = re.search(r'Transacties van \d{2}/\d{2}/(\d{4})', text)
                        if year_match:
                            statement_year = int(year_match.group(1))
                        elif fiscal_year:
                            statement_year = fiscal_year
                        else:
                            statement_year = datetime.now().year

                    # Parse transactions from text
                    # Format: DD/MM DD/MM DESCRIPTION AMOUNT EUR[+-]
                    lines = text.split('\n')
                    for line in lines:
                        tx = self._parse_text_line(
                            line,
                            filename,
                            statement_number,
                            tx_sequence,
                            statement_year,
                        )

                        if tx is None:
                            continue

                        if fiscal_year and tx.booking_date.year != fiscal_year:
                            continue

                        if tx.id in self.existing_ids and not force:
                            session.transactions_skipped += 1
                            continue

                        transactions.append(tx)
                        self.existing_ids.add(tx.id)
                        session.transactions_imported += 1
                        tx_sequence += 1

        except Exception as e:
            error = ImportError(
                file=filename,
                message=f"Failed to read PDF: {e}",
            )
            session.errors.append(error)
            logger.error(f"Failed to read {filename}: {e}")

        logger.info(
            f"Imported {session.transactions_imported} transactions from {filename} "
            f"(skipped: {session.transactions_skipped})"
        )

        return transactions, session

    def _parse_text_line(
        self,
        line: str,
        source_file: str,
        statement_number: str,
        sequence: int,
        statement_year: Optional[int] = None,
    ) -> Optional[Transaction]:
        """Parse a text line from Belfius Mastercard PDF.

        Format: DD/MM DD/MM DESCRIPTION AMOUNT EUR[+-]
        Example: 03/10 06/10 SP TALES.COM PROVO US 38,51 EUR-

        Args:
            line: Text line from PDF
            source_file: Name of source file
            statement_number: Statement identifier
            sequence: Transaction sequence number
            statement_year: Year from statement filename

        Returns:
            Transaction object or None if line doesn't match format
        """
        line = line.strip()
        if not line:
            return None

        # Match pattern: DD/MM DD/MM ... AMOUNT EUR[+-]
        # Transaction date, settlement date, description, amount
        pattern = r'^(\d{2}/\d{2})\s+(\d{2}/\d{2})\s+(.+?)\s+(\d+(?:[.,]\d+)?)\s*EUR([+-])$'
        match = re.match(pattern, line)

        if not match:
            return None

        tx_date_str = match.group(1)  # DD/MM
        settlement_date_str = match.group(2)  # DD/MM
        description = match.group(3).strip()
        amount_str = match.group(4)
        sign = match.group(5)

        # Determine year - use statement_year or current year
        year = statement_year or datetime.now().year

        # Parse dates (DD/MM format, add year)
        try:
            booking_date = datetime.strptime(f"{tx_date_str}/{year}", "%d/%m/%Y").date()
            value_date = datetime.strptime(f"{settlement_date_str}/{year}", "%d/%m/%Y").date()
        except ValueError:
            return None

        # Parse amount
        try:
            amount = parse_belgian_amount(amount_str)
            # Apply sign: - means expense, + means refund
            if sign == '-':
                amount = -abs(amount)
            else:
                amount = abs(amount)
        except ValueError:
            return None

        # Skip zero amounts
        if amount == Decimal('0'):
            return None

        # Generate unique ID using date hash for better deduplication
        date_hash = hashlib.md5(f"{booking_date.isoformat()}|{amount}|{description}".encode()).hexdigest()[:8]
        tx_id = f"MC-{statement_number}-{booking_date.strftime('%Y%m%d')}-{date_hash}"

        return Transaction(
            id=tx_id,
            source_file=source_file,
            source_type='mastercard_pdf',
            statement_number=statement_number,
            transaction_number=str(sequence),
            booking_date=booking_date,
            value_date=value_date,
            amount=amount,
            currency="EUR",
            counterparty_name=description[:100] if description else None,
            description=description,
        )

    def _parse_row(
        self,
        row: List[str],
        source_file: str,
        statement_number: str,
        sequence: int,
        page_num: int,
    ) -> Optional[Transaction]:
        """Parse a single PDF table row into a Transaction.

        Belfius Mastercard statement format:
        - Column 0: Transaction date (DD/MM/YYYY or DD/MM/YY)
        - Column 1: Settlement date
        - Column 2: Description
        - Column 3: Amount (Belgian format, may have + for refunds)

        Args:
            row: Table row as list of strings
            source_file: Name of source file
            statement_number: Statement identifier
            sequence: Transaction sequence number
            page_num: Page number for error reporting

        Returns:
            Transaction object or None if row should be skipped
        """
        # Clean row values
        row = [str(cell).strip() if cell else "" for cell in row]

        # Skip header rows
        if any(header in row[0].lower() for header in ['datum', 'date', 'transactie']):
            return None

        # Parse transaction date (column 0)
        date_str = row[0].strip()
        if not date_str or not re.match(r'\d{2}/\d{2}/\d{2,4}', date_str):
            return None

        booking_date = self._parse_date(date_str)

        # Parse settlement date (column 1)
        settlement_str = row[1].strip() if len(row) > 1 else ""
        try:
            value_date = self._parse_date(settlement_str) if settlement_str else booking_date
        except ValueError:
            value_date = booking_date

        # Get description (column 2)
        description = row[2].strip() if len(row) > 2 else ""
        if not description:
            return None

        # Parse amount (column 3 or last column)
        amount_str = row[3].strip() if len(row) > 3 else row[-1].strip()
        if not amount_str:
            return None

        # Handle refunds (+ prefix)
        is_refund = amount_str.startswith('+')
        amount_str = amount_str.lstrip('+').strip()

        try:
            amount = parse_belgian_amount(amount_str)
            # Mastercard expenses are negative (unless refund)
            if not is_refund:
                amount = -abs(amount)
            else:
                amount = abs(amount)
        except ValueError:
            return None

        # Skip zero amounts
        if amount == Decimal('0'):
            return None

        # Generate unique ID
        tx_id = f"MC-{statement_number}-{sequence:04d}"

        return Transaction(
            id=tx_id,
            source_file=source_file,
            source_type='mastercard_pdf',
            statement_number=statement_number,
            transaction_number=str(sequence),
            booking_date=booking_date,
            value_date=value_date,
            amount=amount,
            currency="EUR",
            counterparty_name=description[:100] if description else None,  # Use description as counterparty
            description=description,
        )

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date from Mastercard PDF format.

        Args:
            date_str: Date string (DD/MM/YYYY or DD/MM/YY)

        Returns:
            Date object
        """
        date_str = date_str.strip()

        # Try DD/MM/YYYY first
        try:
            return datetime.strptime(date_str, "%d/%m/%Y").date()
        except ValueError:
            pass

        # Try DD/MM/YY
        try:
            return datetime.strptime(date_str, "%d/%m/%y").date()
        except ValueError:
            pass

        raise ValueError(f"Cannot parse date: {date_str}")


def import_pdf_files(
    files: List[Path],
    existing_ids: Optional[Set[str]] = None,
    fiscal_year: Optional[int] = None,
    force: bool = False,
) -> Tuple[List[Transaction], List[ImportSession]]:
    """Import transactions from multiple PDF files.

    Args:
        files: List of PDF file paths
        existing_ids: Set of existing transaction IDs for duplicate detection
        fiscal_year: Optional fiscal year filter
        force: If True, re-import even if transaction exists

    Returns:
        Tuple of (all transactions, list of import sessions)
    """
    importer = PDFImporter(existing_ids=existing_ids)
    all_transactions = []
    all_sessions = []

    for file_path in files:
        if not str(file_path).lower().endswith('.pdf'):
            logger.warning(f"Skipping non-PDF file: {file_path}")
            continue

        transactions, session = importer.import_file(
            file_path,
            fiscal_year=fiscal_year,
            force=force,
        )
        all_transactions.extend(transactions)
        all_sessions.append(session)

    return all_transactions, all_sessions
