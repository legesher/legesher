"""Canonical inventory for the pack vocabulary partition (CORE-1396).

Two kinds of knowledge that are **vocabulary, not rules**, and therefore
belong in the language packs rather than in ``style-guides/{lang}.yml``:

* **Symbol vocabulary** — what a Python symbol is *called* in the target
  language. ``_`` is "underscore" in English, "guion bajo" in Spanish,
  "شرطة سفلية" in Arabic. Teaching text and error messages need the name;
  no rule can derive it.
* **Common variable conventions** — the short names a programmer writing
  that language reaches for by habit: the loop counter, the index, the
  throwaway, the coordinate pair. Idiom, not grammar.

Both are *per language*, both are *lookup tables*, and neither is
reverse-engineerable from a style guide's rules — which is exactly the
line the style guides already draw ("Guides are rules, not vocabulary…
symbol names, and idiomatic variable names live in the language packs").
This module is the pack side of that sentence.

Why a Python module and not a YAML/JSON seed
--------------------------------------------
The same reason the term inventory lives in :mod:`term_definitions`: the
*canonical* side of a vocabulary entry (its slug, its glyph, its English
name, what it does) is invariant across every language and must never
drift between the database, the exporter and the generation prompt.
Every consumer reads it from here, so there is one place to change and
nothing to keep in sync. Only the *localized* side — one string per
(entry, language) — is data, and that lives in the database.

Slugs, not glyphs, are the pack keys
------------------------------------
``symbols`` maps a stable ASCII slug (``colon``) to the localized name,
not the raw glyph (``:``). Three reasons, in order of weight:

1. Not every entry has a glyph. ``indentation``, ``newline`` and
   ``space`` are symbols a learner must be able to name, and none of
   them is a printable character.
2. A glyph key would put ``:``, ``#``, ``'``, ``"`` and ``@`` on the
   left-hand side of a YAML mapping — every one of them a quoting
   hazard, and ``#`` is a comment introducer.
3. The glyph is canonical data, identical in every language, so shipping
   it in every pack would be one copy of a constant per pack. Consumers read it
   from :data:`SYMBOLS` here and join on the slug.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "SYMBOLS",
    "VARIABLE_CONVENTIONS",
    "VOCABULARY_SECTIONS",
    "SymbolDefinition",
    "VariableConvention",
    "english_values",
    "inventory_for_section",
    "slugs_for_section",
]

#: The pack sections this partition owns, in emitted file order.
VOCABULARY_SECTIONS: tuple[str, str] = ("symbols", "variable_conventions")


@dataclass(frozen=True)
class SymbolDefinition:
    """One symbol a learner needs to be able to *name*.

    Attributes:
        slug: Stable ASCII key; the pack-section key and the DB entry key.
        glyph: The character(s), or ``None`` for a symbol with no printable
            form (indentation, a line break, a space).
        english_name: The canonical English name — also the ``en`` pack's
            value, so English is seeded rather than generated.
        role: What the symbol does in Python. Prompt context only; never
            shipped in a pack.
    """

    slug: str
    glyph: str | None
    english_name: str
    role: str


@dataclass(frozen=True)
class VariableConvention:
    """One idiomatic short name, described by the ROLE it fills.

    The key is the role (``loop_index``), never the English spelling, so a
    language whose habit differs from English's has somewhere to put it.
    ``english_value`` is what an English-speaking Python programmer writes
    for that role, and is the ``en`` pack's value.

    Attributes:
        slug: Stable ASCII key naming the role.
        english_value: The English idiom (``i`` for the loop counter).
        role: What the name is for. Prompt context only.
    """

    slug: str
    english_value: str
    role: str


# ---------------------------------------------------------------------------
# Symbol vocabulary
# ---------------------------------------------------------------------------
# Scope rule: a symbol earns a row when a beginner has to *say it out loud*
# to be taught Python, or when an error message has to name it ("expected
# a colon"). Operators that are read as words in every language ("plus",
# "minus") are in; operators a learner meets only in specialist code
# (bitwise ~, ^) are out — they can be added later without a schema change,
# which is the whole point of keeping the inventory in one list.
SYMBOLS: tuple[SymbolDefinition, ...] = (
    SymbolDefinition(
        "underscore",
        "_",
        "underscore",
        "Joins words inside an identifier (snake_case); alone, marks a value "
        "the code deliberately ignores.",
    ),
    SymbolDefinition(
        "colon",
        ":",
        "colon",
        "Opens the indented block of a def, class, if, for, while or with "
        "statement; also separates key from value in a dict.",
    ),
    SymbolDefinition(
        "comma", ",", "comma", "Separates items in a list, tuple, or argument list."
    ),
    SymbolDefinition(
        "period",
        ".",
        "period",
        "Attribute access: reaches inside an object for one of its members.",
    ),
    SymbolDefinition(
        "paren_open",
        "(",
        "opening parenthesis",
        "Opens a call's argument list, a tuple, or a grouped expression.",
    ),
    SymbolDefinition(
        "paren_close",
        ")",
        "closing parenthesis",
        "Closes a call's argument list, a tuple, or a grouped expression.",
    ),
    SymbolDefinition(
        "bracket_open",
        "[",
        "opening square bracket",
        "Opens a list literal, an index, or a slice.",
    ),
    SymbolDefinition(
        "bracket_close",
        "]",
        "closing square bracket",
        "Closes a list literal, an index, or a slice.",
    ),
    SymbolDefinition(
        "brace_open",
        "{",
        "opening curly brace",
        "Opens a dict or set literal, or a format-string placeholder.",
    ),
    SymbolDefinition(
        "brace_close",
        "}",
        "closing curly brace",
        "Closes a dict or set literal, or a format-string placeholder.",
    ),
    SymbolDefinition(
        "equals", "=", "equals sign", "Assignment: binds a value to a name."
    ),
    SymbolDefinition(
        "double_equals",
        "==",
        "double equals sign",
        "Equality comparison — distinct from assignment, and the single most "
        "common beginner confusion.",
    ),
    SymbolDefinition(
        "asterisk",
        "*",
        "asterisk",
        "Multiplication; also unpacks an iterable into positional arguments.",
    ),
    SymbolDefinition(
        "double_asterisk",
        "**",
        "double asterisk",
        "Exponentiation; also unpacks a mapping into keyword arguments.",
    ),
    SymbolDefinition("plus", "+", "plus sign", "Addition, and string concatenation."),
    SymbolDefinition("minus", "-", "minus sign", "Subtraction, and numeric negation."),
    SymbolDefinition("slash", "/", "forward slash", "Division, producing a float."),
    SymbolDefinition(
        "percent",
        "%",
        "percent sign",
        "Remainder after division (modulo); also old-style string formatting.",
    ),
    SymbolDefinition(
        "backslash",
        "\\",
        "backslash",
        "Starts an escape sequence inside a string; at end of line, continues "
        "a statement onto the next line.",
    ),
    SymbolDefinition(
        "hash",
        "#",
        "hash sign",
        "Starts a comment: the rest of the line is for humans, not Python.",
    ),
    SymbolDefinition(
        "single_quote",
        "'",
        "single quotation mark",
        "Delimits a string literal.",
    ),
    SymbolDefinition(
        "double_quote",
        '"',
        "double quotation mark",
        "Delimits a string literal.",
    ),
    SymbolDefinition(
        "triple_quote",
        '"""',
        "triple quotation mark",
        "Delimits a string that may span several lines — the docstring form.",
    ),
    SymbolDefinition(
        "arrow",
        "->",
        "arrow",
        "Introduces a function's return-type annotation.",
    ),
    SymbolDefinition(
        "at_sign",
        "@",
        "at sign",
        "Applies a decorator to the function or class defined below it.",
    ),
    SymbolDefinition(
        "semicolon",
        ";",
        "semicolon",
        "Separates two statements written on one line — legal, and against "
        "house style.",
    ),
    SymbolDefinition(
        "pipe",
        "|",
        "vertical bar",
        "Union of two types in an annotation; also set union and bitwise or.",
    ),
    SymbolDefinition(
        "less_than", "<", "less-than sign", "Ordering comparison: strictly smaller."
    ),
    SymbolDefinition(
        "greater_than",
        ">",
        "greater-than sign",
        "Ordering comparison: strictly larger.",
    ),
    SymbolDefinition(
        "ellipsis",
        "...",
        "ellipsis",
        "The Ellipsis literal — a placeholder body, and a slice in array code.",
    ),
    SymbolDefinition(
        "indentation",
        None,
        "indentation",
        "The leading whitespace that makes a block a block. Python's only "
        "grouping construct, so it has to be nameable.",
    ),
    SymbolDefinition(
        "newline",
        None,
        "line break",
        "Ends a statement. Named by error messages far more often than "
        "learners expect.",
    ),
    SymbolDefinition(
        "space",
        None,
        "space",
        "The separator between tokens; four of them make one indentation level.",
    ),
)


