"""Belfius bank CSV importer service."""

import csv
import hashlib
import io
import logging
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional, Set, Tuple

from src.lib.belgian_numbers import parse_belgian_amount
from src.models.transaction import Transaction
from src.models.import_session import ImportSession, ImportError

logger = logging.getLogger(__name__)

# Belfius CSV column indices (0-based)
COL_ACCOUNT = 0
COL_BOOKING_DATE = 1
COL_STATEMENT_NUMBER = 2
COL_TRANSACTION_NUMBER = 3
COL_COUNTERPARTY_ACCOUNT = 4
COL_COUNTERPARTY_NAME = 5
COL_STREET = 6
COL_POSTAL_CITY = 7
COL_TRANSACTION_DESC = 8
COL_VALUE_DATE = 9
COL_AMOUNT = 10
COL_CURRENCY = 11
COL_BIC = 12
COL_COUNTRY_CODE = 13
COL_COMMUNICATIONS = 14

# Number of header lines to skip in Belfius CSV export
HEADER_LINES_TO_SKIP = 13

# Patterns to identify and exclude Mastercard settlements
MASTERCARD_SETTLEMENT_PATTERNS = [
    re.compile(r'MASTERCARD.*AFREKENING', re.IGNORECASE),
    re.compile(r'KREDIETKAART.*AFREKENING', re.IGNORECASE),
    re.compile(r'6287522061', re.IGNORECASE),  # Mastercard customer reference
]


