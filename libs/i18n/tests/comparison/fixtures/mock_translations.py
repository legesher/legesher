"""Mock translation data for testing comparison engine.

This module provides realistic test data covering various edge cases:
- Perfect agreement (all sources identical)
- Partial agreement (3/4 sources agree)
- No agreement (all different but semantically similar)
- Missing sources
- Different word types
- Different forms
- Length variations
- Multiple language scripts
"""

from legesher_i18n.comparison.models import Translation


# Spanish Mock Data
MOCK_SPANISH_TRANSLATIONS = {
    # Perfect agreement (all 4 sources identical)
    "print": {
        "community": Translation(
            "print", "imprimir", "community", "es", "verb", "infinitive", 1.0
        ),
        "claude": Translation(
            "print", "imprimir", "claude", "es", "verb", "infinitive", 0.98
        ),
        "gpt4o": Translation(
            "print", "imprimir", "gpt4o", "es", "verb", "infinitive", 0.97
        ),
        "aya23": Translation(
            "print", "imprimir", "aya23", "es", "verb", "infinitive", 0.95
        ),
    },
    # Partial agreement (3/4 agree)
    "def": {
        "community": Translation(
            "def", "definir", "community", "es", "verb", "infinitive", 1.0
        ),
        "claude": Translation(
            "def",
            "definir",
            "claude",
            "es",
            "verb",
            "infinitive",
            0.95,
            rationale="Infinitive verb form is standard for Python keywords",
            alternatives=["función", "def"],
        ),
        "gpt4o": Translation(
            "def",
            "función",
            "gpt4o",
            "es",
            "noun",
            None,
            0.85,
            rationale="Chose noun form instead of verb",
        ),
        "aya23": Translation(
            "def", "definir", "aya23", "es", "verb", "infinitive", 0.90
        ),
    },
    # No agreement (all different but semantically similar)
    "return": {
        "community": Translation(
            "return", "retornar", "community", "es", "verb", "infinitive", 1.0
        ),
        "claude": Translation(
            "return",
            "devolver",
            "claude",
            "es",
            "verb",
            "infinitive",
            0.92,
            rationale="'devolver' is more natural in Spanish",
            alternatives=["retornar", "regresar"],
        ),
        "gpt4o": Translation(
            "return", "regresar", "gpt4o", "es", "verb", "infinitive", 0.88
        ),
        "aya23": Translation(
            "return", "volver", "aya23", "es", "verb", "infinitive", 0.85
        ),
    },
    # One source kept English (common with Aya)
    "lambda": {
        "community": Translation(
            "lambda",
            "lambda",
            "community",
            "es",
            None,
            None,
            0.8,
            rationale="Commonly kept as 'lambda' in Spanish",
        ),
        "claude": Translation(
            "lambda",
            "función anónima",
            "claude",
            "es",
            "noun phrase",
            None,
            0.75,
            rationale="Descriptive translation",
            alternatives=["lambda", "anónima"],
        ),
        "gpt4o": Translation("lambda", "lambda", "gpt4o", "es", None, None, 0.85),
        "aya23": Translation("lambda", "lambda", "aya23", "es", None, None, 0.90),
    },
    # Missing source (only 3 sources have translation)
    "yield": {
        "community": Translation(
            "yield", "producir", "community", "es", "verb", "infinitive", 0.9
        ),
        "claude": Translation(
            "yield",
            "ceder",
            "claude",
            "es",
            "verb",
            "infinitive",
            0.87,
            alternatives=["producir", "generar"],
        ),
        "gpt4o": Translation(
            "yield", "generar", "gpt4o", "es", "verb", "infinitive", 0.85
        ),
        # aya23 missing
    },
    # Word type differs
    "class": {
        "community": Translation(
            "class", "clase", "community", "es", "noun", "singular", 1.0
        ),
        "claude": Translation(
            "class", "clase", "claude", "es", "noun", "singular", 0.98
        ),
        "gpt4o": Translation(
            "class",
            "clasificar",
            "gpt4o",
            "es",
            "verb",
            "infinitive",
            0.70,
            rationale="Misunderstood as verb instead of noun",
        ),
        "aya23": Translation("class", "clase", "aya23", "es", "noun", "singular", 0.95),
    },
    # Length differs significantly
    "is": {
        "community": Translation("is", "es", "community", "es", "verb", "present", 1.0),
        "claude": Translation("is", "es", "claude", "es", "verb", "present", 0.99),
        "gpt4o": Translation(
            "is",
            "esexactamente",
            "gpt4o",
            "es",
            "verb phrase",
            None,
            0.6,
            rationale="Overly verbose translation",
        ),
        "aya23": Translation("is", "es", "aya23", "es", "verb", "present", 0.97),
    },
    # Additional common terms
    "if": {
        "community": Translation(
            "if", "si", "community", "es", "conjunction", None, 1.0
        ),
        "claude": Translation("if", "si", "claude", "es", "conjunction", None, 0.99),
        "gpt4o": Translation("if", "si", "gpt4o", "es", "conjunction", None, 0.98),
        "aya23": Translation("if", "si", "aya23", "es", "conjunction", None, 0.97),
    },
    "else": {
        "community": Translation(
            "else", "sino", "community", "es", "conjunction", None, 1.0
        ),
        "claude": Translation(
            "else", "sino", "claude", "es", "conjunction", None, 0.95
        ),
        "gpt4o": Translation(
            "else", "de lo contrario", "gpt4o", "es", "phrase", None, 0.75
        ),
        "aya23": Translation("else", "sino", "aya23", "es", "conjunction", None, 0.92),
    },
    "for": {
        "community": Translation(
            "for", "para", "community", "es", "preposition", None, 1.0
        ),
        "claude": Translation("for", "para", "claude", "es", "preposition", None, 0.98),
        "gpt4o": Translation("for", "para", "gpt4o", "es", "preposition", None, 0.96),
        "aya23": Translation("for", "para", "aya23", "es", "preposition", None, 0.94),
    },
    "while": {
        "community": Translation(
            "while", "mientras", "community", "es", "conjunction", None, 1.0
        ),
        "claude": Translation(
            "while", "mientras", "claude", "es", "conjunction", None, 0.97
        ),
        "gpt4o": Translation(
            "while", "mientras", "gpt4o", "es", "conjunction", None, 0.95
        ),
        "aya23": Translation(
            "while", "mientras", "aya23", "es", "conjunction", None, 0.93
        ),
    },
}


