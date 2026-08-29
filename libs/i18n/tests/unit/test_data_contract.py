"""Tests for the "packs are data, not code" contract layer (CORE-1453).

Covers the file-level contract checks (size cap, data-only YAML, top-level
key allowlist, metadata URL schemes), the map-layer round-trip check, the
trust-tier metadata field, and the loader-side enforcement points.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from legesher_i18n.data_contract import (
    MAX_PACK_FILE_BYTES,
    check_file_size,
    check_map_roundtrip,
    check_metadata_urls,
    check_top_level_keys,
    check_yaml_data_only,
    enforce_file_contract,
)
from legesher_i18n.pack_loader import LanguagePackLoader, PackValidationError
from legesher_i18n.schema_validator import LanguagePackMetadata, SchemaValidator

MINIMAL_PACK = """\
language: es
target: python
version: "3.10"
keywords:
  if: si_kw
builtins:
  print: imprimir
metadata:
  author: Legesher Team
  license: MIT
"""


def _write(tmp_path: Path, content: str, name: str = "3.10.yml") -> Path:
    pack = tmp_path / name
    pack.write_text(content, encoding="utf-8")
    return pack


class TestFileSizeCap:
    def test_rejects_oversized_pack_file(self, tmp_path: Path) -> None:
        pack = _write(tmp_path, MINIMAL_PACK + "#" + "x" * MAX_PACK_FILE_BYTES)
        findings = check_file_size(pack)
        assert len(findings) == 1
        assert findings[0].severity == "error"
        assert findings[0].code == "file-size"

    def test_accepts_normal_pack_file(self, tmp_path: Path) -> None:
        pack = _write(tmp_path, MINIMAL_PACK)
        assert check_file_size(pack) == []

    def test_loader_refuses_oversized_pack(self, tmp_path: Path) -> None:
        packs_dir = tmp_path / "legesher_i18n_python_xx" / "packs"
        packs_dir.mkdir(parents=True)
        pack = packs_dir / "3.10.yml"
        pack.write_text(
            MINIMAL_PACK + "#" + "x" * MAX_PACK_FILE_BYTES, encoding="utf-8"
        )
        loader = LanguagePackLoader()
        with pytest.raises(PackValidationError, match="size"):
            loader._resolve_inheritance(pack, set())


class TestDataOnlyYaml:
    def test_rejects_custom_tag(self, tmp_path: Path) -> None:
        pack = _write(
            tmp_path,
            MINIMAL_PACK + 'extra_field: !!python/object/apply:os.system ["true"]\n',
        )
        codes = [f.code for f in check_yaml_data_only(pack)]
        assert "yaml-tag" in codes

    def test_rejects_local_tag(self, tmp_path: Path) -> None:
        pack = _write(tmp_path, MINIMAL_PACK + "extra_field: !custom value\n")
        codes = [f.code for f in check_yaml_data_only(pack)]
        assert "yaml-tag" in codes

    def test_rejects_anchor_and_alias(self, tmp_path: Path) -> None:
        pack = _write(
            tmp_path,
            'language: es\ntarget: python\nversion: "3.10"\n'
            "keywords: &k\n  if: si_kw\nbuiltins: *k\n",
        )
        codes = [f.code for f in check_yaml_data_only(pack)]
        assert "yaml-anchor" in codes

    def test_accepts_plain_pack(self, tmp_path: Path) -> None:
        pack = _write(tmp_path, MINIMAL_PACK)
        assert check_yaml_data_only(pack) == []

    def test_unparseable_yaml_is_an_error_not_a_crash(self, tmp_path: Path) -> None:
        pack = _write(tmp_path, "language: [unclosed\n")
        findings = check_yaml_data_only(pack)
        assert findings and findings[0].severity == "error"


class TestTopLevelKeys:
    def test_rejects_unknown_key(self, tmp_path: Path) -> None:
        pack = _write(tmp_path, MINIMAL_PACK + "on_load: print(1)\n")
        findings = check_top_level_keys(pack)
        assert len(findings) == 1
        assert findings[0].code == "unknown-key"
        assert "on_load" in findings[0].message

    def test_accepts_all_schema_keys(self, tmp_path: Path) -> None:
        pack = _write(tmp_path, MINIMAL_PACK + "implicit_params:\n  self: yo\n")
        assert check_top_level_keys(pack) == []

    def test_schema_rejects_unknown_top_level_key(self, tmp_path: Path) -> None:
        # Runtime enforcement, independent of the gate script: the pydantic
        # schema itself must fail closed on executable-shaped extras.
        with pytest.raises(PackValidationError):
            SchemaValidator.validate_pack(
                {
                    "language": "es",
                    "target": "python",
                    "version": "3.10",
                    "on_load": "print(1)",
                },
                tmp_path / "3.10.yml",
            )


class TestMetadataUrls:
    def test_rejects_non_http_scheme(self, tmp_path: Path) -> None:
        pack = _write(
            tmp_path,
            MINIMAL_PACK.replace(
                "author: Legesher Team", "author: see javascript://alert(1)"
            ),
        )
        findings = check_metadata_urls(pack)
        assert len(findings) == 1
        assert findings[0].code == "url-scheme"

    def test_rejects_file_scheme(self, tmp_path: Path) -> None:
        pack = _write(
            tmp_path,
            MINIMAL_PACK.replace("author: Legesher Team", "author: file:///etc/passwd"),
        )
        assert [f.code for f in check_metadata_urls(pack)] == ["url-scheme"]

    def test_accepts_https_url(self, tmp_path: Path) -> None:
        pack = _write(
            tmp_path,
            MINIMAL_PACK.replace(
                "author: Legesher Team", "author: https://github.com/legesher"
            ),
        )
        assert check_metadata_urls(pack) == []

    def test_accepts_url_free_metadata(self, tmp_path: Path) -> None:
        pack = _write(tmp_path, MINIMAL_PACK)
        assert check_metadata_urls(pack) == []

    def test_pydantic_metadata_rejects_non_http_url(self) -> None:
        with pytest.raises(ValueError, match="scheme"):
            LanguagePackMetadata(author="file:///etc/passwd")


class TestMapRoundtrip:
    def test_detects_cross_partition_shadowing(self) -> None:
        pack = {
            "keywords": {"if": "ako"},
            "builtins": {"print": "ako"},
            "exceptions": {},
            "implicit_params": {},
        }
        findings = check_map_roundtrip(pack, flat=True)
        assert len(findings) == 1
        assert findings[0].severity == "error"
        assert findings[0].code == "roundtrip"

    def test_detects_inconsistent_duplicate_source(self) -> None:
        pack = {
            "keywords": {"if": "ako"},
            "builtins": {"if": "wenn"},
            "exceptions": {},
            "implicit_params": {},
        }
        findings = check_map_roundtrip(pack, flat=True)
        assert [f.code for f in findings] == ["roundtrip"]

    def test_soft_keyword_divergence_is_legal(self) -> None:
        # `type` is a soft keyword (the 3.12 alias statement) AND a builtin;
        # the engine dispatches contextually, so divergent surfaces round-trip
        # fine — every shipped pack does this (22 languages).
        pack = {
            "keywords": {"type": "tipus_"},
            "builtins": {"type": "tipus"},
            "exceptions": {},
            "implicit_params": {},
        }
        assert check_map_roundtrip(pack, flat=True) == []

    def test_soft_keyword_shadowing_still_blocks(self) -> None:
        # The exemption covers divergent surfaces for one canonical term,
        # never two canonical terms sharing one surface.
        pack = {
            "keywords": {"type": "tip"},
            "builtins": {"id": "tip"},
            "exceptions": {},
            "implicit_params": {},
        }
        findings = check_map_roundtrip(pack, flat=True)
        assert [f.code for f in findings] == ["roundtrip"]

    def test_clean_pack_roundtrips(self) -> None:
        pack = {
            "keywords": {"if": "si_kw", "for": "para"},
            "builtins": {"print": "imprimir"},
            "exceptions": {"ValueError": "ErrorDeValor"},
            "implicit_params": {"self": "yo"},
        }
        assert check_map_roundtrip(pack, flat=True) == []

    def test_per_partition_mode_allows_cross_partition_homonyms(self) -> None:
        # JS members: one native word may serve several receivers across
        # partitions (CORE-1582); only in-partition bijectivity is required.
        pack = {
            "keywords": {"if": "ako"},
            "members": {"length": "ako"},
        }
        assert check_map_roundtrip(pack, flat=False) == []


class TestTrustTier:
    def test_review_status_defaults_experimental(self) -> None:
        assert LanguagePackMetadata().review_status == "experimental"

    def test_review_status_accepts_ladder_stages(self) -> None:
        for stage in ("experimental", "reviewed", "official"):
            assert LanguagePackMetadata(review_status=stage).review_status == stage

    def test_review_status_rejects_unknown_stage(self) -> None:
        with pytest.raises(ValueError):
            LanguagePackMetadata(review_status="totally-legit")

    def test_strict_load_warns_on_unofficial_pack(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        loader = LanguagePackLoader()
        with caplog.at_level(logging.WARNING, logger="legesher_i18n.pack_loader"):
            loader.load("es", "python", "3.10", strict=True)
        assert any("official" in rec.message for rec in caplog.records)

    def test_default_load_stays_quiet(self, caplog: pytest.LogCaptureFixture) -> None:
        loader = LanguagePackLoader()
        with caplog.at_level(logging.WARNING, logger="legesher_i18n.pack_loader"):
            loader.load("es", "python", "3.10")
        assert not [rec for rec in caplog.records if "official" in rec.message]


class TestGateScript:
    def _tmp_tree(self, tmp_path: Path, pack_body: str) -> Path:
        packs = tmp_path / "xx" / "legesher_i18n_python_xx" / "packs"
        packs.mkdir(parents=True)
        (packs / "3.10.yml").write_text(pack_body, encoding="utf-8")
        return tmp_path

    def test_main_clean_on_shipped_packs(self) -> None:
        from legesher_i18n.scripts.enforce_data_contract import main

        assert main(["--quiet"]) == 0

    def test_main_fails_on_contract_violation(self, tmp_path: Path) -> None:
        from legesher_i18n.scripts.enforce_data_contract import main

        root = self._tmp_tree(tmp_path, MINIMAL_PACK + "on_load: boom\n")
        assert main(["--root", str(root), "--quiet"]) == 1

    def test_main_fails_on_roundtrip_shadowing(self, tmp_path: Path) -> None:
        from legesher_i18n.scripts.enforce_data_contract import main

        shadowed = MINIMAL_PACK.replace(
            "builtins:\n  print: imprimir", "builtins:\n  print: si_kw"
        )
        root = self._tmp_tree(tmp_path, shadowed)
        assert main(["--root", str(root), "--quiet"]) == 1

    def test_main_clean_on_valid_tmp_tree(self, tmp_path: Path) -> None:
        from legesher_i18n.scripts.enforce_data_contract import main

        root = self._tmp_tree(tmp_path, MINIMAL_PACK)
        assert main(["--root", str(root), "--quiet"]) == 0


class TestEnforceFileContract:
    def test_aggregates_all_file_level_findings(self, tmp_path: Path) -> None:
        pack = _write(
            tmp_path,
            MINIMAL_PACK.replace("author: Legesher Team", "author: ftp://x")
            + "on_load: boom\n",
        )
        codes = {f.code for f in enforce_file_contract(pack)}
        assert codes == {"unknown-key", "url-scheme"}

    def test_clean_pack_has_no_findings(self, tmp_path: Path) -> None:
        pack = _write(tmp_path, MINIMAL_PACK)
        assert enforce_file_contract(pack) == []


class TestUrlSchemeNoSlashes:
    # javascript:/data:/vbscript: URIs never use '//' — the canonical forms
    # of exactly the schemes this gate exists to block (post-merge review
    # finding, 2026-08-09).
    def test_rejects_javascript_scheme_without_slashes(self, tmp_path: Path) -> None:
        pack = _write(
            tmp_path,
            MINIMAL_PACK.replace(
                "author: Legesher Team", "author: see javascript:alert(1)"
            ),
        )
        assert [f.code for f in check_metadata_urls(pack)] == ["url-scheme"]

    def test_rejects_data_uri(self, tmp_path: Path) -> None:
        pack = _write(
            tmp_path,
            MINIMAL_PACK.replace(
                "author: Legesher Team", 'author: "data:text/html;base64,PHNjcmlwdD4="'
            ),
        )
        assert [f.code for f in check_metadata_urls(pack)] == ["url-scheme"]

    def test_prose_colon_with_space_is_not_a_url(self, tmp_path: Path) -> None:
        pack = _write(
            tmp_path,
            MINIMAL_PACK.replace(
                "author: Legesher Team", 'author: "Contact: the Legesher Team"'
            ),
        )
        assert check_metadata_urls(pack) == []

    def test_pydantic_rejects_javascript_scheme_without_slashes(self) -> None:
        from legesher_i18n.schema_validator import LanguagePackMetadata

        with pytest.raises(ValueError, match="scheme"):
            LanguagePackMetadata(author="javascript:alert(document.cookie)")
