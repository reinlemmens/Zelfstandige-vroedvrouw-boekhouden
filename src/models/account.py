"""Account configuration data model."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Partner:
    """Represents a partner in a Maatschap (Belgian partnership).

    Attributes:
        name: Partner name (individual or BV)
        iban: Partner's bank account IBAN
    """

    name: str
    iban: str

    def to_dict(self) -> dict:
        """Convert partner to dictionary for YAML serialization."""
        return {
            'name': self.name,
            'iban': self.iban,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Partner':
        """Create partner from dictionary."""
        return cls(
            name=data['name'],
            iban=data['iban'],
        )


@dataclass
class Account:
    """Configuration for a bank account.

    Supports both standard accounts (eenmanszaak) and Maatschap (partnership) accounts.
    For Maatschap accounts, description-based rules take priority over counterparty rules.

    Attributes:
        id: Unique identifier (slug form, e.g., "goedele", "meraki")
        name: Display name (e.g., "Vroedvrouw Goedele")
        iban: IBAN (e.g., "BE05 0636 4778 9475")
        account_type: 'standard' or 'maatschap'
        partners: List of partners (required for Maatschap accounts)
    """

    id: str
    name: str
    iban: str
    account_type: str  # 'standard' or 'maatschap'
    partners: List[Partner] = field(default_factory=list)

    def __post_init__(self):
        """Validate account data after initialization."""
        if self.account_type not in ('standard', 'maatschap'):
            raise ValueError(f"Invalid account_type: {self.account_type}")

        if self.account_type == 'maatschap' and len(self.partners) < 2:
            raise ValueError("Maatschap accounts must have at least 2 partners")

    @property
    def is_maatschap(self) -> bool:
        """Check if this is a Maatschap (partnership) account."""
        return self.account_type == 'maatschap'

    @property
    def normalized_iban(self) -> str:
        """Get IBAN without spaces for comparison."""
        return self.iban.replace(' ', '').upper()

    def to_dict(self) -> dict:
        """Convert account to dictionary for YAML serialization."""
        result = {
            'id': self.id,
            'name': self.name,
            'iban': self.iban,
            'account_type': self.account_type,
        }
        if self.partners:
            result['partners'] = [p.to_dict() for p in self.partners]
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'Account':
        """Create account from dictionary."""
        partners = []
        if 'partners' in data:
            partners = [Partner.from_dict(p) for p in data['partners']]

        return cls(
            id=data['id'],
            name=data['name'],
            iban=data['iban'],
            account_type=data['account_type'],
            partners=partners,
        )
