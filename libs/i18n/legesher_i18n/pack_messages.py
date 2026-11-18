"""Format rules for the ``messages`` section of a language pack (CORE-2630).

A pack version file may carry localized error messages, nested by
implementation and keyed by the stable catalog key::

    messages:
      cpython:
        NameError.not_defined:
          text: "el nombre '{name}' no está definido"
          src: 998720c0a4af

``text`` is the localized template. ``src`` is a fingerprint of the English
template the text translates, so a translation is never attached to an
English wording it was not written for. The English side of the catalog
(key, English template, matcher, placeholders, version tiers) is not pack
data; it stays in this package.

This module holds the STRUCTURAL rules, the ones the pack schema applies when
a pack loads. A violation here fails the load, like any other malformed
section. Everything about what an entry means (does ``src`` match, do the
placeholders agree, is the key known) is decided where the catalog is joined,
and a failing entry there is skipped without failing the pack: one bad
message must not take a pack's keywords and exception names down with it.
An entry may therefore carry fields this module does not name.
"""

from __future__ import annotations

import re
import reprlib
from typing import Any

from .script_policy import BIDI_CONTROLS

__all__ = [
    "FORBIDDEN_BIDI",
    "MESSAGES_SECTION",
    "MESSAGE_IMPLEMENTATION_PATTERN",
    "MESSAGE_KEY_PATTERN",
    "MESSAGE_SRC_PATTERN",
    "bidi_controls",
    "messages_structure_errors",
]

#: The pack's top-level key.
MESSAGES_SECTION = "messages"

#: An implementation name: ``cpython``, ``v8``. Compared with ``fullmatch``.
MESSAGE_IMPLEMENTATION_PATTERN = re.compile(r"[a-z0-9]+")

#: A catalog key: ``traceback.frame``, ``NameError.not_defined``. The renderer
#: routes on the part before the first dot, so a key always has one.
MESSAGE_KEY_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+")

#: A source fingerprint: twelve lowercase hex digits.
MESSAGE_SRC_PATTERN = re.compile(r"[0-9a-f]{12}")

#: Codepoints a STORED message template may not carry. Isolating an
#: interpolated value is a render-time concern; stored strings stay clean and
#: reviewable. The same twelve the pack auditor forbids in an identifier.
FORBIDDEN_BIDI = frozenset(ord(ch) for ch in BIDI_CONTROLS)


#: Bounded repr for values quoted in an error. A pack value can be built from
#: YAML aliases into something very large; an error must never echo all of it.
_SHORT = reprlib.Repr()
_SHORT.maxstring = 60
_SHORT.maxother = 60
_SHORT.maxlevel = 2
_SHORT.maxlist = _SHORT.maxtuple = _SHORT.maxdict = _SHORT.maxset = 3


def _short(value: Any) -> str:
    """A repr of ``value`` short enough to put in an error message."""
    return _SHORT.repr(value)


def bidi_controls(text: str) -> list[str]:
    """The forbidden bidi control codepoints ``text`` carries, as U+ labels."""
    return [f"U+{ord(ch):04X}" for ch in text if ord(ch) in FORBIDDEN_BIDI]


def messages_structure_errors(messages: Any) -> list[str]:
    """Every structural problem in a pack's ``messages`` section.

    Checks shape only: a mapping of implementation to a mapping of key to
    entry, name patterns, a string ``text`` free of bidi controls and a
    well-formed string ``src``. Fields beyond ``text`` and ``src`` are not
    examined here.

    Args:
        messages: The section as parsed from YAML.

    Returns:
        One line per problem, each naming the path of the offending value.
        Empty when the section is well formed.
    """
    if not isinstance(messages, dict):
        return [f"messages: must be a mapping, got {type(messages).__name__}"]

    errors: list[str] = []
    for implementation, entries in messages.items():
        where = f"messages.{implementation}"
        if not isinstance(
            implementation, str
        ) or not MESSAGE_IMPLEMENTATION_PATTERN.fullmatch(implementation):
            errors.append(
                f"messages: implementation name {_short(implementation)} must be "
                "lowercase letters and digits"
            )
            continue
        if not isinstance(entries, dict):
            errors.append(
                f"{where}: must be a mapping of message key to entry, "
                f"got {type(entries).__name__}"
            )
            continue
        for key, entry in entries.items():
            path = f"{where}.{key}"
            if not isinstance(key, str) or not MESSAGE_KEY_PATTERN.fullmatch(key):
                errors.append(
                    f"{where}: message key {_short(key)} is not a catalog key "
                    "(for example 'NameError.not_defined')"
                )
                continue
            if not isinstance(entry, dict):
                errors.append(
                    f"{path}: must be a mapping with 'text' and 'src', "
                    f"got {type(entry).__name__}"
                )
                continue
            text = entry.get("text")
            if not isinstance(text, str):
                errors.append(
                    f"{path}: 'text' must be a string, got {type(text).__name__}"
                )
            else:
                controls = bidi_controls(text)
                if controls:
                    errors.append(
                        f"{path}: 'text' carries bidi control characters "
                        f"{controls}; a stored template must not"
                    )
            src = entry.get("src")
            if not isinstance(src, str) or not MESSAGE_SRC_PATTERN.fullmatch(src):
                errors.append(
                    f"{path}: 'src' must be twelve lowercase hex digits, "
                    f"got {_short(src)}"
                )
    return errors
