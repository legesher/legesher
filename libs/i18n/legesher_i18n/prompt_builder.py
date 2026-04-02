"""Prompt builder for LLM-powered translation.

Composes provider-agnostic ``(system_prompt, user_prompt)`` tuples for
translating Python identifiers and text elements into target natural
languages.  The system prompt is static per language (cacheable), while
the user prompt changes per call.

Usage
-----
>>> from legesher_i18n.style_guides import StyleGuideLoader
>>> from legesher_i18n.prompt_builder import PromptBuilder
>>>
>>> loader = StyleGuideLoader()
>>> builder = PromptBuilder(loader)
>>> system, user = builder.build_identifier_prompt(
...     identifiers=[{"text": "add_two", "role": "function_name", "context": {}}],
...     target_lang="es",
...     existing_glossary={},
... )
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from legesher_i18n.style_guides import StyleGuideLoader

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Language metadata
# ---------------------------------------------------------------------------

_LANGUAGES_JSON = Path(__file__).parent / "languages.json"


def _load_language_names() -> dict[str, str]:
    """Load language code -> English name mapping from ``languages.json``."""
    try:
        with open(_LANGUAGES_JSON, encoding="utf-8") as fh:
            data = json.load(fh)
        return {code: meta["name"] for code, meta in data.get("languages", {}).items()}
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        logger.warning("Failed to load languages.json, using fallback: %s", exc)
        return {}


# Built-in fallback so the module works even if languages.json is missing.
_FALLBACK_LANGUAGE_NAMES: dict[str, str] = {
    "am": "Amharic",
    "ar": "Arabic",
    "bn": "Bengali",
    "bs": "Bosnian",
    "ca": "Catalan",
    "cs": "Czech",
    "cy": "Welsh",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "fa": "Persian",
    "fi": "Finnish",
    "fr": "French",
    "ga": "Irish",
    "gd": "Scottish Gaelic",
    "gl": "Galician",
    "gu": "Gujarati",
    "he": "Hebrew",
    "hi": "Hindi",
    "hr": "Croatian",
    "hu": "Hungarian",
    "id": "Indonesian",
    "it": "Italian",
    "ja": "Japanese",
    "kn": "Kannada",
    "ko": "Korean",
    "lv": "Latvian",
    "mk": "Macedonian",
    "ml": "Malayalam",
    "mn": "Mongolian",
    "ms": "Malay",
    "my": "Burmese",
    "nl": "Dutch",
    "no": "Norwegian",
    "pl": "Polish",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "si": "Sinhala",
    "sr": "Serbian",
    "su": "Sundanese",
    "sv": "Swedish",
    "te": "Telugu",
    "th": "Thai",
    "tr": "Turkish",
    "ur": "Urdu",
    "uz": "Uzbek",
    "vi": "Vietnamese",
    "zh": "Chinese",
}

# Merged at import time: languages.json values override fallback.
LANGUAGE_NAMES: dict[str, str] = {**_FALLBACK_LANGUAGE_NAMES, **_load_language_names()}

# ---------------------------------------------------------------------------
# Native-language programming precedent framing
# ---------------------------------------------------------------------------

NATIVE_LANG_EXAMPLES: dict[str, str] = {
    "zh": (
        "Programming languages with Chinese keywords already exist "
        "-- notably \u6587\u8a00 (wenyan-lang) and \u6613\u8bed\u8a00 (EPL). "
        "These prove that programming in Chinese is natural and practical."
    ),
    "es": (
        "Programming languages with Spanish keywords already exist "
        "-- notably Latino and Lexico. "
        "These prove that programming in Spanish is natural and practical."
    ),
    "ar": (
        "Programming languages with Arabic keywords already exist "
        "-- notably \u0642\u0644\u0628 (Qalb) and Arablan. "
        "These prove that programming in Arabic is natural and practical."
    ),
    "hi": (
        "Programming languages with Hindi keywords have been explored "
        "in educational contexts, proving that Devanagari-script "
        "programming is viable."
    ),
    "fr": (
        "Programming languages with French keywords already exist "
        "-- notably LSE (Langage Symbolique d'Enseignement). "
        "French-language programming has educational precedent."
    ),
    "ru": (
        "Programming languages with Russian keywords already exist "
        "-- notably Rapira (\u0420\u0430\u043f\u0438\u0440\u0430) "
        "and the 1C:Enterprise language. "
        "These prove that Cyrillic-script programming is natural."
    ),
    "ja": (
        "Programming languages with Japanese keywords already exist "
        "-- notably \u306a\u3067\u3057\u3053 (Nadeshiko) "
        "and \u3072\u307e\u308f\u308a (Himawari). "
        "These prove that Japanese-script programming is natural."
    ),
    "ko": (
        "Programming languages with Korean keywords have been explored "
        "-- notably \uc528\uc557 (Siat). "
        "These prove that Hangul-script programming is viable."
    ),
}

# ---------------------------------------------------------------------------
# Critical rules (always included)
# ---------------------------------------------------------------------------

_CRITICAL_RULES: list[str] = [
    "All translations MUST be valid Python identifiers -- no spaces, no punctuation.",
    "snake_case identifiers stay snake_case, PascalCase stays PascalCase.",
    "Maintain consistent verb/noun choices across similar names.",
    "Translate the CONCEPT, not the English word -- do NOT transliterate.",
]


# ---------------------------------------------------------------------------
# PromptBuilder
# ---------------------------------------------------------------------------


class PromptBuilder:
    """Compose LLM translation prompts from style guides and context.

    This is the central intelligence layer for composing translation
    prompts.  It is provider-agnostic and returns
    ``(system_prompt, user_prompt)`` tuples ready to be sent to any LLM.

    Parameters
    ----------
    style_guide_loader:
        A :class:`StyleGuideLoader` instance used to fetch merged style
        guide dictionaries for each target language.
    """

    def __init__(self, style_guide_loader: StyleGuideLoader) -> None:
        self._loader = style_guide_loader

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_identifier_prompt(
        self,
        identifiers: list[dict[str, Any]],
        target_lang: str,
        existing_glossary: dict[str, str],
    ) -> tuple[str, str]:
        """Build prompts for identifier batch translation.

        Parameters
        ----------
        identifiers:
            List of identifier dicts, each with keys ``text`` (str),
            ``role`` (str -- e.g. ``"function_name"``, ``"parameter"``,
            ``"variable"``, ``"class_name"``), and ``context`` (dict).
        target_lang:
            ISO 639-1 language code (e.g. ``"es"``, ``"ar"``).
        existing_glossary:
            Already-translated identifiers from ``IdentifierMap.get_glossary()``,
            mapping original English text to its translation.

        Returns
        -------
        tuple[str, str]
            ``(system_prompt, user_prompt)``
        """
        system = self._build_system_prompt(target_lang)
        user = self._build_identifier_user_prompt(
            identifiers,
            target_lang,
            existing_glossary,
        )
        return system, user

    def build_text_prompt(
        self,
        texts: list[dict[str, Any]],
        target_lang: str,
        identifier_glossary: dict[str, str],
    ) -> tuple[str, str]:
        """Build prompts for text element batch translation.

        Parameters
        ----------
        texts:
            List of text dicts, each with keys ``text`` (str),
            ``kind`` (str -- e.g. ``"comment"``, ``"docstring"``,
            ``"string"``), and ``context`` (dict).
        target_lang:
            ISO 639-1 language code.
        identifier_glossary:
            ALL file identifiers from Step 3 (original -> translation),
            so that text translations use the same terminology.

        Returns
        -------
        tuple[str, str]
            ``(system_prompt, user_prompt)``
        """
        system = self._build_system_prompt(target_lang)
        user = self._build_text_user_prompt(
            texts,
            target_lang,
            identifier_glossary,
        )
        return system, user

    def estimate_tokens(self, system: str, user: str) -> int:
        """Rough token estimate for a prompt pair.

        Uses ``len(text) / 4`` as a simple chars-to-tokens approximation
        that works reasonably well across languages and tokenizers.

        Parameters
        ----------
        system:
            The system prompt text.
        user:
            The user prompt text.

        Returns
        -------
        int
            Estimated token count (rounded up).
        """
        total_chars = len(system) + len(user)
        return -(-total_chars // 4)  # ceiling division

    # ------------------------------------------------------------------
    # System prompt construction
    # ------------------------------------------------------------------

    def _build_system_prompt(self, target_lang: str) -> str:
        """Compose the full system prompt for *target_lang*.

        Sections:
        1. Language framing (persona + precedent)
        2. Style guide rules
        3. Critical rules
        """
        lang_name = self._resolve_language_name(target_lang)
        sections: list[str] = [
            self._build_framing(target_lang, lang_name),
            self._build_style_guide_section(target_lang),
            self._build_critical_rules_section(),
        ]
        return "\n\n".join(sections)

    def _build_framing(self, target_lang: str, lang_name: str) -> str:
        """Build the language-framing preamble."""
        precedent = NATIVE_LANG_EXAMPLES.get(target_lang)
        if precedent is None:
            precedent = (
                f"No widely-known programming language currently uses "
                f"{lang_name} keywords, but that is exactly what you are "
                f"helping to create -- the first {lang_name} programming "
                f"experience."
            )

        return (
            f"IMAGINE: You are a computer science professor designing "
            f"Python code in {lang_name} for students who think and learn "
            f"in {lang_name}. These students should be able to read code "
            f"as naturally as reading a {lang_name} textbook. Every "
            f"identifier should feel like it belongs in their language "
            f"-- not borrowed from English, not transliterated, but a real "
            f"{lang_name} word that captures what the programming concept "
            f"DOES.\n\n"
            f"{precedent}\n\n"
            f"Write ALL translations in native {lang_name} script. "
            f"Do NOT use Latin/Roman characters (unless {lang_name} "
            f"natively uses the Latin alphabet)."
        )

    def _build_style_guide_section(self, target_lang: str) -> str:
        """Format the loaded style guide into readable prompt text."""
        guide = self._loader.load(target_lang)
        if not guide:
            return "## Style Guide\n\nNo style guide available for this language."

        parts: list[str] = ["## Style Guide"]

        # Naming conventions
        naming = guide.get("naming", {})
        if naming:
            parts.append(self._format_naming_rules(naming))

        # Script requirements
        script = guide.get("script", {})
        if script:
            parts.append(self._format_script_rules(script))

        # Translation conventions
        translation = guide.get("translation", {})
        if translation:
            parts.append(self._format_translation_rules(translation))

        # Formatting rules
        formatting = guide.get("formatting", {})
        if formatting:
            parts.append(self._format_formatting_rules(formatting))

        return "\n\n".join(parts)

    def _build_critical_rules_section(self) -> str:
        """Format the critical rules that always apply."""
        lines = ["## Critical Rules"]
        for rule in _CRITICAL_RULES:
            lines.append(f"- {rule}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Style guide formatting helpers
    # ------------------------------------------------------------------

    def _format_naming_rules(self, naming: dict[str, Any]) -> str:
        """Format the naming conventions section."""
        lines = ["### Naming Conventions"]
        for key, value in naming.items():
            if isinstance(value, dict):
                usage = value.get("usage", "")
                rule = value.get("rule", "")
                unicode_note = value.get("unicode", "")
                detail = value.get("detail", "")

                header = key.replace("_", " ").title()
                lines.append(f"\n**{header}**")
                if usage:
                    lines.append(f"- Usage: {usage}")
                if rule:
                    lines.append(f"- Rule: {rule}")
                if unicode_note:
                    lines.append(f"- Unicode: {unicode_note}")
                if detail:
                    lines.append(f"- {detail.strip()}")

                examples = value.get("examples", [])
                if examples:
                    for ex in examples:
                        lines.append(f"  - e.g. {ex}")
            elif isinstance(value, str):
                lines.append(f"- {key}: {value}")

        return "\n".join(lines)

    def _format_script_rules(self, script: dict[str, Any]) -> str:
        """Format the script/character requirements section."""
        lines = ["### Script Requirements"]

        native = script.get("native_required")
        if native is not None:
            lines.append(f"- Native script required: {native}")

        detail = script.get("detail", "")
        if detail:
            lines.append(f"- {detail.strip()}")

        latin = script.get("latin_mixing", {})
        if isinstance(latin, dict) and latin.get("rule"):
            lines.append(f"- Latin mixing: {latin['rule'].strip()}")

        accent = script.get("accent_handling", {})
        if isinstance(accent, dict) and accent.get("rule"):
            lines.append(f"- Accents: {accent['rule'].strip()}")

        bidi = script.get("bidirectional", {})
        if isinstance(bidi, dict):
            handling = bidi.get("handling", "")
            bidi_detail = bidi.get("detail", "")
            if handling:
                lines.append(f"- Bidirectional handling: {handling}")
            if bidi_detail:
                lines.append(f"  {bidi_detail.strip()}")

        return "\n".join(lines)

    def _format_translation_rules(self, translation: dict[str, Any]) -> str:
        """Format the translation conventions section."""
        lines = ["### Translation Conventions"]

        register = translation.get("register", "")
        if register:
            lines.append(f"- Register: {register}")

        detail = translation.get("detail", "")
        if detail:
            lines.append(f"- {detail.strip()}")

        for section_key in (
            "verb_form",
            "noun_form",
            "boolean_constants",
            "type_constructors",
            "transliteration",
            "compound_consistency",
        ):
            section = translation.get(section_key, {})
            if not isinstance(section, dict):
                continue

            header = section_key.replace("_", " ").title()
            lines.append(f"\n**{header}**")

            for k, v in section.items():
                if k == "examples":
                    for ex in v:
                        lines.append(f"  - e.g. {ex}")
                elif k == "pattern_families":
                    for pf in v:
                        lines.append(f"  - {pf}")
                elif isinstance(v, str):
                    lines.append(f"- {k}: {v.strip()}")

        return "\n".join(lines)

    def _format_formatting_rules(self, formatting: dict[str, Any]) -> str:
        """Format the formatting conventions section."""
        lines = ["### Formatting Rules"]

        prefix = formatting.get("comment_prefix", "")
        if prefix:
            lines.append(f"- Comment prefix: ``{prefix}``")

        docstring = formatting.get("docstring_style", {})
        if isinstance(docstring, dict) and docstring.get("rule"):
            lines.append(f"- Docstrings: {docstring['rule'].strip()}")
            doc_detail = docstring.get("detail", "")
            if doc_detail:
                lines.append(f"  {doc_detail.strip()}")

        punctuation = formatting.get("punctuation", {})
        if isinstance(punctuation, dict) and punctuation.get("rule"):
            lines.append(f"- Punctuation: {punctuation['rule'].strip()}")

        line_length = formatting.get("line_length", {})
        if isinstance(line_length, dict) and line_length.get("rule"):
            lines.append(f"- Line length: {line_length['rule'].strip()}")
            note = line_length.get("note", "")
            if note:
                lines.append(f"  Note: {note.strip()}")

        alignment = formatting.get("alignment", {})
        if isinstance(alignment, dict) and alignment.get("rule"):
            lines.append(f"- Alignment: {alignment['rule'].strip()}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # User prompt construction
    # ------------------------------------------------------------------

    def _build_identifier_user_prompt(
        self,
        identifiers: list[dict[str, Any]],
        target_lang: str,
        existing_glossary: dict[str, str],
    ) -> str:
        """Compose the user prompt for identifier translation."""
        lang_name = self._resolve_language_name(target_lang)
        parts: list[str] = []

        # Existing glossary
        if existing_glossary:
            parts.append(
                "These identifiers have already been translated. "
                "Use consistent terminology:"
            )
            parts.append(self._format_glossary_table(existing_glossary))
            parts.append("")

        # Identifiers to translate
        parts.append(f"Translate the following Python identifiers into {lang_name}.")
        parts.append("")

        parts.append("| # | Identifier | Role |")
        parts.append("|---|-----------|------|")
        for i, ident in enumerate(identifiers, 1):
            text = ident.get("text", "")
            role = ident.get("role", "unknown")
            parts.append(f"| {i} | `{text}` | {role} |")

        parts.append("")
        parts.append(
            "IMPORTANT: If multiple identifiers share a pattern "
            "(e.g., add_two, add_four), use the SAME verb for all of them."
        )

        # Output format
        parts.append("")
        parts.append(
            "Respond with a JSON object mapping each original identifier "
            "to its translation. Example format:"
        )
        parts.append("```json")
        parts.append("{")
        parts.append('  "original_name": "translated_name"')
        parts.append("}")
        parts.append("```")

        return "\n".join(parts)

    def _build_text_user_prompt(
        self,
        texts: list[dict[str, Any]],
        target_lang: str,
        identifier_glossary: dict[str, str],
    ) -> str:
        """Compose the user prompt for text element translation."""
        lang_name = self._resolve_language_name(target_lang)
        parts: list[str] = []

        # Identifier glossary for consistency
        if identifier_glossary:
            parts.append(
                "These identifiers in this code have been translated "
                "as follows. Use the SAME terms in your translations:"
            )
            parts.append(self._format_glossary_table(identifier_glossary))
            parts.append("")

        # Texts to translate
        parts.append(f"Translate the following text elements into {lang_name}.")
        parts.append("")
        parts.append(
            "IMPORTANT: Do NOT translate technical values that are used for "
            "comparison or control flow. Return these UNCHANGED:\n"
            '- Single digits or numbers: "1", "2", "6", "10"\n'
            '- Operators: "+", "-", "*", "/", "^"\n'
            "- Single characters used as flags or keys\n"
            '- The string "__main__" (this is a Python convention, never translate)\n'
            '- Format strings like "=" used for decoration\n'
            "ONLY translate human-readable text (messages, labels, descriptions)."
        )
        parts.append("")

        for i, text_item in enumerate(texts, 1):
            text = text_item.get("text", "")
            kind = text_item.get("kind", "unknown")
            parts.append(f"### Item {i} ({kind})")
            parts.append(f"```\n{text}\n```")
            parts.append("")

        # Output format
        parts.append(
            "Respond with a JSON list of translations in the SAME order "
            "as the items above. Example format:"
        )
        parts.append("```json")
        parts.append("[")
        parts.append('  "translated text for item 1",')
        parts.append('  "translated text for item 2"')
        parts.append("]")
        parts.append("```")

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_language_name(self, lang_code: str) -> str:
        """Resolve a language code to its English name."""
        name = LANGUAGE_NAMES.get(lang_code)
        if name is None:
            logger.warning(
                "Unknown language code '%s', using code as name",
                lang_code,
            )
            return lang_code
        return name

    _MAX_GLOSSARY_ENTRIES = 500

    @staticmethod
    def _format_glossary_table(glossary: dict[str, str]) -> str:
        """Format a glossary dict as a Markdown table.

        Truncates to ``_MAX_GLOSSARY_ENTRIES`` to prevent unbounded
        prompt growth with large codebases.
        """
        entries = sorted(glossary.items())
        if len(entries) > PromptBuilder._MAX_GLOSSARY_ENTRIES:
            logger.warning(
                "Glossary truncated from %d to %d entries",
                len(entries),
                PromptBuilder._MAX_GLOSSARY_ENTRIES,
            )
            entries = entries[: PromptBuilder._MAX_GLOSSARY_ENTRIES]

        lines = [
            "",
            "| Original | Translation |",
            "|----------|-------------|",
        ]
        for original, translation in entries:
            lines.append(f"| `{original}` | `{translation}` |")
        return "\n".join(lines)
