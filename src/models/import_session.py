"""Import session data models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import uuid


@dataclass
class ImportError:
    """Records an error during import.

    Attributes:
        file: Source file name
        line: Line number (for CSV)
        message: Error description
        raw_data: Original data that caused error
    """

    file: str
    message: str
    line: Optional[int] = None
    raw_data: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            'file': self.file,
            'message': self.message,
        }
        if self.line is not None:
            result['line'] = self.line
        if self.raw_data:
            result['raw_data'] = self.raw_data
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'ImportError':
        """Create from dictionary."""
        return cls(
            file=data['file'],
            message=data['message'],
            line=data.get('line'),
            raw_data=data.get('raw_data'),
        )


@dataclass
class ImportSession:
    """Tracks a batch import operation for audit purposes.

    Attributes:
        id: UUID
        timestamp: When import was run
        source_files: Files processed in this session
        transactions_imported: Count of new transactions
        transactions_skipped: Count of duplicates skipped
        transactions_excluded: Count of excluded (e.g., MC settlements)
        errors: Any errors encountered
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    source_files: List[str] = field(default_factory=list)
    transactions_imported: int = 0
    transactions_skipped: int = 0
    transactions_excluded: int = 0
    errors: List[ImportError] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'source_files': self.source_files,
            'transactions_imported': self.transactions_imported,
            'transactions_skipped': self.transactions_skipped,
            'transactions_excluded': self.transactions_excluded,
            'errors': [e.to_dict() for e in self.errors],
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ImportSession':
        """Create from dictionary."""
        return cls(
            id=data['id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            source_files=data['source_files'],
            transactions_imported=data['transactions_imported'],
            transactions_skipped=data['transactions_skipped'],
            transactions_excluded=data['transactions_excluded'],
            errors=[ImportError.from_dict(e) for e in data.get('errors', [])],
        )
