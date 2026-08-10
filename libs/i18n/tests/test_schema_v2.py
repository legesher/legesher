"""Validation suite for the concept-centric schema v2 (CORE-1501).

These tests are the evidence behind the schema decision, not incidental
coverage. Each one pins an invariant that the Hugging Face corpus freezes:

* **the frozen keys** -- golden vectors with literal digests, because the uid
  formula is a one-way door and nothing else pins it
* the payoff -- one concept, one decision, every programming language inherits it
* the endorsement model -- one row per person, count derived, double-voting
  structurally impossible, weighting by reviewer rung applied at query time
* the corpus/canon split -- canon may only ratify an option that exists in the
  corpus and passes identifier validation, and every one of those rules holds
  under UPDATE and DELETE, not just INSERT
* BCP 47 locale fallback (RFC 4647 Lookup) -- ``ar-EG`` resolves through ``ar``
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from collections.abc import Iterator
from pathlib import Path

import pytest

from legesher_i18n.db.schema_v2 import (
    CONTRIBUTOR_TOKEN_LENGTH,
    UID_HASH_LENGTH,
    _SEP,
    apply_schema_v2,
    connect,
    contributor_id,
    endorsement_uid,
    option_uid,
)

#: Fixed salt so the fixture's opaque ids are stable and readable in a failure.
TEST_SALT = "test-salt"

AISHA = contributor_id("aisha", salt=TEST_SALT)
OMAR = contributor_id("omar", salt=TEST_SALT)
LAYLA = contributor_id("layla", salt=TEST_SALT)
ANON = contributor_id("anon", salt=TEST_SALT)


@pytest.fixture
def db() -> Iterator[sqlite3.Connection]:
    """An in-memory database with the v2 schema and a small reference fixture."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema_v2(conn)

    conn.executescript(
        """
        INSERT INTO programming_languages (code, name, status) VALUES
            ('python',     'Python',     'shipping'),
            ('javascript', 'JavaScript', 'planned');

        -- BCP 47, with a real fallback edge: ar-EG -> ar.
        INSERT INTO locales (tag, parent_tag, language_subtag, region_subtag,
                             name, native_name, direction, in_registry) VALUES
            ('ar',    NULL, 'ar', NULL, 'Arabic',            'العربية', 'rtl', 1),
            ('ar-EG', 'ar', 'ar', 'EG', 'Arabic (Egypt)',    'العربية', 'rtl', 1),
            ('tr',    NULL, 'tr', NULL, 'Turkish',           'Türkçe',  'ltr', 1);

        -- One concept spelled differently in each PL: def / function.
        INSERT INTO concepts (id, slug, definition_en, category) VALUES
            (1, 'function-definition',
                'Define a named, reusable block of code.', 'declaration'),
            (2, 'boolean-true', 'Boolean literal for truth.', 'value_literal');

        INSERT INTO terms (concept_id, programming_language, name, category) VALUES
            (1, 'python',     'def',      'keyword'),
            (1, 'javascript', 'function', 'keyword'),
            (2, 'python',     'True',     'special_constant'),
            (2, 'javascript', 'true',     'keyword');
        """
    )
    # Opaque ids -- `contributors.id` is the only identity column the corpus
    # publishes, so even the fixture may not put a name in it.
    conn.executemany(
        "INSERT INTO contributors (id, current_rung) VALUES (?, ?)",
        [
            (AISHA, "native_verified"),
            (OMAR, "contributor"),
            (LAYLA, "certified"),
            (ANON, "anonymous"),
        ],
    )
    conn.commit()
    yield conn
    conn.close()


def _add_option(
    conn: sqlite3.Connection,
    concept_id: int,
    concept_slug: str,
    locale: str,
    surface: str,
    *,
    programming_language: str | None = None,
    source: str = "community",
    valid: bool = True,
) -> str:
    """Insert an option plus one provenance row and its validation cache."""
    uid = option_uid(concept_slug, locale, surface, programming_language)
    conn.execute(
        "INSERT INTO options (uid, concept_id, locale, programming_language, surface_form) "
        "VALUES (?, ?, ?, ?, ?)",
        (uid, concept_id, locale, programming_language, surface),
    )
    conn.execute(
        "INSERT INTO option_provenance (option_uid, source, source_detail) VALUES (?, ?, ?)",
        (uid, source, "test"),
    )
    conn.execute(
        "INSERT INTO option_validations (option_uid, validator_version, identifier_valid, "
        "nfkc_stable, script_consistent) VALUES (?, 'test-1', ?, ?, 1)",
        (uid, int(valid), int(valid)),
    )
    return uid


def _endorse(
    conn: sqlite3.Connection,
    uid: str,
    contributor: str,
    rung: str,
    *,
    created_at: str = "2026-07-14T00:00:00",
    method: str = "portal",
) -> str:
    eid = endorsement_uid(uid, contributor, method, created_at)
    conn.execute(
        "INSERT INTO endorsements (uid, option_uid, contributor_id, method, "
        "rung_at_endorsement, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (eid, uid, contributor, method, rung, created_at),
    )
    return eid


def _select(
    conn: sqlite3.Connection,
    concept_id: int,
    locale: str,
    uid: str,
    surface: str,
    *,
    programming_language: str | None = None,
    status: str = "reviewed",
    identity_ok: int = 0,
) -> None:
    conn.execute(
        "INSERT INTO canon_selections (concept_id, locale, programming_language, option_uid, "
        "surface_form, status, identity_ok, source_file) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            concept_id,
            locale,
            programming_language,
            uid,
            surface,
            status,
            identity_ok,
            f"canon/{locale}.toml",
        ),
    )


# ---------------------------------------------------------------------------
# THE FROZEN KEYS
#
# `option_uid` is the published primary key of the Hugging Face corpus: it is
# what a native speaker's endorsement hangs off. Once the first dataset is
# pushed, the formula CANNOT CHANGE -- a change silently re-keys every option in
# a corpus that other people's work is now attached to.
#
# Before these vectors existed, NOTHING pinned it. `_SEP`, `UID_HASH_LENGTH`,
# the order of the four fields, and the NFC call could all be edited and the
# whole suite still passed green.
#
# >>> THE LITERALS BELOW MAY NEVER CHANGE AFTER THE FIRST HF PUBLISH. <<<
# A diff here is not a test to update. It is a corpus fork.
# ---------------------------------------------------------------------------


def test_uid_formula_constants_are_frozen() -> None:
    """The two constants the digest is built from."""
    assert UID_HASH_LENGTH == 24
    assert _SEP == "\x1f"


def test_option_uid_golden_vectors() -> None:
    """Literal digests, from the current implementation. See the banner above."""
    # ASCII, concept-wide.
    assert option_uid("boolean-true", "es", "verdadero") == (
        "opt_3b5379fa3352b0a64b4063c2"
    )
    # Non-Latin script (Arabic).
    assert option_uid("boolean-true", "ar", "صحيح") == "opt_7739c4b219c286dde5e1ec16"

    # NFC vs NFD: the same word, and therefore the same option. This is the NFC
    # call inside normalize_surface_form -- drop it and these two diverge.
    nfd = unicodedata.normalize("NFD", "doğru")
    assert nfd != "doğru"  # the fixture is a genuine NFD string
    assert option_uid("boolean-true", "tr", "doğru") == ("opt_d7ff0a7e06da60bede693c8d")
    assert option_uid("boolean-true", "tr", nfd) == "opt_d7ff0a7e06da60bede693c8d"

    # Both pl_scope variants: concept-wide ('*') and a PL-scoped option.
    assert option_uid("function-definition", "tr", "işlev") == (
        "opt_7ae08c8e8299d699073cbb18"
    )
    assert option_uid("function-definition", "tr", "işlev", "javascript") == (
        "opt_aebfd4abf3bbb7074c505b4a"
    )

    # The locale is inside the hash, and it is case-sensitive: this is why
    # locales.tag carries a canonical-casing CHECK (see the BCP 47 tests).
    assert option_uid("boolean-true", "ar-EG", "صح") == ("opt_9bb3fb19da327424bf3b91f3")


