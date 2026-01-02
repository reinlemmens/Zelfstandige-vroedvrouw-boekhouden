"""Persistence service for loading and saving data."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from src.models.category import Category
from src.models.rule import CategoryRule
from src.models.transaction import Transaction
from src.models.import_session import ImportSession

logger = logging.getLogger(__name__)


class PersistenceService:
    """Service for loading and saving transactions, rules, and categories."""

    def __init__(
        self,
        data_dir: str = "data/output",
        rules_file: str = "config/rules.yaml",
        categories_file: str = "config/categories.yaml",
    ):
        """Initialize persistence service.

        Args:
            data_dir: Directory for transaction data
            rules_file: Path to rules YAML file
            categories_file: Path to categories YAML file
        """
        self.data_dir = Path(data_dir)
        self.rules_file = Path(rules_file)
        self.categories_file = Path(categories_file)

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

    @property
    def transactions_file(self) -> Path:
        """Path to transactions JSON file."""
        return self.data_dir / "transactions.json"

    # -------------------------------------------------------------------------
    # Categories
    # -------------------------------------------------------------------------

    def load_categories(self) -> Dict[str, Category]:
        """Load categories from YAML file.

        Returns:
            Dictionary mapping category ID to Category object
        """
        if not self.categories_file.exists():
            logger.warning(f"Categories file not found: {self.categories_file}")
            return {}

        with open(self.categories_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        categories = {}
        for cat_data in data.get('categories', []):
            cat = Category.from_dict(cat_data)
            categories[cat.id] = cat

        logger.info(f"Loaded {len(categories)} categories")
        return categories

    def get_category_ids(self) -> List[str]:
        """Get list of valid category IDs."""
        return list(self.load_categories().keys())

    def validate_category(self, category_id: str) -> bool:
        """Check if category ID is valid."""
        return category_id in self.load_categories()

    # -------------------------------------------------------------------------
    # Rules
    # -------------------------------------------------------------------------

    def load_rules(self) -> List[CategoryRule]:
        """Load categorization rules from YAML file.

        Returns:
            List of CategoryRule objects sorted by priority
        """
        if not self.rules_file.exists():
            logger.warning(f"Rules file not found: {self.rules_file}")
            return []

        with open(self.rules_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        rules = []
        for rule_data in data.get('rules', []):
            try:
                rule = CategoryRule.from_dict(rule_data)
                if rule.enabled:
                    rules.append(rule)
            except ValueError as e:
                logger.error(f"Invalid rule {rule_data.get('id', 'unknown')}: {e}")

        # Sort by priority (lower = higher priority)
        rules.sort(key=lambda r: r.priority)

        logger.info(f"Loaded {len(rules)} enabled rules")
        return rules

    def save_rules(self, rules: List[CategoryRule]) -> None:
        """Save categorization rules to YAML file.

        Args:
            rules: List of CategoryRule objects to save
        """
        data = {
            'version': '1.0',
            'rules': [rule.to_dict() for rule in rules],
        }

        self.rules_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.rules_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        logger.info(f"Saved {len(rules)} rules to {self.rules_file}")

    def add_rule(self, rule: CategoryRule) -> None:
        """Add a new rule to the rules file.

        Args:
            rule: The rule to add
        """
        rules = self.load_rules()
        rules.append(rule)
        self.save_rules(rules)

    # -------------------------------------------------------------------------
    # Transactions
    # -------------------------------------------------------------------------

    def load_transactions(self, fiscal_year: Optional[int] = None) -> List[Transaction]:
        """Load transactions from JSON file.

        Args:
            fiscal_year: Optional year to filter transactions

        Returns:
            List of Transaction objects
        """
        if not self.transactions_file.exists():
            logger.info(f"No transactions file found: {self.transactions_file}")
            return []

        with open(self.transactions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        transactions = []
        for tx_data in data.get('transactions', []):
            try:
                tx = Transaction.from_dict(tx_data)
                # Filter by fiscal year if specified
                if fiscal_year is None or tx.booking_date.year == fiscal_year:
                    transactions.append(tx)
            except Exception as e:
                logger.error(f"Error loading transaction {tx_data.get('id', 'unknown')}: {e}")

        logger.info(f"Loaded {len(transactions)} transactions")
        return transactions

    def save_transactions(
        self,
        transactions: List[Transaction],
        fiscal_year: int,
        import_sessions: Optional[List[ImportSession]] = None,
    ) -> None:
        """Save transactions to JSON file.

        Args:
            transactions: List of Transaction objects to save
            fiscal_year: Fiscal year for the data
            import_sessions: Optional list of import session records
        """
        data = {
            'version': '1.0',
            'fiscal_year': fiscal_year,
            'exported_at': datetime.now().isoformat(),
            'transactions': [tx.to_dict() for tx in transactions],
            'import_sessions': [s.to_dict() for s in (import_sessions or [])],
        }

        self.data_dir.mkdir(parents=True, exist_ok=True)

        with open(self.transactions_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(transactions)} transactions to {self.transactions_file}")

    def get_transaction_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """Find a transaction by its ID.

        Args:
            transaction_id: The transaction ID to find

        Returns:
            Transaction if found, None otherwise
        """
        transactions = self.load_transactions()
        for tx in transactions:
            if tx.id == transaction_id:
                return tx
        return None

    def update_transaction(self, transaction: Transaction, fiscal_year: int) -> bool:
        """Update a transaction in the data file.

        Args:
            transaction: The updated transaction
            fiscal_year: Fiscal year for the data

        Returns:
            True if transaction was found and updated, False otherwise
        """
        transactions = self.load_transactions()

        for i, tx in enumerate(transactions):
            if tx.id == transaction.id:
                transactions[i] = transaction
                self.save_transactions(transactions, fiscal_year)
                return True

        return False

    def get_existing_transaction_ids(self) -> set:
        """Get set of existing transaction IDs for duplicate detection.

        Returns:
            Set of transaction ID strings
        """
        transactions = self.load_transactions()
        return {tx.id for tx in transactions}

    # -------------------------------------------------------------------------
    # Settings
    # -------------------------------------------------------------------------

    def load_settings(self, settings_file: str = "config/settings.yaml") -> dict:
        """Load application settings from YAML file.

        Args:
            settings_file: Path to settings file

        Returns:
            Dictionary of settings
        """
        settings_path = Path(settings_file)
        if not settings_path.exists():
            logger.warning(f"Settings file not found: {settings_path}")
            return {}

        with open(settings_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
