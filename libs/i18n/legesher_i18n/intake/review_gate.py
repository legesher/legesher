"""The mechanical gate on a markdown review pull request.

Runs with no database, no salt and no identity minting: in a language-packs
pull-request check through the published package, or on a maintainer's
machine before an import. It reads the file with the importer's own reader
(:func:`legesher_i18n.intake.review_parser.read_review`), checks the pin with
:func:`~legesher_i18n.intake.review_template.check_review_pin`, and runs the
mechanical checks over the ``Suggested`` column:

* ``identifier``: a valid Python identifier AT THE PINNED PYTHON VERSION, made
  term-aware (``except*`` keeps its ``*``). The running interpreter's tables
  answer for itself only, so the release a word needs is read from the pinned
  per-release tables in ``schema_validator`` (the characters CPython 3.13,
  3.14 and 3.15 each added: Sinhala ZWJ, U+30FB and the rest). Below that
  release the word is not an identifier, wherever the check runs. At or above
  it the running interpreter judges, and one whose Unicode tables predate
  the character reports that it cannot, naming the release to run on.
* ``nfkc``: NFKC-stable, with the canon gate's SARA AM allowance as a warning.
* ``script`` and ``format-chars``: the per-locale checks the canon trigger gates on.
* ``collision``: not the current word of another row, not another suggestion
  in the same file, and not a live Python keyword, soft keyword or builtin
  other than the row's own English term. ``keywords.type`` and
  ``builtins.type`` may share a word, as the packs do on purpose.
* ``version-tier`` (warning): a word that is an identifier only from a newer
  CPython release than the row's earliest one needs a second spelling for the
  earlier versions (the Sinhala ZWJ case). The pack exporter writes one
  across the 3.13 boundary only, so for a character 3.14 or 3.15 added the
  warning says the exporter refuses the word as written.

The result is one report naming every failing row by its key.
"""

from __future__ import annotations

import builtins as _builtins
import json
import keyword
import re
import unicodedata
from collections.abc import Collection, Mapping
from dataclasses import asdict, dataclass, field

from legesher_i18n.intake.review_parser import (
    check_submitter,
    code_span,
    read_review,
    template_words,
)
from legesher_i18n.intake.review_template import check_review_pin
from legesher_i18n.schema_validator import (
    _UNICODE_OF_CPYTHON,
    TIERED_IDENTIFIER_RELEASE,
    describe_newer_identifier_characters,
    identifier_characters_newer_than,
    interpreter_needed_for_identifier,
)
from legesher_i18n.surface_validation import (
    allowed_format_chars_for,
    allowed_scripts_for,
    validate_surface,
)

__all__ = ["Finding", "GateReport", "gate_review_file"]

_LIVE_NAMES = (
    frozenset(keyword.kwlist)
    | frozenset(keyword.softkwlist)
    | frozenset(dir(_builtins))
) - {"_"}
_RUNNING_UNICODE = tuple(int(part) for part in unicodedata.unidata_version.split("."))
_VERSION_RE = re.compile(r"\d+\.\d+")
# Bounded and ASCII-only: ``int`` raises on a digit run past its length limit,
# and the pin comes from the review file.
_PIN_RE = re.compile(r"(\d{1,3})\.(\d{1,3})", re.ASCII)
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_SHARED_TERMS = frozenset({"type"})
_TIER_WORD_RE = re.compile(r"\d+\.\d+ to \d+\.\d+: `([^`]+)`")


def _version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def _pin_release(python: str) -> tuple[int, int] | None:
    """The pinned Python as ``(major, minor)``, or ``None`` when it is not one.

    The review file is untrusted. A pin that does not read as a version is
    already a ``pin`` finding, so the row checks carry on without it and the
    gate still returns a report. Never raises, whatever the text.
    """
    match = _PIN_RE.match(python.strip())
    return (int(match[1]), int(match[2])) if match else None


@dataclass(frozen=True)
class Finding:
    """One problem: the row key (``None`` for the file), the check, and why."""

    key: str | None
    check: str
    severity: str
    detail: str