def test_endorsement_uid_golden_vector() -> None:
    """The endorsement key is frozen for the same reason."""
    assert (
        endorsement_uid(
            "opt_7739c4b219c286dde5e1ec16",
            "c_0123456789abcdef",
            "portal",
            "2026-07-14T00:00:00",
        )
        == "end_2ccb6c8fa058a4c6637f8c37"
    )


def test_uid_inputs_may_not_smuggle_the_field_separator() -> None:
    """A U+001F in any field lets two DISTINCT tuples forge ONE uid.

    The docstring used to *assert* that U+001F "can never appear ... so no input
    can forge a different tuple". Nothing enforced it, and the collision is real:

        option_uid('c', 'tr\\x1f*\\x1fx', 'y')  ->  opt_622967141ae3b4589d30863f
        option_uid('c', 'tr',       'x\\x1f*\\x1fy')  ->  opt_622967141ae3b4589d30863f

    (Python's ``.strip()`` treats \\x1f as whitespace only at the EDGES, so an
    interior one survives ``normalize_surface_form`` untouched.)

    The fix is pure input validation -- it changes the digest of nothing that was
    ever legal -- so it stays safe to apply even after the formula is frozen.
    """
    with pytest.raises(ValueError, match="U\\+001F"):
        option_uid("c", "tr\x1f*\x1fx", "y")
    with pytest.raises(ValueError, match="U\\+001F"):
        option_uid("c", "tr", "x\x1f*\x1fy")

    # Every field, and the endorsement digest too.
    with pytest.raises(ValueError, match="U\\+001F"):
        option_uid("con\x1fcept", "tr", "x")
    with pytest.raises(ValueError, match="U\\+001F"):
        option_uid("c", "tr", "x", "java\x1fscript")
    with pytest.raises(ValueError, match="U\\+001F"):
        endorsement_uid("opt_x", "c_y\x1fz", "portal", "2026-07-14T00:00:00")


def test_stored_uids_never_drift_from_their_columns(db: sqlite3.Connection) -> None:
    """Recompute every uid from the row it is supposed to address.

    Catches a formula change, a non-NFC surface_form written past the Python
    helper, and a mis-keyed row -- none of which SQLite can express as a CHECK.
    The same query is what a corpus-integrity job runs over the published data.
    """
    _add_option(db, 1, "function-definition", "tr", "tanımla")
    _add_option(
        db, 1, "function-definition", "tr", "işlev", programming_language="javascript"
    )
    _add_option(db, 2, "boolean-true", "ar", "صحيح")
    _add_option(db, 2, "boolean-true", "ar-EG", "صح")
    db.commit()

    rows = db.execute(
        "SELECT o.uid, c.slug, o.locale, o.surface_form, o.programming_language "
        "FROM options o JOIN concepts c ON c.id = o.concept_id"
    ).fetchall()
    assert rows
    for row in rows:
        assert row["uid"] == option_uid(
            row["slug"],
            row["locale"],
            row["surface_form"],
            row["programming_language"],
        )


# ---------------------------------------------------------------------------
# The schema runs
# ---------------------------------------------------------------------------


def test_foreign_keys_must_be_enabled_per_connection(tmp_path: Path) -> None:
    """`PRAGMA foreign_keys` is per-CONNECTION and OFF by default.

    Every structural guarantee in this schema is a foreign key, and the
    `PRAGMA foreign_keys = ON` at the top of schema_v2.sql applies only to the
    connection that ran the DDL -- it is NOT a property of the file. A plain
    sqlite3.connect() to the resulting database enforces nothing at all.
    """
    path = tmp_path / "v2.db"
    conn = sqlite3.connect(path)
    apply_schema_v2(conn)
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    conn.close()

    # The trap: a fresh, naive connection to the same FILE.
    naive = sqlite3.connect(path)
    assert naive.execute("PRAGMA foreign_keys").fetchone()[0] == 0
    naive.close()

    # schema_v2.connect() is the supported way in, and it turns them on.
    checked = connect(path)
    assert checked.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    with pytest.raises(sqlite3.IntegrityError):
        checked.execute(
            "INSERT INTO options (uid, concept_id, locale, surface_form) "
            "VALUES (?, 999, 'zz', 'x')",
            (option_uid("nope", "zz", "x"),),
        )
    checked.close()


def test_recursive_triggers_must_be_enabled_per_connection(tmp_path: Path) -> None:
    """`PRAGMA recursive_triggers` is the second per-connection trap.

    While it is OFF (SQLite's default), the implicit DELETE inside
    `INSERT OR REPLACE` does NOT fire BEFORE DELETE triggers -- so REPLACE
    walks through every append-only guard as if it were not there. connect()
    and apply_schema_v2() both turn it ON; this pins that they keep doing so.
    """
    path = tmp_path / "v2.db"
    conn = sqlite3.connect(path)
    apply_schema_v2(conn)
    assert conn.execute("PRAGMA recursive_triggers").fetchone()[0] == 1
    conn.close()

    naive = sqlite3.connect(path)
    assert naive.execute("PRAGMA recursive_triggers").fetchone()[0] == 0
    naive.close()

    checked = connect(path)
    assert checked.execute("PRAGMA recursive_triggers").fetchone()[0] == 1
    checked.close()


def test_locale_components_cannot_drift_from_the_tag(db: sqlite3.Connection) -> None:
    """ATTACK (review, 2026-07-14): ('ar-EG', ..., region_subtag='SA') was accepted.

    The component columns are a decomposition of the tag; a prefix-only CHECK
    let them lie to every join that uses them. The recomposition CHECK requires
    that they re-join into exactly the tag.
    """
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO locales (tag, language_subtag, region_subtag, name, "
            "native_name, direction, in_registry) "
            "VALUES ('ar-SA', 'ar', 'EG', 'x', 'x', 'rtl', 1)"
        )
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO locales (tag, language_subtag, script_subtag, name, "
            "native_name, direction, in_registry) "
            "VALUES ('zh', 'zh', 'Hans', 'x', 'x', 'ltr', 1)"
        )
    # And the honest row still goes in.
    db.execute(
        "INSERT INTO locales (tag, language_subtag, script_subtag, name, "
        "native_name, direction, in_registry) "
        "VALUES ('zh-Hans', 'zh', 'Hans', 'Chinese (Simplified)', '中文', 'ltr', 1)"
    )


def test_replace_cannot_rewrite_an_endorsement(db: sqlite3.Connection) -> None:
    """ATTACK (review, 2026-07-14): REPLACE INTO endorsements re-rungs a vote.

    Verified live on a migrated DB with recursive_triggers OFF: the REPLACE's
    implicit DELETE skipped the BEFORE DELETE trigger and rewrote
    rung_at_endorsement contributor -> maintainer (weight 1.0 -> 8.0). With the
    pragma ON, the implicit DELETE hits the trigger and the REPLACE is refused.
    """
    uid = _add_option(db, 2, "boolean-true", "ar", "صحيح")
    eid = _endorse(db, uid, OMAR, "contributor")
    db.commit()

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        db.execute(
            "REPLACE INTO endorsements (uid, option_uid, contributor_id, method, "
            "rung_at_endorsement, created_at) VALUES (?, ?, ?, 'portal', "
            "'maintainer', '2026-07-14T00:00:00')",
            (eid, uid, OMAR),
        )
    rung = db.execute(
        "SELECT rung_at_endorsement FROM endorsements WHERE uid = ?", (eid,)
    ).fetchone()[0]
    assert rung == "contributor"


