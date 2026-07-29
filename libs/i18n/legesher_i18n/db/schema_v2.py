"""Concept-centric schema v2: loader and stable-identifier helpers (CORE-1501).

The DDL itself lives in :data:`SCHEMA_V2_PATH` (``schema_v2.sql``) so that it
stays reviewable as SQL. This module owns the parts that SQLite cannot express:

* :func:`option_uid` / :func:`endorsement_uid` -- the *stable, portable* primary
  keys the Hugging Face corpus publishes. They are content-addressed rather than
  AUTOINCREMENT rowids, because a rowid is a property of one SQLite file: rebuild
  the database from the canon text files and every rowid shifts, dangling every
  endorsement a native speaker ever attached to an option. A content hash is
  reproducible from an export, survives a rebuild, and dedupes by construction.
* :func:`normalize_surface_form` -- the Unicode storage contract (store NFC).

Three layers live in the schema, and the boundary is load-bearing:

``REFERENCE``
    ``programming_languages``, ``locales``, ``concepts``, ``terms``.
``CORPUS``
    ``options``, ``option_provenance``, ``endorsements``, ``option_flags``,
    ``option_validations``, ``contributors``. Append-only, community-writable,
    published to Hugging Face. Endorsement counts are derived, never stored.
``CANON``
    ``canon_selections``. A loaded projection of ``libs/i18n/canon/<locale>.toml``;
    the text files are the source of truth and the DB table is rebuilt from them.

The full design rationale lives in the CORE-1501 design docs, which are not
part of this repository.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
import unicodedata
from pathlib import Path

__all__ = [
    "CONCEPT_WIDE",
    "CONTRIBUTOR_TOKEN_LENGTH",
    "DEFAULT_CONTRIBUTOR_SALT",
    "MIN_PUBLISH_SALT_LENGTH",
    "SCHEMA_V2_PATH",
    "SEEDED_VALIDATOR_VERSION",
    "UID_HASH_LENGTH",
    "annotation_uid",
    "apply_schema_v2",
    "bundle_digest",
    "commentary_uid",
    "connect",
    "contributor_id",
    "endorsement_uid",
    "expansion_uid",
    "normalize_surface_form",
    "option_uid",
    "read_schema_sql",
    "session_uid",
    "style_uid",
]

SCHEMA_V2_PATH = Path(__file__).with_name("schema_v2.sql")

#: ``options.pl_scope`` value meaning "applies to the concept in any programming
#: language". Mirrors ``COALESCE(programming_language, '*')`` in the DDL.
CONCEPT_WIDE = "*"

#: Hex characters kept from the SHA-256 digest. 24 hex chars = 96 bits, which is
#: far past collision risk at corpus scale (~10^5 rows) and keeps the key short
#: enough to read in a Parquet viewer or a PR diff.
#:
#: FROZEN. See ``tests/test_schema_v2.py::test_option_uid_golden_vectors``.
UID_HASH_LENGTH = 24

#: Field separator for the hashed tuples. U+001F (UNIT SEPARATOR) is a control
#: character that must never appear in a concept slug, a locale tag, or a
#: surface form -- and :func:`_digest` now *enforces* that rather than asserting
#: it, because a smuggled separator lets two distinct tuples hash identically:
#:
#: ``('c', 'tr\x1f*\x1fx', 'y')`` and ``('c', 'tr', 'x\x1f*\x1fy')`` join to the
#: same byte string. The guard is pure input validation: it rejects inputs that
#: were never legal, and changes the digest of nothing that was.
#:
#: FROZEN.
_SEP = "\x1f"

#: ``option_validations.validator_version`` values that mean "nobody actually
#: ran a validator here". The canon trigger rejects them: a seeded row must
#: never be mistaken for a validated one (see ``schema_v2.sql``).
SEEDED_VALIDATOR_VERSION = "migration-seed"

#: Hex characters kept from the contributor-token digest. 16 hex = 64 bits: the
#: contributor namespace is tiny (10^4-10^5), so this is collision-free in
#: practice and short enough to read.
CONTRIBUTOR_TOKEN_LENGTH = 16

#: Salt used when no ``LEGESHER_CONTRIBUTOR_SALT`` is set. It is PUBLIC, so a
#: token minted with it is reversible by dictionary attack over a known handle
#: list -- which is exactly the situation for the v1 handles, since
#: ``translations.db`` (and therefore ``translations.created_by``) is committed
#: to this repository, and doubly so now that the source keys are GitHub
#: usernames, which are public and enumerable by construction.
#:
#: **The run that mints the ids for the published corpus must supply a secret
#: salt**; this default exists so tests and local runs are deterministic.
#: ``scripts/migrate_to_v2.py --publish`` HARD-FAILS on it (a warning is not a
#: gate), and :data:`MIN_PUBLISH_SALT_LENGTH` is the floor for a real one.
DEFAULT_CONTRIBUTOR_SALT = "legesher-dev-salt"

#: Minimum length of a salt that is allowed to mint PUBLISHED contributor ids.
#: 32 characters is ``secrets.token_hex(16)``; the recommended generator is
#: ``secrets.token_hex(32)``. Enforced by
#: ``scripts/migrate_to_v2.py::require_publishable_salt``.
MIN_PUBLISH_SALT_LENGTH = 32


def read_schema_sql() -> str:
    """Return the v2 DDL as a single script.

    Returns:
        The contents of ``schema_v2.sql``, suitable for
        :meth:`sqlite3.Connection.executescript`.
    """
    return SCHEMA_V2_PATH.read_text(encoding="utf-8")


def connect(path: str | Path) -> sqlite3.Connection:
    """Open a v2 database with the constraints actually turned on.

    ``PRAGMA foreign_keys`` is a **per-connection** setting that SQLite defaults
    to OFF, and the ``PRAGMA foreign_keys = ON`` at the top of ``schema_v2.sql``
    only applies to the connection that ran the DDL -- it is *not* persisted in
    the file. A fresh :func:`sqlite3.connect` to the resulting database reports
    ``foreign_keys = 0`` and every FK in this schema is silently inert.

    ``PRAGMA recursive_triggers`` is the same class of trap, aimed at the
    triggers instead of the FKs: it also defaults to OFF per connection, and
    while it is OFF the implicit DELETE inside ``INSERT OR REPLACE`` does
    **not** fire ``BEFORE DELETE`` triggers -- so ``REPLACE INTO endorsements``
    rewrites a row every append-only trigger exists to freeze. With it ON, the
    implicit DELETE hits the trigger and the REPLACE is refused like the
    explicit UPDATE/DELETE it really is.

    Every consumer of a v2 database must therefore go through this function (or
    issue both pragmas itself).

    Args:
        path: Path to the database file.

    Returns:
        A connection with foreign keys enforced and append-only triggers
        REPLACE-proof.
    """
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA recursive_triggers = ON")
    return conn


def apply_schema_v2(conn: sqlite3.Connection) -> None:
    """Create the v2 tables, indexes, triggers, and views on ``conn``.

    Enables ``PRAGMA foreign_keys`` on the connection first: SQLite defaults it
    to OFF *per connection*, and every structural guarantee in this schema
    (canon may only ratify an existing option, an endorsement must belong to a
    known contributor) is a foreign key. Enables ``PRAGMA recursive_triggers``
    for the same reason: without it, ``INSERT OR REPLACE`` slips past every
    append-only ``BEFORE DELETE`` trigger (see :func:`connect`).

    Args:
        conn: An open SQLite connection to an empty database.
    """
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA recursive_triggers = ON")
    conn.executescript(read_schema_sql())
    conn.commit()


def normalize_surface_form(surface_form: str) -> str:
    """Apply the storage half of the Unicode contract: store NFC.

    Comparison is a separate concern and uses NFKC + casefold; the two differ on
    purpose. Storing NFKC would silently rewrite a contributor's word (the Thai
    U+0E33 class of corruption), so the corpus stores what the person typed, in
    NFC, and mechanical checks live in ``option_validations``.

    Note that :meth:`str.strip` strips *all* Python whitespace, while SQLite's
    one-argument ``TRIM()`` strips spaces only -- so a naive
    ``surface_form = TRIM(surface_form)`` CHECK is strictly weaker than this
    function. ``options.surface_form`` therefore carries an explicit character
    set in its CHECK (``schema_v2.sql``).

    Args:
        surface_form: The rendering as offered.

    Returns:
        The NFC-normalized, whitespace-stripped rendering.
    """
    return unicodedata.normalize("NFC", surface_form).strip()


def _digest(prefix: str, *parts: str) -> str:
    """Join ``parts`` with the unit separator and hash them.

    Raises:
        ValueError: if any part contains the separator. Without this check the
            joined string is ambiguous and two distinct tuples can produce one
            uid -- a real, reachable collision, not a theoretical one.
    """
    for part in parts:
        if _SEP in part:
            raise ValueError(
                "uid inputs may not contain U+001F (unit separator): "
                f"{part!r}. It is the field delimiter of the hashed tuple; "
                "allowing it would let two distinct tuples forge one uid."
            )
    joined = _SEP.join(parts).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(joined).hexdigest()[:UID_HASH_LENGTH]}"


def option_uid(
    concept_slug: str,
    locale: str,
    surface_form: str,
    programming_language: str | None = None,
) -> str:
    """Compute the stable, public identifier for a candidate rendering.

    The identity of an option is *the rendering itself* -- not the source that
    proposed it. If Aya proposes ``ثابت`` and a native speaker later offers the
    same word, that is one option with two provenance rows, not two options; the
    endorsement count then answers "how many people said this word" without
    double-counting the machine. Content-addressing makes that dedupe automatic
    and matches ``UNIQUE (concept_id, locale, pl_scope, surface_form)``.

    **The formula is FROZEN** once the first corpus is published to Hugging Face:
    the digest is the published key that community endorsements hang off, so
    changing ``_SEP``, :data:`UID_HASH_LENGTH`, the field order, or the NFC call
    silently re-keys every option in the corpus. Golden vectors in
    ``tests/test_schema_v2.py`` pin it with literal digests.

    Args:
        concept_slug: The concept's public slug (``concepts.slug``), *not* its
            integer id -- the integer is internal and never published.
        locale: BCP 47 tag in **canonical case** (``ar``, ``ar-EG``,
            ``zh-Hans``) -- lowercase language, Titlecase script, UPPERCASE
            region. BCP 47 is case-insensitive but this hash is not: ``ar-EG``
            and ``ar-eg`` are the same locale and produce *different* uids, so
            one wrongly-cased tag would permanently fork every option in that
            locale. ``locales.tag`` carries a CHECK constraint pinning the
            canonical form; it is the only tag that may be passed here.
        surface_form: The candidate rendering. Normalized to NFC before hashing,
            so an NFC and an NFD spelling of the same word hash identically.
        programming_language: The PL this option is scoped to, or ``None`` for a
            concept-wide option (the default and the overwhelming majority).

    Returns:
        ``opt_`` followed by 24 hex characters.

    Raises:
        ValueError: if any input contains U+001F.
    """
    return _digest(
        "opt",
        concept_slug,
        locale,
        programming_language or CONCEPT_WIDE,
        normalize_surface_form(surface_form),
    )


def contributor_id(natural_key: str, *, salt: str | None = None) -> str:
    """Mint the opaque, publishable handle for a person.

    ``contributors.id`` is the **only** identity column the corpus exports, and
    the schema promises it is "never a name, email, or handle". A migration that
    writes ``f"c_{created_by}"`` breaks that promise in the one place it is
    load-bearing: the v1 handles include real first names
    (``alt_ur_modern``, ``zh_reviewer_review``, ``ur_reviewer_review``), and
    ``c_<handle>`` satisfies the naive ``LIKE 'c\\_%'`` CHECK.

    The token is a salted digest of the private natural key -- the contributor's
    **GitHub username** (stable, unique, verifiable), or a portal account id. The
    mapping back to a person lives only in ``contributor_identities``, which is
    never exported.

    .. warning::

       **THE SALT IS IMMUTABLE FOREVER, AND MUST BE ESCROWED.**

       It is not a rotatable credential. It is an ingredient of a PRIMARY KEY:

           contributor_id = c_ + HMAC-SHA256(key=salt, msg=source_key)[:16 hex]

       The docs used to say only that the salt must be *secret*. Secrecy is the
       lesser half. If the salt is ever **lost, rotated, or regenerated** after
       the first Hugging Face publish, every ``contributor_id`` changes, every
       endorsement re-keys, **the corpus forks**, and every contributor's history
       is orphaned -- and it is unrecoverable, because you can never again mint a
       matching id for a returning contributor without the original salt.

       Generate it exactly once (``secrets.token_hex(32)``), store it in a secret
       manager, back it up, and never rotate it.
       ``tests/test_schema_v2.py::test_contributor_id_is_frozen_for_a_given_salt``
       pins the derivation; ``migrate_to_v2.py --publish`` refuses to mint with a
       salt that is public or too short.

    Args:
        natural_key: The private key for this person (a GitHub username, an
            account id). Never published.
        salt: Overrides ``$LEGESHER_CONTRIBUTOR_SALT`` and
            :data:`DEFAULT_CONTRIBUTOR_SALT`. **The salt must be secret for the
            published corpus** -- with a public salt, the digest of a known
            username list is trivially reversible -- **and permanent**, per the
            warning above.

    Returns:
        ``c_`` followed by 16 hex characters, matching the CHECK on
        ``contributors.id``.

    Raises:
        ValueError: if ``natural_key`` is empty or contains U+001F.
    """
    key = natural_key.strip()
    if not key:
        raise ValueError("contributor natural_key must be non-empty")
    effective_salt = (
        salt
        if salt is not None
        else os.environ.get("LEGESHER_CONTRIBUTOR_SALT", DEFAULT_CONTRIBUTOR_SALT)
    )
    if _SEP in key:
        raise ValueError(f"contributor natural_key may not contain U+001F: {key!r}")
    # HMAC-SHA256, not sha256(salt || key): the standard keyed construction,
    # with an unambiguous key/message boundary and nothing for a future
    # auditor to squint at. The truncation to CONTRIBUTOR_TOKEN_LENGTH is part
    # of the frozen formula, pinned by the golden vectors.
    token = hmac.new(
        effective_salt.encode("utf-8"), key.encode("utf-8"), hashlib.sha256
    ).hexdigest()[:CONTRIBUTOR_TOKEN_LENGTH]
    return f"c_{token}"


def salt_fingerprint(salt: str) -> str:
    """Fingerprint the contributor salt for ``build_meta``.

    Nothing else in a built database records which salt minted its contributor
    ids -- so without this, a publish script cannot distinguish an artifact
    minted with the escrowed salt from one minted with the dev salt or a typo.
    That mistake is unrecoverable one publish later (the ids fork).

    A plain truncated SHA-256 is enough here: the publish gate already refuses
    short or public salts, so the pre-image space is not enumerable.

    Args:
        salt: The contributor salt (the HMAC key of :func:`contributor_id`).

    Returns:
        The first 16 hex characters of ``sha256(salt)``.
    """
    return hashlib.sha256(salt.encode("utf-8")).hexdigest()[:16]


def endorsement_uid(
    option_uid_: str,
    contributor_id_: str,
    method: str,
    created_at: str,
) -> str:
    """Compute the stable, public identifier for a single endorsement event.

    Includes ``created_at`` so that a retract-then-re-endorse produces a
    *different* row rather than colliding with the retracted one, and so that
    re-running the v1 import is idempotent (same source row in, same uid out).

    Args:
        option_uid_: The option being endorsed.
        contributor_id_: Opaque contributor handle (``c_`` + 16 hex, minted by
            :func:`contributor_id`). Never a name, email, or GitHub handle --
            those live in ``contributor_identities``, never exported (CORE-1502).
        method: How the endorsement was collected (``portal``, ``survey``,
            ``workshop``, ``github``, ``interview``, ``import``).
        created_at: ISO-8601 timestamp of the endorsement.

    Returns:
        ``end_`` followed by 24 hex characters.

    Raises:
        ValueError: if any input contains U+001F.
    """
    return _digest("end", option_uid_, contributor_id_, method, created_at)


# ---------------------------------------------------------------------------
# Review-intake uids (CORE-1538). Deterministic on purpose: re-importing the
# same bundle re-mints the same uids, so ingest is INSERT-idempotent and never
# duplicates. Same freeze rules as option_uid: once sessions are published,
# these formulae are pinned by the golden vectors in
# ``tests/test_review_extensions.py``.
# ---------------------------------------------------------------------------


def bundle_digest(canonical_bundle: bytes) -> str:
    """Full SHA-256 of a canonical review bundle, as stored on the session row.

    The bundle must already be in its canonical serialization (RFC 8785-style
    canonical JSON, UTF-8 bytes) — canonicalization is the submitter's/
    importer's job; this function hashes bytes, full stop.

    Args:
        canonical_bundle: The canonical bundle bytes.

    Returns:
        64 lowercase hex characters (``review_sessions.bundle_digest``).
    """
    return hashlib.sha256(canonical_bundle).hexdigest()


def session_uid(canonical_bundle: bytes) -> str:
    """Content-addressed id of one review session.

    The truncation of :func:`bundle_digest`, prefixed — so the session uid and
    the stored digest verify each other, and re-importing the same bundle is
    idempotent by construction (same bytes in, same primary key out).

    Args:
        canonical_bundle: The canonical bundle bytes.

    Returns:
        ``ses_`` followed by 24 hex characters.
    """
    return f"ses_{bundle_digest(canonical_bundle)[:UID_HASH_LENGTH]}"


def annotation_uid(
    session_uid_: str, option_uid_: str, contributor_id_: str, kind: str
) -> str:
    """Content-addressed id of one option annotation (descriptor vote).

    Keyed WITHOUT a timestamp: within one session, one person annotating one
    option with one kind is one fact — re-import must not duplicate it. A
    retract-then-re-annotate lands in a NEW session, whose uid differs.

    Returns:
        ``ann_`` followed by 24 hex characters.

    Raises:
        ValueError: if any input contains U+001F.
    """
    return _digest("ann", session_uid_, option_uid_, contributor_id_, kind)


def expansion_uid(
    session_uid_: str, option_uid_: str, contributor_id_: str, expansion: str
) -> str:
    """Content-addressed id of one phrase-expansion attestation.

    ``expansion`` is normalized exactly like a surface form (NFC + strip) so an
    NFC and an NFD spelling of the same phrase are one attestation.

    Returns:
        ``exp_`` followed by 24 hex characters.

    Raises:
        ValueError: if any input contains U+001F.
    """
    return _digest(
        "exp",
        session_uid_,
        option_uid_,
        contributor_id_,
        normalize_surface_form(expansion),
    )


def commentary_uid(
    session_uid_: str,
    contributor_id_: str,
    concept_slug: str | None,
    locale: str,
    topic: str,
    body: str,
) -> str:
    """Content-addressed id of one commentary entry.

    The body is hashed first (NFC-normalized) and its hex digest joins the
    tuple: bodies are long free text, and a digest keeps the joined tuple
    short while a hex string can never smuggle the U+001F separator.

    Args:
        session_uid_: The session the commentary arrived in.
        contributor_id_: Opaque contributor handle.
        concept_slug: The concept's public slug, or ``None`` for locale-level
            commentary (hashed as the empty string).
        locale: BCP 47 tag in canonical case.
        topic: The commentary topic (``word_formation``, ``expansion``, …).
        body: The commentary text.

    Returns:
        ``com_`` followed by 24 hex characters.

    Raises:
        ValueError: if any input contains U+001F.
    """
    body_hash = hashlib.sha256(
        unicodedata.normalize("NFC", body).encode("utf-8")
    ).hexdigest()
    return _digest(
        "com",
        session_uid_,
        contributor_id_,
        concept_slug or "",
        locale,
        topic,
        body_hash,
    )


def style_uid(session_uid_: str, contributor_id_: str, locale: str, field: str) -> str:
    """Content-addressed id of one style-profile answer.

    Keyed WITHOUT the value: one person answers one field once per session;
    the value is the payload, not the identity (an edited answer arrives in a
    new session, and the one-live-vote index handles supersession via
    retraction).

    Returns:
        ``sty_`` followed by 24 hex characters.

    Raises:
        ValueError: if any input contains U+001F.
    """
    return _digest("sty", session_uid_, contributor_id_, locale, field)
