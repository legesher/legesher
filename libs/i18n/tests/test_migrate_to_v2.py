"""Identity and provenance invariants of the v1 -> v2 migration (CORE-1501).

Three properties, each of which is a one-way door once the corpus is published:

* **who a contributor IS** -- the private source key is a GitHub username, not a
  first name; the `_old` twins are the words a review REJECTED and must never be
  endorsed; an ambiguous label is refused, never guessed at
* **the salt** -- publish mode hard-fails on a salt that cannot safely be frozen
* **the upstream obligation** -- rows that are another project's work say so in
  the one provenance column that actually ships, and an unmapped source stops
  the migration rather than defaulting into "we wrote this" (CORE-1720)

The migration builds a NEW database and never writes to the v1 source, so these
run against a synthetic v1 fixture rather than the real ``translations.db``.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from legesher_i18n.db.schema_v2 import (
    DEFAULT_CONTRIBUTOR_SALT,
    apply_schema_v2,
    contributor_id,
    salt_fingerprint,
)
from scripts.migrate_to_v2 import (
    CONTRIBUTOR_IDENTITY_MAP,
    Identity,
    LEGACY_COMMUNITY_SOURCE_DETAIL,
    Withdrawn,
    load_identity_maps,
    NON_HUMAN_CREATED_BY,
    PUBLIC_SOURCES,
    SOURCE_MAP,
    SUPERSEDED_BY_REVIEW,
    SUPERSEDED_SOURCE_DETAIL,
    UPSTREAM_PROJECTS,
    classify_source,
    definition_from_brief,
    migrate,
    require_publishable_salt,
    resolve_identity,
)

SALT = "test-salt"

#: A salt that is long enough to be publishable (>= MIN_PUBLISH_SALT_LENGTH).
GOOD_SALT = "a" * 64

#: Synthetic stand-ins for the private identity data. The REAL label -> person
#: map is private data in the durable data home and no longer in this tree
#: (CORE-1794): tests must run without it, and no real label, name, or handle
#: may appear here. The entries mirror the real data's classes: a zh reviewer
#: whose review displaced pack words, a ur reviewer likewise, and an
#: alternatives label that resolves to ONE person.
TEST_IDENTITIES: dict[str, Identity] = {
    "reviewer_zh_review": Identity("zh_reviewer", "Reviewer Zh"),
    "reviewer_ur_review": Identity("ur_reviewer"),
    "alt_ur_modern": Identity("alt_reviewer", "Alt Reviewer"),
}

#: `<label>_old` -> the review label that displaced it (see the real map's
#: `superseded_by_review` in the data home).
TEST_SUPERSEDED: dict[str, str] = {
    "reviewer_zh_review_old": "reviewer_zh_review",
    "reviewer_ur_review_old": "reviewer_ur_review",
}


@pytest.fixture(autouse=True)
def _synthetic_identity_maps() -> Iterator[None]:
    """Populate the module maps in place (they load empty without the data home)."""
    CONTRIBUTOR_IDENTITY_MAP.clear()
    CONTRIBUTOR_IDENTITY_MAP.update(TEST_IDENTITIES)
    SUPERSEDED_BY_REVIEW.clear()
    SUPERSEDED_BY_REVIEW.update(TEST_SUPERSEDED)
    yield
    CONTRIBUTOR_IDENTITY_MAP.clear()
    SUPERSEDED_BY_REVIEW.clear()


#: The v1 shape, reduced to what the identity logic reads. One term, one locale,
#: and one row per `created_by` class the migration must tell apart.
V1_ROWS = [
    # (term, translation, source, created_by)
    (
        "True",
        "真实",
        "community_review",
        "reviewer_zh_review",
    ),  # the reviewer's suggestion
    (
        "True",
        "真",
        "community_review",
        "reviewer_zh_review_old",
    ),  # the word they REJECTED
    ("False", "نوعیت", "community_review", "reviewer_ur_review"),
    ("False", "قسم", "community_review", "reviewer_ur_review_old"),  # REJECTED
    (
        "break",
        "توڑ",
        "community_review",
        "alt_ur_modern",
    ),  # = @alt_reviewer (resolved 2026-07-14)
    ("break", "universal", "community_review", "universal_python"),  # a pipeline
    ("None", "legacy", "community", None),  # MIT legacy: no author
    ("None", "machine", "aya", "ai-aya"),  # a model
]


@pytest.fixture
def v1_db(tmp_path: Path) -> Iterator[Path]:
    """A minimal v1 database carrying one row of every identity class."""
    path = tmp_path / "v1.db"
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE languages (
            code TEXT PRIMARY KEY, name TEXT, native_name TEXT, bcp47 TEXT,
            direction TEXT, numeral_system TEXT, has_case_distinction INTEGER,
            status TEXT, in_registry INTEGER, script TEXT
        );
        CREATE TABLE terms (
            id INTEGER PRIMARY KEY, name TEXT, programming_language TEXT NOT NULL,
            category TEXT, subcategory TEXT,
            description TEXT, version_added TEXT
        );
        CREATE TABLE translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, term_id INTEGER,
            language_code TEXT, translation TEXT, source TEXT, created_by TEXT,
            model_version TEXT, word_type TEXT, word_form TEXT, confidence TEXT,
            model_rationale TEXT, created_at TEXT
        );
        CREATE TABLE selected_translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, term_id INTEGER,
            language_code TEXT, translation TEXT, selected_by TEXT,
            selected_at TEXT, selection_reason TEXT
        );
        INSERT INTO languages
            (code, name, native_name, bcp47, direction, has_case_distinction,
             status, in_registry)
        VALUES ('ur', 'Urdu', 'اردو', 'ur', 'rtl', 0, 'experimental', 1);
        INSERT INTO terms (id, name, programming_language, category) VALUES
            (1, 'True', 'python', 'special_constant'),
            (2, 'False', 'python', 'special_constant'),
            (3, 'break', 'python', 'keyword'),
            (4, 'None', 'python', 'special_constant'),
            (5, 'break', 'javascript', 'keyword'),
            (6, 'type', 'python', 'builtin_type'),
            (7, 'type', 'python', 'keyword');
        """
    )
    term_ids = {"True": 1, "False": 2, "break": 3, "None": 4}
    conn.executemany(
        "INSERT INTO translations (term_id, language_code, translation, source, "
        "created_by, created_at) VALUES (?, 'ur', ?, ?, ?, '2026-03-19T00:00:00')",
        [(term_ids[t], tr, src, by) for t, tr, src, by in V1_ROWS],
    )
    conn.commit()
    conn.close()
    yield path


def _run(v1: Path, tmp_path: Path, **kwargs: object) -> sqlite3.Connection:
    """Migrate and return a connection to the resulting v2 database."""
    target = tmp_path / "v2.db"
    migrate(v1, target, salt=SALT, **kwargs)  # type: ignore[arg-type]
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# FIX 1 -- the private source key is a GitHub username
# ---------------------------------------------------------------------------


