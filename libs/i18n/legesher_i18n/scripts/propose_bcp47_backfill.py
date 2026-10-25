#!/usr/bin/env python3
"""Assign each language its canonical BCP 47 locale tag, and flag the ones we
cannot decide mechanically.

This is **not** a one-shot migration script, despite its name and origin. It
answers a question we ask every time a language is onboarded: *what is this
language's canonical tag, and does a human need to decide something?* The
56-language backfill (CORE-1500) is simply its first run. The 103-language
expansion (CORE-674) will ask it 47 more times.

The judgment it encodes:

1. Look the language up in the vendored IANA registry.
2. Does it carry a ``Suppress-Script``? Then the bare tag is *provably*
   canonical and no script subtag is added.
3. No ``Suppress-Script``? Then a script subtag is a real question, and it is
   answered from **shipped pack content**, not assumption (``zh`` is Simplified
   because the pack is; ``sr`` is Cyrillic because the pack is).
4. Cannot answer it from either? **Raise.** A bare tag must never carry an
   unverified "no script contrast" claim — that is a false negative wearing a
   confident rationale, and it is exactly what would mis-tag ``az`` (Latn/Arab/
   Cyrl), ``ku`` (Latn/Arab) and ``sd`` (Arab/Deva) during the expansion.

Emits ``legesher_i18n/db/migrations/bcp47_backfill.tsv``: one row per language,
mapping today's ``code`` to the tag proposed as its key.

**Read-only against the database.** It writes a TSV for human review; it never
touches ``translations.db``. (Pack regeneration is unsafe until CORE-1400, and
the key promotion is a one-way door — the promote step follows the CORE-1500
migration runbook, which is not part of this repo.)

Every column except ``proposed_tag`` and ``rationale`` is derived: from the DB,
or from the vendored IANA registry via :mod:`legesher_i18n.bcp47`. Only the
handful of genuinely editorial calls are hardcoded here, in
:data:`EDITORIAL_DECISIONS`, each with the reason it is editorial. That split is
the point: it keeps "what the standard says" separable from "what Legesher
chose", so a reviewer can check the former mechanically and argue about the
latter.

Usage:
    uv run python libs/i18n/legesher_i18n/scripts/propose_bcp47_backfill.py
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
I18N_PKG = SCRIPT_DIR.parent
OUTPUT = I18N_PKG / "db" / "migrations" / "bcp47_backfill.tsv"

sys.path.insert(0, str(I18N_PKG.parent))

from legesher_i18n import bcp47  # noqa: E402
from legesher_i18n.db import TranslationDatabase  # noqa: E402


class UnresolvedScriptError(ValueError):
    """A bare tag was about to be proposed for a language whose script is unsettled.

    Raised when the registry sets no ``Suppress-Script`` on the proposed tag's
    language *and* no editorial entry says what to do about it. The default rule
    ("shortest code, no script") would otherwise emit a bare tag carrying a
    machine-generated rationale that asserts "no script contrast" — a claim
    nobody checked, and one that is false for e.g. ``az`` (Latn/Arab/Cyrl),
    ``ku`` (Latn/Arab), or ``sd`` (Arab/Deva). Those are exactly the languages
    the 103-language target adds, so the failure must be loud.
    """


# The editorial calls. Everything not listed here takes the default rule:
#
#   proposed_tag = code
#
# which is correct for any language whose registry record carries a
# Suppress-Script (the script is implied, so adding it is wrong) and which has no
# competing written standard. That default covers 49 of the 56 rows.
#
# A language lands here only if one of three things is true:
#   (a) the registry sets NO Suppress-Script and the language has a live script
#       contrast that the pack content actually resolves (sr, uz, mn, zh);
#   (b) the primary subtag itself is under-specified — a macrolanguage whose
#       written standards differ materially (no -> nb);
#   (c) the language identity is contested (tl vs fil).
#
# Each entry's rationale cites the *evidence*, not an assumption: for the script
# cases, the scripts actually present in the shipped 3.10 pack values.
#
# A language with no Suppress-Script that is in NEITHER this dict nor
# NO_SCRIPT_DESPITE_NO_SUPPRESS raises UnresolvedScriptError. There is no silent
# default for the script question.
EDITORIAL_DECISIONS: dict[str, tuple[str, str]] = {
    "zh": (
        "zh-Hans",
        "No Suppress-Script; zh is a macrolanguage with a live Hans/Hant split. "
        "The shipped pack is unambiguously Simplified (错误, 无, 类, 继续, 异步 — "
        "all simplified forms), so the bare tag under-specifies it. zh-Hans is a "
        "registered, non-deprecated tag. Leaves zh-Hant free for a future pack.",
    ),
    "sr": (
        "sr-Cyrl",
        "No Suppress-Script; Serbian is actively digraphic (Cyrillic + Latin, both "
        "official). Pack values are 100% Cyrillic (Нетачно, Ништа, класа). sr-Cyrl "
        "is a registered, non-deprecated tag. Leaves sr-Latn free.",
    ),
    "uz": (
        "uz-Latn",
        "No Suppress-Script; Uzbek is digraphic (Latin official since 1993, "
        "Cyrillic still in wide use). Pack values are 100% Latin (O'zbek: va, "
        "sifatida, sinf). uz-Latn is a registered, non-deprecated tag.",
    ),
    "mn": (
        "mn-Cyrl",
        "No Suppress-Script; Mongolian is written in Cyrillic (Mongolia) and "
        "Mongolian script (Inner Mongolia). Pack values are 100% Cyrillic (Худал, "
        "Хоосон, анги). mn-Cyrl is a registered, non-deprecated tag.",
    ),
    "no": (
        "nb",
        "DECIDED nb (Madison, 2026-07-15). 'no' is a macrolanguage over two written standards, "
        "Bokmål (nb) and Nynorsk (nn) — this is a language-subtag question, not a "
        "script one (the registry does set Suppress-Script: Latn on 'no'). The "
        "shipped pack is Bokmål (klassen, fortsette, definisjon). The DB's bcp47 "
        "column already says 'nb'. Changing the key changes the published PyPI "
        "dist name, which is why the pack directory is decoupled from the key: "
        "current_pack_dir stays 'no' while a NEW pack would get 'nb'.",
    ),
    "tl": (
        "fil",
        "DECIDED fil (Madison, 2026-07-15). tl = Tagalog (the individual language); fil = Filipino "
        "(the standardized national language, Tagalog-based, what 'Philippines "
        "localization' normally means; CLDR treats tl as an alias for fil). Both "
        "are valid, live registry entries. The pack shipped with pack id tl, name "
        "Filipino and iso639_2 fil (CORE-2479, 2026-10-25).",
    ),
}

# Languages with no Suppress-Script that nonetheless take NO script subtag. The
# registry's silence is not an instruction to add one (RFC 5646 section 4.1: add
# a script subtag only where it *distinguishes*), so these are called out
# explicitly rather than left to look like an oversight.
#
# Keyed by the *proposed tag's* language subtag, not by the DB code — the script
# question belongs to the tag being proposed. That is why `fil` appears here and
# `tl` does not: `tl` has Suppress-Script: Latn, but the tag Legesher would
# actually adopt is `fil`, which does not.
NO_SCRIPT_DESPITE_NO_SUPPRESS: dict[str, str] = {
    "gd": (
        "No Suppress-Script, but Scottish Gaelic has no live script contrast — it "
        "is written in Latin only. Adding gd-Latn would distinguish nothing."
    ),
    "su": (
        "No Suppress-Script. Sundanese has a script contrast in principle (Latin "
        "vs. Sundanese script, Sund), but Latin is the overwhelmingly dominant "
        "modern orthography and the pack is Latin. DECIDED bare tag (Madison, "
        "2026-07-15); su-Latn stays free for a future Sundanese-script pack."
    ),
    "fil": (
        "No Suppress-Script on 'fil' (unlike 'tl', which has Suppress-Script: Latn), "
        "but Filipino has no live script contrast — modern Filipino is written in "
        "Latin only, and Baybayin is historic/ceremonial, not an orthography a pack "
        "would target. fil-Latn would distinguish nothing."
    ),
}

# Rows whose *proposal* is a recommendation awaiting Madison, not a settled call.
# EMPTY since 2026-07-15: the three open calls ('no' -> nb, 'tl' -> fil, 'su'
# bare tag) were all decided as recommended; each rationale records the
# decision. The mechanism stays: a future language whose proposal is a
# recommendation goes in this set, and the TSV's needs_review column follows it
# rather than sniffing the rationale text for a marker.
NEEDS_REVIEW: frozenset[str] = frozenset()

COLUMNS = (
    "code",
    "name",
    "current_bcp47",
    "proposed_tag",
    "script",
    "suppress_script",
    "script_subtag_used",
    "macrolanguage",
    "in_registry",
    "has_pack",
    "current_pack_dir",
    "default_slug_if_new",
    "decision",
    "needs_review",
    "rationale",
)


def default_slug(tag: str) -> str:
    """Map a locale tag to the directory/module slug a **new** pack would get.

    The pack directory name is not free-form: it becomes a Python module name
    (``legesher_i18n_{target}_{slug}``) and a PyPI distribution name
    (``legesher-i18n-{target}-{slug}``). ``zh-Hans`` is therefore not usable as a
    directory name — ``legesher_i18n_python_zh-Hans`` is not a valid identifier.

    Slug rule: lowercase, ``-`` -> ``_``. This is injective over valid locale
    tags (a tag's subtags never contain ``_``), so the mapping is reversible and
    two distinct tags can never collide on one directory.

    This is emphatically **not** the directory an *existing* pack lives in. The
    packs for ``zh`` and ``no`` ship from ``language-packs/python/zh/`` and
    ``.../no/`` and stay there (renaming ``no/`` renames a published PyPI dist);
    the TSV records that separately, in ``current_pack_dir``. A loader must key
    on ``current_pack_dir`` for a pack that already ships, and on
    ``default_slug_if_new`` only when creating one.

    Args:
        tag: A canonical locale tag, e.g. ``"zh-Hans"``.

    Returns:
        The slug a new pack for *tag* would get, e.g. ``"zh_hans"``.
    """
    return tag.lower().replace("-", "_")


def resolve_proposal(code: str) -> tuple[str, str]:
    """Resolve one language code to its proposed tag and the rationale for it.

    Pure: reads the IANA registry, not the DB, so it can be exercised against any
    code — including ones Legesher does not ship yet.

    Args:
        code: The DB's current language code, e.g. ``"zh"``.

    Returns:
        Tuple of (proposed canonical tag, rationale).

    Raises:
        UnresolvedScriptError: If the proposal would be a bare tag for a language
            the registry gives no ``Suppress-Script``, and no editorial entry has
            answered the script question for it.
        ValueError: If the proposed tag is not canonical (the validator and the
            proposal must never disagree).
    """
    if code in EDITORIAL_DECISIONS:
        proposed, rationale = EDITORIAL_DECISIONS[code]
    else:
        proposed, rationale = code, ""

    parsed = bcp47.parse(proposed)
    suppressed = bcp47.suppressed_script(parsed.language)

    if parsed.script is not None:
        # A script subtag is only ever written by an editorial decision, which
        # carries its own evidence-citing rationale.
        pass
    elif suppressed is not None:
        # The default rule: the registry itself says the script is implied.
        rationale = rationale or (
            f"Registry sets Suppress-Script: {suppressed}, so the script is "
            f"implied by the language subtag and adding it would be "
            f"non-canonical. Shortest ISO 639 code, no script, no region."
        )
    else:
        # A bare tag for a language the registry does NOT settle. Somebody has to
        # have looked; the default rule is not allowed to assert it.
        note = NO_SCRIPT_DESPITE_NO_SUPPRESS.get(parsed.language)
        if note is None:
            raise UnresolvedScriptError(
                f"{code!r} would be proposed as the bare tag {proposed!r}, but the "
                f"registry sets no Suppress-Script on {parsed.language!r} and no "
                f"editorial entry answers the script question for it. A bare tag "
                f"here would assert 'no script contrast' that nobody checked. "
                f"Resolve it: add {parsed.language!r} to EDITORIAL_DECISIONS (with "
                f"the script subtag the pack content resolves, as for sr/uz/mn/zh), "
                f"or to NO_SCRIPT_DESPITE_NO_SUPPRESS (with the reason it takes no "
                f"script subtag, as for gd/su)."
            )
        rationale = f"{rationale} {note}".strip()

    if not rationale:
        raise UnresolvedScriptError(
            f"no rationale was produced for {code!r} -> {proposed!r}; every "
            f"proposed tag must carry the reason it takes the form it does"
        )

    # Fail loudly rather than emit a proposal the validator would reject.
    issues = bcp47.check_canonical(proposed)
    if issues:
        raise ValueError(
            f"proposed tag {proposed!r} for {code!r} is not canonical: "
            + "; ".join(str(issue) for issue in issues)
        )

    return proposed, rationale


def build_rows() -> list[dict[str, str]]:
    """Build one proposal row per language in the DB.

    Returns:
        Rows in ``code`` order, keyed by :data:`COLUMNS`.
    """
    db = TranslationDatabase()
    try:
        languages = sorted(db.get_languages(), key=lambda row: row["code"])
    finally:
        db.close()

    rows: list[dict[str, str]] = []
    for language in languages:
        code = language["code"]
        current = language["bcp47"] or ""
        has_pack = bool(language["has_yaml_pack"])

        proposed, rationale = resolve_proposal(code)
        parsed = bcp47.parse(proposed)
        suppressed = bcp47.suppressed_script(parsed.language)

        rows.append(
            {
                "code": code,
                "name": language["name"],
                "current_bcp47": current or "NULL",
                "proposed_tag": proposed,
                "script": parsed.script or suppressed or "-",
                "suppress_script": suppressed or "-",
                "script_subtag_used": "yes" if parsed.script else "no",
                "macrolanguage": (
                    "yes" if bcp47.is_macrolanguage(parsed.language) else "no"
                ),
                "in_registry": str(int(bool(language["in_registry"]))),
                "has_pack": str(int(has_pack)),
                # Where the pack lives TODAY. Packs are named for the code they
                # shipped under, and they do not move: the key changes, the
                # directory does not — the directory feeds a Python module name
                # and a published PyPI dist, so it is a semantics-free slug.
                "current_pack_dir": code if has_pack else "-",
                "default_slug_if_new": default_slug(proposed),
                "decision": "keep" if proposed == code else "change",
                "needs_review": "yes" if code in NEEDS_REVIEW else "no",
                "rationale": rationale.replace("\t", " ").replace("\n", " "),
            }
        )

    return rows


def render_tsv(rows: list[dict[str, str]]) -> str:
    """Render the proposal rows as a TSV document with a provenance header."""
    header = [
        "# CORE-1500 — proposed BCP 47 locale tags for translations.db `languages`.",
        f"# Validated against the IANA Language Subtag Registry snapshot "
        f"{bcp47.registry_file_date()}.",
        "# `script` is the effective ISO 15924 script: the subtag when one is used,",
        "# otherwise the registry's Suppress-Script (implied, not written); '-' where",
        "# the registry provides neither (gd, su — Latin by convention, not by rule).",
        "# `macrolanguage` describes the PROPOSED tag's primary subtag, so the `no`",
        "# row says 'no': the proposal is nb (an individual language), even though",
        "# the code it replaces is the macrolanguage no.",
        "# `current_pack_dir` is where the pack lives TODAY (it does not move; '-' = no",
        "# pack). `default_slug_if_new` is the directory a NEW pack for the proposed tag",
        "# would get. They differ exactly where the key moves but the pack does not",
        "# (no, zh) — a loader keys on current_pack_dir for a pack that already ships.",
        "# AUTO-GENERATED. Regenerate with:",
        "#   uv run python libs/i18n/legesher_i18n/scripts/propose_bcp47_backfill.py",
        "\t".join(COLUMNS),
    ]
    for row in rows:
        header.append("\t".join(row[column] for column in COLUMNS))
    return "\n".join(header) + "\n"


def main() -> int:
    """Regenerate the backfill proposal TSV."""
    rows = build_rows()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render_tsv(rows), encoding="utf-8")

    changed = [row for row in rows if row["decision"] == "change"]
    review = [row for row in rows if row["needs_review"] == "yes"]
    moves = ", ".join(f"{row['code']} -> {row['proposed_tag']}" for row in changed)
    pending = ", ".join(row["code"] for row in review)

    stays = [
        row
        for row in rows
        if row["current_pack_dir"] not in ("-", row["default_slug_if_new"])
    ]
    kept_dirs = ", ".join(
        f"{row['current_pack_dir']}/ (key {row['proposed_tag']})" for row in stays
    )

    print(f"Wrote {len(rows)} rows to {OUTPUT}")
    print(f"  {len(changed)} tags differ from today's code: {moves}")
    if review:
        print(f"  {len(review)} need Madison's decision: {pending}")
    else:
        print("  0 need Madison's decision (all editorial calls decided)")
    print(
        f"  {len(stays)} packs keep a directory that no longer matches the key: "
        f"{kept_dirs}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