def test_replace_cannot_forge_a_validation_under_canon(
    db: sqlite3.Connection,
) -> None:
    """ATTACK: REPLACE INTO option_validations under a live canon row.

    trg_validations_frozen_under_canon is a BEFORE UPDATE/DELETE pair; REPLACE
    used to slip between them via the untriggered implicit DELETE.
    """
    uid = _add_option(db, 2, "boolean-true", "ar", "صحيح")
    _endorse(db, uid, AISHA, "native_verified")
    _select(db, 2, "ar", uid, "صحيح")
    db.commit()

    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "REPLACE INTO option_validations (option_uid, validator_version, "
            "identifier_valid, nfkc_stable, script_consistent) "
            "VALUES (?, 'forged-2', 0, 0, 0)",
            (uid,),
        )
    version = db.execute(
        "SELECT validator_version FROM option_validations WHERE option_uid = ?",
        (uid,),
    ).fetchone()[0]
    assert version == "test-1"


def test_replace_cannot_rewrite_an_option_surface(db: sqlite3.Connection) -> None:
    """ATTACK: REPLACE INTO options rewrites the word under its endorsements."""
    uid = _add_option(db, 2, "boolean-true", "ar", "صحيح")
    _endorse(db, uid, AISHA, "native_verified")
    db.commit()

    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "REPLACE INTO options (uid, concept_id, locale, surface_form) "
            "VALUES (?, 2, 'ar', 'مزور')",
            (uid,),
        )
    surface = db.execute(
        "SELECT surface_form FROM options WHERE uid = ?", (uid,)
    ).fetchone()[0]
    assert surface == "صحيح"


def test_schema_applies_cleanly(db: sqlite3.Connection) -> None:
    """Every table, view, and trigger in the DDL is created."""
    objects = {
        row["name"]
        for row in db.execute(
            "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
        )
    }
    for expected in (
        "build_meta",
        "concepts",
        "terms",
        "options",
        "option_provenance",
        "endorsements",
        "option_validations",
        "contributors",
        "contributor_identities",
        "canon_selections",
        "endorsement_counts",
        "option_standings",
        "term_resolution",
        "pack_export",
        "pack_export_conflicts",
        "locale_fallback",
        "trg_canon_requires_valid_identifier",
        # The invariants that hold under UPDATE / DELETE, not just INSERT.
        "trg_canon_no_update",
        "trg_options_no_delete",
        "trg_options_no_withdraw_while_canon",
        "trg_endorsements_append_only",
        "trg_endorsements_no_delete",
        "trg_validations_frozen_under_canon",
    ):
        assert expected in objects, f"missing schema object: {expected}"


# ---------------------------------------------------------------------------
# The payoff: one concept, one decision, N programming languages
# ---------------------------------------------------------------------------


def test_one_selection_serves_every_programming_language(
    db: sqlite3.Connection,
) -> None:
    """A concept-wide canon row ships to Python AND JavaScript from one decision.

    This is the reason the schema exists: `def` and `function` are one concept,
    so a single Turkish decision reaches both packs. Under v1 this required two
    term rows and two independent translation + review cycles.
    """
    uid = _add_option(db, 1, "function-definition", "tr", "tanımla")
    _select(db, 1, "tr", uid, "tanımla")
    db.commit()

    rows = db.execute(
        "SELECT programming_language, english_term, translation, scope "
        "FROM pack_export WHERE locale = 'tr' AND concept_slug = 'function-definition' "
        "ORDER BY programming_language"
    ).fetchall()

    assert [
        (r["programming_language"], r["english_term"], r["translation"]) for r in rows
    ] == [
        ("javascript", "function", "tanımla"),
        ("python", "def", "tanımla"),
    ]
    assert {r["scope"] for r in rows} == {"concept_wide"}


def test_pl_override_beats_concept_wide_for_that_language_only(
    db: sqlite3.Connection,
) -> None:
    """A PL override changes one pack and leaves the others on the concept-wide word."""
    wide = _add_option(db, 1, "function-definition", "tr", "tanımla")
    js = _add_option(
        db, 1, "function-definition", "tr", "işlev", programming_language="javascript"
    )
    _select(db, 1, "tr", wide, "tanımla")
    _select(db, 1, "tr", js, "işlev", programming_language="javascript")
    db.commit()

    rows = {
        r["programming_language"]: (r["translation"], r["scope"])
        for r in db.execute(
            "SELECT programming_language, translation, scope FROM pack_export "
            "WHERE locale = 'tr' AND concept_slug = 'function-definition'"
        )
    }
    assert rows["python"] == ("tanımla", "concept_wide")
    assert rows["javascript"] == ("işlev", "pl_override")


def test_new_pl_reuse_reports_inherited_coverage(db: sqlite3.Connection) -> None:
    """The 'no re-iteration' number: what a new PL inherits before any work."""
    uid = _add_option(db, 1, "function-definition", "tr", "tanımla")
    _select(db, 1, "tr", uid, "tanımla", status="reviewed")
    db.commit()

    row = db.execute(
        "SELECT concepts_total, concepts_already_selected, concepts_already_reviewed "
        "FROM new_pl_reuse WHERE programming_language = 'javascript' AND locale = 'tr'"
    ).fetchone()
    assert row["concepts_already_selected"] == 1
    assert row["concepts_already_reviewed"] == 1


# ---------------------------------------------------------------------------
# Endorsements: one row per person, count derived
# ---------------------------------------------------------------------------


def test_endorsement_count_is_derived_from_rows(db: sqlite3.Connection) -> None:
    """Three people endorse one option -> COUNT(*) = 3. No stored integer."""
    uid = _add_option(db, 2, "boolean-true", "ar", "صحيح")
    _endorse(db, uid, AISHA, "native_verified", created_at="2026-07-01T00:00:00")
    _endorse(db, uid, OMAR, "contributor", created_at="2026-07-02T00:00:00")
    _endorse(db, uid, LAYLA, "certified", created_at="2026-07-03T00:00:00")
    db.commit()

    row = db.execute(
        "SELECT endorsements, endorsers, weighted_endorsement, native_verified_or_above "
        "FROM endorsement_counts WHERE option_uid = ?",
        (uid,),
    ).fetchone()

    assert row["endorsements"] == 3
    assert row["endorsers"] == 3
    # native_verified (4.0) + contributor (1.0) + certified (8.0)
    assert row["weighted_endorsement"] == pytest.approx(13.0)
    assert row["native_verified_or_above"] == 2

    # Nothing anywhere stores a count.
    columns = {r[1] for r in db.execute("PRAGMA table_info(options)")}
    assert not any("count" in c or "votes" in c for c in columns)


def test_double_voting_is_structurally_impossible(db: sqlite3.Connection) -> None:
    """The same contributor cannot endorse the same option twice."""
    uid = _add_option(db, 2, "boolean-true", "ar", "صحيح")
    _endorse(db, uid, AISHA, "native_verified", created_at="2026-07-01T00:00:00")
    db.commit()

    with pytest.raises(sqlite3.IntegrityError):
        _endorse(db, uid, AISHA, "native_verified", created_at="2026-07-05T00:00:00")


