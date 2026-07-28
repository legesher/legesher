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
| Style guides | `libs/i18n/legesher_i18n/scripts/validate_style_guides.py` | Style-guide schema violations; drift between guides' derived flags and `legesher_i18n/languages.json` | pre-commit hook `validate-style-guides` | Blocking |
| Regen integrity | `libs/i18n/scripts/verify_pack_regen.py` | Regen-vs-shipped diff classes (`value_changed`, `key_added`, `key_removed`, `unknown_section`, `not_regenerated`, ...) — proves DB→YAML regeneration is safe (CORE-1400) | Manual ritual; wired into nothing — run before any pack regeneration | Blocking by convention |
| Untranslated terms | `libs/i18n/scripts/translate/find_untranslated.py` | Pack entries whose translation equals the source term (key == value), net of the intentional-loanword allowlist | pre-commit hook `find-untranslated-terms` (changed pack files) | **Report-only for now** (`--warn-only`); flips strict when pending triage below clears |
| Native review | Human process (intake design: CORE-1538, endorse/pass/flag) | Semantic quality, loanword judgment, everything mechanical gates cannot see | Manual ritual, async | Not a merge blocker (mechanical gates are the floor) |

Local commands (repo root unless noted):

```sh
cd libs/i18n && uv run python -m legesher_i18n.scripts.audit_packs   # Unicode/script audit
uv run python libs/i18n/scripts/audit_collisions.py                  # collision audit
uv run python libs/i18n/scripts/validate_language_pack_yaml.py <files>
cd libs/i18n && uv run python -m legesher_i18n.scripts.validate_style_guides
uv run python libs/i18n/scripts/verify_pack_regen.py                 # before any regen
uv run python libs/i18n/scripts/translate/find_untranslated.py       # untranslated terms
```

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
