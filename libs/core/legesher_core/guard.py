"""The guard: refuse what must not be committed (CORE-1841).

The git clean filter cannot refuse anything. Git treats a filter that is
missing or exits non-zero as a passthrough and stores the file unchanged, and
clean also runs during ``git status`` and ``git diff``, so a filter marked
``required`` would break those commands too. Refusal therefore lives here,
behind ``legesher guard``, which the pre-commit hook runs on staged files and
a pull-request check runs, as ``legesher guard --diff``, on a pull request's
changes (CORE-1323). The hook is a client-side check that ``--no-verify``,
merges and rebases skip; the pull-request check sees changes made anywhere,
though it checks a pull request's net change rather than each commit in it.

Checks, each reported as a :class:`Finding` with a line and column:

- ``encoding``: content that is not UTF-8, or a coding declaration other
  than UTF-8. Python honors the declaration, so a pure-ASCII file declared
  ``utf-7`` runs code a reviewer reads as a string.
- ``unicode``: bidi reordering controls (Trojan Source, CVE-2021-42574),
  invisible and Default_Ignorable characters outside string and comment
  prose, Arabic tatweel, and identifier characters outside every supported
  script. These were the clean filter's refusals (CORE-1343, CORE-1557,
  CORE-1558, CORE-1559).
- ``keyword``: a keyword that is not in its block's stored form, which is
  exactly what the clean filter would rewrite. It fires when a file reached
  the index without the filter, from a machine without Legesher.
- ``artifact``: a file under ``.legesher/`` that is not a regular file, does
  not match its own format, or records a path outside the repository
  (:func:`check_artifact`).
"""

from __future__ import annotations

import codecs
import dataclasses
import io
import logging
import re
import tokenize
import unicodedata
import warnings
from collections.abc import Callable
from dataclasses import dataclass

from . import unicode_guard
from .stored_form import KeywordTable, find_strays, tokenizer_view

logger = logging.getLogger(__name__)

#: Issue kinds that refuse a commit. ``bom`` (a leading byte-order mark) is
#: advisory and allowed.
BLOCKING_KINDS = ("bidi", "invisible", "tatweel", "script")

_CLASSIFICATION = {
    "bidi": "Trojan Source bidi reordering control (CVE-2021-42574)",
    "invisible": "invisible or format character outside string and comment prose",
    "tatweel": "tatweel padding character",
    "script": "identifier character outside every supported script",
}


@dataclass(frozen=True)
class Finding:
    """One reason a file must not be committed as it stands.

    Attributes:
        path: Repository-relative path, as the caller named it.
        line: 1-based line.
        column: 1-based column, counted in characters.
        check: ``"encoding"``, ``"unicode"``, ``"keyword"`` or ``"artifact"``.
        message: What was found and what it should be.
    """

    path: str
    line: int
    column: int
    check: str
    message: str

    def format(self) -> str:
        """``path:line:column: check: message``, the shape editors link.

        A path with a control character is quoted the way git quotes it, so a
        file name can never start a new line of output (a CI log reads a line
        beginning ``::`` as a workflow command).
        """
        return (
            f"{display_path(self.path)}:{self.line}:{self.column}: "
            f"{self.check}: {self.message}"
        )


def display_path(path: str) -> str:
    """``path`` as-is, or C-quoted when it holds a control character."""
    if not any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in path):
        return path
    escapes = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"}
    quoted = "".join(
        escapes.get(ch)
        or (f"\\{ord(ch):03o}" if ord(ch) < 0x20 or ord(ch) == 0x7F else ch)
        for ch in path
    )
    return f'"{quoted}"'


def _position(text: str, offset: int) -> tuple[int, int]:
    """1-based line and column, as Python reads the lines.

    A lone CR breaks a line, and a leading byte-order mark is not a column.
    """
    view = tokenizer_view(text)
    line = view.count("\n", 0, offset) + 1
    start = view.rfind("\n", 0, offset) + 1
    if start == 0 and view.startswith("\ufeff") and offset > 0:
        start = 1
    return line, offset - start + 1


