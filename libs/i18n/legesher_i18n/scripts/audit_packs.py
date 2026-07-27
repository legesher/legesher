#!/usr/bin/env python3
"""Audit every shipped language pack with the Unicode/script safety layer.

Walks ``libs/i18n/language-packs/{target}/{lang}/.../packs/*.yml`` for the
selected ``--target`` (default ``python``), loads each pack with full
inheritance resolution, and runs :meth:`SchemaValidator.validate_pack_strict`
over the merged result. Findings are grouped by language and by finding-code,
printed as a readable report, and the process exits non-zero when any finding
is present.

This is the engine behind the ``validate-packs`` CI job. The data-correction
PRs (CORE-1318) cleared every **error**, so the job now runs this **blocking**:
the process exits non-zero on any error (safety / correctness), while advisory
**warnings** (descriptions-as-terms, non-ASCII digits) are surfaced for native
review without failing CI.

Two of the aggregated checks are Python-specific and are switched off for
non-Python targets (CORE-1372): the CPython-XID min-interpreter check and the
cross-partition collision pass. See :data:`_PYTHON_GATE_TARGETS`. The remaining
per-target grammar (version tokens, identifier rules, partitions) is owned by
CORE-1503's per-target profiles.

Usage::

    python -m legesher_i18n.scripts.audit_packs                    # all python packs
    python -m legesher_i18n.scripts.audit_packs --lang si          # one language
    python -m legesher_i18n.scripts.audit_packs --target javascript
    python -m legesher_i18n.scripts.audit_packs --quiet            # summary only
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

# Targets whose packs run the Python-specific gates in ``validate_pack_strict``:
# the CPython-XID min-interpreter check (a CPython-only Unicode-version trap)
# and the cross-partition collision pass (CPython's ``tokenize`` dispatches
# flat, so a value shared across partitions round-trips to the wrong token —
# CORE-710). JavaScript's acorn AST is category-aware, so cross-partition
# homonyms are legal and neither gate applies. Interim seed for the per-target
# profiles formalised in CORE-1503.
_PYTHON_GATE_TARGETS: frozenset[str] = frozenset({"python"})

# Programming-language targets the audit knows how to walk. Kept in step with
# the on-disk ``language-packs/<target>`` layout.
_KNOWN_TARGETS: tuple[str, ...] = ("python", "javascript")

_DEFAULT_TARGET = "python"


def _language_packs_root(target: str = _DEFAULT_TARGET) -> Path:
    """Return the ``language-packs/<target>`` directory in the working tree."""
    # This file lives at libs/i18n/legesher_i18n/scripts/audit_packs.py;
    # the packs live at libs/i18n/language-packs/<target>.
    return Path(__file__).resolve().parents[2] / "language-packs" / target


def _discover_pack_files(
    root: Path, lang_filter: str | None, target: str = _DEFAULT_TARGET
) -> list[Path]:
    """Return every concrete pack YAML under *root*, optionally filtered.

    Skips the top-level ``version-index.yml`` and any non-pack YAML; only files
    living inside a ``packs/`` directory are returned.
    """
    files: list[Path] = []
    for path in sorted(root.glob(f"*/legesher_i18n_{target}_*/packs/*.yml")):
        lang = path.parents[2].name
        if lang_filter and lang != lang_filter:
            continue
        files.append(path)
    return files


def _audit_pack_file(
    loader: LanguagePackLoader,
    pack_file: Path,
    target: str = _DEFAULT_TARGET,
) -> tuple[str, str, list[Finding]]:
    """Load + audit one pack file. Returns (lang, version, findings).

    Loads through the inheritance-resolving loader so the audit sees the merged
    pack a consumer would actually get. A load failure (malformed YAML, missing
    parent) is surfaced as a single ``load-error`` finding rather than crashing
    the whole run. The Python-only gates run only when *target* is in
    :data:`_PYTHON_GATE_TARGETS`.
    """
    lang = pack_file.parents[2].name
    version = pack_file.stem  # e.g. "3.13" or "default"
    python_gates = target in _PYTHON_GATE_TARGETS

    try:
        # enforce_min_interpreter=False: the auditor inspects the raw pack
        # (it has its own check_min_interpreter_identifier); it must see the
        # 3.13-only Sinhala values rather than have the loader refuse them.
        pack = loader.load(
            lang,
            target,
            None if version == "default" else version,
            enforce_min_interpreter=False,
        )
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
        # getattr: the audit seam accepts pack-like objects (tests pass duck-
        # typed stubs), and packs predating the members field audit as empty.
        members=dict(getattr(pack, "members", {}) or {}),
        operators={},
        standard_library={},
        cultural_notes=[],
        metadata=pack.metadata,
    )
    findings = SchemaValidator.validate_pack_strict(
        schema,
        lang,
        run_min_interpreter=python_gates,
        run_cross_section=python_gates,
    )
    return lang, version, findings


def _print_report(
    results: list[tuple[str, str, list[Finding]]], quiet: bool
) -> tuple[int, int]:
    """Print the grouped report and return ``(errors, warnings)``.

    Errors are BLOCKING (safety / correctness: foreign script, NFKC instability,
    keyword collisions, illegal format chars, min-interpreter traps, duplicate
    targets, invalid identifiers). Warnings are ADVISORY quality signals
    (descriptions-as-terms, non-ASCII digits) that surface for native review but
    do not fail the gate.
    """
    by_lang: dict[str, list[tuple[str, Finding]]] = defaultdict(list)
    code_counter: Counter[str] = Counter()
    errors = 0
    warnings = 0

    for lang, version, findings in results:
        for finding in findings:
            by_lang[lang].append((version, finding))
            code_counter[finding.code] += 1
            if finding.severity == "error":
                errors += 1
            else:
                warnings += 1

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
    print(f"Blocking errors: {errors}")
    print(f"Advisory warnings: {warnings}")
    if code_counter:
        print("By code:")
        for code, count in code_counter.most_common():
            print(f"  {code}: {count}")

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns a process exit code (0 == clean)."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lang",
        default=None,
        help="Audit only this language code (e.g. 'si'). Default: all packs.",
    )
    parser.add_argument(
        "--target",
        default=_DEFAULT_TARGET,
        choices=_KNOWN_TARGETS,
        help=(
            "Programming-language target to audit (default: python). "
            "Non-Python targets skip the CPython-only gates."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only the summary, not per-finding detail.",
    )
    args = parser.parse_args(argv)

    root = _language_packs_root(args.target)
    if not root.exists():
        print(f"language-packs root not found: {root}", file=sys.stderr)
        return 2

    pack_files = _discover_pack_files(root, args.lang, args.target)
    if not pack_files:
        print(f"No pack files found under {root}", file=sys.stderr)
        return 2

    loader = LanguagePackLoader()
    results = [_audit_pack_file(loader, pf, args.target) for pf in pack_files]
    errors, _warnings = _print_report(results, args.quiet)

    # BLOCKING gate (CORE-1318): fail only on ERRORS. Advisory warnings
    # (descriptions-as-terms, non-ASCII digits) are surfaced for native review
    # but do not fail CI. The data-correction PRs cleared every error, so the
    # validate-packs workflow now runs this without continue-on-error.
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
