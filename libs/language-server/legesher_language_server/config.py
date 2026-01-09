"""Configuration management for Legesher Language Server.

This module provides configuration loading from environment variables,
command-line arguments, and defaults for the LSP server.
"""

import logging
import os
import re
import sys

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


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
        default="en", description="Target display language (ISO 639-1 code)"
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

    @field_validator("source_language", "target_language")
    @classmethod
    def validate_language_code(cls, v: str) -> str:
        """Validate language code format (ISO 639-1/639-2).

        Prevents cache pollution and path traversal attempts (CORE-446 security).

        Args:
            v: Language code to validate

        Returns:
            Validated and normalized language code (lowercase)

        Raises:
            ValueError: If language code format is invalid
        """
        if not v:
            raise ValueError("Language code cannot be empty")

        # Check length (2-3 chars for ISO 639-1/639-2)
        if len(v) < 2 or len(v) > 3:
            raise ValueError(f"Language code must be 2-3 characters (ISO 639): '{v}' has {len(v)}")

        # Must be alphabetic only (no path separators, special chars)
        if not v.isalpha():
            raise ValueError(f"Language code must be alphabetic: '{v}' contains invalid characters")

        # Convert to lowercase for consistency
        return v.lower()

    @field_validator("python_version")
    @classmethod
    def validate_python_version(cls, v: str | None) -> str | None:
        """Validate Python version format.

        Args:
            v: Python version string or None

        Returns:
            Validated version string or None

        Raises:
            ValueError: If version format is invalid
        """
        if v is None:
            return v

        # Must match X.Y or X.Y.Z format
        if not re.match(r"^\d+\.\d+(\.\d+)?$", v):
            raise ValueError(f"Invalid Python version format: '{v}' (expected X.Y or X.Y.Z)")

        # Reasonable range check
        parts = v.split(".")
        major, minor = int(parts[0]), int(parts[1])
        if major != 3 or minor < 8 or minor > 20:
            raise ValueError(f"Python version out of supported range: {v}")

        return v

    @field_validator("cache_size")
    @classmethod
    def validate_cache_size(cls, v: int) -> int:
        """Validate cache size to prevent resource exhaustion.

        Args:
            v: Cache size value

        Returns:
            Validated cache size

        Raises:
            ValueError: If cache size is out of acceptable range
        """
        if v < 1 or v > 10000:
            logger.warning(f"Cache size out of range (1-10000): {v}, using 1000")
            return 1000
        return v

    @field_validator("cache_ttl")
    @classmethod
    def validate_cache_ttl(cls, v: int) -> int:
        """Validate cache TTL to prevent resource exhaustion.

        Args:
            v: Cache TTL in seconds

        Returns:
            Validated TTL

        Raises:
            ValueError: If TTL is out of acceptable range
        """
        if v < 0 or v > 86400:  # Max 24 hours
            logger.warning(f"Cache TTL out of range (0-86400): {v}, using 3600")
            return 3600
        return v

    @classmethod
    def from_env(cls) -> "LanguageServerConfig":
        """Load configuration from environment variables with validation.

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

        Note:
            Falls back to safe defaults if environment variables contain invalid values.
            Validation errors are logged as warnings (CORE-446 security).
        """
        try:
            # Parse cache values with error handling
            try:
                cache_size = int(os.getenv("LEGESHER_CACHE_SIZE", "1000"))
            except ValueError:
                logger.warning("Invalid LEGESHER_CACHE_SIZE, using default 1000")
                cache_size = 1000

            try:
                cache_ttl = int(os.getenv("LEGESHER_CACHE_TTL", "3600"))
            except ValueError:
                logger.warning("Invalid LEGESHER_CACHE_TTL, using default 3600")
                cache_ttl = 3600

            return cls(
                source_language=os.getenv("LEGESHER_SOURCE_LANG", "en"),
                target_language=os.getenv("LEGESHER_TARGET_LANG", "en"),
                python_version=os.getenv("LEGESHER_PYTHON_VERSION"),
                cache_size=cache_size,
                cache_ttl=cache_ttl,
                pylance_enabled=os.getenv("LEGESHER_PYLANCE_ENABLED", "true").lower() == "true",
                pylance_path=os.getenv("LEGESHER_PYLANCE_PATH"),
                log_level=os.getenv("LEGESHER_LOG_LEVEL", "INFO"),
            )
        except ValueError as e:
            logger.error(f"Invalid configuration: {e}")
            logger.info("Using safe default configuration")
            # Fall back to safe defaults rather than crash
            return cls()

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
