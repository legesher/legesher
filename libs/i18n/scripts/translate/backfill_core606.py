#!/usr/bin/env python3
"""CORE-606 — backfill selected translations for 5 under-covered terms.

Terms: ``__import__``, ``type``, ``encodingwarning``, ``exceptiongroup``,
``baseexceptiongroup``.

Audited state on ``main`` (2026-07): these terms were largely already present
in the YAML packs and the ``translations`` table, but ``selected_translations``
was behind (0-5 languages each). This script reconciles the database to the
shipped packs and fills the genuine gaps, then leaves the surgical YAML edits
that are actually new (``__import__`` everywhere; a few ``type`` builtin/keyword
gaps; one ``de`` identity fix).

Design (per CORE-606 decisions + repo constraints):
  * DB-first, collision-guarded via ``TranslationDatabase.set_selected``.
  * The shipped pack value is authoritative — the DB mirrors it — EXCEPT where a
    value is generated here (``__import__`` for every pack, and the ``de``
    ``baseexceptiongroup`` identity fix).
  * ``__import__`` is generated experimentally for every pack, wrapped in
    double-underscore boundaries (``__<word>__``), reusing the good dunder
    candidates already in the DB. Flagged experimental pending native review.
  * NO full pack regeneration (additive-exporter corruption risk, CORE-1400) —
    YAML edits are surgical, additive line insertions that preserve headers,
    comments and ordering. ``encodingwarning`` / ``exceptiongroup`` /
    ``baseexceptiongroup`` are already in the packs and need no YAML change.
  * Idempotent: safe to re-run. This IS the regenerable generator for the
    generated values (the maps below are its seed data).

Usage:
    uv run python libs/i18n/scripts/translate/backfill_core606.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve()
I18N_ROOT = HERE.parents[2]  # libs/i18n
sys.path.insert(0, str(I18N_ROOT))

from legesher_i18n.db import TranslationDatabase  # noqa: E402

PACKS = I18N_ROOT / "language-packs" / "python"
DB_PATH = I18N_ROOT / "legesher_i18n" / "db" / "translations.db"

TERMS = [
    "__import__",
    "type",
    "encodingwarning",
    "exceptiongroup",
    "baseexceptiongroup",
]

SELECTED_BY = "CORE-606"
GEN_SOURCE = "claude"
GEN_MODEL = "core-606-experimental"

# Source priority for mirroring the shipped pack when several candidates exist.
SOURCE_RANK = {"claude": 0, "aya": 1, "community": 2, "yaml-import": 3, "yaml_pack": 4}

# ---------------------------------------------------------------------------
# Generated / experimental values (native review pending, CORE-674 pipeline).
# ---------------------------------------------------------------------------
# __import__ for every on-disk pack, dunder-wrapped. Values marked (cand) reuse
# a good double-underscore candidate already present in translations.db.
IMPORT_MAP = {
    "am": "__አስገባ__",
    "ar": "__استيراد__",
    "bn": "__আমদানি__",  # cand
    "bs": "__uvoz__",
    "ca": "__importar__",
    "cs": "__importovat__",
    "cy": "__mewnforio__",
    "da": "__importer__",
    "de": "__importieren__",
    "el": "__εισαγωγή__",  # cand
    "en": "__import__",  # canonical (identity)
    "es": "__importar__",  # cand core "importar"
    "fa": "__واردکردن__",
    "fi": "__tuo__",  # cand
    "fr": "__importer__",
    "ga": "__iompórtáil__",  # cand
    "gd": "__ionphortaich__",
    "gl": "__importar__",
    "gu": "__આયાત__",
    "he": "__ייבוא__",  # cand
    "hi": "__आयात__",  # cand
    "hr": "__uvoz__",
    "hu": "__importál__",
    "id": "__impor__",  # cand
    "it": "__importare__",
    "ja": "__インポート__",
    "kn": "__ಆಮದು__",
    "ko": "__가져오기__",
    "lv": "__importēt__",
    "mk": "__увоз__",
    "ml": "__ഇറക്കുമതി__",
    "mn": "__импортлох__",
    "ms": "__impor__",
    "my": "__တင်သွင်း__",
    "nl": "__importeer__",
    "no": "__importer__",
    "pl": "__importuj__",  # cand
    "pt": "__importar__",
    "ro": "__importă__",
    "ru": "__импорт__",  # cand
    "si": "__ආයාත__",
    "sr": "__увоз__",
    "su": "__impor__",
    "sv": "__importera__",
    "te": "__దిగుమతి__",  # cand
    "th": "__นำเข้า__",
    "tr": "__içeaktar__",
    "ur": "__درآمد__",  # cand
    "uz": "__kiritish__",
    "vi": "__nhập__",
    "zh": "__导入__",
}

# Fix genuine correctness problems (pure identity, or a collision that would
# otherwise leave the term unselected) with a distinct, correct value.
# Keyed by (term, lang) -> replacement value. Everything else (transliterations)
# is promoted as-shipped and flagged experimental for native review.
IDENTITY_FIXES = {
    (
        "baseexceptiongroup",
        "de",
    ): "Basisausnahmegruppe",  # was "BaseExceptionGroup" (identity)
    # fi pack ships exception == exceptiongroup == "ohje" (a mistranslation);
    # give exceptiongroup a distinct, correct Finnish value to clear the collision.
    ("exceptiongroup", "fi"): "poikkeusryhmä",
}

# Which YAML pack file + section each term lives in.
#   term -> list of (version, section)
PLACEMENT = {
    "__import__": [("3.10", "builtins")],
    "type": [("3.10", "builtins"), ("3.12", "keywords")],
    "encodingwarning": [("3.10", "exceptions")],
    "exceptiongroup": [("3.11", "exceptions")],
    "baseexceptiongroup": [("3.11", "exceptions")],
}

TOP_LEVEL_KEYS = (
    "language",
    "target",
    "version",
    "extends",
    "keywords",
    "builtins",
    "exceptions",
    "metadata",
)


def pack_dir(lang: str) -> Path:
    return PACKS / lang / f"legesher_i18n_python_{lang}" / "packs"


def on_disk_langs() -> list[str]:
    return sorted(
        d.name
        for d in PACKS.iterdir()
        if d.is_dir() and (pack_dir(d.name) / "3.10.yml").exists()
    )


def pack_file(lang: str, ver: str) -> Path:
    return pack_dir(lang) / f"{ver}.yml"


def read_pack(lang: str, ver: str) -> dict:
    f = pack_file(lang, ver)
    if not f.exists():
        return {}
    return yaml.safe_load(f.read_text(encoding="utf-8")) or {}


def is_identity(term: str, value: str) -> bool:
    if value is None:
        return True
    return value.strip("_").lower() == term.strip("_").lower()


def shipped_value(lang: str, term: str) -> str | None:
    """The value already shipped in the pack (authoritative for mirroring).

    For ``type`` prefer the 3.10 builtin, then the 3.12 keyword.
    """
    for ver, section in PLACEMENT[term]:
        sec = read_pack(lang, ver).get(section) or {}
        if term in sec:
            return sec[term]
    return None


def db_best_candidate(
    db: TranslationDatabase, term: str, term_id: int, lang: str
) -> str | None:
    rows = db.get_translations(term_id=term_id, language_code=lang)
    if not rows:
        return None
    rows = sorted(
        rows,
        key=lambda r: (
            is_identity(term, r["translation"]),  # real translations first
            SOURCE_RANK.get(r.get("source"), 9),  # then by source rank
        ),
    )
    return rows[0]["translation"]


# ---------------------------------------------------------------------------
# Surgical YAML insertion (preserve header, comments, ordering).
# ---------------------------------------------------------------------------
def yaml_scalar(value: str) -> str:
    """Render a value the way PyYAML would for these packs (plain if safe)."""
    dumped = yaml.dump({"k": value}, allow_unicode=True, default_flow_style=False)
    # dumped == "k: <scalar>\n"
    return dumped[len("k: ") :].rstrip("\n")


def insert_key(
    lang: str, ver: str, section: str, key: str, value: str, dry_run: bool
) -> str:
    """Insert ``key: value`` into ``section`` of a pack file if absent.

    Returns one of: "inserted", "exists", "no-section", "no-file".
    """
    f = pack_file(lang, ver)
    if not f.exists():
        return "no-file"
    lines = f.read_text(encoding="utf-8").splitlines(keepends=True)

    # locate the section header line (column-0 "section:")
    sec_idx = None
    for i, ln in enumerate(lines):
        if ln.rstrip("\n") == f"{section}:":
            sec_idx = i
            break
    if sec_idx is None:
        return "no-section"

    # scan the section body; detect if key already present; find the
    # alphabetical insert slot (ASCII order matches the existing packs).
    insert_at = sec_idx + 1
    slot_found = False
    j = sec_idx + 1
    while j < len(lines):
        stripped = lines[j].rstrip("\n")
        if stripped and not stripped.startswith((" ", "\t")):
            break  # next top-level key -> end of section
        entry = stripped.strip()
        if entry and ":" in entry and not entry.startswith("#"):
            ekey = entry.split(":", 1)[0].strip()
            if ekey == key:
                return "exists"
            if not slot_found and key < ekey:
                insert_at = j
                slot_found = True
        j += 1
    if not slot_found:
        insert_at = j  # end of section
    new_line = f"  {key}: {yaml_scalar(value)}\n"
    if not dry_run:
        lines.insert(insert_at, new_line)
        f.write_text("".join(lines), encoding="utf-8")
    return "inserted"


def replace_value(
    lang: str, ver: str, section: str, key: str, value: str, dry_run: bool
) -> str:
    """Replace ``key``'s value *within* ``section``. Returns status.

    Scan is bounded to the requested section (same top-level-key logic as
    ``insert_key``) so the same key appearing in another section/version is
    never touched.
    """
    f = pack_file(lang, ver)
    if not f.exists():
        return "no-file"
    lines = f.read_text(encoding="utf-8").splitlines(keepends=True)

    sec_idx = None
    for i, ln in enumerate(lines):
        if ln.rstrip("\n") == f"{section}:":
            sec_idx = i
            break
    if sec_idx is None:
        return "no-section"

    j = sec_idx + 1
    while j < len(lines):
        s = lines[j].rstrip("\n")
        if s and not s.startswith((" ", "\t")):
            break  # next top-level key -> end of section
        if s.strip().startswith(f"{key}:") and s.startswith("  "):
            lines[j] = f"  {key}: {yaml_scalar(value)}\n"
            if not dry_run:
                f.write_text("".join(lines), encoding="utf-8")
            return "replaced"
        j += 1
    return "absent"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dry = args.dry_run

    db = TranslationDatabase(db_path=str(DB_PATH))
    term_id = {}
    for t in TERMS:
        row = db.get_term_by_name(t, "python")
        if row is None:
            raise SystemExit(f"term not found in DB: {t!r} (python)")
        term_id[t] = row["id"]
    langs = on_disk_langs()
    missing_import = [lang for lang in langs if lang not in IMPORT_MAP]
    if missing_import:
        raise SystemExit(
            f"IMPORT_MAP is missing entries for on-disk packs: {missing_import}"
        )
    print(f"{'DRY-RUN — ' if dry else ''}on-disk packs: {len(langs)}")

    report: dict[str, dict] = {
        t: {
            "selected": 0,
            "skipped_collision": [],
            "yaml_inserted": 0,
            "yaml_replaced": 0,
            "already_selected": 0,
            "no_value": [],
        }
        for t in TERMS
    }

    for term in TERMS:
        tid = term_id[term]
        for lang in langs:
            # ---- determine authoritative value ----------------------------
            if (term, lang) in IDENTITY_FIXES:
                value = IDENTITY_FIXES[(term, lang)]
                generated = True
            elif term == "__import__":
                value = IMPORT_MAP.get(lang)
                generated = True
            else:
                value = shipped_value(lang, term)
                generated = False
                if value is None or is_identity(term, value):
                    cand = db_best_candidate(db, term, tid, lang)
                    if cand and not is_identity(term, cand):
                        value = cand
            if not value:
                report[term]["no_value"].append(lang)
                continue

            # ---- database: translations + selected_translations -----------
            existing_sel = db.get_selected(term_id=tid, language_code=lang)
            if not dry:
                if generated:
                    db.add_translation(
                        term_id=tid,
                        language_code=lang,
                        translation=value,
                        source=GEN_SOURCE,
                        model_version=GEN_MODEL,
                        confidence="low",
                        created_by=SELECTED_BY,
                        model_rationale="CORE-606 experimental; native review pending",
                    )
                try:
                    db.set_selected(
                        term_id=tid,
                        language_code=lang,
                        translation=value,
                        selected_by=SELECTED_BY,
                        selection_reason="CORE-606 backfill (experimental)",
                    )
                except ValueError as e:  # collision guard
                    report[term]["skipped_collision"].append(f"{lang}: {e}")
                    continue
            if existing_sel and existing_sel.get("translation") == value:
                report[term]["already_selected"] += 1
            else:
                report[term]["selected"] += 1

            # ---- surgical YAML --------------------------------------------
            if (term, lang) in IDENTITY_FIXES:
                for ver, section in PLACEMENT[term]:
                    st = replace_value(lang, ver, section, term, value, dry)
                    if st == "replaced":
                        report[term]["yaml_replaced"] += 1
            else:
                for ver, section in PLACEMENT[term]:
                    st = insert_key(lang, ver, section, term, value, dry)
                    if st == "inserted":
                        report[term]["yaml_inserted"] += 1

    # ------------------------------------------------------------------ report
    print("\n==================== SUMMARY ====================")
    for term in TERMS:
        r = report[term]
        print(f"\n{term}:")
        print(f"  selected set/updated : {r['selected']}")
        print(f"  already selected     : {r['already_selected']}")
        print(f"  yaml inserted        : {r['yaml_inserted']}")
        print(f"  yaml replaced        : {r['yaml_replaced']}")
        if r["no_value"]:
            print(f"  NO VALUE ({len(r['no_value'])}): {r['no_value']}")
        if r["skipped_collision"]:
            print(f"  COLLISIONS SKIPPED ({len(r['skipped_collision'])}):")
            for c in r["skipped_collision"]:
                print(f"     {c}")

    # Fold the WAL into the tracked translations.db so a standalone run leaves a
    # consistent, git-visible artifact (don't rely on implicit close-checkpoint).
    if not dry:
        db._get_connection().execute("PRAGMA wal_checkpoint(TRUNCATE)")

    # Fail loudly if the backfill is incomplete, so CI/automation can catch it.
    incomplete = {
        t: r
        for t in TERMS
        for r in [report[t]]
        if r["skipped_collision"] or r["no_value"]
    }
    if incomplete:
        print(
            f"\nINCOMPLETE: {sorted(incomplete)} had skipped collisions or "
            f"missing values — see report above."
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
