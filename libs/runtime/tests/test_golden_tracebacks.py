"""Golden localized tracebacks for es and ar (CORE-1679).

Real exceptions raised from a real on-disk script, rendered end to end and
compared line-for-line. The harness frames (conftest's ``exec``) are cut by
anchoring on the script's own first frame; the tmp path is normalized to
``script.py``.

PEP 657 anchor lines (``~~~^^^``) appear from Python 3.11; the goldens pin
them, so the suite requires 3.11+ (the workspace floor for DB paths is 3.13).

RTL posture (v1): the Arabic goldens are LOGICAL-order strings — the
renderer inserts no bidi control characters and leaves display reordering to
the terminal. See libs/runtime/README.md.
"""

from __future__ import annotations

import re
import sys

import pytest

from legesher_runtime import TracebackRenderer

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 11), reason="goldens pin PEP 657 anchor lines (3.11+)"
)

#: Bidi control characters the v1 renderer must never emit.
BIDI_CONTROLS = tuple(
    chr(cp)
    for cp in (
        0x2066,
        0x2067,
        0x2068,
        0x2069,
        0x202A,
        0x202B,
        0x202C,
        0x202D,
        0x202E,
        0x200E,
        0x200F,
        0x061C,
    )
)

ZERODIV_SCRIPT = "def dividir(a, b):\n    return a / b\n\ndividir(1, 0)\n"

CHAINED_SCRIPT = (
    "try:\n    {}['clave']\nexcept KeyError as exc:\n    raise ValueError('sin clave') from exc\n"
)


FRAME_MARKERS = ('File "', 'Archivo "', 'الملف "')


def rendered_tail(lang: str, cap) -> list[str]:
    """The rendered traceback minus the test harness's own frames.

    Frame blocks (frame line + echoed source/caret lines) that point at the
    harness (conftest's ``exec``) are dropped; everything else is golden.
    """
    rendered = cap.normalize(
        TracebackRenderer(lang).render(cap.exc_type, cap.exc_value, cap.exc_tb)
    )
    out: list[str] = []
    dropping = False
    for line in rendered.splitlines():
        is_frame = any(marker in line for marker in FRAME_MARKERS) and line.startswith("  ")
        if is_frame:
            dropping = "script.py" not in line
        elif not line.startswith("    "):
            dropping = False  # left the frame block (header/blank/final line)
        if not dropping:
            out.append(line)
    return out


class TestSpanishGoldens:
    def test_zerodivision(self, raise_from_script):
        cap = raise_from_script(ZERODIV_SCRIPT)
        assert rendered_tail("es", cap) == [
            "Rastreo (llamada más reciente al final):",
            '  Archivo "script.py", línea 4, en <module>',
            "    dividir(1, 0)",
            "    ~~~~~~~^^^^^^",
            '  Archivo "script.py", línea 2, en dividir',
            "    return a / b",
            "           ~~^~~",
            "errordedivisiónporcero: división por cero",
        ]

    def test_nameerror_slot_substitution(self, raise_from_script):
        cap = raise_from_script("print(variable_desconocida)\n")
        assert rendered_tail("es", cap) == [
            "Rastreo (llamada más reciente al final):",
            '  Archivo "script.py", línea 1, en <module>',
            "    print(variable_desconocida)",
            "          ^^^^^^^^^^^^^^^^^^^^",
            "Errordenombre: el nombre 'variable_desconocida' no está definido",
        ]

    def test_chained_exception_cause(self, raise_from_script):
        cap = raise_from_script(CHAINED_SCRIPT)
        assert rendered_tail("es", cap) == [
            "Rastreo (llamada más reciente al final):",
            '  Archivo "script.py", línea 2, en <module>',
            "    {}['clave']",
            "    ~~^^^^^^^^^",
            "errordeclave: 'clave'",
            "",
            "La excepción anterior fue la causa directa de la siguiente excepción:",
            "",
            "Rastreo (llamada más reciente al final):",
            '  Archivo "script.py", línea 4, en <module>',
            "    raise ValueError('sin clave') from exc",
            # unmatched custom message: type localized, message passed through
            "errordevalor: sin clave",
        ]


class TestArabicGoldens:
    def test_zerodivision_logical_order(self, raise_from_script):
        cap = raise_from_script(ZERODIV_SCRIPT)
        assert rendered_tail("ar", cap) == [
            "التتبع (آخر استدعاء في الأسفل):",
            '  الملف "script.py"، السطر 4، في <module>',
            "    dividir(1, 0)",
            "    ~~~~~~~^^^^^^",
            '  الملف "script.py"، السطر 2، في dividir',
            "    return a / b",
            "           ~~^~~",
            "خطأالقسمةعلىالصفر: القسمة على صفر",
        ]

    def test_nameerror_slot_substitution(self, raise_from_script):
        cap = raise_from_script("print(variable_desconocida)\n")
        assert rendered_tail("ar", cap) == [
            "التتبع (آخر استدعاء في الأسفل):",
            '  الملف "script.py"، السطر 1، في <module>',
            "    print(variable_desconocida)",
            "          ^^^^^^^^^^^^^^^^^^^^",
            "خطأالاسم: الاسم 'variable_desconocida' غير معرف",
        ]

    def test_output_is_logical_order_without_bidi_controls(self, raise_from_script):
        """v1 RTL posture: logical order, zero bidi control characters."""
        cap = raise_from_script(ZERODIV_SCRIPT)
        rendered = TracebackRenderer("ar").render(cap.exc_type, cap.exc_value, cap.exc_tb)
        for control in BIDI_CONTROLS:
            assert control not in rendered
        # Logical order: the Arabic frame word precedes the LTR path on the
        # line, i.e. the string starts with the Arabic token, not the path.
        frame_line = next(line for line in rendered.splitlines() if "script.py" in line)
        assert re.match(r'\s*الملف "', frame_line)
