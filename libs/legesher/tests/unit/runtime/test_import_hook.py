"""Unit tests for import_hook module."""

import os
import sys
import importlib
import threading
import pytest
from unittest.mock import patch, MagicMock

from legesher.runtime.import_hook import (
    _TranslationCache,
    LegesherMetaPathFinder,
    LegesherLoader,
    _get_cache_size,
    install_import_hook,
    uninstall_import_hook,
    is_hook_installed,
    get_installed_language,
    get_cache_stats,
    clear_cache,
)
from legesher_core import TokenTranslator


class TestLegesherMetaPathFinder:
    """Test LegesherMetaPathFinder class."""

    def test_init_creates_translator(self):
        """Test that initialization creates a translator."""
        finder = LegesherMetaPathFinder(language="es")
        assert finder.language == "es"
        assert isinstance(finder.translator, TokenTranslator)
        assert isinstance(finder.reverse_translator, TokenTranslator)
        assert isinstance(finder.cache, _TranslationCache)
        assert finder.cache.get_stats()["size"] == 0

    def test_find_spec_returns_none_for_nonexistent(self, tmp_path):
        """Test that find_spec returns None when module doesn't exist."""
        finder = LegesherMetaPathFinder(language="es")
        with patch.object(sys, "path", [str(tmp_path)]):
            spec = finder.find_spec("nonexistent_module", None)
            assert spec is None

    def test_find_spec_finds_simple_module(self, tmp_path):
        """Test that find_spec finds a simple .py module."""
        finder = LegesherMetaPathFinder(language="es")
        module_file = tmp_path / "test_module.py"
        module_file.write_text("# Test module")

        with patch.object(sys, "path", [str(tmp_path)]):
            spec = finder.find_spec("test_module", None)
            assert spec is not None
            assert spec.name == "test_module"
            assert isinstance(spec.loader, LegesherLoader)

    def test_invalidate_caches_clears_cache(self):
        """Test that invalidate_caches clears the translation cache."""
        finder = LegesherMetaPathFinder(language="es")
        finder.cache.set(("test.py", 123456), b"cached data")
        assert finder.cache.get_stats()["size"] == 1

        finder.invalidate_caches()
        assert finder.cache.get_stats()["size"] == 0


class TestLegesherLoader:
    """Test LegesherLoader class."""

    def test_init_stores_attributes(self):
        """Test that initialization stores module information."""
        finder = LegesherMetaPathFinder(language="es")
        loader = LegesherLoader("test_module", "/path/to/test.py", finder)

        assert loader.fullname == "test_module"
        assert loader.path == "/path/to/test.py"
        assert loader.finder is finder

    def test_get_filename_returns_path(self):
        """Test that get_filename returns the source file path."""
        finder = LegesherMetaPathFinder(language="es")
        loader = LegesherLoader("test_module", "/path/to/test.py", finder)

        filename = loader.get_filename("test_module")
        assert filename == "/path/to/test.py"

    def test_get_data_raises_for_nonexistent_file(self):
        """Test that get_data raises FileNotFoundError for missing files."""
        finder = LegesherMetaPathFinder(language="es")
        loader = LegesherLoader("test", "/nonexistent/file.py", finder)

        with pytest.raises(FileNotFoundError):
            loader.get_data("/nonexistent/file.py")

    def test_needs_translation_detects_spanish_keywords(self):
        """Native keywords in keyword position fail ast.parse, so True."""
        finder = LegesherMetaPathFinder(language="es")
        loader = LegesherLoader("test", "test.py", finder)

        spanish_code = "definir greet():\n    retornar 42"
        needs_translation = loader._needs_translation(spanish_code)
        assert needs_translation is True

    def test_needs_translation_returns_false_for_english(self):
        """Test that _needs_translation returns False for English code."""
        finder = LegesherMetaPathFinder(language="es")
        loader = LegesherLoader("test", "test.py", finder)

        english_code = "def greet():\n    return 42"
        needs_translation = loader._needs_translation(english_code)
        assert needs_translation is False


