"""Transaction categorization service."""

import logging
from collections import Counter
from typing import Callable, Dict, List, Optional, Tuple

from src.models.transaction import Transaction
from src.models.rule import CategoryRule

logger = logging.getLogger(__name__)


class Categorizer:
    """Apply categorization rules to transactions.

    Supports two-phase matching for Maatschap (partnership) accounts:
    - For Maatschap accounts: description rules are tried first, then counterparty rules
    - For standard accounts: all rules are applied in priority order (existing behavior)
    """

    def __init__(
        self,
        rules: List[CategoryRule],
        get_account_type: Optional[Callable[[str], str]] = None,
    ):
        """Initialize categorizer with rules.

        Args:
            rules: List of categorization rules (should be sorted by priority)
            get_account_type: Optional function to get account type from IBAN.
                              Returns 'maatschap' or 'standard'. If not provided,
                              all accounts are treated as 'standard'.
        """
        # Sort rules by priority (lower = higher priority)
        self.rules = sorted(rules, key=lambda r: r.priority)
        self.get_account_type = get_account_type

        # Pre-filter rules by match_field for two-phase matching
        self.description_rules = [
            r for r in self.rules if r.match_field == 'description'
        ]
        self.counterparty_rules = [
            r for r in self.rules if r.match_field in ('counterparty_name', 'counterparty_iban')
        ]

        logger.debug(
            f"Initialized categorizer with {len(self.rules)} rules "
            f"({len(self.description_rules)} description, {len(self.counterparty_rules)} counterparty)"
        )

    def _get_account_type_for_transaction(self, transaction: Transaction) -> str:
        """Get the account type for a transaction based on its source IBAN.

        Args:
            transaction: Transaction to check

        Returns:
            'maatschap' or 'standard'
        """
        if not self.get_account_type:
            return 'standard'

        iban = transaction.own_account
        if not iban:
            return 'standard'

        return self.get_account_type(iban)

    def _try_rules(
        self,
        transaction: Transaction,
        rules: List[CategoryRule],
    ) -> Tuple[bool, Optional[str]]:
        """Try to match a transaction against a list of rules.

        Args:
            transaction: Transaction to categorize
            rules: List of rules to try

        Returns:
            Tuple of (was_categorized, matched_rule_id)
        """
        for rule in rules:
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

                return True, rule.id

        return False, None

    def categorize(
        self,
        transaction: Transaction,
        force: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """Apply rules to categorize a single transaction.

        For Maatschap accounts, uses two-phase matching:
        1. First, try description-based rules
        2. If no match, fall through to counterparty-based rules

        For standard accounts, applies all rules in priority order.

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

        # Determine account type for this transaction
        account_type = self._get_account_type_for_transaction(transaction)

        if account_type == 'maatschap':
            # Two-phase matching for Maatschap accounts
            # Phase 1: Try description-based rules first
            was_categorized, rule_id = self._try_rules(transaction, self.description_rules)
            if was_categorized:
                logger.debug(
                    f"Transaction {transaction.id} (Maatschap) matched description rule "
                    f"{rule_id} -> {transaction.category}"
                )
                return True, rule_id

            # Phase 2: Fall through to counterparty rules
            was_categorized, rule_id = self._try_rules(transaction, self.counterparty_rules)
            if was_categorized:
                logger.debug(
                    f"Transaction {transaction.id} (Maatschap) matched counterparty rule "
                    f"{rule_id} -> {transaction.category}"
                )
                return True, rule_id

            return False, None
        else:
            # Standard matching: try all rules in priority order
            was_categorized, rule_id = self._try_rules(transaction, self.rules)
            if was_categorized:
                logger.debug(
                    f"Transaction {transaction.id} matched rule {rule_id} -> {transaction.category}"
                )
            return was_categorized, rule_id

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
        maatschap_count = 0
        standard_count = 0

        for tx in transactions:
            # Skip excluded transactions
            if tx.is_excluded:
                skipped_count += 1
                continue

            # Track account type for stats
            account_type = self._get_account_type_for_transaction(tx)
            if account_type == 'maatschap':
                maatschap_count += 1
            else:
                standard_count += 1

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
            'maatschap_transactions': maatschap_count,
            'standard_transactions': standard_count,
        }

        logger.info(
            f"Categorization complete: {categorized_count} categorized, "
            f"{uncategorized_count} uncategorized, {skipped_count} skipped "
            f"({maatschap_count} Maatschap, {standard_count} standard)"
        )

        return result


def categorize_transactions(
    transactions: List[Transaction],
    rules: List[CategoryRule],
    force: bool = False,
    get_account_type: Optional[Callable[[str], str]] = None,
) -> Tuple[List[Transaction], Dict[str, any]]:
    """Convenience function to categorize transactions with rules.

    Args:
        transactions: List of transactions to categorize
        rules: List of categorization rules
        force: If True, re-categorize all transactions
        get_account_type: Optional function to get account type from IBAN

    Returns:
        Tuple of (categorized transactions, statistics dict)
    """
    categorizer = Categorizer(rules, get_account_type=get_account_type)
    stats = categorizer.categorize_all(transactions, force=force)
    return transactions, stats
