"""Tests for the no-trace-wrapper rule on provider legacy fallback prompts.

When ``PromptBuilder`` fails to initialize (import-time failure, missing
style guides, etc.), providers fall back to a built-in ``_SYSTEM_PROMPT``
constant. CORE-950 empirical evidence (gemma3:12b zh+ur trace markers,
Tiny Aya GGUF ``____translated_identifier_X____`` residue) showed the
existing legacy text — "no explanations, quotes, or formatting" — is too
weak. The fallback path must explicitly forbid trace-format wrappers.

Anthropic's legacy ``_build_translation_prompt`` is a structured-JSON
prompt that already asserts "Respond ONLY with the JSON object, no
additional text"; trace markers can't appear in valid JSON output, so the
failure mode does not apply there and it stays unchanged.
"""

from __future__ import annotations

from legesher_i18n.api.providers.cohere_aya import (
    _SYSTEM_PROMPT as COHERE_SYSTEM_PROMPT,
)
from legesher_i18n.api.providers.openai_compat import (
    _SYSTEM_PROMPT as OPENAI_SYSTEM_PROMPT,
)


def test_cohere_legacy_forbids_trace_wrappers() -> None:
    rendered = COHERE_SYSTEM_PROMPT.format(source_lang="en", target_lang="ur")
    s = rendered.lower()
    assert "trace" in s or "wrapper" in s, (
        "Cohere legacy _SYSTEM_PROMPT missing the no-trace-wrapper "
        "instruction. Empirical evidence shows weak prompts let "
        "gemma3-class models emit __original_X_translation_Y_ markers "
        "on lower-resource targets."
    )


def test_openai_legacy_forbids_trace_wrappers() -> None:
    rendered = OPENAI_SYSTEM_PROMPT.format(source_lang="en", target_lang="zh")
    s = rendered.lower()
    assert "trace" in s or "wrapper" in s, (
        "OpenAI-compat legacy _SYSTEM_PROMPT missing the no-trace-wrapper instruction."
    )


def test_cohere_legacy_explicitly_calls_out_pattern_examples() -> None:
    """The strongest anchor is naming the failure mode. Pattern examples
    like ``__original_`` and ``____translated_identifier_`` were observed
    in production output; mentioning them by shape steers the model away.
    """
    rendered = COHERE_SYSTEM_PROMPT.format(source_lang="en", target_lang="ur")
    assert "__original_" in rendered or "____translated_identifier_" in rendered, (
        "Legacy prompt should name observed failure-mode patterns to "
        "anchor the model away from them"
    )


def test_format_braces_render_correctly() -> None:
    """Regression: ``.format(source_lang=..., target_lang=...)`` must not
    raise. If the prompt embeds literal braces (e.g., a JSON example),
    they must be escaped as ``{{`` / ``}}``.
    """
    rendered_cohere = COHERE_SYSTEM_PROMPT.format(source_lang="en", target_lang="es")
    rendered_openai = OPENAI_SYSTEM_PROMPT.format(source_lang="en", target_lang="es")
    assert "{source_lang}" not in rendered_cohere
    assert "{target_lang}" not in rendered_openai
    assert "Spanish" in rendered_cohere or "es" in rendered_cohere
