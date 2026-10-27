"""Markdown review files into review bundles (CORE-2508).

A reviewer copies a pack's generated ``REFERENCE.md``, fills two columns per
row, ticks the boxes and opens a pull request. These tests hold the parser to
three promises: every row verdict mints exactly the rows the lane documents;
every refusal names the row or line it refused; and the words a reviewer saw
reach the database byte for byte, joiners and combining marks included.

The fixtures are the real templates, filled in the test (``review_fixtures``).
"""

from __future__ import annotations

import sqlite3
import unicodedata
from pathlib import Path

import pytest

from legesher_i18n.intake.pipeline import BundleImporter
from legesher_i18n.intake.review_parser import (
    REVIEW_LANE,
    PullRequest,
    ReviewFileRefused,
    parse_review_file,
    read_review_file,
)
from tests.review_fixtures import (
    CODES,
    COMBINING_CODES,
    PR_AUTHOR,
    PR_URL,
    bcp47,
    concept_slug,
    current_word,
    fill,
    review_db,
    review_path,
    row_cells,
    template_text,
)

SALT = "review-parser-test-salt"
SI = template_text("si")
ZWJ = "\u200d"


def pr(author: str = PR_AUTHOR, url: str = PR_URL) -> PullRequest:
    return PullRequest(
        url=url,
        number=int(url.rsplit("/", 1)[1]),
        author=author,
        created_at="2026-10-28T09:00:00Z",
    )


def parse(text: str, code: str, conn: sqlite3.Connection, **kwargs):
    return parse_review_file(
        text,
        template_text=kwargs.pop("template", template_text(code)),
        path=kwargs.pop("path", review_path(code)),
        pull_request=kwargs.pop("pull_request", pr()),
        conn=conn,
    )


@pytest.fixture()
def db(tmp_path: Path) -> Path:
    return review_db(tmp_path / "review.db", CODES)


@pytest.fixture()
def conn(db: Path):
    connection = sqlite3.connect(db)
    yield connection
    connection.close()


def importer(db: Path) -> BundleImporter:
    return BundleImporter(db, salt=SALT, **REVIEW_LANE)


def responses(bundle: dict) -> dict[str, dict]:
    return {response["concept"]: response for response in bundle["responses"]}


def refusal(text: str, code: str = "si", **kwargs) -> str:
    with pytest.raises(ReviewFileRefused) as caught:
        read_review_file(text, kwargs.pop("template", template_text(code)))
    return "\n".join(caught.value.problems)


# --- every template reads ----------------------------------------------------------


@pytest.mark.parametrize("code", CODES)
def test_every_registry_template_reads_back_with_every_row_untouched(code: str) -> None:
    template = template_text(code)
    review = read_review_file(fill(template), template)
    assert review.meta.bcp47 == bcp47(code)
    assert [row.key for row in review.rows] == list(row_cells(template))
    assert {row.verdict for row in review.rows} == {"untouched"}


@pytest.mark.parametrize("code", COMBINING_CODES)
def test_a_filled_review_round_trips_into_a_bundle_the_importer_accepts(
    code: str, db: Path, conn: sqlite3.Connection
) -> None:
    template = template_text(code)
    keys = list(row_cells(template))
    endorsed, kept, suggested = keys[0], keys[1], keys[2]
    # A suggestion built from the pack's own letters: a real word of this
    # script, so script, joiners and combining marks are exercised for real.
    proposal = current_word(template, keys[3]) + current_word(template, keys[4])
    text = fill(
        template,
        {
            endorsed: ("", "✓"),
            kept: ("", "Keep: reads formally, but it is the established word"),
            suggested: (f"`{proposal}`", "shorter and already used in textbooks"),
        },
    )
    parsed = parse(text, code, conn)
    by_concept = responses(parsed.bundle)
    assert set(by_concept) == {concept_slug(k) for k in (endorsed, kept, suggested)}
    assert parsed.bundle["locale"] == bcp47(code)
    assert parsed.bundle["kit_version"].startswith("reference-md/")

    result = importer(db).import_bundle(parsed.bundle, parse_notes=parsed.notes)
    assert result.status == "accepted", result.report
    rows = dict(
        conn.execute(
            "SELECT o.surface_form, e.comment FROM endorsements e"
            " JOIN options o ON o.uid = e.option_uid"
        ).fetchall()
    )
    assert set(rows) == {
        unicodedata.normalize("NFC", current_word(template, endorsed)),
        unicodedata.normalize("NFC", current_word(template, kept)),
        unicodedata.normalize("NFC", proposal),
    }