class CSVImporter:
    """Import transactions from Belfius bank CSV files."""

    def __init__(self, existing_ids: Optional[Set[str]] = None):
        """Initialize CSV importer.

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
        """Import transactions from a single CSV file.

        Args:
            file_path: Path to the CSV file
            fiscal_year: Optional fiscal year filter
            force: If True, re-import even if transaction exists

        Returns:
            Tuple of (list of imported transactions, import session with stats)
        """
        file_path = Path(file_path)
        session = ImportSession(source_files=[str(file_path)])

        transactions = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Skip header lines
                for _ in range(HEADER_LINES_TO_SKIP):
                    next(f, None)

                reader = csv.reader(f, delimiter=';')

                for line_num, row in enumerate(reader, start=HEADER_LINES_TO_SKIP + 1):
                    if not row or len(row) < 15:
                        # Skip empty or malformed rows
                        continue

                    try:
                        tx = self._parse_row(row, file_path.name, line_num)

                        if tx is None:
                            continue

                        # Filter by fiscal year if specified
                        if fiscal_year and tx.booking_date.year != fiscal_year:
                            continue

                        # Check for Mastercard settlement exclusion
                        if self._is_mastercard_settlement(tx):
                            tx.is_excluded = True
                            tx.exclusion_reason = "Mastercard settlement - details in PDF"
                            session.transactions_excluded += 1
                            transactions.append(tx)
                            continue

                        # Check for duplicates
                        if tx.id in self.existing_ids and not force:
                            session.transactions_skipped += 1
                            continue

                        transactions.append(tx)
                        self.existing_ids.add(tx.id)
                        session.transactions_imported += 1

                    except Exception as e:
                        error = ImportError(
                            file=file_path.name,
                            line=line_num,
                            message=str(e),
                            raw_data=';'.join(row) if row else None,
                        )
                        session.errors.append(error)
                        logger.error(f"Error parsing line {line_num}: {e}")

        except Exception as e:
            error = ImportError(
                file=file_path.name,
                message=f"Failed to read file: {e}",
            )
            session.errors.append(error)
            logger.error(f"Failed to read {file_path}: {e}")

        logger.info(
            f"Imported {session.transactions_imported} transactions from {file_path.name} "
            f"(skipped: {session.transactions_skipped}, excluded: {session.transactions_excluded})"
        )

        return transactions, session

    def import_from_bytes(
        self,
        file_bytes: bytes,
        filename: str,
        fiscal_year: Optional[int] = None,
        force: bool = False,
    ) -> Tuple[List[Transaction], ImportSession]:
        """Import transactions from CSV file bytes (for Streamlit uploads).

        Args:
            file_bytes: Raw bytes of the CSV file
            filename: Original filename for error reporting
            fiscal_year: Optional fiscal year filter
            force: If True, re-import even if transaction exists

        Returns:
            Tuple of (list of imported transactions, import session with stats)
        """
        session = ImportSession(source_files=[filename])
        transactions = []

        try:
            # Decode bytes to string and create file-like object
            content = file_bytes.decode('utf-8')
            f = io.StringIO(content)

            # Skip header lines
            for _ in range(HEADER_LINES_TO_SKIP):
                next(f, None)

            reader = csv.reader(f, delimiter=';')

            for line_num, row in enumerate(reader, start=HEADER_LINES_TO_SKIP + 1):
                if not row or len(row) < 15:
                    continue

                try:
                    tx = self._parse_row(row, filename, line_num)

                    if tx is None:
                        continue

                    if fiscal_year and tx.booking_date.year != fiscal_year:
                        continue

                    if self._is_mastercard_settlement(tx):
                        tx.is_excluded = True
                        tx.exclusion_reason = "Mastercard settlement - details in PDF"
                        session.transactions_excluded += 1
                        transactions.append(tx)
                        continue

                    if tx.id in self.existing_ids and not force:
                        session.transactions_skipped += 1
                        continue

                    transactions.append(tx)
                    self.existing_ids.add(tx.id)
                    session.transactions_imported += 1

                except Exception as e:
                    error = ImportError(
                        file=filename,
                        line=line_num,
                        message=str(e),
                        raw_data=';'.join(row) if row else None,
                    )
                    session.errors.append(error)
                    logger.error(f"Error parsing line {line_num}: {e}")

        except Exception as e:
            error = ImportError(
                file=filename,
                message=f"Failed to read file: {e}",
            )
            session.errors.append(error)
            logger.error(f"Failed to read {filename}: {e}")

        logger.info(
            f"Imported {session.transactions_imported} transactions from {filename} "
            f"(skipped: {session.transactions_skipped}, excluded: {session.transactions_excluded})"
        )

        return transactions, session

    def _parse_row(self, row: List[str], source_file: str, line_num: int) -> Optional[Transaction]:
        """Parse a single CSV row into a Transaction.

        Args:
            row: CSV row as list of strings
            source_file: Name of source file
            line_num: Line number for error reporting

        Returns:
            Transaction object or None if row should be skipped
        """
        # Get statement and transaction numbers
        statement_number = row[COL_STATEMENT_NUMBER].strip()
        transaction_number = row[COL_TRANSACTION_NUMBER].strip()

        # Parse dates (DD/MM/YYYY format)
        booking_date = self._parse_belgian_date(row[COL_BOOKING_DATE])
        value_date = self._parse_belgian_date(row[COL_VALUE_DATE])

        # Parse amount (Belgian format: -1.234,56)
        amount = parse_belgian_amount(row[COL_AMOUNT])

        # Get optional fields
        own_account = row[COL_ACCOUNT].strip() or None
        counterparty_iban = row[COL_COUNTERPARTY_ACCOUNT].strip() or None
        counterparty_name = row[COL_COUNTERPARTY_NAME].strip() or None
        counterparty_street = row[COL_STREET].strip() or None
        counterparty_postal_city = row[COL_POSTAL_CITY].strip() or None
        counterparty_bic = row[COL_BIC].strip() if len(row) > COL_BIC else None
        counterparty_country = row[COL_COUNTRY_CODE].strip() if len(row) > COL_COUNTRY_CODE else None

        # Build description from transaction and communications
        transaction_desc = row[COL_TRANSACTION_DESC].strip()
        communications = row[COL_COMMUNICATIONS].strip() if len(row) > COL_COMMUNICATIONS else ""

        # Use the more detailed description
        description = transaction_desc if transaction_desc else communications
        communication = communications or None

        # Generate unique ID
        if statement_number and transaction_number:
            tx_id = f"{statement_number}-{transaction_number}"
        else:
            # For transactions without statement/transaction numbers (e.g., BEATS charges),
            # generate a hash-based ID from date + amount + description
            hash_input = f"{booking_date.isoformat()}|{amount}|{description}"
            tx_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
            tx_id = f"NONUM-{tx_hash}"
            statement_number = statement_number or None
            transaction_number = transaction_number or None

        # Currency
        currency = row[COL_CURRENCY].strip().upper()
        if currency != "EUR":
            raise ValueError(f"Unsupported currency: {currency}")

        return Transaction(
            id=tx_id,
            source_file=source_file,
            source_type='bank_csv',
            statement_number=statement_number,
            transaction_number=transaction_number,
            booking_date=booking_date,
            value_date=value_date,
            amount=amount,
            currency=currency,
            counterparty_name=counterparty_name,
            counterparty_iban=counterparty_iban,
            counterparty_street=counterparty_street,
            counterparty_postal_city=counterparty_postal_city,
            counterparty_bic=counterparty_bic,
            counterparty_country=counterparty_country,
            own_account=own_account,
            communication=communication,
            description=description,
        )

    def _parse_belgian_date(self, date_str: str) -> datetime:
        """Parse date in Belgian format (DD/MM/YYYY).

        Args:
            date_str: Date string in DD/MM/YYYY format

        Returns:
            Date object
        """
        date_str = date_str.strip()
        try:
            return datetime.strptime(date_str, "%d/%m/%Y").date()
        except ValueError:
            # Try alternative formats
            for fmt in ["%d-%m-%Y", "%Y-%m-%d"]:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Cannot parse date: {date_str}")

    def _is_mastercard_settlement(self, tx: Transaction) -> bool:
        """Check if transaction is a Mastercard settlement to be excluded.

        Args:
            tx: Transaction to check

        Returns:
            True if this is a Mastercard settlement that should be excluded
        """
        # Check description
        if tx.description:
            for pattern in MASTERCARD_SETTLEMENT_PATTERNS:
                if pattern.search(tx.description):
                    return True

        # Check counterparty name
        if tx.counterparty_name:
            for pattern in MASTERCARD_SETTLEMENT_PATTERNS:
                if pattern.search(tx.counterparty_name):
                    return True

        return False


def import_csv_files(
    files: List[Path],
    existing_ids: Optional[Set[str]] = None,
    fiscal_year: Optional[int] = None,
    force: bool = False,
) -> Tuple[List[Transaction], List[ImportSession]]:
    """Import transactions from multiple CSV files.

    Args:
        files: List of CSV file paths
        existing_ids: Set of existing transaction IDs for duplicate detection
        fiscal_year: Optional fiscal year filter
        force: If True, re-import even if transaction exists

    Returns:
        Tuple of (all transactions, list of import sessions)
    """
    importer = CSVImporter(existing_ids=existing_ids)
    all_transactions = []
    all_sessions = []

    for file_path in files:
        if not str(file_path).lower().endswith('.csv'):
            logger.warning(f"Skipping non-CSV file: {file_path}")
            continue

        transactions, session = importer.import_file(
            file_path,
            fiscal_year=fiscal_year,
            force=force,
        )
        all_transactions.extend(transactions)
        all_sessions.append(session)

    return all_transactions, all_sessions
