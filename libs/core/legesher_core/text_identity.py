"""Text-identity primitives: the normalization + hashing contract.

One home for the functions every consumer of ``.legesher/`` artifacts
must agree on, whichever side of the product boundary it lives on
[CORE-2024]. Two contracts, stated once:

- **Storage identity** — text entering an artifact is normalized **LF,
  then NFC** (:func:`normalize_text`) and content-addressed with
  :func:`content_hash`. These outputs are baked into artifacts on disk,
  so the functions are frozen: a change is a migration, never an edit —
  add a successor and re-stamp on load, the way :func:`legacy_nfc_hash`
  records the previous recipe (CORE-1710).
- **Collision comparison** — values are *stored* NFC but *compared*
  NFKC + casefold (:func:`compare_key`), so visually interchangeable
  renderings cannot coexist as distinct coinages.
"""

from __future__ import annotations

import hashlib
import unicodedata

from .utils import normalize_newlines

#: Hex digits kept from the SHA-256 digest (64 bits — ample for per-file
#: disambiguation while keeping the artifact readable).
CONTENT_HASH_LENGTH = 16


def normalize_nfc(text: str) -> str:
    """Normalize text to NFC (store-NFC / compare-NFC contract)."""
    return unicodedata.normalize("NFC", text)


def normalize_text(text: str) -> str:
    """The artifact family's storage normalization: **LF, then NFC**.

    Two normalizations, one contract, applied at every point text enters
    a ``.legesher/`` artifact:

    1. **Line endings → LF.** NFC does not touch line endings, so
       ``content_hash("a\\nb") != content_hash("a\\r\\nb")``: a CRLF
       checkout (Windows ``core.autocrlf``) would miss every multi-line
       TM segment and re-anchor every multi-line map node, silently, on
       a file nobody edited. Normalizing at extraction makes node
       identity a property of the *content* rather than of the checkout
       that produced it.
    2. **NFC.** Canonically equivalent spellings hash alike.

    Line endings are a rendering detail Legesher already owns: the
    translator LF-normalizes source as its first step
    (``utils.normalize_newlines``), so stored text and emitted output
    agree. Only ``\\r\\n`` and lone ``\\r`` are folded — U+2028/U+2029/
    U+0085 are content, not terminators, and survive verbatim.

    Order is presentational, not semantic: NFC never produces a ``\\r``,
    so the two steps commute.
    """
    return normalize_nfc(normalize_newlines(text))


def legacy_nfc_hash(text: str) -> str:
    """The pre-LF-policy content hash: SHA-256 over NFC alone.

    Migration support only (CORE-1710). Artifacts written before line
    endings were normalized carry hashes computed this way; a loader can
    recognize one and re-stamp it instead of rejecting the artifact.
    Never use this to hash new text.
    """
    digest = hashlib.sha256(normalize_nfc(text).encode("utf-8")).hexdigest()
    return digest[:CONTENT_HASH_LENGTH]


def content_hash(text: str) -> str:
    """Content hash of a node's text: SHA-256 over :func:`normalize_text`.

    Hashing the normalized form keeps identity stable across canonically
    equivalent renderings *and* across checkouts with different line
    endings (see ``unicode_guard`` for the wider Unicode contract).
    """
    digest = hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()
    return digest[:CONTENT_HASH_LENGTH]


def compare_key(text: str) -> str:
    """Collision-comparison key: NFKC normalization + case fold.

    The store-NFC / compare-NFKC+fold contract: values are *stored* NFC,
    but collision comparison collapses compatibility variants (fullwidth
    forms, ligatures) and case so visually interchangeable renderings
    cannot coexist as distinct coinages.
    """
    return unicodedata.normalize("NFKC", text).casefold()
