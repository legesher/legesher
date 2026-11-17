import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
DOCS = SCRIPTS.parent
REGISTRY = DOCS.parent / "libs" / "i18n" / "legesher_i18n" / "languages.json"


def _active_registry_codes() -> set[str]:
    # Read the registry file directly rather than through language_registry,
    # which is what the generator itself iterates.
    languages = json.loads(REGISTRY.read_text(encoding="utf-8"))["languages"]
    return {
        code
        for code, meta in languages.items()
        if meta["status"] in ("available", "experimental")
    }


def test_cli_emits_json_css_and_langs(tmp_path):
    subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "generate_snippets.py"),
            "--snippets",
            str(DOCS / "snippets"),
            "--out",
            str(tmp_path),
        ],
        check=True,
    )
    data = json.loads((tmp_path / "snippets" / "hello-world.json").read_text())
    assert set(data["variants"]) >= {"en", "es", "ar"}
    assert data["variants"]["ar"]["rtl"] is True
    assert data["variants"]["es"]["code"].startswith("definir ")
    langs = json.loads((tmp_path / "snippet-langs.json").read_text())
    codes = [entry["code"] for entry in langs]
    assert codes[0] == "en"
    duplicated = sorted({code for code in codes if codes.count(code) > 1})
    assert not duplicated, duplicated
    assert set(codes) == _active_registry_codes()
    css = (tmp_path / "legesher-snippets.css").read_text()
    assert 'html[data-snippet-lang="es"]' in css
    assert ".lg-code pre[data-lang]" in css


def test_invalid_snippet_fails_build(tmp_path):
    bad = tmp_path / "snippets_src"
    bad.mkdir()
    (bad / "broken.py").write_text("def broken(:\n")
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "generate_snippets.py"),
            "--snippets",
            str(bad),
            "--out",
            str(tmp_path / "out"),
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "broken.py" in proc.stderr


sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "tests"))
from _story_fixtures import FIXTURES  # noqa: E402


def test_cli_emits_stories(tmp_path):
    subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "generate_snippets.py"),
            "--snippets",
            str(DOCS / "snippets"),
            "--out",
            str(tmp_path),
        ],
        check=True,
    )
    story = json.loads(
        (tmp_path / "stories" / "handle-errors-in-your-words.json").read_text(
            encoding="utf-8"
        )
    )
    assert story["variants"]["ar"]["copy_text"].startswith("تعريف اقسم(")
    assert story["variants"]["ar"]["output"].startswith("محاولة قسمة 10 على 2\n")
    assert (
        story["variants"]["ar"]["rtl"] is True
        and story["variants"]["ar"]["draft"] is True
    )
    assert set(story["variants"]) == _active_registry_codes()
    assert story["steps"][0] == ["type", None]
    assert set(story["title"]) == {"en", "es", "ar"}


def test_explicit_stories_dir_is_emitted(tmp_path):
    subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "generate_snippets.py"),
            "--snippets",
            str(DOCS / "snippets"),
            "--stories",
            str(FIXTURES),
            "--out",
            str(tmp_path),
        ],
        check=True,
    )
    emitted = sorted(p.name for p in (tmp_path / "stories").iterdir())
    assert emitted == ["ok-editor.json", "ok-playground.json"]
    editor = json.loads(
        (tmp_path / "stories" / "ok-editor.json").read_text(encoding="utf-8")
    )
    assert editor["reproduction"] is None
    assert all(v["output"] is None for v in editor["variants"].values())


def test_payload_reports_whether_the_record_is_current():
    from generate_snippets import load_packs
    from stories import (
        load_story,
        runs_on,
        story_payload,
        story_variants,
        variants_digest,
    )

    story = load_story(FIXTURES / "ok-playground")
    variants = story_variants(story, load_packs())
    record = {
        "story": story.id,
        "legesher": "0.25.1",
        "checked": "2026-11-17",
        "digest": variants_digest(variants),
        "python": ["3.12", "3.13"],
        "results": {
            "ar": {"3.12": "match", "3.13": "match"},
            "si": {"3.12": "match", "3.13": "error"},
        },
    }
    assert runs_on(record, "si") == ["3.12"] and runs_on(record, "xx") == []
    payload = story_payload(story, variants, record)
    assert payload["reproduction"] == {
        "legesher": "0.25.1",
        "checked": "2026-11-17",
        "current": True,
        "runs_on": {"ar": ["3.12", "3.13"], "si": ["3.12"]},
    }
    stale = story_payload(story, variants, {**record, "digest": "0" * 64})
    assert stale["reproduction"]["current"] is False
    assert story_payload(story, variants, None)["reproduction"] is None
