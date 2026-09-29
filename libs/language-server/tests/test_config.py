"""Tests for configuration system."""

import logging
import sys

import pytest

from legesher_language_server.config import LanguageServerConfig


def test_default_config():
    """Test default configuration values."""
    config = LanguageServerConfig()

    assert config.source_language == "en"
    assert config.target_language == "en"
    assert config.python_version is None
    assert config.cache_size == 1000
    assert config.cache_ttl == 3600
    assert config.enhanced_intelligence_enabled is True
    assert config.log_level == "INFO"


def test_custom_config():
    """Test custom configuration values."""
    config = LanguageServerConfig(
        source_language="fr",
        target_language="de",
        python_version="3.11",
        cache_size=500,
        cache_ttl=1800,
    )

    assert config.source_language == "fr"
    assert config.target_language == "de"
    assert config.python_version == "3.11"
    assert config.cache_size == 500
    assert config.cache_ttl == 1800


def test_from_env(monkeypatch):
    """Test loading configuration from environment variables."""
    monkeypatch.setenv("LEGESHER_SOURCE_LANG", "pt")
    monkeypatch.setenv("LEGESHER_TARGET_LANG", "ja")
    monkeypatch.setenv("LEGESHER_PYTHON_VERSION", "3.12")
    monkeypatch.setenv("LEGESHER_CACHE_SIZE", "2000")
    monkeypatch.setenv("LEGESHER_CACHE_TTL", "7200")
    monkeypatch.setenv("LEGESHER_ENHANCED_INTELLIGENCE_ENABLED", "false")
    monkeypatch.setenv("LEGESHER_LOG_LEVEL", "DEBUG")

    config = LanguageServerConfig.from_env()

    assert config.source_language == "pt"
    assert config.target_language == "ja"
    assert config.python_version == "3.12"
    assert config.cache_size == 2000
    assert config.cache_ttl == 7200
    assert config.enhanced_intelligence_enabled is False
    assert config.log_level == "DEBUG"


def test_detect_python_version():
    """Test Python version detection."""
    # With explicit version
    config = LanguageServerConfig(python_version="3.10")
    assert config.detect_python_version() == "3.10"

    # Auto-detect
    config = LanguageServerConfig()
    detected = config.detect_python_version()
    expected = f"{sys.version_info.major}.{sys.version_info.minor}"
    assert detected == expected


def test_validate_languages():
    """Test language code validation."""
    # Valid codes
    config = LanguageServerConfig(source_language="en", target_language="es")
    assert config.validate_languages() is True

    # Invalid codes (too long)
    config = LanguageServerConfig(source_language="eng", target_language="es")
    assert config.validate_languages() is False

    # Invalid codes (contains numbers) - field validator rejects non-alphabetic codes
    with pytest.raises(ValueError):
        LanguageServerConfig(source_language="e1", target_language="es")


def test_cache_size_validation():
    """Test cache size must be positive."""
    with pytest.raises(ValueError):
        LanguageServerConfig(cache_size=0)

    with pytest.raises(ValueError):
        LanguageServerConfig(cache_size=-1)

    # Valid
    config = LanguageServerConfig(cache_size=1)
    assert config.cache_size == 1


def test_cache_ttl_validation():
    """Test cache TTL can be zero or positive."""
    # Zero is valid (no expiration)
    config = LanguageServerConfig(cache_ttl=0)
    assert config.cache_ttl == 0

    # Positive is valid
    config = LanguageServerConfig(cache_ttl=3600)
    assert config.cache_ttl == 3600

    # Negative is invalid
    with pytest.raises(ValueError):
        LanguageServerConfig(cache_ttl=-1)


