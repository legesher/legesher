"""Unit tests for import_hook module."""

import os
import sys
import importlib
import importlib.machinery
import importlib.metadata
import importlib.util
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
        module_file.write_text("# Test module\ndefinir f():\n    retornar 1\n")

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
        (pkg_dir / "__init__.py").write_text("definir f():\n    retornar 1\n")

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
        (pkg_dir / "child.py").write_text("definir f():\n    retornar 1\n")

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

    get_data once read with encoding="utf-8", which keeps a BOM as U+FEFF,
    and the translator then saw a BOM-fused first token it could not
    recognise, so a UTF-8-with-BOM native module kept its opening keyword
    native and failed to import. Source is now decoded as the stock loader
    decodes it, where the BOM selects utf-8-sig and is dropped (CORE-2206).
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


# Paths the interpreter opens or creates while _AUDIT_STATE["on"] is set.
# Audit hooks cannot be removed once added, so one hook is registered for
# the whole session and records nothing until a test switches it on.
_AUDIT_STATE: dict = {"on": False, "events": []}


def _record_file_events(event, args):
    # os.fdopen raises an "open" event whose first argument is a file
    # descriptor; only path arguments are recorded. An exception here would
    # propagate into the audited call, so nothing else is attempted.
    if _AUDIT_STATE["on"] and event in ("open", "os.mkdir") and args:
        target = args[0]
        if isinstance(target, (str, bytes, os.PathLike)):
            _AUDIT_STATE["events"].append((event, os.fsdecode(target)))


sys.addaudithook(_record_file_events)


def _purge_modules(*prefixes):
    for name in list(sys.modules):
        if any(name == p or name.startswith(p + ".") for p in prefixes):
            del sys.modules[name]


class TestBytecodeIsolation:
    """The hook never loads a stock .pyc for a file it claims.

    A stock .pyc is validated only by the source's mtime and size. If the
    hook trusted one, bytecode compiled from different source could run
    in place of what the user wrote, and a translated file could end up
    keyed to its native source. Each test plants a poisoned .pyc whose
    header matches the real source exactly, proves the stock loader
    would run it, then proves the hook does not.
    """

    def setup_method(self):
        uninstall_import_hook()

    def teardown_method(self):
        uninstall_import_hook()

    @staticmethod
    def _plant_poisoned_pyc(module_path, real_source, poisoned_source):
        import py_compile

        real_bytes = real_source.encode("utf-8")
        poisoned_bytes = poisoned_source.encode("utf-8")
        # Pad with a trailing comment so both sources have the same size,
        # which the .pyc header records alongside the mtime.
        assert len(poisoned_bytes) < len(real_bytes)
        padding = len(real_bytes) - len(poisoned_bytes)
        poisoned_bytes += b"#" * (padding - 1) + b"\n"
        assert len(poisoned_bytes) == len(real_bytes)

        module_path.write_bytes(poisoned_bytes)
        mtime_ns = module_path.stat().st_mtime_ns
        py_compile.compile(
            str(module_path),
            doraise=True,
            invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP,
        )
        module_path.write_bytes(real_bytes)
        os.utime(module_path, ns=(mtime_ns, mtime_ns))
        importlib.invalidate_caches()

    def _assert_hook_ignores_poison(self, tmp_path, name, real_source, poisoned):
        module_path = tmp_path / f"{name}.py"
        self._plant_poisoned_pyc(module_path, real_source, poisoned)

        sys.path.insert(0, str(tmp_path))
        try:
            # Sanity: the poison is live. The stock loader trusts the
            # matching header and runs the poisoned bytecode.
            stock = importlib.import_module(name)
            assert stock.which() == "POISON", module_path
            sys.modules.pop(name, None)

            install_import_hook(language="es")
            hooked = importlib.import_module(name)
            assert isinstance(hooked.__spec__.loader, LegesherLoader), module_path
            assert hooked.which() == "real", module_path
        finally:
            uninstall_import_hook()
            sys.path.remove(str(tmp_path))
            sys.modules.pop(name, None)

    def test_translated_module_ignores_mtime_matching_stock_pyc(self, tmp_path):
        """A native module runs its own translation, never the stock .pyc."""
        finder = LegesherMetaPathFinder(language="es")
        real = finder.translator.translate_code(
            "def which():\n    if True:\n        return 'real'\n    return None\n"
        )
        assert real.startswith("definir"), real
        self._assert_hook_ignores_poison(
            tmp_path,
            "poisoned_native_es",
            real,
            "def which():\n    return 'POISON'\n",
        )

    def test_claimed_english_module_ignores_mtime_matching_stock_pyc(self, tmp_path):
        """An English module the hook claims runs its source, not the .pyc."""
        # `con` renders `with` under the es pack: plain English that shares
        # a word with the native vocabulary.
        real = "con = 'real'\n\ndef which():\n    return con\n"
        self._assert_hook_ignores_poison(
            tmp_path,
            "poisoned_english_es",
            real,
            "def which():\n    return 'POISON'\n",
        )


