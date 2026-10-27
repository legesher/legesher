"""The mechanical gate on a markdown review pull request.

Runs with no database, no salt and no identity minting: in a language-packs
pull-request check through the published package, or on a maintainer's
machine before an import. It reads the file with the importer's own reader
(:func:`legesher_i18n.intake.review_parser.read_review`), checks the pin with
:func:`~legesher_i18n.intake.review_template.check_review_pin`, and runs the
mechanical checks over the ``Suggested`` column:

* ``identifier``: a valid Python identifier AT THE PINNED PYTHON VERSION, made
  term-aware (``except*`` keeps its ``*``). The running interpreter's tables
  answer for itself only, so the one measured gap is emulated: a character
  CPython 3.13 added to XID (Sinhala ZWJ, U+30FB and 5,672 others, pinned in
  ``schema_validator``) is invalid at a 3.10 to 3.12 pin and valid at 3.13+.
* ``nfkc``: NFKC-stable, with the canon gate's SARA AM allowance as a warning.
* ``script`` and ``format-chars``: the per-locale checks the canon trigger gates on.
* ``collision``: not the current word of another row, not another suggestion
  in the same file, and not a live Python keyword, soft keyword or builtin
  other than the row's own English term. ``keywords.type`` and
  ``builtins.type`` may share a word, as the packs do on purpose.
* ``version-tier`` (warning): a word that is an identifier only from CPython
  3.13, on a row the pack also ships for 3.10 to 3.12, needs a second spelling
  for the earlier tier (the Sinhala ZWJ case, CORE-1521).

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
from legesher_i18n.schema_validator import _XID_CHARS_ADDED_BY_CPYTHON_313
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
_UNICODE_15_1 = tuple(int(part) for part in unicodedata.unidata_version.split(".")) >= (
    15,
    1,
)
_VERSION_RE = re.compile(r"\d+\.\d+")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_SHARED_TERMS = frozenset({"type"})
_TIER_WORD_RE = re.compile(r"\d+\.\d+ to \d+\.\d+: `([^`]+)`")


def _version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


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


def _identifier_at(surface: str, term: str, python: str) -> bool | None:
    """Term-aware identifier validity at *python*, the 3.13 XID gap emulated.

    ``None`` when this interpreter cannot say: a 3.13+ pin on a word using a
    character CPython 3.13 added, judged on older Unicode tables. Substituting
    a stand-in would be wrong both ways (ZWJ may continue a name but never
    start one), so the gate reports it instead of guessing.
    """
    newer = {char for char in surface if char in _XID_CHARS_ADDED_BY_CPYTHON_313}
    if newer and _version(python) < (3, 13):
        return False
    if newer and not _UNICODE_15_1:
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
        if valid is None:
            add(
                key,
                "identifier",
                "fail",
                f"{shown} uses a character only Python 3.13+ reads as part of a name, "
                f"and this interpreter ({unicodedata.unidata_version} Unicode tables) "
                "cannot judge it; run the check on Python 3.13 or newer",
            )
        elif not valid:
            add(
                key,
                "identifier",
                "fail",
                f"{shown} is not a valid Python identifier on Python {meta.python}",
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
        newer = sorted(
            {char for char in surface if char in _XID_CHARS_ADDED_BY_CPYTHON_313}
        )
        earliest = min(
            (_version(v) for v in _VERSION_RE.findall(applies_to)), default=(3, 13)
        )
        if newer and earliest < (3, 13):
            names = ", ".join(
                f"U+{ord(c):04X} {unicodedata.name(c, 'unnamed')}" for c in newer
            )
            add(
                key,
                "version-tier",
                "warn",
                f"{shown} uses {names}, an identifier character only from Python 3.13; "
                "this row also ships for Python 3.10 to 3.12, so the pack needs a "
                "second spelling for that tier",
            )

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
