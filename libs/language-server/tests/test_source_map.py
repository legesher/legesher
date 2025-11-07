"""Tests for source map position mapping.

Tests the bidirectional position mapping system used to translate
positions between localized and English code when keyword lengths differ.

Test for CORE-360 - Pylance Integration.
"""

import pytest

from legesher_language_server.source_map import (
    Position,
    PositionMapping,
    SourceMap,
    SourceMapBuilder,
)


class TestPosition:
    """Test Position namedtuple."""

    def test_position_creation(self):
        """Test creating a position."""
        pos = Position(line=5, character=10)
        assert pos.line == 5
        assert pos.character == 10

    def test_position_comparison(self):
        """Test position comparison operators."""
        pos1 = Position(0, 5)
        pos2 = Position(0, 10)
        pos3 = Position(1, 5)

        # Same line, different character
        assert pos1 < pos2
        assert not pos2 < pos1

        # Different lines
        assert pos1 < pos3
        assert not pos1 > pos3


class TestPositionMapping:
    """Test PositionMapping dataclass."""

    def test_mapping_creation(self):
        """Test creating a position mapping."""
        mapping = PositionMapping(
            original_start=Position(0, 0),
            original_end=Position(0, 7),
            translated_start=Position(0, 0),
            translated_end=Position(0, 3),
        )

        assert mapping.original_start == Position(0, 0)
        assert mapping.original_end == Position(0, 7)
        assert mapping.translated_start == Position(0, 0)
        assert mapping.translated_end == Position(0, 3)