def test_the_source_key_is_a_github_username_not_a_first_name(
    v1_db: Path, tmp_path: Path
) -> None:
    """A first name is ambiguous, collides, and changes. A username does not.

    The PUBLISHED id is unaffected -- it stays the opaque salted digest. What
    improves is the private key it is minted from.
    """
    conn = _run(v1_db, tmp_path)
    keys = {
        r["source_key"]: r["github_handle"]
        for r in conn.execute(
            "SELECT source_key, github_handle FROM contributor_identities"
        )
    }
    assert keys["zh_reviewer"] == "zh_reviewer"
    assert keys["ur_reviewer"] == "ur_reviewer"

    # The raw v1 labels are gone as keys...
    assert "reviewer_zh_review" not in keys
    assert "reviewer_ur_review" not in keys

    # ...and the published id is minted from the username, carrying no name.
    ids = {r["id"] for r in conn.execute("SELECT id FROM contributors")}
    assert contributor_id("zh_reviewer", salt=SALT) in ids
    assert all("reviewer" not in i for i in ids)
    conn.close()


def test_a_word_the_reviewer_rejected_is_never_endorsed(
    v1_db: Path, tmp_path: Path
) -> None:
    """`<name>_review_old` is the word the review REPLACED, not an earlier attestation.

    This is the load-bearing one. Both the original migration and a naive
    "strip `_old` and merge" heuristic record the reviewer as having endorsed the
    exact word she threw out -- inverting the one number the corpus exists to make
    trustworthy.

    Evidence in the real data: zh, 31 term pairs -- `_old` NEVER equals `_new`
    (0/31) and `_new` is ALWAYS the shipped word (31/31); and `reviewer_ur_review_old`
    holds قسم, which the public ur CHANGELOG records as REPLACED by نوعیت.

    v2 needs no new machinery for this: endorsements are positive-only, and
    disagreement is expressed by endorsing a DIFFERENT option -- which is exactly
    what the reviewer did.
    """
    conn = _run(v1_db, tmp_path)
    endorsed = {
        r["surface_form"]
        for r in conn.execute(
            "SELECT o.surface_form FROM endorsements e JOIN options o ON o.uid = e.option_uid"
        )
    }
    # The words they asserted are endorsed...
    assert endorsed == {"真实", "نوعیت", "توڑ"}
    # ...and the words they rejected are NOT, though they remain in the corpus.
    assert "真" not in endorsed and "قسم" not in endorsed

    rejected = conn.execute(
        "SELECT o.surface_form, p.source, p.source_detail, p.contributor_id "
        "FROM options o JOIN option_provenance p ON p.option_uid = o.uid "
        "WHERE o.surface_form IN ('真', 'قسم')"
    ).fetchall()
    assert len(rejected) == 2
    for row in rejected:
        assert row["source"] == "legesher"  # the PACK's word, not the reviewer's
        assert row["contributor_id"] is None  # she did not propose it
        # Neutral label, NOT the v1 `<name>_review_old` label: the label embeds
        # a first name and option_provenance is corpus-layer. The audit trail
        # (which label, which review displaced it) lives privately in
        # SUPERSEDED_BY_REVIEW.
        assert row["source_detail"] == SUPERSEDED_SOURCE_DETAIL
    conn.close()


def test_an_ambiguous_label_resolves_to_one_person(v1_db: Path, tmp_path: Path) -> None:
    """`alt_ur_modern` is @alt_reviewer -- ONE person.

    The real label this stands in for looked like two names, and the public
    CHANGELOG credited the review round jointly -- so the migration held these
    rows back rather than guess. Madison resolved it by hand (2026-07-14): the
    second name in the label named the pack the alternatives responded to, not
    a co-author. (The real resolution and its reasoning live in the data home's
    identity map, CORE-1794.) The resolved rows mint endorsements like anyone
    else's, and no unresolved identity remains.
    """
    assert CONTRIBUTOR_IDENTITY_MAP["alt_ur_modern"].resolved

    conn = _run(v1_db, tmp_path)
    # No unresolved identities survive in the private table...
    assert (
        conn.execute(
            "SELECT COUNT(*) FROM contributor_identities "
            "WHERE source_key LIKE 'unresolved:%'"
        ).fetchone()[0]
        == 0
    )
    # ...her private key is the GitHub username...
    row = conn.execute(
        "SELECT ci.contributor_id, "
        "(SELECT COUNT(*) FROM endorsements e "
        " WHERE e.contributor_id = ci.contributor_id) AS endorsements "
        "FROM contributor_identities ci WHERE ci.source_key = 'alt_reviewer'"
    ).fetchone()
    assert row["endorsements"] == 1  # her word now counts

    # ...and her rendering carries her (opaque) id on its provenance.
    prov = conn.execute(
        "SELECT p.source, p.contributor_id FROM option_provenance p "
        "JOIN options o ON o.uid = p.option_uid WHERE o.surface_form = 'توڑ'"
    ).fetchone()
    assert prov["source"] == "community"
    assert prov["contributor_id"] == row["contributor_id"]
    conn.close()


def test_an_unknown_label_raises_rather_than_being_guessed_at() -> None:
    """A heuristic would silently mis-merge a future contributor. Refuse instead."""
    with pytest.raises(SystemExit, match="unknown v1 created_by label"):
        resolve_identity("some_new_reviewer_2027")

    # And the three classifications stay disjoint -- a label cannot be two things.
    assert not (set(CONTRIBUTOR_IDENTITY_MAP) & set(NON_HUMAN_CREATED_BY))
    assert not (set(CONTRIBUTOR_IDENTITY_MAP) & set(SUPERSEDED_BY_REVIEW))
    assert not (set(SUPERSEDED_BY_REVIEW) & set(NON_HUMAN_CREATED_BY))
    # Every superseded label points at a review that IS a known person.
    for displaced_by in SUPERSEDED_BY_REVIEW.values():
        assert CONTRIBUTOR_IDENTITY_MAP[displaced_by].resolved


def test_pipeline_labels_still_mint_no_endorsement(v1_db: Path, tmp_path: Path) -> None:
    """`universal_python` is a pack, not a person (regression guard)."""
    conn = _run(v1_db, tmp_path)
    prov = conn.execute(
        "SELECT p.source, p.source_detail, p.contributor_id FROM option_provenance p "
        "JOIN options o ON o.uid = p.option_uid WHERE o.surface_form = 'universal'"
    ).fetchone()
    # ANOTHER PROJECT's work -- Apache-2.0, and the whole point of CORE-1720:
    # under the old cut this sat in `import` beside our own packs, so nothing
    # in the PUBLISHED vocabulary said a third-party licence applied.
    assert prov["source"] == "upstream"
    assert prov["source_detail"] == "universal_python"
    assert prov["contributor_id"] is None
    conn.close()


