"""Git integration commands for Legesher.

Git stores each file in its author's language. ``legesher git setup``
configures the clean filter, which only normalizes: a stray keyword is
rewritten to the language its block is stored in (CORE-1841). It also
installs the pre-commit hook that runs ``legesher guard``, because a filter
cannot refuse anything. The keyword-only smudge, which renders an English
file's keywords in your language on checkout, is an opt-in for terminal
editors; every other view renders in the editor or on GitHub, never in files.

Commands:
    legesher git setup: Configure the filter and the guard hook
    legesher git status: Show the current configuration
"""

import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path

import click

from legesher.config import LegesherConfig
from legesher_core.transformer import TokenTranslator

# Configure logger
logger = logging.getLogger(__name__)

#: The filter commands git runs; ``%f`` is the path, so the filter can read
#: the committed version of it.
CLEAN_COMMAND = "legesher-filter --clean --path %f"
SMUDGE_COMMAND = "legesher-filter --smudge --path %f"

#: The hook's second line. A hook is ours to update or remove only when the
#: whole file matches the template below, not when it merely mentions this.
HOOK_MARKER = "# legesher-guard-hook: installed by `legesher git setup`."
_HOOK_TEMPLATE = """#!/bin/sh
{marker}
# Refuses a commit when a staged Legesher file fails `legesher guard`.
# A client-side check: `git commit --no-verify`, merges and rebases skip it.
# `legesher git setup --no-hook` removes it.
LEGESHER={executable}
if [ -n "$LEGESHER" ] && [ -x "$LEGESHER" ]; then
    exec "$LEGESHER" guard --staged
fi
if command -v legesher >/dev/null 2>&1; then
    exec legesher guard --staged
fi
echo "legesher: guard skipped, the legesher command was not found" >&2
exit 0
"""
_SH_QUOTED = r"'(?:[^']|'\\'')*'"
_HOOK_PATTERN = re.compile(
    re.escape(
        _HOOK_TEMPLATE.format(marker=HOOK_MARKER, executable="@EXECUTABLE@")
    ).replace("@EXECUTABLE@", _SH_QUOTED)
)


