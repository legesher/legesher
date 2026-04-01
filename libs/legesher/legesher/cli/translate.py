"""Translate command for Legesher CLI.

This module implements the `legesher translate` command for translating
Python code between natural languages.

Example:
    $ legesher translate input.py --from es --to en --output output.py
    $ cat input.py | legesher translate --from es --to en
    $ legesher translate src/ --from es --to en --output translated/
"""

import json
import shutil
import sys
from importlib.resources import files as resource_files
from pathlib import Path
from typing import Optional

import click

from legesher_core import TokenTranslator
from legesher_core.exceptions import TranslationError


def _load_languages_metadata() -> dict[str, dict]:
    """Load language metadata from legesher_i18n's languages.json."""
    try:
        languages_file = resource_files("legesher_i18n").joinpath("languages.json")
        data = json.loads(languages_file.read_text(encoding="utf-8"))
        return data.get("languages", {})
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ModuleNotFoundError):
        return {}


def _build_supported_languages_text() -> str:
    """Build formatted text listing all supported languages for help output."""
    langs = _load_languages_metadata()
    if not langs:
        return "    en  English\n    es  Spanish\n    ar  Arabic\n    hi  Hindi"
    lines = [
        f"    {code:4s}{info.get('name', code.upper())}"
        for code, info in sorted(langs.items())
        if isinstance(info, dict)
    ]
    return "\n".join(lines)


def _create_llm_backend(llm_backend: str, llm_base_url: Optional[str]):
    """Create an LLM backend based on CLI options.

    Args:
        llm_backend: Backend name (anthropic, cohere-aya, openai-compat)
        llm_base_url: Optional base URL for openai-compat backend

    Returns:
        TextTranslationBackend instance
    """
    from legesher_i18n.api import TranslationCoordinator
    from legesher_i18n.api.backends import ProviderBackendAdapter

    if llm_backend == "anthropic":
        from legesher_i18n.api.providers import AnthropicProvider

        coordinator = TranslationCoordinator(providers=[AnthropicProvider()])
    elif llm_backend == "cohere-aya":
        from legesher_i18n.api.providers import CohereAyaProvider

        coordinator = TranslationCoordinator(providers=[CohereAyaProvider()])
    elif llm_backend == "openai-compat":
        from legesher_i18n.api.providers import OpenAICompatProvider

        kwargs = {}
        if llm_base_url:
            kwargs["base_url"] = llm_base_url
        coordinator = TranslationCoordinator(providers=[OpenAICompatProvider(**kwargs)])
    else:
        raise click.BadParameter(
            f"Unknown LLM backend: {llm_backend}. "
            "Supported: anthropic, cohere-aya, openai-compat"
        )

    # Map CLI names (hyphenated) to provider .name attributes (underscored)
    provider_name_map = {
        "anthropic": "anthropic",
        "cohere-aya": "cohere_aya",
        "openai-compat": "openai_compat",
    }
    preferred = provider_name_map.get(llm_backend, llm_backend)
    return ProviderBackendAdapter(coordinator, preferred_provider=preferred)


