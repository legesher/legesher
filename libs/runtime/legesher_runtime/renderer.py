"""Localized traceback renderer (CORE-1679).

:class:`TracebackRenderer` re-renders a CPython traceback in a target natural
language, combining two vocabularies:

* **structural strings and message templates** from the message catalog
  (``legesher_i18n.messages`` — the ``traceback.*`` rows localize the header,
  frame, cause, and context lines; the ``<ExceptionType>.*`` rows localize
  the message via anchored matchers with named slots);
* **exception TYPE names** from the python language pack for the language
  (``exceptions:`` section — consumed as-is, the packs are the vocabulary
  source of truth).

Rendering strategy — line-wise rewriting of CPython's own output
================================================================

The renderer formats the exception with :func:`traceback.format_exception`
first and then rewrites only the STRUCTURAL lines it positively recognizes:

* the ``Traceback (most recent call last):`` header,
* ``File "...", line N[, in name]`` frame headers (values preserved; frame
  matching happens on the whitespace-stripped line, indent re-attached),
* the chained-exception cause/context sentences,
* the final ``ExceptionType: message`` line(s) — type name via the pack,
  message via the catalog matchers; an UNMATCHED message passes through
  untranslated (localized type name, original message).

Every other line — source lines, PEP 657 caret/anchor lines (``~~~^^^``),
``locals`` dumps, exception-group ``|``-prefixed blocks — passes through
byte-for-byte.

PEP 657 caret spans: offset-mapping approach
--------------------------------------------

Fine-grained error locations are a pair of physical lines: the echoed source
line and, below it, an anchor line whose column offsets point INTO the echoed
line. Two regimes:

* **Plain (unmapped) files** — both lines pass through verbatim, and the
  structural lines this renderer rewrites are always OTHER physical lines,
  so no caret can be misplaced and no offset re-mapping is required.
* **Mapped files** (``source_map`` given and ``has_mapping(file)`` true —
  the ``legesher run`` path, where TRANSLATED source is compiled under the
  NATIVE filename): the interpreter computed the caret columns against the
  translated text, so against the displayed native line they are wrong by
  construction. Until a real column re-map through the token translation
  exists (tracked as a follow-up on the ticket), the renderer applies "no
  caret beats a wrong caret": caret/anchor lines belonging to mapped frames
  are DROPPED, the echoed source line is replaced by the native line from
  the source map (this also fixes ``SyntaxError.text``, which CPython takes
  from the exception object and therefore shows translated source), and the
  displayed line number is passed through ``get_native_line``.

If a future version rewrites the echoed source line AND keeps carets, it
must remap the anchor columns through the same substitution it applies to
the source text.

Known limitation (documented in README): flush-left CONTINUATION lines of a
multi-line exception message (or :pep:`678` ``add_note`` content) that happen
to look like ``SomeType: message`` can be falsely localized; a
``TracebackException``-walk renderer is the eventual fix.

RTL (Arabic) posture, v1: output is in LOGICAL order with no bidi control
characters inserted; terminal display order is left to the terminal's bidi
implementation. See ``libs/runtime/README.md`` for the limitation note.

:meth:`render` NEVER raises — formatting failures (e.g. a bogus traceback
object) degrade to a minimal ``Type: message`` line, rewriting failures
degrade to CPython's own formatting — and the hooks in
:mod:`legesher_runtime.hooks` add one more fallback layer around it. This
class is deliberately standalone so localized logging (CORE-1437) can reuse
it; the excepthooks are thin adapters over it.
"""

from __future__ import annotations

import logging
import re
import sys
import traceback
from pathlib import Path
from types import TracebackType
from typing import Any

from legesher_i18n.messages import MessageRule, load_catalog, match_message

__all__ = ["TracebackRenderer"]

logger = logging.getLogger(__name__)


