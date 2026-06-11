#!/usr/bin/env python3
"""Audit every shipped language pack with the Unicode/script safety layer.

Walks ``libs/i18n/language-packs/python/{lang}/.../packs/*.yml``, loads each
pack with full inheritance resolution, and runs
:meth:`SchemaValidator.validate_pack_strict` over the merged result. Findings
are grouped by language and by finding-code, printed as a readable report, and
the process exits non-zero when any finding is present.

This is the engine behind the ``validate-packs`` CI job. While the shipped
packs still contain known data defects (foreign-script bleed-through, NFKC
instability, etc.), the CI job runs this in **non-blocking** (``continue-on-
error``) mode — the report is informational until the data-correction PRs land.

Usage::

    python -m legesher_i18n.scripts.audit_packs            # audit all packs
    python -m legesher_i18n.scripts.audit_packs --lang si  # one language
    python -m legesher_i18n.scripts.audit_packs --quiet    # summary only
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

from legesher_i18n.pack_loader import LanguagePackLoader
from legesher_i18n.schema_validator import (
    Finding,
    LanguagePackSchema,
    SchemaValidator,
)


def _language_packs_root() -> Path:
    """Return the ``language-packs/python`` directory in the working tree."""
    # This file lives at libs/i18n/legesher_i18n/scripts/audit_packs.py;
    # the packs live at libs/i18n/language-packs/python.
    return Path(__file__).resolve().parents[2] / "language-packs" / "python"


def _discover_pack_files(root: Path, lang_filter: str | None) -> list[Path]:
    """Return every concrete pack YAML under *root*, optionally filtered.

    Skips the top-level ``version-index.yml`` and any non-pack YAML; only files
    living inside a ``packs/`` directory are returned.
    """
    files: list[Path] = []
    for path in sorted(root.glob("*/legesher_i18n_python_*/packs/*.yml")):
        lang = path.parents[2].name
        if lang_filter and lang != lang_filter:
            continue
        files.append(path)
    return files


def _audit_pack_file(
    loader: LanguagePackLoader, pack_file: Path
) -> tuple[str, str, list[Finding]]:
    """Load + audit one pack file. Returns (lang, version, findings).

    Loads through the inheritance-resolving loader so the audit sees the merged
    pack a consumer would actually get. A load failure (malformed YAML, missing
    parent) is surfaced as a single ``load-error`` finding rather than crashing
    the whole run.
    """
    lang = pack_file.parents[2].name
    version = pack_file.stem  # e.g. "3.13" or "default"

    try:
        pack = loader.load(lang, "python", None if version == "default" else version)
    except Exception as exc:  # noqa: BLE001 — report, don't abort the run
        return (
            lang,
            version,
            [
                Finding(
                    severity="error",
                    code="load-error",
                    location=str(pack_file),
                    message=f"{type(exc).__name__}: {exc}",
                )
            ],
        )

    # ``validate_pack_strict`` wants a LanguagePackSchema. Build one via
    # ``model_construct`` from the already-merged pack, *bypassing* Pydantic's
    # ``validate_mappings``: that legacy validator's ``str.isidentifier`` check
    # is interpreter-version-dependent and would reject legitimate ZWJ-bearing
    # Sinhala values before the deterministic safety layer ever sees them. The
    # safety layer is the authority here.
    schema = LanguagePackSchema.model_construct(
        language=pack.language,
        target=pack.target,
        version=pack.version,
        extends=None,
        keywords=dict(pack.keywords),
        builtins=dict(pack.builtins),
        exceptions=dict(pack.exceptions),
        reserved_words=dict(pack.reserved_words),
        operators={},
        standard_library={},
        cultural_notes=[],
        metadata=pack.metadata,
    )
    findings = SchemaValidator.validate_pack_strict(schema, lang)
    return lang, version, findings


def _print_report(results: list[tuple[str, str, list[Finding]]], quiet: bool) -> int:
    """Print the grouped report and return the total finding count."""
    by_lang: dict[str, list[tuple[str, Finding]]] = defaultdict(list)
    code_counter: Counter[str] = Counter()
    total = 0

    for lang, version, findings in results:
        for finding in findings:
            by_lang[lang].append((version, finding))
            code_counter[finding.code] += 1
            total += 1

    if not quiet:
        for lang in sorted(by_lang):
            print(f"\n=== {lang} ({len(by_lang[lang])} findings) ===")
            for version, finding in sorted(
                by_lang[lang],
                key=lambda vf: (vf[0], vf[1].code, vf[1].location, vf[1].message),
            ):
                print(
                    f"  [{finding.severity}] {finding.code} "
                    f"({lang} {version}) {finding.location}: {finding.message}"
                )

    print("\n--- Audit summary ---")
    print(f"Packs audited: {len(results)}")
    print(f"Languages with findings: {len(by_lang)}")
    print(f"Total findings: {total}")
    if code_counter:
        print("By code:")
        for code, count in code_counter.most_common():
            print(f"  {code}: {count}")

    return total


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns a process exit code (0 == clean)."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lang",
        default=None,
        help="Audit only this language code (e.g. 'si'). Default: all packs.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only the summary, not per-finding detail.",
    )
    args = parser.parse_args(argv)

    root = _language_packs_root()
    if not root.exists():
        print(f"language-packs root not found: {root}", file=sys.stderr)
        return 2

    pack_files = _discover_pack_files(root, args.lang)
    if not pack_files:
        print(f"No pack files found under {root}", file=sys.stderr)
        return 2

    loader = LanguagePackLoader()
    results = [_audit_pack_file(loader, pf) for pf in pack_files]
    total = _print_report(results, args.quiet)

    # Non-zero exit on findings so CI can gate on it (the workflow currently
    # runs this with continue-on-error until the data-correction PRs land).
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
