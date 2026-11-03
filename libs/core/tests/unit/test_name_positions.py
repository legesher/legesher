"""A name spelled like a builtin is the builtin only where it is used as one (CORE-2237).

The engine used to translate a builtin's name wherever the token appeared.
From a native language to English that renames the author's own attribute
(``mismo.rango`` became ``self.range``) while every string that refers to it
(``getattr(p, 'rango')``) stays, so the English raises ``AttributeError``.

Slice 1 keeps three positions as written, in both directions and in both
backends: a name after a dot, a keyword-argument name, and a module path.
A name the file binds itself keeps its old rendering everywhere, so a
definition and its uses still agree; telling such a name from the builtin it
shadows is CORE-2614, and soft keywords used as names are CORE-2613. Those
rows are strict xfails below.

The reproductions are executed, not compared as text: the defect was English
that reads plausibly and does not run.
"""

from __future__ import annotations

import contextlib
import io
import tokenize

import pytest

from legesher_core import create_translator_from_language_pack
from legesher_core.name_positions import (
    ATTRIBUTE,
    KEYWORD_ARGUMENT,
    MODULE,
    identity,
    name_roles,
)
from legesher_i18n.pack_loader import LanguagePackLoader
from tests.interpreter_gaps import fragmenting_renderings

#: The tier every interpreter the packages support can load.
TIER = "3.10"

BACKENDS = pytest.mark.parametrize(
    "tree_sitter", [False, True], ids=["token", "tree-sitter"]
)


def translators(language: str, tree_sitter: bool):
    forward = create_translator_from_language_pack(
        "python", language, TIER, use_tree_sitter=tree_sitter
    )
    return forward, forward.reverse()


def run(source: str) -> str:
    """Execute ``source`` and return what it printed."""
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        exec(compile(source, "<translated>", "exec"), {"__name__": "__translated__"})
    return printed.getvalue()


def roles_of(source: str, keyword_of=lambda name: None) -> dict[str, list[str]]:
    """``{role: [kept name, ...]}`` in source order, plus ``"bound"``."""
    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    roles = name_roles(tokens, keyword_of)
    found: dict[str, list[str]] = {}
    for index in sorted(roles.kept):
        found.setdefault(roles.kept[index], []).append(tokens[index].string)
    found["bound"] = sorted({tokens[index].string for index in roles.bindings})
    return found


@pytest.fixture(scope="module")
def pack():
    return LanguagePackLoader().load("es", target="python", version=TIER)


# -- the ticket's reproduction, executed ---------------------------------------


class TestTheReproductionRuns:
    """Valid native Python whose attribute is spelled like a builtin's
    rendering must give English that runs, and the string reference to the
    attribute must still name it."""

    #: As written in the ticket: the English ``self`` and ``getattr`` pass
    #: through, which is what an author mixing the two would type.
    TICKET = (
        "clase Punto:\n"
        "    definir __init__(self):\n"
        "        self.rango = 5\n"
        "p = Punto()\n"
        "imprimir(getattr(p, 'rango'))\n"
    )

    @BACKENDS
    def test_the_ticket_reproduction_runs_in_english(self, tree_sitter):
        _, reverse = translators("es", tree_sitter)
        english = reverse.translate_code(self.TICKET)
        assert "self.rango = 5" in english
        assert run(english) == "5\n"

    @BACKENDS
    @pytest.mark.parametrize("language", ["es", "hi", "ar"])
    def test_written_entirely_in_the_pack_language(
        self, language, tree_sitter, request
    ):
        """Hindi (vowel signs, a virama, an anusvara) and Arabic (harakat in
        the pack's ``print``) are the cases that exercise tokenization:
        Latin identifiers prove little about it."""
        pack = LanguagePackLoader().load(language, target="python", version=TIER)
        keyword, builtin = pack.keywords, pack.builtins
        own = pack.implicit_params["self"]
        cls = {"es": "Punto", "hi": "बिंदु", "ar": "نُقطة"}[language]
        attribute = builtin["range"]
        native = (
            f"{keyword['class']} {cls}:\n"
            f"    {keyword['def']} __init__({own}):\n"
            f"        {own}.{attribute} = 5\n"
            f"p = {cls}()\n"
            f"{builtin['print']}({builtin['getattr']}(p, '{attribute}'))\n"
        )
        # The token backend reads words through ``tokenize``; tree-sitter
        # parses them whole on every interpreter.
        fragmenting = fragmenting_renderings(
            [
                keyword["class"],
                keyword["def"],
                own,
                builtin["print"],
                builtin["getattr"],
            ]
        )
        if fragmenting and not tree_sitter:
            request.applymarker(
                pytest.mark.xfail(
                    strict=True,
                    reason=(
                        "pure-Python tokenize splits a marked word, so the return "
                        "hop never sees it (tests/interpreter_gaps.py, gap 1; CORE-2192)"
                    ),
                )
            )
        _, reverse = translators(language, tree_sitter)
        english = reverse.translate_code(native)
        assert f"self.{attribute} = 5" in english
        assert run(english) == "5\n"