class TestSourceMap:
    """Test SourceMap bidirectional position translation."""

    def test_single_keyword_mapping_forward(self):
        """Test forward mapping with single keyword (definir → def)."""
        # Spanish: "definir foo():" (0, 0-7)
        # English: "def foo():" (0, 0-3)
        mapping = PositionMapping(
            original_start=Position(0, 0),
            original_end=Position(0, 7),
            translated_start=Position(0, 0),
            translated_end=Position(0, 3),
        )
        source_map = SourceMap([mapping])

        # Position within keyword should map proportionally
        result = source_map.to_english(Position(0, 3))  # Middle of "definir"
        assert result.line == 0
        assert result.character >= 0 and result.character <= 3

        # Position after keyword should account for length difference
        result = source_map.to_english(Position(0, 8))  # Space after "definir"
        assert result.line == 0
        assert result.character == 4  # Space after "def" (8 - 4 = 4)

    def test_single_keyword_mapping_reverse(self):
        """Test reverse mapping with single keyword (def → definir)."""
        mapping = PositionMapping(
            original_start=Position(0, 0),
            original_end=Position(0, 7),
            translated_start=Position(0, 0),
            translated_end=Position(0, 3),
        )
        source_map = SourceMap([mapping])

        # Position after keyword in English
        result = source_map.to_original(Position(0, 4))  # Space after "def"
        assert result.line == 0
        assert result.character == 8  # Space after "definir" (4 + 4 = 8)

    def test_multiple_keywords_same_line(self):
        """Test mapping with multiple keywords on same line."""
        # Spanish: "definir foo(): retornar 42"
        # English: "def foo(): return 42"
        mappings = [
            # definir (0, 0-7) → def (0, 0-3)
            PositionMapping(
                original_start=Position(0, 0),
                original_end=Position(0, 7),
                translated_start=Position(0, 0),
                translated_end=Position(0, 3),
            ),
            # retornar (0, 15-23) → return (0, 11-17)
            PositionMapping(
                original_start=Position(0, 15),
                original_end=Position(0, 23),
                translated_start=Position(0, 11),
                translated_end=Position(0, 17),
            ),
        ]
        source_map = SourceMap(mappings)

        # Test position after second keyword
        result = source_map.to_english(Position(0, 24))  # Space after "retornar"
        assert result.line == 0
        # 24 - 4 (first keyword diff) - 2 (second keyword diff) = 18
        assert result.character == 18

    def test_multiple_lines(self):
        """Test mapping across multiple lines."""
        mappings = [
            # Line 0: definir
            PositionMapping(
                original_start=Position(0, 0),
                original_end=Position(0, 7),
                translated_start=Position(0, 0),
                translated_end=Position(0, 3),
            ),
            # Line 1: retornar
            PositionMapping(
                original_start=Position(1, 4),
                original_end=Position(1, 12),
                translated_start=Position(1, 4),
                translated_end=Position(1, 10),
            ),
        ]
        source_map = SourceMap(mappings)

        # Position on line 0 should not be affected by line 1 mapping
        result = source_map.to_english(Position(0, 10))
        assert result.line == 0
        assert result.character == 6  # 10 - 4 = 6

        # Position on line 1
        result = source_map.to_english(Position(1, 13))
        assert result.line == 1
        assert result.character == 11  # 13 - 2 = 11

    def test_position_before_any_mapping(self):
        """Test position that comes before all mappings."""
        # Comment before code: "# Spanish code"
        mapping = PositionMapping(
            original_start=Position(1, 0),
            original_end=Position(1, 7),
            translated_start=Position(1, 0),
            translated_end=Position(1, 3),
        )
        source_map = SourceMap([mapping])

        # Position on line 0 (before any mapping)
        result = source_map.to_english(Position(0, 5))
        assert result.line == 0
        assert result.character == 5  # No change

    def test_position_after_all_mappings(self):
        """Test position that comes after all mappings."""
        mapping = PositionMapping(
            original_start=Position(0, 0),
            original_end=Position(0, 7),
            translated_start=Position(0, 0),
            translated_end=Position(0, 3),
        )
        source_map = SourceMap([mapping])

        # Position on a later line
        result = source_map.to_english(Position(5, 10))
        assert result.line == 5
        assert result.character == 10  # No mappings on this line

    def test_empty_source_map(self):
        """Test source map with no mappings."""
        source_map = SourceMap([])

        # Should return same position
        result = source_map.to_english(Position(0, 10))
        assert result == Position(0, 10)

        result = source_map.to_original(Position(0, 10))
        assert result == Position(0, 10)

    def test_overlapping_mappings_raises_error(self):
        """Test that overlapping mappings raise ValueError."""
        mappings = [
            PositionMapping(
                original_start=Position(0, 0),
                original_end=Position(0, 7),
                translated_start=Position(0, 0),
                translated_end=Position(0, 5),  # Overlaps with next
            ),
            PositionMapping(
                original_start=Position(0, 8),
                original_end=Position(0, 15),
                translated_start=Position(0, 4),  # Overlaps!
                translated_end=Position(0, 10),
            ),
        ]

        with pytest.raises(ValueError, match="Overlapping mappings"):
            SourceMap(mappings)

    def test_repr(self):
        """Test string representation."""
        mapping = PositionMapping(
            original_start=Position(0, 0),
            original_end=Position(0, 7),
            translated_start=Position(0, 0),
            translated_end=Position(0, 3),
        )
        source_map = SourceMap([mapping])

        assert repr(source_map) == "SourceMap(mappings=1)"