class TestDottedImports:
    """Regression tests for CORE-1209: dotted imports under the hook.

    The finder used to break dotted stdlib imports two ways: it joined the
    full dotted name onto parent __path__ entries (looking for
    <stdlib>/http/http/client.py), and it claimed packages with the
    ModuleSpec default of an EMPTY submodule_search_locations list, so
    `import http.client` raised ModuleNotFoundError under the hook.
    """

    def setup_method(self):
        """Ensure import hook is not installed before each test."""
        uninstall_import_hook()

    def teardown_method(self):
        """Clean up import hook after each test."""
        uninstall_import_hook()

    def test_package_spec_has_submodule_search_locations(self, tmp_path):
        """A claimed package spec must point at the package directory."""
        finder = LegesherMetaPathFinder(language="es")
        pkg_dir = tmp_path / "mypkg"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")

        with patch.object(sys, "path", [str(tmp_path)]):
            spec = finder.find_spec("mypkg", None)

        assert spec is not None
        assert spec.submodule_search_locations == [str(pkg_dir)]

    def test_claimed_modules_get_file_attribute(self, tmp_path):
        """Modules loaded through the hook get __file__ like any source module.

        A bare ModuleSpec defaults has_location to False, and the import
        system only sets __file__ for specs with a location, so every
        hook-loaded module used to have no __file__.
        """
        module_path = tmp_path / "located_mod.py"
        module_path.write_text("VALUE = 1\n")

        with patch.object(sys, "path", [str(tmp_path)] + sys.path):
            install_import_hook("es")
            try:
                import located_mod
            finally:
                uninstall_import_hook()
                sys.modules.pop("located_mod", None)

        assert located_mod.__spec__.has_location
        assert located_mod.__file__ == str(module_path)

    def test_find_spec_resolves_tail_against_parent_path(self, tmp_path):
        """A dotted name searches only its tail inside the parent __path__."""
        finder = LegesherMetaPathFinder(language="es")
        pkg_dir = tmp_path / "mypkg"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "child.py").write_text("VALUE = 1")

        # The import machinery passes the parent package's __path__ entries.
        spec = finder.find_spec("mypkg.child", [str(pkg_dir)])
        assert spec is not None
        assert spec.origin == str(pkg_dir / "child.py")

    def test_find_spec_declines_dotted_name_without_path(self, tmp_path):
        """A dotted fullname with path=None must not resolve from sys.path.

        The normal import machinery always passes the parent package's
        __path__ for a submodule, so this call shape never comes from it.
        Resolving the tail against sys.path would claim an unrelated
        top-level module (a stray client.py as `http.client`).
        """
        finder = LegesherMetaPathFinder(language="es")
        (tmp_path / "client.py").write_text("x = 1\n")

        with patch.object(sys, "path", [str(tmp_path)]):
            assert finder.find_spec("http.client", None) is None

    def test_import_http_client_works_despite_decoy_toplevel_client(self, tmp_path):
        """`import http.client` resolves the stdlib module, not a decoy client.py."""
        (tmp_path / "client.py").write_text("x = 1\n")
        saved = {
            name: sys.modules.pop(name)
            for name in list(sys.modules)
            if name == "http" or name.startswith("http.")
        }
        sys.path.insert(0, str(tmp_path))
        try:
            install_import_hook(language="es")
            import http.client

            assert hasattr(http.client, "HTTPConnection")
        finally:
            uninstall_import_hook()
            sys.path.remove(str(tmp_path))
            for name in list(sys.modules):
                if name == "http" or name.startswith("http."):
                    del sys.modules[name]
            sys.modules.update(saved)

    def test_import_http_client_under_hook(self):
        """`import http.client` must work with the hook installed."""
        saved = {
            name: sys.modules.pop(name)
            for name in list(sys.modules)
            if name == "http" or name.startswith("http.")
        }
        try:
            install_import_hook(language="es")
            import http.client

            assert hasattr(http.client, "HTTPConnection")
        finally:
            uninstall_import_hook()
            for name in list(sys.modules):
                if name == "http" or name.startswith("http."):
                    del sys.modules[name]
            sys.modules.update(saved)

    def test_import_os_path_under_hook(self):
        """`import os.path` must work with the hook installed."""
        install_import_hook(language="es")
        import os.path

        assert callable(os.path.join)

    def test_dotted_import_of_translated_submodule(self, tmp_path):
        """A translated submodule of a translated package imports and runs."""
        finder_probe = LegesherMetaPathFinder(language="es")
        native_source = finder_probe.translator.translate_code(
            "def get_value():\n    if True:\n        return 42\n    return 0\n"
        )
        # Sanity: the fixture really is native-language source.
        assert native_source != (
            "def get_value():\n    if True:\n        return 42\n    return 0\n"
        )

        pkg_dir = tmp_path / "paquete_es"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "modulo.py").write_text(native_source, encoding="utf-8")

        sys.path.insert(0, str(tmp_path))
        try:
            install_import_hook(language="es")
            import paquete_es.modulo

            assert paquete_es.modulo.get_value() == 42
        finally:
            uninstall_import_hook()
            sys.path.remove(str(tmp_path))
            for name in ("paquete_es", "paquete_es.modulo"):
                sys.modules.pop(name, None)


