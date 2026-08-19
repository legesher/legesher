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

# CORE-1804: the language-name map that used to live here (~150 entries
# mixing ISO 639-1 and 639-3) was one of three drifting copies. Names now
# come from languages.json via legesher_i18n.language_names, which carries
# both the 639-1 keys and the iso639_2 aliases.


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
        """Resolve a language code to its human-readable name.

        Profile-level overrides win; otherwise the shared languages.json
        derivation is the single source (CORE-1804).
        """
        if self.language_names:
            return self.language_names.get(code, code.upper())
        from legesher_i18n.language_names import language_name

        return language_name(code)


_SHARED_PROMPT_BUILDER = None


def _shared_prompt_builder():
    """Build (once) the shared PromptBuilder for HF profiles.

    Raises loudly when the style-guide stack is broken — there is no
    legacy prompt to fall back to (CORE-1804), and a silent downgrade is
    exactly the CORE-1354 regression this exists to prevent.
    """
    global _SHARED_PROMPT_BUILDER
    if _SHARED_PROMPT_BUILDER is None:
        try:
            from legesher_i18n.prompt_builder import PromptBuilder
            from legesher_i18n.style_guides import StyleGuideLoader

            _SHARED_PROMPT_BUILDER = PromptBuilder(StyleGuideLoader())
        except Exception as exc:
            raise RuntimeError(
                "PromptBuilder failed to initialize — HF generations "
                "require style-guide-aware prompts (CORE-1354) and have "
                f"no legacy fallback (CORE-1804): {exc}"
            ) from exc
    return _SHARED_PROMPT_BUILDER


def default_prompt_builder(
    request: TranslationRequest,
    profile: HFModelProfile,
) -> str:
    """Build the standard translation prompt for HuggingFace models.

    CORE-1804: delegates to the canonical ``PromptBuilder`` so HF/tiny-aya
    generations receive the same style-guide-aware prompts as every other
    model (the old inline prompt here never applied style guides,
    bypassing CORE-1354). Profile truncation limits still apply to the
    deep-context and linguistic-standards sections; a limit of ``None``
    omits the section, matching the old behavior.

    Args:
        request: Translation request with term, language, and optional context
        profile: Model profile (for truncation settings)

    Returns:
        Formatted prompt string (system + user joined — HF models take a
        single prompt string)
    """
    builder = _shared_prompt_builder()
    system, user = builder.build_term_prompt(
        request.term,
        request.target_language,
        role="keyword",
        deep_context=(
            request.context if profile.context_max_chars is not None else None
        ),
        linguistic_standards=(
            request.linguistic_standards
            if profile.standards_max_chars is not None
            else None
        ),
        context_max_chars=profile.context_max_chars,
        standards_max_chars=profile.standards_max_chars,
    )
    return f"{system}\n\n{user}"


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
