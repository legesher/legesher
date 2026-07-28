"""Tests for the CORE-1371 client-shape emitter (emit_js_client_pack.py)."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
SEEDER = SCRIPTS_DIR / "seed_js_terms.py"
EMITTER = SCRIPTS_DIR / "emit_js_client_pack.py"


def run_emit(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(EMITTER), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class TestEmitAgainstRealDb:
    """The committed DB carries the ratified selections — emit from it."""

    def test_emits_the_full_pack(self, tmp_path: Path) -> None:
        out = tmp_path / "ar.ts"
        result = run_emit("--out", str(out), "--source-commit", "TESTCOMMIT")
        assert result.returncode == 0, result.stderr
        text = out.read_text(encoding="utf-8")
        assert "GENERATED FILE — DO NOT EDIT" in text
        assert "@ legesher-next TESTCOMMIT" in text
        assert "const AR_PACK: LanguagePack" in text
        assert "locale: 'ar'," in text
        assert "target: 'javascript'," in text
        assert "direction: 'rtl'," in text
        assert "numeralSystem: 'arab'," in text
        assert "stability: 'experimental'," in text
        assert "while: 'طالما'," in text
        # 62 term lines + 6 metadata lines carry a ": '" value
        assert len(re.findall(r": '", text)) == 68
        for partition in ("keywords", "builtins", "members"):
            assert f"{partition}: Object.freeze({{" in text
        assert text.endswith("export default AR_PACK;\n")

    def test_emit_is_deterministic(self, tmp_path: Path) -> None:
        first, second = tmp_path / "a.ts", tmp_path / "b.ts"
        assert run_emit("--out", str(first), "--source-commit", "X").returncode == 0
        assert run_emit("--out", str(second), "--source-commit", "X").returncode == 0
        assert first.read_bytes() == second.read_bytes()


class TestEmitFailLoud:
    def test_unregistered_language_fails(self, tmp_path: Path) -> None:
        result = run_emit(
            "--out",
            str(tmp_path / "x.ts"),
            "--db-path",
            str(tmp_path / "empty.db"),
        )
        assert result.returncode != 0
        assert "not in the languages registry" in result.stderr

    def test_seeded_but_unselected_never_emits_partial(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        seeded = subprocess.run(
            [sys.executable, str(SEEDER), "--db-path", str(db_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert seeded.returncode == 0
        from legesher_i18n.db.database import TranslationDatabase

        db = TranslationDatabase(db_path=str(db_path))
        try:
            conn = db._get_connection()
            conn.execute(
                "INSERT OR IGNORE INTO languages"
                " (code, name, native_name, direction, numeral_system)"
                " VALUES ('ar', 'Arabic', 'العربية', 'rtl', 'arabic_indic')"
            )
            conn.commit()
        finally:
            db.close()
        out = tmp_path / "ar.ts"
        result = run_emit("--out", str(out), "--db-path", str(db_path))
        assert result.returncode != 0
        assert "unselected" in result.stderr
        assert not out.exists()