# ---------------------------------------------------------------------------
# FIX 2 -- the salt is a one-way door, so publish mode refuses an unsafe one
# ---------------------------------------------------------------------------


def test_publish_mode_hard_fails_on_an_unpublishable_salt() -> None:
    """A warning is not a gate. The salt can never be rotated, so it must be right.

    It is not a rotatable credential -- it is an ingredient of a published primary
    key. And the source keys are now GitHub usernames: public and enumerable by
    construction, so the salt is the only thing preventing re-identification.
    """
    with pytest.raises(SystemExit, match="requires --contributor-salt"):
        require_publishable_salt(None)
    with pytest.raises(SystemExit, match="PUBLIC dev salt"):
        require_publishable_salt(DEFAULT_CONTRIBUTOR_SALT)
    with pytest.raises(SystemExit, match="at least 32 characters"):
        require_publishable_salt("short-secret")

    assert require_publishable_salt(GOOD_SALT) == GOOD_SALT


def test_publish_mode_refuses_the_dev_salt_before_writing_anything(
    v1_db: Path, tmp_path: Path
) -> None:
    """The check runs BEFORE the target is created: no half-built corpus."""
    target = tmp_path / "v2.db"
    with pytest.raises(SystemExit, match="PUBLIC dev salt"):
        migrate(v1_db, target, salt=DEFAULT_CONTRIBUTOR_SALT, publish=True)
    assert not target.exists()


