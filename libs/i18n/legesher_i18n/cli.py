"""Command-line interface for legesher-i18n language pack tools."""

import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import TextIO

import click
import yaml
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.table import Table

from .exceptions import PackValidationError
from .pack_loader import LanguagePackLoader, LanguagePack
from .schema_validator import SchemaValidator
from .db import TranslationDatabase

# Default database path — resolved once so Click's exists=True check works
_DEFAULT_DB_PATH = Path(__file__).parent / "db" / "translations.db"

# Global console instance - can be replaced with quiet version
console = Console()


def _get_version() -> str:
    """Get package version dynamically."""
    try:
        from importlib.metadata import version

        return version("legesher-i18n")
    except Exception:
        return "0.2.1"


def _get_loader() -> LanguagePackLoader:
    """Get a configured LanguagePackLoader instance."""
    return LanguagePackLoader()


# Fallback language names for common language codes
# Used when metadata is not available from language packs
LANGUAGE_NAME_FALLBACKS = {
    "ar": "Arabic",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "fi": "Finnish",
    "fr": "French",
    "he": "Hebrew",
    "hi": "Hindi",
    "hu": "Hungarian",
    "id": "Indonesian",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "ms": "Malay",
    "nl": "Dutch",
    "no": "Norwegian",
    "pl": "Polish",
    "pt": "Portuguese",
    "ru": "Russian",
    "sv": "Swedish",
    "th": "Thai",
    "tr": "Turkish",
    "vi": "Vietnamese",
    "zh": "Chinese",
}


@lru_cache(maxsize=64)
def _get_language_name(lang_code: str) -> str:
    """Get the full language name for a language code.

    Uses LanguagePackLoader to discover available languages and their names.
    Falls back to LANGUAGE_NAME_FALLBACKS or uppercase language code if not found.

    Results are cached for performance when called repeatedly (e.g., in export all).
    """
    loader = _get_loader()

    # Get available languages with names from the loader
    available = loader.list_available_languages("python")
    for code, name in available:
        if code == lang_code:
            return name

    # Fallback to known language names
    if lang_code in LANGUAGE_NAME_FALLBACKS:
        return LANGUAGE_NAME_FALLBACKS[lang_code]

    # Last resort: uppercase code
    return lang_code.upper()


# Python documentation URLs for keywords
# Reference: https://docs.python.org/3/reference/lexical_analysis.html#keywords
KEYWORD_DOCS = {
    "False": "https://docs.python.org/3/library/constants.html#False",
    "None": "https://docs.python.org/3/library/constants.html#None",
    "True": "https://docs.python.org/3/library/constants.html#True",
    "and": "https://docs.python.org/3/reference/expressions.html#boolean-operations",
    "as": "https://docs.python.org/3/reference/compound_stmts.html#the-with-statement",
    "assert": "https://docs.python.org/3/reference/simple_stmts.html#the-assert-statement",
    "async": "https://docs.python.org/3/reference/compound_stmts.html#coroutines",
    "await": "https://docs.python.org/3/reference/expressions.html#await-expression",
    "break": "https://docs.python.org/3/reference/simple_stmts.html#the-break-statement",
    "case": "https://docs.python.org/3/reference/compound_stmts.html#the-match-statement",
    "class": "https://docs.python.org/3/reference/compound_stmts.html#class-definitions",
    "continue": "https://docs.python.org/3/reference/simple_stmts.html#the-continue-statement",
    "def": "https://docs.python.org/3/reference/compound_stmts.html#function-definitions",
    "del": "https://docs.python.org/3/reference/simple_stmts.html#the-del-statement",
    "elif": "https://docs.python.org/3/reference/compound_stmts.html#the-if-statement",
    "else": "https://docs.python.org/3/reference/compound_stmts.html#the-if-statement",
    "except": "https://docs.python.org/3/reference/compound_stmts.html#the-try-statement",
    "except*": "https://docs.python.org/3/reference/compound_stmts.html#except-star",
    "finally": "https://docs.python.org/3/reference/compound_stmts.html#the-try-statement",
    "for": "https://docs.python.org/3/reference/compound_stmts.html#the-for-statement",
    "from": "https://docs.python.org/3/reference/simple_stmts.html#the-import-statement",
    "global": "https://docs.python.org/3/reference/simple_stmts.html#the-global-statement",
    "if": "https://docs.python.org/3/reference/compound_stmts.html#the-if-statement",
    "import": "https://docs.python.org/3/reference/simple_stmts.html#the-import-statement",
    "in": "https://docs.python.org/3/reference/expressions.html#membership-test-operations",
    "is": "https://docs.python.org/3/reference/expressions.html#is-not",
    "lambda": "https://docs.python.org/3/reference/expressions.html#lambda",
    "match": "https://docs.python.org/3/reference/compound_stmts.html#the-match-statement",
    "nonlocal": "https://docs.python.org/3/reference/simple_stmts.html#the-nonlocal-statement",
    "not": "https://docs.python.org/3/reference/expressions.html#boolean-operations",
    "or": "https://docs.python.org/3/reference/expressions.html#boolean-operations",
    "pass": "https://docs.python.org/3/reference/simple_stmts.html#the-pass-statement",
    "raise": "https://docs.python.org/3/reference/simple_stmts.html#the-raise-statement",
    "return": "https://docs.python.org/3/reference/simple_stmts.html#the-return-statement",
    "try": "https://docs.python.org/3/reference/compound_stmts.html#the-try-statement",
    "type": "https://docs.python.org/3/reference/simple_stmts.html#the-type-statement",
    "while": "https://docs.python.org/3/reference/compound_stmts.html#the-while-statement",
    "with": "https://docs.python.org/3/reference/compound_stmts.html#the-with-statement",
    "yield": "https://docs.python.org/3/reference/expressions.html#yield-expressions",
}