class TestSourceMapBuilder:
    """Test SourceMapBuilder for constructing source maps."""

    def test_build_empty_map(self):
        """Test building source map with no mappings."""
        builder = SourceMapBuilder()
        source_map = builder.build()

        assert len(source_map.mappings) == 0

    def test_add_single_mapping(self):
        """Test adding single mapping."""
        builder = SourceMapBuilder()
        builder.add_mapping(
            original_start=Position(0, 0),
            original_end=Position(0, 7),
            translated_start=Position(0, 0),
            translated_end=Position(0, 3),
        )

        source_map = builder.build()
        assert len(source_map.mappings) == 1

        mapping = source_map.mappings[0]
        assert mapping.original_start == Position(0, 0)
        assert mapping.original_end == Position(0, 7)
        assert mapping.translated_start == Position(0, 0)
        assert mapping.translated_end == Position(0, 3)

    def test_add_multiple_mappings(self):
        """Test adding multiple mappings."""
        builder = SourceMapBuilder()

        # Add first mapping
        builder.add_mapping(
            original_start=Position(0, 0),
            original_end=Position(0, 7),
            translated_start=Position(0, 0),
            translated_end=Position(0, 3),
        )

        # Add second mapping
        builder.add_mapping(
            original_start=Position(0, 15),
            original_end=Position(0, 23),
            translated_start=Position(0, 11),
            translated_end=Position(0, 17),
        )

        source_map = builder.build()
        assert len(source_map.mappings) == 2

    def test_builder_sorts_mappings(self):
        """Test that builder creates sorted source map."""
        builder = SourceMapBuilder()

        # Add in reverse order
        builder.add_mapping(
            original_start=Position(1, 0),
            original_end=Position(1, 5),
            translated_start=Position(1, 0),
            translated_end=Position(1, 3),
        )
        builder.add_mapping(
            original_start=Position(0, 0),
            original_end=Position(0, 7),
            translated_start=Position(0, 0),
            translated_end=Position(0, 3),
        )

        source_map = builder.build()

        # Should be sorted by translated position
        assert source_map.mappings[0].translated_start.line == 0
        assert source_map.mappings[1].translated_start.line == 1

    def test_clear(self):
        """Test clearing builder."""
        builder = SourceMapBuilder()
        builder.add_mapping(
            original_start=Position(0, 0),
            original_end=Position(0, 7),
            translated_start=Position(0, 0),
            translated_end=Position(0, 3),
        )

        builder.clear()
        assert len(builder.mappings) == 0

    def test_reuse_builder(self):
        """Test reusing builder after clear."""
        builder = SourceMapBuilder()

        # First build
        builder.add_mapping(
            original_start=Position(0, 0),
            original_end=Position(0, 7),
            translated_start=Position(0, 0),
            translated_end=Position(0, 3),
        )
        source_map1 = builder.build()
        assert len(source_map1.mappings) == 1

        # Clear and build again
        builder.clear()
        builder.add_mapping(
            original_start=Position(1, 0),
            original_end=Position(1, 5),
            translated_start=Position(1, 0),
            translated_end=Position(1, 3),
        )
        source_map2 = builder.build()
        assert len(source_map2.mappings) == 1
        assert source_map2.mappings[0].original_start.line == 1


class TestRealWorldScenarios:
    """Test real-world translation scenarios."""

    def test_spanish_function_definition(self):
        """Test mapping for Spanish function definition.

        Spanish: "definir calcular_impuesto(ingreso):"
        English: "def calcular_impuesto(ingreso):"
        """
        mapping = PositionMapping(
            original_start=Position(0, 0),
            original_end=Position(0, 7),  # "definir"
            translated_start=Position(0, 0),
            translated_end=Position(0, 3),  # "def"
        )
        source_map = SourceMap([mapping])

        # Position at function name should adjust for keyword length change
        func_name_pos_spanish = Position(0, 8)  # Start of "calcular_impuesto"
        func_name_pos_english = source_map.to_english(func_name_pos_spanish)
        assert func_name_pos_english == Position(0, 4)  # After "def "

    def test_complex_statement(self):
        """Test complex statement with multiple keywords.

        Spanish: "si x > 0: retornar verdadero"
        English: "if x > 0: return True"
        """
        mappings = [
            # si → if
            PositionMapping(
                original_start=Position(0, 0),
                original_end=Position(0, 2),
                translated_start=Position(0, 0),
                translated_end=Position(0, 2),
            ),
            # retornar → return
            PositionMapping(
                original_start=Position(0, 10),
                original_end=Position(0, 18),
                translated_start=Position(0, 10),
                translated_end=Position(0, 16),
            ),
            # verdadero → True
            PositionMapping(
                original_start=Position(0, 19),
                original_end=Position(0, 28),
                translated_start=Position(0, 17),
                translated_end=Position(0, 21),
            ),
        ]
        source_map = SourceMap(mappings)

        # End of line in Spanish
        end_spanish = Position(0, 28)
        end_english = source_map.to_english(end_spanish)

        # Should account for all length differences
        # retornar: 8→6 (saves 2)
        # verdadero: 9→4 (saves 5)
        # Total saved: 7 characters
        assert end_english == Position(0, 21)
