"""Tests for the pack-loader version path-traversal guard.

``LanguagePackLoader.load`` joins ``version`` directly into a pack filename
(``{version}.yml``), so an unvalidated value is a path-traversal primitive. The
guard rejects anything that isn't a bare ``X.Y`` version or ``"default"``,
*before* any filesystem access, raising ``ValueError``.
"""

from __future__ import annotations

import pytest

from legesher_i18n.pack_loader import LanguagePackLoader


class TestVersionTraversalGuard:
    """Reject malicious version strings before they hit disk."""

    @pytest.mark.parametrize(
        "bad_version",
        [
            "../../../../etc/passwd",
            "../3.10/../../secret",
            "3.10/../../../etc",
            "..",
            "/absolute/path",
            "3.10;rm -rf",
            "3",  # no minor
            "3.x",  # non-numeric minor
            "latest",
            "",  # empty string
        ],
    )
    def test_malicious_version_raises_value_error(self, bad_version: str) -> None:
        loader = LanguagePackLoader()
        with pytest.raises(ValueError, match="Invalid pack version"):
            loader.load("es", "python", bad_version)

    @pytest.mark.parametrize("good_version", ["3.10", "3.11", "3.13", "3.14"])
    def test_valid_version_passes_guard(self, good_version: str) -> None:
        # A well-formed version must clear the guard and load a real pack
        # (es ships 3.10-3.14). If the guard wrongly rejected it, this raises
        # ValueError instead of loading.
        loader = LanguagePackLoader()
        pack = loader.load("es", "python", good_version)
        assert pack.language == "es"
        assert pack.version == good_version

    def test_none_version_is_allowed(self) -> None:
        # version=None means "load default.yml"; the guard must not reject it.
        # es has no default.yml, so this raises PackNotFoundError — NOT
        # ValueError — proving the guard let None through.
        from legesher_i18n.exceptions import PackNotFoundError

        loader = LanguagePackLoader()
        with pytest.raises(PackNotFoundError):
            loader.load("es", "python", None)

    def test_default_literal_is_allowed_by_guard(self) -> None:
        # "default" clears the guard (it's a legal filename stem). es has no
        # default.yml so it still raises PackNotFoundError, proving the guard
        # admitted the literal rather than rejecting it with ValueError.
        from legesher_i18n.exceptions import PackNotFoundError

        loader = LanguagePackLoader()
        with pytest.raises(PackNotFoundError):
            loader.load("es", "python", "default")
