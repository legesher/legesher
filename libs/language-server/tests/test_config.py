"""Tests for configuration system."""

import sys

import pytest

from legesher_language_server.config import LanguageServerConfig


def test_default_config():
    """Test default configuration values."""
    config = LanguageServerConfig()

    assert config.source_language == "en"
    assert config.target_language == "es"
    assert config.python_version is None
    assert config.cache_size == 1000
    assert config.cache_ttl == 3600
    assert config.pylance_enabled is True
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
    monkeypatch.setenv("LEGESHER_PYLANCE_ENABLED", "false")
    monkeypatch.setenv("LEGESHER_LOG_LEVEL", "DEBUG")

    config = LanguageServerConfig.from_env()

    assert config.source_language == "pt"
    assert config.target_language == "ja"
    assert config.python_version == "3.12"
    assert config.cache_size == 2000
    assert config.cache_ttl == 7200
    assert config.pylance_enabled is False
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

    # Invalid codes (contains numbers)
    config = LanguageServerConfig(source_language="e1", target_language="es")
    assert config.validate_languages() is False


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
