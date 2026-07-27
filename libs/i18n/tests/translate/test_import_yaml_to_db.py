"""Integration tests for the YAML -> database importer (CORE-1400).

``import_yaml_file`` has to resolve each pack slot to a term row, but a
YAML section maps to *several* term categories: ``builtins`` covers
``builtin_func``, ``builtin_type`` and ``special_constant``. Assuming
``builtin_func`` for the whole section made every pack's
``builtins.type`` slot request a category matching neither stored
``type`` row (``builtin_type`` and ``keyword``). ``get_or_create_term``
raised on the ambiguity, the per-term ``except Exception`` swallowed it,
and the row was silently skipped — one slot per language's ``3.10.yml``,
with 14 ``builtin_type`` and 2 ``special_constant`` pack terms one
row-split away from the same failure.

These tests run the real importer against a database that holds the real
dual-slot ``type`` rows and assert nothing is dropped.
"""

import pytest
import yaml

from legesher_i18n.db import TranslationDatabase
from legesher_i18n.term_definitions import YAML_SECTION_CATEGORIES, classify_term
from scripts.translate.import_yaml_to_db import import_yaml_file, resolve_term_id

# A pack in the shipped shape: every ``builtins`` category is represented,
# and ``type`` appears in both ``keywords`` and ``builtins`` with different
# values (22 shipped languages really do differ across those two slots).
FIXTURE_PACK = {
    "language": "xx",
    "target": "python",
    "version": "3.10",
    "keywords": {
        "def": "definir",
        "if": "si",
        "type": "genero",  # PEP 695 soft keyword slot
    },
    "builtins": {
        "print": "imprimir",  # builtin_func
        "bool": "booleano",  # builtin_type
        "type": "tipo",  # builtin_type, same name as the keyword above
        "ellipsis": "elipsis",  # special_constant
        "# a comment key, not a slot": None,
    },
    "exceptions": {"valueerror": "errordevalor"},
    "reserved_words": {"self": "propio"},
    "metadata": {"generated_by": "test"},
}

# keywords (3) + builtins (4 real slots) + exceptions (1). ``reserved_words``
# is outside the importer's section list, and the comment key is not a slot.
EXPECTED_IMPORTED = 8

# The term rows as the real database holds them, dual-slot ``type`` included.
SEEDED_TERMS = [
    ("def", "keyword"),
    ("if", "keyword"),
    ("print", "builtin_func"),
    ("bool", "builtin_type"),
    ("ellipsis", "special_constant"),
    ("valueerror", "exception"),
    ("type", "builtin_type"),
]


@pytest.fixture
def db(tmp_path):
    """Database with the fixture language registered (translations FK)."""
    db_instance = TranslationDatabase(db_path=str(tmp_path / "translations.db"))
    conn = db_instance._get_connection()
    conn.execute(
        "INSERT INTO languages (code, name, native_name) VALUES (?, ?, ?)",
        ("xx", "Test Language", "Test Language"),
    )
    conn.commit()
    yield db_instance
    db_instance.close()


@pytest.fixture
def terms(db):
    """Seed the term rows, returning {(name, category): term_id}."""
    ids = {
        (name, category): db.get_or_create_term(name, "python", category)
        for name, category in SEEDED_TERMS
    }
    ids[("type", "keyword")] = db.get_or_create_term(
        "type",
        "python",
        "keyword",
        subcategory="soft_keyword",
        allow_duplicate_name=True,
    )
    assert ids[("type", "keyword")] != ids[("type", "builtin_type")]
    return ids


@pytest.fixture
def pack_file(tmp_path):
    path = tmp_path / "3.10.yml"
    path.write_text(yaml.safe_dump(FIXTURE_PACK, allow_unicode=True), encoding="utf-8")
    return path


