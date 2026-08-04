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
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from ..register_map.node_identity import content_hash, normalize_nfc

logger = logging.getLogger(__name__)

#: Semver version of the serialized schema. Bump major on breaking shape
#: changes; readers reject artifacts from a different major.
SCHEMA_VERSION = "1.0.0"

#: Artifact discriminator so the file family is self-describing.
ARTIFACT_KIND = "legesher-translation-memory"

DEFAULT_ARTIFACT_FILENAME = "translation_memory.json"

#: Conservative default similarity floor for fuzzy suggestions.
DEFAULT_FUZZY_THRESHOLD = 0.85

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
        # Store-NFC contract (shared with the register map).
        self.source_text = normalize_nfc(self.source_text)
        self.translated_text = normalize_nfc(self.translated_text)
        if self.source_hash != content_hash(self.source_text):
            raise ValueError(
                f"source_hash {self.source_hash!r} does not match the NFC "
                f"content hash of source_text ({content_hash(self.source_text)!r})"
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

    # -- Fuzzy matching (suggestions, never auto-applied) --

    def suggest(
        self,
        source_text: str,
        target_lang: str,
        *,
        threshold: float | None = None,
    ) -> list[tuple[float, TMSegment]]:
        """Score-tiered fuzzy candidates for a source segment.

        Returns ``[(score, segment)]`` sorted by score descending
        (deterministic tie-break on the segment key), including stale
        history. Suggestions are surfaced, never applied: ``lookup``
        ignores them, and promoting one requires an explicit ``add``.
        """
        floor = self.fuzzy_threshold if threshold is None else threshold
        needle = normalize_nfc(source_text)
        scored: list[tuple[float, TMSegment]] = []
        for segment in self.segments.values():
            if segment.target_lang != target_lang:
                continue
            # autojunk=False: difflib's heuristic demotes characters that
            # appear in >1% of a sequence longer than 199 chars to junk —
            # for prose that silently guts spaces, cratering the ratio of
            # near-identical long comments/docstrings (the highest-value
            # segment class) far below any sane threshold.
            score = SequenceMatcher(
                a=needle, b=segment.source_text, autojunk=False
            ).ratio()
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


def _parse_semver(version: str) -> tuple[int, int, int]:
    try:
        major, minor, patch = (int(part) for part in version.split("."))
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Invalid schema_version {version!r}: {exc}") from exc
    return major, minor, patch


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
        major, _minor, _patch = _parse_semver(version)
        expected_major = _parse_semver(SCHEMA_VERSION)[0]
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
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
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
