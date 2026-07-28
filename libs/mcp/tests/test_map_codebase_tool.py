"""map_existing_codebase: the per-file legibility report."""

from __future__ import annotations

from typing import Any

import pytest
from mcp import ClientSession

import legesher_mcp.engine as engine_mod
from tests.conftest import assert_sanitized, call_err, call_ok

pytestmark = pytest.mark.anyio

GOOD = "def add(a, b):\n    return a + b\n"
USES_PRINT = "def report(x):\n    print(x)\n"
BROKEN = "def f(:\n"


async def test_report_over_mixed_files(client: ClientSession) -> None:
    result = await call_ok(
        client,
        "map_existing_codebase",
        {
            "files": [
                {"path": "src/add.py", "source": GOOD},
                {"path": "src/broken.py", "source": BROKEN},
            ],
            "target_lang": "fr",
        },
    )
    by_path = {f["path"]: f for f in result["files"]}
    assert by_path["src/add.py"]["translatable"] is True
    assert by_path["src/add.py"]["construct_counts"] == {"keywords": 2}
    assert by_path["src/broken.py"]["translatable"] is False
    assert by_path["src/broken.py"]["issue"]
    summary = result["summary"]
    assert summary["files_total"] == 2
    assert summary["files_translatable"] == 1
    assert summary["constructs_found"] == 2  # def, return
    assert summary["constructs_mapped"] == 2
    assert summary["coverage_ratio"] == 1.0
    assert summary["pivoted"] is False
    assert result["translated_files"] is None  # report only, by default


async def test_include_translations_returns_translated_files(
    client: ClientSession,
) -> None:
    result = await call_ok(
        client,
        "map_existing_codebase",
        {
            "files": [{"path": "add.py", "source": GOOD}],
            "target_lang": "es",
            "include_translations": True,
        },
    )
    (translated,) = result["translated_files"]
    assert translated["path"] == "add.py"
    assert "definir add(a, b):" in translated["translated_source"]


async def test_unmapped_constructs_are_reported(
    client: ClientSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Simulate a partial pack (all shipped packs are currently complete):
    a construct without a target-pack entry must be surfaced, not hidden."""
    real = engine_mod.LocalEngine.pack_categories

    def partial(pack: Any) -> dict[str, dict[str, str]]:
        categories = real(pack)
        if pack.language == "es":
            categories["builtins"].pop("print", None)
        return categories

    monkeypatch.setattr(engine_mod.LocalEngine, "pack_categories", staticmethod(partial))
    result = await call_ok(
        client,
        "map_existing_codebase",
        {"files": [{"path": "report.py", "source": USES_PRINT}], "target_lang": "es"},
    )
    (entry,) = result["files"]
    assert entry["unmapped_constructs"] == ["print"]
    summary = result["summary"]
    assert summary["unmapped_constructs"] == ["print"]
    assert summary["constructs_found"] == 2  # def, print
    assert summary["constructs_mapped"] == 1
    assert summary["coverage_ratio"] == pytest.approx(1 / 2)


async def test_repo_wide_x_to_y_mapping_pivots(client: ClientSession) -> None:
    native = await call_ok(client, "translate_to_native", {"source": GOOD, "target_lang": "es"})
    result = await call_ok(
        client,
        "map_existing_codebase",
        {
            "files": [{"path": "add.py", "source": native["translated_source"]}],
            "source_lang": "es",
            "target_lang": "fr",
        },
    )
    assert result["summary"]["pivoted"] is True
    assert result["summary"]["files_translatable"] == 1


async def test_lexable_but_invalid_syntax_is_annotated(client: ClientSession) -> None:
    """Missing colon lexes fine (translatable) but fails compile → issue."""
    result = await call_ok(
        client,
        "map_existing_codebase",
        {
            "files": [{"path": "odd.py", "source": "def f()\n    pass\n"}],
            "target_lang": "es",
        },
    )
    (entry,) = result["files"]
    assert entry["translatable"] is True
    assert entry["issue"] is not None
    assert entry["issue"].startswith("syntax:")


async def test_empty_file_list_is_rejected(client: ClientSession) -> None:
    message = await call_err(client, "map_existing_codebase", {"files": [], "target_lang": "es"})
    assert_sanitized(message)


async def test_unknown_target_language_is_a_clean_error(client: ClientSession) -> None:
    message = await call_err(
        client,
        "map_existing_codebase",
        {"files": [{"path": "a.py", "source": GOOD}], "target_lang": "xx"},
    )
    assert "unsupported_language" in message
    assert_sanitized(message)
