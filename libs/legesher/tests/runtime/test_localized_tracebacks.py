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
