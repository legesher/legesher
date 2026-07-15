"""Migrate the v1 translations database to the concept-centric v2 schema (CORE-1501).

Read-only with respect to the source. Writes a NEW database file; ``translations.db``
is never opened for writing (pack regeneration is unsafe until CORE-1400 lands, and
the v1 file stays the operational source until the cutover gate passes).

The migration is additive and reversible in six steps:

1. **Reference** -- programming languages, and locales keyed by BCP 47 (CORE-1500).
2. **Concepts** -- one concept per v1 term, 1:1. The 183 terms have 183 distinct
   names, so the mapping is unambiguous; concept *merging* across programming
   languages is a later, deliberate curation act, never automatic.
3. **Corpus** -- v1 ``translations`` become ``options`` + ``option_provenance``.
   The option's identity is the rendering, not the source that proposed it, so
   rows that re-attest the same word collapse into one option with several
   provenance rows.
4. **Endorsements** -- reconstructed from the community-reviewed rows that name a
   *person*, and ONLY where that person actually asserted the word. The private
   source key is their **GitHub username**, not the v1 handle: a first name is
   ambiguous, it collides, and it changes (:data:`CONTRIBUTOR_IDENTITY_MAP`).
   Contributor ids stay OPAQUE (``c_`` + 16 hex, salted digest) and the mapping
   lives only in ``contributor_identities``, which is never exported.

   Three classes of v1 ``created_by`` mint provenance but NEVER an endorsement:
   pipeline/pack labels (:data:`NON_HUMAN_CREATED_BY`); the words a review
   *rejected* (:data:`SUPERSEDED_BY_REVIEW` -- ``<name>_review_old`` is the
   pack's prior word, not the reviewer's own); and identities that name a person
   but not *one* person (``unresolved:``).
5. **Validation** -- a REAL pass (:func:`validate_surface`) over every option, not
   a stamp. The reserved ``validator_version = 'migration-seed'`` is rejected by
   the canon trigger for exactly this reason.
6. **Canon** -- v1 ``selected_translations`` become ``canon_selections``, *subject
   to the gate*: a selection whose rendering fails validation is refused and
   reported, not shipped. They are then written out as
   ``libs/i18n/canon/<locale>.toml`` (the PR-reviewable source of truth from then
   on).

Every step reconciles row counts and prints the ledger. Nothing is dropped: a
low-quality v1 translation becomes a low-quality *option*, which the corpus keeps
by design and the canon refuses to ship (the CORE-1400 reframe).

Usage:
    LEGESHER_CONTRIBUTOR_SALT=<secret> \\
    python scripts/migrate_to_v2.py --source legesher_i18n/db/translations.db \\
                                    --target build/translations_v2.db [--publish]
"""

from __future__ import annotations

import argparse
import keyword
import os
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from legesher_i18n.db.schema_v2 import (  # noqa: E402
    DEFAULT_CONTRIBUTOR_SALT,
    MIN_PUBLISH_SALT_LENGTH,
    apply_schema_v2,
    contributor_id,
    endorsement_uid,
    normalize_surface_form,
    option_uid,
    salt_fingerprint,
)
from legesher_i18n.script_policy import (  # noqa: E402
    ALWAYS_ALLOWED_SCRIPTS,
    has_policy,
    policy_for,
    scripts_of,
)

#: v1 language codes with no `bcp47` value in the database, and the tag they
#: resolve to. CORE-1500 owns the authoritative, IANA-verified backfill; this map
#: exists so the migration is runnable today and fails loudly on anything new.
BCP47_FALLBACK: dict[str, str] = {
    "ne": "ne",  # Nepali
    "sw": "sw",  # Swahili
    "tl": "tl",  # Tagalog
    "uk": "uk",  # Ukrainian
    "xh": "xh",  # Xhosa
}

#: v1 `source` vocabulary -> v2 provenance source. v1 mixed *where a row came
#: from* with *who asserted it*; v2 separates them.
SOURCE_MAP: dict[str, str] = {
    "aya": "model",
    "claude": "model",
    "claude_agent": "model",
    "machine-composed": "model",
    "yaml-import": "import",
    "yaml_pack": "import",
    "community": "community",
    "community_review": "community",
}

#: v1 sources that represent a *person* asserting a rendering. Only these mint
#: endorsements -- a model proposes, it does not endorse.
ENDORSING_SOURCES: frozenset[str] = frozenset({"community_review"})

#: v1 `created_by` values that are NOT PEOPLE. They sit in `community_review`
#: rows next to real reviewers, but they are pipeline / pack labels: a batch job
#: that lifted words out of the `universal_python` pack, a QA sweep, a
#: language-family batch. Minting endorsements from them corrupts the exact
#: number this whole design exists to make meaningful -- "how many *people* said
#: this word". They become `source='import'` provenance with the label in
#: `source_detail` (which the schema already anticipates: "'aya', 'claude',
#: 'yaml_pack', 'universal_python'"), no contributor, no endorsement.
NON_HUMAN_CREATED_BY: frozenset[str] = frozenset(
    {
        "universal_python",  # 24 rows — lifted from the universal_python pack
        "latino_lang",  # 11 rows — Romance-language batch
        "quality_review",  # 5 rows  — QA sweep
        "quality_review_old",  # 5 rows  — the same sweep, earlier pack generation
    }
)

#: Prefix marking a v1 `created_by` label that names a PERSON but cannot be
#: resolved to ONE person. Such a label is not a usable identity: see
#: :data:`CONTRIBUTOR_IDENTITY_MAP`. Greppable from both sides of the private
#: boundary -- `contributor_identities.source_key` and
#: `option_provenance.source_detail`.
UNRESOLVED_PREFIX = "unresolved:"


@dataclass(frozen=True)
class Identity:
    """The PRIVATE identity a v1 ``created_by`` label resolves to.

    ``github_handle`` is the source key, and ``None`` means UNRESOLVED -- a label
    that names a person but not *which* person, or not *one* person.
    """

    github_handle: str | None
    display_name: str | None = None
    note: str = ""

    @property
    def resolved(self) -> bool:
        return self.github_handle is not None

    def source_key(self, created_by: str) -> str:
        """The private natural key the opaque contributor id is minted from."""
        if self.github_handle is None:
            return f"{UNRESOLVED_PREFIX}{created_by}"
        return self.github_handle


