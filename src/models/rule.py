"""CategoryRule data model."""

from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class CategoryRule:
    """Pattern-matching rule for automatic categorization.

    Attributes:
        id: Unique identifier (auto-generated or user-defined)
        pattern: Match pattern (text or regex)
        pattern_type: 'exact', 'prefix', 'contains', or 'regex'
        match_field: 'counterparty_name', 'description', or 'counterparty_iban'
        target_category: Category ID to assign on match
        priority: Lower = higher priority (first match wins)
        is_therapeutic: If true, also set is_therapeutic flag on match
        enabled: Whether rule is active
        source: 'extracted' (from Excel) or 'manual'
        notes: User notes about this rule
    """

    id: str
    pattern: str
    pattern_type: str  # 'exact', 'prefix', 'contains', 'regex'
    match_field: str  # 'counterparty_name', 'description', 'counterparty_iban'
    target_category: str
    priority: int
    enabled: bool = True
    is_therapeutic: Optional[bool] = None
    source: str = 'manual'  # 'extracted' or 'manual'
    notes: Optional[str] = None

    # Compiled regex pattern (not serialized)
    _compiled_pattern: Optional[re.Pattern] = None

    def __post_init__(self):
        """Validate rule data after initialization."""
        # Validate pattern_type
        valid_pattern_types = ('exact', 'prefix', 'contains', 'regex')
        if self.pattern_type not in valid_pattern_types:
            raise ValueError(f"Invalid pattern_type: {self.pattern_type}. Must be one of {valid_pattern_types}")

        # Validate match_field
        valid_match_fields = ('counterparty_name', 'description', 'counterparty_iban')
        if self.match_field not in valid_match_fields:
            raise ValueError(f"Invalid match_field: {self.match_field}. Must be one of {valid_match_fields}")

        # Validate source
        if self.source not in ('extracted', 'manual'):
            raise ValueError(f"Invalid source: {self.source}")

        # Validate regex pattern compiles
        if self.pattern_type == 'regex':
            try:
                self._compiled_pattern = re.compile(self.pattern, re.IGNORECASE)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {self.pattern}") from e

    def matches(self, value: Optional[str]) -> bool:
        """Check if the pattern matches the given value.

        Args:
            value: The value to match against (e.g., counterparty_name)

        Returns:
            True if the pattern matches, False otherwise
        """
        if value is None:
            return False

        value_lower = value.lower()
        pattern_lower = self.pattern.lower()

        if self.pattern_type == 'exact':
            return value_lower == pattern_lower
        elif self.pattern_type == 'prefix':
            return value_lower.startswith(pattern_lower)
        elif self.pattern_type == 'contains':
            return pattern_lower in value_lower
        elif self.pattern_type == 'regex':
            if self._compiled_pattern is None:
                self._compiled_pattern = re.compile(self.pattern, re.IGNORECASE)
            return bool(self._compiled_pattern.search(value))

        return False

    def to_dict(self) -> dict:
        """Convert rule to dictionary for YAML serialization."""
        result = {
            'id': self.id,
            'pattern': self.pattern,
            'pattern_type': self.pattern_type,
            'match_field': self.match_field,
            'target_category': self.target_category,
            'priority': self.priority,
            'enabled': self.enabled,
            'source': self.source,
        }
        if self.is_therapeutic is not None:
            result['is_therapeutic'] = self.is_therapeutic
        if self.notes:
            result['notes'] = self.notes
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'CategoryRule':
        """Create rule from dictionary."""
        return cls(
            id=data['id'],
            pattern=data['pattern'],
            pattern_type=data['pattern_type'],
            match_field=data['match_field'],
            target_category=data['target_category'],
            priority=data['priority'],
            enabled=data.get('enabled', True),
            is_therapeutic=data.get('is_therapeutic'),
            source=data.get('source', 'manual'),
            notes=data.get('notes'),
        )