# --- one test per row verdict ---------------------------------------------------------


def test_a_tick_endorses_the_current_word(conn: sqlite3.Connection) -> None:
    parsed = parse(fill(SI, {"keywords.and": ("", "✓")}), "si", conn)
    (response,) = parsed.bundle["responses"]
    assert response["concept"] == concept_slug("keywords.and")
    assert response["endorsements"] == [
        {
            "surface_form": current_word(SI, "keywords.and"),
            "annotations": [],
            "comment": None,
        }
    ]
    assert response["commentary"] == []


def test_a_tick_with_a_reason_keeps_the_reason_on_the_endorsement(
    conn: sqlite3.Connection,
) -> None:
    text = fill(SI, {"keywords.as": ("", "✓ Good \u2014 serves all three jobs")})
    (response,) = parse(text, "si", conn).bundle["responses"]
    assert response["endorsements"][0]["comment"] == "Good \u2014 serves all three jobs"


@pytest.mark.parametrize(
    "comments",
    [
        "Keep \u2014 six syllables, but it is the textbook word",
        "✓ Keep \u2014 six syllables, but it is the textbook word",
    ],
)
def test_keep_with_a_note_endorses_the_current_word_and_records_the_note(
    comments: str, conn: sqlite3.Connection
) -> None:
    (response,) = parse(
        fill(SI, {"keywords.async": ("", comments)}), "si", conn
    ).bundle["responses"]
    assert response["endorsements"] == [
        {
            "surface_form": current_word(SI, "keywords.async"),
            "annotations": [],
            "comment": "six syllables, but it is the textbook word",
        }
    ]


def test_a_suggestion_endorses_the_suggested_word_never_the_current_one(
    conn: sqlite3.Connection,
) -> None:
    text = fill(SI, {"keywords.await": ("`රැඳෙන්න`", "watch-and-wait reads as passive")})
    (response,) = parse(text, "si", conn).bundle["responses"]
    assert response["endorsements"] == [
        {
            "surface_form": "රැඳෙන්න",
            "annotations": [],
            "comment": "watch-and-wait reads as passive",
        }
    ]


def test_an_untouched_row_mints_nothing(conn: sqlite3.Connection) -> None:
    parsed = parse(fill(SI, {"keywords.and": ("", "✓")}), "si", conn)
    assert concept_slug("keywords.or") not in responses(parsed.bundle)


def test_a_comment_without_a_verdict_is_commentary_not_a_vote(
    conn: sqlite3.Connection,
) -> None:
    text = fill(SI, {"keywords.del": ("", "unsure: speakers also say මකන්න")})
    (response,) = parse(text, "si", conn).bundle["responses"]
    assert response["endorsements"] == []
    assert response["commentary"] == [
        {"topic": "general", "body": "unsure: speakers also say මකන්න"}
    ]


def test_notes_for_future_updates_become_locale_commentary(
    db: Path, conn: sqlite3.Connection
) -> None:
    notes = (
        "### Error and Exception\n\nThe pack keeps two roots: දෝෂය and ව්\u200dයතිරේකය."
    )
    parsed = parse(fill(SI, notes=notes), "si", conn)
    assert parsed.bundle["locale_commentary"] == [{"topic": "general", "body": notes}]
    assert importer(db).import_bundle(parsed.bundle).status == "accepted"
    (concept_id, body) = conn.execute(
        "SELECT concept_id, body FROM concept_commentary"
    ).fetchone()
    assert concept_id is None
    assert ZWJ in body