def _empty_catalog_reason(db_path: object) -> str:
    """Why :func:`load_catalog` came back empty — the two cases look identical
    at the call site (CORE-1848): no database file at all, or a database that
    predates/skips the messages partition. Diagnostic only; never raises.
    """
    try:
        from legesher_i18n.db.database import default_db_path

        path = Path(db_path) if db_path is not None else default_db_path()  # type: ignore[arg-type]
    except Exception:  # noqa: BLE001 - a diagnostic must not out-crash the renderer
        return f"could not resolve a database path from {db_path!r}"
    if not path.exists():
        return f"no translations database at {path}"
    return (
        f"translations database at {path} has no message catalog rows "
        "(messages partition missing or unseeded)"
    )


#: A structural frame line: ``  File "x", line 1, in f`` (indent preserved).
_FRAME_LINE = re.compile(
    r'^(?P<indent>\s*)File "(?P<file>[^"]+)", line (?P<line>\d+)'
    r"(?:, in (?P<name>.+?))?(?P<suffix>\s*)$"
)

#: A final exception line: no indentation, ``Type: message`` or a bare
#: ``Type``. The type may be dotted (``json.decoder.JSONDecodeError``).
_EXCEPTION_LINE = re.compile(
    r"^(?P<type>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)"
    r"(?:: (?P<message>.*))?$"
)


def _is_caret_line(stripped: str) -> bool:
    """A PEP 657 anchor line (``~~~^^^``) or a SyntaxError caret line."""
    return bool(stripped) and set(stripped) <= {"~", "^"}


