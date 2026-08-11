# Canonical translation selection (CORE-1400)

> **Maintainer notes — not newcomer documentation.** Written for someone already
> working in this code: it assumes repo context, uses internal vocabulary, and
> may cite work-tracker ids (`CORE-####`) an outside reader cannot resolve.
> Public on purpose, but not part of the documentation site and not localized —
> newcomer-facing documentation lives at [docs.legesher.io](https://docs.legesher.io).
> <!-- disposition: MAINTAINER (CORE-1724 audit, 2026-08-11) -->

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
   | 2 | `community` | legesher-translations import — human-written, no named author |
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

## Two source vocabularies, and why they differ

The rank-3 table above is the **v1 `translations.source`** vocabulary. The
published corpus uses a *different*, four-value one — **v2
`option_provenance.source`**, exported as `options.sources` on Hugging Face.
They are easy to confuse because two names appear in both, so keep the axes
straight:

| | v1 `SOURCE_TRUST` | v2 provenance |
| --- | --- | --- |
| answers | *whose word do we ship?* (credibility) | *what do we owe for this row?* (obligation) |
| audience | internal, selection only | **public** — it ships in the dataset |
| shape | fine-grained, grows with the pipelines | four values, deliberately coarse and stable |
| values | `community_review` … `aya` (9) | `legesher`, `upstream`, `community`, `model` |

The trap is `community`. In **v1** it labels the 2,169 rows lifted wholesale
from `legesher/legesher-translations` — another repository's work, with no
individual author on the row. In **v2** those are `upstream`, and `community`
means something narrower: a named individual's own assertion through the
native-review process, carrying credit-on-request and withdrawal-on-request.
Rank 2 is still the right *credibility* call — a human wrote them — but
reading v1 `community` as "our reviewers said so" is wrong.

Crossing the boundary:

| v1 source | v2 provenance |
| --- | --- |
| `community_review` | `community` |
| `community` | `upstream` |
| `yaml-import`, `yaml_pack`, `core-1318-fix`, `machine-composed` | `legesher` |
| `claude`, `claude_agent`, `aya` | `model` |

`machine-composed` lands in `legesher`, not `model`: a human assembled those
values from existing pack material, and `model` would overstate the machine's
involvement.

The authoritative mapping is `scripts/migrate_to_v2.SOURCE_MAP`, which
**refuses to migrate a source it has no bucket for** rather than defaulting
one. An obligation cannot be defaulted — every fallback picks a bucket, and
the only bucket a fallback could pick without asserting something false about
a stranger's work is the one claiming we authored it. That is precisely how
`core-1318-fix` (87 rows) once rode a `.get(..., "import")` default into the
grab-bag without anyone deciding it belonged there (CORE-1720).

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
