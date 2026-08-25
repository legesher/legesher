"""Source mapping between localized and English code positions.

This module provides bidirectional position mapping when translating
Python code between languages. When keywords change length (e.g.,
'definir' (7) → 'def' (3)), line/column positions shift. This class
tracks those shifts to accurately map positions in both directions.

It is what lets an answer computed against canonical English text — a hover
range, a diagnostic span — land on the right characters of the localized
source the reader is actually looking at.
"""

from dataclasses import dataclass
from typing import NamedTuple


class Position(NamedTuple):
    """A position in a text document (0-indexed)."""

    line: int
    character: int


@dataclass
class PositionMapping:
    """Maps a position range between original and translated code.

    Attributes:
        original_start: Starting position in original (localized) code
        original_end: Ending position in original (localized) code
        translated_start: Starting position in translated (English) code
        translated_end: Ending position in translated (English) code
    """

    original_start: Position
    original_end: Position
    translated_start: Position
    translated_end: Position


class SourceMap:
    """Maps positions between localized and English Python code.

    This class enables bidirectional position translation when keywords
    change length during translation. Uses binary search for O(log n)
    lookup performance.

    Example:
        >>> # Spanish: "definir foo():" (line 0, cols 0-6)
        >>> # English: "def foo():" (line 0, cols 0-2)
        >>> mapping = PositionMapping(
        ...     original_start=Position(0, 0),
        ...     original_end=Position(0, 7),
        ...     translated_start=Position(0, 0),
        ...     translated_end=Position(0, 3),
        ... )
        >>> source_map = SourceMap([mapping])
        >>> # Map position after "def" in English to Spanish
        >>> source_map.to_original(Position(0, 4))
        Position(line=0, character=8)
    """

    def __init__(self, mappings: list[PositionMapping]):
        """Initialize source map with position mappings.

        Args:
            mappings: List of position mappings, must be sorted by
                     translated position (line, then character)
        """
        self.mappings = sorted(
            mappings,
            key=lambda m: (m.translated_start.line, m.translated_start.character),
        )
        self._validate_mappings()

    def _validate_mappings(self) -> None:
        """Validate that mappings don't overlap and are well-formed."""
        for i in range(len(self.mappings) - 1):
            curr = self.mappings[i]
            next_map = self.mappings[i + 1]

            # Check no overlap in translated positions
            if curr.translated_end > next_map.translated_start:
                raise ValueError(
                    f"Overlapping mappings: {curr.translated_end} > {next_map.translated_start}"
                )

    def to_english(self, pos: Position) -> Position:
        """Convert position from localized (original) to English (translated).

        Args:
            pos: Position in localized code

        Returns:
            Corresponding position in English code

        Algorithm:
            1. Find mapping containing this position (binary search)
            2. If found, calculate offset within mapping
            3. Apply proportional offset to translated position
            4. If not found, calculate cumulative offset from previous mappings
        """
        # Binary search for mapping containing this position
        left, right = 0, len(self.mappings)

        while left < right:
            mid = (left + right) // 2
            mapping = self.mappings[mid]

            if self._position_in_original_range(pos, mapping):
                # Position is within this mapping - calculate offset
                return self._map_to_translated(pos, mapping)

            if self._position_before_original(pos, mapping):
                right = mid
            else:
                left = mid + 1

        # Position not in any mapping - calculate cumulative offset
        return self._calculate_offset_position(pos, left)

    def to_original(self, pos: Position) -> Position:
        """Convert position from English (translated) to localized (original).

        Args:
            pos: Position in English code

        Returns:
            Corresponding position in localized code
        """
        # Binary search for mapping containing this position
        left, right = 0, len(self.mappings)

        while left < right:
            mid = (left + right) // 2
            mapping = self.mappings[mid]

            if self._position_in_translated_range(pos, mapping):
                # Position is within this mapping - calculate offset
                return self._map_to_original(pos, mapping)

            if pos < mapping.translated_start:
                right = mid
            else:
                left = mid + 1

        # Position not in any mapping - calculate cumulative offset
        return self._calculate_reverse_offset_position(pos, left)

    def _position_in_original_range(self, pos: Position, mapping: PositionMapping) -> bool:
        """Check if position is within mapping's original range."""
        return mapping.original_start <= pos < mapping.original_end

    def _position_in_translated_range(self, pos: Position, mapping: PositionMapping) -> bool:
        """Check if position is within mapping's translated range."""
        return mapping.translated_start <= pos < mapping.translated_end

    def _position_before_original(self, pos: Position, mapping: PositionMapping) -> bool:
        """Check if position is before mapping's original range."""
        return pos < mapping.original_start

    def _map_to_translated(self, pos: Position, mapping: PositionMapping) -> Position:
        """Map position from original to translated within a mapping.

        For positions within a keyword mapping, we map proportionally
        based on the length change.
        """
        # Handle same-line mapping
        if pos.line == mapping.original_start.line:
            # Calculate offset from start of original range
            offset = pos.character - mapping.original_start.character

            # Calculate proportional position in translated range
            original_length = mapping.original_end.character - mapping.original_start.character
            translated_length = (
                mapping.translated_end.character - mapping.translated_start.character
            )

            if original_length > 0:
                # Proportional mapping
                proportion = offset / original_length
                translated_offset = int(proportion * translated_length)
            else:
                translated_offset = offset

            return Position(
                line=mapping.translated_start.line,
                character=mapping.translated_start.character + translated_offset,
            )

        # Multi-line mappings (rare for keywords, but handle it)
        line_offset = pos.line - mapping.original_start.line
        return Position(
            line=mapping.translated_start.line + line_offset,
            character=pos.character,
        )

    def _map_to_original(self, pos: Position, mapping: PositionMapping) -> Position:
        """Map position from translated to original within a mapping."""
        # Handle same-line mapping
        if pos.line == mapping.translated_start.line:
            # Calculate offset from start of translated range
            offset = pos.character - mapping.translated_start.character

            # Calculate proportional position in original range
            translated_length = (
                mapping.translated_end.character - mapping.translated_start.character
            )
            original_length = mapping.original_end.character - mapping.original_start.character

            if translated_length > 0:
                # Proportional mapping
                proportion = offset / translated_length
                original_offset = int(proportion * original_length)
            else:
                original_offset = offset

            return Position(
                line=mapping.original_start.line,
                character=mapping.original_start.character + original_offset,
            )

        # Multi-line mappings
        line_offset = pos.line - mapping.translated_start.line
        return Position(
            line=mapping.original_start.line + line_offset,
            character=pos.character,
        )

    def _calculate_offset_position(self, pos: Position, insert_index: int) -> Position:
        """Calculate position with cumulative offset from previous mappings.

        For positions not in any mapping, we calculate the cumulative
        character offset from all previous mappings on the same line.
        """
        cumulative_offset = 0

        for i in range(insert_index):
            mapping = self.mappings[i]

            # Only count mappings on the same line before this position
            if mapping.original_start.line == pos.line:
                if mapping.original_start.character < pos.character:
                    # Calculate length difference for this mapping
                    original_length = (
                        mapping.original_end.character - mapping.original_start.character
                    )
                    translated_length = (
                        mapping.translated_end.character - mapping.translated_start.character
                    )
                    cumulative_offset += translated_length - original_length

        return Position(
            line=pos.line,
            character=pos.character + cumulative_offset,
        )

    def _calculate_reverse_offset_position(self, pos: Position, insert_index: int) -> Position:
        """Calculate reverse position with cumulative offset."""
        cumulative_offset = 0

        for i in range(insert_index):
            mapping = self.mappings[i]

            # Only count mappings on the same line before this position
            if mapping.translated_start.line == pos.line:
                if mapping.translated_start.character < pos.character:
                    # Calculate length difference for this mapping
                    translated_length = (
                        mapping.translated_end.character - mapping.translated_start.character
                    )
                    original_length = (
                        mapping.original_end.character - mapping.original_start.character
                    )
                    cumulative_offset += original_length - translated_length

        return Position(
            line=pos.line,
            character=pos.character + cumulative_offset,
        )

    def __repr__(self) -> str:
        """String representation of SourceMap."""
        return f"SourceMap(mappings={len(self.mappings)})"