def _sh_quote(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


def _legesher_executable() -> str:
    """The ``legesher`` command running setup, or ``""`` when none is found.

    Named in the hook so a commit from a shell where the project environment
    is not active still runs the guard.
    """
    bin_dir = Path(sys.executable).parent
    for name in ("legesher", "legesher.exe"):
        candidate = bin_dir / name
        if candidate.is_file():
            return str(candidate)
    return shutil.which("legesher") or ""


def hook_script(executable: str) -> str:
    """The pre-commit hook, naming ``executable`` (may be empty)."""
    return _HOOK_TEMPLATE.format(marker=HOOK_MARKER, executable=_sh_quote(executable))


@click.group(name="git")
def git():
    """Git integration commands.

    Configure the clean filter and the guard hook for a repository whose
    files are stored in their authors' languages.

    \b
    Examples:
        # Set up for Spanish
        $ legesher git setup --language es

        # Check the configuration
        $ legesher git status
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
@click.option(
    "--keyword-smudge/--no-keyword-smudge",
    default=False,
    help=(
        "Opt in to rendering an English file's keywords in your language on "
        "checkout, for terminal editors (default: off)"
    ),
)
@click.option(
    "--hook/--no-hook",
    default=True,
    help="Install the pre-commit hook that runs `legesher guard` (default: on)",
)
def git_setup(
    language: str,
    python_version: str | None,
    use_global: bool,
    track_metadata: bool,
    keyword_smudge: bool,
    hook: bool,
):
    """Set up the clean filter and the guard hook.

    Git stores each file in its author's language. The clean filter only
    normalizes: a stray keyword, such as an English `if` typed into a
    Spanish file, is stored in its block's language. It never refuses a
    file; the pre-commit hook runs `legesher guard` for that.

    \b
    - Clean filter (git add): stray keywords join their block's language
    - Guard hook (git commit): refuses Trojan Source characters and
      keywords that skipped the filter
    - Keyword-only smudge (opt-in): renders an English file's keywords in
      your language on checkout

    \b
    Examples:
        $ legesher git setup --language es
        $ legesher git setup --language ar --python-version 3.13
        $ legesher git setup --language es --keyword-smudge
        $ legesher git setup --language es --no-hook
        $ legesher git setup --language es --global
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
        scope = "--global" if use_global else "--local"
        had_smudge = _filter_config("smudge", scope) is not None
        success = _configure_git_filters(
            use_global=use_global, keyword_smudge=keyword_smudge
        )
        if not success:
            click.echo("✗ Failed to configure git filters", err=True)
            sys.exit(1)
        click.echo(f"✓ Clean filter: {CLEAN_COMMAND}")
        still_on = None if keyword_smudge else _filter_config("smudge")
        if keyword_smudge:
            click.echo(f"✓ Keyword-only smudge: {SMUDGE_COMMAND}")
        elif still_on is not None:
            where = (
                "your global git config"
                if _filter_config("smudge", "--global") is not None
                else "another git config file"
            )
            click.echo(
                f"⚠ A smudge filter is still configured in {where} ({still_on}), "
                "so checkouts still render. Run `legesher git setup --global` to "
                "turn it off there, or see `git config --show-origin --get "
                "filter.legesher.smudge`."
            )
        elif had_smudge:
            click.echo(
                "✓ Smudge filter turned off (rendered views are never files). "
                "Files checked out with it keep their rendering until you run "
                "`git checkout -- <path>`; commit or stash your changes first."
            )

        # Step 5: Create .gitattributes (only for project, not global)
        if not use_global:
            click.echo("\nConfiguring .gitattributes...")
            _create_gitattributes(repo_root)
            click.echo("✓ Updated .gitattributes")

        # Step 6: Initialize metadata directory (only for project, not global)
        if not use_global:
            click.echo("\nInitializing metadata system...")
            _initialize_metadata(repo_root, track_metadata)

        # Step 7: The guard hook (only for a repository; repo_root is None
        # exactly when --global)
        if repo_root is not None:
            click.echo("\nConfiguring the guard hook...")
            _report_hook(repo_root, install=hook)

        # Step 8: Verify setup
        click.echo("\nVerifying setup...")
        if _verify_git_setup(use_global=use_global, keyword_smudge=keyword_smudge):
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
            click.echo("Storage: each file in its author's language")
            click.echo("\nNext steps:")
            click.echo(f"1. Write code in {language}")
            click.echo(
                "2. Run 'git add' - an English keyword typed into your file is "
                f"stored in {language}"
            )
            click.echo("3. Run 'git commit' - the guard hook checks what you staged")
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
            click.echo(f"  Filters enabled: {config.git_filter_enabled}")
        except Exception as e:
            click.echo(f"  No configuration found: {e}")

        click.echo()

        # Check git filter configuration
        click.echo("Git filter status:")

        clean = _filter_config("clean")
        if clean is not None:
            click.echo(f"  ✓ Clean filter: {clean}")
        else:
            click.echo("  ✗ Clean filter: Not configured")

        smudge = _filter_config("smudge")
        if smudge is not None:
            click.echo(f"  ✓ Keyword-only smudge: {smudge}")
        else:
            click.echo("  Smudge filter: off (the default)")

        if repo_root:
            state = _hook_state(repo_root)
            if state == "ours":
                click.echo("  ✓ Guard hook: installed")
            elif state == "foreign":
                click.echo(
                    "  ⚠ Guard hook: another pre-commit hook is installed; "
                    "add `legesher guard --staged` to it"
                )
            else:
                click.echo("  ✗ Guard hook: not installed")

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


def _filter_config(mode: str, scope: str | None = None) -> str | None:
    """The ``filter.legesher.<mode>`` command, or ``None``.

    ``scope`` is ``"--local"`` or ``"--global"``; ``None`` reads the value git
    actually uses, whichever file it comes from.
    """
    try:
        result = subprocess.run(
            [
                "git",
                "config",
                *([scope] if scope else []),
                "--get",
                f"filter.legesher.{mode}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    value = result.stdout.strip() if result.returncode == 0 else ""
    return value or None


def _configure_git_filters(
    use_global: bool = False, keyword_smudge: bool = False
) -> bool:
    """Configure the clean filter, and the keyword-only smudge when opted in.

    Without the opt-in an existing smudge command is removed, so re-running
    setup turns a smudge off. ``required`` stays false: git's manual expects
    a project to stay usable when a machine lacks the filter, and a required
    clean filter would turn a failure into an error in ``git status`` too.

    Returns:
        True if successful, False otherwise
    """
    scope_flag = "--global" if use_global else "--local"

    try:
        subprocess.run(
            ["git", "config", scope_flag, "filter.legesher.clean", CLEAN_COMMAND],
            check=True,
            capture_output=True,
        )

        if keyword_smudge:
            subprocess.run(
                ["git", "config", scope_flag, "filter.legesher.smudge", SMUDGE_COMMAND],
                check=True,
                capture_output=True,
            )
        else:
            # Exit status 5 means there was nothing to unset.
            result = subprocess.run(
                ["git", "config", scope_flag, "--unset-all", "filter.legesher.smudge"],
                capture_output=True,
            )
            if result.returncode not in (0, 5):
                raise subprocess.CalledProcessError(result.returncode, result.args)

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


def _verify_git_setup(use_global: bool = False, keyword_smudge: bool = False) -> bool:
    """Check that the clean filter is set, and the smudge only if opted in.

    Returns:
        True if setup verified, False otherwise
    """
    scope_flag = "--global" if use_global else "--local"

    try:
        values = {}
        for mode in ("clean", "smudge"):
            result = subprocess.run(
                ["git", "config", scope_flag, "--get", f"filter.legesher.{mode}"],
                capture_output=True,
                text=True,
            )
            values[mode] = result.stdout.strip() if result.returncode == 0 else None
        if values["clean"] != CLEAN_COMMAND:
            return False
        return (values["smudge"] == SMUDGE_COMMAND) == keyword_smudge

    except Exception as e:
        logger.error(f"Error verifying git setup: {e}")
        return False


def _hooks_dir(repo_root: Path) -> Path:
    """Where git looks for hooks, honoring ``core.hooksPath`` and worktrees."""
    result = subprocess.run(
        ["git", "rev-parse", "--git-path", "hooks"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    path = Path(result.stdout.strip()) if result.returncode == 0 else Path(".git/hooks")
    return path if path.is_absolute() else repo_root / path


def _hook_state(repo_root: Path) -> str:
    """``"ours"``, ``"foreign"`` (anything else) or ``"absent"``.

    Ours means the whole file matches the hook template. A symlink is never
    ours, so setup never writes through one or removes one.
    """
    hook = _hooks_dir(repo_root) / "pre-commit"
    if hook.is_symlink():
        return "foreign"
    if not hook.exists():
        return "absent"
    if not hook.is_file():
        return "foreign"
    try:
        text = hook.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return "foreign"
    return "ours" if _HOOK_PATTERN.fullmatch(text) else "foreign"


def _install_pre_commit_hook(repo_root: Path) -> str:
    """Install the guard hook unless another hook is there.

    Returns:
        ``"installed"``, ``"unchanged"`` (ours, already current) or
        ``"foreign"`` (another pre-commit hook, left untouched).
    """
    state = _hook_state(repo_root)
    if state == "foreign":
        return "foreign"
    hook = _hooks_dir(repo_root) / "pre-commit"
    script = hook_script(_legesher_executable())
    if state == "ours" and hook.read_text(encoding="utf-8") == script:
        return "unchanged"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(script, encoding="utf-8")
    hook.chmod(hook.stat().st_mode | 0o111)
    return "installed"


def _remove_pre_commit_hook(repo_root: Path) -> bool:
    """Remove the guard hook if it is ours. Returns whether it was removed."""
    if _hook_state(repo_root) != "ours":
        return False
    (_hooks_dir(repo_root) / "pre-commit").unlink()
    return True


def _report_hook(repo_root: Path, install: bool) -> None:
    """Install or remove the guard hook, and say what happened."""
    try:
        if not install:
            if _remove_pre_commit_hook(repo_root):
                click.echo("✓ Removed the guard hook")
            else:
                click.echo("✓ Guard hook not installed (--no-hook)")
            return
        outcome = _install_pre_commit_hook(repo_root)
    except OSError as e:
        click.echo(f"⚠ Warning: could not write the guard hook: {e}", err=True)
        return
    if outcome == "foreign":
        click.echo(
            "⚠ Another pre-commit hook is installed, so it was left as it is. "
            "Add this line to it to run the guard: legesher guard --staged"
        )
    elif outcome == "installed":
        click.echo("✓ Installed the guard hook (pre-commit: legesher guard --staged)")
    else:
        click.echo("✓ Guard hook already installed")


# Export commands for registration in main CLI
__all__ = ["git", "git_setup", "git_status"]
