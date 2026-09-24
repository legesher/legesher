"""Guards on the generated schema v2 reference (CORE-2232).

The last hand-written schema reference rotted because nothing failed when
``schema_v2.sql`` moved and the prose did not. These tests pin the property
that replaces it: the generator REFUSES, naming the offender, whenever the SQL
and ``schema_v2.descriptions.yml`` disagree. Each failure mode is produced
for real on a copy of the shipped files, so every assertion here has been
shown to fire.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest
import yaml

_I18N_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _I18N_ROOT / "scripts" / "generate_schema_reference.py"


def _load_module():
    sys.path.insert(0, str(_I18N_ROOT))
    spec = importlib.util.spec_from_file_location("generate_schema_reference", _SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # Registered before exec: @dataclass resolves annotations via sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gen = _load_module()


@pytest.fixture()
def sources(tmp_path: Path) -> dict[str, Path]:
    """Writable copies of the shipped SQL and descriptions."""
    sql = tmp_path / "schema_v2.sql"
    desc = tmp_path / "schema_v2.descriptions.yml"
    sql.write_text(gen.SQL_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    desc.write_text(gen.DESCRIPTIONS_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    return {"sql": sql, "desc": desc}


def _problems(sources: dict[str, Path]) -> list[str]:
    with pytest.raises(gen.SchemaReferenceError) as caught:
        gen.build(sources["sql"], sources["desc"])
    return caught.value.problems


def _edit_sql(sources: dict[str, Path], old: str, new: str) -> None:
    text = sources["sql"].read_text(encoding="utf-8")
    assert text.count(old) == 1, f"fixture anchor not unique: {old!r}"
    sources["sql"].write_text(text.replace(old, new), encoding="utf-8")


def _edit_desc(sources: dict[str, Path], mutate) -> None:
    data = yaml.safe_load(sources["desc"].read_text(encoding="utf-8"))
    mutate(data)
    sources["desc"].write_text(
        yaml.safe_dump(data, allow_unicode=True), encoding="utf-8"
    )


def _one_matching(problems: list[str], pattern: str) -> str:
    hits = [p for p in problems if re.search(pattern, p)]
    assert hits, f"no problem matches {pattern!r}; got:\n" + "\n".join(problems)
    return hits[0]


# ---------------------------------------------------------------------------
# The committed page, and the parse behind it
# ---------------------------------------------------------------------------


def test_committed_reference_is_current() -> None:
    """The committed page is exactly what the generator produces today.

    ``make check-generated`` runs the same comparison; this puts it in the
    i18n suite too, so a stale page fails wherever the tests run.
    """
    committed = (gen.OUT_DIR / gen.OUT_NAME).read_text(encoding="utf-8")
    assert gen.build() == committed, (
        f"{gen.OUT_NAME} is stale; run `{gen.REGENERATE_COMMAND}` and commit it"
    )


def test_parse_round_trips_against_sqlite() -> None:
    """The text parse agrees with SQLite's own reading of the same DDL."""
    sql_text = gen.SQL_PATH.read_text(encoding="utf-8")
    schema = gen.parse_schema(sql_text)
    assert schema.create_table_count == len(schema.tables) > 0
    assert gen.verify_round_trip(schema, sql_text) == []


def test_round_trip_catches_a_column_the_parse_dropped() -> None:
    """A parser bug that loses a column fails the build, naming the table.

    This is the bug class that bit the first draft: `checked_at` begins with
    CHECK and was read as a table constraint.
    """
    sql_text = gen.SQL_PATH.read_text(encoding="utf-8")
    schema = gen.parse_schema(sql_text)
    schema.tables["option_validations"].columns.pop()
    problems = gen.verify_round_trip(schema, sql_text)
    _one_matching(problems, r"option_validations columns parsed as")


def test_round_trip_catches_a_foreign_key_the_parse_dropped() -> None:
    sql_text = gen.SQL_PATH.read_text(encoding="utf-8")
    schema = gen.parse_schema(sql_text)
    schema.tables["canon_selections"].foreign_keys.pop()
    problems = gen.verify_round_trip(schema, sql_text)
    _one_matching(problems, r"canon_selections foreign keys")


