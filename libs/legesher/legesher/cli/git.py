"""Git integration commands for Legesher.

This module provides CLI commands for setting up and managing git filters
that enable transparent translation between local language (working directory)
and canonical English (git storage).

Commands:
    legesher git-setup: Configure git filters for a repository
    legesher git-status: Show current git filter configuration
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click

from legesher.config import LegesherConfig
from legesher_core.transformer import TokenTranslator

# Configure logger
logger = logging.getLogger(__name__)


@click.group(name="git")
def git():
    """Git integration commands.

    Configure git filters to enable transparent translation between
    your local language and canonical English in the repository.

    \b
    Examples:
        # Set up git filters for Spanish
        $ legesher git-setup --language es

        # Check git filter status
        $ legesher git-status
    """
    pass


@git.command(name="setup")
@click.option(
    "--language",
    "-l",
    prompt="Default language",
    help="Natural language code (e.g., 'es', 'ar')",
)
@click.option(
    "--python-version",
    help="Python version (default: auto-detect)",
)
@click.option(
    "--global",
    "use_global",
    is_flag=True,
    help="Configure git filters globally instead of per-repository",
)
@click.option(
    "--track-metadata/--no-track-metadata",
    default=True,
    help="Track metadata files in git (default: yes)",
)
def git_setup(
    language: str,
    python_version: Optional[str],
    use_global: bool,
    track_metadata: bool,
):
    """Set up git filters and metadata tracking for multilingual code.

    This command configures git clean/smudge filters that automatically
    translate code between your local language and canonical English:

    \b
    - Clean filter (git add): Your language → English (stored in git)
    - Smudge filter (git checkout): English → Your language (working directory)

    The setup process:
    1. Validates language pack availability
    2. Creates .legesher/config.yml configuration
    3. Configures git filter settings
    4. Creates .gitattributes entry for *.py files
    5. Initializes metadata directory (.legesher/metadata/)
    6. Optionally adds metadata to .gitignore
    7. Verifies setup is working

    \b
    Examples:
        $ legesher git-setup --language es
        $ legesher git-setup --language ar --python-version 3.13
        $ legesher git-setup --language es --global
        $ legesher git-setup --language es --no-track-metadata
    """
    try:
        # Step 1: Validate we're in a git repository (unless --global)
        if not use_global:
            try:
                repo_root = LegesherConfig._find_repo_root()
                click.echo(f"✓ Found git repository at: {repo_root}")
            except ValueError as e:
                click.echo(f"✗ Error: {e}", err=True)
                click.echo(
                    "\nHint: Run this command from within a git repository.", err=True
                )
                sys.exit(1)
        else:
            repo_root = None

        # Step 2: Validate language pack is available
        click.echo(f"\nValidating language pack '{language}'...")
        try:
            available_languages = TokenTranslator.list_available_languages()
            lang_codes = [code for code, name in available_languages]

            if language not in lang_codes:
                click.echo(f"✗ Language '{language}' not found.", err=True)
                click.echo("\nAvailable languages:", err=True)
                for code, name in available_languages:
                    click.echo(f"  - {code}: {name}", err=True)
                sys.exit(1)

            # Try loading the language pack to validate
            translator = TokenTranslator.from_language_pack(
                language=language,
                python_version=python_version,
            )
            pack_info = translator.get_pack_info()
            click.echo(
                f"✓ Loaded language pack: {language} "
                f"({pack_info['keyword_count']} keywords, "
                f"{pack_info['builtin_count']} builtins)"
            )

        except Exception as e:
            click.echo(f"✗ Error loading language pack: {e}", err=True)
            sys.exit(1)

        # Step 3: Create configuration
        click.echo("\nCreating configuration...")
        config = LegesherConfig(
            language=language,
            python_version=python_version,
            git_canonical_language="en",
            git_filter_enabled=True,
        )

        if use_global:
            config_path = config.save_user_config()
            click.echo(f"✓ Saved global config to: {config_path}")
        else:
            config_path = config.save_project_config(repo_root)
            click.echo(f"✓ Saved project config to: {config_path}")

        # Step 4: Configure git filters
        click.echo("\nConfiguring git filters...")
        success = _configure_git_filters(use_global=use_global)
        if not success:
            click.echo("✗ Failed to configure git filters", err=True)
            sys.exit(1)

        # Step 5: Create .gitattributes (only for project, not global)
        if not use_global:
            click.echo("\nConfiguring .gitattributes...")
            _create_gitattributes(repo_root)
            click.echo("✓ Updated .gitattributes")

        # Step 6: Initialize metadata directory (only for project, not global)
        if not use_global:
            click.echo("\nInitializing metadata system...")
            _initialize_metadata(repo_root, track_metadata)

        # Step 7: Verify setup
        click.echo("\nVerifying setup...")
        if _verify_git_setup(use_global=use_global):
            click.echo("✓ Git filter setup verified")
        else:
            click.echo("⚠ Warning: Could not fully verify setup", err=True)

        # Success message
        click.echo("\n" + "=" * 60)
        click.echo("✓ Git filter setup complete!")
        click.echo("=" * 60)

        if not use_global:
            click.echo("\nYour repository is now configured for multilingual code.")
            click.echo(f"Language: {language}")
            click.echo("Storage: English (canonical)")
            click.echo("\nNext steps:")
            click.echo(f"1. Write code in {language}")
            click.echo("2. Run 'git add' - code will be translated to English")
            click.echo("3. Run 'git commit' - English code stored in repository")
            click.echo(f"4. Run 'git checkout' - code translated back to {language}")
        else:
            click.echo("\nGit filters configured globally for all repositories.")
            click.echo(f"Language: {language}")
            click.echo("\nNote: You still need to run 'legesher git-setup' in each")
            click.echo("repository to create .gitattributes and .legesher/config.yml")

    except Exception as e:
        logger.error(f"Unexpected error during git setup: {e}", exc_info=True)
        click.echo(f"\n✗ Unexpected error: {e}", err=True)
        sys.exit(1)


@git.command(name="status")
def git_status():
    """Show git filter configuration status.

    Displays current git filter configuration, including:
    - Whether filters are configured
    - Language settings
    - Filter commands
    - .gitattributes status

    \b
    Example:
        $ legesher git-status
    """
    try:
        # Check if we're in a git repository
        try:
            repo_root = LegesherConfig._find_repo_root()
            click.echo(f"Repository: {repo_root}\n")
        except ValueError:
            click.echo("Not in a git repository\n")
            repo_root = None

        # Load configuration
        try:
            config = LegesherConfig.load(repo_root)
            click.echo("Configuration:")
            click.echo(f"  Language: {config.language}")
            click.echo(f"  Python version: {config.python_version or '(auto-detect)'}")
            click.echo(f"  Canonical language: {config.git_canonical_language}")
            click.echo(f"  Filters enabled: {config.git_filter_enabled}")
        except Exception as e:
            click.echo(f"  No configuration found: {e}")

        click.echo()

        # Check git filter configuration
        click.echo("Git filter status:")

        # Check clean filter
        result = subprocess.run(
            ["git", "config", "filter.legesher.clean"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            click.echo(f"  ✓ Clean filter: {result.stdout.strip()}")
        else:
            click.echo("  ✗ Clean filter: Not configured")

        # Check smudge filter
        result = subprocess.run(
            ["git", "config", "filter.legesher.smudge"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            click.echo(f"  ✓ Smudge filter: {result.stdout.strip()}")
        else:
            click.echo("  ✗ Smudge filter: Not configured")

        click.echo()

        # Check .gitattributes
        if repo_root:
            gitattributes_path = repo_root / ".gitattributes"
            if gitattributes_path.exists():
                content = gitattributes_path.read_text()
                if "filter=legesher" in content:
                    click.echo("  ✓ .gitattributes configured")
                else:
                    click.echo("  ✗ .gitattributes exists but no legesher filter")
            else:
                click.echo("  ✗ .gitattributes not found")

    except Exception as e:
        logger.error(f"Error checking git status: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _configure_git_filters(use_global: bool = False) -> bool:
    """Configure git clean/smudge filters.

    Args:
        use_global: If True, configure globally; otherwise configure for current repo

    Returns:
        True if successful, False otherwise
    """
    scope_flag = "--global" if use_global else "--local"

    try:
        # Configure clean filter (local → canonical English)
        subprocess.run(
            [
                "git",
                "config",
                scope_flag,
                "filter.legesher.clean",
                "legesher-filter --clean",
            ],
            check=True,
            capture_output=True,
        )

        # Configure smudge filter (canonical English → local)
        subprocess.run(
            [
                "git",
                "config",
                scope_flag,
                "filter.legesher.smudge",
                "legesher-filter --smudge",
            ],
            check=True,
            capture_output=True,
        )

        # Mark filter as required (git will error if filter command fails)
        # Set to false so git doesn't error if legesher isn't installed
        subprocess.run(
            [
                "git",
                "config",
                scope_flag,
                "filter.legesher.required",
                "false",
            ],
            check=True,
            capture_output=True,
        )

        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to configure git filters: {e}")
        return False


def _create_gitattributes(repo_root: Path) -> None:
    """Create or update .gitattributes file.

    Args:
        repo_root: Repository root directory
    """
    gitattributes_path = repo_root / ".gitattributes"

    # Read existing content if file exists
    if gitattributes_path.exists():
        existing_content = gitattributes_path.read_text()
        lines = existing_content.splitlines()
    else:
        lines = []

    # Check if legesher filter is already configured
    legesher_line = "*.py filter=legesher"
    if legesher_line not in lines:
        # Add legesher filter configuration
        if lines and not lines[-1].strip():
            # File exists and last line is blank
            lines.append(legesher_line)
        elif lines:
            # File exists, add blank line then our config
            lines.append("")
            lines.append("# Legesher multilingual code translation")
            lines.append(legesher_line)
        else:
            # New file
            lines.append("# Legesher multilingual code translation")
            lines.append(legesher_line)

    # Write back to file
    gitattributes_path.write_text("\n".join(lines) + "\n")


def _initialize_metadata(repo_root: Path, track_metadata: bool) -> None:
    """Initialize metadata directory and configure tracking.

    Args:
        repo_root: Repository root directory
        track_metadata: Whether to track metadata files in git
    """
    try:
        # Create metadata directory
        metadata_dir = repo_root / ".legesher" / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        click.echo(f"✓ Created metadata directory: {metadata_dir}")

        # Configure .gitignore based on user preference
        if not track_metadata:
            gitignore_path = repo_root / ".gitignore"

            # Read existing content if file exists
            if gitignore_path.exists():
                existing_content = gitignore_path.read_text()
            else:
                existing_content = ""

            # Check if metadata ignore is already configured
            if ".legesher/metadata/" not in existing_content:
                with gitignore_path.open("a") as f:
                    # Add newline if file doesn't end with one
                    if existing_content and not existing_content.endswith("\n"):
                        f.write("\n")
                    f.write("\n# Legesher metadata (optional)\n")
                    f.write(".legesher/metadata/\n")
                click.echo("✓ Added .legesher/metadata/ to .gitignore")
            else:
                click.echo("✓ Metadata already in .gitignore")
        else:
            click.echo("✓ Metadata will be tracked in git")

        # Verify metadata system is working
        try:
            from legesher_core.metadata import MetadataManager

            MetadataManager(repo_root)
            click.echo("✓ Metadata system initialized successfully")
        except Exception as e:
            click.echo(
                f"⚠ Warning: Metadata system initialization had issues: {e}", err=True
            )
            click.echo(
                "  Git filters will still work, but metadata tracking may be limited",
                err=True,
            )

    except Exception as e:
        logger.error(f"Error initializing metadata: {e}", exc_info=True)
        click.echo(f"⚠ Warning: Could not initialize metadata: {e}", err=True)
        click.echo("  Git filters will still work without metadata", err=True)


def _verify_git_setup(use_global: bool = False) -> bool:
    """Verify git filter setup is working.

    Args:
        use_global: Whether checking global or local config

    Returns:
        True if setup verified, False otherwise
    """
    scope_flag = "--global" if use_global else "--local"

    try:
        # Check clean filter
        result = subprocess.run(
            ["git", "config", scope_flag, "filter.legesher.clean"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return False

        # Check smudge filter
        result = subprocess.run(
            ["git", "config", scope_flag, "filter.legesher.smudge"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return False

        return True

    except Exception as e:
        logger.error(f"Error verifying git setup: {e}")
        return False


# Export commands for registration in main CLI
__all__ = ["git", "git_setup", "git_status"]