def test_retraction_frees_the_slot_and_drops_the_count(db: sqlite3.Connection) -> None:
    """Retracting is append-only: the row stays, the count falls, a re-endorse is allowed."""
    uid = _add_option(db, 2, "boolean-true", "ar", "صحيح")
    first = _endorse(db, uid, AISHA, "contributor", created_at="2026-07-01T00:00:00")
    db.commit()

    db.execute(
        "UPDATE endorsements SET retracted_at = '2026-07-04' WHERE uid = ?", (first,)
    )
    db.commit()
    count = db.execute(
        "SELECT endorsements FROM endorsement_counts WHERE option_uid = ?", (uid,)
    ).fetchone()["endorsements"]
    assert count == 0

    # She was promoted; her new endorsement carries the new rung, the old row is untouched.
    _endorse(db, uid, AISHA, "certified", created_at="2026-07-06T00:00:00")
    db.commit()
    row = db.execute(
        "SELECT endorsements, weighted_endorsement FROM endorsement_counts WHERE option_uid = ?",
        (uid,),
    ).fetchone()
    assert row["endorsements"] == 1
    assert row["weighted_endorsement"] == pytest.approx(8.0)
    assert db.execute("SELECT COUNT(*) FROM endorsements").fetchone()[0] == 2


def test_reweighting_the_ladder_does_not_touch_community_data(
    db: sqlite3.Connection,
) -> None:
    """Weight is policy, joined at query time -- not a column on the endorsement."""
    uid = _add_option(db, 2, "boolean-true", "ar", "صحيح")
    _endorse(db, uid, LAYLA, "certified", created_at="2026-07-01T00:00:00")
    db.commit()

    before = db.execute(
        "SELECT weighted_endorsement FROM endorsement_counts WHERE option_uid = ?",
        (uid,),
    ).fetchone()[0]
    db.execute(
        "UPDATE review_rungs SET weight = 20.0, policy_version = 'v1' WHERE rung = ?",
        ("certified",),
    )
    db.commit()
    after = db.execute(
        "SELECT weighted_endorsement FROM endorsement_counts WHERE option_uid = ?",
        (uid,),
    ).fetchone()[0]

    assert before == pytest.approx(8.0)
    assert after == pytest.approx(20.0)
    # The endorsement row itself never changed.
    assert (
        db.execute(
            "SELECT rung_at_endorsement FROM endorsements WHERE option_uid = ?", (uid,)
        ).fetchone()[0]
        == "certified"
    )


def test_native_threshold_is_policy_not_a_magic_number(db: sqlite3.Connection) -> None:
    """`native_verified_or_above` reads review_rungs.counts_as_native, not `rank >= 3`.

    The ladder is explicitly designed to be re-tuned (CORE-1466). A hardcoded
    rank threshold in the view would silently re-define the headline number
    across the whole published corpus the moment a rung is inserted mid-ladder.
    """
    uid = _add_option(db, 2, "boolean-true", "ar", "صحيح")
    _endorse(db, uid, OMAR, "contributor", created_at="2026-07-01T00:00:00")
    _endorse(db, uid, AISHA, "native_verified", created_at="2026-07-02T00:00:00")
    db.commit()

    def native_count() -> int:
        return db.execute(
            "SELECT native_verified_or_above FROM endorsement_counts WHERE option_uid = ?",
            (uid,),
        ).fetchone()[0]

    assert native_count() == 1

    # Re-tune the policy: `contributor` now counts. No community row is touched.
    db.execute(
        "UPDATE review_rungs SET counts_as_native = 1 WHERE rung = 'contributor'"
    )
    db.commit()
    assert native_count() == 2


def test_four_candidates_with_counts_are_ranked(db: sqlite3.Connection) -> None:
    """Madison's case: `true` has four candidate words in one locale, each with a count."""
    words = {
        "صحيح": [AISHA, OMAR, LAYLA],  # 3 endorsers
        "صواب": [OMAR],
        "حق": [ANON],  # anonymous: recorded, weighted zero
        "نعم": [],
    }
    uids = {}
    for i, (word, endorsers) in enumerate(words.items()):
        uid = _add_option(db, 2, "boolean-true", "ar", word)
        uids[word] = uid
        for j, who in enumerate(endorsers):
            rung = db.execute(
                "SELECT current_rung FROM contributors WHERE id = ?", (who,)
            ).fetchone()[0]
            _endorse(db, uid, who, rung, created_at=f"2026-07-0{i + 1}T0{j}:00:00")
    db.commit()

    standings = db.execute(
        "SELECT surface_form, endorsements, weighted_endorsement, standing "
        "FROM option_standings WHERE concept_slug = 'boolean-true' AND locale = 'ar' "
        "ORDER BY standing, surface_form"
    ).fetchall()

    assert len(standings) == 4
    assert standings[0]["surface_form"] == "صحيح"
    assert standings[0]["endorsements"] == 3
    assert standings[0]["standing"] == 1

    counts = {r["surface_form"]: r["endorsements"] for r in standings}
    assert counts == {"صحيح": 3, "صواب": 1, "حق": 1, "نعم": 0}

    # An anonymous endorsement is counted but carries no weight -- brigading is
    # visible in the row count while the weighted standing stays honest.
    weights = {r["surface_form"]: r["weighted_endorsement"] for r in standings}
    assert weights["حق"] == pytest.approx(0.0)
    assert weights["صواب"] == pytest.approx(1.0)


def test_same_word_from_model_and_human_is_one_option(db: sqlite3.Connection) -> None:
    """Content-addressed uid: identity is the rendering, provenance is a child row.

    v1 keyed candidates by source, so the same word proposed by Aya and by a
    human became two rows -- which is why 16,710 translation rows hold only
    11,336 distinct renderings.
    """
    machine = option_uid("boolean-true", "ar", "صحيح")
    human = option_uid("boolean-true", "ar", "صحيح")
    assert machine == human

    uid = _add_option(db, 2, "boolean-true", "ar", "صحيح", source="model")
    db.execute(
        "INSERT INTO option_provenance (option_uid, source, source_detail) VALUES (?, ?, ?)",
        (uid, "community", "review-portal"),
    )
    db.commit()

    assert db.execute("SELECT COUNT(*) FROM options").fetchone()[0] == 1
    assert (
        db.execute(
            "SELECT COUNT(*) FROM option_provenance WHERE option_uid = ?", (uid,)
        ).fetchone()[0]
        == 2
    )


def test_option_uid_is_normalization_stable(db: sqlite3.Connection) -> None:
    """An NFD and an NFC spelling of the same word are the same option."""
    assert option_uid("boolean-true", "tr", "doğru") == option_uid(
        "boolean-true", "tr", "doğru".replace("ğ", "ğ")
    )
    assert option_uid("boolean-true", "es", "verdadero") != option_uid(
        "boolean-true", "es", "cierto"
    )
    # Scope is part of the identity: a JS-specific option is not the concept-wide one.
    assert option_uid("boolean-true", "es", "cierto") != option_uid(
        "boolean-true", "es", "cierto", programming_language="javascript"
    )


def test_options_are_append_only(db: sqlite3.Connection) -> None:
    """A bad option is evidence, not garbage: it may be withdrawn, never rewritten."""
    uid = _add_option(db, 2, "boolean-true", "ar", "صحيح")
    db.commit()

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        db.execute("UPDATE options SET surface_form = 'x' WHERE uid = ?", (uid,))

    db.execute("UPDATE options SET withdrawn_at = '2026-07-14' WHERE uid = ?", (uid,))
    db.commit()  # withdrawal is the permitted update


