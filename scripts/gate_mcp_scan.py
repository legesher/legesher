"""Turn an MCP scanner report into a CI gate (CORE-1423).

``mcp-scanner`` (Cisco AI Defense's open scanner) prints findings and then
exits ``0`` whether or not it found any — verified against v4.8.x, including
a deliberately poisoned tool description that it correctly flagged HIGH and
still exited zero on. A job that only runs the scanner is therefore not a
gate; it is a log line. This script is the gate.

Two failure conditions, and the second matters as much as the first:

1. **Any item the scanner judged unsafe.** Printed with its analyzer,
   severity, and threat names, then a non-zero exit.
2. **Nothing was actually scanned.** A report whose every entry is
   ``skipped`` — or which has no entries at all — is a green light that
   checked nothing. A scanner that silently stopped working must not read
   as a pass.

Usage::

    mcp-scanner --analyzers yara --format raw static --tools tools.json \\
        > report.json
    uv run python scripts/gate_mcp_scan.py report.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

#: Report entries carry the scanned item's name under one of these keys,
#: depending on what was scanned. Used for the failure message only.
_NAME_KEYS = ("tool_name", "prompt_name", "resource_uri", "name")

#: The scanner marks an entry it did not actually analyze this way.
_SKIPPED = "skipped"


def _name(entry: dict[str, Any]) -> str:
    for key in _NAME_KEYS:
        value = entry.get(key)
        if isinstance(value, str) and value:
            return value
    return "<unnamed>"


def _describe(entry: dict[str, Any]) -> str:
    findings = entry.get("findings")
    if not isinstance(findings, dict) or not findings:
        return "(no analyzer detail)"
    parts = []
    for analyzer, detail in sorted(findings.items()):
        if not isinstance(detail, dict):
            continue
        severity = detail.get("severity", "?")
        threats = detail.get("threat_names") or []
        parts.append(
            f"{analyzer}={severity} {', '.join(str(t) for t in threats)}".strip()
        )
    return "; ".join(parts) or "(no analyzer detail)"


def evaluate(report: Any) -> tuple[int, list[str]]:
    """``(exit_code, lines)`` for one parsed scanner report."""
    lines: list[str] = []
    if not isinstance(report, dict):
        return 1, ["scan report is not a JSON object"]
    results = report.get("scan_results")
    if not isinstance(results, list) or not results:
        return 1, ["scan report contains no results — the scan did not run"]

    completed = [
        e for e in results if isinstance(e, dict) and e.get("status") != _SKIPPED
    ]
    skipped = len(results) - len(completed)
    unsafe = [e for e in completed if e.get("is_safe") is not True]

    if not completed:
        return 1, [
            f"every one of the {len(results)} report entries was {_SKIPPED} — "
            "nothing was analyzed, so this is not a pass"
        ]

    lines.append(
        f"scanned {len(completed)} item(s)"
        + (f", {skipped} skipped" if skipped else "")
        + f", analyzers: {', '.join(report.get('requested_analyzers') or ['?'])}"
    )
    if unsafe:
        lines.append(f"FAIL: {len(unsafe)} item(s) flagged")
        lines.extend(f"  - {_name(entry)}: {_describe(entry)}" for entry in unsafe)
        return 1, lines
    lines.append("PASS: no findings")
    return 0, lines


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: gate_mcp_scan.py <scanner-report.json>", file=sys.stderr)
        return 2
    path = Path(argv[1])
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"could not read the scan report: {type(exc).__name__}", file=sys.stderr)
        return 1
    code, lines = evaluate(report)
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