# -- the forward cases from the ticket -----------------------------------------


class TestForwardKeepsTheEnglishNames:
    CASES = {
        "an attribute": ("user.id = 1\n", "user.id = 1\n"),
        "a keyword argument": (
            "parser.add_argument('--n', type=int)\n",
            "parser.add_argument('--n', type=entero)\n",
        ),
        "a library function": ("fd = os.open(p, 0)\n", "fd = os.open(p, 0)\n"),
    }

    @BACKENDS
    @pytest.mark.parametrize("english,spanish", list(CASES.values()), ids=list(CASES))
    def test_forward_and_back(self, english, spanish, tree_sitter):
        forward, reverse = translators("es", tree_sitter)
        assert forward.translate_code(english) == spanish
        assert reverse.translate_code(spanish) == english


# -- the slice 1 rows of the 2026-09-27 position table, both directions --------


#: (English, Spanish) where the English names are the library's and the
#: Spanish author kept them, and where the Spanish author's own names are
#: spelled like a builtin's rendering. Each pair must translate into the
#: other in both directions.
SLICE_ONE_ROWS = {
    "attribute access": (
        "fd = os.open(p, 0)\nn = len(np.sum(xs))\n",
        "fd = os.open(p, 0)\nn = longitud(np.sum(xs))\n",
    ),
    "attribute access, native spelling": (
        "x = punto.rango + punto.longitud\n",
        "x = punto.rango + punto.longitud\n",
    ),
    "keyword argument": (
        "parser.add_argument('--n', type=int, help=str(len(xs)))\n",
        "parser.add_argument('--n', type=entero, help=cadena(longitud(xs)))\n",
    ),
    "keyword argument, native spelling": (
        "crear(tipo=int, lista=[1])\n",
        "crear(tipo=entero, lista=[1])\n",
    ),
    "keyword argument in a class header": (
        "class Celda(Base, metaclass=type):\n    pass\n",
        "clase Celda(Base, metaclass=tipo):\n    pasar\n",
    ),
    "attribute on self": (
        "class Lector:\n    def leer(self):\n        self.input = input()\n",
        "clase Lector:\n    definir leer(mismo):\n        mismo.input = entrada()\n",
    ),
    "attribute on self, native spelling": (
        "class Lector:\n    def leer(self):\n        self.entrada = input()\n",
        "clase Lector:\n    definir leer(mismo):\n        mismo.entrada = entrada()\n",
    ),
    "import path": (
        "import input\nfrom list.dict import x\nimport type.str as t\n",
        "importar input\ndesde list.dict importar x\nimportar type.str como t\n",
    ),
    "import path, native spelling": (
        "import entrada\nfrom lista.cadena import x\n",
        "importar entrada\ndesde lista.cadena importar x\n",
    ),
    "a module bound by import, used later": (
        "import entrada\nentrada.leer(len(xs))\n",
        "importar entrada\nentrada.leer(longitud(xs))\n",
    ),
    "a relative import keeps its keyword": (
        "from . import uno\nfrom .. import dos\nfrom .tres import cuatro\n",
        "desde . importar uno\ndesde .. importar dos\ndesde .tres importar cuatro\n",
    ),
    "a soft keyword after a dot": (
        "m = pattern.match(text)\n",
        "m = pattern.match(text)\n",
    ),
}


class TestSliceOnePositions:
    @BACKENDS
    @pytest.mark.parametrize(
        "english,spanish", list(SLICE_ONE_ROWS.values()), ids=list(SLICE_ONE_ROWS)
    )
    def test_english_to_spanish(self, english, spanish, tree_sitter):
        forward, _ = translators("es", tree_sitter)
        assert forward.translate_code(english) == spanish

    @BACKENDS
    @pytest.mark.parametrize(
        "english,spanish", list(SLICE_ONE_ROWS.values()), ids=list(SLICE_ONE_ROWS)
    )
    def test_spanish_to_english(self, english, spanish, tree_sitter):
        _, reverse = translators("es", tree_sitter)
        assert reverse.translate_code(spanish) == english


