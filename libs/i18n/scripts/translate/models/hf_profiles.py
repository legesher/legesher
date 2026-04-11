"""HuggingFace model profiles for the generic translation engine.

This module defines model profile configurations and a registry for HuggingFace
models used in the translation pipeline. Adding a new HF model requires only
defining a profile here — no new model class or file needed.

Profiles configure:
- Model ID and architecture (causal vs seq2seq)
- Generation parameters (temperature, max_tokens, etc.)
- Prompt building (default or custom)
- Context handling (truncation limits)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Callable

from .base import TranslationRequest

# Comprehensive language code → name mapping (merged from all existing models)
DEFAULT_LANGUAGE_NAMES: dict[str, str] = {
    # ISO 639-1 codes (used by Legesher language packs)
    "ar": "Arabic",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "fi": "Finnish",
    "fr": "French",
    "he": "Hebrew",
    "hi": "Hindi",
    "hu": "Hungarian",
    "id": "Indonesian",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "ms": "Malay",
    "nl": "Dutch",
    "no": "Norwegian",
    "pl": "Polish",
    "pt": "Portuguese",
    "ru": "Russian",
    "sv": "Swedish",
    "th": "Thai",
    "tr": "Turkish",
    "vi": "Vietnamese",
    "zh": "Chinese",
    # Additional languages supported by Tiny Aya / Aya-101
    "am": "Amharic",
    "bn": "Bengali",
    "bg": "Bulgarian",
    "bs": "Bosnian",
    "ca": "Catalan",
    "cs": "Czech",
    "cy": "Welsh",
    "et": "Estonian",
    "eu": "Basque",
    "fa": "Persian",
    "ga": "Irish",
    "gd": "Scottish Gaelic",
    "gl": "Galician",
    "gu": "Gujarati",
    "ha": "Hausa",
    "hr": "Croatian",
    "ig": "Igbo",
    "jv": "Javanese",
    "kn": "Kannada",
    "km": "Khmer",
    "lo": "Lao",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "mg": "Malagasy",
    "mk": "Macedonian",
    "ml": "Malayalam",
    "mn": "Mongolian",
    "mr": "Marathi",
    "mt": "Maltese",
    "my": "Burmese",
    "ne": "Nepali",
    "pa": "Punjabi",
    "ro": "Romanian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "sn": "Shona",
    "sr": "Serbian",
    "su": "Sundanese",
    "sw": "Swahili",
    "ta": "Tamil",
    "te": "Telugu",
    "tl": "Tagalog",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "uz": "Uzbek",
    "wo": "Wolof",
    "xh": "Xhosa",
    "yo": "Yoruba",
    "zu": "Zulu",
    # ISO 639-3 codes (used by Aya-101)
    "afr": "Afrikaans",
    "amh": "Amharic",
    "aze": "Azerbaijani",
    "bel": "Belarusian",
    "ben": "Bengali",
    "bul": "Bulgarian",
    "cat": "Catalan",
    "ceb": "Cebuano",
    "ces": "Czech",
    "cym": "Welsh",
    "epo": "Esperanto",
    "est": "Estonian",
    "eus": "Basque",
    "fil": "Filipino",
    "fry": "Frisian",
    "gla": "Scottish Gaelic",
    "gle": "Irish",
    "glg": "Galician",
    "guj": "Gujarati",
    "hat": "Haitian Creole",
    "hau": "Hausa",
    "hye": "Armenian",
    "ibo": "Igbo",
    "isl": "Icelandic",
    "jav": "Javanese",
    "kan": "Kannada",
    "kat": "Georgian",
    "kaz": "Kazakh",
    "khm": "Khmer",
    "kir": "Kyrgyz",
    "kur": "Kurdish",
    "lao": "Lao",
    "lat": "Latin",
    "lav": "Latvian",
    "lit": "Lithuanian",
    "ltz": "Luxembourgish",
    "mal": "Malayalam",
    "mar": "Marathi",
    "mkd": "Macedonian",
    "mlg": "Malagasy",
    "mlt": "Maltese",
    "mon": "Mongolian",
    "mri": "Maori",
    "mya": "Burmese",
    "nep": "Nepali",
    "nso": "Northern Sotho",
    "nya": "Nyanja",
    "ory": "Oriya",
    "pan": "Punjabi",
    "pes": "Persian",
    "pus": "Pashto",
    "sin": "Sinhala",
    "slk": "Slovak",
    "slv": "Slovenian",
    "smo": "Samoan",
    "sna": "Shona",
    "snd": "Sindhi",
    "som": "Somali",
    "sot": "Southern Sotho",
    "sqi": "Albanian",
    "srp": "Serbian",
    "sun": "Sundanese",
    "swa": "Swahili",
    "tam": "Tamil",
    "tel": "Telugu",
    "tgk": "Tajik",
    "twi": "Twi",
    "ukr": "Ukrainian",
    "urd": "Urdu",
    "uzb": "Uzbek",
    "xho": "Xhosa",
    "yid": "Yiddish",
    "yor": "Yoruba",
    "zul": "Zulu",
}


@dataclass
class HFModelProfile:
    """Configuration profile for a HuggingFace model.

    Defines everything the generic HuggingFace engine needs to use a model:
    model identity, architecture, generation parameters, and prompt building.

    Adding a new model to the pipeline requires only creating a profile
    and registering it — no new Python class needed.

    Attributes:
        name: Short CLI name (e.g., "tiny-aya-earth")
        model_id: HuggingFace repo ID (e.g., "CohereLabs/tiny-aya-earth")
        architecture: Model type — "causal" or "seq2seq"
        use_chat_template: Whether to use tokenizer.apply_chat_template()
        generation_params: kwargs for model.generate()
        dtype: Tensor dtype — "bfloat16", "float16", "float32", or "auto"
        context_max_chars: Max chars for request.context (None = omit context)
        standards_max_chars: Max chars for linguistic_standards (None = omit)
        prompt_builder: Custom prompt function, or None for default
        language_names: Override language name mapping, or None for default
    """

    name: str
    model_id: str
    architecture: str = "causal"
    use_chat_template: bool = True
    generation_params: dict = field(
        default_factory=lambda: {
            "temperature": 0.1,
            "max_new_tokens": 4096,
            "top_p": 0.95,
            "do_sample": True,
        }
    )
    dtype: str = "bfloat16"
    context_max_chars: int | None = 800
    standards_max_chars: int | None = 500
    prompt_builder: Callable | None = None
    language_names: dict[str, str] | None = None

    def get_language_name(self, code: str) -> str:
        """Resolve a language code to its human-readable name."""
        names = self.language_names or DEFAULT_LANGUAGE_NAMES
        return names.get(code, code.upper())


def default_prompt_builder(
    request: TranslationRequest,
    profile: HFModelProfile,
) -> str:
    """Build a standard translation prompt for HuggingFace models.

    This prompt works well for most multilingual models. Custom prompt
    builders can be provided per profile for models with special needs.

    Args:
        request: Translation request with term, language, and optional context
        profile: Model profile (for language names and truncation settings)

    Returns:
        Formatted prompt string
    """
    language_name = profile.get_language_name(request.target_language)

    prompt = f"""You are a multilingual expert translating Python programming terms.

