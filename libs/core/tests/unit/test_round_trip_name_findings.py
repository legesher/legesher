"""A byte-identical round trip is not VERIFIED when it cannot vouch for a name (CORE-2237).

Before the fix, ``mismo.rango`` went to ``self.range`` and came back as
``mismo.rango``: byte-identical, VERIFIED, and English that raises
``AttributeError``. Byte identity cannot see that class, so the report now
carries name findings, and any finding turns the verdict into NOT VERIFIED:

* ``renamed``: a name the engine keeps (an attribute, a keyword argument, a
  module path) changed on the way out. This is the old engine's defect,
  reproduced here by turning the kept-name rule off.
* ``unchecked``: the trip changed the token structure, so names could not be
  compared one to one.
* ``kept_pack_term``: native source with a kept name spelled like a pack
  term. Kept is right for the author's own attribute and wrong for a
  library name an earlier version localized (``os.abrir``), and the check
  cannot tell which.
* ``shadowed`` (CORE-2614) and ``soft_keyword`` (CORE-2613): what the engine
  still renders wrongly.
"""

from __future__ import annotations

import json

import pytest

import legesher_core.transformer as transformer
from legesher_core import create_translator_from_language_pack
from legesher_core.round_trip import (
    FindingKind,
    Layer,
    verify_round_trip,
)
from legesher_i18n.pack_loader import LanguagePackLoader

TIER = "3.10"


def engine_translate(language: str):
    """A ``TranslateFn`` over the token engine for one pack."""
    forward = create_translator_from_language_pack(
        "python", language, TIER, use_tree_sitter=False
    )
    reverse = forward.reverse()

    def translate(source, source_lang, target_lang, python_version):
        return (forward if source_lang == "en" else reverse).translate_code(
            source
        ), False

    return translate


def verify(
    source: str, source_lang: str, through_lang: str, *, language="es", translate=None
):
    pack = LanguagePackLoader().load(language, target="python", version=TIER)
    return verify_round_trip(
        source,
        source_lang,
        through_lang,
        TIER,
        translate=translate or engine_translate(language),
        pack=pack,
    )


#: The ticket's forward cases, written in English.
FORWARD = "user.id = 1\nparser.add_argument('--n', type=int)\nfd = os.open(p, 0)\n"

#: The reproduction written entirely in Spanish.
REPRODUCTION = (
    "clase Punto:\n"
    "    definir __init__(mismo):\n"
    "        mismo.rango = 5\n"
    "p = Punto()\n"
    "imprimir(obtenerelatributo(p, 'rango'))\n"
)


class TestTheOldEngineIsCaught:
    """The verifier's own guard: with the kept-name rule turned off (the
    engine before CORE-2237), every trip below is byte-identical and must
    still not read VERIFIED."""

    @pytest.fixture
    def old_engine(self, monkeypatch):
        monkeypatch.setattr(transformer, "kept_names", lambda tokens, keyword_of: {})

    def test_forward_renames_are_reported(self, old_engine):
        report = verify(FORWARD, "en", "es")
        assert report.round_trips is True
        assert [f.kind for f in report.findings] == [FindingKind.RENAMED] * 3
        assert [f.role for f in report.findings] == [
            "attribute",
            "keyword_argument",
            "attribute",
        ]
        assert [(f.line, f.offset) for f in report.findings] == [
            (1, 6),
            (2, 28),
            (3, 9),
        ]
        assert "NOT VERIFIED" in report.verdict_line
        assert "renamed where it cannot be the builtin" in report.verdict_line
        assert Layer.BUILTINS not in report.verified

    def test_the_fixed_engine_verifies_the_same_source(self):
        report = verify(FORWARD, "en", "es")
        assert report.findings == ()
        assert report.verdict_line.startswith("legesher: round-trip VERIFIED")
        assert Layer.BUILTINS in report.verified