@dataclass
class GateReport:
    """Everything the gate found in one review file."""

    path: str
    pin: str | None
    findings: list[Finding] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not any(finding.severity == "fail" for finding in self.findings)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "pin": self.pin,
            "passed": self.passed,
            "counts": self.counts,
            "findings": [asdict(finding) for finding in self.findings],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n"

    def to_markdown(self) -> str:
        def plural(count: int, noun: str) -> str:
            return f"{count} {noun}{'' if count == 1 else 's'}"

        lines = [f"### Review file check: {code_span(self.path)}", ""]
        if self.pin:
            lines += [f"Pin: {code_span(self.pin)}", ""]
        if self.counts:
            lines += [
                "Read: "
                + ", ".join(
                    plural(self.counts.get(name, 0), name)
                    for name in ("endorsement", "suggestion", "comment")
                )
                + f" over {plural(self.counts.get('row', 0), 'row')}.",
                "",
            ]
        failing = [f for f in self.findings if f.severity == "fail"]
        keys = sorted({f.key for f in failing if f.key})
        if self.passed:
            lines.append("**Passes.** No failing rows.")
        else:
            lines.append(
                f"**Fails.** {plural(len(failing), 'problem')}"
                + (
                    f" on {plural(len(keys), 'row')}: "
                    + ", ".join(f"`{k}`" for k in keys)
                    if keys
                    else ""
                )
                + "."
            )
        if self.findings:
            lines += [
                "",
                "| Row | Check | Severity | Detail |",
                "| --- | ----- | -------- | ------ |",
            ]
            for finding in self.findings:
                where = code_span(finding.key) if finding.key else "(file)"
                detail = finding.detail.replace("|", "\\|").replace("\n", " ")
                lines.append(
                    f"| {where} | {finding.check} | {finding.severity} | {detail} |"
                )
        return "\n".join(lines) + "\n"


def _can_judge(release: tuple[int, int]) -> bool:
    """Whether this interpreter's Unicode tables know the characters *release* added."""
    needed = tuple(int(part) for part in _UNICODE_OF_CPYTHON[release].split("."))
    return _RUNNING_UNICODE[: len(needed)] >= needed


def _identifier_at(surface: str, term: str, python: str) -> bool | None:
    """Term-aware identifier validity at *python*, the per-release XID gaps emulated.

    The release a word needs comes from the pinned tables, never from the
    running interpreter, so the answer is the same wherever the gate runs:
    ``False`` when the word uses a character a CPython release newer than
    *python* added. ``None`` when this interpreter cannot say: the pin is new
    enough, but the word uses a character this interpreter's older Unicode
    tables do not know. Substituting a stand-in would be wrong both ways (ZWJ
    may continue a name but never start one), so the gate reports it instead
    of guessing. A pin that does not read as a version says nothing about
    "newer than", so that test is skipped and the running interpreter judges
    the word, where its tables can.
    """
    needed = interpreter_needed_for_identifier(surface)
    pinned = _pin_release(python)
    if needed is not None and pinned is not None and pinned < needed:
        return False
    if needed is not None and not _can_judge(needed):
        return None
    return validate_surface(surface, term, frozenset()).identifier_valid


