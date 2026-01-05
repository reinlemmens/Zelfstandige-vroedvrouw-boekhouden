"""Session state model for export/import functionality."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

# Current schema version
CURRENT_VERSION = "1.0"


@dataclass
class SessionState:
    """Represents the exportable session state.

    Attributes:
        version: Schema version for migration support
        company_name: User-entered company name
        fiscal_year: Selected fiscal year
        exported_at: ISO timestamp when exported
        transactions: List of transaction dictionaries
        existing_ids: List of transaction IDs for duplicate detection
        categorization_done: Whether auto-categorization has been run
        import_stats: Statistics from last file import
        custom_rules_loaded: True if custom rules.yaml was uploaded
        custom_categories_loaded: True if custom categories.yaml was uploaded
    """

    version: str
    company_name: str
    fiscal_year: int
    exported_at: str
    transactions: List[Dict[str, Any]]
    existing_ids: List[str]
    categorization_done: bool
    import_stats: Optional[Dict[str, Any]] = None
    custom_rules_loaded: bool = False
    custom_categories_loaded: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert session state to dictionary for JSON serialization."""
        return {
            'version': self.version,
            'company_name': self.company_name,
            'fiscal_year': self.fiscal_year,
            'exported_at': self.exported_at,
            'transactions': self.transactions,
            'existing_ids': self.existing_ids,
            'categorization_done': self.categorization_done,
            'import_stats': self.import_stats,
            'custom_rules_loaded': self.custom_rules_loaded,
            'custom_categories_loaded': self.custom_categories_loaded,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionState':
        """Create SessionState from dictionary."""
        return cls(
            version=data.get('version', '1.0'),
            company_name=data.get('company_name', 'sessie'),
            fiscal_year=data['fiscal_year'],
            exported_at=data.get('exported_at', ''),
            transactions=data.get('transactions', []),
            existing_ids=data.get('existing_ids', []),
            categorization_done=data.get('categorization_done', False),
            import_stats=data.get('import_stats'),
            custom_rules_loaded=data.get('custom_rules_loaded', False),
            custom_categories_loaded=data.get('custom_categories_loaded', False),
        )


def validate_state_dict(data: Dict[str, Any]) -> tuple[bool, str]:
    """Validate that a dictionary contains valid session state data.

    Args:
        data: Dictionary to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['fiscal_year', 'transactions']

    for field_name in required_fields:
        if field_name not in data:
            return False, f"Vereist veld ontbreekt: {field_name}"

    if not isinstance(data.get('fiscal_year'), int):
        return False, "fiscal_year moet een getal zijn"

    if not isinstance(data.get('transactions'), list):
        return False, "transactions moet een lijst zijn"

    return True, ""


def validate_version(version: str) -> tuple[bool, str]:
    """Validate that a version string is supported.

    Args:
        version: Version string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    supported_versions = ['1.0']

    if version not in supported_versions:
        return False, f"Versie {version} wordt niet ondersteund"

    return True, ""
