"""Translation memory data model — the node-keyed prose cache (CORE-411).

The translation memory (TM) caches translated *prose* segments — comments
and docstrings (:data:`~legesher_core.translation_memory.replay.PROSE_CLASSES`)
— keyed by

    (node identity, source-content hash, target language)

where node identity is the register map's minted ``node_id`` and the
source hash is the NFC content hash of the source prose (the same
``node_identity.content_hash`` the register map uses; store-NFC /
compare-NFC contract).

Design invariants:

- **Query before model**: :meth:`TranslationMemory.lookup` answers only
  from the exact key. A hit returns the cached translation with no model
  call; anything else is a miss. Fuzzy candidates are *suggestions*
  (:meth:`TranslationMemory.suggest`) and are never applied automatically.
- **Precise invalidation**: a source edit changes the hash, so the stale
  segment simply stops matching — it is retained as history for fuzzy
  matching, never returned by ``lookup``. A map correction invalidates via
  :meth:`TranslationMemory.invalidate_node`, scoped to one node (and
  optionally one language); unrelated segments are untouched.
- **Instrumentation, not telemetry**: hit/miss/fuzzy counters live on the
  store and surface via :meth:`TranslationMemory.stats`. They are session
  state — never serialized — so cache runs cannot dirty the committed
  artifact. Any telemetry wiring is governed elsewhere (opt-out).

Artifact family: this is a versioned JSON artifact under ``.legesher/``
with the same discipline as the register map document (schema_version,
artifact discriminator, sorted order-stable content). The document payload
is self-describing and embeds losslessly under one key of a future
combined artifact, mirroring how ``RegisterMapDocument`` embeds the
IdentifierMap payload (CORE-1435 / CORE-1663 ride the same family). See
``libs/core/docs/translation-memory.md``.
"""

from __future__ import annotations

import json
import logging
import math
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Collection, Mapping

from ..artifact_io import atomic_write_text, parse_semver
from ..register_map.node_identity import (
    content_hash,
    legacy_nfc_hash,
    normalize_text,
)

logger = logging.getLogger(__name__)

#: Semver version of the serialized schema. Bump major on breaking shape
#: changes; readers reject artifacts from a different major.
SCHEMA_VERSION = "1.0.0"

#: Artifact discriminator so the file family is self-describing.
ARTIFACT_KIND = "legesher-translation-memory"

DEFAULT_ARTIFACT_FILENAME = "translation_memory.json"

#: Conservative default similarity floor for fuzzy suggestions.
DEFAULT_FUZZY_THRESHOLD = 0.85

#: Length-scaled floor (CORE-1709). Similarity is a poor discriminator on
#: short strings: ``"# step 1"`` vs ``"# step 2"`` scores 0.875 — above
#: the default threshold — while being a different instruction. One
#: character in eight is a large semantic difference and a small textual
#: one. Segments at or under :data:`SHORT_SEGMENT_CHARS` must clear
#: :data:`SHORT_SEGMENT_FLOOR`; the requirement relaxes linearly back to
#: the configured threshold by :data:`LONG_SEGMENT_CHARS`, so
#: long-docstring recall (the high-value case) is untouched.
#:
#: Both constants are calibrated against real cases on either side of
#: the line, not chosen for roundness:
#:
#: - ``"# step 1"`` vs ``"# step 2"`` — 0.875, must be REJECTED (a
#:   different instruction, the noise this gate exists for).
#: - ``"# helo"`` vs ``"# hello"`` — 0.923, must be KEPT (a typo fix,
#:   the highest-value short suggestion there is).
#: - ``"# compute the tax"`` vs ``"# compute the tax rate"`` — 0.87 at
#:   22 chars, must be KEPT (a genuine edit).
#:
#: The first two are the same length, so length alone cannot separate
#: them — the floor has to sit between their scores, which puts it at
#: 0.90, not higher. The third is why the scaled band stops at 20 chars
#: rather than reaching into the range where ordinary edits live.
SHORT_SEGMENT_CHARS = 12
LONG_SEGMENT_CHARS = 20
SHORT_SEGMENT_FLOOR = 0.90

#: Default cap on retained dead-node history per file (CORE-1708).
DEFAULT_STALE_HISTORY = 200


def effective_threshold(floor: float, length: int) -> float:
    """The similarity floor a candidate of ``length`` chars must clear.

    Never returns less than ``floor``: the scaling only ever tightens,
    so an explicitly-raised threshold is always honoured.
    """
    if length >= LONG_SEGMENT_CHARS:
        return floor
    if length <= SHORT_SEGMENT_CHARS:
        return max(floor, SHORT_SEGMENT_FLOOR)
    progress = (length - SHORT_SEGMENT_CHARS) / (
        LONG_SEGMENT_CHARS - SHORT_SEGMENT_CHARS
    )
    return max(floor, SHORT_SEGMENT_FLOOR + progress * (floor - SHORT_SEGMENT_FLOOR))