class TestParseFirstTranslationDetection:
    """Regression tests for CORE-1209: parse-first translation detection.

    Pre-fix detection was permanently False: the old body guarded on a
    translator attribute that never existed, so the word-scan branch it
    guarded never ran and nothing was ever translated. Restoring
    detection with that word-scan would flag any module sharing a single
    word with the active pack's native vocabulary, and the finder claims
    every .py on the search path, so plain-English modules would be
    "translated" and corrupted: under the es pack `con = ...` would fail
    to import with a SyntaxError (`con` renders `with`), and an
    `ErrorDeOS` attribute would be silently renamed to `OSError`.
    Detection instead translates only source that fails ast.parse, and a
    translation that does not itself parse is discarded.
    """

    def setup_method(self):
        """Ensure import hook is not installed before each test."""
        uninstall_import_hook()

    def teardown_method(self):
        """Clean up import hook after each test."""
        uninstall_import_hook()

    def test_english_module_with_native_vocab_word_imports_unchanged(self, tmp_path):
        """`con = sqlite3.connect(...)` imports as-is under the es pack."""
        (tmp_path / "english_con_module.py").write_text(
            'import sqlite3\ncon = sqlite3.connect(":memory:")\n'
        )
        sys.path.insert(0, str(tmp_path))
        try:
            install_import_hook(language="es")
            import english_con_module

            assert hasattr(english_con_module, "con")
            english_con_module.con.close()
        finally:
            uninstall_import_hook()
            sys.path.remove(str(tmp_path))
            sys.modules.pop("english_con_module", None)

    def test_english_module_attribute_is_not_renamed(self, tmp_path):
        """An `ErrorDeOS` attribute stays; no silent rename to OSError."""
        (tmp_path / "english_attr_module.py").write_text("ErrorDeOS = 41\n")
        sys.path.insert(0, str(tmp_path))
        try:
            install_import_hook(language="es")
            import english_attr_module

            assert english_attr_module.ErrorDeOS == 41
            assert "OSError" not in vars(english_attr_module)
        finally:
            uninstall_import_hook()
            sys.path.remove(str(tmp_path))
            sys.modules.pop("english_attr_module", None)

    def test_genuine_syntax_error_reports_the_users_own_line(self, tmp_path):
        """A broken English module reports ITS error, not a relocated one.

        The parse probe fails for broken English just as it does for
        native source, so the module went down the translation path;
        translation rewrote an unrelated `con` into the keyword `with`
        and the compiler reported that earlier line instead of the
        missing colon the user actually wrote.
        """
        source = (
            "import os\n"
            "\n"
            "con = 5\n"  # `con` renders `with` under the es pack
            "\n"
            "def go(x)\n"  # the real bug, line 5
            "    return x\n"
        )
        (tmp_path / "broken_without_hook.py").write_text(source, encoding="utf-8")
        (tmp_path / "broken_under_hook.py").write_text(source, encoding="utf-8")

        sys.path.insert(0, str(tmp_path))
        try:
            with pytest.raises(SyntaxError) as without_hook:
                importlib.import_module("broken_without_hook")

            install_import_hook(language="es")
            with pytest.raises(SyntaxError) as under_hook:
                importlib.import_module("broken_under_hook")
        finally:
            uninstall_import_hook()
            sys.path.remove(str(tmp_path))
            for name in ("broken_without_hook", "broken_under_hook"):
                sys.modules.pop(name, None)

        assert without_hook.value.lineno == 5
        assert under_hook.value.lineno == without_hook.value.lineno
        assert under_hook.value.msg == without_hook.value.msg
        assert (under_hook.value.text or "").strip() == "def go(x)"