# Arabic Mock Data (RTL script)
MOCK_ARABIC_TRANSLATIONS = {
    "def": {
        "community": Translation(
            "def", "تعريف", "community", "ar", "verb", "infinitive", 1.0
        ),
        "claude": Translation(
            "def", "تعريف", "claude", "ar", "verb", "infinitive", 0.97
        ),
        "gpt4o": Translation("def", "وظيفة", "gpt4o", "ar", "noun", None, 0.80),
        "aya23": Translation("def", "تعريف", "aya23", "ar", "verb", "infinitive", 0.93),
    },
    "print": {
        "community": Translation(
            "print", "طباعة", "community", "ar", "verb", "infinitive", 1.0
        ),
        "claude": Translation(
            "print", "طباعة", "claude", "ar", "verb", "infinitive", 0.98
        ),
        "gpt4o": Translation(
            "print", "طباعة", "gpt4o", "ar", "verb", "infinitive", 0.96
        ),
        "aya23": Translation(
            "print", "طباعة", "aya23", "ar", "verb", "infinitive", 0.94
        ),
    },
    "return": {
        "community": Translation(
            "return", "إرجاع", "community", "ar", "verb", "infinitive", 1.0
        ),
        "claude": Translation(
            "return",
            "عودة",
            "claude",
            "ar",
            "noun",
            None,
            0.88,
            rationale="Used noun form instead of verb",
        ),
        "gpt4o": Translation(
            "return", "إرجاع", "gpt4o", "ar", "verb", "infinitive", 0.92
        ),
        "aya23": Translation(
            "return", "رجوع", "aya23", "ar", "verb", "infinitive", 0.85
        ),
    },
    "if": {
        "community": Translation(
            "if", "إذا", "community", "ar", "conjunction", None, 1.0
        ),
        "claude": Translation("if", "إذا", "claude", "ar", "conjunction", None, 0.99),
        "gpt4o": Translation("if", "إذا", "gpt4o", "ar", "conjunction", None, 0.98),
        "aya23": Translation("if", "إذا", "aya23", "ar", "conjunction", None, 0.97),
    },
    "else": {
        "community": Translation(
            "else", "وإلا", "community", "ar", "conjunction", None, 1.0
        ),
        "claude": Translation(
            "else", "وإلا", "claude", "ar", "conjunction", None, 0.96
        ),
        "gpt4o": Translation("else", "خلاف ذلك", "gpt4o", "ar", "phrase", None, 0.80),
        "aya23": Translation("else", "وإلا", "aya23", "ar", "conjunction", None, 0.93),
    },
}


