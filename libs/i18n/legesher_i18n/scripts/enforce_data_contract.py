#!/usr/bin/env python3
"""Enforce the "packs are data, not code" contract over the pack tree (CORE-1453).

Two layers per pack file:

1. **File-level** (pre-merge, so a child cannot hide behind a clean parent):
   size cap, data-only YAML (no tags, no anchors/aliases), top-level key
   allowlist, http(s)-only metadata URLs — see
   :mod:`legesher_i18n.data_contract`.
2. **Map-level** (post-merge, the pack a consumer actually gets):
   render-vs-execute round-trip — the localized surface must map back to
   the canonical form byte-identically. Python targets check the flat
   namespace (CPython tokenizes flat, CORE-710); member-bearing targets
   check per partition (CORE-1582).

Exits non-zero on any finding: every check here is a safety property, so
there is no advisory tier. Registered as the ``enforce-pack-data-contract``
pre-commit hook; org GitHub Actions are disabled, so pre-commit/local runs
are the executing gate (see libs/i18n/docs/quality-gates.md).

Usage::

    python -m legesher_i18n.scripts.enforce_data_contract              # all python packs
    python -m legesher_i18n.scripts.enforce_data_contract --lang es    # one language
    python -m legesher_i18n.scripts.enforce_data_contract --target javascript
    python -m legesher_i18n.scripts.enforce_data_contract --quiet      # summary only
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from legesher_i18n.data_contract import check_map_roundtrip, enforce_file_contract
from legesher_i18n.pack_loader import LanguagePackLoader
from legesher_i18n.schema_validator import Finding
from legesher_i18n.scripts.audit_packs import (
    _KNOWN_TARGETS,
    _PYTHON_GATE_TARGETS,
    _discover_pack_files,
    _language_packs_root,
)

_DEFAULT_TARGET = "python"


def _check_pack_file(
    loader: LanguagePackLoader, pack_file: Path, target: str
) -> list[Finding]:
    """Run file-level then map-level contract checks on one pack file."""
    findings = enforce_file_contract(pack_file)
    if findings:
        # A file that already violates the contract is not worth merging;
        # inheritance resolution would only re-report the same root cause.
        return findings

    try:
        merged, _chain = loader._resolve_inheritance(pack_file, set())
    except Exception as exc:  # noqa: BLE001 — report, don't abort the run
        return [
            Finding(
                severity="error",
                code="load-error",
                location=str(pack_file),
                message=f"{type(exc).__name__}: {exc}",
            )
        ]

    return check_map_roundtrip(merged, flat=target in _PYTHON_GATE_TARGETS)


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns a process exit code (0 == clean)."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lang",
        default=None,
        help="Check only this language code (e.g. 'es'). Default: all packs.",
    )
    parser.add_argument(
        "--target",
        default=_DEFAULT_TARGET,
        choices=_KNOWN_TARGETS,
        help="Programming-language target to check (default: python).",
    )
    parser.add_argument(
        "--root",
        default=None,
        help=(
            "Override the language-packs/<target> root directory "
            "(testing seam; default: the in-repo tree)."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print only the summary, not per-finding detail.",
    )
    args = parser.parse_args(argv)

    root = Path(args.root) if args.root else _language_packs_root(args.target)
    if not root.exists():
        print(f"language-packs root not found: {root}", file=sys.stderr)
        return 2

    pack_files = _discover_pack_files(root, args.lang, args.target)
    if not pack_files:
        print(f"No pack files found under {root}", file=sys.stderr)
        return 2

    loader = LanguagePackLoader()
    all_findings: list[Finding] = []
    for pack_file in pack_files:
        findings = _check_pack_file(loader, pack_file, args.target)
        all_findings.extend(findings)
        if findings and not args.quiet:
            for finding in findings:
                print(
                    f"  [{finding.severity}] {finding.code} "
                    f"{finding.location}: {finding.message}"
                )

    print("\n--- Data-contract summary (CORE-1453) ---")
    print(f"Pack files checked: {len(pack_files)}")
    print(f"Findings: {len(all_findings)}")

    return 1 if all_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
