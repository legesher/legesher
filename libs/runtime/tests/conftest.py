"""Shared helpers: raise real exceptions from a controlled on-disk script,
and a message catalog the suite can rely on wherever it runs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import legesher_i18n
import pytest
from legesher_i18n.db.schema_v2 import apply_schema_v2, connect
from legesher_i18n.exceptions import LanguagePackError
from legesher_i18n.language_registry import (
    get_active_language_codes,
    get_language_name,
    get_native_name,
    is_rtl_language,
)
from legesher_i18n.pack_loader import LanguagePackLoader
from legesher_i18n.pack_messages import DEFAULT_STATUS, entry_problem, message_fingerprint

CATALOG_SEED = Path(legesher_i18n.__file__).parent / "db" / "seeds" / "cpython_messages.json"


def _pack_translations(implementation: str) -> dict[str, dict[tuple[str, str], dict]]:
    """``{locale: {(key, src): entry}}`` from every shipped pack's ``messages``.

    Every version file is read, so a translation of a later wording (3.11,
    3.12) is found as well as the base file's. A tier this interpreter
    cannot load (the ja and si 3.13+ files on 3.10 to 3.12) is skipped; it
    carries no messages.
    """
    loader = LanguagePackLoader()
    found: dict[str, dict[tuple[str, str], dict]] = {}
    for locale in get_active_language_codes():
        for version in loader.list_available_versions():
            try:
                pack = loader.load(locale, "python", version, enforce_min_interpreter=False)
            except LanguagePackError:
                continue
            for key, entry in (pack.messages.get(implementation) or {}).items():
                found.setdefault(locale, {})[(key, entry["src"])] = entry
    return found


@pytest.fixture(scope="session", autouse=True)
def seeded_message_catalog(tmp_path_factory: pytest.TempPathFactory):
    """Build the message catalog this suite renders from, then make it the default.

    The renderer reads ``traceback.*`` structure and exception messages from
    the translations database (``legesher_i18n.messages.load_catalog``), whose
    default location is ``legesher_i18n/db/translations.db``: a gitignored,
    locally built file. A fresh checkout or a CI runner has no such file, the
    catalog loads empty, the renderer degrades to English by design, and 17
    of these tests fail without a defect in sight (CORE-2129).

    So the suite builds its own: a temporary v2 database with the English
    side from the tracked catalog seed (``db/seeds/cpython_messages.json``),
    inserted as ``libs/i18n/scripts/seed_message_templates.py`` inserts it,
    and the translations from the shipped language packs' ``messages``
    sections, matched to their English row by key and fingerprint and kept
    only when they pass the join rule an install applies (the seed carries no
    translations, CORE-2630). The scripts are not imported: they
    are reachable only by putting ``libs/i18n`` on ``sys.path`` under the
    generic package name ``scripts``, which several workspace directories
    share. Both halves are what ships, so the goldens still describe it.

    Only the default resolution is redirected: tests that pass ``db_path``
    explicitly (the degraded-catalog cases) see exactly what they ask for.
    """
    seed = json.loads(CATALOG_SEED.read_text(encoding="utf-8"))
    db_path = tmp_path_factory.mktemp("catalog") / "translations.db"

    connection = connect(db_path)
    try:
        apply_schema_v2(connection)
        translations = _pack_translations(seed["implementation"])
        locales = sorted(translations)
        connection.executemany(
            "INSERT INTO locales (tag, language_subtag, name, native_name, direction) "
            "VALUES (?, ?, ?, ?, ?)",
            [
                (
                    tag,
                    tag,
                    get_language_name(tag),
                    get_native_name(tag),
                    "rtl" if is_rtl_language(tag) else "ltr",
                )
                for tag in locales
            ],
        )
        for template in seed["templates"]:
            cursor = connection.execute(
                "INSERT INTO message_templates "
                "(implementation, key, template_en, placeholders, matcher, "
                " version_added, version_removed) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    seed["implementation"],
                    template["key"],
                    template["template_en"],
                    json.dumps(template.get("placeholders", []), ensure_ascii=False),
                    template.get("matcher"),
                    template.get("version_added", seed["version_added"]),
                    template.get("version_removed"),
                ),
            )
            src = message_fingerprint(template["template_en"])
            declared = [p["name"] for p in template.get("placeholders", [])]
            for locale in locales:
                entry = translations[locale].get((template["key"], src))
                # The join rule an install applies: an entry it would skip
                # is not put in the database either.
                if entry is None or entry_problem(
                    entry, template_en=template["template_en"], placeholders=declared
                ):
                    continue
                connection.execute(
                    "INSERT INTO message_translations "
                    "(template_id, locale, template, status, "
                    " source, model_version, created_by) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        cursor.lastrowid,
                        locale,
                        entry["text"],
                        entry.get("status", DEFAULT_STATUS),
                        "pack",
                        None,
                        "conftest",
                    ),
                )
        connection.commit()
    finally:
        connection.close()

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr("legesher_i18n.messages.default_db_path", lambda: db_path)
        yield db_path


class Captured:
    def __init__(self, exc_info, path: Path):
        self.exc_type, self.exc_value, self.exc_tb = exc_info
        self.path = path

    def normalize(self, rendered: str) -> str:
        """Make renderer output stable: the tmp script path becomes script.py."""
        return rendered.replace(str(self.path), "script.py")


@pytest.fixture
def raise_from_script(tmp_path: Path):
    """Run ``code`` from a real file and capture the exception it raises.

    A real on-disk file keeps ``linecache`` honest, so the traceback carries
    the actual source lines (and their PEP 657 caret lines) exactly as a user
    would see them.
    """

    def _raise(code: str) -> Captured:
        path = tmp_path / "script.py"
        path.write_text(code, encoding="utf-8")
        compiled = compile(code, str(path), "exec")
        try:
            exec(compiled, {"__name__": "__main__"})  # noqa: S102
        except BaseException:
            return Captured(sys.exc_info(), path)
        raise AssertionError("script did not raise")

    return _raise
