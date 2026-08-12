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

One format today: the ``language_pack_review`` form, tagged in
:data:`STAGE0_KIT_VERSION`. A second form layout slots in beside it by adding
its field readers and bumping that tag; nothing in the pipeline changes,
because every lane produces the same bundle shape.

Two lane-specific notes, both deliberate:

* **Attestations.** The old form asserts nativeness and CoC agreement only.
  ``original_work`` is implicit in offering one's own words, and the license
  grant follows GitHub's inbound=outbound terms for contributions to a
  repository; a DCO sign-off is NOT collected on this lane, so ``dco`` is
  ``false`` in the bundle and the Stage-0 importer runs with
  ``required_attestations=('original_work', 'coc_agreed')``. The Stage-1
  bundle app collects the full set.
* **Consent.** The form carries the required CONTRIBUTOR_PRIVACY checkbox and
  a credit-preference dropdown (CORE-397). Both are read here, with the notice
  version taken from the checkbox's own label so a version bump re-consents
  naturally. An unticked box means no consent block, and the importer then
  mints NO identity (decision 2026-08-11) while still recording the words.
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
#: The consent checkbox names the notice version it binds ("… (v1.0) and
#: agree"), so the version is READ FROM THE FORM rather than hardcoded here: a
#: notice bump re-consents naturally on the next contribution (CORE-397).
_CONSENT_RE = re.compile(
    r"^[-*]\s*\[(?P<checked>[xX ])\]\s*I have read .*?\(v(?P<version>[0-9][0-9.]*)\)",
    re.MULTILINE,
)

#: How the `language_claim` dropdown maps to a rung and to the fluency
#: attestation. Only an actual native claim is `native_claimed`: the rung is a
#: PUBLISHED column that weights endorsements (2.0 vs 1.0), so "fluent" must not
#: inherit a native speaker's weight — which the old single "native or fluent"
#: checkbox silently allowed.
_LANGUAGE_CLAIM: dict[str, tuple[str, bool]] = {
    "i am a native speaker": ("native_claimed", True),
    "i am fluent, not native": ("contributor", True),
    "i work with this language professionally": ("contributor", False),
    "i am learning it": ("contributor", False),
}

#: The `credit` dropdown. "A display name I will give you" has NO accompanying
#: text field on the form, and the importer refuses `credit_preference='name'`
#: without `credit_text` — so it falls back to the anonymous default and leaves
#: the maintainer a note. The notice already tells contributors credit can be
#: changed by asking, so nothing is lost that a reply cannot recover.
_CREDIT_CHOICE: dict[str, str] = {
    "anonymous": "anonymous",
    "my github handle": "handle",
    "a display name": "anonymous",
}

_EMOJIS = ("✅", "❓", "🤔")


@dataclass
class ParsedIssue:
    """The bundle plus everything the parser could not carry into it."""

    bundle: dict
    notes: list[str] = field(default_factory=list)


#: The form's fields, in the order GitHub renders them. Parsing is matched
#: against this sequence rather than against whatever `###` lines appear,
#: because a contributor can TYPE `###` into any textarea: the rendered body
#: gives a forged heading exactly the same shape as a real one. Reading the
#: last (or the first) occurrence of a label lets a submitter who chose
#: "I am learning it" award themselves `native_claimed` — double endorsement
#: weight on a published column — from the Additional-context box.
_FIELD_ORDER: tuple[str, ...] = (
    "Language being reviewed",
    "Python version reviewed",
    "Your relationship to this language",
    "Anything you want us to know about your background",
    "Review notes",
    "Additional context",
    "How would you like to be credited?",
    "Consent",
)

#: Fields the form marks required. Their absence means the body is not this
#: form (or a heading was injected out of order and swallowed them), and the
#: parse refuses rather than importing a submission it half-understood.
_REQUIRED_FIELDS: frozenset[str] = frozenset(
    {
        "Language being reviewed",
        "Your relationship to this language",
        "Review notes",
        "How would you like to be credited?",
        "Consent",
    }
)


