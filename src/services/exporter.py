"""Service for exporting transactions to various formats."""

import logging
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

import pandas as pd

from src.models.transaction import Transaction

logger = logging.getLogger(__name__)


def export_to_excel(
    transactions: List[Transaction],
    output_path: Path,
    fiscal_year: Optional[int] = None,
) -> None:
    """Export transactions to an Excel file.

    Args:
        transactions: List of transactions to export
        output_path: Path where the Excel file should be saved
        fiscal_year: Optional fiscal year to filter transactions
    """
    if not transactions:
        logger.warning("No transactions to export")
        return

    # Filter by year if specified
    if fiscal_year:
        transactions = [
            t for t in transactions 
            if t.booking_date.year == fiscal_year
        ]

    if not transactions:
        logger.warning(f"No transactions found for fiscal year {fiscal_year}")
        return

    # Sort by date (descending)
    transactions.sort(key=lambda t: t.booking_date, reverse=True)

    # Convert to list of dicts for DataFrame - retain all columns from input
    data = []
    for t in transactions:
        row = {
            'Rekening': t.own_account,
            'Boekingsdatum': t.booking_date,
            'Valutadatum': t.value_date,
            'Rekeninguittrekselnr': t.statement_number,
            'Transactienr': t.transaction_number,
            'Tegenpartij': t.counterparty_name,
            'Rekening Tegenpartij': t.counterparty_iban,
            'Straat en nummer': t.counterparty_street,
            'Postcode en plaats': t.counterparty_postal_city,
            'BIC': t.counterparty_bic,
            'Landcode': t.counterparty_country,
            'Omschrijving': t.description,
            'Bedrag': float(t.amount),  # Convert Decimal to float for Excel
            'Devies': t.currency,
            'Categorie': t.category,
            'Therapeutisch': 'Ja' if t.is_therapeutic else 'Nee',
            'Uitgesloten': 'Ja' if t.is_excluded else 'Nee',
            'Reden uitsluiting': t.exclusion_reason,
            'ID': t.id,
            'Bron': t.source_file,
        }
        data.append(row)

    df = pd.DataFrame(data)

    # Create directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to Excel
    try:
        # Use openpyxl engine
        df.to_excel(output_path, index=False, engine='openpyxl')
        logger.info(f"Exported {len(transactions)} transactions to {output_path}")
    except Exception as e:
        logger.error(f"Failed to export to Excel: {e}")
        raise


def export_to_csv(
    transactions: List[Transaction],
    output_path: Path,
    fiscal_year: Optional[int] = None,
) -> None:
    """Export transactions to a CSV file.

    Args:
        transactions: List of transactions to export
        output_path: Path where the CSV file should be saved
        fiscal_year: Optional fiscal year to filter transactions
    """
    if not transactions:
        logger.warning("No transactions to export")
        return

    # Filter by year if specified
    if fiscal_year:
        transactions = [
            t for t in transactions 
            if t.booking_date.year == fiscal_year
        ]

    # Sort by date (descending)
    transactions.sort(key=lambda t: t.booking_date, reverse=True)

    # Convert to list of dicts for DataFrame - retain all columns from input
    data = []
    for t in transactions:
        row = {
            'Rekening': t.own_account,
            'Boekingsdatum': t.booking_date,
            'Valutadatum': t.value_date,
            'Rekeninguittrekselnr': t.statement_number,
            'Transactienr': t.transaction_number,
            'Tegenpartij': t.counterparty_name,
            'Rekening Tegenpartij': t.counterparty_iban,
            'Straat en nummer': t.counterparty_street,
            'Postcode en plaats': t.counterparty_postal_city,
            'BIC': t.counterparty_bic,
            'Landcode': t.counterparty_country,
            'Omschrijving': t.description,
            'Bedrag': t.amount,
            'Devies': t.currency,
            'Categorie': t.category,
            'Therapeutisch': t.is_therapeutic,
            'Uitgesloten': t.is_excluded,
            'Reden uitsluiting': t.exclusion_reason,
            'ID': t.id,
            'Bron': t.source_file,
        }
        data.append(row)

    df = pd.DataFrame(data)

    # Create directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    try:
        df.to_csv(output_path, index=False, sep=';', decimal=',')
        logger.info(f"Exported {len(transactions)} transactions to {output_path}")
    except Exception as e:
        logger.error(f"Failed to export to CSV: {e}")
        raise
