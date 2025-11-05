"""Configuration management for Legesher Language Server.

This module provides configuration loading from environment variables,
command-line arguments, and defaults for the LSP server.
"""

import os
import sys

from pydantic import BaseModel, Field


class LanguageServerConfig(BaseModel):
    """Configuration for Legesher Language Server.

    Attributes:
        source_language: Source code language (default: 'en' for English)
        target_language: Target display language for translation
        python_version: Python version for language pack selection (auto-detected if None)
        cache_size: Maximum number of cached translations (LRU cache)
        cache_ttl: Time-to-live for cache entries in seconds
        pylance_enabled: Whether to enable Pylance proxy integration
        pylance_path: Path to Pylance language server executable
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """

    # Language configuration
    source_language: str = Field(default="en", description="Source code language (ISO 639-1 code)")
    target_language: str = Field(
        default="es", description="Target display language (ISO 639-1 code)"
    )

    # Python configuration
    python_version: str | None = Field(
        default=None, description="Python version (e.g., '3.10', '3.11'). Auto-detected if None."
    )

    # Performance configuration
    cache_size: int = Field(default=1000, ge=1, description="Maximum number of cached translations")
    cache_ttl: int = Field(
        default=3600, ge=0, description="Cache time-to-live in seconds (0 = no expiration)"
    )

    # Pylance integration (CORE-360)
    pylance_enabled: bool = Field(default=True, description="Enable Pylance proxy integration")
    pylance_path: str | None = Field(
        default=None, description="Path to Pylance server (auto-detected if None)"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    @classmethod
    def from_env(cls) -> "LanguageServerConfig":
        """Load configuration from environment variables.

        Environment variables:
            LEGESHER_SOURCE_LANG: Source language code
            LEGESHER_TARGET_LANG: Target language code
            LEGESHER_PYTHON_VERSION: Python version
            LEGESHER_CACHE_SIZE: Cache size
            LEGESHER_CACHE_TTL: Cache TTL in seconds
            LEGESHER_PYLANCE_ENABLED: Enable Pylance (true/false)
            LEGESHER_PYLANCE_PATH: Path to Pylance
            LEGESHER_LOG_LEVEL: Logging level

        Returns:
            Configured LanguageServerConfig instance
        """
        return cls(
            source_language=os.getenv("LEGESHER_SOURCE_LANG", "en"),
            target_language=os.getenv("LEGESHER_TARGET_LANG", "es"),
            python_version=os.getenv("LEGESHER_PYTHON_VERSION"),
            cache_size=int(os.getenv("LEGESHER_CACHE_SIZE", "1000")),
            cache_ttl=int(os.getenv("LEGESHER_CACHE_TTL", "3600")),
            pylance_enabled=os.getenv("LEGESHER_PYLANCE_ENABLED", "true").lower() == "true",
            pylance_path=os.getenv("LEGESHER_PYLANCE_PATH"),
            log_level=os.getenv("LEGESHER_LOG_LEVEL", "INFO"),
        )

    def detect_python_version(self) -> str:
        """Detect or return configured Python version.

        Returns:
            Python version string (e.g., '3.10', '3.11')
        """
        if self.python_version:
            return self.python_version

        # Use runtime version
        return f"{sys.version_info.major}.{sys.version_info.minor}"

    def validate_languages(self) -> bool:
        """Validate that language codes are valid ISO 639-1 codes.

        Returns:
            True if both languages are valid 2-letter codes
        """
        return (
            len(self.source_language) == 2
            and len(self.target_language) == 2
            and self.source_language.isalpha()
            and self.target_language.isalpha()
        )
