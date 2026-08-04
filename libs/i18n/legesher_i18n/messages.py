"""Read API for the localized error-message catalog (CORE-1679).

The messages partition (``message_templates`` / ``message_translations``)
lives in the translations database — the database is the source of truth,
activated by ``scripts/activate_messages_partition.py`` and filled by
``scripts/seed_message_templates.py``. This module is the runtime-facing
read path: :func:`load_catalog` performs ONE SQLite read and returns plain,
immutable rules (compiled matcher + localized template), so consumers such
as the ``legesher-runtime`` traceback renderer hold no SQLite connection at
render time.

Version tiering: templates are keyed by ``(implementation, key,
version_added)`` with an optional ``version_removed`` — CPython 3.12's
rewordings must not invalidate 3.11's translations. :func:`load_catalog`
resolves the tier for the requested interpreter version, so exactly one row
per key survives.

Substitution: :meth:`MessageRule.render` replaces ``{slot}`` placeholders by
literal string replacement, NOT ``str.format`` — templates may legitimately
carry stray braces (CPython's ``f-string: valid expression required before
'}'``) that ``str.format`` would reject.
"""

from __future__ import annotations

import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

from .db.database import default_db_path

__all__ = [
    "MessageRule",
    "load_catalog",
    "match_message",
]

#: Probe string for detecting catch-all matchers at load time. A matcher that
#: fullmatches this improbable text (e.g. ``KeyError.key``'s ``^(?P<key>.+)$``,
#: which exists because a KeyError's message IS the repr of the key) would
#: match ANY single-line message — safe only when scoped to its exception
#: type. Such rules are flagged ``catch_all`` and excluded from UNSCOPED
#: :func:`match_message` calls, so a generic message can never "successfully
#: localize" to its own English text via the wrong rule.
_CATCH_ALL_PROBE = "\x02legesher catch-all probe 47\x03"


def _parse_version(version: str | None) -> tuple[int, int]:
    """``'3.12'`` / ``'3.12.4'`` -> ``(3, 12)``; ``None`` -> the running interpreter."""
    if version is None:
        return sys.version_info[:2]
    parts = version.split(".")
    try:
        return int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
    except ValueError as exc:
        raise ValueError(f"not an X.Y version string: {version!r}") from exc


@dataclass(frozen=True)
class MessageRule:
    """One catalog entry, resolved for a locale and interpreter version.

    Attributes:
        key: Stable message identity (``'ZeroDivisionError.division_by_zero'``,
            ``'traceback.header'``).
        matcher: The anchored, compiled regex whose named groups are the
            template's placeholders.
        template: The localized template — the English one when the requested
            locale carries no translation for this row (``localized`` False).
        template_en: The English template, always.
        localized: Whether ``template`` is an actual translation.
        status: Review rung of the translation (``'machine'``…) or ``None``
            when falling back to English.
        version_added: The tier this wording entered at.
        catch_all: The matcher fullmatches arbitrary text (``KeyError.key``).
            Usable only when scoped to its exception type; excluded from
            unscoped :func:`match_message` calls.

    Note: an EMPTY-template rule matching an empty message (``^$`` rows such
    as ``KeyboardInterrupt.interrupt``) renders ``""`` — for callers, a
    matched-but-empty result means "nothing to localize", which is distinct
    from :func:`match_message` returning ``None`` (nothing matched).
    """

    key: str
    matcher: re.Pattern[str]
    template: str
    template_en: str
    localized: bool
    status: str | None
    version_added: str
    catch_all: bool = False

    def render(self, values: dict[str, str]) -> str:
        """Substitute matched slot values into the localized template."""
        rendered = self.template
        for name, value in values.items():
            rendered = rendered.replace("{" + name + "}", value)
        return rendered


