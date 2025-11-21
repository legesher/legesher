"""Unit tests for source mapper functionality."""

from legesher.runtime.source_mapper import (
    LegesherSourceMapper,
    SourceMapping,
    get_source_mapper,
)


class TestSourceMapping:
    """Test SourceMapping dataclass."""

    def test_source_mapping_creation(self):
        """Test creating a SourceMapping instance."""
        mapping = SourceMapping(
            native_file="test.py",
            native_line=5,
            english_line=5,
            native_code="linea de código",
            english_code="code line",
        )

        assert mapping.native_file == "test.py"
        assert mapping.native_line == 5
        assert mapping.english_line == 5
        assert mapping.native_code == "linea de código"
        assert mapping.english_code == "code line"


class TestLegesherSourceMapper:
    """Test LegesherSourceMapper class."""

    def test_mapper_initialization(self):
        """Test that mapper initializes with empty mappings."""
        mapper = LegesherSourceMapper()
        assert not mapper.has_mapping("any_file.py")

    def test_register_mapping(self):
        """Test registering a source mapping."""
        mapper = LegesherSourceMapper()

        native_source = "linea 1\nlinea 2\nlinea 3"
        english_source = "line 1\nline 2\nline 3"

        mapper.register_mapping("test.py", native_source, english_source)

        assert mapper.has_mapping("test.py")

    def test_get_native_line(self):
        """Test retrieving native line number from English line."""
        mapper = LegesherSourceMapper()

        mapper.register_mapping(
            "test.py", "linea 1\nlinea 2\nlinea 3", "line 1\nline 2\nline 3"
        )

        # 1:1 mapping for MVP
        assert mapper.get_native_line("test.py", 1) == 1
        assert mapper.get_native_line("test.py", 2) == 2
        assert mapper.get_native_line("test.py", 3) == 3

    def test_get_native_line_missing_file(self):
        """Test retrieving line from non-existent file."""
        mapper = LegesherSourceMapper()

        assert mapper.get_native_line("missing.py", 1) is None

    def test_get_native_source_line(self):
        """Test retrieving native source code line."""
        mapper = LegesherSourceMapper()

        native_source = "linea 1\nlinea 2\nlinea 3"
        mapper.register_mapping("test.py", native_source, "line 1\nline 2\nline 3")

        assert mapper.get_native_source_line("test.py", 1) == "linea 1"
        assert mapper.get_native_source_line("test.py", 2) == "linea 2"
        assert mapper.get_native_source_line("test.py", 3) == "linea 3"

    def test_get_native_source_line_out_of_range(self):
        """Test retrieving line number out of range."""
        mapper = LegesherSourceMapper()

        mapper.register_mapping("test.py", "linea 1\nlinea 2", "line 1\nline 2")

        assert (
            mapper.get_native_source_line("test.py", 0) is None
        )  # Line numbers start at 1
        assert mapper.get_native_source_line("test.py", 999) is None  # Out of range

    def test_clear_mappings(self):
        """Test clearing all mappings."""
        mapper = LegesherSourceMapper()

        mapper.register_mapping("test1.py", "linea 1", "line 1")
        mapper.register_mapping("test2.py", "linea 2", "line 2")

        assert mapper.has_mapping("test1.py")
        assert mapper.has_mapping("test2.py")

        mapper.clear()

        assert not mapper.has_mapping("test1.py")
        assert not mapper.has_mapping("test2.py")

    def test_has_mapping(self):
        """Test checking if mapping exists."""
        mapper = LegesherSourceMapper()

        assert not mapper.has_mapping("test.py")

        mapper.register_mapping("test.py", "linea 1", "line 1")

        assert mapper.has_mapping("test.py")
        assert not mapper.has_mapping("other.py")


class TestGlobalSourceMapper:
    """Test global source mapper singleton."""

    def test_get_source_mapper(self):
        """Test getting global source mapper instance."""
        mapper1 = get_source_mapper()
        mapper2 = get_source_mapper()

        # Should return same instance
        assert mapper1 is mapper2

    def test_global_mapper_state_persists(self):
        """Test that global mapper state persists across calls."""
        mapper = get_source_mapper()
        mapper.clear()  # Start fresh

        mapper.register_mapping("test.py", "linea 1", "line 1")

        # Get mapper again
        mapper2 = get_source_mapper()

        # State should persist
        assert mapper2.has_mapping("test.py")

        # Cleanup
        mapper.clear()
