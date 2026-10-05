"""TracebackRenderer unit behavior (CORE-1679)."""

from __future__ import annotations

import sys
import traceback

import pytest

from legesher_runtime import TracebackRenderer


@pytest.fixture(scope="module")
def es() -> TracebackRenderer:
    return TracebackRenderer("es")


class TestStructuralLines:
    def test_header_is_localized(self, es):
        out = es.render_text("Traceback (most recent call last):\n")
        assert out == "Rastreo (llamada más reciente al final):\n"

    def test_frame_line_keeps_values_and_indent(self, es):
        out = es.render_text('  File "/tmp/x.py", line 3, in funcion\n')
        assert out == '  Archivo "/tmp/x.py", línea 3, en funcion\n'

    def test_syntaxerror_frame_without_scope(self, es):
        out = es.render_text('  File "/tmp/x.py", line 3\n')
        assert out == '  Archivo "/tmp/x.py", línea 3\n'

    def test_cause_and_context_sentences(self, es):
        cause = "The above exception was the direct cause of the following exception:\n"
        context = "During handling of the above exception, another exception occurred:\n"
        assert "causa directa" in es.render_text(cause)
        assert "ocurrió otra excepción" in es.render_text(context)

    def test_source_and_caret_lines_pass_through_verbatim(self, es):
        block = "    return a / b\n           ~~^~~\n"
        assert es.render_text(block) == block


class TestExceptionLine:
    def test_type_and_message_localized(self, es):
        out = es.render_text("ZeroDivisionError: division by zero\n")
        assert out == "errordedivisiónporcero: división por cero\n"

    def test_slot_values_survive_substitution(self, es):
        out = es.render_text("NameError: name 'contador' is not defined\n")
        assert out == "Errordenombre: el nombre 'contador' no está definido\n"

    def test_unmatched_message_passes_through_untranslated(self, es):
        out = es.render_text("ValueError: a completely custom message\n")
        assert out == "errordevalor: a completely custom message\n"

    def test_unknown_type_line_passes_through(self, es):
        line = "SomeCustomError: whatever happened\n"
        assert es.render_text(line) == line

    def test_bare_type_line_for_empty_message(self, es):
        assert es.render_text("KeyboardInterrupt\n") == "interrupcióndelteclado\n"

    def test_indented_type_like_source_line_is_untouched(self, es):
        # A raise statement echoed as a SOURCE line is indented — it must not
        # be mistaken for the final exception line.
        line = '    raise ValueError("division by zero")\n'
        assert es.render_text(line) == line

    def test_english_renderer_keeps_pascal_case(self):
        en = TracebackRenderer("en")
        line = "ZeroDivisionError: division by zero\n"
        assert en.render_text(line) == line

    def test_keyerror_catch_all_fires_only_for_keyerror(self, es):
        # The catalog's KeyError.key rule matches ANY text; the renderer's
        # type scoping (key_prefix) confines it to KeyError lines.
        assert es.render_text("KeyError: 'edad'\n") == "errordeclave: 'edad'\n"
        # An OSError message no template knows passes through UNCHANGED —
        # it must not be swallowed by the KeyError catch-all.
        line = "OSError: something the catalog never templated\n"
        out = es.render_text(line)
        assert out.endswith(": something the catalog never templated\n")


class TestVersionTiering:
    def test_unboundlocalerror_wording_follows_python_version(self):
        old = TracebackRenderer("es", "3.10")
        new = TracebackRenderer("es", "3.11")
        old_msg = "UnboundLocalError: local variable 'x' referenced before assignment\n"
        new_msg = (
            "UnboundLocalError: cannot access local variable 'x' "
            "where it is not associated with a value\n"
        )
        assert "referenciada antes" in old.render_text(old_msg)
        assert "no tiene un valor asociado" in new.render_text(new_msg)
        # And the 3.10 renderer passes the 3.11 wording through untranslated.
        assert "cannot access local variable" in old.render_text(new_msg)