def test_every_column_is_rendered() -> None:
    """Nothing parsed is dropped on the way to the page."""
    page = gen.build()
    schema = gen.parse_schema(gen.SQL_PATH.read_text(encoding="utf-8"))
    for table in schema.tables.values():
        assert f"### `{table.name}`" in page
        for column in table.columns:
            assert f"**`{column.name}`**" in page, f"{table.name}.{column.name}"
    for name in [*schema.views, *schema.triggers, *schema.indexes]:
        assert f"`{name}`" in page, name


# ---------------------------------------------------------------------------
# The two-sided check: SQL without a description, description without SQL
# ---------------------------------------------------------------------------


def test_undescribed_table_fails_naming_it(sources) -> None:
    _edit_sql(
        sources,
        "CREATE TABLE import_sources (",
        "CREATE TABLE ghost_ledger (id INTEGER PRIMARY KEY);\n\nCREATE TABLE import_sources (",
    )
    _one_matching(_problems(sources), r"table `ghost_ledger` has no description")


def test_orphaned_table_description_fails_naming_it(sources) -> None:
    _edit_desc(
        sources,
        lambda d: d["tables"].__setitem__(
            "reviews", {"description": "A table that was never built.", "columns": {}}
        ),
    )
    _one_matching(_problems(sources), r"tables\.reviews: describes table `reviews`")


def test_undescribed_column_fails_naming_it(sources) -> None:
    _edit_sql(
        sources,
        "    spec_url    TEXT,\n",
        "    spec_url    TEXT,\n    homepage    TEXT,\n",
    )
    _one_matching(
        _problems(sources),
        r"column `programming_languages\.homepage` has no description",
    )


def test_orphaned_column_description_fails_naming_it(sources) -> None:
    _edit_desc(
        sources,
        lambda d: d["tables"]["options"]["columns"].__setitem__("sources", "Stale."),
    )
    _one_matching(_problems(sources), r"describes column `options\.sources`")


def test_renamed_column_fails_on_both_sides(sources) -> None:
    """A rename in the SQL alone is caught twice: new name bare, old name orphaned."""
    _edit_sql(sources, "    spec_url    TEXT,\n", "    spec_link   TEXT,\n")
    problems = _problems(sources)
    _one_matching(problems, r"`programming_languages\.spec_link` has no description")
    _one_matching(problems, r"describes column `programming_languages\.spec_url`")


@pytest.mark.parametrize(
    ("anchor", "addition", "expected"),
    [
        (
            "CREATE VIEW locale_fallback AS",
            "CREATE VIEW ghost_view AS SELECT 1 AS one;\n\n",
            r"view `ghost_view` has no description",
        ),
        (
            "CREATE TRIGGER trg_options_no_delete",
            "CREATE TRIGGER trg_ghost BEFORE DELETE ON concepts\n"
            "BEGIN SELECT RAISE(ABORT, 'no'); END;\n\n",
            r"trigger `trg_ghost` has no description",
        ),
    ],
)
def test_undescribed_view_or_trigger_fails_naming_it(
    sources, anchor, addition, expected
):
    text = sources["sql"].read_text(encoding="utf-8")
    sources["sql"].write_text(
        text.replace(anchor, addition + anchor, 1), encoding="utf-8"
    )
    _one_matching(_problems(sources), expected)


@pytest.mark.parametrize(
    ("group", "name", "expected"),
    [
        ("views", "ghost_view", r"views\.ghost_view: describes view"),
        ("triggers", "trg_ghost", r"triggers\.trg_ghost: describes trigger"),
        ("sections", "LEGACY", r"sections\.LEGACY: describes section banner"),
        ("pragmas", "journal_mode", r"pragmas\.journal_mode: describes pragma"),
    ],
)
def test_orphaned_description_fails_naming_it(sources, group, name, expected):
    _edit_desc(sources, lambda d: d[group].__setitem__(name, "Describes nothing."))
    _one_matching(_problems(sources), expected)


