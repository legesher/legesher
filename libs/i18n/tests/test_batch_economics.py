"""Tests for the model-call economics fixes (CORE-1805).

Covers the three leaks:
1. Batch identifier path — O(batches), not O(identifiers), provider calls,
   asserted with a counting mock through the backend adapter.
2. Context-aware cache keys — repeat calls with identical context hit the
   cache; different contexts get distinct entries.
3. Anthropic prompt caching — the static system prompt is sent as a
   cacheable block with ``cache_control``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from legesher_i18n.api.backends import ProviderBackendAdapter
from legesher_i18n.api.cache import CacheBackend, context_fingerprint
from legesher_i18n.api.coordinator import TranslationCoordinator
from legesher_i18n.api.providers.base import (
    TranslationProvider,
    TranslationResult,
)


class CountingBatchProvider(TranslationProvider):
    """Mock provider that counts calls to every model-call surface."""

    name = "counting"
    requires_api_key = False

    def __init__(self):
        self.translate_calls = 0
        self.batch_calls = 0
        self.batch_sizes: list[int] = []

    def is_available(self) -> bool:
        return True

    def supports(self, source_lang: str, target_lang: str) -> bool:
        return True

    async def translate(self, text, source_lang, target_lang, context=None):
        self.translate_calls += 1
        return TranslationResult(
            text=f"t:{text}",
            source_lang=source_lang,
            target_lang=target_lang,
            provider=self.name,
            quality_score=9.0,
            billed_characters=len(text),
        )

    async def translate_batch_with_context(self, items, source_lang, target_lang):
        self.batch_calls += 1
        self.batch_sizes.append(len(items))
        return [
            TranslationResult(
                text=f"t:{item['text']}",
                source_lang=source_lang,
                target_lang=target_lang,
                provider=self.name,
                quality_score=9.0,
                billed_characters=len(item["text"]),
            )
            for item in items
        ]

    async def get_usage(self):
        return None


class DictCache(CacheBackend):
    """In-memory cache used to observe key behavior."""

    def __init__(self):
        self.store: dict[str, str] = {}

    def get(self, text, source_lang, target_lang, context_hash=None):
        return self.store.get(
            self._make_key(text, source_lang, target_lang, context_hash)
        )

    def set(
        self, text, source_lang, target_lang, translation, provider, context_hash=None
    ):
        self.store[self._make_key(text, source_lang, target_lang, context_hash)] = (
            translation
        )

    def clear(self):
        n = len(self.store)
        self.store.clear()
        return n

    def get_stats(self):
        return {"backend": "dict", "total_entries": len(self.store)}


def make_coordinator(provider):
    return TranslationCoordinator(
        providers=[provider],
        cache=DictCache(),
        usage_tracker=None,
    )


def identifier_items(n):
    return [
        {
            "text": f"identifier_{i}",
            "context": {
                "role": "function_name",
                "glossary": {"add": "sumar"},
                "forbidden_values": ["si", "para"],
            },
        }
        for i in range(n)
    ]


class TestBatchIdentifierPath:
    """Leak 1: the batch path must issue O(batches) provider calls."""

    def test_adapter_batch_is_one_provider_call(self):
        """A full batch of context-carrying identifiers = ONE provider call.

        CORE-1805 acceptance: a full-file run issues O(batches), not
        O(identifiers), provider calls — asserted with a counting mock.
        """
        provider = CountingBatchProvider()
        adapter = ProviderBackendAdapter(make_coordinator(provider))

        n = 25
        results = adapter.translate_batch(identifier_items(n), "en", "es")

        assert len(results) == n
        assert results[0] == "t:identifier_0"
        assert provider.batch_calls == 1
        assert provider.batch_sizes == [n]
        assert provider.translate_calls == 0  # never degraded to per-item

    def test_mixed_identifier_and_text_items_stay_batched(self):
        """Mixed kinds still resolve in O(batches) calls, order preserved."""
        provider = CountingBatchProvider()
        adapter = ProviderBackendAdapter(make_coordinator(provider))

        items = identifier_items(3) + [
            {"text": "a comment", "context": {"kind": "comment", "glossary": {}}},
        ]
        results = adapter.translate_batch(items, "en", "es")

        assert results == [
            "t:identifier_0",
            "t:identifier_1",
            "t:identifier_2",
            "t:a comment",
        ]
        # The coordinator hands the whole batch to the provider once; the
        # provider is free to split by kind internally.
        assert provider.batch_calls == 1
        assert provider.translate_calls == 0

    def test_cached_items_do_not_reach_the_provider(self):
        """A repeat batch with identical context is served from cache."""
        provider = CountingBatchProvider()
        coordinator = make_coordinator(provider)
        adapter = ProviderBackendAdapter(coordinator)

        items = identifier_items(5)
        adapter.translate_batch(items, "en", "es")
        adapter.translate_batch(items, "en", "es")

        assert provider.batch_calls == 1  # second run fully cached
        assert provider.translate_calls == 0

    def test_default_provider_batch_falls_back_to_per_item(self):
        """Providers without a batched path still work (base implementation)."""

        class PerItemOnly(CountingBatchProvider):
            async def translate_batch_with_context(
                self, items, source_lang, target_lang
            ):
                return await TranslationProvider.translate_batch_with_context(
                    self, items, source_lang, target_lang
                )

        provider = PerItemOnly()
        adapter = ProviderBackendAdapter(make_coordinator(provider))

        results = adapter.translate_batch(identifier_items(4), "en", "es")

        assert len(results) == 4
        assert provider.translate_calls == 4


class TestContextAwareCacheKeys:
    """Leak 2: context hashes into the cache key instead of bypassing it."""

    def test_fingerprint_is_stable_and_context_sensitive(self):
        ctx_a = {"role": "function_name", "glossary": {"a": "1", "b": "2"}}
        ctx_a_reordered = {"glossary": {"b": "2", "a": "1"}, "role": "function_name"}
        ctx_b = {"role": "variable", "glossary": {"a": "1", "b": "2"}}

        assert context_fingerprint(ctx_a) == context_fingerprint(ctx_a_reordered)
        assert context_fingerprint(ctx_a) != context_fingerprint(ctx_b)
        assert context_fingerprint(None) is None
        assert context_fingerprint({}) is None

    def test_keys_differ_by_context_hash(self):
        base = CacheBackend._make_key("def", "en", "es")
        with_ctx = CacheBackend._make_key("def", "en", "es", "abc123")
        other_ctx = CacheBackend._make_key("def", "en", "es", "def456")

        assert base != with_ctx
        assert with_ctx != other_ctx
        # No-context keys keep the historical shape (existing entries valid)
        assert base == CacheBackend._make_key("def", "en", "es", None)

    @pytest.mark.asyncio
    async def test_repeat_translate_with_identical_context_hits_cache(self):
        provider = CountingBatchProvider()
        coordinator = make_coordinator(provider)
        context = {"role": "function_name", "glossary": {"add": "sumar"}}

        first = await coordinator.translate("compute", "en", "es", context=context)
        second = await coordinator.translate("compute", "en", "es", context=context)

        assert first.text == "t:compute"
        assert second.text == "t:compute"
        assert second.cached is True
        assert provider.translate_calls == 1

    @pytest.mark.asyncio
    async def test_different_context_is_a_different_cache_entry(self):
        provider = CountingBatchProvider()
        coordinator = make_coordinator(provider)

        await coordinator.translate(
            "compute", "en", "es", context={"role": "function_name"}
        )
        result = await coordinator.translate(
            "compute", "en", "es", context={"role": "variable"}
        )

        assert result.cached is False
        assert provider.translate_calls == 2


class TestAnthropicPromptCaching:
    """Leak 3: the static system prompt is sent with cache_control."""

    @pytest.fixture
    def provider(self):
        with patch("legesher_i18n.api.providers.anthropic.AsyncAnthropic"):
            from legesher_i18n.api.providers.anthropic import AnthropicProvider

            return AnthropicProvider(api_key="sk-ant-test-key")

    def _mock_response(self, text='{"translation": "definir"}'):
        response = MagicMock()
        response.content = [MagicMock(text=text)]
        response.usage = MagicMock(
            input_tokens=100,
            output_tokens=20,
            cache_read_input_tokens=80,
            cache_creation_input_tokens=0,
        )
        return response

    @pytest.mark.asyncio
    async def test_system_prompt_carries_cache_control(self, provider):
        provider.client.messages.create = AsyncMock(return_value=self._mock_response())

        await provider.complete("STATIC SYSTEM PROMPT", "user prompt")

        kwargs = provider.client.messages.create.call_args.kwargs
        system = kwargs["system"]
        assert isinstance(system, list)
        assert system[0]["text"] == "STATIC SYSTEM PROMPT"
        assert system[0]["cache_control"] == {"type": "ephemeral"}

    @pytest.mark.asyncio
    async def test_cache_usage_is_accounted(self, provider):
        provider.client.messages.create = AsyncMock(return_value=self._mock_response())

        await provider.complete("STATIC SYSTEM PROMPT", "user prompt")

        assert provider.total_cache_read_tokens == 80
        assert provider.total_cache_creation_tokens == 0

    @pytest.mark.asyncio
    async def test_identifier_batch_is_one_api_call(self, provider):
        """The Anthropic batched path sends ONE request for N identifiers."""
        provider.client.messages.create = AsyncMock(
            return_value=self._mock_response(
                '{"identifier_0": "id_cero", "identifier_1": "id_uno", '
                '"identifier_2": "id_dos"}'
            )
        )

        items = [
            {"text": f"identifier_{i}", "context": {"role": "variable"}}
            for i in range(3)
        ]
        results = await provider.translate_batch_with_context(items, "en", "es")

        assert provider.client.messages.create.await_count == 1
        assert [r.text for r in results] == ["id_cero", "id_uno", "id_dos"]
        # Batch tokens/cost ride on the first result
        assert results[0].metadata["input_tokens"] == 100
        assert "input_tokens" not in results[1].metadata
        assert all(r.metadata["batch_size"] == 3 for r in results)

    @pytest.mark.asyncio
    async def test_identifier_batch_prompt_lists_every_identifier(self, provider):
        """The single request carries the full identifier table."""
        provider.client.messages.create = AsyncMock(
            return_value=self._mock_response('{"alpha": "a", "beta": "b"}')
        )

        items = [
            {"text": "alpha", "context": {"role": "variable"}},
            {"text": "beta", "context": {"role": "variable"}},
        ]
        await provider.translate_batch_with_context(items, "en", "es")

        user_prompt = provider.client.messages.create.call_args.kwargs["messages"][0][
            "content"
        ]
        assert "`alpha`" in user_prompt
        assert "`beta`" in user_prompt