class TestRetiredEnvironmentVariables:
    """Renaming a setting silently is its own kind of breakage (CORE-1890)."""

    def test_retired_enable_flag_is_reported(self, monkeypatch, caplog):
        """A leftover LEGESHER_PYLANCE_ENABLED must not be ignored in silence.

        The rename ships without aliases, which is defensible — nothing is
        published, so nothing can depend on the old names. What is not
        defensible is a user who set `LEGESHER_PYLANCE_ENABLED=false` quietly
        getting the feature switched back **on**, because the new key defaults
        to true. The setting is not honoured; it is at least announced.
        """
        monkeypatch.delenv("LEGESHER_ENHANCED_INTELLIGENCE_ENABLED", raising=False)
        monkeypatch.setenv("LEGESHER_PYLANCE_ENABLED", "false")

        with caplog.at_level(logging.WARNING):
            config = LanguageServerConfig.from_env()

        assert config.enhanced_intelligence_enabled is True, (
            "the retired variable should not be honoured — it is reported, not obeyed"
        )
        assert "LEGESHER_PYLANCE_ENABLED" in caplog.text, (
            "a retired setting was ignored without telling anyone"
        )
        assert "LEGESHER_ENHANCED_INTELLIGENCE_ENABLED" in caplog.text, (
            "the warning does not name the replacement"
        )

    def test_retired_path_variable_is_reported(self, monkeypatch, caplog):
        """A leftover LEGESHER_PYLANCE_PATH pin must not vanish quietly."""
        monkeypatch.delenv("LEGESHER_LANGUAGE_SERVER_PATH", raising=False)
        monkeypatch.setenv("LEGESHER_PYLANCE_PATH", "/somewhere/pyright-langserver")

        with caplog.at_level(logging.WARNING):
            config = LanguageServerConfig.from_env()

        assert config.language_server_path is None
        assert "LEGESHER_PYLANCE_PATH" in caplog.text
        assert "LEGESHER_LANGUAGE_SERVER_PATH" in caplog.text

    def test_no_warning_when_no_retired_variables_are_set(self, monkeypatch, caplog):
        """Guards the tests above: the warning must not fire unconditionally."""
        for name in ("LEGESHER_PYLANCE_ENABLED", "LEGESHER_PYLANCE_PATH"):
            monkeypatch.delenv(name, raising=False)

        with caplog.at_level(logging.WARNING):
            LanguageServerConfig.from_env()

        assert "LEGESHER_PYLANCE" not in caplog.text


def test_language_role_defaults():
    """The named role slots default to English like the rest (CORE-1760)."""
    config = LanguageServerConfig()

    assert config.file_language == "en"
    assert config.working_language == "en"


def test_language_role_validation():
    """The role slots get the same code validation as the original pair."""
    config = LanguageServerConfig(file_language="FA", working_language="PT")
    assert config.file_language == "fa"
    assert config.working_language == "pt"

    with pytest.raises(ValueError):
        LanguageServerConfig(working_language="../etc")
    with pytest.raises(ValueError):
        LanguageServerConfig(file_language="")


def test_validate_languages_covers_role_slots():
    """validate_languages() answers for every role, not just the old pair."""
    assert LanguageServerConfig(file_language="fa", working_language="pt").validate_languages()
    assert not LanguageServerConfig(working_language="por").validate_languages()


def test_legacy_target_language_seeds_roles_from_env(monkeypatch):
    """LEGESHER_TARGET_LANG stands for every role it used to mean (CORE-1760).

    Setting only target_language would leave file_language and
    working_language at "en" while the file is actually parsed as the chosen
    language — the lockstep this model advertises, silently broken.
    """
    monkeypatch.setenv("LEGESHER_TARGET_LANG", "ja")

    config = LanguageServerConfig.from_env()

    assert config.target_language == "ja"
    assert config.file_language == "ja"
    assert config.working_language == "ja"


def test_target_language_alone_seeds_the_file_language():
    """A config built through the deprecated slot is served in that language (CORE-1976).

    Providers now read each document's language and fall back to
    file_language, so a model constructed the old way, with target_language
    only, would otherwise be served in English with nothing to say so.
    """
    config = LanguageServerConfig(target_language="es")

    assert config.file_language == "es"


def test_file_language_alone_seeds_the_deprecated_slot():
    config = LanguageServerConfig(file_language="fa")

    assert config.target_language == "fa"


def test_both_language_slots_given_are_kept_as_given():
    config = LanguageServerConfig(target_language="es", file_language="fr")

    assert (config.target_language, config.file_language) == ("es", "fr")


def test_apply_legacy_target_language_keeps_roles_in_lockstep():
    """The shared helper every old-vocabulary entry point routes through."""
    config = LanguageServerConfig()

    config.apply_legacy_target_language("de")

    assert config.target_language == "de"
    assert config.file_language == "de"
    assert config.working_language == "de"
