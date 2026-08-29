"""Local translation-engine adapter for the MCP tools.

This module is the single seam between the MCP layer and the foundation
packages, mirroring the invocation pattern the hosted REST API uses:

- ``legesher_core.language_interface.create_translator_from_language_pack``
  builds a directional en→X translator from a language pack; ``.reverse()``
  yields X→en. X→Y therefore pivots through English (X→en, then en→Y) —
  the engine has no direct X→Y path, and the ``pivoted`` flag surfaces
  when the pivot was taken.
- ``legesher_i18n.pack_loader.LanguagePackLoader`` loads the per-language
  term dictionaries (keywords / builtins / exceptions / reserved words).
- ``legesher_i18n.language_registry`` provides the language allowlist.
- Validation is STATIC ONLY: ``compile()`` — never ``exec()``/``eval()`` —
  so submitted code is parsed but never executed. Non-English sources are
  reverse-translated to English first, because ``compile()`` only
  understands English keywords.

Error hygiene: engine/loader exception messages can embed filesystem paths
or source fragments. Everything that crosses this seam is re-raised as
:class:`EngineError` with a machine code and a generic, content-free
message.
"""

from __future__ import annotations

import io
import re
import threading
import time
import tokenize
from dataclasses import dataclass, field
from typing import Any

from legesher_core.exceptions import TranslationError
from legesher_core.language_interface import create_translator_from_language_pack
from legesher_core.utils import merge_exception_translations
from legesher_i18n.exceptions import LanguagePackError
from legesher_i18n.language_registry import (
    LANGUAGE_METADATA,
    get_active_language_codes,
)
from legesher_i18n.pack_loader import LanguagePack, LanguagePackLoader

#: Packs are authored against English, so English is the pivot for X→Y
#: and the fixed target of ``translate_to_source``.
PIVOT_LANGUAGE = "en"

#: Registry pattern for language codes (same as the hosted API schemas).
#: Checked BEFORE any pack/path resolution — path-traversal guard.
LANG_CODE_PATTERN = r"^[a-z]{2,3}(-[A-Za-z0-9]+)?$"

_LANG_CODE_RE = re.compile(LANG_CODE_PATTERN)

#: Construct categories in lookup-precedence order. ``keywords`` wins over
#: ``implicit_params`` on conflict, matching the pack's own precedence
#: (``LanguagePack.get_keyword_translation``).
CATEGORIES: tuple[str, ...] = ("keywords", "builtins", "exceptions", "implicit_params")


class EngineError(Exception):
    """A tool-facing engine failure: machine ``code`` + content-free message."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class TranslationOutcome:
    """Result of one translation request."""

    translated_source: str
    #: True when the translation went through the English pivot (X→en→Y).
    pivoted: bool


@dataclass(frozen=True)
class SyntaxIssue:
    """Location and message of a syntax problem (1-based line/column)."""

    message: str
    line: int | None = None
    offset: int | None = None


@dataclass(frozen=True)
class ValidationOutcome:
    """Result of statically validating one source submission."""

    valid: bool
    issue: SyntaxIssue | None = None


@dataclass(frozen=True)
class LanguageInfo:
    """One language as listed by the ``legesher://languages`` resource."""

    code: str
    name: str
    native: str
    rtl: bool
    status: str
    #: Whether a Python language pack is discoverable for this code in
    #: this environment (registry entries can exist before a pack ships).
    pack_available: bool


@dataclass(frozen=True)
class ConstructScan:
    """Constructs found in an English-form source.

    Attributes:
        ordered: ``(category, english_term)`` pairs in first-occurrence
            order, deduplicated.
        counts: Occurrence totals per category.
        tokenized: False when the source could not be tokenized (the scan
            is then empty, which is a result, not an error).
    """

    ordered: list[tuple[str, str]] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    tokenized: bool = True


#: Filename baked into compile() diagnostics instead of any real path.
_COMPILE_FILENAME = "<submitted-source>"


#: How long a pack-availability scan stays fresh. A stdio session outlives
#: the answer rarely; a long-lived HTTP deployment (CORE-1420) would serve a
#: stale catalog forever without a bound, so the scan expires and is redone
#: on the next read. Scanning is a directory walk, not a YAML parse.
PACK_DISCOVERY_TTL_SECONDS = 60.0