def length_band(length: int, floor: float) -> tuple[int, int]:
    """Inclusive candidate-length range that can still reach ``floor``.

    ``SequenceMatcher.ratio()`` is ``2 * M / T``, where ``T`` is the
    combined length and ``M`` the number of matched characters. Since
    ``M <= min(len(a), len(b))``, the ratio is bounded above by
    ``2 * min / (la + lb)`` — so for a needle of length ``la`` a
    candidate of length ``lb`` can only reach ``floor`` when

        floor * la / (2 - floor)  <=  lb  <=  la * (2 - floor) / floor

    Anything outside is rejected on arithmetic alone, before difflib is
    constructed at all. This is an exact bound, not a heuristic: no
    candidate that could have scored at or above the floor is excluded.
    """
    if floor <= 0:
        return 0, sys.maxsize
    low = math.ceil(floor * length / (2 - floor)) if floor < 2 else length
    high = math.floor(length * (2 - floor) / floor)
    return low, high


#: Provenance vocabulary: who minted a cached translation.
MINTED_BY: frozenset[str] = frozenset({"model", "human", "import"})

#: Segment lifecycle. ``stale`` segments are history: they participate in
#: fuzzy matching but are never returned by ``lookup``.
SEGMENT_STATUSES: frozenset[str] = frozenset({"active", "stale"})

#: The exact-match key: (node_id, source_hash, target_lang).
SegmentKey = tuple[str, str, str]


def default_artifact_path(repo_root: Path) -> Path:
    """The canonical location of the TM artifact in a repo."""
    return repo_root / ".legesher" / DEFAULT_ARTIFACT_FILENAME


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class PruneStats:
    """What one :meth:`TranslationMemory.prune` did.

    Attributes:
        demoted: Active segments whose node is gone, marked stale.
        dropped: Stale segments evicted past the history cap.
        retained: Stale segments kept as fuzzy history.
    """

    demoted: int = 0
    dropped: int = 0
    retained: int = 0

    def __add__(self, other: "PruneStats") -> "PruneStats":
        return PruneStats(
            demoted=self.demoted + other.demoted,
            dropped=self.dropped + other.dropped,
            retained=self.retained + other.retained,
        )


@dataclass
class TMSegment:
    """One cached prose translation, keyed by (node, source hash, language).

    Attributes:
        node_id: Register-map node identity of the prose element.
        source_hash: ``node_identity.content_hash`` of the source prose.
        target_lang: Target language code (e.g. ``"es"``).
        source_text: The source prose segment, NFC-normalized. Stored so
            stale segments can serve as fuzzy-match history.
        translated_text: The cached translation, NFC-normalized.
        minted_by: Provenance: one of :data:`MINTED_BY`.
        minted_at: ISO-8601 timestamp of minting.
        attribution: Free-form source attribution (model name, reviewer,
            import origin).
        status: One of :data:`SEGMENT_STATUSES`.
    """

    node_id: str
    source_hash: str
    target_lang: str
    source_text: str
    translated_text: str
    minted_by: str
    minted_at: str
    attribution: str = ""
    status: str = "active"

    def __post_init__(self) -> None:
        if self.minted_by not in MINTED_BY:
            raise ValueError(
                f"Invalid minted_by {self.minted_by!r}; "
                f"expected one of {sorted(MINTED_BY)}"
            )
        if self.status not in SEGMENT_STATUSES:
            raise ValueError(
                f"Invalid status {self.status!r}; "
                f"expected one of {sorted(SEGMENT_STATUSES)}"
            )
        # Storage contract, shared with the register map: LF, then NFC
        # (``node_identity.normalize_text``). The LF half matters most
        # here — prose segments are the multi-line class, so a CRLF
        # checkout would otherwise miss every docstring segment.
        raw_source = self.source_text
        self.source_text = normalize_text(self.source_text)
        self.translated_text = normalize_text(self.translated_text)
        if self.source_hash != content_hash(self.source_text):
            # Migration (CORE-1710): a segment written before the LF
            # policy stored CRLF prose and a hash taken over it. Its
            # stored hash is "wrong" only by that rule, so re-stamp it
            # rather than refusing to load — an artifact from last week
            # must not become unopenable, which would brick `map edit`
            # and `map compact` on every repo that has one.
            if self.source_hash == legacy_nfc_hash(raw_source):
                logger.debug(
                    "Migrating pre-LF-policy TM segment %s: re-hashing "
                    "normalized source",
                    self.node_id,
                )
                self.source_hash = content_hash(self.source_text)
            else:
                raise ValueError(
                    f"source_hash {self.source_hash!r} does not match the "
                    f"content hash of source_text "
                    f"({content_hash(self.source_text)!r})"
                )

    @property
    def key(self) -> SegmentKey:
        return (self.node_id, self.source_hash, self.target_lang)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "source_hash": self.source_hash,
            "target_lang": self.target_lang,
            "source_text": self.source_text,
            "translated_text": self.translated_text,
            "minted_by": self.minted_by,
            "minted_at": self.minted_at,
            "attribution": self.attribution,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TMSegment":
        return cls(
            node_id=data["node_id"],
            source_hash=data["source_hash"],
            target_lang=data["target_lang"],
            source_text=data["source_text"],
            translated_text=data["translated_text"],
            minted_by=data["minted_by"],
            minted_at=data["minted_at"],
            attribution=data.get("attribution", ""),
            status=data.get("status", "active"),
        )


