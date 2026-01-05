"""PLV Web Interface - Streamlit Application.

Web-based interface for Belgian midwife financial reporting.
Allows users to upload bank statements, categorize transactions,
view P&L summaries, and download reports.
"""

import io
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Set

import streamlit as st
import yaml

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.models.transaction import Transaction
from src.models.rule import CategoryRule
from src.models.category import Category
from src.models.report import Report
from src.services.csv_importer import CSVImporter
from src.services.pdf_importer import PDFImporter
from src.services.categorizer import Categorizer
from src.services.report_generator import ReportGenerator
from src.services.session_export import (
    create_export_zip,
    get_export_filename,
    validate_import_zip,
    import_session_zip,
    session_to_dict,
    dict_to_session,
)

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="PLV - Vroedvrouw Boekhouding",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# Constants
# =============================================================================

CURRENT_YEAR = datetime.now().year
AVAILABLE_YEARS = [2024, 2025, CURRENT_YEAR] if CURRENT_YEAR > 2025 else [2024, 2025]
# Default to previous year in Jan-Mar (typically processing last year's books), otherwise current year
DEFAULT_FISCAL_YEAR = CURRENT_YEAR - 1 if datetime.now().month <= 3 else CURRENT_YEAR
if DEFAULT_FISCAL_YEAR not in AVAILABLE_YEARS:
    DEFAULT_FISCAL_YEAR = max(AVAILABLE_YEARS)

# Default Belgian expense categories for independent midwives
DEFAULT_CATEGORIES = [
    # Income
    Category(id='omzet', name='Omzet', type='income', tax_deductible=False, description='Revenue from services (RIZIV, patients, hospitals)'),

    # Expenses - Fully deductible
    Category(id='admin-kosten', name='Admin kosten', type='expense', tax_deductible=True, description='Administrative costs (accountant, etc.)'),
    Category(id='bankkosten', name='Bankkosten', type='expense', tax_deductible=True, description='Bank fees and charges'),
    Category(id='boeken-en-tijdschriften', name='Boeken en tijdschriften', type='expense', tax_deductible=True, description='Professional books and journals'),
    Category(id='bureelbenodigdheden', name='Bureelbenodigdheden', type='expense', tax_deductible=True, description='Office supplies'),
    Category(id='drukwerk-en-publiciteit', name='Drukwerk en publiciteit', type='expense', tax_deductible=True, description='Printing and advertising'),
    Category(id='huur-onroerend-goed', name='Huur onroerend goed', type='expense', tax_deductible=True, description='Practice rent'),
    Category(id='investeringen-over-3-jaar', name='Investeringen (afschrijving)', type='expense', tax_deductible=True, description='Equipment depreciated over 3+ years'),
    Category(id='klein-materiaal', name='Klein materiaal', type='expense', tax_deductible=True, description='Small equipment (<500 EUR)'),
    Category(id='kosten-opleiding-en-vorming', name='Opleiding en vorming', type='expense', tax_deductible=True, description='Training, courses, conferences'),
    Category(id='licenties-software', name='Licenties en software', type='expense', tax_deductible=True, description='Software subscriptions'),
    Category(id='medisch-materiaal', name='Medisch materiaal', type='expense', tax_deductible=True, description='Medical supplies and consumables'),
    Category(id='sociale-bijdragen', name='Sociale bijdragen', type='expense', tax_deductible=True, description='Social security contributions'),
    Category(id='telefonie', name='Telefonie en internet', type='expense', tax_deductible=True, description='Phone and internet costs'),
    Category(id='verzekering-beroepsaansprakelijkheid', name='Beroepsverzekering', type='expense', tax_deductible=True, description='Professional liability insurance'),
    Category(id='vapz', name='VAPZ', type='expense', tax_deductible=True, description='Supplementary pension for self-employed'),
    Category(id='vervoer', name='Vervoer', type='expense', tax_deductible=True, description='Transport and travel costs'),
    Category(id='sponsoring', name='Sponsoring', type='expense', tax_deductible=True, description='Sponsorship costs'),
    Category(id='lidmaatschap', name='Lidmaatschap', type='expense', tax_deductible=True, description='Professional memberships (VBOV, etc.)'),
    Category(id='maatschap', name='Maatschap', type='expense', tax_deductible=True, description='Partnership contributions'),

    # Expenses - Partially deductible (Belgian tax rules)
    Category(id='onthaal', name='Onthaal', type='expense', tax_deductible=True, deductibility_pct=50, description='Reception costs (50% deductible)'),
    Category(id='relatiegeschenken', name='Relatiegeschenken', type='expense', tax_deductible=True, deductibility_pct=50, description='Business gifts (50% deductible)'),
    Category(id='restaurant', name='Restaurant', type='expense', tax_deductible=True, deductibility_pct=69, description='Restaurant expenses (69% deductible)'),

    # Excluded from P&L
    Category(id='interne-storting', name='Interne storting', type='excluded', tax_deductible=False, description='Internal bank transfers'),
    Category(id='loon', name='Loon', type='excluded', tax_deductible=False, description='Owner salary withdrawals'),
    Category(id='verkeerde-rekening', name='Verkeerde rekening', type='excluded', tax_deductible=False, description='Private expenses (wrong account)'),
    Category(id='verkeerde-rekening-matched', name='Verkeerde rekening (matched)', type='excluded', tax_deductible=False, description='Matched expense/reimbursement pairs'),
    Category(id='mastercard', name='Mastercard afrekening', type='excluded', tax_deductible=False, description='Credit card settlement (details in statement)'),
    Category(id='prive-opname', name='Privé-opname', type='excluded', tax_deductible=False, description='Private withdrawals'),
    Category(id='voorafbetaling', name='Voorafbetaling belasting', type='excluded', tax_deductible=False, description='Tax prepayments'),
]

