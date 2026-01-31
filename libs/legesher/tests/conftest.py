"""Shared test fixtures for legesher CLI tests.

Loads translation maps from actual language pack YAML files (the source of truth).
"""

import pytest

from legesher_i18n import LanguagePackLoader


@pytest.fixture(scope="session")
def language_pack_loader():
    """Create a LanguagePackLoader instance (cached for session)."""
    return LanguagePackLoader()


@pytest.fixture(scope="session")
def spanish_pack(language_pack_loader):
    """Load the Spanish language pack for Python 3.10 (base)."""
    return language_pack_loader.load("es", target="python", version="3.10")


@pytest.fixture(scope="session")
def arabic_pack(language_pack_loader):
    """Load the Arabic language pack for Python 3.10 (base)."""
    return language_pack_loader.load("ar", target="python", version="3.10")


@pytest.fixture(scope="session")
def spanish_keywords(spanish_pack):
    """Spanish keyword translations from real language pack."""
    return spanish_pack.keywords


@pytest.fixture(scope="session")
def spanish_builtins(spanish_pack):
    """Spanish builtin translations from real language pack."""
    return spanish_pack.builtins


@pytest.fixture(scope="session")
def arabic_keywords(arabic_pack):
    """Arabic keyword translations from real language pack."""
    return arabic_pack.keywords


@pytest.fixture(scope="session")
def arabic_builtins(arabic_pack):
    """Arabic builtin translations from real language pack."""
    return arabic_pack.builtins
