"""Language abstraction interface for creating translators.

This module provides factory functions and utilities for creating translator instances,
supporting multiple backends (token-based, tree-sitter) and programming languages.

Introduced in CORE-415 to enable:
- Polymorphic translator usage via Protocol
- Easy switching between translator backends
- Environment-based configuration
- Foundation for multi-language support (TypeScript, JavaScript, etc.)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from .types import BuiltinMap, KeywordMap, TextTranslationBackend, Translator

# Lazy loading: Only import translators when actually needed
# This allows the module to be imported without requiring tree-sitter.
# TYPE_CHECKING imports preserve precise return types on the _get_*_translator
# helpers without forcing the heavy tree-sitter deps at module import time.
if TYPE_CHECKING:
    from .transformer import TokenTranslator as _TokenTranslator
    from .tree_sitter.llm_translator import LLMTranslator as _LLMTranslator
    from .tree_sitter.translator import TreeSitterTranslator as _TreeSitterTranslator

#: Identifier for translator backends.
#:
#: Valid values are ``"token"`` (token-based, stable default),
#: ``"tree-sitter"`` (AST-based, faster), and ``"llm"`` (LLM-powered full
#: translation of identifiers, comments, and strings).
TranslatorBackend = Literal["token", "tree-sitter", "llm"]

# Environment variable truthy values (case-insensitive)
_TRUTHY_VALUES = frozenset(("true", "1", "yes", "on"))


def _should_use_tree_sitter(use_tree_sitter: bool | None) -> bool:
    """Determine whether to use tree-sitter backend.

    Args:
        use_tree_sitter: Explicit preference (True/False) or None to check environment

    Returns:
        True if tree-sitter should be used, False otherwise
    """
    if use_tree_sitter is not None:
        return use_tree_sitter
    env_value = os.getenv("LEGESHER_USE_TREE_SITTER", "false").lower()
    return env_value in _TRUTHY_VALUES


def _get_token_translator() -> "type[_TokenTranslator]":
    """Lazy import of TokenTranslator."""
    from .transformer import TokenTranslator

    return TokenTranslator


def _get_tree_sitter_translator() -> "type[_TreeSitterTranslator]":
    """Lazy import of TreeSitterTranslator."""
    from .tree_sitter.translator import TreeSitterTranslator

    return TreeSitterTranslator


def _get_llm_translator() -> "type[_LLMTranslator]":
    """Lazy import of LLMTranslator."""
    from .tree_sitter.llm_translator import LLMTranslator

    return LLMTranslator


@dataclass
class TranslatorConfig:
    """Configuration for creating translator instances.

    This dataclass provides a clean way to pass multiple configuration options
    to translator factory functions, reducing parameter count and improving
    readability.

    Attributes:
        programming_language: Target programming language ("python", "typescript")
        programming_language_version: Version of the programming language (e.g., "3.13")
        use_tree_sitter: Backend selection (None = check environment variable)
        natural_language: Natural language for translations (e.g., "es", "ar")

    Example:
        >>> config = TranslatorConfig(
        ...     programming_language="python",
        ...     programming_language_version="3.13",
        ...     use_tree_sitter=True
        ... )
        >>> translator = create_translator_from_config(config, keyword_map, builtin_map)
    """

    programming_language: str = "python"
    programming_language_version: str = "3.13"
    use_tree_sitter: bool | None = None
    natural_language: str | None = None

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        supported = get_supported_languages()
        if self.programming_language not in supported:
            raise ValueError(
                f"Unsupported programming language: {self.programming_language!r}. "
                f"Supported: {', '.join(supported.keys())}"
            )

    @property
    def resolved_use_tree_sitter(self) -> bool:
        """Resolve the tree-sitter preference (explicit or from environment)."""
        return _should_use_tree_sitter(self.use_tree_sitter)

    @property
    def backend(self) -> TranslatorBackend:
        """Get the backend name that will be used."""
        return "tree-sitter" if self.resolved_use_tree_sitter else "token"


def create_translator(
    programming_language: str,
    keyword_map: KeywordMap,
    builtin_map: BuiltinMap,
    programming_language_version: str = "3.13",
    use_tree_sitter: bool | None = None,
    backend: TextTranslationBackend | None = None,
    reserved_word_map: dict[str, str] | None = None,
) -> Translator:
    """Factory function to create a translator instance.

    This factory provides a unified interface for creating translators,
    supporting multiple backends and programming languages. The backend
    can be selected explicitly or via environment variable.

    Args:
        programming_language: Target programming language ("python", "typescript")
        keyword_map: Keyword translation mappings (e.g., {"def": "definir"})
        builtin_map: Built-in function translation mappings (e.g., {"print": "imprimir"})
        programming_language_version: Version for version-aware packs (default: "3.13")
        use_tree_sitter: Backend selection:
            - True: Use TreeSitterTranslator (AST-based, better error handling)
            - False: Use TokenTranslator (simpler, token-based)
            - None: Check LEGESHER_USE_TREE_SITTER environment variable
        reserved_word_map: Optional mapping of Python conventions like ``self``
            and ``cls`` to target language (CORE-710). Forwarded to the
            translator. Defaults to None (empty) for backward compat.

    Environment Variables:
        LEGESHER_USE_TREE_SITTER: Set to enable tree-sitter backend
            Truthy values: "true", "1", "yes", "on" (case-insensitive)
            Falsy values: "false", "0", "no", "off", "" (case-insensitive)
            Default: "false" (token-based)

    Returns:
        Translator instance implementing the Translator protocol

    Raises:
        NotImplementedError: For programming languages not yet supported
        ValueError: For invalid programming language names

    Examples:
        >>> # Token-based (default, stable)
        >>> translator = create_translator("python", keyword_map, builtin_map)

        >>> # Tree-sitter (AST-based, better error recovery)
        >>> translator = create_translator("python", keyword_map, builtin_map,
        ...                               use_tree_sitter=True)

        >>> # Use environment variable
        >>> # $ export LEGESHER_USE_TREE_SITTER=true
        >>> translator = create_translator("python", keyword_map, builtin_map)

        >>> # Polymorphic usage through Protocol
        >>> def translate_with_protocol(t: Translator, code: str) -> str:
        ...     return t.translate_code(code, "en", "es")
        >>> result = translate_with_protocol(translator, "def hello(): pass")

    See Also:
        - create_translator_from_config: Create from TranslatorConfig dataclass
        - create_translator_from_language_pack: Convenience function for language packs
        - get_default_backend: Query the default backend from environment
        - get_supported_languages: List all supported programming languages
    """
    should_use_ts = _should_use_tree_sitter(use_tree_sitter)

    if programming_language == "python":
        # If an LLM backend is provided, use LLMTranslator for full translation
        if backend is not None:
            LLMTranslator = _get_llm_translator()
            return LLMTranslator(
                keyword_map=keyword_map,
                builtin_map=builtin_map,
                backend=backend,
                python_version=programming_language_version,
                reserved_word_map=reserved_word_map,
            )
        elif should_use_ts:
            TreeSitterTranslator = _get_tree_sitter_translator()
            return TreeSitterTranslator(
                keyword_map=keyword_map,
                builtin_map=builtin_map,
                reserved_word_map=reserved_word_map,
                python_version=programming_language_version,
            )
        else:
            TokenTranslator = _get_token_translator()
            return TokenTranslator(
                keyword_map=keyword_map,
                builtin_map=builtin_map,
                reserved_word_map=reserved_word_map,
                python_version=programming_language_version,
            )
    elif programming_language == "typescript":
        raise NotImplementedError(
            "TypeScript support is not currently implemented. "
            "Tracked as CORE-421 through CORE-427 in our internal roadmap; "
            "not currently scheduled."
        )
    else:
        supported = list(get_supported_languages().keys())
        raise ValueError(
            f"Unsupported programming language: {programming_language!r}. "
            f"Supported languages: {', '.join(supported)} "
            f"(typescript coming in Phase 2C)"
        )


def create_translator_from_config(
    config: TranslatorConfig,
    keyword_map: KeywordMap,
    builtin_map: BuiltinMap,
) -> Translator:
    """Create a translator from a TranslatorConfig dataclass.

    This provides a cleaner API when multiple configuration options are needed,
    reducing parameter count and improving code readability.

    Args:
        config: TranslatorConfig with all configuration options
        keyword_map: Keyword translation mappings
        builtin_map: Built-in function translation mappings

    Returns:
        Translator instance configured according to the config

    Example:
        >>> config = TranslatorConfig(
        ...     programming_language="python",
        ...     programming_language_version="3.13",
        ...     use_tree_sitter=True
        ... )
        >>> translator = create_translator_from_config(config, keyword_map, builtin_map)
    """
    return create_translator(
        programming_language=config.programming_language,
        keyword_map=keyword_map,
        builtin_map=builtin_map,
        programming_language_version=config.programming_language_version,
        use_tree_sitter=config.use_tree_sitter,
    )


def create_translator_from_language_pack(
    programming_language: str,
    natural_language: str,
    programming_language_version: str | None = None,
    use_tree_sitter: bool | None = None,
) -> Translator:
    """Convenience factory for creating translators from language packs.

    This function loads a language pack and creates the appropriate translator
    instance. It's a higher-level wrapper around create_translator().

    Args:
        programming_language: Target programming language ("python", "typescript")
        natural_language: Natural language code (e.g., "es", "ar", "zh")
        programming_language_version: Version for version-aware packs (auto-detected if None)
        use_tree_sitter: Backend selection (None = check environment)

    Returns:
        Translator instance configured with the language pack

    Raises:
        NotImplementedError: For programming languages not yet supported
        UnsupportedLanguageError: If language pack not found

    Examples:
        >>> # Load Spanish language pack
        >>> translator = create_translator_from_language_pack("python", "es")

        >>> # Load with specific Python version
        >>> translator = create_translator_from_language_pack("python", "es", "3.13")

        >>> # Use tree-sitter backend
        >>> translator = create_translator_from_language_pack(
        ...     "python", "es", use_tree_sitter=True
        ... )

        >>> # Environment variable takes effect
        >>> # $ export LEGESHER_USE_TREE_SITTER=true
        >>> translator = create_translator_from_language_pack("python", "es")
    """
    should_use_ts = _should_use_tree_sitter(use_tree_sitter)

    if programming_language == "python":
        if should_use_ts:
            TreeSitterTranslator = _get_tree_sitter_translator()
            return TreeSitterTranslator.from_language_pack(
                language=natural_language, python_version=programming_language_version
            )
        else:
            TokenTranslator = _get_token_translator()
            return TokenTranslator.from_language_pack(
                language=natural_language, python_version=programming_language_version
            )
    elif programming_language == "typescript":
        raise NotImplementedError(
            "TypeScript support is not currently implemented. "
            "Tracked as CORE-421 through CORE-427 in our internal roadmap; "
            "not currently scheduled."
        )
    else:
        supported = list(get_supported_languages().keys())
        raise ValueError(
            f"Unsupported programming language: {programming_language!r}. "
            f"Supported languages: {', '.join(supported)}"
        )


def get_default_backend() -> TranslatorBackend:
    """Get the default translator backend based on environment.

    Checks the LEGESHER_USE_TREE_SITTER environment variable to determine
    which backend should be used by default.

    Returns:
        "tree-sitter" if environment variable is truthy, otherwise "token"

    Examples:
        >>> get_default_backend()
        'token'

        >>> import os
        >>> os.environ['LEGESHER_USE_TREE_SITTER'] = 'true'
        >>> get_default_backend()
        'tree-sitter'

        >>> os.environ['LEGESHER_USE_TREE_SITTER'] = '1'
        >>> get_default_backend()
        'tree-sitter'

        >>> os.environ['LEGESHER_USE_TREE_SITTER'] = 'false'
        >>> get_default_backend()
        'token'
    """
    env_value = os.getenv("LEGESHER_USE_TREE_SITTER", "false").lower()
    return "tree-sitter" if env_value in ("true", "1", "yes", "on") else "token"


def get_supported_languages() -> dict[str, list[str]]:
    """Return dict of supported programming languages and their implementations.

    Returns:
        Dictionary mapping programming language names to lists of available backends.
        Empty list indicates language is planned but not yet implemented.

    Examples:
        >>> languages = get_supported_languages()
        >>> print(languages)
        {
            'python': ['token', 'tree-sitter'],
            'typescript': []  # Coming in Phase 2C
        }

        >>> # Check if Python is supported
        >>> 'python' in get_supported_languages()
        True

        >>> # Check available backends for Python
        >>> backends = get_supported_languages()['python']
        >>> 'tree-sitter' in backends
        True
    """
    return {
        "python": ["token", "tree-sitter"],
        "typescript": [],  # Coming in Phase 2C (CORE-421 through CORE-427)
    }


__all__ = [
    # Types
    "Translator",
    "TranslatorBackend",
    "TranslatorConfig",
    # Factory functions
    "create_translator",
    "create_translator_from_config",
    "create_translator_from_language_pack",
    # Utilities
    "get_default_backend",
    "get_supported_languages",
]
