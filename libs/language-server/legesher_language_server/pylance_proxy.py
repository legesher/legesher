"""Pylance/Pyright proxy for Python intelligence with translation.

This module provides a proxy layer between Legesher Language Server and
Pylance (Microsoft's Python language server), enabling advanced Python
intelligence features (type checking, advanced hover, go-to-definition)
while translating between localized keywords and English.

Implementation for CORE-360 - Pylance Integration.
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from lsprotocol.types import (
    Diagnostic,
    Hover,
    HoverParams,
)

from .config import LanguageServerConfig
from .incremental_translator import IncrementalTranslator

logger = logging.getLogger(__name__)


class PylanceProxy:
    """Proxy to Pylance/Pyright for Python intelligence.

    This class manages a Pyright subprocess and translates LSP requests/
    responses between localized code and English, enabling Pylance features
    to work with non-English keywords.

    Architecture:
        User Code (Spanish) →  Translate to English  → Pylance
                                                        ↓
        User IDE (Spanish)  ←  Translate to Spanish  ← Pylance Response

    Example:
        >>> proxy = PylanceProxy(config)
        >>> await proxy.start()
        >>> if proxy.is_running():
        ...     hover = await proxy.forward_hover(params)
    """

    def __init__(self, config: LanguageServerConfig):
        """Initialize Pylance proxy.

        Args:
            config: Language server configuration
        """
        self.config = config
        self.process: subprocess.Popen | None = None
        self.pyright_path: str | None = None

        # Translation engine
        # TODO: Load actual keyword maps from legesher-i18n
        self.translator = IncrementalTranslator(
            source_lang=config.source_language,
            target_lang=config.target_language,
            keyword_map=self._get_keyword_map(config.target_language),
            builtin_map={},  # Optional: translate builtins
        )

        # Document cache: uri -> (translated_content, source_map)
        self._document_cache: dict[str, Any] = {}

        # Performance tracking
        self._request_count = 0
        self._total_latency = 0.0

    def _get_keyword_map(self, lang: str) -> dict[str, str]:
        """Get keyword translation map for language.

        TODO: Load from legesher-i18n language packs

        Args:
            lang: Target language code

        Returns:
            Dictionary mapping localized keywords to English
        """
        if lang == "es":
            return {
                "definir": "def",
                "clase": "class",
                "retornar": "return",
                "si": "if",
                "sino": "elif",
                "si_no": "else",
                "mientras": "while",
                "para": "for",
                "en": "in",
                "romper": "break",
                "continuar": "continue",
                "pasar": "pass",
                "intentar": "try",
                "excepto": "except",
                "finalmente": "finally",
                "elevar": "raise",
                "asertir": "assert",
                "importar": "import",
                "desde": "from",
                "como": "as",
                "global": "global",
                "no_local": "nonlocal",
                "lambda": "lambda",
                "con": "with",
                "rendimiento": "yield",
                "eliminar": "del",
                "verdadero": "True",
                "falso": "False",
                "nulo": "None",
                "y": "and",
                "o": "or",
                "no": "not",
                "es": "is",
            }
        elif lang == "ar":
            return {
                "تعريف": "def",
                "صنف": "class",
                "إرجاع": "return",
                "إذا": "if",
                "وإلا_إذا": "elif",
                "وإلا": "else",
                "بينما": "while",
                "لكل": "for",
                "في": "in",
                "كسر": "break",
                "متابعة": "continue",
                "تمرير": "pass",
            }
        else:
            return {}

    async def start(self) -> bool:
        """Start Pyright subprocess.

        Returns:
            True if successfully started, False otherwise
        """
        if not self.config.pylance_enabled:
            logger.info("Pylance integration disabled in config")
            return False

        # Find Pyright installation
        self.pyright_path = self._find_pyright()
        if not self.pyright_path:
            logger.warning(
                "Pyright not found. Install with: npm install -g pyright\n"
                "Pylance features will not be available."
            )
            return False

        try:
            # Start Pyright in LSP server mode
            self.process = subprocess.Popen(
                [self.pyright_path, "--stdio"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,  # Binary mode for proper encoding
            )

            logger.info(f"Pyright server started: {self.pyright_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to start Pyright: {e}")
            self.process = None
            return False

    def _find_pyright(self) -> str | None:
        """Find Pyright installation.

        Checks:
        1. Configured path (config.pylance_path)
        2. npm global installation
        3. System PATH

        Returns:
            Path to Pyright executable or None if not found
        """
        # Check configured path first
        if self.config.pylance_path:
            if os.path.isfile(self.config.pylance_path):
                return self.config.pylance_path

        # Check npm global installation
        npm_global = shutil.which("pyright")
        if npm_global:
            return npm_global

        # Check common installation locations
        common_paths = [
            "/usr/local/bin/pyright",
            "/usr/bin/pyright",
            str(Path.home() / ".local/bin/pyright"),
            str(Path.home() / ".npm-global/bin/pyright"),
        ]

        for path in common_paths:
            if os.path.isfile(path):
                return path

        return None

    async def stop(self) -> None:
        """Stop Pyright subprocess gracefully."""
        if self.process:
            try:
                # Send shutdown request first
                self.process.terminate()
                self.process.wait(timeout=5)
                logger.info("Pyright server stopped")
            except subprocess.TimeoutExpired:
                # Force kill if not responding
                self.process.kill()
                logger.warning("Pyright server forcefully terminated")
            finally:
                self.process = None

    def is_running(self) -> bool:
        """Check if Pyright subprocess is running.

        Returns:
            True if process is alive, False otherwise
        """
        return self.process is not None and self.process.poll() is None

    async def forward_hover(self, params: HoverParams) -> Hover | None:
        """Forward hover request to Pylance with translation.

        Args:
            params: Hover request parameters

        Returns:
            Hover information or None if not available
        """
        if not self.is_running():
            return None

        # TODO: Implement full LSP communication
        # For now, return None to fallback to basic hover provider
        logger.debug(f"Pylance hover forward not yet implemented: {params.text_document.uri}")
        return None

    async def forward_diagnostic(self, uri: str, content: str) -> list[Diagnostic]:
        """Forward diagnostic request to Pylance with translation.

        Args:
            uri: Document URI
            content: Document content in localized language

        Returns:
            List of diagnostics with translated messages
        """
        if not self.is_running():
            return []

        # TODO: Implement full LSP communication
        # For now, return empty list to fallback to basic diagnostic provider
        logger.debug(f"Pylance diagnostic forward not yet implemented: {uri}")
        return []

    async def translate_document_for_pylance(self, uri: str, content: str) -> str | None:
        """Translate document content for Pylance.

        Args:
            uri: Document URI
            content: Original content in localized language

        Returns:
            Translated content in English or None on error
        """
        try:
            result = await self.translator.translate_to_english(content)

            # Cache for future position mappings
            self._document_cache[uri] = {
                "translated": result.translated_code,
                "source_map": result.source_map,
                "hash": result.content_hash,
            }

            return result.translated_code

        except Exception as e:
            logger.error(f"Translation failed for {uri}: {e}")
            return None

    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics.

        Returns:
            Dictionary with performance metrics
        """
        avg_latency = self._total_latency / self._request_count if self._request_count > 0 else 0

        return {
            "request_count": self._request_count,
            "total_latency_ms": self._total_latency * 1000,
            "average_latency_ms": avg_latency * 1000,
            "cache_size": len(self._document_cache),
            "translation_cache_size": self.translator.get_cache_size(),
        }

    def clear_caches(self) -> None:
        """Clear all caches."""
        self._document_cache.clear()
        self.translator.clear_cache()
        logger.debug("Caches cleared")

    def __repr__(self) -> str:
        """String representation."""
        status = "running" if self.is_running() else "stopped"
        return f"PylanceProxy(status={status}, path={self.pyright_path})"