class TestAModulePathSpelledLikeAKeyword:
    """Welsh writes ``if`` as ``os``. In a module path, and before a dot
    after ``import os``, the word can only be the module."""

    @BACKENDS
    def test_welsh_os(self, tree_sitter):
        keyword = (
            LanguagePackLoader().load("cy", target="python", version=TIER).keywords
        )
        assert keyword["if"] == "os", "the case this test exists for"
        english = "import os.path\nx = os.path.join('a', 'b')\nif x:\n    pass\n"
        welsh = (
            f"{keyword['import']} os.path\nx = os.path.join('a', 'b')\n"
            f"{keyword['if']} x:\n    {keyword['pass']}\n"
        )
        forward, reverse = translators("cy", tree_sitter)
        assert forward.translate_code(english) == welsh
        assert reverse.translate_code(welsh) == english


# -- a binding keeps its uses in agreement (the interim rule) ------------------


class TestABindingAndItsUsesAgree:
    """Until binding lands (CORE-2614), a name the file binds keeps its old
    rendering in every position, so the definition and each use translate
    together and the English runs. Without this, keeping ``p.tipo`` while
    renaming the field ``tipo`` would break code that runs today."""

    PROGRAMS = {
        "a class field read as an attribute and passed by keyword": (
            "clase P:\n"
            "    tipo = 'x'\n"
            "    definir __init__(mismo, tipo='y'):\n"
            "        mismo.tipo = tipo\n"
            "p = P(tipo='z')\n"
            "imprimir(p.tipo, P.tipo)\n",
            "z x\n",
        ),
        "a method spelled like a builtin, called as an attribute": (
            "clase Pila:\n"
            "    definir longitud(mismo):\n"
            "        devolver 3\n"
            "imprimir(Pila().longitud())\n",
            "3\n",
        ),
        "a parameter spelled like a builtin, passed by keyword": (
            "definir f(lista=nulo):\n    devolver lista\nimprimir(f(lista=[1]))\n",
            "[1]\n",
        ),
        "an imported name spelled like a builtin, used later": (
            "desde builtins importar longitud\nimprimir(longitud([1, 2]))\n",
            "2\n",
        ),
    }

    @BACKENDS
    @pytest.mark.parametrize(
        "spanish,printed", list(PROGRAMS.values()), ids=list(PROGRAMS)
    )
    def test_runs_in_english(self, spanish, printed, tree_sitter):
        _, reverse = translators("es", tree_sitter)
        assert run(reverse.translate_code(spanish)) == printed


# -- rows a later slice owns: strict xfails naming the ticket ------------------


LATER_SLICES = {
    "a builtin shadowed by an import": (
        "from os import open\nfd = open(p, 0)\n",
        "abrir",
        "CORE-2614: a builtin shadowed by an import is still rendered as the builtin",
    ),
    "the user's own function": (
        "def len(x):\n    return 0\nn = len(y)\n",
        "longitud",
        "CORE-2614: a user's own def len is still rendered as the builtin",
    ),
    "the user's own method": (
        "class Pila:\n    def len(self):\n        return 0\n",
        "longitud",
        "CORE-2614: a method spelled like a builtin is still rendered as it",
    ),
    "a parameter": (
        "def f(input, list=None):\n    return list\n",
        "entrada",
        "CORE-2614: a parameter spelled like a builtin is still rendered as it",
    ),
    "a class field": (
        "class Celda:\n    type: str = 'x'\n",
        "tipo",
        "CORE-2614: a class field spelled like a builtin is still rendered as it",
    ),
    "a soft keyword used as a variable": (
        "match = 1\ncase = 2\n",
        "coincidir",
        "CORE-2613: a soft keyword used as a name is still rendered as the keyword",
    ),
}


class TestLaterSlices:
    @pytest.mark.parametrize(
        "english,rendering",
        [
            pytest.param(
                english, rendering, marks=pytest.mark.xfail(strict=True, reason=reason)
            )
            for english, rendering, reason in LATER_SLICES.values()
        ],
        ids=list(LATER_SLICES),
    )
    def test_never_rendered_as_the_builtin(self, english, rendering):
        forward, reverse = translators("es", False)
        spanish = forward.translate_code(english)
        assert reverse.translate_code(spanish) == english, "the trip itself must hold"
        assert rendering not in spanish