#: v1 `created_by` label -> the person behind it, keyed by GITHUB USERNAME.
#:
#: The v1 label is a bad key: `zh_reviewer_review` is a first name, first names are
#: ambiguous, they collide, and they change. A GitHub username is stable, unique
#: and verifiable, so it -- not the label -- is what `contributor_identities.
#: source_key` holds and what the opaque `c_<hash>` is minted from. (The PUBLIC
#: id is unchanged: it stays the opaque digest. Only the private key improves.)
#:
#: ONLY labels that record a person's OWN assertion belong here. The `_old`
#: twins do NOT -- see :data:`SUPERSEDED_BY_REVIEW`, which is the more serious
#: half of this fix.
#:
#: THIS MAP IS EXPLICIT ON PURPOSE. A heuristic (strip `_old`, strip `_review`)
#: would silently mis-merge a future contributor whose handle happens to end that
#: way -- and, as it turns out, would also have merged a reviewer with the words
#: she REJECTED. An unknown label RAISES (:func:`resolve_identity`); it is never
#: guessed at.
CONTRIBUTOR_IDENTITY_MAP: dict[str, Identity] = {
    # zh review: NextME14's 31 suggested replacements. These are the words she
    # asserted, and they are the words the pack ships.
    "zh_reviewer_review": Identity("NextME14", "NextME14"),
    # ur review: the 2 applied suggestions the ur CHANGELOG credits to @rafaym1
    # by name (`type`: قسم -> نوعیت, `userwarning`: صارفانتباہ -> صارفاطلاع).
    "ur_reviewer_review": Identity("rafaym1"),
    # ur_modern alternatives (English transliterations in Urdu script).
    # RESOLVED by Madison (2026-07-14): this is sarr266 (@sarr266), ONE person --
    # "rafaym1" in the label names the pack her alternatives responded to, not a
    # co-author of the rows. (The ur CHANGELOG credits "@sarr266 & @rafaym1"
    # because the REVIEW ROUND was joint; the `alt_ur_modern` rows are hers.)
    "alt_ur_modern": Identity("sarr266", "sarr266"),
}

#: v1 `created_by` label -> the review label that DISPLACED it.
#:
#: *** These rows are the word the reviewer REJECTED. ***
#:
#: `<name>_review_old` is not "the same person, one pack generation earlier". It
#: is the rendering that was in the pack BEFORE that person's review, i.e. the
#: word their review replaced. The data says so unambiguously, from two
#: independent directions:
#:
#:   * zh, 31 term pairs: `_old` NEVER equals `_new` (0/31); `_new` is ALWAYS the
#:     value in `selected_translations` (31/31); `_old` NEVER is (0/31).
#:   * ur: `ur_reviewer_review_old` holds قسم and صارفانتباہ -- character for character
#:     the two words the PUBLIC ur CHANGELOG records as REPLACED
#:     ("`type` (builtin): `قسم` -> `نوعیت`").
#:
#: Treating them as the reviewer's own attestation -- which both the original
#: migration and a naive `_old`-strip merge do -- mints 33 endorsements that
#: record two real native speakers as having endorsed the exact words they threw
#: out. That is a worse corruption of the endorsement count than double-counting:
#: it inverts it.
#:
#: v2 already models this correctly and needs no new machinery. The schema is
#: explicit that endorsements are POSITIVE only and that "disagreement is
#: expressed by endorsing a different option" -- which is precisely what NextME14
#: did: she disagreed with 假 by endorsing 错误. So the superseded word stays in
#: the corpus as an option (it really did ship once -- that is evidence), with
#: `import` provenance under the NEUTRAL label
#: :data:`SUPERSEDED_SOURCE_DETAIL`, and it mints NO contributor and NO
#: endorsement. The v1 label itself (`zh_reviewer_review_old`) contains a real first
#: name, and `option_provenance` is a CORPUS-layer table with no publish gate
#: over it -- the schema's contract is that `contributors.id` is the ONLY
#: identity column the corpus exports, so the label must not ride along in
#: `source_detail`. The audit trail (which label, which review displaced it)
#: lives here, in this map, on the private side of the boundary.
SUPERSEDED_BY_REVIEW: dict[str, str] = {
    "zh_reviewer_review_old": "zh_reviewer_review",  # 31 zh words NextME14 replaced
    "ur_reviewer_review_old": "ur_reviewer_review",  # 2 ur words @rafaym1 replaced
}

#: The neutral `source_detail` for superseded pack words. Deliberately carries
#: no trace of WHOSE review displaced the word: `SELECT ... WHERE source_detail
#: = 'superseded_pack_word'` still answers the audit question ("which options
#: are pre-review pack words?") without exporting a name fragment.
SUPERSEDED_SOURCE_DETAIL = "superseded_pack_word"

#: The legacy `community` rows (`created_by` NULL) came from
#: `legesher/legesher-translations` -- a PUBLIC, MIT-licensed repository (created
#: 2019) with 149 contributors in its `.all-contributorsrc`.
#:
#: MIT permits relicensing but REQUIRES the copyright and permission notice be
#: retained. Recording the origin on every one of those rows is what makes that
#: obligation machine-visible (`SELECT ... WHERE source_detail =
#: 'legesher-translations'`) instead of folklore that survives only as long as
#: the person who remembers it. The dataset card MUST carry the attribution.
LEGACY_COMMUNITY_SOURCE_DETAIL = "legesher-translations"
LEGACY_COMMUNITY_LICENSE = "MIT"
LEGACY_COMMUNITY_REPO = "https://github.com/legesher/legesher-translations"

#: Rung assigned to endorsements reconstructed from v1. These reviewers pre-date
#: the ladder, so they are imported at the lowest non-zero rung and can be
#: promoted later; back-dating them to `certified` would fabricate authority.
IMPORT_RUNG = "contributor"

