"""Positions where a name spelled like a builtin cannot be the builtin (CORE-2237).

A builtin is not a reserved word. In ``self.range``, ``f(type=int)`` and
``import input`` the names are an attribute, a parameter of the callee and a
module, whatever the pack says about ``range``, ``type`` and ``input``. This
module finds those positions in a token stream, so a translator leaves the
name as written in both directions.

It reads tokens, not a syntax tree, because localized source does not parse
until its keywords are English. Three positions keep their spelling:

- a name directly after ``.``: attribute access, ``self.x``, a dotted module
  path. The ``import`` of ``from . import x`` is still the keyword.
- the name of a keyword argument in a call or a class header.
- a module path in ``import`` and ``from ... import``, and a module name bound
  by a plain ``import`` wherever the file uses it. Module names stay canonical.

A name the file binds itself (a definition, a parameter, an assignment target,
an imported name) keeps the rendering it had before, in every position, so the
binding and each use of it still agree: ``definir longitud(mismo)`` and
``p.longitud()`` translate together. Telling such a name from the builtin it
shadows needs scope, which this module does not model.

This file is kept byte-identical at ``libs/core/legesher_core/name_positions.py``
and ``libs/language-server/legesher_language_server/name_positions.py``. The
language server does not depend on legesher-core, and its proxy must send the
type checker the English that ``legesher run`` executes.
``scripts/tests/test_name_positions_copies.py`` fails when the copies differ.
Edit one and copy it over the other. The two packages format at 88 and 100
columns, so keep each line one that ruff leaves alone at both widths.
"""

from __future__ import annotations

import keyword
import tokenize
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

__all__ = [
    "ATTRIBUTE",
    "KEYWORD_ARGUMENT",
    "MODULE",
    "SOFT_KEYWORDS",
    "NameRoles",
    "identity",
    "kept_names",
    "name_roles",
    "word_at",
]

#: Roles of a name kept as written.
ATTRIBUTE = "attribute"
KEYWORD_ARGUMENT = "keyword_argument"
MODULE = "module"

#: Soft keywords, spelled out because ``keyword.softkwlist`` depends on the
#: running interpreter (``type`` joined it in 3.12) and packs are versioned
#: by target grammar, not by the interpreter they run under.
SOFT_KEYWORDS = frozenset({"_", "case", "match", "type"})

_SKIPPED = frozenset({tokenize.COMMENT, tokenize.NL, tokenize.ENCODING})
#: Format characters that occur inside words: ZWNJ and ZWJ.
_JOINERS = frozenset({"\u200c", "\u200d"})
_BOUNDARIES = frozenset(
    {
        tokenize.NEWLINE,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.ENDMARKER,
    }
)
_OPENERS = {"(": ")", "[": "]", "{": "}"}
_CLOSERS = frozenset(_OPENERS.values())
_COMPOUND = frozenset(
    {
        "async",
        "class",
        "def",
        "elif",
        "else",
        "except",
        "finally",
        "for",
        "if",
        "try",
        "while",
        "with",
    }
)
_AUGMENTED = frozenset(
    {"+=", "-=", "*=", "/=", "//=", "%=", "**=", ">>=", "<<=", "&=", "|=", "^=", "@="}
)
#: After a name, a literal or a closing bracket, a bracket indexes or calls.
_LITERALS = frozenset({tokenize.NUMBER, tokenize.STRING})
#: A soft keyword at the start of a line is a name when one of these follows.
_NAME_FOLLOWERS = _AUGMENTED | {"=", ".", ":", ",", ")", "]", "}", ";", ":="}


def _inside_word(ch: str) -> bool:
    return unicodedata.category(ch)[0] == "M" or ch in _JOINERS


def _continues(token: tokenize.TokenInfo, previous: tokenize.TokenInfo) -> bool:
    """Whether ``token`` is the next fragment of a word the tokenizer split:
    touching the previous token, and either marks and format characters or
    the NAME after them."""
    if token.start != previous.end:
        return False
    if token.type == tokenize.ERRORTOKEN:
        return all(_inside_word(ch) for ch in token.string)
    return token.type == tokenize.NAME and previous.type == tokenize.ERRORTOKEN


