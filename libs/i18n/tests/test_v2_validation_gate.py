"""CORE-1514: the v2 canon-validation gate, fixed in BOTH directions.

The Q7 triage (CORE-1501) found the gate simultaneously over- and
under-inclusive: it refused 25 legitimate Thai SARA-AM selections while shipping
12 of 15 mixed-script Thai corruptions, and it refused every locale's `except*`
forever. These tests pin the three fixes as behaviour, not implementation:

* **SARA-AM is a recorded FACT, and an explicit canon ALLOWANCE.** The validator
  records *why* a value is NFKC-unstable (`nfkc_delta_class`), and the canon gate
  accepts `sara-am-only` when the value is identifier-valid and single-script.
* **Identifier validation is TERM-AWARE.** `except*` (PEP 654) carries a
  structural `*`; the check validates the stem and requires the `*` to mirror the
  source term. There is no blanket `*` allowance elsewhere.
* **Script-consistency is REAL and locale-aware.** A cross-script confusable
  (`บайтс`, Cyrillic-in-Thai) or an embedded-Latin value is refused; a legitimate
  Han+Kana Japanese value is not.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator

import pytest

from legesher_i18n.db.schema_v2 import apply_schema_v2, option_uid
from scripts.migrate_to_v2 import allowed_scripts_for, validate_surface

THAI = frozenset({"Thai"})
ETHIOPIC = frozenset({"Ethiopic"})
LATIN = frozenset({"Latin"})

# A real Thai selection the OLD gate refused only for NFKC instability -- pure
# Thai, a valid identifier, unstable exclusively because of U+0E33 (SARA AM).
THAI_FINALLY = "ทำเสมอ"


# ---------------------------------------------------------------------------
# FIX 1 -- nfkc_delta_class: the fact of WHY a value is NFKC-unstable
# ---------------------------------------------------------------------------


def test_sara_am_is_recorded_as_its_own_nfkc_delta_class() -> None:
    """The 25 Thai refusals share one cause: U+0E33 -> U+0E4D U+0E32, nothing else."""
    v = validate_surface(THAI_FINALLY, "finally", THAI)
    assert v.nfkc_stable is False
    assert v.nfkc_delta_class == "sara-am-only"
    # The value is otherwise clean: a single-script, valid Python identifier.
    assert v.identifier_valid is True
    assert v.script_consistent is True


def test_a_stable_value_carries_no_nfkc_delta_class() -> None:
    """A fact, not a stamp: no delta means no class."""
    v = validate_surface("verdadero", "true", LATIN)
    assert v.nfkc_stable is True
    assert v.nfkc_delta_class is None


def test_a_non_sara_am_instability_is_classed_other() -> None:
    """An NFKC delta that is NOT pure SARA-AM must not borrow the allowance."""
    # U+FDFA (ARABIC LIGATURE SALLALLAHOU ALAYHE WASALLAM) NFKC-expands to a whole
    # phrase -- a real instability that is not SARA-AM.
    v = validate_surface("ﷺ", "x", frozenset({"Arabic"}))
    assert v.nfkc_stable is False
    assert v.nfkc_delta_class == "other"


# ---------------------------------------------------------------------------
# FIX 2 -- term-aware identifier validation
# ---------------------------------------------------------------------------


def test_except_star_is_valid_with_its_mirrored_asterisk() -> None:
    """am `ከቀረ*` renders `except*`; the `*` mirrors the source token (PEP 654).

    The plain `str.isidentifier()` rule refused this forever. The stem `ከቀረ` is a
    valid identifier and the trailing `*` mirrors the term, so it is valid.
    """
    v = validate_surface("ከቀረ*", "except*", ETHIOPIC)
    assert v.identifier_valid is True


def test_except_star_must_actually_carry_the_asterisk() -> None:
    """Dropping the structural `*` is not a faithful rendering of `except*`."""
    v = validate_surface("ከቀረ", "except*", ETHIOPIC)
    assert v.identifier_valid is False


def test_there_is_no_blanket_asterisk_allowance() -> None:
    """A `*` on a term that does not carry one stays invalid."""
    v = validate_surface("foo*", "eval", LATIN)
    assert v.identifier_valid is False


def test_a_dunder_is_a_plain_valid_identifier() -> None:
    """`__import__` and its translations are already valid identifiers (underscores)."""
    v = validate_surface("__นำเข้า__", "__import__", THAI)
    assert v.identifier_valid is True


# ---------------------------------------------------------------------------
# FIX 3 -- real, locale-aware script-consistency
# ---------------------------------------------------------------------------


def test_a_cross_script_confusable_is_not_script_consistent() -> None:
    """`บайтс` (bytes): Thai บ + Cyrillic айтс. NFKC-stable, valid identifier -- the
    old gate shipped it. The locale-aware check refuses Cyrillic in a Thai value."""
    v = validate_surface("บайтс", "bytes", THAI)
    assert v.identifier_valid is True  # still a valid identifier...
    assert v.nfkc_stable is True  # ...and NFKC-stable...
    assert v.script_consistent is False  # ...but not script-consistent.


def test_embedded_latin_in_a_thai_value_is_not_script_consistent() -> None:
    v = validate_surface("เทคนิคfor", "for", THAI)
    assert v.script_consistent is False


def test_a_legitimate_japanese_han_kana_mix_is_script_consistent() -> None:
    """ja legitimately mixes Han + Hiragana + Katakana; the naive one-script
    heuristic wrongly flagged it. The locale policy allows all three."""
    v = validate_surface("サーバー", "server", allowed_scripts_for("ja"))
    assert v.script_consistent is True


def test_pure_thai_is_script_consistent() -> None:
    v = validate_surface(THAI_FINALLY, "finally", THAI)
    assert v.script_consistent is True


# ---------------------------------------------------------------------------
# The canon gate (SQL trigger) agrees with the validator
# ---------------------------------------------------------------------------


@pytest.fixture
def db() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema_v2(conn)
    conn.executescript(
        """
        INSERT INTO programming_languages (code, name, status)
            VALUES ('python', 'Python', 'shipping');
        INSERT INTO locales (tag, language_subtag, name, native_name, direction, in_registry)
            VALUES ('th', 'th', 'Thai', 'ไทย', 'ltr', 1);
        INSERT INTO concepts (id, slug, definition_en, category) VALUES
            (1, 'finally-clause', 'Run cleanup unconditionally.', 'control_flow'),
            (2, 'bytes-type', 'Immutable sequence of bytes.', 'type_system');
        """
    )
    conn.commit()
    yield conn
    conn.close()


def _add_validated(
    conn: sqlite3.Connection,
    concept_id: int,
    slug: str,
    surface: str,
    *,
    identifier_valid: int,
    nfkc_stable: int,
    nfkc_delta_class: str | None,
    script_consistent: int,
) -> str:
    uid = option_uid(slug, "th", surface)
    conn.execute(
        "INSERT INTO options (uid, concept_id, locale, surface_form) VALUES (?, ?, 'th', ?)",
        (uid, concept_id, surface),
    )
    conn.execute(
        "INSERT INTO option_validations (option_uid, validator_version, identifier_valid, "
        "nfkc_stable, nfkc_delta_class, script_consistent) VALUES (?, 'py-identifier-v2', ?, ?, ?, ?)",
        (uid, identifier_valid, nfkc_stable, nfkc_delta_class, script_consistent),
    )
    return uid


def _select(conn: sqlite3.Connection, concept_id: int, uid: str, surface: str) -> None:
    conn.execute(
        "INSERT INTO canon_selections (concept_id, locale, option_uid, surface_form, source_file) "
        "VALUES (?, 'th', ?, ?, 'canon/th.toml')",
        (concept_id, uid, surface),
    )


def test_canon_accepts_a_sara_am_only_selection(db: sqlite3.Connection) -> None:
    """The 25 Thai refusals lift: NFKC-unstable is fine when the delta is SARA-AM
    and the value is an identifier-valid, single-script rendering."""
    uid = _add_validated(
        db,
        1,
        "finally-clause",
        THAI_FINALLY,
        identifier_valid=1,
        nfkc_stable=0,
        nfkc_delta_class="sara-am-only",
        script_consistent=1,
    )
    db.commit()
    _select(db, 1, uid, THAI_FINALLY)  # must NOT raise
    db.commit()
    assert db.execute("SELECT COUNT(*) FROM canon_selections").fetchone()[0] == 1


def test_canon_still_refuses_a_non_sara_am_instability(db: sqlite3.Connection) -> None:
    """The allowance is SARA-AM specific: any other NFKC instability still blocks."""
    uid = _add_validated(
        db,
        1,
        "finally-clause",
        THAI_FINALLY,
        identifier_valid=1,
        nfkc_stable=0,
        nfkc_delta_class="other",
        script_consistent=1,
    )
    db.commit()
    with pytest.raises(sqlite3.IntegrityError, match="identifier/NFKC"):
        _select(db, 1, uid, THAI_FINALLY)


def test_canon_refuses_a_script_inconsistent_selection(db: sqlite3.Connection) -> None:
    """The under-inclusive half: a mixed-script confusable that passes identifier
    and NFKC checks is now blocked by the real script-consistency gate."""
    uid = _add_validated(
        db,
        2,
        "bytes-type",
        "บайтс",
        identifier_valid=1,
        nfkc_stable=1,
        nfkc_delta_class=None,
        script_consistent=0,
    )
    db.commit()
    with pytest.raises(sqlite3.IntegrityError, match="identifier/NFKC"):
        _select(db, 2, uid, "บайтс")