#: The validator that actually runs (see :func:`validate_surface`). It is a real
#: version string, NOT the reserved 'migration-seed' -- the canon trigger rejects
#: that value precisely so a stamped row can never pass for a checked one. Bumped
#: to v2 for the CORE-1514 fixes: term-aware identifiers, the SARA-AM NFKC delta
#: class, and real locale-aware script-consistency.
VALIDATOR_VERSION = "py-identifier-v2"

#: Printed after every run, and enforced by ``--publish`` where it can be.
#:
#: Items 1 and 2 are the ones that are UNRECOVERABLE if they are got wrong, so
#: ``--publish`` refuses to run rather than trusting the reader.
PRE_PUBLISH_CHECKLIST = f"""\
PRE-PUBLISH CHECKLIST (the first HF push freezes all of this)

  1. THE SALT IS IMMUTABLE FOREVER, AND ESCROWED.  [--publish enforces]
     contributor_id = c_ + HMAC-SHA256(key=salt, msg=source_key)[:16 hex].
     The salt must be SECRET, and
     it must also be PERMANENT: if it is ever lost, rotated, or regenerated after
     the first publish, EVERY contributor_id changes, every endorsement re-keys,
     the corpus FORKS, and every contributor's history is orphaned. There is no
     recovery -- you can never again mint a matching id for a returning
     contributor, because you cannot reproduce the digest.
       - generate ONCE:  python -c "import secrets; print(secrets.token_hex(32))"
       - store in a secret manager, BACK IT UP, and NEVER ROTATE IT
       - it is not a credential you can cycle; it is a primary-key ingredient
       - every built DB records sha256(salt)[:16] in the private build_meta
         table: before pushing, verify it matches the escrowed salt's
         fingerprint (schema_v2.salt_fingerprint) so a dev-salt or wrong-salt
         artifact can never be published by accident

  2. NO UNRESOLVED CONTRIBUTOR IDENTITY.  [--publish enforces]
     A `{UNRESOLVED_PREFIX}*` source_key means one label, two humans (see
     CONTRIBUTOR_IDENTITY_MAP). Publishing it would either half-count or
     double-count real people. BLOCKER: Madison must split it.

  3. MIT ATTRIBUTION FOR THE LEGACY CORPUS.  [manual -- the dataset card]
     The `community` rows come from {LEGACY_COMMUNITY_REPO}
     ({LEGACY_COMMUNITY_LICENSE}, 149 contributors in its .all-contributorsrc).
     MIT permits relicensing but REQUIRES the copyright and permission notice be
     retained. The dataset card MUST carry that notice and credit the repo and
     its contributors. The row count carrying the obligation is in the ledger.

  4. contributor_identities IS NEVER EXPORTED.  [CORE-1502]
     It is the only way back from an opaque id to a person.
"""


@dataclass
class Ledger:
    """Row-count reconciliation between the v1 source and the v2 target."""

    counts: dict[str, int] = field(default_factory=dict)

    def record(self, key: str, value: int) -> None:
        self.counts[key] = value

    def report(self) -> str:
        width = max(len(k) for k in self.counts)
        return "\n".join(f"  {k.ljust(width)}  {v:>7,}" for k, v in self.counts.items())


@dataclass(frozen=True)
class Validation:
    """The mechanical verdict on one rendering."""

    identifier_valid: bool
    nfkc_stable: bool
    #: WHY the value is NFKC-unstable, or None when it is stable. A fact, kept
    #: separate from the canon policy that acts on it (see validate_surface).
    nfkc_delta_class: str | None
    script_consistent: bool
    collides_en_keyword: bool


#: The Thai SARA AM character and its NFKC decomposition (NIKHAHIT + SARA AA).
#: U+0E33 is the ONLY source of NFKC instability across the 25 refused Thai
#: selections, and CPython NFKC-normalizes identifiers (PEP 3131), so both
#: spellings are one identifier at runtime -- no spoofing surface.
_SARA_AM = "ำ"
_SARA_AM_NFKC = unicodedata.normalize("NFKC", _SARA_AM)  # "ํา"

#: Base scripts for the DB languages that do NOT ship a pack yet, so the v2
#: validator can classify their options. ``script_policy.SCRIPT_POLICIES`` is
#: keyed to shipped packs only (``tests/test_script_policy_coverage.py`` forbids
#: orphan entries), so these live here until they ship. Same set as
#: :data:`BCP47_FALLBACK`.
NON_PACK_SCRIPTS: dict[str, frozenset[str]] = {
    "ne": frozenset({"Devanagari"}),  # Nepali
    "sw": frozenset({"Latin"}),  # Swahili
    "tl": frozenset({"Latin"}),  # Tagalog
    "uk": frozenset({"Cyrillic"}),  # Ukrainian
    "xh": frozenset({"Latin"}),  # Xhosa
}


def allowed_scripts_for(code: str) -> frozenset[str] | None:
    """Resolve the Unicode scripts a locale's identifiers may legitimately use.

    Reads the shared, default-deny ``script_policy`` table -- the single source
    of truth the pack auditor also uses, so the v2 validator and the pack audit
    finally agree on what "foreign script" means -- falling back to
    :data:`NON_PACK_SCRIPTS` for the handful of DB-only languages. Returns
    ``None`` for an un-policied code, which the script check treats as a
    violation, never a silent pass.

    Args:
        code: The v1 two-letter language code (``th``, ``ja``, ``no``).

    Returns:
        The allowed scripts, or ``None`` if the code has no policy.
    """
    if has_policy(code):
        return policy_for(code).scripts
    return NON_PACK_SCRIPTS.get(code)


def _is_identifier_char(char: str) -> bool:
    """Whether ``char`` may appear inside a Python identifier (letters/digits/_)."""
    return char == "_" or char.isalnum()


def _structural_affixes(term_name: str) -> tuple[str, str]:
    """The leading/trailing NON-identifier characters the source term carries.

    A faithful translation of ``except*`` (PEP 654) must keep the trailing
    ``*``; the identifier check validates the *stem* and requires the surface to
    mirror these affixes. Today ``except*`` is the only term that exercises this,
    but the logic generalizes to any structural affix (a future ``*args``). A
    term that is already a valid identifier -- every dunder included -- has none.
    """
    start = 0
    while start < len(term_name) and not _is_identifier_char(term_name[start]):
        start += 1
    end = len(term_name)
    while end > start and not _is_identifier_char(term_name[end - 1]):
        end -= 1
    return term_name[:start], term_name[end:]