class LocalEngine:
    """Translate, validate, and look up terms against the local engine.

    Translator instances are cached per ``(source_lang, target_lang,
    python_version)`` — pack loading does filesystem I/O and YAML parsing,
    so construction is the expensive step, not translation. The pack
    loader caches loaded packs internally.

    Two caches with deliberately different lifetimes:

    - **Pack availability** (which languages have a pack) expires after
      ``pack_discovery_ttl`` seconds, so a pack installed mid-process shows
      up without a restart.
    - **Loaded packs and built translators** are kept until
      :meth:`refresh_packs` is called explicitly. Pack *content* for a given
      version is immutable in practice, and re-parsing every pack on a timer
      would be pure cost.
    """

    def __init__(self, pack_discovery_ttl: float = PACK_DISCOVERY_TTL_SECONDS) -> None:
        self._loader = LanguagePackLoader()
        self._translators: dict[tuple[str, str, str], Any] = {}
        self._pack_codes: frozenset[str] | None = None
        self._pack_codes_read_at = 0.0
        self._pack_discovery_ttl = pack_discovery_ttl
        self._lock = threading.Lock()

    def refresh_packs(self) -> None:
        """Drop every pack-derived cache: availability, packs, translators.

        The explicit invalidation hook, for when pack *content* may have
        changed on disk (a pack upgraded in place) rather than just the set
        of installed packs. The TTL alone does not cover that case.
        """
        with self._lock:
            self._pack_codes = None
            self._pack_codes_read_at = 0.0
            self._translators.clear()
            self._loader.clear_cache()

    # -- language registry ------------------------------------------------

    def ensure_known_language(self, code: str) -> None:
        """Allowlist gate: pattern match AND registry membership.

        Runs BEFORE any pack/path resolution so a crafted code can never
        reach the filesystem layer.

        Raises:
            EngineError: ``unsupported_language`` when either check fails.
        """
        if not _LANG_CODE_RE.fullmatch(code) or code not in LANGUAGE_METADATA:
            raise EngineError(
                "unsupported_language",
                f"Unsupported language code: {code[:40]!r}. "
                "Read the legesher://languages resource for the catalog.",
            )

    def list_languages(self) -> list[LanguageInfo]:
        """All active (non-deprecated) registry languages, sorted by code."""
        pack_codes = self._discover_pack_codes()
        infos: list[LanguageInfo] = []
        for code in sorted(get_active_language_codes()):
            meta = LANGUAGE_METADATA[code]
            infos.append(
                LanguageInfo(
                    code=code,
                    name=str(meta["name"]),
                    native=str(meta["native"]),
                    rtl=bool(meta["rtl"]),
                    status=str(meta["status"]),
                    pack_available=code in pack_codes,
                )
            )
        return infos

    def _discover_pack_codes(self) -> frozenset[str]:
        """Which languages have a Python pack installed, rescanned on expiry."""
        with self._lock:
            now = time.monotonic()
            if (
                self._pack_codes is None
                or now - self._pack_codes_read_at >= self._pack_discovery_ttl
            ):
                # Drop the loader's own discovery cache too: without it the
                # rescan would just re-read the same stale dict.
                self._loader.refresh_discovery()
                pairs = self._loader.list_available_languages("python")
                self._pack_codes = frozenset(code for code, _name in pairs)
                self._pack_codes_read_at = now
            return self._pack_codes

    # -- packs / terms ----------------------------------------------------

    def load_pack(self, language: str, python_version: str) -> LanguagePack:
        """Load a language pack with sanitized failure messages.

        Raises:
            EngineError: ``unsupported_language`` or
                ``language_pack_not_found`` (loader messages embed
                filesystem paths — never echoed).
        """
        self.ensure_known_language(language)
        try:
            return self._loader.load(language, target="python", version=python_version)
        except LanguagePackError as exc:
            raise EngineError(
                "language_pack_not_found",
                f"No language pack for {language!r} targeting Python {python_version}.",
            ) from exc

    @staticmethod
    def pack_categories(pack: LanguagePack) -> dict[str, dict[str, str]]:
        """Category → (English term → translation) mappings for one pack.

        Packs store exception keys lowercase (``valueerror``) while Python
        spells them PascalCase (``ValueError``); the engine remaps them at
        translator-build time (``merge_exception_translations``). The MCP
        surface exposes the canonical spelling so terms match what
        actually appears in code.
        """
        return {
            "keywords": dict(pack.keywords),
            "builtins": dict(pack.builtins),
            "exceptions": merge_exception_translations({}, pack.exceptions),
            "implicit_params": dict(pack.implicit_params),
        }

    # -- translation ------------------------------------------------------

    def translate(
        self,
        *,
        source: str,
        source_lang: str,
        target_lang: str,
        python_version: str,
    ) -> TranslationOutcome:
        """Translate ``source`` from ``source_lang`` to ``target_lang``.

        Supports en→X (forward), X→en (reversed), and X→Y via the English
        pivot. The engine's token path accepts both complete files and
        fragments, so no separate snippet mode is needed.

        Raises:
            EngineError: ``unsupported_language``,
                ``language_pack_not_found``, or ``invalid_source``.
        """
        self.ensure_known_language(source_lang)
        self.ensure_known_language(target_lang)

        if source_lang == target_lang:
            return TranslationOutcome(translated_source=source, pivoted=False)

        if PIVOT_LANGUAGE in (source_lang, target_lang):
            translator = self._translator_for(source_lang, target_lang, python_version)
            translated = self._run(translator, source, source_lang, target_lang)
            return TranslationOutcome(translated_source=translated, pivoted=False)

        # X→Y has no direct engine path: pivot through English and say so.
        to_english = self._translator_for(source_lang, PIVOT_LANGUAGE, python_version)
        from_english = self._translator_for(PIVOT_LANGUAGE, target_lang, python_version)
        english = self._run(to_english, source, source_lang, PIVOT_LANGUAGE)
        translated = self._run(from_english, english, PIVOT_LANGUAGE, target_lang)
        return TranslationOutcome(translated_source=translated, pivoted=True)

    def _translator_for(self, source_lang: str, target_lang: str, python_version: str) -> Any:
        """Return a cached translator for the direction, building on miss."""
        key = (source_lang, target_lang, python_version)
        with self._lock:
            cached = self._translators.get(key)
            if cached is not None:
                return cached
            translator = self._build_translator(source_lang, target_lang, python_version)
            self._translators[key] = translator
            return translator

    @staticmethod
    def _build_translator(source_lang: str, target_lang: str, python_version: str) -> Any:
        """Build a directional translator from the non-English side's pack."""
        pack_language = target_lang if source_lang == PIVOT_LANGUAGE else source_lang
        try:
            translator = create_translator_from_language_pack(
                "python",
                pack_language,
                programming_language_version=python_version,
            )
        except (LanguagePackError, TranslationError) as exc:
            # The loader's message embeds filesystem paths — never echo it.
            raise EngineError(
                "language_pack_not_found",
                f"No language pack for {pack_language!r} targeting Python {python_version}.",
            ) from exc
        if source_lang != PIVOT_LANGUAGE:
            return translator.reverse()
        return translator

    @staticmethod
    def _run(translator: Any, source: str, source_lang: str, target_lang: str) -> str:
        """Run one translation hop, normalizing the engine's return type."""
        try:
            result = translator.translate_code(
                source, source_lang=source_lang, target_lang=target_lang
            )
        except TranslationError as exc:
            # Engine messages can embed source fragments — respond generically.
            raise EngineError(
                "invalid_source",
                "Source could not be tokenized as Python code.",
            ) from exc
        if isinstance(result, tuple):  # (code, metadata) when metadata requested
            result = result[0]
        if not isinstance(result, str):  # pragma: no cover — engine contract
            raise EngineError("invalid_source", "Translation produced an unexpected result.")
        return result

    # -- validation (static only) -----------------------------------------

    @staticmethod
    def compile_check(source: str) -> ValidationOutcome:
        """compile()-only syntax check of ENGLISH-form source. Never executed.

        Callers translate non-English sources to English first —
        ``compile()`` only understands English keywords. Parses with the
        grammar of the interpreter running the server, not the requested
        ``python_version`` (documented Phase-1 limitation, same as the
        hosted API).
        """
        try:
            compile(source, _COMPILE_FILENAME, "exec", dont_inherit=True)
        except SyntaxError as exc:
            return ValidationOutcome(
                valid=False,
                issue=SyntaxIssue(
                    message=exc.msg or "invalid syntax",
                    line=exc.lineno,
                    offset=exc.offset,
                ),
            )
        except (ValueError, RecursionError, MemoryError):
            # Null bytes, pathological nesting, etc. — invalid, not a crash.
            return ValidationOutcome(
                valid=False,
                issue=SyntaxIssue(message="Source could not be compiled."),
            )
        return ValidationOutcome(valid=True)

    # -- construct scanning -----------------------------------------------

    def scan_constructs(self, english_source: str, python_version: str) -> ConstructScan:
        """Find engine constructs present in an English-form source.

        Tokenizes with the stdlib ``tokenize`` module (lexing only — the
        code is never executed) and matches NAME tokens against the
        English pack's inventory for ``python_version``, which is the
        canonical construct list per category.
        """
        inventory = self.pack_categories(self.load_pack(PIVOT_LANGUAGE, python_version))
        category_terms: list[tuple[str, frozenset[str]]] = [
            (category, frozenset(inventory[category])) for category in CATEGORIES
        ]

        ordered: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()
        counts: dict[str, int] = {}
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(english_source).readline))
        except (tokenize.TokenError, IndentationError, SyntaxError, ValueError):
            return ConstructScan(tokenized=False)

        for tok in tokens:
            if tok.type != tokenize.NAME:
                continue
            for category, terms in category_terms:
                if tok.string in terms:
                    counts[category] = counts.get(category, 0) + 1
                    key = (category, tok.string)
                    if key not in seen:
                        seen.add(key)
                        ordered.append(key)
                    break  # first matching category wins (precedence order)
        return ConstructScan(ordered=ordered, counts=counts, tokenized=True)


_engine: LocalEngine | None = None
_engine_lock = threading.Lock()


def get_engine() -> LocalEngine:
    """Process-wide engine instance (translator/pack caches are warm)."""
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = LocalEngine()
    return _engine
