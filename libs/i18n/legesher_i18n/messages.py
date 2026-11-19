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
reads the English side (key, template, matcher, placeholders, version tiers)
from the seed the database is filled from, which ships as package data, and
the translations from the language pack for the locale: its ``messages``
section (CORE-2630). A pack entry is used only when it passes the join rules
in :func:`legesher_i18n.pack_messages.entry_problem`; an entry that fails is
skipped and that message prints as the interpreter printed it. The seed
carries no translations: a locale whose pack carries no messages prints the
interpreter's own text.

Rows in the database always win; an explicit ``db_path`` is never replaced
by the seed or by a pack.

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
import logging
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NamedTuple

from .db.database import default_db_path
from .exceptions import PackNotFoundError
from .pack_loader import LanguagePackLoader
from .pack_messages import (
    DEFAULT_STATUS,
    IMPLEMENTATION_TARGETS,
    PLACEHOLDER_KINDS,
    entry_problem,
    message_fingerprint,
)

__all__ = [
    "MessageRule",
    "load_catalog",
    "match_message",
    "pack_message_problems",
]

logger = logging.getLogger(__name__)

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

#: A pack version file's stem: ``3.12``.
_VERSION_FILE = re.compile(r"\d+\.\d+")

#: Longest key quoted in a reason before it is cut.
_KEY_LABEL_LIMIT = 80


def _key_label(key: object) -> str:
    """``key`` as a reason starts with it, cut when it is very long."""
    text = str(key)
    if len(text) <= _KEY_LABEL_LIMIT:
        return text
    return text[:_KEY_LABEL_LIMIT] + f"... ({len(text)} characters)"


class _Row(NamedTuple):
    """One catalog row, from the database or from a seed file."""

    key: str
    template_en: str
    matcher: str
    version_added: str | None
    version_removed: str | None
    translated: str | None
    status: str | None
    #: ``(name, kind)`` per declared placeholder; ``kind`` is ``None`` for a
    #: placeholder copied verbatim.
    placeholders: tuple[tuple[str, str | None], ...]


def _declares_kinds(raw: Any) -> bool:
    """Whether stored placeholders carry a ``kind`` field on any placeholder."""
    try:
        declared = json.loads(raw) if isinstance(raw, str) else raw
    except ValueError:
        return False
    return isinstance(declared, list) and any(
        isinstance(placeholder, dict) and "kind" in placeholder
        for placeholder in declared
    )


