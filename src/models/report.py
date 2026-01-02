"""Data models for financial reports."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Literal

ItemType = Literal['income', 'expense', 'depreciation', 'uncategorized']

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
