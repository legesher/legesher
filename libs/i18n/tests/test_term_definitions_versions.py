"""The term inventory is version-aware, one table drives every accessor.

``term_definitions.VERSION_ADDITIONS`` records what each Python release added.
``get_keywords_for_version``, ``get_builtins_for_version``,
``get_exceptions_for_version``, ``classify_term`` and
``get_all_terms_by_category`` all read it, so a release is registered once.

Nothing here names a release in an assertion: every case is taken from the
table, so the next release is covered the day its row is added.
"""

import pytest

from legesher_i18n import term_definitions as td

CATEGORIES = ("keyword", "builtin_func", "builtin_type", "exception")


def _key(version: str) -> tuple[int, int]:
    major, minor = version.split(".")[:2]
    return int(major), int(minor)


def _previous(version: str) -> str:
    major, minor = _key(version)
    return f"{major}.{minor - 1}"


#: ``(version, category, term)`` for every term the table adds.
ADDITIONS = [
    pytest.param(version, category, term, id=f"{version}-{category}-{term}")
    for version, by_category in td.VERSION_ADDITIONS.items()
    for category, terms in by_category.items()
    for term in terms
]


def _accessor(category: str, version: str) -> list[str]:
    return td.get_all_terms_by_category(version)[category]


def test_the_table_is_not_empty_and_is_ordered_oldest_first():
    versions = list(td.VERSION_ADDITIONS)
    assert versions, "an empty table would make every case below vanish"
    assert versions == sorted(versions, key=_key)
    assert len(ADDITIONS) > len(versions)


def test_the_table_uses_only_the_four_versioned_categories():
    used = {
        category
        for by_category in td.VERSION_ADDITIONS.values()
        for category in by_category
    }
    assert used <= set(CATEGORIES), used - set(CATEGORIES)


@pytest.mark.parametrize(("version", "category", "term"), ADDITIONS)
def test_an_added_term_is_listed_from_its_release_on(version, category, term):
    assert term in _accessor(category, version)
    newest = max(td.VERSION_ADDITIONS, key=_key)
    assert term in _accessor(category, newest)
    major, minor = _key(newest)
    assert term in _accessor(category, f"{major}.{minor + 1}")


@pytest.mark.parametrize(("version", "category", "term"), ADDITIONS)
def test_an_added_term_is_not_listed_before_its_release(version, category, term):
    assert term not in _accessor(category, _previous(version))


@pytest.mark.parametrize(("version", "category", "term"), ADDITIONS)
def test_an_added_term_is_classified_only_from_its_release_on(version, category, term):
    assert td.classify_term(term, version) == category
    before = td.classify_term(term, _previous(version))
    # ``type`` is the one name with two slots: the builtin in every release
    # and the soft keyword from 3.12. Before its keyword release it is still
    # a term, in its other category.
    other_slots = {
        other
        for other in CATEGORIES
        if other != category and term in _accessor(other, _previous(version))
    }
    assert before in (other_slots or {"unknown"}), before
    assert before != category


@pytest.mark.parametrize(("version", "category", "term"), ADDITIONS)
def test_an_added_term_is_a_python_term_only_from_its_release_on(
    version, category, term
):
    assert td.is_python_term(term, version)
    if td.classify_term(term, _previous(version)) == "unknown":
        assert not td.is_python_term(term, _previous(version))


def test_no_term_is_listed_twice_in_one_category():
    newest = max(td.VERSION_ADDITIONS, key=_key)
    for category in CATEGORIES:
        terms = _accessor(category, newest)
        repeated = sorted({term for term in terms if terms.count(term) > 1})
        assert repeated == [], f"{category}: {repeated}"


def test_the_per_category_accessors_agree_with_the_category_table():
    for version in [*td.VERSION_ADDITIONS, _previous(next(iter(td.VERSION_ADDITIONS)))]:
        by_category = td.get_all_terms_by_category(version)
        assert td.get_keywords_for_version(version) == by_category["keyword"]
        assert td.get_exceptions_for_version(version) == by_category["exception"]
        assert td.get_builtins_for_version(version) == (
            by_category["builtin_func"]
            + by_category["builtin_type"]
            + by_category["special_constant"]
        )


def test_versions_compare_as_numbers_not_as_text():
    # As text, "3.9" sorts after "3.10", so a 3.9 request used to be handed
    # the 3.10 soft keywords.
    oldest = next(iter(td.VERSION_ADDITIONS))
    major, minor = _key(oldest)
    assert minor >= 10, "the case below needs a two-digit minor to mean anything"
    for term in td.VERSION_ADDITIONS[oldest].get("keyword", []):
        assert term not in td.get_keywords_for_version(f"{major}.9")
    assert td.VERSION_ADDITIONS[oldest].get("keyword"), "nothing was checked"


def test_the_accessors_hand_out_copies():
    newest = max(td.VERSION_ADDITIONS, key=_key)
    for accessor in (
        td.get_keywords_for_version,
        td.get_builtins_for_version,
        td.get_exceptions_for_version,
    ):
        accessor(newest).append("mutated")
        assert "mutated" not in accessor(newest)
    td.get_all_terms_by_category(newest)["builtin_func"].append("mutated")
    assert "mutated" not in td.BUILTIN_FUNCTIONS
    assert "mutated" not in td.get_all_terms_by_category(newest)["builtin_func"]


def test_every_per_release_list_in_the_module_is_in_the_table():
    # A ``KEYWORDS_3_16 = [...]`` that nobody wired into the table would be
    # exported, importable and ignored by every accessor.
    wired = {
        id(terms)
        for by_category in td.VERSION_ADDITIONS.values()
        for terms in by_category.values()
    }
    prefixes = (
        "KEYWORDS_3_",
        "BUILTIN_FUNCTIONS_3_",
        "BUILTIN_TYPES_3_",
        "EXCEPTIONS_3_",
    )
    per_release = {
        name: value for name, value in vars(td).items() if name.startswith(prefixes)
    }
    assert per_release, "the module no longer names its per-release lists this way"
    unwired = sorted(
        name for name, value in per_release.items() if id(value) not in wired
    )
    assert unwired == [], unwired
    missing_export = sorted(set(per_release) - set(td.__all__))
    assert missing_export == [], missing_export