TERM TO TRANSLATE: "{request.term}"
TARGET LANGUAGE: {language_name}
"""

    # Add context if available and profile allows it
    if request.context and profile.context_max_chars is not None:
        context_short = request.context[: profile.context_max_chars]
        if len(request.context) > profile.context_max_chars:
            context_short += "..."
        prompt += f"""
CONTEXT:
{context_short}
"""

    # Add linguistic standards if available and profile allows it
    if request.linguistic_standards and profile.standards_max_chars is not None:
        standards_short = request.linguistic_standards[: profile.standards_max_chars]
        if len(request.linguistic_standards) > profile.standards_max_chars:
            standards_short += "..."
        prompt += f"""
STANDARDS:
{standards_short}
"""

    prompt += f"""
TASK:
Translate "{request.term}" to {language_name} for Python programming:
1. Focus on the programming CONCEPT, not word-for-word translation
2. Use natural {language_name} that programmers would understand
3. Prefer appropriate grammatical forms (infinitive for verbs, singular for nouns)
4. The translation MUST be a valid Python identifier (no spaces, no punctuation)
5. Do NOT transliterate English — translate the meaning

OUTPUT:
Respond with ONLY a valid JSON object (no markdown, no extra text):
{{
  "translation": "the translated term",
  "word_type": "verb|noun|etc",
  "form": "infinitive|singular|etc",
  "confidence": 0.85,
  "alternatives": ["alt1", "alt2"],
  "rationale": "Why you chose this translation"
}}
"""

    return prompt


# ---------------------------------------------------------------------------
# Profile Registry
# ---------------------------------------------------------------------------

HF_PROFILES: dict[str, HFModelProfile] = {}


def register_profile(profile: HFModelProfile) -> None:
    """Register a model profile in the global registry.

    Args:
        profile: Model profile to register
    """
    HF_PROFILES[profile.name] = profile


def get_profile(name: str) -> HFModelProfile:
    """Look up a registered profile by name.

    Args:
        name: Profile name (e.g., "tiny-aya-earth")

    Returns:
        The matching HFModelProfile

    Raises:
        KeyError: If no profile is registered with that name
    """
    if name not in HF_PROFILES:
        available = ", ".join(sorted(HF_PROFILES.keys())) or "(none)"
        raise KeyError(
            f"No HuggingFace model profile '{name}' found. "
            f"Available profiles: {available}"
        )
    return HF_PROFILES[name]


def list_profiles() -> list[str]:
    """Return sorted list of registered profile names."""
    return sorted(HF_PROFILES.keys())


# ---------------------------------------------------------------------------
# Tiny Aya Profiles
# ---------------------------------------------------------------------------

_TINY_AYA_GENERATION_PARAMS = {
    "temperature": 0.1,
    "max_new_tokens": 4096,
    "top_p": 0.95,
    "do_sample": True,
}

for _variant, _model_id in [
    ("earth", "CohereLabs/tiny-aya-earth"),
    ("fire", "CohereLabs/tiny-aya-fire"),
    ("water", "CohereLabs/tiny-aya-water"),
    ("global", "CohereLabs/tiny-aya-global"),
]:
    register_profile(
        HFModelProfile(
            name=f"tiny-aya-{_variant}",
            model_id=_model_id,
            architecture="causal",
            use_chat_template=True,
            generation_params=dict(_TINY_AYA_GENERATION_PARAMS),
            dtype="bfloat16",
            context_max_chars=800,
            standards_max_chars=500,
        )
    )
