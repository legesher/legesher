"""Interactive initialization command for Legesher projects.

This module provides the `legesher init` command for setting up Legesher in
a new Python project. It guides users through language selection, Python version
detection, git integration setup, and AI context generation.

Example:
    $ legesher init
    $ legesher init --language es ar zh  # Pre-select languages
    $ legesher init --no-git             # Skip git setup
    $ legesher init --no-ai-context      # Skip AI context generation
"""

import re
import subprocess
import sys
from pathlib import Path
from collections.abc import Sequence

import click
import questionary

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore[import-not-found]

from legesher_core import AIContextGenerator
from legesher_i18n import LanguagePackLoader, PackNotFoundError
from legesher_i18n.language_registry import LANGUAGE_METADATA


# Generate AVAILABLE_LANGUAGES from LANGUAGE_METADATA (single source of truth)
AVAILABLE_LANGUAGES = {
    code: f"{meta['name']} ({meta['native']})"
    for code, meta in LANGUAGE_METADATA.items()
}


@click.command()
@click.option(
    "--language",
    "-l",
    multiple=True,
    type=click.Choice(list(AVAILABLE_LANGUAGES.keys()), case_sensitive=False),
    help="Pre-select languages (can specify multiple times)",
)
@click.option(
    "--python-version",
    "-p",
    type=str,
    help="Python version (auto-detected from pyproject.toml if not provided)",
)
@click.option(
    "--git/--no-git",
    default=None,
    help="Enable/disable git integration (prompts if not specified)",
)
@click.option(
    "--ai-context/--no-ai-context",
    default=None,
    help="Enable/disable AI context generation (prompts if not specified)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Overwrite existing configuration",
)
def init(
    language: tuple[str, ...],
    python_version: str | None,
    git: bool | None,
    ai_context: bool | None,
    force: bool,
) -> None:
    """Initialize Legesher in your Python project.

    This interactive command helps you set up Legesher for multilingual
    Python development. It will:

    \b
    1. Detect your Python version from pyproject.toml
    2. Let you choose which languages to support
    3. Optionally set up git filters for canonical English storage
    4. Generate AI assistant context files
    5. Create .legesher/config.yml with your preferences

    Examples:

        \b
        # Interactive setup (recommended)
        $ legesher init

        \b
        # Pre-select Spanish and Arabic, skip prompts
        $ legesher init -l es -l ar --git --ai-context

        \b
        # Force overwrite existing configuration
        $ legesher init --force
    """
    click.echo(click.style("\n🌍 Welcome to Legesher!\n", fg="cyan", bold=True))
    click.echo("Let's set up your project for multilingual Python development.\n")

    # Check if already initialized
    config_path = Path(".legesher/config.yml")
    if config_path.exists() and not force:
        click.echo(
            click.style(
                "❌ Legesher is already initialized in this project.",
                fg="red",
            )
        )
        click.echo(f"   Config found at: {config_path}\n")
        click.echo("   Use --force to overwrite existing configuration.")
        sys.exit(1)

    # Step 1: Detect Python version
    detected_version = _detect_python_version()
    if python_version:
        py_version = python_version
        click.echo(f"✓ Using Python version: {py_version} (from --python-version flag)")
    elif detected_version:
        py_version = detected_version
        click.echo(f"✓ Detected Python version: {py_version} (from pyproject.toml)")
    else:
        if sys.stdin.isatty():
            py_version = questionary.text(
                "Python version (e.g., 3.13):",
                default="3.13",
            ).ask()
            if not py_version:
                click.echo(click.style("\n❌ Setup cancelled.", fg="red"))
                sys.exit(1)
        else:
            click.echo(
                click.style(
                    "❌ Cannot detect Python version in non-interactive mode.",
                    fg="red",
                )
            )
            click.echo("   Use --python-version / -p to specify it.")
            sys.exit(1)

    click.echo()

    # Step 2: Language selection
    if language:
        selected_languages = list(language)
        click.echo(f"✓ Using pre-selected languages: {', '.join(selected_languages)}")
    else:
        if sys.stdin.isatty():
            selected_languages = _select_languages()
            if not selected_languages:
                click.echo(click.style("\n❌ Setup cancelled.", fg="red"))
                sys.exit(1)
        else:
            click.echo(
                click.style(
                    "❌ No languages specified in non-interactive mode.",
                    fg="red",
                )
            )
            click.echo("   Use --language / -l to specify languages.")
            sys.exit(1)

    click.echo()

    # Step 3: Git integration
    if git is None:
        if sys.stdin.isatty():
            git_enabled = questionary.confirm(
                "Set up git filters for canonical English storage?",
                default=True,
            ).ask()
            if git_enabled is None:
                click.echo(click.style("\n❌ Setup cancelled.", fg="red"))
                sys.exit(1)
        else:
            git_enabled = True
    else:
        git_enabled = git

    if git_enabled:
        click.echo("✓ Git integration will be enabled")
    else:
        click.echo("○ Git integration will be skipped")

    click.echo()

    # Step 4: AI context generation
    if ai_context is None:
        if sys.stdin.isatty():
            ai_enabled = questionary.confirm(
                "Generate AI assistant context files? (helps Claude Code, Copilot, etc.)",
                default=True,
            ).ask()
            if ai_enabled is None:
                click.echo(click.style("\n❌ Setup cancelled.", fg="red"))
                sys.exit(1)
        else:
            ai_enabled = True
    else:
        ai_enabled = ai_context

    if ai_enabled:
        click.echo("✓ AI context generation will be enabled")
    else:
        click.echo("○ AI context generation will be skipped")

    click.echo("\n" + "─" * 60 + "\n")

    # Step 5: Generate files
    click.echo(click.style("📦 Creating Legesher configuration...\n", bold=True))

    # Create .legesher directory structure
    legesher_dir = Path(".legesher")
    legesher_dir.mkdir(exist_ok=True)
    (legesher_dir / "metadata").mkdir(exist_ok=True)

    # Generate config.yml
    _generate_config(
        config_path, selected_languages, py_version, git_enabled, ai_enabled
    )
    click.echo(f"✓ Created {config_path}")

    # Generate AI context files if enabled
    generated_ai_contexts = []
    if ai_enabled:
        loader = LanguagePackLoader()  # Cache: reuse for all languages
        for lang in selected_languages:
            try:
                pack = loader.load(lang, "python", py_version)

                # Generate AI context
                generator = AIContextGenerator(
                    language_code=lang,
                    python_version=py_version,
                    keywords=pack.keywords,
                    builtins=pack.builtins,
                    exceptions=getattr(pack, "exceptions", {}),
                )

                ai_context_path = legesher_dir / f"AI-CONTEXT-{lang}.md"
                generator.generate(ai_context_path)
                click.echo(f"✓ Generated {ai_context_path}")
                generated_ai_contexts.append(lang)
            except PackNotFoundError:
                click.echo(
                    click.style(
                        f"  ⚠ Language pack '{lang}' not found for Python {py_version}",
                        fg="yellow",
                    )
                )
                click.echo(f"    Available packs may not support Python {py_version}")
            except Exception as e:
                click.echo(
                    click.style(
                        f"  ⚠ Unexpected error generating AI context for {lang}: {e}",
                        fg="yellow",
                    )
                )

    # Setup git if enabled
    if git_enabled:
        _setup_git_integration()

    # Success summary
    click.echo("\n" + "─" * 60 + "\n")
    click.echo(click.style("✅ Legesher setup complete!\n", fg="green", bold=True))

    click.echo("📁 Created files:")
    click.echo(f"   • {config_path}")
    if generated_ai_contexts:
        for lang in generated_ai_contexts:
            click.echo(f"   • .legesher/AI-CONTEXT-{lang}.md")
    if git_enabled:
        click.echo("   • .gitattributes (updated)")
        click.echo("   • .git/config (updated)")

    click.echo("\n🚀 Next steps:")
    click.echo("   1. Start coding in your language!")
    click.echo("   2. Create a new .py file and write Python code")
    click.echo(f"   3. Use these language keywords: {', '.join(selected_languages)}")
    click.echo("   4. AI assistants will understand your multilingual code\n")

    if generated_ai_contexts:
        click.echo("💡 Tip: Your AI coding assistant (Claude Code, Copilot, etc.)")
        click.echo("   can now understand your multilingual code thanks to the")
        click.echo("   AI-CONTEXT files. They'll suggest code in your language!\n")