def test_orphaned_index_note_fails_naming_it(sources) -> None:
    _edit_desc(
        sources,
        lambda d: d["tables"]["options"]["indexes"].__setitem__("idx_gone", "Removed."),
    )
    _one_matching(_problems(sources), r"no index `idx_gone` on `options`")


def test_new_section_banner_needs_a_description(sources) -> None:
    rule = "-- " + "=" * 75
    _edit_sql(
        sources,
        "CREATE TABLE message_templates (",
        f"{rule}\n-- ARCHIVE\n{rule}\n\nCREATE TABLE message_templates (",
    )
    _one_matching(_problems(sources), r"section banner `ARCHIVE` has no description")


def test_seed_insert_needs_a_description(sources) -> None:
    _edit_desc(sources, lambda d: d["tables"]["review_rungs"].pop("seed"))
    _one_matching(
        _problems(sources), r"seed INSERT into `review_rungs` has no description"
    )


# ---------------------------------------------------------------------------
# Enumerated values
# ---------------------------------------------------------------------------


def test_new_enum_value_needs_a_description(sources) -> None:
    """A value added to a described CHECK list cannot ship undescribed."""
    _edit_sql(sources, "'supersedes')),", "'supersedes', 'deprecates')),")
    _one_matching(
        _problems(sources),
        r"value 'deprecates' of `concept_relations\.relation` has no description",
    )


def test_removed_enum_value_leaves_an_orphan(sources) -> None:
    _edit_sql(sources, "'contrast',\n", "")
    _one_matching(_problems(sources), r"'contrast' is not an allowed value")


def test_values_on_a_column_without_a_check_list_fail(sources) -> None:
    _edit_desc(
        sources,
        lambda d: d["tables"]["locales"]["columns"].__setitem__(
            "name", {"description": "English name.", "values": {"x": "y"}}
        ),
    )
    _one_matching(_problems(sources), r"`locales\.name` has no CHECK")


# ---------------------------------------------------------------------------
# The SQL stays minimal, and the prose stays honest
# ---------------------------------------------------------------------------


def test_prose_comment_in_the_sql_fails(sources) -> None:
    """Prose that creeps back into the DDL is refused: the page would not show it."""
    _edit_sql(
        sources,
        "CREATE TABLE concepts (",
        "-- The semantic core.\nCREATE TABLE concepts (",
    )
    _one_matching(_problems(sources), r"schema_v2\.sql:\d+: comment outside the header")


def test_trailing_comment_in_the_sql_fails(sources) -> None:
    _edit_sql(
        sources, "    spec_url    TEXT,\n", "    spec_url    TEXT,  -- the spec\n"
    )
    _one_matching(_problems(sources), r"comment outside the header")


def test_duplicate_description_key_fails(sources) -> None:
    """Plain YAML keeps the last duplicate; this loader refuses it."""
    text = sources["desc"].read_text(encoding="utf-8")
    anchor = "      spec_url: |\n"
    assert text.count(anchor) == 1
    sources["desc"].write_text(
        text.replace(anchor, "      spec_url: A first description.\n" + anchor),
        encoding="utf-8",
    )
    _one_matching(_problems(sources), r"duplicate key 'spec_url'")


def test_dangling_cross_reference_fails(sources) -> None:
    _edit_desc(
        sources,
        lambda d: d.__setitem__("overview", d["overview"] + "\nSee [[deep_contexts]]."),
    )
    _one_matching(
        _problems(sources), r"cross-reference \[\[deep_contexts\]\] names nothing"
    )


def test_dangling_column_cross_reference_fails(sources) -> None:
    _edit_desc(
        sources, lambda d: d.__setitem__("scope", d["scope"] + "\n[[options.sources]]")
    )
    _one_matching(_problems(sources), r"\[\[options\.sources\]\] names no column")


def test_placeholder_description_fails(sources) -> None:
    _edit_desc(
        sources, lambda d: d["tables"]["locales"]["columns"].__setitem__("name", "TODO")
    )
    _one_matching(_problems(sources), r"tables\.locales\.columns\.name: a placeholder")


