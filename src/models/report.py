"""Data models for financial reports."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Literal

ItemType = Literal['income', 'expense', 'depreciation', 'uncategorized']


@dataclass
class DisallowedExpenseItem:
    """Represents a disallowed expense (verworpen uitgave) for tax purposes."""
    category: str
    total_amount: Decimal  # Total expense amount
    deductible_pct: int  # Percentage that IS deductible
    deductible_amount: Decimal  # Amount that IS deductible
    disallowed_amount: Decimal  # Amount that is NOT deductible (verworpen)


@dataclass
class ReportLineItem:
    """Represents a single line item in a financial report."""
    category: str
    amount: Decimal
    item_type: ItemType
    sub_items: List['ReportLineItem'] = field(default_factory=list)


@dataclass
class Report:
    """Represents a full P&L statement for a fiscal year."""
    fiscal_year: int
    income_items: List[ReportLineItem] = field(default_factory=list)
    expense_items: List[ReportLineItem] = field(default_factory=list)
    depreciation_items: List[ReportLineItem] = field(default_factory=list)
    uncategorized_items: List[ReportLineItem] = field(default_factory=list)
    disallowed_expenses: List[DisallowedExpenseItem] = field(default_factory=list)
    verkeerde_rekening_items: List[ReportLineItem] = field(default_factory=list)

    @property
    def total_income(self) -> Decimal:
        """Calculates the total income."""
        return sum(item.amount for item in self.income_items)

    @property
    def total_expenses(self) -> Decimal:
        """Calculates the total expenses, including depreciation."""
        total = sum(item.amount for item in self.expense_items)
        total += sum(item.amount for item in self.depreciation_items)
        return total

    @property
    def profit_loss(self) -> Decimal:
        """Calculates the final profit or loss from categorized items."""
        return self.total_income + self.total_expenses # Expenses are negative

    @property
    def total_uncategorized(self) -> Decimal:
        """Calculates the total of uncategorized transactions."""
        return sum(item.amount for item in self.uncategorized_items)

    @property
    def total_disallowed(self) -> Decimal:
        """Calculates the total disallowed expenses (verworpen uitgaven)."""
        return sum(item.disallowed_amount for item in self.disallowed_expenses)

    @property
    def verkeerde_rekening_balance(self) -> Decimal:
        """Net balance of verkeerde-rekening transactions.

        Zero = balanced (expenses match reimbursements)
        Negative = unreimbursed expenses
        Positive = over-reimbursed
        """
        if not self.verkeerde_rekening_items:
            return Decimal(0)
        return sum(item.amount for item in self.verkeerde_rekening_items)

    @property
    def has_data_quality_warnings(self) -> bool:
        """Check if any data quality warnings should be displayed."""
        return self.total_uncategorized != 0 or self.verkeerde_rekening_balance != 0
