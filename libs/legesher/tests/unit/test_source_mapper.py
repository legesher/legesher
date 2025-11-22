"""Tests for the source mapping engine."""

import threading

from legesher.runtime.source_mapper import (
    SourceMapping,
    LegesherSourceMapper,
    get_source_mapper,
    reset_source_mapper,
)


class TestSourceMapping:
    """Tests for SourceMapping dataclass."""

    def test_source_mapping_creation(self):
        """Test creating a source mapping."""
        mapping = SourceMapping(
            native_file="test.py",
            native_line=5,
            english_line=5,
            native_code="si verdad:",
            english_code="if True:",
        )

        assert mapping.native_file == "test.py"
        assert mapping.native_line == 5
        assert mapping.english_line == 5
        assert mapping.native_code == "si verdad:"
        assert mapping.english_code == "if True:"


class TestLegesherSourceMapper:
    """Tests for LegesherSourceMapper class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = LegesherSourceMapper()
        self.native_source = """si verdad:
    imprimir('hola')
    x = 5"""
        self.english_source = """if True:
    print('hello')
    x = 5"""

    def test_initialization(self):
        """Test mapper initialization."""
        mapper = LegesherSourceMapper()
        assert mapper.get_mapped_files() == []

    def test_register_mapping(self):
        """Test registering a source mapping."""
        self.mapper.register_mapping("test.py", self.native_source, self.english_source)

        assert self.mapper.has_mapping("test.py")
        assert "test.py" in self.mapper.get_mapped_files()

    def test_get_native_line(self):
        """Test getting native line number from English line."""
        self.mapper.register_mapping("test.py", self.native_source, self.english_source)

        # Test 1:1 mapping
        assert self.mapper.get_native_line("test.py", 1) == 1
        assert self.mapper.get_native_line("test.py", 2) == 2
        assert self.mapper.get_native_line("test.py", 3) == 3

    def test_get_native_line_missing_file(self):
        """Test getting native line for non-existent file."""
        result = self.mapper.get_native_line("nonexistent.py", 1)
        assert result is None

    def test_get_native_source_line(self):
        """Test getting native source code line."""
        self.mapper.register_mapping("test.py", self.native_source, self.english_source)

        # Test retrieving each line
        assert self.mapper.get_native_source_line("test.py", 1) == "si verdad:"
        assert (
            self.mapper.get_native_source_line("test.py", 2) == "    imprimir('hola')"
        )
        assert self.mapper.get_native_source_line("test.py", 3) == "    x = 5"

    def test_get_native_source_line_out_of_range(self):
        """Test getting source line with out-of-range line number."""
        self.mapper.register_mapping("test.py", self.native_source, self.english_source)

        # Line 0 (invalid)
        assert self.mapper.get_native_source_line("test.py", 0) is None

        # Line beyond file length
        assert self.mapper.get_native_source_line("test.py", 100) is None

    def test_get_native_source_line_missing_file(self):
        """Test getting source line for non-existent file."""
        result = self.mapper.get_native_source_line("nonexistent.py", 1)
        assert result is None

    def test_has_mapping(self):
        """Test checking if mapping exists."""
        assert not self.mapper.has_mapping("test.py")

        self.mapper.register_mapping("test.py", self.native_source, self.english_source)

        assert self.mapper.has_mapping("test.py")
        assert not self.mapper.has_mapping("other.py")

    def test_clear_mapping(self):
        """Test clearing mapping for specific file."""
        self.mapper.register_mapping("test.py", self.native_source, self.english_source)

        assert self.mapper.has_mapping("test.py")

        self.mapper.clear_mapping("test.py")

        assert not self.mapper.has_mapping("test.py")
        assert self.mapper.get_native_line("test.py", 1) is None
        assert self.mapper.get_native_source_line("test.py", 1) is None

    def test_clear_all(self):
        """Test clearing all mappings."""
        self.mapper.register_mapping("test1.py", "x = 1", "x = 1")
        self.mapper.register_mapping("test2.py", "y = 2", "y = 2")

        assert len(self.mapper.get_mapped_files()) == 2

        self.mapper.clear_all()

        assert len(self.mapper.get_mapped_files()) == 0
        assert not self.mapper.has_mapping("test1.py")
        assert not self.mapper.has_mapping("test2.py")

    def test_get_mapped_files(self):
        """Test getting list of mapped files."""
        assert self.mapper.get_mapped_files() == []

        self.mapper.register_mapping("test1.py", "x = 1", "x = 1")
        self.mapper.register_mapping("test2.py", "y = 2", "y = 2")

        files = self.mapper.get_mapped_files()
        assert len(files) == 2
        assert "test1.py" in files
        assert "test2.py" in files

    def test_get_line_count(self):
        """Test getting line count for mapped file."""
        self.mapper.register_mapping("test.py", self.native_source, self.english_source)

        assert self.mapper.get_line_count("test.py") == 3

    def test_get_line_count_missing_file(self):
        """Test getting line count for non-existent file."""
        assert self.mapper.get_line_count("nonexistent.py") is None

    def test_register_mapping_overwrites(self):
        """Test that registering a mapping twice overwrites the first."""
        self.mapper.register_mapping("test.py", "x = 1", "x = 1")
        self.mapper.register_mapping("test.py", "y = 2", "y = 2")

        # Should have the second mapping
        assert self.mapper.get_native_source_line("test.py", 1) == "y = 2"

    def test_empty_source(self):
        """Test handling empty source code."""
        self.mapper.register_mapping("test.py", "", "")

        assert self.mapper.has_mapping("test.py")
        assert self.mapper.get_line_count("test.py") == 0
        assert self.mapper.get_native_source_line("test.py", 1) is None

    def test_single_line_source(self):
        """Test handling single-line source code."""
        self.mapper.register_mapping("test.py", "x = 1", "x = 1")

        assert self.mapper.get_line_count("test.py") == 1
        assert self.mapper.get_native_source_line("test.py", 1) == "x = 1"
        assert self.mapper.get_native_line("test.py", 1) == 1

    def test_multiline_with_blank_lines(self):
        """Test handling source with blank lines."""
        native = "x = 1\n\ny = 2"
        english = "x = 1\n\ny = 2"

        self.mapper.register_mapping("test.py", native, english)

        assert self.mapper.get_line_count("test.py") == 3
        assert self.mapper.get_native_source_line("test.py", 1) == "x = 1"
        assert self.mapper.get_native_source_line("test.py", 2) == ""
        assert self.mapper.get_native_source_line("test.py", 3) == "y = 2"

    def test_thread_safety(self):
        """Test thread safety of mapper operations."""
        results = []
        errors = []

        def register_and_retrieve(file_num):
            try:
                filename = f"test{file_num}.py"
                source = f"x{file_num} = {file_num}"

                self.mapper.register_mapping(filename, source, source)
                line = self.mapper.get_native_source_line(filename, 1)

                results.append((filename, line))
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=register_and_retrieve, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        assert len(errors) == 0

        # Verify all registrations succeeded
        assert len(results) == 10

        # Verify each file has correct mapping
        for i in range(10):
            filename = f"test{i}.py"
            expected = f"x{i} = {i}"
            actual = self.mapper.get_native_source_line(filename, 1)
            assert actual == expected


class TestGlobalSourceMapper:
    """Tests for global source mapper singleton."""

    def setup_method(self):
        """Reset global mapper before each test."""
        reset_source_mapper()

    def test_get_source_mapper_returns_instance(self):
        """Test that get_source_mapper returns a mapper instance."""
        mapper = get_source_mapper()
        assert isinstance(mapper, LegesherSourceMapper)

    def test_get_source_mapper_singleton(self):
        """Test that get_source_mapper returns the same instance."""
        mapper1 = get_source_mapper()
        mapper2 = get_source_mapper()

        assert mapper1 is mapper2

    def test_get_source_mapper_persistence(self):
        """Test that mappings persist across get_source_mapper calls."""
        mapper1 = get_source_mapper()
        mapper1.register_mapping("test.py", "x = 1", "x = 1")

        mapper2 = get_source_mapper()
        assert mapper2.has_mapping("test.py")

    def test_reset_source_mapper(self):
        """Test resetting the global mapper."""
        mapper1 = get_source_mapper()
        mapper1.register_mapping("test.py", "x = 1", "x = 1")

        reset_source_mapper()

        mapper2 = get_source_mapper()
        assert not mapper2.has_mapping("test.py")

    def test_thread_safety_singleton(self):
        """Test thread safety of singleton creation."""
        mappers = []

        def get_mapper():
            mapper = get_source_mapper()
            mappers.append(id(mapper))

        # Reset before test
        reset_source_mapper()

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=get_mapper)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All should be the same instance
        assert len(set(mappers)) == 1


class TestIntegrationScenarios:
    """Integration tests for realistic usage scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_source_mapper()
        self.mapper = get_source_mapper()

    def test_error_reporting_scenario(self):
        """Test a realistic error reporting scenario."""
        # Simulate a native Spanish file
        native_spanish = """# Programa de ejemplo
si verdad:
    imprimir('Hola mundo')
    x = 10 / 0  # Error aquí
    imprimir(x)"""

        english_translated = """# Example program
if True:
    print('Hello world')
    x = 10 / 0  # Error here
    print(x)"""

        # Register the mapping
        self.mapper.register_mapping("ejemplo.py", native_spanish, english_translated)

        # Simulate error on line 4 of English source
        error_english_line = 4
        native_line = self.mapper.get_native_line("ejemplo.py", error_english_line)
        native_code = self.mapper.get_native_source_line("ejemplo.py", native_line)

        # Verify we can retrieve the original native code
        assert native_line == 4
        assert native_code == "    x = 10 / 0  # Error aquí"

    def test_multiple_files_scenario(self):
        """Test scenario with multiple files."""
        # File 1: Spanish
        self.mapper.register_mapping(
            "modulo1.py", "clase MiClase:\n    pasar", "class MyClass:\n    pass"
        )

        # File 2: French
        self.mapper.register_mapping(
            "module2.py", "si faux:\n    passer", "if False:\n    pass"
        )

        # File 3: Arabic
        self.mapper.register_mapping(
            "module3.py", "# تعليق\nطباعة('مرحبا')", "# Comment\nprint('hello')"
        )

        # Verify all files are tracked
        files = self.mapper.get_mapped_files()
        assert len(files) == 3
        assert "modulo1.py" in files
        assert "module2.py" in files
        assert "module3.py" in files

        # Verify each file's mappings work independently
        assert self.mapper.get_native_source_line("modulo1.py", 1) == "clase MiClase:"
        assert self.mapper.get_native_source_line("module2.py", 1) == "si faux:"
        assert self.mapper.get_native_source_line("module3.py", 2) == "طباعة('مرحبا')"

    def test_reload_scenario(self):
        """Test scenario where a file is reloaded with new content."""
        # Initial version
        self.mapper.register_mapping("script.py", "x = 1", "x = 1")

        assert self.mapper.get_native_source_line("script.py", 1) == "x = 1"

        # File is modified and reloaded
        self.mapper.clear_mapping("script.py")
        self.mapper.register_mapping("script.py", "y = 2\nz = 3", "y = 2\nz = 3")

        # Should have new content
        assert self.mapper.get_line_count("script.py") == 2
        assert self.mapper.get_native_source_line("script.py", 1) == "y = 2"
        assert self.mapper.get_native_source_line("script.py", 2) == "z = 3"