def word_at(tokens: Sequence[tokenize.TokenInfo], index: int) -> str:
    """The whole word that starts at ``tokens[index]``, with the fragments a
    pre-3.12 tokenizer split it into folded back together."""
    end = index
    while end + 1 < len(tokens) and _continues(tokens[end + 1], tokens[end]):
        end += 1
    if end == index:
        return tokens[index].string
    return tokens[index].line[tokens[index].start[1] : tokens[end].end[1]]


def identity(name: str) -> str:
    """The form Python compares identifiers in (NFKC); ASCII is its own."""
    return name if name.isascii() else unicodedata.normalize("NFKC", name)


@dataclass(frozen=True)
class NameRoles:
    """What the token pass found, by index into the token list it was given.

    ``kept`` maps each NAME token that keeps its spelling to its role.
    ``bindings`` maps each NAME token at a binding site to its ``identity``.
    ``soft_keyword_statements`` holds the ``match`` and ``case`` tokens that
    open a statement; any other soft-keyword token is a name.

    CPython 3.10 and 3.11 tokenize a name as ``\\w+``, so a vowel sign, a
    virama or a joiner splits one word into NAME and ERRORTOKEN fragments
    (CORE-2192). The pass reads such a run as one word: its index is the
    first fragment's, and ``words`` holds its whole text.
    """

    kept: Mapping[int, str]
    bindings: Mapping[int, str]
    soft_keyword_statements: frozenset[int]
    words: Mapping[int, str]
    #: Positions that would be kept but for a binding of the same name in the
    #: file, with their role: they keep the old rendering.
    unkept: Mapping[int, str]


def kept_names(
    tokens: Sequence[tokenize.TokenInfo],
    keyword_of: Callable[[str], str | None],
) -> Mapping[int, str]:
    """Indices of the NAME tokens a translator must leave as written."""
    return name_roles(tokens, keyword_of).kept


def name_roles(
    tokens: Sequence[tokenize.TokenInfo],
    keyword_of: Callable[[str], str | None],
) -> NameRoles:
    """Classify the NAME tokens of one source text.

    ``keyword_of`` returns what a NAME token translates to through the
    caller's keyword table, or None. Only English keywords are interpreted,
    so the same table works in both directions: from English it maps
    ``import`` to a native word (and the token itself is the keyword), from a
    native language it maps the native word to ``import``.
    """
    return _Pass(tokens, keyword_of).run()