# Python documentation URLs for builtins
# Reference: https://docs.python.org/3/library/functions.html
BUILTIN_DOCS = {
    "abs": "https://docs.python.org/3/library/functions.html#abs",
    "aiter": "https://docs.python.org/3/library/functions.html#aiter",
    "all": "https://docs.python.org/3/library/functions.html#all",
    "anext": "https://docs.python.org/3/library/functions.html#anext",
    "any": "https://docs.python.org/3/library/functions.html#any",
    "ascii": "https://docs.python.org/3/library/functions.html#ascii",
    "bin": "https://docs.python.org/3/library/functions.html#bin",
    "bool": "https://docs.python.org/3/library/functions.html#bool",
    "breakpoint": "https://docs.python.org/3/library/functions.html#breakpoint",
    "bytearray": "https://docs.python.org/3/library/functions.html#func-bytearray",
    "bytes": "https://docs.python.org/3/library/functions.html#func-bytes",
    "callable": "https://docs.python.org/3/library/functions.html#callable",
    "chr": "https://docs.python.org/3/library/functions.html#chr",
    "classmethod": "https://docs.python.org/3/library/functions.html#classmethod",
    "compile": "https://docs.python.org/3/library/functions.html#compile",
    "complex": "https://docs.python.org/3/library/functions.html#complex",
    "delattr": "https://docs.python.org/3/library/functions.html#delattr",
    "dict": "https://docs.python.org/3/library/functions.html#func-dict",
    "dir": "https://docs.python.org/3/library/functions.html#dir",
    "divmod": "https://docs.python.org/3/library/functions.html#divmod",
    "enumerate": "https://docs.python.org/3/library/functions.html#enumerate",
    "eval": "https://docs.python.org/3/library/functions.html#eval",
    "exec": "https://docs.python.org/3/library/functions.html#exec",
    "filter": "https://docs.python.org/3/library/functions.html#filter",
    "float": "https://docs.python.org/3/library/functions.html#float",
    "format": "https://docs.python.org/3/library/functions.html#format",
    "frozenset": "https://docs.python.org/3/library/functions.html#func-frozenset",
    "getattr": "https://docs.python.org/3/library/functions.html#getattr",
    "globals": "https://docs.python.org/3/library/functions.html#globals",
    "hasattr": "https://docs.python.org/3/library/functions.html#hasattr",
    "hash": "https://docs.python.org/3/library/functions.html#hash",
    "help": "https://docs.python.org/3/library/functions.html#help",
    "hex": "https://docs.python.org/3/library/functions.html#hex",
    "id": "https://docs.python.org/3/library/functions.html#id",
    "input": "https://docs.python.org/3/library/functions.html#input",
    "int": "https://docs.python.org/3/library/functions.html#int",
    "isinstance": "https://docs.python.org/3/library/functions.html#isinstance",
    "issubclass": "https://docs.python.org/3/library/functions.html#issubclass",
    "iter": "https://docs.python.org/3/library/functions.html#iter",
    "len": "https://docs.python.org/3/library/functions.html#len",
    "list": "https://docs.python.org/3/library/functions.html#func-list",
    "locals": "https://docs.python.org/3/library/functions.html#locals",
    "map": "https://docs.python.org/3/library/functions.html#map",
    "max": "https://docs.python.org/3/library/functions.html#max",
    "memoryview": "https://docs.python.org/3/library/functions.html#func-memoryview",
    "min": "https://docs.python.org/3/library/functions.html#min",
    "next": "https://docs.python.org/3/library/functions.html#next",
    "object": "https://docs.python.org/3/library/functions.html#object",
    "oct": "https://docs.python.org/3/library/functions.html#oct",
    "open": "https://docs.python.org/3/library/functions.html#open",
    "ord": "https://docs.python.org/3/library/functions.html#ord",
    "pow": "https://docs.python.org/3/library/functions.html#pow",
    "print": "https://docs.python.org/3/library/functions.html#print",
    "property": "https://docs.python.org/3/library/functions.html#property",
    "range": "https://docs.python.org/3/library/functions.html#func-range",
    "repr": "https://docs.python.org/3/library/functions.html#repr",
    "reversed": "https://docs.python.org/3/library/functions.html#reversed",
    "round": "https://docs.python.org/3/library/functions.html#round",
    "set": "https://docs.python.org/3/library/functions.html#func-set",
    "setattr": "https://docs.python.org/3/library/functions.html#setattr",
    "slice": "https://docs.python.org/3/library/functions.html#slice",
    "sorted": "https://docs.python.org/3/library/functions.html#sorted",
    "staticmethod": "https://docs.python.org/3/library/functions.html#staticmethod",
    "str": "https://docs.python.org/3/library/functions.html#func-str",
    "sum": "https://docs.python.org/3/library/functions.html#sum",
    "super": "https://docs.python.org/3/library/functions.html#super",
    "tuple": "https://docs.python.org/3/library/functions.html#func-tuple",
    "type": "https://docs.python.org/3/library/functions.html#type",
    "vars": "https://docs.python.org/3/library/functions.html#vars",
    "zip": "https://docs.python.org/3/library/functions.html#zip",
    "__import__": "https://docs.python.org/3/library/functions.html#import__",
}

# Exception documentation URLs
EXCEPTION_DOCS = "https://docs.python.org/3/library/exceptions.html"

# Default example identifiers (language-neutral, commonly used in programming)
# These are simple identifiers that work across all languages
DEFAULT_EXAMPLE_NAMES = {
    "func": "func",
    "class": "MyClass",
    "var": "x",
    "list": "items",
    "result": "result",
    "value": "value",
    "condition": "condition",
}


class QuietConsole:
    """A console that suppresses all output for --quiet mode."""

    def print(self, *args, **kwargs):
        """Do nothing - suppress output."""
        pass


def get_console(quiet: bool = False) -> Console:
    """Get appropriate console based on quiet flag."""
    if quiet:
        return QuietConsole()  # type: ignore
    return console


