"""Migrate the v1 translations database to the concept-centric v2 schema (CORE-1501).

Read-only with respect to the source. Writes a NEW database file; ``translations.db``
is never opened for writing (pack regeneration is unsafe until CORE-1400 lands, and
the v1 file stays the operational source until the cutover gate passes).

The migration is additive and reversible in six steps:

1. **Reference** -- programming languages, and locales keyed by BCP 47 (CORE-1500).
2. **Concepts** -- deduped by slug ACROSS programming languages: python ``break``
   and javascript ``break`` are one concept with a per-PL ``terms`` row each
   (the concept layer's whole point -- a shared word never re-runs translation
   + review per target). Within ONE PL, a token naming two constructs (python
   ``type``: builtin + the 3.12 soft keyword) splits into two concepts via a
   category-suffixed slug, the second ``terms`` row riding as
   ``export_role='secondary'``. ``definition_en`` seeds from the v1
   description, else the term's context brief, else an explicit TODO marker.
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

Every step reconciles row counts and prints the ledger. Nothing in the six
steps is dropped: a low-quality v1 translation becomes a low-quality *option*,
which the corpus keeps by design and the canon refuses to ship (the CORE-1400
reframe).

EXCEPTION — the messages partition (CORE-1679): message_templates /
message_translations rows living in the operational v1 database (activated by
activate_messages_partition.py) are NOT migrated by this script; a v2 build
starts with the partition empty and must be re-seeded from the catalog seeds
(seed_message_templates.py). To make that gap impossible to trip over
silently, the migration REFUSES a source that carries message rows unless
--acknowledge-message-rows-not-migrated is passed.

Usage:
    LEGESHER_DATA_REPO=<path-to-private-data-repo-checkout> \\
    LEGESHER_CONTRIBUTOR_SALT=<secret> \\
    python scripts/migrate_to_v2.py --source legesher_i18n/db/translations.db \\
                                    --target build/translations_v2.db [--publish]

LEGESHER_DATA_REPO points at the checkout of the private data repository whose
``identity/contributor_identity_map.json`` holds the label -> person map
(CORE-1794); without it the map loads EMPTY and every human ``created_by``
label refuses the build. ``LEGESHER_IDENTITY_MAP`` may name the JSON directly.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
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
    is_identity_translation,
    normalize_surface_form,
    option_uid,
    salt_fingerprint,
)
from legesher_i18n.surface_validation import (  # noqa: E402
    VALIDATOR_VERSION,
    Validation,
    allowed_format_chars_for,
    allowed_scripts_for,
    validate_surface,
)

# Re-exported because tests/test_v2_validation_gate.py imports them from here:
# this script was the validators' home before CORE-1688 moved them into the
# package so the importer could run the same checks.
__all__ = [
    "VALIDATOR_VERSION",
    "Validation",
    "allowed_format_chars_for",
    "allowed_scripts_for",
    "validate_surface",
]

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
#:
#: The v2 vocabulary is cut on ONE question -- **what do we owe for this row?**
#: -- because `source` is the only provenance column the corpus publishes
#: (`source_detail` is private). See `option_provenance` in
#: docs/schema-v2-reference.md for the full rationale, and CORE-1720 for why the previous
#: pipeline-origin cut had to go: it hid two other projects' work inside a
#: 13,650-row `import` bucket, and nothing in the *published* vocabulary said
#: "someone else's licence applies here".
#:
#: EXHAUSTIVE over the v1 vocabulary on purpose -- see :func:`classify_source`.
#:
#: The four values, and the obligation each one records:
#:
#:   legesher   our own work                     nothing beyond the dataset licence
#:   upstream   another open-source project      retain their notice, credit them
#:   community  an individual via native review  credit / withdrawal on request
#:   model      machine-generated                disclose which model
#:
#: Mirrors the CHECK on `option_provenance.source` in schema_v2.sql. The schema
#: is the floor -- it refuses the retired vocabulary outright rather than
#: trusting this module to be careful.
PUBLIC_SOURCES: frozenset[str] = frozenset(
    {"legesher", "upstream", "community", "model"}
)

SOURCE_MAP: dict[str, str] = {
    # machine-generated -- disclose which machine
    "aya": "model",
    # CORE-1866 regeneration (CohereLabs/aya-101, Apache-2.0). The key is the
    # pipeline's model-registry key -- the run loop writes source=<registry key>,
    # not get_model_name().
    "aya101-hf": "model",
    "claude": "model",
    "claude_agent": "model",
    # our own work -- nothing owed beyond the dataset licence
    "yaml-import": "legesher",
    "yaml_pack": "legesher",
    "core-1318-fix": "legesher",
    "core-1763-fix": "legesher",  # our own QA sweep: corruption-class term replacements
    # CORE-2079: candidate rows restored where a selection had been repaired
    # without its candidate (the CORE-1883 star-mirror restore and the
    # CORE-1905 audit replacements). The values were already chosen through
    # our own selection layer; the restored rows are our own bookkeeping, so
    # nothing is owed beyond the dataset licence.
    "selection-repair": "legesher",
    # NOT `model`: these were composed BY US from existing pack material
    # (CORE-1303/1317), not generated by a model. Calling them `model` would
    # overstate the machine involvement in words a human assembled.
    "machine-composed": "legesher",
    # NOT `community`: the 2,169 `source='community'` rows all carry a NULL
    # author because they were lifted wholesale from a DIFFERENT PROJECT --
    # legesher/legesher-translations -- and what we owe them is that project's
    # notice, not an individual's credit-and-withdrawal rights. See
    # LEGACY_COMMUNITY_SOURCE_DETAIL.
    "community": "upstream",
    # an individual through our native-review process
    "community_review": "community",
}


def classify_source(v1_source: str) -> str:
    """The v2 obligation bucket for a v1 ``source`` value.

    RAISES on an unknown value rather than defaulting. An obligation cannot be
    defaulted: every silent fallback picks a bucket, and the only bucket a
    fallback could pick without asserting something false about a stranger's
    work is one that claims *we* authored it. That is exactly how
    ``core-1318-fix`` (87 rows) rode the old ``.get(..., "import")`` default
    into the grab-bag without anyone deciding it belonged there.

    A new v1 source is a governance question -- "what do we owe for it?" -- so
    it stops the migration until a human answers it here.

    Args:
        v1_source: The ``translations.source`` value.

    Returns:
        One of ``legesher`` / ``upstream`` / ``community`` / ``model``.

    Raises:
        SystemExit: when the value is not in :data:`SOURCE_MAP`.
    """
    try:
        return SOURCE_MAP[v1_source]
    except KeyError:
        raise SystemExit(
            f"Unknown v1 translation source {v1_source!r}.\n"
            "The v2 `source` vocabulary is an OBLIGATION cut, not a pipeline "
            "label, so a new\nsource cannot be defaulted -- decide what it "
            "obliges us to do and add it to\nSOURCE_MAP in "
            f"{Path(__file__).name}:\n"
            "  legesher  -- our own work; nothing owed beyond the dataset licence\n"
            "  upstream  -- another open-source project's work; retain their "
            "notice, credit them\n"
            "  community -- an individual via native review; credit on request, "
            "withdrawal on request\n"
            "  model     -- machine-generated; disclose which model"
        ) from None


#: v1 sources that represent a *person* asserting a rendering. Only these mint
#: endorsements -- a model proposes, it does not endorse.
ENDORSING_SOURCES: frozenset[str] = frozenset({"community_review"})

#: v1 `created_by` values that are NOT PEOPLE -> the obligation bucket each one
#: belongs to. They sit in `community_review` rows next to real reviewers, but
#: they are pipeline / pack labels: a batch job that lifted words out of another
#: project's pack, a QA sweep. Minting endorsements from them corrupts the exact
#: number this whole design exists to make meaningful -- "how many *people* said
#: this word" -- so none of them mints a contributor or an endorsement; the
#: label goes in `source_detail` (which the schema already anticipates: "'aya',
#: 'claude', 'yaml_pack', 'universal_python'").
#:
#: The bucket is per-label, not per-set, because these four labels split across
#: TWO obligations. Two of them are OTHER PROJECTS' work and are the reason
#: CORE-1720 exists: under the old cut they landed in `import` alongside our own
#: packs, so the published corpus never said a third-party licence applied.
#: Their licences are verified (2026-08-05); the card credits them and the
#: NOTICE file beside it retains their text:
#: UniversalPython is Apache-2.0, Latino is MIT.
NON_HUMAN_CREATED_BY: dict[str, str] = {
    "universal_python": "upstream",  # 24 rows (ur) — UniversalPython, Apache-2.0
    "latino_lang": "upstream",  # 11 rows (es) — Latino, MIT
    "quality_review": "legesher",  # 5 rows  — our own QA sweep
    "quality_review_old": "legesher",  # 5 rows  — the same sweep, earlier pack generation
}

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


@dataclass(frozen=True)
class Withdrawn:
    """A contributor who asked to be forgotten (CORE-1780).

    Replaces that person's :class:`Identity` in :data:`CONTRIBUTOR_IDENTITY_MAP`.

    It carries the OPAQUE id and NOT the username, and that is the whole point.
    The map is the durable store of who a v1 label is (a `withdrawn` entry in
    the data home's contributor_identity_map.json since CORE-1794), and it is
    re-read on every rebuild. Leaving the username there under a "withdrawn"
    flag would mean nothing had been erased -- the mapping back to the person
    would simply be annotated. So the username goes, and the id it minted stays.

    Because the id is already published and opaque, keeping it costs the person
    nothing. What it buys is the two things withdrawal has to do at once:

    * their **endorsements survive** -- the id is what those rows key on, and
      other people's picks depend on those counts;
    * their **identity cannot come back** -- a rebuild has no username to mint
      from, so it cannot recreate the row it just erased.

    ``withdrawn_at`` is an ISO-8601 date, recorded for the same reason the DB
    column exists: to distinguish "this person withdrew" from "we have never
    heard of this person". A later import that meets a bundle still carrying the
    username can then detect the withdrawal rather than honour the bundle. See
    ``libs/i18n/docs/contributor-withdrawal-runbook.md``.
    """

    contributor_id: str
    withdrawn_at: str

    @property
    def resolved(self) -> bool:
        """Always ``True``: a withdrawal is a decision, not an open question.

        This matters because ``--publish`` refuses to build while any identity is
        UNRESOLVED. A withdrawal must not read as unresolved -- we know exactly
        who this was and we have deliberately forgotten them.
        """
        return True

    def source_key(self, created_by: str) -> str:
        """There is no natural key any more; the opaque id IS the key."""
        return self.contributor_id


#: The `consent_version` recorded for people who contributed BEFORE
#: `CONTRIBUTOR_PRIVACY.md` existed (CORE-1780, decided 2026-08-10).
#:
#: It is not a signature, and it must never be read as one. It means: *this
#: person contributed under the project's open-source terms before a
#: contributor notice existed, through a public pull request under their own
#: account, and was credited by handle in the pack CHANGELOGs at the time.*
#:
#: Recording it is the accurate answer to a question with three possible ones.
#: NULL would say nobody ever agreed to anything, which is false. `1.0` would
#: claim they accepted a document that did not exist. This says what actually
#: happened, and leaves the version column doing its job -- describing what a
#: person agreed to *at the time*, which is the only reason to version consent.
#:
#: It grants nothing. Everyone carrying it keeps `credit_preference =
#: 'anonymous'` (the column default), so nothing about them is published beyond
#: the opaque id, and withdrawal applies to them exactly as it does to anyone
#: else. Version 1.0 of the notice is FORWARD-LOOKING: it governs contributions
#: made after its publication.
PRE_NOTICE_CONSENT = "oss-pre-notice"

#: Contributor ids that are ALREADY PUBLISHED in the corpus.
#:
#: These are public values -- they ship in the `contributors` and `endorsements`
#: configs of `legesher/language-corpus` -- so listing them here discloses
#: nothing. What they are FOR is the one check a withdrawal cannot make for
#: itself.
#:
#: A :class:`Withdrawn` entry carries an id the migration cannot recompute: the
#: username it was minted from is gone, which is the point. So a typo, a
#: truncation, or an id minted under the wrong salt would be taken at face
#: value, and `contributor_id` is a PUBLISHED column -- the next push would
#: silently re-key that person's endorsements to an id belonging to nobody,
#: orphaning their real one. That is precisely the outcome CONTRIBUTOR_PRIVACY.md
#: and the dataset card promise cannot happen ("no revision of this dataset is
#: affected"), and every other one-way door in this script hard-fails rather
#: than trusting the operator.
#:
#: Update this set when a NEW contributor first appears in a published revision.
#: Nothing is removed on withdrawal: the id stays published and stays valid, and
#: it is the identity behind it that is erased.
PUBLISHED_CONTRIBUTOR_IDS: frozenset[str] = frozenset(
    {
        "c_0c841c2c564b8e7b",
        "c_21433bed09ebda0b",
        "c_fff76267e6885d43",
    }
)


def require_published_withdrawal_ids() -> None:
    """Refuse to publish while any ``Withdrawn`` names an unpublished id.

    Raises:
        SystemExit: if a :class:`Withdrawn` entry carries an id that is not in
            :data:`PUBLISHED_CONTRIBUTOR_IDS`.
    """
    unknown = {
        label: entry.contributor_id
        for label, entry in CONTRIBUTOR_IDENTITY_MAP.items()
        if isinstance(entry, Withdrawn)
        and entry.contributor_id not in PUBLISHED_CONTRIBUTOR_IDS
    }
    if unknown:
        listing = "\n".join(f"  {label} -> {cid}" for label, cid in unknown.items())
        raise SystemExit(
            "withdrawn contributor id is not one this corpus has published:\n"
            f"{listing}\n\n"
            "A withdrawal carries an id the migration CANNOT recompute -- the "
            "username it was minted from\nis gone. So this is the only check "
            "available, and it is not optional: `contributor_id` is a\n"
            "PUBLISHED column, and a wrong value silently re-keys that person's "
            "endorsements to an id\nbelonging to nobody while orphaning their "
            "real one.\n\n"
            "Either the id is wrong (recompute it from their username BEFORE "
            "erasing it -- runbook step 1),\nor they are a newer contributor "
            "whose id has since been published, in which case add it to\n"
            "PUBLISHED_CONTRIBUTOR_IDS in the same change."
        )


#: v1 `created_by` label -> the person behind it, keyed by GITHUB USERNAME.
#:
#: The v1 label is a bad key: several embed a reviewer's FIRST NAME, and first
#: names are ambiguous, they collide, and they change. A GitHub username is
#: stable, unique and verifiable, so it -- not the label -- is what
#: `contributor_identities.source_key` holds and what the opaque `c_<hash>` is
#: minted from. (The PUBLIC id is unchanged: it stays the opaque digest. Only
#: the private key improves.)
#:
#: THE MAP ITSELF IS PRIVATE DATA [CORE-1794]. The labels and the identities
#: they resolve to are exactly the PII the corpus design never exports, so the
#: entries live in the durable data home (`identity/contributor_identity_map
#: .json`), never in this tree. :func:`load_identity_maps` populates this dict
#: at import -- see it for the resolution order. It remains the durable store
#: re-read on every rebuild; only its address changed.
#:
#: ONLY labels that record a person's OWN assertion belong here. The `_old`
#: twins do NOT -- see :data:`SUPERSEDED_BY_REVIEW`, which is the more serious
#: half of this fix.
#:
#: THE MAP IS EXPLICIT ON PURPOSE. A heuristic (strip `_old`, strip `_review`)
#: would silently mis-merge a future contributor whose handle happens to end that
#: way -- and, as it turns out, would also have merged a reviewer with the words
#: she REJECTED. An unknown label RAISES (:func:`resolve_identity`); it is never
#: guessed at.
CONTRIBUTOR_IDENTITY_MAP: dict[str, Identity | Withdrawn] = {}

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
#:   * ur: the `_old` twin holds قسم and صارفانتباہ -- character for character
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
#: expressed by endorsing a different option" -- which is precisely what the zh
#: reviewer did: disagreed with 假 by endorsing 错误. So the superseded word stays in
#: the corpus as an option (it really did ship once -- that is evidence), with
#: `legesher` provenance -- it was OUR pack's word, and we owe nothing for it
#: beyond the dataset licence -- under the NEUTRAL label
#: :data:`SUPERSEDED_SOURCE_DETAIL`, and it mints NO contributor and NO
#: endorsement. The v1 label itself embeds a real first name, and
#: `option_provenance` is a CORPUS-layer table with no publish gate
#: over it -- the schema's contract is that `contributors.id` is the ONLY
#: identity column the corpus exports, so the label must not ride along in
#: `source_detail`. The audit trail (which label, which review displaced it)
#: lives here, in this map, on the private side of the boundary -- and because
#: the labels themselves are name-bearing, the entries live in the durable data
#: home alongside the identity map [CORE-1794], loaded by
#: :func:`load_identity_maps`.
SUPERSEDED_BY_REVIEW: dict[str, str] = {}

#: The neutral `source_detail` for superseded pack words. Deliberately carries
#: no trace of WHOSE review displaced the word: `SELECT ... WHERE source_detail
#: = 'superseded_pack_word'` still answers the audit question ("which options
#: are pre-review pack words?") without exporting a name fragment.
SUPERSEDED_SOURCE_DETAIL = "superseded_pack_word"


def load_identity_maps(path: Path | None = None) -> None:
    """(Re)populate the private identity maps from the durable data home.

    The maps are mutated IN PLACE so references already imported elsewhere
    (``from migrate_to_v2 import CONTRIBUTOR_IDENTITY_MAP``) stay live.

    Resolution order for the JSON file:

    1. an explicit ``path`` argument (tests, one-off overrides);
    2. ``$LEGESHER_IDENTITY_MAP`` -- a direct file path;
    3. ``$LEGESHER_DATA_REPO/identity/contributor_identity_map.json`` -- the
       checkout of the private data repository.

    A missing file leaves the maps EMPTY. That is deliberate fail-loud
    behaviour, not a default: every human label then raises in
    :func:`resolve_identity` instead of being guessed at, and the error says
    how to point the script at the data home. [CORE-1794]
    """
    if path is None:
        direct = os.environ.get("LEGESHER_IDENTITY_MAP")
        data_repo = os.environ.get("LEGESHER_DATA_REPO")
        if direct:
            path = Path(direct)
        elif data_repo:
            path = Path(data_repo) / "identity" / "contributor_identity_map.json"
    CONTRIBUTOR_IDENTITY_MAP.clear()
    SUPERSEDED_BY_REVIEW.clear()
    if path is None or not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    identities = data.get("identities", {})
    withdrawn = data.get("withdrawn", {})
    superseded = data.get("superseded_by_review", {})

    # Malformed entries fail LOUDLY, at load. A misspelt key silently becoming
    # Identity(None) would surface only at --publish as a spurious "unresolved
    # identity" pointing the operator at the wrong problem.
    for label, entry in identities.items():
        if not isinstance(entry, dict) or "github_handle" not in entry:
            raise SystemExit(
                f"identity map {path}: entry for {label!r} must be an object "
                "with a 'github_handle' key (null means UNRESOLVED)."
            )
        CONTRIBUTOR_IDENTITY_MAP[label] = Identity(
            entry["github_handle"],
            entry.get("display_name"),
            entry.get("note") or "",
        )
    for label, entry in withdrawn.items():
        if label in identities:
            raise SystemExit(
                f"identity map {path}: {label!r} appears in both 'identities' "
                "and 'withdrawn' -- a withdrawal REPLACES the identity entry."
            )
        if not isinstance(entry, dict) or not {
            "contributor_id",
            "withdrawn_at",
        } <= set(entry):
            raise SystemExit(
                f"identity map {path}: withdrawn entry for {label!r} needs "
                "'contributor_id' and 'withdrawn_at'."
            )
        CONTRIBUTOR_IDENTITY_MAP[label] = Withdrawn(
            entry["contributor_id"], entry["withdrawn_at"]
        )
    for old_label, displaced_by in superseded.items():
        if displaced_by not in CONTRIBUTOR_IDENTITY_MAP:
            raise SystemExit(
                f"identity map {path}: superseded_by_review points "
                f"{old_label!r} at {displaced_by!r}, which is not a known "
                "identity -- every displaced label must resolve to a person."
            )
        if old_label in CONTRIBUTOR_IDENTITY_MAP:
            raise SystemExit(
                f"identity map {path}: {old_label!r} cannot be both a "
                "superseded label and an identity -- a label cannot be two "
                "things (it would credit a reviewer with a rejected word)."
            )
        SUPERSEDED_BY_REVIEW[old_label] = displaced_by
    overlap = (set(CONTRIBUTOR_IDENTITY_MAP) | set(SUPERSEDED_BY_REVIEW)) & set(
        NON_HUMAN_CREATED_BY
    )
    if overlap:
        raise SystemExit(
            f"identity map {path}: {sorted(overlap)} collide with "
            "NON_HUMAN_CREATED_BY pipeline labels -- a label cannot be both "
            "a person and a pipeline."
        )


load_identity_maps()

#: The legacy `community` rows (`created_by` NULL) came from
#: `legesher/legesher-translations` -- a PUBLIC, MIT-licensed repository (created
#: 2019) with 149 contributors in its `.all-contributorsrc`.
#:
#: They classify as `upstream`, not `community`: the obligation is to another
#: project's notice, not to an individual's credit-and-withdrawal rights. That
#: distinction is the whole reason the two are separate buckets -- a person who
#: asks to be removed from `community` is exercising a right we granted them;
#: a licence notice is not ours to drop on request.
#:
#: We hold the copyright (`Copyright (c) 2019 Legesher`), verified 2026-08-05.
#: So retaining the MIT notice is a **commitment to the 149 contributors**, not
#: third-party legal exposure -- we cannot breach our own licence. Credit them
#: because it is right, and say it in those terms rather than implying a legal
#: compulsion that does not exist.
#:
#: `source='upstream'` is what makes the obligation machine-visible IN THE
#: PUBLISHED ARTIFACT (`options.sources`). `source_detail` names WHICH upstream
#: project, but it never ships -- so the card, not the data, is where a
#: consumer learns the project names and their notices.
LEGACY_COMMUNITY_SOURCE_DETAIL = "legesher-translations"
LEGACY_COMMUNITY_LICENSE = "MIT"
LEGACY_COMMUNITY_REPO = "https://github.com/legesher/legesher-translations"

#: Every OTHER PROJECT whose work is in the corpus: `source_detail` -> the credit
#: line a human has to be able to write from it. All three licences VERIFIED
#: 2026-08-05 by reading the licence file in each repository (CORE-1720).
#:
#: This drives the pre-publish checklist, which names each project and its terms
#: so an unattributed upstream can never again reach a push unnoticed. The
#: VERBATIM notices live in `export_corpus.NOTICE_FILE`, shipped beside the
#: dataset card and linked from it -- a notice that only exists in a build log
#: satisfies nothing, so it has to travel with what a consumer receives.
#:
#: ADDING A PROJECT HERE IS HALF THE WORK: its notice must be added to
#: `NOTICE_FILE` and its row to the card's Upstream projects table in the same
#: change. A test asserts every project named here appears in both.
UPSTREAM_PROJECTS: dict[str, tuple[str, str, str]] = {
    LEGACY_COMMUNITY_SOURCE_DETAIL: (
        "legesher-translations",
        LEGACY_COMMUNITY_REPO,
        LEGACY_COMMUNITY_LICENSE,
    ),
    "universal_python": (
        "UniversalPython",
        "https://github.com/UniversalPython/UniversalPython",
        # The heaviest of the three: Apache-2.0 also requires STATING THAT
        # CHANGES WERE MADE. These renderings were adapted into our pack
        # conventions, not reproduced verbatim, so the card must say so.
        "Apache-2.0",
    ),
    "latino_lang": (
        "Latino",
        "https://github.com/lenguaje-latino/latino",
        # GitHub's licence API reports NOASSERTION -- it could not classify
        # LICENSE.txt's formatting. The file is standard MIT; read it, do not
        # trust the API here.
        "MIT",
    ),
}

#: Rung assigned to endorsements reconstructed from v1. These reviewers pre-date
#: the ladder, so they are imported at the lowest non-zero rung and can be
#: promoted later; back-dating them to `certified` would fabricate authority.
IMPORT_RUNG = "contributor"

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

  3. UPSTREAM ATTRIBUTION.  [manual -- the card and its NOTICE]
     Rows marked `source='upstream'` are ANOTHER PROJECT'S WORK. Three projects,
     all verified 2026-08-05, each named with its row count in the ledger above
     and its terms in the ATTRIBUTION block printed before this checklist.
     Each is CREDITED in the card's Upstream projects table, and its VERBATIM
     notice lives in the `NOTICE` file shipped beside the card: a summary does
     not satisfy a retention clause, and Apache-2.0 (UniversalPython)
     additionally requires STATING THAT CHANGES WERE MADE. Both halves ship on
     every export and both are on the push allowlist; do NOT paste the notices
     back into the card, which is tested to be free of them.
     `source` is the only provenance column that ships, so `upstream` is what
     makes the obligation machine-visible in the published artifact.
     `source_detail` -- which names WHICH project -- never leaves the database,
     which is exactly why the card has to carry the names.
     {LEGACY_COMMUNITY_REPO} is OURS
     ({LEGACY_COMMUNITY_LICENSE}, Copyright (c) 2019 Legesher; 149 contributors
     in its .all-contributorsrc), so retaining its notice is a commitment to
     those contributors, not third-party legal exposure.

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


def resolve_identity(created_by: str) -> Identity | Withdrawn:
    """Map a v1 ``created_by`` label to the person behind it.

    Args:
        created_by: The raw v1 label (already known not to be in
            :data:`NON_HUMAN_CREATED_BY`).

    Returns:
        Either an :class:`Identity`, which may be UNRESOLVED
        (``github_handle is None``), or a :class:`Withdrawn` for someone who
        asked to be forgotten.

        **Check the type before touching attributes.** ``Withdrawn`` has no
        ``github_handle``, so the usual unresolved test raises AttributeError on
        one rather than returning False; ``Withdrawn.resolved`` is always True,
        because a withdrawal is a decision rather than an open question.

    Raises:
        SystemExit: on an unknown label. It is NOT guessed at, and it is NOT
            passed through as its own contributor: either is a silent decision
            about a real person's identity, taken by a script.
    """
    try:
        return CONTRIBUTOR_IDENTITY_MAP[created_by]
    except KeyError:
        empty_hint = (
            "\nNOTE: the identity map is EMPTY. It is private data and lives in "
            "the durable\ndata home, not in this tree [CORE-1794] -- set "
            "$LEGESHER_DATA_REPO to your checkout\nof the private data "
            "repository (or $LEGESHER_IDENTITY_MAP to the JSON itself)."
            if not CONTRIBUTOR_IDENTITY_MAP
            else ""
        )
        raise SystemExit(
            f"unknown v1 created_by label {created_by!r}.{empty_hint}\n"
            "Every label must be classified BY HAND, because every wrong answer "
            "is silent:\n"
            "  * a person             -> identities in the data home's "
            "contributor_identity_map.json,\n"
            "                            keyed by their GitHub username\n"
            "  * a pipeline / pack    -> NON_HUMAN_CREATED_BY\n"
            "  * a word a review REPLACED -> superseded_by_review in the same "
            "JSON\n"
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
        if classify_source(row["source"]) != "community":
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


#: Where the per-term Tier-1 translation briefs live. Each carries a
#: ``## Quick Summary`` section whose first paragraph is a ready-made
#: ``definition_en``.
CONTEXT_BRIEF_DIR = Path(__file__).resolve().parents[1] / "context" / "python"


def definition_from_brief(
    term_name: str, context_dir: Path = CONTEXT_BRIEF_DIR
) -> str | None:
    """Extract a ``definition_en`` from the term's context brief, if one exists.

    Reads ``<context_dir>/<term_name>.md`` and returns the first paragraph
    under its ``## Quick Summary`` heading, joined to a single line. The
    corpus publishes ``concepts.definition_en`` verbatim (CORE-1505), so
    without this seed ~243 of the 246 v1 terms would publish a literal
    ``TODO: seed from context/python/<name>.md`` placeholder.

    Args:
        term_name: The English term exactly as named in v1 (``elif``,
            ``except*``, ``__import__``) -- also the brief's file stem.
        context_dir: The briefs directory (overridable for tests).

    Returns:
        The summary paragraph, or ``None`` when the brief or its Quick
        Summary section is missing or empty (the caller keeps the explicit
        TODO marker -- absent debt must stay visible, not become an empty
        string or another section's prose).
    """
    stem = brief_stem(term_name)
    if stem is None:
        return None
    path = context_dir / f"{stem}.md"
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        start = next(
            index
            for index, line in enumerate(lines)
            if line.strip().lower() == "## quick summary"
        )
    except StopIteration:
        return None
    paragraph: list[str] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if not stripped:
            if paragraph:
                break
            continue
        # Any heading or rule ends the section -- an EMPTY Quick Summary must
        # yield None, never fall through and harvest a later section's prose
        # (which could be literal code-fence markup, published verbatim).
        if stripped.startswith(("#", "---")):
            break
        paragraph.append(stripped)
    return " ".join(paragraph) or None


def brief_stem(term_name: str) -> str | None:
    """Filesystem-safe brief stem for a v1 term name, or ``None`` if unsafe.

    The briefs use ``_star`` for ``*`` (``except*`` -> ``except_star.md``).
    The name comes from a database row and is interpolated into a path, so
    anything that would escape the briefs directory (separators, ``..``) is
    refused outright -- this pipeline feeds the published artifact, and
    future ingest paths write into the same database.
    """
    stem = term_name.replace("*", "_star")
    if "/" in stem or "\\" in stem or Path(stem).name != stem:
        return None
    return stem


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


def count_message_rows(src: sqlite3.Connection) -> int:
    """message_templates rows in the source, 0 when the partition is absent.

    The messages partition (CORE-1679) lives in the operational v1 database
    but is NOT carried over by this migration -- a v2 build re-seeds it from
    the catalog seed files. This counter powers the refusal that keeps that
    gap loud instead of silent.
    """
    try:
        return src.execute("SELECT COUNT(*) FROM message_templates").fetchone()[0]
    except sqlite3.OperationalError:
        return 0


def migrate(
    source: Path,
    target: Path,
    *,
    salt: str | None = None,
    publish: bool = False,
    acknowledge_message_rows_not_migrated: bool = False,
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
        acknowledge_message_rows_not_migrated: The messages partition
            (CORE-1679) is NOT carried over; a source carrying message rows is
            refused unless this is True (re-seed the v2 build with
            ``seed_message_templates.py`` afterwards).

    Returns:
        The reconciliation ledger.

    Raises:
        SystemExit: in publish mode, if the salt is unfit or any contributor
            identity is unresolved.
    """
    if publish:
        require_publishable_salt(salt)
        require_published_withdrawal_ids()
    if target.exists():
        raise SystemExit(f"refusing to overwrite {target}")
    target.parent.mkdir(parents=True, exist_ok=True)

    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row

    message_rows = count_message_rows(src)
    if message_rows and not acknowledge_message_rows_not_migrated:
        src.close()
        raise SystemExit(
            f"source database carries {message_rows} message_templates rows "
            "(the CORE-1679 messages partition), which this migration does "
            "NOT carry over -- the v2 build would silently start without "
            "them. Re-run with --acknowledge-message-rows-not-migrated and "
            "re-seed the v2 build via seed_message_templates.py "
            "(db/seeds/*.json), or drop the partition from the source first."
        )
    if message_rows:
        print(
            f"NOTE: {message_rows} message_templates rows in the source are NOT "
            "migrated (messages partition, CORE-1679). Re-seed the v2 build "
            "with seed_message_templates.py."
        )

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
                "corpus. Resolve it in the data home's "
                "contributor_identity_map.json first (the in-tree map is "
                "empty by design and reloaded from that JSON on every run "
                "[CORE-1794]). No target database was created."
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
    # v1 terms became multi-target with the JavaScript seeding (CORE-1371);
    # every PL present in the source is seeded, not just python.
    pl_status = {"python": "shipping", "javascript": "in_progress"}
    pl_names = {"python": "Python", "javascript": "JavaScript"}
    for pl_row in src.execute(
        "SELECT DISTINCT programming_language FROM terms ORDER BY programming_language"
    ):
        code = pl_row["programming_language"]
        dst.execute(
            "INSERT INTO programming_languages (code, name, status) VALUES (?, ?, ?)",
            (code, pl_names.get(code, code.title()), pl_status.get(code, "planned")),
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

    # -- 2. Concepts (deduped by slug across PLs) ----------------------------
    # A concept is cross-PL by design: python `break` and javascript `break`
    # are ONE concept with two terms rows (that reuse is the whole point of
    # the concept layer — a shared word never re-runs translation + review
    # per target). The first term to name a slug declares the concept; later
    # same-slug terms attach to it.
    #
    # definition_en is v1's description when present, else the first Quick
    # Summary paragraph of the term's context brief; only when both are
    # missing does the explicit TODO placeholder remain (it is NOT NULL in
    # the schema, so absent debt stays visible rather than hidden).
    definitions_seeded = 0
    definitions_todo = 0
    term_rows = 0
    term_tokens_seen: set[tuple[str, str]] = set()
    concept_by_slug: dict[str, int] = {}
    #: v1 term id -> (v2 concept id, slug, programming language). One mapping
    #: for all per-term facts, so the options and canon passes cannot pick up
    #: one dict and miss another.
    concept_of_term: dict[int, tuple[int, str, str]] = {}
    #: v1 term id -> the English source term, for the identity_ok compare
    #: (CORE-1355). Distinct from term_name_of_concept: secondary terms
    #: (python `type` the soft keyword) share a concept but every term row
    #: still names the same English token it is compared against.
    english_of_term: dict[int, str] = {}
    #: concept ids that already carry their Tier-1 brief row.
    briefed_concepts: set[int] = set()
    #: v2 concept id -> the English source term (e.g. 'except*'). The identifier
    #: validator is term-aware, so it needs the token, not just the slug (which
    #: has lost the structural '*': 'except*' -> slug 'except*' but dunders map
    #: '_' -> '-'). Kept as the real term name.
    term_name_of_concept: dict[int, str] = {}
    for row in src.execute("SELECT * FROM terms ORDER BY id"):
        base_slug = row["name"].strip().lower().replace("_", "-")
        token = (row["programming_language"], row["name"])
        # One token may name TWO constructs within a PL (python `type`: the
        # builtin and the 3.12 soft keyword — v1 keeps both under distinct
        # categories, and 51 locales picked different words for them). Those
        # are different CONCEPTS sharing a spelling: the second gets a
        # category-disambiguated slug and rides as export_role='secondary'
        # (the schema's idx_terms_one_primary allows exactly one primary
        # reading per (PL, name)).
        if token in term_tokens_seen:
            slug = f"{base_slug}-{row['category']}"
            export_role = "secondary"
        else:
            slug = base_slug
            export_role = "primary"
        concept_id = concept_by_slug.get(slug)
        if concept_id is None:
            definition = row["description"] or definition_from_brief(row["name"])
            if definition:
                definitions_seeded += 1
            else:
                definitions_todo += 1
                definition = f"TODO: seed from context/python/{row['name']}.md"
            cur = dst.execute(
                "INSERT INTO concepts (slug, definition_en, category) VALUES (?, ?, ?)",
                (slug, definition, row["category"]),
            )
            concept_id = int(cur.lastrowid or 0)
            concept_by_slug[slug] = concept_id
            term_name_of_concept[concept_id] = row["name"]
        # The Tier-1 brief claim: only when the PYTHON term is seen (the briefs
        # are python briefs), only once per concept, and only for a file that
        # actually exists — no dangling paths, and order-independent should a
        # javascript term ever declare the concept first.
        if (
            row["programming_language"] == "python"
            and concept_id not in briefed_concepts
        ):
            stem = brief_stem(row["name"])
            if stem is not None and (CONTEXT_BRIEF_DIR / f"{stem}.md").is_file():
                dst.execute(
                    "INSERT INTO concept_briefs (concept_id, tier, path) VALUES (?, 1, ?)",
                    (concept_id, f"libs/i18n/context/python/{stem}.md"),
                )
                briefed_concepts.add(concept_id)
        concept_of_term[row["id"]] = (concept_id, slug, row["programming_language"])
        english_of_term[row["id"]] = row["name"]
        term_tokens_seen.add(token)
        dst.execute(
            "INSERT INTO terms (concept_id, programming_language, name, category, subcategory, "
            "version_added, export_role) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                concept_id,
                row["programming_language"],
                row["name"],
                row["category"],
                row["subcategory"],
                row["version_added"],
                export_role,
            ),
        )
        term_rows += 1
    ledger.record("concepts", len(concept_by_slug))
    ledger.record("terms", term_rows)
    ledger.record("definitions_seeded", definitions_seeded)
    ledger.record("definitions_todo", definitions_todo)

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
    #: source_detail -> rows, for every OTHER PROJECT's work in the build. Keyed
    #: by project so the pre-publish checklist can name each one and its licence
    #: instead of reporting a single opaque `upstream` total: the point of the
    #: bucket is that a reader can act on it, and "2,204 upstream rows" is not
    #: something anyone can write a credit line from.
    upstream_project_rows: dict[str, int] = defaultdict(int)

    for row in src.execute("SELECT * FROM translations ORDER BY id"):
        v1_translation_rows += 1
        concept_id, slug, _pl = concept_of_term[row["term_id"]]
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

        source_kind = classify_source(row["source"])
        created_by = (row["created_by"] or "").strip()
        source_detail = row["source"]
        contributor: str | None = None
        identity: Identity | Withdrawn | None = None

        if created_by in NON_HUMAN_CREATED_BY:
            # A pipeline label, not a person: it must not become a contributor and
            # must not mint an endorsement. Keep the label as provenance. The
            # bucket is per-label because two of these labels are other projects'
            # work and two are our own QA -- see NON_HUMAN_CREATED_BY.
            source_kind = NON_HUMAN_CREATED_BY[created_by]
            source_detail = created_by
            non_human_rows += 1
            if source_kind == "upstream":
                upstream_project_rows[created_by] += 1
        elif created_by in SUPERSEDED_BY_REVIEW:
            # The word the reviewer REJECTED (see SUPERSEDED_BY_REVIEW). It stays
            # in the corpus -- it really shipped once, and that is evidence -- but
            # it is the PACK's word, not the reviewer's. Endorsing it here would
            # record a native speaker as endorsing the word she threw out. Her
            # disagreement is already expressed, exactly as the schema intends, by
            # the endorsement she DOES have on the replacement. The neutral label
            # (not created_by) is deliberate: the v1 label embeds a first name and
            # option_provenance is corpus-layer -- see SUPERSEDED_SOURCE_DETAIL.
            source_kind = "legesher"
            source_detail = SUPERSEDED_SOURCE_DETAIL
            superseded_rows += 1
        elif source_kind == "upstream" and not created_by:
            # The 2,169 legacy rows. They carry no author because they were lifted
            # wholesale from legesher/legesher-translations (MIT, 149 contributors).
            # `upstream` on the row is what makes the attribution obligation
            # visible IN THE PUBLISHED CORPUS; the label naming which project
            # stays private, so the card credits it and NOTICE retains its text.
            source_detail = LEGACY_COMMUNITY_SOURCE_DETAIL
            upstream_project_rows[LEGACY_COMMUNITY_SOURCE_DETAIL] += 1
        elif source_kind == "upstream":
            # An `upstream` row this loop cannot attribute to a project. No such
            # row exists today (all 2,169 legacy rows have a NULL author), but
            # the branch above only recognises them BY THAT NULL -- so a future
            # `source='community'` row carrying an author would fall straight
            # through, publish `upstream` ("a third-party licence applies here")
            # and name no project anywhere, in the data or the card. An
            # unattributable obligation is the exact failure CORE-1720 exists to
            # close, so it stops the build instead of shipping quietly.
            raise SystemExit(
                f"Cannot attribute an `upstream` row: source={row['source']!r}, "
                f"created_by={created_by!r}.\n"
                "`upstream` publishes the claim that another project's licence "
                "applies, so every\nsuch row must resolve to an entry in "
                "UPSTREAM_PROJECTS -- otherwise the corpus asserts\nan obligation "
                "it gives a consumer no way to discharge. Map the label in\n"
                "NON_HUMAN_CREATED_BY and add its project, URL and licence to "
                "UPSTREAM_PROJECTS."
            )
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
                # For a WITHDRAWN person the id is TAKEN from the map rather
                # than minted: there is no username left to mint it from, which
                # is the erasure working, and it is what stops a rebuild undoing
                # the withdrawal. For everyone else it is minted from the GITHUB
                # USERNAME rather than the v1 first-name label -- the public id
                # is unchanged in kind (an opaque digest); what improves is the
                # private key behind it: stable, unique, verifiable.
                contributor = (
                    identity.contributor_id
                    if isinstance(identity, Withdrawn)
                    else contributor_id(source_key, salt=salt)
                )
                if contributor in set(contributors.values()):
                    # One person, two v1 labels, only some of them withdrawn --
                    # the half-finished state runbook step 2 can leave. Checked
                    # for BOTH kinds because either can be processed first, and
                    # the failure is the same either way. Without it the build
                    # dies on a raw UNIQUE constraint naming neither the person
                    # nor the labels, while the labels left behind still carry
                    # their username.
                    raise SystemExit(
                        f"contributor id {contributor} is claimed by two "
                        "entries in CONTRIBUTOR_IDENTITY_MAP.\nOne person holds "
                        "more than one v1 label and only some were withdrawn, "
                        "so the labels\nleft behind still carry their username "
                        "and the erasure is incomplete. Convert EVERY\nlabel "
                        "belonging to that person."
                    )
                dst.execute(
                    "INSERT INTO contributors (id, current_rung) VALUES (?, ?)",
                    (contributor, IMPORT_RUNG),
                )
                if isinstance(identity, Withdrawn):
                    # A TOMBSTONE: every identity column NULL, `withdrawn_at`
                    # set, so a later import can tell "this person withdrew"
                    # apart from "we have never met this person". Their
                    # endorsements below are written exactly as for anyone else
                    # -- counts survive, PII does not.
                    dst.execute(
                        "INSERT INTO contributor_identities "
                        "(contributor_id, withdrawn_at) VALUES (?, ?)",
                        (contributor, identity.withdrawn_at),
                    )
                else:
                    # The mapping lives ONLY here, and is never exported.
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
                # Cache for BOTH paths: a second row from the same contributor
                # must reuse the id, not attempt another INSERT.
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
    ledger.record("upstream-attributed rows", sum(upstream_project_rows.values()))
    for detail, rows in sorted(upstream_project_rows.items()):
        ledger.record(f"  {UPSTREAM_PROJECTS[detail][0]}", rows)
    ledger.record("endorsements", len(endorsements))

    # -- 5. Validation (a REAL pass, over the whole corpus) --------------------
    # Not a stamp. `validator_version = 'migration-seed'` is rejected by the canon
    # trigger precisely so that a seeded row can never be mistaken for a validated
    # one; what runs here is validate_surface(), and whatever it finds, it reports.
    invalid_identifier = 0
    nfkc_unstable = 0
    sara_am_only = 0
    script_inconsistent = 0
    format_char_dirty = 0
    #: uid -> verdict, so the canon pass (step 6) reuses the verdict computed
    #: here instead of re-running validate_surface on every selected option. One
    #: verdict per option; every selected uid is an option (checked in step 6).
    verdicts: dict[str, Validation] = {}
    for uid, surface in options_seen.items():
        concept_id, code = option_meta[uid]
        verdict = validate_surface(
            surface,
            term_name_of_concept[concept_id],
            allowed_scripts_for(code),
            allowed_format_chars_for(code),
        )
        verdicts[uid] = verdict
        invalid_identifier += not verdict.identifier_valid
        nfkc_unstable += not verdict.nfkc_stable
        sara_am_only += verdict.nfkc_delta_class == "sara-am-only"
        script_inconsistent += not verdict.script_consistent
        format_char_dirty += not verdict.format_chars_clean
        dst.execute(
            "INSERT INTO option_validations (option_uid, validator_version, identifier_valid, "
            "nfkc_stable, nfkc_delta_class, script_consistent, collides_en_keyword, "
            "format_chars_clean) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                uid,
                VALIDATOR_VERSION,
                int(verdict.identifier_valid),
                int(verdict.nfkc_stable),
                verdict.nfkc_delta_class,
                int(verdict.script_consistent),
                int(verdict.collides_en_keyword),
                int(verdict.format_chars_clean),
            ),
        )
    ledger.record("options validated", len(options_seen))
    ledger.record("  invalid identifier", invalid_identifier)
    ledger.record("  NFKC-unstable", nfkc_unstable)
    ledger.record("    of which SARA-AM only", sara_am_only)
    ledger.record("  script-inconsistent", script_inconsistent)
    ledger.record("  format-char dirty", format_char_dirty)

    # -- 6. Canon ------------------------------------------------------------
    # The gate is now real, so it bites: a v1 selection whose rendering fails
    # validation is REFUSED, and reported. It is not silently shipped, and it is
    # not silently dropped either -- the option stays in the corpus as evidence,
    # which is the CORE-1400 reframe working exactly as designed.
    selected_rows = 0
    canon_rows = 0
    identity_rows = 0
    rejected: list[tuple[str, str, str, str]] = []
    for row in src.execute("SELECT * FROM selected_translations ORDER BY id"):
        selected_rows += 1
        concept_id, slug, term_pl = concept_of_term[row["term_id"]]
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
        # identifier): identifier-valid AND script-consistent AND format-char
        # clean AND (NFKC-stable OR SARA-AM only). Reported reason is the FIRST
        # failing check, in that order. Reuse the verdict computed in step 5
        # (same option, same inputs) rather than re-running the validator.
        verdict = verdicts[uid]
        nfkc_ok = verdict.nfkc_stable or verdict.nfkc_delta_class == "sara-am-only"
        if not (
            verdict.identifier_valid
            and verdict.script_consistent
            and verdict.format_chars_clean
            and nfkc_ok
        ):
            if not verdict.identifier_valid:
                reason = "not a valid identifier"
            elif not verdict.script_consistent:
                reason = "mixed / foreign script"
            elif not verdict.format_chars_clean:
                reason = "forbidden format/invisible character"
            else:
                reason = "NFKC-unstable"
            rejected.append((locale, slug, surface, reason))
            continue

        # PL-scoped: a v1 selection belongs to its term's target. The corpus
        # shows real per-PL divergence (abs -> قيمة_مطلقة for javascript vs
        # القيمةالمطلقة for python), so canon rows carry the PL rather than
        # claiming the concept-wide '*' scope.
        # Identity marker (CORE-1355): a surface that IS the English term is
        # a deliberate cognate/loanword (policy 2026-07-05), not a gap.
        identity_ok = int(
            is_identity_translation(english_of_term[row["term_id"]], surface)
        )
        dst.execute(
            "INSERT INTO canon_selections (concept_id, locale, programming_language, "
            "option_uid, surface_form, status, identity_ok, "
            "decided_by, decided_at, decision_reason, source_file) "
            "VALUES (?, ?, ?, ?, ?, 'machine', ?, ?, ?, ?, ?)",
            (
                concept_id,
                locale,
                term_pl,
                uid,
                surface,
                identity_ok,
                row["selected_by"],
                row["selected_at"],
                row["selection_reason"],
                f"libs/i18n/canon/{locale}.toml",
            ),
        )
        canon_rows += 1
        identity_rows += identity_ok

    ledger.record("v1 selected rows", selected_rows)
    ledger.record("canon_selections", canon_rows)
    ledger.record("  identity_ok (deliberate cognate/loanword)", identity_rows)
    ledger.record("canon REFUSED by gate", len(rejected))

    # -- Pre-notice consent -------------------------------------------------
    # Everyone the migration mints contributed BEFORE CONTRIBUTOR_PRIVACY.md
    # existed, so none of them agreed to it -- and leaving consent_version NULL
    # would say the opposite of what happened, which is that they contributed
    # through public pull requests under their own accounts and were credited by
    # handle in the pack CHANGELOGs at the time.
    #
    # `consent_at` is the EARLIEST v1 record of their work, not the build date:
    # it dates their participation as closely as the data allows, and a fresh
    # timestamp would read as a fresh agreement.
    #
    # It grants nothing. credit_preference stays 'anonymous' (the column
    # default) and withdrawal applies identically -- see PRE_NOTICE_CONSENT.
    # Skipped for withdrawn rows (the consent is revoked) and for `unresolved:`
    # keys (one label, two people: neither of them consented to anything as
    # that row).
    dst.execute(
        "UPDATE contributor_identities "
        "   SET consent_version = ?, "
        "       consent_at = (SELECT MIN(p.created_at) FROM option_provenance p "
        "                      WHERE p.contributor_id = "
        "                            contributor_identities.contributor_id) "
        " WHERE withdrawn_at IS NULL "
        "   AND source_key IS NOT NULL "
        "   AND source_key NOT LIKE ?",
        (PRE_NOTICE_CONSENT, f"{UNRESOLVED_PREFIX}%"),
    )
    ledger.record(
        f"  consent recorded as {PRE_NOTICE_CONSENT}",
        dst.execute(
            "SELECT COUNT(*) FROM contributor_identities WHERE consent_version = ?",
            (PRE_NOTICE_CONSENT,),
        ).fetchone()[0],
    )

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
            "`_new` is always the\n  shipped word, 31/31. ur: the `_old` twin is "
            "قسم / صارفانتباہ, exactly the\n  two words the public ur CHANGELOG "
            "records as REPLACED.)\n"
            "  Endorsing them would record two native speakers as endorsing the "
            "words they\n  threw out. They stay as options with `import` provenance; "
            "the reviewers'\n  disagreement is already expressed -- as the schema "
            "intends -- by the\n  endorsement they DO have on the replacement."
        )

    if upstream_project_rows:
        total = sum(upstream_project_rows.values())
        print(
            f"\nATTRIBUTION: {total:,} rows are ANOTHER PROJECT'S WORK and carry "
            "that project's\n  licence terms. Every one must be credited in the "
            "dataset card, and its notice\n  retained in the NOTICE file beside it "
            "-- a summary satisfies neither.\n"
        )
        for detail, rows in sorted(
            upstream_project_rows.items(), key=lambda kv: -kv[1]
        ):
            name, url, spdx = UPSTREAM_PROJECTS[detail]
            print(f"  {rows:>6,}  {name:<24} {spdx:<12} {url}")
        print(
            "\n  Published as `source='upstream'` on each row, so `options.sources` "
            "tells a\n  consumer that a third-party licence applies. WHICH project "
            "is NOT published:\n  `source_detail` never ships (it carries v1 reviewer "
            "labels with real first\n  names), so the card and its NOTICE are the "
            "only place the project names\n  and notices exist.\n"
            f"  {LEGACY_COMMUNITY_REPO}\n"
            "  is OURS (Copyright (c) 2019 Legesher) -- retaining its notice is a "
            "commitment\n  to its 149 contributors, not third-party legal exposure. "
            "Credit them because\n  it is right. Apache-2.0 (UniversalPython) is the "
            "one genuinely heavier\n  obligation here: it also requires STATING THAT "
            "CHANGES WERE MADE."
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
                "frozen into the\npublished corpus. Resolve it in the data "
                "home's contributor_identity_map.json first."
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
    parser.add_argument(
        "--acknowledge-message-rows-not-migrated",
        action="store_true",
        help=(
            "proceed although the source carries CORE-1679 message_templates / "
            "message_translations rows, which this migration does NOT carry "
            "over; the v2 build must be re-seeded via seed_message_templates.py"
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

    ledger = migrate(
        args.source,
        args.target,
        salt=salt,
        publish=args.publish,
        acknowledge_message_rows_not_migrated=args.acknowledge_message_rows_not_migrated,
    )
    print("Migration ledger:")
    print(ledger.report())
    print()
    print(PRE_PUBLISH_CHECKLIST)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
