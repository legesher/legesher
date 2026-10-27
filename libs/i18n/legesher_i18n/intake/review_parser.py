"""Markdown review lane: a filled review template → canonical review bundle.

A reviewer copies a pack's generated ``REFERENCE.md`` (``reference/<tag>.md`` in
language-packs) to ``reviews/<tag>/<tag>-<github-username>.md``, fills the
``Suggested`` and ``Comments`` columns, ticks the boxes under "Before you
submit" and opens a pull request. Once it merges, this module turns the file
into the SAME bundle every other lane produces, so one pipeline imports it.

The reader keys on structure, never on prose: the hidden first line, the
checkbox lines, the column positions and the row keys. Every cell a reviewer
is not meant to touch is compared with the template the file was copied from,
byte for byte, so a review always says which exact words it judged. Wording
the reviewer is meant to change (the About-you answers, the credit line) is
read against the template's own options by position.

Row vocabulary (REVIEWING.md section 7, "How to submit this review"):

* ``✓`` in Comments, Suggested empty: an endorsement of the current word. Text
  after the tick rides as the endorsement's comment (``✓ Good: reads well``).
* ``Keep`` plus a note (``✓ Keep: …`` reads the same): an endorsement of the
  current word with the note as its comment, the recorded limitation.
* A word in Suggested, reasoning in Comments: an endorsement of the SUGGESTED
  word (a new option when the corpus has not met it), never of the current one.
* Comments with neither: commentary on the concept, no vote either way.
* Untouched: no opinion, nothing minted.
* "Notes for Future Updates": locale-wide commentary (no concept).

Two row kinds need a decision, recorded here and tested:

* A dialect row marked ``inherited from <base>`` judges the word FOR THE
  DIALECT: a tick endorses that word in the dialect's locale, and a suggestion
  proposes a dialect word. Nothing is recorded against the base locale. A
  parse note names each such row so the import ritual sees it.
* A ``(no word in this pack)`` row has no word to endorse, so a tick or a
  ``Keep`` there is refused by key. A suggestion proposes the first word for the
  term; a comment is commentary.

Identity comes from the pull request, never from the file: the username typed
under About you and the one in the file name are checks against the PR author
and are refused on a mismatch (GitHub logins compare case-insensitively). A
submission may assert its own words, never facts about a person (CORE-1688).

The lane's importer parameters are :data:`REVIEW_LANE`: ``method='github'``,
``elicited='after_reveal'`` on every row (the reviewer saw the current word
before answering; that is the lane record the promotion gate reads), and the
full attestation set, because the template collects a DCO sign-off.
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from legesher_i18n.intake.review_template import (
    METADATA_PREFIX,
    ReviewTemplateError,
    code_span,
    TemplateMetadata,
    parse_metadata_line,
    review_folder,
)

__all__ = [
    "BUNDLE_VERSION",
    "REVIEW_LANE",
    "ParsedReview",
    "PullRequest",
    "ReviewFile",
    "ReviewFileRefused",
    "ReviewRow",
    "check_submitter",
    "code_span",
    "parse_review_file",
    "read_review",
    "read_review_file",
    "template_words",
]

#: Bundle 1.1 adds the pull-request source and locale-wide commentary.
BUNDLE_VERSION = "1.1"

#: ``BundleImporter`` keyword arguments for this lane.
REVIEW_LANE: dict[str, object] = {
    "method": "github",
    "elicited_default": "after_reveal",
    "required_attestations": ("original_work", "coc_agreed", "dco"),
}

NO_WORD = "(no word in this pack)"
TICKS = ("✓", "✔", "✅")
#: ``Keep`` only as a whole verdict: alone, or followed by punctuation and a note.
#: "Keep in mind this reads as when" is a comment, never an endorsement.
_KEEP_RE = re.compile(
    r"^keep(?=\s*(?:$|[:,.\-\u2013\u2014]))[\s:,.\-\u2013\u2014]*", re.IGNORECASE
)
_INHERITED_RE = re.compile(r" · inherited from (?P<base>\S+)$")
_KEY_CELL_RE = re.compile(r"^`(?P<key>[a-z_]+\.[^`]+)`$")
_CODE_SPAN_RE = re.compile(r"`([^`]*)`")
_CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")
_CHECKBOX_RE = re.compile(r"^- \[(?P<mark>[ xX])\] (?P<label>.*)$")
_PRIVACY_VERSION_RE = re.compile(r"version (?P<version>\d+(?:\.\d+)*)")
_HEADING_RE = re.compile(r"^## (?P<title>.+?)\s*$")

#: The columns a reviewer must leave as they are, by position.
_FIXED_COLUMNS = ("Key", "English", "current word", "Applies to")
_COLUMNS = 6

#: The boxes under "Before you submit", in template order: five required, one optional.
_CONSENT_FIELDS = (
    "original_work",
    "dco",
    "license_grant",
    "coc_agreed",
    "privacy",
    "research_use",
)
_REQUIRED_BOXES = 5

#: The About-you relationship options, in template order: (rung, native_or_fluent).
#: Only a native claim earns ``native_claimed``: the rung is a published weight,
#: and "fluent" must not inherit a native speaker's (the issue lane's rule).
_RELATIONSHIPS = (
    ("native_claimed", True),
    ("contributor", True),
    ("contributor", False),
    ("contributor", False),
)

#: The credit options, in template order. The third carries a name in a code span.
_CREDITS = ("anonymous", "handle", "name")
_NAME_PLACEHOLDER = "<name>"
_USERNAME_PLACEHOLDER = "<your-github-username>"

#: ``terms.category`` values a template section's keys resolve through.
_SECTION_CATEGORIES: dict[str, tuple[str, ...]] = {
    "keywords": ("keyword",),
    "builtins": ("builtin_func", "builtin_type", "special_constant"),
    "exceptions": ("exception",),
    "implicit_params": ("implicit_param",),
}

_ABOUT = "About you"
_CONSENT = "Before you submit"
_NOTES = "Notes for Future Updates"


class ReviewFileRefused(ValueError):
    """A review file the lane will not import, with every problem found.

    Each problem names the row key or the line it is about, so the report can
    go back to the reviewer as it is.
    """

    def __init__(self, problems: list[str]) -> None:
        self.problems = list(problems)
        super().__init__("review file refused:\n- " + "\n- ".join(self.problems))


@dataclass(frozen=True)
class PullRequest:
    """The pull request that carried the file, as GitHub reports it."""

    url: str
    number: int
    author: str
    created_at: str | None = None


@dataclass(frozen=True)
class ReviewRow:
    """One term row of a review file, with the verdict its two cells carry."""

    key: str
    line: int
    current: str | None
    applies_to: str
    inherited_from: str | None
    suggested: str
    comments: str
    verdict: str
    comment: str | None


@dataclass
class ReviewFile:
    """What a review file says, read against the template it was copied from."""

    meta: TemplateMetadata
    rows: list[ReviewRow]
    username: str | None
    relationship: int | None
    ticked: dict[str, bool]
    consent_version: str | None
    credit: tuple[str, str | None] | None
    locale_notes: str | None
    notes: list[str] = field(default_factory=list)

    @property
    def answered(self) -> list[ReviewRow]:
        return [row for row in self.rows if row.verdict != "untouched"]


@dataclass
class ParsedReview:
    """The bundle plus everything the parser could not carry into it."""

    bundle: dict
    notes: list[str]
    review: ReviewFile


# --- reading ---------------------------------------------------------------------


def _lines(text: str) -> list[str]:
    return text.lstrip("\ufeff").replace("\r\n", "\n").split("\n")


def _sections(
    lines: list[str], titles: list[str]
) -> tuple[dict[str, tuple[int, int]], list[str]]:
    """``title -> (first body line, end)`` for the *titles*, matched in order outside fences.

    In-order matching keeps a heading typed into an earlier section inert, as
    the issue lane does. A title that never appears is returned as missing.
    """
    found: list[tuple[str, int]] = []
    expected = 0
    in_fence = False
    for index, line in enumerate(lines):
        if line.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        match = None if in_fence else _HEADING_RE.match(line)
        if match is None or expected >= len(titles):
            continue
        try:
            position = titles.index(match.group("title"), expected)
        except ValueError:
            continue
        found.append((titles[position], index))
        expected = position + 1
    spans: dict[str, tuple[int, int]] = {}
    for number, (title, index) in enumerate(found):
        end = found[number + 1][1] if number + 1 < len(found) else len(lines)
        spans[title] = (index + 1, end)
    return spans, [title for title in titles if title not in spans]


def _headings(lines: list[str]) -> list[str]:
    titles: list[str] = []
    in_fence = False
    for line in lines:
        if line.startswith(("```", "~~~")):
            in_fence = not in_fence
        elif not in_fence and (match := _HEADING_RE.match(line)):
            titles.append(match.group("title"))
    return titles


def _cells(line: str) -> list[str]:
    body = line.strip()
    body = body[1:] if body.startswith("|") else body
    body = body[:-1] if body.endswith("|") and not body.endswith("\\|") else body
    return [cell.strip().replace("\\|", "|") for cell in _CELL_SPLIT_RE.split(body)]


def _term_rows(lines: list[str]) -> list[tuple[int, list[str]]]:
    """``(line index, cells)`` of every term row outside code fences."""
    rows: list[tuple[int, list[str]]] = []
    in_fence = False
    for index, line in enumerate(lines):
        if line.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence or not line.lstrip().startswith("|"):
            continue
        cells = _cells(line)
        if cells and _KEY_CELL_RE.match(cells[0]):
            rows.append((index, cells))
    return rows


def _header_rows(lines: list[str]) -> list[tuple[int, str]]:
    return [
        (index, line)
        for index, line in enumerate(lines)
        if line.lstrip().startswith("| Key |")
    ]


def _checkboxes(lines: list[str]) -> list[tuple[bool, str]]:
    """``(ticked, label)`` per checkbox item, continuation lines joined."""
    boxes: list[tuple[bool, str]] = []
    for line in lines:
        match = _CHECKBOX_RE.match(line)
        if match:
            boxes.append((match.group("mark") in "xX", match.group("label").strip()))
        elif boxes and line.startswith("  ") and line.strip():
            ticked, label = boxes[-1]
            boxes[-1] = (ticked, f"{label} {line.strip()}")
    return boxes


def _answer(line: str) -> str:
    """The part of a ``… (keep one): a · b · c`` line after the colon."""
    return line.split("):", 1)[1].strip() if "):" in line else ""


def _line_starting(lines: list[str], prefix: str) -> str | None:
    return next((line for line in lines if line.startswith(prefix)), None)


def _pick(
    answer: str, options: list[str], *, prefixed: int | None = None
) -> int | None:
    """The one option *answer* keeps, by position; ``None`` unless exactly one is kept.

    The kept answer must BE an option (split on ``·``, case and spacing aside),
    never merely contain one: "non-native speaker" contains "native speaker",
    and the rung it would earn is a published weight. The option at index
    *prefixed* carries a fill-in (``this name: `<name>```) and matches by its
    text before the code span.
    """
    parts = [part.strip().casefold() for part in answer.split("·") if part.strip()]
    if len(parts) != 1:
        return None
    for index, option in enumerate(options):
        folded = option.casefold()
        if parts[0] == folded or (index == prefixed and parts[0].startswith(folded)):
            return index
    return None


def _verdict(suggested: str, comments: str) -> tuple[str, str | None]:
    if suggested:
        return "suggest", comments or None
    if not comments:
        return "untouched", None
    rest = comments
    tick = next((mark for mark in TICKS if comments.startswith(mark)), None)
    if tick is not None:
        # U+FE0F is the emoji presentation selector some keyboards add after ✔.
        rest = comments[len(tick) :].lstrip("\ufe0f").strip()
    keep = _KEEP_RE.match(rest)
    if keep is not None:
        return "keep", rest[keep.end() :].strip() or None
    if tick is not None:
        return "endorse", rest or None
    return "comment", comments


def _unwrap(cell: str) -> str:
    match = re.fullmatch(r"`([^`]+)`", cell)
    return match.group(1) if match else cell


def read_review(text: str, template_text: str) -> tuple[ReviewFile | None, list[str]]:
    """Read *text* against *template_text*; the file (when readable) and every problem.

    The gate wants both halves: a report of what is wrong AND the rows it could
    still check. :func:`read_review_file` is the refusing form the importer uses.
    """
    problems: list[str] = []
    notes: list[str] = []
    template_lines = _lines(template_text)
    lines = _lines(text)
    template_meta = parse_metadata_line(template_text)

    try:
        meta = parse_metadata_line(text)
    except ReviewTemplateError as error:
        return None, [f"line 1: {error}"]
    if lines[0] != template_lines[0]:
        problems.append(
            "line 1: the hidden first line pins "
            + ", ".join(
                code_span(v)
                for v in (meta.pack, meta.pack_version, meta.python, meta.digest)
            )
            + "; the template it is checked against pins "
            + ", ".join(
                code_span(v)
                for v in (
                    template_meta.pack,
                    template_meta.pack_version,
                    template_meta.python,
                    template_meta.digest,
                )
            )
            + " (pack, version, Python, digest). A review is read only against the exact "
            "template it was copied from."
        )
    for number, line in enumerate(lines[1:], start=2):
        if METADATA_PREFIX in line:
            problems.append(
                f"line {number}: a second {METADATA_PREFIX} line; a review file "
                "carries exactly one, on line 1"
            )

    titles = _headings(template_lines)
    spans, missing = _sections(lines, titles)
    template_spans, _ = _sections(template_lines, titles)
    for title in missing:
        problems.append(f"the section '## {title}' is missing; it is in the template")
    found = _headings(lines)
    for title in sorted({title for title in titles if found.count(title) > 1}):
        notes.append(
            f"the heading '## {title}' appears {found.count(title)} times; the section "
            "was read from the first, so text after a repeat may belong elsewhere"
        )

    def body(
        source: list[str], span_map: dict[str, tuple[int, int]], title: str
    ) -> list[str]:
        start, end = span_map.get(title, (0, 0))
        return source[start:end]

    # About you.
    about = body(lines, spans, _ABOUT)
    template_about = body(template_lines, template_spans, _ABOUT)
    username: str | None = None
    user_line = _line_starting(about, "- GitHub username:")
    if user_line is None:
        problems.append("About you: the '- GitHub username:' line is missing")
    else:
        span = _CODE_SPAN_RE.search(user_line)
        typed = span.group(1).strip() if span else ""
        username = None if typed in ("", _USERNAME_PLACEHOLDER) else typed
    relationship: int | None = None
    template_rel = _line_starting(template_about, "- Your relationship to")
    review_rel = _line_starting(about, "- Your relationship to")
    rel_options = [part.strip() for part in _answer(template_rel or "").split("·")]
    if len(rel_options) != len(_RELATIONSHIPS):
        raise ValueError(
            f"the template's relationship line changed shape: {template_rel!r}"
        )
    if review_rel is None:
        problems.append("About you: the '- Your relationship to' line is missing")
    elif _answer(review_rel) != _answer(template_rel or ""):
        relationship = _pick(_answer(review_rel), rel_options)
    if relationship is None:
        notes.append(
            "the relationship line under About you does not keep exactly one answer: "
            "recorded at the 'contributor' rung, the safe default; ask in the reply"
        )

    # Before you submit.
    consent = body(lines, spans, _CONSENT)
    template_consent = body(template_lines, template_spans, _CONSENT)
    boxes = _checkboxes(consent)
    template_boxes = _checkboxes(template_consent)
    if len(template_boxes) != len(_CONSENT_FIELDS):
        raise ValueError(
            f"the template carries {len(template_boxes)} boxes, not {len(_CONSENT_FIELDS)}"
        )
    ticked: dict[str, bool] = {}
    consent_version: str | None = None
    if [label for _, label in boxes] != [label for _, label in template_boxes]:
        problems.append(
            "Before you submit: the boxes differ from the template's "
            f"({len(boxes)} found, {len(template_boxes)} expected, or a label was "
            "reworded). Tick the boxes; do not edit their wording."
        )
    else:
        ticked = {name: mark for name, (mark, _) in zip(_CONSENT_FIELDS, boxes)}
        for name, (mark, label) in list(zip(_CONSENT_FIELDS, boxes))[:_REQUIRED_BOXES]:
            if not mark:
                problems.append(
                    f"Before you submit: the required box '{label}' is not ticked"
                )
        version = _PRIVACY_VERSION_RE.search(
            template_boxes[_CONSENT_FIELDS.index("privacy")][1]
        )
        if version is None:
            raise ValueError("the template's privacy box names no notice version")
        consent_version = version.group("version")

    credit: tuple[str, str | None] | None = None
    template_credit = _line_starting(template_consent, "Credit me as")
    review_credit = _line_starting(consent, "Credit me as")
    credit_options = [
        part.strip() for part in _answer(template_credit or "").split("·")
    ]
    if len(credit_options) != len(_CREDITS):
        raise ValueError(
            f"the template's credit line changed shape: {template_credit!r}"
        )
    if review_credit is not None and _answer(review_credit) != _answer(
        template_credit or ""
    ):
        name_prefix = credit_options[2].split("`", 1)[0].strip()
        choice = _pick(
            _answer(review_credit), [*credit_options[:2], name_prefix], prefixed=2
        )
        if choice is not None and _CREDITS[choice] == "name":
            span = _CODE_SPAN_RE.search(_answer(review_credit))
            name = span.group(1).strip() if span else ""
            credit = None if name in ("", _NAME_PLACEHOLDER) else ("name", name)
        elif choice is not None:
            credit = (_CREDITS[choice], None)
    if credit is None:
        notes.append(
            "the credit line does not keep exactly one choice (or names no name): "
            "recorded as 'anonymous', the default; ask in the reply"
        )

    # Term tables. The notes section is free text: a table pasted there is prose.
    tables = list(lines)
    start, end = spans.get(_NOTES, (0, 0))
    tables[start:end] = [""] * (end - start)
    template_rows = {cells[0]: cells for _, cells in _term_rows(template_lines)}
    template_headers = {line for _, line in _header_rows(template_lines)}
    for index, line in _header_rows(tables):
        if line not in template_headers:
            problems.append(
                f"line {index + 1}: a table header differs from the template's; "
                f"it has {len(_cells(line))} columns where the template has {_COLUMNS}"
            )
    rows: list[ReviewRow] = []
    seen: dict[str, int] = {}
    for index, cells in _term_rows(tables):
        key = _KEY_CELL_RE.match(cells[0]).group("key")  # type: ignore[union-attr]
        number = index + 1
        if key in seen:
            problems.append(
                f"`{key}` appears more than once (lines {seen[key]} and {number})"
            )
            continue
        seen[key] = number
        expected = template_rows.get(cells[0])
        if expected is None:
            problems.append(f"`{key}` (line {number}) is not a row of this template")
            continue
        if len(cells) != _COLUMNS:
            problems.append(
                f"`{key}` (line {number}) has {len(cells)} columns where the template "
                f"has {_COLUMNS}; a '|' inside a comment must be written '\\|'"
            )
            continue
        edited = False
        for column, (got, want) in enumerate(zip(cells[:4], expected[:4])):
            if got == want:
                continue
            edited = True
            name = _FIXED_COLUMNS[column]
            if unicodedata.normalize("NFC", got) == unicodedata.normalize("NFC", want):
                problems.append(
                    f"`{key}` (line {number}): the {name} cell differs from the template "
                    "only in Unicode normalization (an editor rewrote it); restore the "
                    "template's text"
                )
            else:
                problems.append(
                    f"`{key}` (line {number}): the {name} cell was edited; it must read "
                    f"{want} exactly as in the template"
                )
        if edited:
            continue
        current = None if expected[2] == NO_WORD else _unwrap(expected[2])
        inherited = _INHERITED_RE.search(expected[3])
        suggested = _unwrap(cells[4])
        verdict, comment = _verdict(suggested, cells[5])
        if current is None and verdict in ("endorse", "keep"):
            problems.append(
                f"`{key}` (line {number}): this pack has no word for the term, so there "
                "is nothing to endorse; put a word in Suggested, or a note without ✓ "
                "or Keep in Comments"
            )
            continue
        if verdict == "keep" and comment is None:
            notes.append(
                f"`{key}`: Keep without a note, recorded as a plain endorsement"
            )
        if verdict == "suggest" and comment is None:
            notes.append(
                f"`{key}`: a suggestion without reasoning; ask for it in the reply"
            )
        if inherited is not None and verdict != "untouched":
            notes.append(
                f"`{key}` is inherited from {inherited.group('base')}: the verdict is "
                f"recorded for {meta.bcp47}, never for {inherited.group('base')}"
            )
        rows.append(
            ReviewRow(
                key=key,
                line=number,
                current=current,
                applies_to=expected[3],
                inherited_from=inherited.group("base") if inherited else None,
                suggested=suggested,
                comments=cells[5],
                verdict=verdict,
                comment=comment,
            )
        )
    absent = [cell for cell in template_rows if cell.strip("`") not in seen]
    if absent:
        notes.append(
            f"{len(absent)} template row(s) deleted from the file: read as no opinion"
        )

    # Notes for Future Updates: what the reviewer added to the template's paragraph.
    template_notes = "\n".join(body(template_lines, template_spans, _NOTES)).strip()
    review_notes = "\n".join(body(lines, spans, _NOTES)).strip()
    added = (
        review_notes.replace(template_notes, "", 1).strip()
        if template_notes
        else review_notes
    )

    review = ReviewFile(
        meta=meta,
        rows=rows,
        username=username,
        relationship=relationship,
        ticked=ticked,
        consent_version=consent_version,
        credit=credit,
        locale_notes=added or None,
        notes=notes,
    )
    return review, problems


def template_words(template_text: str) -> dict[str, tuple[str, str | None, str]]:
    """``key -> (English term, current word or None, Applies to)`` for every row of a template."""
    words: dict[str, tuple[str, str | None, str]] = {}
    for _, cells in _term_rows(_lines(template_text)):
        key = _KEY_CELL_RE.match(cells[0]).group("key")  # type: ignore[union-attr]
        current = None if cells[2] == NO_WORD else _unwrap(cells[2])
        words[key] = (_unwrap(cells[1]), current, cells[3])
    return words


def read_review_file(text: str, template_text: str) -> ReviewFile:
    """Read a review file, refusing it with every problem when it cannot be trusted.

    Raises:
        ReviewFileRefused: naming each row or line that is wrong.
    """
    review, problems = read_review(text, template_text)
    if problems or review is None:
        raise ReviewFileRefused(problems)
    return review


def check_submitter(
    meta: TemplateMetadata, username: str | None, *, path: str, author: str
) -> list[str]:
    """Problems with where the file sits and who it names, against the PR author."""
    problems: list[str] = []
    folder = review_folder(meta.code, meta.bcp47)
    expected = f"reviews/{folder}/{folder}-{author}.md"
    parts = PurePosixPath(path).parts
    name = parts[-1] if parts else ""
    named: str | None = None
    if (
        len(parts) == 3
        and parts[:2] == ("reviews", folder)
        and name.startswith(f"{folder}-")
        and name.endswith(".md")
    ):
        named = name[len(folder) + 1 : -len(".md")]
        suffix = f"-{meta.pack_version}"
        if named.endswith(suffix):
            named = named[: -len(suffix)]
    if named is None:
        problems.append(
            f"{code_span(path)} is not where a review of this pin lives: expected {expected} "
            f"(or {expected[:-3]}-{meta.pack_version}.md after a pack version bump)"
        )
    elif named.casefold() != author.casefold():
        problems.append(
            f"{code_span(path)}: the file name names {code_span(named)}, but the pull request was opened by "
            f"{author}. The username in the name must be the account that opens it."
        )
    if username is not None and username.casefold() != author.casefold():
        problems.append(
            f"About you: the GitHub username reads {code_span(username)}, but the pull request "
            f"was opened by {author}"
        )
    return problems


# --- the bundle ------------------------------------------------------------------


def _concept(conn: sqlite3.Connection, key: str) -> list[str]:
    section, term = key.split(".", 1)
    categories = _SECTION_CATEGORIES.get(section, ())
    marks = ",".join("?" for _ in categories)
    return [
        slug
        for (slug,) in conn.execute(
            "SELECT DISTINCT c.slug FROM terms t JOIN concepts c ON c.id = t.concept_id"
            f" WHERE t.name = ? AND t.programming_language = 'python' AND t.category IN ({marks})"
            " ORDER BY c.slug",
            (term, *categories),
        )
    ]


def parse_review_file(
    text: str,
    *,
    template_text: str,
    path: str,
    pull_request: PullRequest,
    conn: sqlite3.Connection,
) -> ParsedReview:
    """Turn one merged review file into a review bundle.

    Args:
        text: the review file as it is on the merged branch.
        template_text: the template it was copied from (same hidden first line).
        path: its path in language-packs (``reviews/<tag>/<tag>-<user>.md``).
        pull_request: the pull request that carried it; identity comes from here.
        conn: the target v2 database, used only to resolve row keys to concepts.

    Raises:
        ReviewFileRefused: naming every row or line that is wrong.
    """
    review, problems = read_review(text, template_text)
    if review is None:
        raise ReviewFileRefused(problems)
    problems += check_submitter(
        review.meta, review.username, path=path, author=pull_request.author
    )

    responses: dict[str, dict] = {}
    for row in review.answered:
        slugs = _concept(conn, row.key)
        if len(slugs) != 1:
            problems.append(
                f"`{row.key}` (line {row.line}): resolves to "
                f"{len(slugs) or 'no'} concept(s) in this database"
                f"{' (' + ', '.join(slugs) + ')' if slugs else ''}; the database "
                "is older or newer than the template"
            )
            continue
        response = responses.setdefault(
            slugs[0],
            {
                "concept": slugs[0],
                "blind": None,
                "endorsements": [],
                "ranking": [],
                "flags": [],
                "expansion": None,
                "commentary": [],
            },
        )
        if row.verdict in ("endorse", "keep"):
            response["endorsements"].append(
                {"surface_form": row.current, "annotations": [], "comment": row.comment}
            )
        elif row.verdict == "suggest":
            response["endorsements"].append(
                {
                    "surface_form": row.suggested,
                    "annotations": [],
                    "comment": row.comment,
                }
            )
        else:
            response["commentary"].append({"topic": "general", "body": row.comment})
    if problems:
        raise ReviewFileRefused(problems)

    rung, fluent = (
        _RELATIONSHIPS[review.relationship]
        if review.relationship is not None
        else ("contributor", False)
    )
    preference, credit_text = review.credit or ("anonymous", None)
    consent: dict[str, str] = {
        "consent_version": review.consent_version or "",
        "credit_preference": preference,
    }
    if credit_text:
        consent["credit_text"] = credit_text
    bundle: dict = {
        "bundle_version": BUNDLE_VERSION,
        "kit_version": review.meta.kit_version,
        "locale": review.meta.bcp47,
        # Options are concept-wide, as the pack migration mints them.
        "programming_language": None,
        "track": "reserved_words",
        "contributor": {
            "source_key": pull_request.author,
            "claimed_rung": rung,
            "contact_captured": False,
            "consent": consent,
        },
        "attestations": {
            "native_or_fluent": fluent,
            "original_work": review.ticked["original_work"],
            "license_grant": "Apache-2.0",
            "coc_agreed": review.ticked["coc_agreed"],
            "dco": review.ticked["dco"],
            "research_use": review.ticked["research_use"],
        },
        "responses": [responses[slug] for slug in sorted(responses)],
        "source": {
            "kind": "github_pull_request",
            "url": pull_request.url,
            "id": pull_request.number,
            "created_at": pull_request.created_at,
            "path": path,
        },
    }
    if review.locale_notes:
        bundle["locale_commentary"] = [
            {"topic": "general", "body": review.locale_notes}
        ]
    return ParsedReview(bundle=bundle, notes=list(review.notes), review=review)
