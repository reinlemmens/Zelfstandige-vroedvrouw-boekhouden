"""Session export/import service for Streamlit app."""

import io
import json
import re
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from src.models.transaction import Transaction
from src.models.session_state import (
    CURRENT_VERSION,
    SessionState,
    validate_state_dict,
    validate_version,
)


def sanitize_filename(company_name: str) -> str:
    """Sanitize company name for use in filename.

    Converts to lowercase, replaces spaces with hyphens,
    removes non-alphanumeric characters.

    Args:
        company_name: User-entered company name

    Returns:
        Sanitized filename-safe string
    """
    if not company_name or not company_name.strip():
        return 'sessie'

    # Convert to lowercase
    name = company_name.lower().strip()

    # Replace spaces with hyphens
    name = name.replace(' ', '-')

    # Remove non-alphanumeric characters (except hyphens)
    name = re.sub(r'[^a-z0-9-]', '', name)

    # Remove multiple consecutive hyphens
    name = re.sub(r'-+', '-', name)

    # Remove leading/trailing hyphens
    name = name.strip('-')

    return name if name else 'sessie'


def session_to_dict(
    transactions: List[Transaction],
    existing_ids: Set[str],
    fiscal_year: int,
    categorization_done: bool,
    import_stats: Optional[Dict[str, Any]],
    company_name: str,
    custom_rules_loaded: bool,
    custom_categories_loaded: bool,
) -> Dict[str, Any]:
    """Convert session state to serializable dictionary.

    Args:
        transactions: List of Transaction objects
        existing_ids: Set of transaction IDs
        fiscal_year: Selected fiscal year
        categorization_done: Whether categorization has been run
        import_stats: Statistics from last import
        company_name: User-entered company name
        custom_rules_loaded: True if custom rules were uploaded
        custom_categories_loaded: True if custom categories were uploaded

    Returns:
        Dictionary suitable for JSON serialization
    """
    return {
        'version': CURRENT_VERSION,
        'company_name': company_name or 'sessie',
        'fiscal_year': fiscal_year,
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'transactions': [tx.to_dict() for tx in transactions],
        'existing_ids': list(existing_ids),
        'categorization_done': categorization_done,
        'import_stats': import_stats,
        'custom_rules_loaded': custom_rules_loaded,
        'custom_categories_loaded': custom_categories_loaded,
    }


def dict_to_session(data: Dict[str, Any]) -> Tuple[
    List[Transaction],
    Set[str],
    int,
    bool,
    Optional[Dict[str, Any]],
    str,
    bool,
    bool,
]:
    """Convert dictionary to session state values.

    Args:
        data: Dictionary from state.json

    Returns:
        Tuple of (transactions, existing_ids, fiscal_year, categorization_done,
                  import_stats, company_name, custom_rules_loaded, custom_categories_loaded)
    """
    transactions = [Transaction.from_dict(tx) for tx in data.get('transactions', [])]
    existing_ids = set(data.get('existing_ids', []))
    fiscal_year = data['fiscal_year']
    categorization_done = data.get('categorization_done', False)
    import_stats = data.get('import_stats')
    company_name = data.get('company_name', 'sessie')
    custom_rules_loaded = data.get('custom_rules_loaded', False)
    custom_categories_loaded = data.get('custom_categories_loaded', False)

    return (
        transactions,
        existing_ids,
        fiscal_year,
        categorization_done,
        import_stats,
        company_name,
        custom_rules_loaded,
        custom_categories_loaded,
    )


