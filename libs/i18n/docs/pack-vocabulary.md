# Pack vocabulary: symbols and variable conventions

Two pack sections, added in CORE-1396, holding knowledge that is
**vocabulary rather than rules**:

| Section | Holds | Shape | Consumer |
| --- | --- | --- | --- |
| `symbols` | What a Python symbol is **called** in this language | slug → prose name | teaching text, error messages |
| `variable_conventions` | The idiomatic short name for a variable **role** | slug → identifier | code suggestions, teaching text |

```yaml
symbols:
  colon: dos puntos
  underscore: guion bajo
  indentation: sangría
variable_conventions:
  loop_index: i
  throwaway: _
  accumulator: total
```

## Why the packs and not the style guides

The style guides already drew the line and pointed here — `style-guides/README.md`
has said "Guides are **rules, not vocabulary**… symbol names, and idiomatic
variable names live in the **language packs**" since they were written. The
pack side of that sentence did not exist until now.

The line holds up under pressure, which is the test that matters:

- A style guide rule is something you can **check code against**. "Identifiers
  join multi-word ideas with underscores" is a rule; a linter could enforce it.
- "`_` is called *guion bajo* in Spanish" is not checkable. It is a fact about
  the language, a lookup table with one row per symbol, and no rule derives it.

The same test separates the two new sections from each other. `symbols` is
never executed; `variable_conventions` is advice someone types into real code.
That difference drives every design decision below.

**CORE-1396 removed nothing from any style guide.** Nothing needed removing:
across all 61 files (52 language guides plus `python.yml` and the eight
`_*.yml` overlays) the complete key inventory is `language` / `extends` /
`version` / `status` / `supports.*` / `naming.*` / `script.*` / `formatting.*`
/ `rendering.*` — not one vocabulary-shaped key among them. The guides were
written vocabulary-free and stayed that way; this ticket built the side they
pointed at.

Separately, the list-merge semantics of the guide chain are unsettled
(CORE-1782 — lists are replaced wholesale, not concatenated), so moving
anything *out* of a guide is blocked regardless of whether it needed moving.

## Where the pieces live

```text
legesher_i18n/vocabulary_definitions.py   canonical inventory (code)
        │
        ├──> scripts/seed_vocabulary.py ──> vocabulary_entries      (DB)
        │                              └──> selected_vocabulary     (DB, `en`)
        │
        ├──> scripts/translate/generate_vocabulary.py ──> the other 50 locales
        │
        └──> scripts/translate/prompts/vocabulary_prompt.md   (the spec)

selected_vocabulary ──> scripts/translate/yaml_exporter.py ──> 3.10.yml
```

The **canonical inventory is code**, for the same reason the term inventory is:
which slugs exist, what glyph each names, and what it does are identical in all
51 languages. One place to change, nothing to keep in sync, and the generation
prompt is rendered from it so it can never ask for a slug the schema rejects.

Only the localized side — one string per (entry, language) — is data.

### Slugs, not glyphs, are the keys

`symbols` maps `colon`, not `:`. Three reasons:

1. Not every entry has a glyph. `indentation`, `newline` and `space` are named
   constantly by error messages and by teaching, and none is a printable
   character.
2. Glyph keys would put `:`, `#`, `'`, `"` and `@` on the left-hand side of a
   YAML mapping. Every one is a quoting hazard and `#` starts a comment.
3. The glyph is a constant. Shipping it in 51 packs is 51 copies of the same
   character; consumers read it from `vocabulary_definitions` and join on slug.

`variable_conventions` is keyed by **role** (`loop_index`), never by the
English spelling, so a language whose habit differs from English's has
somewhere to put it.

## Two validation regimes

| | `symbols` | `variable_conventions` |
| --- | --- | --- |
| Valid Python identifier | no — prose, with spaces | **yes** (PEP 3131) |
| Length cap | 60 code points | none (but short is the point) |
| Control / format characters | refused | refused |
| Trailing `*` (the soft-keyword marker) | refused | **refused** — the starred form is a term-section device, and refusing it first keeps the `SOFT_KEYWORDS` short-circuit unreachable |
| NFKC-stable | not required — prose is never parsed | **required**, with the term gates' SARA-AM allowance (NFC-stable values whose only NFKC delta is Thai U+0E33 pass; CPython folds it in identifiers) |
| CPython 3.13-only XID characters | irrelevant | **refused** |
| Python keyword | irrelevant | refused (`_` is fine) |
| Collides with a translated term surface | irrelevant | refused |
| Shadows a builtin | irrelevant | warning |
| Two entries sharing a value | warning | warning |

One function is the authority — `selection.vocabulary_value_error` — and it is
called by the pydantic layer, the strict validator, the database write
boundary, the exporter and the generation script, so no two layers can disagree
about what is publishable.

The 3.13-XID rule is the one that differs from a term translation, and the
reason is worth knowing: a pack translation carrying a 3.13-only character is
handled by the exporter's interpreter-floor tiering, which strips it for the
pre-3.13 files and restores it in a 3.13 overlay. A **recommended name** has no
overlay to be tiered into, so the constraint is absolute rather than managed.

The NFKC rule exists because Python folds identifiers at parse time: advice to
name your loop variable fullwidth `ｉ` would be advice about an identifier the
interpreter never creates — it binds `i`. The SARA-AM allowance mirrors the
term-side `check_normalization` posture exactly (CORE-1514): the same Thai
orthography is legal as a term surface and as a recommended name, or as
neither. One policy, both partitions.

## Why the vocabulary sections sit outside `TRANSLATION_SECTIONS`

Deliberate. Three of the generic safety checks would fight correct data:

