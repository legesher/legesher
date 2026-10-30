#!/usr/bin/env python3
"""Validate showcase hello_world examples against shipped packs (CORE-1403).

The preview repository showcases one `hello_world.py` per language
(`languages/<lang>/hello_world.py`, including the `en` canonical). Pack
edits happen in THIS repo, so a pack change can silently break those
examples. For every example whose language has a shipped Python pack,
this gate:

1. builds the pack's EN→<lang> translator via
   ``create_translator_from_language_pack("python", <lang>)`` and calls
   ``.reverse()`` on it (the same construction ``GitFilter`` uses for its
   clean filter), then
2. reverse-translates the example to canonical English and requires the
   result to ``ast.parse``.

An example token the pack no longer maps survives reverse translation
untouched and surfaces as a parse failure for that language.

Examples-root resolution, in priority order:

1. ``--examples-root`` CLI argument
2. ``LEGESHER_PREVIEW_ROOT`` environment variable

Nothing else is searched: the checkout is never guessed from a directory
name. If neither is given, or the path given is not a directory: with
``--skip-if-missing`` (the pre-commit mode, so contributors without the
showcase examples checkout aren't blocked) print a notice and exit 0;
otherwise exit 2 with a message naming ``LEGESHER_PREVIEW_ROOT``.

Coverage mismatches are warnings, not failures: an example with no
shipped pack cannot be validated, and a pack with no example is a
showcase gap. ``--strict-coverage`` promotes missing examples for
existing packs to failures.

Usage (repo root):
    LEGESHER_PREVIEW_ROOT=/path/to/preview-checkout \\
        uv run python libs/i18n/scripts/validate_showcase_examples.py
    uv run python libs/i18n/scripts/validate_showcase_examples.py \\
        --examples-root /path/to/preview-checkout
    uv run python libs/i18n/scripts/validate_showcase_examples.py \\
        --skip-if-missing --quiet    # pre-commit mode

Exit codes:
    0 — every validated example reverse-translates and parses
        (or examples root missing under --skip-if-missing)
    1 — at least one language regressed (or strict-coverage miss)
    2 — examples root not found (without --skip-if-missing)
"""

import argparse
import ast
import os
import sys
from dataclasses import dataclass
from pathlib import Path


# Environment variable naming the showcase examples checkout
EXAMPLES_ROOT_ENV = "LEGESHER_PREVIEW_ROOT"

# Layout inside the preview repository checkout
EXAMPLES_SUBDIR = "languages"
EXAMPLE_FILENAME = "hello_world.py"

CANONICAL_LANGUAGE = "en"
PROGRAMMING_LANGUAGE = "python"


@dataclass
class Finding:
    """One per-language validation failure."""

    language: str
    kind: str  # "pack_error" | "translate_error" | "parse_error" | "missing_example"
    message: str

    def render(self) -> str:
        return f"FAIL [{self.language}] {self.kind}: {self.message}"


def resolve_examples_root(cli_value: str | None) -> Path | None:
    """Resolve the showcase examples checkout root.

    Priority: CLI arg > ``LEGESHER_PREVIEW_ROOT`` env var. Nothing else is
    searched, so no path is derived from a repository's name. Returns None
    when neither is set or the chosen path is not a directory.
    """
    value = cli_value or os.environ.get(EXAMPLES_ROOT_ENV)
    if not value:
        return None
    candidate = Path(value)
    return candidate if candidate.is_dir() else None


def discover_examples(examples_root: Path) -> dict[str, Path]:
    """Map language code -> hello_world.py path under <root>/languages/."""
    languages_dir = examples_root / EXAMPLES_SUBDIR
    if not languages_dir.is_dir():
        return {}

    examples: dict[str, Path] = {}
    for lang_dir in sorted(languages_dir.iterdir()):
        example = lang_dir / EXAMPLE_FILENAME
        if lang_dir.is_dir() and example.is_file():
            examples[lang_dir.name] = example
    return examples


def pack_languages() -> set[str]:
    """Language codes with a shipped Python pack (includes 'en')."""
    from legesher_i18n import LanguagePackLoader

    loader = LanguagePackLoader()
    return {code for code, _ in loader.list_available_languages(PROGRAMMING_LANGUAGE)}


