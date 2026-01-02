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
    # Will be implemented in Phase 7 (US5)
    click.echo("List command - not yet implemented")


@cli.command()
@click.argument('transaction_id')
@click.argument('category')
@click.option('-t', '--therapeutic', is_flag=True, help='Mark as therapeutic')
@click.option('--note', default=None, help='Override note')
@pass_context
def assign(ctx: Context, transaction_id: str, category: str, therapeutic: bool, note: Optional[str]):
    """Manually assign category to a transaction."""
    # Will be implemented in Phase 7 (US5)
    click.echo("Assign command - not yet implemented")


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
    # Will be implemented in Phase 6 (US4)
    click.echo("Rules list command - not yet implemented")


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
    # Will be implemented in Phase 6 (US4)
    click.echo("Rules add command - not yet implemented")


@rules.command('disable')
@click.argument('rule_id')
@pass_context
def rules_disable(ctx: Context, rule_id: str):
    """Disable a categorization rule."""
    # Will be implemented in Phase 6 (US4)
    click.echo("Rules disable command - not yet implemented")


@rules.command('test')
@click.argument('pattern')
@click.option('-t', '--type', 'pattern_type', type=click.Choice(['exact', 'prefix', 'contains', 'regex']), default='contains')
@click.option('-f', '--field', type=click.Choice(['counterparty_name', 'description', 'counterparty_iban']), default='counterparty_name')
@pass_context
def rules_test(ctx: Context, pattern: str, pattern_type: str, field: str):
    """Test a pattern against existing transactions."""
    # Will be implemented in Phase 6 (US4)
    click.echo("Rules test command - not yet implemented")


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
    # Will be implemented in Phase 6 (US4)
    click.echo("Bootstrap command - not yet implemented")


@cli.command()
@click.option('-o', '--format', 'output_format', type=click.Choice(['table', 'json', 'yaml']), default='table')
@pass_context
def categories(ctx: Context, output_format: str):
    """List available categories."""
    # Will be implemented in Phase 7 (US5)
    click.echo("Categories command - not yet implemented")


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