class SourceMapBuilder:
    """Builder for creating SourceMap during code translation.

    Example:
        >>> builder = SourceMapBuilder()
        >>> # During translation, record each keyword change
        >>> builder.add_mapping(
        ...     original_start=Position(0, 0),
        ...     original_end=Position(0, 7),
        ...     translated_start=Position(0, 0),
        ...     translated_end=Position(0, 3),
        ... )
        >>> source_map = builder.build()
    """

    def __init__(self):
        """Initialize empty source map builder."""
        self.mappings: list[PositionMapping] = []

    def add_mapping(
        self,
        original_start: Position,
        original_end: Position,
        translated_start: Position,
        translated_end: Position,
    ) -> None:
        """Add a position mapping.

        Args:
            original_start: Start position in original code
            original_end: End position in original code
            translated_start: Start position in translated code
            translated_end: End position in translated code
        """
        self.mappings.append(
            PositionMapping(
                original_start=original_start,
                original_end=original_end,
                translated_start=translated_start,
                translated_end=translated_end,
            )
        )

    def build(self) -> SourceMap:
        """Build the final SourceMap.

        Returns:
            SourceMap with all recorded mappings
        """
        return SourceMap(self.mappings)

    def clear(self) -> None:
        """Clear all mappings."""
        self.mappings.clear()