def test_the_template_note_paragraph_alone_is_not_commentary(
    conn: sqlite3.Connection,
) -> None:
    parsed = parse(fill(SI, {"keywords.and": ("", "✓")}), "si", conn)
    assert "locale_commentary" not in parsed.bundle


# --- Sinhala joiners and the Python tiers ------------------------------------------


def test_a_tick_on_a_tiered_row_endorses_the_newest_form_with_its_joiner(
    db: Path, conn: sqlite3.Connection
) -> None:
    cells = row_cells(SI)["keywords.True"]
    assert cells[3].startswith("3.13+ (3.10 to 3.12:"), cells
    parsed = parse(fill(SI, {"keywords.True": ("", "✓")}), "si", conn)
    (endorsement,) = parsed.bundle["responses"][0]["endorsements"]
    assert ZWJ in endorsement["surface_form"]
    assert endorsement["surface_form"] == current_word(SI, "keywords.True")
    importer(db).import_bundle(parsed.bundle)
    (surface,) = conn.execute("SELECT surface_form FROM options").fetchone()
    assert surface == current_word(SI, "keywords.True")


def test_a_suggestion_keeps_its_joiner_through_the_bundle_and_the_database(
    db: Path, conn: sqlite3.Connection
) -> None:
    text = fill(SI, {"keywords.is": ("`අනන්\u200dයවේ`", "වේ alone only means becomes")})
    parsed = parse(text, "si", conn)
    assert (
        parsed.bundle["responses"][0]["endorsements"][0]["surface_form"]
        == "අනන්\u200dයවේ"
    )
    importer(db).import_bundle(parsed.bundle)
    (surface,) = conn.execute("SELECT surface_form FROM options").fetchone()
    assert surface == "අනන්\u200dයවේ" and ZWJ in surface


# --- refusals, each naming what it refused ---------------------------------------------


def _edit_cell(text: str, key: str, index: int, value: str) -> str:
    lines = text.split("\n")
    for number, line in enumerate(lines):
        if line.startswith(f"| `{key}` |"):
            cells = line.split(" | ")
            cells[index] = value
            lines[number] = " | ".join(cells)
    return "\n".join(lines)


def test_an_edited_current_word_is_refused_by_key() -> None:
    text = _edit_cell(fill(SI), "keywords.if", 2, "`හොත්`")
    problems = refusal(text)
    assert "keywords.if" in problems and "current word" in problems


def test_an_edited_applies_to_cell_is_refused_by_key() -> None:
    text = _edit_cell(fill(SI), "keywords.True", 3, "3.10+")
    problems = refusal(text)
    assert "keywords.True" in problems and "Applies to" in problems


def test_a_current_word_changed_only_in_unicode_form_is_refused_and_says_so() -> None:
    # The first Sinhala word with a composed vowel sign (ේ is ෙ + ්, and so on).
    key, word = next(
        (key, cells[2].strip("`"))
        for key, cells in row_cells(SI).items()
        if unicodedata.normalize("NFD", cells[2]) != cells[2]
    )
    decomposed = unicodedata.normalize("NFD", word)
    text = _edit_cell(fill(SI), key, 2, f"`{decomposed}`")
    problems = refusal(text)
    assert f"`{key}`" in problems and "Unicode normalization" in problems


def test_a_pin_naming_an_unknown_pack_version_is_refused_by_name() -> None:
    text = fill(SI).replace("pack_version=0.0.3", "pack_version=9.9.9", 1)
    problems = refusal(text)
    assert "9.9.9" in problems and "0.0.3" in problems


def test_a_duplicated_hidden_line_is_refused_with_its_line_number() -> None:
    text = fill(SI)
    first = text.split("\n", 1)[0]
    lines = text.split("\n")
    lines.insert(40, first)
    problems = refusal("\n".join(lines))
    assert "line 41" in problems


