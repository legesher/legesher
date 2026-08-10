# Translation quality gates — inventory (CORE-1021)

The automated quality checks that stand between a pack edit (or a generation
run) and shipped language packs. The 103-language generation ritual cites this
inventory: run every gate marked "manual" below as part of that ritual.

**Execution reality (2026-07):** org GitHub Actions are disabled, so
workflow-declared gates do not currently run on push/PR — they are
*declarative only*. The executing gates today are pre-commit hooks and manual
local runs. The "Executes today" column reflects that; local commands are
listed under the table.

## Gate inventory

| Check | Script / process | What it catches | Executes today | Blocking? |
|---|---|---|---|---|
| Unicode/script audit | `libs/i18n/legesher_i18n/scripts/audit_packs.py` (uses `script_policy.py` + `schema_validator.py`) | NFKC instability, foreign-script bleed-through, illegal bidi/format controls, live-keyword collisions, min-interpreter XID traps, duplicate targets, invalid identifiers; undecodable/malformed packs surface as `load-error` | Workflow-declarative only (`.github/workflows/validate-packs.yml`); run manually | Blocking on errors; warnings advisory (CORE-1318) |
| Collision audit | `libs/i18n/scripts/audit_collisions.py` | Cross-section/cross-partition collisions across the DB and all packs, incl. non-pack-edit paths (CORE-950, CORE-710) | Workflow-declarative only (`.github/workflows/ci.yml`); run manually | Blocking |
| Pack schema/format | `libs/i18n/scripts/validate_language_pack_yaml.py` | Non-string values, unquoted YAML booleans, spaces/punctuation in values, structure, intra-pack duplicate translations, script-aware conventions | pre-commit hook `validate-language-pack-yaml` (changed pack files) | Blocking |
| Data contract | `libs/i18n/legesher_i18n/scripts/enforce_data_contract.py` (uses `data_contract.py`) | "Packs are data, not code" (CORE-1453): file-size cap, YAML tags/anchors/aliases, unknown top-level keys, non-http(s) metadata URLs, render-vs-execute round-trip on the merged pack (soft-keyword divergence exempt) | pre-commit hook `enforce-pack-data-contract` (pack-file changes trigger a full-tree walk) | Blocking |
| Term screening | `libs/i18n/scripts/translate/screen_terms.py` (prompt: `scripts/translate/prompts/term_screening_prompt.md`) | Offensive/unfortunate translations (CORE-401): profanity, slurs, sexual/scatological readings, unfortunate connotations, embarrassing collisions. LLM screen per language writes `reports/term-screening/<lang>.yml`; `--gate` is mechanical — unscreened language, stale coverage digest (pack changed since screen), or untriaged flag all fail | Manual ritual + generation-ritual step per new pack (`--gate --lang <code>`) | Blocking when run; flags route to native review (CORE-1538) |
| Style guides | `libs/i18n/legesher_i18n/scripts/validate_style_guides.py` | Style-guide schema violations; drift between guides' derived flags and `legesher_i18n/languages.json` | pre-commit hook `validate-style-guides` | Blocking |
| Regen integrity | `libs/i18n/scripts/verify_pack_regen.py` | Regen-vs-shipped diff classes (`value_changed`, `key_added`, `key_removed`, `unknown_section`, `not_regenerated`, ...) — proves DB→YAML regeneration is safe (CORE-1400) | Manual ritual; wired into nothing — run before any pack regeneration | Blocking by convention |
| Untranslated terms | `libs/i18n/scripts/translate/find_untranslated.py` | Pack entries whose translation equals the source term (key == value), net of the intentional-loanword allowlist; allowlisted cognates report as their own class (identity_ok, CORE-1355), and `--check-db` drift-checks the allowlist against the corpus DB's selected translations — drift blocks even under `--warn-only` | pre-commit hook `find-untranslated-terms` (changed pack files, runs `--check-db`) | **Report-only for pack findings** (`--warn-only`); DB drift always blocking; flips fully strict when pending triage below clears |
| Showcase examples | `libs/i18n/scripts/validate_showcase_examples.py` | Pack edits that break the preview-repo `hello_world.py` showcase: each example must reverse-translate to canonical English via its pack (`create_translator_from_language_pack` + `reverse()`) and `ast.parse`; coverage gaps (example↔pack) reported as warnings (`--strict-coverage` promotes missing examples to failures) (CORE-1403) | pre-commit hook `validate-showcase-examples` (any pack-file change triggers a full 51-language sweep; skips with a notice when no preview checkout) | **Blocking** since 2026-08-10 (CORE-1779: the 11-item pending list cleared, 51/51) — see the showcase-gate detail below |
| Native review | Human process (intake design: CORE-1538, endorse/pass/flag) | Semantic quality, loanword judgment, everything mechanical gates cannot see | Manual ritual, async | Not a merge blocker (mechanical gates are the floor) |