class FakeSourceMapper:
    """Duck-typed stand-in for legesher.runtime.source_mapper (1:1 lines)."""

    def __init__(self, filename: str, native_source: str):
        self.filename = filename
        self.native_lines = native_source.splitlines()

    def has_mapping(self, filename: str) -> bool:
        return filename == self.filename

    def get_native_line(self, filename: str, english_line: int) -> int | None:
        return english_line if filename == self.filename else None

    def get_native_source_line(self, filename: str, line_no: int) -> str | None:
        if filename == self.filename and 0 < line_no <= len(self.native_lines):
            return self.native_lines[line_no - 1]
        return None


class TestMappedFrames:
    """Frames compiled from translated source (the `legesher run` path)."""

    NATIVE = "definir dividir(a, b):\n    devolver a / b\n\ndividir(1, 0)\n"

    def rendered(self, formatted: str) -> str:
        mapper = FakeSourceMapper("/tmp/nativo.py", self.NATIVE)
        renderer = TracebackRenderer("es", source_map=mapper)
        return renderer.render_text(formatted)

    def test_caret_lines_for_mapped_frames_are_dropped(self):
        formatted = (
            "Traceback (most recent call last):\n"
            '  File "/tmp/nativo.py", line 2, in dividir\n'
            "    return a / b\n"
            "           ~~^~~\n"
            "ZeroDivisionError: division by zero\n"
        )
        out = self.rendered(formatted)
        assert "~" not in out and "^" not in out  # no caret beats a wrong caret

    def test_source_echo_is_replaced_with_native_line(self):
        formatted = '  File "/tmp/nativo.py", line 2, in dividir\n    return a / b\n'
        out = self.rendered(formatted)
        assert "    devolver a / b\n" in out
        assert "return a / b" not in out

    def test_syntaxerror_text_and_caret_from_mapped_file(self):
        # CPython echoes SyntaxError.text from the exception object — i.e.
        # the TRANSLATED line — with a caret computed against it.
        formatted = (
            '  File "/tmp/nativo.py", line 1\n'
            "    definir dividir(a, b):\n"
            "            ^^^^^^^\n"
            "SyntaxError: invalid syntax\n"
        )
        out = self.rendered(formatted)
        assert "    definir dividir(a, b):\n" in out  # native text shown
        assert "^" not in out
        assert "errordesintaxis: sintaxis inválida" in out

    def test_unmapped_frames_keep_carets_byte_identical(self):
        formatted = '  File "/tmp/otro.py", line 2, in f\n    return a / b\n           ~~^~~\n'
        out = self.rendered(formatted)
        assert "           ~~^~~\n" in out
        assert "    return a / b\n" in out

    def test_broken_mapper_degrades_to_unmapped(self):
        class BrokenMapper:
            def has_mapping(self, filename):
                raise RuntimeError("mapper bug")

        renderer = TracebackRenderer("es", source_map=BrokenMapper())
        formatted = '  File "/tmp/x.py", line 2, in f\n    return a / b\n           ~~^~~\n'
        out = renderer.render_text(formatted)
        assert "~~^~~" in out  # treated as unmapped, never raises


class ShiftedSourceMapper(FakeSourceMapper):
    """Mapper where translated line N maps to native line N - 3.

    The MVP mapper is 1:1, but the renderer's mapper protocol allows shifts
    (a translation that folds or expands lines). The CORE-1777 repro is a
    header naming translated line 12 above the source text of native line 9.
    """

    SHIFT = 3

    def get_native_line(self, filename: str, english_line: int) -> int | None:
        return english_line - self.SHIFT if filename == self.filename else None


