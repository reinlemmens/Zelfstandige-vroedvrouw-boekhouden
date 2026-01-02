"""Extract categorization rules from historical Excel files."""

import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from src.models.rule import CategoryRule

logger = logging.getLogger(__name__)

# Category name to ID mapping (Dutch names from Excel -> slug IDs)
CATEGORY_NAME_TO_ID = {
    'omzet': 'omzet',
    'admin kosten': 'admin-kosten',
    'bankkosten': 'bankkosten',
    'boeken en tijdschriften': 'boeken-en-tijdschriften',
    'bureelbenodigdheden': 'bureelbenodigdheden',
    'drukwerk en publiciteit': 'drukwerk-en-publiciteit',
    'huur onroerend goed': 'huur-onroerend-goed',
    'interne storting': 'interne-storting',
    'investeringen over 3 jaar': 'investeringen-over-3-jaar',
    'klein materiaal': 'klein-materiaal',
    'kosten opleiding en vorming': 'kosten-opleiding-en-vorming',
    'licenties software': 'licenties-software',
    'loon': 'loon',
    'maatschap huis van meraki': 'maatschap-huis-van-meraki',
    'medisch materiaal': 'medisch-materiaal',
    'onthaal': 'onthaal',
    'relatiegeschenken': 'relatiegeschenken',
    'restaurant': 'restaurant',
    'sociale bijdragen': 'sociale-bijdragen',
    'telefonie': 'telefonie',
    'verkeerde rekening': 'verkeerde-rekening',
    'verzekering beroepsaansprakelijkheid': 'verzekering-beroepsaansprakelijkheid',
    'vrij aanvullend pensioen zelfstandigen': 'vapz',
    'vapz': 'vapz',
    'vervoer': 'vervoer',
    'mastercard': 'mastercard',
    'sponsoring': 'sponsoring',
}


