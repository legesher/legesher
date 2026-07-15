"""BCP 47 locale-tag parsing, validation, canonicalization, and fallback.

CORE-1500. Legesher keys languages by a bare ISO 639-1 code (``ar``, ``zh``,
``no``). That key cannot express three things the roadmap needs:

* **Script.** ``zh`` alone does not say Simplified or Traditional; ``sr`` does
  not say Cyrillic or Latin. The packs *are* one or the other.
* **Languages with no 2-letter code.** Dinka is ISO 639-3 ``din`` only. The
  103-language target includes it, so a 2-char key cannot represent the roadmap.
* **Regional variants.** ``pt`` cannot coexist with a future ``pt-BR``.

BCP 47 (RFC 5646) is the standard that solves all three, and it is what every
consumer of Legesher already speaks (HTML ``lang``, VS Code, HTTP
``Accept-Language``, CLDR/ICU, PyPI ``Natural Language`` classifiers).

This module is the single source of truth for *what a valid Legesher locale tag
is*. It validates against a vendored snapshot of the IANA Language Subtag
Registry — the normative subtag list behind RFC 5646 — so validation is offline
and deterministic (see ``scripts/refresh_iana_subtags.py``).

What "valid" means here
-----------------------
Three progressively stricter questions, exposed as three functions:

1. :func:`parse` — is the tag *well-formed*? (Does it match the RFC 5646
   grammar: ``language[-script][-region][-variant...]``.)
2. :func:`validate` — is it *valid*? (Well-formed, **and** every subtag exists
   in the registry, **and** no subtag is deprecated.)
3. :func:`check_canonical` — is it *canonical*? (Valid, **and** correctly cased,
   **and** carrying no script subtag the registry says to suppress.)

A tag can be well-formed but invalid (``xx-Zzzz``: right shape, no such
subtags), and valid but non-canonical (``ar-Arab``: every subtag is real, but
the registry's ``Suppress-Script: Arab`` on ``ar`` says the script is redundant).
Legesher's *keys* must be canonical; Legesher's *inputs* (a user's
``Accept-Language``) need only be well-formed.

Deliberate restriction
----------------------
RFC 5646 also permits extensions (``-u-``, ``-t-``), private use (``-x-``), and
extlangs (``zh-cmn``). Legesher locale *keys* accept none of them: they carry no
meaning for a language pack, extlang is deprecated in practice, and each is a
second way to spell the same locale — exactly the ambiguity a primary key must
not have. :func:`parse` rejects them with a clear message rather than silently
dropping them.

Example:
    >>> parse("zh-Hans")
    LocaleTag(language='zh', script='Hans', region=None, variants=())
    >>> validate("ar-Arab")   # valid, but not canonical
    []
    >>> check_canonical("ar-Arab")[0].code
    'suppress-script'
    >>> canonicalize("ZH-hans")
    'zh-Hans'
    >>> fallback_chain("pt-BR")
    ['pt-BR', 'pt']
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

__all__ = [
    "REGISTRY_PATH",
    "Issue",
    "InvalidLocaleTagError",
    "LocaleTag",
    "canonicalize",
    "check_canonical",
    "fallback_chain",
    "is_canonical",
    "is_macrolanguage",
    "is_valid",
    "parse",
    "registry_file_date",
    "suppressed_script",
    "validate",
]

REGISTRY_PATH = Path(__file__).parent / "data" / "iana-language-subtag-registry.tsv"

# RFC 5646 section 2.1 ABNF, narrowed to the shape Legesher accepts as a key:
#   langtag = language ["-" script] ["-" region] *("-" variant)
# language: 2-3 alpha (ISO 639-1/-3). RFC 5646 also allows 4 (reserved) and 5-8
# (registered); none exist in the registry today. The two absent shapes fail
# differently, on purpose: 4-alpha is "reserved for future use" (section 2.2.1)
# — no such subtag CAN be registered under the current RFC, so it is rejected as
# malformed — while 5-8 alpha is registrable, so it parses and then fails with
# "unknown subtag", the error that would become "valid" if IANA ever registers one.
_LANGUAGE_RE = re.compile(r"^[A-Za-z]{2,3}$|^[A-Za-z]{5,8}$")
_SCRIPT_RE = re.compile(r"^[A-Za-z]{4}$")
_REGION_RE = re.compile(r"^[A-Za-z]{2}$|^[0-9]{3}$")
_VARIANT_RE = re.compile(r"^[0-9][A-Za-z0-9]{3}$|^[A-Za-z0-9]{5,8}$")

_SINGLETON_RE = re.compile(r"^[A-WYZa-wyz0-9]$")  # extension singleton (not 'x')


class InvalidLocaleTagError(ValueError):
    """Raised when a locale tag is not well-formed under RFC 5646."""


@dataclass(frozen=True)
class Issue:
    """A single validation finding.

    Attributes:
        code: Stable machine-readable identifier (e.g. ``"deprecated"``,
            ``"suppress-script"``). Callers key on this, never on ``message``.
        message: Human-readable explanation, safe to surface in CI output.
    """

    code: str
    message: str

    def __str__(self) -> str:
        """Render as ``code: message``."""
        return f"{self.code}: {self.message}"


@dataclass(frozen=True)
class LocaleTag:
    """A parsed, well-formed BCP 47 locale tag.

    Attributes:
        language: The primary language subtag, lowercased (``"zh"``, ``"din"``).
        script: ISO 15924 script subtag in Titlecase, or ``None``.
        region: ISO 3166-1 alpha-2 (uppercased) or UN M.49 numeric, or ``None``.
        variants: Registered variant subtags, lowercased, in tag order.
    """

    language: str
    script: str | None = None
    region: str | None = None
    variants: tuple[str, ...] = ()

    def __str__(self) -> str:
        """Render the tag in canonical RFC 5646 casing."""
        parts = [self.language]
        if self.script:
            parts.append(self.script)
        if self.region:
            parts.append(self.region)
        parts.extend(self.variants)
        return "-".join(parts)


@dataclass(frozen=True)
class _SubtagRecord:
    """One row of the vendored IANA registry snapshot."""

    scope: str
    suppress_script: str
    deprecated: str
    preferred_value: str
    macrolanguage: str
    description: str


@lru_cache(maxsize=1)
def _registry() -> tuple[dict[tuple[str, str], _SubtagRecord], str]:
    """Load and index the vendored IANA registry snapshot.

    Cached: the snapshot is a static, git-tracked file, so it is parsed once per
    process. Subtag lookups are case-insensitive, so the index is keyed by
    ``(type, subtag.lower())``.

    Returns:
        Tuple of (index, ``File-Date`` of the snapshot).

    Raises:
        FileNotFoundError: If the vendored snapshot is missing. Regenerate it
            with ``scripts/refresh_iana_subtags.py``.
    """
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(
            f"vendored IANA subtag registry not found at {REGISTRY_PATH}. "
            f"Regenerate it with: uv run python "
            f"libs/i18n/legesher_i18n/scripts/refresh_iana_subtags.py"
        )

    index: dict[tuple[str, str], _SubtagRecord] = {}
    file_date = ""

    for line in REGISTRY_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            if "File-Date:" in line:
                file_date = line.split("File-Date:", 1)[1].strip()
            continue
        if not line or line.startswith("type\t"):
            continue

        fields = line.split("\t")
        # Trailing empty cells may be stripped by editors; pad to full width.
        fields += [""] * (8 - len(fields))
        record_type, subtag = fields[0], fields[1]
        index[(record_type, subtag.lower())] = _SubtagRecord(
            scope=fields[2],
            suppress_script=fields[3],
            deprecated=fields[4],
            preferred_value=fields[5],
            macrolanguage=fields[6],
            description=fields[7],
        )

    return index, file_date


def registry_file_date() -> str:
    """Return the ``File-Date`` of the vendored IANA registry snapshot."""
    return _registry()[1]


def _lookup(record_type: str, subtag: str) -> _SubtagRecord | None:
    """Look up one subtag in the registry index (case-insensitive)."""
    return _registry()[0].get((record_type, subtag.lower()))


def parse(tag: str) -> LocaleTag:
    """Parse a locale tag and check it is well-formed.

    Well-formedness is purely structural — it asks whether the tag matches the
    RFC 5646 grammar, not whether its subtags exist. Positional: a 4-alpha
    subtag in the second position is a script, a 2-alpha subtag there is a
    region, and so on. Casing is normalized on the way out, so ``ZH-hans`` and
    ``zh-Hans`` parse to the same :class:`LocaleTag`.

    Args:
        tag: The candidate tag, e.g. ``"zh-Hans"`` or ``"pt-BR"``.

    Returns:
        The parsed tag with canonical casing.

    Raises:
        InvalidLocaleTagError: If the tag is empty, malformed, or uses a
            construct Legesher excludes from its key domain (extension,
            private-use, or extlang subtags).
    """
    if not tag or not tag.strip():
        raise InvalidLocaleTagError("locale tag is empty")
    if tag != tag.strip():
        raise InvalidLocaleTagError(f"{tag!r} has leading or trailing whitespace")

    subtags = tag.split("-")
    if any(not subtag for subtag in subtags):
        raise InvalidLocaleTagError(
            f"{tag!r} has an empty subtag (leading, trailing, or doubled '-')"
        )

    for subtag in subtags:
        if subtag.lower() == "x":
            raise InvalidLocaleTagError(
                f"{tag!r} uses a private-use subtag ('-x-'); Legesher locale keys "
                f"must be publicly interpretable"
            )
        if len(subtag) == 1 and _SINGLETON_RE.match(subtag):
            raise InvalidLocaleTagError(
                f"{tag!r} uses a BCP 47 extension ('-{subtag.lower()}-'); extensions "
                f"carry no pack meaning and are not accepted in Legesher locale keys"
            )

    language, *rest = subtags
    if not _LANGUAGE_RE.match(language):
        raise InvalidLocaleTagError(
            f"{tag!r}: {language!r} is not a well-formed primary language subtag "
            f"(expected 2-3 letters, e.g. 'zh' or 'din')"
        )
    language = language.lower()

    # An extlang is a 3-alpha subtag immediately after a 2-alpha language
    # (e.g. 'zh-cmn'). It is structurally indistinguishable from nothing else in
    # that position, so it is detectable — and rejected, per the module docstring.
    if rest and len(language) == 2 and len(rest[0]) == 3 and rest[0].isalpha():
        raise InvalidLocaleTagError(
            f"{tag!r} uses an extlang subtag ({rest[0]!r}); use the extlang's own "
            f"primary subtag instead (e.g. 'cmn', not 'zh-cmn')"
        )

    script: str | None = None
    region: str | None = None
    variants: list[str] = []

    position = 0
    if position < len(rest) and _SCRIPT_RE.match(rest[position]):
        script = rest[position].capitalize()
        position += 1
    if position < len(rest) and _REGION_RE.match(rest[position]):
        region = rest[position].upper()
        position += 1
    while position < len(rest):
        subtag = rest[position]
        if not _VARIANT_RE.match(subtag):
            raise InvalidLocaleTagError(
                f"{tag!r}: {subtag!r} is not a well-formed subtag in this position "
                f"(expected a variant: 5-8 alphanumerics, or 4 starting with a digit)"
            )
        variants.append(subtag.lower())
        position += 1

    if len(set(variants)) != len(variants):
        raise InvalidLocaleTagError(f"{tag!r} repeats a variant subtag")

    return LocaleTag(
        language=language, script=script, region=region, variants=tuple(variants)
    )


def suppressed_script(language: str) -> str | None:
    """Return the script the registry suppresses for *language*, if any.

    ``Suppress-Script`` is the registry's own answer to "does this language have
    a default script?". It is a positive instruction: RFC 5646 section 4.1 says a
    tag SHOULD NOT carry a script subtag when the registry suppresses it, because
    the script adds nothing (``ar`` already implies Arabic). Its *absence* is not
    an instruction to add one — most languages with no ``Suppress-Script`` (Irish
    Gaelic, Sundanese) still take no script subtag; only those with a live script
    contrast do (``sr``, ``uz``, ``zh``, ``mn``).

    Args:
        language: A primary language subtag, e.g. ``"ar"``.

    Returns:
        The suppressed script subtag (``"Arab"``), or ``None`` if the language
        has no suppressed script or is not in the registry.
    """
    record = _lookup("language", language)
    return record.suppress_script or None if record else None


def is_macrolanguage(language: str) -> bool:
    """Return True if *language* is a registry macrolanguage.

    A macrolanguage subtag stands for a cluster of individual languages: ``ar``
    covers Egyptian, Levantine, and Standard Arabic; ``zh`` covers Mandarin,
    Cantonese, and Wu. RFC 5646 permits macrolanguage tags, and using them is
    normal practice (CLDR keys Arabic as ``ar``, not ``arb``) — this predicate
    exists to *surface* the cases for review, not to reject them.

    Args:
        language: A primary language subtag, e.g. ``"zh"``.

    Returns:
        True if the registry gives the subtag ``Scope: macrolanguage``.
    """
    record = _lookup("language", language)
    return record is not None and record.scope == "macrolanguage"


def validate(tag: str) -> list[Issue]:
    """Validate a tag: well-formed, all subtags registered, none deprecated.

    This is the gate for *accepting* a tag. It does not require canonical form —
    ``ar-Arab`` passes here (its subtags are all real) and is only flagged by
    :func:`check_canonical`.

    Args:
        tag: The candidate tag.

    Returns:
        A list of :class:`Issue`. Empty means valid.

    Raises:
        InvalidLocaleTagError: If the tag is not even well-formed. A malformed
            tag has no subtags worth reporting on individually, so this is an
            exception rather than an issue.
    """
    parsed = parse(tag)
    issues: list[Issue] = []

    checks = [("language", parsed.language)]
    if parsed.script:
        checks.append(("script", parsed.script))
    if parsed.region:
        checks.append(("region", parsed.region))
    checks.extend(("variant", variant) for variant in parsed.variants)

    for record_type, subtag in checks:
        record = _lookup(record_type, subtag)
        if record is None:
            issues.append(
                Issue(
                    "unknown-subtag",
                    f"{subtag!r} is not a registered {record_type} subtag in the "
                    f"IANA registry (snapshot {registry_file_date()})",
                )
            )
            continue
        if record.deprecated:
            preferred = (
                f"; use {record.preferred_value!r} instead"
                if record.preferred_value
                else ""
            )
            issues.append(
                Issue(
                    "deprecated",
                    f"{record_type} subtag {subtag!r} was deprecated on "
                    f"{record.deprecated}{preferred}",
                )
            )

    return issues


def check_canonical(tag: str) -> list[Issue]:
    """Check a tag is in Legesher's canonical form.

    Canonical means :func:`validate` passes *and*:

    * casing is ``language-Script-REGION-variant`` (RFC 5646 section 2.1.1);
    * no script subtag that the registry suppresses for that language
      (``ar-Arab`` -> ``ar``);
    * no deprecated subtag with a registered ``Preferred-Value``.

    Note what this deliberately does **not** flag: a macrolanguage primary
    subtag. ``ar``, ``ms``, and ``zh`` are macrolanguages, and RFC 5646 permits
    them as tags — narrowing ``ar`` to ``arb`` is an editorial call about what a
    pack contains, not a standards violation, so it is not machine-checkable.

    Args:
        tag: The candidate tag.

    Returns:
        A list of :class:`Issue`. Empty means canonical.

    Raises:
        InvalidLocaleTagError: If the tag is not well-formed.
    """
    parsed = parse(tag)
    issues = validate(tag)

    if str(parsed) != tag:
        issues.append(
            Issue(
                "casing",
                f"{tag!r} is not canonically cased; write it as {str(parsed)!r} "
                f"(language lowercase, Script titlecase, REGION uppercase)",
            )
        )

    suppressed = suppressed_script(parsed.language)
    if parsed.script and suppressed and parsed.script == suppressed:
        issues.append(
            Issue(
                "suppress-script",
                f"the registry sets Suppress-Script: {suppressed} on "
                f"{parsed.language!r}, so the script subtag is redundant; "
                f"write {parsed.language!r}, not {tag!r}",
            )
        )

    return issues


def is_valid(tag: str) -> bool:
    """Return True if *tag* is well-formed and every subtag is registered and live."""
    try:
        return not validate(tag)
    except InvalidLocaleTagError:
        return False


def is_canonical(tag: str) -> bool:
    """Return True if *tag* is in Legesher's canonical form."""
    try:
        return not check_canonical(tag)
    except InvalidLocaleTagError:
        return False