class TestABuiltinUsedAsTheBuiltinStillTranslates:
    """The table's annotation and decorator rows are the builtin itself."""

    @pytest.mark.parametrize(
        "english,spanish",
        [
            (
                "x: int = 1\nys: list[str] = []\n",
                "x: entero = 1\nys: lista[cadena] = []\n",
            ),
            (
                "class C:\n    @property\n    def v(self):\n        return 1\n",
                "clase C:\n    @propiedad\n    definir v(mismo):\n        devolver 1\n",
            ),
            ("print(type(x), len(xs))\n", "imprimir(tipo(x), longitud(xs))\n"),
        ],
        ids=["annotation", "decorator", "call"],
    )
    def test_both_directions(self, english, spanish):
        forward, reverse = translators("es", False)
        assert forward.translate_code(english) == spanish
        assert reverse.translate_code(spanish) == english


# -- the token pass itself -----------------------------------------------------


class TestNameRoles:
    def test_positions_and_roles(self):
        found = roles_of(
            "import a.b as c, d\n"
            "user.id = f(type=1, key=len)\n"
            "class C(B, metaclass=M):\n"
            "    pass\n"
        )
        assert found[MODULE] == ["a", "b", "d"]
        assert found[ATTRIBUTE] == ["id"]
        assert found[KEYWORD_ARGUMENT] == ["type", "key", "metaclass"]
        assert found["bound"] == ["C", "c"]

    def test_a_bound_name_is_not_kept_anywhere(self):
        found = roles_of("type = 3\nx.type\nf(type=1)\n")
        assert ATTRIBUTE not in found and KEYWORD_ARGUMENT not in found
        assert found["bound"] == ["type"]

    @pytest.mark.parametrize(
        "source,bound",
        [
            (
                "def f(a, b=len, *args, c: int = 2, **kw) -> list:\n    pass\n",
                ["a", "args", "b", "c", "f", "kw"],
            ),
            ("g = lambda a, list=None: f(a, sum=list)\n", ["a", "g", "list"]),
            ("for i, (j, k) in z:\n    pass\n", ["i", "j", "k"]),
            ("with open(p) as fh, q as (m, n):\n    pass\n", ["fh", "m", "n"]),
            ("a[i], b.c, (d, *e) = v\n", ["d", "e"]),
            ("x: dict[str, int] = {}\ny += 1\n", ["x", "y"]),
            ("if (n := len(a)) > 1:\n    pass\n", ["n"]),
            ("from m import open as o, len\n", ["len", "o", "open"]),
            ("class P[T](B):\n    pass\n", ["P", "T"]),
            ("try:\n    pass\nexcept E as err:\n    pass\n", ["err"]),
            ("ys = [x for x in range(3)]\n", ["x", "ys"]),
            ("global total\n", ["total"]),
        ],
    )
    def test_bindings(self, source, bound):
        assert roles_of(source)["bound"] == bound

    def test_a_type_alias_binds_its_alias_not_type(self):
        found = roles_of("type X = int\ntype Y[T] = list[T]\np.add(type=int)\n")
        assert found[KEYWORD_ARGUMENT] == ["type"]
        assert found["bound"] == ["T", "X", "Y"]

    def test_an_annotation_inside_a_signature_binds_nothing(self):
        # ``str`` and ``int`` in ``Dict[str, int]`` are uses of the builtin.
        found = roles_of("def f(x: dict[str, int]) -> list[str]:\n    pass\n")
        assert found["bound"] == ["f", "x"]

    def test_soft_keyword_statements(self):
        tokens = list(
            tokenize.generate_tokens(
                io.StringIO(
                    "match = re.match(p, s)\n"
                    "match x:\n"
                    "    case [a, b]:\n"
                    "        pass\n"
                    "    case 1: pass\n"
                    "match(x)\n"
                ).readline
            )
        )
        statements = name_roles(tokens, lambda name: None).soft_keyword_statements
        assert sorted(tokens[index].start for index in statements) == [
            (2, 0),
            (3, 4),
            (5, 4),
        ]

    def test_native_keywords_are_read_through_the_table(self, pack):
        native = {rendering: english for english, rendering in pack.keywords.items()}
        found = roles_of(
            "importar entrada\ndesde . importar x\nclase C:\n    tipo = 1\n",
            native.get,
        )
        assert found[MODULE] == ["entrada"]
        assert found["bound"] == ["C", "tipo", "x"]

    def test_binding_identity_is_nfkc(self):
        # Python reads identifiers NFKC, so the full-width spelling binds
        # the same name; the attribute must follow the binding.
        found = roles_of("ｔｙｐｅ = 1\nx.type\n")
        assert ATTRIBUTE not in found
        assert identity("ｔｙｐｅ") == "type"