# Default categorization rules for Belgian independent midwives
DEFAULT_RULES = [
    # === INCOME: RIZIV/INAMI (health insurance reimbursements) ===
    CategoryRule(id='riziv-niv', pattern='RIZIV|INAMI', pattern_type='regex', match_field='counterparty_name', target_category='omzet', priority=90, is_therapeutic=True),
    CategoryRule(id='riziv-mut', pattern='MUTUALITEIT|MUTUALITE|ZIEKENFONDS', pattern_type='regex', match_field='counterparty_name', target_category='omzet', priority=90, is_therapeutic=True),
    CategoryRule(id='riziv-cm', pattern='CM LEUVEN|CHRISTELIJKE MUTUALITEIT', pattern_type='regex', match_field='counterparty_name', target_category='omzet', priority=90, is_therapeutic=True),
    CategoryRule(id='riziv-bond', pattern='LANDSBOND|NATIONAAL VERBOND', pattern_type='regex', match_field='counterparty_name', target_category='omzet', priority=90, is_therapeutic=True),
    CategoryRule(id='riziv-partena', pattern='PARTENA', pattern_type='contains', match_field='counterparty_name', target_category='omzet', priority=90, is_therapeutic=True),

    # === INCOME: Hospitals and care centers ===
    CategoryRule(id='hospital-uz', pattern='UZ LEUVEN|UZ GENT|UZ BRUSSEL|UZ ANTWERPEN', pattern_type='regex', match_field='counterparty_name', target_category='omzet', priority=85, is_therapeutic=True),
    CategoryRule(id='hospital-az', pattern='^AZ ', pattern_type='regex', match_field='counterparty_name', target_category='omzet', priority=85, is_therapeutic=True),
    CategoryRule(id='hospital-sint', pattern='SINT-.*ZIEKENHUIS|SINT-.*KLINIEK', pattern_type='regex', match_field='counterparty_name', target_category='omzet', priority=85, is_therapeutic=True),
    CategoryRule(id='hospital-imec', pattern='GASTHUISZUSTERS', pattern_type='contains', match_field='counterparty_name', target_category='omzet', priority=85, is_therapeutic=True),

    # === INCOME: Online payments ===
    CategoryRule(id='mollie', pattern='MOLLIE', pattern_type='contains', match_field='counterparty_name', target_category='omzet', priority=80, is_therapeutic=False),

    # === INCOME: More mutualiteiten ===
    CategoryRule(id='solidaris', pattern='SOLIDARIS', pattern_type='contains', match_field='counterparty_name', target_category='omzet', priority=90, is_therapeutic=True),
    CategoryRule(id='onafhankelijk-zf', pattern='ONAFHANKELIJK ZIEKENFONDS|OZ ZIEKENFONDS', pattern_type='regex', match_field='counterparty_name', target_category='omzet', priority=90, is_therapeutic=True),
    CategoryRule(id='liberale-mut', pattern='LIBERALE MUTUALITEIT|LM ', pattern_type='regex', match_field='counterparty_name', target_category='omzet', priority=90, is_therapeutic=True),
    CategoryRule(id='helan', pattern='HELAN', pattern_type='contains', match_field='counterparty_name', target_category='omzet', priority=90, is_therapeutic=True),

    # === SOCIAL CONTRIBUTIONS ===
    CategoryRule(id='acerta-soc', pattern='ACERTA', pattern_type='contains', match_field='counterparty_name', target_category='sociale-bijdragen', priority=80),
    CategoryRule(id='liantis', pattern='LIANTIS', pattern_type='contains', match_field='counterparty_name', target_category='sociale-bijdragen', priority=80),
    CategoryRule(id='xerius', pattern='XERIUS', pattern_type='contains', match_field='counterparty_name', target_category='sociale-bijdragen', priority=80),
    CategoryRule(id='partena-soc', pattern='PARTENA.*SOCIAAL', pattern_type='regex', match_field='counterparty_name', target_category='sociale-bijdragen', priority=80),
    CategoryRule(id='ucm', pattern='UCM', pattern_type='contains', match_field='counterparty_name', target_category='sociale-bijdragen', priority=80),

    # === VAPZ (supplementary pension) ===
    CategoryRule(id='vapz-desc', pattern='VAPZ', pattern_type='contains', match_field='description', target_category='vapz', priority=85),
    CategoryRule(id='vapz-counter', pattern='VAPZ', pattern_type='contains', match_field='counterparty_name', target_category='vapz', priority=85),
    CategoryRule(id='vivium-vapz', pattern='VIVIUM', pattern_type='contains', match_field='counterparty_name', target_category='vapz', priority=75),

    # === PROFESSIONAL INSURANCE ===
    CategoryRule(id='amma', pattern='AMMA', pattern_type='contains', match_field='counterparty_name', target_category='verzekering-beroepsaansprakelijkheid', priority=80),
    CategoryRule(id='axa-pro', pattern='AXA.*BEROEP|BEROEP.*AXA', pattern_type='regex', match_field='description', target_category='verzekering-beroepsaansprakelijkheid', priority=75),

    # === MEMBERSHIPS ===
    CategoryRule(id='vbov', pattern='VBOV|VROEDVROUWEN', pattern_type='regex', match_field='counterparty_name', target_category='lidmaatschap', priority=80),
    CategoryRule(id='orde-artsen', pattern='ORDE VAN', pattern_type='contains', match_field='counterparty_name', target_category='lidmaatschap', priority=75),

    # === BANK FEES ===
    CategoryRule(id='bank-kosten', pattern='BEHEERSKOSTEN|REKENINGKOSTEN|KAARTKOSTEN', pattern_type='regex', match_field='description', target_category='bankkosten', priority=80),
    CategoryRule(id='mastercard-fee', pattern='JAARLIJKSE BIJDRAGE.*CARD', pattern_type='regex', match_field='description', target_category='bankkosten', priority=80),

    # === TELECOM ===
    CategoryRule(id='proximus', pattern='PROXIMUS', pattern_type='contains', match_field='counterparty_name', target_category='telefonie', priority=75),
    CategoryRule(id='telenet', pattern='TELENET', pattern_type='contains', match_field='counterparty_name', target_category='telefonie', priority=75),
    CategoryRule(id='orange', pattern='ORANGE BELGIUM', pattern_type='contains', match_field='counterparty_name', target_category='telefonie', priority=75),
    CategoryRule(id='mobile-vikings', pattern='MOBILE VIKINGS', pattern_type='contains', match_field='counterparty_name', target_category='telefonie', priority=75),

    # === MEDICAL SUPPLIES ===
    CategoryRule(id='medische-wereld', pattern='MEDISCHE WERELD', pattern_type='contains', match_field='counterparty_name', target_category='medisch-materiaal', priority=75),
    CategoryRule(id='apotheek', pattern='APOTHEEK|PHARMACIE', pattern_type='regex', match_field='counterparty_name', target_category='medisch-materiaal', priority=70),

    # === OFFICE SUPPLIES ===
    CategoryRule(id='bol-com', pattern='BOL.COM', pattern_type='contains', match_field='counterparty_name', target_category='bureelbenodigdheden', priority=60),
    CategoryRule(id='amazon', pattern='AMAZON', pattern_type='contains', match_field='counterparty_name', target_category='bureelbenodigdheden', priority=60),

    # === SOFTWARE ===
    CategoryRule(id='google', pattern='GOOGLE', pattern_type='contains', match_field='counterparty_name', target_category='licenties-software', priority=70),
    CategoryRule(id='microsoft', pattern='MICROSOFT', pattern_type='contains', match_field='counterparty_name', target_category='licenties-software', priority=70),
    CategoryRule(id='apple', pattern='APPLE.COM', pattern_type='contains', match_field='counterparty_name', target_category='licenties-software', priority=70),

    # === TRANSPORT ===
    CategoryRule(id='nmbs', pattern='NMBS|SNCB', pattern_type='regex', match_field='counterparty_name', target_category='vervoer', priority=75),
    CategoryRule(id='de-lijn', pattern='DE LIJN', pattern_type='contains', match_field='counterparty_name', target_category='vervoer', priority=75),
    CategoryRule(id='tankstation', pattern='ESSO|SHELL|TOTAL|Q8|TEXACO|LUKOIL', pattern_type='regex', match_field='counterparty_name', target_category='vervoer', priority=70),

    # === TRAINING ===
    CategoryRule(id='opleiding', pattern='OPLEIDING|CURSUS|CONGRES|STUDIEDAG', pattern_type='regex', match_field='description', target_category='kosten-opleiding-en-vorming', priority=70),

    # === EXCLUDED: Internal transfers ===
    CategoryRule(id='eigen-rekening', pattern='EIGEN REKENING', pattern_type='contains', match_field='description', target_category='interne-storting', priority=95),
    CategoryRule(id='overschrijving-eigen', pattern='OVERSCHRIJVING.*EIGEN', pattern_type='regex', match_field='description', target_category='interne-storting', priority=95),

    # === EXCLUDED: Tax prepayments ===
    CategoryRule(id='voorafbetaling', pattern='VOORAFBETALING|VOORAFBETALINGEN', pattern_type='regex', match_field='counterparty_name', target_category='voorafbetaling', priority=90),
    CategoryRule(id='fod-fin', pattern='FOD FINANCIEN|SPF FINANCES', pattern_type='regex', match_field='counterparty_name', target_category='voorafbetaling', priority=85),

    # === EXCLUDED: Mastercard settlement ===
    CategoryRule(id='mastercard-afr', pattern='MASTERCARD.*AFREKENING|AFREKENING.*MASTERCARD', pattern_type='regex', match_field='description', target_category='mastercard', priority=95),
]