class TestBomIsStrippedBeforeTranslation:
    """Regression tests for CORE-1209: a leading BOM never reaches the translator.

    get_data reads with encoding="utf-8", which keeps a BOM as U+FEFF.
    Stripping it only inside the parse probe left the translator with a
    BOM-fused first token it could not recognise, so a UTF-8-with-BOM
    native module kept its opening keyword native while the rest
    translated, and failed exactly as if the hook were not installed.
    """

    def setup_method(self):
        """Ensure import hook is not installed before each test."""
        uninstall_import_hook()

    def teardown_method(self):
        """Clean up import hook after each test."""
        uninstall_import_hook()

    def test_utf8_bom_native_module_imports_and_runs(self, tmp_path):
        """A UTF-8-with-BOM Spanish module translates whole and runs."""
        english_source = (
            "def get_value():\n    if True:\n        return 42\n    return 0\n"
        )
        finder_probe = LegesherMetaPathFinder(language="es")
        native_source = finder_probe.translator.translate_code(english_source)
        # Sanity: the fixture really is native-language source.
        assert native_source != english_source

        # U+FEFF encodes to the three UTF-8 BOM bytes.
        module_path = tmp_path / "bom_native_es.py"
        module_path.write_text("\ufeff" + native_source, encoding="utf-8")
        assert module_path.read_bytes().startswith(b"\xef\xbb\xbf")

        sys.path.insert(0, str(tmp_path))
        try:
            install_import_hook(language="es")
            import bom_native_es

            assert bom_native_es.get_value() == 42
        finally:
            uninstall_import_hook()
            sys.path.remove(str(tmp_path))
            sys.modules.pop("bom_native_es", None)

    def test_utf8_bom_english_module_imports_untranslated(self, tmp_path):
        """A UTF-8-with-BOM English module still imports as-is."""
        module_path = tmp_path / "bom_english_module.py"
        module_path.write_text(
            '\ufeffimport sqlite3\ncon = sqlite3.connect(":memory:")\nErrorDeOS = 41\n',
            encoding="utf-8",
        )
        assert module_path.read_bytes().startswith(b"\xef\xbb\xbf")

        sys.path.insert(0, str(tmp_path))
        try:
            install_import_hook(language="es")
            import bom_english_module

            assert bom_english_module.ErrorDeOS == 41
            assert "OSError" not in vars(bom_english_module)
            bom_english_module.con.close()
        finally:
            uninstall_import_hook()
            sys.path.remove(str(tmp_path))
            sys.modules.pop("bom_english_module", None)


class TestImportHookInstallation:
    """Test import hook installation and management."""

    def setup_method(self):
        """Ensure import hook is not installed before each test."""
        uninstall_import_hook()

    def teardown_method(self):
        """Clean up import hook after each test."""
        uninstall_import_hook()

    def test_install_import_hook_adds_to_meta_path(self):
        """Test that install_import_hook adds finder to sys.meta_path."""
        initial_count = len(sys.meta_path)
        install_import_hook(language="es")

        assert len(sys.meta_path) == initial_count + 1
        assert isinstance(sys.meta_path[0], LegesherMetaPathFinder)
        assert sys.meta_path[0].language == "es"

    def test_install_import_hook_raises_if_already_installed(self):
        """Test that installing twice raises RuntimeError."""
        install_import_hook(language="es")

        with pytest.raises(RuntimeError) as exc_info:
            install_import_hook(language="es")
        assert "already installed" in str(exc_info.value)

    def test_uninstall_import_hook_removes_from_meta_path(self):
        """Test that uninstall_import_hook removes finder."""
        install_import_hook(language="es")
        initial_count = len(sys.meta_path)
        uninstall_import_hook()

        assert len(sys.meta_path) == initial_count - 1
        for finder in sys.meta_path:
            assert not isinstance(finder, LegesherMetaPathFinder)

    def test_uninstall_import_hook_safe_when_not_installed(self):
        """Test that uninstall_import_hook is safe to call when not installed."""
        uninstall_import_hook()
        uninstall_import_hook()  # Should not raise

    def test_is_hook_installed_returns_correct_status(self):
        """Test that is_hook_installed returns correct status."""
        assert is_hook_installed() is False

        install_import_hook(language="es")
        assert is_hook_installed() is True

        uninstall_import_hook()
        assert is_hook_installed() is False

    def test_get_installed_language_returns_correct_language(self):
        """Test that get_installed_language returns correct language."""
        assert get_installed_language() is None

        install_import_hook(language="fr")
        assert get_installed_language() == "fr"

        uninstall_import_hook()
        assert get_installed_language() is None


