"""Identity and provenance invariants of the v1 -> v2 migration (CORE-1501).

Three properties, each of which is a one-way door once the corpus is published:

* **who a contributor IS** -- the private source key is a GitHub username, not a
  first name; the `_old` twins are the words a review REJECTED and must never be
  endorsed; an ambiguous label is refused, never guessed at
* **the salt** -- publish mode hard-fails on a salt that cannot safely be frozen
* **the MIT obligation** -- the legacy rows carry their origin on the row

The migration builds a NEW database and never writes to the v1 source, so these
run against a synthetic v1 fixture rather than the real ``translations.db``.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from legesher_i18n.db.schema_v2 import (
    DEFAULT_CONTRIBUTOR_SALT,
    contributor_id,
    salt_fingerprint,
)
from scripts.migrate_to_v2 import (
    CONTRIBUTOR_IDENTITY_MAP,
    LEGACY_COMMUNITY_SOURCE_DETAIL,
    NON_HUMAN_CREATED_BY,
    SUPERSEDED_BY_REVIEW,
    SUPERSEDED_SOURCE_DETAIL,
    migrate,
    require_publishable_salt,
    resolve_identity,
)

SALT = "test-salt"

#: A salt that is long enough to be publishable (>= MIN_PUBLISH_SALT_LENGTH).
GOOD_SALT = "a" * 64

#: The v1 shape, reduced to what the identity logic reads. One term, one locale,
#: and one row per `created_by` class the migration must tell apart.
V1_ROWS = [
    # (term, translation, source, created_by)
    ("True", "真实", "community_review", "zh_reviewer_review"),  # her suggestion
    ("True", "真", "community_review", "zh_reviewer_review_old"),  # the word she REJECTED
    ("False", "نوعیت", "community_review", "ur_reviewer_review"),
    ("False", "قسم", "community_review", "ur_reviewer_review_old"),  # REJECTED
    (
        "break",
        "توڑ",
        "community_review",
        "alt_ur_modern",
    ),  # = @sarr266 (resolved 2026-07-14)
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
            id INTEGER PRIMARY KEY, name TEXT, category TEXT, subcategory TEXT,
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
        INSERT INTO terms (id, name, category) VALUES
            (1, 'True', 'special_constant'),
            (2, 'False', 'special_constant'),
            (3, 'break', 'keyword'),
            (4, 'None', 'special_constant');
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
    assert keys["NextME14"] == "NextME14"
    assert keys["rafaym1"] == "rafaym1"

    # The raw v1 labels are gone as keys...
    assert "zh_reviewer_review" not in keys
    assert "ur_reviewer_review" not in keys

    # ...and the published id is minted from the username, carrying no name.
    ids = {r["id"] for r in conn.execute("SELECT id FROM contributors")}
    assert contributor_id("NextME14", salt=SALT) in ids
    assert all("nextme14" not in i and "rafaym1" not in i for i in ids)
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
    (0/31) and `_new` is ALWAYS the shipped word (31/31); and `ur_reviewer_review_old`
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
        assert row["source"] == "import"  # the PACK's word, not the reviewer's
        assert row["contributor_id"] is None  # she did not propose it
        # Neutral label, NOT the v1 `<name>_review_old` label: the label embeds
        # a first name and option_provenance is corpus-layer. The audit trail
        # (which label, which review displaced it) lives privately in
        # SUPERSEDED_BY_REVIEW.
        assert row["source_detail"] == SUPERSEDED_SOURCE_DETAIL
    conn.close()


def test_the_sarr266_label_resolves_to_sarr266(v1_db: Path, tmp_path: Path) -> None:
    """`alt_ur_modern` is @sarr266 -- ONE person (Madison, 2026-07-14).

    The label looked like two names, and the ur CHANGELOG credits the review
    round to "@sarr266 & @rafaym1" jointly -- so the migration held these rows
    back rather than guess. Madison resolved it: "rafaym1" in the label names the
    pack her alternatives responded to, not a co-author. Her rows now mint
    endorsements like anyone else's, and no unresolved identity remains.
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
        "FROM contributor_identities ci WHERE ci.source_key = 'sarr266'"
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
    assert not (set(CONTRIBUTOR_IDENTITY_MAP) & NON_HUMAN_CREATED_BY)
    assert not (set(CONTRIBUTOR_IDENTITY_MAP) & set(SUPERSEDED_BY_REVIEW))
    assert not (set(SUPERSEDED_BY_REVIEW) & NON_HUMAN_CREATED_BY)
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
    assert prov["source"] == "import"
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
# FIX 3 -- the MIT obligation rides on the row
# ---------------------------------------------------------------------------


def test_legacy_community_rows_carry_their_mit_provenance(
    v1_db: Path, tmp_path: Path
) -> None:
    """The `community` rows came from legesher/legesher-translations (MIT, public).

    MIT permits relicensing but REQUIRES the copyright and permission notice be
    retained. Recording the origin ON THE ROW is what makes that obligation
    machine-visible -- a query, not folklore that survives only as long as the
    person who remembers it. The dataset card must carry the attribution.
    """
    conn = _run(v1_db, tmp_path)
    rows = conn.execute(
        "SELECT p.source, p.source_detail, p.contributor_id FROM option_provenance p "
        "WHERE p.source_detail = ?",
        (LEGACY_COMMUNITY_SOURCE_DETAIL,),
    ).fetchall()

    assert len(rows) == 1  # the one `community` row in the fixture
    assert rows[0]["source"] == "community"
    assert rows[0]["contributor_id"] is None  # no author, hence no endorsement

    # It is not a person: it mints no contributor and no endorsement.
    assert conn.execute("SELECT COUNT(*) FROM endorsements").fetchone()[0] == 3
    conn.close()


def test_the_migration_reports_the_attribution_row_count(
    v1_db: Path, tmp_path: Path
) -> None:
    """The obligation is counted in the ledger, so it cannot be shipped unnoticed."""
    ledger = migrate(v1_db, tmp_path / "v2.db", salt=SALT)
    assert ledger.counts["MIT-attributed rows"] == 1
    assert ledger.counts["superseded-by-review rows"] == 2
    assert ledger.counts["endorsements"] == 3


# ---------------------------------------------------------------------------
# FIX 4 -- no name fragment rides into the corpus layer
# ---------------------------------------------------------------------------


def test_superseded_rows_carry_a_neutral_source_detail(
    v1_db: Path, tmp_path: Path
) -> None:
    """The rejected-word rows must not carry `zh_reviewer_review_old` into the corpus.

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
        "WHERE source_detail LIKE '%nextme14%' OR source_detail LIKE '%rafaym1%' "
        "   OR source_detail LIKE '%sarr266%'"
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