def canonicalize(tag: str) -> str:
    """Rewrite a valid tag into Legesher's canonical form.

    Applies, in order: canonical casing, deprecated-subtag substitution via the
    registry's ``Preferred-Value`` (``iw`` -> ``he``, ``heploc`` -> ``alalc97``;
    ``no-bok`` is rejected upstream as malformed), and removal of a suppressed
    script subtag (``ar-Arab`` -> ``ar``). Every subtag — variants included —
    must be registered and either live or replaceable.

    It does **not** narrow macrolanguages (``zh`` stays ``zh``) and does **not**
    add a script subtag — both are editorial decisions about pack content that a
    function cannot make. :mod:`legesher_i18n.scripts.propose_bcp47_backfill`
    holds those decisions, each with its evidence.

    Args:
        tag: The tag to canonicalize.

    Returns:
        The canonical tag.

    Raises:
        InvalidLocaleTagError: If the tag is not well-formed.
        ValueError: If a subtag is unregistered, or is deprecated with no
            registered replacement — there is nothing to canonicalize *to*.
    """
    parsed = parse(tag)

    language_record = _lookup("language", parsed.language)
    if language_record is None:
        raise ValueError(
            f"{parsed.language!r} is not a registered language subtag "
            f"(snapshot {registry_file_date()})"
        )
    language = parsed.language
    if language_record.deprecated:
        if not language_record.preferred_value:
            raise ValueError(
                f"language subtag {language!r} is deprecated "
                f"({language_record.deprecated}) with no registered replacement"
            )
        language = language_record.preferred_value.lower()

    script = parsed.script
    region = parsed.region
    for record_type, value in (("script", script), ("region", region)):
        if value is None:
            continue
        record = _lookup(record_type, value)
        if record is None:
            raise ValueError(
                f"{value!r} is not a registered {record_type} subtag "
                f"(snapshot {registry_file_date()})"
            )
        if record.deprecated:
            if not record.preferred_value:
                raise ValueError(
                    f"{record_type} subtag {value!r} is deprecated "
                    f"({record.deprecated}) with no registered replacement"
                )
            if record_type == "script":
                script = record.preferred_value.capitalize()
            else:
                region = record.preferred_value.upper()

    variants: list[str] = []
    for variant in parsed.variants:
        record = _lookup("variant", variant)
        if record is None:
            raise ValueError(
                f"{variant!r} is not a registered variant subtag "
                f"(snapshot {registry_file_date()})"
            )
        if record.deprecated:
            if not record.preferred_value:
                raise ValueError(
                    f"variant subtag {variant!r} is deprecated "
                    f"({record.deprecated}) with no registered replacement"
                )
            # The only in-registry case is variant-for-variant (heploc ->
            # alalc97); whole-tag advice lives in Comments, which the registry
            # deliberately does not machine-encode.
            variant = record.preferred_value.lower()
        if variant not in variants:  # substitution can collide with a sibling
            variants.append(variant)

    if script and script == suppressed_script(language):
        script = None

    return str(
        LocaleTag(
            language=language, script=script, region=region, variants=tuple(variants)
        )
    )