@dataclass
class TranslationMemory:
    """Per-file TM store: exact lookup, entry-scoped invalidation, fuzzy
    suggestions, and hit-rate counters.

    Counters (``hits`` / ``misses`` / ``fuzzy_suggestions``) are session
    instrumentation for the enhanced-mode/agent layers; they are exposed
    via :meth:`stats` and deliberately excluded from serialization.

    ``fuzzy_threshold`` is likewise session configuration, not artifact
    state: it participates in dataclass equality but is never serialized,
    so a loaded store always starts at :data:`DEFAULT_FUZZY_THRESHOLD`.
    """

    file: str | None = None
    segments: dict[SegmentKey, TMSegment] = field(default_factory=dict)
    fuzzy_threshold: float = DEFAULT_FUZZY_THRESHOLD

    # Instrumentation (never serialized).
    hits: int = field(default=0, compare=False)
    misses: int = field(default=0, compare=False)
    fuzzy_suggestions: int = field(default=0, compare=False)

    # -- Write path --

    def add(
        self,
        node_id: str,
        source_text: str,
        target_lang: str,
        translated_text: str,
        *,
        minted_by: str,
        minted_at: str | None = None,
        attribution: str = "",
    ) -> TMSegment:
        """Cache a translation for a prose segment.

        The source hash is computed here (NFC contract); an existing
        segment at the same exact key is replaced and becomes active.
        """
        segment = TMSegment(
            node_id=node_id,
            source_hash=content_hash(source_text),
            target_lang=target_lang,
            source_text=source_text,
            translated_text=translated_text,
            minted_by=minted_by,
            minted_at=minted_at if minted_at is not None else _utc_now_iso(),
            attribution=attribution,
        )
        self.segments[segment.key] = segment
        return segment

    # -- Query-before-model path --

    def lookup(
        self, node_id: str, source_text: str, target_lang: str
    ) -> TMSegment | None:
        """Exact TM lookup: hit returns the cached segment (no model call),
        anything else is a miss.

        Only the counters are mutated — never the segments. A stale
        segment is history, not an answer.
        """
        key = (node_id, content_hash(source_text), target_lang)
        segment = self.segments.get(key)
        if segment is not None and segment.status == "active":
            self.hits += 1
            return segment
        self.misses += 1
        return None

    # -- Precise invalidation --

    def invalidate_node(self, node_id: str, *, target_lang: str | None = None) -> int:
        """Mark a node's cached segments stale (map correction).

        Scoped to one node, and to one language when ``target_lang`` is
        given; unrelated segments are untouched (entry-scoped
        invalidation, no over-invalidation). Stale segments are retained
        as fuzzy-match history. Returns the number of segments marked.
        """
        count = 0
        for segment in self.segments.values():
            if segment.node_id != node_id or segment.status != "active":
                continue
            if target_lang is not None and segment.target_lang != target_lang:
                continue
            segment.status = "stale"
            count += 1
        return count

    # -- Garbage collection (dead-node segments) --

    def prune(
        self,
        live_node_ids: Collection[str],
        *,
        keep_history: int = DEFAULT_STALE_HISTORY,
    ) -> PruneStats:
        """Demote segments whose node is gone, and bound the history.

        A segment whose ``node_id`` no longer exists in the register map
        can never be returned by :meth:`lookup` — node IDs are never
        reused — but it stayed ``active`` forever: surfacing in
        :meth:`suggest`, inflating :meth:`stats`, and growing the
        committed artifact without bound over a file's life (CORE-1708).

        Retention is **demote, bounded** rather than delete: a deleted
        docstring frequently comes back, and its old translation is the
        single best fuzzy candidate when it does. So dead-node segments
        become ``stale`` — history, invisible to ``lookup``, still
        available to ``suggest`` — and the stale pool is then capped at
        ``keep_history`` most recent by ``minted_at``, which is what
        actually bounds the artifact. Pass ``keep_history=0`` to drop
        dead history entirely.

        **Live segments are never touched**, so replay for live nodes is
        byte-identical before and after a prune.
        """
        live = set(live_node_ids)
        demoted = 0
        for segment in self.segments.values():
            if segment.node_id in live or segment.status != "active":
                continue
            segment.status = "stale"
            demoted += 1
        # Newest-first, with the segment key as a deterministic tie-break
        # so two segments minted in the same second evict reproducibly.
        stale = sorted(
            (s for s in self.segments.values() if s.status == "stale"),
            key=lambda segment: (segment.minted_at, segment.key),
            reverse=True,
        )
        dropped = 0
        for segment in stale[keep_history:]:
            del self.segments[segment.key]
            dropped += 1
        return PruneStats(
            demoted=demoted, dropped=dropped, retained=len(stale) - dropped
        )

    # -- Fuzzy matching (suggestions, never auto-applied) --

    def suggest(
        self,
        source_text: str,
        target_lang: str,
        *,
        threshold: float | None = None,
        scale_floor: bool = True,
    ) -> list[tuple[float, TMSegment]]:
        """Score-tiered fuzzy candidates for a source segment.

        Returns ``[(score, segment)]`` sorted by score descending
        (deterministic tie-break on the segment key), including stale
        history. Suggestions are surfaced, never applied: ``lookup``
        ignores them, and promoting one requires an explicit ``add``.

        **Prefilters (CORE-1709).** A full ``SequenceMatcher.ratio()``
        against every segment is O(n·m²) and measured ~405 ms at 10k
        segments — fine once per file, ruinous in an agent loop that
        suggests per segment. Two gates run first, both exact upper
        bounds on the score, so the result set is unchanged:

        1. :func:`length_band` — arithmetic on lengths alone, no
           difflib object constructed.
        2. ``quick_ratio()`` — an O(n) character-multiset bound that
           difflib guarantees is ``>= ratio()``.

        Only survivors pay for the quadratic ``ratio()``.

        ``scale_floor`` applies the length-scaled floor
        (:func:`effective_threshold`) that keeps near-identical short
        comments out of the results; pass ``False`` for the raw
        flat-threshold behaviour.
        """
        floor = self.fuzzy_threshold if threshold is None else threshold
        needle = normalize_text(source_text)
        if scale_floor:
            floor = effective_threshold(floor, len(needle))
        low, high = length_band(len(needle), floor)
        scored: list[tuple[float, TMSegment]] = []
        # autojunk=False: difflib's heuristic demotes characters that
        # appear in >1% of a sequence longer than 199 chars to junk —
        # for prose that silently guts spaces, cratering the ratio of
        # near-identical long comments/docstrings (the highest-value
        # segment class) far below any sane threshold.
        #
        # The needle stays argument `a` and the candidate argument `b`,
        # matching the pre-prefilter call exactly: difflib's ratio is not
        # contractually symmetric, so swapping them to exploit its b-side
        # caching could shift a borderline score across the threshold.
        matcher = SequenceMatcher(autojunk=False)
        matcher.set_seq1(needle)
        for segment in self.segments.values():
            if segment.target_lang != target_lang:
                continue
            if not low <= len(segment.source_text) <= high:
                continue
            matcher.set_seq2(segment.source_text)
            if matcher.quick_ratio() < floor:
                continue
            score = matcher.ratio()
            if score >= floor:
                scored.append((score, segment))
        scored.sort(key=lambda pair: (-pair[0], pair[1].key))
        self.fuzzy_suggestions += len(scored)
        return scored

    # -- Instrumentation --

    def stats(self) -> dict[str, Any]:
        """Hit-rate instrumentation for the layers that read the cache."""
        lookups = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "fuzzy_suggestions": self.fuzzy_suggestions,
            "lookups": lookups,
            "hit_rate": (self.hits / lookups) if lookups else None,
            "segments": len(self.segments),
            "stale_segments": sum(
                1 for segment in self.segments.values() if segment.status == "stale"
            ),
        }

    def reset_counters(self) -> None:
        self.hits = 0
        self.misses = 0
        self.fuzzy_suggestions = 0

    # -- Serialization (order-stable, counters excluded) --

    def to_dict(self) -> dict[str, Any]:
        """Serialize with a sorted, insertion-order-independent segment
        list so the artifact is git-friendly."""
        ordered = sorted(
            self.segments.values(),
            key=lambda segment: (
                segment.node_id,
                segment.target_lang,
                segment.source_hash,
            ),
        )
        return {
            "file": self.file,
            "segments": [segment.to_dict() for segment in ordered],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TranslationMemory":
        store = cls(file=data.get("file"))
        for segment_data in data.get("segments", []):
            segment = TMSegment.from_dict(segment_data)
            if segment.key in store.segments:
                raise ValueError(f"Duplicate TM segment key {segment.key!r}")
            store.segments[segment.key] = segment
        return store


@dataclass
class TranslationMemoryDocument:
    """The persisted TM artifact (one per repo, many files).

    Lives at ``.legesher/translation_memory.json``, keyed by source file
    path like the register map document. The payload is self-describing
    (schema_version + artifact discriminator), so a future combined
    artifact-family document embeds it losslessly under one key — the same
    contract ``RegisterMapDocument.embed_identifier_map`` establishes for
    the identifier map (CORE-1435 / CORE-1663).
    """

    source_lang: str = "en"
    schema_version: str = SCHEMA_VERSION
    files: dict[str, TranslationMemory] = field(default_factory=dict)

    def get_or_create(self, file: str) -> TranslationMemory:
        """The per-file store for ``file``, creating it if absent."""
        store = self.files.get(file)
        if store is None:
            store = TranslationMemory(file=file)
            self.files[file] = store
        return store

    def prune(
        self,
        live_node_ids: Mapping[str, Collection[str]],
        *,
        keep_history: int = DEFAULT_STALE_HISTORY,
    ) -> PruneStats:
        """Prune every per-file store against the map's live node IDs.

        ``live_node_ids`` maps source-file path to the node IDs that
        file's register map still holds — see
        :func:`legesher_core.translation_memory.live_node_ids`. A file
        **absent from the mapping** has every one of its segments treated
        as dead: the file itself is gone from the map (deleted or
        renamed), which is exactly when its TM store should collapse to
        bounded history rather than persist in full.
        """
        totals = PruneStats()
        for path, store in self.files.items():
            totals = totals + store.prune(
                live_node_ids.get(path, ()), keep_history=keep_history
            )
        return totals

    def stats(self) -> dict[str, Any]:
        """Counters aggregated across every per-file store."""
        totals = {
            "hits": 0,
            "misses": 0,
            "fuzzy_suggestions": 0,
            "segments": 0,
            "stale_segments": 0,
        }
        for store in self.files.values():
            file_stats = store.stats()
            for name in totals:
                totals[name] += file_stats[name]
        lookups = totals["hits"] + totals["misses"]
        totals["lookups"] = lookups
        totals["hit_rate"] = (totals["hits"] / lookups) if lookups else None
        return totals

    # -- Serialization --

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact": ARTIFACT_KIND,
            "source_lang": self.source_lang,
            "files": {
                path: store.to_dict() for path, store in sorted(self.files.items())
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TranslationMemoryDocument":
        artifact = data.get("artifact")
        if artifact != ARTIFACT_KIND:
            raise ValueError(
                f"Not a translation memory artifact: artifact={artifact!r} "
                f"(expected {ARTIFACT_KIND!r})"
            )
        version = data.get("schema_version", "")
        major, _minor, _patch = parse_semver(version)
        expected_major = parse_semver(SCHEMA_VERSION)[0]
        if major != expected_major:
            raise ValueError(
                f"Unsupported schema_version {version!r}: this reader "
                f"handles major version {expected_major}"
            )
        document = cls(
            source_lang=data.get("source_lang", "en"),
            schema_version=version,
        )
        for path, store_data in data.get("files", {}).items():
            document.files[path] = TranslationMemory.from_dict(store_data)
        return document

    def save(self, path: Path) -> None:
        """Write the artifact as human-readable, git-friendly JSON."""
        atomic_write_text(
            path, json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n"
        )
        logger.info("Saved translation memory: %d file(s) to %s", len(self.files), path)

    @classmethod
    def load(cls, path: Path) -> "TranslationMemoryDocument":
        data = json.loads(path.read_text(encoding="utf-8"))
        document = cls.from_dict(data)
        logger.info(
            "Loaded translation memory: %d file(s) from %s",
            len(document.files),
            path,
        )
        return document
