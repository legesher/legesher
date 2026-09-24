"""The MCP scan gate must fail on findings AND on a vacuous pass (CORE-1423).

The scanner itself exits ``0`` whether or not it found anything, so the gate
is the only thing standing between a poisoned tool description and a green
check. The second family of tests is the one that earns its keep: a report
with nothing in it, or one where every entry was skipped, is the shape a
broken scanner produces, and it must not read as "clean".

Run with:  uv run pytest scripts/tests -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gate_mcp_scan import evaluate, main  # noqa: E402


def _entry(name: str, *, safe: bool = True, status: str = "completed", **extra):
    return {
        "status": status,
        "is_safe": safe,
        "tool_name": name,
        "findings": extra.get("findings", {}),
    }


def _report(*entries, analyzers=("yara",)):
    return {
        "server_url": "static",
        "requested_analyzers": list(analyzers),
        "scan_results": list(entries),
    }


class TestClean:
    def test_all_safe_passes(self) -> None:
        code, lines = evaluate(_report(_entry("a"), _entry("b")))
        assert code == 0
        assert any("PASS" in line for line in lines)
        assert any("scanned 2 item(s)" in line for line in lines)

    def test_a_skipped_entry_alongside_real_ones_still_passes(self) -> None:
        code, lines = evaluate(_report(_entry("a"), _entry("r", status="skipped")))
        assert code == 0
        assert any("1 skipped" in line for line in lines)


class TestFindings:
    def test_an_unsafe_entry_fails_and_is_named(self) -> None:
        flagged = _entry(
            "translate_to_native",
            safe=False,
            findings={
                "yara_analyzer": {
                    "severity": "HIGH",
                    "threat_names": ["PROMPT INJECTION", "CREDENTIAL HARVESTING"],
                }
            },
        )
        code, lines = evaluate(_report(_entry("ok"), flagged))
        assert code == 1
        body = "\n".join(lines)
        assert "translate_to_native" in body
        assert "HIGH" in body
        assert "PROMPT INJECTION" in body

    @pytest.mark.parametrize("value", [False, None, "yes", 0])
    def test_anything_but_true_is_unsafe(self, value) -> None:
        # Fail closed: only an explicit `is_safe: true` is a pass, so a
        # report shape the scanner changes cannot quietly become green.
        entry = {"status": "completed", "is_safe": value, "tool_name": "t"}
        assert evaluate(_report(entry))[0] == 1


class TestVacuousPass:
    """A gate that cannot tell "clean" from "did not run" is not a gate."""

    def test_no_results_fails(self) -> None:
        code, lines = evaluate(_report())
        assert code == 1
        assert "did not run" in "\n".join(lines)

    def test_every_entry_skipped_fails(self) -> None:
        code, lines = evaluate(
            _report(_entry("a", status="skipped"), _entry("b", status="skipped"))
        )
        assert code == 1
        assert "nothing was analyzed" in "\n".join(lines)

    def test_missing_scan_results_key_fails(self) -> None:
        assert evaluate({"server_url": "static"})[0] == 1

    @pytest.mark.parametrize("report", [None, [], "clean", 0])
    def test_a_non_object_report_fails(self, report) -> None:
        assert evaluate(report)[0] == 1


class TestCli:
    def test_reads_a_report_file(self, tmp_path: Path) -> None:
        path = tmp_path / "report.json"
        path.write_text(json.dumps(_report(_entry("a"))), encoding="utf-8")
        assert main(["gate", str(path)]) == 0

    def test_a_missing_file_fails_rather_than_passing(self, tmp_path: Path) -> None:
        assert main(["gate", str(tmp_path / "nope.json")]) == 1

    def test_unparseable_json_fails(self, tmp_path: Path) -> None:
        path = tmp_path / "report.json"
        path.write_text("not json", encoding="utf-8")
        assert main(["gate", str(path)]) == 1

    def test_wrong_arity_is_a_usage_error(self) -> None:
        assert main(["gate"]) == 2