def identifier_format_allowlist(language: str) -> frozenset[str]:
    """Format characters this language's identifiers may contain.

    Read from the language's script policy: the Sinhala ZWJ (U+200D) and the
    Persian and Urdu ZWNJ (U+200C) today. Empty for every other language and
    for a language with no registered policy: default-deny. Deliberately not
    the string and comment allowlist, so a joiner in a comment never licenses
    one inside a name.
    """
    try:
        from legesher_i18n.script_policy import policy_for

        return frozenset(policy_for(language).allowed_format_chars)
    except (ImportError, KeyError):
        return frozenset()


def _string_comment_format_chars(source: str) -> set[str]:
    """Non-bidi invisible characters found inside string and comment tokens.

    Category ``Cf`` plus the non-``Cf`` Default_Ignorable marks (such as the
    U+FE0F emoji presentation selector), so legitimate invisibles in prose are
    allowed once the scan nets the full Default_Ignorable set (CORE-1559).
    Bidi controls are never collected: they are dangerous even in literals.
    """
    allowed: set[str] = set()
    try:
        for tok in tokenize.generate_tokens(
            io.StringIO(tokenizer_view(source)).readline
        ):
            is_prose = tok.type in (tokenize.STRING, tokenize.COMMENT) or (
                hasattr(tokenize, "FSTRING_MIDDLE")
                and tok.type == tokenize.FSTRING_MIDDLE
            )
            if not is_prose:
                continue
            for ch in tok.string:
                if ch in unicode_guard.BIDI_CONTROLS:
                    continue
                if unicodedata.category(
                    ch
                ) == "Cf" or unicode_guard.is_default_ignorable(ch):
                    allowed.add(ch)
    except (tokenize.TokenError, IndentationError, SyntaxError, ValueError):
        return set()
    return allowed


def _literal_spans(source: str) -> list[tuple[int, int]] | None:
    """Character spans of every string and comment token, or ``None``.

    The complement is code position. ``None`` means the source cannot be
    tokenized, and the code-position scan then scans nothing.
    """
    # The tokenize pass reads the view in which every lone CR is LF, because
    # Python breaks a line there and tokenize over io.StringIO does not: over
    # the raw text tokenize can fail on source Python runs, and a line table
    # that broke at a CR the tokenizer did not shifted every later span
    # (reviews of CORE-1841). The view has the same length, so the offsets
    # hold for the original. str.splitlines would also break at U+000B,
    # U+000C, U+0085, U+2028 and U+2029, so the table follows LF alone.
    source = tokenizer_view(source)
    line_starts = [0]
    index = source.find("\n")
    while index != -1:
        line_starts.append(index + 1)
        index = source.find("\n", index + 1)

    def offset_of(position: tuple[int, int]) -> int | None:
        row, column = position
        if not 0 < row <= len(line_starts):
            return None
        return line_starts[row - 1] + column

    spans: list[tuple[int, int]] = []
    try:
        for tok in tokenize.generate_tokens(
            io.StringIO(tokenizer_view(source)).readline
        ):
            is_literal = tok.type in (tokenize.STRING, tokenize.COMMENT) or (
                hasattr(tokenize, "FSTRING_MIDDLE")
                and tok.type == tokenize.FSTRING_MIDDLE
            )
            if not is_literal:
                continue
            start, end = offset_of(tok.start), offset_of(tok.end)
            if start is None or end is None:
                continue
            spans.append((start, end))
    except (tokenize.TokenError, IndentationError, SyntaxError, ValueError):
        return None
    return spans