# =============================================================================
# Session State Initialization (T004)
# =============================================================================

def init_session_state():
    """Initialize session state variables for the application."""
    if 'transactions' not in st.session_state:
        st.session_state.transactions = []

    if 'existing_ids' not in st.session_state:
        st.session_state.existing_ids = set()

    if 'fiscal_year' not in st.session_state:
        st.session_state.fiscal_year = DEFAULT_FISCAL_YEAR

    if 'categorization_done' not in st.session_state:
        st.session_state.categorization_done = False

    if 'import_stats' not in st.session_state:
        st.session_state.import_stats = None

    if 'categories' not in st.session_state:
        st.session_state.categories = DEFAULT_CATEGORIES.copy()

    if 'rules' not in st.session_state:
        st.session_state.rules = DEFAULT_RULES.copy()

    # Session state export/import variables
    if 'company_name' not in st.session_state:
        st.session_state.company_name = ''

    if 'custom_rules_loaded' not in st.session_state:
        st.session_state.custom_rules_loaded = False

    if 'custom_categories_loaded' not in st.session_state:
        st.session_state.custom_categories_loaded = False

    if 'custom_rules_content' not in st.session_state:
        st.session_state.custom_rules_content = None

    if 'custom_categories_content' not in st.session_state:
        st.session_state.custom_categories_content = None

    if 'uploaded_files_content' not in st.session_state:
        st.session_state.uploaded_files_content = {}


# =============================================================================
# Config Loading Functions (for uploaded YAML files)
# =============================================================================

def parse_categories_yaml(content: bytes) -> List[Category]:
    """Parse categories from uploaded YAML content.

    Args:
        content: Raw bytes from uploaded YAML file

    Returns:
        List of Category objects
    """
    try:
        data = yaml.safe_load(content.decode('utf-8'))

        categories = []
        for cat_data in data.get('categories', []):
            cat = Category(
                id=cat_data['id'],
                name=cat_data['name'],
                type=cat_data.get('type', 'expense'),
                tax_deductible=cat_data.get('tax_deductible', True),
                deductibility_pct=cat_data.get('deductibility_pct', 100),
                description=cat_data.get('description', ''),
            )
            categories.append(cat)

        return categories

    except Exception as e:
        st.error(f"Fout bij laden categorieën: {e}")
        return []


def parse_rules_yaml(content: bytes) -> List[CategoryRule]:
    """Parse categorization rules from uploaded YAML content.

    Args:
        content: Raw bytes from uploaded YAML file

    Returns:
        List of CategoryRule objects
    """
    try:
        data = yaml.safe_load(content.decode('utf-8'))

        rules = []
        for rule_data in data.get('rules', []):
            rule = CategoryRule(
                id=rule_data['id'],
                pattern=rule_data['pattern'],
                pattern_type=rule_data.get('pattern_type', 'contains'),
                match_field=rule_data.get('match_field', 'counterparty_name'),
                target_category=rule_data['target_category'],
                priority=rule_data.get('priority', 50),
                is_therapeutic=rule_data.get('is_therapeutic'),
                enabled=rule_data.get('enabled', True),
            )
            rules.append(rule)

        return rules

    except Exception as e:
        st.error(f"Fout bij laden regels: {e}")
        return []


# =============================================================================
# Belgian Number Formatting Helper (T008)
# =============================================================================

def format_belgian_currency(amount: Decimal, include_symbol: bool = True) -> str:
    """Format a decimal amount in Belgian currency format.

    Belgian format: 1.234,56 EUR (period as thousands separator, comma as decimal)

    Args:
        amount: Decimal amount to format
        include_symbol: Whether to include EUR symbol

    Returns:
        Formatted string
    """
    # Convert to float for formatting
    value = float(amount)

    # Format with 2 decimal places
    abs_value = abs(value)

    # Split into integer and decimal parts
    int_part = int(abs_value)
    dec_part = round((abs_value - int_part) * 100)

    # Format integer part with period as thousands separator
    int_str = f"{int_part:,}".replace(",", ".")

    # Combine with comma as decimal separator
    formatted = f"{int_str},{dec_part:02d}"

    # Add negative sign if needed
    if value < 0:
        formatted = f"-{formatted}"

    # Add EUR symbol if requested
    if include_symbol:
        formatted = f"{formatted} EUR"

    return formatted