def _sections(body: str) -> dict[str, str]:
    """Split a rendered issue-form body into ``{label: content}``.

    Headings are matched against :data:`_FIELD_ORDER` **in sequence**: a known
    label counts as a section boundary only when it is the next one still
    expected. A duplicate of a label already consumed is content, not a
    heading — which is what makes a forged heading inert.

    Raises:
        ValueError: if a required field never appears in order, which is what a
            heading injected ahead of its turn produces (it consumes the
            sections that should have followed).
    """
    # A real form emits each heading EXACTLY once, so a repeat is tampering —
    # and in-order matching alone cannot catch a forgery that jumps exactly one
    # field ahead (text typed into "Additional context" impersonating the
    # "credited?" dropdown that legitimately follows it). Refuse, rather than
    # guess which occurrence was the form's.
    seen: list[str] = [
        m.group("label").strip()
        for m in _SECTION_RE.finditer(body)
        if m.group("label").strip() in _FIELD_ORDER
    ]
    duplicated = sorted({label for label in seen if seen.count(label) > 1})
    if duplicated:
        raise ValueError(
            f"form heading(s) {duplicated} appear more than once in the issue "
            "body. GitHub renders each field once, so a repeat means the text "
            "was typed into a free-text box — possibly to override a dropdown "
            "the submitter did not choose. Import refused; read the issue."
        )

    out: dict[str, str] = {}
    boundaries: list[tuple[str, int, int]] = []
    expected = 0
    for match in _SECTION_RE.finditer(body):
        label = match.group("label").strip()
        try:
            position = _FIELD_ORDER.index(label, expected)
        except ValueError:
            continue  # unknown, or already consumed: it is body text
        boundaries.append((label, match.start(), match.end()))
        expected = position + 1

    for index, (label, _, content_start) in enumerate(boundaries):
        end = boundaries[index + 1][1] if index + 1 < len(boundaries) else len(body)
        out[label] = body[content_start:end].strip()

    missing = _REQUIRED_FIELDS - set(out)
    if missing:
        raise ValueError(
            f"the issue body is missing required form section(s) "
            f"{sorted(missing)} — either it is not a language_pack_review "
            "submission, or a heading was typed out of order and swallowed "
            "them. Import refused rather than reading a partial form."
        )
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

    claimed_rung, native_or_fluent = _claim_from(sections, notes)
    consent = _consent_from(sections, notes)

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
            "claimed_rung": claimed_rung,
            "contact_captured": False,
            **({"consent": consent} if consent else {}),
        },
        "attestations": {
            "native_or_fluent": native_or_fluent,
            # Implicit in offering one's own words on a public issue.
            "original_work": True,
            # GitHub inbound=outbound: issue contributions ride the repo license.
            "license_grant": "Apache-2.0",
            "coc_agreed": _coc_agreed(sections.get("Consent", "")),
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


def _claim_from(sections: dict[str, str], notes: list[str]) -> tuple[str, bool]:
    """Map the `language_claim` dropdown to (rung, native_or_fluent)."""
    answer = sections.get("Your relationship to this language", "").strip().casefold()
    for prefix, (rung, fluent) in _LANGUAGE_CLAIM.items():
        if answer.startswith(prefix):
            return rung, fluent
    if answer and answer != "_no response_":
        notes.append(
            f"unrecognized language-claim answer {answer!r}: recorded at the "
            "'contributor' rung, which is the safe default"
        )
    return "contributor", False


def _consent_from(sections: dict[str, str], notes: list[str]) -> dict[str, str] | None:
    """The consent block, or None when the privacy checkbox is not ticked.

    A submission without consent still ingests as evidence; it simply mints no
    identity (decision 2026-08-11). Consent is never inferred.
    """
    # Scoped to the Consent section: a whole-body scan takes the FIRST match,
    # and every free-text field renders before this one, so a decoy line could
    # both forge the notice version and (unticked) suppress identity minting.
    match = _CONSENT_RE.search(sections.get("Consent", ""))
    if not match or match.group("checked") not in "xX":
        return None
    choice = sections.get("How would you like to be credited?", "").strip().casefold()
    preference = "anonymous"
    for prefix, value in _CREDIT_CHOICE.items():
        if choice.startswith(prefix):
            preference = value
            break
    if choice.startswith("a display name"):
        notes.append(
            "contributor asked to be credited by display name, but the form "
            "collects no name field: recorded as 'anonymous' for now. Ask them "
            "for the name in the reply, then set it as a maintainer action."
        )
    return {"consent_version": match.group("version"), "credit_preference": preference}