class TestPackageDataUnderHook:
    """Regression tests for CORE-2204: packages that ship data files.

    LegesherLoader had no get_resource_reader, which the stock
    SourceFileLoader inherits from FileLoader, so importlib.resources
    raised "Can't open orphan path" for every package the hook claimed
    (`import requests` failed in certifi's where()). get_data also
    translated any path it was handed, so pkgutil.get_data returned a
    rewritten text file and raised on a binary one.
    """

    DATA_BINARY = bytes(range(256))

    @classmethod
    def setup_class(cls):
        # Native source whose translation parses: the old get_data returned
        # it rewritten as `if True: pass`, so comparing bytes catches any
        # data file that still goes down the translation path.
        finder = LegesherMetaPathFinder(language="es")
        english = "if True:\n    pass\n"
        cls.DATA_TEXT = finder.translator.translate_code(english)
        assert cls.DATA_TEXT != english
        assert finder.reverse_translator.translate_code(cls.DATA_TEXT) == english

    def setup_method(self):
        uninstall_import_hook()

    def teardown_method(self):
        uninstall_import_hook()
        _AUDIT_STATE["on"] = False
        _AUDIT_STATE["events"].clear()

    def _make_package(self, tmp_path, name):
        finder = LegesherMetaPathFinder(language="es")
        init_source = finder.translator.translate_code(
            "from importlib.resources import files\n\n"
            "def read_data():\n"
            "    return files(__name__).joinpath('data.txt').read_text("
            "encoding='utf-8')\n"
        )
        assert init_source.startswith("desde"), init_source
        pkg_dir = tmp_path / name
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text(init_source, encoding="utf-8")
        (pkg_dir / "data.txt").write_text(self.DATA_TEXT, encoding="utf-8")
        (pkg_dir / "blob.bin").write_bytes(self.DATA_BINARY)
        importlib.invalidate_caches()
        return pkg_dir

    def _import_under_hook(self, tmp_path, name):
        sys.path.insert(0, str(tmp_path))
        install_import_hook(language="es")
        module = importlib.import_module(name)
        assert isinstance(module.__spec__.loader, LegesherLoader), module.__file__
        return module

    def _cleanup(self, tmp_path, name):
        uninstall_import_hook()
        sys.path.remove(str(tmp_path))
        _purge_modules(name)

    def test_importlib_resources_reads_package_data(self, tmp_path):
        """files(pkg).joinpath(...).read_text() works for a claimed package."""
        import importlib.resources

        pkg_dir = self._make_package(tmp_path, "datapkg_resources")
        try:
            pkg = self._import_under_hook(tmp_path, "datapkg_resources")
            data = importlib.resources.files(pkg).joinpath("data.txt")
            assert data.read_text(encoding="utf-8") == self.DATA_TEXT, pkg_dir
            assert pkg.read_data() == self.DATA_TEXT, pkg_dir
            blob = importlib.resources.files(pkg).joinpath("blob.bin")
            assert blob.read_bytes() == self.DATA_BINARY, pkg_dir
        finally:
            self._cleanup(tmp_path, "datapkg_resources")

    def test_resource_reader_is_the_file_reader(self, tmp_path):
        """The reader serves files from the package directory."""
        pkg_dir = self._make_package(tmp_path, "datapkg_reader")
        try:
            pkg = self._import_under_hook(tmp_path, "datapkg_reader")
            reader = pkg.__spec__.loader.get_resource_reader(pkg.__name__)
            assert reader is not None, pkg_dir
            assert reader.resource_path("data.txt") == str(pkg_dir / "data.txt")
            assert reader.is_resource("data.txt")
            assert not reader.is_resource("missing.txt")
        finally:
            self._cleanup(tmp_path, "datapkg_reader")

    def test_pkgutil_get_data_returns_bytes_untouched(self, tmp_path):
        """pkgutil.get_data returns data files as stored, text or binary."""
        import pkgutil

        pkg_dir = self._make_package(tmp_path, "datapkg_pkgutil")
        try:
            self._import_under_hook(tmp_path, "datapkg_pkgutil")
            text = pkgutil.get_data("datapkg_pkgutil", "data.txt")
            assert text == self.DATA_TEXT.encode("utf-8"), pkg_dir / "data.txt"
            blob = pkgutil.get_data("datapkg_pkgutil", "blob.bin")
            assert blob == self.DATA_BINARY, pkg_dir / "blob.bin"
        finally:
            self._cleanup(tmp_path, "datapkg_pkgutil")

    def test_claimed_package_never_touches_stock_bytecode(self, tmp_path, monkeypatch):
        """A claimed package reads and writes only its Legesher-tagged cache.

        Until CORE-2205 the hook touched no __pycache__ at all. It now caches
        compiled code under a Legesher-specific name, so the invariant is
        stated directly: the stock .pyc path is never opened, and the only
        __pycache__ paths touched are the tagged record, its own temporary
        file, and the directory itself.
        """
        import importlib.resources
        import importlib.util

        # With a pycache prefix the stock cache path has no __pycache__
        # component, so pin the default layout and also check the exact
        # path the stock loader would use.
        monkeypatch.setattr(sys, "pycache_prefix", None)
        monkeypatch.setattr(sys, "dont_write_bytecode", False)
        pkg_dir = self._make_package(tmp_path, "datapkg_nocache")
        stock_pyc = importlib.util.cache_from_source(str(pkg_dir / "__init__.py"))
        tagged = stock_pyc[: -len(".pyc")] + ".legesher-es.pyc"
        pycache = os.path.dirname(stock_pyc)
        try:
            _AUDIT_STATE["events"].clear()
            _AUDIT_STATE["on"] = True
            pkg = self._import_under_hook(tmp_path, "datapkg_nocache")
            importlib.resources.files(pkg).joinpath("data.txt").read_text(
                encoding="utf-8"
            )
            _AUDIT_STATE["on"] = False

            events = list(_AUDIT_STATE["events"])
            opened_source = [p for _, p in events if p == str(pkg_dir / "__init__.py")]
            assert opened_source, "audit hook saw no open of the package source"
            assert stock_pyc not in [p for _, p in events], stock_pyc
            unexpected = [
                (event, path)
                for event, path in events
                if "__pycache__" in path
                and path != tagged
                and not path.startswith(tagged + ".")
                and path != pycache
            ]
            assert unexpected == [], unexpected
            assert sorted(os.listdir(pycache)) == [os.path.basename(tagged)], pycache
        finally:
            _AUDIT_STATE["on"] = False
            self._cleanup(tmp_path, "datapkg_nocache")

    def test_package_data_resolves_after_chdir(self, tmp_path, monkeypatch):
        """A package found via a relative sys.path entry keeps working after chdir."""
        import importlib.resources

        pkg_dir = self._make_package(tmp_path, "datapkg_relative")
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, "")  # what `python -c` and the REPL put first
        try:
            install_import_hook(language="es")
            pkg = importlib.import_module("datapkg_relative")
            assert isinstance(pkg.__spec__.loader, LegesherLoader), pkg.__file__
            assert pkg.__file__ == str(pkg_dir / "__init__.py"), pkg.__file__
            os.chdir(elsewhere)
            data = importlib.resources.files(pkg).joinpath("data.txt")
            assert data.read_text(encoding="utf-8") == self.DATA_TEXT, pkg_dir
        finally:
            uninstall_import_hook()
            sys.path.remove("")
            _purge_modules("datapkg_relative")

    def test_import_requests_under_hook(self, tmp_path):
        """`import requests` works under the hook, certifi's data included.

        Installed packages load through the stock machinery (CORE-2205), so
        requests and certifi must work and must not be claimed. The resource
        reader itself is covered by the claimed packages in this class.
        """
        import subprocess

        pytest.importorskip(
            "requests", reason="requests is not installed in this environment"
        )
        script = (
            "import sys\n"
            "from legesher.runtime import install_import_hook\n"
            "from legesher.runtime.import_hook import LegesherLoader\n"
            "install_import_hook('es')\n"
            "assert 'certifi' not in sys.modules, 'certifi loaded before the hook'\n"
            "import requests, requests.utils, certifi\n"
            "for mod in (requests.utils, certifi):\n"
            "    loader = mod.__spec__.loader\n"
            "    assert not isinstance(loader, LegesherLoader), (mod.__name__, loader)\n"
            "print(requests.certs.where())\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            timeout=120,
        )
        assert result.returncode == 0, result.stderr
        bundle = result.stdout.strip().splitlines()[-1]
        assert os.path.isfile(bundle), bundle


