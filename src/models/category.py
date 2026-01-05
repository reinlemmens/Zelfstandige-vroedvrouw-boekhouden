"""Category data model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Category:
    """Predefined expense/income category for Belgian tax filing.

    Attributes:
        id: Unique identifier (slug form, e.g., "huur-onroerend-goed")
        name: Display name (Dutch, e.g., "Huur onroerend goed")
        type: 'income', 'expense', or 'excluded' (owner withdrawals, corrections)
        tax_deductible: Whether expense is tax-deductible
        deductibility_pct: Percentage deductible (100 if fully deductible)
        description: Help text for user
    """

    id: str
    name: str
    type: str  # 'income', 'expense', or 'excluded'
    tax_deductible: bool
    deductibility_pct: int = 100
    description: Optional[str] = None

    def __post_init__(self):
        """Validate category data after initialization."""
        if self.type not in ('income', 'expense', 'excluded'):
            raise ValueError(f"Invalid category type: {self.type}")

    def to_dict(self) -> dict:
        """Convert category to dictionary for JSON/YAML serialization."""
        result = {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'tax_deductible': self.tax_deductible,
        }
        if self.deductibility_pct != 100:
            result['deductibility_pct'] = self.deductibility_pct
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
            deductibility_pct=data.get('deductibility_pct', 100),
            description=data.get('description'),
        )