def format_belgian_number(value: float, decimals: int = 2) -> str:
    """Format a number in Belgian format (comma as decimal separator).

    Args:
        value: Number to format
        decimals: Number of decimal places

    Returns:
        Formatted string
    """
    abs_value = abs(value)
    int_part = int(abs_value)

    # Format integer part with period as thousands separator
    int_str = f"{int_part:,}".replace(",", ".")

    # Calculate decimal part
    dec_value = abs_value - int_part
    dec_str = f"{dec_value:.{decimals}f}"[2:]  # Remove "0."

    formatted = f"{int_str},{dec_str}"

    if value < 0:
        formatted = f"-{formatted}"

    return formatted


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a percentage in Belgian format.

    Args:
        value: Percentage value (e.g., 50.5 for 50.5%)
        decimals: Number of decimal places

    Returns:
        Formatted string with % symbol
    """
    return f"{format_belgian_number(value, decimals)}%"


# =============================================================================
# Main Application
# =============================================================================

def main():
    """Main application entry point."""
    # Initialize session state
    init_session_state()

    # Application title
    st.title("PLV - Profit & Loss voor Vroedvrouwen")
    st.markdown("*Financieel rapportage voor zelfstandige vroedvrouwen*")

    # Sidebar - Year Selection and Config Upload
    with st.sidebar:
        st.header("Instellingen")

        # Company name input (T037)
        company_name = st.text_input(
            "Bedrijfsnaam",
            value=st.session_state.company_name,
            key="company_name_input",
            placeholder="bijv. Vroedvrouw Goedele",
            help="Wordt gebruikt in de bestandsnaam bij het exporteren van je sessie",
        )

        if company_name != st.session_state.company_name:
            st.session_state.company_name = company_name

        # Fiscal year selector
        fiscal_year = st.selectbox(
            "Boekjaar",
            options=AVAILABLE_YEARS,
            index=AVAILABLE_YEARS.index(st.session_state.fiscal_year),
            key="year_select",
        )

        if fiscal_year != st.session_state.fiscal_year:
            st.session_state.fiscal_year = fiscal_year
            st.rerun()

        # Config upload section
        st.divider()
        st.subheader("Configuratie")

        # Rules upload (optional - override defaults)
        rules_file = st.file_uploader(
            "Upload rules.yaml (optioneel)",
            type=['yaml', 'yml'],
            key="rules_upload",
            help="Vervang de standaardregels met je eigen categorisatieregels.",
        )

        if rules_file is not None:
            rules_content = rules_file.read()
            parsed_rules = parse_rules_yaml(rules_content)
            if parsed_rules and parsed_rules != st.session_state.rules:
                st.session_state.rules = parsed_rules
                st.session_state.categorization_done = False
                st.session_state.custom_rules_loaded = True
                st.session_state.custom_rules_content = rules_content
                st.success(f"✅ {len(parsed_rules)} regels geladen")
                st.rerun()

        # Categories upload (optional - override defaults)
        categories_file = st.file_uploader(
            "Upload categories.yaml (optioneel)",
            type=['yaml', 'yml'],
            key="categories_upload",
            help="Upload aangepaste categorieën. Standaard Belgische categorieën zijn al ingeladen.",
        )

        if categories_file is not None:
            categories_content = categories_file.read()
            parsed_categories = parse_categories_yaml(categories_content)
            if parsed_categories and parsed_categories != st.session_state.categories:
                st.session_state.categories = parsed_categories
                st.session_state.custom_categories_loaded = True
                st.session_state.custom_categories_content = categories_content
                st.success(f"✅ {len(parsed_categories)} categorieën geladen")
                st.rerun()

        # Display config status
        st.divider()
        st.caption(f"Geladen: {len(st.session_state.categories)} categorieën, {len(st.session_state.rules)} regels")

        # Transaction stats in sidebar
        if st.session_state.transactions:
            st.divider()
            st.metric("Transacties", len(st.session_state.transactions))

        # =================================================================
        # Session Export/Import (T019-T021, T029)
        # =================================================================
        st.divider()
        st.subheader("Sessie")

        # Export section - visible when transactions exist (T019)
        if st.session_state.transactions:
            # Checkbox for source files inclusion (T020)
            include_source_files = st.checkbox(
                "Bronbestanden toevoegen",
                value=False,
                key="export_include_source",
                help="Voeg de originele bronbestanden toe aan het exportbestand",
            )

            # Create export ZIP (T021)
            try:
                # First create the state dict
                state_dict = session_to_dict(
                    transactions=st.session_state.transactions,
                    existing_ids=st.session_state.existing_ids,
                    fiscal_year=st.session_state.fiscal_year,
                    categorization_done=st.session_state.categorization_done,
                    import_stats=st.session_state.import_stats,
                    company_name=st.session_state.company_name or 'sessie',
                    custom_rules_loaded=st.session_state.custom_rules_loaded,
                    custom_categories_loaded=st.session_state.custom_categories_loaded,
                )

                # Then create the ZIP
                zip_bytes = create_export_zip(
                    state_dict=state_dict,
                    custom_rules_content=st.session_state.custom_rules_content if st.session_state.custom_rules_loaded else None,
                    custom_categories_content=st.session_state.custom_categories_content if st.session_state.custom_categories_loaded else None,
                    source_files=st.session_state.uploaded_files_content if include_source_files else None,
                    include_source_files=include_source_files,
                )

                export_filename = get_export_filename(
                    company_name=st.session_state.company_name or 'sessie',
                    fiscal_year=st.session_state.fiscal_year,
                )

                st.download_button(
                    label="📦 Exporteer sessie",
                    data=zip_bytes,
                    file_name=export_filename,
                    mime="application/zip",
                    help="Download een ZIP-bestand met je huidige sessiegegevens om later verder te werken",
                )
            except Exception as e:
                st.error(f"Export fout: {str(e)}")

        # Import section (T029)
        import_file = st.file_uploader(
            "Importeer sessie",
            type=['zip'],
            key="session_import",
            help="Upload een eerder geëxporteerde sessie om verder te werken",
        )

        if import_file is not None:
            try:
                zip_content = import_file.read()

                # Validate ZIP structure (returns 3 values)
                is_valid, error_msg, _ = validate_import_zip(zip_content)
                if not is_valid:
                    st.error(f"Ongeldig sessiebestand: {error_msg}")
                else:
                    # Show confirmation if we have existing data (T030)
                    has_existing_data = bool(st.session_state.transactions)

                    if has_existing_data:
                        st.warning("⚠️ Dit zal je huidige sessiegegevens vervangen!")

                    if st.button("Importeren", key="confirm_import", type="primary"):
                        # Perform import (T026-T028) - returns 5 values
                        success, message, state_dict, rules_content, categories_content = import_session_zip(zip_content)

                        if not success:
                            st.error(message)
                        else:
                            # Convert state_dict to session values
                            (
                                transactions,
                                existing_ids,
                                fiscal_year,
                                categorization_done,
                                import_stats,
                                company_name,
                                custom_rules_loaded,
                                custom_categories_loaded,
                            ) = dict_to_session(state_dict)

                            # Restore session state
                            st.session_state.transactions = transactions
                            st.session_state.existing_ids = existing_ids
                            st.session_state.fiscal_year = fiscal_year
                            st.session_state.categorization_done = categorization_done
                            st.session_state.import_stats = import_stats
                            st.session_state.company_name = company_name
                            st.session_state.custom_rules_loaded = custom_rules_loaded
                            st.session_state.custom_categories_loaded = custom_categories_loaded

                            # Restore rules if present
                            if rules_content:
                                parsed_rules = parse_rules_yaml(rules_content)
                                if parsed_rules:
                                    st.session_state.rules = parsed_rules
                                    st.session_state.custom_rules_content = rules_content

                            # Restore categories if present
                            if categories_content:
                                parsed_categories = parse_categories_yaml(categories_content)
                                if parsed_categories:
                                    st.session_state.categories = parsed_categories
                                    st.session_state.custom_categories_content = categories_content

                            # Show success message (T031)
                            tx_count = len(st.session_state.transactions)
                            st.success(f"✅ Sessie geïmporteerd: {tx_count} transacties hersteld")

                            st.rerun()

            except Exception as e:
                # Display error message (T032)
                st.error(f"Import fout: {str(e)}")

        # Session info message
        st.divider()
        st.caption(
            "💡 Exporteer je sessie om later verder te werken. "
            "Sessiegegevens worden gewist bij sluiten van de browser."
        )

        # Debug expander
        with st.expander("🔧 Debug Info", expanded=False):
            st.json({
                'fiscal_year': st.session_state.fiscal_year,
                'transactions_count': len(st.session_state.transactions),
                'existing_ids_count': len(st.session_state.existing_ids),
                'categorization_done': st.session_state.categorization_done,
                'categories_loaded': len(st.session_state.categories),
                'rules_loaded': len(st.session_state.rules),
            })

    # ==========================================================================
    # Main Content Area
    # ==========================================================================

    # File Upload Section (T011)
    st.header("1. Bestanden Uploaden")

    uploaded_files = st.file_uploader(
        "Sleep bank- en kredietkaartafschriften hierheen",
        type=['csv', 'pdf'],
        accept_multiple_files=True,
        help="Belfius bankafschriften en Mastercard statements",
    )

    # Import Button and Processing (T012, T013, T014, T016, T017, T018)
    if uploaded_files:
        col1, col2 = st.columns([1, 4])
        with col1:
            import_button = st.button("Importeren", type="primary", width="stretch")

        if import_button:
            process_uploaded_files(uploaded_files)

    # Display import statistics (T013)
    if st.session_state.import_stats:
        stats = st.session_state.import_stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Geïmporteerd", stats.get('imported', 0))
        with col2:
            st.metric("Overgeslagen (duplicaten)", stats.get('skipped', 0))
        with col3:
            st.metric("Uitgesloten", stats.get('excluded', 0))

        if stats.get('errors'):
            with st.expander(f"⚠️ {len(stats['errors'])} fout(en)", expanded=False):
                for error in stats['errors']:
                    st.warning(f"**{error.get('file', 'Onbekend')}**: {error.get('message', 'Onbekende fout')}")

    # Transaction Table (T015)
    if st.session_state.transactions:
        st.divider()
        col1, col2 = st.columns([3, 1])
        with col1:
            st.header("2. Transacties")

        with col2:
            categorize_button = st.button(
                "Automatisch categoriseren",
                type="primary",
                width="stretch",
                disabled=st.session_state.categorization_done and not st.session_state.get('recategorize_all', False),
            )

        # Build DataFrame for display
        display_transactions()

        recategorize_all = st.checkbox(
            "Hercategoriseer alle",
            key="recategorize_all",
            help="Ook reeds gecategoriseerde transacties opnieuw verwerken",
        )

        # Run categorization (T020, T024)
        if categorize_button:
            run_categorization(force=recategorize_all)

        # Display categorization statistics (T021, T023)
        if st.session_state.categorization_done:
            display_categorization_stats()

            # P&L Summary Section (T025-T031)
            st.divider()
            st.header("3. Resultatenrekening")
            display_pnl_summary()


def run_categorization(force: bool = False):
    """Run categorization on transactions (T020, T024)."""
    if not st.session_state.rules:
        st.warning("Geen categorisatieregels geladen. Upload een rules.yaml bestand in de sidebar.")
        return

    with st.spinner("Transacties worden gecategoriseerd..."):
        categorizer = Categorizer(st.session_state.rules)
        stats = categorizer.categorize_all(st.session_state.transactions, force=force)

    # Store stats in session state
    st.session_state.categorization_stats = stats
    st.session_state.categorization_done = True

    st.success(f"✅ {stats['categorized']} transactie(s) gecategoriseerd!")
    st.rerun()


def display_categorization_stats():
    """Display categorization statistics (T021, T023)."""
    stats = st.session_state.get('categorization_stats', {})

    # Count uncategorized transactions
    uncategorized = [tx for tx in st.session_state.transactions if tx.category is None]
    categorized = [tx for tx in st.session_state.transactions if tx.category is not None]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Gecategoriseerd", len(categorized))

    with col2:
        st.metric(
            "Niet gecategoriseerd",
            len(uncategorized),
            delta=f"-{len(uncategorized)}" if len(uncategorized) > 0 else None,
            delta_color="inverse" if len(uncategorized) > 0 else "off",
        )

    with col3:
        total = len(st.session_state.transactions)
        pct = (len(categorized) / total * 100) if total > 0 else 0
        st.metric("Dekking", f"{pct:.1f}%")

    # Highlight uncategorized transactions (T023)
    if uncategorized:
        with st.expander(f"⚠️ {len(uncategorized)} niet-gecategoriseerde transactie(s)", expanded=False):
            for tx in uncategorized[:10]:  # Show first 10
                st.text(f"• {tx.booking_date} | {tx.counterparty_name or tx.description or 'Onbekend'} | {format_belgian_currency(tx.amount)}")
            if len(uncategorized) > 10:
                st.caption(f"... en {len(uncategorized) - 10} meer")


def display_pnl_summary():
    """Display P&L summary with charts (T025-T031)."""
    import plotly.express as px
    import plotly.graph_objects as go

    # Generate report (T026)
    categories_dict = {cat.id: cat for cat in st.session_state.categories}
    generator = ReportGenerator(
        transactions=st.session_state.transactions,
        assets=[],  # No assets for now
        categories=categories_dict,
    )
    report = generator.generate_pnl_report(st.session_state.fiscal_year)

    uncategorized_count = len(report.uncategorized_items)
    if uncategorized_count:
        st.warning(
            f"⚠️ {uncategorized_count} niet-gecategoriseerde transactie(s) "
            f"({format_belgian_currency(report.total_uncategorized)}) "
            "zijn niet opgenomen in deze resultatenrekening. "
            "Categoriseer deze eerst voor een volledig beeld."
        )

    # P&L Summary Cards (T025, T031)
    st.subheader("Resultatenrekening")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Totaal Inkomsten",
            format_belgian_currency(report.total_income),
            delta=None,
        )

    with col2:
        st.metric(
            "Totaal Kosten",
            format_belgian_currency(abs(report.total_expenses)),
            delta=None,
        )

    with col3:
        profit = report.profit_loss
        st.metric(
            "Netto Resultaat",
            format_belgian_currency(profit),
            delta="Winst" if profit > 0 else "Verlies",
            delta_color="normal" if profit > 0 else "inverse",
        )

    with col4:
        if report.total_disallowed > 0:
            st.metric(
                "Verworpen Uitgaven",
                format_belgian_currency(report.total_disallowed),
                help="Niet volledig aftrekbaar (restaurant 69%, onthaal 50%)",
            )

    # Expense Breakdown Table (T027)
    if report.expense_items:
        st.subheader("Kostenanalyse per Categorie")

        expense_data = []
        for item in sorted(report.expense_items, key=lambda x: x.amount):
            cat_name = item.category
            # Try to get display name from categories
            if item.category in categories_dict:
                cat_name = categories_dict[item.category].name
            expense_data.append({
                'Categorie': cat_name,
                'Bedrag': float(abs(item.amount)),
                'Percentage': float(abs(item.amount) / abs(report.total_expenses) * 100) if report.total_expenses else 0,
            })

        if expense_data:
            import pandas as pd
            expense_df = pd.DataFrame(expense_data)
            expense_df = expense_df.sort_values('Bedrag', ascending=False)

            # Display table
            col1, col2 = st.columns([2, 1])

            with col1:
                # Format for display
                display_expense_df = expense_df.copy()
                display_expense_df['Bedrag'] = expense_df['Bedrag'].apply(
                    lambda x: format_belgian_currency(Decimal(str(x)), include_symbol=False)
                )
                display_expense_df['Percentage'] = expense_df['Percentage'].apply(
                    lambda x: f"{x:.1f}%"
                )

                st.dataframe(
                    display_expense_df,
                    width="stretch",
                    hide_index=True,
                )

            # Pie Chart (T028)
            with col2:
                fig = px.pie(
                    expense_df,
                    values='Bedrag',
                    names='Categorie',
                    title='Kostenverdeling',
                    hole=0.4,
                )
                fig.update_traces(textposition='inside', textinfo='percent')
                fig.update_layout(
                    showlegend=False,
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=300,
                )
                st.plotly_chart(fig, width="stretch")

    # Mollie Analysis Section (T029, T030)
    display_mollie_analysis()

    # Download Section (T032-T038)
    st.divider()
    display_download_section(report)

    return report


def display_download_section(report: Report):
    """Display report download buttons (T032-T038)."""
    st.subheader("Rapporten Downloaden")

    # Group download buttons in expander (T038)
    with st.expander("Download opties", expanded=True):
        col1, col2 = st.columns(2)

        # Excel Report (T032, T033)
        with col1:
            excel_bytes = generate_excel_report(report)
            if excel_bytes:
                st.download_button(
                    label="Download Excel Rapport",
                    data=excel_bytes,
                    file_name=f"PLV_Rapport_{st.session_state.fiscal_year}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch",
                )

        # CSV Export (T036, T037)
        with col2:
            csv_bytes = generate_transactions_csv()
            if csv_bytes:
                st.download_button(
                    label="Exporteer Transacties (CSV)",
                    data=csv_bytes,
                    file_name=f"Transacties_{st.session_state.fiscal_year}.csv",
                    mime="text/csv",
                    width="stretch",
                )


def generate_excel_report(report: Report) -> Optional[bytes]:
    """Generate Excel report in memory (T033)."""
    try:
        # Create Excel file in memory using the same generator as the CLI.
        output = io.BytesIO()
        categories_dict = {cat.id: cat for cat in st.session_state.categories}
        generator = ReportGenerator(
            transactions=st.session_state.transactions,
            assets=[],  # No assets for now
            categories=categories_dict,
        )
        generator.export_to_excel(report, output)
        output.seek(0)
        return output.getvalue()
    except Exception as e:
        st.error(f"Fout bij genereren Excel rapport: {e}")
        return None


def generate_transactions_csv() -> Optional[bytes]:
    """Generate transactions CSV export (T037)."""
    import pandas as pd

    try:
        tx_data = []
        for tx in st.session_state.transactions:
            tx_data.append({
                'Datum': tx.booking_date.isoformat() if tx.booking_date else '',
                'Bedrag': format_belgian_number(float(tx.amount)),
                'Tegenpartij': tx.counterparty_name or '',
                'Omschrijving': tx.description or '',
                'Categorie': tx.category or '',
                'Bron': tx.source_type,
                'ID': tx.id,
            })

        if not tx_data:
            return None

        df = pd.DataFrame(tx_data)
        df = df.sort_values('Datum', ascending=False)

        # Export to CSV with Belgian formatting (semicolon delimiter)
        output = io.StringIO()
        df.to_csv(output, index=False, sep=';', encoding='utf-8')

        return output.getvalue().encode('utf-8')

    except Exception as e:
        st.error(f"Fout bij genereren CSV export: {e}")
        return None


def display_mollie_analysis():
    """Display Mollie payment analysis (T029, T030)."""
    # Find Mollie transactions
    mollie_transactions = [
        tx for tx in st.session_state.transactions
        if tx.counterparty_name and 'mollie' in tx.counterparty_name.lower()
    ]

    if not mollie_transactions:
        return

    st.subheader("Mollie Betalingsanalyse")

    # Calculate Mollie metrics (T030)
    mollie_income = sum(
        tx.amount for tx in mollie_transactions
        if tx.amount > 0
    )

    total_income = sum(
        tx.amount for tx in st.session_state.transactions
        if tx.amount > 0 and tx.category == 'omzet'
    )

    mollie_pct = (float(mollie_income) / float(total_income) * 100) if total_income > 0 else 0

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Mollie Transacties", len(mollie_transactions))

    with col2:
        st.metric("Mollie Omzet", format_belgian_currency(mollie_income))

    with col3:
        st.metric(
            "Aandeel Online Betalingen",
            f"{mollie_pct:.1f}%",
            help="Percentage van totale omzet via Mollie",
        )


def process_uploaded_files(uploaded_files):
    """Process uploaded files and import transactions.

    Handles T012, T014, T016, T017, T018.
    """
    csv_importer = CSVImporter(existing_ids=st.session_state.existing_ids)
    pdf_importer = PDFImporter(existing_ids=st.session_state.existing_ids)

    total_imported = 0
    total_skipped = 0
    total_excluded = 0
    all_errors = []

    with st.spinner("Bestanden worden verwerkt..."):
        for uploaded_file in uploaded_files:
            filename = uploaded_file.name
            file_content = uploaded_file.read()

            # Check for empty files (T017)
            if len(file_content) == 0:
                all_errors.append({
                    'file': filename,
                    'message': 'Bestand is leeg - geen transacties gevonden',
                })
                continue

            try:
                if filename.lower().endswith('.csv'):
                    # Import CSV
                    transactions, session = csv_importer.import_from_bytes(
                        file_content,
                        filename,
                        fiscal_year=st.session_state.fiscal_year,
                    )
                elif filename.lower().endswith('.pdf'):
                    # Import PDF (T018 - handle parsing failures)
                    try:
                        transactions, session = pdf_importer.import_from_bytes(
                            file_content,
                            filename,
                            fiscal_year=st.session_state.fiscal_year,
                        )
                    except Exception as pdf_error:
                        all_errors.append({
                            'file': filename,
                        'message': f'Kaartafschrift kon niet worden gelezen: {str(pdf_error)}',
                        })
                        continue
                else:
                    # Invalid file type (T016)
                    all_errors.append({
                        'file': filename,
                        'message': 'Ongeldig bestandsformaat - alleen ondersteunde bestandsformaten worden geaccepteerd',
                    })
                    continue

                # Check for empty result (T017)
                if not transactions and session.transactions_imported == 0:
                    if not session.errors:
                        st.info(f"Geen transacties gevonden in {filename}")

                # Add transactions to session state
                st.session_state.transactions.extend(transactions)

                # Update existing_ids for duplicate detection (T014)
                for tx in transactions:
                    st.session_state.existing_ids.add(tx.id)

                # Store file content for potential export (T018)
                st.session_state.uploaded_files_content[filename] = file_content

                # Accumulate stats
                total_imported += session.transactions_imported
                total_skipped += session.transactions_skipped
                total_excluded += getattr(session, 'transactions_excluded', 0)

                # Collect errors
                for error in session.errors:
                    all_errors.append({
                        'file': error.file,
                        'message': error.message,
                    })

            except Exception as e:
                # General error handling (T016)
                all_errors.append({
                    'file': filename,
                    'message': f'Fout bij verwerken: {str(e)}',
                })

    # Store import statistics
    st.session_state.import_stats = {
        'imported': total_imported,
        'skipped': total_skipped,
        'excluded': total_excluded,
        'errors': all_errors,
    }

    # Show success message
    if total_imported > 0:
        st.success(f"✅ {total_imported} transactie(s) geïmporteerd!")

    # Reset categorization flag since we have new transactions
    st.session_state.categorization_done = False

    st.rerun()


def display_transactions():
    """Display transaction table with filtering, detail view, and category editing (T015)."""
    import pandas as pd

    transactions = st.session_state.transactions
    if 'tx_selected_original_idx' not in st.session_state:
        st.session_state.tx_selected_original_idx = None
    if 'tx_selected_original_idxs' not in st.session_state:
        st.session_state.tx_selected_original_idxs = []
    if 'tx_editor_reset' not in st.session_state:
        st.session_state.tx_editor_reset = False
    if 'tx_view_order' not in st.session_state:
        st.session_state.tx_view_order = []
    if 'tx_select_all_visible' not in st.session_state:
        st.session_state.tx_select_all_visible = False

    def _set_selection(original_idxs: list[int]) -> None:
        unique = sorted({int(x) for x in original_idxs})
        st.session_state.tx_selected_original_idxs = unique
        st.session_state.tx_selected_original_idx = unique[0] if len(unique) == 1 else None
        st.session_state.tx_editor_reset = True

    def _navigate(delta: int) -> None:
        order = [int(x) for x in (st.session_state.get('tx_view_order') or [])]
        current = st.session_state.get('tx_selected_original_idx')
        if current is None:
            return
        current = int(current)
        if current not in order:
            return
        pos = order.index(current)
        new_pos = pos + int(delta)
        if 0 <= new_pos < len(order):
            _set_selection([order[new_pos]])

    def _toggle_select_all_visible(visible_ids: list[int]) -> None:
        selected = set(int(x) for x in (st.session_state.get('tx_selected_original_idxs') or []))
        if st.session_state.get('tx_select_all_visible'):
            selected.update(int(x) for x in visible_ids)
        else:
            selected.difference_update(int(x) for x in visible_ids)
        _set_selection(list(selected))

    # Convert to DataFrame with transaction index for selection
    data = []
    for idx, tx in enumerate(transactions):
        data.append({
            '_idx': idx,  # Hidden index for selection
            'Datum': tx.booking_date,
            'Bedrag': float(tx.amount),
            'Tegenpartij': tx.counterparty_name or '-',
            'Omschrijving': (tx.description or '-')[:50],
            'Categorie': tx.category or '(niet gecategoriseerd)',
            'Bron': tx.source_type,
        })

    df = pd.DataFrame(data)

    # Sort by date descending
    df = df.sort_values('Datum', ascending=False).reset_index(drop=True)

    # =========================================================================
    # FILTERS SECTION
    # =========================================================================
    with st.expander("Filters", expanded=True):
        # Row 1: Text search and date range
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            # Text search across all text columns
            search_text = st.text_input(
                "Zoeken in tegenpartij/omschrijving",
                key="tx_search",
                placeholder="Typ om te zoeken...",
            )

        with col2:
            # Date range - start
            min_date = df['Datum'].min() if len(df) > 0 else datetime.now().date()
            max_date = df['Datum'].max() if len(df) > 0 else datetime.now().date()
            date_from = st.date_input(
                "Van datum",
                value=min_date,
                min_value=min_date,
                max_value=max_date,
                key="date_from",
            )

        with col3:
            # Date range - end
            date_to = st.date_input(
                "Tot datum",
                value=max_date,
                min_value=min_date,
                max_value=max_date,
                key="date_to",
            )

        # Row 2: Amount range and category/source filters
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

        with col1:
            # Amount range - min
            min_amount = float(df['Bedrag'].min()) if len(df) > 0 else -10000
            max_amount = float(df['Bedrag'].max()) if len(df) > 0 else 10000
            amount_from = st.number_input(
                "Min bedrag (EUR)",
                value=min_amount,
                min_value=min_amount,
                max_value=max_amount,
                step=10.0,
                key="amount_from",
            )

        with col2:
            # Amount range - max
            amount_to = st.number_input(
                "Max bedrag (EUR)",
                value=max_amount,
                min_value=min_amount,
                max_value=max_amount,
                step=10.0,
                key="amount_to",
            )

        with col3:
            # Category filter
            categories = ['Alle'] + sorted(df['Categorie'].unique().tolist())
            selected_category = st.selectbox("Categorie", categories, key="filter_cat")

        with col4:
            # Source filter
            sources = ['Alle'] + sorted(df['Bron'].unique().tolist())
            selected_source = st.selectbox("Bron", sources, key="filter_source")

        # Row 3: Checkboxes
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            show_uncategorized = st.checkbox("Alleen niet-gecategoriseerd", key="filter_uncat")

        with col2:
            show_income = st.checkbox("Alleen inkomsten", key="filter_income")

        with col3:
            show_expenses = st.checkbox("Alleen uitgaven", key="filter_expenses")

    # =========================================================================
    # APPLY FILTERS
    # =========================================================================
    filtered_df = df.copy()

    # Text search
    if search_text:
        search_lower = search_text.lower()
        mask = (
            filtered_df['Tegenpartij'].str.lower().str.contains(search_lower, na=False) |
            filtered_df['Omschrijving'].str.lower().str.contains(search_lower, na=False)
        )
        filtered_df = filtered_df[mask]

    # Date range
    if date_from and date_to:
        filtered_df = filtered_df[
            (filtered_df['Datum'] >= date_from) &
            (filtered_df['Datum'] <= date_to)
        ]

    # Amount range
    filtered_df = filtered_df[
        (filtered_df['Bedrag'] >= amount_from) &
        (filtered_df['Bedrag'] <= amount_to)
    ]

    # Category filter
    if selected_category != 'Alle':
        filtered_df = filtered_df[filtered_df['Categorie'] == selected_category]

    # Source filter
    if selected_source != 'Alle':
        filtered_df = filtered_df[filtered_df['Bron'] == selected_source]

    # Uncategorized only
    if show_uncategorized:
        filtered_df = filtered_df[filtered_df['Categorie'] == '(niet gecategoriseerd)']

    # Income/expenses
    if show_income and not show_expenses:
        filtered_df = filtered_df[filtered_df['Bedrag'] > 0]
    elif show_expenses and not show_income:
        filtered_df = filtered_df[filtered_df['Bedrag'] < 0]

    # =========================================================================
    # TRANSACTION TABLE WITH SELECTION
    # =========================================================================
    matching_count = len(filtered_df)

    # Keep selected transaction(s) visible even if they no longer match filters
    pinned_selected = False
    selected_original_idxs = [int(x) for x in (st.session_state.get('tx_selected_original_idxs') or [])]
    if selected_original_idxs and len(df) > 0:
        visible_set = set(int(x) for x in filtered_df['_idx'].tolist()) if len(filtered_df) > 0 else set()
        missing_ids = [x for x in selected_original_idxs if x not in visible_set]
        if missing_ids:
            pinned_rows_df = df[df['_idx'].isin(missing_ids)]
            if len(pinned_rows_df) > 0:
                filtered_df = pd.concat([pinned_rows_df, filtered_df], ignore_index=True)
                pinned_selected = True

    filtered_df = filtered_df.reset_index(drop=True)
    st.session_state.tx_view_order = filtered_df['_idx'].tolist()

    caption = f"Tonen: {matching_count} van {len(df)} transacties"
    if pinned_selected:
        caption += " (+ geselecteerde transactie buiten filters)"
    st.caption(caption)

    # Format currency column for display
    def format_amount(val):
        return format_belgian_currency(Decimal(str(val)), include_symbol=False)

    # Create display DataFrame (without _idx column)
    display_df = filtered_df.drop(columns=['_idx']).copy()
    display_df['Bedrag'] = filtered_df['Bedrag'].apply(format_amount)

    # Use data_editor with selection for clicking
    if len(filtered_df) > 0:
        visible_ids = [int(x) for x in filtered_df['_idx'].tolist()]
        st.checkbox(
            "Selecteer alles (zichtbaar)",
            key="tx_select_all_visible",
            on_change=_toggle_select_all_visible,
            args=(visible_ids,),
        )

        # Add selection column
        display_df.insert(0, 'Selecteer', False)

        # Pre-select the currently selected transactions
        selected_set = set(int(x) for x in (st.session_state.get('tx_selected_original_idxs') or []))
        if selected_set:
            for row_pos in filtered_df.index[filtered_df['_idx'].isin(selected_set)].tolist():
                display_df.at[int(row_pos), 'Selecteer'] = True

        if st.session_state.get('tx_editor_reset'):
            st.session_state.pop('tx_editor', None)
            st.session_state.tx_editor_reset = False

        edited_df = st.data_editor(
            display_df,
            width="stretch",
            hide_index=True,
            key="tx_editor",
            column_config={
                'Selecteer': st.column_config.CheckboxColumn('', width='small', default=False),
                'Datum': st.column_config.DateColumn('Datum', format='DD/MM/YYYY'),
                'Bedrag': st.column_config.TextColumn('Bedrag (EUR)'),
                'Tegenpartij': st.column_config.TextColumn('Tegenpartij', width='medium'),
                'Omschrijving': st.column_config.TextColumn('Omschrijving', width='large'),
                'Categorie': st.column_config.TextColumn('Categorie'),
                'Bron': st.column_config.TextColumn('Bron'),
            },
            disabled=['Datum', 'Bedrag', 'Tegenpartij', 'Omschrijving', 'Categorie', 'Bron'],
        )

        # Find selected rows
        selected_rows = edited_df[edited_df['Selecteer'] == True].index.tolist()
        selected_original_idxs = [int(filtered_df.iloc[i]['_idx']) for i in selected_rows]
        st.session_state.tx_selected_original_idxs = sorted({int(x) for x in selected_original_idxs})
        st.session_state.tx_selected_original_idx = (
            st.session_state.tx_selected_original_idxs[0]
            if len(st.session_state.tx_selected_original_idxs) == 1
            else None
        )

        # =====================================================================
        # TRANSACTION DETAIL VIEW AND CATEGORY EDITING
        # =====================================================================
        selected_original_idxs = [int(x) for x in (st.session_state.get('tx_selected_original_idxs') or [])]
        if selected_original_idxs:
            st.divider()
            if len(selected_original_idxs) == 1:
                st.subheader("Transactie Details")
            else:
                st.subheader("Selectie")

            if len(selected_original_idxs) == 1:
                tx = transactions[int(selected_original_idxs[0])]

            # Display full transaction details
            col1, col2 = st.columns([2, 1])

            with col1:
                if len(selected_original_idxs) == 1:
                    with st.container(border=True):
                        st.markdown("**Algemene Informatie**")

                        communication_value = getattr(tx, 'communication', None) or tx.description

                        # Full details in a clean format
                        detail_data = {
                            'Veld': [
                                'Transactie ID',
                                'Boekingsdatum',
                                'Bedrag',
                                'Tegenpartij naam',
                                'Tegenpartij rekening',
                                'Mededeling',
                                'Volledige omschrijving',
                                'Bron',
                                'Huidige categorie',
                            ],
                            'Waarde': [
                                tx.id,
                                tx.booking_date.strftime('%d/%m/%Y') if tx.booking_date else '-',
                                format_belgian_currency(tx.amount),
                                tx.counterparty_name or '-',
                                getattr(tx, 'counterparty_iban', None) or getattr(tx, 'counterparty_account', None) or '-',
                                communication_value or '-',
                                tx.description or '-',
                                tx.source_type,
                                tx.category or '(niet gecategoriseerd)',
                            ],
                        }
                        detail_df = pd.DataFrame(detail_data)
                        st.dataframe(
                            detail_df,
                            width="stretch",
                            hide_index=True,
                            column_config={
                                'Veld': st.column_config.TextColumn('Veld', width='medium'),
                                'Waarde': st.column_config.TextColumn('Waarde', width='large'),
                            },
                        )
                else:
                    st.info(
                        f"{len(selected_original_idxs)} transacties geselecteerd. "
                        "Details worden verborgen bij multiselect."
                    )

            with col2:
                with st.container(border=True):
                    st.markdown("**Categorie Aanpassen**")

                    # Build category options
                    category_options = ['(niet gecategoriseerd)'] + [
                        cat.id for cat in st.session_state.categories
                    ]
                    category_labels = {'(niet gecategoriseerd)': '(niet gecategoriseerd)'}
                    for cat in st.session_state.categories:
                        category_labels[cat.id] = f"{cat.name} ({cat.type})"

                    # Category selector
                    if len(selected_original_idxs) == 1:
                        current_cat = tx.category or '(niet gecategoriseerd)'
                        current_idx = category_options.index(current_cat) if current_cat in category_options else 0
                        select_key = f"cat_select_{selected_original_idxs[0]}"
                    else:
                        current_idx = 0
                        select_key = "cat_select_bulk"

                    new_category = st.selectbox(
                        "Kies nieuwe categorie",
                        options=category_options,
                        index=int(current_idx),
                        format_func=lambda x: category_labels.get(x, x),
                        key=select_key,
                    )

                    # Apply button
                    def _save_category(original_idxs: list[int], select_key: str, labels: dict) -> None:
                        new_category_value = st.session_state.get(select_key)
                        for original_idx in original_idxs:
                            if new_category_value == '(niet gecategoriseerd)':
                                st.session_state.transactions[int(original_idx)].category = None
                            else:
                                st.session_state.transactions[int(original_idx)].category = new_category_value
                        st.session_state.tx_last_save_msg = (
                            f"✅ Categorie bijgewerkt naar: {labels.get(new_category_value, new_category_value)}"
                        )
                        _set_selection(list(original_idxs))

                    st.button(
                        "Categorie opslaan" if len(selected_original_idxs) == 1 else f"Categorie opslaan ({len(selected_original_idxs)})",
                        type="primary",
                        width="stretch",
                        key=f"save_cat_{selected_original_idxs[0]}" if len(selected_original_idxs) == 1 else "save_cat_bulk",
                        on_click=_save_category,
                        args=(list(selected_original_idxs), select_key, category_labels),
                    )

                    last_save_msg = st.session_state.pop('tx_last_save_msg', None)
                    if last_save_msg:
                        st.success(last_save_msg)

                    if len(selected_original_idxs) == 1:
                        # Navigation buttons (single-select only)
                        nav_col1, nav_col2 = st.columns(2)
                        order = [int(x) for x in (st.session_state.get('tx_view_order') or [])]
                        try:
                            pos = order.index(int(selected_original_idxs[0]))
                        except ValueError:
                            pos = None
                        has_prev = pos is not None and pos > 0
                        has_next = pos is not None and pos < (len(order) - 1)

                        with nav_col1:
                            st.button(
                                "Previous",
                                width="stretch",
                                disabled=not has_prev,
                                key=f"tx_prev_{selected_original_idxs[0]}",
                                on_click=_navigate,
                                args=(-1,),
                            )
                        with nav_col2:
                            st.button(
                                "Next",
                                width="stretch",
                                disabled=not has_next,
                                key=f"tx_next_{selected_original_idxs[0]}",
                                on_click=_navigate,
                                args=(1,),
                            )

                    # Show category description
                    if new_category != '(niet gecategoriseerd)':
                        cat_obj = next(
                            (c for c in st.session_state.categories if c.id == new_category),
                            None,
                        )
                        if cat_obj:
                            st.caption(f"*{cat_obj.description}*")
                            if cat_obj.deductibility_pct and cat_obj.deductibility_pct < 100:
                                st.info(f"💡 {cat_obj.deductibility_pct}% fiscaal aftrekbaar")
    else:
        st.info("Geen transacties gevonden met de huidige filters.")


if __name__ == "__main__":
    main()