class _Pass:
    def __init__(
        self,
        tokens: Sequence[tokenize.TokenInfo],
        keyword_of: Callable[[str], str | None],
    ) -> None:
        self.tokens = tokens
        self.keyword_of = keyword_of
        self.keywords: dict[int, str] = {}
        self.candidates: dict[int, str] = {}
        self.module_paths: set[int] = set()
        self.bindings: dict[int, str] = {}
        self.modules: set[str] = set()
        self.statements: set[int] = set()
        self.words: dict[int, str] = {}

    # -- token helpers -------------------------------------------------------

    def keyword(self, index: int) -> str | None:
        """The English hard keyword a NAME token is, or None."""
        if index not in self.keywords:
            if self.tokens[index].type != tokenize.NAME:
                self.keywords[index] = ""
                return None
            text = self.word(index)
            translated = self.keyword_of(text)
            if translated is not None and keyword.iskeyword(translated):
                found: str | None = translated
            elif keyword.iskeyword(text):
                found = text
            else:
                found = None
            self.keywords[index] = found or ""
        return self.keywords[index] or None

    def soft_keyword(self, index: int) -> str | None:
        """The English soft keyword a NAME token renders, or None."""
        if self.tokens[index].type != tokenize.NAME:
            return None
        text = self.word(index)
        translated = self.keyword_of(text)
        if translated in SOFT_KEYWORDS:
            return translated
        return text if text in SOFT_KEYWORDS else None

    def is_op(self, index: int | None, *strings: str) -> bool:
        if index is None:
            return False
        token = self.tokens[index]
        return token.type == tokenize.OP and token.string in strings

    def is_name(self, index: int | None) -> bool:
        """A NAME token that is not a hard keyword."""
        return (
            index is not None
            and self.tokens[index].type == tokenize.NAME
            and self.keyword(index) is None
        )

    @staticmethod
    def at(statement: list[int], position: int) -> int | None:
        return statement[position] if position < len(statement) else None

    def word(self, index: int) -> str:
        return self.words.get(index, self.tokens[index].string)

    def bind(self, index: int) -> None:
        self.bindings[index] = identity(self.word(index))

    # -- the pass ------------------------------------------------------------

    def run(self) -> NameRoles:
        significant = self.significant()
        for statement in self.statements_of(significant):
            self.statement(statement)
        bound = set(self.bindings.values())
        kept: dict[int, str] = {}
        unkept: dict[int, str] = {}
        for index, role in self.candidates.items():
            if identity(self.word(index)) not in bound:
                kept[index] = role
            else:
                unkept[index] = role
        for index in self.module_paths:
            kept[index] = MODULE
        modules = self.modules - bound
        if modules:
            for position, index in enumerate(significant):
                if (
                    self.tokens[index].type != tokenize.NAME
                    or index in kept
                    or identity(self.word(index)) not in modules
                ):
                    continue
                # Spelled like a keyword, it is the module only when a dot
                # follows: Welsh ``os.path`` against ``os x:`` (``if x:``).
                following = self.at(significant, position + 1)
                if self.keyword(index) is None or self.is_op(following, "."):
                    kept[index] = MODULE
        return NameRoles(
            kept=kept,
            bindings=self.bindings,
            soft_keyword_statements=frozenset(self.statements),
            words=self.words,
            unkept=unkept,
        )

    def significant(self) -> list[int]:
        """Indices of the tokens that matter, with each split word's later
        fragments folded into its first NAME token."""
        significant: list[int] = []
        first: int | None = None  # the NAME token the current word began at
        for index, token in enumerate(self.tokens):
            if token.type in _SKIPPED:
                first = None
                continue
            if first is not None and _continues(token, self.tokens[index - 1]):
                start, end = self.tokens[first].start[1], token.end[1]
                self.words[first] = token.line[start:end]
                continue
            first = index if token.type == tokenize.NAME else None
            significant.append(index)
        return significant

    def statements_of(self, significant: list[int]) -> list[list[int]]:
        """Split at NEWLINE/INDENT/DEDENT, a top-level ``;``, and the colon
        that ends a compound statement's header."""
        statements: list[list[int]] = []
        current: list[int] = []
        depth = 0
        for index in significant:
            token = self.tokens[index]
            if token.type in _BOUNDARIES:
                if current:
                    statements.append(current)
                current, depth = [], 0
                continue
            if token.type == tokenize.OP:
                if token.string in _OPENERS:
                    depth += 1
                elif token.string in _CLOSERS:
                    depth = max(depth - 1, 0)
                elif depth == 0 and token.string == ";":
                    if current:
                        statements.append(current)
                    current = []
                    continue
                elif depth == 0 and token.string == ":" and current:
                    if self.opens_block(current):
                        statements.append(current + [index])
                        current = []
                        continue
            current.append(index)
        if current:
            statements.append(current)
        return statements

    def opens_block(self, statement: list[int]) -> bool:
        head = statement[0]
        if self.tokens[head].type != tokenize.NAME:
            return False
        word = self.keyword(head)
        if word in _COMPOUND:
            # A lambda's colon inside the header sits at the same depth only
            # after the header's own colon, so the first one ends the header.
            return not self.inside_lambda(statement)
        if self.soft_keyword(head) in ("match", "case"):
            follower = statement[1] if len(statement) > 1 else None
            if follower is not None and not self.is_op(follower, *_NAME_FOLLOWERS):
                self.statements.add(head)
                return True
        return False

    def inside_lambda(self, statement: list[int]) -> bool:
        """True when an unclosed top-level ``lambda`` precedes the colon."""
        depth = 0
        open_lambdas = 0
        for index in statement:
            token = self.tokens[index]
            if token.type == tokenize.OP:
                if token.string in _OPENERS:
                    depth += 1
                elif token.string in _CLOSERS:
                    depth = max(depth - 1, 0)
                elif token.string == ":" and depth == 0 and open_lambdas:
                    open_lambdas -= 1
            elif depth == 0 and self.keyword(index) == "lambda":
                open_lambdas += 1
        return open_lambdas > 0

    # -- one statement -------------------------------------------------------

    def statement(self, statement: list[int]) -> None:
        head = statement[0]
        word = self.keyword(head)
        if word == "import":
            self.import_statement(statement)
        elif word == "from":
            self.from_statement(statement)
        elif word in ("global", "nonlocal"):
            for index in statement[1:]:
                if self.is_name(index):
                    self.bind(index)
        elif self.type_alias(statement):
            self.bind(statement[1])
        elif word is None and head not in self.statements:
            self.assignment(statement)
        self.expressions(statement)

    def type_alias(self, statement: list[int]) -> bool:
        """``type X = ...`` and ``type X[T] = ...`` (3.12): the soft keyword
        opens the statement and ``X`` is what it binds."""
        if len(statement) < 3 or self.soft_keyword(statement[0]) != "type":
            return False
        if not self.is_name(statement[1]) or not self.is_op(statement[2], "=", "["):
            return False
        self.statements.add(statement[0])
        return True

    def import_statement(self, statement: list[int]) -> None:
        """``import a.b as c, d``: a, b and d are module paths, c is bound,
        and d is a module name the rest of the file may use. A module path
        holds only module names, even one spelled like a pack's keyword
        (Welsh writes ``if`` as ``os``)."""
        clause: list[int] = []
        for index in [*statement[1:], None]:
            if index is not None and not self.is_op(index, ","):
                clause.append(index)
                continue
            as_at = [p for p, i in enumerate(clause) if self.keyword(i) == "as"]
            alias = as_at[0] if as_at else None
            path = clause if alias is None else clause[:alias]
            names = [i for i in path if self.tokens[i].type == tokenize.NAME]
            self.module_paths.update(names)
            if alias is None and names:
                self.modules.add(identity(self.word(names[0])))
            elif alias is not None:
                for i in clause[alias + 1 :]:
                    if self.is_name(i):
                        self.bind(i)
            clause = []

    def from_statement(self, statement: list[int]) -> None:
        """``from a.b import c as d``: a and b are module paths; c and d are
        names the import binds."""
        imported = False
        for index in statement[1:]:
            if not imported and self.keyword(index) == "import":
                imported = True
            elif imported and self.is_name(index):
                self.bind(index)
            elif not imported and self.tokens[index].type == tokenize.NAME:
                self.module_paths.add(index)

    def assignment(self, statement: list[int]) -> None:
        """Bind the targets of ``a = b``, ``a, *b = c``, ``a += b`` and
        ``a: T = b``."""
        depth = 0
        targets_end = 0
        for position, index in enumerate(statement):
            token = self.tokens[index]
            if token.type != tokenize.OP:
                if depth == 0 and self.keyword(index) == "lambda":
                    break  # a lambda's ``=`` is a default, not an assignment
                continue
            if token.string in _OPENERS:
                depth += 1
            elif token.string in _CLOSERS:
                depth = max(depth - 1, 0)
            elif depth == 0 and token.string in (":", *_AUGMENTED):
                # An annotation or an augmented assignment: one target list.
                targets_end = position
                break
            elif depth == 0 and token.string == "=":
                targets_end = position
        if targets_end:
            self.targets(statement[:targets_end])

    def targets(self, span: list[int]) -> None:
        """Bind each name in a target list that is not indexed, called or
        dotted: ``a, (b, c)`` binds three names, ``a[i].b`` binds none."""
        grouping: list[bool] = []
        previous: int | None = None
        for position, index in enumerate(span):
            token = self.tokens[index]
            if token.type == tokenize.OP and token.string in _OPENERS:
                accessed = previous is not None and (
                    self.is_name(previous)
                    or self.tokens[previous].type in _LITERALS
                    or self.is_op(previous, ")", "]", "}")
                )
                grouping.append(not accessed)
            elif token.type == tokenize.OP and token.string in _CLOSERS:
                if grouping:
                    grouping.pop()
            elif self.is_name(index) and all(grouping):
                following = self.at(span, position + 1)
                accessed = self.is_op(following, ".", "(", "[")
                if not self.is_op(previous, ".") and not accessed:
                    self.bind(index)
            previous = index

    def special_brackets(self, statement: list[int]) -> dict[int, str]:
        """Positions of a definition's type-parameter ``[`` and a function's
        parameter ``(``: ``def f[T](x)``, ``class C[T](Base)``, ``type X[T]``."""
        kinds: dict[int, str] = {}
        alias = self.soft_keyword(statement[0]) == "type"
        if alias and statement[0] in self.statements:
            if len(statement) > 2 and self.is_op(statement[2], "["):
                kinds[2] = "type_params"  # ``type X[T] = ...``
        for position, index in enumerate(statement):
            word = self.keyword(index)
            if word not in ("def", "class"):
                continue
            after = position + 2  # the token after the name
            if after < len(statement) and self.is_op(statement[after], "["):
                kinds[after] = "type_params"
                after = self.closing(statement, after) + 1
            if word == "def" and after < len(statement):
                if self.is_op(statement[after], "("):
                    kinds[after] = "params"
        return kinds

    def closing(self, statement: list[int], opening: int) -> int:
        level = 0
        for position in range(opening, len(statement)):
            if self.is_op(statement[position], *_OPENERS):
                level += 1
            elif self.is_op(statement[position], *_CLOSERS):
                level -= 1
                if level == 0:
                    return position
        return len(statement) - 1

    def expressions(self, statement: list[int]) -> None:
        """Positions any statement can hold: attributes, keyword arguments,
        definitions and their parameters, lambda parameters, ``for`` and
        ``as`` targets, and ``:=``."""
        special = self.special_brackets(statement)
        brackets: list[str] = []  # "call", "params", "type_params" or "other"
        lambdas: list[int] = []  # the bracket depth of each open lambda header
        for position, index in enumerate(statement):
            token = self.tokens[index]
            previous = statement[position - 1] if position else None
            following = self.at(statement, position + 1)
            depth = len(brackets)

            if token.type == tokenize.OP:
                if token.string in _OPENERS:
                    kind = special.get(position)
                    if kind is None:
                        kind = "call" if token.string == "(" else "other"
                    brackets.append(kind)
                elif token.string in _CLOSERS:
                    if brackets:
                        brackets.pop()
                elif token.string == ":" and lambdas and lambdas[-1] == depth:
                    lambdas.pop()
                continue

            if token.type != tokenize.NAME:
                continue

            word = self.keyword(index)
            if word is not None:
                if word in ("def", "class") and self.is_name(following):
                    assert following is not None
                    self.bind(following)
                elif word == "lambda":
                    lambdas.append(depth)
                elif word == "for":
                    self.for_targets(statement, position + 1, depth)
                elif word == "as":
                    self.as_targets(statement, position + 1)
                if self.is_op(previous, ".") and word != "import":
                    self.candidates[index] = ATTRIBUTE
                continue

            if self.is_op(previous, "."):
                self.candidates[index] = ATTRIBUTE
                continue
            if self.is_op(following, ":="):
                self.bind(index)
                continue

            after_lambda = previous is not None and self.keyword(previous) == "lambda"
            opens_item = after_lambda or self.is_op(previous, "(", "[", ",", "*", "**")
            innermost = brackets[-1] if brackets else None
            if lambdas and lambdas[-1] == depth:
                if opens_item:
                    self.bind(index)
            elif innermost in ("params", "type_params"):
                if opens_item:
                    self.bind(index)
            elif (
                innermost == "call"
                and self.is_op(previous, "(", ",")
                and self.is_op(following, "=")
            ):
                self.candidates[index] = KEYWORD_ARGUMENT

    def for_targets(self, statement: list[int], start: int, depth: int) -> None:
        """``for a, b in``: the targets run to the ``in`` at the same depth."""
        level = depth
        end = start
        while end < len(statement):
            index = statement[end]
            if self.is_op(index, *_OPENERS):
                level += 1
            elif self.is_op(index, *_CLOSERS):
                level -= 1
                if level < depth:
                    break
            elif level == depth and self.keyword(index) == "in":
                break
            end += 1
        self.targets(statement[start:end])

    def as_targets(self, statement: list[int], start: int) -> None:
        """``with x as a``, ``except E as a``, ``with x as (a, b)``."""
        if start >= len(statement):
            return
        first = statement[start]
        if self.is_name(first):
            following = statement[start + 1] if start + 1 < len(statement) else None
            if not self.is_op(following, ".", "[", "("):
                self.bind(first)
        elif self.is_op(first, "(", "["):
            self.targets(statement[start : self.closing(statement, start) + 1])