class TestNativeSource:
    def test_the_reproduction_is_not_verified(self):
        report = verify(REPRODUCTION, "es", "en")
        assert report.round_trips is True
        assert [(f.kind, f.role, f.layer) for f in report.findings] == [
            (FindingKind.KEPT_PACK_TERM, "attribute", Layer.BUILTINS)
        ]
        assert report.verdict_line == (
            "legesher: round-trip NOT VERIFIED — es→en→es · byte-identical, but "
            "1 name(s) it cannot vouch for · first at line 3 col 15: an attribute "
            "spelled like a pack term, kept as written (CORE-2237) · grammar 3.10"
        )

    @pytest.mark.parametrize(
        "source,role",
        [
            ("importar os\nfd = os.abrir('p', 0)\n", "attribute"),
            ("f(tipo=1)\n", "keyword_argument"),
            ("importar entrada\n", "module"),
        ],
    )
    def test_each_kept_role_spelled_like_a_pack_term(self, source, role):
        report = verify(source, "es", "en")
        assert [(f.kind, f.role) for f in report.findings] == [
            (FindingKind.KEPT_PACK_TERM, role)
        ]
        assert "NOT VERIFIED" in report.verdict_line

    @pytest.mark.parametrize("language", ["hi", "ar"])
    def test_a_marked_script(self, language):
        """Devanagari vowel signs and Arabic harakat, where tokenization is
        the thing being tested. On CPython 3.10 and 3.11 the tokenizer splits
        these words; the check reads each one whole all the same."""
        pack = LanguagePackLoader().load(language, target="python", version=TIER)
        own, attribute = pack.implicit_params["self"], pack.builtins["range"]
        source = f"{pack.builtins['print']}({own}.{attribute})\n"
        report = verify(source, language, "en", language=language)
        assert [(f.kind, f.role) for f in report.findings] == [
            (FindingKind.KEPT_PACK_TERM, "attribute")
        ]
        assert attribute not in report.verdict_line

    def test_a_soft_keyword_after_a_dot_is_ambiguous(self):
        # An earlier version rendered ``pattern.match`` as ``patron.coincidir``.
        report = verify("m = patron.coincidir(texto)\n", "es", "en")
        assert [(f.kind, f.layer) for f in report.findings] == [
            (FindingKind.KEPT_PACK_TERM, Layer.KEYWORDS)
        ]

    def test_a_hard_keyword_in_a_module_path_is_not_ambiguous(self):
        # Welsh writes ``if`` as ``os``. English never has a keyword in a
        # module path, so no earlier version produced this one.
        welsh = LanguagePackLoader().load("cy", target="python", version=TIER).keywords
        source = f"{welsh['import']} os.path\nx = os.path.join('a', 'b')\n"
        report = verify(source, "cy", "en", language="cy")
        assert report.round_trips is True
        assert report.findings == ()

    def test_the_author_writing_the_library_name_verifies(self):
        report = verify(
            "importar os\nfd = os.open('p', 0)\nx = '{}'.format(1)\n", "es", "en"
        )
        assert report.findings == ()
        assert report.verdict_line.startswith("legesher: round-trip VERIFIED")