# ---------------------------------------------------------------------------
# Corpus / canon split
# ---------------------------------------------------------------------------


def test_canon_cannot_ship_a_word_that_is_not_in_the_corpus(
    db: sqlite3.Connection,
) -> None:
    """Every shipped word is traceable to an offered option."""
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO canon_selections (concept_id, locale, option_uid, surface_form, "
            "source_file) VALUES (2, 'ar', 'opt_doesnotexist', 'صحيح', 'canon/ar.toml')"
        )


def test_canon_rejects_an_invalid_identifier(db: sqlite3.Connection) -> None:
    """CORE-1400, correctly scoped: gate the SELECTION, not the corpus.

    The corpus happily holds the dirty rendering (it is real evidence of what a
    model produced). The canon refuses to ship it.
    """
    bad = _add_option(db, 2, "boolean-true", "ar", "قيمة صحيحة تماما", valid=False)
    db.commit()

    assert (
        db.execute("SELECT COUNT(*) FROM options WHERE uid = ?", (bad,)).fetchone()[0]
        == 1
    )

    with pytest.raises(sqlite3.IntegrityError, match="identifier/NFKC"):
        _select(db, 2, "ar", bad, "قيمة صحيحة تماما")


def test_canon_rejects_an_unvalidated_option(db: sqlite3.Connection) -> None:
    """Silence is not a pass: an option with no validation row cannot be selected."""
    uid = option_uid("boolean-true", "ar", "صحيح")
    db.execute(
        "INSERT INTO options (uid, concept_id, locale, surface_form) VALUES (?, 2, 'ar', ?)",
        (uid, "صحيح"),
    )
    db.commit()

    with pytest.raises(sqlite3.IntegrityError, match="unvalidated"):
        _select(db, 2, "ar", uid, "صحيح")


def test_canon_rejects_a_scope_mismatch(db: sqlite3.Connection) -> None:
    """A JavaScript-scoped option cannot be selected for Python, or concept-wide."""
    js_only = _add_option(
        db, 1, "function-definition", "tr", "işlev", programming_language="javascript"
    )
    db.commit()

    with pytest.raises(sqlite3.IntegrityError, match="pl_scope"):
        _select(db, 1, "tr", js_only, "işlev", programming_language="python")

    with pytest.raises(sqlite3.IntegrityError, match="pl_scope"):
        _select(db, 1, "tr", js_only, "işlev")


def test_canon_row_must_name_its_source_file(db: sqlite3.Connection) -> None:
    """The canon is text in the monorepo; a DB row with no file behind it cannot exist."""
    uid = _add_option(db, 2, "boolean-true", "ar", "صحيح")
    db.commit()

    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO canon_selections (concept_id, locale, option_uid, surface_form) "
            "VALUES (2, 'ar', ?, 'صحيح')",
            (uid,),
        )


def test_pack_export_conflicts_catches_the_soft_keyword_hazard(
    db: sqlite3.Connection,
) -> None:
    """Two concepts sharing one (pl, spelling) must not resolve to two words in a pack.

    Python's `type` is both a builtin and a 3.12 soft keyword. v1 cannot even
    represent that (UNIQUE(name, programming_language)); v2 can, which creates a
    pack-key collision the old proposal's pack_export would have emitted
    silently. `export_role` keeps the pack unambiguous and this view surfaces
    the divergence for a maintainer to adjudicate.
    """
    db.executescript(
        """
        INSERT INTO concepts (id, slug, definition_en, category) VALUES
            (3, 'type-of-object', 'Return the type of an object.', 'builtin_operation'),
            (4, 'type-alias',     'Declare a new name for an existing type.', 'type_system');
        INSERT INTO terms (concept_id, programming_language, name, category, export_role) VALUES
            (3, 'python', 'type', 'builtin_func', 'primary'),
            (4, 'python', 'type', 'soft_keyword', 'secondary');
        """
    )
    a = _add_option(db, 3, "type-of-object", "tr", "tür")
    b = _add_option(db, 4, "type-alias", "tr", "türadı")
    _select(db, 3, "tr", a, "tür")
    _select(db, 4, "tr", b, "türadı")
    db.commit()

    # The pack stays unambiguous: exactly one row for python/type.
    exported = db.execute(
        "SELECT translation FROM pack_export WHERE programming_language = 'python' "
        "AND locale = 'tr' AND english_term = 'type'"
    ).fetchall()
    assert [r["translation"] for r in exported] == ["tür"]

    # And the divergence is reported rather than silently dropped.
    conflict = db.execute(
        "SELECT distinct_renderings FROM pack_export_conflicts "
        "WHERE programming_language = 'python' AND english_term = 'type'"
    ).fetchone()
    assert conflict["distinct_renderings"] == 2


def test_pack_export_conflicts_does_not_fire_on_a_legitimate_pl_override(
    db: sqlite3.Connection,
) -> None:
    """A PL override is the feature, not a conflict.

    The old view joined `canon_selections` WITHOUT applying the precedence rule
    (`cs.pl_scope IN ('*', t.programming_language)`, no ranking), so a concept
    with both a concept-wide word and a legitimate PL override produced two rows
    and read as two conflicting renderings of one term. Since this view's whole
    contract is "must be EMPTY, or the pack is ambiguous", a CI gate asserting
    that would have made the PL-override feature unusable. It now groups
    `term_resolution` -- i.e. the words the pack actually ships.
    """
    wide = _add_option(db, 1, "function-definition", "tr", "tanımla")
    js = _add_option(
        db, 1, "function-definition", "tr", "işlev", programming_language="javascript"
    )
    _select(db, 1, "tr", wide, "tanımla")
    _select(db, 1, "tr", js, "işlev", programming_language="javascript")
    db.commit()

    # Both packs ship, each with one unambiguous word...
    shipped = {
        r["programming_language"]: r["translation"]
        for r in db.execute(
            "SELECT programming_language, translation FROM pack_export "
            "WHERE locale = 'tr' AND concept_slug = 'function-definition'"
        )
    }
    assert shipped == {"python": "tanımla", "javascript": "işlev"}

    # ...and the view stays empty, as its contract requires.
    assert db.execute("SELECT COUNT(*) FROM pack_export_conflicts").fetchone()[0] == 0


def test_canon_collisions_flags_two_concepts_sharing_a_word(
    db: sqlite3.Connection,
) -> None:
    """v1's find_collisions(), re-keyed by concept."""
    a = _add_option(db, 1, "function-definition", "tr", "aynı")
    b = _add_option(db, 2, "boolean-true", "tr", "aynı")
    _select(db, 1, "tr", a, "aynı")
    _select(db, 2, "tr", b, "aynı")
    db.commit()

    rows = db.execute(
        "SELECT translation, concepts FROM canon_collisions "
        "WHERE programming_language = 'python' AND locale = 'tr'"
    ).fetchall()
    assert [(r["translation"], r["concepts"]) for r in rows] == [("aynı", 2)]


# ---------------------------------------------------------------------------
# BCP 47 locale fallback
# ---------------------------------------------------------------------------


