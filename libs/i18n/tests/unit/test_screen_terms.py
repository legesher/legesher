"""Tests for the term-screening sweep harness (CORE-401).

Covers term collection, the coverage digest, report/triage loading, and the
gate semantics: unscreened language, untriaged flag, stale digest, stale
triage entry.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "translate"))

import screen_terms  # noqa: E402

ES_PACK = {
    "language": "es",
    "target": "python",
    "version": "3.10",
    "keywords": {"if": "si_kw", "for": "para"},
    "builtins": {"print": "imprimir"},
}

AR_PACK = {
    "language": "ar",
    "target": "python",
    "version": "3.10",
    "keywords": {"if": "إذا"},
}


def _write_packs(tmp_path: Path, packs: dict[str, dict]) -> Path:
    root = tmp_path / "language-packs" / "python"
    for lang, data in packs.items():
        packs_dir = root / lang / f"legesher_i18n_python_{lang}" / "packs"
        packs_dir.mkdir(parents=True)
        with open(packs_dir / f"{data['version']}.yml", "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True)
    return root


def _write_report(
    reports_dir: Path,
    lang: str,
    digest: str,
    flags: list[dict] | None = None,
) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "language": lang,
        "target": "python",
        "screener": "test-screener",
        "screened_at": "2026-08-04",
        "coverage_digest": digest,
        "flags": flags or [],
    }
    path = reports_dir / f"{lang}.yml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(report, f, allow_unicode=True)
    return path


class TestCollectTerms:
    def test_collects_all_partitions_for_language(self, tmp_path: Path) -> None:
        root = _write_packs(tmp_path, {"es": ES_PACK})
        terms = screen_terms.collect_terms(root, lang_filter="es")
        assert set(terms) == {"es"}
        triples = set(terms["es"])
        assert ("keywords", "if", "si_kw") in triples
        assert ("builtins", "print", "imprimir") in triples

    def test_skips_english_reference_pack(self, tmp_path: Path) -> None:
        en = dict(ES_PACK, language="en")
        root = _write_packs(tmp_path, {"en": en, "es": ES_PACK})
        assert set(screen_terms.collect_terms(root)) == {"es"}

    def test_unions_across_version_files(self, tmp_path: Path) -> None:
        root = _write_packs(tmp_path, {"es": ES_PACK})
        extra = dict(ES_PACK, version="3.12", keywords={"match": "coincidir"})
        packs_dir = root / "es" / "legesher_i18n_python_es" / "packs"
        with open(packs_dir / "3.12.yml", "w", encoding="utf-8") as f:
            yaml.safe_dump(extra, f, allow_unicode=True)
        triples = set(screen_terms.collect_terms(root, lang_filter="es")["es"])
        assert ("keywords", "match", "coincidir") in triples
        assert ("keywords", "if", "si_kw") in triples


class TestCoverageDigest:
    def test_digest_is_stable_for_same_surface(self, tmp_path: Path) -> None:
        root = _write_packs(tmp_path, {"es": ES_PACK})
        terms = screen_terms.collect_terms(root, lang_filter="es")["es"]
        assert screen_terms.coverage_digest(terms) == screen_terms.coverage_digest(
            list(reversed(terms))
        )

    def test_digest_changes_when_surface_changes(self, tmp_path: Path) -> None:
        root = _write_packs(tmp_path, {"es": ES_PACK})
        d1 = screen_terms.coverage_digest(
            screen_terms.collect_terms(root, lang_filter="es")["es"]
        )
        changed = dict(ES_PACK, builtins={"print": "escribir"})
        root2 = _write_packs(tmp_path / "b", {"es": changed})
        d2 = screen_terms.coverage_digest(
            screen_terms.collect_terms(root2, lang_filter="es")["es"]
        )
        assert d1 != d2


class TestGate:
    def _digest_for(self, root: Path, lang: str) -> str:
        return screen_terms.coverage_digest(
            screen_terms.collect_terms(root, lang_filter=lang)[lang]
        )

    def test_missing_report_is_an_error(self, tmp_path: Path) -> None:
        root = _write_packs(tmp_path, {"es": ES_PACK})
        errors, _warnings = screen_terms.gate(
            root, tmp_path / "reports", tmp_path / "triage.yml"
        )
        assert any("es" in e and "report" in e.lower() for e in errors)

    def test_clean_report_passes(self, tmp_path: Path) -> None:
        root = _write_packs(tmp_path, {"es": ES_PACK})
        _write_report(tmp_path / "reports", "es", self._digest_for(root, "es"))
        errors, warnings = screen_terms.gate(
            root, tmp_path / "reports", tmp_path / "triage.yml"
        )
        assert errors == []
        assert warnings == []

    def test_untriaged_flag_is_an_error(self, tmp_path: Path) -> None:
        root = _write_packs(tmp_path, {"es": ES_PACK})
        flag = {
            "term": "si_kw",
            "english": "if",
            "partition": "keywords",
            "category": "unfortunate_connotation",
            "note": "test",
        }
        _write_report(tmp_path / "reports", "es", self._digest_for(root, "es"), [flag])
        errors, _warnings = screen_terms.gate(
            root, tmp_path / "reports", tmp_path / "triage.yml"
        )
        assert any("untriaged" in e.lower() for e in errors)

    def test_triaged_flag_passes(self, tmp_path: Path) -> None:
        root = _write_packs(tmp_path, {"es": ES_PACK})
        flag = {
            "term": "si_kw",
            "english": "if",
            "partition": "keywords",
            "category": "unfortunate_connotation",
            "note": "test",
        }
        _write_report(tmp_path / "reports", "es", self._digest_for(root, "es"), [flag])
        triage = {
            "es:keywords:if:si_kw": {
                "disposition": "accepted",
                "rationale": "native review pending; benign in context",
            }
        }
        triage_path = tmp_path / "triage.yml"
        triage_path.write_text(yaml.safe_dump(triage), encoding="utf-8")
        errors, _warnings = screen_terms.gate(root, tmp_path / "reports", triage_path)
        assert errors == []

    def test_stale_digest_is_an_error(self, tmp_path: Path) -> None:
        root = _write_packs(tmp_path, {"es": ES_PACK})
        _write_report(tmp_path / "reports", "es", "0" * 64)
        errors, _warnings = screen_terms.gate(
            root, tmp_path / "reports", tmp_path / "triage.yml"
        )
        assert any("digest" in e.lower() or "stale" in e.lower() for e in errors)

    def test_stale_triage_entry_is_a_warning_not_error(self, tmp_path: Path) -> None:
        root = _write_packs(tmp_path, {"es": ES_PACK})
        _write_report(tmp_path / "reports", "es", self._digest_for(root, "es"))
        triage = {"es:keywords:gone": {"disposition": "fixed", "rationale": "renamed"}}
        triage_path = tmp_path / "triage.yml"
        triage_path.write_text(yaml.safe_dump(triage), encoding="utf-8")
        errors, warnings = screen_terms.gate(root, tmp_path / "reports", triage_path)
        assert errors == []
        assert any("gone" in w for w in warnings)

    def test_lang_filter_limits_scope(self, tmp_path: Path) -> None:
        root = _write_packs(tmp_path, {"es": ES_PACK, "ar": AR_PACK})
        _write_report(tmp_path / "reports", "es", self._digest_for(root, "es"))
        errors, _warnings = screen_terms.gate(
            root, tmp_path / "reports", tmp_path / "triage.yml", lang_filter="es"
        )
        assert errors == []

    def test_malformed_report_fails_loudly(self, tmp_path: Path) -> None:
        root = _write_packs(tmp_path, {"es": ES_PACK})
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / "es.yml").write_text("flags: {not: [a, list\n", encoding="utf-8")
        with pytest.raises(SystemExit):
            screen_terms.gate(root, reports, tmp_path / "triage.yml")

    def test_invalid_disposition_fails_loudly(self, tmp_path: Path) -> None:
        root = _write_packs(tmp_path, {"es": ES_PACK})
        _write_report(tmp_path / "reports", "es", self._digest_for(root, "es"))
        triage_path = tmp_path / "triage.yml"
        triage_path.write_text(
            yaml.safe_dump({"es:keywords:if": {"disposition": "yolo"}}),
            encoding="utf-8",
        )
        with pytest.raises(SystemExit):
            screen_terms.gate(root, tmp_path / "reports", triage_path)


class TestMain:
    def test_gate_mode_exit_codes(self, tmp_path: Path) -> None:
        root = _write_packs(tmp_path, {"es": ES_PACK})
        digest = screen_terms.coverage_digest(
            screen_terms.collect_terms(root, lang_filter="es")["es"]
        )
        _write_report(tmp_path / "reports", "es", digest)
        argv = [
            "--gate",
            "--packs-dir",
            str(root),
            "--reports-dir",
            str(tmp_path / "reports"),
            "--triage",
            str(tmp_path / "triage.yml"),
        ]
        assert screen_terms.main(argv) == 0
        assert (
            screen_terms.main(
                [
                    "--gate",
                    "--packs-dir",
                    str(root),
                    "--reports-dir",
                    str(tmp_path / "empty"),
                    "--triage",
                    str(tmp_path / "triage.yml"),
                ]
            )
            == 1
        )

    def test_collect_mode_emits_json(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        import json

        root = _write_packs(tmp_path, {"es": ES_PACK})
        rc = screen_terms.main(["--collect", "--lang", "es", "--packs-dir", str(root)])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["es"]["coverage_digest"]
        assert {"partition": "keywords", "english": "if", "term": "si_kw"} in payload[
            "es"
        ]["terms"]


class TestTriageKeyIncludesSurface:
    # A regen can replace a flagged term with a DIFFERENT offensive word; an
    # acceptance recorded for the old surface must not green-light the new
    # one (post-merge review finding, 2026-08-09), so the triage key carries
    # the localized term.
    def test_flag_key_includes_localized_term(self) -> None:
        assert screen_terms.flag_key("es", "keywords", "if", "si_kw") == (
            "es:keywords:if:si_kw"
        )

    def test_old_surface_acceptance_does_not_cover_new_surface(
        self, tmp_path: Path
    ) -> None:
        root = _write_packs(tmp_path, {"es": ES_PACK})
        digest = screen_terms.coverage_digest(
            screen_terms.collect_terms(root, lang_filter="es")["es"]
        )
        flag = {
            "term": "si_kw",
            "english": "if",
            "partition": "keywords",
            "category": "profanity",
            "note": "test",
        }
        _write_report(tmp_path / "reports", "es", digest, [flag])
        triage = {
            "es:keywords:if:old_word": {
                "disposition": "accepted",
                "rationale": "about the OLD surface",
            }
        }
        triage_path = tmp_path / "triage.yml"
        triage_path.write_text(yaml.safe_dump(triage), encoding="utf-8")
        errors, warnings = screen_terms.gate(root, tmp_path / "reports", triage_path)
        assert any("untriaged" in e.lower() and "si_kw" in e for e in errors)
        assert any("old_word" in w for w in warnings)  # stale entry surfaced