def test_a_repeated_key_is_refused_by_key() -> None:
    text = fill(SI)
    row = next(
        line for line in text.split("\n") if line.startswith("| `keywords.or` |")
    )
    problems = refusal(text.replace(row, f"{row}\n{row}", 1))
    assert "keywords.or" in problems and "more than once" in problems


def test_a_missing_column_is_refused_by_key() -> None:
    text = fill(SI)
    row = next(
        line for line in text.split("\n") if line.startswith("| `keywords.or` |")
    )
    problems = refusal(text.replace(row, row[: -len(" |")], 1))
    assert "keywords.or" in problems and "5 columns" in problems


def test_an_extra_column_is_refused_by_key() -> None:
    text = fill(SI, {"keywords.or": ("", "✓ | and also this")})
    problems = refusal(text)
    assert "keywords.or" in problems and "7 columns" in problems


def test_a_key_the_template_does_not_have_is_refused_by_key() -> None:
    text = fill(SI)
    row = next(
        line for line in text.split("\n") if line.startswith("| `keywords.or` |")
    )
    problems = refusal(text.replace(row, row.replace("keywords.or", "keywords.xor"), 1))
    assert "keywords.xor" in problems


@pytest.mark.parametrize(
    ("box", "name"),
    [
        (0, "own work"),
        (1, "Developer Certificate of Origin"),
        (2, "Apache-2.0"),
        (3, "Code of Conduct"),
        (4, "CONTRIBUTOR_PRIVACY.md"),
    ],
)
def test_an_unticked_required_box_is_refused_by_name(box: int, name: str) -> None:
    text = fill(SI, ticked=[index for index in range(6) if index != box])
    assert name in refusal(text)


def test_the_optional_research_box_may_stay_unticked(conn: sqlite3.Connection) -> None:
    parsed = parse(fill(SI, ticked=range(5)), "si", conn)
    assert parsed.bundle["attestations"]["research_use"] is False


def test_an_edited_consent_wording_is_refused() -> None:
    text = fill(SI).replace("I agree to the Code of Conduct.", "I agree.", 1)
    assert "Before you submit" in refusal(text)


def test_a_file_name_username_that_is_not_the_pr_author_is_refused(
    conn: sqlite3.Connection,
) -> None:
    # About you names the PR author; only the file name names someone else.
    with pytest.raises(ReviewFileRefused) as caught:
        parse(fill(SI), "si", conn, path=review_path("si", "someone-else"))
    problems = caught.value.problems
    assert len(problems) == 1
    assert (
        "the file name names `someone-else`" in problems[0] and PR_AUTHOR in problems[0]
    )


def test_an_about_you_username_that_is_not_the_pr_author_is_refused(
    conn: sqlite3.Connection,
) -> None:
    with pytest.raises(ReviewFileRefused) as caught:
        parse(fill(SI, username="someone-else"), "si", conn)
    assert "GitHub username" in "\n".join(caught.value.problems)


def test_usernames_match_case_insensitively_and_identity_comes_from_the_pr(
    conn: sqlite3.Connection,
) -> None:
    text = fill(SI, {"keywords.and": ("", "✓")}, username=PR_AUTHOR.upper())
    parsed = parse(text, "si", conn, path=review_path("si", PR_AUTHOR.upper()))
    assert parsed.bundle["contributor"]["source_key"] == PR_AUTHOR


@pytest.mark.parametrize(
    "path",
    [
        "reviews/hi/hi-native-reviewer.md",
        "reviews/si/si-native-reviewer-0.0.2.md",
        "reviews/incoming/si/si-native-reviewer.md",
        "si-native-reviewer.md",
    ],
)
def test_a_file_outside_its_pinned_place_is_refused(
    path: str, conn: sqlite3.Connection
) -> None:
    with pytest.raises(ReviewFileRefused) as caught:
        parse(fill(SI), "si", conn, path=path)
    assert path in "\n".join(caught.value.problems)


