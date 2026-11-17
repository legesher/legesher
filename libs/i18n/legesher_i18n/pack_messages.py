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

This module holds both sets of rules for an entry.

The STRUCTURAL rules (:func:`messages_structure_errors`) are the ones the pack
schema applies when a pack loads. A violation there fails the load, like any
other malformed section.

The JOIN rules (:func:`entry_problem`) decide whether an entry may be used for
one English template: is it only the fields this release knows, does ``src``
match, do the placeholders agree. They are applied where the catalog is
joined (:func:`legesher_i18n.messages.load_catalog`), and a failing entry
there is skipped without failing the pack: one bad message must not take a
pack's keywords and exception names down with it. The message then prints as
the interpreter printed it.
"""

from __future__ import annotations

import hashlib
import re
import reprlib
import unicodedata
from collections.abc import Collection
from typing import Any

from .script_policy import BIDI_CONTROLS

__all__ = [
    "ALLOWED_STATUSES",
    "DEFAULT_STATUS",
    "ENTRY_FIELDS",
    "FORBIDDEN_BIDI",
    "IMPLEMENTATION_TARGETS",
    "MESSAGES_SECTION",
    "MESSAGE_IMPLEMENTATION_PATTERN",
    "MESSAGE_KEY_PATTERN",
    "MESSAGE_SRC_PATTERN",
    "PLACEHOLDER",
    "PLACEHOLDER_KINDS",
    "bidi_controls",
    "entry_problem",
    "message_fingerprint",
    "messages_structure_errors",
    "used_placeholders",
]

#: The pack's top-level key.
MESSAGES_SECTION = "messages"

#: The pack target that carries each implementation's messages. An
#: implementation with no entry here has no pack to read or write, and with
#: no translations database the catalog reads no translations for it.
IMPLEMENTATION_TARGETS: dict[str, str] = {"cpython": "python"}

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


#: A ``{name}`` placeholder. A template may carry other braces (CPython's
#: "f-string: valid expression required before '}'"), which is why templates
#: are never read with ``str.format``.
PLACEHOLDER = re.compile(r"\{(\w+)\}")

#: The review rungs a translation may carry: the ``message_translations.status``
#: CHECK set.
ALLOWED_STATUSES = ("machine", "experimental", "reviewed", "official")

#: The rung of an entry that states none.
DEFAULT_STATUS = "machine"

#: Every field an entry may carry on this release. An entry with any other
#: field is not used: a field added by a later release may change what the
#: text means (plural forms, for one), and a reader that does not know it
#: must not guess.
ENTRY_FIELDS = frozenset({"text", "src", "status"})

#: What a placeholder's value is, when that matters to a renderer: a line
#: number or a count. Declared on the English side only. A placeholder with
#: no kind is copied verbatim.
PLACEHOLDER_KINDS = ("line", "count")


def used_placeholders(template: str) -> set[str]:
    """Placeholder names a template interpolates, ignoring ``{{ }}`` escapes."""
    stripped = template.replace("{{", "").replace("}}", "")
    return set(PLACEHOLDER.findall(stripped))


def message_fingerprint(template_en: str) -> str:
    """The ``src`` value for an English template.

    The first twelve hex digits of the SHA-256 of the NFC-normalized
    template, encoded as UTF-8. The matcher is deliberately not part of it:
    a fix to how a message is recognized keeps every translation of its
    wording valid.
    """
    normalized = unicodedata.normalize("NFC", template_en)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]


def entry_problem(
    entry: Any, *, template_en: str, placeholders: Collection[str]
) -> str | None:
    """Why ``entry`` cannot be used for one English template, or ``None``.

    The rules, in order:

    1. The entry is a mapping carrying only :data:`ENTRY_FIELDS`, with a
       string ``text`` free of control characters (category ``Cc``, such as
       NUL or the ESC that starts a terminal escape sequence), of line and
       paragraph separators (U+2028, U+2029) and of lone surrogates, a
       well-formed ``src`` and, when present, a ``status`` from
       :data:`ALLOWED_STATUSES`. The text is written to a terminal.
    2. ``src`` is the fingerprint of ``template_en``. A translation written
       for another wording of the same key (an earlier Python version's, or
       one since corrected) is not used.
    3. The placeholders in ``text`` are exactly ``placeholders``.
    4. ``text`` is empty only when ``template_en`` is.

    Args:
        entry: One pack entry, as loaded.
        template_en: The English template that applies to the running
            interpreter for the entry's key.
        placeholders: The placeholder names that template declares.

    Returns:
        A one-line reason, or ``None`` when the entry is usable.
    """
    if not isinstance(entry, dict):
        return f"entry is not a mapping ({type(entry).__name__})"
    unknown = sorted(_short(name) for name in set(entry) - ENTRY_FIELDS)
    if unknown:
        return f"fields this release does not know: {', '.join(unknown[:5])}"
    text = entry.get("text")
    if not isinstance(text, str):
        return "'text' is not a string"
    controls = [
        f"U+{ord(ch):04X}"
        for ch in text
        if unicodedata.category(ch) in ("Cc", "Cs", "Zl", "Zp")
    ]
    if controls:
        return f"'text' carries control characters {_short(controls)}"
    src = entry.get("src")
    if not isinstance(src, str) or not MESSAGE_SRC_PATTERN.fullmatch(src):
        return "'src' is not twelve lowercase hex digits"
    if "status" in entry and entry["status"] not in ALLOWED_STATUSES:
        return (
            f"status {_short(entry['status'])} is not one of {list(ALLOWED_STATUSES)}"
        )
    expected = message_fingerprint(template_en)
    if src != expected:
        return (
            f"src {src} does not match the English template (expected {expected}); "
            "the translation was written for another wording"
        )
    used = used_placeholders(text)
    if used != set(placeholders):
        return (
            f"placeholders {_short(sorted(used))} != declared "
            f"{_short(sorted(placeholders))}"
        )
    if text == "" and template_en != "":
        return "empty text for a template that is not empty"
    return None


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
