"""Tests for the CORE-1371 prep: JS term seeding + pipeline target wiring."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from legesher_i18n.db.database import TranslationDatabase

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
SEEDER = SCRIPTS_DIR / "seed_js_terms.py"
REAL_INDEX = (
    Path(__file__).parent.parent.parent / "context" / "javascript" / "index.json"
)


def run_seeder(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SEEDER), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class TestSeeder:
    def test_seeds_the_62_term_inventory(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        result = run_seeder("--db-path", str(db_path))
        assert result.returncode == 0, result.stderr
        db = TranslationDatabase(db_path=str(db_path))
        try:
            terms = db.get_terms(programming_language="javascript")
            assert len(terms) == 62
            by_category: dict[str, int] = {}
            for row in terms:
                by_category[row["category"]] = by_category.get(row["category"], 0) + 1
            assert by_category == {"keyword": 17, "builtin": 16, "member": 29}
            # Python rows untouched (fresh DB: zero before and after)
            assert db.get_terms(programming_language="python") == []
        finally:
            db.close()

    def test_refuses_to_reseed(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        assert run_seeder("--db-path", str(db_path)).returncode == 0
        second = run_seeder("--db-path", str(db_path))
        assert second.returncode != 0
        assert "refusing" in second.stderr

    def test_dry_run_writes_nothing(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        result = run_seeder("--db-path", str(db_path), "--dry-run")
        assert result.returncode == 0
        db = TranslationDatabase(db_path=str(db_path))
        try:
            assert db.get_terms(programming_language="javascript") == []
        finally:
            db.close()

    def test_drifted_corpus_fails_loudly(self, tmp_path: Path) -> None:
        index = json.loads(REAL_INDEX.read_text(encoding="utf-8"))
        index["documents"] = index["documents"][:-1]  # drop one term
        bad_index = tmp_path / "index.json"
        bad_index.write_text(json.dumps(index), encoding="utf-8")
        result = run_seeder(
            "--db-path", str(tmp_path / "test.db"), "--index-path", str(bad_index)
        )
        assert result.returncode != 0
        assert "drifted" in result.stderr


class TestPipelineTargetWiring:
    def test_config_defaults_to_python(self) -> None:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from translate.pipeline import PipelineConfig

        assert PipelineConfig().target == "python"

    def test_claude_model_threads_target_into_prompt_builder(self) -> None:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from translate.models.claude_model import ClaudeModel

        model = ClaudeModel(dry_run=True, target="javascript")
        assert model.target == "javascript"
        assert model._prompt_builder is not None
        system, _ = model._prompt_builder.build_identifier_prompt(
            identifiers=[{"text": "addTwo", "role": "function_name", "context": {}}],
            target_lang="ar",
            existing_glossary={},
        )
        assert "## Target Guide (JavaScript)" in system

    def test_db_inventory_feeds_term_selection(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        assert run_seeder("--db-path", str(db_path)).returncode == 0
        sys.path.insert(0, str(SCRIPTS_DIR))
        from translate.pipeline import PipelineConfig, TranslationPipeline

        config = PipelineConfig(
            models=["claude"],
            languages=["ar"],
            dry_run=True,
            output_db=db_path,
            target="javascript",
        )
        pipeline = TranslationPipeline(config)
        terms = pipeline._get_terms_to_translate()
        assert len(terms) == 62
        assert "of" in terms and "log" in terms and "console" in terms

    def test_unseeded_target_fails_loudly(self, tmp_path: Path) -> None:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from translate.pipeline import PipelineConfig, TranslationPipeline

        config = PipelineConfig(
            models=["claude"],
            languages=["ar"],
            dry_run=True,
            output_db=tmp_path / "empty.db",
            target="javascript",
        )
        pipeline = TranslationPipeline(config)
        with pytest.raises(ValueError, match="No terms seeded"):
            pipeline._get_terms_to_translate()
