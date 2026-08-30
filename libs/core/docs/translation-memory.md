# Translation memory — node-keyed prose cache

> **Maintainer notes — not newcomer documentation.** Written for someone already
> working in this code: it assumes repo context, uses internal vocabulary, and
> may cite work-tracker ids (`CORE-####`) an outside reader cannot resolve.
> Public on purpose, but not part of the documentation site and not localized —
> newcomer-facing documentation lives at [docs.legesher.io](https://docs.legesher.io).
> <!-- disposition: MAINTAINER (CORE-1724 audit, 2026-08-11) -->

Status: shipped with CORE-411 (schema v1.0.0)
Module: `legesher_core.translation_memory` (`model.py`; the map-driven
replay renderer moved to the commercial map engine, CORE-2011/CORE-2027)
Artifact: `.legesher/translation_memory.json`

The translation memory (TM) is the prose cache of the Legesher map: it
caches translated prose segments — comments and docstrings — so a segment is
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

- **Node identity** — the map engine's minted `node_id` (mint-and-store;
  the node-identity contract is documented with the commercial map engine). The key is node-scoped:
  identical prose under a different node is a fuzzy suggestion, never an
  exact hit.
- **Source-content hash** — `text_identity.content_hash` of the source
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

The map engine's replay renderer (commercial, CORE-2027) is the wire-in
seam: map prose entries become TM segments, the `translate` model seam is
reached only on a miss, and a fully warmed TM renders byte-identical
output with zero model consultations (the REPLAY invariant). Per-file stores materialize in the
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
`[(score, segment)]` sorted by score descending (difflib ratio over
normalized text; default threshold 0.85, configurable per store or per
call), including stale history. Suggestions below identity are
**surfaced, not applied**: `lookup` ignores them entirely, and promoting
a candidate requires an explicit `add()` (with its own provenance).

### Prefilters

A full `SequenceMatcher.ratio()` against every segment is O(n·m²) —
measured ~495 ms at 10k segments, so an agent loop suggesting per
segment spends seconds per file. Two gates run first, and **both are
exact upper bounds on the score**, so the result set is unchanged:

1. **Length band** — since `ratio = 2M/T` and `M ≤ min(la, lb)`, a
   candidate can only reach `floor` when
   `floor·la/(2−floor) ≤ lb ≤ la·(2−floor)/floor`. Pure arithmetic; no
   difflib object is constructed for a rejected candidate.
2. **`quick_ratio()`** — difflib's O(n) character-multiset bound, which
   it guarantees is `≥ ratio()`.

Measured **12.5× at 10k segments** (495 ms → 40 ms per suggest), with
results verified identical to the unfiltered scan on a golden corpus.
The needle stays argument `a` and the candidate argument `b`: difflib's
ratio is not contractually symmetric, so swapping them to exploit its
b-side caching could move a borderline score across the threshold.

### Length-scaled floor

Similarity is a poor discriminator on short strings. `"# step 1"` vs
`"# step 2"` scores 0.875 — above the default threshold — while being a
different instruction. Segments at or under 12 chars must clear 0.90,
relaxing linearly back to the configured threshold by 20 chars.

The constants are calibrated against cases on both sides of the line,
not chosen for roundness: `"# helo"` → `"# hello"` (0.923, a typo fix)
must be **kept** and is the same length as the step-1/step-2 pair, so
only the score can separate them; `"# compute the tax"` →
`"# compute the tax rate"` (0.87 at 22 chars) must also be kept, which
is why the scaled band stops well short of where ordinary edits live.
Pass `scale_floor=False` for the raw flat threshold.

## Pruning dead-node segments

A segment whose register-map node was deleted can never be returned by
`lookup` — node IDs are never reused — but it used to stay `active`
forever: surfacing in `suggest`, inflating `stats`, and growing the
committed artifact without bound over a file's life.

`prune(live_node_ids, keep_history=200)` (and the document-level
equivalent, driven by the map engine's live-node set) fixes that.
**Retention is demote-then-bound, not delete:**

- Dead-node segments become `stale` — history, invisible to `lookup`,
  still available to `suggest`. A deleted docstring frequently comes
  back, and its old translation is then the single best candidate there
  is; deleting outright throws that away.
- The stale pool is then capped at `keep_history` most recent by
  `minted_at` (segment key as a deterministic tie-break). **That cap is
  what actually bounds the artifact** — demotion alone does not.
- **Live segments are never touched**, so rendered output for live nodes
  is byte-identical before and after a prune.
- A file absent from the mapping has every segment treated as dead: the
  file is gone from the map, which is exactly when its store should
  collapse to bounded history.

`keep_history=0` drops dead history entirely. Surfaced through the
commercial map engine's `compact` command.

## Serialization & artifact family

`TranslationMemoryDocument` is a versioned JSON artifact
(`schema_version`, semver; readers reject a different major;
`artifact: "legesher-translation-memory"`) written to
`.legesher/translation_memory.json`, keyed by source-file path like the
register map document. Content is sorted and order-stable (segments sort
by `(node_id, target_lang, source_hash)`; files sort by path), so
save → load → save is byte-identical and diffs stay git-friendly.

Writes are atomic (`artifact_io.atomic_write_text`: sibling temp file,
fsync, `os.replace`), so a crash mid-write leaves the previous valid
artifact rather than a truncated one. Segment text obeys the family's
storage normalization — **LF, then NFC** — which matters most here:
prose is the multi-line class, so before that rule a CRLF checkout
missed every docstring segment. The storage normalization contract lives
in `legesher_core.text_identity`.

Artifact-family note: the document payload is self-describing and embeds
losslessly under a single key of a future combined document — the
artifact-family embed contract shared with the commercial map engine.
CORE-1435 (team map artifact) and CORE-1663 ride the same family.

Deferred (per CORE-411): TMX/TBX export and CAT-tool interop.
