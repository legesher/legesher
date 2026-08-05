"""Publish-surface invariants of the HF corpus export (CORE-1505).

The export is a one-way door: the first push freezes the published keys, the
license posture, and -- if anything private leaks -- the leak. So the tests
here are about what must NEVER cross the boundary, not just what does:

* ``contributor_identities`` and ``canon_selections`` stay private, and the
  fixture deliberately CONTAINS a row of each so absence is proven, not assumed
* ``source_detail`` (real first names ride in it), ``display_name``,
  ``source_key`` and ``comment`` never survive into any Parquet file
* contributor ids are opaque ``c_`` + 16 hex tokens, nothing else
* endorsement counts are derivable from the published rows and match the
  ``endorsement_counts`` view -- derived, never stored
* ``--push`` without the CORE-1502 sign-off exits before writing anything
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
import types
from pathlib import Path

import pytest

from legesher_i18n.db.schema_v2 import (
    SCHEMA_V2_PATH,
    DEFAULT_CONTRIBUTOR_SALT,
    apply_schema_v2,
    contributor_id,
    endorsement_uid,
    option_uid,
    salt_fingerprint,
)
from scripts.export_corpus import (
    CONFIG_BASE_TABLE,
    CONFIG_SCHEMA,
    CONFIG_SQL,
    DEFAULT_TARGET_REPO,
    FORBIDDEN_COLUMNS,
    NEVER_EXPORT,
    PUSH_ALLOW_PATTERNS,
    TARGET_OVERRIDE_ENV_VAR,
    export_corpus,
    main,
    require_intended_target,
    require_publish_grade_db,
)

pa = pytest.importorskip("pyarrow")
pq = pytest.importorskip("pyarrow.parquet")

SALT = "test-salt"

#: Strings that exist in the fixture database's PRIVATE columns and must not
#: appear anywhere in the published files.
PRIVATE_STRINGS = (
    "alice-gh",  # contributor_identities.source_key / github_handle
    "Alice Realname",  # contributor_identities.display_name
    "alice@example.com",  # contributor_identities.email (CORE-1538 contact)
    "zh_reviewer_review",  # option_provenance.source_detail (a real first name)
    "great word, Alice!",  # endorsements.comment (free text, may carry PII)
)

CONTRIBUTOR_ALICE = contributor_id("alice-gh", salt=SALT)
CONTRIBUTOR_BOB = contributor_id("bob-gh", salt=SALT)

OPT_TRUE_UR = option_uid("true-constant", "ur", "سچ")
OPT_TRUE_ZH = option_uid("true-constant", "zh-Hans", "真")
OPT_FALSE_UR = option_uid("false-constant", "ur", "جھوٹ")  # withdrawn


@pytest.fixture
def v2_db(tmp_path: Path) -> Path:
    """A tiny synthetic v2 database exercising every boundary of the export.

    2 concepts, 2 locales (one with a script subtag), 3 options (one
    withdrawn), 2 contributors, 3 endorsements (one retracted, one carrying a
    free-text comment), validations on 2 of the 3 options, provenance rows
    including a ``source_detail`` with a real-looking first name, and -- the
    load-bearing part -- one ``canon_selections`` row and one
    ``contributor_identities`` row, so their absence downstream is a tested
    fact rather than a vacuous truth.
    """
    path = tmp_path / "v2.db"
    conn = sqlite3.connect(path)
    apply_schema_v2(conn)

    conn.execute(
        "INSERT INTO programming_languages (code, name, status) "
        "VALUES ('python', 'Python', 'shipping')"
    )
    conn.executemany(
        "INSERT INTO locales (tag, language_subtag, script_subtag, name, "
        "native_name, direction, in_registry) VALUES (?, ?, ?, ?, ?, ?, 1)",
        [
            ("ur", "ur", None, "Urdu", "اردو", "rtl"),
            ("zh-Hans", "zh", "Hans", "Chinese (Simplified)", "简体中文", "ltr"),
        ],
    )
    conn.executemany(
        "INSERT INTO concepts (id, slug, definition_en, category) VALUES (?, ?, ?, ?)",
        [
            (1, "true-constant", "The boolean truth value.", "value_literal"),
            (2, "false-constant", "The boolean false value.", "value_literal"),
        ],
    )
    conn.executemany(
        "INSERT INTO terms (concept_id, programming_language, name, category) "
        "VALUES (?, 'python', ?, 'keyword')",
        [(1, "True"), (2, "False")],
    )
    conn.executemany(
        "INSERT INTO contributors (id) VALUES (?)",
        [(CONTRIBUTOR_ALICE,), (CONTRIBUTOR_BOB,)],
    )
    # PRIVATE: the way back from the opaque id to a person. Never exported.
    conn.execute(
        "INSERT INTO contributor_identities (contributor_id, source_key, "
        "display_name, github_handle, email) VALUES (?, 'alice-gh', "
        "'Alice Realname', 'alice-gh', 'alice@example.com')",
        (CONTRIBUTOR_ALICE,),
    )
    conn.executemany(
        "INSERT INTO options (uid, concept_id, locale, surface_form, "
        "first_seen_at, withdrawn_at) VALUES (?, ?, ?, ?, ?, ?)",
        [
            (OPT_TRUE_UR, 1, "ur", "سچ", "2026-06-01T00:00:00", None),
            (OPT_TRUE_ZH, 1, "zh-Hans", "真", "2026-06-02T00:00:00", None),
            (
                OPT_FALSE_UR,
                2,
                "ur",
                "جھوٹ",
                "2026-06-03T00:00:00",
                "2026-06-20T00:00:00",
            ),
        ],
    )
    conn.executemany(
        "INSERT INTO option_validations (option_uid, validator_version, "
        "identifier_valid, nfkc_stable, script_consistent, collides_en_keyword, "
        "min_interpreter_ok) VALUES (?, 'py-identifier-v1', 1, 1, 1, 0, 1)",
        [(OPT_TRUE_UR,), (OPT_TRUE_ZH,)],
    )
    # Provenance: same rendering attested by a model AND by a person -- and the
    # community row's source_detail is a v1 reviewer label carrying a first
    # name, which is exactly what must not be published.
    conn.executemany(
        "INSERT INTO option_provenance (option_uid, source, source_detail, "
        "model_version, contributor_id) VALUES (?, ?, ?, ?, ?)",
        [
            (OPT_TRUE_UR, "model", "aya", "aya-101", None),
            (OPT_TRUE_UR, "community", "zh_reviewer_review", None, CONTRIBUTOR_ALICE),
            (OPT_TRUE_ZH, "import", "yaml_pack", None, None),
        ],
    )
    endorsement_rows = [
        (OPT_TRUE_UR, CONTRIBUTOR_ALICE, "portal", "contributor", None, None),
        (
            OPT_TRUE_UR,
            CONTRIBUTOR_BOB,
            "survey",
            "native_verified",
            "great word, Alice!",  # free text: may carry PII, never exported
            None,
        ),
        (
            OPT_TRUE_ZH,
            CONTRIBUTOR_ALICE,
            "portal",
            "contributor",
            None,
            "2026-07-01T00:00:00",  # retracted
        ),
    ]
    for index, (opt, person, method, rung, comment, retracted) in enumerate(
        endorsement_rows
    ):
        created = f"2026-06-1{index}T00:00:00"
        conn.execute(
            "INSERT INTO endorsements (uid, option_uid, contributor_id, method, "
            "rung_at_endorsement, comment, created_at, retracted_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                endorsement_uid(opt, person, method, created),
                opt,
                person,
                method,
                rung,
                comment,
                created,
                retracted,
            ),
        )
    # PRIVATE: the maintainer decision. Never exported.
    conn.execute(
        "INSERT INTO canon_selections (concept_id, locale, option_uid, "
        "surface_form, status, source_file) "
        "VALUES (1, 'ur', ?, 'سچ', 'machine', 'libs/i18n/canon/ur.toml')",
        (OPT_TRUE_UR,),
    )
    conn.commit()
    conn.close()
    return path


@pytest.fixture
def exported(v2_db: Path, tmp_path: Path) -> Path:
    """Run the export once and return the output directory."""
    out = tmp_path / "corpus"
    export_corpus(v2_db, out)
    return out


def _read(exported: Path, config: str) -> dict[str, list[object]]:
    """Load one config's Parquet file as plain Python columns."""
    return pq.read_table(exported / "data" / f"{config}.parquet").to_pydict()


