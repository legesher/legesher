"""Tests for IdentifierMap — consistent cross-file, cross-language identifier translations.

Tests CRUD operations, multi-language storage, persistence (save/load),
merge behavior, and the split_identifier/reassemble_identifier helpers.
"""

import json

import pytest

from legesher_core.tree_sitter.identifier_map import (
    IdentifierMap,
    reassemble_identifier,
    split_identifier,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def id_map():
    """Fresh empty IdentifierMap."""
    return IdentifierMap(source_lang="en")


@pytest.fixture
def populated_map():
    """IdentifierMap pre-populated with a few translations."""
    m = IdentifierMap(source_lang="en")
    m.add("calculate_tax", "es", "calcular_impuesto")
    m.add("calculate_tax", "zh", "\u8ba1\u7b97\u7a0e\u6b3e")
    m.add("user_name", "es", "nombre_usuario")
    return m


# ===========================================================================
# Basic CRUD
# ===========================================================================


class TestBasicOperations:
    """Test add, get, has, __len__, __contains__."""

    def test_add_and_get(self, id_map):
        id_map.add("my_var", "es", "mi_var")
        assert id_map.get("my_var", "es") == "mi_var"

    def test_get_returns_none_for_missing_identifier(self, id_map):
        assert id_map.get("nonexistent", "es") is None

    def test_get_returns_none_for_missing_language(self, id_map):
        id_map.add("my_var", "es", "mi_var")
        assert id_map.get("my_var", "zh") is None

    def test_has_returns_true(self, id_map):
        id_map.add("my_var", "es", "mi_var")
        assert id_map.has("my_var", "es") is True

    def test_has_returns_false(self, id_map):
        assert id_map.has("my_var", "es") is False

    def test_len(self, populated_map):
        assert len(populated_map) == 2  # calculate_tax, user_name

    def test_contains(self, populated_map):
        assert "calculate_tax" in populated_map
        assert "missing" not in populated_map

    def test_add_overwrites_existing(self, id_map):
        id_map.add("x", "es", "old")
        id_map.add("x", "es", "new")
        assert id_map.get("x", "es") == "new"


# ===========================================================================
# Query methods
# ===========================================================================


class TestQueryMethods:
    """Test get_untranslated, get_glossary, get_all_identifiers, get_languages."""

    def test_get_untranslated(self, populated_map):
        untranslated = populated_map.get_untranslated(
            ["calculate_tax", "user_name", "new_var"], "es"
        )
        assert untranslated == ["new_var"]

    def test_get_untranslated_all_present(self, populated_map):
        untranslated = populated_map.get_untranslated(
            ["calculate_tax", "user_name"], "es"
        )
        assert untranslated == []

    def test_get_untranslated_all_missing(self, id_map):
        untranslated = id_map.get_untranslated(["a", "b"], "es")
        assert untranslated == ["a", "b"]

    def test_get_glossary(self, populated_map):
        glossary = populated_map.get_glossary("es")
        assert glossary == {
            "calculate_tax": "calcular_impuesto",
            "user_name": "nombre_usuario",
        }

    def test_get_glossary_filters_by_language(self, populated_map):
        glossary = populated_map.get_glossary("zh")
        assert "user_name" not in glossary
        assert glossary == {"calculate_tax": "\u8ba1\u7b97\u7a0e\u6b3e"}

    def test_get_glossary_empty_for_unknown_language(self, populated_map):
        assert populated_map.get_glossary("ur") == {}

    def test_get_all_identifiers(self, populated_map):
        ids = populated_map.get_all_identifiers()
        assert set(ids) == {"calculate_tax", "user_name"}

    def test_get_languages(self, populated_map):
        langs = populated_map.get_languages()
        assert langs == {"es", "zh"}


# ===========================================================================
# Merge
# ===========================================================================


class TestMerge:
    """Test merge behavior: new translations added, existing not overwritten."""

    def test_merge_adds_new_identifiers(self, populated_map):
        other = IdentifierMap()
        other.add("new_func", "es", "nueva_funcion")
        populated_map.merge(other)
        assert populated_map.get("new_func", "es") == "nueva_funcion"

    def test_merge_adds_new_language(self, populated_map):
        other = IdentifierMap()
        other.add(
            "calculate_tax", "ur", "\u062d\u0633\u0627\u0628_\u0679\u06cc\u06a9\u0633"
        )
        populated_map.merge(other)
        assert (
            populated_map.get("calculate_tax", "ur")
            == "\u062d\u0633\u0627\u0628_\u0679\u06cc\u06a9\u0633"
        )

    def test_merge_does_not_overwrite(self, populated_map):
        other = IdentifierMap()
        other.add("calculate_tax", "es", "SHOULD_NOT_OVERWRITE")
        populated_map.merge(other)
        assert populated_map.get("calculate_tax", "es") == "calcular_impuesto"


# ===========================================================================
# Multi-language storage
# ===========================================================================


class TestMultiLanguage:
    """Same identifier stored for multiple target languages."""

    def test_multi_language_same_identifier(self, id_map):
        id_map.add("greeting", "es", "saludo")
        id_map.add("greeting", "zh", "\u95ee\u5019")
        id_map.add("greeting", "ur", "\u0633\u0644\u0627\u0645")

        assert id_map.get("greeting", "es") == "saludo"
        assert id_map.get("greeting", "zh") == "\u95ee\u5019"
        assert id_map.get("greeting", "ur") == "\u0633\u0644\u0627\u0645"

    def test_languages_tracks_all(self, id_map):
        id_map.add("x", "es", "y")
        id_map.add("x", "zh", "z")
        id_map.add("x", "ur", "w")
        assert id_map.get_languages() == {"es", "zh", "ur"}


# ===========================================================================
# Persistence (save / load)
# ===========================================================================


class TestPersistence:
    """Test JSON save and load round-trip."""

    def test_save_and_load_round_trip(self, populated_map, tmp_path):
        path = tmp_path / "identifier_map.json"
        populated_map.save(path)

        loaded = IdentifierMap.load(path)
        assert loaded.source_lang == "en"
        assert len(loaded) == len(populated_map)
        assert loaded.get("calculate_tax", "es") == "calcular_impuesto"
        assert loaded.get("calculate_tax", "zh") == "\u8ba1\u7b97\u7a0e\u6b3e"
        assert loaded.get("user_name", "es") == "nombre_usuario"

    def test_save_creates_parent_directories(self, id_map, tmp_path):
        path = tmp_path / "nested" / "deep" / "map.json"
        id_map.add("x", "es", "y")
        id_map.save(path)
        assert path.exists()

    def test_json_output_is_human_readable(self, populated_map, tmp_path):
        path = tmp_path / "map.json"
        populated_map.save(path)
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        # Check sorted keys (human-readable)
        assert data["version"] == 1
        assert "identifiers" in data
        # Check identifiers are sorted
        id_keys = list(data["identifiers"].keys())
        assert id_keys == sorted(id_keys)
        # Check indentation (2-space indent)
        assert "  " in text

    def test_load_nonexistent_raises_error(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            IdentifierMap.load(tmp_path / "does_not_exist.json")


class TestLoadOrCreate:
    """Test load_or_create factory method."""

    def test_creates_empty_when_file_does_not_exist(self, tmp_path):
        path = tmp_path / "new_map.json"
        m = IdentifierMap.load_or_create(path, source_lang="en")
        assert len(m) == 0
        assert m.source_lang == "en"

    def test_loads_when_file_exists(self, populated_map, tmp_path):
        path = tmp_path / "map.json"
        populated_map.save(path)

        loaded = IdentifierMap.load_or_create(path)
        assert len(loaded) == 2
        assert loaded.get("calculate_tax", "es") == "calcular_impuesto"


# ===========================================================================
# split_identifier
# ===========================================================================


class TestSplitIdentifier:
    """Test splitting compound identifiers into words."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("calculate_tax", ["calculate", "tax"]),
            ("my_long_variable", ["my", "long", "variable"]),
            ("_private_var", ["private", "var"]),  # leading underscore stripped
            ("UserProfile", ["User", "Profile"]),
            ("calculateTax", ["calculate", "Tax"]),
            ("MAX_RETRY_COUNT", ["MAX", "RETRY", "COUNT"]),
            ("simple", ["simple"]),
            ("HTMLParser", ["HTML", "Parser"]),
            ("getHTTPResponse", ["get", "HTTP", "Response"]),
        ],
    )
    def test_split(self, text, expected):
        assert split_identifier(text) == expected

    def test_split_empty_parts_excluded(self):
        # Double underscore shouldn't produce empty parts
        result = split_identifier("a__b")
        assert "" not in result


# ===========================================================================
# reassemble_identifier
# ===========================================================================


class TestReassembleIdentifier:
    """Test reassembling word parts into identifiers."""

    def test_snake_case(self):
        assert (
            reassemble_identifier(["Calculate", "Tax"], "snake_case") == "calculate_tax"
        )

    def test_screaming_snake_case(self):
        assert (
            reassemble_identifier(["max", "retry"], "SCREAMING_SNAKE_CASE")
            == "MAX_RETRY"
        )

    def test_pascal_case(self):
        assert reassemble_identifier(["user", "profile"], "PascalCase") == "UserProfile"

    def test_camel_case(self):
        assert (
            reassemble_identifier(["calculate", "tax"], "camelCase") == "calculateTax"
        )

    def test_lowercase(self):
        assert reassemble_identifier(["Hello", "World"], "lowercase") == "hello_world"

    def test_empty_parts(self):
        assert reassemble_identifier([], "snake_case") == ""

    def test_single_part(self):
        assert reassemble_identifier(["hello"], "PascalCase") == "Hello"

    def test_unknown_convention_falls_back_to_lowercase(self):
        assert reassemble_identifier(["Foo", "Bar"], "unknown") == "foo_bar"


class TestIdentifierMapPackCollisionDetection:
    """Test validate_against_pack and pack-aware add() (CORE-710)."""

    def _make_pack(self):
        from legesher_i18n.pack_loader import LanguagePack

        return LanguagePack(
            language="es",
            target="python",
            version="3.10",
            keywords={"def": "definir", "in": "en"},
            builtins={"print": "imprimir", "len": "longitud"},
            exceptions={"ValueError": "ErrorDeValor"},
            reserved_words={"self": "propio", "cls": "clase_ref"},
        )

    def test_validate_against_pack_returns_none_when_safe(self):
        """A novel translation that matches no pack term: no collision."""
        pack = self._make_pack()
        imap = IdentifierMap()
        assert imap.validate_against_pack("calcular_impuesto", pack) is None

    def test_validate_against_pack_detects_keyword_collision(self):
        pack = self._make_pack()
        imap = IdentifierMap()
        assert imap.validate_against_pack("definir", pack) == "keyword:def"

    def test_validate_against_pack_detects_builtin_collision(self):
        pack = self._make_pack()
        imap = IdentifierMap()
        assert imap.validate_against_pack("imprimir", pack) == "builtin:print"

    def test_validate_against_pack_detects_exception_collision(self):
        pack = self._make_pack()
        imap = IdentifierMap()
        assert (
            imap.validate_against_pack("ErrorDeValor", pack) == "exception:ValueError"
        )

    def test_validate_against_pack_detects_reserved_word_collision(self):
        """Madison's test 6 motivating case: e → propio collides with self."""
        pack = self._make_pack()
        imap = IdentifierMap()
        assert imap.validate_against_pack("propio", pack) == "reserved_word:self"

    def test_add_with_pack_at_construction_raises_on_collision(self):
        """Madison's test 6 skeleton: pack at construction, add raises on collide."""
        pack = self._make_pack()
        imap = IdentifierMap(pack=pack)
        with pytest.raises(ValueError, match="collision|reserved"):
            imap.add("e", "es", "propio")

    def test_add_with_per_call_pack_raises_on_collision(self):
        """Per-call pack override also triggers collision check."""
        pack = self._make_pack()
        imap = IdentifierMap()  # no pack at construction
        with pytest.raises(ValueError, match="collision"):
            imap.add("e", "es", "definir", pack=pack)

    def test_add_without_pack_does_not_check(self):
        """Backward-compat: existing 3-arg add() with no pack accepts any value."""
        imap = IdentifierMap()
        # Even a literal pack reserved value is accepted when no pack is given
        imap.add("e", "es", "definir")
        assert imap.get("e", "es") == "definir"

    def test_add_with_pack_accepts_non_colliding_translation(self):
        """Pack-aware add accepts translations that don't collide."""
        pack = self._make_pack()
        imap = IdentifierMap(pack=pack)
        imap.add("calculate_tax", "es", "calcular_impuesto")
        assert imap.get("calculate_tax", "es") == "calcular_impuesto"

    def test_collision_message_identifies_section_and_key(self):
        """The error message names the colliding section so callers can fix."""
        pack = self._make_pack()
        imap = IdentifierMap(pack=pack)
        with pytest.raises(ValueError) as exc_info:
            imap.add("e", "es", "propio")
        assert "reserved_word:self" in str(exc_info.value)

    def test_pack_attribute_is_stored_at_construction(self):
        """The pack reference is exposed for callers who want to introspect it."""
        pack = self._make_pack()
        imap = IdentifierMap(pack=pack)
        assert imap.pack is pack

        imap_no_pack = IdentifierMap()
        assert imap_no_pack.pack is None

    def test_merge_does_not_run_pack_collision_check(self):
        """merge() bypasses add() so pack-collision is not enforced.

        Documenting current behavior: merging two maps trusts the inputs
        (typical for translation-memory merges across runs). If a future
        requirement is to validate during merge, that's a separate feature.
        """
        from legesher_core.tree_sitter.identifier_map import IdentifierMap

        pack = self._make_pack()
        imap_with_pack = IdentifierMap(pack=pack)

        # Build a second map with a translation that WOULD collide if
        # added through `add()` with the pack
        other = IdentifierMap()
        other.add("e", "es", "propio")  # 'propio' = pack's self translation

        # merge() should NOT raise even though `propio` collides with pack
        imap_with_pack.merge(other)
        assert imap_with_pack.get("e", "es") == "propio"

    def test_validate_against_pack_handles_empty_pack_dicts(self):
        """A pack with empty keyword/builtin/exception/reserved_word dicts.

        validate_against_pack should return None (no collisions possible
        when the pack is empty). Edge case for very-early-stage packs.
        """
        from legesher_i18n.pack_loader import LanguagePack
        from legesher_core.tree_sitter.identifier_map import IdentifierMap

        empty_pack = LanguagePack(language="zz", target="python", version="3.10")
        imap = IdentifierMap()
        assert imap.validate_against_pack("anything", empty_pack) is None
        assert imap.validate_against_pack("propio", empty_pack) is None

    def test_validate_against_pack_with_empty_translation_returns_none(self):
        """An empty-string translation matches no pack value, so returns None.

        The caller is responsible for rejecting empty translations BEFORE
        calling validate_against_pack — this method only checks collision,
        not validity. Documenting current behavior so future callers know
        not to rely on it for empty-string rejection.
        """
        from legesher_core.tree_sitter.identifier_map import IdentifierMap

        pack = self._make_pack()
        imap = IdentifierMap()
        assert imap.validate_against_pack("", pack) is None

    def test_validate_against_pack_section_priority_keyword_first(self):
        """When a translation matches multiple sections, keyword-section wins.

        Pin the order: keyword → builtin → exception → reserved_word.
        Synthetic case: pack has 'shared' as the value in BOTH keyword
        and reserved_word sections (impossible in real data due to
        check_duplicates, but defensive).
        """
        from legesher_i18n.pack_loader import LanguagePack
        from legesher_core.tree_sitter.identifier_map import IdentifierMap

        pack = LanguagePack(
            language="zz",
            target="python",
            version="3.10",
            keywords={"def": "shared"},  # 'shared' matches keyword `def`
            reserved_words={"self": "shared"},  # AND reserved_word `self`
        )
        imap = IdentifierMap()
        # Keyword section is checked first → returns keyword:def
        assert imap.validate_against_pack("shared", pack) == "keyword:def"

    def test_pack_arg_persists_across_multiple_add_calls(self):
        """The pack at construction is checked on every add() call."""
        import pytest

        from legesher_core.tree_sitter.identifier_map import IdentifierMap

        pack = self._make_pack()
        imap = IdentifierMap(pack=pack)
        # First add succeeds (no collision)
        imap.add("calculate_tax", "es", "calcular_impuesto")
        # Second add with collision still raises (pack reference persists)
        with pytest.raises(ValueError, match="collision"):
            imap.add("e", "es", "propio")
        # First add still in map
        assert imap.get("calculate_tax", "es") == "calcular_impuesto"

    def test_validate_against_pack_finds_first_collision_on_iteration_order(self):
        """When a translation matches multiple values within ONE section.

        Real-world impossible (check_duplicates rejects it) but pinning:
        validate_against_pack returns the first match encountered during
        iteration, which is dict-insertion-order in modern Python.
        """
        from legesher_i18n.pack_loader import LanguagePack
        from legesher_core.tree_sitter.identifier_map import IdentifierMap

        pack = LanguagePack(
            language="zz",
            target="python",
            version="3.10",
            keywords={"def": "shared", "class": "shared"},  # synthetic dup
        )
        imap = IdentifierMap()
        result = imap.validate_against_pack("shared", pack)
        # Returns one of the two; insertion order says "def" first
        assert result == "keyword:def"
