"""Configuration management for Legesher Language Server.

This module provides configuration loading from environment variables,
command-line arguments, and defaults for the LSP server.
"""

import logging
import os
import re
import sys

from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


# Settings renamed in CORE-1890, mapped to what replaced them. Deliberately not
# honoured — the rename ships without aliases because nothing is published and a
# compatibility layer would be debt with no debtor. Kept at module level rather
# than on the model: pydantic reinterprets underscore-prefixed class attributes
# as private attributes, which are not plain dicts.
RETIRED_ENV_VARS = {
    "LEGESHER_PYLANCE_ENABLED": "LEGESHER_ENHANCED_INTELLIGENCE_ENABLED",
    "LEGESHER_PYLANCE_PATH": "LEGESHER_LANGUAGE_SERVER_PATH",
}


class LanguageServerConfig(BaseModel):
    """Configuration for Legesher Language Server.

    Attributes:
        source_language: Canonical language the project's code is stored in
            (default: 'en' for English)
        target_language: Deprecated single slot for "the other language"; kept
            in lockstep with file_language so code written against it keeps
            working (CORE-1760)
        file_language: Language a file is written in unless the client says
            otherwise. Each document's own language arrives in a
            ``legesher/documentLanguage`` notification; this is the fallback
            for any document the client has not named (CORE-1976)
        working_language: Language the user reads and writes in right now —
            what hover and other render surfaces should target
        python_version: Python version for language pack selection (auto-detected if None)
        cache_size: Maximum number of cached translations (LRU cache)
        cache_ttl: Time-to-live for cache entries in seconds
        enhanced_intelligence_enabled: Whether to enable enhanced Python intelligence
        language_server_path: Path to the Python language server executable
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """

    # Language configuration (CORE-1760: the roles are named — canonical /
    # file / working — because one "target" slot cannot say both what a file
    # is written in and what the user wants to read in.)
    source_language: str = Field(default="en", description="Source code language (ISO 639-1 code)")
    target_language: str = Field(
        default="en",
        description="Deprecated alias kept in lockstep with file_language (ISO 639-1 code)",
    )
    file_language: str = Field(
        default="en",
        description="Language of any document the client has not named (ISO 639-1 code)",
    )
    working_language: str = Field(
        default="en",
        description="Language the user reads and writes in right now (ISO 639-1 code)",
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

    # Enhanced Python intelligence (CORE-360, CORE-1890)
    enhanced_intelligence_enabled: bool = Field(
        default=True, description="Enable enhanced Python intelligence"
    )
    language_server_path: str | None = Field(
        default=None, description="Path to the Python language server (auto-detected if None)"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    @field_validator("source_language", "target_language", "file_language", "working_language")
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

    @model_validator(mode="after")
    def keep_file_language_in_lockstep(self) -> "LanguageServerConfig":
        """Hold the deprecated slot and the file-language role together from construction.

        The entry points keep them in lockstep, but a model built directly with
        only ``target_language`` left ``file_language`` at "en". That was
        harmless while providers read the deprecated slot. They now serve each
        document in its own language and fall back to ``file_language``
        (CORE-1976), so a configuration written the old way would be served in
        English with nothing to say so. Whichever of the two is given seeds
        the other; when both are given, both are kept as given.
        """
        given = self.model_fields_set
        if "target_language" in given and "file_language" not in given:
            self.file_language = self.target_language
        elif "file_language" in given and "target_language" not in given:
            self.target_language = self.file_language
        return self

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
    def _warn_about_retired_variables(cls) -> None:
        """Say when a retired setting is present but no longer read.

        Dropping the old names is the right call, but dropping them *silently*
        is not: someone who set ``LEGESHER_PYLANCE_ENABLED=false`` would find
        the feature switched back on, because the replacement defaults to true.
        The value is not honoured — that would reintroduce the alias we
        deliberately avoided — but its presence is announced, so the change is
        something a user can see rather than something they discover.
        """
        for retired, replacement in RETIRED_ENV_VARS.items():
            if retired in os.environ:
                logger.warning(
                    f"{retired} is set but no longer read; it was renamed to "
                    f"{replacement} (CORE-1890). The old value is being ignored — "
                    "set the new variable to keep your configuration."
                )

    @classmethod
    def from_env(cls) -> "LanguageServerConfig":
        """Load configuration from environment variables with validation.

        Environment variables:
            LEGESHER_SOURCE_LANG: Source language code
            LEGESHER_TARGET_LANG: Target language code
            LEGESHER_PYTHON_VERSION: Python version
            LEGESHER_CACHE_SIZE: Cache size
            LEGESHER_CACHE_TTL: Cache TTL in seconds
            LEGESHER_ENHANCED_INTELLIGENCE_ENABLED: Enable enhanced Python intelligence (true/false)
            LEGESHER_LANGUAGE_SERVER_PATH: Path to the Python language server
            LEGESHER_LOG_LEVEL: Logging level

        Returns:
            Configured LanguageServerConfig instance

        Note:
            Falls back to safe defaults if environment variables contain invalid values.
            Validation errors are logged as warnings (CORE-446 security).
        """
        cls._warn_about_retired_variables()

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

            # LEGESHER_TARGET_LANG predates the role split and stands for all
            # three of the slots it used to mean at once (CORE-1760); passing
            # it once would leave file_language and working_language at "en"
            # while the file is parsed as something else.
            target_lang = os.getenv("LEGESHER_TARGET_LANG", "en")

            return cls(
                source_language=os.getenv("LEGESHER_SOURCE_LANG", "en"),
                target_language=target_lang,
                file_language=target_lang,
                working_language=target_lang,
                python_version=os.getenv("LEGESHER_PYTHON_VERSION"),
                cache_size=cache_size,
                cache_ttl=cache_ttl,
                enhanced_intelligence_enabled=os.getenv(
                    "LEGESHER_ENHANCED_INTELLIGENCE_ENABLED", "true"
                ).lower()
                == "true",
                language_server_path=os.getenv("LEGESHER_LANGUAGE_SERVER_PATH"),
                log_level=os.getenv("LEGESHER_LOG_LEVEL", "INFO"),
            )
        except ValueError as e:
            logger.error(f"Invalid configuration: {e}")
            logger.info("Using safe default configuration")
            # Fall back to safe defaults rather than crash
            return cls()

    def apply_legacy_target_language(self, code: str) -> None:
        """Set the deprecated target slot and the roles it used to stand for.

        ``target_language`` predates the role split and always meant the file
        and working languages at once (CORE-1760). Every entry point that
        still speaks the old vocabulary — the ``--target-lang`` flag,
        ``LEGESHER_TARGET_LANG``, a client sending only ``targetLanguage`` —
        therefore has to seed all three, or the roles this model advertises as
        being in lockstep silently disagree: the file would be parsed as the
        chosen language while ``file_language`` still read ``en``.

        Args:
            code: Validated ISO 639-1 language code.
        """
        self.target_language = code
        self.file_language = code
        self.working_language = code

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
            True if every language role holds a valid 2-letter code
        """
        return all(
            len(code) == 2 and code.isalpha()
            for code in (
                self.source_language,
                self.target_language,
                self.file_language,
                self.working_language,
            )
        )