def test_unrecognised_statement_fails(sources) -> None:
    _edit_sql(
        sources,
        "CREATE TABLE concepts (",
        "CREATE VIRTUAL TABLE concept_search USING fts5(slug);\n\nCREATE TABLE concepts (",
    )
    _one_matching(_problems(sources), r"unrecognised statement")


def test_object_before_the_first_banner_fails(sources) -> None:
    """The page renders by section, so an unsectioned table would vanish from it."""
    _edit_sql(
        sources,
        "PRAGMA foreign_keys = ON;",
        "PRAGMA foreign_keys = ON;\n\nCREATE TABLE stray (id INTEGER PRIMARY KEY);",
    )
    _one_matching(_problems(sources), r"comes before the first section banner")


def test_duplicate_section_banner_fails(sources) -> None:
    rule = "-- " + "=" * 75
    _edit_sql(
        sources,
        "CREATE TABLE message_templates (",
        f"{rule}\n-- REFERENCE\n{rule}\n\nCREATE TABLE message_templates (",
    )
    _one_matching(_problems(sources), r"banner `REFERENCE` appears more than once")


def test_second_seed_insert_fails(sources) -> None:
    """A second INSERT must not silently replace the first one's rows on the page."""
    _edit_sql(
        sources,
        "CREATE TABLE contributors (",
        "INSERT INTO review_rungs (rung, rank, weight, counts_as_native, policy_version) "
        "VALUES ('guest', 9, 0.0, 0, 'v0-draft');\n\nCREATE TABLE contributors (",
    )
    _one_matching(_problems(sources), r"a second seed INSERT into review_rungs")


def test_if_not_exists_table_fails_cleanly(sources) -> None:
    _edit_sql(
        sources, "CREATE TABLE concepts (", "CREATE TABLE IF NOT EXISTS concepts ("
    )
    _one_matching(_problems(sources), r"cannot read a table name")


def test_header_prose_reaches_the_page(sources) -> None:
    """The header is the one place prose may sit in the SQL, so it is rendered."""
    _edit_sql(
        sources,
        "-- endorsement corpus.\n",
        "-- endorsement corpus.\n-- Header note that must not hide.\n",
    )
    assert "Header note that must not hide." in gen.build(
        sources["sql"], sources["desc"]
    )


# ---------------------------------------------------------------------------
# Adversarial review of PR #224: each of these once passed the gate with a
# wrong or incomplete page
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        # A bracket identifier is quoted to SQLite but was not to the lexer, so
        # a `[/*]` ... `[*/]` pair hid a live UPDATE the page never showed.
        (
            "CREATE TABLE concepts (",
            "CREATE VIEW zz AS SELECT 1 AS [/*]; UPDATE review_rungs SET weight = 100; "
            "SELECT 1 AS [*/];\nCREATE TABLE concepts (",
            r"bracket-quoted identifiers are not part",
        ),
        (
            "    spec_url    TEXT,\n",
            '    "spec url"  TEXT,\n',
            r"double-quoted identifiers",
        ),
        (
            "    spec_url    TEXT,\n",
            "    `spec_url`  TEXT,\n",
            r"backtick-quoted identifiers",
        ),
        (
            "PRAGMA foreign_keys = ON;",
            "PRAGMA foreign_keys = ON; /* SMUGGLED */",
            r"block comments are not part",
        ),
    ],
)
def test_quoting_the_lexer_cannot_see_through_is_refused(sources, old, new, expected):
    _edit_sql(sources, old, new)
    _one_matching(_problems(sources), expected)


def test_two_enum_checks_on_one_column_fail(sources) -> None:
    """The page shows one allowed-values list; a second IN-list would vanish."""
    _edit_sql(
        sources,
        "CHECK (direction IN ('ltr', 'rtl'))",
        "CHECK (direction IN ('ltr')) CHECK (direction IN ('ltr', 'rtl'))",
    )
    _one_matching(_problems(sources), r"column direction has 2 IN-list CHECKs")