def test_publish_mode_refuses_an_unresolved_identity(
    v1_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unresolved label is a publish BLOCKER, not a footnote.

    Every real label is resolved today, so the refusal MECHANISM is kept honest
    by putting one back: publishing an unresolved identity would freeze a
    placeholder contributor_id into a corpus other people's endorsements then
    hang off.
    """
    from scripts import migrate_to_v2

    monkeypatch.setitem(
        migrate_to_v2.CONTRIBUTOR_IDENTITY_MAP,
        "alt_ur_modern",
        migrate_to_v2.Identity(None, note="test: forced back to unresolved"),
    )
    target = tmp_path / "v2.db"
    with pytest.raises(SystemExit, match="unresolved contributor identity"):
        migrate(v1_db, target, salt=GOOD_SALT, publish=True)

    # The refusal fires BEFORE the build (review, 2026-07-14): the previous
    # behavior detected this only after dst.commit(), leaving a fully-built,
    # real-salt-minted artifact on disk -- exactly the file that must never be
    # around to publish by accident.
    assert not target.exists()


def test_publish_mode_succeeds_with_every_identity_resolved(
    v1_db: Path, tmp_path: Path
) -> None:
    """With the shipped map fully resolved, publish mode goes green -- the gate
    is not a wall."""
    ledger = migrate(v1_db, tmp_path / "v2.db", salt=GOOD_SALT, publish=True)
    assert ledger.counts["  UNRESOLVED identities"] == 0
    assert ledger.counts["contributors (people)"] == 3


# ---------------------------------------------------------------------------
# The PUBLIC source vocabulary is an obligation cut (CORE-1720)
# ---------------------------------------------------------------------------


def test_the_public_source_vocabulary_is_exactly_four_obligations() -> None:
    """`source` ships in `options.sources`, so its vocabulary is a public promise.

    Four values, four obligations. Anything else reaching the column means a
    consumer is being told something we did not decide.
    """
    assert set(SOURCE_MAP.values()) <= PUBLIC_SOURCES
    assert set(NON_HUMAN_CREATED_BY.values()) <= PUBLIC_SOURCES
    # The schema is the floor, not the convention: it must refuse the retired
    # vocabulary outright rather than trusting the migration to be careful.
    db = sqlite3.connect(":memory:")
    apply_schema_v2(db)
    # FKs off so the CHECK is what fails, not a missing parent option.
    db.execute("PRAGMA foreign_keys = OFF")
    for retired in ("import", "maintainer", "literature"):
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            db.execute(
                "INSERT INTO option_provenance (option_uid, source) VALUES (?, ?)",
                ("opt_" + "0" * 24, retired),
            )
    for kept in sorted(PUBLIC_SOURCES):
        db.execute(
            "INSERT INTO option_provenance (option_uid, source, source_detail) "
            "VALUES (?, ?, 'x')",
            ("opt_" + "0" * 24, kept),
        )
    db.close()


def test_an_unknown_v1_source_stops_the_migration() -> None:
    """An obligation cannot be defaulted.

    Every silent fallback picks a bucket, and the only bucket a fallback could
    pick without asserting something false about a stranger's work is the one
    claiming we authored it. `core-1318-fix` (87 real rows) rode exactly that
    default into the `import` grab-bag for months without anyone deciding it
    belonged there.
    """
    with pytest.raises(SystemExit, match="Unknown v1 translation source"):
        classify_source("some-new-pipeline-2027")

    # The nine real v1 sources are all mapped, so the refusal only ever fires
    # on something genuinely new.
    assert classify_source("core-1318-fix") == "legesher"
    assert classify_source("community") == "upstream"


def test_an_unattributable_upstream_row_stops_the_build(
    v1_db: Path, tmp_path: Path
) -> None:
    """`upstream` without a project to name is an obligation with no discharge.

    The legacy branch recognises the 2,169 legesher-translations rows *by their
    NULL author*. A future `source='community'` row that carried an author would
    fall through it, publish `upstream` -- "another project's licence applies
    here" -- and name no project in the data or the card. Refuse instead.
    """
    conn = sqlite3.connect(v1_db)
    conn.execute(
        "INSERT INTO translations (term_id, language_code, translation, source, "
        "created_by, created_at) VALUES (4, 'ur', 'stray', 'community', "
        "'some_other_project', '2026-03-19T00:00:00')"
    )
    conn.commit()
    conn.close()

    with pytest.raises(SystemExit, match="Cannot attribute an `upstream` row"):
        migrate(v1_db, tmp_path / "v2.db", salt=SALT)


def test_every_upstream_label_has_a_credit_line() -> None:
    """`upstream` without a project, licence and URL is an unpayable obligation.

    The bucket exists so a human can write the credit; a label that classifies
    as `upstream` but has no entry here would publish "someone else's licence
    applies" while withholding whose.
    """
    upstream_labels = {
        label for label, kind in NON_HUMAN_CREATED_BY.items() if kind == "upstream"
    } | {LEGACY_COMMUNITY_SOURCE_DETAIL}
    assert upstream_labels == set(UPSTREAM_PROJECTS)
    for name, url, spdx in UPSTREAM_PROJECTS.values():
        assert name and url.startswith("https://") and spdx


# ---------------------------------------------------------------------------
# FIX 3 -- the upstream obligation rides on the row
# ---------------------------------------------------------------------------


def test_legacy_community_rows_are_upstream_not_community(
    v1_db: Path, tmp_path: Path
) -> None:
    """The v1 `community` rows came from legesher/legesher-translations (MIT).

    They are `upstream`, NOT `community`, and the distinction is the point of
    the whole vocabulary: what we owe here is another repository's notice, not
    an individual's credit-and-withdrawal rights. Someone who asks to be removed
    from `community` is exercising a right we granted them; a licence notice is
    not ours to drop on request.

    `source='upstream'` is what makes the obligation visible IN THE PUBLISHED
    ARTIFACT -- `options.sources` ships, `source_detail` does not -- so the card
    is where the project names and their notices live (CORE-1720).
    """
    conn = _run(v1_db, tmp_path)
    rows = conn.execute(
        "SELECT p.source, p.source_detail, p.contributor_id FROM option_provenance p "
        "WHERE p.source_detail = ?",
        (LEGACY_COMMUNITY_SOURCE_DETAIL,),
    ).fetchall()

    assert len(rows) == 1  # the one `community` row in the fixture
    assert rows[0]["source"] == "upstream"
    assert rows[0]["contributor_id"] is None  # no author, hence no endorsement

    # It is not a person: it mints no contributor and no endorsement.
    assert conn.execute("SELECT COUNT(*) FROM endorsements").fetchone()[0] == 3
    conn.close()


def test_the_migration_reports_the_attribution_row_count(
    v1_db: Path, tmp_path: Path
) -> None:
    """The obligation is counted in the ledger, so it cannot be shipped unnoticed."""
    ledger = migrate(v1_db, tmp_path / "v2.db", salt=SALT)
    assert ledger.counts["upstream-attributed rows"] == 2
    # ...and it is broken out BY PROJECT, because a credit line cannot be
    # written from an opaque total.
    assert ledger.counts["  legesher-translations"] == 1
    assert ledger.counts["  UniversalPython"] == 1
    assert ledger.counts["superseded-by-review rows"] == 2
    assert ledger.counts["endorsements"] == 3


# ---------------------------------------------------------------------------
# FIX 4 -- no name fragment rides into the corpus layer
# ---------------------------------------------------------------------------


def test_superseded_rows_carry_a_neutral_source_detail(
    v1_db: Path, tmp_path: Path
) -> None:
    """The rejected-word rows must not carry `reviewer_zh_review_old` into the corpus.

    `option_provenance` is a CORPUS-layer table with no publish gate over it,
    and the schema's contract is that `contributors.id` is the ONLY identity
    column the corpus exports. The v1 label embeds a first name, so it stays on
    the private side (SUPERSEDED_BY_REVIEW); the row gets the neutral label.
    """
    conn = _run(v1_db, tmp_path)
    details = [
        r["source_detail"]
        for r in conn.execute(
            "SELECT source_detail FROM option_provenance WHERE source_detail = ?",
            (SUPERSEDED_SOURCE_DETAIL,),
        )
    ]
    assert len(details) == 2  # the two `_old` rows in the fixture

    # No name fragment anywhere in the corpus-layer provenance.
    leaked = conn.execute(
        "SELECT COUNT(*) FROM option_provenance "
        "WHERE source_detail LIKE '%reviewer%' OR source_detail LIKE '%alt_ur%'"
    ).fetchone()[0]
    assert leaked == 0
    conn.close()


# ---------------------------------------------------------------------------
# FIX 5 -- the artifact records which salt minted it
# ---------------------------------------------------------------------------


def test_build_meta_records_the_salt_fingerprint(v1_db: Path, tmp_path: Path) -> None:
    """A built DB carries sha256(salt)[:16], so the push script can verify the
    artifact was minted with the escrowed salt -- nothing else in the file
    records which salt produced its contributor ids."""
    conn = _run(v1_db, tmp_path)
    meta = {
        r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM build_meta")
    }
    assert meta["salt_fingerprint"] == salt_fingerprint(SALT)
    assert meta["salt_fingerprint"] != salt_fingerprint("some-other-salt")
    assert meta["publish_build"] == "0"
    conn.close()


# ---------------------------------------------------------------------------
# definition_en seeding from the context briefs (CORE-1312)
# ---------------------------------------------------------------------------


def test_definition_from_brief_extracts_the_quick_summary(tmp_path: Path) -> None:
    brief = tmp_path / "elif.md"
    brief.write_text(
        "# Python Keyword: `elif` - Translation Brief (Tier 1)\n\n"
        "**Category:** keyword\n\n---\n\n"
        "## Quick Summary\n\n"
        "The `elif` keyword provides additional conditional branches.\n"
        "It tests an alternative condition.\n\n"
        "---\n\n## Code Examples\n",
        encoding="utf-8",
    )
    assert definition_from_brief("elif", tmp_path) == (
        "The `elif` keyword provides additional conditional branches."
        " It tests an alternative condition."
    )


def test_definition_from_brief_missing_file_or_section(tmp_path: Path) -> None:
    assert definition_from_brief("nonexistent", tmp_path) is None
    no_section = tmp_path / "break.md"
    no_section.write_text("# break\n\nProse without the heading.\n", encoding="utf-8")
    assert definition_from_brief("break", tmp_path) is None


def test_definition_from_brief_reads_the_real_briefs() -> None:
    """The shipped briefs actually seed: elif must resolve to real prose,
    not remain a TODO placeholder in the published corpus."""
    text = definition_from_brief("elif")
    assert text is not None
    assert "elif" in text
    assert not text.startswith("TODO")


# ---------------------------------------------------------------------------
# Multi-target v1: concepts merge on slug; terms and canon stay per-PL
# ---------------------------------------------------------------------------


def test_shared_terms_merge_into_one_concept(v1_db: Path, tmp_path: Path) -> None:
    """python `break` + javascript `break` = ONE concept, two terms rows."""
    conn = _run(v1_db, tmp_path)
    assert (
        conn.execute("SELECT COUNT(*) FROM concepts WHERE slug='break'").fetchone()[0]
        == 1
    )
    rows = conn.execute(
        "SELECT programming_language FROM terms t JOIN concepts c "
        "ON c.id=t.concept_id WHERE c.slug='break' ORDER BY 1"
    ).fetchall()
    assert [r["programming_language"] for r in rows] == ["javascript", "python"]
    # both PLs exist in the reference table, with python as the shipping target
    pls = dict(
        conn.execute("SELECT code, status FROM programming_languages").fetchall()
    )
    assert pls == {"python": "shipping", "javascript": "in_progress"}
    conn.close()


def test_canon_selections_are_pl_scoped(v1_db: Path, tmp_path: Path) -> None:
    """A v1 selection belongs to its term's target — divergent per-PL picks
    (real case: abs -> different Arabic renderings per target) must coexist."""
    src = sqlite3.connect(v1_db)
    # A selection must exist as a candidate first (the migration hard-errors
    # on a selected value absent from the corpus).
    src.executemany(
        "INSERT INTO translations (term_id, language_code, translation, source, "
        "created_by, created_at) VALUES (?, 'ur', ?, 'aya', 'ai-aya', "
        "'2026-03-19T00:00:00')",
        [(3, "توڑو"), (5, "روکو")],
    )
    src.executemany(
        "INSERT INTO selected_translations (term_id, language_code, translation, "
        "selected_by, selected_at, selection_reason) VALUES (?, 'ur', ?, "
        "'quality_review', '2026-03-20T00:00:00', 'test')",
        [(3, "توڑو"), (5, "روکو")],  # python break vs javascript break: divergent
    )
    src.commit()
    src.close()
    conn = _run(v1_db, tmp_path)
    rows = conn.execute(
        "SELECT pl_scope, surface_form FROM canon_selections cs "
        "JOIN concepts c ON c.id=cs.concept_id WHERE c.slug='break' ORDER BY 1"
    ).fetchall()
    assert [(r["pl_scope"], r["surface_form"]) for r in rows] == [
        ("javascript", "روکو"),
        ("python", "توڑو"),
    ]
    conn.close()


def test_one_token_two_constructs_splits_into_secondary_concept(
    v1_db: Path, tmp_path: Path
) -> None:
    """python `type` (builtin + 3.12 soft keyword) = two concepts sharing a
    spelling: category-suffixed slug, second terms row export_role='secondary'
    (the branch the real publish build executes)."""
    conn = _run(v1_db, tmp_path)
    slugs = {
        r["slug"]
        for r in conn.execute("SELECT slug FROM concepts WHERE slug LIKE 'type%'")
    }
    assert slugs == {"type", "type-keyword"}
    rows = conn.execute(
        "SELECT c.slug, t.category, t.export_role FROM terms t "
        "JOIN concepts c ON c.id = t.concept_id WHERE t.name='type' ORDER BY t.id"
    ).fetchall()
    assert [(r["slug"], r["category"], r["export_role"]) for r in rows] == [
        ("type", "builtin_type", "primary"),
        ("type-keyword", "keyword", "secondary"),
    ]
    conn.close()


def test_same_token_selections_land_on_their_distinct_concepts(
    v1_db: Path, tmp_path: Path
) -> None:
    """51 real locales picked different words for type-the-builtin vs
    type-the-keyword — both selections must survive, one per concept."""
    src = sqlite3.connect(v1_db)
    src.executemany(
        "INSERT INTO translations (term_id, language_code, translation, source, "
        "created_by, created_at) VALUES (?, 'ur', ?, 'aya', 'ai-aya', "
        "'2026-03-19T00:00:00')",
        [(6, "قسم_بلٹ_ان"), (7, "قسم_کلیدی")],
    )
    src.executemany(
        "INSERT INTO selected_translations (term_id, language_code, translation, "
        "selected_by, selected_at, selection_reason) VALUES (?, 'ur', ?, "
        "'quality_review', '2026-03-20T00:00:00', 'test')",
        [(6, "قسم_بلٹ_ان"), (7, "قسم_کلیدی")],
    )
    src.commit()
    src.close()
    conn = _run(v1_db, tmp_path)
    rows = conn.execute(
        "SELECT c.slug, cs.surface_form FROM canon_selections cs "
        "JOIN concepts c ON c.id = cs.concept_id WHERE c.slug LIKE 'type%' "
        "ORDER BY c.slug"
    ).fetchall()
    assert [(r["slug"], r["surface_form"]) for r in rows] == [
        ("type", "قسم_بلٹ_ان"),
        ("type-keyword", "قسم_کلیدی"),
    ]
    conn.close()


def test_definition_precedence_and_ledger_counts(v1_db: Path, tmp_path: Path) -> None:
    """Three precedence branches through migrate() itself: the v1 description
    wins over the brief; the brief seeds when the description is NULL; the
    explicit TODO marker survives when both are missing. The ledger counts pin
    the split."""
    src = sqlite3.connect(v1_db)
    src.executescript(
        """
        INSERT INTO terms (id, name, programming_language, category, description)
            VALUES (8, 'zzz_nobrief', 'python', 'keyword', NULL);
        INSERT INTO terms (id, name, programming_language, category, description)
            VALUES (9, 'elif', 'python', 'keyword', 'the v1 description wins');
        """
    )
    src.commit()
    src.close()
    target = tmp_path / "v2.db"
    ledger = migrate(v1_db, target, salt=SALT)
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row

    def definition(slug: str) -> str:
        return conn.execute(
            "SELECT definition_en FROM concepts WHERE slug=?", (slug,)
        ).fetchone()["definition_en"]

    assert definition("elif") == "the v1 description wins"
    assert definition("zzz-nobrief") == "TODO: seed from context/python/zzz_nobrief.md"
    assert not definition("break").startswith("TODO")  # seeded from the brief
    # Fixture concepts: True/False/break/None/type/type-keyword all seed from
    # real briefs, elif from its description -> 7 seeded; zzz_nobrief -> 1 TODO.
    assert ledger.counts["definitions_seeded"] == 7
    assert ledger.counts["definitions_todo"] == 1
    conn.close()


def test_concept_briefs_rows_only_for_existing_files(
    v1_db: Path, tmp_path: Path
) -> None:
    """No dangling Tier-1 brief claims: rows exist only for briefs on disk,
    with the filesystem-safe stem in the recorded path."""
    src = sqlite3.connect(v1_db)
    src.execute(
        "INSERT INTO terms (id, name, programming_language, category)"
        " VALUES (8, 'zzz_nobrief', 'python', 'keyword')"
    )
    src.commit()
    src.close()
    conn = _run(v1_db, tmp_path)
    paths = [
        r["path"] for r in conn.execute("SELECT path FROM concept_briefs ORDER BY path")
    ]
    i18n_root = Path(__file__).resolve().parents[1]
    for path in paths:
        on_disk = i18n_root / path.removeprefix("libs/i18n/")
        assert on_disk.is_file(), f"dangling brief claim: {path}"
    assert not any("zzz_nobrief" in p for p in paths)
    conn.close()


def test_definition_from_brief_star_stem_and_empty_section(tmp_path: Path) -> None:
    """The `*` -> `_star` stem mapping, the unsafe-name guard, and the
    empty-Quick-Summary branch (must yield None, never a later section)."""
    real = definition_from_brief("except*")  # against the shipped briefs
    assert real is not None and not real.startswith("TODO")

    star = tmp_path / "x_star.md"
    star.write_text("## Quick Summary\n\nMapped fine.\n", encoding="utf-8")
    assert definition_from_brief("x*", tmp_path) == "Mapped fine."

    empty = tmp_path / "empty.md"
    empty.write_text(
        "## Quick Summary\n\n---\n\n## Code Examples\n\n```python\nx = 1\n```\n",
        encoding="utf-8",
    )
    assert definition_from_brief("empty", tmp_path) is None

    (tmp_path / "evil.md").write_text("## Quick Summary\n\nnope\n", encoding="utf-8")
    assert definition_from_brief("../evil", tmp_path / "sub") is None


def test_unknown_pl_seeds_with_planned_status(v1_db: Path, tmp_path: Path) -> None:
    """A third PL landing in v1 terms gets the fallback: title-cased name,
    status 'planned'."""
    src = sqlite3.connect(v1_db)
    src.execute(
        "INSERT INTO terms (id, name, programming_language, category)"
        " VALUES (30, 'match', 'rust', 'keyword')"
    )
    src.commit()
    src.close()
    conn = _run(v1_db, tmp_path)
    row = conn.execute(
        "SELECT name, status FROM programming_languages WHERE code='rust'"
    ).fetchone()
    assert (row["name"], row["status"]) == ("Rust", "planned")
    conn.close()


# ---------------------------------------------------------------------------
# CORE-1679 -- the messages partition is NOT migrated, and that gap is loud
# ---------------------------------------------------------------------------


def _activate_and_seed_messages(v1: Path) -> None:
    """Give the fixture the messages partition with one seeded row."""
    conn = sqlite3.connect(v1)
    conn.executescript(
        """
        CREATE TABLE message_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT, implementation TEXT NOT NULL,
            key TEXT NOT NULL, template_en TEXT NOT NULL, placeholders TEXT,
            matcher TEXT, concept_id INTEGER, version_added TEXT,
            version_removed TEXT
        );
        INSERT INTO message_templates (implementation, key, template_en)
        VALUES ('cpython', 'ZeroDivisionError.division_by_zero', 'division by zero');
        """
    )
    conn.commit()
    conn.close()


def test_source_with_message_rows_is_refused_without_acknowledgement(
    v1_db: Path, tmp_path: Path
) -> None:
    """The v2 build would silently start without the CORE-1679 message rows;
    the migration must refuse rather than let that happen unnoticed."""
    _activate_and_seed_messages(v1_db)
    with pytest.raises(SystemExit, match="message_templates"):
        migrate(v1_db, tmp_path / "v2.db", salt=SALT)
    assert not (tmp_path / "v2.db").exists()  # refused BEFORE building


def test_source_with_message_rows_proceeds_with_acknowledgement(
    v1_db: Path, tmp_path: Path
) -> None:
    _activate_and_seed_messages(v1_db)
    conn = _run(v1_db, tmp_path, acknowledge_message_rows_not_migrated=True)
    # The v2 build's partition starts EMPTY (re-seed via seed_message_templates.py).
    assert conn.execute("SELECT COUNT(*) FROM message_templates").fetchone()[0] == 0
    conn.close()


def test_source_without_message_partition_needs_no_acknowledgement(
    v1_db: Path, tmp_path: Path
) -> None:
    conn = _run(v1_db, tmp_path)  # the pre-CORE-1679 shape keeps working
    conn.close()


# CORE-1355 -- the migration populates canon_selections.identity_ok
# ---------------------------------------------------------------------------


def test_identity_translations_carry_identity_ok(v1_db: Path, tmp_path: Path) -> None:
    """Canon rows whose surface equals the English term (case/NFKC-insensitive)
    carry identity_ok = 1; all others 0. Latin-script locale: the script gate
    would refuse Latin cognates for `ur`."""
    conn = sqlite3.connect(v1_db)
    conn.execute(
        "INSERT INTO languages (code, name, native_name, bcp47, direction, "
        "has_case_distinction, status, in_registry) "
        "VALUES ('cs', 'Czech', 'čeština', 'cs', 'ltr', 1, 'experimental', 1)"
    )
    # (term_id, surface): break -> break (identity), None -> none (identity
    # via casefold), True -> pravda (translated)
    for term_id, surface in [(3, "break"), (4, "none"), (1, "pravda")]:
        conn.execute(
            "INSERT INTO translations (term_id, language_code, translation, "
            "source, created_by, created_at) "
            "VALUES (?, 'cs', ?, 'aya', 'ai-aya', '2026-03-19T00:00:00')",
            (term_id, surface),
        )
        conn.execute(
            "INSERT INTO selected_translations (term_id, language_code, "
            "translation, selected_by, selected_at, selection_reason) "
            "VALUES (?, 'cs', ?, 'universal_python', '2026-03-19T00:00:00', 'test')",
            (term_id, surface),
        )
    conn.commit()
    conn.close()

    v2 = _run(v1_db, tmp_path)
    got = {
        row["surface_form"]: row["identity_ok"]
        for row in v2.execute(
            "SELECT surface_form, identity_ok FROM canon_selections WHERE locale = 'cs'"
        )
    }
    assert got == {"break": 1, "none": 1, "pravda": 0}


# ---------------------------------------------------------------------------
# Withdrawal is an erasure that survives a rebuild (CORE-1780)
# ---------------------------------------------------------------------------


def test_a_withdrawn_contributor_keeps_their_endorsements_and_loses_their_identity(
    v1_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The promise in CONTRIBUTOR_PRIVACY.md, enforced where it can actually hold.

    This map is source code and is re-read on every rebuild, so it -- not the
    built database -- is where a withdrawal has to be recorded. Editing the
    built artifact would be undone by the next migration, and dropping the entry
    outright makes `resolve_identity` refuse the whole build.

    So the entry stays and the USERNAME goes, replaced by the opaque id it
    already minted. Both halves of the promise are asserted below: the evidence
    survives, the person does not.
    """
    from scripts import migrate_to_v2

    # The id this person already has in the published corpus. Under a withdrawal
    # it is copied into the map verbatim -- there is no username left to mint it
    # from, which is precisely what makes the erasure stick.
    withdrawn_id = contributor_id("alt_reviewer", salt=GOOD_SALT)
    monkeypatch.setitem(
        migrate_to_v2.CONTRIBUTOR_IDENTITY_MAP,
        "alt_ur_modern",
        migrate_to_v2.Withdrawn(withdrawn_id, "2026-08-10"),
    )
    # The test salt mints different ids than the published corpus, so the
    # published-id gate is pointed at this run's id. The gate itself is tested
    # separately, including against the shipped map.
    monkeypatch.setattr(
        migrate_to_v2, "PUBLISHED_CONTRIBUTOR_IDS", frozenset({withdrawn_id})
    )

    target = tmp_path / "v2.db"
    ledger = migrate(v1_db, target, salt=GOOD_SALT, publish=True)

    # A withdrawal is a decision, not an open question: it must not read as an
    # unresolved identity, which would refuse the build outright.
    assert ledger.counts["  UNRESOLVED identities"] == 0
    assert ledger.counts["contributors (people)"] == 3

    db = sqlite3.connect(target)

    # 1. The person is gone. Every column that could lead back to them is NULL,
    #    and the tombstone says a withdrawal happened rather than leaving a row
    #    indistinguishable from a contributor we never met.
    row = db.execute(
        "SELECT source_key, display_name, github_handle, contact, email, withdrawn_at "
        "FROM contributor_identities WHERE contributor_id = ?",
        (withdrawn_id,),
    ).fetchone()
    assert row is not None, "the tombstone row must exist"
    assert row[:5] == (None, None, None, None, None)
    assert row[5] == "2026-08-10"

    # 2. Their username survives NOWHERE in the built database -- not in the
    #    identity table, not in provenance, not in a stray label.
    assert (
        db.execute(
            "SELECT COUNT(*) FROM contributor_identities WHERE source_key = 'alt_reviewer'"
        ).fetchone()[0]
        == 0
    )

    # 3. Their evidence is intact. This is the half that is easy to get wrong:
    #    deleting the endorsements would silently move which word a pack ships,
    #    for everyone, on the strength of one person's privacy request.
    assert (
        db.execute(
            "SELECT COUNT(*) FROM endorsements WHERE contributor_id = ?",
            (withdrawn_id,),
        ).fetchone()[0]
        > 0
    )
    db.close()