# ---------------------------------------------------------------------------
# The five configs exist and reconcile with the database
# ---------------------------------------------------------------------------


def test_export_emits_the_five_corpus_configs(exported: Path) -> None:
    """One Parquet file per config, and the ledger's counts are the files'."""
    expected_rows = {
        "concepts": 2,
        "terms": 2,
        "options": 3,
        "endorsements": 3,
        "contributors": 2,
    }
    ledger = json.loads((exported / "reconciliation.json").read_text())
    assert set(ledger["configs"]) == set(expected_rows) == set(CONFIG_SQL)
    assert ledger["ok"] is True

    for config, rows in expected_rows.items():
        parquet_path = exported / "data" / f"{config}.parquet"
        assert parquet_path.exists()
        assert pq.read_table(parquet_path).num_rows == rows
        assert ledger["configs"][config] == {"db_rows": rows, "parquet_rows": rows}


def test_options_carry_validations_and_aggregated_sources(exported: Path) -> None:
    """The options config joins the validation cache and the provenance kinds.

    The withdrawn, unvalidated option is still published (append-only corpus:
    a bad option is evidence) with null validation columns and its
    ``withdrawn_at`` visible.
    """
    options = _read(exported, "options")
    for column in (
        "identifier_valid",
        "nfkc_stable",
        "script_consistent",
        "collides_en_keyword",
        "min_interpreter_ok",
        "validator_version",
        "checked_at",
    ):
        assert column in options

    by_uid = {uid: index for index, uid in enumerate(options["option_uid"])}
    assert set(by_uid) == {OPT_TRUE_UR, OPT_TRUE_ZH, OPT_FALSE_UR}

    # Two provenance kinds collapse into one sources list; detail stays home.
    assert options["sources"][by_uid[OPT_TRUE_UR]] == ["community", "model"]
    assert options["sources"][by_uid[OPT_TRUE_ZH]] == ["import"]
    assert options["sources"][by_uid[OPT_FALSE_UR]] == []

    validated = by_uid[OPT_TRUE_UR]
    assert options["identifier_valid"][validated] is True
    assert options["collides_en_keyword"][validated] is False
    assert options["validator_version"][validated] == "py-identifier-v1"

    withdrawn = by_uid[OPT_FALSE_UR]
    assert options["withdrawn_at"][withdrawn] == "2026-06-20T00:00:00"
    assert options["identifier_valid"][withdrawn] is None
    assert options["validator_version"][withdrawn] is None