def test_a_review_after_a_version_bump_carries_the_pinned_version_in_its_name(
    conn: sqlite3.Connection,
) -> None:
    parsed = parse(
        fill(SI, {"keywords.and": ("", "✓")}),
        "si",
        conn,
        path="reviews/si/si-native-reviewer-0.0.3.md",
    )
    assert parsed.bundle["source"]["path"] == "reviews/si/si-native-reviewer-0.0.3.md"


def test_a_complete_file_reports_no_deleted_rows(conn: sqlite3.Connection) -> None:
    parsed = parse(fill(SI, {"keywords.and": ("", "✓")}), "si", conn)
    assert not any("deleted" in note for note in parsed.notes), parsed.notes


def test_a_deleted_row_is_no_opinion_and_counted_in_a_note(
    conn: sqlite3.Connection,
) -> None:
    text = fill(SI, {"keywords.and": ("", "✓")})
    row = next(
        line for line in text.split("\n") if line.startswith("| `keywords.or` |")
    )
    parsed = parse(text.replace(f"{row}\n", "", 1), "si", conn)
    assert "1 template row(s) deleted from the file: read as no opinion" in parsed.notes


def test_every_problem_is_reported_at_once() -> None:
    text = _edit_cell(fill(SI, ticked=range(4)), "keywords.if", 2, "`x`")
    problems = refusal(text)
    assert "keywords.if" in problems and "CONTRIBUTOR_PRIVACY.md" in problems


# --- About you and credit ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("relationship", "rung", "fluent"),
    [
        ("native speaker", "native_claimed", True),
        ("fluent", "contributor", True),
        ("professional", "contributor", False),
        ("learning", "contributor", False),
    ],
)
def test_relationship_maps_onto_the_rung_and_the_fluency_attestation(
    relationship: str, rung: str, fluent: bool, conn: sqlite3.Connection
) -> None:
    bundle = parse(fill(SI, relationship=relationship), "si", conn).bundle
    assert bundle["contributor"]["claimed_rung"] == rung
    assert bundle["attestations"]["native_or_fluent"] is fluent


def test_an_unanswered_relationship_is_the_safe_default_and_a_note(
    conn: sqlite3.Connection,
) -> None:
    parsed = parse(fill(SI, relationship=None), "si", conn)
    assert parsed.bundle["contributor"]["claimed_rung"] == "contributor"
    assert any("relationship" in note for note in parsed.notes)


@pytest.mark.parametrize(
    ("credit", "expected"),
    [
        ("anonymous", {"credit_preference": "anonymous"}),
        ("my GitHub handle", {"credit_preference": "handle"}),
        ("this name: `සුපුන්`", {"credit_preference": "name", "credit_text": "සුපුන්"}),
    ],
)
def test_the_credit_line_maps_onto_consent(
    credit: str, expected: dict, conn: sqlite3.Connection
) -> None:
    consent = parse(fill(SI, credit=credit), "si", conn).bundle["contributor"][
        "consent"
    ]
    assert consent == {"consent_version": "1.0", **expected}


def test_an_unanswered_credit_line_falls_back_to_anonymous_with_a_note(
    conn: sqlite3.Connection,
) -> None:
    parsed = parse(fill(SI, credit=None), "si", conn)
    assert parsed.bundle["contributor"]["consent"]["credit_preference"] == "anonymous"
    assert any("credit" in note for note in parsed.notes)


# --- re-import and the lane record ----------------------------------------------------


def test_reimporting_the_same_file_from_the_same_pr_is_a_zero_row_noop(
    db: Path, conn: sqlite3.Connection
) -> None:
    text = fill(
        SI, {"keywords.and": ("", "✓"), "keywords.if": ("`හොත්`", "නම් also means names")}
    )
    first = importer(db).import_bundle(parse(text, "si", conn).bundle)
    assert first.status == "accepted"
    tables = (
        "review_sessions",
        "options",
        "endorsements",
        "session_options",
        "concept_commentary",
    )
    before = {
        t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables
    }
    again = importer(db).import_bundle(parse(text, "si", conn).bundle)
    assert (again.status, again.session_uid) == ("duplicate", first.session_uid)
    after = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}
    assert after == before