- **Script consistency** would flag a language that keeps `i` for the loop
  counter. Many will, and rightly — `i` descends from mathematical index
  notation, not from the English word "index".
- **The round-trip bijection** (`data_contract.check_map_roundtrip`) demands
  that no two source terms share a surface. Nothing reverse-translates advice,
  so the bijection is not a property these sections have or need.
- **Keyword collision** uses `keyword.softkwlist`, which contains `_` — the
  canonical throwaway name this section exists to record.

So they get `check_symbols` and `check_variable_conventions` instead, which
apply the parts that do transfer and nothing that does not.

## All-or-nothing per section

A vocabulary section ships with **every** slug the inventory declares, or it
does not ship. A pack carrying 20 of 33 symbol names would render an English
fallback in the middle of localized teaching text with nothing to signal it,
and the consumer could not distinguish "this language has no word for it" from
"nobody has generated it yet".

Enforced twice: the exporter skips an incomplete section with a warning
(`yaml_exporter._build_vocabulary_sections`), and the validator flags a
hand-edited pack that is partial (`check_vocabulary_inventory`).

The partition is otherwise **optional**: a language with no vocabulary at all
exports exactly as it did before CORE-1396. That asymmetry with the term
inventory — where an unresolved slot is a hard stop — is what lets vocabulary
be filled language by language without any pack becoming unexportable
meanwhile.

## Version tiering: none

Symbol names and variable idiom do not change with the interpreter, so the
whole partition lives in `3.10.yml` and the later version files inherit it
through `extends`. The loader still merges the sections per key, so a future
overlay would inherit rather than silently drop — but there is nothing to
override today.

## Not in the Hugging Face dataset — a decision, not an oversight

`scripts/export_packs.py` enumerates what the `legesher/language-packs`
dataset publishes — `SECTIONS = ("keywords", "builtins", "exceptions",
"implicit_params")` — and the vocabulary sections are deliberately absent.
The exclusion is the conservative default and it stands: the partition is
new, every shipped pack carries it empty, and generated values enter at the
experimental tier ahead of native review. A public dataset should not gain a
column the review process has not yet touched just because the schema grew
one.

Changing this is a deliberate act with a forced checklist, not a drift:

1. Extend `SECTIONS` in `scripts/export_packs.py`.
2. Extend `CATEGORY_BLURBS` in the same edit — the card render indexes
   `CATEGORY_BLURBS[name]` for every section, and the parity test
   (`test_export_packs.py`, "CATEGORY_BLURBS and SECTIONS have drifted")
   pins the two sets equal, so a new section cannot reach the dataset
   undescribed.
3. Mind the shape: dataset rows are term-per-row with a `category` column,
   and `symbols` values are prose, not identifiers — the card's identifier
   framing ("a rendering has to be a legal identifier") would need the same
   two-regime split this document describes.

## Compatibility: vocabulary-carrying packs need a loader that knows them

The pack schema is `extra="forbid"`. That cuts both ways:

- An i18n version **from before this partition** hard-fails on a pack that
  carries `symbols` or `variable_conventions` — the unknown keys are a
  validation error, not ignored extras. A vocabulary-carrying pack is
  therefore not a drop-in for an older runtime.
- A pack **without** the sections loads identically on every version — both
  default to `{}` — which is why all 51 shipped packs are unaffected.

Ship vocabulary in a pack only once the consuming version floor includes the
schema that understands it; until then the sections live in the database and
the export simply does not emit them.

## Filling a language

```bash
cd libs/i18n

# 1. Inventory + English. Deterministic, idempotent, no API key.
#    English is SEEDED, never generated — the English name of a symbol IS
#    the inventory entry, so a model call would reproduce a constant.
uv run python scripts/seed_vocabulary.py --db legesher_i18n/db/translations.db

# 2. The other 50 locales. Needs ANTHROPIC_API_KEY.
uv run python scripts/translate/generate_vocabulary.py \
    --db legesher_i18n/db/translations.db --all --skip-complete

# 3. Regenerate the packs from the DB (never hand-edit a pack file).
uv run python scripts/export_packs.py

# 4. The gates.
uv run python scripts/verify_pack_regen.py --db legesher_i18n/db/translations.db
uv run python scripts/audit_collisions.py            # expect 51/51
uv run pre-commit run --files language-packs/python/*/*/packs/*.yml

# 5. The durable-home push (libs/i18n/CLAUDE.md). The database is an
#    untracked working copy; an unpushed generation exists on one
#    workstation only.
```

`--dry-run` on the generation script renders and prints every prompt without
an API call, which is the cheap way to review the framing before a run.

## Review status

Generated values enter at the **experimental** tier — where all 51 packs
already sit, and where model generation is the norm. Native review rides the
standing review queue; it is not a precondition for the values existing.

The generation script stores the model's `notes` as the rationale on every
candidate row. That field — where a model records the answers it was least sure
of — is a better triage signal for a reviewer than a confidence score, and is
the thing to read first.

## The prompt is linguist-framed, and here it matters

House convention is "you are a linguist", not "you are a translator". Both
sections have an answer that is linguistically correct and useless:

- A translator calques "hash sign". A linguist reports that speakers call `#` a
  grid, a lattice, or the musical sharp — and that `_` is *guion bajo* ("low
  dash") in Spanish, not a loan of "underscore".
- A translator renames all fifteen variable roles into native abbreviations,
  describing no real codebase. A linguist reports that `i` is what programmers
  actually type in most languages, and flags the roles where the language
  genuinely diverges.

The full specification is `scripts/translate/prompts/vocabulary_prompt.md`.