def _compiles(source: str) -> bool:
    """Whether Python would compile ``source``; never prints its warnings."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            compile(
                tokenizer_view(source), "<legesher-guard>", "exec", dont_inherit=True
            )
        except (SyntaxError, ValueError, MemoryError, RecursionError):
            return False
    return True


def identifier_script_issues(source: str, language: str) -> list[unicode_guard.Issue]:
    """Apply the identifier allowlist to every character in code position.

    Deliberately not driven by NAME tokens: on CPython 3.10 and 3.11 the
    tokenizer's name pattern is ``\\w+``, which does not match a nonspacing
    mark, so ``to<U+2D7F>tal`` lexes as NAME / ERRORTOKEN / NAME and the mark
    belongs to no NAME token. Scanning the complement of the string and
    comment spans has no such version dependence. ASCII outside
    ``[A-Za-z0-9_]`` is Python's own syntax and is skipped.
    """
    spans = _literal_spans(source)
    if spans is None:
        # Fail closed: source Python would run but tokenize cannot read is
        # scanned whole, as if every character were in code position.
        if not _compiles(source):
            return []
        spans = []
    allowed = identifier_format_allowlist(language)
    issues: list[unicode_guard.Issue] = []
    cursor = 0
    for start, end in [*spans, (len(source), len(source))]:
        for offset in range(cursor, max(cursor, start)):
            ch = source[offset]
            if ch.isascii() and not (ch.isalnum() or ch == "_"):
                continue
            issues.extend(
                issue
                for issue in unicode_guard.scan_identifier(ch, allowed, start=offset)
                if issue.kind in ("script", "invisible")
            )
        cursor = max(cursor, end)
    return issues


def scan_unicode(text: str, language: str) -> list[unicode_guard.Issue]:
    """Every blocking Unicode issue in ``text``, one per offset, in order.

    Two passes with two allowlists, because they ask different questions. The
    whole-text scan may meet an invisible anywhere, so it allows what prose
    legitimately contains plus what the language's names need. The
    code-position scan then allows only the language's own format characters,
    so a U+FE0F in a comment no longer licenses one in a name. A leading
    byte-order mark is allowed; offsets count it.
    """
    body = unicode_guard.strip_bom(text)
    shift = len(text) - len(body)
    allowed = _string_comment_format_chars(body) | identifier_format_allowlist(language)
    issues = unicode_guard.scan_text(body, allowed_format_chars=allowed)
    try:
        issues = issues + identifier_script_issues(body, language)
    except Exception as exc:  # pragma: no cover - defensive
        # A defect in the newest layer must never take the Trojan Source
        # check down with it.
        logger.error(f"guard: identifier scan failed: {exc}")
    first_by_offset: dict[int, unicode_guard.Issue] = {}
    for issue in issues:
        if issue.kind in BLOCKING_KINDS:
            first_by_offset.setdefault(issue.offset, issue)
    return [
        dataclasses.replace(issue, offset=offset + shift)
        for offset, issue in sorted(first_by_offset.items())
    ]


#: Encodings a Legesher file may declare, as ``codecs`` names them.
_UTF8 = frozenset({"utf-8", "utf-8-sig"})


def _declaration_is_utf8(declared: str, data: bytes) -> bool:
    """Whether a declared encoding reads these bytes exactly as UTF-8 does.

    Any spelling of UTF-8 (``utf8``, ``UTF_8``), and ``ascii`` over bytes that
    are all ASCII. Anything else, ``utf-7`` above all, reads text differently.
    """
    try:
        name = codecs.lookup(declared).name
    except LookupError:
        return False
    return name in _UTF8 or (name == "ascii" and data.isascii())


#: Index modes that are not a regular file's content.
_SYMLINK_MODE = "120000"
_GITLINK_MODE = "160000"


def _leaves_repository(value: object) -> bool:
    """Whether a repository-relative path setting points outside the repo."""
    if not isinstance(value, str):
        return False
    if value.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", value):
        return True
    depth = 0
    for part in re.split(r"[\\/]+", value):
        if part == "..":
            depth -= 1
            if depth < 0:
                return True
        elif part not in ("", "."):
            depth += 1
    return False


def _artifact(path: str, message: str) -> Finding:
    return Finding(path, 1, 1, "artifact", message)


#: The largest file under .legesher/ the guard parses; the toolchain's own
#: artifacts are far smaller, and anything larger is a finding, not a load.
MAX_ARTIFACT_BYTES = 5 * 1024 * 1024

#: The formats the open toolchain owns, by lower-cased name under .legesher/.
KNOWN_ARTIFACTS = ("config.yml", "translation_memory.json", "identifier_map.json")


def is_legesher_path(path: str) -> bool:
    """Whether ``path`` is ``.legesher`` or under it, in any letter case.

    Case matters because a case-insensitive file system opens
    ``.LEGESHER/config.yml`` as the configuration.
    """
    return path.split("/", 1)[0].casefold() == ".legesher"


def is_known_artifact(path: str) -> bool:
    """Whether the guard parses ``path`` (callers never load the others)."""
    if not is_legesher_path(path) or "/" not in path:
        return False
    name = path.split("/", 1)[1].casefold()
    return name in KNOWN_ARTIFACTS or (
        name.startswith("metadata/") and name.endswith(".yml")
    )


def check_artifact(path: str, data: bytes, *, mode: str = "100644") -> list[Finding]:
    """Findings for ``.legesher`` itself or one file under it (CORE-1323).

    Every entry must be a regular file: a symlink could point anywhere. The
    formats this toolchain owns must parse and match their own rules, and a
    path they record must stay inside the repository. Any other file, the
    map engine's included, is opaque: callers do not even load it, and its
    format is never described here. The directory is matched in any letter
    case.
    """
    if mode == _SYMLINK_MODE:
        return [
            _artifact(
                path, "a symlink under .legesher/ can point outside the repository"
            )
        ]
    if mode == _GITLINK_MODE:
        return [_artifact(path, "a submodule under .legesher/ is not a Legesher file")]
    if not is_known_artifact(path):
        return []
    if len(data) > MAX_ARTIFACT_BYTES:
        return [_artifact(path, f"too large to check ({len(data)} bytes)")]
    name = path.split("/", 1)[1].casefold()
    try:
        if name == "config.yml":
            return _check_config(path, data)
        if name.startswith("metadata/"):
            return _check_metadata(path, data)
        if name == "translation_memory.json":
            return _check_json(path, data, _translation_memory_problem)
        return _check_json(path, data, _identifier_map_problem)
    except (RecursionError, MemoryError):
        return [_artifact(path, "nested too deeply to check")]


def _load_yaml(path: str, data: bytes) -> tuple[object, list[Finding]]:
    import yaml

    try:
        return yaml.safe_load(data.decode("utf-8")), []
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        reason = str(exc).splitlines()[0]
        return None, [_artifact(path, f"not valid YAML: {reason}")]


def _check_config(path: str, data: bytes) -> list[Finding]:
    config, problems = _load_yaml(path, data)
    if problems:
        return problems
    if config is None:
        return []
    if not isinstance(config, dict):
        return [_artifact(path, "the configuration must be a mapping")]
    metadata = config.get("metadata")
    directory = metadata.get("directory") if isinstance(metadata, dict) else None
    if directory is None:
        return []
    # Under .legesher/ every entry is itself checked (no symlinks), so the
    # directory cannot reach outside the repository through the tree; a `..`
    # anywhere could step back out before that check applies.
    parts = [
        part for part in re.split(r"[\\/]+", str(directory)) if part not in ("", ".")
    ]
    if (
        _leaves_repository(directory)
        or ".." in parts
        or not parts
        or not is_legesher_path("/".join(parts))
    ):
        return [
            _artifact(
                path,
                f"metadata.directory {directory!r} must stay under .legesher/ "
                "(it leaves the repository or can through a symlink)",
            )
        ]
    return []


def _check_metadata(path: str, data: bytes) -> list[Finding]:
    from .metadata import REQUIRED_METADATA_FIELDS

    metadata, problems = _load_yaml(path, data)
    if problems:
        return problems
    if not isinstance(metadata, dict):
        return [_artifact(path, "metadata must be a mapping")]
    findings = []
    missing = [field for field in REQUIRED_METADATA_FIELDS if field not in metadata]
    if missing:
        findings.append(_artifact(path, f"metadata is missing {', '.join(missing)}"))
    if _leaves_repository(metadata.get("file")):
        findings.append(
            _artifact(
                path, f"metadata `file` {metadata['file']!r} leaves the repository"
            )
        )
    return findings


def _check_json(
    path: str, data: bytes, problem: Callable[[object], str | None]
) -> list[Finding]:
    import json

    try:
        document = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        return [_artifact(path, f"not valid JSON: {exc}")]
    reason = problem(document)
    return [_artifact(path, reason)] if reason else []


def _translation_memory_problem(document: object) -> str | None:
    from .translation_memory.model import TranslationMemoryDocument

    if not isinstance(document, dict):
        return "a translation memory must be an object"
    try:
        TranslationMemoryDocument.from_dict(document)
    except (ValueError, TypeError, KeyError) as exc:
        return f"not a valid translation memory: {exc}"
    return None


def _identifier_map_problem(document: object) -> str | None:
    from .tree_sitter.identifier_map import IdentifierMap

    try:
        IdentifierMap.from_dict(document)
    except ValueError as exc:
        return str(exc)
    return None


def check_blob(
    data: bytes, *, path: str, local: KeywordTable, stored: str | None = None
) -> list[Finding]:
    """All findings for one file's bytes.

    A declared encoding other than UTF-8, or bytes that are not UTF-8, is an
    ``encoding`` finding, and the other checks are skipped: the guard cannot
    vouch for text it cannot read as Python would.
    """
    declared: str | None
    try:
        declared, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
    except SyntaxError as exc:
        declared, problem = None, str(exc)
    if declared is not None and not _declaration_is_utf8(declared, data):
        message = f"declares its encoding as {declared}; Legesher files must be UTF-8"
        return [Finding(path, 1, 1, "encoding", message)]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        line = data.count(b"\n", 0, exc.start) + 1
        message = (
            f"byte 0x{data[exc.start]:02X} is not UTF-8; Legesher files must be UTF-8"
        )
        return [Finding(path, line, 1, "encoding", message)]
    if declared is None:
        message = f"unreadable coding declaration ({problem})"
        return [Finding(path, 1, 1, "encoding", message)]
    return check_source(text, path=path, local=local, stored=stored)


def check_source(
    text: str, *, path: str, local: KeywordTable, stored: str | None = None
) -> list[Finding]:
    """All findings for one file, ordered by position.

    Args:
        text: The content about to be committed.
        path: How to name the file in findings.
        local: The keyword table of the language this machine or repository
            writes in; also the script policy the Unicode check applies.
        stored: The version already committed, when there is one. It decides
            which language each block is stored in.
    """
    located: list[tuple[int, int, Finding]] = []
    for issue in scan_unicode(text, local.language):
        line, column = _position(text, issue.offset)
        classification = _CLASSIFICATION.get(issue.kind, "disallowed character")
        message = f"{issue.codepoint} {issue.char_name}: {classification}"
        located.append(
            (issue.offset, 0, Finding(path, line, column, "unicode", message))
        )
    for stray in find_strays(text, local=local, stored=stored):
        line, column = _position(text, stray.offset)
        message = (
            f"`{stray.found}` in a block stored in {stray.language}; "
            f"its stored form is `{stray.stored}`"
        )
        located.append(
            (stray.offset, 1, Finding(path, line, column, "keyword", message))
        )
    return [finding for _, _, finding in sorted(located, key=lambda item: item[:2])]


__all__ = [
    "BLOCKING_KINDS",
    "Finding",
    "check_artifact",
    "check_blob",
    "check_source",
    "identifier_format_allowlist",
    "identifier_script_issues",
    "scan_unicode",
]