def validate_language(language: str, example_path: Path) -> Finding | None:
    """Reverse-translate one example to canonical English and ast.parse it.

    Returns a Finding on failure, None on success.
    """
    from legesher_core.language_interface import create_translator_from_language_pack

    try:
        en_to_local = create_translator_from_language_pack(
            programming_language=PROGRAMMING_LANGUAGE,
            natural_language=language,
        )
        local_to_en = en_to_local.reverse()
    except Exception as exc:  # noqa: BLE001 — any engine failure is a finding
        return Finding(language, "pack_error", f"{type(exc).__name__}: {exc}")

    source = example_path.read_text(encoding="utf-8")
    try:
        canonical = local_to_en.translate_code(source, language, CANONICAL_LANGUAGE)
    except Exception as exc:  # noqa: BLE001 — any engine failure is a finding
        return Finding(language, "translate_error", f"{type(exc).__name__}: {exc}")

    try:
        ast.parse(canonical, filename=str(example_path))
    except SyntaxError as exc:
        return Finding(
            language,
            "parse_error",
            f"reverse-translated example does not parse: line {exc.lineno}: {exc.msg}",
        )
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--examples-root",
        help="Path to the preview repository checkout that holds the "
        "showcase examples (default: $LEGESHER_PREVIEW_ROOT)",
    )
    parser.add_argument(
        "--skip-if-missing",
        action="store_true",
        help="Exit 0 with a notice when the examples root does not exist "
        "(pre-commit mode; default is exit 2)",
    )
    parser.add_argument(
        "--strict-coverage",
        action="store_true",
        help="Treat a shipped pack with no showcase example as a failure "
        "(default: warning)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Only print failures and the final summary",
    )
    args = parser.parse_args(argv)

    examples_root = resolve_examples_root(args.examples_root)
    if examples_root is None:
        wanted = args.examples_root or os.environ.get(EXAMPLES_ROOT_ENV)
        if wanted:
            reason = f"showcase examples root not found: {wanted}"
        else:
            reason = (
                f"no showcase examples checkout given: {EXAMPLES_ROOT_ENV} "
                "is not set and --examples-root was not passed"
            )
        if args.skip_if_missing:
            print(f"NOTICE: {reason}; skipping showcase validation.")
            return 0
        print(f"ERROR: {reason}")
        print(
            f"Set {EXAMPLES_ROOT_ENV} to the preview repository checkout or "
            "pass --examples-root (or use --skip-if-missing)."
        )
        return 2

    examples = discover_examples(examples_root)
    packs = pack_languages()

    findings: list[Finding] = []
    warnings: list[str] = []
    validated = 0
    passed = 0

    # Coverage: examples without a pack / packs without an example
    for language in sorted(set(examples) - packs):
        warnings.append(
            f"warning: example '{language}' has no shipped {PROGRAMMING_LANGUAGE} "
            "pack — skipped"
        )
    for language in sorted(packs - set(examples)):
        if args.strict_coverage:
            findings.append(
                Finding(
                    language,
                    "missing_example",
                    f"shipped pack has no showcase {EXAMPLE_FILENAME} "
                    "(--strict-coverage)",
                )
            )
        else:
            warnings.append(
                f"warning: pack '{language}' is missing a showcase {EXAMPLE_FILENAME}"
            )

    # Validation: every language with both a pack and an example
    for language in sorted(set(examples) & packs):
        validated += 1
        finding = validate_language(language, examples[language])
        if finding is None:
            passed += 1
            if not args.quiet:
                print(f"ok   [{language}] {examples[language].name}")
        else:
            findings.append(finding)

    if not args.quiet:
        for warning in warnings:
            print(warning)
    for finding in findings:
        print(finding.render())

    print(
        f"showcase examples: {passed}/{validated} passed, "
        f"{len(findings)} failure(s), {len(warnings)} warning(s) "
        f"(examples root: {examples_root})"
    )
    if validated == 0 and packs:
        # An examples root with nothing to validate (empty placeholder
        # dir, partial clone) must not read as a green blocking gate —
        # treat it exactly like a missing root.
        print(
            f"notice: examples root {examples_root} contains no validatable "
            "examples; nothing was checked"
        )
        return 0 if args.skip_if_missing else 2
    if findings:
        print(
            "hint: failures in languages you did not touch usually mean a "
            "stale preview repository checkout; pull it and re-run "
            "(see libs/i18n/docs/quality-gates.md, showcase-gate detail)"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
