"""Import-guard tests: the token path must work without tree-sitter C extensions.

``legesher_core`` re-exports :class:`TreeSitterTranslator` and
:class:`LLMTranslator`, whose implementation modules import the ``tree_sitter``
and ``tree_sitter_python`` C extensions. Those imports must stay lazy (PEP 562)
so that ``import legesher_core`` — and the pure-stdlib ``TokenTranslator``
path — works in environments without the C extensions installed (minimal
installs, browser Python runtimes).

The C extensions ARE installed in the development environment, so each test
spawns a subprocess whose first act is to install a meta-path import blocker
for ``tree_sitter`` / ``tree_sitter_python``, simulating their absence.
"""

import subprocess
import sys
import textwrap

import pytest

#: Prelude installed before any legesher import in the subprocess: a meta-path
#: finder that makes the tree-sitter C extensions unimportable. Placed first in
#: ``sys.meta_path`` so it wins over every real finder. It must NOT block the
#: ``legesher_core.tree_sitter`` subpackage — only the top-level distributions.
BLOCKER_PRELUDE = textwrap.dedent("""
    import sys

    class _TreeSitterBlocker:
        _blocked = ("tree_sitter", "tree_sitter_python")

        def find_spec(self, fullname, path=None, target=None):
            if fullname.partition(".")[0] in self._blocked:
                raise ModuleNotFoundError(
                    f"No module named {fullname!r} (blocked by test)",
                    name=fullname,
                )
            return None

    sys.meta_path.insert(0, _TreeSitterBlocker())
    """)


def run_without_tree_sitter(payload: str) -> subprocess.CompletedProcess:
    """Run ``payload`` in a fresh interpreter with tree-sitter blocked."""
    script = BLOCKER_PRELUDE + textwrap.dedent(payload)
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=120,
    )


class TestImportWithoutTreeSitter:
    """The pure-stdlib token path with the C extensions unavailable."""

    def test_blocker_blocks_tree_sitter(self):
        """Sanity: the meta-path blocker really makes tree_sitter unimportable."""
        result = run_without_tree_sitter("""
            try:
                import tree_sitter
            except ModuleNotFoundError:
                print("blocked")
            else:
                raise SystemExit("tree_sitter imported despite blocker")
            """)
        assert result.returncode == 0, result.stderr
        assert "blocked" in result.stdout

    def test_token_path_translates_without_tree_sitter(self):
        """import legesher_core + TokenTranslator work end-to-end without C extensions."""
        result = run_without_tree_sitter("""
            import legesher_core
            from legesher_core import TokenTranslator

            translator = TokenTranslator.from_language_pack("es")
            print(
                translator.translate_code(
                    "def f():\\n    pass\\n", source_lang="en", target_lang="es"
                )
            )
            """)
        assert result.returncode == 0, (
            f"token path failed without tree-sitter:\n{result.stderr}"
        )
        assert "definir" in result.stdout, result.stdout

    def test_translate_code_with_map_raises_clear_error(self):
        """CORE-1662 (f): plain translate_code works without the C
        extensions; the opt-in translate_code_with_map raises the friendly
        extra-naming ImportError instead of a raw ModuleNotFoundError."""
        result = run_without_tree_sitter("""
            from legesher_core import TokenTranslator

            translator = TokenTranslator({"def": "definir"}, {"print": "imprimir"})
            source = "def f():\\n    pass\\n"
            assert "definir" in translator.translate_code(source, "en", "es")
            try:
                translator.translate_code_with_map(source, "en", "es")
            except ImportError as exc:
                assert "legesher-core[treesitter]" in str(exc), str(exc)
                print("clear map error")
            else:
                raise SystemExit("expected ImportError from translate_code_with_map")
            """)
        assert result.returncode == 0, result.stderr
        assert "clear map error" in result.stdout

    @pytest.mark.parametrize("export", ["TreeSitterTranslator", "LLMTranslator"])
    def test_tree_sitter_exports_raise_clear_error(self, export):
        """Accessing tree-sitter-backed exports raises an error naming the extra."""
        result = run_without_tree_sitter(f"""
            import legesher_core

            try:
                getattr(legesher_core, "{export}")
            except ImportError as exc:
                message = str(exc)
                assert "treesitter" in message, message
                assert "legesher-core[treesitter]" in message, message
                print("clear error: " + message)
            else:
                raise SystemExit("expected ImportError for {export}")
            """)
        assert result.returncode == 0, result.stderr
        assert "clear error:" in result.stdout

    def test_factory_tree_sitter_backend_raises_clear_error(self):
        """create_translator(use_tree_sitter=True) also names the extra."""
        result = run_without_tree_sitter("""
            from legesher_core import create_translator

            try:
                create_translator("python", {"def": "definir"}, {}, use_tree_sitter=True)
            except ImportError as exc:
                assert "legesher-core[treesitter]" in str(exc), str(exc)
                print("clear factory error")
            else:
                raise SystemExit("expected ImportError from factory")
            """)
        assert result.returncode == 0, result.stderr
        assert "clear factory error" in result.stdout

    def test_unknown_attribute_still_raises_attribute_error(self):
        """PEP 562 __getattr__ must not swallow genuinely unknown attributes."""
        result = run_without_tree_sitter("""
            import legesher_core

            try:
                legesher_core.DoesNotExist
            except AttributeError:
                print("attribute error")
            """)
        assert result.returncode == 0, result.stderr
        assert "attribute error" in result.stdout


class TestLazyExportsWithTreeSitterInstalled:
    """With the C extensions available, the lazy exports resolve normally."""

    def test_dir_still_lists_lazy_exports(self):
        from legesher_core import __all__ as public_names

        import legesher_core

        listed = dir(legesher_core)
        assert "TreeSitterTranslator" in listed
        assert "LLMTranslator" in listed
        assert "TreeSitterTranslator" in public_names
        assert "LLMTranslator" in public_names

    def test_lazy_exports_resolve_to_real_classes(self):
        from legesher_core import LLMTranslator, TreeSitterTranslator
        from legesher_core.tree_sitter.llm_translator import (
            LLMTranslator as DirectLLMTranslator,
        )
        from legesher_core.tree_sitter.translator import (
            TreeSitterTranslator as DirectTreeSitterTranslator,
        )

        assert TreeSitterTranslator is DirectTreeSitterTranslator
        assert LLMTranslator is DirectLLMTranslator

    def test_subpackage_dir_still_lists_lazy_exports(self):
        from legesher_core import tree_sitter as tree_sitter_pkg

        listed = dir(tree_sitter_pkg)
        for name in tree_sitter_pkg.__all__:
            assert name in listed, name