def _identifier_valid(surface: str, term_name: str) -> bool:
    """Term-aware Python-identifier check.

    A plain ``str.isidentifier()`` refuses ``except*`` in every locale forever
    (the literal ``*``) and would blanket-accept a stray ``*`` on any other term.
    Instead, carry the structural affixes of the SOURCE term: the surface must
    mirror them exactly, and the stem between them must be a valid identifier.
    """
    prefix, suffix = _structural_affixes(term_name)
    if not surface.startswith(prefix) or not surface.endswith(suffix):
        return False
    if len(surface) < len(prefix) + len(suffix):
        return False
    stem = (
        surface[len(prefix) : len(surface) - len(suffix)]
        if suffix
        else surface[len(prefix) :]
    )
    return stem.isidentifier()


def _nfkc_delta_class(surface: str) -> str | None:
    """Classify WHY ``surface`` is NFKC-unstable -- a fact, not a policy.

    ``None`` when already NFKC-stable. ``'sara-am-only'`` when the ONLY unstable
    character is U+0E33 (Thai SARA AM) and decomposing it reproduces the NFKC
    form exactly -- legitimate Thai orthography CPython itself normalizes
    (PEP 3131), so there is no spoofing surface. ``'other'`` for any other
    instability, which stays a hard block.
    """
    nfkc = unicodedata.normalize("NFKC", surface)
    if nfkc == surface:
        return None
    unstable = {c for c in surface if unicodedata.normalize("NFKC", c) != c}
    if unstable == {_SARA_AM} and surface.replace(_SARA_AM, _SARA_AM_NFKC) == nfkc:
        return "sara-am-only"
    return "other"


def _script_consistent(surface: str, allowed_scripts: frozenset[str] | None) -> bool:
    """Real, per-character, locale-aware script-consistency.

    Every letter's script must fall within the locale's allowlist (``Common``
    and ``Inherited`` are always allowed). This is the honest version of the old
    ``len(scripts) <= 1`` heuristic, which was wrong in both directions: it
    passed an NFKC-stable Cyrillic-in-Thai confusable, and it flagged legitimate
    Japanese (Han + Kana). An un-policied locale is default-deny.
    """
    if allowed_scripts is None:
        return False
    present = scripts_of(surface) - ALWAYS_ALLOWED_SCRIPTS
    return present <= allowed_scripts


def validate_surface(
    surface: str, term_name: str, allowed_scripts: frozenset[str] | None
) -> Validation:
    """Run the mechanical checks the canon trigger gates on.

    This is the honest version of what the migration used to *stamp*. The
    previous script wrote ``identifier_valid = 1, nfkc_stable = 1`` for every
    canon-bound row under ``validator_version = 'migration-seed'`` without
    running anything, which made the CORE-1400 gate circular: "pack_export
    reproduces all 5,136 selections" was true *because the gate was bypassed*.
    Two real defects were hiding under the stamp (Amharic ``ከቀረ*``, and 25
    NFKC-unstable Thai renderings) -- and the Q7 triage (CORE-1514) then found
    the honest v1 check was itself over- AND under-inclusive: it refused all 25
    of those Thai SARA-AM selections and every locale's ``except*``, while
    passing 12 of 15 mixed-script confusables. This v2 check fixes all three.

    Args:
        surface: The NFC-normalized rendering.
        term_name: The English source term (e.g. ``except*``), so the identifier
            check can carry the term's structural affixes.
        allowed_scripts: The Unicode scripts legitimate for this locale (see
            :func:`allowed_scripts_for`), or ``None`` for an un-policied locale.

    Returns:
        The verdict. ``identifier_valid`` is Python's own rule made term-aware;
        ``nfkc_delta_class`` records why an unstable value is unstable; and
        ``script_consistent`` is checked against the locale's real allowlist.
    """
    return Validation(
        identifier_valid=_identifier_valid(surface, term_name),
        nfkc_stable=unicodedata.normalize("NFKC", surface) == surface,
        nfkc_delta_class=_nfkc_delta_class(surface),
        script_consistent=_script_consistent(surface, allowed_scripts),
        collides_en_keyword=keyword.iskeyword(surface),
    )


def resolve_identity(created_by: str) -> Identity:
    """Map a v1 ``created_by`` label to the person behind it.

    Args:
        created_by: The raw v1 label (already known not to be in
            :data:`NON_HUMAN_CREATED_BY`).

    Returns:
        The identity, which may be UNRESOLVED (``github_handle is None``).

    Raises:
        SystemExit: on an unknown label. It is NOT guessed at, and it is NOT
            passed through as its own contributor: either is a silent decision
            about a real person's identity, taken by a script.
    """
    try:
        return CONTRIBUTOR_IDENTITY_MAP[created_by]
    except KeyError:
        raise SystemExit(
            f"unknown v1 created_by label {created_by!r}.\n"
            "Every label must be classified BY HAND, because every wrong answer "
            "is silent:\n"
            "  * a person             -> CONTRIBUTOR_IDENTITY_MAP, with their "
            "GitHub username\n"
            "  * a pipeline / pack    -> NON_HUMAN_CREATED_BY\n"
            "  * a word a review REPLACED -> SUPERSEDED_BY_REVIEW\n"
            "A heuristic (strip '_old' / '_review') would mis-merge two humans "
            "into one\ncontributor, AND would credit a reviewer with the word she "
            "rejected."
        ) from None


def scan_unresolved_identities(src: sqlite3.Connection) -> set[str]:
    """Find the v1 labels that would block ``--publish``, without building anything.

    Applies the same classification the build loop applies -- non-human labels
    and superseded-review labels never mint a contributor, only community-kind
    rows resolve an identity -- but over ``SELECT DISTINCT`` instead of the full
    table, so ``--publish`` can refuse *before* the target database exists.
    An unknown label exits here too, via :func:`resolve_identity`.

    Args:
        src: Read-only connection to the v1 database.

    Returns:
        The v1 ``created_by`` labels whose identity is unresolved.
    """
    labels: set[str] = set()
    for row in src.execute("SELECT DISTINCT created_by, source FROM translations"):
        created_by = (row["created_by"] or "").strip()
        if not created_by:
            continue
        if created_by in NON_HUMAN_CREATED_BY or created_by in SUPERSEDED_BY_REVIEW:
            continue
        if SOURCE_MAP.get(row["source"], "import") != "community":
            continue
        if not resolve_identity(created_by).resolved:
            labels.add(created_by)
    return labels