class TestSourceEncoding:
    """Regression tests for CORE-2206: PEP 263 coding declarations.

    get_data read every module as UTF-8, so a module declaring
    `# -*- coding: latin-1 -*-` with real latin-1 bytes imported without
    the hook and raised UnicodeDecodeError from hook internals with it.
    """

    COOKIE = "# -*- coding: latin-1 -*-\n"

    def setup_method(self):
        uninstall_import_hook()

    def teardown_method(self):
        uninstall_import_hook()

    def _import_under_hook(self, tmp_path, name):
        sys.path.insert(0, str(tmp_path))
        importlib.invalidate_caches()
        try:
            install_import_hook(language="es")
            module = importlib.import_module(name)
            assert isinstance(module.__spec__.loader, LegesherLoader), module
            return module
        finally:
            uninstall_import_hook()
            sys.path.remove(str(tmp_path))
            sys.modules.pop(name, None)

    def test_latin1_english_module_keeps_its_text(self, tmp_path):
        """An English latin-1 module imports with its non-ASCII text intact."""
        # `con` renders `with` under es: English sharing a word with the
        # pack, so the hook claims it and must leave it untranslated.
        source = self.COOKIE + "GREETING = 'café'\ncon = 1\n"
        module_path = tmp_path / "latin1_english.py"
        module_path.write_bytes(source.encode("latin-1"))
        assert b"\xe9" in module_path.read_bytes()

        module = self._import_under_hook(tmp_path, "latin1_english")
        assert module.GREETING == "café", module_path

    def test_latin1_native_module_translates_and_keeps_its_text(self, tmp_path):
        """A native latin-1 module is translated and its strings survive.

        The translated source must be compiled from text: compiled from
        UTF-8 bytes, the surviving latin-1 cookie would re-decode `é` as
        two characters.
        """
        finder = LegesherMetaPathFinder(language="es")
        native = finder.translator.translate_code(
            "def greeting():\n    if True:\n        return 'café'\n    return None\n"
        )
        assert native.startswith("definir"), native
        module_path = tmp_path / "latin1_native.py"
        module_path.write_bytes((self.COOKIE + native).encode("latin-1"))

        module = self._import_under_hook(tmp_path, "latin1_native")
        assert module.greeting() == "café", module_path

    def test_undecodable_module_raises_syntax_error_naming_the_file(self, tmp_path):
        """Bytes invalid in the declared encoding fail as stock Python fails."""
        module_path = tmp_path / "undecodable_mod.py"
        module_path.write_bytes(b"VALUE = '\xff\xfe'\n")

        sys.path.insert(0, str(tmp_path))
        importlib.invalidate_caches()
        try:
            with pytest.raises(SyntaxError) as stock:
                importlib.import_module("undecodable_mod")
            sys.modules.pop("undecodable_mod", None)

            install_import_hook(language="es")
            with pytest.raises(SyntaxError) as hooked:
                importlib.import_module("undecodable_mod")
        finally:
            uninstall_import_hook()
            sys.path.remove(str(tmp_path))
            sys.modules.pop("undecodable_mod", None)

        assert hooked.value.filename == str(module_path), hooked.value
        assert hooked.value.msg == stock.value.msg

    def test_get_source_decodes_by_the_declared_encoding(self, tmp_path):
        """Callers of loader.get_source (pdb, doctest) get the text that ran.

        Decoding the returned UTF-8 source by its surviving latin-1
        declaration, as SourceLoader.get_source does, would garble it.
        """
        source = self.COOKIE + "GREETING = 'café'\n"
        module_path = tmp_path / "latin1_source.py"
        module_path.write_bytes(source.encode("latin-1"))
        finder = LegesherMetaPathFinder(language="es")
        loader = LegesherLoader("latin1_source", str(module_path), finder)

        assert "'café'" in loader.get_source("latin1_source"), module_path

    @staticmethod
    def _outcome(module_name):
        try:
            module = importlib.import_module(module_name)
        except SyntaxError as exc:
            return ("SyntaxError", exc.msg, os.path.basename(exc.filename or ""))
        return ("imported", module.VALUE, None)

    @pytest.mark.parametrize(
        "case, raw",
        [
            # Invalid UTF-8 in a comment: tokenize rejects it, while the
            # compiler accepts it on 3.10 to 3.13 and rejects it on 3.14.
            ("comment_line1", b"VALUE = 1  # \xff\xfe\ncon = 2\n"),
            ("comment_line3", b"import os\n\nVALUE = 1  # caf\xe9\ncon = 2\n"),
            # A latin-1 comment ahead of a line-2 cookie.
            (
                "cookie_line2",
                b"# Auteur: Fr\xe9d\xe9ric\n# -*- coding: latin-1 -*-\nVALUE = 1\ncon = 2\n",
            ),
            # A cookie naming a codec that does not produce text.
            ("rot13_cookie", b"# -*- coding: rot13 -*-\nVALUE = 1\ncon = 2\n"),
            # Two BOMs: the second is a stray U+FEFF character.
            ("double_bom", b"\xef\xbb\xbf\xef\xbb\xbfVALUE = 1\ncon = 2\n"),
            # An unknown codec.
            ("unknown_codec", b"# -*- coding: no-such-codec -*-\nVALUE = 1\ncon = 2\n"),
        ],
    )
    def test_edge_encodings_match_stock_python(self, tmp_path, case, raw):
        """Whatever stock Python does with these bytes, the hook does too.

        Imported or refused, and when refused, the same message naming the
        module's own file, on every supported interpreter. Each file ends
        with `con = 2` (`con` renders `with` under es), so the hook claims
        it and the comparison exercises the hook's own decoding.
        """
        stock_dir, hook_dir = tmp_path / "stock", tmp_path / "hook"
        stock_dir.mkdir()
        hook_dir.mkdir()
        name = f"edge_{case}"
        (stock_dir / f"{name}.py").write_bytes(raw)
        (hook_dir / f"{name}.py").write_bytes(raw)

        # The hook must claim every case, refused ones included, or a refusal
        # would only be stock Python agreeing with itself.
        with patch.object(sys, "path", [str(hook_dir)]):
            importlib.invalidate_caches()
            spec = LegesherMetaPathFinder(language="es").find_spec(name, None)
        assert spec is not None, hook_dir / f"{name}.py"

        sys.path.insert(0, str(stock_dir))
        importlib.invalidate_caches()
        try:
            stock = self._outcome(name)
        finally:
            sys.path.remove(str(stock_dir))
            sys.modules.pop(name, None)

        sys.path.insert(0, str(hook_dir))
        importlib.invalidate_caches()
        try:
            install_import_hook(language="es")
            hooked = self._outcome(name)
            if hooked[0] == "imported":
                loader = sys.modules[name].__spec__.loader
                assert isinstance(loader, LegesherLoader), hook_dir / f"{name}.py"
        finally:
            uninstall_import_hook()
            sys.path.remove(str(hook_dir))
            sys.modules.pop(name, None)

        assert hooked == stock, (hook_dir / f"{name}.py", stock, hooked)