def apply_migrations(data: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    """Apply any needed migrations to older state data.

    Args:
        data: State dictionary to migrate

    Returns:
        Tuple of (migrated_data, migration_message or None)
    """
    version = data.get('version', '1.0')
    migration_message = None

    # Currently only version 1.0 exists, no migrations needed
    # Future migrations would go here:
    #
    # if version == '1.0' and CURRENT_VERSION > '1.0':
    #     data = migrate_1_0_to_1_1(data)
    #     migration_message = f"Sessiebestand geüpgraded van v1.0 naar v{CURRENT_VERSION}"

    if version != CURRENT_VERSION:
        # For future versions, add migration logic above
        migration_message = f"Sessiebestand versie {version} geladen"

    return data, migration_message


def create_export_zip(
    state_dict: Dict[str, Any],
    custom_rules_content: Optional[bytes] = None,
    custom_categories_content: Optional[bytes] = None,
    source_files: Optional[Dict[str, bytes]] = None,
    include_source_files: bool = False,
) -> bytes:
    """Create a ZIP file containing session state and optional files.

    Args:
        state_dict: Session state dictionary
        custom_rules_content: Raw bytes of custom rules.yaml (if uploaded)
        custom_categories_content: Raw bytes of custom categories.yaml (if uploaded)
        source_files: Dictionary of {filename: content} for source files
        include_source_files: Whether to include source files in export

    Returns:
        ZIP file as bytes
    """
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Always include state.json
        state_json = json.dumps(state_dict, indent=2, ensure_ascii=False)
        zf.writestr('state.json', state_json)

        # Include custom rules if uploaded
        if custom_rules_content and state_dict.get('custom_rules_loaded'):
            zf.writestr('rules.yaml', custom_rules_content)

        # Include custom categories if uploaded
        if custom_categories_content and state_dict.get('custom_categories_loaded'):
            zf.writestr('categories.yaml', custom_categories_content)

        # Include source files if requested
        if include_source_files and source_files:
            for filename, content in source_files.items():
                zf.writestr(f'source_files/{filename}', content)

    buffer.seek(0)
    return buffer.getvalue()


def validate_import_zip(zip_content: bytes) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Validate an import ZIP file.

    Args:
        zip_content: Raw bytes of uploaded ZIP file

    Returns:
        Tuple of (is_valid, error_message, state_dict or None)
    """
    try:
        buffer = io.BytesIO(zip_content)

        # Check if it's a valid ZIP
        if not zipfile.is_zipfile(buffer):
            return False, "Upload een .zip bestand", None

        buffer.seek(0)

        with zipfile.ZipFile(buffer, 'r') as zf:
            # Check for state.json
            if 'state.json' not in zf.namelist():
                return False, "Ongeldig sessiebestand: state.json niet gevonden", None

            # Read and parse state.json
            try:
                state_content = zf.read('state.json').decode('utf-8')
                state_dict = json.loads(state_content)
            except json.JSONDecodeError:
                return False, "Ongeldig sessiebestand: corrupte data", None
            except UnicodeDecodeError:
                return False, "Ongeldig sessiebestand: ongeldige encoding", None

            # Validate state structure
            is_valid, error = validate_state_dict(state_dict)
            if not is_valid:
                return False, f"Ongeldig sessiebestand: {error}", None

            # Validate version
            version = state_dict.get('version', '1.0')
            is_valid, error = validate_version(version)
            if not is_valid:
                return False, error, None

            return True, "", state_dict

    except zipfile.BadZipFile:
        return False, "Upload een geldig .zip bestand", None
    except Exception as e:
        return False, f"Fout bij lezen bestand: {str(e)}", None


def import_session_zip(
    zip_content: bytes,
) -> Tuple[
    bool,
    str,
    Optional[Dict[str, Any]],
    Optional[bytes],
    Optional[bytes],
]:
    """Import a session from ZIP file.

    Args:
        zip_content: Raw bytes of uploaded ZIP file

    Returns:
        Tuple of (success, message, state_dict, rules_content, categories_content)
    """
    # Validate first
    is_valid, error, state_dict = validate_import_zip(zip_content)
    if not is_valid:
        return False, error, None, None, None

    # Apply migrations if needed
    state_dict, migration_msg = apply_migrations(state_dict)

    # Extract optional files
    rules_content = None
    categories_content = None

    buffer = io.BytesIO(zip_content)
    with zipfile.ZipFile(buffer, 'r') as zf:
        if 'rules.yaml' in zf.namelist():
            rules_content = zf.read('rules.yaml')

        if 'categories.yaml' in zf.namelist():
            categories_content = zf.read('categories.yaml')

    # Build success message
    tx_count = len(state_dict.get('transactions', []))
    message = f"✅ {tx_count} transactie(s) hersteld"
    if migration_msg:
        message = f"{migration_msg}\n{message}"

    return True, message, state_dict, rules_content, categories_content


def get_export_filename(company_name: str, fiscal_year: int) -> str:
    """Generate the export filename.

    Args:
        company_name: User-entered company name
        fiscal_year: Selected fiscal year

    Returns:
        Filename in format plv-{company}-{year}.zip
    """
    safe_name = sanitize_filename(company_name)
    return f"plv-{safe_name}-{fiscal_year}.zip"