def test_the_source_is_the_pull_request(conn: sqlite3.Connection) -> None:
    bundle = parse(fill(SI), "si", conn).bundle
    assert bundle["source"] == {
        "kind": "github_pull_request",
        "url": PR_URL,
        "id": 400,
        "created_at": "2026-10-28T09:00:00Z",
        "path": review_path("si"),
    }


@pytest.mark.parametrize("field", ["locale_commentary", "source.kind", "source.path"])
def test_a_1_0_bundle_cannot_carry_the_1_1_fields(
    field: str, db: Path, conn: sqlite3.Connection
) -> None:
    bundle = parse(
        fill(SI, {"keywords.and": ("", "✓")}, notes="word order note"), "si", conn
    ).bundle
    bundle["bundle_version"] = "1.0"
    if field != "locale_commentary":
        bundle.pop("locale_commentary")
    if field == "source.path":
        bundle["source"]["kind"] = "github_issue"
    if field == "source.kind":
        bundle["source"].pop("path")
    result = importer(db).import_bundle(bundle)
    assert result.status == "returned", result.report
    schema = next(s for s in result.report["stages"] if s["stage"] == "schema")
    assert schema["status"] == "fail"


def test_the_same_file_from_another_pr_is_another_session(
    conn: sqlite3.Connection,
) -> None:
    from legesher_i18n.db.schema_v2 import session_uid
    from legesher_i18n.intake.canonical import canonicalize

    text = fill(SI, {"keywords.and": ("", "✓")})
    one = parse(text, "si", conn).bundle
    other = parse(
        text,
        "si",
        conn,
        pull_request=pr(url="https://github.com/legesher/language-packs/pull/401"),
    ).bundle
    assert session_uid(canonicalize(one)) != session_uid(canonicalize(other))


def test_a_markdown_review_is_distinguishable_from_a_blind_app_session(
    db: Path, conn: sqlite3.Connection
) -> None:
    """The lane record: ``session_options.elicited``.

    A review file shows the current word before the reviewer answers, so every
    row it mints is ``after_reveal``; the app's blind-first rows are
    ``blind``. The promotion gate reads both views below, and from either one
    a session joins to the rows that say which kind of signal it carries.
    """
    review = parse(
        fill(SI, {"keywords.if": ("`හොත්`", "නම් also means names")}), "si", conn
    ).bundle
    assert importer(db).import_bundle(review).status == "accepted"
    app = {
        "bundle_version": "1.0",
        "kit_version": "review-app/0.1",
        "locale": "si",
        "track": "reserved_words",
        "programming_language": None,
        "contributor": {"source_key": "app-reviewer", "claimed_rung": "native_claimed"},
        "attestations": {
            "original_work": True,
            "license_grant": "Apache-2.0",
            "coc_agreed": True,
            "dco": True,
            "native_or_fluent": True,
        },
        "responses": [
            {
                "concept": concept_slug("keywords.if"),
                "blind": {"surface_form": "නම්"},
                "endorsements": [{"surface_form": "හොත්"}],
                "ranking": ["නම්", "හොත්"],
            }
        ],
    }
    assert BundleImporter(db, salt=SALT).import_bundle(app).status == "accepted"

    lanes = dict(
        conn.execute(
            "SELECT s.method, group_concat(DISTINCT so.elicited) FROM review_sessions s"
            " JOIN session_options so ON so.session_uid = s.uid GROUP BY s.method"
        ).fetchall()
    )
    assert lanes == {
        "github": "after_reveal",
        "portal": "blind,after_reveal",
    } or lanes == {"github": "after_reveal", "portal": "after_reveal,blind"}
    (total,) = conn.execute(
        "SELECT total_reviewers FROM pack_promotion_status WHERE locale = 'si'"
    ).fetchone()
    assert total == 2
    blind_sessions = {
        uid
        for (uid,) in conn.execute(
            "SELECT DISTINCT r.session_uid FROM latest_rankings r"
            " JOIN session_options so ON so.session_uid = r.session_uid"
            " WHERE so.elicited = 'blind'"
        )
    }
    critique_sessions = {
        uid
        for (uid,) in conn.execute(
            "SELECT s.uid FROM review_sessions s WHERE NOT EXISTS ("
            " SELECT 1 FROM session_options so WHERE so.session_uid = s.uid"
            " AND so.elicited = 'blind')"
        )
    }
    assert len(blind_sessions) == 1 and len(critique_sessions) == 1
    assert not blind_sessions & critique_sessions
    (kit,) = conn.execute(
        "SELECT kit_version FROM review_sessions WHERE method = 'github'"
    ).fetchone()
    assert kit == review["kit_version"]