class RuleExtractor:
    """Extract categorization rules from historical Excel data."""

    def __init__(self, min_occurrences: int = 2):
        """Initialize rule extractor.

        Args:
            min_occurrences: Minimum times a counterparty must appear to create a rule
        """
        self.min_occurrences = min_occurrences

    def extract_from_excel(
        self,
        file_path: Path,
        sheet_name: str = "Verrichtingen",
    ) -> Tuple[List[CategoryRule], List[Dict]]:
        """Extract rules from a single Excel file.

        Args:
            file_path: Path to Excel file
            sheet_name: Name of sheet with transactions (supports wildcards)

        Returns:
            Tuple of (list of rules, list of ambiguous patterns)
        """
        file_path = Path(file_path)

        try:
            # Get all sheet names
            xl = pd.ExcelFile(file_path)
            matching_sheets = [s for s in xl.sheet_names if sheet_name.lower() in s.lower()]

            if not matching_sheets:
                logger.warning(f"No sheets matching '{sheet_name}' in {file_path}")
                return [], []

            all_mappings = defaultdict(lambda: defaultdict(int))

            for sheet in matching_sheets:
                df = pd.read_excel(file_path, sheet_name=sheet)
                self._extract_mappings_from_df(df, all_mappings)

            return self._generate_rules(all_mappings)

        except Exception as e:
            logger.error(f"Error extracting from {file_path}: {e}")
            return [], []

    def _extract_mappings_from_df(
        self,
        df: pd.DataFrame,
        mappings: Dict[str, Dict[str, int]],
    ) -> None:
        """Extract counterparty -> category mappings from DataFrame.

        Args:
            df: DataFrame with transaction data
            mappings: Dictionary to update with mappings
        """
        # Find the counterparty and category columns
        counterparty_col = None
        category_col = None

        for col in df.columns:
            col_lower = str(col).lower()
            if 'tegenpartij' in col_lower or 'naam' in col_lower:
                counterparty_col = col
            elif 'categorie' in col_lower or 'category' in col_lower or 'rubriek' in col_lower:
                category_col = col

        if counterparty_col is None or category_col is None:
            logger.warning(f"Could not find counterparty or category columns in DataFrame")
            return

        for _, row in df.iterrows():
            counterparty = str(row.get(counterparty_col, '')).strip()
            category = str(row.get(category_col, '')).strip()

            if not counterparty or not category or counterparty == 'nan' or category == 'nan':
                continue

            # Normalize counterparty name for pattern matching
            normalized = self._normalize_name(counterparty)
            if not normalized:
                continue

            # Normalize category to ID
            category_id = self._normalize_category(category)
            if not category_id:
                continue

            mappings[normalized][category_id] += 1

    def _normalize_name(self, name: str) -> str:
        """Normalize counterparty name for pattern matching.

        Args:
            name: Raw counterparty name

        Returns:
            Normalized name for use as pattern
        """
        # Remove extra whitespace
        name = ' '.join(name.split())

        # Skip very short names
        if len(name) < 3:
            return ''

        # Skip if mostly numbers
        if sum(c.isdigit() for c in name) > len(name) * 0.5:
            return ''

        return name

    def _normalize_category(self, category: str) -> Optional[str]:
        """Normalize category name to ID.

        Args:
            category: Category name from Excel

        Returns:
            Category ID or None if not recognized
        """
        category_lower = category.lower().strip()

        # Direct match
        if category_lower in CATEGORY_NAME_TO_ID:
            return CATEGORY_NAME_TO_ID[category_lower]

        # Fuzzy match
        for name, cat_id in CATEGORY_NAME_TO_ID.items():
            if name in category_lower or category_lower in name:
                return cat_id

        logger.debug(f"Unknown category: {category}")
        return None

    def _generate_rules(
        self,
        mappings: Dict[str, Dict[str, int]],
    ) -> Tuple[List[CategoryRule], List[Dict]]:
        """Generate rules from counterparty->category mappings.

        Args:
            mappings: Dictionary of counterparty -> {category -> count}

        Returns:
            Tuple of (list of rules, list of ambiguous patterns)
        """
        rules = []
        ambiguous = []
        priority = 10

        for pattern, categories in sorted(mappings.items(), key=lambda x: -sum(x[1].values())):
            total_count = sum(categories.values())

            # Skip if below minimum occurrences
            if total_count < self.min_occurrences:
                continue

            # Check for ambiguity
            if len(categories) > 1:
                # Find dominant category
                dominant_cat = max(categories.items(), key=lambda x: x[1])
                dominant_ratio = dominant_cat[1] / total_count

                if dominant_ratio < 0.8:
                    # Too ambiguous - flag for manual review
                    ambiguous.append({
                        'pattern': pattern,
                        'categories': dict(categories),
                        'total': total_count,
                    })
                    continue

                # Use dominant category
                target_category = dominant_cat[0]
            else:
                target_category = list(categories.keys())[0]

            # Create rule
            rule_id = f"rule-{len(rules) + 1:03d}"
            rule = CategoryRule(
                id=rule_id,
                pattern=pattern,
                pattern_type='contains',
                match_field='counterparty_name',
                target_category=target_category,
                priority=priority,
                enabled=True,
                source='extracted',
            )
            rules.append(rule)
            priority += 1

        logger.info(f"Generated {len(rules)} rules, {len(ambiguous)} ambiguous patterns")
        return rules, ambiguous


def extract_rules_from_excel_files(
    files: List[Path],
    sheet_name: str = "Verrichtingen",
    min_occurrences: int = 2,
) -> Tuple[List[CategoryRule], List[Dict]]:
    """Extract rules from multiple Excel files.

    Args:
        files: List of Excel file paths
        sheet_name: Sheet name pattern to search for
        min_occurrences: Minimum occurrences to create a rule

    Returns:
        Tuple of (combined rules, combined ambiguous patterns)
    """
    extractor = RuleExtractor(min_occurrences=min_occurrences)
    all_rules = []
    all_ambiguous = []

    for file_path in files:
        file_path = Path(file_path)
        if not file_path.suffix.lower() in ('.xlsx', '.xls'):
            logger.warning(f"Skipping non-Excel file: {file_path}")
            continue

        rules, ambiguous = extractor.extract_from_excel(file_path, sheet_name)
        all_rules.extend(rules)
        all_ambiguous.extend(ambiguous)

    # Deduplicate rules by pattern
    seen_patterns = set()
    unique_rules = []
    for rule in all_rules:
        if rule.pattern.lower() not in seen_patterns:
            seen_patterns.add(rule.pattern.lower())
            unique_rules.append(rule)

    # Re-number priorities
    for i, rule in enumerate(unique_rules):
        rule.priority = (i + 1) * 10
        rule.id = f"rule-{i + 1:03d}"

    return unique_rules, all_ambiguous
