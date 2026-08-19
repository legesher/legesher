"""Tests for the canon export.

The load-bearing ones are the refusals. This artifact publishes terminology
under other people's languages, so the interesting property is not that a
correct database exports correctly — it is that a database carrying something
unpublishable stops the export dead rather than shipping it.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pytest

from legesher_i18n.db.schema_v2 import apply_schema_v2
from scripts.export_canon import (
    DECLARED_LICENSE,
    DEFAULT_TARGET_REPO,
    PUSH_ENV_VAR,
    ROLE_BY_DECIDER,
    TARGET_OVERRIDE_ENV_VAR,
    ExportRefused,
    export_canon,
    map_decider_role,
    require_intended_target,
    require_push_approval,
)
from scripts.correct_canon_review_rung import correct

OPT_ZH = "opt_" + "a" * 24
OPT_UK = "opt_" + "b" * 24
OPT_JS = "opt_" + "c" * 24


@pytest.fixture
def canon_db(tmp_path: Path) -> Path:
    """A v2 database holding exactly the rows the three filters must remove.

    One publishable Chinese row decided by a native reviewer, one Ukrainian
    showcase row, and one Arabic JavaScript row. If any filter regresses, a
    test here fails with the specific row that got through.
    """
    path = tmp_path / "v2.db"
    conn = sqlite3.connect(path)
    apply_schema_v2(conn)

    conn.executemany(
        "INSERT INTO programming_languages (code, name, status) VALUES (?, ?, ?)",
        [("python", "Python", "shipping"), ("javascript", "JavaScript", "planned")],
    )
    conn.executemany(
        "INSERT INTO locales (tag, language_subtag, script_subtag, name, "
        "native_name, direction, in_registry) VALUES (?, ?, ?, ?, ?, ?, 1)",
        [
            ("zh-Hans", "zh", "Hans", "Chinese (Simplified)", "简体中文", "ltr"),
            ("uk", "uk", None, "Ukrainian", "Українська", "ltr"),
            ("ar", "ar", None, "Arabic", "العربية", "rtl"),
        ],
    )
    conn.executemany(
        "INSERT INTO concepts (id, slug, definition_en, category) VALUES (?, ?, ?, ?)",
        [
            (1, "true-constant", "The boolean truth value.", "value_literal"),
            (2, "print-builtin", "Write to standard output.", "builtin_operation"),
            (3, "const-declaration", "An immutable binding.", "declaration"),
        ],
    )
    conn.executemany(
        "INSERT INTO terms (concept_id, programming_language, name, category) "
        "VALUES (?, ?, ?, 'keyword')",
        [(1, "python", "True"), (2, "python", "print"), (3, "javascript", "const")],
    )
    conn.executemany(
        "INSERT INTO options (uid, concept_id, locale, surface_form, "
        "first_seen_at) VALUES (?, ?, ?, ?, '2026-06-01T00:00:00')",
        [
            (OPT_ZH, 1, "zh-Hans", "真实"),
            (OPT_UK, 2, "uk", "друкувати"),
            (OPT_JS, 3, "ar", "ثابت"),
        ],
    )
    conn.executemany(
        "INSERT INTO option_validations (option_uid, validator_version, "
        "identifier_valid, nfkc_stable, script_consistent, collides_en_keyword, "
        "min_interpreter_ok) VALUES (?, 'py-identifier-v1', 1, 1, 1, 0, 1)",
        [(OPT_ZH,), (OPT_UK,), (OPT_JS,)],
    )
    conn.executemany(
        "INSERT INTO canon_selections (concept_id, locale, programming_language, "
        "option_uid, surface_form, status, decided_by, decision_reason, "
        "source_file) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            # Publishable: a native speaker's correction, still at `machine`
            # exactly as the real database has it.
            (
                1,
                "zh-Hans",
                "python",
                OPT_ZH,
                "真实",
                "machine",
                "reviewer_one_review",
                "Native speaker review correction",
                "libs/i18n/canon/zh-Hans.toml",
            ),
            # Showcase material, six words and no pack behind it.
            (
                2,
                "uk",
                "python",
                OPT_UK,
                "друкувати",
                "machine",
                "language-showcase-draft",
                "Showcase draft",
                "libs/i18n/canon/uk.toml",
            ),
            # The term T4 population: a JavaScript-only concept in Arabic.
            (
                3,
                "ar",
                "javascript",
                OPT_JS,
                "ثابت",
                "machine",
                "claude-fable-5",
                "CORE-1371 in-session curation",
                "libs/i18n/canon/ar.toml",
            ),
        ],
    )
    conn.commit()
    conn.close()
    return path


def _rows(out_dir: Path) -> dict[str, list]:
    pq = pytest.importorskip("pyarrow.parquet")
    return pq.read_table(out_dir / "data" / "canon.parquet").to_pydict()


def test_javascript_selections_never_reach_the_artifact(
    canon_db: Path, tmp_path: Path
) -> None:
    """The T4 population is excluded by target, not by hoping nobody looks.

    ``canon_selections`` carries ``programming_language`` as a real populated
    column, so an unfiltered export would publish unreviewed Arabic JavaScript
    terminology *labelled by target* — worse than the corpus case, where it
    was only recoverable by a join.
    """
    out = tmp_path / "out"
    summary = export_canon(canon_db, out)
    rows = _rows(out)

    assert "ثابت" not in rows["surface_form"]
    assert "ar" not in rows["locale"]
    assert summary["filters"]["pl_scope"] == "python"


def test_the_showcase_locale_never_reaches_the_artifact(
    canon_db: Path, tmp_path: Path
) -> None:
    out = tmp_path / "out"
    export_canon(canon_db, out)
    assert "uk" not in _rows(out)["locale"]


def test_the_publishable_row_survives_with_its_role_mapped(
    canon_db: Path, tmp_path: Path
) -> None:
    out = tmp_path / "out"
    export_canon(canon_db, out)
    rows = _rows(out)

    assert rows["locale"] == ["zh-Hans"]
    assert rows["surface_form"] == ["真实"]
    # The handle is gone; the fact that a native speaker decided it is not.
    assert rows["decided_by"] == ["native-reviewer"]


def test_an_unmapped_decider_refuses_the_export() -> None:
    """A default here is a silent data-loss bug wearing a sensible hat.

    This is not hypothetical: a mapping built from the ten most common values
    dropped a single-row reviewer into ``automated`` during scoping.
    """
    with pytest.raises(ExportRefused) as caught:
        map_decider_role("someone_we_have_not_seen")
    assert "no role mapping" in str(caught.value)


def test_a_reviewer_never_seen_before_resolves_on_their_first_row() -> None:
    """Handles resolve by shape, so a new reviewer needs no code change.

    Enumerating names would mean a reviewer's first contribution classifies as
    `automated` until someone remembers to add them — silent, and exactly the
    erasure this mapping exists to prevent.
    """
    assert map_decider_role("someone_new_review") == "native-reviewer"


def test_a_process_label_shaped_like_a_handle_is_not_a_reviewer() -> None:
    """`quality_review` fits the handle shape but is a maintainer pass.

    Explicit entries are consulted before the shape for exactly this reason;
    counting it as native review would overstate how much of the canon a
    native speaker has seen.
    """
    assert map_decider_role("quality_review") == "automated"


def test_no_contributor_handle_appears_in_the_exporter_source() -> None:
    """This repo goes public; contributor names must not be in it.

    The published artifact maps handles to roles precisely so identities stay
    out of it — listing those identities in the source that does the mapping
    would undo that one import statement away.
    """
    from scripts import export_canon

    source = Path(export_canon.__file__).read_text(encoding="utf-8")
    handles = re.findall(r"[\"\']([a-z][a-z0-9_.-]*_review)[\"\']", source)
    assert [h for h in handles if h not in {"quality_review"}] == []


def test_a_null_decider_refuses_rather_than_defaulting() -> None:
    with pytest.raises(ExportRefused):
        map_decider_role(None)


def test_every_mapped_role_is_a_published_role() -> None:
    """The mapping cannot invent a role the card does not document."""
    from scripts.export_canon import PUBLISHED_ROLES

    assert set(ROLE_BY_DECIDER.values()) <= set(PUBLISHED_ROLES)


def test_no_internal_ticket_reaches_the_artifact(
    canon_db: Path, tmp_path: Path
) -> None:
    """No published file may cite a ticket, in any column or the card."""
    out = tmp_path / "out"
    export_canon(canon_db, out)

    for path in (out / "README.md", out / "reconciliation.json"):
        assert "CORE-" not in path.read_text(encoding="utf-8")
    for values in _rows(out).values():
        for value in values:
            assert "CORE-" not in str(value)


def test_no_contributor_handle_reaches_the_artifact(
    canon_db: Path, tmp_path: Path
) -> None:
    out = tmp_path / "out"
    export_canon(canon_db, out)
    assert "reviewer_one" not in (out / "README.md").read_text(encoding="utf-8")
    for values in _rows(out).values():
        for value in values:
            assert not str(value).endswith("_review")


def test_withheld_columns_are_absent(canon_db: Path, tmp_path: Path) -> None:
    """`decision_reason` and the source-file columns stay behind this round."""
    out = tmp_path / "out"
    export_canon(canon_db, out)
    columns = set(_rows(out))
    assert not columns & {
        "decision_reason",
        "source_file",
        "source_revision",
        "programming_language",
        "pl_scope",
    }


def test_identity_ok_is_a_real_boolean(canon_db: Path, tmp_path: Path) -> None:
    """SQLite has no bool; the artifact should not make a consumer guess."""
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    out = tmp_path / "out"
    export_canon(canon_db, out)
    schema = pq.read_table(out / "data" / "canon.parquet").schema
    assert schema.field("identity_ok").type == pa.bool_()


def test_an_empty_export_refuses(tmp_path: Path) -> None:
    """Zero rows means the filters or the database are wrong, not that we ship nothing."""
    path = tmp_path / "empty.db"
    conn = sqlite3.connect(path)
    apply_schema_v2(conn)
    conn.commit()
    conn.close()
    with pytest.raises(ExportRefused, match="zero rows"):
        export_canon(path, tmp_path / "out")


def test_the_card_declares_the_licence(canon_db: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    export_canon(canon_db, out)
    card = (out / "README.md").read_text(encoding="utf-8")
    assert f"license: {DECLARED_LICENSE}" in card
    assert DECLARED_LICENSE == "apache-2.0"


def test_the_card_states_the_three_layers(canon_db: Path, tmp_path: Path) -> None:
    """The naming split is the point; the card has to carry it."""
    out = tmp_path / "out"
    export_canon(canon_db, out)
    card = (out / "README.md").read_text(encoding="utf-8")
    assert "the corpus is the evidence" in card.lower()
    assert "legesher/language-corpus" in card
    assert "legesher/language-packs" in card


def test_the_card_separates_row_rung_from_pack_tier(
    canon_db: Path, tmp_path: Path
) -> None:
    """Two ladders that move independently; conflating them is a known failure."""
    out = tmp_path / "out"
    export_canon(canon_db, out)
    assert "Row rung is not pack tier" in (out / "README.md").read_text(
        encoding="utf-8"
    )


def test_push_refuses_without_the_governance_signoff() -> None:
    with pytest.raises(ExportRefused, match="governance-signoff"):
        require_push_approval(None)


def test_push_refuses_without_the_env_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """The flag and the variable are two separate keys on purpose."""
    monkeypatch.delenv(PUSH_ENV_VAR, raising=False)
    with pytest.raises(ExportRefused, match=PUSH_ENV_VAR):
        require_push_approval("CORE-1502")


def test_push_refuses_an_unrepeated_non_default_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(TARGET_OVERRIDE_ENV_VAR, raising=False)
    with pytest.raises(ExportRefused, match="not the canonical"):
        require_intended_target("someone-else/language-canon")


def test_the_canonical_target_needs_no_override() -> None:
    require_intended_target(DEFAULT_TARGET_REPO)


def test_the_rung_correction_moves_native_review_and_is_idempotent(
    canon_db: Path,
) -> None:
    """One native reviewer earns `experimental`, never `reviewed`."""
    conn = sqlite3.connect(canon_db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        first = correct(conn)
        second = correct(conn)
        rung = conn.execute(
            "SELECT status FROM canon_selections WHERE decided_by = 'reviewer_one_review'"
        ).fetchone()["status"]
    finally:
        conn.close()

    assert first["moved"] == 1
    assert second["moved"] == 0
    assert second["already_correct"] == 1
    assert rung == "experimental"


def test_the_rung_correction_dry_run_reports_and_writes_nothing(
    canon_db: Path,
) -> None:
    """A dry run that always reports zero reads as 'nothing to do'."""
    conn = sqlite3.connect(canon_db)
    conn.row_factory = sqlite3.Row
    try:
        result = correct(conn, dry_run=True)
        rung = conn.execute(
            "SELECT status FROM canon_selections WHERE decided_by = 'reviewer_one_review'"
        ).fetchone()["status"]
    finally:
        conn.close()

    assert result["moved"] == 1
    assert rung == "machine"


def test_a_stray_parquet_refuses_the_export(canon_db: Path, tmp_path: Path) -> None:
    """Every *.parquet in data/ is push-eligible, so a leftover would publish.

    Writing `canon.parquet` overwrites only itself. Without this guard a
    previous run's differently-named file rides into the dataset repo beside
    the real one and survives the public flip.
    """
    out = tmp_path / "out"
    export_canon(canon_db, out)
    (out / "data" / "canon-OLD-REVISION.parquet").write_text("stale")

    with pytest.raises(ExportRefused, match="does not write"):
        export_canon(canon_db, out)


def test_a_dangling_concept_refuses_rather_than_vanishing(
    canon_db: Path, tmp_path: Path
) -> None:
    """The concepts join is INNER: an orphan row would disappear silently."""
    conn = sqlite3.connect(canon_db)
    # Drop the concept out from under a canon row without touching the row.
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("DELETE FROM concepts WHERE id = 1")
    conn.commit()
    conn.close()

    with pytest.raises(ExportRefused, match="survived the concepts join"):
        export_canon(canon_db, tmp_path / "out")


def test_the_correction_deletes_only_the_targeted_scope(canon_db: Path) -> None:
    """One option can be canon under two targets with the same uid.

    A delete keyed on option_uid would remove both rows and restore one,
    silently dropping the other target's selection.
    """
    conn = sqlite3.connect(canon_db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # Give the reviewed Chinese option a second, JavaScript-scoped canon row,
    # exactly as `if` in Arabic has today.
    conn.execute(
        "INSERT INTO canon_selections (concept_id, locale, programming_language, "
        "option_uid, surface_form, status, decided_by, source_file) "
        "VALUES (1, 'zh-Hans', 'javascript', ?, '真实', 'machine', "
        "'automated', 'libs/i18n/canon/zh-Hans.toml')",
        (OPT_ZH,),
    )
    conn.commit()

    try:
        correct(conn)
        surviving = conn.execute(
            "SELECT pl_scope, status FROM canon_selections "
            "WHERE option_uid = ? ORDER BY pl_scope",
            (OPT_ZH,),
        ).fetchall()
    finally:
        conn.close()

    assert [(row["pl_scope"], row["status"]) for row in surviving] == [
        ("javascript", "machine"),
        ("python", "experimental"),
    ]


def _locale_rows(out_dir: Path) -> dict[str, list]:
    pq = pytest.importorskip("pyarrow.parquet")
    return pq.read_table(out_dir / "data" / "locales.parquet").to_pydict()


def test_the_locales_config_has_one_row_per_canon_locale(
    canon_db: Path, tmp_path: Path
) -> None:
    out = tmp_path / "out"
    export_canon(canon_db, out)
    assert _locale_rows(out)["locale"] == sorted(set(_rows(out)["locale"]))


def test_locale_counts_are_derived_from_the_canon_rows(
    canon_db: Path, tmp_path: Path
) -> None:
    """The two configs cannot disagree, because one is counted from the other."""
    out = tmp_path / "out"
    export_canon(canon_db, out)
    canon, locales = _rows(out), _locale_rows(out)

    assert sum(locales["decisions"]) == len(canon["locale"])
    for index, locale in enumerate(locales["locale"]):
        rungs = [
            canon["status"][i]
            for i, row_locale in enumerate(canon["locale"])
            if row_locale == locale
        ]
        assert locales["decisions"][index] == len(rungs)
        assert locales["experimental"][index] == rungs.count("experimental")
        assert locales["machine"][index] == rungs.count("machine")


def test_language_attributes_live_only_in_the_locales_config(
    canon_db: Path, tmp_path: Path
) -> None:
    """Normalised on purpose, unlike the packs dataset.

    The packs `vocabulary` config denormalised language_name / native_name /
    rtl / tier into 46,512 rows, which means a locale's tier has to be updated
    in two places and can drift. Here the attributes exist once and `canon`
    joins on `locale`.
    """
    out = tmp_path / "out"
    export_canon(canon_db, out)
    canon_columns = set(_rows(out))
    assert not canon_columns & {"language_name", "native_name", "rtl"}
    assert {"language_name", "native_name", "rtl"} <= set(_locale_rows(out))


def test_pack_tier_is_absent_from_the_canon_dataset(
    canon_db: Path, tmp_path: Path
) -> None:
    """Row rung and pack tier are two ladders; carrying both here conflates them."""
    out = tmp_path / "out"
    export_canon(canon_db, out)
    assert "tier" not in set(_rows(out))
    assert "tier" not in set(_locale_rows(out))


def test_a_locale_with_no_metadata_row_refuses(canon_db: Path, tmp_path: Path) -> None:
    """The artifact must not name a language it cannot describe."""
    conn = sqlite3.connect(canon_db)
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("DELETE FROM locales WHERE tag = 'zh-Hans'")
    conn.commit()
    conn.close()

    with pytest.raises(ExportRefused, match="no row in the locales table"):
        export_canon(canon_db, tmp_path / "out")