# --- review findings (fix pass) ------------------------------------------------------


@pytest.mark.parametrize(
    "relationship",
    [
        "non-native speaker",
        "native speaker · fluent",
        "not a native speaker",
        "fluent-ish",
    ],
)
def test_a_relationship_that_only_contains_an_option_is_not_that_option(
    relationship: str, conn: sqlite3.Connection
) -> None:
    bundle = parse(fill(SI, relationship=relationship), "si", conn).bundle
    assert bundle["contributor"]["claimed_rung"] == "contributor"
    assert bundle["attestations"]["native_or_fluent"] is False


@pytest.mark.parametrize(
    "comments",
    [
        "Keep in mind this reads as when; replace it",
        "keeping it is wrong",
        "Keeps the meaning",
    ],
)
def test_keep_starting_a_sentence_is_a_comment_not_an_endorsement(
    comments: str, conn: sqlite3.Connection
) -> None:
    (response,) = parse(fill(SI, {"keywords.if": ("", comments)}), "si", conn).bundle[
        "responses"
    ]
    assert response["endorsements"] == []
    assert response["commentary"] == [{"topic": "general", "body": comments}]


def test_an_emoji_tick_drops_its_presentation_selector(
    conn: sqlite3.Connection,
) -> None:
    text = fill(SI, {"keywords.and": ("", "✔\ufe0f reads well")})
    (response,) = parse(text, "si", conn).bundle["responses"]
    assert response["endorsements"][0]["comment"] == "reads well"


def test_a_template_heading_typed_twice_is_a_parse_note(
    conn: sqlite3.Connection,
) -> None:
    notes = "Compounds join with ZWJ.\n\n## How to submit this review\n\nmore notes"
    parsed = parse(fill(SI, notes=notes), "si", conn)
    assert any(
        "## How to submit this review" in note and "2 times" in note
        for note in parsed.notes
    )


@pytest.mark.parametrize(
    "value",
    [
        "plain",
        "a`b",
        "``x``",
        "`lead",
        "trail`",
        "![t](https://example.invalid/x.png) @team",
    ],
)
def test_code_span_keeps_any_value_inert(value: str) -> None:
    from legesher_i18n.intake.review_parser import code_span

    span = code_span(value)
    fence = len(span) - len(span.lstrip("`"))
    inner = span[fence:-fence]
    assert span.startswith("`" * fence) and span.endswith("`" * fence)
    assert "`" * fence not in inner
    assert inner.strip() == value


def test_a_repeated_locale_commentary_entry_is_refused_by_the_schema(
    db: Path, conn: sqlite3.Connection
) -> None:
    bundle = parse(fill(SI, notes="word order note"), "si", conn).bundle
    bundle["locale_commentary"] = bundle["locale_commentary"] * 2
    result = importer(db).import_bundle(bundle)
    assert result.status == "returned", result.report
