"""Belgian number parsing helpers."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


_HAS_DIGIT_RE = re.compile(r"\d")


def parse_belgian_amount(value: str) -> Decimal:
    """Convert Belgian number format (1.234,56) to Decimal."""
    if value is None:
        raise ValueError("Amount is required")

    text = str(value).strip()
    if not text:
        raise ValueError("Amount is required")

    text = text.replace("\u00a0", " ").strip()
    text = text.replace("EUR", "").replace("€", "").strip()
    text = text.replace(" ", "")

    sign = ""
    if text.endswith("-"):
        sign = "-"
        text = text[:-1]
    elif text.endswith("+"):
        text = text[:-1]

    if text.startswith(("+", "-")):
        sign = "-" if text.startswith("-") else sign
        text = text[1:]

    if not _HAS_DIGIT_RE.search(text):
        raise ValueError(f"Invalid Belgian amount: {value}")

    normalized = text.replace(".", "").replace(",", ".")
    normalized = f"{sign}{normalized}"

    try:
        return Decimal(normalized)
    except InvalidOperation:
        raise ValueError(f"Invalid Belgian amount: {value}") from None
