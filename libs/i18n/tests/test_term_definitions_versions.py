"""The term inventory is version-aware, and one table drives every accessor.

``term_definitions.VERSION_ADDITIONS`` records what each Python release added.
``get_keywords_for_version``, ``get_builtins_for_version``,
``get_exceptions_for_version``, ``classify_term`` and
``get_all_terms_by_category`` all read it.

Nothing here names a release in an assertion: every case is taken from the
table, so the next release is covered the day its row is added.
"""

import copy

import pytest

from legesher_i18n import term_definitions as td

CATEGORIES = ("keyword", "builtin_func", "builtin_type", "exception")

#: The lists every release starts from, by category, read from the module.
BASE = {
    "keyword": td.KEYWORDS_BASE + td.SPECIAL_VALUES,
    "builtin_func": td.BUILTIN_FUNCTIONS,
    "builtin_type": td.BUILTIN_TYPES,
    "exception": td.EXCEPTIONS,
}


def _key(version: str) -> tuple[int, int]:
    major, minor = version.split(".")[:2]
    return int(major), int(minor)


def _previous(version: str) -> str:
    major, minor = _key(version)
    return f"{major}.{minor - 1}"


def _next(version: str) -> str:
    major, minor = _key(version)
    return f"{major}.{minor + 1}"


REGISTERED = list(td.VERSION_ADDITIONS)

#: Every registered release, the one before the oldest and the one after the newest.
VERSIONS_TO_ASK = [_previous(REGISTERED[0]), *REGISTERED, _next(REGISTERED[-1])]

#: ``(version, category, term)`` for every term the table adds.
ADDITIONS = [
    pytest.param(version, category, term, id=f"{version}-{category}-{term}")
    for version, by_category in td.VERSION_ADDITIONS.items()
    for category, terms in by_category.items()
    for term in terms
]


def _expected(category: str, version: str) -> list[str]:
    """What an accessor must return, derived here from the raw table."""
    expected = list(BASE[category])
    for release, by_category in td.VERSION_ADDITIONS.items():
        if _key(release) <= _key(version):
            expected.extend(by_category.get(category, []))
    return expected


def _accessor(category: str, version: str) -> list[str]:
    return td.get_all_terms_by_category(version)[category]


def test_the_table_has_a_row_for_every_minor_oldest_first():
    assert REGISTERED, "an empty table would make every case below vanish"
    major, first_minor = _key(REGISTERED[0])
    last_minor = _key(REGISTERED[-1])[1]
    # No release is skipped: one that added nothing has an empty row, so
    # "registered and added nothing" cannot be mistaken for "never looked at".
    assert [_key(version) for version in REGISTERED] == [
        (major, minor) for minor in range(first_minor, last_minor + 1)
    ]
    assert ADDITIONS, "a table of empty rows would make the cases below vanish"


def test_the_newest_registered_version_is_the_last_row():
    assert td.NEWEST_REGISTERED_VERSION == REGISTERED[-1]


def test_the_table_uses_only_the_four_versioned_categories():
    used = {
        category
        for by_category in td.VERSION_ADDITIONS.values()
        for category in by_category
    }
    assert used <= set(CATEGORIES), used - set(CATEGORIES)


def test_no_list_in_the_table_is_empty():
    # An emptied list makes its parametrized cases disappear without a
    # failure. A release that added nothing has an empty ROW instead.
    empty = sorted(
        f"{version} {category}"
        for version, by_category in td.VERSION_ADDITIONS.items()
        for category, terms in by_category.items()
        if not terms
    )
    assert empty == [], empty


@pytest.mark.parametrize("version", VERSIONS_TO_ASK)
@pytest.mark.parametrize("category", CATEGORIES)
def test_every_accessor_returns_the_base_plus_the_rows_up_to_the_version(
    category, version
):
    expected = _expected(category, version)
    assert td.get_all_terms_by_category(version)[category] == expected
    if category == "keyword":
        assert td.get_keywords_for_version(version) == expected
    if category == "exception":
        assert td.get_exceptions_for_version(version) == expected


@pytest.mark.parametrize("version", VERSIONS_TO_ASK)
def test_the_builtins_accessor_is_functions_then_types_then_constants(version):
    assert td.get_builtins_for_version(version) == (
        _expected("builtin_func", version)
        + _expected("builtin_type", version)
        + td.SPECIAL_CONSTANTS
    )


@pytest.mark.parametrize(("version", "category", "term"), ADDITIONS)
def test_an_added_term_is_listed_from_its_release_on(version, category, term):
    assert term in _accessor(category, version)
    assert term in _accessor(category, REGISTERED[-1])
    assert term in _accessor(category, _next(REGISTERED[-1]))


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
    for category in CATEGORIES:
        terms = _accessor(category, REGISTERED[-1])
        repeated = sorted({term for term in terms if terms.count(term) > 1})
        assert repeated == [], f"{category}: {repeated}"


def test_versions_compare_as_numbers_not_as_text():
    # As text, "3.9" sorts after "3.10", so a 3.9 request used to be handed
    # the 3.10 soft keywords.
    oldest = REGISTERED[0]
    major, minor = _key(oldest)
    assert minor >= 10, "the case below needs a two-digit minor to mean anything"
    added = td.VERSION_ADDITIONS[oldest].get("keyword")
    assert added, "nothing would be checked"
    for term in added:
        assert term not in td.get_keywords_for_version(f"{major}.9")


def test_a_patch_version_reads_as_its_minor():
    for version in REGISTERED:
        assert td.get_all_terms_by_category(
            f"{version}.7"
        ) == td.get_all_terms_by_category(version)


def test_a_bare_major_reads_as_its_first_minor():
    major = _key(REGISTERED[0])[0]
    assert td.get_all_terms_by_category(str(major)) == td.get_all_terms_by_category(
        f"{major}.0"
    )


@pytest.mark.parametrize("malformed", ["latest", "", "3.13rc1", "3.x", "three.ten"])
@pytest.mark.parametrize(
    "accessor",
    [
        td.get_keywords_for_version,
        td.get_builtins_for_version,
        td.get_exceptions_for_version,
        td.get_all_terms_by_category,
        lambda version: td.classify_term("print", version),
        lambda version: td.is_python_term("print", version),
    ],
    ids=[
        "keywords",
        "builtins",
        "exceptions",
        "by_category",
        "classify_term",
        "is_python_term",
    ],
)
def test_a_malformed_version_is_refused_by_name(accessor, malformed):
    # Compared as text, these used to give an arbitrary answer.
    with pytest.raises(ValueError, match="not an X.Y version string") as excinfo:
        accessor(malformed)
    assert repr(malformed) in str(excinfo.value)


@pytest.mark.parametrize("version", VERSIONS_TO_ASK)
def test_the_accessors_hand_out_copies(version):
    # At every version, not only the newest: below the first release that
    # adds to a category, an accessor could hand out the module's own list.
    before = copy.deepcopy(
        {
            name: value
            for name, value in vars(td).items()
            if name.isupper() and isinstance(value, (list, dict))
        }
    )
    try:
        for result in (
            td.get_keywords_for_version(version),
            td.get_builtins_for_version(version),
            td.get_exceptions_for_version(version),
            *td.get_all_terms_by_category(version).values(),
        ):
            result.append("mutated")
            result.clear()
        after = {name: getattr(td, name) for name in before}
        assert after == before
    finally:
        # A failure here means a module list was emptied. Put the contents
        # back in place so the tests that run after this one still mean
        # something.
        for name, value in before.items():
            current = getattr(td, name)
            if isinstance(current, list) and current != value:
                current[:] = value


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