def _placeholders(declared: Any) -> tuple[tuple[str, str | None], ...]:
    """``(name, kind)`` pairs from a template's declared placeholders.

    ``declared`` is the seed's list, or the JSON text the database stores.
    Anything else, or a kind this release does not know, reads as no kind:
    the placeholder is then copied verbatim, which is always safe.
    """
    if isinstance(declared, str):
        try:
            declared = json.loads(declared)
        except ValueError:
            return ()
    if not isinstance(declared, list):
        return ()
    pairs: list[tuple[str, str | None]] = []
    for placeholder in declared:
        if not isinstance(placeholder, dict) or not isinstance(
            placeholder.get("name"), str
        ):
            continue
        kind = placeholder.get("kind")
        pairs.append((placeholder["name"], kind if kind in PLACEHOLDER_KINDS else None))
    return tuple(pairs)


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
        slot_kinds: ``(placeholder, kind)`` for each placeholder the English
            side marks as a line number (``'line'``) or a count
            (``'count'``). A placeholder that is not listed is copied
            verbatim. Empty when the catalog source predates the marker.

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
    slot_kinds: tuple[tuple[str, str], ...] = ()

    def kind_of(self, placeholder: str) -> str | None:
        """``'line'``, ``'count'``, or ``None`` for a verbatim placeholder."""
        return dict(self.slot_kinds).get(placeholder)

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

    One read of the database, or of the seed files and the locale's language
    pack when the default database has no catalog rows; the returned rules
    are plain compiled objects with no database handle behind them.

    Where the catalog comes from, in order:

    1. An explicit ``db_path`` is read alone. One without catalog rows
       yields an empty catalog rather than an error, and callers degrade to
       untranslated passthrough.
    2. The default database, when it holds rows with a matcher for
       ``implementation``, is the whole catalog: English and translations.
    3. Otherwise (the default database is missing, unreadable, predates the
       messages partition or holds no such rows, which is every installed
       package) the English side comes from the seed in :data:`SEED_DIR` and
       the translations from the ``messages`` section of the language pack
       for ``locale`` at this interpreter version, or at the newest version
       the pack has below it. A pack entry is used only
       when :func:`legesher_i18n.pack_messages.entry_problem` finds nothing
       wrong with it for the English row that applies; otherwise that rule
       is not localized. When there is no such pack file, it does not load,
       or it carries no messages for ``implementation``, no rule is
       localized.

    Args:
        locale: BCP 47 tag (``'es'``, ``'ar'``). A locale with no translations
            still gets the full catalog, falling back to the English templates
            (``localized=False`` on those rules).
        python_version: ``'X.Y'`` string, or ``None`` for the running
            interpreter. Selects the version tier per key.
        implementation: ``message_templates.implementation``. Defaults to
            the CPython catalog.
        db_path: Override the translations database (tests); defaults to
            :func:`legesher_i18n.db.database.default_db_path`.

    Returns:
        One :class:`MessageRule` per applicable template row that carries a
        matcher, highest applicable ``version_added`` winning per key.
    """
    version = _parse_version(python_version)
    entries: dict[str, Any] | None = None
    if db_path is not None:
        rows = _database_rows(Path(db_path), locale, implementation)
    else:
        rows = _database_rows(default_db_path(), locale, implementation)
        if not rows:
            rows = _seed_rows(implementation)
            entries = _pack_entries(locale, version, implementation)

    applicable = _applicable_rows(rows, version)
    if entries is not None:
        usable, problems = _join(entries, applicable)
        for problem in problems:
            logger.debug("%s pack message not used: %s", locale, problem)
    rules: list[MessageRule] = []
    for row in applicable.values():
        translated, status = row.translated, row.status
        if entries is not None:
            translated, status = usable.get(row.key, (None, None))
        compiled = re.compile(row.matcher)
        rules.append(
            MessageRule(
                key=row.key,
                matcher=compiled,
                template=translated if translated is not None else row.template_en,
                template_en=row.template_en,
                localized=translated is not None,
                status=status,
                version_added=row.version_added or "",
                catch_all=compiled.fullmatch(_CATCH_ALL_PROBE) is not None,
                slot_kinds=tuple(
                    (name, kind) for name, kind in row.placeholders if kind
                ),
            )
        )
    return rules


def pack_message_problems(
    locale: str,
    python_version: str | None = None,
    *,
    implementation: str = "cpython",
    loader: LanguagePackLoader | None = None,
) -> list[str]:
    """Why entries of ``locale``'s pack would not be used, one line each.

    Joins the pack's ``messages`` for ``implementation`` against the English
    side in the seed, as an installed package does, and reports every entry
    the join would skip: an entry that fails
    :func:`legesher_i18n.pack_messages.entry_problem`, and an entry whose key
    has no English row at this interpreter version yet. At run time such an
    entry is skipped without an error; this is how a pack is checked before
    it ships.

    Two kinds of unused entry are expected and not reported, because a later
    pack file can add or override an entry but never remove one: the
    translation of an earlier wording of a message, inherited by the files
    after the one that rewords it, and the translation of a message removed
    with no rewording to replace it.

    Args:
        locale: The pack's language code.
        python_version: ``'X.Y'`` string, or ``None`` for the running
            interpreter.
        implementation: Which implementation's messages to check.
        loader: The pack loader to read with. Pass one loader when checking
            many packs, so they are discovered once.

    Returns:
        ``"<key>: <reason>"`` lines, sorted by key. Empty when every entry
        joins, and when the pack carries no messages for ``implementation``
        or there is no pack for the locale at this version.

    Raises:
        Exception: Whatever the pack loader raises for a pack file that
            exists and does not load: :class:`LanguagePackError` for one that
            fails validation, a YAML error for one that does not parse.
    """
    version = _parse_version(python_version)
    target = IMPLEMENTATION_TARGETS.get(implementation)
    if target is None:
        return []
    loader = loader or LanguagePackLoader()
    requested = f"{version[0]}.{version[1]}"
    try:
        pack = loader.load(locale, target, requested, enforce_min_interpreter=False)
    except PackNotFoundError:
        return []
    entries = pack.messages.get(implementation) or {}
    rows = _seed_rows(implementation)
    applicable = _applicable_rows(rows, version)

    # An entry for an earlier wording is expected only when it really is
    # inherited: the pack carried the same entry at a version where that
    # wording applied, and the entry was checked there. An entry that names
    # an earlier wording but first appears, or changes, after that wording
    # stopped applying is a stale fingerprint, and is reported.
    earlier_files = [
        stem
        for stem in _pack_versions(loader, locale, target)
        if _parse_version(stem) < version
    ]
    earlier_entries: dict[str, dict[str, Any]] = {}

    def entries_at(stem: str) -> dict[str, Any]:
        if stem not in earlier_entries:
            earlier = loader.load(locale, target, stem, enforce_min_interpreter=False)
            earlier_entries[stem] = earlier.messages.get(implementation) or {}
        return earlier_entries[stem]

    def applicable_at(stem: str) -> dict[str, _Row]:
        # The wording printed at that version: a later rewording supersedes
        # an earlier one whether or not the earlier row names a removal.
        return _applicable_rows(rows, _parse_version(stem))

    inherited: set[str] = set()
    for key, entry in entries.items():
        if not isinstance(entry, dict):
            continue
        current = applicable.get(key)
        for row in rows:
            if (
                row.key != key
                or row is current
                or entry.get("src") != message_fingerprint(row.template_en)
            ):
                continue
            if any(
                applicable_at(stem).get(key) is row
                and entries_at(stem).get(key) == entry
                for stem in earlier_files
            ):
                inherited.add(key)
                break
    _, problems = _join(
        {key: entry for key, entry in entries.items() if key not in inherited},
        applicable,
        report_unknown=True,
    )
    return problems


def _pack_versions(loader: LanguagePackLoader, locale: str, target: str) -> list[str]:
    """The ``X.Y`` stems of the pack's own version files, oldest first."""
    pack_dir = loader._discover_packs().get(f"{target}-{locale}")
    if pack_dir is None:
        return []
    return sorted(
        (
            path.stem
            for path in (pack_dir / "packs").glob("*.yml")
            if _VERSION_FILE.fullmatch(path.stem)
        ),
        key=_parse_version,
    )


