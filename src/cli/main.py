"""CLI entry point for PLV transaction categorization tool."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click

from src import __version__
from src.services.persistence import PersistenceService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
)
logger = logging.getLogger(__name__)


class Context:
    """CLI context object holding shared state."""

    def __init__(self):
        self.verbose: bool = False
        self.quiet: bool = False
        self.json_output: bool = False
        self.config_path: str = "config/settings.yaml"
        self.data_dir: str = "data/output"
        self.persistence: Optional[PersistenceService] = None

    def get_persistence(self) -> PersistenceService:
        """Get or create persistence service."""
        if self.persistence is None:
            settings = {}
            settings_path = Path(self.config_path)
            if settings_path.exists():
                import yaml
                with open(settings_path, 'r') as f:
                    settings = yaml.safe_load(f) or {}

            self.persistence = PersistenceService(
                data_dir=settings.get('data_dir', self.data_dir),
                rules_file=settings.get('rules_file', 'config/rules.yaml'),
                categories_file=settings.get('categories_file', 'config/categories.yaml'),
            )
        return self.persistence


pass_context = click.make_pass_decorator(Context, ensure=True)


@click.group()
@click.option('-v', '--verbose', is_flag=True, help='Enable verbose output')
@click.option('-q', '--quiet', is_flag=True, help='Suppress non-error output')
@click.option('-j', '--json', 'json_output', is_flag=True, help='Output as JSON')
@click.option('--config', 'config_path', default='config/settings.yaml', help='Config file path')
@click.option('--data-dir', default='data/output', help='Data directory path')
@click.version_option(version=__version__, prog_name='plv')
@pass_context
def cli(ctx: Context, verbose: bool, quiet: bool, json_output: bool, config_path: str, data_dir: str):
    """PLV - P&L tool for Belgian midwife tax filing.

    Import, categorize, and manage financial transactions for tax preparation.
    """
    ctx.verbose = verbose
    ctx.quiet = quiet
    ctx.json_output = json_output
    ctx.config_path = config_path
    ctx.data_dir = data_dir

    # Adjust logging level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif quiet:
        logging.getLogger().setLevel(logging.ERROR)


@cli.command('import')
@click.argument('files', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('-y', '--year', type=int, default=None, help='Fiscal year (default: current)')
@click.option('-n', '--dry-run', is_flag=True, help='Preview without saving')
@click.option('-f', '--force', is_flag=True, help='Re-import duplicates')
@pass_context
def import_cmd(ctx: Context, files: tuple, year: Optional[int], dry_run: bool, force: bool):
    """Import transactions from bank CSV and/or Mastercard PDF files."""
    import json
    from src.services.csv_importer import import_csv_files
    from src.services.pdf_importer import import_pdf_files

    # Default to current year if not specified
    if year is None:
        year = datetime.now().year

    persistence = ctx.get_persistence()

    # Get existing transaction IDs for duplicate detection
    existing_ids = persistence.get_existing_transaction_ids()

    # Separate CSV and PDF files
    csv_files = [Path(f) for f in files if f.lower().endswith('.csv')]
    pdf_files = [Path(f) for f in files if f.lower().endswith('.pdf')]

    all_transactions = []
    all_sessions = []

    # Import CSV files
    if csv_files:
        transactions, sessions = import_csv_files(
            csv_files,
            existing_ids=existing_ids,
            fiscal_year=year,
            force=force,
        )
        all_transactions.extend(transactions)
        all_sessions.extend(sessions)
        # Update existing_ids for PDF import
        existing_ids = existing_ids.union({tx.id for tx in transactions})

    # Import PDF files
    if pdf_files:
        transactions, sessions = import_pdf_files(
            pdf_files,
            existing_ids=existing_ids,
            fiscal_year=year,
            force=force,
        )
        all_transactions.extend(transactions)
        all_sessions.extend(sessions)

    # Calculate totals
    total_imported = sum(s.transactions_imported for s in all_sessions)
    total_skipped = sum(s.transactions_skipped for s in all_sessions)
    total_excluded = sum(s.transactions_excluded for s in all_sessions)
    total_errors = sum(len(s.errors) for s in all_sessions)

    # Save if not dry run
    if not dry_run and all_transactions:
        # Load existing transactions and merge
        existing_transactions = persistence.load_transactions()

        # Add new non-excluded transactions
        new_transactions = [tx for tx in all_transactions if not tx.is_excluded]
        merged = existing_transactions + new_transactions

        persistence.save_transactions(merged, year, all_sessions)

    # Output results
    if ctx.json_output:
        result = {
            'imported': total_imported,
            'skipped_duplicates': total_skipped,
            'excluded': total_excluded,
            'errors': total_errors,
            'dry_run': dry_run,
        }
        click.echo(json.dumps(result, indent=2))
    else:
        if not ctx.quiet:
            click.echo(f"Imported: {total_imported} transactions")
            click.echo(f"Skipped duplicates: {total_skipped}")
            click.echo(f"Excluded (MC settlements): {total_excluded}")
            if total_errors > 0:
                click.echo(f"Errors: {total_errors}")
            if dry_run:
                click.echo("(Dry run - no changes saved)")

    # Exit with appropriate code
    if total_errors > 0 and total_imported == 0:
        sys.exit(2)  # Complete failure
    elif total_errors > 0:
        sys.exit(1)  # Partial failure


@cli.command()
@click.option('-y', '--year', type=int, default=None, help='Fiscal year (default: current)')
@click.option('-a', '--all', 'all_transactions', is_flag=True, help='Re-categorize all')
@click.option('-n', '--dry-run', is_flag=True, help='Preview without saving')
@pass_context
def categorize(ctx: Context, year: Optional[int], all_transactions: bool, dry_run: bool):
    """Apply categorization rules to transactions."""
    import json
    from src.services.categorizer import categorize_transactions

    # Default to current year if not specified
    if year is None:
        year = datetime.now().year

    persistence = ctx.get_persistence()

    # Load transactions and rules
    transactions = persistence.load_transactions(fiscal_year=year)
    rules = persistence.load_rules()

    if not transactions:
        if not ctx.quiet:
            click.echo(f"No transactions found for year {year}")
        return

    if not rules:
        if not ctx.quiet:
            click.echo("No categorization rules found. Use 'plv bootstrap' to extract rules from Excel.")
        return

    # Categorize transactions
    transactions, stats = categorize_transactions(
        transactions,
        rules,
        force=all_transactions,
    )

    # Count current categorization status
    already_categorized = sum(1 for tx in transactions if tx.category is not None and not tx.is_excluded)
    total_non_excluded = sum(1 for tx in transactions if not tx.is_excluded)

    # Save if not dry run
    if not dry_run:
        persistence.save_transactions(transactions, year)

    # Output results
    if ctx.json_output:
        result = {
            'categorized': stats['categorized'],
            'uncategorized': stats['uncategorized'],
            'rules_applied': stats['rules_applied'],
            'total_categorized': already_categorized,
            'total_transactions': total_non_excluded,
            'dry_run': dry_run,
        }
        click.echo(json.dumps(result, indent=2))
    else:
        if not ctx.quiet:
            click.echo(f"Categorized: {stats['categorized']} (total: {already_categorized}/{total_non_excluded})")
            click.echo(f"Uncategorized: {stats['uncategorized']}")
            if stats['rules_applied']:
                click.echo("Rules applied:")
                for rule_id, count in sorted(stats['rules_applied'].items(), key=lambda x: -x[1])[:10]:
                    click.echo(f"  {rule_id}: {count}")
            if dry_run:
                click.echo("(Dry run - no changes saved)")

    # Exit with code 1 if uncategorized remain
    if stats['uncategorized'] > 0:
        sys.exit(1)


@cli.command('list')
@click.option('-y', '--year', type=int, default=None, help='Fiscal year')
@click.option('-c', '--category', default=None, help='Filter by category')
@click.option('-u', '--uncategorized', is_flag=True, help='Show only uncategorized')
@click.option('-t', '--therapeutic', is_flag=True, help='Show only therapeutic')
@click.option('--from', 'from_date', default=None, help='Start date (YYYY-MM-DD)')
@click.option('--to', 'to_date', default=None, help='End date (YYYY-MM-DD)')
@click.option('-o', '--format', 'output_format', type=click.Choice(['table', 'json', 'csv']), default='table')
@click.option('-l', '--limit', type=int, default=50, help='Max rows')
@pass_context
def list_cmd(ctx: Context, year: Optional[int], category: Optional[str], uncategorized: bool,
             therapeutic: bool, from_date: Optional[str], to_date: Optional[str],
             output_format: str, limit: int):
    """List transactions with optional filtering."""
    import json
    import csv as csv_module
    from io import StringIO

    if year is None:
        year = datetime.now().year

    persistence = ctx.get_persistence()
    transactions = persistence.load_transactions(fiscal_year=year)

    # Apply filters
    filtered = []
    for tx in transactions:
        if tx.is_excluded:
            continue
        if uncategorized and tx.category is not None:
            continue
        if category and tx.category != category:
            continue
        if therapeutic and not tx.is_therapeutic:
            continue
        if from_date:
            from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
            if tx.booking_date < from_dt:
                continue
        if to_date:
            to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()
            if tx.booking_date > to_dt:
                continue
        filtered.append(tx)

    # Sort by date descending
    filtered.sort(key=lambda x: x.booking_date, reverse=True)

    # Apply limit
    total = len(filtered)
    if limit and limit < total:
        filtered = filtered[:limit]

    # Output
    if output_format == 'json':
        data = [tx.to_dict() for tx in filtered]
        click.echo(json.dumps(data, indent=2))
    elif output_format == 'csv':
        output = StringIO()
        writer = csv_module.writer(output)
        writer.writerow(['ID', 'Date', 'Amount', 'Category', 'Counterparty', 'Description'])
        for tx in filtered:
            writer.writerow([
                tx.id, tx.booking_date.isoformat(), str(tx.amount),
                tx.category or '', tx.counterparty_name or '', (tx.description or '')[:50]
            ])
        click.echo(output.getvalue())
    else:
        # Table format
        if not filtered:
            click.echo("No transactions found")
            return

        click.echo(f"{'ID':<12} {'Date':<12} {'Amount':>10} {'Category':<25} {'Counterparty':<30}")
        click.echo("-" * 95)
        for tx in filtered:
            cat = tx.category or '(uncategorized)'
            name = (tx.counterparty_name or '')[:28]
            click.echo(f"{tx.id:<12} {tx.booking_date.isoformat():<12} {tx.amount:>10.2f} {cat:<25} {name:<30}")
        click.echo(f"\nTotal: {total} transactions | Showing {len(filtered)}")


@cli.command()
@click.argument('transaction_id')
@click.argument('category')
@click.option('-t', '--therapeutic', is_flag=True, help='Mark as therapeutic')
@click.option('--note', default=None, help='Override note')
@pass_context
def assign(ctx: Context, transaction_id: str, category: str, therapeutic: bool, note: Optional[str]):
    """Manually assign category to a transaction."""
    persistence = ctx.get_persistence()

    # Validate category
    if not persistence.validate_category(category):
        click.echo(f"Error: Invalid category '{category}'")
        click.echo("Use 'plv categories' to see available categories")
        sys.exit(2)

    # Validate therapeutic flag
    if therapeutic and category != 'omzet':
        click.echo("Error: --therapeutic flag only valid for 'omzet' category")
        sys.exit(2)

    # Find and update transaction
    transactions = persistence.load_transactions()
    found = False

    for tx in transactions:
        if tx.id == transaction_id:
            tx.category = category
            tx.is_manual_override = True
            tx.matched_rule_id = None
            if therapeutic:
                tx.is_therapeutic = True
            found = True
            break

    if not found:
        click.echo(f"Error: Transaction '{transaction_id}' not found")
        sys.exit(1)

    # Save
    year = datetime.now().year
    persistence.save_transactions(transactions, year)

    if not ctx.quiet:
        click.echo(f"Assigned category '{category}' to transaction {transaction_id}")


@cli.group()
def rules():
    """Manage categorization rules."""
    pass


@rules.command('list')
@click.option('-c', '--category', default=None, help='Filter by category')
@click.option('-o', '--format', 'output_format', type=click.Choice(['table', 'json', 'yaml']), default='table')
@pass_context
def rules_list(ctx: Context, category: Optional[str], output_format: str):
    """List categorization rules."""
    import json
    import yaml

    persistence = ctx.get_persistence()
    rules_list = persistence.load_rules()

    # Filter by category
    if category:
        rules_list = [r for r in rules_list if r.target_category == category]

    if output_format == 'json':
        data = [r.to_dict() for r in rules_list]
        click.echo(json.dumps(data, indent=2))
    elif output_format == 'yaml':
        data = {'rules': [r.to_dict() for r in rules_list]}
        click.echo(yaml.dump(data, default_flow_style=False))
    else:
        if not rules_list:
            click.echo("No rules found")
            return
        click.echo(f"{'ID':<15} {'Pattern':<30} {'Type':<10} {'Category':<25}")
        click.echo("-" * 85)
        for r in rules_list:
            pattern = r.pattern[:28] if len(r.pattern) > 28 else r.pattern
            click.echo(f"{r.id:<15} {pattern:<30} {r.pattern_type:<10} {r.target_category:<25}")
        click.echo(f"\nTotal: {len(rules_list)} rules")


@rules.command('add')
@click.option('-p', '--pattern', required=True, help='Match pattern')
@click.option('-c', '--category', required=True, help='Target category')
@click.option('-t', '--type', 'pattern_type', type=click.Choice(['exact', 'prefix', 'contains', 'regex']), default='contains')
@click.option('-f', '--field', type=click.Choice(['counterparty_name', 'description', 'counterparty_iban']), default='counterparty_name')
@click.option('--priority', type=int, default=100, help='Priority (lower = higher)')
@click.option('--therapeutic', is_flag=True, help='Set therapeutic flag')
@pass_context
def rules_add(ctx: Context, pattern: str, category: str, pattern_type: str, field: str, priority: int, therapeutic: bool):
    """Add a new categorization rule."""
    from src.models.rule import CategoryRule
    import uuid

    persistence = ctx.get_persistence()

    # Validate category
    if not persistence.validate_category(category):
        click.echo(f"Error: Invalid category '{category}'")
        sys.exit(2)

    # Create rule
    rule_id = f"rule-{uuid.uuid4().hex[:8]}"
    rule = CategoryRule(
        id=rule_id,
        pattern=pattern,
        pattern_type=pattern_type,
        match_field=field,
        target_category=category,
        priority=priority,
        is_therapeutic=therapeutic if therapeutic else None,
        enabled=True,
        source='manual',
    )

    # Add to existing rules
    persistence.add_rule(rule)

    if not ctx.quiet:
        click.echo(f"Added rule '{rule_id}': {pattern} -> {category}")


@rules.command('disable')
@click.argument('rule_id')
@pass_context
def rules_disable(ctx: Context, rule_id: str):
    """Disable a categorization rule."""
    persistence = ctx.get_persistence()

    # Load all rules (including disabled)
    import yaml
    with open(persistence.rules_file, 'r') as f:
        data = yaml.safe_load(f)

    found = False
    for rule in data.get('rules', []):
        if rule['id'] == rule_id:
            rule['enabled'] = False
            found = True
            break

    if not found:
        click.echo(f"Error: Rule '{rule_id}' not found")
        sys.exit(1)

    with open(persistence.rules_file, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    if not ctx.quiet:
        click.echo(f"Disabled rule '{rule_id}'")


@rules.command('test')
@click.argument('pattern')
@click.option('-t', '--type', 'pattern_type', type=click.Choice(['exact', 'prefix', 'contains', 'regex']), default='contains')
@click.option('-f', '--field', type=click.Choice(['counterparty_name', 'description', 'counterparty_iban']), default='counterparty_name')
@pass_context
def rules_test(ctx: Context, pattern: str, pattern_type: str, field: str):
    """Test a pattern against existing transactions."""
    from src.models.rule import CategoryRule

    persistence = ctx.get_persistence()
    transactions = persistence.load_transactions()

    # Create a temporary rule for testing
    test_rule = CategoryRule(
        id='test',
        pattern=pattern,
        pattern_type=pattern_type,
        match_field=field,
        target_category='test',
        priority=1,
    )

    matches = []
    for tx in transactions:
        if tx.is_excluded:
            continue
        field_value = getattr(tx, field, None)
        if test_rule.matches(field_value):
            matches.append(tx)

    if not matches:
        click.echo(f"No matches for pattern '{pattern}'")
        return

    click.echo(f"Found {len(matches)} matches:\n")
    for tx in matches[:20]:
        field_value = getattr(tx, field, '') or ''
        click.echo(f"  {tx.id}: {field_value[:50]}")

    if len(matches) > 20:
        click.echo(f"  ... and {len(matches) - 20} more")


@cli.command()
@click.argument('excel_files', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('-s', '--sheet', default='Verrichtingen', help='Sheet name pattern')
@click.option('-m', '--min-occurrences', type=int, default=2, help='Min occurrences for rule')
@click.option('-o', '--output', default='config/rules.yaml', help='Output rules file')
@click.option('-n', '--dry-run', is_flag=True, help='Preview without saving')
@click.option('--merge', is_flag=True, help='Merge with existing rules')
@pass_context
def bootstrap(ctx: Context, excel_files: tuple, sheet: str, min_occurrences: int,
              output: str, dry_run: bool, merge: bool):
    """Extract categorization rules from Excel files."""
    import json
    from src.services.rule_extractor import extract_rules_from_excel_files

    files = [Path(f) for f in excel_files]
    rules, ambiguous = extract_rules_from_excel_files(
        files,
        sheet_name=sheet,
        min_occurrences=min_occurrences,
    )

    if merge:
        persistence = ctx.get_persistence()
        existing = persistence.load_rules()
        existing_patterns = {r.pattern.lower() for r in existing}
        rules = existing + [r for r in rules if r.pattern.lower() not in existing_patterns]

    # Output results
    if ctx.json_output:
        result = {
            'rules_extracted': len(rules),
            'patterns_ambiguous': len(ambiguous),
            'coverage_estimate': f"{len(rules) * 100 // max(len(rules) + len(ambiguous), 1)}%",
        }
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"Extracted: {len(rules)} rules")
        click.echo(f"Ambiguous: {len(ambiguous)} patterns (skipped)")

        if ambiguous and ctx.verbose:
            click.echo("\nAmbiguous patterns:")
            for a in ambiguous[:10]:
                click.echo(f"  {a['pattern']}: {a['categories']}")

    # Save if not dry run
    if not dry_run and rules:
        persistence = ctx.get_persistence()
        persistence.save_rules(rules)
        click.echo(f"\nSaved to {output}")
    elif dry_run:
        click.echo("\n(Dry run - no changes saved)")


@cli.group()
def assets():
    """Manage depreciable business assets."""
    pass


@assets.command('add')
@click.option('-n', '--name', required=True, help='Asset description')
@click.option('-d', '--date', 'purchase_date', required=True, help='Purchase date (YYYY-MM-DD)')
@click.option('-a', '--amount', required=True, type=float, help='Purchase amount in EUR')
@click.option('-y', '--years', required=True, type=int, help='Depreciation period (1-10 years)')
@click.option('--notes', default=None, help='Additional notes')
@pass_context
def assets_add(ctx: Context, name: str, purchase_date: str, amount: float, years: int, notes: Optional[str]):
    """Register a new depreciable asset."""
    from decimal import Decimal
    from src.services.asset_service import add_asset, calculate_annual_depreciation

    # Parse date
    try:
        parsed_date = datetime.strptime(purchase_date, "%Y-%m-%d").date()
    except ValueError:
        click.echo(f"Error: Invalid date format '{purchase_date}'. Use YYYY-MM-DD.")
        sys.exit(1)

    # Validate years
    if not (1 <= years <= 10):
        click.echo(f"Error: Depreciation years must be 1-10, got {years}")
        sys.exit(1)

    # Validate amount
    if amount <= 0:
        click.echo(f"Error: Amount must be positive, got {amount}")
        sys.exit(1)

    persistence = ctx.get_persistence()

    try:
        asset, duplicate = add_asset(
            persistence=persistence,
            name=name,
            purchase_date=parsed_date,
            purchase_amount=Decimal(str(amount)),
            depreciation_years=years,
            notes=notes,
            source="manual",
        )
    except ValueError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)

    # Calculate annual depreciation for display
    annual_dep = calculate_annual_depreciation(asset)

    # Output
    if ctx.json_output:
        import json
        result = asset.to_dict()
        result['annual_depreciation'] = str(annual_dep)
        click.echo(json.dumps(result, indent=2))
    else:
        if duplicate:
            click.echo(f"Warning: Similar asset exists: '{duplicate.name}' ({duplicate.id})")

        click.echo(f"Added asset '{asset.id}': {asset.name}")
        click.echo(f"  Purchase: €{asset.purchase_amount:.2f} on {asset.purchase_date}")
        first_year = asset.first_depreciation_year
        last_year = asset.last_depreciation_year
        click.echo(f"  Depreciation: €{annual_dep:.2f}/year for {years} years ({first_year}-{last_year})")


@assets.command('list')
@click.option('-s', '--status', type=click.Choice(['active', 'fully_depreciated', 'disposed', 'all']), default='all', help='Filter by status')
@click.option('-y', '--year', type=int, default=None, help='Show status as of year')
@click.option('-o', '--format', 'output_format', type=click.Choice(['table', 'json', 'csv']), default='table', help='Output format')
@pass_context
def assets_list(ctx: Context, status: str, year: Optional[int], output_format: str):
    """List all registered assets with their depreciation status."""
    import json
    import csv as csv_module
    from io import StringIO
    from src.services.depreciation import get_asset_status, get_book_value, get_current_depreciation_year
    from src.models.asset import AssetStatus

    if year is None:
        year = datetime.now().year

    persistence = ctx.get_persistence()
    assets = persistence.load_assets()

    # Filter by status
    filtered = []
    for asset in assets:
        asset_status = get_asset_status(asset, datetime(year, 12, 31).date())
        if status == 'all' or asset_status.value == status:
            filtered.append((asset, asset_status))

    # Calculate totals
    total_book_value = sum(get_book_value(a, year) for a, _ in filtered)

    if output_format == 'json':
        data = []
        for asset, asset_status in filtered:
            item = asset.to_dict()
            item['status'] = asset_status.value
            item['book_value'] = str(get_book_value(asset, year))
            item['annual_depreciation'] = str(asset.annual_depreciation)
            current_year = get_current_depreciation_year(asset, year)
            item['current_year'] = current_year
            data.append(item)
        click.echo(json.dumps(data, indent=2))
    elif output_format == 'csv':
        output = StringIO()
        writer = csv_module.writer(output)
        writer.writerow(['ID', 'Name', 'Purchase Date', 'Amount', 'Years', 'Status', 'Book Value'])
        for asset, asset_status in filtered:
            book_value = get_book_value(asset, year)
            writer.writerow([
                asset.id, asset.name, asset.purchase_date.isoformat(),
                str(asset.purchase_amount), asset.depreciation_years,
                asset_status.value, str(book_value)
            ])
        click.echo(output.getvalue())
    else:
        # Table format
        if not filtered:
            click.echo("No assets found")
            return

        click.echo(f"{'ID':<16} {'Name':<22} {'Purchase':<12} {'Amount':>10} {'Years':>6} {'Status':<20} {'Book Value':>12}")
        click.echo("-" * 105)
        for asset, asset_status in filtered:
            book_value = get_book_value(asset, year)
            current_year = get_current_depreciation_year(asset, year)
            status_str = asset_status.value
            if current_year:
                status_str = f"{asset_status.value} ({current_year}/{asset.depreciation_years})"
            click.echo(f"{asset.id:<16} {asset.name[:20]:<22} {asset.purchase_date.isoformat():<12} €{asset.purchase_amount:>8.2f} {asset.depreciation_years:>6} {status_str:<20} €{book_value:>10.2f}")

        click.echo(f"\nTotal: {len(filtered)} assets | Book value: €{total_book_value:.2f}")


@assets.command('depreciation')
@click.option('-y', '--year', type=int, default=None, help='Fiscal year')
@click.option('-o', '--format', 'output_format', type=click.Choice(['table', 'json', 'csv']), default='table', help='Output format')
@click.option('-d', '--detail', is_flag=True, help='Show detailed breakdown')
@pass_context
def assets_depreciation(ctx: Context, year: Optional[int], output_format: str, detail: bool):
    """Show depreciation schedule for a fiscal year."""
    import json
    from src.services.depreciation import get_depreciation_for_year, get_book_value

    if year is None:
        year = datetime.now().year

    persistence = ctx.get_persistence()
    assets = persistence.load_assets()
    entries = get_depreciation_for_year(assets, year)

    total_depreciation = sum(e.amount for e in entries)

    if output_format == 'json':
        data = {
            'fiscal_year': year,
            'total_depreciation': str(total_depreciation),
            'category': 'afschrijvingen',
            'entries': [e.to_dict() for e in entries],
        }
        click.echo(json.dumps(data, indent=2))
    else:
        # Table format
        click.echo(f"Depreciation Schedule: {year}")
        click.echo("=" * 30)
        click.echo()

        if not entries:
            click.echo("No depreciation for this year")
            return

        click.echo(f"Total depreciation: €{total_depreciation:.2f}")
        click.echo()
        click.echo("Category: afschrijvingen")

        for entry in entries:
            year_info = f"(year {entry.year_number} of {entry.year_number + int(entry.remaining_book_value > 0) * (int(entry.remaining_book_value / entry.amount) if entry.amount > 0 else 0)})"
            # Get total years from the asset
            for asset in assets:
                if asset.id == entry.asset_id:
                    year_info = f"(year {entry.year_number} of {asset.depreciation_years})"
                    break
            click.echo(f"  {entry.asset_name}: €{entry.amount:.2f} {year_info}")

        if detail:
            click.echo()
            click.echo("-" * 50)
            for entry in entries:
                for asset in assets:
                    if asset.id == entry.asset_id:
                        click.echo()
                        click.echo(f"Asset: {asset.name} ({asset.id})")
                        click.echo(f"  Purchase: €{asset.purchase_amount:.2f} on {asset.purchase_date}")
                        click.echo(f"  Period: {asset.depreciation_years} years ({asset.first_depreciation_year}-{asset.last_depreciation_year})")
                        click.echo()
                        click.echo("  Year   Depreciation   Book Value")
                        for y in range(asset.first_depreciation_year, asset.last_depreciation_year + 1):
                            annual = asset.annual_depreciation
                            book = get_book_value(asset, y)
                            marker = " ← current year" if y == year else ""
                            click.echo(f"  {y}   €{annual:>10.2f}   €{book:>10.2f}{marker}")
                        break


@assets.command('import')
@click.argument('excel_file', type=click.Path(exists=True))
@click.option('-s', '--sheet', default='Resultaat', help='Sheet name')
@click.option('-n', '--dry-run', is_flag=True, help='Preview without saving')
@click.option('--merge', is_flag=True, help='Merge with existing assets')
@pass_context
def assets_import(ctx: Context, excel_file: str, sheet: str, dry_run: bool, merge: bool):
    """Import assets from Excel Resultaat sheet (one-time migration)."""
    import json
    from pathlib import Path
    from src.services.asset_importer import import_and_save_assets

    persistence = ctx.get_persistence()

    try:
        imported, skipped, final = import_and_save_assets(
            persistence=persistence,
            file_path=Path(excel_file),
            sheet_name=sheet,
            merge=merge,
            dry_run=dry_run,
        )
    except FileNotFoundError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}")
        sys.exit(2)

    # Output
    if ctx.json_output:
        result = {
            'imported': len(imported),
            'skipped': len(skipped),
            'total': len(final),
            'dry_run': dry_run,
            'assets': [a.to_dict() for a in imported],
        }
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"Importing from: {Path(excel_file).name} (sheet: {sheet})")
        click.echo()

        if imported:
            click.echo(f"Found {len(imported)} depreciable assets:")
            click.echo()
            for asset in imported:
                years_range = f"{asset.first_depreciation_year}-{asset.last_depreciation_year}"
                click.echo(f"  {asset.name:<20} €{asset.purchase_amount:>8.2f}    {asset.depreciation_years} years ({years_range})")
            click.echo()

        click.echo(f"Imported: {len(imported)} assets")
        if skipped:
            click.echo(f"Skipped: {len(skipped)} duplicates")

        if dry_run:
            click.echo("\n(Dry run - no changes saved)")


@assets.command('dispose')
@click.argument('asset_id')
@click.option('-d', '--date', 'disposal_date', required=True, help='Disposal date (YYYY-MM-DD)')
@click.option('--notes', default=None, help='Reason for disposal')
@pass_context
def assets_dispose(ctx: Context, asset_id: str, disposal_date: str, notes: Optional[str]):
    """Mark an asset as disposed (sold/discarded)."""
    import json
    from src.services.asset_service import dispose_asset
    from src.services.depreciation import get_book_value

    # Parse date
    try:
        parsed_date = datetime.strptime(disposal_date, "%Y-%m-%d").date()
    except ValueError:
        click.echo(f"Error: Invalid date format '{disposal_date}'. Use YYYY-MM-DD.")
        sys.exit(1)

    persistence = ctx.get_persistence()

    try:
        asset = dispose_asset(
            persistence=persistence,
            asset_id=asset_id,
            disposal_date=parsed_date,
            notes=notes,
        )
    except ValueError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)

    # Calculate final depreciation year and book value
    final_dep_year = min(parsed_date.year, asset.last_depreciation_year)
    remaining_book_value = get_book_value(asset, parsed_date.year)

    # Output
    if ctx.json_output:
        result = asset.to_dict()
        result['final_depreciation_year'] = final_dep_year
        result['remaining_book_value'] = str(remaining_book_value)
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"Disposed asset '{asset.id}': {asset.name}")
        click.echo(f"  Disposal date: {asset.disposal_date}")
        click.echo(f"  Final depreciation year: {final_dep_year}")
        click.echo(f"  Remaining book value at disposal: €{remaining_book_value:.2f}")


@cli.command('report')
@click.option('-y', '--year', type=int, default=None, help='Fiscal year (default: current)')
@click.option('-o', '--output', 'output_path', default=None, help='Output file path for Excel export')
@pass_context
def report_cmd(ctx: Context, year: Optional[int], output_path: Optional[str]):
    """Generate a Profit & Loss report."""
    from src.services.report_generator import ReportGenerator
    
    if year is None:
        year = datetime.now().year

    persistence = ctx.get_persistence()
    transactions = persistence.load_transactions() # Load all transactions
    assets = persistence.load_assets()

    generator = ReportGenerator(transactions, assets)
    report = generator.generate_pnl_report(fiscal_year=year)

    if output_path:
        final_path = Path(output_path)
        if final_path.suffix.lower() not in ('.xlsx', '.xls'):
            click.echo("Error: Output file must have an .xlsx or .xls extension for Excel export.")
            sys.exit(1)
            
        if final_path.exists():
            i = 1
            stem = final_path.stem
            suffix = final_path.suffix
            while final_path.exists():
                final_path = final_path.with_name(f"{stem}-{i}{suffix}")
                i += 1
        
        try:
            generator.export_to_excel(report, final_path)
            if not ctx.quiet:
                click.echo(f"Report exported to {final_path}")
        except Exception as e:
            click.echo(f"Error exporting to Excel: {e}", err=True)
            sys.exit(1)
    else:
        # Display in console
        console_output = generator.format_for_console(report)
        click.echo(console_output)

@cli.command('export')
@click.option('-y', '--year', type=int, default=None, help='Fiscal year (default: all)')
@click.option('-o', '--output', 'output_path', required=True, help='Output file path')
@click.option('--format', 'file_format', type=click.Choice(['csv', 'excel']), default=None, help='Output format (inferred from extension if omitted)')
@pass_context
def export(ctx: Context, year: Optional[int], output_path: str, file_format: Optional[str]):
    """Export transactions to CSV or Excel file."""
    from src.services.exporter import export_to_csv, export_to_excel

    path = Path(output_path)
    
    # Infer format from extension if not provided
    if not file_format:
        if path.suffix.lower() == '.csv':
            file_format = 'csv'
        elif path.suffix.lower() in ('.xlsx', '.xls'):
            file_format = 'excel'
        else:
            click.echo("Error: Could not infer format from file extension. Please specify --format.")
            sys.exit(1)

    persistence = ctx.get_persistence()
    transactions = persistence.load_transactions()

    try:
        if file_format == 'csv':
            export_to_csv(transactions, path, fiscal_year=year)
        else:
            export_to_excel(transactions, path, fiscal_year=year)
        
        if not ctx.quiet:
            click.echo(f"Exported transactions to {path}")
            
    except Exception as e:
        click.echo(f"Error exporting transactions: {e}")
        sys.exit(1)



def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
