"""End-to-end localized tracebacks for translated scripts (CORE-1679).

Mirrors what `legesher run` does — translate native source, register the
source mapping, compile the TRANSLATED code under the NATIVE filename — and
asserts the caret contract on the rendered traceback: carets are either
correctly positioned or absent, never misplaced. Since caret columns are
computed by the interpreter against the translated text, the v1 posture for
mapped frames is: show the native line, remap the line number, DROP the
caret/anchor lines (no caret beats a wrong caret).
"""

from __future__ import annotations

import sys

import pytest
from legesher_core import TokenTranslator
from legesher_runtime import TracebackRenderer

from legesher.runtime.source_mapper import get_source_mapper, reset_source_mapper

NATIVE_RUNTIME = "definir dividir(a, b):\n    devolver a / b\n\ndividir(1, 0)\n"
NATIVE_SYNTAX = "devolver (1, 2\n"


#: Structural frame text ("Archivo", "línea", "en") and localized message
#: bodies come from the ``traceback.*`` / ``<ExceptionType>.*`` catalog rows,
#: which live in ``translations.db``. That database is an untracked working
#: copy since CORE-1794 (see libs/i18n/CLAUDE.md, "Durable home & sync
#: ritual"), so a fresh clone — CI included — does not have it, and
#: ``TracebackRenderer`` degrades by design to an empty catalog and English
#: passthrough. Exception *names* come from the in-repo language pack, so they
#: localize either way; only catalog-backed assertions need this guard. Same
#: pattern as libs/i18n/tests/test_messages_catalog.py (CORE-1899).
def _catalog_available() -> bool:
    """Whether the ``traceback.*`` rules this test asserts on can be loaded.

    Deliberately checks the catalog's CONTENT, not whether a database file
    exists. `TranslationDatabase` creates an empty database when the path is
    missing, and CI runs the i18n suite in the same job before this one — so
    by the time these tests run, an empty `translations.db` is sitting at the
    default path. A file-existence guard reads that as "catalog available",
    runs anyway, and fails on a catalog with no rows in it.
    """
    try:
        from legesher_i18n.messages import load_catalog

        version = f"{sys.version_info[0]}.{sys.version_info[1]}"
        return any(r.key.startswith("traceback.") for r in load_catalog("es", version))
    except Exception:  # noqa: BLE001 - no i18n package, no catalog either
        return False


requires_catalog = pytest.mark.skipif(
    not _catalog_available(),
    reason=(
        "translations.db is an untracked working copy (CORE-1794); copy it in "
        "from the private data home — libs/i18n/CLAUDE.md, 'Durable home & "
        "sync ritual'"
    ),
)


@pytest.fixture(autouse=True)
def clean_mapper():
    reset_source_mapper()
    yield
    reset_source_mapper()


def run_translated(tmp_path, native_code: str):
    """Translate, register the mapping, compile under the native filename."""
    path = tmp_path / "programa.py"
    path.write_text(native_code, encoding="utf-8")
    en_to_native = TokenTranslator.from_language_pack("es")
    translated = en_to_native.reverse().translate_code(native_code)
    mapper = get_source_mapper()
    mapper.register_mapping(
        filename=str(path), native_source=native_code, english_source=translated
    )
    try:
        exec(compile(translated, str(path), "exec"), {"__name__": "__main__"})  # noqa: S102
    except BaseException:
        return sys.exc_info(), str(path), mapper
    raise AssertionError("script did not raise")


def caret_lines(text: str) -> list[str]:
    return [
        line
        for line in text.splitlines()
        if line.strip() and set(line.strip()) <= {"~", "^"}
    ]


def mapped_region(rendered: str, path: str) -> str:
    """The rendered text from the first frame of the mapped file onward."""
    lines = rendered.splitlines()
    start = next(i for i, line in enumerate(lines) if path in line)
    return "\n".join(lines[start:])


class TestRuntimeFrames:
    def test_native_lines_shown_and_no_misplaced_carets(self, tmp_path):
        exc_info, path, mapper = run_translated(tmp_path, NATIVE_RUNTIME)
        renderer = TracebackRenderer("es", source_map=mapper)
        rendered = renderer.render(*exc_info)
        region = mapped_region(rendered, path)
        # Native tokens are what the user wrote — and what must be echoed.
        assert "devolver a / b" in region
        assert "return a / b" not in region
        # Caret columns were computed against the translated text
        # ("    return a / b"); against "    devolver a / b" they would sit
        # 2-3 columns off. The contract: correctly positioned or absent.
        assert caret_lines(region) == []

    @requires_catalog
    def test_frame_structure_and_message_are_localized(self, tmp_path):
        """The catalog-backed half of the contract.

        Split from the native-echo assertions above (CORE-1899): those hold
        with or without the catalog, and folding both into one test meant the
        whole case failed wherever ``translations.db`` is absent — which is
        every CI run — masking a green native-echo path behind a red test.
        """
        exc_info, path, mapper = run_translated(tmp_path, NATIVE_RUNTIME)
        renderer = TracebackRenderer("es", source_map=mapper)
        region = mapped_region(renderer.render(*exc_info), path)
        # Structure + message are localized end to end.
        assert 'Archivo "' + path + '", línea 2, en dividir' in region
        assert "errordedivisiónporcero: división por cero" in region

    def test_unmapped_harness_frames_keep_their_carets(self, tmp_path):
        # The contract is scoped: only MAPPED frames lose carets. This test
        # file's own exec frame is unmapped and keeps CPython's output.
        exc_info, path, mapper = run_translated(tmp_path, NATIVE_RUNTIME)
        renderer = TracebackRenderer("es", source_map=mapper)
        rendered = renderer.render(*exc_info)
        if sys.version_info >= (3, 11):
            before_mapped = rendered.split(path)[0]
            assert caret_lines(before_mapped)  # harness anchors survive


class TestSyntaxErrorFrames:
    def test_syntaxerror_text_is_native_and_caret_absent(self, tmp_path):
        # SyntaxError.text comes from the exception object — i.e. the
        # TRANSLATED line — and SyntaxError.offset points into it. Both are
        # remapped: native text echoed, caret dropped.
        exc_info, path, mapper = run_translated(tmp_path, NATIVE_SYNTAX)
        assert exc_info[0] is SyntaxError
        renderer = TracebackRenderer("es", source_map=mapper)
        rendered = renderer.render(*exc_info)
        region = mapped_region(rendered, path)
        assert "devolver (1, 2" in region  # native, not "return (1, 2"
        assert "return (1, 2" not in region
        assert caret_lines(region) == []
        assert "errordesintaxis:" in region
