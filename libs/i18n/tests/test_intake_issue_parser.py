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

### Reviewer qualifications

Native speaker of Urdu, CS student.

### Review notes

**Keywords:**

- `elif` → `ورنہ_اگر` ✅ natural and widely understood
- `break` → `توڑ` ❓ consider `توڑو` — imperative reads better in a program
- `pass` → `گزر` 🤔 not sure a good translation exists for this concept

### Additional context

_No response_

### Reviewer confirmation

- [x] I am a native or fluent speaker of this language
- [x] I agree to follow this project's [Code of Conduct](../../CODE_OF_CONDUCT.md)
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
    assert "consent" not in bundle["contributor"]  # old form has no checkbox
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
    # No consent on the old form -> evidence, no identity (decision 2026-08-11).
    assert (
        conn.execute("SELECT COUNT(*) FROM contributor_identities").fetchone()[0] == 0
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


def test_unchecked_native_claim_stays_contributor(db_path: Path) -> None:
    body = ISSUE_BODY.replace(
        "- [x] I am a native or fluent speaker of this language",
        "- [ ] I am a native or fluent speaker of this language",
    )
    conn = sqlite3.connect(db_path)
    parsed = parse_issue(issue_payload(body), conn)
    conn.close()
    assert parsed.bundle["contributor"]["claimed_rung"] == "contributor"


def test_missing_locale_code_is_a_parse_error(db_path: Path) -> None:
    body = ISSUE_BODY.replace("Urdu (ur)", "Other")
    conn = sqlite3.connect(db_path)
    with pytest.raises(ValueError, match="locale"):
        parse_issue(issue_payload(body), conn)
    conn.close()
