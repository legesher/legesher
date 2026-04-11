"""Backend adapter bridging async TranslationCoordinator to sync TextTranslationBackend.

This module provides the ProviderBackendAdapter that wraps the async
TranslationCoordinator into the synchronous TextTranslationBackend protocol
defined in legesher-core. This allows any TranslationProvider to be used
as an LLM backend for full code translation.
"""

import asyncio
import concurrent.futures
import logging
from typing import Any

from .coordinator import TranslationCoordinator

logger = logging.getLogger(__name__)

# Shared thread pool for running async coroutines from sync contexts
# Cached to avoid creating a new pool per call
_THREAD_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=2)


def _run_async(coro):
    """Run an async coroutine synchronously, handling existing event loops."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        # We're inside an existing event loop — use shared thread pool
        future = _THREAD_POOL.submit(asyncio.run, coro)
        return future.result()
    else:
        return asyncio.run(coro)


class ProviderBackendAdapter:
    """Adapts async TranslationCoordinator to sync TextTranslationBackend.

    This adapter implements the TextTranslationBackend protocol from
    legesher-core, allowing any configured TranslationProvider to be
    used as an LLM backend for the LLMTranslator.

    The adapter handles the async-to-sync conversion, event loop
    detection, and batch translation coordination.

    Example:
        >>> from legesher_i18n.api import TranslationCoordinator
        >>> from legesher_i18n.api.providers import AnthropicProvider
        >>>
        >>> coordinator = TranslationCoordinator(
        ...     providers=[AnthropicProvider(api_key="...")],
        ... )
        >>> backend = ProviderBackendAdapter(coordinator)
        >>>
        >>> # Use with LLMTranslator
        >>> from legesher_core import create_translator
        >>> translator = create_translator("python", kw_map, bi_map, backend=backend)
    """

    def __init__(
        self,
        coordinator: TranslationCoordinator,
        preferred_provider: str | None = None,
    ) -> None:
        """Initialize the adapter.

        Args:
            coordinator: Configured TranslationCoordinator with providers
            preferred_provider: Optional provider name to prefer
        """
        self._coordinator = coordinator
        self._preferred_provider = preferred_provider

    def translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Translate a single piece of text synchronously.

        Wraps the async coordinator.translate() call.
        """
        result = _run_async(
            self._coordinator.translate(
                text=text,
                source_lang=source_lang,
                target_lang=target_lang,
                preferred_provider=self._preferred_provider,
                context=context,
            )
        )
        return result.text

    def translate_batch(
        self,
        items: list[dict[str, Any]],
        source_lang: str,
        target_lang: str,
    ) -> list[str]:
        """Translate a batch of items synchronously.

        When items carry context (glossary, kind, role), translates each
        item individually so per-item context reaches the provider via
        the PromptBuilder.  Falls back to the coordinator's batch API
        when no context is present, preserving batching performance.
        """
        # Only use per-item path when context carries PromptBuilder-relevant
        # data (glossary, element kind, or identifier role).
        # Empty context dicts use the fast batch path.
        has_prompt_context = any(
            item.get("context", {}).get("glossary")
            or item.get("context", {}).get("kind")
            or item.get("context", {}).get("role")
            for item in items
        )

        if not has_prompt_context:
            # Fast path: no context to forward, use batch API
            texts = [item["text"] for item in items]
            results = _run_async(
                self._coordinator.translate_batch(
                    texts=texts,
                    source_lang=source_lang,
                    target_lang=target_lang,
                )
            )
            return [
                r.text if r.text and r.provider != "error" else original
                for r, original in zip(results, texts)
            ]

        # Per-item path: forward context to providers
        results = []
        for item in items:
            text = item["text"]
            context = item.get("context")
            try:
                result = _run_async(
                    self._coordinator.translate(
                        text=text,
                        source_lang=source_lang,
                        target_lang=target_lang,
                        preferred_provider=self._preferred_provider,
                        context=context,
                    )
                )
                if result.text and result.provider != "error":
                    results.append(result.text)
                else:
                    results.append(text)
            except Exception:
                logger.warning("Translation failed for item: %s...", text[:50])
                results.append(text)
        return results
