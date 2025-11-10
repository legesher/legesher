"""Command-line interface for legesher-i18n language pack tools."""

import sys
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.table import Table

from .exceptions import PackValidationError
from .pack_loader import LanguagePackLoader
from .schema_validator import SchemaValidator
from .db import TranslationDatabase

console = Console()


@click.group()
@click.version_option(version="0.0.1", prog_name="legesher-i18n")
def cli():
    """Legesher i18n language pack tools.

    Validate language packs, show available versions, and generate
    compatibility matrices for Python keyword translations.
    """
    pass


@cli.command()
@click.argument("pack_file", type=click.Path(exists=True, path_type=Path))
@click.option("--strict", is_flag=True, help="Fail on warnings")
def validate(pack_file: Path, strict: bool):
    """Validate a language pack file.

    Checks schema validation, completeness, and inheritance chains.

    Examples:

        legesher-i18n validate languages/python/3.13/es.yml

        legesher-i18n validate languages/python/3.13/es.yml --strict
    """
    try:
        # Load pack data from YAML
        with open(pack_file) as f:
            pack_data = yaml.safe_load(f)

        # Schema validation
        console.print(f"[cyan]Validating:[/cyan] {pack_file}")
        pack_schema = SchemaValidator.validate_pack(pack_data, pack_file)
        console.print("✅ [green]Schema validation passed[/green]")

        # Check completeness
        warnings = SchemaValidator.check_completeness(pack_schema)
        if warnings:
            for warning in warnings:
                console.print(f"⚠️  [yellow]Warning:[/yellow] {warning}")
                if strict:
                    console.print(
                        "[red]Validation failed in strict mode (warnings present)[/red]"
                    )
                    sys.exit(1)

        # Try to load the pack with inheritance
        console.print("\n[cyan]Loading pack with inheritance...[/cyan]")

        # Determine pack root from file path
        # Navigate up to find the 'languages' directory
        current = pack_file.parent
        pack_root = None
        while current.parent != current:
            if current.name == "languages":
                pack_root = current  # The languages directory itself
                break
            current = current.parent

        # Try to load pack (may fail on security checks, which is OK for validation)
        pack = None
        try:
            loader = LanguagePackLoader(pack_root=pack_root)
            pack = loader.load(
                language=pack_schema.language,
                target=pack_schema.target,
                version=pack_schema.version,
            )
            console.print("✅ [green]Pack loaded successfully[/green]")
        except Exception as load_error:
            console.print(
                f"⚠️  [yellow]Warning:[/yellow] Pack loading failed: {load_error}"
            )
            console.print(
                "[dim]Schema validation passed, but pack cannot be loaded with inheritance.[/dim]"
            )

        # Display pack information
        console.print("\n[bold cyan]Pack Information:[/bold cyan]")
        if pack:
            console.print(f"   Language: [bold]{pack.language}[/bold]")
            console.print(f"   Target: [bold]{pack.target}[/bold]")
            console.print(f"   Version: [bold]{pack.version}[/bold]")
            console.print(f"   Keywords: [bold]{len(pack.keywords)}[/bold]")
            console.print(f"   Builtins: [bold]{len(pack.builtins)}[/bold]")

            if pack.inheritance_chain:
                chain = " → ".join(pack.inheritance_chain)
                console.print(f"   Inheritance: [dim]{chain}[/dim]")
            else:
                console.print("   Inheritance: [dim]none[/dim]")
        else:
            # Show basic info from schema
            console.print(f"   Language: [bold]{pack_schema.language}[/bold]")
            console.print(f"   Target: [bold]{pack_schema.target}[/bold]")
            console.print(f"   Version: [bold]{pack_schema.version}[/bold]")
            console.print(
                f"   Keywords: [bold]{len(pack_schema.keywords)}[/bold] (from schema only)"
            )
            console.print(
                f"   Builtins: [bold]{len(pack_schema.builtins)}[/bold] (from schema only)"
            )
            if pack_schema.extends:
                console.print(f"   Extends: [dim]{pack_schema.extends}[/dim]")

        # Success summary
        console.print(
            f"\n✅ [bold green]Validation complete![/bold green] "
            f"({len(warnings)} warning{'s' if len(warnings) != 1 else ''})"
        )

        sys.exit(0)

    except PackValidationError as e:
        console.print(f"\n❌ [red]Validation failed:[/red] {pack_file}")
        for error in e.errors:
            console.print(f"   [red]•[/red] {error}")
        sys.exit(1)

    except FileNotFoundError:
        console.print(f"❌ [red]Error:[/red] File not found: {pack_file}")
        sys.exit(1)

    except yaml.YAMLError as e:
        console.print(f"❌ [red]YAML parse error:[/red] {e}")
        sys.exit(1)

    except Exception as e:
        console.print(f"❌ [red]Unexpected error:[/red] {e}")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


