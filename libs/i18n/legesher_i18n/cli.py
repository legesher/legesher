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


if __name__ == "__main__":
    cli()