# ---------------------------------------------------------------------------
# Common variable conventions
# ---------------------------------------------------------------------------
# Keyed by ROLE, so a language is free to disagree with English. Several
# languages will legitimately keep `i` — it descends from mathematical
# notation, not from English — and that is a finding, not a failure: the
# point of asking is to find out which roles a language DOES rename.
#
# Every ``english_value`` here is a valid Python identifier and they are
# pairwise distinct, so the seeded `en` pack passes its own gate.
VARIABLE_CONVENTIONS: tuple[VariableConvention, ...] = (
    VariableConvention(
        "loop_index", "i", "The counter of the outermost loop over a range."
    ),
    VariableConvention(
        "nested_loop_index", "j", "The counter of a loop nested inside the first."
    ),
    VariableConvention(
        "inner_loop_index", "k", "The counter of a loop nested two deep."
    ),
    VariableConvention("count", "n", "A count of things, or the size of a collection."),
    VariableConvention(
        "index", "idx", "A position within a sequence, when 'i' would be unclear."
    ),
    VariableConvention(
        "coordinate_x",
        "x",
        "The horizontal coordinate, or a generic first value of a pair.",
    ),
    VariableConvention(
        "coordinate_y",
        "y",
        "The vertical coordinate, or a generic second value of a pair.",
    ),
    VariableConvention(
        "temporary", "tmp", "A short-lived value held only to be used a line later."
    ),
    VariableConvention(
        "accumulator", "total", "The running sum or tally a loop builds up."
    ),
    VariableConvention(
        "throwaway",
        "_",
        "A value the code is required to receive but deliberately ignores.",
    ),
    VariableConvention(
        "exception_alias", "e", "The exception bound by 'except SomeError as ...'."
    ),
    VariableConvention(
        "file_handle", "f", "An open file, usually inside a with block."
    ),
    VariableConvention(
        "item", "item", "The current element of a collection being iterated."
    ),
    VariableConvention("key", "key", "The key half of a key/value pair."),
    VariableConvention("value", "val", "The value half of a key/value pair."),
)