Local commands (repo root unless noted):

```sh
cd libs/i18n && uv run python -m legesher_i18n.scripts.audit_packs   # Unicode/script audit
uv run python libs/i18n/scripts/audit_collisions.py                  # collision audit
uv run python libs/i18n/scripts/validate_language_pack_yaml.py <files>
cd libs/i18n && uv run python -m legesher_i18n.scripts.enforce_data_contract   # data contract (CORE-1453)
cd libs/i18n && uv run python -m legesher_i18n.scripts.validate_style_guides
uv run python libs/i18n/scripts/verify_pack_regen.py                 # before any regen
uv run python libs/i18n/scripts/translate/find_untranslated.py       # untranslated terms
uv run python libs/i18n/scripts/validate_showcase_examples.py        # showcase examples (needs preview-repo checkout)
uv run python libs/i18n/scripts/translate/screen_terms.py --gate     # term-screening gate (CORE-401)
```

## Showcase-examples gate detail

Strict since 2026-08-10 (CORE-1779). The 11 regressions pending at gate
introduction were cleared by example fixes in preview-repo (#25) plus
the CORE-1763 term replacements; `--warn-only` was removed from the script
outright so the gate cannot be silently re-softened.

Operational notes, because the examples live in a different repo:

- **Preview state matters.** The 51/51 green assumes a preview-repo
  checkout at (or after) its PR #25 merge. A stale checkout can fail your
  commit with regressions that no longer exist on preview `main` — `git -C
  ../preview-repo pull` first. `LEGESHER_PREVIEW_ROOT` overrides the
  sibling-checkout resolution.
- **Blast radius is the full sweep**, not just the language you edited:
  the hook validates all 51 examples (~1s), so a failure can name a
  language your change did not touch. That is the cross-language
  regression signal working as designed.
- **Recovery for a legitimate pack change** that breaks an example: land
  the example fix in preview-repo first (that repo has no gate on this
  path), pull it, then commit the pack change here. For a genuinely stuck
  moment, `SKIP=validate-showcase-examples git commit …` skips only this
  hook — never `--no-verify`.

## Untranslated-terms gate detail

Allowlist: `libs/i18n/scripts/translate/untranslated_allowlist.yml` —
`"<lang>:<term>"` entries asserting a deliberate loanword / policy keep
(best-effort NATIVE translation policy, CORE-1318). Seeded 2026-07-28 from a
full 51-pack sweep (7 raw findings across 6 languages):

- `cs:lambda`, `cy:lambda`, `ga:lambda`, `hr:lambda`, `lv:lambda` — Greek-letter
  name, identical in these Latin-script languages; every non-Latin pack carries
  a transliteration of the same word; cy/ga also have a community-source
  agreement row in `translations.db`.
- `cs:ascii` — acronym; no pack translates it semantically.

**Pending native-review triage** (kept OUT of the allowlist; the reason the
hook runs `--warn-only`):

- `da:stopiteration` (exceptions) — plausibly a correct Danish compound
  ("stop" + "iteration"; cf. `no: stoppiterasjon`, `sv: stoppiteration`) that
  coincidentally equals the English term, but `translations.db` carries only
  yaml-import/automated backfill provenance — no community or native
  confirmation. Needs a Danish reviewer to either confirm (→ allowlist it) or
  supply a translation.

**Flipping the gate strict:** when the pending list above is empty, remove
`--warn-only` from the `find-untranslated-terms` entry in
`.pre-commit-config.yaml`. From then on any new key == value entry not in the
allowlist fails the commit.

## Recorded dispositions

### UTF-8 / encoding validation — covered, no new gate

Every pack consumer opens pack YAML with an explicit `encoding="utf-8"`:
`legesher_i18n/pack_loader.py` (lines 474, 688 — the loader behind
`audit_packs`, which reports an undecodable file as a blocking `load-error`
finding), `scripts/validate_language_pack_yaml.py` (line 72 — the pre-commit
hook fails on it), and `scripts/translate/find_untranslated.py`. The generic
`check-yaml` pre-commit hook parses every pack file as well. A non-UTF-8 pack
file therefore cannot pass the existing gates; a separate encoding check would
be redundant. (Normalization stability — NFKC, a different axis from encoding —
is already the Unicode/script audit's job via `legesher_i18n/script_policy.py`.)

### Round-trip translate→back-translate check — DEFERRED

Not built. Rationale: native review owns semantic quality (endorse/pass/flag,
CORE-1538); a back-translation gate would add model-API cost and
nondeterminism without machine-checkable ground truth, and its failure mode
(flagging legitimate non-literal translations) duplicates the triage native
review already performs. Revisit after the 103-language generation, when the
volume of unreviewed packs may justify an automated semantic screen.