def test_schemas_are_pinned_not_inferred(exported: Path) -> None:
    """Every published column carries its declared Arrow type, never `null`.

    Inference types a column from the data it happens to hold, so an all-NULL
    column (``concepts.definition_source`` in this fixture) would export as
    Arrow type ``null`` and flip to ``string`` the moment data arrives --
    schema drift across HF revisions. The pinned CONFIG_SCHEMA is the
    contract; the flags are real booleans, not SQLite's 0/1.
    """
    for config in CONFIG_SQL:
        schema = pq.read_table(exported / "data" / f"{config}.parquet").schema
        assert schema.names == [column for column, _ in CONFIG_SCHEMA[config]]
        for field in schema:
            assert field.type != pa.null(), f"{config}.{field.name} inferred as null"

    concepts = pq.read_table(exported / "data" / "concepts.parquet").schema
    assert concepts.field("definition_source").type == pa.string()  # all-NULL

    options = pq.read_table(exported / "data" / "options.parquet").schema
    assert options.field("identifier_valid").type == pa.bool_()
    assert options.field("sources").type == pa.list_(pa.string())


# ---------------------------------------------------------------------------
# Nothing private crosses the boundary
# ---------------------------------------------------------------------------


def test_no_forbidden_column_survives_in_any_parquet(exported: Path) -> None:
    """source_detail / source_key / display_name / comment never publish.

    Checked against the WRITTEN files, not the SQL: the files are what leave
    the machine. And beyond column names, the private strings the fixture
    planted (a display name, a reviewer label with a first name, a free-text
    comment) must not appear in any published value either.
    """
    parquet_files = sorted((exported / "data").glob("*.parquet"))
    assert len(parquet_files) == 5

    for parquet_path in parquet_files:
        table = pq.read_table(parquet_path)
        assert not set(table.schema.names) & FORBIDDEN_COLUMNS

        published_values = repr(table.to_pydict())
        for private in PRIVATE_STRINGS:
            assert private not in published_values, (
                f"{private!r} leaked into {parquet_path.name}"
            )


