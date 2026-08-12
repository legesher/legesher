"""Translation memory — node-keyed prose cache (CORE-411).

Caches translated prose segments (comments and docstrings —
``PROSE_CLASSES``) keyed by (register-map node identity, NFC
source-content hash, target language), with query-before-model lookup,
entry-scoped invalidation, score-tiered fuzzy suggestions, and
deterministic replay.

Second member of the register-map artifact family (see
``libs/core/docs/translation-memory.md``). Pure stdlib: importable
without the optional tree-sitter C extensions.
"""

from .model import (
    ARTIFACT_KIND,
    DEFAULT_ARTIFACT_FILENAME,
    DEFAULT_FUZZY_THRESHOLD,
    DEFAULT_STALE_HISTORY,
    LONG_SEGMENT_CHARS,
    MINTED_BY,
    SCHEMA_VERSION,
    SEGMENT_STATUSES,
    SHORT_SEGMENT_CHARS,
    SHORT_SEGMENT_FLOOR,
    PruneStats,
    TMSegment,
    TranslationMemory,
    TranslationMemoryDocument,
    default_artifact_path,
    effective_threshold,
    length_band,
)
from .replay import (
    PROSE_CLASSES,
    RenderedSegment,
    TranslateFn,
    live_node_ids,
    prose_entries,
    render_file_prose,
    render_prose,
)

__all__ = [
    "ARTIFACT_KIND",
    "DEFAULT_ARTIFACT_FILENAME",
    "DEFAULT_FUZZY_THRESHOLD",
    "DEFAULT_STALE_HISTORY",
    "LONG_SEGMENT_CHARS",
    "MINTED_BY",
    "PROSE_CLASSES",
    "SCHEMA_VERSION",
    "SEGMENT_STATUSES",
    "SHORT_SEGMENT_CHARS",
    "SHORT_SEGMENT_FLOOR",
    "PruneStats",
    "RenderedSegment",
    "TMSegment",
    "TranslateFn",
    "TranslationMemory",
    "TranslationMemoryDocument",
    "default_artifact_path",
    "effective_threshold",
    "length_band",
    "live_node_ids",
    "prose_entries",
    "render_file_prose",
    "render_prose",
]