class TestFallbackFrameRemap:
    """Empty-catalog fallback frames still remap line numbers (CORE-1777).

    With a stale or missing translations database, ``load_catalog`` degrades
    to an empty catalog and ``_render_frame`` falls back to re-emitting the
    header. That fallback used to keep the TRANSLATED-source line number
    while ``render_text`` had already swapped the echoed source below it for
    the NATIVE line at the REMAPPED number.
    """

    #: Native line 9 is the line the ticket's repro echoes.
    NATIVE = "\n" * 8 + "    devolver a / b\n"

    def renderer(self, tmp_path, mapper) -> TracebackRenderer:
        # A missing database is the stale-DB degraded mode: empty catalog,
        # no structural rules, fallback path guaranteed — no requires_catalog
        # guard needed because the test DEPENDS on the catalog being absent.
        return TracebackRenderer("es", db_path=tmp_path / "missing.db", source_map=mapper)

    def test_fallback_header_shows_the_remapped_line_number(self, tmp_path):
        mapper = ShiftedSourceMapper("/tmp/programa.py", self.NATIVE)
        renderer = self.renderer(tmp_path, mapper)
        formatted = '  File "/tmp/programa.py", line 12, in dividir\n    return a / b\n'
        out = renderer.render_text(formatted)
        assert '  File "/tmp/programa.py", line 9, in dividir\n' in out
        assert "line 12" not in out
        # The header now matches the echoed source: native line 9.
        assert "    devolver a / b\n" in out

    def test_fallback_syntaxerror_header_is_remapped_too(self, tmp_path):
        # The no-scope frame shape (SyntaxError) takes the same fallback.
        mapper = ShiftedSourceMapper("/tmp/programa.py", self.NATIVE)
        renderer = self.renderer(tmp_path, mapper)
        out = renderer.render_text('  File "/tmp/programa.py", line 12\n')
        assert out == '  File "/tmp/programa.py", line 9\n'

    def test_unmapped_fallback_frame_passes_through_byte_identical(self, tmp_path):
        mapper = ShiftedSourceMapper("/tmp/programa.py", self.NATIVE)
        renderer = self.renderer(tmp_path, mapper)
        formatted = '  File "/tmp/otro.py", line 12, in f\n    return a / b\n'
        assert renderer.render_text(formatted) == formatted

    def test_one_to_one_mapped_fallback_frame_is_unchanged(self, tmp_path):
        # The production shape: `legesher run` registers a strictly 1:1
        # mapping (LegesherSourceMapper.register_mapping), so the remap
        # resolves to the same number and the header must come out exactly as
        # CPython wrote it — only the source echo is swapped for the native
        # line. This is the case a regression in the splice would actually
        # reach today.
        mapper = FakeSourceMapper("/tmp/programa.py", "\n" * 11 + "    devolver a / b\n")
        renderer = self.renderer(tmp_path, mapper)
        formatted = '  File "/tmp/programa.py", line 12, in dividir\n    return a / b\n'
        out = renderer.render_text(formatted)
        assert '  File "/tmp/programa.py", line 12, in dividir\n' in out
        assert "    devolver a / b\n" in out  # native echo still applies


class TestIdentityCognates:
    """``localized_type_name`` consumes the canonical identity predicate.

    ``schema_v2.is_identity_translation`` (NFKC + casefold, CORE-1355) is the
    single rule behind ``canon_selections.identity_ok``; the renderer's old
    ``.lower()`` re-derivation disagreed with it on width/compatibility
    variants, so a cognate the DB marks ``identity_ok`` rendered as a fake
    localization (CORE-1777).
    """

    def renderer_with_vocabulary(self, tmp_path, names: dict) -> TracebackRenderer:
        renderer = TracebackRenderer("es", db_path=tmp_path / "missing.db")
        renderer._exception_names = dict(names)
        return renderer

    def test_width_variant_cognate_renders_as_identity(self, tmp_path):
        # Fullwidth "ValueError" is the same word under NFKC + casefold; the
        # old comparison saw a different string and rendered the fullwidth
        # form as if it were a localization.
        renderer = self.renderer_with_vocabulary(tmp_path, {"valueerror": "ＶａｌｕｅＥｒｒｏｒ"})
        assert renderer.localized_type_name("ValueError") == "ValueError"

    def test_exception_line_with_width_variant_pack_word(self, tmp_path):
        renderer = self.renderer_with_vocabulary(tmp_path, {"valueerror": "ＶａｌｕｅＥｒｒｏｒ"})
        out = renderer.render_text("ValueError: boom\n")
        assert out == "ValueError: boom\n"

    def test_case_variant_identity_still_wins(self, tmp_path):
        # The en pack's identity mappings: lowercase word == English name.
        renderer = self.renderer_with_vocabulary(tmp_path, {"valueerror": "valueerror"})
        assert renderer.localized_type_name("ValueError") == "ValueError"

    def test_real_localization_still_renders(self, tmp_path):
        renderer = self.renderer_with_vocabulary(tmp_path, {"valueerror": "errordevalor"})
        assert renderer.localized_type_name("ValueError") == "errordevalor"