def test_contributors_are_opaque_ids_only(exported: Path) -> None:
    """The contributors config is the ladder position of an opaque token.

    No identity column at all: names, handles, and source keys live in
    ``contributor_identities``, which the fixture populates and the export
    must never read.
    """
    contributors = _read(exported, "contributors")
    assert set(contributors) == {"id", "current_rung", "joined_at"}
    assert sorted(contributors["id"]) == sorted([CONTRIBUTOR_ALICE, CONTRIBUTOR_BOB])
    for opaque_id in contributors["id"]:
        assert re.fullmatch(r"c_[0-9a-f]{16}", str(opaque_id))


# ---------------------------------------------------------------------------
# Counts are derived, never stored
# ---------------------------------------------------------------------------


def test_endorsement_counts_are_derivable_and_match_the_view(
    v2_db: Path, exported: Path
) -> None:
    """COUNT(*) over the published rows reproduces the endorsement_counts view.

    No config stores a count column; the retracted endorsement is published
    (append-only evidence) but does not count.
    """
    endorsements = _read(exported, "endorsements")
    assert "comment" not in endorsements

    derived: dict[str, int] = {}
    for option, retracted in zip(
        endorsements["option_uid"], endorsements["retracted_at"]
    ):
        if retracted is None:
            derived[str(option)] = derived.get(str(option), 0) + 1

    conn = sqlite3.connect(v2_db)
    view = dict(
        conn.execute(
            "SELECT option_uid, endorsements FROM endorsement_counts "
            "WHERE endorsements > 0"
        )
    )
    conn.close()

    assert derived == view == {OPT_TRUE_UR: 2}

    ledger = json.loads((exported / "reconciliation.json").read_text())
    assert ledger["derived_endorsements"] == {
        "parquet_active_endorsements": 2,
        "endorsement_counts_view_sum": 2,
    }


# ---------------------------------------------------------------------------
# The dataset card and the push gate
# ---------------------------------------------------------------------------


def test_dataset_card_names_the_configs_and_the_governance_gate(
    exported: Path,
) -> None:
    """README.md carries the config table and the CORE-1502 private-first banner."""
    card = (exported / "README.md").read_text(encoding="utf-8")
    for config in CONFIG_SQL:
        assert f"config_name: {config}" in card
        assert f"data/{config}.parquet" in card
    assert "license: other" in card
    assert "Private-first" in card
    assert "language:\n  - ur\n  - zh\n" in card  # exact primary-subtag rollup
    assert "| zh-Hans |" in card  # exact locale list, straight from options.locale
    assert "CORE-1502" in card
    assert "never published" in card  # the corpus/canon split