@click.command(epilog="\b\nSupported Languages:\n" + _build_supported_languages_text())
@click.argument("input", type=click.Path(exists=True), required=False)
@click.option(
    "--from",
    "source_lang",
    default="en",
    help="Source language code (default: en)",
    show_default=True,
)
@click.option(
    "--to",
    "target_lang",
    required=True,
    help="Target language code (required)",
)
@click.option(
    "--output",
    type=click.Path(),
    help="Output file or directory path",
)
@click.option(
    "--full",
    is_flag=True,
    default=False,
    help="Enable full LLM translation (identifiers, comments, strings, docstrings)",
)
@click.option(
    "--llm-backend",
    type=click.Choice(["anthropic", "cohere-aya", "openai-compat"]),
    default="anthropic",
    help="LLM backend for --full translation",
    show_default=True,
)
@click.option(
    "--llm-base-url",
    type=str,
    default=None,
    help="Base URL for openai-compat backend (e.g., http://localhost:8000)",
)
@click.option(
    "--identifier-map",
    type=click.Path(),
    default=None,
    help="Path to load/save identifier map for cross-file consistency",
)
@click.option(
    "--checkpoint",
    type=click.Path(),
    default=None,
    help="Path to checkpoint file for resuming batch jobs (plain text, one path per line)",
)
def translate(
    input: Optional[str],
    source_lang: str,
    target_lang: str,
    output: Optional[str],
    full: bool,
    llm_backend: str,
    llm_base_url: Optional[str],
    identifier_map: Optional[str],
    checkpoint: Optional[str],
):
    """Translate Python code between natural languages.

    Legesher translates Python keywords and built-ins while preserving
    variable names, function names, and the semantic meaning of your code.

    \b
    Arguments:
        INPUT   File or directory to translate (omit or use '-' for stdin)

    \b
    Examples:
        # Translate a single file
        $ legesher translate input.py --from es --to en --output output.py

        # Translate from stdin to stdout
        $ cat input.py | legesher translate --from es --to en
        $ echo "definir foo(): retornar 42" | legesher translate --from es --to en

        # Translate a directory recursively
        $ legesher translate src/ --from es --to en --output translated/

        # Full LLM translation (identifiers, comments, strings)
        $ legesher translate src/ --to es --full --llm-backend anthropic

        # Full translation with local model
        $ legesher translate src/ --to ur --full --llm-backend openai-compat \\
            --llm-base-url http://localhost:8000

        # Resume interrupted batch with identifier map
        $ legesher translate src/ --to zh --full \\
            --identifier-map .legesher/identifier_map.json \\
            --checkpoint .legesher/checkpoint.txt
    """
    try:
        # Load translator based on translation direction and mode
        if full:
            # Full LLM translation requires English source (tree-sitter parses English grammar)
            if source_lang != "en":
                click.echo(
                    f"Error: --full mode requires English source (--from en). "
                    f"Got --from {source_lang}. Translate to English first, "
                    f"then use --full to translate to {target_lang}.",
                    err=True,
                )
                sys.exit(1)
            backend = _create_llm_backend(llm_backend, llm_base_url)

            from legesher_core import TokenTranslator, create_translator

            # Load keyword/builtin maps via TokenTranslator (uses the working pack loader)
            base_translator = TokenTranslator.from_language_pack(target_lang)

            # Load identifier map for cross-file consistency
            id_map = None
            if identifier_map:
                from legesher_core.tree_sitter.identifier_map import IdentifierMap

                id_map = IdentifierMap.load_or_create(Path(identifier_map))

            translator = create_translator(
                "python",
                keyword_map=base_translator.mapper.keyword_map,
                builtin_map=base_translator.mapper.builtin_map,
                backend=backend,
            )

            # Inject identifier map if provided
            if id_map is not None:
                translator.identifier_map = id_map

            click.echo(
                f"Full translation mode: {llm_backend} backend, "
                f"{source_lang} → {target_lang}",
                err=True,
            )
        elif source_lang == "en":
            # Standard keyword-only translation
            translator = TokenTranslator.from_language_pack(target_lang)
        else:
            # Translating from non-English to English (or another language)
            source_translator = TokenTranslator.from_language_pack(source_lang)
            if target_lang == "en":
                translator = source_translator.reverse()
            else:
                raise NotImplementedError(
                    f"Direct translation from {source_lang} to {target_lang} "
                    "is not yet supported. Please translate to English first, "
                    "then to the target language."
                )

        # Determine input mode
        if input is None or input == "-":
            # Stdin mode
            _handle_stdin(translator, source_lang, target_lang, output)
        elif Path(input).is_file():
            # Single file mode
            _handle_file(translator, input, source_lang, target_lang, output)
        elif Path(input).is_dir():
            # Directory mode
            _handle_directory(
                translator,
                input,
                source_lang,
                target_lang,
                output,
                checkpoint_path=checkpoint,
            )
        else:
            click.echo(f"Error: Invalid input: {input}", err=True)
            sys.exit(1)

        # Save identifier map after translation (if using --full + --identifier-map)
        if full and identifier_map and hasattr(translator, "identifier_map"):
            translator.identifier_map.save(Path(identifier_map))
            click.echo(
                f"Saved identifier map: {len(translator.identifier_map)} identifiers "
                f"→ {identifier_map}",
                err=True,
            )

    except KeyError:
        # Language not supported
        available = _get_available_languages()
        click.echo(f"Error: Language '{target_lang}' not supported.", err=True)
        click.echo(f"Available languages: {', '.join(available)}", err=True)
        sys.exit(1)
    except TranslationError as e:
        click.echo(f"Translation error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


def _handle_stdin(
    translator: TokenTranslator,
    source_lang: str,
    target_lang: str,
    output: Optional[str],
):
    """Handle translation from stdin.

    Args:
        translator: Initialized TokenTranslator instance
        source_lang: Source language code
        target_lang: Target language code
        output: Optional output file path

    Raises:
        TranslationError: If translation fails
    """
    # Read from stdin
    source_code = sys.stdin.read()

    if not source_code.strip():
        click.echo("Error: No input received from stdin", err=True)
        sys.exit(1)

    # Translate
    translated_code = translator.translate_code(source_code, source_lang, target_lang)

    # Output
    if output:
        # Write to file
        output_file = Path(output)

        # Create parent directory if needed
        output_file.parent.mkdir(parents=True, exist_ok=True)

        output_file.write_text(translated_code, encoding="utf-8")
        click.echo(f"✓ Translated to {output}")
    else:
        # Write to stdout
        sys.stdout.write(translated_code)


def _handle_file(
    translator: TokenTranslator,
    input_path: str,
    source_lang: str,
    target_lang: str,
    output_path: Optional[str],
):
    """Handle single file translation.

    Args:
        translator: Initialized TokenTranslator instance
        input_path: Input file path
        source_lang: Source language code
        target_lang: Target language code
        output_path: Optional output file path

    Raises:
        TranslationError: If translation fails
    """
    input_file = Path(input_path)

    # Read source
    try:
        source_code = input_file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        click.echo(
            f"Error: Could not read {input_path} as UTF-8. "
            "Ensure the file is text-encoded.",
            err=True,
        )
        sys.exit(1)

    # Translate
    translated_code = translator.translate_code(source_code, source_lang, target_lang)

    # Determine output
    if output_path is None:
        # Write to stdout
        sys.stdout.write(translated_code)
    else:
        output_file = Path(output_path)

        # Create parent directory if needed
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write translated code
        try:
            output_file.write_text(translated_code, encoding="utf-8")
        except PermissionError:
            click.echo(f"Error: Permission denied writing to {output_path}", err=True)
            sys.exit(1)

        # Preserve file permissions (executable bit, etc.)
        try:
            shutil.copymode(input_file, output_file)
        except Exception:
            # If permission copying fails, continue anyway
            # (e.g., on Windows or with different filesystems)
            pass

        click.echo(f"✓ Translated {input_path} → {output_path}")


def _handle_directory(
    translator: TokenTranslator,
    input_dir: str,
    source_lang: str,
    target_lang: str,
    output_dir: Optional[str],
    checkpoint_path: Optional[str] = None,
):
    """Handle recursive directory translation.

    Args:
        translator: Initialized TokenTranslator instance
        input_dir: Input directory path
        source_lang: Source language code
        target_lang: Target language code
        output_dir: Optional output directory path

    Raises:
        TranslationError: If translation fails
    """
    input_path = Path(input_dir)

    # Find all .py files recursively
    py_files = list(input_path.rglob("*.py"))

    if not py_files:
        click.echo(f"Warning: No .py files found in {input_dir}")
        return

    # Determine output directory
    if output_dir is None:
        # Create parallel directory with _translated suffix
        output_path = Path(f"{input_dir}_translated")
    else:
        output_path = Path(output_dir)

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)

    # Load checkpoint (completed files to skip)
    completed_files: set[str] = set()
    if checkpoint_path and Path(checkpoint_path).exists():
        completed_files = set(
            Path(checkpoint_path).read_text(encoding="utf-8").strip().splitlines()
        )
        if completed_files:
            click.echo(
                f"Resuming: {len(completed_files)} files already completed",
                err=True,
            )

    # Translate each file
    success_count = 0
    error_count = 0
    skipped_count = 0

    for i, py_file in enumerate(py_files, 1):
        # Calculate relative path
        rel_path = py_file.relative_to(input_path)
        output_file = output_path / rel_path

        # Skip if already completed (checkpoint resume)
        if str(rel_path) in completed_files:
            skipped_count += 1
            continue

        # Create output directory for this file
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Show progress
        click.echo(f"[{i}/{len(py_files)}] Translating {rel_path}...", nl=False)

        try:
            # Read source
            source_code = py_file.read_text(encoding="utf-8")

            # Translate
            translated_code = translator.translate_code(
                source_code, source_lang, target_lang
            )

            # Write output
            output_file.write_text(translated_code, encoding="utf-8")

            # Preserve permissions
            try:
                shutil.copymode(py_file, output_file)
            except Exception:
                # If permission copying fails, continue anyway
                pass

            click.echo(" ✓")
            success_count += 1

            # Save checkpoint after each successful file
            if checkpoint_path:
                with open(checkpoint_path, "a", encoding="utf-8") as cp:
                    cp.write(str(rel_path) + "\n")

        except UnicodeDecodeError:
            click.echo(" ✗ Error: Could not decode as UTF-8", err=True)
            error_count += 1
            continue
        except TranslationError as e:
            click.echo(f" ✗ Error: {e}", err=True)
            error_count += 1
            continue
        except Exception as e:
            click.echo(f" ✗ Unexpected error: {e}", err=True)
            error_count += 1
            continue

    # Summary
    total = len(py_files)
    click.echo(f"\n✓ Translated {success_count}/{total} files")
    if skipped_count > 0:
        click.echo(f"  Skipped {skipped_count} (already completed)")
    if error_count > 0:
        click.echo(f"✗ {error_count} files failed", err=True)
        sys.exit(1)


def _get_available_languages() -> list[str]:
    """Get list of available language codes.

    Returns:
        List of available language codes (e.g., ['en', 'es', 'ar'])
    """
    try:
        # Try to get from TokenTranslator if available
        return TokenTranslator.list_available_languages()
    except AttributeError:
        # Fallback to languages.json metadata
        langs = _load_languages_metadata()
        if langs:
            return sorted(langs.keys())
        return ["en", "es", "ar", "hi"]
