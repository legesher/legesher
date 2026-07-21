"""Tree-sitter integration for Legesher.

This module provides tree-sitter-based parsing and translation for Python code.
Tree-sitter offers performance benefits and incremental parsing capabilities
for real-time IDE integration.

Components:
    - PythonParser: Tree-sitter wrapper for parsing Python code
    - TreeSitterTranslator: Tree-sitter-based code translator (≥2x faster than token-based)
    - TreeSitterError: Exception for tree-sitter operations

The components backed by the ``tree_sitter`` / ``tree_sitter_python`` C
extensions are re-exported lazily (PEP 562): importing this package never
imports the C extensions, so the pure-stdlib token path stays importable in
environments without them (minimal installs, browser Python runtimes). The C
extensions ship in the optional ``treesitter`` extra
(``pip install legesher-core[treesitter]``).

See: https://tree-sitter.github.io/tree-sitter/
"""

from typing import TYPE_CHECKING

from .identifier_map import IdentifierMap
from .identifier_validator import IdentifierValidator
from .translation_logger import TranslationLogger

if TYPE_CHECKING:
    from .extractor import TranslatableExtractor
    from .llm_translator import LLMTranslator
    from .parser import PythonParser, TreeSitterError
    from .translator import TreeSitterTranslator

__all__ = [
    "IdentifierMap",
    "IdentifierValidator",
    "LLMTranslator",
    "PythonParser",
    "TranslatableExtractor",
    "TranslationLogger",
    "TreeSitterError",
    "TreeSitterTranslator",
]

#: Distributions provided by the optional ``treesitter`` extra.
_OPTIONAL_DEPENDENCIES = frozenset({"tree_sitter", "tree_sitter_python"})

#: Lazily re-exported names -> submodule that defines them. Each of these
#: submodules imports the C extensions (directly or via ``.parser``).
_LAZY_EXPORTS = {
    "LLMTranslator": "llm_translator",
    "PythonParser": "parser",
    "TranslatableExtractor": "extractor",
    "TreeSitterError": "parser",
    "TreeSitterTranslator": "translator",
}


def _missing_optional_dependency(exc: BaseException | None) -> str | None:
    """Return the missing optional dependency behind ``exc``, if any.

    Walks the exception chain looking for an :class:`ImportError` whose
    ``name`` is one of the optional C-extension distributions. Any other
    import failure is a real bug and must not be re-labelled as a missing
    optional dependency.
    """
    seen: set[int] = set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        name = getattr(exc, "name", None)
        if isinstance(name, str) and name.partition(".")[0] in _OPTIONAL_DEPENDENCIES:
            return name.partition(".")[0]
        exc = exc.__cause__ or exc.__context__
    return None


def __getattr__(name: str) -> object:
    """Import tree-sitter-backed components on first attribute access (PEP 562)."""
    submodule = _LAZY_EXPORTS.get(name)
    if submodule is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    import importlib

    try:
        module = importlib.import_module(f".{submodule}", __name__)
    except ImportError as exc:
        missing = _missing_optional_dependency(exc)
        if missing is None:
            raise
        raise ImportError(
            f"{__name__}.{name} requires the optional tree-sitter backend "
            f"(missing dependency: {missing!r}). "
            "Install it with: pip install 'legesher-core[treesitter]'. "
            "The token-based TokenTranslator works without it."
        ) from exc
    return getattr(module, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_LAZY_EXPORTS))
