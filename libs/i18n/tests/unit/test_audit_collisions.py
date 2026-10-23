"""Tests for the ``audit_collisions.py`` CI script.

CORE-950 Round 2 Copilot review: ``audit_packs()`` previously did
``if not pack.exists(): continue`` which silently swallowed missing
packs. If a pack dir was accidentally removed/renamed, the audit
would still report success on the smaller surviving set. The fix
derives the expected pack list from ``languages.json`` (the canonical
registry) and fails when an expected pack is missing.

These tests exercise the contract by monkey-patching the script's
internal ``_expected_pack_codes`` so failure cases are reproducible
without touching the real registry.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))


@pytest.fixture
def audit_module():
    """Re-import the script fresh for each test (lets us patch
    module-level helpers without bleeding state across tests)."""
    import importlib

    import audit_collisions

    importlib.reload(audit_collisions)
    return audit_collisions


class TestExpectedPackEnforcement:
    def test_missing_expected_pack_fails_audit(
        self, audit_module, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If an expected language code has no pack file on disk, the
        audit must return False (Copilot review on PR #237).
        """
        # Real codes that exist on disk + one fake.
        monkeypatch.setattr(
            audit_module,
            "_expected_pack_codes",
            lambda: ["en", "es", "DEFINITELY_NOT_A_REAL_CODE"],
        )

        assert audit_module.audit_packs() is False, (
            "audit_packs() must fail when an expected pack is missing"
        )

    def test_all_expected_packs_present_passes(
        self, audit_module, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sanity: when every expected code has a real pack and packs
        are clean, audit returns True. Uses a small subset to keep the
        test fast.
        """
        monkeypatch.setattr(
            audit_module,
            "_expected_pack_codes",
            lambda: ["en", "es", "fr"],
        )

        assert audit_module.audit_packs() is True

    def test_empty_expected_list_fails(
        self, audit_module, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If we can't read languages.json (corrupt, missing), the
        audit must NOT silently pass with zero packs audited -- the
        whole point of the Copilot fix is that empty surfaces shouldn't
        look like clean ones.
        """
        monkeypatch.setattr(
            audit_module,
            "_expected_pack_codes",
            lambda: [],
        )

        assert audit_module.audit_packs() is False

    def test_expected_codes_come_from_languages_json(self, audit_module) -> None:
        """The default ``_expected_pack_codes`` must read from
        ``languages.json``. If anyone refactors it to glob the dir
        instead, the regression-protection contract breaks.
        """
        codes = audit_module._expected_pack_codes()
        # 52 supported languages (languages.json).
        assert len(codes) == 52, f"Expected 52 codes, got {len(codes)}"
        # Spot-checks against known entries.
        for required in ("en", "es", "ar", "ur", "zh", "ja"):
            assert required in codes, f"{required} missing from registry"


class TestTargetGating:
    """The cross-section pack layer is Python-specific (CORE-1372)."""

    def test_non_python_target_skips_pack_layer(
        self, audit_module, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A target without a cross-section profile skips the pack layer and
        passes — acorn-style targets are category-aware, so cross-partition
        homonyms are legal. The skip is logged, never silent, and must not
        touch ``_expected_pack_codes`` (there are no JS packs on disk yet).
        """

        def _boom() -> list[str]:
            raise AssertionError("pack layer must not run for a non-python target")

        monkeypatch.setattr(audit_module, "_expected_pack_codes", _boom)

        assert audit_module.audit_packs(target="javascript") is True

    def test_default_target_is_python(self, audit_module) -> None:
        """Calling with no target preserves the Python behaviour (all 51
        packs audited, zero collisions)."""
        assert audit_module.audit_packs() is True
        assert audit_module.audit_packs(target="python") is True
