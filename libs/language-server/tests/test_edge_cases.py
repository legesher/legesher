"""Edge case tests for Pylance integration robustness.

Tests error handling, cleanup, and graceful degradation scenarios.
"""

import pytest

from legesher_language_server.config import LanguageServerConfig
from legesher_language_server.pylance_proxy import PylanceProxy


class TestCacheCleanup:
    """Test cache management and cleanup."""

    @pytest.mark.asyncio
    async def test_clear_caches_removes_documents(self):
        """Test that clear_caches cleans up document cache."""
        config = LanguageServerConfig(
            source_language="es", target_language="en", pylance_enabled=True
        )

        proxy = PylanceProxy(config)

        # Add document to cache
        uri = "file:///test.py"
        spanish_code = "definir foo():\n    pasar"
        await proxy.translate_document_for_pylance(uri, spanish_code)

        # Verify it's in cache
        assert uri in proxy._document_cache

        # Clear caches
        proxy.clear_caches()

        # Verify it's gone
        assert uri not in proxy._document_cache

    @pytest.mark.asyncio
    async def test_clear_caches_idempotent(self):
        """Test that clearing empty cache doesn't error."""
        config = LanguageServerConfig(
            source_language="es", target_language="en", pylance_enabled=True
        )

        proxy = PylanceProxy(config)

        # Should not raise error when cache is empty
        proxy.clear_caches()
        proxy.clear_caches()  # Second call should also be safe


class TestErrorHandling:
    """Test error handling in translation."""

    @pytest.mark.asyncio
    async def test_translate_invalid_code_returns_gracefully(self):
        """Test that invalid code is handled gracefully."""
        config = LanguageServerConfig(
            source_language="es", target_language="en", pylance_enabled=True
        )

        proxy = PylanceProxy(config)

        # Invalid Python syntax - tokenizer handles gracefully by returning unchanged
        result = await proxy.translate_document_for_pylance(
            "file:///test.py", "!!!! invalid syntax !!!!"
        )

        # Should return the code (unchanged since no keywords to translate)
        # The important thing is it doesn't crash
        assert result is not None


class TestStopCleanup:
    """Test stop() method cleanup."""

    @pytest.mark.asyncio
    async def test_stop_without_start_no_error(self):
        """Test that stop() without start() doesn't error."""
        config = LanguageServerConfig(
            source_language="es", target_language="en", pylance_enabled=True
        )

        proxy = PylanceProxy(config)

        # Should not raise error
        await proxy.stop()

    @pytest.mark.asyncio
    async def test_stop_idempotent(self):
        """Test that calling stop() multiple times is safe."""
        config = LanguageServerConfig(
            source_language="es", target_language="en", pylance_enabled=True
        )

        proxy = PylanceProxy(config)

        # Multiple stops should not raise errors
        await proxy.stop()
        await proxy.stop()
        await proxy.stop()


class TestGracefulDegradation:
    """Test graceful degradation when Pylance unavailable."""

    @pytest.mark.asyncio
    async def test_hover_when_not_running_returns_none(self):
        """Test that hover returns None when proxy not running."""
        from lsprotocol.types import HoverParams, Position, TextDocumentIdentifier

        config = LanguageServerConfig(
            source_language="es", target_language="en", pylance_enabled=True
        )

        proxy = PylanceProxy(config)

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///test.py"),
            position=Position(line=0, character=0),
        )

        hover = await proxy.forward_hover(params)

        # Should return None gracefully
        assert hover is None

    @pytest.mark.asyncio
    async def test_diagnostic_when_not_running_returns_empty(self):
        """Test that diagnostics return empty list when proxy not running."""
        config = LanguageServerConfig(
            source_language="es", target_language="en", pylance_enabled=True
        )

        proxy = PylanceProxy(config)

        diagnostics = await proxy.forward_diagnostic("file:///test.py", "definir foo():\n    pasar")

        # Should return empty list gracefully
        assert diagnostics == []


class TestDocumentLifecycleWithFailure:
    """Test complete document lifecycle with Pylance failures."""

    @pytest.mark.asyncio
    async def test_document_lifecycle_with_pylance_stopped(self):
        """Test complete lifecycle when Pylance is not running.

        Scenario:
        1. Create proxy without starting Pylance
        2. Translate documents (should work using translator directly)
        3. Verify cache is populated
        4. Clear cache (cleanup)
        """
        config = LanguageServerConfig(
            source_language="es", target_language="en", pylance_enabled=True
        )

        proxy = PylanceProxy(config)

        uri = "file:///test.py"
        spanish_code_v1 = "definir foo():\n    pasar"

        # Step 1: Translate without Pylance running
        result = await proxy.translate_document_for_pylance(uri, spanish_code_v1)

        # Should still return translated code (using translator directly)
        assert result is not None
        assert uri in proxy._document_cache

        # Step 2: Change document
        spanish_code_v2 = "definir foo():\n    retornar 42"
        result = await proxy.translate_document_for_pylance(uri, spanish_code_v2)

        # Should still work
        assert result is not None

        # Step 3: Cleanup cache gracefully
        proxy.clear_caches()
        assert uri not in proxy._document_cache

        # Verify no exceptions were raised and proxy remains functional

    @pytest.mark.asyncio
    async def test_concurrent_failures_dont_crash(self):
        """Test that multiple concurrent failures don't crash the server."""
        import asyncio

        config = LanguageServerConfig(
            source_language="es", target_language="en", pylance_enabled=True
        )

        proxy = PylanceProxy(config)

        # Create multiple translation tasks that will all "fail"
        # (since Pylance isn't actually running)
        tasks = []
        for i in range(10):
            uri = f"file:///test{i}.py"
            code = f"definir test{i}():\n    pasar"
            tasks.append(proxy.translate_document_for_pylance(uri, code))

        # All should complete without crashing
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # All should return translated code
        assert len(results) == 10
        assert all(r is not None for r in results)

        # Cache should have all documents
        assert len(proxy._document_cache) == 10

    @pytest.mark.asyncio
    async def test_stop_after_translation_cleans_up(self):
        """Test that stop() after translations still works properly."""
        config = LanguageServerConfig(
            source_language="es", target_language="en", pylance_enabled=True
        )

        proxy = PylanceProxy(config)

        # Translate some documents
        await proxy.translate_document_for_pylance("file:///test1.py", "definir foo(): pasar")
        await proxy.translate_document_for_pylance("file:///test2.py", "definir bar(): pasar")

        # Verify documents are cached
        assert len(proxy._document_cache) == 2

        # Stop should complete without error
        await proxy.stop()

        # Note: document cache is NOT cleared by stop() - that's intentional
        # Cache remains for potential restart
        assert len(proxy._document_cache) == 2