def _applicable_rows(rows: list[_Row], version: tuple[int, int]) -> dict[str, _Row]:
    """The one row per key that applies to ``version``.

    The highest ``version_added`` at or below ``version`` wins, skipping a
    row whose ``version_removed`` is at or below it. Keys keep the order
    they first appear in, which is the order first-match-wins depends on.
    """
    best: dict[str, tuple[tuple[int, int], _Row]] = {}
    for row in rows:
        added = _parse_version(row.version_added) if row.version_added else (0, 0)
        if added > version:
            continue
        if row.version_removed and _parse_version(row.version_removed) <= version:
            continue
        current = best.get(row.key)
        if current is None or added > current[0]:
            best[row.key] = (added, row)
    return {key: row for key, (_, row) in best.items()}


def _pack_entries(
    locale: str, version: tuple[int, int], implementation: str
) -> dict[str, Any] | None:
    """The pack's entries for ``implementation``, or ``None`` when it has none.

    The pack file for the interpreter's version is read; when the pack has
    no such file (an interpreter newer than the pack), the newest of the
    pack's own files below it is. That is safe because every entry is joined
    by fingerprint: a message the newer interpreter reworded is a different
    English template, so the older translation does not attach to it, and
    every message it did not reword stays translated.

    ``None`` covers every way a pack can have nothing to offer: no pack for
    the locale, no pack file at or below this interpreter version, a pack
    file that does not load, a pack with no messages for the implementation,
    and any error while finding the pack. No rule is then localized.

    The pack's minimum interpreter is not enforced: that guard protects
    translated identifiers that would not parse, and rendering a message
    executes none.
    """
    target = IMPLEMENTATION_TARGETS.get(implementation)
    if target is None:
        return None
    try:
        loader = LanguagePackLoader()
        candidates = [
            stem
            for stem in _pack_versions(loader, locale, target)
            if _parse_version(stem) <= version
        ]
        if not candidates:
            return None
        pack = loader.load(
            locale, target, candidates[-1], enforce_min_interpreter=False
        )
    except Exception:  # noqa: BLE001 - a missing or broken pack degrades, never crashes
        return None
    return pack.messages.get(implementation) or None


