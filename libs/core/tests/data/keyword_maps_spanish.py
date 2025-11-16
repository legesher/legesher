"""Spanish translation maps for Python keywords and builtins.

This module provides hardcoded translation maps for translating Python
keywords and builtin functions to Spanish. These are used for testing
the token-based transformer before the version-aware language pack system
(CORE-345) is implemented.

Language: Spanish (Español)
ISO Code: es
Python Version: 3.13
"""

# TODO: Consider importing keywords from legesher_i18n.scripts.translate.term_classifier
#       for source of truth validation. Currently hardcoded for test fixtures.

# Python 3.13 Keywords - Spanish Translations
# Based on common Spanish programming terminology
SPANISH_KEYWORDS = {
    # Control flow
    "if": "si",
    "elif": "sinosi",
    "else": "sino",
    "for": "para",
    "while": "mientras",
    "break": "romper",
    "continue": "continuar",
    "pass": "pasar",
    # Function/class definition
    "def": "definir",
    "class": "clase",
    "return": "retornar",
    "yield": "producir",
    "lambda": "lambda",  # Lambda often stays same in Spanish
    # Exception handling
    "try": "intentar",
    "except": "excepto",
    "finally": "finalmente",
    "raise": "lanzar",
    "assert": "afirmar",
    # Imports
    "import": "importar",
    "from": "desde",
    "as": "como",
    # Context managers
    "with": "con",
    # Async keywords
    "async": "asincrono",
    "await": "esperar",
    # Boolean/None
    "True": "Verdadero",
    "False": "Falso",
    "None": "Nada",
    # Operators
    "and": "y",
    "or": "o",
    "not": "no",
    "in": "en",
    "is": "es",
    # Other
    "del": "eliminar",
    "global": "global",  # Often stays same
    "nonlocal": "nolocal",
}

# Common Python Builtins - Spanish Translations
# Focusing on ~30 most commonly used builtins
SPANISH_BUILTINS = {
    # I/O functions
    "print": "imprimir",
    "input": "entrada",
    "open": "abrir",
    # Type conversions
    "int": "entero",
    "float": "flotante",
    "str": "cadena",
    "bool": "booleano",
    "list": "lista",
    "dict": "diccionario",
    "set": "conjunto",
    "tuple": "tupla",
    # Sequence operations
    "len": "longitud",
    "range": "rango",
    "sum": "suma",
    "max": "maximo",
    "min": "minimo",
    "sorted": "ordenado",
    "reversed": "invertido",
    "enumerate": "enumerar",
    "zip": "comprimir",
    # Functional programming
    "map": "mapear",
    "filter": "filtrar",
    "any": "alguno",
    "all": "todos",
    # Object introspection
    "type": "tipo",
    "isinstance": "esinstancia",
    "hasattr": "tieneatributo",
    "getattr": "obteneratributo",
    "setattr": "estableceratributo",
    "dir": "directorio",
    "help": "ayuda",
    # Math functions
    "abs": "absoluto",
    "round": "redondear",
    "pow": "potencia",
}

# Reverse maps for translating from Spanish back to English
ENGLISH_KEYWORDS = {v: k for k, v in SPANISH_KEYWORDS.items()}
ENGLISH_BUILTINS = {v: k for k, v in SPANISH_BUILTINS.items()}

# Validation: Ensure all Python 3.13 keywords are covered
PYTHON_313_KEYWORDS = {
    "False",
    "None",
    "True",
    "and",
    "as",
    "assert",
    "async",
    "await",
    "break",
    "class",
    "continue",
    "def",
    "del",
    "elif",
    "else",
    "except",
    "finally",
    "for",
    "from",
    "global",
    "if",
    "import",
    "in",
    "is",
    "lambda",
    "nonlocal",
    "not",
    "or",
    "pass",
    "raise",
    "return",
    "try",
    "while",
    "with",
    "yield",
}

# Check coverage (should be 100%)
_missing_keywords = PYTHON_313_KEYWORDS - set(SPANISH_KEYWORDS.keys())
if _missing_keywords:
    raise ValueError(f"Missing Spanish translations for keywords: {_missing_keywords}")
