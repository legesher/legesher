"""
Empirical quality scores for translation providers per language pair.

Scores are on a 0-10 scale based on:
- Translation accuracy for technical/programming terminology
- Handling of formal register
- Consistency across translations
- Community feedback and testing

These scores help select the best provider for each language pair.
"""

PROVIDER_QUALITY = {
    "deepl": {
        # European languages - DeepL's strength
        "es-en": 9.5,  # Spanish-English: Excellent
        "en-es": 9.5,
        "fr-en": 9.3,  # French-English: Excellent
        "en-fr": 9.3,
        "de-en": 9.4,  # German-English: Excellent
        "en-de": 9.4,
        "it-en": 9.2,  # Italian-English: Excellent
        "en-it": 9.2,
        "pt-en": 9.3,  # Portuguese-English: Excellent
        "en-pt": 9.3,
        "nl-en": 9.1,  # Dutch-English: Excellent
        "en-nl": 9.1,
        "pl-en": 8.9,  # Polish-English: Very good
        "en-pl": 8.9,
        "ru-en": 8.7,  # Russian-English: Very good
        "en-ru": 8.7,
        # Non-European (recently added, improving)
        "ar-en": 8.0,  # Arabic-English: Good (recently added 2023)
        "en-ar": 8.0,
        "zh-en": 8.5,  # Chinese-English: Very good
        "en-zh": 8.5,
        "ja-en": 8.6,  # Japanese-English: Very good
        "en-ja": 8.6,
        "ko-en": 8.4,  # Korean-English: Very good
        "en-ko": 8.4,
        # Not supported
        "hi-en": 0.0,  # Hindi: Not supported yet
        "en-hi": 0.0,
    },
    "google": {
        # European languages
        "es-en": 8.5,  # Spanish-English: Very good
        "en-es": 8.5,
        "fr-en": 8.3,  # French-English: Very good
        "en-fr": 8.3,
        "de-en": 8.4,  # German-English: Very good
        "en-de": 8.4,
        "it-en": 8.2,  # Italian-English: Very good
        "en-it": 8.2,
        "pt-en": 8.4,  # Portuguese-English: Very good
        "en-pt": 8.4,
        # Arabic - Google's strength
        "ar-en": 8.8,  # Arabic-English: Excellent (Google's strength)
        "en-ar": 8.8,
        # Asian languages - Google's strength
        "zh-en": 9.0,  # Chinese-English: Excellent
        "en-zh": 9.0,
        "ja-en": 8.7,  # Japanese-English: Very good
        "en-ja": 8.7,
        "ko-en": 8.5,  # Korean-English: Very good
        "en-ko": 8.5,
        # South Asian - Only major provider supporting
        "hi-en": 8.0,  # Hindi-English: Good (only option)
        "en-hi": 8.0,
        "bn-en": 7.5,  # Bengali-English: Adequate
        "en-bn": 7.5,
        # Other
        "tr-en": 8.2,  # Turkish-English: Very good
        "en-tr": 8.2,
        "id-en": 8.0,  # Indonesian-English: Good
        "en-id": 8.0,
        "vi-en": 8.1,  # Vietnamese-English: Good
        "en-vi": 8.1,
        "th-en": 7.9,  # Thai-English: Good
        "en-th": 7.9,
    },
    "libretranslate": {
        # Open-source, lower quality but free and private
        "es-en": 7.5,  # Spanish-English: Adequate for keywords
        "en-es": 7.5,
        "fr-en": 7.3,  # French-English: Adequate
        "en-fr": 7.3,
        "de-en": 7.4,  # German-English: Adequate
        "en-de": 7.4,
        "it-en": 7.2,  # Italian-English: Adequate
        "en-it": 7.2,
        "pt-en": 7.3,  # Portuguese-English: Adequate
        "en-pt": 7.3,
        "ar-en": 6.5,  # Arabic-English: Passable
        "en-ar": 6.5,
        "zh-en": 7.0,  # Chinese-English: Adequate
        "en-zh": 7.0,
        "ja-en": 6.8,  # Japanese-English: Passable
        "en-ja": 6.8,
        "ru-en": 7.1,  # Russian-English: Adequate
        "en-ru": 7.1,
        "hi-en": 6.0,  # Hindi-English: Passable (if supported)
        "en-hi": 6.0,
    },
    "argos": {
        # Offline translation, lower quality
        "es-en": 6.5,  # Spanish-English: Passable
        "en-es": 6.5,
        "fr-en": 6.3,  # French-English: Passable
        "en-fr": 6.3,
        "de-en": 6.8,  # German-English: Adequate
        "en-de": 6.8,
        "it-en": 6.2,  # Italian-English: Passable
        "en-it": 6.2,
        "pt-en": 6.4,  # Portuguese-English: Passable
        "en-pt": 6.4,
        "ar-en": 5.5,  # Arabic-English: Weak
        "en-ar": 5.5,
        "zh-en": 5.0,  # Chinese-English: Weak
        "en-zh": 5.0,
        "ru-en": 6.1,  # Russian-English: Passable
        "en-ru": 6.1,
    },
}