class TestStockPrecedence:
    """Regression tests for CORE-2206: which file a module name resolves to.

    The finder walked each path entry for `__init__.py` and `.py` only, so
    a compiled extension lost to a same-named `.py` file (452 such pairs in
    one venv, including mypyc.options). The finder now asks the stock
    PathFinder which file stock Python would load, and claims only a
    source file, so FileFinder precedence holds exactly.
    """

    EXT = importlib.machinery.EXTENSION_SUFFIXES[0]

    def setup_method(self):
        uninstall_import_hook()

    def teardown_method(self):
        uninstall_import_hook()

    def test_extension_beats_same_named_py(self, tmp_path):
        """A `twin<ext>` beside `twin.py` is left to the extension loader."""
        (tmp_path / "twin.py").write_text("definir f():\n    retornar 1\n")
        finder = LegesherMetaPathFinder(language="es")

        with patch.object(sys, "path", [str(tmp_path)]):
            importlib.invalidate_caches()
            control = finder.find_spec("twin", None)
            assert control is not None, "control: twin.py alone must be claimed"

            (tmp_path / f"twin{self.EXT}").write_bytes(b"not a real extension")
            importlib.invalidate_caches()
            assert finder.find_spec("twin", None) is None, tmp_path / "twin.py"

    def test_extension_in_earlier_entry_beats_py_in_later_entry(self, tmp_path):
        """Path-entry order decides across directories, as stock does."""
        first, second = tmp_path / "first", tmp_path / "second"
        first.mkdir()
        second.mkdir()
        (first / f"cross{self.EXT}").write_bytes(b"not a real extension")
        (second / "cross.py").write_text("definir f():\n    retornar 1\n")
        finder = LegesherMetaPathFinder(language="es")

        with patch.object(sys, "path", [str(first), str(second)]):
            importlib.invalidate_caches()
            assert finder.find_spec("cross", None) is None, second / "cross.py"

    def test_real_extension_twin_is_not_claimed(self):
        """mypyc.options ships as both options.py and a compiled extension."""
        parent = importlib.util.find_spec("mypyc")
        if parent is None:
            pytest.skip("mypyc is not installed in this environment")
        stock = importlib.machinery.PathFinder.find_spec(
            "mypyc.options", parent.submodule_search_locations
        )
        if not isinstance(stock.loader, importlib.machinery.ExtensionFileLoader):
            pytest.skip("mypyc.options is not compiled in this environment")

        finder = LegesherMetaPathFinder(language="es")
        spec = finder.find_spec("mypyc.options", parent.submodule_search_locations)
        assert spec is None, stock.origin

    def test_sourceless_bytecode_is_not_claimed(self, tmp_path):
        """A lone .pyc in a path entry is stock's to load, never the hook's."""
        import py_compile

        source = tmp_path / "src_only.py"
        source.write_text("VALUE = 1\n")
        py_compile.compile(
            str(source), cfile=str(tmp_path / "sourceless_mod.pyc"), doraise=True
        )
        source.unlink()
        finder = LegesherMetaPathFinder(language="es")

        with patch.object(sys, "path", [str(tmp_path)]):
            importlib.invalidate_caches()
            assert finder.find_spec("sourceless_mod", None) is None

    def test_name_matching_differs_only_in_case_is_not_claimed(self, tmp_path):
        """`import casemod` never loads CaseMod.py, on any filesystem."""
        (tmp_path / "CaseMod.py").write_text("VALUE = 1\n")
        finder = LegesherMetaPathFinder(language="es")

        with patch.dict(os.environ), patch.object(sys, "path", [str(tmp_path)]):
            os.environ.pop("PYTHONCASEOK", None)
            importlib.invalidate_caches()
            assert finder.find_spec("casemod", None) is None, tmp_path / "CaseMod.py"


class TestStockImportersOwnTheirNames:
    """Regression tests for CORE-2206 review: built-in and frozen names.

    The hook sits at the front of sys.meta_path, ahead of the builtin and
    frozen importers. Stock Python never looks on sys.path for a name they
    own, so a user's file with that name must not replace the real module.
    """

    def setup_method(self):
        uninstall_import_hook()

    def teardown_method(self):
        uninstall_import_hook()

    @staticmethod
    def _shadow(tmp_path, name):
        (tmp_path / f"{name}.py").write_text("definir f():\n    retornar 1\n")
        finder = LegesherMetaPathFinder(language="es")
        with patch.object(sys, "path", [str(tmp_path)]):
            importlib.invalidate_caches()
            return finder.find_spec(name, None)

    def test_builtin_module_name_is_not_claimed(self, tmp_path):
        name = next(
            (n for n in sorted(sys.builtin_module_names) if not n.startswith("_")),
            None,
        )
        if name is None:
            pytest.skip("this interpreter has no public built-in modules")
        assert self._shadow(tmp_path, name) is None, tmp_path / f"{name}.py"
        # Control: the same file under an ordinary name is claimed.
        assert self._shadow(tmp_path, "ordinary_shadow_control") is not None

    def test_frozen_module_name_is_not_claimed(self, tmp_path):
        name = "__hello__"
        if importlib.machinery.FrozenImporter.find_spec(name) is None:
            pytest.skip("__hello__ is not frozen in this interpreter")
        assert self._shadow(tmp_path, name) is None, tmp_path / f"{name}.py"


class TestNonSourceEntriesStayStock:
    """Namespace portions and zip entries are the stock loaders' to load."""

    def test_namespace_package_is_not_claimed(self, tmp_path):
        (tmp_path / "ns_portion").mkdir()
        (tmp_path / "ns_portion" / "child.py").write_text("VALUE = 1\n")
        finder = LegesherMetaPathFinder(language="es")
        with patch.object(sys, "path", [str(tmp_path)]):
            importlib.invalidate_caches()
            assert finder.find_spec("ns_portion", None) is None, tmp_path

    def test_zip_entry_is_not_claimed(self, tmp_path):
        import zipfile

        # Plain source: zipimporter compiles an entry while finding it, so
        # native source in a zip fails there, with or without the hook.
        archive = tmp_path / "bundle.zip"
        with zipfile.ZipFile(archive, "w") as zf:
            zf.writestr("zipped_mod.py", "VALUE = 1\n")
        finder = LegesherMetaPathFinder(language="es")
        with patch.object(sys, "path", [str(archive)]):
            importlib.invalidate_caches()
            assert finder.find_spec("zipped_mod", None) is None, archive