# Chinese Mock Data (logographic script)
MOCK_CHINESE_TRANSLATIONS = {
    "def": {
        "community": Translation("def", "定义", "community", "zh", "verb", None, 1.0),
        "claude": Translation("def", "定义", "claude", "zh", "verb", None, 0.98),
        "gpt4o": Translation("def", "函数", "gpt4o", "zh", "noun", None, 0.85),
        "aya23": Translation("def", "定义", "aya23", "zh", "verb", None, 0.95),
    },
    "print": {
        "community": Translation("print", "打印", "community", "zh", "verb", None, 1.0),
        "claude": Translation("print", "打印", "claude", "zh", "verb", None, 0.99),
        "gpt4o": Translation("print", "打印", "gpt4o", "zh", "verb", None, 0.97),
        "aya23": Translation("print", "打印", "aya23", "zh", "verb", None, 0.96),
    },
    "return": {
        "community": Translation(
            "return", "返回", "community", "zh", "verb", None, 1.0
        ),
        "claude": Translation("return", "返回", "claude", "zh", "verb", None, 0.98),
        "gpt4o": Translation("return", "返回", "gpt4o", "zh", "verb", None, 0.96),
        "aya23": Translation("return", "返回", "aya23", "zh", "verb", None, 0.94),
    },
}


def get_all_mock_translations():
    """Get all mock translation data."""
    return {
        "es": MOCK_SPANISH_TRANSLATIONS,
        "ar": MOCK_ARABIC_TRANSLATIONS,
        "zh": MOCK_CHINESE_TRANSLATIONS,
    }


def get_mock_translations_for_term(term: str, language: str):
    """
    Get mock translations for a specific term and language.

    Args:
        term: Python term (e.g., "def")
        language: Language code (e.g., "es", "ar", "zh")

    Returns:
        Dict of source -> Translation, or empty dict if not found
    """
    all_data = get_all_mock_translations()
    lang_data = all_data.get(language, {})
    return lang_data.get(term, {})


def get_mock_terms_for_language(language: str):
    """
    Get all available terms for a language.

    Args:
        language: Language code (e.g., "es", "ar", "zh")

    Returns:
        List of term strings
    """
    all_data = get_all_mock_translations()
    lang_data = all_data.get(language, {})
    return list(lang_data.keys())


def get_available_languages():
    """Get list of available mock languages."""
    return ["es", "ar", "zh"]


def get_statistics():
    """Get statistics about mock data coverage."""
    all_data = get_all_mock_translations()
    stats = {
        "total_languages": len(all_data),
        "terms_per_language": {},
        "total_terms": 0,
        "sources_per_term": {},
    }

    for lang, terms in all_data.items():
        stats["terms_per_language"][lang] = len(terms)
        stats["total_terms"] += len(terms)

        for term, sources in terms.items():
            key = f"{lang}:{term}"
            stats["sources_per_term"][key] = len(sources)

    return stats
