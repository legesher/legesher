"""LLMTranslator threads forbidden_values into the per-batch backend context.

CORE-710 + CORE-950: when LLMTranslator is constructed from a language
pack, it must compute the union of pack reserved values (keywords +
builtins + exceptions + reserved_words) and inject that flat list into
every identifier translation request so the backend (provider) can pass
it to PromptBuilder.

These tests verify the contract by inspecting the items the translator
sends to ``backend.translate_batch``.
"""

from __future__ import annotations

from typing import Any

from legesher_core.tree_sitter.llm_translator import LLMTranslator


class _RecordingBackend:
    """TextTranslationBackend stub that records every batch call."""

    def __init__(self, translations: dict[str, str] | None = None) -> None:
        self.translations = translations or {}
        self.batch_calls: list[list[dict[str, Any]]] = []

    def translate_text(
        self, text: str, source_lang: str, target_lang: str, context: dict | None = None
    ) -> str:
        return self.translations.get(text, f"t_{text}")

    def translate_batch(
        self, items: list[dict], source_lang: str, target_lang: str
    ) -> list[str]:
        self.batch_calls.append(list(items))
        return [self.translations.get(i["text"], f"t_{i['text']}") for i in items]


class TestForbiddenValuesPlumbing:
    def test_explicit_forbidden_values_injected_into_context(self) -> None:
        """When constructed with ``forbidden_identifier_values``, every
        identifier item sent to ``translate_batch`` must carry that list
        in its ``context.forbidden_values``.
        """
        backend = _RecordingBackend()
        translator = LLMTranslator(
            keyword_map={"def": "definir", "return": "devolver"},
            builtin_map={"print": "imprimir"},
            backend=backend,
            forbidden_identifier_values=["mismo", "definir", "imprimir"],
        )

        code = "def f():\n    counter = 1\n    return counter\n"
        translator.translate_code(code, source_lang="en", target_lang="es")

        # At least one identifier batch must have been sent.
        identifier_calls = [
            call
            for call in backend.batch_calls
            if call and "kind" not in call[0].get("context", {})
        ]
        assert identifier_calls, (
            "LLMTranslator never made an identifier batch call -- "
            "test setup may be wrong"
        )

        for call in identifier_calls:
            for item in call:
                forbidden = item["context"].get("forbidden_values")
                assert forbidden == ["mismo", "definir", "imprimir"], (
                    f"forbidden_values not threaded into item context: "
                    f"{item['context']!r}"
                )

    def test_default_no_forbidden_values_means_none_in_context(self) -> None:
        """If the caller does not provide ``forbidden_identifier_values``,
        the context entry should be absent (or None) so PromptBuilder
        omits the section entirely.
        """
        backend = _RecordingBackend()
        translator = LLMTranslator(
            keyword_map={"def": "definir", "return": "devolver"},
            builtin_map={"print": "imprimir"},
            backend=backend,
        )

        code = "def f():\n    counter = 1\n    return counter\n"
        translator.translate_code(code, source_lang="en", target_lang="es")

        identifier_calls = [
            call
            for call in backend.batch_calls
            if call and "kind" not in call[0].get("context", {})
        ]
        for call in identifier_calls:
            for item in call:
                forbidden = item["context"].get("forbidden_values")
                assert not forbidden, (
                    f"Expected no forbidden_values when not configured, "
                    f"got {forbidden!r}"
                )

    def test_forbidden_values_not_injected_into_text_items(self) -> None:
        """Text items (comments, docstrings, strings) don't have collision
        risk with reserved Python conventions -- they're free-form prose.
        ``forbidden_values`` belongs only on identifier items.
        """
        backend = _RecordingBackend()
        translator = LLMTranslator(
            keyword_map={"def": "definir", "return": "devolver"},
            builtin_map={"print": "imprimir"},
            backend=backend,
            forbidden_identifier_values=["mismo"],
        )

        code = '"""Module docstring."""\n\ndef f():\n    # leading comment\n    pass\n'
        translator.translate_code(code, source_lang="en", target_lang="es")

        # Find text-element batches.
        text_calls = [
            call
            for call in backend.batch_calls
            if call and "kind" in call[0].get("context", {})
        ]
        for call in text_calls:
            for item in call:
                # Either the key is missing entirely, or empty/None.
                forbidden = item["context"].get("forbidden_values")
                assert not forbidden, (
                    f"Text items should not carry forbidden_values, got {forbidden!r}"
                )
