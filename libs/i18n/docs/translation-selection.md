# Canonical translation selection (CORE-1400)

How Legesher decides which translation value is *canonical* for a
`(term, language)` pair — the value that lands in `selected_translations`
and is exported into the shipped YAML packs.

## Why a selection rule exists

The `translations` table is a **candidate pool** and is dirty *by
design*: it keeps every suggestion each source ever produced, including
raw model output that is not a valid Python identifier (e.g. the French
Aya candidate `arithmeticerror → "erreur arithmétique"` — two words, a
space, unusable as code). Under the options model (CORE-1501) that is
fine: candidates are evidence, not product.

What must never be dirty is what gets **published**. Before CORE-1400 the
YAML exporter chose values directly from the candidate pool by
confidence, so a full pack regeneration would have reverted ~183 cleaned
exception values (plus dirty keyword/builtin candidates) back to invalid
raw forms. The selection rule moves that decision to one documented,
gated place.

## The rule

For each `(term, language)` pair, in precedence order:

1. **Validity gate.** A value is selectable only if it passes the pack
   schema's identifier check (`legesher_i18n.selection.is_valid_pack_value`,
   which delegates to `LanguagePackSchema._is_valid_identifier`):
   non-empty, no leading/trailing whitespace, no spaces or punctuation,
   valid Python identifier per PEP 3131. The soft keyword `except*` has a
   documented allowance: its translations may carry an optional trailing
   `*` on an otherwise-valid identifier (both starred, e.g. `excepter*`,
   and unstarred, e.g. `кроме`, forms ship today). Invalid candidates
   stay in the pool; they can never become canonical.

2. **Shipped-pack anchor.** If the language already ships a pack value
   for the term and that value passes the gate, it is canonical. Shipped
   packs have passed the mechanical quality floor (collision audit, NFKC
   guard, schema validation) and carry surgical curation (CORE-1303,
   CORE-1317, CORE-1318) that must survive regeneration value-for-value
   (the regen gate certifies values, keys, sections, and metadata; YAML
   byte representation may differ).

3. **Source trust.** Otherwise the best valid candidate wins, ordered by
   `selection.SOURCE_TRUST` (most → least trusted):

   | rank | source | why |
   |------|--------|-----|
   | 1 | `community_review` | outcome of a native-reviewer pass |
   | 2 | `community` | community-contributed value |
   | 3 | `core-1318-fix` | curated corrections from the CORE-1318 audit |
   | 4 | `machine-composed` | curated machine composition (CORE-1317 style) |
   | 5 | `claude_agent` | linguist-framed agent output |
   | 6 | `claude` | single-shot Claude output |
   | 7 | `yaml_pack` | value imported back from a shipped pack |
   | 8 | `yaml-import` | bulk pack import (older, less provenance) |
   | 9 | `aya` | raw Aya model output |

   Ties break by confidence (`high` > `medium` > `low` > unset), then by
   lexicographically smallest translation so repeated runs agree.
   Unlisted sources rank below every listed source.

4. **No fallback.** If nothing passes the gate the term stays
   unselected, and the exporter refuses to emit the pack — with
   `IncompleteSelectionError` in strict mode; the non-strict bulk path
   skips the language with a warning and writes nothing, and the regen
   gate's `not_regenerated` finding blocks on the skip. Silent dropping
   or "best dirty value" fallbacks are forbidden either way: no partial
   pack ever reaches disk.

## Enforcement points

- **Write boundary** — `TranslationDatabase.set_selected` raises
  `ValueError` for any value that fails the gate, and for round-trip
  collisions (two different *term names* in one language sharing a
  selected value). Same-name terms are exempt: `type` exists as both the
  3.10 builtin and the 3.12 soft keyword (two term rows since CORE-1400,
  `UNIQUE(name, programming_language, category)`), and the same surface
  token mapping to the same translation in both slots is not an
  ambiguity.
- **Export boundary** — the YAML exporter (`scripts/translate/yaml_exporter.py`)
  reads **only** `selected_translations`, never the candidate pool. In
  strict mode a partially-selected language raises
  `IncompleteSelectionError`; a zero-selection language, and any language
  on the non-strict bulk path, is skipped with a warning and no file is
  written. Data-integrity failures in a bulk run are collected and raised
  together as `BulkExportError` after the healthy languages complete.
- **Audit** — `scripts/audit_collisions.py` (DB + pack layers) and
  `scripts/verify_pack_regen.py` (value-aware regen diff) are the quality
  floor: the regen gate is the backstop that turns any silent skip into a
  blocking `not_regenerated` / `export_failed` finding. Run it before any
  regen-and-commit workflow (CI wiring is CORE-1579; org Actions are
  currently off).

## Backfill provenance

The one-time cleanup that brought `selected_translations` into line with
this rule is `scripts/translate/backfill_core1400.py`. Rows it created
carry `selected_by = 'CORE-1400'` and a `selection_reason` naming the
precedence branch that fired (e.g. `shipped-pack-value`).
