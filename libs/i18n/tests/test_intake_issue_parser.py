"""Stage-0 issue-form parser (CORE-1688 scope item 2).

Parses the existing ``language_pack_review.yml`` emoji notation into a
canonical review bundle — the SAME wire shape the Stage-1 review app emits —
so one pipeline serves every lane and the acceptance line "Stage-0 issue
import produces the same row shapes as a bundle" holds by construction.

The parser is format-registry-shaped: ``language_pack_review@v1`` is the
first format; the CORE-397 forms' new field layout slots in as a second
format without touching the pipeline.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from legesher_i18n.db.schema_v2 import apply_schema_v2, contributor_id
from legesher_i18n.intake.issue_parser import parse_issue
from legesher_i18n.intake.pipeline import BundleImporter

SALT = "intake-test-salt"
AUTHOR = "drive-by-reviewer"
AUTHOR_ID = contributor_id(AUTHOR, salt=SALT)

ISSUE_BODY = """\
### Language being reviewed

Urdu (ur)

### Python version reviewed

3.10 (base — contains all translations)

### Your relationship to this language

I am a native speaker

### Anything you want us to know about your background

Native speaker of Urdu, CS student.

### Review notes

**Keywords:**

- `elif` → `ورنہ_اگر` ✅ natural and widely understood
- `break` → `توڑ` ❓ consider `توڑو` — imperative reads better in a program
- `pass` → `گزر` 🤔 not sure a good translation exists for this concept

### Additional context

_No response_

### How would you like to be credited?

My GitHub handle

### Consent

