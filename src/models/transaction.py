"""Transaction data model."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class Transaction:
    """Represents a single financial movement from bank statement or credit card.

    Attributes:
        id: Unique identifier: {statement_number}-{transaction_number}
        source_file: Original file name (for audit trail)
        source_type: 'bank_csv' or 'mastercard_pdf'
        statement_number: Bank statement number (e.g., "00012")
        transaction_number: Transaction sequence within statement
        booking_date: Date transaction was booked
        value_date: Date transaction was valued
        amount: Transaction amount (negative = expense, positive = income)
        currency: Always "EUR"
        counterparty_name: Name of other party (may be None for fees)
        counterparty_iban: IBAN of other party (when available)
        description: Full transaction description/communication
        category: Assigned category (None = uncategorized)
        matched_rule_id: ID of rule that assigned category (None if manual)
        is_therapeutic: True if revenue from direct patient care
        is_manual_override: True if category was manually assigned
        is_excluded: True if excluded (e.g., Mastercard settlement)
        exclusion_reason: Reason for exclusion
    """

    # Required fields
    id: str
    source_file: str
    source_type: str  # 'bank_csv' or 'mastercard_pdf'
    statement_number: str
    transaction_number: str
    booking_date: date
    value_date: date
    amount: Decimal
    currency: str = "EUR"

    # Optional fields
    counterparty_name: Optional[str] = None
    counterparty_iban: Optional[str] = None
    counterparty_street: Optional[str] = None
    counterparty_postal_city: Optional[str] = None
    counterparty_bic: Optional[str] = None
    counterparty_country: Optional[str] = None
    own_account: Optional[str] = None
    communication: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    matched_rule_id: Optional[str] = None

    # Flags
    is_therapeutic: bool = False
    is_manual_override: bool = False
    is_excluded: bool = False
    exclusion_reason: Optional[str] = None

    def __post_init__(self):
        """Validate transaction data after initialization."""
        # Validate source_type
        if self.source_type not in ('bank_csv', 'mastercard_pdf'):
            raise ValueError(f"Invalid source_type: {self.source_type}")

        # Validate currency
        if self.currency != "EUR":
            raise ValueError(f"Only EUR currency supported, got: {self.currency}")

        # Validate amount is not zero
        if self.amount == Decimal('0'):
            raise ValueError("Transaction amount cannot be zero")

        # Validate is_therapeutic only for Omzet category
        if self.is_therapeutic and self.category != "omzet":
            raise ValueError("is_therapeutic can only be True for 'omzet' category")

    def to_dict(self) -> dict:
        """Convert transaction to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'source_file': self.source_file,
            'source_type': self.source_type,
            'statement_number': self.statement_number,
            'transaction_number': self.transaction_number,
            'booking_date': self.booking_date.isoformat(),
            'value_date': self.value_date.isoformat(),
            'amount': str(self.amount),
            'currency': self.currency,
            'counterparty_name': self.counterparty_name,
            'counterparty_iban': self.counterparty_iban,
            'counterparty_street': self.counterparty_street,
            'counterparty_postal_city': self.counterparty_postal_city,
            'counterparty_bic': self.counterparty_bic,
            'counterparty_country': self.counterparty_country,
            'own_account': self.own_account,
            'communication': self.communication,
            'description': self.description,
            'category': self.category,
            'matched_rule_id': self.matched_rule_id,
            'is_therapeutic': self.is_therapeutic,
            'is_manual_override': self.is_manual_override,
            'is_excluded': self.is_excluded,
            'exclusion_reason': self.exclusion_reason,
        }

    @property
    def counterparty_account(self) -> Optional[str]:
        """Backward-compatible alias for `counterparty_iban`."""
        return self.counterparty_iban

    @classmethod
    def from_dict(cls, data: dict) -> 'Transaction':
        """Create transaction from dictionary."""
        return cls(
            id=data['id'],
            source_file=data['source_file'],
            source_type=data['source_type'],
            statement_number=data['statement_number'],
            transaction_number=data['transaction_number'],
            booking_date=date.fromisoformat(data['booking_date']),
            value_date=date.fromisoformat(data['value_date']),
            amount=Decimal(data['amount']),
            currency=data.get('currency', 'EUR'),
            counterparty_name=data.get('counterparty_name'),
            counterparty_iban=data.get('counterparty_iban'),
            counterparty_street=data.get('counterparty_street'),
            counterparty_postal_city=data.get('counterparty_postal_city'),
            counterparty_bic=data.get('counterparty_bic'),
            counterparty_country=data.get('counterparty_country'),
            own_account=data.get('own_account'),
            communication=data.get('communication'),
            description=data.get('description'),
            category=data.get('category'),
            matched_rule_id=data.get('matched_rule_id'),
            is_therapeutic=data.get('is_therapeutic', False),
            is_manual_override=data.get('is_manual_override', False),
            is_excluded=data.get('is_excluded', False),
            exclusion_reason=data.get('exclusion_reason'),
        )