def test_push_without_signoff_exits_before_writing_anything(
    v2_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A refused push leaves NO artifact: the gate runs before the export.

    Both keys are required -- the --governance-signoff flag AND the
    LEGESHER_HF_PUSH_APPROVED environment variable -- and either one missing
    must abort before a byte is written or a network library imported.
    """
    out = tmp_path / "corpus"
    monkeypatch.delenv("LEGESHER_HF_PUSH_APPROVED", raising=False)

    argv = ["--db", str(v2_db), "--out", str(out), "--push"]
    with pytest.raises(SystemExit, match="governance-signoff"):
        main(argv)
    assert not out.exists()

    with pytest.raises(SystemExit, match="LEGESHER_HF_PUSH_APPROVED"):
        main([*argv, "--governance-signoff", "CORE-1502"])
    assert not out.exists()

    # A sign-off citing the wrong ticket is not a sign-off.
    monkeypatch.setenv("LEGESHER_HF_PUSH_APPROVED", "1")
    with pytest.raises(SystemExit, match="governance-signoff"):
        main([*argv, "--governance-signoff", "CORE-9999"])
    assert not out.exists()


# ---------------------------------------------------------------------------
# Every refusal gate refuses (negative tests)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "from_clause",
    [
        "FROM contributors, contributor_identities",  # comma-join
        'FROM "contributor_identities"',  # quoted name
        "FROM main.canon_selections",  # schema-qualified
    ],
)
def test_a_config_mentioning_a_private_table_is_refused(
    v2_db: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    from_clause: str,
) -> None:
    """The private-table gate scans the whole SQL, not a FROM/JOIN parse.

    Each parametrized clause is a verified bypass of the naive regex approach
    (comma-joins, quoted names, schema-qualified references); all must refuse
    -- and BEFORE anything is written, so a refused export leaves no artifact.
    """
    evil = CONFIG_SQL["contributors"].replace("FROM contributors", from_clause)
    monkeypatch.setitem(CONFIG_SQL, "contributors", evil)

    out = tmp_path / "corpus"
    with pytest.raises(SystemExit, match="never published"):
        export_corpus(v2_db, out)
    assert not out.exists()


def test_a_malformed_locale_tag_refuses_the_export(v2_db: Path, tmp_path: Path) -> None:
    """A wrongly-cased tag is a permanent corpus fork; the export refuses it.

    The plant mirrors the documented real threat: one row inserted by one
    script through a raw connection (foreign keys default OFF in sqlite3, so
    the locales FK never fires). The DB CHECK guards locales.tag, not
    options.locale -- the export gate is the last line before the one-way door.
    """
    conn = sqlite3.connect(v2_db)
    conn.execute(
        "INSERT INTO options (uid, concept_id, locale, surface_form) "
        "VALUES (?, 1, 'zh-hans', '假')",
        (option_uid("true-constant", "zh-hans", "假"),),
    )
    conn.commit()
    conn.close()

    out = tmp_path / "corpus"
    with pytest.raises(SystemExit, match="malformed BCP 47"):
        export_corpus(v2_db, out)
    assert not out.exists()


def test_an_orphan_endorsement_fails_reconciliation(
    v2_db: Path, tmp_path: Path
) -> None:
    """A derived count that disagrees with the view is a hard failure.

    An endorsement pointing at a nonexistent option (planted through a raw,
    FK-off connection) is invisible to the endorsement_counts view but present
    in the exported rows: derived 3 vs view 2. The export must exit nonzero
    and the written ledger must say ok: false.
    """
    orphan_option = "opt_" + "0" * 24
    created = "2026-07-01T00:00:00"
    conn = sqlite3.connect(v2_db)
    conn.execute(
        "INSERT INTO endorsements (uid, option_uid, contributor_id, method, "
        "rung_at_endorsement, created_at) VALUES (?, ?, ?, 'portal', "
        "'contributor', ?)",
        (
            endorsement_uid(orphan_option, CONTRIBUTOR_BOB, "portal", created),
            orphan_option,
            CONTRIBUTOR_BOB,
            created,
        ),
    )
    conn.commit()
    conn.close()

    out = tmp_path / "corpus"
    with pytest.raises(SystemExit, match="reconciliation mismatch") as excinfo:
        export_corpus(v2_db, out)
    assert excinfo.value.code  # nonzero exit

    ledger = json.loads((out / "reconciliation.json").read_text())
    assert ledger["ok"] is False
    assert ledger["derived_endorsements"] == {
        "parquet_active_endorsements": 3,
        "endorsement_counts_view_sum": 2,
    }


def test_a_stale_unknown_parquet_refuses_the_export(
    v2_db: Path, tmp_path: Path
) -> None:
    """--push uploads the directory, so a stale artifact must block the run.

    The stray is refused, not silently deleted: a human decides what it was.
    Nothing else is written.
    """
    out = tmp_path / "corpus"
    stale = out / "data" / "legacy_options.parquet"
    stale.parent.mkdir(parents=True)
    stale.write_bytes(b"stale artifact from an older run")

    with pytest.raises(SystemExit, match="not produced by this exporter"):
        export_corpus(v2_db, out)
    assert stale.exists()
    assert not (out / "data" / "options.parquet").exists()


def test_a_forbidden_column_is_deleted_before_the_refusal(
    v2_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The post-write audit fails loudly AND leaves nothing behind.

    If a future SQL edit smuggles `comment` past the schema pin (both are
    monkeypatched here, as that editor would have to), the poisoned file must
    not survive its own refusal -- otherwise the next upload_folder run would
    push the very artifact the gate exists to stop.
    """
    evil_sql = CONFIG_SQL["endorsements"].replace(
        "retracted_at", "retracted_at, comment"
    )
    monkeypatch.setitem(CONFIG_SQL, "endorsements", evil_sql)
    monkeypatch.setitem(
        CONFIG_SCHEMA,
        "endorsements",
        [*CONFIG_SCHEMA["endorsements"], ("comment", "string")],
    )

    out = tmp_path / "corpus"
    with pytest.raises(SystemExit, match="forbidden"):
        export_corpus(v2_db, out)
    assert not (out / "data" / "endorsements.parquet").exists()


def test_a_missing_database_is_a_clear_refusal(tmp_path: Path) -> None:
    """A wrong --db path gets a pointed message, not a sqlite3 traceback."""
    out = tmp_path / "corpus"
    with pytest.raises(SystemExit, match="no database at"):
        export_corpus(tmp_path / "does-not-exist.db", out)
    assert not out.exists()


# ---------------------------------------------------------------------------
# Publish-grade gate: build_meta provenance + salt fingerprint (CORE-1312)
# ---------------------------------------------------------------------------


def _meta_db(tmp_path: Path, name: str, rows: list[tuple[str, str]]) -> Path:
    """A schema-only v2 database with the given build_meta rows."""
    path = tmp_path / name
    conn = sqlite3.connect(path)
    apply_schema_v2(conn)
    conn.executemany("INSERT INTO build_meta (key, value) VALUES (?, ?)", rows)
    conn.commit()
    conn.close()
    return path


def test_push_refuses_non_publish_grade_databases(tmp_path: Path) -> None:
    """A dev build, a dev-salt artifact, or an unknown file never pushes."""
    dev_build = _meta_db(
        tmp_path,
        "dev.db",
        [
            ("salt_fingerprint", salt_fingerprint(DEFAULT_CONTRIBUTOR_SALT)),
            ("publish_build", "0"),
        ],
    )
    with pytest.raises(SystemExit, match="NOT built with --publish"):
        require_publish_grade_db(dev_build)

    # publish_build=1 with the dev salt's fingerprint should be impossible
    # (migrate refuses the dev salt under --publish), but belt-and-braces:
    dev_salt = _meta_db(
        tmp_path,
        "dev-salt.db",
        [
            ("salt_fingerprint", salt_fingerprint(DEFAULT_CONTRIBUTOR_SALT)),
            ("publish_build", "1"),
        ],
    )
    with pytest.raises(SystemExit, match="PUBLIC dev salt"):
        require_publish_grade_db(dev_salt)

    stranger = tmp_path / "stranger.db"
    conn = sqlite3.connect(stranger)
    conn.execute("CREATE TABLE t (x)")
    conn.commit()
    conn.close()
    with pytest.raises(SystemExit, match="no readable build_meta"):
        require_publish_grade_db(stranger)
    # And the same refusal (not a raw sqlite3 traceback) for a file that
    # exists but is not a SQLite database at all.
    not_a_db = tmp_path / "corrupt.db"
    not_a_db.write_bytes(b"definitely not sqlite")
    with pytest.raises(SystemExit, match="no readable build_meta"):
        require_publish_grade_db(not_a_db)


def test_push_verifies_the_escrowed_salt_fingerprint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The operator must HOLD the salt the artifact was minted with."""
    escrowed = "correct-horse-battery-staple-0123456789"
    artifact = _meta_db(
        tmp_path,
        "publish.db",
        [
            ("salt_fingerprint", salt_fingerprint(escrowed)),
            ("publish_build", "1"),
        ],
    )
    monkeypatch.delenv("LEGESHER_CONTRIBUTOR_SALT", raising=False)
    with pytest.raises(SystemExit, match="is not set"):
        require_publish_grade_db(artifact)
    monkeypatch.setenv(
        "LEGESHER_CONTRIBUTOR_SALT", "some-other-salt-entirely-000000000"
    )
    with pytest.raises(SystemExit, match="does not match"):
        require_publish_grade_db(artifact)
    monkeypatch.setenv("LEGESHER_CONTRIBUTOR_SALT", escrowed)
    require_publish_grade_db(artifact)  # verified: no exit


def test_push_gate_checks_provenance_before_exporting(
    v2_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Approval keys alone are not enough: a non-publish DB stops the run
    before a single byte of export output exists."""
    monkeypatch.setenv("LEGESHER_HF_PUSH_APPROVED", "1")
    out = tmp_path / "corpus"
    with pytest.raises(SystemExit, match="NOT built with --publish"):
        main(
            [
                "--db",
                str(v2_db),
                "--out",
                str(out),
                "--push",
                "--governance-signoff",
                "CORE-1502",
            ]
        )
    assert not out.exists()


def test_push_refuses_a_missing_database_with_the_gate_message(
    tmp_path: Path,
) -> None:
    """Under --push the provenance gate's message is the one an operator with
    a wrong --db path actually sees."""
    with pytest.raises(SystemExit, match="no database at"):
        require_publish_grade_db(tmp_path / "does-not-exist.db")


# ---------------------------------------------------------------------------
# Intended-target gate (a typo must not mint frozen keys elsewhere)
# ---------------------------------------------------------------------------


def test_target_repo_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(TARGET_OVERRIDE_ENV_VAR, raising=False)
    require_intended_target(DEFAULT_TARGET_REPO)  # canonical: no second key
    with pytest.raises(SystemExit, match="not the canonical"):
        require_intended_target("legesher/translation")  # the classic typo
    monkeypatch.setenv(TARGET_OVERRIDE_ENV_VAR, "legesher/language-packs-staging")
    with pytest.raises(SystemExit, match="not the canonical"):
        require_intended_target("legesher/translation")  # override must MATCH
    require_intended_target("legesher/language-packs-staging")  # repeated: ok


# ---------------------------------------------------------------------------
# Hub auth preflight + the full gated push, with a stubbed huggingface_hub
# ---------------------------------------------------------------------------


def _stub_hub(
    monkeypatch: pytest.MonkeyPatch, *, whoami_error: Exception | None = None
) -> dict[str, dict]:
    """Install a stub huggingface_hub module; returns a call recorder."""
    calls: dict[str, dict] = {}

    class _Api:
        def whoami(self):
            if whoami_error is not None:
                raise whoami_error
            return {"name": "tester"}

        def create_repo(self, **kwargs):
            calls["create_repo"] = kwargs

        def upload_folder(self, **kwargs):
            calls["upload_folder"] = kwargs

    stub = types.ModuleType("huggingface_hub")
    stub.HfApi = _Api  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "huggingface_hub", stub)
    return calls