def _detect_python_version() -> str | None:
    """Detect Python version from pyproject.toml.

    Returns:
        Python version string (e.g., "3.13") or None if not found
    """
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return None

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        # Try to extract from project.requires-python
        requires_python = data.get("project", {}).get("requires-python", "")
        if requires_python:
            # Parse ">=3.13" or "^3.13" or "~=3.13" etc.
            match = re.search(r"(\d+\.\d+)", requires_python)
            if match:
                return match.group(1)

        # Try to extract from tool.poetry.dependencies.python
        poetry_python = (
            data.get("tool", {})
            .get("poetry", {})
            .get("dependencies", {})
            .get("python", "")
        )
        if poetry_python:
            match = re.search(r"(\d+\.\d+)", poetry_python)
            if match:
                return match.group(1)

    except Exception:
        # Silently fail if pyproject.toml is malformed or missing required fields
        # User will be prompted for version if detection fails
        pass

    return None


def _select_languages() -> list[str]:
    """Interactive language selection with multi-select checkboxes.

    Returns:
        List of selected language codes
    """
    click.echo(click.style("🌐 Language Selection", bold=True))
    click.echo(
        "Select the languages you want to code in (space to select, enter to confirm):\n"
    )

    choices = [
        questionary.Choice(
            title=f"{code}: {name}",
            value=code,
        )
        for code, name in sorted(AVAILABLE_LANGUAGES.items(), key=lambda x: x[1])
    ]

    selected = questionary.checkbox(
        "Languages:",
        choices=choices,
    ).ask()

    if not selected:
        return []

    click.echo()
    click.echo(f"✓ Selected {len(selected)} language(s): {', '.join(selected)}")
    return selected


