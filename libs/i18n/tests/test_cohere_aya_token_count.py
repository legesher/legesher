"""Tests for the Cohere V2 SDK token-count read path.

Empirical CORE-950 finding: 27 smoke calls during the Cohere integration
test all reported ``tokens_in=0, tokens_out=0`` because ``cohere_aya.py``
read ``response.usage.input_tokens`` / ``output_tokens``, but the
Cohere V2 SDK 6.x exposes tokens under a different attribute path.
This breaks ``get_usage()`` totals and ``cost_estimate_usd``.

The Cohere V2 SDK does not have a public stable contract on this --
different SDK builds expose tokens under either ``usage.tokens`` or
``usage.billed_units``. The fix is a defensive multi-path read that
tries each candidate location in priority order and falls through to
the legacy direct attribute as a last resort.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from legesher_i18n.api.providers.cohere_aya import CohereAyaProvider


def _make_response(usage: object, text: str = "hola") -> MagicMock:
    """Build a fake Cohere V2 chat response with the given usage shape."""
    response = MagicMock()
    response.message.content = [MagicMock(text=text)]
    response.usage = usage
    return response


@pytest.mark.asyncio
async def test_tokens_path_populated(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cohere V2 SDK 6.1.0 builds expose tokens at ``usage.tokens.X``."""
    usage = MagicMock(spec=["tokens"])
    usage.tokens = MagicMock(input_tokens=42, output_tokens=7)

    fake_client = MagicMock()
    fake_client.chat = AsyncMock(return_value=_make_response(usage))

    provider = CohereAyaProvider(api_key="dummy", model="c4ai-aya-expanse-32b")
    monkeypatch.setattr(provider, "_get_client", lambda: fake_client)

    result = await provider.translate("hello", "en", "es")
    assert result.metadata["tokens_in"] == 42
    assert result.metadata["tokens_out"] == 7


@pytest.mark.asyncio
async def test_billed_units_path_populated(monkeypatch: pytest.MonkeyPatch) -> None:
    """Other Cohere V2 SDK builds expose tokens at ``usage.billed_units.X``."""
    usage = MagicMock(spec=["billed_units"])
    usage.billed_units = MagicMock(input_tokens=11, output_tokens=3)

    fake_client = MagicMock()
    fake_client.chat = AsyncMock(return_value=_make_response(usage))

    provider = CohereAyaProvider(api_key="dummy", model="c4ai-aya-expanse-32b")
    monkeypatch.setattr(provider, "_get_client", lambda: fake_client)

    result = await provider.translate("hello", "en", "es")
    assert result.metadata["tokens_in"] == 11
    assert result.metadata["tokens_out"] == 3


@pytest.mark.asyncio
async def test_legacy_direct_attributes_still_supported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Backward compat: pre-V2 SDK shape (``usage.input_tokens``) must
    still populate token counts -- this is the path the existing code
    reads, and downgrading would be a regression for users on older
    SDKs.
    """
    usage = MagicMock(spec=["input_tokens", "output_tokens"])
    usage.input_tokens = 99
    usage.output_tokens = 8

    fake_client = MagicMock()
    fake_client.chat = AsyncMock(return_value=_make_response(usage))

    provider = CohereAyaProvider(api_key="dummy", model="c4ai-aya-expanse-32b")
    monkeypatch.setattr(provider, "_get_client", lambda: fake_client)

    result = await provider.translate("hello", "en", "es")
    assert result.metadata["tokens_in"] == 99
    assert result.metadata["tokens_out"] == 8


@pytest.mark.asyncio
async def test_no_usage_data_yields_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    """If the SDK response has no usage info at all, the read must not
    raise -- we just record zeros.
    """
    usage = MagicMock(spec=[])  # No attributes at all.

    fake_client = MagicMock()
    fake_client.chat = AsyncMock(return_value=_make_response(usage))

    provider = CohereAyaProvider(api_key="dummy", model="c4ai-aya-expanse-32b")
    monkeypatch.setattr(provider, "_get_client", lambda: fake_client)

    result = await provider.translate("hello", "en", "es")
    assert result.metadata["tokens_in"] == 0
    assert result.metadata["tokens_out"] == 0


@pytest.mark.asyncio
async def test_get_usage_after_translations(monkeypatch: pytest.MonkeyPatch) -> None:
    """End-to-end: aggregate get_usage() picks up populated counts so
    characters are counted correctly.
    """
    usage = MagicMock(spec=["tokens"])
    usage.tokens = MagicMock(input_tokens=10, output_tokens=2)

    fake_client = MagicMock()
    fake_client.chat = AsyncMock(return_value=_make_response(usage))

    provider = CohereAyaProvider(api_key="dummy", model="c4ai-aya-expanse-32b")
    monkeypatch.setattr(provider, "_get_client", lambda: fake_client)

    await provider.translate("hello", "en", "es")
    await provider.translate("world", "en", "es")

    stats = await provider.get_usage()
    assert stats is not None
    # 2 calls * (10 + 2) tokens * 4 chars/token = 96 chars
    assert stats.total_characters == 96
    # Characters are measured; price is operator-configured (api/rates.py).
    assert stats.cost_estimate_usd is None
