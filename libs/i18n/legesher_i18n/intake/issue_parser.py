"""Stage-0 parser: GitHub issue-form emoji notation → canonical review bundle.

The existing ``language_pack_review.yml`` form stays open (zero-friction,
good-first-issue); this parser turns a filled-in issue into the SAME wire
shape the Stage-1 review app emits, so one pipeline serves every lane:

* ``✅`` — endorsement of the reviewed translation (``method='github'``)
* ``❓`` — a better word exists: endorsement of the ALTERNATIVE named in the
  comment (a new option if the corpus has not met it), never of the reviewed
  word
* ``🤔`` — commentary on the concept; no endorsement either way

Sessions mint ``method='github'``, ``elicited='quick'`` (the importer's lane
parameters). The issue's URL/number/author ride the bundle's ``source`` block,
which is part of the canonical bytes — the same issue always re-mints the
same session uid, so re-import is a no-op.

Format registry: ``FORMATS`` maps a format tag to its section parser. The
CORE-397 forms' new field layout lands as a second entry; nothing in the
pipeline changes.

Two lane-specific notes, both deliberate:

* **Attestations.** The old form asserts nativeness and CoC agreement only.
  ``original_work`` is implicit in offering one's own words, and the license
  grant follows GitHub's inbound=outbound terms for contributions to a
  repository; a DCO sign-off is NOT collected on this lane, so ``dco`` is
  ``false`` in the bundle and the Stage-0 importer runs with
  ``required_attestations=('original_work', 'coc_agreed')``. The Stage-1
  bundle app collects the full set.
* **Consent.** The old form has no CONTRIBUTOR_PRIVACY checkbox, so the
  bundle carries no consent block and the importer mints NO identity
  (decision 2026-08-11) — the reply invites the contributor to consent.
  The CORE-397 replacement forms add the required checkbox.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field

__all__ = ["ParsedIssue", "parse_issue", "STAGE0_KIT_VERSION"]

STAGE0_KIT_VERSION = "issue-form/language_pack_review@v1"

_SECTION_RE = re.compile(r"^### +(?P<label>.+?) *$", re.MULTILINE)
_LOCALE_RE = re.compile(r"\(([A-Za-z]{2,3}(?:-[A-Za-z]{2,4})?)\)\s*$")
_NOTE_LINE_RE = re.compile(
    r"^[-*]\s*`(?P<term>[^`]+)`\s*(?:→|->|⇒)\s*`(?P<translation>[^`]+)`\s*(?P<rest>.*)$"
)
_BACKTICK_RE = re.compile(r"`([^`]+)`")
_NATIVE_CLAIM_RE = re.compile(
    r"^[-*]\s*\[(?P<checked>[xX ])\]\s*I am a native or fluent speaker", re.MULTILINE
)

_EMOJIS = ("✅", "❓", "🤔")


@dataclass
class ParsedIssue:
    """The bundle plus everything the parser could not carry into it."""

    bundle: dict
    notes: list[str] = field(default_factory=list)


def _sections(body: str) -> dict[str, str]:
    """Split a rendered issue-form body into ``{label: content}``."""
    out: dict[str, str] = {}
    matches = list(_SECTION_RE.finditer(body))
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        out[match.group("label").strip()] = body[start:end].strip()
    return out


def _concept_slug(conn: sqlite3.Connection, term: str, notes: list[str]) -> str | None:
    rows = conn.execute(
        "SELECT DISTINCT c.slug FROM terms t JOIN concepts c ON c.id = t.concept_id"
        " WHERE t.name = ? AND t.programming_language = 'python' ORDER BY c.slug",
        (term,),
    ).fetchall()
    if not rows:
        notes.append(f"unknown term `{term}`: no concept maps to it; line skipped")
        return None
    if len(rows) > 1:
        notes.append(
            f"term `{term}` maps to {len(rows)} concepts "
            f"({', '.join(slug for (slug,) in rows)}); using {rows[0][0]!r} — "
            "verify during the import ritual"
        )
    return rows[0][0]


def parse_issue(payload: dict, conn: sqlite3.Connection) -> ParsedIssue:
    """Parse one ``gh issue view --json`` payload into a review bundle.

    Args:
        payload: Keys ``number``, ``url``, ``author.login``, ``body``,
            ``createdAt`` (the shape ``gh issue view --json`` returns).
        conn: An open connection to the target v2 database, used only to map
            English term names to concept slugs.

    Returns:
        The bundle plus parse notes (unknown terms, unparsable lines,
        ambiguities) for the import ledger.

    Raises:
        ValueError: if the form names no usable locale code — nothing
            downstream can be keyed without one.
    """
    notes: list[str] = []
    sections = _sections(payload.get("body") or "")

    language_field = sections.get("Language being reviewed", "")
    locale_match = _LOCALE_RE.search(language_field)
    if not locale_match:
        raise ValueError(
            f"no locale code found in {language_field!r}: the form's language "
            "field must name a code in parentheses, e.g. 'Urdu (ur)'"
        )
    locale = locale_match.group(1)

    native_match = _NATIVE_CLAIM_RE.search(payload.get("body") or "")
    native_claimed = bool(native_match and native_match.group("checked") in "xX")

    responses: dict[str, dict] = {}

    def response_for(slug: str) -> dict:
        return responses.setdefault(
            slug,
            {
                "concept": slug,
                "blind": None,
                "endorsements": [],
                "ranking": [],
                "flags": [],
                "expansion": None,
                "commentary": [],
            },
        )

    for raw_line in sections.get("Review notes", "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("**", "#")):
            continue
        match = _NOTE_LINE_RE.match(line)
        if not match:
            if line.startswith(("-", "*")):
                notes.append(f"unparsable review line kept for the ritual: {line!r}")
            continue
        term = match.group("term").strip()
        translation = match.group("translation").strip()
        rest = match.group("rest").strip()
        emoji = next((e for e in _EMOJIS if e in rest), None)
        if emoji is None:
            notes.append(f"no ✅/❓/🤔 marker on line, kept for the ritual: {line!r}")
            continue
        comment = rest.replace(emoji, "", 1).strip() or None

        slug = _concept_slug(conn, term, notes)
        if slug is None:
            continue
        response = response_for(slug)

        if emoji == "✅":
            response["endorsements"].append(
                {"surface_form": translation, "annotations": [], "comment": comment}
            )
        elif emoji == "❓":
            alternative = None
            if comment:
                alt_match = _BACKTICK_RE.search(comment)
                if alt_match:
                    alternative = alt_match.group(1).strip()
            if alternative:
                response["endorsements"].append(
                    {
                        "surface_form": alternative,
                        "annotations": [],
                        "comment": comment,
                    }
                )
            else:
                # A doubt with no named alternative is commentary, not a vote.
                response["commentary"].append(
                    {
                        "topic": "general",
                        "body": f"`{term}` → `{translation}`: {comment or 'reviewer unsure'}",
                    }
                )
        else:  # 🤔
            response["commentary"].append(
                {
                    "topic": "general",
                    "body": f"`{term}` → `{translation}`: {comment or 'reviewer unsure'}",
                }
            )

    extra = sections.get("Additional context", "")
    if extra and extra != "_No response_":
        notes.append(
            "additional-context text stays on the issue (linked via source.url); "
            "not ingested as commentary — it is not keyed to a concept"
        )

    bundle = {
        "bundle_version": "1.0",
        "kit_version": STAGE0_KIT_VERSION,
        "locale": locale,
        # Reviewed words render CONCEPTS: options are concept-wide, exactly as
        # the pack migration mints them, so the same word is ONE option.
        "programming_language": None,
        "track": "reserved_words",
        "contributor": {
            "source_key": payload["author"]["login"],
            "claimed_rung": "native_claimed" if native_claimed else "contributor",
            "contact_captured": False,
        },
        "attestations": {
            "native_or_fluent": native_claimed,
            # Implicit in offering one's own words on a public issue.
            "original_work": True,
            # GitHub inbound=outbound: issue contributions ride the repo license.
            "license_grant": "Apache-2.0",
            "coc_agreed": _coc_agreed(payload.get("body") or ""),
            # NOT collected on this lane; the Stage-0 importer does not require it.
            "dco": False,
        },
        "responses": [responses[slug] for slug in sorted(responses)],
        "source": {
            "kind": "github_issue",
            "url": payload["url"],
            "id": payload["number"],
            "created_at": payload.get("createdAt"),
        },
    }
    return ParsedIssue(bundle=bundle, notes=notes)


_COC_RE = re.compile(
    r"^[-*]\s*\[(?P<checked>[xX ])\]\s*I agree to follow", re.MULTILINE
)


def _coc_agreed(body: str) -> bool:
    match = _COC_RE.search(body)
    return bool(match and match.group("checked") in "xX")