class TestWhatTheEngineStillRendersWrongly:
    def test_a_shadowed_builtin(self):
        report = verify("def f(list=None):\n    return list\n", "en", "es")
        assert report.round_trips is True
        assert [(f.kind, f.role, f.line, f.offset) for f in report.findings] == [
            (FindingKind.SHADOWED, "binding", 1, 7)
        ]
        assert "rendered as the builtin (CORE-2614)" in report.verdict_line
        assert Layer.BUILTINS not in report.verified

    def test_a_soft_keyword_used_as_a_name(self):
        report = verify("match = 1\nprint(match)\n", "en", "es")
        assert [f.kind for f in report.findings] == [FindingKind.SOFT_KEYWORD] * 2
        assert "rendered as the keyword (CORE-2613)" in report.verdict_line
        assert Layer.KEYWORDS not in report.verified

    @pytest.mark.parametrize("tier", ["3.10", "3.13"])
    def test_a_bound_name_renamed_after_a_dot(self, tier):
        # ``type`` is a keyword before it is a builtin in the 3.12+ packs.
        pack = LanguagePackLoader().load("es", target="python", version=tier)
        report = verify_round_trip(
            "def f(type):\n    return type\nx.type = 1\n",
            "en",
            "es",
            tier,
            translate=engine_translate("es"),
            pack=pack,
        )
        assert report.round_trips is True
        assert [(f.kind, f.role) for f in report.findings] == [
            (FindingKind.SHADOWED, "binding"),
            (FindingKind.SHADOWED, "attribute"),
        ]
        assert "NOT VERIFIED" in report.verdict_line

    def test_an_implicit_parameter_renamed_as_a_keyword_argument(self):
        source = (
            "import json\n"
            "class E(json.JSONEncoder):\n"
            "    @classmethod\n"
            "    def make(cls):\n"
            "        return cls()\n"
            "print(json.dumps(1, cls=E))\n"
        )
        report = verify(source, "en", "es")
        assert [(f.kind, f.role, f.layer) for f in report.findings] == [
            (FindingKind.SHADOWED, "keyword_argument", Layer.IMPLICIT_PARAMS)
        ]
        assert (
            "a keyword argument renamed because the code binds" in report.verdict_line
        )

    def test_soft_keyword_statements_are_not_findings(self):
        source = "match x:\n    case 1:\n        pass\n    case _: pass\n"
        assert verify(source, "en", "es").findings == ()

    def test_native_side_bindings(self):
        report = verify("definir longitud(x):\n    devolver 0\n", "es", "en")
        assert [(f.kind, f.line, f.offset) for f in report.findings] == [
            (FindingKind.SHADOWED, 1, 9)
        ]

    def test_implicit_parameters_are_meant_to_be_bound(self):
        source = "clase C:\n    definir m(mismo):\n        devolver mismo\n"
        assert verify(source, "es", "en").findings == ()


class TestUncheckable:
    def test_a_trip_that_changes_the_token_count(self):
        def translate(source, source_lang, target_lang, python_version):
            if target_lang == "es":
                return source.replace("user.id", "user . id ; 0"), False
            return source.replace("user . id ; 0", "user.id"), False

        report = verify(FORWARD, "en", "es", translate=translate)
        assert report.round_trips is True
        assert report.findings[0].kind is FindingKind.UNCHECKED
        assert "token structure changed" in report.verdict_line
        assert report.verified == frozenset()


class TestNoFalseAlarms:
    @pytest.mark.parametrize(
        "source,source_lang,through_lang",
        [
            ("print(len([1, 2]))\nx = '{}'.format(1)\n", "en", "es"),
            ("import os.path\nprint(os.path.join('a', 'b'))\n", "en", "es"),
            ("imprimir(longitud([1, 2]))\n", "es", "en"),
            ("desde . importar uno\n", "es", "en"),
        ],
    )
    def test_clean_code_verifies(self, source, source_lang, through_lang):
        report = verify(source, source_lang, through_lang)
        assert report.findings == ()
        assert "NOT VERIFIED" not in report.verdict_line


class TestReportShape:
    def test_findings_are_serialised_without_source_content(self):
        report = verify(REPRODUCTION, "es", "en")
        payload = json.loads(json.dumps(report.to_dict()))
        assert payload["finding_count"] == 1
        assert payload["findings"] == [
            {
                "line": 3,
                "offset": 15,
                "kind": "kept_pack_term",
                "role": "attribute",
                "layer": "builtins",
            }
        ]
        assert "rango" not in report.verdict_line

    def test_findings_are_bounded_and_counted(self):
        source = "".join(f"x{n}.rango = {n}\n" for n in range(30))
        pack = LanguagePackLoader().load("es", target="python", version=TIER)
        report = verify_round_trip(
            source,
            "es",
            "en",
            TIER,
            translate=engine_translate("es"),
            pack=pack,
            max_divergences=5,
        )
        assert report.finding_count == 30
        assert len(report.findings) == 5
        assert "30 name(s)" in report.verdict_line

    def test_a_failed_trip_still_reads_failed(self):
        def translate(source, source_lang, target_lang, python_version):
            return ("mismo.rango = 6\n" if target_lang == "es" else source), False

        report = verify("mismo.rango = 5\n", "es", "en", translate=translate)
        assert report.round_trips is False
        assert report.verdict_line.startswith("legesher: round-trip FAILED")
        assert report.finding_count == 1