@click.group()
@click.version_option(version=_get_version(), prog_name="legesher-i18n")
def cli():
    """Legesher i18n language pack tools.

    Validate language packs, show available versions, and generate
    compatibility matrices for Python keyword translations.
    """
    pass


@cli.command()
@click.argument("pack_file", type=click.Path(exists=True, path_type=Path))
@click.option("--strict", is_flag=True, help="Fail on warnings")
@click.option("--quiet", "-q", is_flag=True, help="Suppress output (for CI/scripts)")
def validate(pack_file: Path, strict: bool, quiet: bool):
    """Validate a language pack file.

    Checks schema validation, completeness, and inheritance chains.

    Examples:

        legesher-i18n validate programming_languages/python/3.13/es.yml

        legesher-i18n validate programming_languages/python/3.13/es.yml --strict
    """
    out = get_console(quiet)
    try:
        # Load pack data from YAML
        with open(pack_file, encoding="utf-8") as f:
            pack_data = yaml.safe_load(f)

        # Schema validation
        out.print(f"[cyan]Validating:[/cyan] {pack_file}")
        pack_schema = SchemaValidator.validate_pack(pack_data, pack_file)
        out.print("✅ [green]Schema validation passed[/green]")

        # Check completeness
        warnings = SchemaValidator.check_completeness(pack_schema)
        if warnings:
            for warning in warnings:
                out.print(f"⚠️  [yellow]Warning:[/yellow] {warning}")
                if strict:
                    out.print(
                        "[red]Validation failed in strict mode (warnings present)[/red]"
                    )
                    sys.exit(1)

        # Try to load the pack with inheritance
        out.print("\n[cyan]Loading pack with inheritance...[/cyan]")

        # Determine pack root from file path
        # Navigate up to find the 'programming_languages' directory
        current = pack_file.parent
        pack_root = None
        while current.parent != current:
            if current.name == "programming_languages":
                pack_root = current  # The programming_languages directory itself
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
            out.print("✅ [green]Pack loaded successfully[/green]")
        except Exception as load_error:
            out.print(f"⚠️  [yellow]Warning:[/yellow] Pack loading failed: {load_error}")
            out.print(
                "[dim]Schema validation passed, but pack cannot be loaded with inheritance.[/dim]"
            )

        # Display pack information
        out.print("\n[bold cyan]Pack Information:[/bold cyan]")
        if pack:
            out.print(f"   Language: [bold]{pack.language}[/bold]")
            out.print(f"   Target: [bold]{pack.target}[/bold]")
            out.print(f"   Version: [bold]{pack.version}[/bold]")
            out.print(f"   Keywords: [bold]{len(pack.keywords)}[/bold]")
            out.print(f"   Builtins: [bold]{len(pack.builtins)}[/bold]")

            if pack.inheritance_chain:
                chain = " → ".join(pack.inheritance_chain)
                out.print(f"   Inheritance: [dim]{chain}[/dim]")
            else:
                out.print("   Inheritance: [dim]none[/dim]")
        else:
            # Show basic info from schema
            out.print(f"   Language: [bold]{pack_schema.language}[/bold]")
            out.print(f"   Target: [bold]{pack_schema.target}[/bold]")
            out.print(f"   Version: [bold]{pack_schema.version}[/bold]")
            out.print(
                f"   Keywords: [bold]{len(pack_schema.keywords)}[/bold] (from schema only)"
            )
            out.print(
                f"   Builtins: [bold]{len(pack_schema.builtins)}[/bold] (from schema only)"
            )
            if pack_schema.extends:
                out.print(f"   Extends: [dim]{pack_schema.extends}[/dim]")

        # Success summary
        out.print(
            f"\n✅ [bold green]Validation complete![/bold green] "
            f"({len(warnings)} warning{'s' if len(warnings) != 1 else ''})"
        )

        sys.exit(0)

    except PackValidationError as e:
        out.print(f"\n❌ [red]Validation failed:[/red] {pack_file}")
        for error in e.errors:
            out.print(f"   [red]•[/red] {error}")
        sys.exit(1)

    except FileNotFoundError:
        out.print(f"❌ [red]Error:[/red] File not found: {pack_file}")
        sys.exit(1)

    except yaml.YAMLError as e:
        out.print(f"❌ [red]YAML parse error:[/red] {e}")
        sys.exit(1)

    except Exception as e:
        out.print(f"❌ [red]Unexpected error:[/red] {e}")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