def test_round_trip_catches_an_object_on_the_wrong_table() -> None:
    sql_text = gen.SQL_PATH.read_text(encoding="utf-8")
    schema = gen.parse_schema(sql_text)
    schema.triggers["trg_options_withdrawal_is_final"].table = "concepts"
    schema.indexes["idx_terms_name"].table = "locales"
    problems = gen.verify_round_trip(schema, sql_text)
    _one_matching(
        problems, r"trigger trg_options_withdrawal_is_final parsed as on concepts"
    )
    _one_matching(problems, r"index idx_terms_name parsed as on locales")


def test_round_trip_catches_seed_rows_the_build_changed(sources) -> None:
    """A trigger (or anything else) that rewrites the seed must not go unseen."""
    _edit_sql(
        sources,
        "INSERT INTO review_rungs",
        "CREATE TRIGGER trg_reweigh AFTER INSERT ON review_rungs "
        "BEGIN UPDATE review_rungs SET weight = 100 WHERE rung = NEW.rung; END;\n\n"
        "INSERT INTO review_rungs",
    )
    _edit_desc(sources, lambda d: d["triggers"].__setitem__("trg_reweigh", "Reweighs."))
    _one_matching(_problems(sources), r"seed rows of review_rungs as parsed are not")


def test_index_on_a_misspelled_table_name_fails(sources) -> None:
    _edit_sql(sources, "ON terms(name);", "ON Terms(name);")
    _one_matching(_problems(sources), r"index `idx_terms_name` is on `Terms`")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("A note.\n<!-- draft", r"would hide or restructure"),
        ("A note.\n\n```text\nnever closed", r"unclosed code fence"),
        ("A note.\n\n## Not a heading here", r"would hide or restructure"),
        ("A note.\n\n<details><summary>x</summary>", r"would hide or restructure"),
    ],
)
def test_markdown_that_would_break_the_page_fails(sources, text, expected):
    _edit_desc(sources, lambda d: d["sections"].__setitem__("REFERENCE", text))
    _one_matching(_problems(sources), expected)


def test_non_string_value_keys_fail_instead_of_crashing(sources) -> None:
    _edit_desc(
        sources,
        lambda d: d["tables"]["locales"]["columns"].__setitem__(
            "in_registry",
            {"description": "Published.", "values": {0: "No.", 1: "Yes."}},
        ),
    )
    _one_matching(
        _problems(sources), r"in_registry\.values: keys \[0, 1\] are not strings"
    )


def test_indexes_given_as_a_list_fail_instead_of_crashing(sources) -> None:
    _edit_desc(sources, lambda d: d["tables"]["options"].__setitem__("indexes", ["x"]))
    _one_matching(_problems(sources), r"tables\.options\.indexes: expected a mapping")


@pytest.mark.parametrize(
    "ref", ["[[ message_templates ]]", "[[dropped-table]]", "[[terms.name.old]]"]
)
def test_malformed_cross_reference_fails(sources, ref) -> None:
    _edit_desc(sources, lambda d: d.__setitem__("scope", d["scope"] + f"\n{ref}"))
    _one_matching(_problems(sources), r"malformed cross-reference")


def test_duplicate_pragma_fails(sources) -> None:
    _edit_sql(
        sources,
        "PRAGMA foreign_keys = ON;",
        "PRAGMA foreign_keys = ON;\nPRAGMA foreign_keys = OFF;",
    )
    _one_matching(_problems(sources), r"PRAGMA foreign_keys is set twice")


def test_on_update_action_is_rendered(sources) -> None:
    _edit_sql(
        sources,
        "parent_tag           TEXT REFERENCES locales(tag) ON DELETE RESTRICT,",
        "parent_tag           TEXT REFERENCES locales(tag) ON DELETE RESTRICT ON UPDATE CASCADE,",
    )
    assert "on delete restrict on update cascade" in gen.build(
        sources["sql"], sources["desc"]
    )


def test_enum_literal_whitespace_is_kept(sources) -> None:
    _edit_sql(sources, "'in_progress', 'planned'", "'in  progress', 'planned'")
    assert "`in  progress`" in gen.build(sources["sql"], sources["desc"])