@pytest.mark.integration
class TestImportYamlFile:
    """The importer must not drop pack values it cannot categorise."""

    def test_dual_slot_pack_import_drops_nothing(self, db, terms, pack_file):
        """The regression test: a skip here is a lost pack value."""
        imported, skipped = import_yaml_file(pack_file, "xx", db)

        assert (imported, skipped) == (EXPECTED_IMPORTED, 0)

    def test_type_lands_in_the_slot_its_section_names(self, db, terms, pack_file):
        """The two 'type' slots keep their own values, not each other's."""
        import_yaml_file(pack_file, "xx", db)

        builtin = db.get_translations(
            term_id=terms[("type", "builtin_type")], language_code="xx"
        )
        keyword = db.get_translations(
            term_id=terms[("type", "keyword")], language_code="xx"
        )
        assert [row["translation"] for row in builtin] == ["tipo"]
        assert [row["translation"] for row in keyword] == ["genero"]

    def test_import_creates_no_new_term_rows(self, db, terms, pack_file):
        """Resolution reuses rows; it never adds a third 'type'."""
        before = len(db.get_terms(programming_language="python"))

        import_yaml_file(pack_file, "xx", db)

        assert len(db.get_terms(programming_language="python")) == before

    def test_null_slots_are_the_only_legitimate_skip(self, db, terms, tmp_path):
        """An unfilled slot is a skip; a filled one never is."""
        pack = {**FIXTURE_PACK, "builtins": {**FIXTURE_PACK["builtins"], "sum": None}}
        path = tmp_path / "3.10.yml"
        path.write_text(yaml.safe_dump(pack, allow_unicode=True), encoding="utf-8")

        imported, skipped = import_yaml_file(path, "xx", db)

        assert (imported, skipped) == (EXPECTED_IMPORTED, 1)


@pytest.mark.unit
class TestResolveTermId:
    """Section -> category resolution, in order."""

    def test_section_order_beats_lowest_id(self, db, terms):
        """'builtins' must reach the builtin row, 'keywords' the keyword row."""
        assert (
            resolve_term_id(db, "type", YAML_SECTION_CATEGORIES["builtins"])
            == terms[("type", "builtin_type")]
        )
        assert (
            resolve_term_id(db, "type", YAML_SECTION_CATEGORIES["keywords"])
            == terms[("type", "keyword")]
        )

    def test_later_categories_in_the_section_resolve(self, db, terms):
        """'builtin_type' and 'special_constant' are not the first try."""
        assert (
            resolve_term_id(db, "bool", YAML_SECTION_CATEGORIES["builtins"])
            == terms[("bool", "builtin_type")]
        )
        assert (
            resolve_term_id(db, "ellipsis", YAML_SECTION_CATEGORIES["builtins"])
            == terms[("ellipsis", "special_constant")]
        )

    def test_created_row_takes_the_category_the_term_lists_give_it(self, db):
        """A created row carries its real category, not the section's first.

        CORE-1400: ``categories[0]`` filed every unseen ``builtins`` slot as
        ``builtin_func``, contradicting ``classify_term`` on 21 rows of a
        bootstrap import.
        """
        for name, expected in (
            ("bool", "builtin_type"),  # first category is builtin_func
            ("ellipsis", "special_constant"),  # last category in the section
            ("print", "builtin_func"),  # genuinely the first category
        ):
            term_id = resolve_term_id(db, name, YAML_SECTION_CATEGORIES["builtins"])

            row = db.get_term_by_name(name, "python")
            assert row is not None
            assert row["id"] == term_id
            assert row["category"] == expected, name
            assert row["category"] == classify_term(name, python_version="3.13"), name

    def test_the_two_type_slots_create_two_rows(self, db):
        """A bootstrap import must not let one row absorb both 'type' slots.

        ``builtins.type`` and ``keywords.type`` are separate pack slots; 22
        shipped languages give them different values. Reusing the one
        existing row for the second slot files both under it.
        """
        builtin_id = resolve_term_id(db, "type", YAML_SECTION_CATEGORIES["builtins"])
        keyword_id = resolve_term_id(db, "type", YAML_SECTION_CATEGORIES["keywords"])

        assert builtin_id != keyword_id
        rows = {
            row["id"]: row["category"]
            for row in db.get_terms(programming_language="python")
            if row["name"] == "type"
        }
        assert rows == {builtin_id: "builtin_type", keyword_id: "keyword"}

    def test_unknown_name_falls_back_to_the_primary_category(self, db):
        """No canonical list knows the name, so the section's first wins.

        The fallback is deliberate, not a classification: ``classify_term``
        answers ``unknown`` here and there is no second slot to claim, so the
        single row is reused rather than split.
        """
        assert classify_term("unheardof", python_version="3.13") == "unknown"

        term_id = resolve_term_id(db, "unheardof", YAML_SECTION_CATEGORIES["builtins"])

        row = db.get_term_by_name("unheardof", "python")
        assert row is not None
        assert row["id"] == term_id
        assert row["category"] == "builtin_func"

        # A second section for the same unknown name reuses the row.
        assert (
            resolve_term_id(db, "unheardof", YAML_SECTION_CATEGORIES["keywords"])
            == term_id
        )