def _join(
    entries: dict[str, Any],
    applicable: dict[str, _Row],
    *,
    report_unknown: bool = False,
) -> tuple[dict[str, tuple[str, str]], list[str]]:
    """Pair pack entries with the English rows they translate.

    Args:
        entries: The pack's entries for one implementation, by key.
        applicable: The English row that applies per key.
        report_unknown: Also report an entry whose key has no applicable
            row. At run time such an entry is ignored without comment,
            because a pack may be newer than the catalog it is read with.

    Returns:
        ``(usable, problems)``: ``(text, status)`` per key for the entries
        that passed the join rules, and a ``"<key>: <reason>"`` line for
        each entry that did not, sorted by key.
    """
    usable: dict[str, tuple[str, str]] = {}
    problems: list[str] = []
    for key in sorted(entries, key=str):
        entry = entries[key]
        row = applicable.get(key)
        if row is None:
            if report_unknown:
                problems.append(
                    f"{_key_label(key)}: no English message with this key applies here"
                )
            continue
        problem = entry_problem(
            entry,
            template_en=row.template_en,
            placeholders=[name for name, _ in row.placeholders],
        )
        if problem is not None:
            problems.append(f"{_key_label(key)}: {problem}")
            continue
        usable[key] = (entry["text"], entry.get("status", DEFAULT_STATUS))
    return usable, problems


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
            rows = connection.execute(
                "SELECT t.key, t.template_en, t.matcher, t.version_added, "
                "       t.version_removed, tr.template, tr.status, t.placeholders "
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
        seed_kinds: dict[tuple[str, str], tuple[tuple[str, str | None], ...]] | None = (
            None
        )
        result: list[_Row] = []
        for row in rows:
            placeholders = _placeholders(row[7])
            if not _declares_kinds(row[7]):
                # Rows seeded before placeholder kinds existed. The seeder is
                # append-once, so they never gain them; the seed is the
                # English side's truth, so take the kinds from its row with
                # the same key and wording.
                if seed_kinds is None:
                    seed_kinds = {
                        (seed_row.key, seed_row.template_en): seed_row.placeholders
                        for seed_row in _seed_rows(implementation)
                    }
                from_seed = seed_kinds.get((row[0], row[1]))
                if from_seed is not None and [n for n, _ in from_seed] == [
                    n for n, _ in placeholders
                ]:
                    placeholders = from_seed
            result.append(_Row(*row[:7], placeholders))
        return result
    finally:
        connection.close()


def _seed_rows(implementation: str) -> list[_Row]:
    """The seed's English rows for ``implementation``, shaped like :func:`_database_rows`.

    Reads what ``scripts/seed_message_templates.py`` writes: templates
    without a matcher are skipped, and a template's own ``version_added``
    overrides the file's. Only the English side is read. Translations come
    from the language packs (CORE-2630); a translation left in a seed file
    never reaches an install. Templates are read in file order, the order the seeder
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
            rows.append(
                _Row(
                    template["key"],
                    template["template_en"],
                    matcher,
                    template.get("version_added", seed.get("version_added")),
                    template.get("version_removed"),
                    None,
                    None,
                    _placeholders(template.get("placeholders", [])),
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