class TestTranslationCache:
    """Test _TranslationCache LRU cache implementation."""

    def test_cache_init_with_default_size(self):
        """Test cache initialization with default size."""
        cache = _TranslationCache()
        assert cache._max_size == 128
        stats = cache.get_stats()
        assert stats["size"] == 0
        assert stats["max_size"] == 128
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["evictions"] == 0

    def test_cache_init_with_custom_size(self):
        """Test cache initialization with custom size."""
        cache = _TranslationCache(max_size=256)
        assert cache._max_size == 256
        assert cache.get_stats()["max_size"] == 256

    def test_cache_init_validates_negative_size(self):
        """Test that negative cache size is clamped to 0."""
        cache = _TranslationCache(max_size=-10)
        assert cache._max_size == 0

    def test_cache_with_zero_size_stores_nothing(self):
        """Test that cache with max_size=0 doesn't store items."""
        cache = _TranslationCache(max_size=0)
        cache.set(("test.py", 123), b"content")

        # Should not store anything - immediately evicted
        assert cache.get(("test.py", 123)) is None
        stats = cache.get_stats()
        assert stats["size"] == 0
        assert stats["evictions"] == 1
        assert stats["misses"] == 1

    def test_cache_get_miss_returns_none(self):
        """Test that cache miss returns None."""
        cache = _TranslationCache()
        result = cache.get(("test.py", 123))
        assert result is None
        assert cache.get_stats()["misses"] == 1
        assert cache.get_stats()["hits"] == 0

    def test_cache_set_and_get(self):
        """Test basic cache set and get."""
        cache = _TranslationCache()
        key = ("test.py", 123)
        value = b"cached content"

        cache.set(key, value)
        result = cache.get(key)

        assert result == value
        stats = cache.get_stats()
        assert stats["size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 0

    def test_cache_lru_eviction(self):
        """Test that LRU eviction removes oldest entries."""
        cache = _TranslationCache(max_size=3)

        # Add 3 items (fill cache)
        cache.set(("file1.py", 1), b"content1")
        cache.set(("file2.py", 2), b"content2")
        cache.set(("file3.py", 3), b"content3")
        assert cache.get_stats()["size"] == 3
        assert cache.get_stats()["evictions"] == 0

        # Add 4th item - should evict oldest (file1.py)
        cache.set(("file4.py", 4), b"content4")
        assert cache.get_stats()["size"] == 3
        assert cache.get_stats()["evictions"] == 1

        # file1 should be evicted
        assert cache.get(("file1.py", 1)) is None
        assert cache.get(("file2.py", 2)) == b"content2"
        assert cache.get(("file3.py", 3)) == b"content3"
        assert cache.get(("file4.py", 4)) == b"content4"

    def test_cache_lru_update_on_get(self):
        """Test that accessing an item marks it as recently used."""
        cache = _TranslationCache(max_size=3)

        cache.set(("file1.py", 1), b"content1")
        cache.set(("file2.py", 2), b"content2")
        cache.set(("file3.py", 3), b"content3")

        # Access file1 to mark it as recently used
        cache.get(("file1.py", 1))

        # Add file4 - should evict file2 (oldest), not file1
        cache.set(("file4.py", 4), b"content4")

        assert cache.get(("file1.py", 1)) == b"content1"  # Still cached
        assert cache.get(("file2.py", 2)) is None  # Evicted
        assert cache.get(("file3.py", 3)) == b"content3"
        assert cache.get(("file4.py", 4)) == b"content4"

    def test_cache_clear_resets_cache_and_stats(self):
        """Test that clear() empties cache and resets statistics."""
        cache = _TranslationCache()
        cache.set(("file1.py", 1), b"content1")
        cache.set(("file2.py", 2), b"content2")
        cache.get(("file1.py", 1))  # Hit
        cache.get(("file3.py", 3))  # Miss

        stats_before = cache.get_stats()
        assert stats_before["size"] == 2
        assert stats_before["hits"] == 1
        assert stats_before["misses"] == 1

        cache.clear()

        stats_after = cache.get_stats()
        assert stats_after["size"] == 0
        assert stats_after["hits"] == 0
        assert stats_after["misses"] == 0
        assert stats_after["evictions"] == 0

    def test_cache_hit_rate_calculation(self):
        """Test that hit rate is calculated correctly."""
        cache = _TranslationCache()
        cache.set(("file1.py", 1), b"content1")

        cache.get(("file1.py", 1))  # Hit
        cache.get(("file1.py", 1))  # Hit
        cache.get(("file1.py", 1))  # Hit
        cache.get(("file2.py", 2))  # Miss

        stats = cache.get_stats()
        assert stats["hits"] == 3
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.75  # 3/4 = 75%

    def test_cache_hit_rate_zero_when_no_accesses(self):
        """Test that hit rate is 0 when cache is empty."""
        cache = _TranslationCache()
        stats = cache.get_stats()
        assert stats["hit_rate"] == 0.0

    def test_cache_thread_safety(self):
        """Test that cache operations are thread-safe."""
        cache = _TranslationCache(max_size=100)
        errors = []

        def worker(thread_id):
            try:
                for i in range(20):
                    key = (f"file{thread_id}_{i}.py", i)
                    cache.set(key, f"content_{thread_id}_{i}".encode())
                    result = cache.get(key)
                    assert result is not None
            except Exception as e:
                errors.append(e)

        # Run 10 threads concurrently
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread-safety errors: {errors}"
        stats = cache.get_stats()
        assert stats["size"] <= 100  # Cache size should be bounded


class TestCacheConfiguration:
    """Test cache configuration precedence and resolution."""

    def test_get_cache_size_with_explicit_parameter(self):
        """Test that explicit parameter has highest precedence."""
        with patch.dict(os.environ, {"LEGESHER_CACHE_SIZE": "64"}):
            size = _get_cache_size(explicit_size=256)
            assert size == 256

    def test_get_cache_size_from_environment_variable(self):
        """Test that environment variable is used when no explicit size."""
        with patch.dict(os.environ, {"LEGESHER_CACHE_SIZE": "512"}):
            size = _get_cache_size()
            assert size == 512

    def test_get_cache_size_invalid_env_var_falls_back(self):
        """Test that invalid env var falls back to config/default."""
        with patch.dict(os.environ, {"LEGESHER_CACHE_SIZE": "invalid"}):
            size = _get_cache_size()
            assert size == 128  # Default

    def test_get_cache_size_from_config_file(self):
        """Test that config file is used when env var not set."""
        mock_config = MagicMock()
        mock_config.runtime_cache_size = 1024

        with patch(
            "legesher.runtime.import_hook.LegesherConfig.load", return_value=mock_config
        ):
            with patch.dict(os.environ, {}, clear=True):
                size = _get_cache_size()
                assert size == 1024

    def test_get_cache_size_default_when_no_config(self):
        """Test that default is used when no configuration exists."""
        with patch.dict(os.environ, {}, clear=True):
            with patch(
                "legesher.runtime.import_hook.LegesherConfig.load",
                side_effect=Exception("No config"),
            ):
                size = _get_cache_size()
                assert size == 128  # Default

    def test_get_cache_size_validates_negative_values(self):
        """Test that negative values are clamped to 0."""
        assert _get_cache_size(explicit_size=-10) == 0

        with patch.dict(os.environ, {"LEGESHER_CACHE_SIZE": "-50"}):
            assert _get_cache_size() == 0

    def test_install_hook_with_explicit_cache_size(self):
        """Test installing import hook with explicit cache size."""
        try:
            finder = install_import_hook(language="es", cache_size=512)
            assert finder.cache._max_size == 512
        finally:
            uninstall_import_hook()

    def test_install_hook_with_env_var_cache_size(self):
        """Test installing import hook with environment variable."""
        with patch.dict(os.environ, {"LEGESHER_CACHE_SIZE": "256"}):
            try:
                finder = install_import_hook(language="es")
                assert finder.cache._max_size == 256
            finally:
                uninstall_import_hook()


class TestCacheAPI:
    """Test public cache management API."""

    def setup_method(self):
        """Ensure import hook is not installed before each test."""
        uninstall_import_hook()

    def teardown_method(self):
        """Clean up import hook after each test."""
        uninstall_import_hook()

    def test_get_cache_stats_when_no_hook_installed(self):
        """Test that get_cache_stats returns None when no hook installed."""
        assert get_cache_stats() is None

    def test_get_cache_stats_returns_statistics(self):
        """Test that get_cache_stats returns cache statistics."""
        install_import_hook(language="es", cache_size=128)
        stats = get_cache_stats()

        assert stats is not None
        assert "hits" in stats
        assert "misses" in stats
        assert "evictions" in stats
        assert "size" in stats
        assert "max_size" in stats
        assert "hit_rate" in stats
        assert stats["max_size"] == 128

    def test_clear_cache_when_no_hook_installed(self):
        """Test that clear_cache is safe when no hook installed."""
        clear_cache()  # Should not raise

    def test_clear_cache_clears_installed_hook(self):
        """Test that clear_cache clears the cache in installed hook."""
        finder = install_import_hook(language="es")

        # Add something to cache
        finder.cache.set(("test.py", 123), b"content")
        assert finder.cache.get_stats()["size"] == 1

        clear_cache()

        stats = get_cache_stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0