def _arm_push_env(monkeypatch: pytest.MonkeyPatch, v2_db: Path, salt: str) -> None:
    """Turn every non-network push key: approval, salt, publish-grade meta."""
    monkeypatch.setenv("LEGESHER_HF_PUSH_APPROVED", "1")
    monkeypatch.setenv("LEGESHER_CONTRIBUTOR_SALT", salt)
    conn = sqlite3.connect(v2_db)
    conn.executemany(
        "INSERT INTO build_meta (key, value) VALUES (?, ?)",
        [
            ("salt_fingerprint", salt_fingerprint(salt)),
            ("publish_build", "1"),
        ],
    )
    conn.commit()
    conn.close()


def test_failed_hub_auth_refuses_before_the_export_runs(
    v2_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The runbook promise: bad credentials fail BEFORE the export, so no
    push-ready artifact is left behind."""
    _arm_push_env(monkeypatch, v2_db, "escrowed-salt-0123456789-0123456789")
    _stub_hub(monkeypatch, whoami_error=RuntimeError("401 unauthorized"))
    out = tmp_path / "corpus"
    with pytest.raises(SystemExit, match="not authenticated"):
        main(
            [
                "--db",
                str(v2_db),
                "--out",
                str(out),
                "--push",
                "--governance-signoff",
                "CORE-1502",
            ]
        )
    assert not out.exists()


def test_fully_gated_push_uploads_only_exporter_artifacts(
    v2_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The whole happy path: all four gates pass, the export runs, and the
    upload is allowlisted to exactly the exporter-written files."""
    _arm_push_env(monkeypatch, v2_db, "escrowed-salt-0123456789-0123456789")
    calls = _stub_hub(monkeypatch)
    out = tmp_path / "corpus"
    assert (
        main(
            [
                "--db",
                str(v2_db),
                "--out",
                str(out),
                "--push",
                "--governance-signoff",
                "CORE-1502",
            ]
        )
        == 0
    )
    assert (out / "reconciliation.json").is_file()
    assert calls["create_repo"]["private"] is True
    assert calls["create_repo"]["repo_id"] == DEFAULT_TARGET_REPO
    assert calls["upload_folder"]["allow_patterns"] == list(PUSH_ALLOW_PATTERNS)


# ---------------------------------------------------------------------------
# Schema completeness: every table is classified, never merely omitted
# ---------------------------------------------------------------------------

#: Reference tables that are neither exported nor private: public-by-nature
#: vocabulary and structural metadata. A NEW table added to the schema must be
#: placed in exactly one bucket -- this test is what forces the decision.
NEUTRAL_TABLES: frozenset[str] = frozenset(
    {
        "programming_languages",
        "locales",
        "review_rungs",
        "concept_briefs",
        "concept_relations",
        "concept_slug_aliases",
        "message_templates",
        "message_translations",
        "import_sources",
    }
)


def test_every_schema_table_is_deliberately_classified() -> None:
    schema_tables = set(
        re.findall(r"CREATE TABLE (\w+)", SCHEMA_V2_PATH.read_text("utf-8"))
    )
    read_tables = set(CONFIG_BASE_TABLE.values()) | {
        "option_validations",  # joined into the options config
        "option_provenance",  # aggregated into options.sources
    }
    unclassified = schema_tables - read_tables - NEVER_EXPORT - NEUTRAL_TABLES
    assert not unclassified, (
        f"schema tables with no export classification: {sorted(unclassified)}. "
        "Every table must be in the export read-set, NEVER_EXPORT, or "
        "NEUTRAL_TABLES -- exclusion by omission is exactly what NEVER_EXPORT "
        "exists to prevent."
    )
    # No stale or typo'd declarations, and no table in two buckets.
    assert NEVER_EXPORT <= schema_tables
    assert not (NEVER_EXPORT & read_tables)
    assert not (NEVER_EXPORT & NEUTRAL_TABLES)