@cli.command()
@click.argument("language", type=str)
@click.option("--target", default="python", help="Target language (default: python)")
@click.option("--quiet", "-q", is_flag=True, help="Suppress output (for CI/scripts)")
def show(language: str, target: str, quiet: bool):
    """Show all available versions for a language.

    Displays a table with version numbers, keyword counts, and inheritance.

    Examples:

        legesher-i18n show es

        legesher-i18n show ar --target python
    """
    out = get_console(quiet)
    try:
        # Find the programming_languages directory
        # Start from package location and look for programming_languages dir
        package_dir = Path(__file__).parent.parent
        languages_dir = package_dir / "programming_languages"

        if not languages_dir.exists():
            out.print(
                f"❌ [red]Error:[/red] Programming languages directory not found at {languages_dir}"
            )
            sys.exit(1)

        # Find all version directories for this language and target
        target_dir = languages_dir / target
        if not target_dir.exists():
            out.print(f"❌ [red]Error:[/red] Target language '{target}' not found")
            sys.exit(1)

        # Collect all versions
        versions_data = []

        # Find all version directories
        version_dirs = [
            d for d in target_dir.iterdir() if d.is_dir() and d.name[0].isdigit()
        ]

        if not version_dirs:
            out.print(f"❌ [red]Error:[/red] No version directories found for {target}")
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
                    with open(pack_file, encoding="utf-8") as f:
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
                    out.print(
                        f"⚠️  [yellow]Warning:[/yellow] Failed to load {version}: {e}"
                    )

        if not versions_data:
            out.print(f"❌ [red]Error:[/red] No language packs found for '{language}'")
            out.print(
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
                match = re.search(r"(\d+\.\d+)", extends)
                if match:
                    extends = f"→ {match.group(1)}"

            table.add_row(
                data["version"],
                str(data["keywords"]),
                str(data["builtins"]),
                extends,
            )

        out.print()
        out.print(table)
        out.print(f"\n[dim]Found {len(versions_data)} version(s) for {language}[/dim]")

    except KeyboardInterrupt:
        out.print("\n[yellow]Interrupted[/yellow]")
        sys.exit(130)
    except Exception as e:
        out.print(f"❌ [red]Error:[/red] {e}")
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
    default=None,
    help="Path to database file (default: package db)",
    type=click.Path(path_type=Path),
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress output (for CI/scripts)")
def init(db_path: Path | None, quiet: bool):
    """Initialize the translation database.

    Creates the database file and all required tables if they don't exist.

    Examples:

        legesher-i18n db init

        legesher-i18n db init --db-path /custom/path/translations.db
    """
    out = get_console(quiet)
    try:
        # Resolve the path before instantiation to check pre-existence
        if db_path:
            resolved_path = Path(db_path).resolve()
        else:
            resolved_path = (Path(__file__).parent / "db" / "translations.db").resolve()

        already_exists = resolved_path.exists()

        out.print(f"[cyan]Initializing database at:[/cyan] {resolved_path}")

        database = TranslationDatabase(db_path=str(db_path) if db_path else None)

        if already_exists:
            out.print(f"[yellow]Database already exists at:[/yellow] {resolved_path}")
            out.print("[dim]Tables will be created if they don't exist.[/dim]")

        database.close()

        out.print("✅ [green]Database initialized successfully![/green]")
        out.print(f"\n[dim]Location: {resolved_path}[/dim]")

    except Exception as e:
        out.print(f"❌ [red]Error initializing database:[/red] {e}")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


@db.command()
@click.option(
    "--db-path",
    default=_DEFAULT_DB_PATH,
    help="Path to database file (default: package db)",
    type=click.Path(exists=True, path_type=Path),
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress output (for CI/scripts)")
def stats(db_path: Path, quiet: bool):
    """Show database statistics.

    Displays counts of terms, translations, selected translations, and languages.

    Examples:

        legesher-i18n db stats

        legesher-i18n db stats --db-path /custom/path/translations.db
    """
    out = get_console(quiet)
    try:
        database = TranslationDatabase(db_path=str(db_path))
        db_stats = database.get_stats()

        conn = database._get_connection()

        # Translations by source
        source_stats = conn.execute(
            """
            SELECT source, COUNT(*) as count
            FROM translations
            GROUP BY source
            ORDER BY count DESC
        """
        ).fetchall()

        # Translations by language
        language_stats = conn.execute(
            """
            SELECT language_code, COUNT(*) as count
            FROM translations
            GROUP BY language_code
            ORDER BY count DESC
        """
        ).fetchall()

        database.close()

        # Display overview
        out.print("\n[bold cyan]Translation Database Statistics[/bold cyan]\n")

        # Summary table
        summary_table = Table(title="Overview")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", justify="right", style="green")

        summary_table.add_row("Terms", str(db_stats["terms_count"]))
        summary_table.add_row("Languages", str(db_stats["languages_count"]))
        summary_table.add_row(
            "  With YAML Packs", str(db_stats["languages_with_packs"])
        )
        summary_table.add_row(
            "Translation Suggestions", str(db_stats["translations_count"])
        )
        summary_table.add_row(
            "Selected Translations", str(db_stats["selected_translations_count"])
        )

        out.print(summary_table)

        # Terms by category
        if db_stats.get("terms_by_category"):
            out.print("\n[bold]Terms by Category[/bold]\n")
            cat_table = Table()
            cat_table.add_column("Category", style="cyan")
            cat_table.add_column("Count", justify="right", style="green")
            for cat, count in sorted(db_stats["terms_by_category"].items()):
                cat_table.add_row(cat, str(count))
            out.print(cat_table)

        # Translations by source
        if source_stats:
            out.print("\n[bold]Translations by Source[/bold]\n")
            source_table = Table()
            source_table.add_column("Source", style="cyan")
            source_table.add_column("Count", justify="right", style="green")

            for source, count in source_stats:
                source_table.add_row(source, str(count))

            out.print(source_table)

        # Translations by language
        if language_stats:
            out.print("\n[bold]Translations by Language[/bold]\n")
            lang_table = Table()
            lang_table.add_column("Language", style="cyan")
            lang_table.add_column("Count", justify="right", style="green")

            for lang, count in language_stats:
                lang_table.add_row(lang, str(count))

            out.print(lang_table)

        out.print(f"\n[dim]Database: {database.db_path}[/dim]\n")

    except FileNotFoundError:
        out.print(f"❌ [red]Error:[/red] Database not found at {db_path}")
        out.print("\n[dim]Run 'legesher-i18n db init' to create the database.[/dim]")
        sys.exit(1)
    except Exception as e:
        out.print(f"❌ [red]Error reading database:[/red] {e}")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


@db.command()
@click.option(
    "--db-path",
    default=_DEFAULT_DB_PATH,
    help="Path to database file (default: package db)",
    type=click.Path(exists=True, path_type=Path),
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress output (for CI/scripts)")
def vacuum(db_path: Path, quiet: bool):
    """Optimize database size.

    Runs SQLite VACUUM command to reclaim unused space and optimize the database file.

    Examples:

        legesher-i18n db vacuum

        legesher-i18n db vacuum --db-path /custom/path/translations.db
    """
    out = get_console(quiet)
    try:
        database = TranslationDatabase(db_path=str(db_path))
        resolved_path = Path(database.db_path)
        out.print(f"[cyan]Optimizing database:[/cyan] {resolved_path}")

        conn = database._get_connection()

        # Get size before
        size_before = resolved_path.stat().st_size

        # Run VACUUM
        conn.execute("VACUUM")

        # Get size after
        size_after = resolved_path.stat().st_size

        database.close()

        # Calculate savings
        savings = size_before - size_after
        percent_saved = (savings / size_before * 100) if size_before > 0 else 0

        out.print("✅ [green]Database optimized successfully![/green]")
        out.print(f"\n[dim]Size before: {size_before:,} bytes[/dim]")
        out.print(f"[dim]Size after: {size_after:,} bytes[/dim]")
        out.print(f"[dim]Saved: {savings:,} bytes ({percent_saved:.1f}%)[/dim]")

    except FileNotFoundError:
        out.print(f"❌ [red]Error:[/red] Database not found at {db_path}")
        out.print("\n[dim]Run 'legesher-i18n db init' to create the database.[/dim]")
        sys.exit(1)
    except Exception as e:
        out.print(f"❌ [red]Error optimizing database:[/red] {e}")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


@db.command()
@click.option(
    "--db-path",
    default=None,
    help="Path to database file (default: package db)",
    type=click.Path(path_type=Path),
)
@click.option(
    "--language",
    "-l",
    default=None,
    help="Filter by language code (e.g., fi, el, hu)",
)
@click.option("--json-output", "--json", is_flag=True, help="Output as JSON")
@click.option("--quiet", "-q", is_flag=True, help="Suppress output (for CI/scripts)")
def collisions(
    db_path: Path | None, language: str | None, json_output: bool, quiet: bool
):
    """Detect translation collisions in the database.

    A collision occurs when the same translated word is the selected
    translation for 2+ different Python terms in the same language.
    Collisions break round-trip translation because the translator
    cannot determine which English keyword to map back to.

    Examples:

        legesher-i18n db collisions

        legesher-i18n db collisions --language fi

        legesher-i18n db collisions --json
    """
    out = get_console(quiet)
    database = None
    try:
        database = TranslationDatabase(db_path=str(db_path) if db_path else None)
        results = database.find_collisions(language_code=language)

        if json_output:
            click.echo(json.dumps(results, ensure_ascii=False, indent=2))
            if results:
                sys.exit(1)  # Non-zero exit for CI integration
            return

        if not results:
            out.print("✅ [green]No translation collisions found.[/green]")
            return

        # Count unique languages
        languages = {c["language_code"] for c in results}
        total_terms = sum(len(c["terms"]) for c in results)

        out.print(
            f"[yellow]Translation Collisions[/yellow] "
            f"({len(results)} groups across {len(languages)} languages)\n"
        )

        for collision in results:
            lang = collision["language_code"]
            trans = collision["translation"]
            terms = collision["terms"]
            term_names = ", ".join(t["term_name"] for t in terms)
            categories = ", ".join(t["category"] for t in terms)
            out.print(f'  [{lang}] "{trans}" -> {term_names} ({categories})')

        out.print(
            f"\n[dim]Total: {len(results)} collision groups, "
            f"{total_terms} affected terms[/dim]"
        )
        sys.exit(1)  # Non-zero exit for CI integration

    except FileNotFoundError:
        out.print(f"❌ [red]Error:[/red] Database not found at {db_path}")
        out.print("\n[dim]Run 'legesher-i18n db init' to create the database.[/dim]")
        sys.exit(1)
    except Exception as e:
        out.print(f"❌ [red]Error detecting collisions:[/red] {e}")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)
    finally:
        if database is not None:
            database.close()


# Add db group to main CLI
cli.add_command(db)


# =============================================================================
# Export Commands - Export language pack keywords to various formats
# =============================================================================


def _get_available_languages(target: str = "python") -> list[str]:
    """Get list of available language codes for a target.

    Uses LanguagePackLoader to discover available packs.
    """
    loader = _get_loader()
    available = loader.list_available_languages(target)
    return sorted([code for code, name in available])


def _load_pack_data(language: str, target: str, version: str) -> dict:
    """Load pack data with inheritance resolution using LanguagePackLoader.

    Delegates to LanguagePackLoader which handles:
    - Inheritance chain resolution
    - Circular inheritance detection
    - Maximum depth checks
    - Path traversal protection
    """
    loader = _get_loader()
    pack = loader.load(language=language, target=target, version=version)

    return {
        "language": pack.language,
        "target": pack.target,
        "version": pack.version,
        "keywords": dict(pack.keywords),
        "builtins": dict(pack.builtins),
        "exceptions": dict(pack.exceptions),
    }


def _load_language_pack(
    language: str, target: str = "python", version: str = "3.13"
) -> LanguagePack:
    """Load a language pack with inheritance resolution using LanguagePackLoader."""
    loader = _get_loader()
    return loader.load(language=language, target=target, version=version)


def _generate_export_data(pack: LanguagePack) -> dict:
    """Generate export data dictionary from a language pack."""
    language_name = _get_language_name(pack.language)

    return {
        "language": pack.language,
        "language_name": language_name,
        "target": pack.target,
        "version": pack.version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "keywords": dict(sorted(pack.keywords.items())),
        "builtins": dict(sorted(pack.builtins.items())),
        "exceptions": dict(sorted(pack.exceptions.items())) if pack.exceptions else {},
        "stats": {
            "total_keywords": len(pack.keywords),
            "total_builtins": len(pack.builtins),
            "total_exceptions": len(pack.exceptions) if pack.exceptions else 0,
        },
        "inheritance_chain": pack.inheritance_chain if pack.inheritance_chain else [],
    }


def _export_json(data: dict, output: Path | TextIO) -> None:
    """Export data to JSON format.

    Args:
        data: Export data dictionary
        output: Path to file or file-like object (e.g., sys.stdout)
    """
    if isinstance(output, Path):
        with open(output, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    else:
        json.dump(data, output, indent=2, ensure_ascii=False)
        output.write("\n")


def _export_csv(data: dict, output: Path | TextIO) -> None:
    """Export data to CSV format.

    Args:
        data: Export data dictionary
        output: Path to file or file-like object (e.g., sys.stdout)
    """
    if isinstance(output, Path):
        f = open(output, "w", newline="", encoding="utf-8")
        should_close = True
    else:
        f = output
        should_close = False

    try:
        writer = csv.writer(f)

        # Header
        writer.writerow(
            ["category", "english", data["language_name"].lower(), "example"]
        )

        # Keywords
        for eng, trans in data["keywords"].items():
            example = (
                f"{trans} func():"
                if eng == "def"
                else f"{trans} x"
                if eng == "return"
                else ""
            )
            writer.writerow(["keyword", eng, trans, example])

        # Builtins
        for eng, trans in data["builtins"].items():
            example = (
                f'{trans}("value")'
                if eng == "print"
                else f"{trans}(x)"
                if eng == "len"
                else ""
            )
            writer.writerow(["builtin", eng, trans, example])

        # Exceptions
        for eng, trans in data.get("exceptions", {}).items():
            writer.writerow(["exception", eng, trans, ""])
    finally:
        if should_close:
            f.close()


# Note: Markdown export removed - use scripts/generate_reference_docs.py instead
# for comprehensive REFERENCE.md files with localized examples.


# =============================================================================
# Export Commands - JSON and CSV formats
# =============================================================================


@click.group()
def export():
    """Export language pack keywords to various formats.

    Export keywords, builtins, and exceptions from language packs
    to JSON or CSV formats for documentation and validation.

    Note: For comprehensive Markdown reference documentation,
    use the generate_reference_docs.py script instead.
    """
    pass


@export.command(name="json")
@click.option("--lang", required=True, help="Language code (e.g., es, ar, zh)")
@click.option("--target", default="python", help="Target language (default: python)")
@click.option("--version", default="3.13", help="Python version (default: 3.13)")
@click.option("--output", "-o", type=str, help="Output file path (use '-' for stdout)")
@click.option(
    "--dry-run", is_flag=True, help="Preview what would be generated without writing"
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress output (for CI/scripts)")
def export_json(
    lang: str, target: str, version: str, output: str | None, dry_run: bool, quiet: bool
):
    """Export language pack to JSON format.

    Use --output - to write to stdout for piping to other commands.

    Examples:

        legesher-i18n export json --lang es

        legesher-i18n export json --lang ar --output arabic_keywords.json

        legesher-i18n export json --lang es --output - | jq '.keywords'
    """
    out = get_console(quiet)
    try:
        out.print(f"[cyan]Loading language pack:[/cyan] {lang} ({target} {version})")
        pack = _load_language_pack(lang, target, version)

        data = _generate_export_data(pack)

        if dry_run:
            out.print("\n[cyan]Dry run - would export:[/cyan]")
            out.print(f"   Language: {data['language_name']} ({data['language']})")
            out.print(f"   Keywords: {data['stats']['total_keywords']}")
            out.print(f"   Builtins: {data['stats']['total_builtins']}")
            out.print(f"   Exceptions: {data['stats']['total_exceptions']}")
            if output == "-":
                out.print("   Output: stdout")
            else:
                out.print(f"   Output: {output or f'{lang}_keywords.json'}")
            return

        # Handle output destination
        if output == "-":
            _export_json(data, sys.stdout)
        else:
            output_path = Path(output) if output else Path(f"{lang}_keywords.json")
            _export_json(data, output_path)

            out.print(f"✅ [green]Exported to:[/green] {output_path}")
            out.print(f"   Keywords: {data['stats']['total_keywords']}")
            out.print(f"   Builtins: {data['stats']['total_builtins']}")
            out.print(f"   Exceptions: {data['stats']['total_exceptions']}")

    except FileNotFoundError as e:
        out.print(f"❌ [red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        out.print(f"❌ [red]Error:[/red] {e}")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


@export.command(name="csv")
@click.option("--lang", required=True, help="Language code (e.g., es, ar, zh)")
@click.option("--target", default="python", help="Target language (default: python)")
@click.option("--version", default="3.13", help="Python version (default: 3.13)")
@click.option("--output", "-o", type=str, help="Output file path (use '-' for stdout)")
@click.option(
    "--dry-run", is_flag=True, help="Preview what would be generated without writing"
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress output (for CI/scripts)")
def export_csv(
    lang: str, target: str, version: str, output: str | None, dry_run: bool, quiet: bool
):
    """Export language pack to CSV format.

    Use --output - to write to stdout for piping to other commands.

    Examples:

        legesher-i18n export csv --lang es

        legesher-i18n export csv --lang zh --output chinese_keywords.csv

        legesher-i18n export csv --lang es --output - > keywords.csv
    """
    out = get_console(quiet)
    try:
        out.print(f"[cyan]Loading language pack:[/cyan] {lang} ({target} {version})")
        pack = _load_language_pack(lang, target, version)

        data = _generate_export_data(pack)
        total_rows = (
            data["stats"]["total_keywords"]
            + data["stats"]["total_builtins"]
            + data["stats"]["total_exceptions"]
        )

        if dry_run:
            out.print("\n[cyan]Dry run - would export:[/cyan]")
            out.print(f"   Language: {data['language_name']} ({data['language']})")
            out.print(f"   Total rows: {total_rows}")
            if output == "-":
                out.print("   Output: stdout")
            else:
                out.print(f"   Output: {output or f'{lang}_keywords.csv'}")
            return

        # Handle output destination
        if output == "-":
            _export_csv(data, sys.stdout)
        else:
            output_path = Path(output) if output else Path(f"{lang}_keywords.csv")
            _export_csv(data, output_path)

            out.print(f"✅ [green]Exported to:[/green] {output_path}")
            out.print(f"   Total rows: {total_rows}")

    except FileNotFoundError as e:
        out.print(f"❌ [red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        out.print(f"❌ [red]Error:[/red] {e}")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


@export.command(name="all")
@click.option("--target", default="python", help="Target language (default: python)")
@click.option("--version", default="3.13", help="Python version (default: 3.13)")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["json", "csv"]),
    default="json",
    help="Export format (json or csv)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("."),
    help="Output directory",
)
@click.option(
    "--dry-run", is_flag=True, help="Preview what would be generated without writing"
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress output (for CI/scripts)")
def export_all(
    target: str, version: str, fmt: str, output_dir: Path, dry_run: bool, quiet: bool
):
    """Export all available language packs.

    Generates export files for all languages found in the pack directory.
    Shows a progress bar when processing multiple packs.

    Note: For Markdown reference documentation, use:
        python scripts/generate_reference_docs.py

    Examples:

        legesher-i18n export all --format json --output-dir ./data/

        legesher-i18n export all --format csv --output-dir ./exports/

        legesher-i18n export all --dry-run  # Preview without writing
    """
    out = get_console(quiet)
    try:
        # Get available languages using new structure
        languages = _get_available_languages(target)

        if not languages:
            out.print("❌ [red]Error:[/red] No language packs found")
            sys.exit(1)

        export_funcs = {
            "json": _export_json,
            "csv": _export_csv,
        }

        extensions = {
            "json": ".json",
            "csv": ".csv",
        }

        if dry_run:
            out.print(
                f"[cyan]Dry run - would export {len(languages)} language packs:[/cyan]\n"
            )
            for lang in sorted(languages):
                language_name = _get_language_name(lang)
                output_file = output_dir / f"{lang}{extensions[fmt]}"
                out.print(f"   {language_name} ({lang}) → {output_file}")
            out.print(f"\n[dim]Format: {fmt}, Output directory: {output_dir}[/dim]")
            return

        output_dir.mkdir(parents=True, exist_ok=True)

        out.print(
            f"[cyan]Exporting {len(languages)} language packs to {fmt} format...[/cyan]\n"
        )

        success_count = 0
        failed_langs = []

        # Use progress bar for visual feedback
        if not quiet:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Exporting...", total=len(languages))

                for lang in sorted(languages):
                    language_name = _get_language_name(lang)
                    progress.update(task, description=f"Exporting {language_name}...")

                    try:
                        pack = _load_language_pack(lang, target, version)
                        data = _generate_export_data(pack)

                        output_file = output_dir / f"{lang}{extensions[fmt]}"
                        export_funcs[fmt](data, output_file)
                        success_count += 1

                    except Exception as e:
                        failed_langs.append((lang, str(e)))

                    progress.advance(task)
        else:
            # Quiet mode - no progress bar
            for lang in sorted(languages):
                try:
                    pack = _load_language_pack(lang, target, version)
                    data = _generate_export_data(pack)

                    output_file = output_dir / f"{lang}{extensions[fmt]}"
                    export_funcs[fmt](data, output_file)
                    success_count += 1

                except Exception as e:
                    failed_langs.append((lang, str(e)))

        # Report results
        out.print()
        for lang in sorted(languages):
            if not any(failed_lang == lang for failed_lang, _ in failed_langs):
                language_name = _get_language_name(lang)
                output_file = output_dir / f"{lang}{extensions[fmt]}"
                out.print(f"   ✅ {language_name} ({lang}) → {output_file.name}")

        for lang, error in failed_langs:
            out.print(f"   ⚠️  [yellow]{lang}:[/yellow] {error}")

        out.print(
            f"\n✅ [green]Exported {success_count}/{len(languages)} language packs to {output_dir}[/green]"
        )

    except Exception as e:
        out.print(f"❌ [red]Error:[/red] {e}")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


# Add export group to main CLI
cli.add_command(export)


# =============================================================================
# Registry Commands - Validate and list language packs
# =============================================================================


@click.group()
def registry():
    """Language pack registry management.

    List available language packs and validate translations
    for completeness and correctness.
    """
    pass


@registry.command(name="list")
@click.option("--target", default="python", help="Target language (default: python)")
@click.option("--version", default="3.13", help="Python version (default: 3.13)")
@click.option("--quiet", "-q", is_flag=True, help="Suppress output (for CI/scripts)")
def registry_list(target: str, version: str, quiet: bool):
    """List all available language packs.

    Shows available languages with their translation counts and status.

    Examples:

        legesher-i18n registry list

        legesher-i18n registry list --version 3.14
    """
    out = get_console(quiet)
    try:
        # Get available languages using new structure
        languages = _get_available_languages(target)

        if not languages:
            out.print(f"❌ [red]Error:[/red] No language packs found for '{target}'")
            sys.exit(1)

        # Create table
        table = Table(title=f"Available Language Packs ({target} {version})")
        table.add_column("Code", style="cyan", no_wrap=True)
        table.add_column("Language", style="bold")
        table.add_column("Keywords", justify="right", style="green")
        table.add_column("Builtins", justify="right", style="green")
        table.add_column("Status", justify="center")

        for lang in languages:
            try:
                pack_data = _load_pack_data(lang, target, version)

                keywords = len(pack_data.get("keywords", {}))
                builtins = len(pack_data.get("builtins", {}))
                language_name = _get_language_name(lang)

                # Status based on translation completeness
                if keywords > 30 and builtins > 50:
                    status = "[green]✓ complete[/green]"
                else:
                    status = "[yellow]partial[/yellow]"

                table.add_row(lang, language_name, str(keywords), str(builtins), status)

            except Exception:
                table.add_row(
                    lang,
                    _get_language_name(lang),
                    "?",
                    "?",
                    "[red]error[/red]",
                )

        out.print()
        out.print(table)
        out.print(f"\n[dim]Found {len(languages)} language pack(s)[/dim]")

    except Exception as e:
        out.print(f"❌ [red]Error:[/red] {e}")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


@registry.command(name="validate")
@click.option("--lang", help="Language code to validate (or 'all')")
@click.option("--target", default="python", help="Target language (default: python)")
@click.option("--version", default="3.13", help="Python version (default: 3.13)")
@click.option("--strict", is_flag=True, help="Fail on warnings")
@click.option("--quiet", "-q", is_flag=True, help="Suppress output (for CI/scripts)")
def registry_validate(lang: str, target: str, version: str, strict: bool, quiet: bool):
    """Validate language pack translations.

    Checks for completeness against the English reference pack
    and validates translation quality.

    Examples:

        legesher-i18n registry validate --lang es

        legesher-i18n registry validate --lang all --strict
    """
    out = get_console(quiet)
    try:
        # Get available languages
        all_languages = _get_available_languages(target)

        if not all_languages:
            out.print(f"❌ [red]Error:[/red] No language packs found for '{target}'")
            sys.exit(1)

        # Load English reference pack
        try:
            en_data = _load_pack_data("en", target, version)
        except Exception as e:
            out.print(f"❌ [red]Error:[/red] English reference pack not found: {e}")
            sys.exit(1)

        en_keywords = set(en_data.get("keywords", {}).keys())
        en_builtins = set(en_data.get("builtins", {}).keys())

        # Determine which languages to validate
        if lang == "all" or lang is None:
            languages_to_validate = [code for code in all_languages if code != "en"]
        else:
            if lang not in all_languages:
                out.print(f"❌ [red]Error:[/red] Language pack not found: {lang}")
                sys.exit(1)
            languages_to_validate = [lang]

        out.print(
            f"[cyan]Validating {len(languages_to_validate)} language pack(s)...[/cyan]\n"
        )

        all_passed = True

        for lang_code in sorted(languages_to_validate):
            language_name = _get_language_name(lang_code)

            out.print(f"[bold]{language_name} ({lang_code}):[/bold]")

            try:
                pack_data = _load_pack_data(lang_code, target, version)

                pack_keywords = set(pack_data.get("keywords", {}).keys())
                pack_builtins = set(pack_data.get("builtins", {}).keys())

                # Check for missing keywords
                missing_keywords = en_keywords - pack_keywords
                missing_builtins = en_builtins - pack_builtins

                # Check for extra keywords (might be errors)
                extra_keywords = pack_keywords - en_keywords

                # Check for empty translations
                empty_keywords = [
                    k for k, v in pack_data.get("keywords", {}).items() if not v
                ]
                empty_builtins = [
                    k for k, v in pack_data.get("builtins", {}).items() if not v
                ]

                # Check for duplicate translations (same translation for different terms)
                # Using Counter for O(n) complexity instead of O(n²) list.count()
                keyword_counts = Counter(
                    v for v in pack_data.get("keywords", {}).values() if v
                )
                builtin_counts = Counter(
                    v for v in pack_data.get("builtins", {}).values() if v
                )

                duplicate_keywords = [
                    v for v, count in keyword_counts.items() if count > 1
                ]
                duplicate_builtins = [
                    v for v, count in builtin_counts.items() if count > 1
                ]

                errors = []
                warnings = []

                if missing_keywords:
                    errors.append(
                        f"Missing {len(missing_keywords)} keywords: {', '.join(sorted(missing_keywords)[:5])}..."
                    )
                if missing_builtins:
                    warnings.append(
                        f"Missing {len(missing_builtins)} builtins: {', '.join(sorted(missing_builtins)[:5])}..."
                    )
                if empty_keywords:
                    errors.append(
                        f"Empty translations for keywords: {', '.join(empty_keywords[:5])}"
                    )
                if empty_builtins:
                    warnings.append(
                        f"Empty translations for builtins: {', '.join(empty_builtins[:5])}"
                    )
                if extra_keywords:
                    warnings.append(
                        f"Extra keywords not in reference: {', '.join(extra_keywords)}"
                    )
                if duplicate_keywords:
                    warnings.append(
                        f"Duplicate keyword translations detected: {', '.join(list(set(duplicate_keywords))[:3])}"
                    )
                if duplicate_builtins:
                    warnings.append(
                        f"Duplicate builtin translations detected (first 3): {', '.join(list(set(duplicate_builtins))[:3])}"
                    )

                # Report results
                if errors:
                    for error in errors:
                        out.print(f"   ❌ [red]{error}[/red]")
                    all_passed = False

                if warnings:
                    for warning in warnings:
                        out.print(f"   ⚠️  [yellow]{warning}[/yellow]")
                    if strict:
                        all_passed = False

                if not errors and not warnings:
                    out.print("   ✅ [green]All checks passed[/green]")
                elif not errors:
                    out.print(
                        f"   ✅ [green]Validation passed[/green] ({len(warnings)} warning{'s' if len(warnings) != 1 else ''})"
                    )

                out.print()

            except Exception as e:
                out.print(f"   ❌ [red]Error loading pack: {e}[/red]")
                all_passed = False
                out.print()

        if all_passed:
            out.print("✅ [bold green]All validations passed![/bold green]")
            sys.exit(0)
        else:
            if strict:
                out.print("❌ [bold red]Validation failed (strict mode)[/bold red]")
            else:
                out.print(
                    "⚠️  [bold yellow]Validation completed with issues[/bold yellow]"
                )
            sys.exit(1 if strict else 0)

    except Exception as e:
        out.print(f"❌ [red]Error:[/red] {e}")
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


# Add registry group to main CLI
cli.add_command(registry)


if __name__ == "__main__":
    cli()
