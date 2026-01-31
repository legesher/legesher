"""Shared test fixtures for legesher-core tests.

Loads translation maps from actual language pack YAML files (the source of truth)
instead of hardcoded Python dictionaries. This ensures tests validate against
the same translations that end users will experience.
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


@pytest.fixture(scope="session")
def english_keywords_from_spanish(spanish_keywords):
    """Reverse map: Spanish → English keywords."""
    return {v: k for k, v in spanish_keywords.items()}


@pytest.fixture(scope="session")
def english_builtins_from_spanish(spanish_builtins):
    """Reverse map: Spanish → English builtins."""
    return {v: k for k, v in spanish_builtins.items()}


@pytest.fixture(scope="session")
def english_keywords_from_arabic(arabic_keywords):
    """Reverse map: Arabic → English keywords."""
    return {v: k for k, v in arabic_keywords.items()}


@pytest.fixture(scope="session")
def english_builtins_from_arabic(arabic_builtins):
    """Reverse map: Arabic → English builtins."""
    return {v: k for k, v in arabic_builtins.items()}