def test_withdrawal_does_not_change_what_the_corpus_publishes(
    v1_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No published value changes when someone withdraws.

    The earlier version of this test compared ledger COUNTS, which are invariant
    under the one mistake this procedure can actually make -- a wrong
    ``Withdrawn.contributor_id``. Counts stay identical while the published id
    set silently changes, so it asserted nothing about the claim it names.
    ``contributor_id`` is a published column; compare the ids themselves.
    """
    from scripts import migrate_to_v2

    def published_ids(db_path: Path) -> set[str]:
        db = sqlite3.connect(db_path)
        try:
            return {r[0] for r in db.execute("SELECT id FROM contributors")}
        finally:
            db.close()

    before_path = tmp_path / "before.db"
    before = migrate(v1_db, before_path, salt=GOOD_SALT, publish=True)

    monkeypatch.setitem(
        migrate_to_v2.CONTRIBUTOR_IDENTITY_MAP,
        "alt_ur_modern",
        migrate_to_v2.Withdrawn(
            contributor_id("alt_reviewer", salt=GOOD_SALT), "2026-08-10"
        ),
    )
    monkeypatch.setattr(
        migrate_to_v2,
        "PUBLISHED_CONTRIBUTOR_IDS",
        frozenset({contributor_id("alt_reviewer", salt=GOOD_SALT)}),
    )
    after_path = tmp_path / "after.db"
    after = migrate(v1_db, after_path, salt=GOOD_SALT, publish=True)

    assert published_ids(before_path) == published_ids(after_path)
    for key in ("options", "endorsements", "contributors (people)"):
        assert before.counts[key] == after.counts[key], key


def test_publish_refuses_a_withdrawn_id_the_corpus_has_never_published(
    v1_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The gate that stands in for a check the migration cannot make itself.

    A withdrawal carries an id that cannot be recomputed -- the username is
    gone. A typo therefore re-keys a real person's published endorsements to an
    id belonging to nobody, silently, and the counts do not move. Every other
    one-way door here hard-fails; so does this one.
    """
    from scripts import migrate_to_v2

    monkeypatch.setitem(
        migrate_to_v2.CONTRIBUTOR_IDENTITY_MAP,
        "alt_ur_modern",
        migrate_to_v2.Withdrawn("c_0000000000000000", "2026-08-10"),
    )
    target = tmp_path / "v2.db"
    with pytest.raises(SystemExit, match="not one this corpus has published"):
        migrate(v1_db, target, salt=GOOD_SALT, publish=True)
    assert not target.exists(), "the refusal must fire before anything is built"


def test_a_half_converted_person_is_refused_by_name_not_by_traceback(
    v1_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One person, two v1 labels, only one withdrawn.

    The labels are per-review-round, so a person can hold several. Converting
    some and not others leaves their username in the ones left behind -- an
    incomplete erasure. Previously this died on a raw UNIQUE constraint naming
    neither the person nor the labels.
    """
    from scripts import migrate_to_v2

    shared = contributor_id("alt_reviewer", salt=GOOD_SALT)
    monkeypatch.setitem(
        migrate_to_v2.CONTRIBUTOR_IDENTITY_MAP,
        "reviewer_ur_review",
        migrate_to_v2.Withdrawn(shared, "2026-08-10"),
    )
    monkeypatch.setattr(migrate_to_v2, "PUBLISHED_CONTRIBUTOR_IDS", frozenset({shared}))
    with pytest.raises(SystemExit, match="claimed by two entries"):
        migrate(v1_db, tmp_path / "v2.db", salt=GOOD_SALT, publish=True)


def test_the_shipped_map_only_withdraws_published_ids() -> None:
    """Guards the real map, which the monkeypatching tests above cannot."""
    from scripts import migrate_to_v2

    migrate_to_v2.require_published_withdrawal_ids()


def test_pre_notice_consent_is_recorded_and_grants_nothing(
    v1_db: Path, tmp_path: Path
) -> None:
    """Everyone in the v1 data contributed before the notice existed.

    Three answers were possible and only one is true. NULL says nobody ever
    agreed to anything; `1.0` claims they accepted a document that did not
    exist; `oss-pre-notice` says what happened. The test pins the third, and
    pins that recording it changed nothing about how they are treated.
    """
    from scripts import migrate_to_v2

    target = tmp_path / "v2.db"
    migrate(v1_db, target, salt=GOOD_SALT, publish=True)
    db = sqlite3.connect(target)

    rows = db.execute(
        "SELECT consent_version, credit_preference, consent_public_credit, consent_at "
        "FROM contributor_identities WHERE source_key IS NOT NULL"
    ).fetchall()
    assert rows, "the fixture must mint at least one resolved contributor"

    for version, preference, public_credit, consent_at in rows:
        assert version == migrate_to_v2.PRE_NOTICE_CONSENT
        # It is a record, not a grant: nothing about them becomes publishable.
        assert preference == "anonymous"
        assert public_credit == 0
        # Dated to their work, not to the build -- a fresh timestamp would read
        # as a fresh agreement.
        assert consent_at is not None

    # An `unresolved:` key is one label standing for two people; neither of them
    # consented to anything as that row, so it must stay blank.
    unresolved = db.execute(
        "SELECT consent_version FROM contributor_identities "
        "WHERE source_key LIKE 'unresolved:%'"
    ).fetchall()
    assert all(v is None for (v,) in unresolved)
    db.close()


def test_withdrawal_clears_the_consent_it_revoked(
    v1_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A tombstone must not keep asserting consent the person took back."""
    from scripts import migrate_to_v2

    withdrawn_id = contributor_id("alt_reviewer", salt=GOOD_SALT)
    monkeypatch.setitem(
        migrate_to_v2.CONTRIBUTOR_IDENTITY_MAP,
        "alt_ur_modern",
        migrate_to_v2.Withdrawn(withdrawn_id, "2026-08-10"),
    )
    monkeypatch.setattr(
        migrate_to_v2, "PUBLISHED_CONTRIBUTOR_IDS", frozenset({withdrawn_id})
    )
    target = tmp_path / "v2.db"
    migrate(v1_db, target, salt=GOOD_SALT, publish=True)

    db = sqlite3.connect(target)
    version, consent_at, withdrawn_at = db.execute(
        "SELECT consent_version, consent_at, withdrawn_at FROM contributor_identities "
        "WHERE contributor_id = ?",
        (withdrawn_id,),
    ).fetchone()
    assert version is None and consent_at is None
    assert withdrawn_at == "2026-08-10"
    db.close()


# ---------------------------------------------------------------------------
# CORE-1794 -- the identity maps load from the private data home
# ---------------------------------------------------------------------------


def _write_map(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_load_identity_maps_round_trips_the_data_home_json(tmp_path: Path) -> None:
    """The JSON contract: identities, withdrawn, superseded_by_review."""
    j = _write_map(
        tmp_path / "map.json",
        {
            "identities": {
                "reviewer_zh_review": {
                    "github_handle": "zh_reviewer",
                    "display_name": "Reviewer Zh",
                    "note": "zh review",
                },
                "open_label": {"github_handle": None},
            },
            "withdrawn": {
                "gone_label": {
                    "contributor_id": "c_0000000000000000",
                    "withdrawn_at": "2026-08-10",
                }
            },
            "superseded_by_review": {"reviewer_zh_review_old": "reviewer_zh_review"},
        },
    )
    load_identity_maps(j)
    assert CONTRIBUTOR_IDENTITY_MAP["reviewer_zh_review"] == Identity(
        "zh_reviewer", "Reviewer Zh", "zh review"
    )
    assert not CONTRIBUTOR_IDENTITY_MAP["open_label"].resolved
    gone = CONTRIBUTOR_IDENTITY_MAP["gone_label"]
    assert isinstance(gone, Withdrawn) and gone.resolved
    assert gone.source_key("gone_label") == "c_0000000000000000"
    assert SUPERSEDED_BY_REVIEW == {"reviewer_zh_review_old": "reviewer_zh_review"}


def test_load_identity_maps_missing_file_leaves_maps_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The documented fail-loud contract: no data home, EMPTY maps, no guess."""
    monkeypatch.delenv("LEGESHER_IDENTITY_MAP", raising=False)
    monkeypatch.delenv("LEGESHER_DATA_REPO", raising=False)
    load_identity_maps(tmp_path / "absent.json")
    assert CONTRIBUTOR_IDENTITY_MAP == {} and SUPERSEDED_BY_REVIEW == {}
    load_identity_maps()  # no path, no env: same outcome
    assert CONTRIBUTOR_IDENTITY_MAP == {} and SUPERSEDED_BY_REVIEW == {}


def test_load_identity_maps_env_resolution_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """$LEGESHER_IDENTITY_MAP (direct file) outranks $LEGESHER_DATA_REPO."""
    repo = tmp_path / "data-repo"
    (repo / "identity").mkdir(parents=True)
    _write_map(
        repo / "identity" / "contributor_identity_map.json",
        {"identities": {"from_repo": {"github_handle": "repo_person"}}},
    )
    direct = _write_map(
        tmp_path / "direct.json",
        {"identities": {"from_direct": {"github_handle": "direct_person"}}},
    )

    monkeypatch.delenv("LEGESHER_IDENTITY_MAP", raising=False)
    monkeypatch.setenv("LEGESHER_DATA_REPO", str(repo))
    load_identity_maps()
    assert set(CONTRIBUTOR_IDENTITY_MAP) == {"from_repo"}

    monkeypatch.setenv("LEGESHER_IDENTITY_MAP", str(direct))
    load_identity_maps()
    assert set(CONTRIBUTOR_IDENTITY_MAP) == {"from_direct"}


def test_unknown_label_error_names_the_data_home_when_the_map_is_empty() -> None:
    """The designed first-contact failure for a clone without the data home."""
    CONTRIBUTOR_IDENTITY_MAP.clear()
    with pytest.raises(SystemExit, match="identity map is EMPTY"):
        resolve_identity("anyone_2027")
    # And the hint does NOT appear when the map is populated -- the label is
    # then genuinely unknown, which is a different problem.
    CONTRIBUTOR_IDENTITY_MAP.update(TEST_IDENTITIES)
    with pytest.raises(SystemExit, match="unknown v1 created_by label") as exc:
        resolve_identity("anyone_2027")
    assert "identity map is EMPTY" not in str(exc.value)


def test_load_identity_maps_rejects_malformed_entries(tmp_path: Path) -> None:
    """A misspelt key must fail at load, not surface later as 'unresolved'."""
    with pytest.raises(SystemExit, match="github_handle"):
        load_identity_maps(
            _write_map(
                tmp_path / "bad-identity.json",
                {"identities": {"label": {"handle": "wrong-key-name"}}},
            )
        )
    with pytest.raises(SystemExit, match="contributor_id"):
        load_identity_maps(
            _write_map(
                tmp_path / "bad-withdrawn.json",
                {"withdrawn": {"label": {"withdrawn_at": "2026-08-10"}}},
            )
        )


def test_load_identity_maps_enforces_cross_map_consistency(tmp_path: Path) -> None:
    """A label cannot be two things, and a displaced label needs a person."""
    with pytest.raises(SystemExit, match="not a known identity"):
        load_identity_maps(
            _write_map(
                tmp_path / "dangling.json",
                {"superseded_by_review": {"x_old": "nobody"}},
            )
        )
    with pytest.raises(SystemExit, match="both 'identities' and 'withdrawn'"):
        load_identity_maps(
            _write_map(
                tmp_path / "both.json",
                {
                    "identities": {"label": {"github_handle": "person"}},
                    "withdrawn": {
                        "label": {
                            "contributor_id": "c_0000000000000000",
                            "withdrawn_at": "2026-08-10",
                        }
                    },
                },
            )
        )
    with pytest.raises(SystemExit, match="NON_HUMAN_CREATED_BY"):
        load_identity_maps(
            _write_map(
                tmp_path / "pipeline.json",
                {"identities": {"universal_python": {"github_handle": "person"}}},
            )
        )


def test_the_database_never_ships_in_built_artifacts() -> None:
    """The pdm exclude is privacy-gating (CORE-1794): pin it in pyproject.

    The wheel shipped the full database before this exclude existed. The build
    backend reads files from disk, not from git, so untracking alone does not
    keep a locally-present database out of an artifact -- the exclude does.
    """
    # tomllib is 3.11+; legesher-i18n declares tomli for older interpreters.
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[import-not-found, no-redef]

    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject.open("rb") as fh:
        build = tomllib.load(fh)["tool"]["pdm"]["build"]
    assert "legesher_i18n/db/translations.db*" in build["excludes"]