_BY_SECTION: dict[
    str, tuple[SymbolDefinition, ...] | tuple[VariableConvention, ...]
] = {
    "symbols": SYMBOLS,
    "variable_conventions": VARIABLE_CONVENTIONS,
}


def inventory_for_section(
    section: str,
) -> tuple[SymbolDefinition, ...] | tuple[VariableConvention, ...]:
    """The canonical entries of *section*, in inventory order.

    Raises:
        KeyError: If *section* is not one of :data:`VOCABULARY_SECTIONS`.
    """
    try:
        return _BY_SECTION[section]
    except KeyError:
        raise KeyError(
            f"Unknown vocabulary section '{section}'; expected one of "
            f"{list(VOCABULARY_SECTIONS)}."
        ) from None


def slugs_for_section(section: str) -> tuple[str, ...]:
    """The slugs of *section*, in inventory order."""
    return tuple(entry.slug for entry in inventory_for_section(section))


def english_values(section: str) -> dict[str, str]:
    """The canonical English value per slug — the seeded ``en`` pack content.

    English is *seeded*, never generated: for ``symbols`` the value is the
    English name the rest of this module already states, and for
    ``variable_conventions`` it is the English idiom. Sending either to a
    model would be asking it to reproduce a constant.
    """
    if section == "symbols":
        return {entry.slug: entry.english_name for entry in SYMBOLS}
    if section == "variable_conventions":
        return {entry.slug: entry.english_value for entry in VARIABLE_CONVENTIONS}
    raise KeyError(
        f"Unknown vocabulary section '{section}'; expected one of "
        f"{list(VOCABULARY_SECTIONS)}."
    )