def fallback_chain(tag: str) -> list[str]:
    """Build the RFC 4647 "Lookup" fallback chain for a locale tag.

    Lookup (RFC 4647 section 3.4) resolves a requested locale against available
    ones by progressively truncating the requested tag from the right until
    something matches. ``ar-EG`` falls back to ``ar``; ``zh-Hant-TW`` walks
    ``zh-Hant-TW`` -> ``zh-Hant`` -> ``zh``.

    This is the mechanism that lets Legesher ship one ``ar`` pack and still serve
    a user who asks for ``ar-EG`` — and, later, ship ``pt-BR`` on top of ``pt``
    without duplicating every keyword.

    Note this is *locale* fallback, and is distinct from the packs' existing
    ``extends:`` field, which chains a pack to its predecessor across **Python
    versions** (``3.12.yml`` extends ``3.11.yml``) within one language. The two
    are orthogonal and will compose: a ``pt-BR`` pack for Python 3.13 would
    inherit along both axes.

    Args:
        tag: The requested tag (need only be well-formed, not canonical).

    Returns:
        Tags from most to least specific, always including *tag* itself
        (canonically cased) and ending at the bare language subtag.

    Raises:
        InvalidLocaleTagError: If the tag is not well-formed.

    Example:
        >>> fallback_chain("zh-Hant-TW")
        ['zh-Hant-TW', 'zh-Hant', 'zh']
    """
    parsed = parse(tag)
    subtags = str(parsed).split("-")

    chain: list[str] = []
    while subtags:
        chain.append("-".join(subtags))
        subtags.pop()
        # RFC 4647 section 3.4 step 3: a truncation that would leave a trailing
        # single-character subtag must drop that subtag too. Legesher rejects
        # singletons in parse(), so this cannot trigger today — it is kept so the
        # function stays correct if the key domain is ever widened.
        if subtags and len(subtags[-1]) == 1:
            subtags.pop()

    return chain