def require_publishable_salt(salt: str | None) -> str:
    """Refuse to mint published contributor ids with a salt that cannot hold.

    The salt is not a rotatable credential -- it is an ingredient of a PRIMARY
    KEY. ``contributor_id = c_ + HMAC-SHA256(key=salt, msg=source_key)``, so a salt that is
    public is reversible (the GitHub usernames it keys are, by definition,
    enumerable), and a salt that is later lost or rotated re-keys every
    contributor and FORKS the corpus.

    Args:
        salt: The salt supplied for this run, if any.

    Returns:
        The salt, when it is fit to publish with.

    Raises:
        SystemExit: if the salt is absent, is the public dev salt, or is short
            enough to brute-force against a known username list.
    """
    if not salt:
        raise SystemExit(
            "--publish requires --contributor-salt / $LEGESHER_CONTRIBUTOR_SALT."
        )
    if salt == DEFAULT_CONTRIBUTOR_SALT:
        raise SystemExit(
            f"--publish refuses the PUBLIC dev salt ({DEFAULT_CONTRIBUTOR_SALT!r}).\n"
            "It is in this repository, so every contributor id minted with it is "
            "reversible\nby a dictionary attack over the (public) GitHub usernames "
            "it keys."
        )
    if len(salt) < MIN_PUBLISH_SALT_LENGTH:
        raise SystemExit(
            f"--publish requires a salt of at least {MIN_PUBLISH_SALT_LENGTH} "
            f"characters (got {len(salt)}).\n"
            "The source keys are GitHub usernames -- public and enumerable -- so "
            "the salt is\nthe ONLY thing standing between the published corpus and "
            "a re-identification\nattack. Generate it once:\n"
            '    python -c "import secrets; print(secrets.token_hex(32))"\n'
            "then escrow it: it can never be rotated (see PRE_PUBLISH_CHECKLIST)."
        )
    return salt


def _locale_tag(code: str, bcp47: str | None) -> str:
    """Resolve a v1 two-letter code to its BCP 47 tag."""
    if bcp47:
        return bcp47
    if code in BCP47_FALLBACK:
        return BCP47_FALLBACK[code]
    raise SystemExit(
        f"language {code!r} has no bcp47 tag and no fallback. "
        "Add it to BCP47_FALLBACK or complete the CORE-1500 backfill first."
    )


def _split_tag(tag: str) -> tuple[str, str | None, str | None]:
    """Split a canonical BCP 47 tag into (language, script, region).

    The subtag columns are derived from the TAG, never from v1's ``script``
    column: that column holds a script *name* (``'Arabic'``, ``'Latin'``), not an
    ISO 15924 subtag (``Arab``, ``Latn``), and the previous migration wrote it
    straight into ``locales.script_subtag`` -- a column documented as ISO 15924.
    The CHECK constraint on that column is what surfaced it.

    Under BCP 47 the script subtag is also *omitted* when it is the language's
    suppress-script default (``ar``, not ``ar-Arab``), so the tag -- not the
    language's writing system -- is the only correct source.
    """
    parts = tag.split("-")
    language, rest = parts[0], parts[1:]
    script = rest.pop(0) if rest and len(rest[0]) == 4 else None
    region = rest.pop(0) if rest else None
    return language, script, region


