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

import fnmatch
import json
import re
import sqlite3
import sys
import types
from pathlib import Path
from unittest import mock

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
import scripts.export_corpus as export_corpus_module
from scripts.export_corpus import (
    CONFIG_BASE_TABLE,
    CONFIG_SCHEMA,
    CONFIG_SQL,
    DEFAULT_TARGET_REPO,
    FORBIDDEN_COLUMNS,
    LANGUAGE_LIST_WIDTH,
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
#: Legesher organisation repositories a reader with no access can open. Only
#: the ones the card links today; extend it when the card links another.
PUBLIC_LEGESHER_REPOS = frozenset({"legesher", "legesher-translations"})

#: Strings that exist in the fixture database's PRIVATE columns and must not
#: appear anywhere in the published files.
PRIVATE_STRINGS = (
    "alice-gh",  # contributor_identities.source_key / github_handle
    "Alice Realname",  # contributor_identities.display_name
    "alice@example.com",  # contributor_identities.email (CORE-1538 contact)
    "reviewer_zh_review",  # option_provenance.source_detail (the label class that embeds a reviewer's first name)
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
        "min_interpreter_ok, format_chars_clean) "
        "VALUES (?, 'py-identifier-v1', 1, 1, 1, 0, 1, 1)",
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
            (OPT_TRUE_UR, "community", "reviewer_zh_review", None, CONTRIBUTOR_ALICE),
            (OPT_TRUE_ZH, "legesher", "yaml_pack", None, None),
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
        assert ledger["configs"][config] == {
            "db_rows": rows,
            "parquet_rows": rows,
            "quarantined_rows": 0,
        }


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
    assert options["sources"][by_uid[OPT_TRUE_ZH]] == ["legesher"]
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
    """README.md carries the config table, the locale list, and the promises."""
    card = (exported / "README.md").read_text(encoding="utf-8")
    for config in CONFIG_SQL:
        assert f"config_name: {config}" in card
        assert f"data/{config}.parquet" in card
        assert f"| `{config}` |" in card  # the Configs table names every one
    assert "license: cc-by-4.0" in card
    assert "language:\n  - ur\n  - zh\n" in card  # exact primary-subtag rollup
    assert "growing dataset" in card


def test_no_published_file_cites_an_internal_ticket(exported: Path) -> None:
    """Nothing a reader can see may reference a Linear issue.

    The card and its companions are read outside the project, where a bare
    ``CORE-####`` is an unresolvable reference. This is a publish-surface
    rule, not a style preference, so it is asserted over every text file the
    export writes rather than over the card alone.
    """
    for name in ("README.md", "NOTICE", "PRIVACY.md"):
        text = (exported / name).read_text(encoding="utf-8")
        assert not re.search(r"CORE-\d+", text), f"{name} cites an internal ticket"


def test_every_upstream_project_is_both_credited_and_its_notice_retained(
    exported: Path,
) -> None:
    """A fourth upstream cannot ship credited but unretained, or vice versa.

    ``migrate_to_v2.UPSTREAM_PROJECTS`` is where a new project gets classified
    as ``upstream``; the card's table is where it gets credited and NOTICE is
    where its licence text is retained. Nothing but this test connects the
    three, and the failure mode -- rows attributed to a project whose notice
    was never carried across -- is a licence breach, not a typo.
    """
    from scripts.migrate_to_v2 import UPSTREAM_PROJECTS

    card = (exported / "README.md").read_text(encoding="utf-8")
    notice = (exported / "NOTICE").read_text(encoding="utf-8")

    # A licence BODY, not just a mention: a one-line credit satisfies nothing.
    bodies = {
        "MIT": "Permission is hereby granted, free of charge",
        "Apache-2.0": "Licensed under the Apache License, Version 2.0",
    }

    assert UPSTREAM_PROJECTS, "expected at least one upstream project"
    for name, url, licence in UPSTREAM_PROJECTS.values():
        assert name in card, f"{name} is not credited on the card"
        assert url in card, f"{name}'s repository is not linked on the card"

        # Bound the search to THIS project's block. Searching the remainder
        # of the file lets a later project's MIT copy satisfy an earlier one
        # whose own body was deleted -- which is the licence breach this test
        # is the only guard against.
        assert name in notice, f"{name} has no section in NOTICE"
        after = notice.split(name, 1)[1]
        others = [
            after.index(other)
            for other, *_ in ((v[0],) for v in UPSTREAM_PROJECTS.values())
            if other != name and other in after
        ]
        block = after[: min(others)] if others else after

        assert licence in bodies, f"no known licence body for {licence}"
        assert bodies[licence] in block, (
            f"{name} is named in NOTICE but its own {licence} text is not "
            "retained in its section"
        )


def test_the_locale_query_is_gated_like_every_other_published_query() -> None:
    """The card's locale SQL sits under the NEVER_EXPORT gate.

    It feeds published text, so it is publish-surface SQL. The gate is
    structural precisely so that "it only reads `locales` today" is not the
    thing standing between a private table and the Hub.
    """
    from scripts.export_corpus import (
        CARD_LOCALE_SQL,
        _assert_configs_avoid_private_tables,
    )

    _assert_configs_avoid_private_tables()  # the real queries pass

    with mock.patch(
        "scripts.export_corpus.CARD_LOCALE_SQL",
        CARD_LOCALE_SQL + "\nJOIN contributor_identities ci ON 1=0",
    ):
        with pytest.raises(SystemExit, match="contributor_identities"):
            _assert_configs_avoid_private_tables()


def test_the_push_commit_message_names_no_internal_ticket() -> None:
    """Hub commit history is as public as the files it carries."""
    recorded: dict[str, object] = {}

    class _Api:
        def create_repo(self, **kwargs: object) -> None:
            recorded["create"] = kwargs

        def upload_folder(self, **kwargs: object) -> None:
            recorded.update(kwargs)

    with mock.patch("scripts.export_corpus._require_hf_api", lambda: lambda: _Api()):
        export_corpus_module.push_to_hub(Path("/tmp/nowhere"), DEFAULT_TARGET_REPO)

    assert not re.search(r"CORE-\d+", str(recorded["commit_message"]))
    # And a renamed banner cannot linger on the remote beside its replacement.
    assert recorded["delete_patterns"] == ["assets/*.png"]


def test_exporting_over_the_source_banner_does_not_delete_it(
    v2_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A wrong --out wastes a run; it must not damage the working tree.

    ``--out libs/i18n`` makes ``<out>/assets`` the repository's own asset
    directory, so the stale-PNG sweep would delete the tracked banner and every
    later export would refuse until someone restored it from git. Reproduced
    against a temporary tree rather than the real one -- a test that writes a
    dataset card over ``libs/i18n/README.md`` to prove a point is a worse bug
    than the one it is checking for.
    """
    fake_repo = tmp_path / "i18n"
    (fake_repo / "assets").mkdir(parents=True)
    source = fake_repo / "assets" / "language-corpus-card.png"
    source.write_bytes(export_corpus_module.CARD_IMAGE_SOURCE.read_bytes())
    before = source.read_bytes()
    # Another tracked image in the same directory: exempting only the banner
    # would still delete this one out of the working tree.
    bystander = fake_repo / "assets" / "some-other-diagram.png"
    bystander.write_bytes(b"\x89PNG\r\n\x1a\n bystander")
    monkeypatch.setattr(export_corpus_module, "CARD_IMAGE_SOURCE", source)

    with pytest.raises(SystemExit, match="this export did not write"):
        export_corpus(v2_db, fake_repo)

    assert source.is_file(), "the source banner was deleted"
    assert source.read_bytes() == before
    assert bystander.is_file(), "an unrelated tracked image was deleted"


def test_the_push_allowlist_covers_exactly_what_the_export_writes(
    exported: Path,
) -> None:
    """Nothing the export writes may be missing from the push allowlist.

    Dropping a pattern does not fail anything: the push simply leaves that
    file behind, and the card ships pointing at something that is not there.
    The banner is the loud case (a broken image at the top of the page);
    NOTICE and PRIVACY.md are the quiet ones -- links that resolve to nothing.
    """
    written = sorted(
        path.relative_to(exported).as_posix()
        for path in exported.rglob("*")
        if path.is_file()
    )
    assert written, "the export wrote nothing"

    for relative in written:
        assert any(
            fnmatch.fnmatch(relative, pattern) for pattern in PUSH_ALLOW_PATTERNS
        ), f"{relative} is written but not on the push allowlist"

    # And no pattern is dead weight -- one that matches nothing is either a
    # typo or a file we stopped writing.
    for pattern in PUSH_ALLOW_PATTERNS:
        assert any(fnmatch.fnmatch(rel, pattern) for rel in written), (
            f"allowlist pattern {pattern!r} matches nothing the export writes"
        )


def test_the_card_states_the_config_count_it_can_prove(exported: Path) -> None:
    """The configs count is rendered from CONFIG_SQL, not asserted."""
    card = (exported / "README.md").read_text(encoding="utf-8")
    rows = [line for line in card.splitlines() if line.startswith("| `")]
    config_rows = [line for line in rows if line.split("`")[1] in CONFIG_SQL]

    assert len(config_rows) == len(CONFIG_SQL)
    assert f"{'Five' if len(CONFIG_SQL) == 5 else len(CONFIG_SQL)} configs" in card
    assert export_corpus_module.CARD_CONFIG_COUNT_PLACEHOLDER not in card


def test_a_broken_card_template_refuses_before_anything_is_written(
    v2_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A lost placeholder aborts pre-flight, not mid-export."""
    out = tmp_path / "corpus"
    monkeypatch.setattr(
        export_corpus_module,
        "DATASET_CARD",
        export_corpus_module.DATASET_CARD.replace(
            export_corpus_module.CARD_REPO_PLACEHOLDER, "legesher/language-corpus"
        ),
    )

    with pytest.raises(SystemExit, match="has vanished from DATASET_CARD"):
        export_corpus(v2_db, out)

    assert not (out / "data").exists()
    assert not (out / "README.md").exists()


def test_a_foreign_readme_refuses_before_anything_is_written(
    v2_db: Path, tmp_path: Path
) -> None:
    """--out over a package directory must not overwrite its README.

    This is not hypothetical: an earlier draft of the banner test pointed
    --out at libs/i18n and overwrote the package README. The refusal is
    PRE-FLIGHT, so a wrong --out leaves the directory exactly as it was
    rather than dropping fresh Parquet beside a stale card and a
    reconciliation ledger reporting the wrong counts.
    """
    victim = tmp_path / "some-package"
    victim.mkdir()
    readme = victim / "README.md"
    readme.write_text("# some-package\n\nNot a dataset card.\n")

    with pytest.raises(SystemExit, match="not a dataset card"):
        export_corpus(v2_db, victim)

    assert readme.read_text() == "# some-package\n\nNot a dataset card.\n"
    assert not (victim / "data").exists()
    assert not (victim / "reconciliation.json").exists()


def test_a_stray_image_refuses_before_anything_is_written(
    v2_db: Path, tmp_path: Path
) -> None:
    """The stray-image refusal is pre-flight too.

    It used to run after every Parquet file had been rewritten, leaving fresh
    data beside the previous run's card and a ledger reporting counts that no
    longer matched the files next to it.
    """
    out = tmp_path / "corpus"
    export_corpus(v2_db, out)
    ledger_before = (out / "reconciliation.json").read_text()
    (out / "assets" / "old-banner.png").write_bytes(b"\x89PNG\r\n\x1a\n stray")
    parquet = out / "data" / "options.parquet"
    stamp = parquet.stat().st_mtime_ns

    with pytest.raises(SystemExit, match="this export did not write"):
        export_corpus(v2_db, out)

    assert parquet.stat().st_mtime_ns == stamp, "Parquet was rewritten anyway"
    assert (out / "reconciliation.json").read_text() == ledger_before


def test_the_card_names_the_repo_it_is_actually_published_to(
    v2_db: Path, tmp_path: Path
) -> None:
    """A rehearsal push must not ship a card pointing at the real dataset.

    The load example and the "suggest a dataset" link both name the repo, and
    the push target is a runtime value -- so both follow ``--target-repo``
    rather than being frozen to the canonical id.
    """
    out = tmp_path / "rehearsal"
    export_corpus(v2_db, out, "someone-else/rehearsal-corpus")
    card = (out / "README.md").read_text(encoding="utf-8")

    assert 'load_dataset("someone-else/rehearsal-corpus", "options")' in card
    assert "huggingface.co/datasets/someone-else/rehearsal-corpus/discussions" in card
    assert DEFAULT_TARGET_REPO not in card
    assert export_corpus_module.CARD_REPO_PLACEHOLDER not in card


def test_the_card_links_nowhere_that_a_public_reader_cannot_reach(
    exported: Path,
) -> None:
    """Every Legesher repository the card links must be a public one.

    The dataset page is read by people with no access to our source repos, so
    a link there is a 404 with our name on it. The check is an allowlist of
    the organisation's public repositories rather than a list of private
    names, so the test itself names nothing that is not public. The Hub
    discussions tab is the reply channel that is as public as the dataset
    itself.
    """
    card = (exported / "README.md").read_text(encoding="utf-8")
    linked = {
        name.removesuffix(".git")
        for name in re.findall(
            r"github\.com/legesher/([A-Za-z0-9_.-]+)", card, re.IGNORECASE
        )
    }
    assert linked, "the card no longer links any Legesher repository"
    not_public = linked - PUBLIC_LEGESHER_REPOS
    assert not not_public, f"card links non-public repositories: {sorted(not_public)}"
    assert "/discussions" in card  # the reply channel is on the Hub


def test_the_privacy_posture_ships_as_its_own_file(exported: Path) -> None:
    """The posture left the card for PRIVACY.md, and the card links it."""
    card = (exported / "README.md").read_text(encoding="utf-8")
    privacy = (exported / "PRIVACY.md").read_text(encoding="utf-8")

    assert "[`PRIVACY.md`](PRIVACY.md)" in card
    assert "PRIVACY.md" in PUSH_ALLOW_PATTERNS
    # The card keeps a short pointer, not the bullet list it used to carry.
    assert "## PII posture" not in card
    assert "## Privacy" in card

    for promise in ("Withdrawal", "Counts survive", "privacy@legesher.com"):
        assert promise in privacy


def test_dataset_card_lists_every_locale_with_its_name(exported: Path) -> None:
    """The locale list is flowing text, not a table.

    A markdown table must carry a header row, and every column here held the
    same thing -- so the header was either the same words repeated across the
    page or a blank band above the data. A list has no header to get wrong.
    """
    card = (exported / "README.md").read_text(encoding="utf-8")
    section = card.split("## Languages")[1].split("## Configs")[0]

    assert "| --- |" not in section, "the locale list should not be a table"
    assert "`ur` Urdu" in section
    assert "`zh-Hans` Chinese (Simplified)" in section
    assert "All 2 locales" in section  # the count is rendered, never hardcoded

    body = [line for line in section.splitlines() if line.startswith("`")]
    assert body and " · " in body[0], "entries are separated for scanning"
    for line in section.splitlines():
        assert len(line) <= LANGUAGE_LIST_WIDTH, f"unwrapped line: {line!r}"

    # Markdown joins the wrapped lines back into one paragraph with a single
    # space, so every line but the last must carry its trailing separator --
    # without it two languages render run together with nothing between them.
    for line in body[:-1]:
        assert line.endswith(" ·"), f"separator lost at a line break: {line!r}"
    assert not body[-1].endswith("·")
    assert " ·  · " not in " ".join(body)  # and never doubled


def test_the_locale_list_keeps_its_separators_when_markdown_reflows_it(
    v2_db: Path, tmp_path: Path
) -> None:
    """A many-locale list still reads correctly once the line breaks collapse.

    The fixture has two locales and never wraps, so the wrap path needs a
    database wide enough to exercise it.
    """
    conn = sqlite3.connect(v2_db)
    for index in range(40):
        locale = f"q{chr(ord('a') + index % 26)}{chr(ord('a') + index // 26)}"
        conn.execute(
            "INSERT INTO locales (tag, language_subtag, name, native_name) "
            "VALUES (?, ?, ?, ?)",
            (locale, locale, f"Testlang {index}", f"Testlang {index}"),
        )
        conn.execute(
            "INSERT INTO options (uid, concept_id, locale, surface_form) "
            "VALUES (?, 1, ?, ?)",
            (option_uid("true-constant", locale, f"w{index}"), locale, f"w{index}"),
        )
    conn.commit()
    conn.close()

    out = tmp_path / "corpus-wide"
    export_corpus(v2_db, out)
    card = (out / "README.md").read_text(encoding="utf-8")
    section = card.split("## Languages")[1].split("## Configs")[0]
    body = [line for line in section.splitlines() if line.startswith("`")]

    assert len(body) > 1, "expected the list to wrap across several lines"
    # Collapse the line breaks the way a markdown renderer does.
    reflowed = " ".join(body)
    assert reflowed.count(" · ") == reflowed.count("`") // 2 - 1
    assert "` `" not in reflowed  # no two entries touching without a separator


def test_dataset_card_sections_run_in_the_agreed_order(exported: Path) -> None:
    """The card's shape is a decision, not an accident (Madison, 2026-08-17).

    Orientation first (what it is, which languages, what the columns are),
    then provenance walked in the order the work happened (upstream who came
    before us, our own renderings, the people who attest them, the machine),
    then the legal and privacy posture last.
    """
    card = (exported / "README.md").read_text(encoding="utf-8")
    sections = [line[3:] for line in card.splitlines() if line.startswith("## ")]
    assert sections == [
        "What this corpus is",
        "Languages",
        "Configs",
        "Where each rendering came from",
        "Upstream projects",
        "Legesher-produced renderings",
        "Community contributions",
        "Machine-generated renderings",
        "Licence and attribution",
        "Privacy",
    ]


def test_every_internal_card_link_resolves_to_a_heading(exported: Path) -> None:
    """No `](#anchor)` may point at a heading the card does not have.

    The sections move around; a stale in-page link is silent on the Hub and
    only shows up as a click that goes nowhere.
    """
    card = (exported / "README.md").read_text(encoding="utf-8")
    slugs = {
        re.sub(r"[^a-z0-9 -]", "", line.lstrip("#").strip().lower()).replace(" ", "-")
        for line in card.splitlines()
        if line.startswith("#")
    }
    anchors = set(re.findall(r"\]\(#([^)]+)\)", card))
    assert anchors, "expected the card to cross-reference its own sections"
    assert anchors <= slugs, f"dangling anchors: {sorted(anchors - slugs)}"


def test_upstream_notices_leave_the_card_but_still_travel_with_the_data(
    exported: Path,
) -> None:
    """Third-party licence text lives in NOTICE, not on the card.

    The card is about this dataset's licence; the retention obligation is
    satisfied by a file shipped beside it, which is on the push allowlist. So
    the card must NOT carry the licence bodies, and NOTICE must.
    """
    card = (exported / "README.md").read_text(encoding="utf-8")
    notice = (exported / "NOTICE").read_text(encoding="utf-8")

    warranty = "THE SOFTWARE IS PROVIDED"
    assert warranty not in card
    assert "Permission is hereby granted" not in card
    assert "WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND" not in card

    assert card.count(warranty) == 0
    assert notice.count(warranty) == 2  # both MIT-licensed upstreams
    assert "Copyright (c) 2019 Legesher" in notice
    assert "Copyright (c) 2015 - Latino" in notice
    assert "apache.org/licenses/LICENSE-2.0" in notice
    assert "CHANGES WERE MADE" in notice  # Apache-2.0 section 4(b)

    # The card still points at it, and the pointer resolves.
    assert "[`NOTICE`](NOTICE)" in card
    assert "NOTICE" in PUSH_ALLOW_PATTERNS


def test_dataset_card_invites_dataset_suggestions(exported: Path) -> None:
    """The upstream section asks readers to name projects we should include."""
    card = (exported / "README.md").read_text(encoding="utf-8")
    assert "Is there a dataset we should add?" in card
    assert "Open a discussion" in card


def test_dataset_card_banner_image_ships_with_the_export(exported: Path) -> None:
    """The card's relative image link resolves inside the export directory."""
    card = (exported / "README.md").read_text(encoding="utf-8")
    assert "![Legesher language corpus](assets/language-corpus-card.png)" in card
    assert (exported / "assets" / "language-corpus-card.png").is_file()


def test_a_stray_image_beside_the_banner_refuses_the_export(
    v2_db: Path, tmp_path: Path
) -> None:
    """A bystander PNG is REFUSED, never deleted.

    Everything under ``assets/`` is published, so a stray image would ship on
    the dataset page. Refusing rather than deleting is what makes the sweep
    safe for an arbitrary ``--out``: the export cannot tell a stale banner
    from a file that simply lives there, so it must not guess.
    """
    out = tmp_path / "corpus"
    export_corpus(v2_db, out)
    stray = out / "assets" / "old-banner.png"
    stray.write_bytes(b"\x89PNG\r\n\x1a\n stray")

    with pytest.raises(SystemExit, match="this export did not write"):
        export_corpus(v2_db, out)

    assert stray.exists(), "the bystander was deleted rather than refused"
    assert (out / "assets" / "language-corpus-card.png").is_file()


def test_a_missing_banner_refuses_before_any_file_is_written(
    v2_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The banner gate aborts with the output directory untouched.

    Every other refusal in ``export_corpus`` runs before a byte is written;
    this one must too, or a missing image leaves a half-built export whose
    Parquet files have no card beside them.
    """
    out = tmp_path / "corpus"
    monkeypatch.setattr(
        export_corpus_module, "CARD_IMAGE_SOURCE", tmp_path / "not-there.png"
    )

    with pytest.raises(SystemExit, match="banner image is missing"):
        export_corpus(v2_db, out)

    assert not (out / "data").exists()
    assert not (out / "README.md").exists()


def test_a_locale_whose_every_option_is_quarantined_leaves_the_card(
    v2_db: Path, tmp_path: Path
) -> None:
    """The card names only locales the `options` config actually publishes.

    ``zh-Hans`` has exactly one option in the fixture. Quarantining it (CORE-1828)
    exports no zh-Hans rows, so announcing `zh` in the Hub-indexed `language:`
    header would claim coverage the data does not have.
    """
    conn = sqlite3.connect(v2_db)
    conn.execute(
        "INSERT INTO option_screenings (option_uid, verdict, screened_by, "
        "screen_version) VALUES (?, 'quarantined', 'importer', 'manual-interim-v1')",
        (OPT_TRUE_ZH,),
    )
    conn.commit()
    conn.close()

    out = tmp_path / "corpus-quarantined"
    export_corpus(v2_db, out)
    card = (out / "README.md").read_text(encoding="utf-8")

    assert OPT_TRUE_ZH not in _read(out, "options")["option_uid"]
    assert "zh-Hans" not in card
    assert "language:\n  - ur\n" in card  # the zh rollup entry is gone too


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
    monkeypatch.setenv(TARGET_OVERRIDE_ENV_VAR, "legesher/language-corpus-staging")
    with pytest.raises(SystemExit, match="not the canonical"):
        require_intended_target("legesher/translation")  # override must MATCH
    require_intended_target("legesher/language-corpus-staging")  # repeated: ok


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
    # ONE sanctioned exception: option_screenings is private BY DEFAULT
    # (NEVER_EXPORT) and joins the read-set only when the CORE-1797
    # export_verdicts flag is on, through the sanitized SCREENINGS_CONFIG_SQL.
    # Being declared in both buckets is that flag's design, not drift.
    sanctioned_dual = {"option_screenings"}
    assert NEVER_EXPORT <= schema_tables
    assert not (NEVER_EXPORT & (read_tables - sanctioned_dual))
    assert not (NEVER_EXPORT & NEUTRAL_TABLES)


def test_a_quarantined_option_is_absent_from_the_export(
    v2_db: Path, tmp_path: Path
) -> None:
    """CORE-1828: an uncleared community submission never exports.

    The option row and its endorsement rows are held back, the ledger says how
    many (no silent caps), and a later 'cleared' verdict restores them.
    """
    conn = sqlite3.connect(v2_db)
    conn.execute(
        "INSERT INTO option_screenings (option_uid, verdict, screened_by, "
        "screen_version) VALUES (?, 'quarantined', 'importer', 'manual-interim-v1')",
        (OPT_TRUE_ZH,),
    )
    conn.commit()
    conn.close()

    out = tmp_path / "corpus-quarantined"
    ledger = export_corpus(v2_db, out)
    assert ledger["ok"] is True
    assert OPT_TRUE_ZH not in _read(out, "options")["option_uid"]
    assert OPT_TRUE_ZH not in _read(out, "endorsements")["option_uid"]
    assert ledger["configs"]["options"]["quarantined_rows"] == 1
    assert ledger["configs"]["endorsements"]["quarantined_rows"] == 1

    conn = sqlite3.connect(v2_db)
    conn.execute(
        "INSERT INTO option_screenings (option_uid, verdict, screened_by, "
        "screen_version, note) VALUES (?, 'cleared', 'madi', "
        "'manual-interim-v1', 'import ritual')",
        (OPT_TRUE_ZH,),
    )
    conn.commit()
    conn.close()

    out = tmp_path / "corpus-cleared"
    ledger = export_corpus(v2_db, out)
    assert ledger["ok"] is True
    assert OPT_TRUE_ZH in _read(out, "options")["option_uid"]
    assert ledger["configs"]["options"]["quarantined_rows"] == 0


def test_screening_verdicts_export_only_under_the_flag(
    v2_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CORE-1797 sub-decision: verdicts stay private by default; the
    export_verdicts flag publishes a SANITIZED trail — no screened_by, no
    note, and no event for an option the export itself withholds."""
    conn = sqlite3.connect(v2_db)
    conn.execute(
        "INSERT INTO option_screenings (option_uid, verdict, screened_by, "
        "screen_version, note) VALUES (?, 'cleared', 'madi', "
        "'auto-gate-v1', 'fast path')",
        (OPT_TRUE_ZH,),
    )
    conn.commit()
    conn.close()

    off = tmp_path / "corpus-verdicts-off"
    assert export_corpus(v2_db, off)["ok"] is True
    assert not (off / "data" / "screenings.parquet").exists()

    monkeypatch.setenv("LEGESHER_MODERATION_EXPORT_VERDICTS", "1")
    on = tmp_path / "corpus-verdicts-on"
    ledger = export_corpus(v2_db, on)
    assert ledger["ok"] is True
    table = _read(on, "screenings")
    assert set(table) == {"option_uid", "verdict", "screen_version", "screened_at"}
    assert OPT_TRUE_ZH in table["option_uid"]
    # Every published event belongs to an option the export publishes: a
    # verdict trail on a withheld option would leak that it exists.
    assert set(table["option_uid"]) <= set(_read(on, "options")["option_uid"])
    assert ledger["configs"]["screenings"]["db_rows"] == len(table["option_uid"])


def test_export_works_on_a_database_that_predates_screening(
    v2_db: Path, tmp_path: Path
) -> None:
    """A carried-forward database has no `option_withheld` view (CORE-1838).

    The intake ritual carries the previous database copy forward, and only the
    IMPORT lane upgrades it. An export run before the next import opens the
    file `mode=ro`, so it cannot install anything — it has to read a
    pre-screening database as what it is: one where no verdict was ever
    recorded, and therefore nothing is withheld.
    """
    conn = sqlite3.connect(v2_db)
    conn.execute("DROP TRIGGER trg_canon_no_quarantined_option")
    for view in ("option_standings", "terminology_export", "quarantine_queue"):
        conn.execute(f"DROP VIEW {view}")
    for view in ("option_withheld", "option_screening_status"):
        conn.execute(f"DROP VIEW {view}")
    conn.execute("DROP TABLE option_screenings")
    conn.commit()
    conn.close()

    ledger = export_corpus(v2_db, tmp_path / "corpus-carried-forward")
    assert ledger["ok"] is True
    assert ledger["configs"]["options"]["quarantined_rows"] == 0
    assert (
        OPT_TRUE_ZH
        in _read(tmp_path / "corpus-carried-forward", "options")["option_uid"]
    )


def test_a_held_option_is_withheld_from_the_export_like_a_quarantined_one(
    v2_db: Path, tmp_path: Path
) -> None:
    """Every export predicate is `<> 'cleared'`, so held and rejected behave
    identically to quarantined. Pinned so a future verdict cannot leak."""
    for verdict in ("held", "rejected"):
        conn = sqlite3.connect(v2_db)
        conn.execute(
            "INSERT INTO option_screenings (option_uid, verdict, screened_by, "
            "screen_version) VALUES (?, ?, 'madi', 'manual-interim-v1')",
            (OPT_TRUE_ZH, verdict),
        )
        conn.commit()
        conn.close()
        out = tmp_path / f"corpus-{verdict}"
        ledger = export_corpus(v2_db, out)
        assert ledger["ok"] is True
        assert OPT_TRUE_ZH not in _read(out, "options")["option_uid"], verdict
        assert ledger["configs"]["options"]["quarantined_rows"] == 1, verdict
