# Candidate sources: models, initiatives, and the license line

Where the candidates a reviewer judges come from, how each source is
fetched and attributed, and which sources may be *stored* versus only
*shown*. Registry table: `import_sources` (doc 02); provenance attaches per
option via `option_provenance` (`source ∈ model|community|maintainer|
import|literature`, `source_detail → import_sources.id`).

The content-addressed option identity does the deduplication: the same word
proposed by Aya, found in Hedy, and typed by a reviewer is **one option**
with three provenance trails — which is precisely what makes "how many
people said this word" meaningful next to "and two other projects chose it
independently."

## 1. The reviewer (highest-value source)

The blind-phase suggestion (`elicited='blind'`) plus any post-reveal
additions. Persisted as `source='community'` provenance with the
contributor's opaque id, word_form, rationale, and self-annotations.
A reviewer typing a word that already exists as an option adds provenance +
endorsement, not a duplicate.

## 2. The model panel

Multiple models generate independently per (concept × locale), each running
the linguist-not-translator prompt (brief + dynamic consistency-group
injection + locale `terminology_policy` + script/keyboard constraints —
doc 06 of the multi-pl proposal). Output schema is the brief's Translation
Output Format (term, form, confidence, rationale, established-term report).

- Panel roster is config, not code: seed with Aya (Expanse / 101 lineage —
  the multilingual bet), Claude (current), and at least one open multilingual
  baseline (NLLB-class or Qwen-class) so the panel never collapses to one
  vendor. Each panelist = one `import_sources` row
  (`model:<family>-<version>`), `redistributable=1` (our own generations),
  attribution = model card.
- **Policy, enforced at generation**: transliteration is never an acceptable
  fallback; the legal answer set is native coinage with rationale, genuine
  cognate kept as-is, or an explicit "no good native form exists" escalation
  (2026-07-05). A panel candidate that arrives transliterated anyway gets
  `option_flags(reason='transliteration')` at import — the flag lane is for
  model-policy violations; the *annotation* lane is for community
  description (doc 02).
- Low-resource honesty: UniPy's evaluation (French 50.1% / Greek 38.6% raw
  acceptability; LLM collapse on Bengali/Hindi) is the standing argument
  that panel output is **material for review, never a shipping path** — and
  why panel disagreement with a human carries zero gate weight.
- Model rationale strings are stored in `option_provenance.rationale`
  (export decision = CORE-1501 Q6).

## 3. The initiatives (prior-art terms as reference candidates)

Verified 2026-07-18 (licenses via GitHub API; mechanisms per doc 10 of the
multi-pl proposal):

| source | what exists | license | posture |
| --- | --- | --- | --- |
| **UniversalPython** | per-language YAML dictionaries `universalpython/languages/<code>/default.yaml` (14 dirs incl. ur, hi, ko, tr; `reserved:` maps native→English incl. digits/punctuation) | Apache-2.0 | **importable**: fetch at kit build, pin `fetched_ref`, store as options (`source='import'`), attribute "UniversalPython" per option |
| **Hedy** | per-language keyword translations (Weblate-managed YAML under `content/keywords/`; ~40+ languages) — verify exact paths at import | EUPL-1.2 | **reference-only** (EUPL → Apache re-licensing not permitted) |
| **UniPy** (GMU) | hand-built native-annotator dictionaries, 8 languages (es, fr, el, zh, hi, bn, ckb, ar) | no license file found | **reference-only** (all-rights-reserved default) |
| **Scratch** | Transifex block-vocabulary translations, 70+ languages (concept overlap: repeat/if-else/broadcast tier) | repo AGPL-3.0; translation content terms separate | **reference-only** |

**The reference-only mechanics** (the license line, drawn precisely):

- Reference terms ship **in the review kit only**, marked
  `reference_only: true`, each with attribution + source URL + fetched
  revision. The kit is a transient build artifact, not a published dataset.
- The importer **never persists** a reference-only term as an option. If a
  reviewer endorses one, the app records the reviewer *submitting that word
  themselves* (`source='community'`, their attestation, their judgment on a
  single word — single terms are facts; the initiative's protected asset is
  its curated compilation) with a `matches_reference:<source>` note in
  provenance rationale for honesty.
- Bulk redistribution of any reference-only mapping table in the Apache-2.0
  corpus is structurally impossible: `import_sources.redistributable=0`
  excludes the source from every exporter.
- Open item for counsel review: confirm the single-term/compilation line,
  and EU database-rights posture for Hedy (NL-based).
- The collaboration path beats the license path: Bazaz (UniversalPython) is
  already embedded in Tiny Aya; Hedy's team and the UniPy authors are
  plausible partners for explicit term-list grants — at which point a
  source flips to `redistributable=1` by data change, not redesign.

Why initiative terms earn their place in the kit: they are the only
candidates with **classroom exposure** (Hedy, Scratch) or **native-annotator
curation** (UniPy) behind them — evidence a model candidate cannot carry.
The reviewer sees that evidence *after* ranking (source-blind rule,
doc 01 §3).

## 4. Current shipped pack + v1 candidate pool

The shipped pack value (v1 `selected_translations`, migrating to canon) is
always a candidate — reviewers must be able to dethrone it. The 16,797-row
v1 `translations` pool migrates as options with their original source
provenance (`aya`, `claude`, `community`, `yaml-import`, …), so review
starts against everything ever proposed, not a blank page.

## 5. Kit-build pipeline

```
build-review-kit <locale>:
  1. snapshot DB → concepts, briefs, canon, options+standings, validations
  2. run model panel for concepts lacking fresh panel coverage (cache by
     (concept, locale, model, prompt_rev))
  3. fetch initiative sources at pinned refs → normalize (NFC) → match to
     concepts by English token per PL → label redistributable vs reference
  4. dedupe everything by (concept, locale, pl_scope, NFC(form)) → candidate
     cards with badge lists
  5. emit kit.json + manifest (kit_version, attribution block, license notes)
```

Initiative matching caveat: their dictionaries key by English *token*
(UniversalPython: per-PL reserved map; Hedy: its own keyword set; Scratch:
block labels). Mapping token → concept reuses the same curation table the
multi-PL work builds (`terms`), so a Hedy `repeat` lands on the right
concept, and tokens with no concept (Hedy-specific pedagogy words) drop out
of scope automatically.