def test_rendered_lines_carry_no_trailing_whitespace(sources) -> None:
    """A trailing space would be rewritten by the whitespace hook, and the page
    could then never match its own regeneration."""
    _edit_desc(
        sources,
        lambda d: d["tables"]["programming_languages"]["columns"].__setitem__(
            "spec_url", "Link to the specification. \nSecond line."
        ),
    )
    page = gen.build(sources["sql"], sources["desc"])
    assert not [line for line in page.splitlines() if line != line.rstrip()]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("<textarea>\nswallows everything after it", r"would hide or restructure"),
        ("<pre>\nalso runs to an end tag", r"would hide or restructure"),
        ("A processing instruction <?php", r"would hide or restructure"),
        ("Fake heading\n============", r"is a heading"),
        ("Fake heading\n---", r"is a heading"),
    ],
)
def test_raw_html_blocks_and_setext_headings_fail(sources, text, expected):
    """Second review round: these restructured the page and passed the gate."""
    _edit_desc(sources, lambda d: d["sections"].__setitem__("REFERENCE", text))
    _one_matching(_problems(sources), expected)


def test_a_rule_inside_a_code_fence_is_not_a_heading(sources) -> None:
    text = "An example:\n\n```text\nvalue\n-----\n```"
    _edit_desc(sources, lambda d: d["sections"].__setitem__("REFERENCE", text))
    assert gen.build(sources["sql"], sources["desc"])


def test_section_anchor_follows_github_slugs(sources) -> None:
    rule = "-- " + "=" * 75
    _edit_sql(
        sources,
        "CREATE TABLE message_templates (",
        f"{rule}\n-- ARCHIVE (LEGACY)\n{rule}\n\nCREATE TABLE message_templates (",
    )
    _edit_desc(
        sources, lambda d: d["sections"].__setitem__("ARCHIVE (LEGACY)", "Old tables.")
    )
    page = gen.build(sources["sql"], sources["desc"])
    assert "(#archive-legacy)" in page
    assert "## Archive (Legacy)" in page


def test_seed_cell_newline_does_not_break_the_table(sources) -> None:
    _edit_sql(
        sources,
        "'Unauthenticated signal. Recorded, weighted zero; brigading evidence.'",
        "'Unauthenticated signal.' || char(10) || '| forged | row |'",
    )
    page = gen.build(sources["sql"], sources["desc"])
    rows = [line for line in page.splitlines() if line.startswith("| ")]
    assert not [r for r in rows if r.startswith("| forged")]
    assert "Unauthenticated signal.<br>" in page


def test_header_fence_outlasts_tildes_in_the_header(sources) -> None:
    _edit_sql(
        sources,
        "-- endorsement corpus.\n",
        "-- endorsement corpus.\n-- ~~~~ tilde run\n",
    )
    page = gen.build(sources["sql"], sources["desc"])
    assert "~~~~~text" in page and "~~~~ tilde run" in page


def test_cross_reference_inside_inline_code_is_left_as_written(sources) -> None:
    _edit_desc(
        sources, lambda d: d.__setitem__("scope", d["scope"] + "\nWrite `[[options]]`.")
    )
    assert "`[[options]]`" in gen.build(sources["sql"], sources["desc"])


# ---------------------------------------------------------------------------
# The command line
# ---------------------------------------------------------------------------


def test_cli_refuses_and_writes_nothing(sources, tmp_path, capsys) -> None:
    _edit_sql(
        sources,
        "    spec_url    TEXT,\n",
        "    spec_url    TEXT,\n    homepage    TEXT,\n",
    )
    out = tmp_path / "out"
    code = gen.main(
        [
            "--sql",
            str(sources["sql"]),
            "--descriptions",
            str(sources["desc"]),
            "--out",
            str(out),
        ]
    )
    assert code == 1
    assert "programming_languages.homepage" in capsys.readouterr().err
    assert not (out / gen.OUT_NAME).exists()


def test_cli_writes_the_page(sources, tmp_path) -> None:
    out = tmp_path / "out"
    code = gen.main(
        [
            "--sql",
            str(sources["sql"]),
            "--descriptions",
            str(sources["desc"]),
            "--out",
            str(out),
        ]
    )
    assert code == 0
    assert (out / gen.OUT_NAME).read_text(encoding="utf-8") == gen.build()