class TestNeverRaise:
    def test_render_falls_back_to_original_on_internal_failure(self, raise_from_script):
        cap = raise_from_script("1 / 0\n")
        renderer = TracebackRenderer("es")
        original = "".join(traceback.format_exception(cap.exc_type, cap.exc_value, cap.exc_tb))

        def explode(_text: str) -> str:
            raise RuntimeError("renderer bug")

        renderer.render_text = explode  # type: ignore[method-assign]
        out = renderer.render(cap.exc_type, cap.exc_value, cap.exc_tb)
        assert out == original  # fallback is the original traceback, verbatim

    def test_bogus_traceback_object_degrades_to_minimal_line(self):
        # The review repro: render(ValueError, ValueError("x"), "not a tb")
        # used to raise AttributeError out of format_exception.
        renderer = TracebackRenderer("es")
        out = renderer.render(ValueError, ValueError("x"), "not a tb")  # type: ignore[arg-type]
        assert out == "errordevalor: x\n"

    def test_bogus_traceback_with_catalog_message_localizes_minimal_line(self):
        renderer = TracebackRenderer("es")
        out = renderer.render(
            ZeroDivisionError,
            ZeroDivisionError("division by zero"),
            object(),  # type: ignore[arg-type]
        )
        assert out == "errordedivisiónporcero: división por cero\n"

    def test_degraded_construction_is_passthrough_not_crash(self, tmp_path):
        # Nonexistent database + nonexistent language: everything passes
        # through and nothing raises.
        renderer = TracebackRenderer("xx", db_path=tmp_path / "missing.db")
        line = "ZeroDivisionError: division by zero\n"
        assert renderer.render_text(line) == line


class TestEmptyCatalogDiagnostic:
    """An empty catalog logs WHICH degraded mode it is (CORE-1848).

    ``load_catalog`` returns ``[]`` both when the database file is absent and
    when the file exists without the messages partition; the renderer's debug
    line is the one place that tells them apart.
    """

    def test_missing_database_is_named(self, tmp_path, caplog):
        with caplog.at_level("DEBUG", logger="legesher_runtime.renderer"):
            TracebackRenderer("es", db_path=tmp_path / "missing.db")
        assert "no translations database at" in caplog.text
        assert str(tmp_path / "missing.db") in caplog.text

    def test_database_without_messages_partition_is_named(self, tmp_path, caplog):
        import sqlite3

        db = tmp_path / "translations.db"
        connection = sqlite3.connect(db)
        connection.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY)")
        connection.commit()
        connection.close()
        with caplog.at_level("DEBUG", logger="legesher_runtime.renderer"):
            TracebackRenderer("es", db_path=db)
        assert "messages partition missing or unseeded" in caplog.text
        assert str(db) in caplog.text


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="PEP 657 caret and anchor lines arrived in Python 3.11; 3.10 prints none",
)
class TestPep657Preservation:
    def test_caret_and_anchor_lines_are_byte_identical(self, raise_from_script):
        cap = raise_from_script("def sumar(a, b):\n    return a + b\n\nsumar('x', 1)\n")
        original = "".join(traceback.format_exception(cap.exc_type, cap.exc_value, cap.exc_tb))
        rendered = TracebackRenderer("es").render(cap.exc_type, cap.exc_value, cap.exc_tb)
        original_carets = [
            line
            for line in original.splitlines()
            if line.strip() and set(line.strip()) <= {"~", "^"}
        ]
        rendered_carets = [
            line
            for line in rendered.splitlines()
            if line.strip() and set(line.strip()) <= {"~", "^"}
        ]
        assert original_carets and original_carets == rendered_carets
