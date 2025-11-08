"""Pylance/Pyright proxy for Python intelligence with translation.

This module provides a proxy layer between Legesher Language Server and
Pylance (Microsoft's Python language server), enabling advanced Python
intelligence features (type checking, advanced hover, go-to-definition)
while translating between localized keywords and English.

Implementation for CORE-360 - Pylance Integration.
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from lsprotocol.types import (
    Diagnostic,
    Hover,
    HoverParams,
    Position,
    Range,
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

        # JSON-RPC request tracking
        self._request_id = 0
        self._pending_requests: dict[int, asyncio.Future] = {}
        self._reader_task: asyncio.Task | None = None
        self._initialized = False

        # Performance tracking
        self._request_count = 0
        self._total_latency = 0.0

    def _find_language_pack(self, lang: str) -> Path | None:
        """Find language pack directory using multiple strategies.

        Checks:
        1. Development location: libs/i18n-python-{lang}/ (relative to this file)
        2. Installed package: try importing legesher_i18n_python_{lang}
        3. Site-packages: check importlib metadata

        Args:
            lang: Target language code

        Returns:
            Path to language pack directory or None if not found
        """
        from pathlib import Path

        # Strategy 1: Development monorepo structure (libs/ directory)
        dev_pack_dir = Path(__file__).parent.parent.parent / f"i18n-python-{lang}"
        if dev_pack_dir.exists():
            return dev_pack_dir

        # Strategy 2: Try importing the package (works if installed)
        try:
            import importlib.util

            pack_module_name = f"legesher_i18n_python_{lang}"
            spec = importlib.util.find_spec(pack_module_name)
            if spec and spec.origin:
                # Return parent directory of the package
                return Path(spec.origin).parent.parent
        except (ImportError, AttributeError):
            pass

        # Strategy 3: Check site-packages using importlib.metadata
        try:
            import importlib.metadata

            pack_dist_name = f"legesher-i18n-python-{lang}"
            dist = importlib.metadata.distribution(pack_dist_name)
            # Get files from distribution
            if dist.files:
                # Find the packs directory
                for file in dist.files:
                    if "packs" in str(file):
                        return Path(dist.locate_file(file)).parent.parent
        except (ImportError, importlib.metadata.PackageNotFoundError):
            pass

        return None

    def _get_keyword_map(self, lang: str) -> dict[str, str]:
        """Get keyword translation map for language.

        Loads from legesher-i18n language packs dynamically.

        Args:
            lang: Target language code

        Returns:
            Dictionary mapping localized keywords to English
        """
        try:
            import yaml

            # Find language pack using robust discovery
            pack_dir = self._find_language_pack(lang)
            if not pack_dir:
                logger.warning(f"Language pack for '{lang}' not found")
                return {}

            # Load the base pack (3.10 has all keywords)
            pack_file = pack_dir / f"legesher_i18n_python_{lang}" / "packs" / "3.10.yml"

            if pack_file.exists():
                with open(pack_file, encoding="utf-8") as f:
                    pack_data = yaml.safe_load(f)

                # Get keyword translations and reverse them (localized -> English)
                keywords = pack_data.get("keywords", {})
                # Reverse the mapping: English->Spanish becomes Spanish->English
                return {v: k for k, v in keywords.items()}
            else:
                logger.warning(f"Language pack file not found: {pack_file}")

        except Exception as e:
            logger.warning(f"Failed to load language pack for '{lang}': {e}")

        # Fallback: empty dict if pack not found
        return {}

    async def start(self) -> bool:
        """Start Pyright subprocess and initialize LSP connection.

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

            # Start background reader task
            self._reader_task = asyncio.create_task(self._read_responses())

            # Initialize LSP connection
            initialized = await self._initialize_pyright()
            if not initialized:
                logger.error("Failed to initialize Pyright")
                await self.stop()
                return False

            logger.info(f"Pyright server started and initialized: {self.pyright_path}")
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

    async def _initialize_pyright(self) -> bool:
        """Initialize Pyright with LSP initialize handshake.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Send initialize request
            init_params = {
                "processId": os.getpid(),
                "clientInfo": {"name": "legesher", "version": "0.1.0"},
                "rootUri": None,
                "capabilities": {
                    "textDocument": {
                        "hover": {"contentFormat": ["markdown", "plaintext"]},
                        "diagnostic": {"dynamicRegistration": False},
                    }
                },
            }

            response = await self._send_request("initialize", init_params, timeout=10.0)
            if not response or "error" in response:
                logger.error(f"Initialize request failed: {response}")
                return False

            # Send initialized notification
            await self._send_notification("initialized", {})

            self._initialized = True
            logger.debug("Pyright initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Pyright initialization failed: {e}")
            return False

    async def _send_request(self, method: str, params: dict, timeout: float = 5.0) -> dict | None:
        """Send JSON-RPC request to Pyright and wait for response.

        Args:
            method: LSP method name
            params: Method parameters
            timeout: Request timeout in seconds

        Returns:
            Response dictionary or None on error
        """
        if not self.process or not self.process.stdin:
            return None

        # Generate request ID
        self._request_id += 1
        request_id = self._request_id

        # Create JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }

        # Create future for response
        future: asyncio.Future = asyncio.Future()
        self._pending_requests[request_id] = future

        try:
            # Send request
            message = json.dumps(request)
            content = f"Content-Length: {len(message)}\r\n\r\n{message}"
            self.process.stdin.write(content.encode("utf-8"))
            self.process.stdin.flush()

            logger.debug(f"Sent request {request_id}: {method}")

            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=timeout)
            return response

        except asyncio.TimeoutError:
            logger.warning(f"Request {request_id} timed out: {method}")
            self._pending_requests.pop(request_id, None)
            return None
        except Exception as e:
            logger.error(f"Request {request_id} failed: {e}")
            self._pending_requests.pop(request_id, None)
            return None

    async def _send_notification(self, method: str, params: dict) -> None:
        """Send JSON-RPC notification to Pyright (no response expected).

        Args:
            method: LSP method name
            params: Method parameters
        """
        if not self.process or not self.process.stdin:
            return

        # Create JSON-RPC notification (no id field)
        notification = {"jsonrpc": "2.0", "method": method, "params": params}

        try:
            message = json.dumps(notification)
            content = f"Content-Length: {len(message)}\r\n\r\n{message}"
            self.process.stdin.write(content.encode("utf-8"))
            self.process.stdin.flush()

            logger.debug(f"Sent notification: {method}")

        except Exception as e:
            logger.error(f"Failed to send notification {method}: {e}")

    async def _read_responses(self) -> None:
        """Background task to read JSON-RPC responses from Pyright stdout."""
        if not self.process or not self.process.stdout:
            return

        try:
            while self.is_running():
                # Read Content-Length header
                header = await self._read_line()
                if not header:
                    break

                # Parse Content-Length
                if not header.startswith("Content-Length:"):
                    continue

                content_length = int(header.split(":")[1].strip())

                # Read blank line
                await self._read_line()

                # Read message body
                message_bytes = await self._read_bytes(content_length)
                if not message_bytes:
                    break

                # Parse JSON response
                try:
                    response = json.loads(message_bytes.decode("utf-8"))
                    await self._handle_response(response)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")

        except Exception as e:
            logger.error(f"Response reader crashed: {e}")

    async def _read_line(self) -> str:
        """Read a line from Pyright stdout."""
        if not self.process or not self.process.stdout:
            return ""

        try:
            line = self.process.stdout.readline()
            return line.decode("utf-8").strip()
        except Exception:
            return ""

    async def _read_bytes(self, count: int) -> bytes:
        """Read specified number of bytes from Pyright stdout."""
        if not self.process or not self.process.stdout:
            return b""

        try:
            return self.process.stdout.read(count)
        except Exception:
            return b""

    async def _handle_response(self, response: dict) -> None:
        """Handle JSON-RPC response from Pyright.

        Args:
            response: Parsed JSON-RPC response
        """
        # Check if this is a response to our request
        if "id" in response:
            request_id = response["id"]
            future = self._pending_requests.pop(request_id, None)
            if future and not future.done():
                future.set_result(response)
                logger.debug(f"Received response for request {request_id}")
        else:
            # This is a notification from server (e.g., diagnostics)
            logger.debug(f"Received notification: {response.get('method', 'unknown')}")

    async def stop(self) -> None:
        """Stop Pyright subprocess gracefully."""
        # Cancel reader task
        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        # Stop subprocess
        if self.process:
            try:
                # Send shutdown request if initialized
                if self._initialized:
                    await self._send_request("shutdown", {}, timeout=2.0)
                    await self._send_notification("exit", {})

                self.process.terminate()
                self.process.wait(timeout=5)
                logger.info("Pyright server stopped")
            except subprocess.TimeoutExpired:
                # Force kill if not responding
                self.process.kill()
                logger.warning("Pyright server forcefully terminated")
            finally:
                self.process = None
                self._initialized = False

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
        if not self.is_running() or not self._initialized:
            return None

        start_time = time.time()

        try:
            uri = params.text_document.uri
            position = params.position

            # Get document content from cache or translate
            cache_entry = self._document_cache.get(uri)
            if not cache_entry:
                logger.debug(f"Document {uri} not in cache for hover")
                return None

            source_map = cache_entry["source_map"]

            # Translate position to English coordinates
            english_pos = source_map.to_english(
                Position(line=position.line, character=position.character)
            )

            # Send hover request to Pyright
            hover_params = {
                "textDocument": {"uri": uri},
                "position": {"line": english_pos.line, "character": english_pos.character},
            }

            response = await self._send_request("textDocument/hover", hover_params)
            if not response or "error" in response:
                return None

            result = response.get("result")
            if not result:
                return None

            # Translate response position back to original
            if "range" in result:
                eng_range = result["range"]
                start_pos = source_map.to_original(
                    Position(
                        line=eng_range["start"]["line"],
                        character=eng_range["start"]["character"],
                    )
                )
                end_pos = source_map.to_original(
                    Position(
                        line=eng_range["end"]["line"],
                        character=eng_range["end"]["character"],
                    )
                )

                hover_range = Range(
                    start=Position(line=start_pos.line, character=start_pos.character),
                    end=Position(line=end_pos.line, character=end_pos.character),
                )
            else:
                hover_range = None

            # Create Hover object
            hover = Hover(contents=result.get("contents", ""), range=hover_range)

            # Track performance
            elapsed = time.time() - start_time
            self._request_count += 1
            self._total_latency += elapsed

            logger.debug(f"Hover completed in {elapsed * 1000:.1f}ms")
            return hover

        except Exception as e:
            logger.error(f"Hover forward failed: {e}")
            return None

    async def forward_diagnostic(self, uri: str, content: str) -> list[Diagnostic]:
        """Forward diagnostic request to Pylance with translation.

        Args:
            uri: Document URI
            content: Document content in localized language

        Returns:
            List of diagnostics with translated messages
        """
        if not self.is_running() or not self._initialized:
            return []

        try:
            # Translate document to English
            result = await self.translator.translate_to_english(content)

            # Cache translation
            self._document_cache[uri] = {
                "translated": result.translated_code,
                "source_map": result.source_map,
                "hash": result.content_hash,
            }

            # Send didOpen to sync document with Pyright
            await self._send_notification(
                "textDocument/didOpen",
                {
                    "textDocument": {
                        "uri": uri,
                        "languageId": "python",
                        "version": 1,
                        "text": result.translated_code,
                    }
                },
            )

            # Request diagnostics
            diag_params = {"textDocument": {"uri": uri}}
            response = await self._send_request("textDocument/diagnostic", diag_params)

            if not response or "error" in response:
                return []

            result_data = response.get("result", {})
            items = result_data.get("items", [])

            # Translate diagnostics back to original positions
            diagnostics = []
            source_map = self._document_cache[uri]["source_map"]

            for item in items:
                # Translate range
                eng_range = item["range"]
                start_pos = source_map.to_original(
                    Position(
                        line=eng_range["start"]["line"],
                        character=eng_range["start"]["character"],
                    )
                )
                end_pos = source_map.to_original(
                    Position(
                        line=eng_range["end"]["line"],
                        character=eng_range["end"]["character"],
                    )
                )

                diag_range = Range(
                    start=Position(line=start_pos.line, character=start_pos.character),
                    end=Position(line=end_pos.line, character=end_pos.character),
                )

                # Create diagnostic
                # TODO: Translate message using error_templates.py
                diagnostic = Diagnostic(
                    range=diag_range,
                    message=item.get("message", ""),
                    severity=item.get("severity", 1),
                    source="pylance",
                )

                diagnostics.append(diagnostic)

            return diagnostics

        except Exception as e:
            logger.error(f"Diagnostic forward failed: {e}")
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
            "initialized": self._initialized,
        }

    def clear_caches(self) -> None:
        """Clear all caches."""
        self._document_cache.clear()
        self.translator.clear_cache()
        logger.debug("Caches cleared")

    def __repr__(self) -> str:
        """String representation."""
        status = "running" if self.is_running() else "stopped"
        init_status = "initialized" if self._initialized else "not initialized"
        return f"PylanceProxy(status={status}, {init_status}, path={self.pyright_path})"