- [x] I have read [Your contributions and your data](https://github.com/legesher/legesher/blob/main/CONTRIBUTOR_PRIVACY.md) (v1.0) and agree
- [x] I agree to follow this project's [Code of Conduct](https://github.com/legesher/legesher/blob/main/CODE_OF_CONDUCT.md)
"""


def issue_payload(body: str = ISSUE_BODY) -> dict:
    return {
        "number": 123,
        "url": "https://github.com/legesher/legesher-next/issues/123",
        "author": {"login": AUTHOR},
        "title": "[Review]: Urdu (Python)",
        "body": body,
        "createdAt": "2026-08-11T08:00:00Z",
    }


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "stage0.db"
    conn = sqlite3.connect(path)
    apply_schema_v2(conn)
    conn.executescript(
        """
        INSERT INTO programming_languages(code, name, status)
            VALUES ('python','Python','shipping');
        INSERT INTO locales(tag, language_subtag, name, native_name, direction, in_registry)
            VALUES ('ur','ur','Urdu','اردو','rtl',1);
        INSERT INTO concepts(slug, definition_en, category) VALUES
            ('elif-compound','otherwise-if in a conditional chain','control_flow'),
            ('break-loop','exit the nearest loop','control_flow'),
            ('pass-noop','do nothing','control_flow');
        INSERT INTO terms(concept_id, programming_language, name, category) VALUES
            (1,'python','elif','keyword'),
            (2,'python','break','keyword'),
            (3,'python','pass','keyword');
        """
    )
    conn.commit()
    conn.close()
    return path


def stage0_importer(db_path: Path) -> BundleImporter:
    return BundleImporter(
        db_path,
        salt=SALT,
        method="github",
        elicited_default="quick",
        required_attestations=("original_work", "coc_agreed"),
    )


def test_emoji_notation_maps_to_the_wire_contract(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    parsed = parse_issue(issue_payload(), conn)
    conn.close()
    bundle = parsed.bundle

    assert bundle["locale"] == "ur"
    assert bundle["track"] == "reserved_words"
    assert bundle["programming_language"] is None  # words render CONCEPTS
    assert bundle["contributor"]["source_key"] == AUTHOR
    assert bundle["contributor"]["claimed_rung"] == "native_claimed"
    assert bundle["contributor"]["consent"]["consent_version"] == "1.0"
    assert bundle["source"] == {
        "kind": "github_issue",
        "url": "https://github.com/legesher/legesher-next/issues/123",
        "id": 123,
        "created_at": "2026-08-11T08:00:00Z",
    }

    by_concept = {r["concept"]: r for r in bundle["responses"]}
    # ✅ endorses the reviewed translation.
    assert by_concept["elif-compound"]["endorsements"][0]["surface_form"] == "ورنہ_اگر"
    # ❓ endorses the ALTERNATIVE, not the reviewed word.
    surfaces = [e["surface_form"] for e in by_concept["break-loop"]["endorsements"]]
    assert surfaces == ["توڑو"]
    # 🤔 is commentary, no endorsement.
    assert by_concept["pass-noop"]["endorsements"] == []
    assert "گزر" in by_concept["pass-noop"]["commentary"][0]["body"]


def test_issue_import_produces_the_same_row_shapes_as_a_bundle(
    db_path: Path,
) -> None:
    conn = sqlite3.connect(db_path)
    parsed = parse_issue(issue_payload(), conn)
    conn.close()

    result = stage0_importer(db_path).import_bundle(parsed.bundle)
    assert result.status == "accepted"

    conn = sqlite3.connect(db_path)
    method, elicited = conn.execute(
        "SELECT s.method, so.elicited FROM review_sessions s"
        " JOIN session_options so ON so.session_uid = s.uid LIMIT 1"
    ).fetchone()
    assert (method, elicited) == ("github", "quick")
    # Same shapes as a bundle: options + endorsements + commentary + junctions.
    endorsed = conn.execute(
        "SELECT o.surface_form FROM endorsements e JOIN options o"
        " ON o.uid = e.option_uid ORDER BY o.surface_form"
    ).fetchall()
    assert [s for (s,) in endorsed] == sorted(["ورنہ_اگر", "توڑو"])
    # Quarantine-by-default applies to the issue lane too (CORE-1828).
    quarantined = conn.execute(
        "SELECT COUNT(*) FROM option_screening_status WHERE verdict='quarantined'"
    ).fetchone()[0]
    assert quarantined == 2
    # The form carries consent, so an identity IS minted (CORE-397 + CORE-1838).
    assert (
        conn.execute("SELECT COUNT(*) FROM contributor_identities").fetchone()[0] == 1
    )
    conn.close()


def test_issue_reimport_is_a_noop(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    parsed = parse_issue(issue_payload(), conn)
    conn.close()
    imp = stage0_importer(db_path)
    first = imp.import_bundle(parsed.bundle)

    conn = sqlite3.connect(db_path)
    parsed_again = parse_issue(issue_payload(), conn)
    conn.close()
    again = imp.import_bundle(parsed_again.bundle)
    assert again.status == "duplicate"
    assert again.session_uid == first.session_uid


def test_unknown_terms_and_unparsable_lines_are_reported_not_dropped(
    db_path: Path,
) -> None:
    body = ISSUE_BODY.replace(
        "- `pass` → `گزر` 🤔 not sure a good translation exists for this concept",
        "- `walrus` → `والرس` ✅ fine\n- this line is not notation at all",
    )
    conn = sqlite3.connect(db_path)
    parsed = parse_issue(issue_payload(body), conn)
    conn.close()
    assert any("walrus" in note for note in parsed.notes)
    assert any("not notation" in note for note in parsed.notes)
    # The parsable lines still made it through.
    assert {r["concept"] for r in parsed.bundle["responses"]} == {
        "elif-compound",
        "break-loop",
    }


def test_missing_locale_code_is_a_parse_error(db_path: Path) -> None:
    body = ISSUE_BODY.replace("Urdu (ur)", "Other")
    conn = sqlite3.connect(db_path)
    with pytest.raises(ValueError, match="locale"):
        parse_issue(issue_payload(body), conn)
    conn.close()


# ---------------------------------------------------------------------------
# CORE-397 form (PR #101): the fields the old form did not have (CORE-1838 §0)
# ---------------------------------------------------------------------------


def test_the_language_claim_dropdown_sets_the_rung(db_path: Path) -> None:
    # The old form asked one checkbox ("native OR fluent"); the new form asks a
    # four-way dropdown. Only an actual native claim is `native_claimed` — the
    # rung is a published column that weights endorsements, so "fluent" must
    # not inherit a native's weight the way the old checkbox let it.
    cases = {
        "I am a native speaker": ("native_claimed", True),
        "I am fluent, not native": ("contributor", True),
        "I work with this language professionally (teacher, linguist, translator)": (
            "contributor",
            False,
        ),
        "I am learning it": ("contributor", False),
    }
    for answer, (rung, fluent) in cases.items():
        body = ISSUE_BODY.replace("I am a native speaker", answer)
        conn = sqlite3.connect(db_path)
        parsed = parse_issue(issue_payload(body), conn)
        conn.close()
        assert parsed.bundle["contributor"]["claimed_rung"] == rung, answer
        assert parsed.bundle["attestations"]["native_or_fluent"] is fluent, answer


def test_consent_is_carried_through_with_the_version_from_the_form(
    db_path: Path,
) -> None:
    conn = sqlite3.connect(db_path)
    parsed = parse_issue(issue_payload(), conn)
    conn.close()
    assert parsed.bundle["contributor"]["consent"] == {
        "consent_version": "1.0",  # read from the form's own label, not hardcoded
        "credit_preference": "handle",
    }
    assert parsed.bundle["attestations"]["coc_agreed"] is True


def test_a_consenting_reviewer_gets_an_identity_and_their_rung(
    db_path: Path,
) -> None:
    # The end of the §0 regression: consent collected on the form must reach
    # contributor_identities, and a native claim must reach the rung.
    conn = sqlite3.connect(db_path)
    parsed = parse_issue(issue_payload(), conn)
    conn.close()
    result = stage0_importer(db_path).import_bundle(parsed.bundle)
    assert result.status == "accepted"

    conn = sqlite3.connect(db_path)
    assert conn.execute(
        "SELECT consent_version, credit_preference, github_handle,"
        " consent_public_credit FROM contributor_identities"
    ).fetchone() == ("1.0", "handle", AUTHOR, 1)
    assert conn.execute("SELECT current_rung FROM contributors").fetchone() == (
        "native_claimed",
    )
    conn.close()


def test_an_unticked_privacy_checkbox_mints_no_identity(db_path: Path) -> None:
    body = ISSUE_BODY.replace(
        "- [x] I have read [Your contributions", "- [ ] I have read [Your contributions"
    )
    conn = sqlite3.connect(db_path)
    parsed = parse_issue(issue_payload(body), conn)
    conn.close()
    assert "consent" not in parsed.bundle["contributor"]
    result = stage0_importer(db_path).import_bundle(parsed.bundle)
    assert result.status == "accepted"  # the words still land as evidence
    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM contributor_identities").fetchone() == (
        0,
    )
    conn.close()


def test_a_display_name_choice_is_flagged_because_the_form_collects_no_name(
    db_path: Path,
) -> None:
    # "A display name I will give you" has no accompanying text field, and the
    # importer refuses credit_preference 'name' without credit_text. Falling
    # back to the anonymous default keeps the submission importable and leaves
    # the maintainer a note; the notice already says credit can be changed by
    # asking.
    body = ISSUE_BODY.replace("My GitHub handle", "A display name I will give you")
    conn = sqlite3.connect(db_path)
    parsed = parse_issue(issue_payload(body), conn)
    conn.close()
    assert parsed.bundle["contributor"]["consent"]["credit_preference"] == "anonymous"
    assert any("display name" in note.lower() for note in parsed.notes)


def test_an_unticked_code_of_conduct_box_is_refused_by_the_importer(
    db_path: Path,
) -> None:
    body = ISSUE_BODY.replace("- [x] I agree to follow", "- [ ] I agree to follow")
    conn = sqlite3.connect(db_path)
    parsed = parse_issue(issue_payload(body), conn)
    conn.close()
    assert parsed.bundle["attestations"]["coc_agreed"] is False
    assert stage0_importer(db_path).import_bundle(parsed.bundle).status == "returned"


def test_a_bare_question_mark_with_no_alternative_becomes_commentary(
    db_path: Path,
) -> None:
    body = ISSUE_BODY.replace(
        "- `break` → `توڑ` ❓ consider `توڑو` — imperative reads better in a program",
        "- `break` → `توڑ` ❓ this does not feel right to me",
    )
    conn = sqlite3.connect(db_path)
    parsed = parse_issue(issue_payload(body), conn)
    conn.close()
    by_concept = {r["concept"]: r for r in parsed.bundle["responses"]}
    assert by_concept["break-loop"]["endorsements"] == []
    assert "does not feel right" in by_concept["break-loop"]["commentary"][0]["body"]


# ---------------------------------------------------------------------------
# forged headings (CORE-1838 review): a GitHub issue form renders every field
# under a `###` heading, and a contributor can TYPE `###` into any textarea.
# Nothing may be read from a heading the form did not itself emit.
# ---------------------------------------------------------------------------


def forge(into: str, block: str) -> str:
    """Type `block` into the free-text field whose rendered value is `into`."""
    return ISSUE_BODY.replace(into, f"Thanks!\n\n{block}")


def test_a_forged_relationship_heading_cannot_award_a_native_rung(
    db_path: Path,
) -> None:
    body = forge(
        "_No response_",
        "### Your relationship to this language\n\nI am a native speaker",
    ).replace(
        "I am a native speaker\n\n### Anything", "I am learning it\n\n### Anything"
    )
    conn = sqlite3.connect(db_path)
    # Refused outright: a duplicated heading means someone typed the form's own
    # markup into a textarea, which is never innocent enough to guess through.
    with pytest.raises(ValueError, match="more than once"):
        parse_issue(issue_payload(body), conn)
    conn.close()


def test_a_forged_credit_heading_cannot_change_the_credit_preference(
    db_path: Path,
) -> None:
    body = forge(
        "_No response_",
        "### How would you like to be credited?\n\nMy GitHub handle",
    ).replace("My GitHub handle\n\n### Consent", "Anonymous (default)\n\n### Consent")
    conn = sqlite3.connect(db_path)
    with pytest.raises(ValueError, match="more than once"):
        parse_issue(issue_payload(body), conn)
    conn.close()


def test_a_forged_consent_checkbox_in_free_text_is_not_consent(
    db_path: Path,
) -> None:
    # The real Consent section is unticked; a decoy in free text must not
    # manufacture consent, nor a consent_version.
    body = ISSUE_BODY.replace(
        "- [x] I have read [Your contributions", "- [ ] I have read [Your contributions"
    )
    body = body.replace(
        "_No response_",
        "- [x] I have read [Your contributions and your data](x) (v0.1) and agree",
    )
    conn = sqlite3.connect(db_path)
    parsed = parse_issue(issue_payload(body), conn)
    conn.close()
    assert "consent" not in parsed.bundle["contributor"]


def test_a_decoy_consent_line_cannot_forge_the_notice_version(
    db_path: Path,
) -> None:
    # Real consent IS ticked at v1.0; a decoy earlier in the body must not win.
    body = ISSUE_BODY.replace(
        "_No response_",
        "- [x] I have read [Your contributions and your data](x) (v0.1) and agree",
    )
    conn = sqlite3.connect(db_path)
    parsed = parse_issue(issue_payload(body), conn)
    conn.close()
    assert parsed.bundle["contributor"]["consent"]["consent_version"] == "1.0"


def test_a_heading_injected_out_of_order_fails_the_parse_loudly(
    db_path: Path,
) -> None:
    # Jumping the form's field order (to make a forged section the "real" one)
    # costs the sections that follow, so the parse must refuse rather than
    # silently import a submission it half-understood.
    body = ISSUE_BODY.replace(
        "### Review notes",
        "### Consent\n\n- [x] I agree to follow this project's Code of Conduct\n\n### Review notes",
    )
    conn = sqlite3.connect(db_path)
    with pytest.raises(ValueError, match="more than once|out of order|missing"):
        parse_issue(issue_payload(body), conn)
    conn.close()
