# Translation memory — node-keyed prose cache

Status: shipped with CORE-411 (schema v1.0.0)
Module: `legesher_core.translation_memory` (`model.py`, `replay.py`)
Artifact: `.legesher/translation_memory.json`

The translation memory (TM) is the prose cache of the Legesher map: it
caches translated prose segments — comments and docstrings, the
register-map classes in `replay.PROSE_CLASSES` — so a segment is
translated by a model (or a human) once and replayed deterministically
thereafter.

The `string` element class is deliberately **excluded** from the prose
layer: string literals are code-adjacent values (their content is
load-bearing at runtime), so they stay with the code path rather than the
prose cache. Only `comment` and `docstring` segments are TM territory.

## Keying

Each cached segment is keyed by the triple

```text
(node identity, source-content hash, target language)
```

- **Node identity** — the register map's minted `node_id` (mint-and-store;
  see `docs/register-map-node-identity.md`). The key is node-scoped:
  identical prose under a different node is a fuzzy suggestion, never an
  exact hit.
- **Source-content hash** — `node_identity.content_hash` of the source
  prose: `sha256(NFC(text))` truncated to 16 hex chars. The store-NFC /
  compare-NFC contract is shared with the register map, so canonically
  equivalent renderings of the same source hit the same segment.
- **Target language** — the language code of the cached translation.

The value is the translated text (stored NFC) plus provenance —
`minted_by` (`model | human | import`), `minted_at`, a free-form
`attribution` string — and a `status` (`active | stale`).

## Query before model

`TranslationMemory.lookup(node_id, source_text, target_lang)` answers only
from the exact key: a hit returns the cached translation with **no model
call**; anything else is a miss. Lookup never mutates the store except the
instrumentation counters (`hits` / `misses` / `fuzzy_suggestions`, exposed
via `stats()`). Counters are session instrumentation for the
enhanced-mode/agent layers and are deliberately **not serialized** — cache
runs must not dirty the committed artifact. Telemetry wiring is governed
elsewhere (opt-out); this layer only counts.

`replay.render_prose(map_doc, tm_doc, target_lang, translate=...)` is the
minimal wire-in seam: comments/docstrings from the register map become TM
segments, the `translate` model seam is reached only on a miss, and a
fully warmed TM renders byte-identical output with zero model
consultations (the REPLAY invariant). Per-file stores materialize in the
document only once a segment is actually cached, so prose-free files and
model-less preview renders leave the artifact untouched.

## Invalidation semantics (entry-scoped)

- **Source edit** — the segment's hash no longer matches, so `lookup`
  misses naturally. The stale-by-hash segment is *retained as history* for
  fuzzy matching; re-translation adds a new segment at the new hash.
- **Map correction** — when the node's term changes in the register map's
  translation column, `invalidate_node(node_id, target_lang=...)` marks
  exactly that node's segments (optionally one language) `stale`.
  Unrelated segments are untouched: invalidation is entry-scoped, never
  file- or store-wide.
- `stale` segments are history, not answers: they participate in
  `suggest()` but are never returned by `lookup`.

## Fuzzy matching (suggestions, never auto-applied)

`suggest(source_text, target_lang, threshold=...)` returns
`[(score, segment)]` sorted by score descending (difflib ratio over NFC
text; default threshold 0.85, configurable per store or per call),
including stale history. Suggestions below identity are **surfaced, not
applied**: `lookup` ignores them entirely, and promoting a candidate
requires an explicit `add()` (with its own provenance).

## Serialization & artifact family

`TranslationMemoryDocument` is a versioned JSON artifact
(`schema_version`, semver; readers reject a different major;
`artifact: "legesher-translation-memory"`) written to
`.legesher/translation_memory.json`, keyed by source-file path like the
register map document. Content is sorted and order-stable (segments sort
by `(node_id, target_lang, source_hash)`; files sort by path), so
save → load → save is byte-identical and diffs stay git-friendly.

Artifact-family note: this is the second member of the register-map
artifact family. The document payload is self-describing and embeds
losslessly under a single key of a future combined document — the same
contract `RegisterMapDocument.embed_identifier_map` establishes for the
identifier map. CORE-1435 (team map artifact) and CORE-1663 ride the same
family.

Deferred (per CORE-411): TMX/TBX export and CAT-tool interop.
