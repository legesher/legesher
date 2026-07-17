"""Target-gating of the audit gates (CORE-1372).

Two checks in ``validate_pack_strict`` are Python-specific and must not run
against a non-Python target:

* the CPython-XID min-interpreter check (a CPython Unicode-version trap), and
* the cross-partition collision pass (CPython ``tokenize`` dispatches flat;
  JavaScript's acorn AST is category-aware, so cross-partition homonyms are
  legal — D4).

These tests assert both the engine toggles (``validate_pack_strict`` /
``_strict_duplicate_findings``) and the audit script's target plumbing
(``audit_packs``' packs root, discovery glob, and per-file gating). Fixtures are
synthetic — they assert gate *behaviour*, not the state of any shipped pack.
"""

from __future__ import annotations

from types import SimpleNamespace

from legesher_i18n.schema_validator import LanguagePackSchema, SchemaValidator
from legesher_i18n.scripts import audit_packs

# A character that only became a valid identifier char in CPython 3.13
# (Unicode 13.0 XID). Pulled from the validator's own set so the test tracks it.
_XID_313_ONLY = next(iter(SchemaValidator._XID_ONLY_FROM_CPYTHON_313))


def _schema(**sections: object) -> LanguagePackSchema:
    return LanguagePackSchema.model_construct(
        language=sections.get("language", "en"),
        target=sections.get("target", "python"),
        version=sections.get("version", "3.10"),
        extends=None,
        keywords=sections.get("keywords", {}),
        builtins=sections.get("builtins", {}),
        exceptions=sections.get("exceptions", {}),
        reserved_words=sections.get("reserved_words", {}),
        operators={},
        standard_library={},
        cultural_notes=[],
        metadata=None,
    )


def _codes(findings) -> list[str]:
    return [f.code for f in findings]


class TestCrossSectionToggle:
    """``run_cross_section`` gates only the cross-partition pass."""

    def test_cross_section_runs_by_default(self) -> None:
        schema = _schema(
            builtins={"len": "shared"},
            reserved_words={"self": "shared"},
        )
        findings = SchemaValidator._strict_duplicate_findings(schema)
        assert any(
            f.code == "duplicate-target" and "multiple sections" in f.message
            for f in findings
        )

    def test_cross_section_suppressed_when_off(self) -> None:
        schema = _schema(
            builtins={"len": "shared"},
            reserved_words={"self": "shared"},
        )
        findings = SchemaValidator._strict_duplicate_findings(
            schema, include_cross_section=False
        )
        assert not any("multiple sections" in f.message for f in findings)

    def test_intra_section_duplicates_still_run_when_cross_off(self) -> None:
        # In-partition reversibility (Rule 2) applies to every target, so a
        # duplicate *within* a partition is still an error even for JS.
        schema = _schema(keywords={"if": "same", "while": "same"})
        findings = SchemaValidator._strict_duplicate_findings(
            schema, include_cross_section=False
        )
        assert any(
            f.code == "duplicate-target" and "is reused" in f.message for f in findings
        )


class TestMinInterpreterToggle:
    """``run_min_interpreter`` gates the CPython-XID check."""

    def test_min_interpreter_runs_by_default(self) -> None:
        schema = _schema(version="3.10", builtins={"len": f"x{_XID_313_ONLY}"})
        findings = SchemaValidator.validate_pack_strict(schema, "en")
        assert "min-interpreter-xid" in _codes(findings)

    def test_min_interpreter_suppressed_when_off(self) -> None:
        schema = _schema(version="3.10", builtins={"len": f"x{_XID_313_ONLY}"})
        findings = SchemaValidator.validate_pack_strict(
            schema, "en", run_min_interpreter=False
        )
        assert "min-interpreter-xid" not in _codes(findings)


class TestAuditPackFileTargetGating:
    """``_audit_pack_file`` runs the Python-only gates only for python."""

    def _pack(self) -> SimpleNamespace:
        # Both a cross-partition homonym and a 3.13-only XID char.
        return SimpleNamespace(
            language="en",
            target="python",
            version="3.10",
            keywords={},
            builtins={"len": "shared"},
            exceptions={},
            reserved_words={"self": "shared", "cls": f"y{_XID_313_ONLY}"},
            metadata=None,
        )

    def test_python_target_flags_both(self) -> None:
        loader = SimpleNamespace(load=lambda *a, **k: self._pack())
        pack_path = audit_packs._language_packs_root("python") / "en/x/packs/3.10.yml"
        _lang, _version, findings = audit_packs._audit_pack_file(
            loader, pack_path, "python"
        )
        codes = _codes(findings)
        assert "min-interpreter-xid" in codes
        assert any(
            f.code == "duplicate-target" and "multiple sections" in f.message
            for f in findings
        )

    def test_javascript_target_skips_both(self) -> None:
        loader = SimpleNamespace(load=lambda *a, **k: self._pack())
        pack_path = (
            audit_packs._language_packs_root("javascript") / "en/x/packs/3.10.yml"
        )
        _lang, _version, findings = audit_packs._audit_pack_file(
            loader, pack_path, "javascript"
        )
        codes = _codes(findings)
        assert "min-interpreter-xid" not in codes
        assert not any("multiple sections" in f.message for f in findings)


class TestPacksRootAndDiscovery:
    """The packs root and discovery glob follow ``--target``."""

    def test_root_is_target_scoped(self) -> None:
        assert audit_packs._language_packs_root("python").name == "python"
        assert audit_packs._language_packs_root("javascript").name == "javascript"
        # Default preserves python.
        assert audit_packs._language_packs_root().name == "python"

    def test_discovery_glob_matches_target_package_dir(self, tmp_path) -> None:
        # A JS-named package dir is discovered for the javascript target...
        js = tmp_path / "es" / "legesher_i18n_javascript_es" / "packs"
        js.mkdir(parents=True)
        (js / "es2022.yml").write_text("", encoding="utf-8")
        # ...and a python-named one under the same root is not.
        py = tmp_path / "fr" / "legesher_i18n_python_fr" / "packs"
        py.mkdir(parents=True)
        (py / "3.10.yml").write_text("", encoding="utf-8")

        found = audit_packs._discover_pack_files(tmp_path, None, "javascript")
        names = {p.name for p in found}
        assert names == {"es2022.yml"}
