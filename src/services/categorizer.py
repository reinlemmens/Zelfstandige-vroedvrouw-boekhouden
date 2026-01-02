"""Transaction categorization service."""

import logging
from collections import Counter
from typing import Dict, List, Optional, Tuple

from src.models.transaction import Transaction
from src.models.rule import CategoryRule

logger = logging.getLogger(__name__)


class Categorizer:
    """Apply categorization rules to transactions."""

    def __init__(self, rules: List[CategoryRule]):
        """Initialize categorizer with rules.

        Args:
            rules: List of categorization rules (should be sorted by priority)
        """
        # Sort rules by priority (lower = higher priority)
        self.rules = sorted(rules, key=lambda r: r.priority)
        logger.debug(f"Initialized categorizer with {len(self.rules)} rules")

    def categorize(
        self,
        transaction: Transaction,
        force: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """Apply rules to categorize a single transaction.

        Args:
            transaction: Transaction to categorize
            force: If True, re-categorize even if already categorized

        Returns:
            Tuple of (was_categorized, matched_rule_id)
        """
        # Skip if already categorized and not forcing
        if transaction.category is not None and not force:
            return False, None

        # Skip if excluded
        if transaction.is_excluded:
            return False, None

        # Skip if manually overridden and not forcing
        if transaction.is_manual_override and not force:
            return False, None

        # Try each rule in priority order
        for rule in self.rules:
            if not rule.enabled:
                continue

            # Get the field value to match against
            field_value = self._get_field_value(transaction, rule.match_field)

            if rule.matches(field_value):
                # Apply the category
                transaction.category = rule.target_category
                transaction.matched_rule_id = rule.id
                transaction.is_manual_override = False

                # Apply therapeutic flag if rule specifies it
                if rule.is_therapeutic is not None:
                    transaction.is_therapeutic = rule.is_therapeutic

                logger.debug(
                    f"Transaction {transaction.id} matched rule {rule.id} -> {rule.target_category}"
                )
                return True, rule.id

        return False, None

    def _get_field_value(self, transaction: Transaction, field: str) -> Optional[str]:
        """Get the value of a transaction field for matching.

        Args:
            transaction: Transaction to get field from
            field: Field name to get

        Returns:
            Field value or None
        """
        if field == 'counterparty_name':
            return transaction.counterparty_name
        elif field == 'description':
            return transaction.description
        elif field == 'counterparty_iban':
            return transaction.counterparty_iban
        else:
            logger.warning(f"Unknown match field: {field}")
            return None

    def categorize_all(
        self,
        transactions: List[Transaction],
        force: bool = False,
    ) -> Dict[str, any]:
        """Categorize multiple transactions.

        Args:
            transactions: List of transactions to categorize
            force: If True, re-categorize all transactions

        Returns:
            Dictionary with categorization statistics
        """
        categorized_count = 0
        uncategorized_count = 0
        skipped_count = 0
        rules_applied: Counter = Counter()

        for tx in transactions:
            # Skip excluded transactions
            if tx.is_excluded:
                skipped_count += 1
                continue

            was_categorized, rule_id = self.categorize(tx, force=force)

            if was_categorized:
                categorized_count += 1
                if rule_id:
                    rules_applied[rule_id] += 1
            elif tx.category is None:
                uncategorized_count += 1

        result = {
            'categorized': categorized_count,
            'uncategorized': uncategorized_count,
            'skipped': skipped_count,
            'rules_applied': dict(rules_applied),
        }

        logger.info(
            f"Categorization complete: {categorized_count} categorized, "
            f"{uncategorized_count} uncategorized, {skipped_count} skipped"
        )

        return result


def categorize_transactions(
    transactions: List[Transaction],
    rules: List[CategoryRule],
    force: bool = False,
) -> Tuple[List[Transaction], Dict[str, any]]:
    """Convenience function to categorize transactions with rules.

    Args:
        transactions: List of transactions to categorize
        rules: List of categorization rules
        force: If True, re-categorize all transactions

    Returns:
        Tuple of (categorized transactions, statistics dict)
    """
    categorizer = Categorizer(rules)
    stats = categorizer.categorize_all(transactions, force=force)
    return transactions, stats
