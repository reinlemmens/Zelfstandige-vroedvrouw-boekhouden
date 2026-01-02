"""Category data model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Category:
    """Predefined expense/income category for Belgian tax filing.

    Attributes:
        id: Unique identifier (slug form, e.g., "huur-onroerend-goed")
        name: Display name (Dutch, e.g., "Huur onroerend goed")
        type: 'income' or 'expense'
        tax_deductible: Whether expense is tax-deductible
        description: Help text for user
    """

    id: str
    name: str
    type: str  # 'income' or 'expense'
    tax_deductible: bool
    description: Optional[str] = None

    def __post_init__(self):
        """Validate category data after initialization."""
        if self.type not in ('income', 'expense'):
            raise ValueError(f"Invalid category type: {self.type}")

    def to_dict(self) -> dict:
        """Convert category to dictionary for YAML serialization."""
        result = {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'tax_deductible': self.tax_deductible,
        }
        if self.description:
            result['description'] = self.description
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'Category':
        """Create category from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            type=data['type'],
            tax_deductible=data['tax_deductible'],
            description=data.get('description'),
        )
