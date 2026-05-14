"""Tests for the Cohere Aya error-message fidelity upgrade (CORE-870).

Empirical AYA-213 finding: during a 10-file cond5 c=8 run on 2026-05-14,
18 of the 28 logged failures rendered as ``Cohere Aya translation failed:``
with nothing after the colon. The original code at the except block did
``logger.error("Cohere Aya translation failed: %s", e)`` which calls
``str(e)``, and some cohere SDK exception types have an empty ``str()``
because their message lives on ``.body`` / ``.message`` attributes.

This file verifies that the upgraded except block always produces a
non-empty, actionable error string — including the exception class name,
``status_code`` when present, and the Cohere debug trace ID when the
exception carries response headers.
"""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from legesher_i18n.api.providers.base import TranslationError
from legesher_i18n.api.providers.cohere_aya import CohereAyaProvider


class _EmptyStrError(Exception):
    """Stand-in for a cohere SDK exception whose ``str()`` is empty."""

    def __str__(self) -> str:
        return ""


class _ApiErrorLike(Exception):
    """Stand-in for ``cohere.core.api_error.ApiError`` shape.

    The real SDK error has ``status_code`` and ``headers`` attributes and an
    empty ``str()``. We mirror that surface here without importing cohere.
    """

    def __init__(self, status_code: int, headers: dict | None = None) -> None:
        super().__init__()
        self.status_code = status_code
        self.headers = headers or {}

    def __str__(self) -> str:
        return ""


@pytest.mark.asyncio
async def test_empty_str_exception_surfaces_class_name(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """When str(e) is empty, the log + raised error must include type(e).__name__."""
    fake_client = MagicMock()
    fake_client.chat = AsyncMock(side_effect=_EmptyStrError())

    provider = CohereAyaProvider(api_key="dummy", model="c4ai-aya-expanse-32b")
    monkeypatch.setattr(provider, "_get_client", lambda: fake_client)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(TranslationError) as exc_info:
            await provider.translate("hello", "en", "es")

    log_text = "\n".join(r.getMessage() for r in caplog.records)
    assert "_EmptyStrError" in log_text
    assert "_EmptyStrError" in str(exc_info.value)
    # The body must not be just the colon
    assert not str(exc_info.value).rstrip().endswith(":")


@pytest.mark.asyncio
async def test_api_error_surfaces_status_code_and_trace_id(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """ApiError-shaped exceptions must surface status_code and trace_id."""
    err = _ApiErrorLike(
        status_code=503,
        headers={"x-debug-trace-id": "trace_abc123"},
    )
    fake_client = MagicMock()
    fake_client.chat = AsyncMock(side_effect=err)

    provider = CohereAyaProvider(api_key="dummy", model="c4ai-aya-expanse-32b")
    monkeypatch.setattr(provider, "_get_client", lambda: fake_client)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(TranslationError) as exc_info:
            await provider.translate("hello", "en", "es")

    body = str(exc_info.value)
    assert "_ApiErrorLike" in body
    assert "status_code=503" in body
    assert "trace_id=trace_abc123" in body

    log_text = "\n".join(r.getMessage() for r in caplog.records)
    assert "status_code=503" in log_text
    assert "trace_id=trace_abc123" in log_text


@pytest.mark.asyncio
async def test_exception_with_nonempty_str_still_works(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Non-empty str(e) (e.g. ConnectionError) must still appear in the body."""
    err = ConnectionError("All connection attempts failed")
    fake_client = MagicMock()
    fake_client.chat = AsyncMock(side_effect=err)

    provider = CohereAyaProvider(api_key="dummy", model="c4ai-aya-expanse-32b")
    monkeypatch.setattr(provider, "_get_client", lambda: fake_client)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(TranslationError) as exc_info:
            await provider.translate("hello", "en", "es")

    body = str(exc_info.value)
    assert "ConnectionError" in body
    assert "All connection attempts failed" in body


@pytest.mark.asyncio
async def test_logging_is_defensive_against_broken_headers(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """An exception with malformed metadata must not break logging itself."""

    class _BrokenAttrError(Exception):
        @property
        def status_code(self) -> int:
            raise RuntimeError("nope")

        @property
        def headers(self) -> dict:
            raise RuntimeError("also nope")

        def __str__(self) -> str:
            return ""

    fake_client = MagicMock()
    fake_client.chat = AsyncMock(side_effect=_BrokenAttrError())

    provider = CohereAyaProvider(api_key="dummy", model="c4ai-aya-expanse-32b")
    monkeypatch.setattr(provider, "_get_client", lambda: fake_client)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(TranslationError) as exc_info:
            await provider.translate("hello", "en", "es")

    # Class name must still appear; logging must not have raised.
    assert "_BrokenAttrError" in str(exc_info.value)
