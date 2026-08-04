"""Shared fixtures for translation memory tests (CORE-411).

Mirrors tests/register_map/conftest.py: minimal hand-rolled
keyword/builtin maps so the integration seam does not depend on any
particular language pack's contents.
"""

import pytest

from legesher_core.token_mapper import TokenMapper


@pytest.fixture(scope="session")
def keyword_map():
    """Minimal keyword map for testing."""
    return {
        "def": "definir",
        "class": "clase",
        "if": "si",
        "else": "sino",
        "return": "retornar",
        "import": "importar",
        "from": "desde",
        "for": "para",
        "in": "en",
        "pass": "pasar",
        "True": "Verdadero",
        "False": "Falso",
        "None": "Nada",
    }


@pytest.fixture(scope="session")
def builtin_map():
    """Minimal builtin map for testing."""
    return {
        "print": "imprimir",
        "len": "longitud",
        "range": "rango",
        "int": "entero",
        "str": "cadena",
    }


@pytest.fixture(scope="session")
def mapper(keyword_map, builtin_map):
    return TokenMapper(keyword_map, builtin_map)