@cli.command()
@click.argument("language", type=str)
@click.option("--target", default="python", help="Target language (default: python)")
def show(language: str, target: str):
    """Show all available versions for a language.

    Displays a table with version numbers, keyword counts, and inheritance.

    Examples:

        legesher-i18n show es

        legesher-i18n show ar --target python
    """
    try:
        # Find the languages directory
        # Start from package location and look for languages dir
        package_dir = Path(__file__).parent.parent
        languages_dir = package_dir / "languages"

        if not languages_dir.exists():
            console.print(
                f"❌ [red]Error:[/red] Languages directory not found at {languages_dir}"
            )
            sys.exit(1)

        # Find all version directories for this language and target
        target_dir = languages_dir / target
        if not target_dir.exists():
            console.print(f"❌ [red]Error:[/red] Target language '{target}' not found")
            sys.exit(1)

        # Collect all versions
        versions_data = []

        # Find all version directories
        version_dirs = [
            d for d in target_dir.iterdir() if d.is_dir() and d.name[0].isdigit()
        ]

        if not version_dirs:
            console.print(
                f"❌ [red]Error:[/red] No version directories found for {target}"
            )
            sys.exit(1)

        # Sort versions (3.10, 3.11, 3.12, 3.13)
        version_dirs.sort(key=lambda d: [int(x) for x in d.name.split(".")])

        # Check each version for the language pack
        for version_dir in version_dirs:
            version = version_dir.name
            pack_file = version_dir / f"{language}.yml"

            if pack_file.exists():
                try:
                    # Load pack data
                    with open(pack_file) as f:
                        pack_data = yaml.safe_load(f)

                    versions_data.append(
                        {
                            "version": version,
                            "keywords": len(pack_data.get("keywords", {})),
                            "builtins": len(pack_data.get("builtins", {})),
                            "extends": pack_data.get("extends", "—"),
                        }
                    )
                except Exception as e:
                    console.print(
                        f"⚠️  [yellow]Warning:[/yellow] Failed to load {version}: {e}"
                    )

        if not versions_data:
            console.print(
                f"❌ [red]Error:[/red] No language packs found for '{language}'"
            )
            console.print(
                f"\n[dim]Searched in: {target_dir}/<version>/{language}.yml[/dim]"
            )
            sys.exit(1)

        # Create rich table
        table = Table(title=f"{language.upper()} Language Packs for {target.title()}")
        table.add_column("Version", style="cyan", no_wrap=True)
        table.add_column("Keywords", justify="right", style="green")
        table.add_column("Builtins", justify="right", style="green")
        table.add_column("Extends", style="dim")

        for data in versions_data:
            # Format extends path - show just the version if it's a parent reference
            extends = data["extends"]
            if extends != "—" and "../" in extends:
                # Extract version from path like ../3.10/es.yml
                import re

                match = re.search(r"(\d+\.\d+)", extends)
                if match:
                    extends = f"→ {match.group(1)}"

            table.add_row(
                data["version"],
                str(data["keywords"]),
                str(data["builtins"]),
                extends,
            )

        console.print()
        console.print(table)
        console.print(
            f"\n[dim]Found {len(versions_data)} version(s) for {language}[/dim]"
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"❌ [red]Error:[/red] {e}")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


@click.group()
def db():
    """Database management commands.

    Manage the translation database for storing translations from multiple
    sources (community, AI models) with review history.
    """
    pass


@db.command()
@click.option(
    "--db-path",
    default=".legesher/translations.db",
    help="Path to database file",
    type=click.Path(path_type=Path),
)
def init(db_path: Path):
    """Initialize the translation database.

    Creates the database file and all required tables if they don't exist.

    Examples:

        legesher-i18n db init

        legesher-i18n db init --db-path /custom/path/translations.db
    """
    try:
        console.print(f"[cyan]Initializing database at:[/cyan] {db_path}")

        # Check if database already exists
        if db_path.exists():
            console.print(f"[yellow]Database already exists at:[/yellow] {db_path}")
            console.print("[dim]Tables will be created if they don't exist.[/dim]")

        # Initialize database
        db = TranslationDatabase(db_path=str(db_path))
        db.close()

        console.print("✅ [green]Database initialized successfully![/green]")
        console.print(f"\n[dim]Location: {db_path}[/dim]")

    except Exception as e:
        console.print(f"❌ [red]Error initializing database:[/red] {e}")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