def _generate_config(
    config_path: Path,
    languages: Sequence[str],
    python_version: str,
    git_enabled: bool,
    ai_enabled: bool,
) -> None:
    """Generate .legesher/config.yml configuration file.

    Args:
        config_path: Path to config.yml
        languages: List of selected language codes
        python_version: Python version string
        git_enabled: Whether git integration is enabled
        ai_enabled: Whether AI context is enabled
    """
    config_content = f"""# Legesher Configuration
# Generated by: legesher init
# Documentation: https://docs.legesher.io

# Languages enabled in this project
languages:
{_yaml_list(languages, indent=2)}

# Python version for language pack compatibility
python_version: "{python_version}"

# Git integration (canonical English storage)
git:
  enabled: {str(git_enabled).lower()}
  canonical_language: "en"

# AI assistant context generation
ai_context:
  enabled: {str(ai_enabled).lower()}
  context_files:
{_yaml_list([f"AI-CONTEXT-{lang}.md" for lang in languages], indent=4)}

# Translation preferences
translation:
  # Default source language (for ambiguous cases)
  default_source: "en"

  # Default target language (for CLI commands)
  default_target: "{languages[0] if languages else "en"}"

  # Preserve comments during translation
  preserve_comments: true

  # Preserve string literals during translation
  preserve_strings: true

# Editor integration
editor:
  # Enable LSP hover context enrichment
  lsp_hover: true

  # Enable inline completion context injection
  inline_completion: true

  # Show bilingual tooltips
  bilingual_tooltips: true
"""

    config_path.write_text(config_content, encoding="utf-8")


def _yaml_list(items: Sequence[str], indent: int = 0) -> str:
    """Format a list as YAML list items.

    Args:
        items: List of strings
        indent: Number of spaces for indentation

    Returns:
        YAML formatted list
    """
    prefix = " " * indent
    return "\n".join(f"{prefix}- {item}" for item in items)


def _setup_git_integration() -> None:
    """Set up git filters and attributes for canonical English storage."""
    # Create .gitattributes
    gitattributes_path = Path(".gitattributes")
    gitattributes_content = """# Legesher: Store Python files as English in git
*.py filter=legesher diff=legesher

# Legesher metadata is stored as-is
.legesher/** -filter -diff
"""

    if gitattributes_path.exists():
        existing = gitattributes_path.read_text(encoding="utf-8")
        if "filter=legesher" not in existing:
            with open(gitattributes_path, "a", encoding="utf-8") as f:
                f.write("\n" + gitattributes_content)
            click.echo("✓ Updated .gitattributes")
        else:
            click.echo("○ .gitattributes already configured")
    else:
        gitattributes_path.write_text(gitattributes_content, encoding="utf-8")
        click.echo("✓ Created .gitattributes")

    # Configure git filters
    try:
        subprocess.run(
            ["git", "config", "filter.legesher.clean", "legesher git clean %f"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        subprocess.run(
            ["git", "config", "filter.legesher.smudge", "legesher git smudge %f"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        click.echo("✓ Configured git filters")
    except subprocess.CalledProcessError as e:
        click.echo(
            click.style(
                f"  ⚠ Could not configure git filters: {e}",
                fg="yellow",
            )
        )
        click.echo("    You can manually configure them later with:")
        click.echo('    git config filter.legesher.clean "legesher git clean %f"')
        click.echo('    git config filter.legesher.smudge "legesher git smudge %f"')


__all__ = ["init"]