def test_locale_tag_must_be_canonical_bcp47(db: sqlite3.Connection) -> None:
    """The locale key is inside the FROZEN option hash, so its casing is load-bearing.

    BCP 47 is case-INSENSITIVE; SQLite TEXT keys and SHA-256 are case-SENSITIVE:

        option_uid(..., 'ar-EG', ...)  ->  opt_9bb3fb19da327424bf3b91f3
        option_uid(..., 'ar-eg', ...)  ->  opt_31e241ca1f4f029c8e52e4b8

    One 'ar-eg' row, inserted once by one script, permanently FORKS every option
    in that locale into two disjoint corpora. Before the CHECK existed, every
    string below was accepted into the primary key.
    """
    for bad in (
        "ar-eg",  # region must be UPPERCASE -- the corpus-forking one
        "AR",  # language must be lowercase
        "ar-eg-x",
        "en_US",  # underscore is not a BCP 47 separator
        "not a tag!",
        "zzzzz-Qaaa-QQ",  # 5-char primary subtag
        "zh-hans",  # script must be Titlecase
        "zh-HANS",
        "x" * 40,
        "",
        " ar",
    ):
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            db.execute(
                "INSERT INTO locales (tag, language_subtag, name, native_name) "
                "VALUES (?, 'ar', 'n', 'n')",
                (bad,),
            )

    # And the canonical shapes we actually use are all accepted.
    for good, lang, script, region in (
        ("de", "de", None, None),
        ("din", "din", None, None),  # ISO 639-3, no 639-1 equivalent
        ("zh-Hans", "zh", "Hans", None),
        ("pt-BR", "pt", None, "BR"),
        ("es-419", "es", None, "419"),  # UN M.49 region
        ("sr-Latn-RS", "sr", "Latn", "RS"),
    ):
        db.execute(
            "INSERT INTO locales (tag, language_subtag, script_subtag, region_subtag, "
            "name, native_name) VALUES (?, ?, ?, ?, 'n', 'n')",
            (good, lang, script, region),
        )
    db.commit()


def test_the_forking_locale_casing_is_now_unreachable(db: sqlite3.Connection) -> None:
    """The concrete failure the CHECK exists to prevent: a second, forked 'ar' corpus."""
    canonical = option_uid("boolean-true", "ar-EG", "صح")
    forked = option_uid("boolean-true", "ar-eg", "صح")
    assert canonical != forked  # same locale to a human, two keys to the corpus

    # The bad-cased tag can no longer become a locale, so the forked uid has no
    # row it could ever be attached to.
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO locales (tag, language_subtag, region_subtag, name, native_name) "
            "VALUES ('ar-eg', 'ar', 'EG', 'n', 'n')"
        )


def test_locale_fallback_chain(db: sqlite3.Connection) -> None:
    """RFC 4647 Lookup: ar-EG tries itself, then ar."""
    chain = db.execute(
        "SELECT resolved_tag, depth FROM locale_fallback WHERE request_tag = 'ar-EG' "
        "ORDER BY depth"
    ).fetchall()
    assert [(r["resolved_tag"], r["depth"]) for r in chain] == [("ar-EG", 0), ("ar", 1)]


def test_dialect_inherits_the_parent_word_until_it_diverges(
    db: sqlite3.Connection,
) -> None:
    """ar-EG ships the ar word for free; when Egypt picks its own, only Egypt changes.

    This is why the corpus must be keyed by BCP 47 from the start (CORE-1500):
    with a bare `ar` key, Egyptian and Gulf endorsements average into a term that
    is nobody's natural choice.
    """
    msa = _add_option(db, 2, "boolean-true", "ar", "صحيح")
    _select(db, 2, "ar", msa, "صحيح")
    db.commit()

    row = db.execute(
        "SELECT translation, resolved_locale, locale_distance FROM pack_export "
        "WHERE locale = 'ar-EG' AND programming_language = 'python' AND english_term = 'True'"
    ).fetchone()
    assert (row["translation"], row["resolved_locale"], row["locale_distance"]) == (
        "صحيح",
        "ar",
        1,
    )

    egyptian = _add_option(db, 2, "boolean-true", "ar-EG", "صح")
    _select(db, 2, "ar-EG", egyptian, "صح")
    db.commit()

    row = db.execute(
        "SELECT translation, resolved_locale, locale_distance FROM pack_export "
        "WHERE locale = 'ar-EG' AND programming_language = 'python' AND english_term = 'True'"
    ).fetchone()
    assert (row["translation"], row["resolved_locale"], row["locale_distance"]) == (
        "صح",
        "ar-EG",
        0,
    )

    # The parent locale is untouched.
    parent = db.execute(
        "SELECT translation FROM pack_export WHERE locale = 'ar' "
        "AND programming_language = 'python' AND english_term = 'True'"
    ).fetchone()
    assert parent["translation"] == "صحيح"


# ---------------------------------------------------------------------------
# The invariants hold under UPDATE and DELETE, not just INSERT
#
# Every rule in this schema was originally enforced by a BEFORE INSERT trigger
# only, and every one of them was defeated by a one-line UPDATE or DELETE that
# re-entered the forbidden state afterwards. One test per landed attack.
# ---------------------------------------------------------------------------


def test_canon_surface_cannot_be_rewritten_after_insert(db: sqlite3.Connection) -> None:
    """ATTACK: UPDATE canon_selections SET surface_form -> ship a word no option offered."""
    uid = _add_option(db, 2, "boolean-true", "ar", "صحيح")
    _select(db, 2, "ar", uid, "صحيح")
    db.commit()

    with pytest.raises(sqlite3.IntegrityError, match="canon_selections"):
        db.execute(
            "UPDATE canon_selections SET surface_form = 'خطأ' WHERE option_uid = ?",
            (uid,),
        )

    assert (
        db.execute(
            "SELECT translation FROM pack_export WHERE locale = 'ar' "
            "AND programming_language = 'python' AND english_term = 'True'"
        ).fetchone()["translation"]
        == "صحيح"
    )


def test_validation_cannot_be_flipped_under_a_canon_row(db: sqlite3.Connection) -> None:
    """ATTACK: UPDATE option_validations SET identifier_valid = 1 -> ship 'de f!'.

    The canon trigger only fires on INSERT, so flipping the validation flag after
    the fact (or deleting the validation row) walked an invalid identifier
    straight into the pack.
    """
    good = _add_option(db, 1, "function-definition", "tr", "tanimla")
    _select(db, 1, "tr", good, "tanimla")
    db.commit()

    with pytest.raises(sqlite3.IntegrityError, match="canon-selected"):
        db.execute(
            "UPDATE option_validations SET identifier_valid = 0 WHERE option_uid = ?",
            (good,),
        )
    with pytest.raises(sqlite3.IntegrityError, match="canon-selected"):
        db.execute("DELETE FROM option_validations WHERE option_uid = ?", (good,))

    # The corpus-side half: an invalid option still cannot reach the canon by
    # having its verdict rewritten first, because the *canon* row is what the
    # trigger checks -- and that check now runs against a verdict nobody can
    # quietly repoint underneath it.
    bad = _add_option(db, 1, "function-definition", "tr", "de f!", valid=False)
    db.commit()
    with pytest.raises(sqlite3.IntegrityError, match="identifier/NFKC"):
        _select(db, 1, "tr", bad, "de f!")


def test_canon_rejects_a_migration_seeded_validation(db: sqlite3.Connection) -> None:
    """A stamp is not a verdict (finding 6: the CORE-1400 gate was circular).

    The migration used to write `identifier_valid = 1, nfkc_stable = 1,
    validator_version = 'migration-seed'` for all 5,136 canon-bound rows WITHOUT
    RUNNING A VALIDATOR, and the trigger passed them -- including one surface that
    is not a valid Python identifier and 25 that are NFKC-unstable.
    """
    uid = option_uid("boolean-true", "ar", "صحيح")
    db.execute(
        "INSERT INTO options (uid, concept_id, locale, surface_form) VALUES (?, 2, 'ar', ?)",
        (uid, "صحيح"),
    )
    db.execute(
        "INSERT INTO option_validations (option_uid, validator_version, identifier_valid, "
        "nfkc_stable, script_consistent) VALUES (?, 'migration-seed', 1, 1, 1)",
        (uid,),
    )
    db.commit()

    with pytest.raises(sqlite3.IntegrityError, match="unvalidated"):
        _select(db, 2, "ar", uid, "صحيح")