@db.command()
@click.option(
    "--db-path",
    default=".legesher/translations.db",
    help="Path to database file",
    type=click.Path(exists=True, path_type=Path),
)
def stats(db_path: Path):
    """Show database statistics.

    Displays counts of translations, reviews, and other data by source and language.

    Examples:

        legesher-i18n db stats

        legesher-i18n db stats --db-path /custom/path/translations.db
    """
    try:
        db = TranslationDatabase(db_path=str(db_path))

        # Get statistics
        conn = db._get_connection()

        # Total translations
        total_translations = conn.execute(
            "SELECT COUNT(*) FROM translations"
        ).fetchone()[0]

        # Translations by source
        source_stats = conn.execute("""
            SELECT source, COUNT(*) as count
            FROM translations
            GROUP BY source
            ORDER BY count DESC
        """).fetchall()

        # Translations by language
        language_stats = conn.execute("""
            SELECT language_code, COUNT(*) as count
            FROM translations
            GROUP BY language_code
            ORDER BY count DESC
        """).fetchall()

        # Total reviews
        total_reviews = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]

        # Total deep contexts
        total_contexts = conn.execute("SELECT COUNT(*) FROM deep_contexts").fetchone()[
            0
        ]

        # Total linguistic standards
        total_standards = conn.execute(
            "SELECT COUNT(*) FROM linguistic_standards"
        ).fetchone()[0]

        db.close()

        # Display overview
        console.print("\n[bold cyan]Translation Database Statistics[/bold cyan]\n")

        # Summary table
        summary_table = Table(title="Overview")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", justify="right", style="green")

        summary_table.add_row("Total Translations", str(total_translations))
        summary_table.add_row("Total Reviews", str(total_reviews))
        summary_table.add_row("Deep Contexts", str(total_contexts))
        summary_table.add_row("Linguistic Standards", str(total_standards))

        console.print(summary_table)

        # Translations by source
        if source_stats:
            console.print("\n[bold]Translations by Source[/bold]\n")
            source_table = Table()
            source_table.add_column("Source", style="cyan")
            source_table.add_column("Count", justify="right", style="green")

            for source, count in source_stats:
                source_table.add_row(source, str(count))

            console.print(source_table)

        # Translations by language
        if language_stats:
            console.print("\n[bold]Translations by Language[/bold]\n")
            lang_table = Table()
            lang_table.add_column("Language", style="cyan")
            lang_table.add_column("Count", justify="right", style="green")

            for language, count in language_stats:
                lang_table.add_row(language, str(count))

            console.print(lang_table)

        console.print(f"\n[dim]Database: {db_path}[/dim]\n")

    except FileNotFoundError:
        console.print(f"❌ [red]Error:[/red] Database not found at {db_path}")
        console.print(
            "\n[dim]Run 'legesher-i18n db init' to create the database.[/dim]"
        )
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ [red]Error reading database:[/red] {e}")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


@db.command()
@click.option(
    "--db-path",
    default=".legesher/translations.db",
    help="Path to database file",
    type=click.Path(exists=True, path_type=Path),
)
def vacuum(db_path: Path):
    """Optimize database size.

    Runs SQLite VACUUM command to reclaim unused space and optimize the database file.

    Examples:

        legesher-i18n db vacuum

        legesher-i18n db vacuum --db-path /custom/path/translations.db
    """
    try:
        console.print(f"[cyan]Optimizing database:[/cyan] {db_path}")

        db = TranslationDatabase(db_path=str(db_path))
        conn = db._get_connection()

        # Get size before
        size_before = db_path.stat().st_size

        # Run VACUUM
        conn.execute("VACUUM")

        # Get size after
        size_after = db_path.stat().st_size

        db.close()

        # Calculate savings
        savings = size_before - size_after
        percent_saved = (savings / size_before * 100) if size_before > 0 else 0

        console.print("✅ [green]Database optimized successfully![/green]")
        console.print(f"\n[dim]Size before: {size_before:,} bytes[/dim]")
        console.print(f"[dim]Size after: {size_after:,} bytes[/dim]")
        console.print(f"[dim]Saved: {savings:,} bytes ({percent_saved:.1f}%)[/dim]")

    except FileNotFoundError:
        console.print(f"❌ [red]Error:[/red] Database not found at {db_path}")
        console.print(
            "\n[dim]Run 'legesher-i18n db init' to create the database.[/dim]"
        )
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ [red]Error optimizing database:[/red] {e}")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


# Add db group to main CLI
cli.add_command(db)


if __name__ == "__main__":
    cli()