class TracebackRenderer:
    """Render tracebacks with localized structure, type names, and messages.

    Args:
        lang: Target language code (``'es'``, ``'ar'``). ``'en'`` renders a
            structurally identical traceback (identity transform).
        python_version: ``'X.Y'`` catalog/pack tier, or ``None`` for the
            running interpreter (messages are raised by THIS interpreter, so
            auto is almost always right).
        db_path: Override the translations database (tests only).
        source_map: Optional source mapper for translated files — an object
            with ``has_mapping(filename)``, ``get_native_line(filename,
            lineno)``, and ``get_native_source_line(filename, lineno)`` (the
            ``legesher.runtime.source_mapper`` protocol). Frames in mapped
            files get native source echo, remapped line numbers, and their
            translated-offset caret lines dropped (see module docstring).

    Construction is best-effort: a missing catalog or language pack degrades
    to empty vocabularies (everything passes through), never an exception.
    """

    def __init__(
        self,
        lang: str,
        python_version: str | None = None,
        *,
        db_path: object = None,
        source_map: Any = None,
    ) -> None:
        self.lang = lang
        self.source_map = source_map
        # Resolve "auto" once: the running interpreter raises the messages
        # being rendered, so its version is the correct default tier — and an
        # explicit version avoids the pack loader's project-scanning
        # auto-detection inside an exception hook.
        self.python_version = python_version or f"{sys.version_info[0]}.{sys.version_info[1]}"

        try:
            rules = load_catalog(lang, self.python_version, db_path=db_path)
        except Exception:  # noqa: BLE001 - degraded catalog, never a crash
            rules = []
        if not rules:  # say WHICH degraded mode this is, or the next person bisects
            logger.debug(
                "empty message catalog for %r (python %s): %s — structural lines "
                "and messages pass through in English",
                lang,
                self.python_version,
                _empty_catalog_reason(db_path),
            )
        self._structural: dict[str, MessageRule] = {
            r.key: r for r in rules if r.key.startswith("traceback.")
        }
        self._by_type: dict[str, list[MessageRule]] = {}
        for rule in rules:
            prefix, _, _ = rule.key.partition(".")
            if prefix != "traceback":
                self._by_type.setdefault(prefix, []).append(rule)

        self._exception_names: dict[str, str] = {}
        try:  # pack vocabulary: consumed as-is; missing pack = English names
            from legesher_i18n import load_language_pack

            pack = load_language_pack(lang, "python", self.python_version)
            self._exception_names = dict(pack.exceptions)
        except Exception:  # noqa: BLE001 - degraded vocabulary, never a crash
            self._exception_names = {}

    # -- public API ---------------------------------------------------------

    def render(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_tb: TracebackType | None,
    ) -> str:
        """Render one exception (with chained context) as localized text.

        Never raises — this contract holds WITHOUT the hooks, because the
        class is a consumer surface of its own (localized logging,
        CORE-1437). Failure ladder: formatting the exception fails (bogus
        traceback object) -> minimal ``Type: message`` line; rewriting fails
        -> CPython's own formatting, verbatim.
        """
        try:
            original = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        except BaseException:  # noqa: BLE001 - bogus tb/type: minimal output
            return self._render_minimal(exc_type, exc_value)
        try:
            return self.render_text(original)
        except BaseException:  # noqa: BLE001 - the never-raise contract
            return original

    def render_text(self, formatted: str) -> str:
        """Rewrite an already-formatted traceback string line by line.

        Only positively recognized structural lines are rewritten; everything
        else (source lines, caret/anchor lines, group sections) passes
        through byte-for-byte — except within frames of MAPPED files, where
        caret lines are dropped and the source echo is re-read from the
        native source (see the module docstring).
        """
        out: list[str] = []
        frame_file: str | None = None  # file of the current frame block
        frame_line_no: int | None = None
        echo_pending = False  # next indented line is the frame's source echo
        for raw in formatted.splitlines(keepends=True):
            body = raw.rstrip("\r\n")
            newline = raw[len(body) :]
            stripped = body.strip()
            indent = body[: len(body) - len(body.lstrip())]

            frame = _FRAME_LINE.fullmatch(body)
            if frame is not None and indent:
                frame_file = frame.group("file")
                frame_line_no = int(frame.group("line"))
                mapped = self._mapped(frame_file)
                if mapped:
                    frame_line_no = self._native_lineno(frame_file, frame_line_no)
                echo_pending = True
                out.append(self._render_frame(frame, frame_line_no, newline))
                continue

            if indent:
                if frame_file is not None and self._mapped(frame_file):
                    if _is_caret_line(stripped):
                        # Caret columns were computed against TRANSLATED
                        # source; against the native line they are wrong by
                        # construction. No caret beats a wrong caret.
                        continue
                    if echo_pending and stripped:
                        echo_pending = False
                        native = self._native_source_line(frame_file, frame_line_no)
                        if native is not None and native.strip():
                            out.append(f"{indent}{native.strip()}{newline}")
                            continue
                if stripped:
                    echo_pending = False
                out.append(raw)
                continue

            # Flush-left line: the frame block (if any) has ended.
            frame_file = None
            frame_line_no = None
            echo_pending = False
            out.append(self._render_flush_left(body, stripped, newline) or raw)
        return "".join(out)

    def localized_type_name(self, type_name: str) -> str:
        """The pack's word for an exception type, or the English name.

        Packs key exceptions lowercase (``zerodivisionerror``) while Python
        spells them PascalCase (see ``legesher_core.utils
        .merge_exception_translations``). When the pack word is merely the
        case-folded English name (the ``en`` pack's identity mappings), the
        canonical PascalCase spelling wins.
        """
        word = self._exception_names.get(type_name.lower())
        if word is None or word.lower() == type_name.lower():
            return type_name
        return word

    def localize_message(self, type_name: str, message: str) -> str | None:
        """Localize one exception message via the catalog matchers.

        Scoped matching (``key_prefix=type_name``) is the catalog's intended
        consumption: rules are pre-bucketed by type here AND the scope is
        passed through, so a catch-all rule (``KeyError.key``) can only ever
        fire for its own exception type.

        Returns ``None`` when no matcher for this type matches — the caller
        passes the original message through untranslated.
        """
        rules = self._by_type.get(type_name, [])
        return match_message(rules, message, key_prefix=type_name)

    # -- degraded output ----------------------------------------------------

    def _render_minimal(
        self, exc_type: type[BaseException] | Any, exc_value: BaseException | Any
    ) -> str:
        """A one-line ``Type: message`` when the traceback cannot be formatted."""
        try:
            name = getattr(exc_type, "__name__", None) or str(exc_type)
            localized_type = self.localized_type_name(name)
            try:
                message = str(exc_value)
            except BaseException:  # noqa: BLE001
                message = ""
            if message:
                localized = self.localize_message(name, message)
                message = message if localized is None else localized
            if message:
                return f"{localized_type}: {message}\n"
            return f"{localized_type}\n"
        except BaseException:  # noqa: BLE001 - truly last resort
            return "<unrenderable exception>\n"

    # -- source-map plumbing (all guarded: a broken mapper = unmapped) -------

    def _mapped(self, filename: str) -> bool:
        if self.source_map is None:
            return False
        try:
            return bool(self.source_map.has_mapping(filename))
        except BaseException:  # noqa: BLE001
            return False

    def _native_lineno(self, filename: str, lineno: int) -> int:
        try:
            native = self.source_map.get_native_line(filename, lineno)
            return int(native) if native is not None else lineno
        except BaseException:  # noqa: BLE001
            return lineno

    def _native_source_line(self, filename: str, lineno: int | None) -> str | None:
        if lineno is None:
            return None
        try:
            return self.source_map.get_native_source_line(filename, lineno)
        except BaseException:  # noqa: BLE001
            return None

    # -- line rewriting -----------------------------------------------------

    def _structural_sub(
        self, key: str, line_body: str, overrides: dict[str, str] | None = None
    ) -> str | None:
        """Rewrite ``line_body`` via structural rule ``key`` if it matches."""
        rule = self._structural.get(key)
        if rule is None:
            return None
        match = rule.matcher.fullmatch(line_body)
        if match is None:
            return None
        values = match.groupdict()
        if overrides:
            values.update(overrides)
        return rule.render(values)

    def _render_frame(self, frame: re.Match[str], line_no: int | None, newline: str) -> str:
        """Rewrite one frame header line (matched on the STRIPPED body)."""
        indent = frame.group("indent")
        stripped = frame.group(0).strip()
        key = "traceback.frame" if frame.group("name") else "traceback.frame_no_scope"
        overrides = {"line": str(line_no)} if line_no is not None else None
        localized = self._structural_sub(key, stripped, overrides)
        if localized is not None:
            return indent + localized + newline
        return frame.group(0) + newline

    def _render_flush_left(self, body: str, stripped: str, newline: str) -> str | None:
        """Rewrite a flush-left structural line; None = pass through."""
        if not stripped:
            return None

        # Structural one-liners (header / cause / context).
        for key in ("traceback.header", "traceback.cause", "traceback.context"):
            localized = self._structural_sub(key, body)
            if localized is not None:
                return localized + newline

        # The final exception line(s): "Type: message" or a bare "Type".
        exc = _EXCEPTION_LINE.fullmatch(body)
        if exc is not None:
            dotted = exc.group("type")
            simple = dotted.rsplit(".", maxsplit=1)[-1]
            message = exc.group("message")
            known_type = simple.lower() in self._exception_names
            has_rules = simple in self._by_type
            if known_type or has_rules:
                # Localize only the LAST path component; the module path
                # (e.g. json.decoder.) stays as-is.
                localized_type = dotted[: len(dotted) - len(simple)] + self.localized_type_name(
                    simple
                )
                if message is None:
                    return localized_type + newline
                localized_message = self.localize_message(simple, message)
                if localized_message is None:
                    localized_message = message  # unmatched: pass through
                if localized_message == "":
                    # CPython prints a bare type name for empty messages.
                    return localized_type + newline
                return f"{localized_type}: {localized_message}{newline}"

        return None