def migrate(
    source: Path, target: Path, *, salt: str | None = None, publish: bool = False
) -> Ledger:
    """Build a v2 database from a v1 database.

    Args:
        source: Path to the v1 ``translations.db``. Opened read-only.
        target: Path for the new v2 database. Must not already exist.
        salt: Salt for minting opaque contributor ids. Defaults to
            ``$LEGESHER_CONTRIBUTOR_SALT``, then to the public dev salt.
        publish: Build a database intended for the Hugging Face push. Every
            one-way door is checked BEFORE it is walked through: the salt must be
            secret, long, and permanent (:func:`require_publishable_salt`), and no
            contributor identity may still be unresolved. A warning is not enough
            for either -- both are unrecoverable once the corpus is out.

    Returns:
        The reconciliation ledger.

    Raises:
        SystemExit: in publish mode, if the salt is unfit or any contributor
            identity is unresolved.
    """
    if publish:
        require_publishable_salt(salt)
    if target.exists():
        raise SystemExit(f"refusing to overwrite {target}")
    target.parent.mkdir(parents=True, exist_ok=True)

    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row

    if publish:
        # Every one-way door is checked BEFORE the target exists. Checking
        # after the build (the previous behavior) left a fully-built,
        # real-salt-minted artifact on disk on refusal -- exactly the file
        # that must never be around to publish by accident.
        pre_unresolved = scan_unresolved_identities(src)
        if pre_unresolved:
            src.close()
            labels = ", ".join(repr(label) for label in sorted(pre_unresolved))
            raise SystemExit(
                f"--publish REFUSED before building: unresolved contributor "
                f"identity ({labels}) would be frozen into the published "
                "corpus. Resolve it in CONTRIBUTOR_IDENTITY_MAP first. "
                "No target database was created."
            )

    dst = sqlite3.connect(target)
    apply_schema_v2(dst)

    ledger = Ledger()

    effective_salt = (
        salt
        if salt is not None
        else os.environ.get("LEGESHER_CONTRIBUTOR_SALT", DEFAULT_CONTRIBUTOR_SALT)
    )
    dst.executemany(
        "INSERT INTO build_meta (key, value) VALUES (?, ?)",
        [
            ("salt_fingerprint", salt_fingerprint(effective_salt)),
            ("publish_build", "1" if publish else "0"),
            ("source_db", source.name),
        ],
    )

    # -- 1. Reference --------------------------------------------------------
    dst.execute(
        "INSERT INTO programming_languages (code, name, status) VALUES ('python', 'Python', "
        "'shipping')"
    )

    locale_of: dict[str, str] = {}
    language_rows = {
        _locale_tag(row["code"], row["bcp47"]): row
        for row in src.execute("SELECT * FROM languages")
    }
    # Parents before children: parent_tag is a self-referential FK.
    for tag in sorted(language_rows, key=lambda t: (t.count("-"), t)):
        row = language_rows[tag]
        locale_of[row["code"]] = tag
        language, script, region = _split_tag(tag)
        parent = tag.rsplit("-", 1)[0] if "-" in tag else None
        dst.execute(
            "INSERT INTO locales (tag, parent_tag, language_subtag, script_subtag, "
            "region_subtag, name, native_name, direction, numeral_system, "
            "has_case_distinction, status, in_registry) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                tag,
                parent if parent in language_rows else None,
                language,
                script,
                region,
                row["name"],
                row["native_name"],
                row["direction"] or "ltr",
                row["numeral_system"],
                row["has_case_distinction"]
                if row["has_case_distinction"] is not None
                else 1,
                row["status"] or "experimental",
                row["in_registry"] or 0,
            ),
        )
    ledger.record("locales", len(locale_of))

    # -- 2. Concepts (1:1 with v1 terms) -------------------------------------
    # definition_en is seeded empty and backfilled from the 183 context briefs by
    # a separate pass; it is NOT NULL in the schema, so a placeholder marks the
    # debt explicitly rather than hiding it.
    concept_of_term: dict[int, tuple[int, str]] = {}
    #: v2 concept id -> the English source term (e.g. 'except*'). The identifier
    #: validator is term-aware, so it needs the token, not just the slug (which
    #: has lost the structural '*': 'except*' -> slug 'except*' but dunders map
    #: '_' -> '-'). Kept as the real term name.
    term_name_of_concept: dict[int, str] = {}
    for row in src.execute("SELECT * FROM terms ORDER BY id"):
        slug = row["name"].strip().lower().replace("_", "-")
        cur = dst.execute(
            "INSERT INTO concepts (slug, definition_en, category) VALUES (?, ?, ?)",
            (
                slug,
                row["description"]
                or f"TODO: seed from context/python/{row['name']}.md",
                row["category"],
            ),
        )
        concept_id = int(cur.lastrowid or 0)
        concept_of_term[row["id"]] = (concept_id, slug)
        term_name_of_concept[concept_id] = row["name"]
        dst.execute(
            "INSERT INTO terms (concept_id, programming_language, name, category, subcategory, "
            "version_added) VALUES (?, 'python', ?, ?, ?, ?)",
            (
                concept_id,
                row["name"],
                row["category"],
                row["subcategory"],
                row["version_added"],
            ),
        )
        dst.execute(
            "INSERT INTO concept_briefs (concept_id, tier, path) VALUES (?, 1, ?)",
            (concept_id, f"libs/i18n/context/python/{row['name']}.md"),
        )
    ledger.record("concepts", len(concept_of_term))
    ledger.record("terms", len(concept_of_term))

    # -- 3. Corpus: options + provenance -------------------------------------
    v1_translation_rows = 0
    options_seen: dict[str, str] = {}
    #: option uid -> (concept id, v1 language code), so the validation pass can
    #: recover the term name (for term-aware id checks) and the locale's script
    #: policy without re-joining. One option is always one (concept, locale).
    option_meta: dict[str, tuple[int, str]] = {}
    contributors: dict[str, str] = {}  # SOURCE KEY (github username) -> c_<hex>
    unresolved: dict[str, int] = defaultdict(int)  # v1 label -> rows it holds
    endorsements: dict[tuple[str, str], str] = {}
    provenance_by_option: dict[str, int] = defaultdict(int)
    non_human_rows = 0
    superseded_rows = 0
    legacy_mit_rows = 0

    for row in src.execute("SELECT * FROM translations ORDER BY id"):
        v1_translation_rows += 1
        concept_id, slug = concept_of_term[row["term_id"]]
        locale = locale_of[row["language_code"]]
        surface = normalize_surface_form(row["translation"])
        if not surface:
            continue
        uid = option_uid(slug, locale, surface)
        option_meta.setdefault(uid, (concept_id, row["language_code"]))

        if uid not in options_seen:
            dst.execute(
                "INSERT INTO options (uid, concept_id, locale, surface_form, first_seen_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (uid, concept_id, locale, surface, row["created_at"]),
            )
            options_seen[uid] = surface

        source_kind = SOURCE_MAP.get(row["source"], "import")
        created_by = (row["created_by"] or "").strip()
        source_detail = row["source"]
        contributor: str | None = None
        identity: Identity | None = None

        if created_by in NON_HUMAN_CREATED_BY:
            # A pipeline label, not a person: it must not become a contributor and
            # must not mint an endorsement. Keep the label as provenance.
            source_kind = "import"
            source_detail = created_by
            non_human_rows += 1
        elif created_by in SUPERSEDED_BY_REVIEW:
            # The word the reviewer REJECTED (see SUPERSEDED_BY_REVIEW). It stays
            # in the corpus -- it really shipped once, and that is evidence -- but
            # it is the PACK's word, not the reviewer's. Endorsing it here would
            # record a native speaker as endorsing the word she threw out. Her
            # disagreement is already expressed, exactly as the schema intends, by
            # the endorsement she DOES have on the replacement. The neutral label
            # (not created_by) is deliberate: the v1 label embeds a first name and
            # option_provenance is corpus-layer -- see SUPERSEDED_SOURCE_DETAIL.
            source_kind = "import"
            source_detail = SUPERSEDED_SOURCE_DETAIL
            superseded_rows += 1
        elif source_kind == "community" and not created_by:
            # The 2,169 legacy rows. They carry no author because they were lifted
            # wholesale from legesher/legesher-translations (MIT, 149 contributors).
            # Recording the origin ON THE ROW is what makes the MIT attribution
            # obligation queryable rather than folklore.
            source_detail = LEGACY_COMMUNITY_SOURCE_DETAIL
            legacy_mit_rows += 1
        elif source_kind == "community":
            identity = resolve_identity(created_by)
            source_key = identity.source_key(created_by)
            if not identity.resolved:
                # One label, TWO humans. The rows are kept -- they are real
                # evidence of a real rendering -- but they mint no endorsement,
                # because a single contributor_id standing for two people would
                # half-count them both. Marked on BOTH sides of the private
                # boundary so it cannot be lost: source_detail here, source_key in
                # contributor_identities. --publish refuses while it is open.
                source_detail = source_key
                unresolved[created_by] += 1

            contributor = contributors.get(source_key)
            if contributor is None:
                # Opaque id, minted from the GITHUB USERNAME rather than the v1
                # first-name label. The public id is unchanged in kind (an opaque
                # digest); what improves is the private key it is derived from --
                # stable, unique, verifiable. The mapping lives ONLY in
                # contributor_identities, which is never exported.
                contributor = contributor_id(source_key, salt=salt)
                dst.execute(
                    "INSERT INTO contributors (id, current_rung) VALUES (?, ?)",
                    (contributor, IMPORT_RUNG),
                )
                dst.execute(
                    "INSERT INTO contributor_identities (contributor_id, source_key, "
                    "display_name, github_handle) VALUES (?, ?, ?, ?)",
                    (
                        contributor,
                        source_key,
                        identity.display_name,
                        identity.github_handle,
                    ),
                )
                contributors[source_key] = contributor

        dst.execute(
            "INSERT INTO option_provenance (option_uid, source, source_detail, model_version, "
            "contributor_id, word_type, word_form, confidence, rationale, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                uid,
                source_kind,
                source_detail,
                row["model_version"],
                contributor,
                row["word_type"],
                row["word_form"],
                row["confidence"],
                row["model_rationale"],
                row["created_at"],
            ),
        )
        provenance_by_option[uid] += 1

        # -- 4. Endorsements -------------------------------------------------
        # An endorsement is a claim about ONE person, so it needs an identity that
        # names one: `identity.resolved` is the gate. The (uid, contributor) key
        # dedupes multiple attestations of the same option by the same resolved
        # person (two v1 rows, same word, same human -> ONE endorsement). Note
        # `_old` labels never reach this branch at all: SUPERSEDED_BY_REVIEW rows
        # are the words a review REJECTED and mint no endorsement (0/31 of them
        # even equal the reviewer's word), so there is nothing to collapse.
        if (
            row["source"] in ENDORSING_SOURCES
            and contributor
            and identity is not None
            and identity.resolved
        ):
            key = (uid, contributor)
            if key not in endorsements:
                eid = endorsement_uid(uid, contributor, "import", row["created_at"])
                endorsements[key] = eid
                dst.execute(
                    "INSERT INTO endorsements (uid, option_uid, contributor_id, method, "
                    "rung_at_endorsement, created_at) VALUES (?, ?, ?, 'import', ?, ?)",
                    (eid, uid, contributor, IMPORT_RUNG, row["created_at"]),
                )

    resolved_people = len(contributors) - len(unresolved)
    ledger.record("v1 translation rows", v1_translation_rows)
    ledger.record("options", len(options_seen))
    ledger.record("option_provenance", sum(provenance_by_option.values()))
    ledger.record("contributors (people)", resolved_people)
    ledger.record("  UNRESOLVED identities", len(unresolved))
    ledger.record("pipeline-label rows", non_human_rows)
    ledger.record("superseded-by-review rows", superseded_rows)
    ledger.record("MIT-attributed rows", legacy_mit_rows)
    ledger.record("endorsements", len(endorsements))

    # -- 5. Validation (a REAL pass, over the whole corpus) --------------------
    # Not a stamp. `validator_version = 'migration-seed'` is rejected by the canon
    # trigger precisely so that a seeded row can never be mistaken for a validated
    # one; what runs here is validate_surface(), and whatever it finds, it reports.
    invalid_identifier = 0
    nfkc_unstable = 0
    sara_am_only = 0
    script_inconsistent = 0
    for uid, surface in options_seen.items():
        concept_id, code = option_meta[uid]
        verdict = validate_surface(
            surface, term_name_of_concept[concept_id], allowed_scripts_for(code)
        )
        invalid_identifier += not verdict.identifier_valid
        nfkc_unstable += not verdict.nfkc_stable
        sara_am_only += verdict.nfkc_delta_class == "sara-am-only"
        script_inconsistent += not verdict.script_consistent
        dst.execute(
            "INSERT INTO option_validations (option_uid, validator_version, identifier_valid, "
            "nfkc_stable, nfkc_delta_class, script_consistent, collides_en_keyword) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                uid,
                VALIDATOR_VERSION,
                int(verdict.identifier_valid),
                int(verdict.nfkc_stable),
                verdict.nfkc_delta_class,
                int(verdict.script_consistent),
                int(verdict.collides_en_keyword),
            ),
        )
    ledger.record("options validated", len(options_seen))
    ledger.record("  invalid identifier", invalid_identifier)
    ledger.record("  NFKC-unstable", nfkc_unstable)
    ledger.record("    of which SARA-AM only", sara_am_only)
    ledger.record("  script-inconsistent", script_inconsistent)

    # -- 6. Canon ------------------------------------------------------------
    # The gate is now real, so it bites: a v1 selection whose rendering fails
    # validation is REFUSED, and reported. It is not silently shipped, and it is
    # not silently dropped either -- the option stays in the corpus as evidence,
    # which is the CORE-1400 reframe working exactly as designed.
    selected_rows = 0
    canon_rows = 0
    rejected: list[tuple[str, str, str, str]] = []
    for row in src.execute("SELECT * FROM selected_translations ORDER BY id"):
        selected_rows += 1
        concept_id, slug = concept_of_term[row["term_id"]]
        code = row["language_code"]
        locale = locale_of[code]
        surface = normalize_surface_form(row["translation"])
        uid = option_uid(slug, locale, surface)
        if uid not in options_seen:
            # Cannot happen against the current data (verified: 0 of 5,136 selected
            # values are absent from the candidate table), but the canon FK makes it
            # a hard error rather than a silent orphan.
            raise SystemExit(
                f"selected value not present as an option: {slug}/{locale}/{surface}"
            )

        # The exact same rule the SQL trigger enforces (trg_canon_requires_valid_
        # identifier): identifier-valid AND script-consistent AND (NFKC-stable OR
        # SARA-AM only). Reported reason is the FIRST failing check, in that order.
        verdict = validate_surface(
            surface, term_name_of_concept[concept_id], allowed_scripts_for(code)
        )
        nfkc_ok = verdict.nfkc_stable or verdict.nfkc_delta_class == "sara-am-only"
        if not (verdict.identifier_valid and verdict.script_consistent and nfkc_ok):
            if not verdict.identifier_valid:
                reason = "not a valid identifier"
            elif not verdict.script_consistent:
                reason = "mixed / foreign script"
            else:
                reason = "NFKC-unstable"
            rejected.append((locale, slug, surface, reason))
            continue

        dst.execute(
            "INSERT INTO canon_selections (concept_id, locale, option_uid, surface_form, status, "
            "decided_by, decided_at, decision_reason, source_file) "
            "VALUES (?, ?, ?, ?, 'machine', ?, ?, ?, ?)",
            (
                concept_id,
                locale,
                uid,
                surface,
                row["selected_by"],
                row["selected_at"],
                row["selection_reason"],
                f"libs/i18n/canon/{locale}.toml",
            ),
        )
        canon_rows += 1

    ledger.record("v1 selected rows", selected_rows)
    ledger.record("canon_selections", canon_rows)
    ledger.record("canon REFUSED by gate", len(rejected))

    dst.commit()
    src.close()
    dst.close()

    if rejected:
        print("\nCanon selections REFUSED by the CORE-1400 gate (they stay in the")
        print("corpus as options; they are simply not shipped):\n")
        for locale, slug, surface, reason in rejected:
            print(f"  {locale:<6} {slug:<28} {surface!r:<30} {reason}")
        print()

    if superseded_rows:
        print(
            f"\nNOT ENDORSED: {superseded_rows} rows are words a review REJECTED.\n"
            "  `<name>_review_old` holds the rendering that was in the pack BEFORE "
            "that\n  person's review -- the word they replaced -- not an earlier "
            "attestation of\n  their own. (zh: `_old` never equals `_new`, 0/31, and "
            "`_new` is always the\n  shipped word, 31/31. ur: `ur_reviewer_review_old` is "
            "قسم / صارفانتباہ, exactly the\n  two words the public ur CHANGELOG "
            "records as REPLACED.)\n"
            "  Endorsing them would record two native speakers as endorsing the "
            "words they\n  threw out. They stay as options with `import` provenance; "
            "the reviewers'\n  disagreement is already expressed -- as the schema "
            "intends -- by the\n  endorsement they DO have on the replacement."
        )

    if legacy_mit_rows:
        print(
            f"\nATTRIBUTION: {legacy_mit_rows:,} rows carry an MIT obligation.\n"
            f"  They come from {LEGACY_COMMUNITY_REPO}\n"
            f"  ({LEGACY_COMMUNITY_LICENSE}; 149 contributors in its "
            ".all-contributorsrc). MIT permits\n"
            "  relicensing but REQUIRES the copyright and permission notice be "
            "retained,\n"
            "  so the dataset card MUST credit the repo and its contributors.\n"
            "  Machine-visible as: option_provenance.source_detail = "
            f"{LEGACY_COMMUNITY_SOURCE_DETAIL!r}"
        )

    if unresolved:
        print("\n*** BLOCKER: UNRESOLVED CONTRIBUTOR IDENTITY ***\n")
        for label, rows in sorted(unresolved.items()):
            note = CONTRIBUTOR_IDENTITY_MAP[label].note
            print(f"  {label!r}: {rows} rows, 0 endorsements minted")
            print(f"    {note}")
        print(
            "\n  These rows STAY in the corpus as options + community provenance --\n"
            "  they are real renderings that real people offered. What they do NOT do\n"
            "  is mint an endorsement, because one contributor_id cannot stand for two\n"
            "  humans: it would half-count them both, and the endorsement count is the\n"
            "  one number this whole design exists to make trustworthy.\n"
            "\n  Madison must resolve this. --publish refuses until she does."
        )
        if publish:
            raise SystemExit(
                "\n--publish REFUSED: an unresolved contributor identity would be "
                "frozen into the\npublished corpus. Resolve it in "
                "CONTRIBUTOR_IDENTITY_MAP first."
            )

    return ledger


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path, required=True, help="v1 translations.db (read-only)"
    )
    parser.add_argument(
        "--target", type=Path, required=True, help="new v2 database to create"
    )
    parser.add_argument(
        "--contributor-salt",
        default=None,
        help=(
            "secret salt for minting opaque contributor ids. Defaults to "
            "$LEGESHER_CONTRIBUTOR_SALT, then to the PUBLIC dev salt. The run "
            "that produces the published corpus MUST pass a secret one, and that "
            "salt can NEVER be rotated afterwards -- see --publish."
        ),
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help=(
            "build a database intended for the Hugging Face push. HARD-FAILS "
            "(rather than warning) on the public dev salt, a short salt, or an "
            "unresolved contributor identity -- each of which is unrecoverable "
            "once the corpus is out."
        ),
    )
    args = parser.parse_args()

    salt = args.contributor_salt or os.environ.get("LEGESHER_CONTRIBUTOR_SALT")
    if not salt and not args.publish:
        print(
            "WARNING: no --contributor-salt / $LEGESHER_CONTRIBUTOR_SALT. Falling back\n"
            f"         to the PUBLIC dev salt ({DEFAULT_CONTRIBUTOR_SALT!r}). The v1\n"
            "         handles are in this repo's git history, so contributor ids minted\n"
            "         with it are reversible by dictionary attack. Fine for a local run;\n"
            "         NOT fine for the database that gets pushed to Hugging Face --\n"
            "         --publish refuses it outright.\n"
        )

    ledger = migrate(args.source, args.target, salt=salt, publish=args.publish)
    print("Migration ledger:")
    print(ledger.report())
    print()
    print(PRE_PUBLISH_CHECKLIST)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