def load_catalog(
    locale: str,
    python_version: str | None = None,
    *,
    implementation: str = "cpython",
    db_path: str | Path | None = None,
) -> list[MessageRule]:
    """Load the message catalog for one locale and interpreter version.

    One SQLite read; the returned rules are plain compiled objects with no
    database handle behind them.

    Args:
        locale: BCP 47 tag (``'es'``, ``'ar'``). A locale with no translations
            still gets the full catalog, falling back to the English templates
            (``localized=False`` on those rules).
        python_version: ``'X.Y'`` string, or ``None`` for the running
            interpreter. Selects the version tier per key.
        implementation: ``message_templates.implementation`` — default the
            CPython catalog.
        db_path: Override the translations database (tests); defaults to
            :func:`legesher_i18n.db.database.default_db_path`.

    Returns:
        One :class:`MessageRule` per applicable template row that carries a
        matcher, highest applicable ``version_added`` winning per key. An
        older database without the messages partition (e.g. a stale
        ``~/.legesher`` copy) yields an empty catalog rather than an error —
        callers degrade to untranslated passthrough.
    """
    version = _parse_version(python_version)
    path = Path(db_path) if db_path is not None else default_db_path()

    # Read-only open (the migrate_to_v2 source pattern): a plain
    # sqlite3.connect on a missing/wrong path would silently CREATE an empty
    # database file as a side effect of a read API. Missing file or
    # unreadable database degrades to the empty catalog.
    if not path.exists():
        return []
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    except sqlite3.OperationalError:
        return []
    try:
        try:
            rows = connection.execute(
                "SELECT t.key, t.template_en, t.matcher, t.version_added, "
                "       t.version_removed, tr.template, tr.status "
                "FROM message_templates t "
                "LEFT JOIN message_translations tr "
                "       ON tr.template_id = t.id AND tr.locale = ? "
                "WHERE t.implementation = ? AND t.matcher IS NOT NULL "
                # Contractual determinism: rule order (and therefore
                # first-match-wins in match_message) is seed insertion order.
                "ORDER BY t.id",
                (locale, implementation),
            ).fetchall()
        except sqlite3.OperationalError:
            return []  # partition not activated in this database file
    finally:
        connection.close()

    best: dict[str, tuple[tuple[int, int], MessageRule]] = {}
    for key, template_en, matcher, added, removed, translated, status in rows:
        added_v = _parse_version(added) if added else (0, 0)
        if added_v > version:
            continue
        if removed and _parse_version(removed) <= version:
            continue
        compiled = re.compile(matcher)
        rule = MessageRule(
            key=key,
            matcher=compiled,
            template=translated if translated is not None else template_en,
            template_en=template_en,
            localized=translated is not None,
            status=status,
            version_added=added or "",
            catch_all=compiled.fullmatch(_CATCH_ALL_PROBE) is not None,
        )
        current = best.get(key)
        if current is None or added_v > current[0]:
            best[key] = (added_v, rule)

    return [rule for _, rule in best.values()]


def match_message(
    rules: list[MessageRule], message: str, *, key_prefix: str | None = None
) -> str | None:
    """Render the first rule whose matcher fullmatches ``message``.

    Args:
        rules: Candidate rules, e.g. a full :func:`load_catalog` result.
        message: The English message as raised.
        key_prefix: Exception-type scope (``'KeyError'``): only rules whose
            key starts with ``'{key_prefix}.'`` are considered. **This is the
            intended way to consume the catalog** — messages are matched per
            raised exception type. When omitted, ``catch_all`` rules (whose
            matchers accept arbitrary text, like ``KeyError.key``) are
            EXCLUDED, so an unscoped call can never report a false
            "localization" that is really an arbitrary message echoed through
            a catch-all template.

    Returns:
        The localized rendering with slot values substituted, or ``None``
        when nothing matched (callers pass the original through
        untranslated). A matched empty string means "matched, nothing to
        localize" (see :class:`MessageRule`).
    """
    if key_prefix is not None:
        prefix = key_prefix + "."
        candidates = [rule for rule in rules if rule.key.startswith(prefix)]
    else:
        candidates = [rule for rule in rules if not rule.catch_all]
    for rule in candidates:
        match = rule.matcher.fullmatch(message)
        if match is not None:
            return rule.render(match.groupdict())
    return None
