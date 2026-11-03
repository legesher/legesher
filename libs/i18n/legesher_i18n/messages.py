"""Read API for the localized error-message catalog (CORE-1679).

The messages partition (``message_templates`` / ``message_translations``)
lives in the translations database — the database is the source of truth,
activated by ``scripts/activate_messages_partition.py`` and filled by
``scripts/seed_message_templates.py`` from the tracked seeds in
``db/seeds/``. This module is the runtime-facing read path:
:func:`load_catalog` reads once (the database, or the seed files when it
falls back) and returns plain, immutable rules (compiled matcher + localized
template), so consumers such as the ``legesher-runtime`` traceback renderer
hold no SQLite connection at render time.

No wheel and no clone carries the database (CORE-1794), so when the DEFAULT
database has no catalog rows (templates with a matcher), :func:`load_catalog`
reads the seed the database is filled from, which ships as package data. An
installed package therefore renders the catalog a seeded checkout renders.
Rows in the database always win; an explicit ``db_path`` is never replaced
by the seed.

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

import json
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

#: The tracked catalog seeds, one JSON file per catalog, each naming its
#: ``implementation`` (``cpython_messages.json``, ``v8_jej_messages.json``).
#: Package data: an installed wheel carries them, the database it fills never.
SEED_DIR = Path(__file__).parent / "db" / "seeds"

#: One catalog row as the database read returns it: key, template_en,
#: matcher, version_added, version_removed, translated template, status.
_Row = tuple[str, str, str, str, str | None, str | None, str | None]


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

    One read of the database, or of the seed files when the default database
    has no catalog rows; the returned rules are plain compiled objects with
    no database handle behind them.

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
        matcher, highest applicable ``version_added`` winning per key. When
        the default database is missing, unreadable, predates the messages
        partition (e.g. a stale ``~/.legesher`` copy) or holds no rows with a
        matcher for ``implementation``, the rows come from the seed in
        :data:`SEED_DIR` instead. An explicit ``db_path`` is read alone: one without catalog
        rows yields an empty catalog rather than an error, and callers
        degrade to untranslated passthrough.
    """
    version = _parse_version(python_version)
    if db_path is not None:
        rows = _database_rows(Path(db_path), locale, implementation)
    else:
        rows = _database_rows(default_db_path(), locale, implementation) or _seed_rows(
            locale, implementation
        )

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


def _database_rows(path: Path, locale: str, implementation: str) -> list[_Row]:
    """The catalog rows ``path`` holds for ``implementation``; ``[]`` when none."""
    # Read-only open (the migrate_to_v2 source pattern): a plain
    # sqlite3.connect on a missing/wrong path would silently CREATE an empty
    # database file as a side effect of a read API. Missing file or
    # unreadable database degrades to no rows. DatabaseError, not only
    # OperationalError: a file that is not SQLite at all ("file is not a
    # database") raises the parent class, on the first query.
    if not path.exists():
        return []
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    except sqlite3.DatabaseError:
        return []
    try:
        try:
            return connection.execute(
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
        except sqlite3.DatabaseError:
            return []  # partition not activated, or not a SQLite file
    finally:
        connection.close()


def _seed_rows(locale: str, implementation: str) -> list[_Row]:
    """The seed rows for ``implementation``, shaped like :func:`_database_rows`.

    Reads what ``scripts/seed_message_templates.py`` writes: templates
    without a matcher are skipped, a template's own ``version_added``
    overrides the file's, and a translation's status defaults to
    ``machine``. Templates are read in file order, the order the seeder
    inserts them, so first-match-wins holds; files are read in name order
    (the seeder takes one file per run, and each implementation has one seed
    today). A file that cannot be read or is not JSON is skipped, as a
    missing database is; the seeds' shape is checked by the seeder's
    validation, not here.
    """
    rows: list[_Row] = []
    for path in sorted(SEED_DIR.glob("*.json")):
        try:
            seed = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if seed.get("implementation") != implementation:
            continue
        for template in seed.get("templates", []):
            matcher = template.get("matcher")
            if matcher is None:
                continue
            translation = template.get("translations", {}).get(locale) or {}
            rows.append(
                (
                    template["key"],
                    template["template_en"],
                    matcher,
                    template.get("version_added", seed.get("version_added")),
                    template.get("version_removed"),
                    translation.get("template"),
                    translation.get("status", "machine") if translation else None,
                )
            )
    return rows


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