def test_a_canon_selected_option_cannot_be_withdrawn(db: sqlite3.Connection) -> None:
    """ATTACK: insert a clean canon row, THEN withdraw the option -> still exports."""
    uid = _add_option(db, 2, "boolean-true", "ar", "صحيح")
    _select(db, 2, "ar", uid, "صحيح")
    db.commit()

    with pytest.raises(sqlite3.IntegrityError, match="canon-selected"):
        db.execute(
            "UPDATE options SET withdrawn_at = '2026-07-14' WHERE uid = ?", (uid,)
        )


def test_a_withdrawal_cannot_be_reversed(db: sqlite3.Connection) -> None:
    """Un-withdrawing after the canon refused the row is the same attack, backwards."""
    uid = _add_option(db, 2, "boolean-true", "ar", "خطأ")
    db.execute("UPDATE options SET withdrawn_at = '2026-07-14' WHERE uid = ?", (uid,))
    db.commit()

    with pytest.raises(sqlite3.IntegrityError, match="cannot be reversed"):
        db.execute("UPDATE options SET withdrawn_at = NULL WHERE uid = ?", (uid,))


def test_deleting_an_option_cannot_cascade_away_its_endorsements(
    db: sqlite3.Connection,
) -> None:
    """ATTACK: DELETE FROM options -> every community endorsement cascades away."""
    uid = _add_option(db, 2, "boolean-true", "ar", "صحيح")
    _endorse(db, uid, AISHA, "native_verified")
    _endorse(db, uid, OMAR, "contributor", created_at="2026-07-15T00:00:00")
    db.commit()

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        db.execute("DELETE FROM options WHERE uid = ?", (uid,))

    assert db.execute("SELECT COUNT(*) FROM endorsements").fetchone()[0] == 2


def test_an_endorsements_rung_is_immutable(db: sqlite3.Connection) -> None:
    """ATTACK: UPDATE endorsements SET rung_at_endorsement -> weight 0.0 becomes 8.0.

    `rung_at_endorsement` is the whole basis of weighting: the PR claims it is an
    immutable snapshot, and it was not. An anonymous vote could be promoted to
    `maintainer` in one statement.
    """
    uid = _add_option(db, 2, "boolean-true", "ar", "صحيح")
    _endorse(db, uid, ANON, "anonymous")
    db.commit()
    assert db.execute(
        "SELECT weighted_endorsement FROM endorsement_counts WHERE option_uid = ?",
        (uid,),
    ).fetchone()[0] == pytest.approx(0.0)

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        db.execute("UPDATE endorsements SET rung_at_endorsement = 'maintainer'")

    assert db.execute(
        "SELECT weighted_endorsement FROM endorsement_counts WHERE option_uid = ?",
        (uid,),
    ).fetchone()[0] == pytest.approx(0.0)


def test_an_endorsement_cannot_be_moved_to_another_word(db: sqlite3.Connection) -> None:
    """ATTACK: UPDATE endorsements SET option_uid -> a person's vote moves to a word
    they never said."""
    said = _add_option(db, 2, "boolean-true", "ar", "صحيح")
    other = _add_option(db, 2, "boolean-true", "ar", "صواب")
    _endorse(db, said, AISHA, "native_verified")
    db.commit()

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        db.execute("UPDATE endorsements SET option_uid = ?", (other,))
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        db.execute("UPDATE endorsements SET contributor_id = ?", (OMAR,))
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        db.execute("DELETE FROM endorsements")

    counts = {
        r["option_uid"]: r["endorsements"]
        for r in db.execute("SELECT option_uid, endorsements FROM endorsement_counts")
    }
    assert counts[said] == 1
    assert counts[other] == 0


def test_a_retraction_cannot_be_reversed(db: sqlite3.Connection) -> None:
    """Retraction is append-only in both directions: un-retracting rewrites history."""
    uid = _add_option(db, 2, "boolean-true", "ar", "صحيح")
    eid = _endorse(db, uid, AISHA, "native_verified")
    db.execute(
        "UPDATE endorsements SET retracted_at = '2026-07-15' WHERE uid = ?", (eid,)
    )
    db.commit()

    with pytest.raises(sqlite3.IntegrityError, match="cannot be reversed"):
        db.execute("UPDATE endorsements SET retracted_at = NULL WHERE uid = ?", (eid,))


def test_provenance_is_append_only(db: sqlite3.Connection) -> None:
    """Who proposed a word is evidence too."""
    uid = _add_option(db, 2, "boolean-true", "ar", "صحيح", source="model")
    db.commit()

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        db.execute("UPDATE option_provenance SET source = 'community'")
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        db.execute("DELETE FROM option_provenance WHERE option_uid = ?", (uid,))


def test_a_contributor_id_cannot_be_repointed(db: sqlite3.Connection) -> None:
    """The opaque handle is stamped into every published endorsement uid."""
    with pytest.raises(sqlite3.IntegrityError, match="published key"):
        db.execute(
            "UPDATE contributors SET id = ? WHERE id = ?", (contributor_id("x"), AISHA)
        )

    # Promotion -- the one legitimate write -- still works.
    db.execute(
        "UPDATE contributors SET current_rung = 'certified' WHERE id = ?", (AISHA,)
    )
    db.commit()


def test_a_surface_form_cannot_smuggle_the_separator_or_exotic_whitespace(
    db: sqlite3.Connection,
) -> None:
    """The DB-level floor under schema_v2._digest's guard.

    SQLite's one-argument TRIM() strips SPACES ONLY, so `x = TRIM(x)` accepted a
    tab- or newline-padded surface that Python's .strip() would have removed --
    meaning the stored value and the hashed value could disagree.
    """
    for bad in ("x\x1fy", "\ty", "y\n", " y", "y　"):
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            db.execute(
                "INSERT INTO options (uid, concept_id, locale, surface_form) "
                "VALUES (?, 2, 'ar', ?)",
                (option_uid("boolean-true", "ar", "placeholder"), bad),
            )


# ---------------------------------------------------------------------------
# Governance
# ---------------------------------------------------------------------------


def test_withdrawal_keeps_the_endorsement_and_drops_the_identity(
    db: sqlite3.Connection,
) -> None:
    """CORE-1502's recommendation, made structural: counts survive, PII does not."""
    uid = _add_option(db, 2, "boolean-true", "ar", "صحيح")
    _endorse(db, uid, AISHA, "native_verified")
    db.execute(
        "INSERT INTO contributor_identities (contributor_id, source_key, display_name, "
        "consent_public_credit) VALUES (?, 'aisha', 'Aisha K.', 1)",
        (AISHA,),
    )
    db.commit()

    db.execute("DELETE FROM contributor_identities WHERE contributor_id = ?", (AISHA,))
    db.commit()

    row = db.execute(
        "SELECT endorsements FROM endorsement_counts WHERE option_uid = ?", (uid,)
    ).fetchone()
    assert row["endorsements"] == 1
    assert (
        db.execute(
            "SELECT COUNT(*) FROM contributors WHERE id = ?", (AISHA,)
        ).fetchone()[0]
        == 1
    )


