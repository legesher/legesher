import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
DOCS = SCRIPTS.parent


def test_cli_emits_json_css_and_langs(tmp_path):
    subprocess.run(
        [sys.executable, str(SCRIPTS / "generate_snippets.py"),
         "--snippets", str(DOCS / "snippets"), "--out", str(tmp_path)],
        check=True,
    )
    data = json.loads((tmp_path / "snippets" / "hello-world.json").read_text())
    assert set(data["variants"]) >= {"en", "es", "ar"}
    assert data["variants"]["ar"]["rtl"] is True
    assert data["variants"]["es"]["code"].startswith("definir ")
    langs = json.loads((tmp_path / "snippet-langs.json").read_text())
    assert langs[0]["code"] == "en" and len(langs) == 51
    css = (tmp_path / "legesher-snippets.css").read_text()
    assert 'html[data-snippet-lang="es"]' in css
    assert ".lg-code pre[data-lang]" in css


def test_invalid_snippet_fails_build(tmp_path):
    bad = tmp_path / "snippets_src"
    bad.mkdir()
    (bad / "broken.py").write_text("def broken(:\n")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "generate_snippets.py"),
         "--snippets", str(bad), "--out", str(tmp_path / "out")],
        capture_output=True, text=True,
    )
    assert proc.returncode != 0
    assert "broken.py" in proc.stderr