def gate_review_file(
    text: str,
    *,
    template_text: str,
    path: str,
    author: str,
    known_versions: Collection[str],
    python_versions: Collection[str],
    registry_entry: Mapping[str, object] | None,
) -> GateReport:
    """Check one review file and report every problem, row by row.

    Args:
        text: the review file.
        template_text: the template it was copied from.
        path: the file's path in language-packs.
        author: the pull request author's GitHub login.
        known_versions: every version the pinned pack has carried.
        python_versions: the Python versions the pack has a version file for.
        registry_entry: the registry entry for the pinned code, or ``None``.
    """
    review, problems = read_review(text, template_text)
    report = GateReport(
        path=path,
        pin=review.meta.kit_version if review is not None else None,
        findings=[Finding(None, "structure", "fail", problem) for problem in problems]
        + [
            Finding(None, "note", "note", note)
            for note in (review.notes if review else [])
        ],
    )
    if review is None:
        return report
    meta = review.meta
    report.findings += [
        Finding(None, "pin", "fail", problem)
        for problem in check_review_pin(
            meta,
            known_versions=known_versions,
            python_versions=python_versions,
            registry_entry=registry_entry,
        )
    ]
    report.findings += [
        Finding(None, "submitter", "fail", problem)
        for problem in check_submitter(meta, review.username, path=path, author=author)
    ]

    words = template_words(template_text)
    allowed_scripts = allowed_scripts_for(meta.code)
    allowed_format = allowed_format_chars_for(meta.code)
    # Every word a row ships, the earlier-tier forms in its Applies-to cell too
    # (`3.13+ (3.10 to 3.12: \`X\`)`): a suggestion must collide with none of them.
    folded_current: list[tuple[str, str]] = []
    for other_key, (_, word, applies) in words.items():
        shipped = ([word] if word is not None else []) + _TIER_WORD_RE.findall(applies)
        folded_current += [
            (other_key, unicodedata.normalize("NFKC", w)) for w in shipped
        ]
    suggestions = {
        row.key: unicodedata.normalize("NFC", row.suggested)
        for row in review.rows
        if row.verdict == "suggest"
    }

    def add(key: str | None, check: str, severity: str, detail: str) -> None:
        report.findings.append(Finding(key, check, severity, detail))

    for key, surface in suggestions.items():
        term = key.split(".", 1)[1]
        english, _, applies_to = words[key]
        verdict = validate_surface(surface, term, allowed_scripts, allowed_format)
        shown = code_span(surface)
        valid = _identifier_at(surface, term, meta.python)
        needed = interpreter_needed_for_identifier(surface)
        if valid is None:
            release = f"{needed[0]}.{needed[1]}"
            add(
                key,
                "identifier",
                "fail",
                f"{shown} uses a character only Python {release}+ reads as part of a "
                f"name, and this interpreter ({unicodedata.unidata_version} Unicode "
                f"tables) cannot judge it; run the check on Python {release} or newer",
            )
        elif not valid:
            pinned = _pin_release(meta.python)
            too_new = (
                describe_newer_identifier_characters(surface, floor=pinned)
                if needed is not None and pinned is not None
                else ""
            )
            add(
                key,
                "identifier",
                "fail",
                f"{shown} is not a valid Python identifier on Python {meta.python}"
                + (f": it uses {too_new}" if too_new else ""),
            )
        if not verdict.nfkc_stable:
            folded = unicodedata.normalize("NFKC", surface)
            if verdict.nfkc_delta_class == "sara-am-only":
                add(
                    key,
                    "nfkc",
                    "warn",
                    f"{shown} changes under NFKC only by SARA AM; canon allows it",
                )
            else:
                add(
                    key,
                    "nfkc",
                    "fail",
                    f"{shown} is not NFKC-stable (Python reads it as {code_span(folded)})",
                )
        if not verdict.script_consistent:
            add(
                key,
                "script",
                "fail",
                f"{shown} mixes in a script this language's policy does not allow",
            )
        if not verdict.format_chars_clean:
            add(
                key,
                "format-chars",
                "fail",
                f"{shown} carries a format or invisible character this language's "
                "policy does not allow",
            )
        folded = unicodedata.normalize("NFKC", surface)
        for other in sorted({o for o, word in folded_current if word == folded}):
            shared = term in _SHARED_TERMS and other.split(".", 1)[1] == term
            if other != key and not shared:
                add(
                    key,
                    "collision",
                    "fail",
                    f"{shown} is already a word for `{other}` in this pack",
                )
        for other, word in suggestions.items():
            shared = term in _SHARED_TERMS and other.split(".", 1)[1] == term
            if (
                other != key
                and unicodedata.normalize("NFKC", word) == folded
                and not shared
            ):
                add(
                    key,
                    "collision",
                    "fail",
                    f"{shown} is also suggested for `{other}` in this file",
                )
        if folded in _LIVE_NAMES and folded != english:
            add(
                key,
                "collision",
                "fail",
                f"{shown} is the live Python name `{folded}`, which this pack must not shadow",
            )
        # The row ships from its earliest version on. A character a later
        # release added cannot be read there, whichever release that is.
        earliest = min(
            (_version(v)[:2] for v in _VERSION_RE.findall(applies_to)),
            default=needed or (3, 13),
        )
        if needed is not None and identifier_characters_newer_than(
            surface, floor=earliest
        ):
            newer = identifier_characters_newer_than(surface, floor=earliest)
            names = describe_newer_identifier_characters(surface, floor=earliest)
            characters = sum(len(found) for found in newer.values())
            first = f"{earliest[0]}.{earliest[1]}"
            last = f"{needed[0]}.{needed[1] - 1}"
            older = first if first == last else f"{first} to {last}"
            detail = (
                f"{shown} uses {names}, "
                + (
                    "identifier characters"
                    if characters > 1
                    else "an identifier character"
                )
                + " only from the Python "
                + ("releases" if len(newer) > 1 else "release")
                + " named"
                + f"; this row also ships for Python {older}, so the pack needs a "
                "second spelling for that tier"
            )
            if needed > TIERED_IDENTIFIER_RELEASE:
                tiered = ".".join(str(part) for part in TIERED_IDENTIFIER_RELEASE)
                detail += (
                    f". The pack exporter writes a second spelling across the "
                    f"Python {tiered} boundary only, so it refuses this word as "
                    "written"
                )
            add(key, "version-tier", "warn", detail)

    free_text = [row.comments for row in review.rows] + [
        review.locale_notes or "",
        (review.credit or ("", ""))[1] or "",
    ]
    for row_text in free_text:
        for address in _EMAIL_RE.findall(row_text):
            add(
                None,
                "privacy",
                "warn",
                f"an email address ({code_span(address)}) is in the file, which is public; "
                "ask the reviewer to remove it",
            )

    endorsements = sum(row.verdict in ("endorse", "keep") for row in review.rows)
    report.counts = {
        "row": len(review.rows),
        "endorsement": endorsements,
        "suggestion": len(suggestions),
        "comment": sum(row.verdict == "comment" for row in review.rows),
    }
    return report