class TestClaimNarrowing:
    """Regression tests for CORE-2205: the hook claims only what it translates.

    The finder claimed every .py on sys.path, the standard library and
    site-packages included, so every such module recompiled from source
    with no bytecode cache: 7 to 20 times the stock import cost. It now
    leaves stock roots to the stock machinery and claims a project file
    only when its first bytes contain one of the pack's native keywords.
    """

    BENCH_TARGETS = (
        "asyncio",
        "unittest",
        "logging.config",
        "email.parser",
        "concurrent.futures",
    )

    def setup_method(self):
        uninstall_import_hook()

    def teardown_method(self):
        uninstall_import_hook()

    @staticmethod
    def _native(language, english="def f():\n    if True:\n        return 1\n"):
        finder = LegesherMetaPathFinder(language=language)
        native = finder.translator.translate_code(english)
        assert native != english, language
        return finder, native

    def test_stdlib_modules_are_not_claimed(self):
        finder = LegesherMetaPathFinder(language="es")
        assert finder.find_spec("json", None) is None
        email_path = importlib.util.find_spec("email").submodule_search_locations
        assert finder.find_spec("email.parser", email_path) is None
        concurrent_path = importlib.util.find_spec(
            "concurrent"
        ).submodule_search_locations
        assert finder.find_spec("concurrent.futures", concurrent_path) is None

    def test_benchmark_targets_load_entirely_through_stock(self):
        """After the CORE-2205 benchmark imports, no module is the hook's."""
        import subprocess

        script = (
            "import importlib, sys\n"
            "from legesher.runtime import install_import_hook\n"
            "from legesher.runtime.import_hook import LegesherLoader\n"
            "install_import_hook('es')\n"
            f"for target in {self.BENCH_TARGETS!r}:\n"
            "    top = target.partition('.')[0]\n"
            "    for name in list(sys.modules):\n"
            "        if name == top or name.startswith(top + '.'):\n"
            "            del sys.modules[name]\n"
            "    importlib.import_module(target)\n"
            "claimed = sorted(n for n, m in list(sys.modules.items())\n"
            "    if isinstance(getattr(getattr(m, '__spec__', None), 'loader', None),\n"
            "                  LegesherLoader))\n"
            "assert claimed == [], claimed\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script], capture_output=True, text=True, timeout=120
        )
        assert result.returncode == 0, result.stderr

    def test_stdlib_submodule_lookup_skips_the_path_finder(self):
        """A lookup confined to the standard library costs no filesystem work."""
        finder = LegesherMetaPathFinder(language="es")
        asyncio_path = importlib.util.find_spec("asyncio").submodule_search_locations
        with patch.object(
            importlib.machinery.PathFinder,
            "find_spec",
            side_effect=AssertionError("PathFinder consulted for a stdlib path"),
        ):
            assert finder.find_spec("asyncio.events", asyncio_path) is None

    @pytest.mark.parametrize("install_dir", ["site-packages", "dist-packages"])
    def test_native_source_in_site_packages_is_not_claimed(self, tmp_path, install_dir):
        """Installed packages ship plain Python and always load through stock."""
        _, native = self._native("es")
        site_dir = tmp_path / "lib" / "python3" / install_dir
        site_dir.mkdir(parents=True)
        (site_dir / "installed_native.py").write_text(native, encoding="utf-8")
        finder = LegesherMetaPathFinder(language="es")
        with patch.object(sys, "path", [str(site_dir)]):
            importlib.invalidate_caches()
            assert finder.find_spec("installed_native", None) is None, site_dir

    def test_native_source_under_a_stock_root_is_not_claimed(self, tmp_path):
        """Anything under the interpreter's prefixes is the stock machinery's."""
        _, native = self._native("es")
        (tmp_path / "under_prefix.py").write_text(native, encoding="utf-8")
        finder = LegesherMetaPathFinder(language="es")
        finder._stock_roots = (os.path.realpath(tmp_path),)
        finder.invalidate_caches()
        with patch.object(sys, "path", [str(tmp_path)]):
            importlib.invalidate_caches()
            assert finder.find_spec("under_prefix", None) is None, tmp_path

    def test_stock_roots_cover_the_library(self):
        from legesher.runtime.import_hook import _stock_roots

        import sysconfig

        roots = _stock_roots()
        for key in ("stdlib", "platstdlib", "purelib", "platlib"):
            real = os.path.realpath(sysconfig.get_paths()[key])
            assert any(real == r or real.startswith(r + os.sep) for r in roots), key

    @pytest.mark.parametrize("layout", ["venv_in_project", "system_prefix"])
    def test_project_under_an_interpreter_prefix_is_claimed(
        self, tmp_path, monkeypatch, layout
    ):
        """A prefix is not a stock root; only its library directories are.

        `python -m venv .` makes the project root the prefix, and a system
        interpreter at /usr puts an application at /usr/src/app under it.
        Native files there must still be translated, while the prefix's
        own `lib` directory stays stock.
        """
        _, native = self._native("es")
        prefix = tmp_path / "prefix"
        project = prefix if layout == "venv_in_project" else prefix / "src" / "app"
        library = prefix / "lib" / "python3" / "vendored"
        project.mkdir(parents=True, exist_ok=True)
        library.mkdir(parents=True)
        (project / "under_prefix_app.py").write_text(native, encoding="utf-8")
        (library / "under_prefix_lib.py").write_text(native, encoding="utf-8")
        for name in ("prefix", "base_prefix", "exec_prefix", "base_exec_prefix"):
            monkeypatch.setattr(sys, name, str(prefix))
        finder = LegesherMetaPathFinder(language="es")

        with patch.object(sys, "path", [str(project), str(library)]):
            importlib.invalidate_caches()
            claimed = finder.find_spec("under_prefix_app", None)
            vendored = finder.find_spec("under_prefix_lib", None)
        assert claimed is not None, project / "under_prefix_app.py"
        assert vendored is None, library / "under_prefix_lib.py"

    def test_english_project_module_is_not_claimed(self, tmp_path):
        """No native keyword as a whole word: the file loads through stock.

        `sitio` and `foo` contain the es forms `si` and `o`, but not as words.
        """
        (tmp_path / "plain_english.py").write_text(
            "import os\n\nsitio = os.getcwd()\nfoo = [sitio]\n"
        )
        finder = LegesherMetaPathFinder(language="es")
        with patch.object(sys, "path", [str(tmp_path)]):
            importlib.invalidate_caches()
            assert finder.find_spec("plain_english", None) is None, tmp_path

    def test_english_pack_claims_nothing(self, tmp_path):
        """Under `en` every keyword form is the English keyword itself."""
        (tmp_path / "en_module.py").write_text("def f():\n    return 1\n")
        finder = LegesherMetaPathFinder(language="en")
        with patch.object(sys, "path", [str(tmp_path)]):
            importlib.invalidate_caches()
            assert finder.find_spec("en_module", None) is None, tmp_path

    @pytest.mark.parametrize("language", ["es", "ar", "hi", "th", "si"])
    def test_native_project_module_is_claimed(self, tmp_path, language):
        """Scripts with combining marks and joiners match as whole words."""
        _, native = self._native(language)
        name = f"native_claim_{language}"
        (tmp_path / f"{name}.py").write_text(native, encoding="utf-8")
        finder = LegesherMetaPathFinder(language=language)
        with patch.object(sys, "path", [str(tmp_path)]):
            importlib.invalidate_caches()
            spec = finder.find_spec(name, None)
        assert spec is not None, tmp_path / f"{name}.py"
        assert isinstance(spec.loader, LegesherLoader)

    def test_claim_scan_decodes_by_the_coding_declaration(self, tmp_path):
        """A cp1251 Russian module is claimed: its keywords are not UTF-8 bytes."""
        finder, native = self._native("ru")
        source = "# -*- coding: cp1251 -*-\n" + native
        module_path = tmp_path / "cp1251_native.py"
        module_path.write_bytes(source.encode("cp1251"))
        with patch.object(sys, "path", [str(tmp_path)]):
            importlib.invalidate_caches()
            spec = finder.find_spec("cp1251_native", None)
        assert spec is not None, module_path

    def test_mixed_stock_and_project_search_path_is_still_searched(self, tmp_path):
        """A namespace package with one installed and one project portion."""
        _, native = self._native("es")
        stock_portion = tmp_path / "lib" / "site-packages" / "nsx"
        project_portion = tmp_path / "project" / "nsx"
        stock_portion.mkdir(parents=True)
        project_portion.mkdir(parents=True)
        (project_portion / "native_child.py").write_text(native, encoding="utf-8")
        finder = LegesherMetaPathFinder(language="es")
        importlib.invalidate_caches()
        spec = finder.find_spec(
            "nsx.native_child", [str(stock_portion), str(project_portion)]
        )
        assert spec is not None, project_portion / "native_child.py"

    def test_invalidate_caches_clears_the_location_memo(self, tmp_path):
        """A path entry's stock verdict is recomputed after invalidate_caches."""
        _, native = self._native("es")
        pkg = tmp_path / "memo_pkg"
        pkg.mkdir()
        (pkg / "child.py").write_text(native, encoding="utf-8")
        finder = LegesherMetaPathFinder(language="es")
        finder._stock_roots = ()
        importlib.invalidate_caches()
        assert finder.find_spec("memo_pkg.child", [str(pkg)]) is not None

        finder._stock_roots = (os.path.realpath(tmp_path),)
        finder.invalidate_caches()
        # With the memo cleared the entry is now stock, so the lookup ends
        # before the path finder is consulted.
        with patch.object(
            importlib.machinery.PathFinder,
            "find_spec",
            side_effect=AssertionError("stale location memo: PathFinder consulted"),
        ):
            assert finder.find_spec("memo_pkg.child", [str(pkg)]) is None, pkg

    def test_keyword_followed_by_a_combining_mark_is_not_a_match(self, tmp_path):
        """`यां` is one identifier: `या` (hi `or`) plus an anusvara.

        The anusvara is a combining mark, which a `\\w` word boundary treats
        as the end of a word; Python treats it as part of the identifier.
        """
        (tmp_path / "hi_identifier.py").write_text("यां = 1\n", encoding="utf-8")
        finder = LegesherMetaPathFinder(language="hi")
        with patch.object(sys, "path", [str(tmp_path)]):
            importlib.invalidate_caches()
            assert finder.find_spec("hi_identifier", None) is None, tmp_path

    def test_keyword_form_that_changes_under_nfkc_is_matched(self, tmp_path):
        """Thai `return` contains SARA AM, which NFKC decomposes.

        The file keeps the pack's own spelling, so the scan must normalize
        the text the same way it normalizes the keyword forms.
        """
        import unicodedata

        finder = LegesherMetaPathFinder(language="th")
        forms = [
            native
            for native, english in finder.reverse_translator.mapper.keyword_map.items()
            if english == "return"
        ]
        assert forms and unicodedata.normalize("NFKC", forms[0]) != forms[0]
        (tmp_path / "th_return.py").write_text(
            f"x = 1\n{forms[0]} x\n", encoding="utf-8"
        )
        with patch.object(sys, "path", [str(tmp_path)]):
            importlib.invalidate_caches()
            assert finder.find_spec("th_return", None) is not None, tmp_path

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "CORE-1539: the claim scan reads a bounded prefix, so a native "
            "file whose first native keyword sits past it loads through "
            "stock untranslated. A per-file language header removes the bound."
        ),
    )
    def test_native_keyword_beyond_the_prefix_bound_is_claimed(self, tmp_path):
        from legesher.runtime.import_hook import _CLAIM_PREFIX_BYTES

        _, native = self._native("es")
        padding = ("#" * 79 + "\n") * (_CLAIM_PREFIX_BYTES // 80 + 1)
        module_path = tmp_path / "late_native.py"
        module_path.write_text(padding + native, encoding="utf-8")
        finder = LegesherMetaPathFinder(language="es")
        with patch.object(sys, "path", [str(tmp_path)]):
            importlib.invalidate_caches()
            assert finder.find_spec("late_native", None) is not None, module_path


class TestBytecodeCache:
    """Regression tests for CORE-2205: files the hook translates are cached.

    Every claimed file recompiled from source on every run. The loader now
    caches compiled code under __pycache__ with a Legesher-specific name,
    keyed by a hash of the native source bytes and everything that decides
    the translation, never by modification time alone.
    """

    ENGLISH = "def value():\n    if True:\n        return 41\n    return 0\n"

    @pytest.fixture(autouse=True)
    def _isolated(self, monkeypatch):
        uninstall_import_hook()
        monkeypatch.setattr(sys, "dont_write_bytecode", False)
        monkeypatch.setattr(sys, "pycache_prefix", None)
        yield
        uninstall_import_hook()

    def _write(self, tmp_path, name, english=None):
        finder = LegesherMetaPathFinder(language="es")
        native = finder.translator.translate_code(english or self.ENGLISH)
        assert native.startswith("definir"), native
        path = tmp_path / f"{name}.py"
        path.write_text(native, encoding="utf-8")
        return path

    @staticmethod
    def _paths(module_path, language="es"):
        stock = importlib.util.cache_from_source(str(module_path))
        return stock, stock[: -len(".pyc")] + f".legesher-{language}.pyc"

    @staticmethod
    def _import(tmp_path, name, language="es"):
        """Import under a freshly installed hook; return (module, stats)."""
        from legesher.runtime.import_hook import get_bytecode_cache_stats

        sys.path.insert(0, str(tmp_path))
        importlib.invalidate_caches()
        try:
            install_import_hook(language=language)
            module = importlib.import_module(name)
            assert isinstance(module.__spec__.loader, LegesherLoader), module
            return module, get_bytecode_cache_stats()
        finally:
            uninstall_import_hook()
            sys.path.remove(str(tmp_path))
            sys.modules.pop(name, None)

    def test_first_import_writes_only_the_tagged_file(self, tmp_path):
        module_path = self._write(tmp_path, "cache_first")
        stock, tagged = self._paths(module_path)

        module, stats = self._import(tmp_path, "cache_first")
        assert module.value() == 41
        assert module.__cached__ == tagged, module.__cached__
        assert stats == {"hits": 0, "misses": 1, "writes": 1, "write_errors": 0}
        assert os.listdir(os.path.dirname(tagged)) == [os.path.basename(tagged)]
        assert not os.path.exists(stock), stock

    def test_second_import_hits_without_translating(self, tmp_path):
        from legesher_core import TokenTranslator

        self._write(tmp_path, "cache_hit")
        self._import(tmp_path, "cache_hit")

        with patch.object(
            TokenTranslator,
            "translate_code",
            side_effect=AssertionError("translated on a cache hit"),
        ):
            module, stats = self._import(tmp_path, "cache_hit")
        assert module.value() == 41
        assert stats == {"hits": 1, "misses": 0, "writes": 0, "write_errors": 0}

    def test_hit_registers_the_source_mapping(self, tmp_path):
        """Localized tracebacks still map lines for a module loaded from cache."""
        module_path = self._write(tmp_path, "cache_mapping")
        self._import(tmp_path, "cache_mapping")

        mapper = MagicMock()
        with patch(
            "legesher.runtime.import_hook.get_source_mapper", return_value=mapper
        ):
            _, stats = self._import(tmp_path, "cache_mapping")
        assert stats["hits"] == 1
        mapper.register_mapping.assert_called_once()
        kwargs = mapper.register_mapping.call_args.kwargs
        assert kwargs["filename"] == str(module_path)
        assert kwargs["english_source"] == self.ENGLISH
        assert kwargs["native_source"] == module_path.read_text(encoding="utf-8")

    def test_hit_on_a_claimed_english_file_registers_nothing(self, tmp_path):
        """English sharing a pack word is claimed, cached, and never mapped."""
        (tmp_path / "cache_english.py").write_text("con = 1\n")
        module, first = self._import(tmp_path, "cache_english")
        assert module.con == 1 and first["writes"] == 1, first

        mapper = MagicMock()
        with patch(
            "legesher.runtime.import_hook.get_source_mapper", return_value=mapper
        ):
            module, second = self._import(tmp_path, "cache_english")
        assert module.con == 1
        assert second["hits"] == 1, second
        mapper.register_mapping.assert_not_called()

    def test_record_honours_pycache_prefix(self, tmp_path, monkeypatch):
        """With sys.pycache_prefix set, the record lives under the prefix."""
        prefix = tmp_path / "pyc_prefix"
        project = tmp_path / "project"
        project.mkdir()
        module_path = self._write(project, "cache_prefixed")
        monkeypatch.setattr(sys, "pycache_prefix", str(prefix))
        stock, tagged = self._paths(module_path)
        assert tagged.startswith(str(prefix)), tagged

        module, stats = self._import(project, "cache_prefixed")
        assert module.value() == 41 and stats["writes"] == 1, stats
        assert os.path.exists(tagged), tagged
        assert not os.path.exists(stock), stock
        assert not (project / "__pycache__").exists(), project

    def test_record_is_no_more_readable_than_its_source(self, tmp_path, monkeypatch):
        """The record holds the translated source, so it keeps the source's mode."""
        if os.name != "posix":
            pytest.skip("POSIX permission bits")
        module_path = self._write(tmp_path, "cache_private")
        os.chmod(module_path, 0o600)
        old_umask = os.umask(0o022)
        try:
            self._import(tmp_path, "cache_private")
        finally:
            os.umask(old_umask)
        _, tagged = self._paths(module_path)
        assert os.stat(tagged).st_mode & 0o777 == 0o600, oct(os.stat(tagged).st_mode)

    @pytest.mark.parametrize(
        "part",
        ["language", "maps", "python_version", "optimize", "magic", "engine"],
    )
    def test_every_salt_part_changes_the_key(self, monkeypatch, part):
        """Each input that decides the compiled code is part of the key."""
        import types as pytypes

        from legesher.runtime import import_hook

        raw = b"definir f():\n    retornar 1\n"
        # Hold the pack distribution version fixed, so a changed language
        # cannot differ only through the version lookup it drives.
        monkeypatch.setattr(importlib.metadata, "version", lambda dist: "1.0.0")
        baseline = LegesherMetaPathFinder(language="es")
        changed = LegesherMetaPathFinder(language="es")
        if part == "language":
            changed.language = "xx"
        elif part == "maps":
            mapper = changed.reverse_translator.mapper
            mapper.keyword_map = dict(mapper.keyword_map, extra_word="pass")
        elif part == "python_version":
            changed.reverse_translator.python_version = "3.0"
        elif part == "optimize":
            monkeypatch.setattr(sys, "flags", pytypes.SimpleNamespace(optimize=2))
        elif part == "magic":
            monkeypatch.setattr(importlib.util, "MAGIC_NUMBER", b"\x00\x00\r\n")
        else:
            monkeypatch.setattr(import_hook, "_ENGINE_DIGEST", "changed-engine")
        changed._bytecode_salt = changed._compute_bytecode_salt()
        assert changed._bytecode_key(raw) != baseline._bytecode_key(raw), part

    def test_same_size_and_mtime_with_new_bytes_misses(self, tmp_path):
        """The key is the source content, never the modification time."""
        module_path = self._write(tmp_path, "cache_mtime")
        self._import(tmp_path, "cache_mtime")
        mtime_ns = module_path.stat().st_mtime_ns

        changed = module_path.read_text(encoding="utf-8").replace("41", "42")
        module_path.write_text(changed, encoding="utf-8")
        os.utime(module_path, ns=(mtime_ns, mtime_ns))

        module, stats = self._import(tmp_path, "cache_mtime")
        assert module.value() == 42, module_path
        assert stats["hits"] == 0 and stats["misses"] == 1

    @pytest.mark.parametrize("change", ["engine", "cli", "pack"])
    def test_version_change_misses(self, tmp_path, monkeypatch, change):
        import legesher
        import legesher_core

        self._write(tmp_path, f"cache_version_{change}")
        self._import(tmp_path, f"cache_version_{change}")

        if change == "engine":
            monkeypatch.setattr(legesher_core, "__version__", "999.0.0")
        elif change == "cli":
            monkeypatch.setattr(legesher, "__version__", "999.0.0")
        else:
            real_version = importlib.metadata.version
            monkeypatch.setattr(
                importlib.metadata,
                "version",
                lambda dist: (
                    "999.0.0"
                    if dist == "legesher-i18n-python-es"
                    else real_version(dist)
                ),
            )
        _, stats = self._import(tmp_path, f"cache_version_{change}")
        assert stats["hits"] == 0 and stats["misses"] == 1, change

    def test_record_for_another_language_is_rejected(self, tmp_path):
        """The language is part of the key, not only of the file name."""
        module_path = self._write(tmp_path, "cache_language")
        self._import(tmp_path, "cache_language")
        _, es_record = self._paths(module_path, "es")
        _, ar_record = self._paths(module_path, "ar")
        with open(es_record, "rb") as src, open(ar_record, "wb") as dst:
            dst.write(src.read())

        finder = LegesherMetaPathFinder(language="ar")
        loader = LegesherLoader("cache_language", str(module_path), finder)
        key = finder._bytecode_key(module_path.read_bytes())
        assert loader._read_bytecode(ar_record, key) is None, ar_record

    @pytest.mark.parametrize(
        "damage", ["truncated", "garbage", "foreign_key", "not_code"]
    )
    def test_damaged_record_is_ignored_and_rewritten(self, tmp_path, damage):
        module_path = self._write(tmp_path, f"cache_damage_{damage}")
        self._import(tmp_path, f"cache_damage_{damage}")
        _, tagged = self._paths(module_path)
        data = open(tagged, "rb").read()
        if damage == "truncated":
            data = data[: len(data) // 2]
        elif damage == "garbage":
            data = data[:37] + b"\x00not marshal data"
        elif damage == "foreign_key":
            data = data[:5] + bytes(32) + data[37:]
        else:
            import marshal

            data = data[:37] + marshal.dumps((None, 42))
        with open(tagged, "wb") as record:
            record.write(data)

        module, stats = self._import(tmp_path, f"cache_damage_{damage}")
        assert module.value() == 41, tagged
        assert stats["hits"] == 0 and stats["writes"] == 1, stats

    def test_unwritable_pycache_still_imports(self, tmp_path):
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            pytest.skip("root ignores directory permissions")
        module_path = self._write(tmp_path, "cache_readonly")
        stock, _ = self._paths(module_path)
        pycache = os.path.dirname(stock)
        os.mkdir(pycache)
        os.chmod(pycache, 0o555)
        try:
            module, stats = self._import(tmp_path, "cache_readonly")
        finally:
            os.chmod(pycache, 0o755)
        assert module.value() == 41
        assert stats["writes"] == 0 and stats["write_errors"] == 1, stats
        assert os.listdir(pycache) == [], pycache

    def test_dont_write_bytecode_writes_nothing(self, tmp_path, monkeypatch):
        module_path = self._write(tmp_path, "cache_nowrite")
        monkeypatch.setattr(sys, "dont_write_bytecode", True)
        module, stats = self._import(tmp_path, "cache_nowrite")
        assert module.value() == 41
        assert stats["writes"] == 0
        assert not (tmp_path / "__pycache__").exists(), module_path

    def test_failed_replace_leaves_no_temp_and_stock_bytecode_alone(
        self, tmp_path, monkeypatch
    ):
        """Only the hook's own temporary file is ever removed."""
        import py_compile

        module_path = self._write(tmp_path, "cache_replace")
        stock, tagged = self._paths(module_path)
        # A stock .pyc from some earlier stock compile of this path.
        other = tmp_path / "stock_source.py"
        other.write_text("VALUE = 1\n")
        py_compile.compile(str(other), cfile=stock, doraise=True)
        stock_bytes = open(stock, "rb").read()

        def failing_replace(src, dst):
            raise OSError("simulated replace failure")

        monkeypatch.setattr(os, "replace", failing_replace)
        module, stats = self._import(tmp_path, "cache_replace")
        assert module.value() == 41
        assert stats["write_errors"] == 1, stats
        pycache = os.path.dirname(stock)
        assert sorted(os.listdir(pycache)) == [os.path.basename(stock)], pycache
        assert open(stock, "rb").read() == stock_bytes, stock
        assert not os.path.exists(tagged), tagged

    def test_stock_python_ignores_the_cached_record(self, tmp_path):
        """Stock Python never runs bytecode compiled from translated source.

        With the Legesher record in place, a fresh interpreter without the
        hook still compiles the native source itself, and fails on it.
        """
        import subprocess

        module_path = self._write(tmp_path, "cache_stock_blind")
        self._import(tmp_path, "cache_stock_blind")
        _, tagged = self._paths(module_path)
        assert os.path.exists(tagged), tagged

        result = subprocess.run(
            [sys.executable, "-c", "import cache_stock_blind"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode != 0, result.stdout
        assert "SyntaxError" in result.stderr, result.stderr

    def test_moved_project_reports_the_new_filename(self, tmp_path):
        """A record copied with its project reports where the code now lives."""
        import shutil

        first = tmp_path / "first"
        first.mkdir()
        self._write(first, "cache_moved")
        self._import(first, "cache_moved")
        moved = tmp_path / "moved"
        shutil.copytree(first, moved)

        module, stats = self._import(moved, "cache_moved")
        assert stats["hits"] == 1, stats
        assert module.value.__code__.co_filename == str(moved / "cache_moved.py")


class TestSymlinkedPackage:
    """Regression test for CORE-2206: the traversal guard is gone.

    The guard resolved `<entry>/<name>` and required it to stay inside the
    entry, so a symlinked package directory was silently skipped and its
    native source reached the stock loader untranslated. Module names are
    gated by isidentifier() on every dotted component, which already
    rejects every traversal shape.
    """

    def setup_method(self):
        uninstall_import_hook()

    def teardown_method(self):
        uninstall_import_hook()

    def test_symlinked_native_package_is_claimed_and_translated(self, tmp_path):
        finder = LegesherMetaPathFinder(language="es")
        native = finder.translator.translate_code(
            "def value():\n    if True:\n        return 7\n    return 0\n"
        )
        real_pkg = tmp_path / "elsewhere" / "real_pkg"
        real_pkg.mkdir(parents=True)
        (real_pkg / "__init__.py").write_text(native, encoding="utf-8")
        entry = tmp_path / "entry"
        entry.mkdir()
        (entry / "linked_pkg").symlink_to(real_pkg, target_is_directory=True)

        sys.path.insert(0, str(entry))
        importlib.invalidate_caches()
        try:
            install_import_hook(language="es")
            pkg = importlib.import_module("linked_pkg")
            assert isinstance(pkg.__spec__.loader, LegesherLoader), entry / "linked_pkg"
            assert pkg.value() == 7
        finally:
            uninstall_import_hook()
            sys.path.remove(str(entry))
            sys.modules.pop("linked_pkg", None)

    @pytest.mark.parametrize(
        "name",
        [
            "../malicious",
            "evil..module",
            "hack/../../etc/passwd",
            "nul\x00byte",
            f"sep{os.sep}name",
            "trailing.",
            ".leading",
            "",
        ],
    )
    def test_traversal_shaped_names_are_rejected(self, tmp_path, name):
        """Every traversal shape fails the identifier gate before any lookup.

        With a parent path supplied, the dotted-name-without-path decline
        does not apply, so the identifier gate is the only thing standing
        between the name and a filesystem lookup.
        """
        finder = LegesherMetaPathFinder(language="es")
        with patch.object(
            importlib.machinery.PathFinder,
            "find_spec",
            side_effect=AssertionError(f"lookup reached for {name!r}"),
        ):
            assert finder.find_spec(name, None) is None
            assert finder.find_spec(name, [str(tmp_path)]) is None


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