def test_contributor_id_cannot_be_a_handle(db: sqlite3.Connection) -> None:
    """`contributors.id` is the ONE identity column the corpus publishes.

    The old CHECK (``id LIKE 'c\\_%'``) rejected only a *bare* handle, which gave
    false comfort: ``c_<handle>`` sailed straight through it -- and
    ``'c_' || created_by`` is exactly what the migration used to write, minting
    ``c_alt_ur_modern``, ``c_reviewer_zh_review``, ``c_reviewer_ur_review``. The CHECK
    is now a SHAPE (``c_`` + 16 hex), which a name cannot satisfy.
    """
    for forged in (
        "madiedgar",  # a bare handle
        "c_madiedgar",  # a handle behind the prefix -- the real hole
        "c_alt_ur_modern",  # what the migration actually produced
        "c_reviewer_zh_review",
        "c_" + "z" * 16,  # right length, not hex
        "c_" + "ab" * 4,  # hex, wrong length
        "c_ABCDEF0123456789",  # uppercase hex
    ):
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO contributors (id) VALUES (?)", (forged,))

    # And a minted one is accepted.
    db.execute("INSERT INTO contributors (id) VALUES (?)", (contributor_id("x"),))


def test_contributor_id_is_an_opaque_token_not_a_handle() -> None:
    """The minted id carries no trace of the person it stands for.

    The source key is now a GITHUB USERNAME (stable, unique, verifiable) rather
    than the v1 first-name label -- but it is just as private, and the published
    id must leak neither.
    """
    minted = contributor_id("zh_reviewer", salt=TEST_SALT)
    assert minted.startswith("c_")
    assert len(minted) == 18
    assert "zh_reviewer".lower() not in minted.lower()
    assert int(minted.removeprefix("c_"), 16) >= 0  # pure hex

    # A distinct person is a distinct id.
    assert minted != contributor_id("ur_reviewer", salt=TEST_SALT)

    # And the old first-name label leaks nothing either, wherever it still appears.
    legacy = contributor_id("alt_ur_modern", salt=TEST_SALT)
    assert "alt" not in legacy and "reviewer" not in legacy


# ---------------------------------------------------------------------------
# THE SALT IS A ONE-WAY DOOR
#
# contributor_id = c_ + HMAC-SHA256(key=salt, msg=source_key), truncated to 16
# hex. HMAC, not sha256(salt || key): the standard keyed construction, chosen
# while the formula was still free to change (review decision, 2026-07-15).
#
# The docs used to say only that the salt must be SECRET. Secrecy is the lesser
# half. The salt is an ingredient of a PUBLISHED PRIMARY KEY, so it must also be
# PERMANENT: if it is ever lost, rotated, or regenerated after the first Hugging
# Face publish, every contributor_id changes, every endorsement re-keys, THE
# CORPUS FORKS, and every contributor's history is orphaned -- unrecoverably,
# because a returning contributor's matching id can never be minted again.
#
# These tests pin the derivation so a change to it cannot land silently. They are
# the same class of guard as the option_uid golden vectors above.
# ---------------------------------------------------------------------------


def test_contributor_id_is_frozen_for_a_given_salt() -> None:
    """Same (source_key, salt) -> same id. Always, and with a pinned shape.

    Literal digests, so that a change to the derivation -- the HMAC key/message
    roles, the hash, CONTRIBUTOR_TOKEN_LENGTH, the `c_` prefix -- fails HERE
    rather than silently re-keying a published corpus.

    Each vector was derived TWO independent ways before pinning -- Python's
    ``hmac`` stdlib and ``openssl dgst -sha256 -hmac`` -- so the pin carries
    cross-implementation evidence, not just a snapshot of this module's output:

        $ echo -n "zh_reviewer" | openssl dgst -sha256 -hmac "test-salt"
        52380ea8e8a87e15...
    """
    # Determinism, restated as the property it actually is: idempotence.
    for _ in range(3):
        assert contributor_id("zh_reviewer", salt=TEST_SALT) == "c_52380ea8e8a87e15"
    assert contributor_id("ur_reviewer", salt=TEST_SALT) == "c_2a8a31dbb854a12f"

    # The shape the `contributors.id` CHECK enforces: 'c_' + exactly 16 lowercase
    # hex. Pinned here too, because the CHECK and the minter must not drift apart.
    for key in ("zh_reviewer", "ur_reviewer", "unresolved:alt_ur_modern"):
        minted = contributor_id(key, salt=TEST_SALT)
        assert len(minted) == 2 + CONTRIBUTOR_TOKEN_LENGTH == 18
        assert re.fullmatch(r"c_[0-9a-f]{16}", minted), minted


def test_rotating_the_salt_forks_the_corpus(db: sqlite3.Connection) -> None:
    """WHY the salt may never be rotated, demonstrated rather than asserted.

    One returning contributor, one changed salt: her endorsement re-keys onto an
    id that has no history, and the id that HAS her history can never be minted
    again. This is the failure the escrow requirement exists to prevent.
    """
    original = contributor_id("zh_reviewer", salt=TEST_SALT)
    rotated = contributor_id("zh_reviewer", salt="rotated-salt")
    assert original != rotated  # the same human, two disjoint corpora

    db.execute("INSERT INTO contributors (id) VALUES (?)", (original,))
    uid = _add_option(db, 2, "boolean-true", "ar", "صحيح")
    _endorse(db, uid, original, "contributor")
    db.commit()

    # Post-rotation, the person shows up as a stranger: her endorsement is not
    # reachable from the id the new salt mints for her.
    assert (
        db.execute(
            "SELECT COUNT(*) FROM endorsements WHERE contributor_id = ?", (rotated,)
        ).fetchone()[0]
        == 0
    )
    assert (
        db.execute(
            "SELECT COUNT(*) FROM endorsements WHERE contributor_id = ?", (original,)
        ).fetchone()[0]
        == 1
    )

    # And her real row cannot be re-pointed at the new id to repair it: the
    # published key is immutable by trigger. There is no recovery without the
    # original salt -- which is why it is escrowed, not merely secret.
    with pytest.raises(sqlite3.IntegrityError, match="published key"):
        db.execute("UPDATE contributors SET id = ? WHERE id = ?", (rotated, original))


# ---------------------------------------------------------------------------
# CORE-1355 -- identity-translation marker: the compare rule and the
# coverage split that separates deliberate cognates from untranslated gaps.
# ---------------------------------------------------------------------------


def test_is_identity_translation_rules() -> None:
    from legesher_i18n.db.schema_v2 import is_identity_translation

    assert is_identity_translation("break", "break")
    assert is_identity_translation("None", "none")  # case-insensitive
    assert is_identity_translation("ascii", "ａｓｃｉｉ")  # NFKC-insensitive
    assert not is_identity_translation("True", "pravda")
    assert not is_identity_translation("break", "brea")
    assert not is_identity_translation("", "")  # empty is not a cognate claim


def test_canon_coverage_splits_cognates_from_translated(
    db: sqlite3.Connection,
) -> None:
    uid_def = _add_option(db, 1, "function-definition", "tr", "tanımla")
    _select(db, 1, "tr", uid_def, "tanımla")
    # canon_selections is a loaded projection (UPDATE is trigger-blocked),
    # so the marker is set at insert — as the migration does.
    uid_true = _add_option(db, 2, "boolean-true", "tr", "True")
    _select(db, 2, "tr", uid_true, "True", identity_ok=1)

    row = db.execute(
        "SELECT canon_terms, identity_cognates, translated_terms "
        "FROM canon_coverage WHERE locale = 'tr'"
    ).fetchone()
    assert row["canon_terms"] == 2
    assert row["identity_cognates"] == 1
    assert row["translated_terms"] == 1
