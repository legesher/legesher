"""Metadata management commands for Legesher.

This module provides CLI commands for viewing and managing translation metadata
stored in .legesher/metadata/ directory. Each source file has a corresponding
YAML metadata file that tracks translation history, git operations, and file
configuration.

Commands:
    legesher metadata show: Display metadata for a specific file
    legesher metadata history: Show translation history for a file
    legesher metadata list: List all files with metadata
    legesher metadata validate: Validate metadata file integrity
    legesher metadata raw: Display raw YAML metadata
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from legesher_core.metadata import MetadataManager

# Configure logger
logger = logging.getLogger(__name__)

# Rich console for beautiful output
console = Console()


@click.group(name="metadata")
def metadata():
    """Manage translation metadata for Legesher files.

    View and manage metadata that tracks translation history, git operations,
    and file configuration for multilingual code.

    \b
    Examples:
        # Show metadata for a file
        $ legesher metadata show src/calculator.py

        # Show translation history
        $ legesher metadata history src/calculator.py --limit 5

        # List all tracked files
        $ legesher metadata list

        # Validate metadata integrity
        $ legesher metadata validate src/calculator.py

        # View raw YAML metadata
        $ legesher metadata raw src/calculator.py
    """
    pass


@metadata.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--repo",
    type=click.Path(),
    default=".",
    help="Repository root (default: current directory)",
)
def show(file_path: str, repo: str):
    """Show metadata for a specific file.

    Displays comprehensive metadata including original language, translations,
    and recent history entries in a formatted table.

    \b
    Example:
        $ legesher metadata show src/calculator.py
        $ legesher metadata show src/main.py --repo /path/to/repo
    """
    try:
        # Initialize manager
        repo_path = Path(repo).resolve()
        manager = MetadataManager(repo_path)
        file = Path(file_path).resolve()

        # Load metadata
        metadata_data = manager.get_metadata(file)
        if metadata_data is None:
            console.print(
                f"[red]✗[/red] No metadata found for: {file_path}", style="bold"
            )
            console.print(
                "\n[yellow]Hint:[/yellow] Run 'legesher git-setup' to initialize metadata"
            )
            sys.exit(1)

        # Display file header
        console.print(f"\n[bold cyan]File:[/bold cyan] {metadata_data['file']}")
        console.print("━" * 60)

        # Display basic info
        console.print(
            f"[bold]Original Language:[/bold]    {metadata_data['original_language']}"
        )
        console.print(
            f"[bold]Canonical Language:[/bold]   {metadata_data['canonical_language']}"
        )
        console.print(
            f"[bold]Python Version:[/bold]       {metadata_data['python_version']}"
        )

        # Format timestamps
        created = _format_timestamp(metadata_data["created_at"])
        updated = _format_timestamp(metadata_data["updated_at"])
        console.print(f"[bold]Created:[/bold]              {created}")
        console.print(f"[bold]Last Updated:[/bold]         {updated}")

        # Display translations table
        if metadata_data["translations"]:
            console.print("\n[bold cyan]Translations[/bold cyan]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Language", style="cyan")
            table.add_column("Method", style="green")
            table.add_column("Timestamp", style="yellow")
            table.add_column("Version", style="blue")
            table.add_column("Commit", style="dim")

            for trans in metadata_data["translations"]:
                table.add_row(
                    trans["language"],
                    trans["method"],
                    _format_timestamp(trans["timestamp"]),
                    trans["translator_version"],
                    trans.get("commit_sha", "N/A")[:7]
                    if trans.get("commit_sha")
                    else "N/A",
                )

            console.print(table)
        else:
            console.print("\n[dim]No translations recorded yet[/dim]")

        # Display recent history (last 5 entries)
        if metadata_data["history"]:
            console.print("\n[bold cyan]Recent History[/bold cyan] (last 5 entries)")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Timestamp", style="yellow")
            table.add_column("Action", style="green")
            table.add_column("From", style="cyan")
            table.add_column("To", style="cyan")
            table.add_column("Commit", style="dim")

            # Show last 5 entries
            for entry in metadata_data["history"][-5:]:
                action_color = "green" if entry["action"] == "smudge" else "yellow"
                table.add_row(
                    _format_timestamp(entry["timestamp"]),
                    f"[{action_color}]{entry['action']}[/{action_color}]",
                    entry["from_language"],
                    entry["to_language"],
                    entry.get("commit_sha", "N/A")[:7]
                    if entry.get("commit_sha")
                    else "N/A",
                )

            console.print(table)
        else:
            console.print("\n[dim]No history entries yet[/dim]")

        console.print()  # Extra newline for spacing

    except Exception as e:
        logger.error(f"Error showing metadata: {e}", exc_info=True)
        console.print(f"[red]✗[/red] Error: {e}", style="bold")
        sys.exit(1)


@metadata.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--repo",
    type=click.Path(),
    default=".",
    help="Repository root (default: current directory)",
)
@click.option(
    "--limit",
    type=int,
    default=10,
    help="Limit number of history entries (default: 10)",
)
def history(file_path: str, repo: str, limit: int):
    """Show translation history for a file.

    Displays git filter operations (clean/smudge) in chronological order,
    showing how the file has been translated over time.

    \b
    Example:
        $ legesher metadata history src/calculator.py
        $ legesher metadata history src/main.py --limit 20
    """
    try:
        # Initialize manager
        repo_path = Path(repo).resolve()
        manager = MetadataManager(repo_path)
        file = Path(file_path).resolve()

        # Load metadata
        metadata_data = manager.get_metadata(file)
        if metadata_data is None:
            console.print(
                f"[red]✗[/red] No metadata found for: {file_path}", style="bold"
            )
            console.print(
                "\n[yellow]Hint:[/yellow] Run 'legesher git-setup' to initialize metadata"
            )
            sys.exit(1)

        # Display header
        console.print(
            f"\n[bold cyan]Translation History:[/bold cyan] {metadata_data['file']}"
        )
        console.print("━" * 60)

        if not metadata_data["history"]:
            console.print("\n[dim]No history entries yet[/dim]\n")
            sys.exit(0)

        # Display history table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Timestamp", style="yellow")
        table.add_column("Action", style="green")
        table.add_column("Translation", style="cyan")
        table.add_column("Commit", style="dim")

        # Show most recent entries first, up to limit
        history_entries = metadata_data["history"][-limit:]
        total_entries = len(metadata_data["history"])

        for entry in reversed(history_entries):
            action_color = "green" if entry["action"] == "smudge" else "yellow"
            translation = f"{entry['from_language']} → {entry['to_language']}"
            commit = (
                entry.get("commit_sha", "N/A")[:7] if entry.get("commit_sha") else "N/A"
            )

            table.add_row(
                _format_timestamp(entry["timestamp"]),
                f"[{action_color}]{entry['action']}[/{action_color}]",
                translation,
                commit,
            )

        console.print(table)

        # Show summary
        if total_entries > limit:
            console.print(
                f"\n[dim]Showing {limit} of {total_entries} total entries[/dim]"
            )
        else:
            console.print(f"\n[dim]Total entries: {total_entries}[/dim]")

        console.print()  # Extra newline for spacing

    except Exception as e:
        logger.error(f"Error showing history: {e}", exc_info=True)
        console.print(f"[red]✗[/red] Error: {e}", style="bold")
        sys.exit(1)


@metadata.command(name="list")
@click.option(
    "--repo",
    type=click.Path(),
    default=".",
    help="Repository root (default: current directory)",
)
def list_files(repo: str):
    """List all files with metadata.

    Displays all files tracked by Legesher metadata system, showing their
    original language and number of translations.

    \b
    Example:
        $ legesher metadata list
        $ legesher metadata list --repo /path/to/repo
    """
    try:
        # Initialize manager
        repo_path = Path(repo).resolve()
        manager = MetadataManager(repo_path)

        # Get all metadata files
        metadata_files = manager.list_metadata_files()

        if not metadata_files:
            console.print("\n[dim]No metadata files found[/dim]")
            console.print(
                "\n[yellow]Hint:[/yellow] Run 'legesher git-setup' to initialize metadata\n"
            )
            sys.exit(0)

        # Display header
        console.print(f"\n[bold cyan]Tracked Files:[/bold cyan] {len(metadata_files)}")
        console.print("━" * 60)

        # Create table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("File", style="cyan")
        table.add_column("Original Lang", style="green")
        table.add_column("Python Ver", style="yellow")
        table.add_column("Translations", style="blue", justify="right")
        table.add_column("History", style="dim", justify="right")

        # Load each metadata file and add to table
        for metadata_file in sorted(metadata_files):
            # Get the source file path from metadata file
            relative_metadata = metadata_file.relative_to(manager.metadata_dir)
            # Remove .yml extension to get source file path
            source_file = str(relative_metadata)[:-4]

            metadata_data = manager.get_metadata(Path(source_file))
            if metadata_data:
                table.add_row(
                    metadata_data["file"],
                    metadata_data["original_language"],
                    metadata_data["python_version"],
                    str(len(metadata_data["translations"])),
                    str(len(metadata_data["history"])),
                )

        console.print(table)
        console.print()  # Extra newline for spacing

    except Exception as e:
        logger.error(f"Error listing metadata files: {e}", exc_info=True)
        console.print(f"[red]✗[/red] Error: {e}", style="bold")
        sys.exit(1)


@metadata.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--repo",
    type=click.Path(),
    default=".",
    help="Repository root (default: current directory)",
)
def validate(file_path: str, repo: str):
    """Validate metadata for a file.

    Checks that the metadata file exists, is valid YAML, and contains all
    required fields.

    \b
    Example:
        $ legesher metadata validate src/calculator.py
    """
    try:
        # Initialize manager
        repo_path = Path(repo).resolve()
        manager = MetadataManager(repo_path)
        file = Path(file_path).resolve()

        console.print(f"\n[bold cyan]Validating metadata:[/bold cyan] {file_path}")
        console.print("━" * 60)

        # Validate metadata
        is_valid = manager.validate_metadata(file)

        if is_valid:
            console.print("\n[green]✓[/green] [bold]Metadata is valid[/bold]")

            # Load and show basic info
            metadata_data = manager.get_metadata(file)
            if metadata_data:
                console.print("\n[bold]Metadata Summary:[/bold]")
                console.print(f"  File: {metadata_data['file']}")
                console.print(
                    f"  Original Language: {metadata_data['original_language']}"
                )
                console.print(f"  Python Version: {metadata_data['python_version']}")
                console.print(f"  Translations: {len(metadata_data['translations'])}")
                console.print(f"  History Entries: {len(metadata_data['history'])}")
        else:
            console.print("\n[red]✗[/red] [bold]Metadata is invalid or missing[/bold]")
            console.print(
                "\n[yellow]Hint:[/yellow] Run 'legesher git-setup' to initialize metadata"
            )
            sys.exit(1)

        console.print()  # Extra newline for spacing

    except Exception as e:
        logger.error(f"Error validating metadata: {e}", exc_info=True)
        console.print(f"[red]✗[/red] Error: {e}", style="bold")
        sys.exit(1)


@metadata.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--repo",
    type=click.Path(),
    default=".",
    help="Repository root (default: current directory)",
)
def raw(file_path: str, repo: str):
    """Display raw YAML metadata for a file.

    Shows the complete YAML metadata file with syntax highlighting.
    Useful for debugging and understanding the metadata structure.

    \b
    Example:
        $ legesher metadata raw src/calculator.py
    """
    try:
        # Initialize manager
        repo_path = Path(repo).resolve()
        manager = MetadataManager(repo_path)
        file = Path(file_path).resolve()

        # Get metadata path
        metadata_path = manager._get_metadata_path(file)

        if not metadata_path.exists():
            console.print(
                f"\n[red]✗[/red] Metadata file not found: {metadata_path}", style="bold"
            )
            console.print(
                "\n[yellow]Hint:[/yellow] Run 'legesher git-setup' to initialize metadata"
            )
            sys.exit(1)

        # Read raw YAML
        with open(metadata_path, "r", encoding="utf-8") as f:
            yaml_content = f.read()

        # Display header
        console.print(f"\n[bold cyan]Raw Metadata:[/bold cyan] {file_path}")
        console.print(f"[dim]Location: {metadata_path}[/dim]")
        console.print("━" * 60)
        console.print()

        # Display with syntax highlighting
        syntax = Syntax(yaml_content, "yaml", theme="monokai", line_numbers=True)
        console.print(syntax)
        console.print()  # Extra newline for spacing

    except Exception as e:
        logger.error(f"Error displaying raw metadata: {e}", exc_info=True)
        console.print(f"[red]✗[/red] Error: {e}", style="bold")
        sys.exit(1)


def _format_timestamp(timestamp: str) -> str:
    """Format ISO 8601 timestamp to human-readable format.

    Args:
        timestamp: ISO 8601 timestamp string (e.g., "2025-11-06T10:30:00Z")

    Returns:
        Formatted timestamp (e.g., "2025-11-06 10:30:00 UTC")
    """
    try:
        # Parse ISO 8601 timestamp
        if timestamp.endswith("Z"):
            dt = datetime.fromisoformat(timestamp[:-1])
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        else:
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        # If parsing fails, return original
        return timestamp


# Export commands for registration in main CLI
__all__ = ["metadata", "show", "history", "list_files", "validate", "raw"]
