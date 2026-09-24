<!-- GENERATED FILE: do not edit by hand.
     Structure:    libs/i18n/legesher_i18n/db/schema_v2.sql
     Descriptions: libs/i18n/legesher_i18n/db/schema_v2.descriptions.yml
     Regenerate:   make generate-schema-reference -->

# Translations Schema v2 Reference

> **Generated from the schema. Do not edit this page.** Tables, columns, types,
> keys, indexes, triggers and views are parsed from
> [`schema_v2.sql`](../legesher_i18n/db/schema_v2.sql); every description comes
> from [`schema_v2.descriptions.yml`](../legesher_i18n/db/schema_v2.descriptions.yml).
> Edit those, then run `make generate-schema-reference`. The generator refuses when the two
> disagree (an undescribed table or column, or a description of something the
> SQL no longer has), and `make check-generated` fails when this page is stale.

## Scope

This page covers **schema v2 only**: the 31 tables, 21 views, 54 triggers and 27 indexes in `schema_v2.sql`. Schema v1 (`schema.py`: `terms`, `languages`, `translations`, `selected_translations`, `vocabulary_entries`, `vocabulary_translations`, `selected_vocabulary`) is a separate database and is not described here.

Requires SQLite 3.31 or later (the schema uses STORED generated columns).

Two schemas are live, and they answer different questions. The language-pack
pipeline reads the v1 database (`schema.py`): packs are exported from its
`selected_translations`. The corpus and canon datasets are exported from the
v2 database described here, and community review lands here too (options,
endorsements, screenings, the canon projection). The pack build has not moved
onto v2, so neither schema is stale: query the one that belongs to your
pipeline. The quickest tell is that v1 has `selected_translations` and v2 has
`options`. The messages partition ([`message_templates`](#message_templates),
[`message_translations`](#message_translations), [`message_endorsements`](#message_endorsements)) is defined here but can
also be activated into a v1 database by
`scripts/activate_messages_partition.py`.

A hand-written concepts page on the layer boundary, and on which database is
authoritative for what, is planned as separate work. This page links to it
once it exists.

## Overview

Legesher translations schema v2: concept-centric, with an endorsement corpus
(CORE-1501). CORE-1501 designed it to supersede the v1 schema in `schema.py`;
see Scope for why both are still live.

The full design / migration / HF-dataset rationale lives in the CORE-1501
design docs, which are not part of this repository.

Three layers, and the boundary between them is load-bearing:

- **REFERENCE**: [`programming_languages`](#programming_languages), [`locales`](#locales), [`concepts`](#concepts),
  [`terms`](#terms), [`concept_briefs`](#concept_briefs).
  Maintainer-curated. Small. Ships in the monorepo.
- **CORPUS**: [`options`](#options), [`option_provenance`](#option_provenance), [`endorsements`](#endorsements),
  [`option_flags`](#option_flags), [`option_validations`](#option_validations), [`contributors`](#contributors).
  Community-writable, APPEND-ONLY, published to Hugging Face.
  Every rendering anyone ever offered, and every person who
  endorsed it. Counts are DERIVED (COUNT(*)), never stored.
- **CANON**: [`canon_selections`](#canon_selections).
  The maintainer decision. Lives in the monorepo as PR-reviewable
  text (`libs/i18n/canon/<locale>.toml`); this table is a LOADED
  PROJECTION of those files, never a write target. Enforced by
  source_file NOT NULL + a CI drift test. Never published as a
  writable dataset.

The sections below follow the order of `schema_v2.sql`, whose banners do
not map one-to-one onto the three layers: the CORPUS banner also holds the
reviewer ladder, the private identity and build tables and the screening
events, and REVIEW INTAKE mixes layers (its own section says which).

## Connection requirements

`PRAGMA foreign_keys = ON`

NOT PERSISTED. `foreign_keys` is a PER-CONNECTION setting that SQLite
defaults to OFF; this line only covers the connection that runs the DDL. A
fresh sqlite3.connect() to the resulting FILE reports foreign_keys = 0 and
every FK below is silently inert. Consumers must open the database through
schema_v2.connect() (or issue the pragma themselves), as asserted by
tests/test_schema_v2.py::test_foreign_keys_must_be_enabled_per_connection.

## Contents

Sections follow the banners in `schema_v2.sql`. Triggers are documented with
the table they guard, wherever the SQL declares them.

| Section | Tables | Views | Triggers declared |
|---|---|---|---|
| [Reference](#reference) | [`programming_languages`](#programming_languages), [`locales`](#locales), [`concepts`](#concepts), [`concept_slug_aliases`](#concept_slug_aliases), [`concept_briefs`](#concept_briefs), [`concept_relations`](#concept_relations), [`terms`](#terms) | none | 0 |
| [Corpus](#corpus) | [`review_rungs`](#review_rungs), [`contributors`](#contributors), [`contributor_identities`](#contributor_identities), [`build_meta`](#build_meta), [`options`](#options), [`option_provenance`](#option_provenance), [`endorsements`](#endorsements), [`option_flags`](#option_flags), [`option_validations`](#option_validations), [`option_screenings`](#option_screenings) | [`option_screening_status`](#option_screening_status), [`option_withheld`](#option_withheld) | 2 |
| [Canon](#canon) | [`canon_selections`](#canon_selections) | none | 0 |
| [Triggers](#triggers) | none | none | 19 |
| [Views](#views) | none | [`locale_fallback`](#locale_fallback), [`endorsement_counts`](#endorsement_counts), [`option_standings`](#option_standings), [`canon_resolution`](#canon_resolution), [`term_resolution`](#term_resolution), [`pack_export`](#pack_export), [`canon_coverage`](#canon_coverage), [`pack_export_conflicts`](#pack_export_conflicts), [`canon_collisions`](#canon_collisions), [`review_queue`](#review_queue), [`locale_progress`](#locale_progress), [`new_pl_reuse`](#new_pl_reuse) | 0 |
| [Deferred](#deferred) | [`message_templates`](#message_templates), [`message_translations`](#message_translations) | none | 0 |
| [Review Intake](#review-intake) | [`import_sources`](#import_sources), [`review_sessions`](#review_sessions), [`session_options`](#session_options), [`session_endorsements`](#session_endorsements), [`session_rankings`](#session_rankings), [`option_annotations`](#option_annotations), [`option_expansions`](#option_expansions), [`concept_commentary`](#concept_commentary), [`commentary_moderation`](#commentary_moderation), [`style_ratifications`](#style_ratifications), [`message_endorsements`](#message_endorsements) | [`latest_rankings`](#latest_rankings), [`option_promotion_status`](#option_promotion_status), [`second_endorsement_queue`](#second_endorsement_queue), [`quarantine_queue`](#quarantine_queue), [`pack_promotion_status`](#pack_promotion_status), [`terminology_export`](#terminology_export), [`transliteration_preference`](#transliteration_preference) | 33 |

## Reference

Maintainer-curated tables: the programming languages, the locales, the
concepts and the per-language terms that spell them.

### `programming_languages`

One row per programming language Legesher knows about, keyed by a short
lowercase code. [`terms`](#terms) hang off it: a concept is spelled once per
programming language.

**Columns**

- **`code`** · `TEXT` · primary key

  The key: 'python', 'javascript', 'rust'.

- **`name`** · `TEXT` · not null

  Display name of the programming language.

- **`status`** · `TEXT` · not null · default `'planned'`

  How far Legesher's support for this programming language has come.
  `migrate_to_v2.py` seeds python as `shipping` and javascript as
  `in_progress`.

  Allowed values: `shipping`, `in_progress`, `planned`.

- **`spec_url`** · `TEXT`

  Link to the language's own specification, when recorded.

- **`created_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the row was inserted.

- **`updated_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the row was last changed. The default fills it on insert; no
  trigger maintains it, so writers set it themselves.

### `locales`

One table, keyed by BCP 47 (RFC 5646). There is no separate `languages`
table: a language tag IS a well-formed locale tag ('ar' and 'ar-EG' occupy
the same column), so a two-table language/locale split would only reintroduce
the redundant key v1 already suffers from. See CORE-1500.

**THE TAG IS INSIDE THE FROZEN OPTION HASH, SO ITS CASING IS LOAD-BEARING.**
BCP 47 is case-INSENSITIVE ('ar-EG' and 'ar-eg' are the same locale) but
SQLite TEXT keys and SHA-256 are case-SENSITIVE:

```text
option_uid(..., 'ar-EG', ...)  ->  opt_9bb3fb19da327424bf3b91f3
option_uid(..., 'ar-eg', ...)  ->  opt_31e241ca1f4f029c8e52e4b8
```

One wrongly-cased row, inserted once by one script, permanently FORKS every
option in that locale into two disjoint corpora. Before this CHECK existed,
'ar-eg', 'AR', 'en_US', 'not a tag!', 'zzzzz-Qaaa-QQ' and a 40-character
string were all accepted.

The CHECK below pins RFC 5646 canonical form (RFC 5646 §2.1.1: lowercase
language, Titlecase script, UPPERCASE region) for the subtag shapes we
actually use. It is deliberately a WHITELIST: extensions, private-use
(x-...), grandfathered tags, and variant subtags (rozaj, 1996) are rejected
until someone extends this list on purpose, because every tag admitted here
becomes a permanent key.

This CHECK is the last-resort DB-level floor, not the real validator. A
GLOB cannot know that 'qq-Zzzz-ZZ' is well-formed but unregistered, so the
write path is expected to go through `legesher_i18n.bcp47` (a full RFC
5646 parser with IANA subtag-registry lookup) and use is_canonical() /
is_valid() before inserting a tag here.

**Columns**

- **`tag`** · `TEXT` · primary key

  The BCP 47 tag and the key: 'ar', 'ar-EG', 'zh-Hans', 'din'.

- **`parent_tag`** · `TEXT` · references [`locales`](#locales)`(tag)` on delete restrict

  `parent_tag` is the RFC 4647 "Lookup" fallback edge: ar-EG -> ar -> (root).
  Self-referential, so sr-Latn-RS -> sr-Latn -> sr works without a schema
  change. Root locales have parent_tag NULL.

- **`language_subtag`** · `TEXT` · not null

  ISO 639-1 where it exists, else 639-3 ('din').

- **`script_subtag`** · `TEXT`

  ISO 15924, only when not suppress-script.

- **`region_subtag`** · `TEXT`

  ISO 3166-1 alpha-2.

- **`name`** · `TEXT` · not null

  English name of the locale. Carried over from v1 `languages.name`.

- **`native_name`** · `TEXT` · not null

  The locale's name in its own language. Carried over from v1
  `languages.native_name`.

- **`direction`** · `TEXT` · not null · default `'ltr'`

  Writing direction of the locale's script.

  Allowed values: `ltr`, `rtl`.

- **`numeral_system`** · `TEXT`

  The locale's native digit system, as recorded in v1
  `languages.numeral_system` (the JS client pack maps it to a CLDR
  numbering-system id). NULL when not recorded.

- **`has_case_distinction`** · `INTEGER` · not null · default `1`

  1 when the locale's script distinguishes upper and lower case. Script
  metadata the prompt builder consumes; carried over from v1.

  Allowed values: `0`, `1`.

- **`terminology_policy`** · `TEXT`

  Per-locale terminology policy the prompt builder injects (purist vs
  loanword-tolerant, register/diglossia). Doc 06 asked for this; v1 had
  nowhere to put it.

- **`iso639_3`** · `TEXT`

  Metadata only, never a key.

- **`status`** · `TEXT` · not null · default `'experimental'`

  Maturity of the locale, carried over from v1 `languages.status`.

  Allowed values: `experimental`, `in_review`, `official`.

- **`in_registry`** · `INTEGER` · not null · default `0`

  1 when the locale is published in the language registry (v1
  `languages.in_registry`, CORE-611). [`review_queue`](#review_queue) only lists these
  locales.

  Allowed values: `0`, `1`.

- **`created_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the row was inserted.

- **`updated_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the row was last changed. The default fills it on insert; no
  trigger maintains it, so writers set it themselves.

**Constraints**

```sql
CHECK (
    tag GLOB '[a-z][a-z]'
 OR tag GLOB '[a-z][a-z][a-z]'
 OR tag GLOB '[a-z][a-z]-[A-Z][a-z][a-z][a-z]'
 OR tag GLOB '[a-z][a-z][a-z]-[A-Z][a-z][a-z][a-z]'
 OR tag GLOB '[a-z][a-z]-[A-Z][A-Z]'
 OR tag GLOB '[a-z][a-z][a-z]-[A-Z][A-Z]'
 OR tag GLOB '[a-z][a-z]-[0-9][0-9][0-9]'
 OR tag GLOB '[a-z][a-z][a-z]-[0-9][0-9][0-9]'
 OR tag GLOB '[a-z][a-z]-[A-Z][a-z][a-z][a-z]-[A-Z][A-Z]'
 OR tag GLOB '[a-z][a-z][a-z]-[A-Z][a-z][a-z][a-z]-[A-Z][A-Z]'
 OR tag GLOB '[a-z][a-z]-[A-Z][a-z][a-z][a-z]-[0-9][0-9][0-9]'
 OR tag GLOB '[a-z][a-z][a-z]-[A-Z][a-z][a-z][a-z]-[0-9][0-9][0-9]'
)
CHECK (language_subtag GLOB '[a-z][a-z]' OR language_subtag GLOB '[a-z][a-z][a-z]')
CHECK (script_subtag IS NULL OR script_subtag GLOB '[A-Z][a-z][a-z][a-z]')
CHECK (region_subtag IS NULL
       OR region_subtag GLOB '[A-Z][A-Z]'
       OR region_subtag GLOB '[0-9][0-9][0-9]')
CHECK (
    tag = language_subtag
          || CASE WHEN script_subtag IS NULL THEN '' ELSE '-' || script_subtag END
          || CASE WHEN region_subtag IS NULL THEN '' ELSE '-' || region_subtag END
)
CHECK (parent_tag IS NULL OR parent_tag <> tag)
```

Canonical BCP 47 (RFC 5646) syntax AND casing. GLOB is case-sensitive;
LIKE is not, so GLOB is the only usable operator here.

```text
lang        2-3 lowercase alpha        ar, din
-Script     4 alpha, Titlecase         zh-Hans
-REGION     2 UPPERCASE alpha          ar-EG
            or 3 digits (UN M.49)      es-419
```

The component columns must agree with the tag's canonical casing too;
they are what a rebuild would re-join the tag from.

Exact recomposition, not just a prefix match: the component columns are
a DECOMPOSITION of the tag, and a prefix check still admitted
('ar-EG', ..., region_subtag='SA'): a row whose components lie to every
join that uses them. If the columns cannot re-join into the tag, the row
is wrong.

**Indexes**

- <a id="idx_locales_parent"></a>`idx_locales_parent`: on `parent_tag`

### `concepts`

The semantic core. `slug` is the PUBLIC, FROZEN key: it is what the Hugging
Face corpus exports and what community endorsements are attached to. The
INTEGER id is internal and must never leave this database.

**Columns**

- **`id`** · `INTEGER` · primary key, autoincrement

  Internal integer key. Never exported: rebuilds renumber it, so
  everything published keys by `slug`.

- **`slug`** · `TEXT` · not null · unique

  The public, frozen key: 'function-definition', 'yield-generator'.

- **`definition_en`** · `TEXT` · not null

  The identity: what the official docs say it does.

- **`definition_source`** · `TEXT`

  Citation / URL for definition_en.

- **`category`** · `TEXT` · not null

  PL-NEUTRAL: control_flow, declaration,
  error_handling, value_literal, type_system,
  concurrency, module_system, builtin_operation,
  exception_type, accessor, memory

  MIGRATION CAVEAT: migrate_to_v2.py seeds this from v1 `terms.category`,
  which is PL-LOCAL vocabulary (keyword, builtin_func, ...). Recategorizing
  to the PL-neutral vocabulary below is a follow-up curation pass; until it
  runs, treat migrated values as provisional.

- **`pattern_class`** · `TEXT`

  action_keyword, state_keyword, noun_type, ...

- **`notes`** · `TEXT`

  Free-text maintainer notes on the concept.

- **`created_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the row was inserted.

- **`updated_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the row was last changed. The default fills it on insert; no
  trigger maintains it, so writers set it themselves.

**Constraints**

```sql
CHECK (slug = LOWER(slug) AND slug NOT LIKE '% %' AND instr(slug, char(31)) = 0)
```

The slug is a hashed field of options.uid, so a U+001F in it would let two
distinct tuples forge one uid (see options.surface_form).

### `concept_slug_aliases`

A published slug can never be deleted or silently repointed; renames go
through here so already-published option/endorsement rows stay resolvable.

**Columns**

- **`alias`** · `TEXT` · primary key

  The retired slug, still resolvable.

- **`concept_id`** · `INTEGER` · not null · references [`concepts`](#concepts)`(id)` on delete cascade

  The concept the retired slug now resolves to.

- **`retired_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the slug was retired.

- **`reason`** · `TEXT`

  Why the concept was renamed.

### `concept_briefs`

Where each concept's context brief lives in the repository, per tier.
`migrate_to_v2.py` records a tier-1 brief only when the Python brief file
exists, so no row points at a missing file.

**Columns**

- **`concept_id`** · `INTEGER` · part of the primary key · not null · references [`concepts`](#concepts)`(id)` on delete cascade

  The concept the brief explains.

- **`tier`** · `INTEGER` · part of the primary key · not null · default `1`

  Brief depth, 1 or 2. `migrate_to_v2.py` records tier 1 only.

  Allowed values: `1`, `2`.

- **`path`** · `TEXT` · not null

  Repo-relative markdown path.

- **`updated_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the row was last changed. The default fills it on insert; no
  trigger maintains it, so writers set it themselves.

**Constraints**

```sql
PRIMARY KEY (concept_id, tier)
```

### `concept_relations`

Makes the briefs' cross-reference rules queryable ("return/yield/await must
share verb form").

**Columns**

- **`concept_id`** · `INTEGER` · part of the primary key · not null · references [`concepts`](#concepts)`(id)` on delete cascade

  One side of the relation.

- **`related_concept`** · `INTEGER` · part of the primary key · not null · references [`concepts`](#concepts)`(id)` on delete cascade

  The other side. A concept cannot relate to itself.

- **`relation`** · `TEXT` · part of the primary key · not null

  What the two concepts owe each other when rendered.

  Allowed values:

  - `consistency_group`: Render with the same word form.
  - `contrast`: Must stay distinguishable.
  - `supersedes`: e.g. `except*` vs `except`.

- **`note`** · `TEXT`

  Free-text explanation of the relation.

**Constraints**

```sql
PRIMARY KEY (concept_id, related_concept, relation)
CHECK (concept_id <> related_concept)
```

### `terms`

A concept's surface form in ONE programming language.

UNIQUE includes concept_id so one spelling may map to two concepts in the
same PL (Python `type`: builtin AND 3.12 soft keyword). That is the whole
point. But it creates an export hazard: a pack is a map keyed by the English
token, so two concepts sharing (pl, name) cannot emit two different words.
`export_role` resolves it: exactly one primary per (pl, name); secondaries
are curation/documentation rows and are excluded from pack_export. Divergent
renderings across the two are surfaced by pack_export_conflicts.

**Columns**

- **`id`** · `INTEGER` · primary key, autoincrement

  Internal integer key.

- **`concept_id`** · `INTEGER` · not null · references [`concepts`](#concepts)`(id)` on delete restrict

  The concept this term spells.

- **`programming_language`** · `TEXT` · not null · references [`programming_languages`](#programming_languages)`(code)` on delete restrict

  The programming language the spelling belongs to.

- **`name`** · `TEXT` · not null

  The spelling: 'def', 'fn', 'func'.

- **`category`** · `TEXT` · not null

  PL-LOCAL: keyword, soft_keyword, builtin_func,
  builtin_type, exception, contextual_keyword, ...

- **`subcategory`** · `TEXT`

  Finer PL-local grouping within `category`.

- **`version_added`** · `TEXT`

  In this PL's own version scheme.

- **`version_removed`** · `TEXT`

  The version of this PL that removed the term, in its own version
  scheme. NULL while the term is current.

- **`usage_note`** · `TEXT`

  How THIS PL's usage varies from definition_en.

- **`doc_url`** · `TEXT`

  Link to the programming language's documentation for the term.

- **`export_role`** · `TEXT` · not null · default `'primary'`

  Which of the terms sharing one (pl, name) the pack exports. The
  partial unique index `idx_terms_one_primary` allows exactly one
  primary per (pl, name).

  Allowed values:

  - `primary`: Exported into packs. The default.
  - `secondary`: Curation and documentation only; excluded from [`pack_export`](#pack_export).

- **`created_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the row was inserted.

- **`updated_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the row was last changed. The default fills it on insert; no
  trigger maintains it, so writers set it themselves.

**Constraints**

```sql
UNIQUE (programming_language, name, concept_id)
```

**Indexes**

- <a id="idx_terms_one_primary"></a>`idx_terms_one_primary`: unique on `programming_language`, `name` where `export_role = 'primary'`

- <a id="idx_terms_concept"></a>`idx_terms_concept`: on `concept_id`

- <a id="idx_terms_pl"></a>`idx_terms_pl`: on `programming_language`, `category`

- <a id="idx_terms_name"></a>`idx_terms_name`: on `name`

## Corpus

CORPUS: community-writable, append-only, published to Hugging Face.

### `review_rungs`

The reviewer ladder (CORE-1466). Weight is POLICY, versioned and editable;
it is deliberately NOT stored on the endorsement row, so re-weighting the
ladder never rewrites community data.

**Columns**

- **`rung`** · `TEXT` · primary key

  The rung's name, used as the key everywhere a rung is recorded.

- **`rank`** · `INTEGER` · not null · unique

  The rung's position on the ladder, lowest first. Unique.

- **`weight`** · `REAL` · not null · check `weight >= 0`

  How much one endorsement at this rung counts in
  `endorsement_counts.weighted_endorsement`. Never negative.

- **`counts_as_native`** · `INTEGER` · not null · default `0`

  `counts_as_native` is what `endorsement_counts.native_verified_or_above`
  means. It lives here, on the policy table, rather than as a hardcoded
  `rank >= 3` in the view: the ladder is explicitly designed to be re-tuned
  (CORE-1466), and a magic number in a view would silently re-define the
  headline number the moment a rung is inserted in the middle.

  Allowed values: `0`, `1`.

- **`policy_version`** · `TEXT` · not null

  Which version of the ladder policy this row belongs to.

- **`description`** · `TEXT`

  What reaching the rung means.

**Seed rows**

PROPOSED ladder and weights, pending maintainer sign-off (see design.md Q4).

| `rung` | `rank` | `weight` | `counts_as_native` | `policy_version` | `description` |
|---|---|---|---|---|---|
| anonymous | 0 | 0.0 | 0 | v0-draft | Unauthenticated signal. Recorded, weighted zero; brigading evidence. |
| contributor | 1 | 1.0 | 0 | v0-draft | Authenticated account, no verified native claim. |
| native_claimed | 2 | 2.0 | 0 | v0-draft | Self-declared native speaker of the locale. |
| native_verified | 3 | 4.0 | 1 | v0-draft | Native status vouched by a maintainer or ambassador. |
| certified | 4 | 8.0 | 1 | v0-draft | Certified Contributor (CORE-1446); paid-reviewer eligible. |
| maintainer | 5 | 8.0 | 1 | v0-draft | Legesher maintainer. Same weight as certified by design. |

### `contributors`

An opaque, stable, pseudonymous handle. This is the ONLY identity column the
corpus exports. Real-world identity lives in contributor_identities, which is
never published. Withdrawal (CORE-1780) REDACTS AND TOMBSTONES that row --
every identifying column NULL, `withdrawn_at` set, the row itself retained --
and keeps the contributor + their endorsements: counts survive, PII does not.
Do NOT delete the identity row: the tombstone is what stops a replayed review
bundle re-minting the erased identity. See contributor_identities.withdrawn_at.

THE CHECK IS A SHAPE, NOT A PREFIX. `LIKE 'c\_%'` was not a constraint at all:
`c_<v1 label>` satisfies it (labels that embed real first names), and that
is precisely what a migration
doing `'c_' || created_by` produces. The id must be `c_` + exactly 16
lowercase hex characters: a token that cannot carry a name (see
schema_v2.contributor_id, which mints it from a SALTED digest of the private
natural key).

**>>> THE SALT IS IMMUTABLE FOREVER, AND MUST BE ESCROWED. <<<**

It must be SECRET (the private source keys are GitHub usernames, public and
enumerable, so a public salt is reversible by dictionary attack). But secrecy
is the lesser half: the salt is an ingredient of THIS PRIMARY KEY. Lose it,
rotate it, or regenerate it after the first HF publish and every id below
changes, every endorsement re-keys, the corpus FORKS, and every contributor's
history is orphaned, with no way back, because a returning contributor's
matching id can never be minted again.

Generate once (secrets.token_hex(32)), store in a secret manager, back it up,
NEVER rotate. `migrate_to_v2.py --publish` refuses a public or short salt.

**Columns**

- **`id`** · `TEXT` · primary key

  'c_' + 16 hex. Never a name, email, or handle.

- **`current_rung`** · `TEXT` · not null · default `'contributor'` · references [`review_rungs`](#review_rungs)`(rung)`

  The contributor's rung today. The promotion path, so it stays mutable;
  each endorsement snapshots the rung it was made at.

- **`joined_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the contributor was first recorded.

**Constraints**

```sql
CHECK (id GLOB 'c_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
            || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]')
```

**Triggers**

<a id="trg_contributor_id_is_immutable"></a>

- **`trg_contributor_id_is_immutable`** · BEFORE UPDATE OF id

  The opaque handle is stamped into every published endorsement uid; repointing
  it re-keys the corpus. (current_rung, the promotion path, stays mutable.)

  Refuses with: `contributors.id is the published key: it cannot be repointed`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_contributor_id_is_immutable
  BEFORE UPDATE OF id ON contributors
  BEGIN
      SELECT RAISE(ABORT, 'contributors.id is the published key: it cannot be repointed');
  END
  ```

  </details>

### `contributor_identities`

PRIVATE. Never exported, never pushed to Hugging Face. The export script
must fail loudly if this table appears in a dataset config (CORE-1502).

`source_key` is the pre-image of contributors.id: the token is minted from it,
so it is the ONLY way back from an opaque id to a person, which is why this
table is the hard boundary of the publish surface.

IT IS A GITHUB USERNAME, not the raw v1 `created_by` label. A first name is a
bad key: it is ambiguous, it collides, and it changes. And v1's labels show
how misleading they can be: a `<label>_old` twin LOOKS like the same person
one pack generation earlier, but holds the words that review REJECTED (see
SUPERSEDED_BY_REVIEW in migrate_to_v2.py; those rows mint no contributor and
no endorsement at all). Usernames are stable, unique and verifiable. (The
PUBLISHED id is unaffected: it stays the opaque digest; only the private key
improves.)
The v1 label -> username map is CONTRIBUTOR_IDENTITY_MAP, loaded by
migrate_to_v2.py from the private data home (CORE-1794) and
explicit by design: a heuristic that strips `_old`/`_review` would silently
mis-merge a future contributor, and would have merged a reviewer with the
words she threw out.

A source_key prefixed `unresolved:` means a label that names a person but not
WHICH person, or not ONE person. It mints no endorsements, and
`migrate_to_v2.py --publish` refuses to build a corpus while one exists.
(One v1 label sat in this state, one label possibly naming two people,
until a maintainer resolved it to a single person on 2026-07-14. The
resolution and its reasoning live in the data home's identity map.)

**Columns**

- **`contributor_id`** · `TEXT` · primary key · references [`contributors`](#contributors)`(id)` on delete cascade

  The opaque [`contributors`](#contributors) id this identity sits behind. One identity
  per contributor.

- **`source_key`** · `TEXT` · unique

  GitHub username. NEVER published. Unique.

- **`display_name`** · `TEXT`

  The name to credit, when the contributor chose credit by name. Cleared
  on withdrawal.

- **`github_handle`** · `TEXT`

  The handle to credit, when the contributor chose credit by handle.
  Cleared on withdrawal.

- **`contact`** · `TEXT`

  A private contact detail. Cleared on withdrawal.

- **`consent_public_credit`** · `INTEGER` · not null · default `0`

  The derived boolean: 1 when `credit_preference` is not 'anonymous'.
  Kept alongside the three-way choice; the importer writes both.

  Allowed values: `0`, `1`.

- **`consent_version`** · `TEXT`

  Which version of CONTRIBUTOR_PRIVACY.md this person agreed to. Versioned
  because consent describes what someone accepted AT THE TIME; a single
  boolean cannot survive the notice being rewritten.

  `oss-pre-notice` is a real value and is NOT a signature: it marks people
  who contributed before the notice existed, through public pull requests
  under their own accounts, credited by handle in the pack CHANGELOGs.
  NULL would claim nobody ever agreed to anything; '1.0' would claim they
  accepted a document that did not exist. It grants nothing: they keep
  credit_preference = 'anonymous' and withdrawal applies identically.
  Notice 1.0 is FORWARD-LOOKING: it governs contributions made after it was
  published. See PRE_NOTICE_CONSENT in scripts/migrate_to_v2.py.

- **`consent_at`** · `TEXT`

  When the consent in `consent_version` was given. Cleared on withdrawal.

- **`credit_preference`** · `TEXT` · not null · default `'anonymous'`

  Decided 2026-07-21 (CORE-1538; closes the CORE-1501 Q1 thread): how
  public credit reads is the contributor's explicit three-way choice.
  consent_public_credit stays as the derived boolean
  (credit_preference <> 'anonymous'); the importer writes both.

  Allowed values: `anonymous`, `handle`, `name`.

- **`email`** · `TEXT` · check: see constraints

  Contact email, captured at every submission (decided 2026-07-21).
  PRIVATE like everything in this table; NEVER in a bundle, because bundles are
  public PR artifacts, so the address travels a private channel and lands
  only here. The importer stores it trimmed with the domain lowercased and
  runs the real syntax check; this CHECK is the DB floor (one @, dotted
  domain, no ASCII whitespace (space, tab, CR, LF); LIKE wildcards match
  control characters, so the tab/newline family needs its own guards).
  Deliverability verification is a magic-link flow recorded in
  email_verified_at; an unverified email never blocks.

- **`email_verified_at`** · `TEXT`

  When the magic-link check confirmed the address. NULL until then.

- **`withdrawn_at`** · `TEXT`

  WITHDRAWAL (CORE-1780, decided 2026-08-10). A withdrawal REDACTS and
  TOMBSTONES: source_key, display_name, github_handle, contact, email and
  email_verified_at all go NULL; credit_preference returns to 'anonymous'
  and consent_public_credit to 0 (it is NOT NULL, so it cannot be nulled);
  consent_version and consent_at are cleared, because the consent they
  record has been revoked. Then this timestamp is set. The row stays.

  It is deliberately NOT a soft delete. A row that keeps source_key and
  merely flags it has erased nothing: the mapping back to the person is
  still here, annotated. And it is deliberately not a DELETE either: the
  empty row is what lets a later import tell "this person withdrew" apart
  from "we have never met this person", so a replay of an older review
  bundle, which still carries their username, cannot silently mint the
  identity again and undo the erasure. See
  `libs/i18n/docs/contributor-withdrawal-runbook.md` for the importer rule
  and `CONTRIBUTOR_PRIVACY.md` (repo root) for what the contributor was
  promised.

  `contributors` and `endorsements` are untouched: counts survive, PII does
  not. Nothing PUBLISHED changes: no export has ever carried this table.

**Constraints**

```sql
CHECK (credit_preference <> 'name'   OR display_name  IS NOT NULL)
CHECK (credit_preference <> 'handle' OR github_handle IS NOT NULL)
-- email
CHECK (email IS NULL
       OR (email = TRIM(email)
           AND email NOT LIKE '% %'
           AND email NOT GLOB '*' || char(9)  || '*'
           AND email NOT GLOB '*' || char(10) || '*'
           AND email NOT GLOB '*' || char(13) || '*'
           AND email LIKE '%_@_%.%_'
           AND email NOT LIKE '%@%@%'))
```

A credit choice must have something to credit.

### `build_meta`

PRIVATE. Never exported (same boundary as contributor_identities).

Facts about the BUILD, not the corpus: which schema built this file, when,
and, load-bearing, `salt_fingerprint`: sha256 of the contributor salt,
truncated. Nothing else in a built database records WHICH salt minted its
contributor ids, so without this row the push script cannot tell an artifact
minted with the escrowed salt from one minted with a dev or fat-fingered
salt, a mistake that is unrecoverable one publish later. The fingerprint
verifies the salt without revealing it (the publish gate already requires
the salt itself to be long and high-entropy).

**Columns**

- **`key`** · `TEXT` · primary key

  The fact's name. `migrate_to_v2.py` writes `salt_fingerprint`,
  `publish_build` and `source_db`.

- **`value`** · `TEXT` · not null

  The fact, as text.

### `options`

An OPTION is a candidate rendering of ONE concept in ONE locale.

Identity is the rendering itself, (concept, locale, pl_scope, surface_form),
NOT the source that proposed it. Aya proposing «ثابت» and a human offering
«ثابت» are the SAME option with two provenance rows, not two options. v1 keys
candidates by source, which is why 16,710 translation rows collapse to 11,335
distinct renderings: 5,375 rows are the same word re-attested. (v1 holds
11,336 distinct (term, language, translation) triples; the 11,336th is a
Bengali word stored under two byte sequences that NFC collapses into one;
see migration.md.)

`uid` is content-addressed (see schema_v2.option_uid): deterministic,
reproducible from an export, and stable across a DB rebuild. Publishing an
AUTOINCREMENT rowid would be a bug: rebuilding the DB from files would
renumber it and dangle every published endorsement.

APPEND-ONLY: a bad option is evidence, not garbage (this is the CORE-1400
reframe: the 183 dirty exception translations are simply low-quality
options). Only `withdrawn_at` may be updated; triggers enforce the rest on
UPDATE *and* on DELETE, because a DELETE here cascades away every endorsement a
native speaker ever attached to the row.

**Columns**

- **`uid`** · `TEXT` · primary key

  'opt_' + 24 hex, content-addressed.

- **`concept_id`** · `INTEGER` · not null · references [`concepts`](#concepts)`(id)` on delete restrict

  The concept this option renders.

- **`locale`** · `TEXT` · not null · references [`locales`](#locales)`(tag)` on delete restrict

  The locale this option renders the concept in.

- **`programming_language`** · `TEXT` · references [`programming_languages`](#programming_languages)`(code)` on delete restrict

  `programming_language` NULL = the option applies to the concept in ANY PL
  (the default and the overwhelming majority). Non-NULL = offered specifically
  for that PL's use of the concept.

- **`pl_scope`** · `TEXT` · not null · generated `COALESCE(programming_language, '*')` STORED

  `pl_scope` exists because SQLite treats
  NULLs as distinct in a UNIQUE index; it is the key, NULL is the meaning.
  `'*'` when `programming_language` is NULL, otherwise the PL code.

- **`surface_form`** · `TEXT` · not null

  The rendering itself. Stored NFC; compared NFKC + casefold.

- **`first_seen_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the rendering was first offered. Frozen by
  [`trg_options_append_only`](#trg_options_append_only): it is brigading-detection evidence.

- **`withdrawn_at`** · `TEXT`

  Contributor withdrawal / moderation; row stays.

**Constraints**

```sql
UNIQUE (concept_id, locale, pl_scope, surface_form)
CHECK (uid GLOB 'opt_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
           || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
           || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]')
CHECK (surface_form <> ''
       AND surface_form = TRIM(surface_form, char(9, 10, 11, 12, 13, 28, 29, 30, 31, 32,
                                                  133, 160, 5760, 8192, 8193, 8194, 8195,
                                                  8196, 8197, 8198, 8199, 8200, 8201, 8202,
                                                  8232, 8233, 8239, 8287, 12288)))
CHECK (instr(surface_form, char(31)) = 0)
```

SQLite's one-argument TRIM() strips SPACES ONLY, so `x = TRIM(x)` is
strictly weaker than schema_v2.normalize_surface_form's str.strip(),
which strips every Python whitespace character. The explicit set below
closes the gap. NFC itself is not expressible in SQLite; the uid-drift
test (recompute the uid from the stored columns) is what pins it.

U+001F is the field delimiter of the hashed uid tuple. An INTERIOR one
survives str.strip()'s edge-only trim and lets two distinct tuples forge
one uid. schema_v2._digest raises on it; this is the DB-level floor.

**Indexes**

- <a id="idx_options_identity"></a>`idx_options_identity`: unique on `uid`, `concept_id`, `locale`

  Parent key for the canon composite FK below.

- <a id="idx_options_lookup"></a>`idx_options_lookup`: on `locale`, `concept_id`

**Triggers**

<a id="trg_options_append_only"></a>

- **`trg_options_append_only`** · BEFORE UPDATE OF concept_id, locale, programming_language, surface_form, uid, first_seen_at

  The rendering, its concept, and its locale are immutable. Only `withdrawn_at`
  may change.
  first_seen_at is in the frozen list too: it is brigading-detection evidence
  (a burst of first_seen_at timestamps is the signal), so back-dating it is an
  attack, not a correction.

  Refuses with: `options are append-only: withdraw the row, do not edit it`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_options_append_only
  BEFORE UPDATE OF concept_id, locale, programming_language, surface_form, uid,
                   first_seen_at ON options
  BEGIN
      SELECT RAISE(ABORT, 'options are append-only: withdraw the row, do not edit it');
  END
  ```

  </details>

<a id="trg_options_withdrawal_is_final"></a>

- **`trg_options_withdrawal_is_final`** · BEFORE UPDATE OF withdrawn_at · conditional

  Withdrawal is a one-way door. Un-withdrawing after a canon row was refused is
  the same attack as never withdrawing.

  Refuses with: `options are append-only: a withdrawal cannot be reversed`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_options_withdrawal_is_final
  BEFORE UPDATE OF withdrawn_at ON options
  WHEN OLD.withdrawn_at IS NOT NULL AND NEW.withdrawn_at IS NULL
  BEGIN
      SELECT RAISE(ABORT, 'options are append-only: a withdrawal cannot be reversed');
  END
  ```

  </details>

<a id="trg_options_no_delete"></a>

- **`trg_options_no_delete`** · BEFORE DELETE

  A DELETE cascades to option_provenance, endorsements, option_flags and
  option_validations: it silently destroys every endorsement a native speaker
  ever attached to the word. There is no legitimate caller.

  Refuses with: `options are append-only: DELETE would cascade away the endorsements; withdraw instead`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_options_no_delete
  BEFORE DELETE ON options
  BEGIN
      SELECT RAISE(ABORT,
          'options are append-only: DELETE would cascade away the endorsements; withdraw instead');
  END
  ```

  </details>

<a id="trg_options_no_withdraw_while_canon"></a>

- **`trg_options_no_withdraw_while_canon`** · BEFORE UPDATE OF withdrawn_at · conditional

  The canon may not outlive the option it ratifies. Withdrawing a shipped word
  must fail loudly rather than leave a canon row pointing at a withdrawn option
  (the FK is ON DELETE RESTRICT, but withdrawal is an UPDATE, not a DELETE).

  Refuses with: `options: this option is canon-selected; remove it from the canon file before withdrawing`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_options_no_withdraw_while_canon
  BEFORE UPDATE OF withdrawn_at ON options
  WHEN NEW.withdrawn_at IS NOT NULL
   AND OLD.withdrawn_at IS NULL
   AND EXISTS (SELECT 1 FROM canon_selections cs WHERE cs.option_uid = OLD.uid)
  BEGIN
      SELECT RAISE(ABORT,
          'options: this option is canon-selected; remove it from the canon file before withdrawing');
  END
  ```

  </details>

### `option_provenance`

WHO/WHAT proposed this rendering, and why. Append-only, many per option.
A model is a provenance, never a contributor: models propose, people endorse.

`source` IS PUBLIC: it is the only provenance column the corpus exports,
aggregated per option into `options.sources`. `source_detail` is PRIVATE (it
carries v1 reviewer labels containing real first names), so `source` alone
has to be a useful public vocabulary, and it is cut on ONE question:

*** WHAT DO WE OWE FOR THIS ROW? ***

Obligation, not pipeline origin. That is what makes the vocabulary stable:
a future row's bucket is decided by asking what it obliges us to do, not by
which script happened to insert it. The predecessor vocabulary
('import' / 'community' / 'model' / 'maintainer' / 'literature') was cut on
pipeline origin, and it hid two other projects' work inside a 13,650-row
`import` grab-bag for months, and nothing in the published vocabulary said
"someone else's licence applies here" (CORE-1720).

The two retired values fold in by obligation, not by deletion:

- 'maintainer'  -> 'legesher': a maintainer coinage is our own work; the
  person is already recorded on the endorsement, and the
  REVIEW RUNG 'maintainer' (review_rungs) is untouched.
- 'literature'  -> 'upstream': an established rendering taken from CS
  pedagogy or a standards body owes that body a citation,
  which is the `upstream` obligation. Name it in
  `source_detail` / `import_sources`.

**Columns**

- **`id`** · `INTEGER` · primary key, autoincrement

  Internal integer key.

- **`option_uid`** · `TEXT` · not null · references [`options`](#options)`(uid)` on delete cascade

  The option this provenance row attests.

- **`source`** · `TEXT` · not null

  The public provenance bucket, cut on what the row obliges us to do.

  Allowed values:

  - `legesher`: Our own packs, curated corrections, compositions. What we owe: nothing beyond the dataset licence.
  - `upstream`: Lifted from another open-source project. What we owe: retain their notice, credit them.
  - `community`: Offered by an individual through our native-review process. What we owe: credit on request, withdrawal on request.
  - `model`: Machine-generated. What we owe: disclose which model.

- **`source_detail`** · `TEXT`

  PRIVATE detail behind `source`: 'aya', 'claude', 'yaml_pack',
  'universal_python'. For `model` and `upstream` rows it carries the
  [`import_sources.id`](#import_sources) (CORE-1720).

- **`model_version`** · `TEXT`

  Which model version produced a `model` row.

- **`contributor_id`** · `TEXT` · references [`contributors`](#contributors)`(id)` on delete set null

  The contributor who offered the rendering, when a person did. The one
  legitimate write after insert; set NULL if the contributor row goes.

- **`word_type`** · `TEXT`

  Grammatical type the proposer assigned to the rendering.

- **`word_form`** · `TEXT`

  infinitive_verb, noun, masdar, ...

- **`confidence`** · `TEXT`

  The proposer's stated confidence, when it gave one.

- **`rationale`** · `TEXT`

  The proposer's reasoning. CORE-1502: publish-or-strip is a decision.

- **`created_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the provenance row was recorded.

**Constraints**

```sql
CHECK (source <> 'model' OR model_version IS NOT NULL OR source_detail IS NOT NULL)
```

A machine proposal must say which machine: an unattributed 'model' row is
unauditable provenance. Other sources may leave the detail null.

**Indexes**

- <a id="idx_provenance_option"></a>`idx_provenance_option`: on `option_uid`

- <a id="idx_provenance_source"></a>`idx_provenance_source`: on `source`

**Triggers**

<a id="trg_provenance_append_only"></a>

- **`trg_provenance_append_only`** · BEFORE UPDATE OF id, option_uid, source, source_detail, model_version, created_at

  Provenance is evidence of who/what proposed a word. (contributor_id is
  excluded from the UPDATE list: it is the one legitimate write. Note this is
  NOT the withdrawal path: withdrawal (CORE-1780) leaves provenance and
  endorsements untouched and redacts contributor_identities instead.)

  Refuses with: `option_provenance is append-only`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_provenance_append_only
  BEFORE UPDATE OF id, option_uid, source, source_detail, model_version, created_at
  ON option_provenance
  BEGIN
      SELECT RAISE(ABORT, 'option_provenance is append-only');
  END
  ```

  </details>

<a id="trg_provenance_no_delete"></a>

- **`trg_provenance_no_delete`** · BEFORE DELETE

  Provenance rows are never deleted: the evidence of who or what proposed a
  word stays.

  Refuses with: `option_provenance is append-only`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_provenance_no_delete
  BEFORE DELETE ON option_provenance
  BEGIN
      SELECT RAISE(ABORT, 'option_provenance is append-only');
  END
  ```

  </details>

### `endorsements`

ONE ROW PER ENDORSEMENT. The count is COUNT(*), never a stored integer.

This is what makes the corpus auditable:

- dedupe: the partial UNIQUE below makes double-voting impossible
- weighting: rung_at_endorsement + review_rungs.weight, joined at query
  time, so the ladder can be re-weighted without touching
  community data
- brigading: created_at + method + rung distribution are all on the row

Endorsements are POSITIVE only. Disagreement is expressed by endorsing a
different option (CORE-1466: "propose an option, don't edit the winner").
Harm ("this word is offensive/wrong") goes to option_flags, so it never
pollutes the count of people who said the word.

**Columns**

- **`uid`** · `TEXT` · primary key

  'end_' + 24 hex.

- **`option_uid`** · `TEXT` · not null · references [`options`](#options)`(uid)` on delete cascade

  The option endorsed.

- **`contributor_id`** · `TEXT` · not null · references [`contributors`](#contributors)`(id)` on delete restrict

  Who endorsed it.

- **`method`** · `TEXT` · not null

  How the endorsement reached us.

  Allowed values:

  - `portal`: Review portal vote.
  - `survey`: A survey response.
  - `workshop`: Collected at a workshop.
  - `github`: PR / issue.
  - `interview`: Collected in an interview.
  - `import`: Reconstructed from v1 community rows.

- **`rung_at_endorsement`** · `TEXT` · not null · references [`review_rungs`](#review_rungs)`(rung)`

  Snapshot of the endorser's rung AT THE TIME. Immutable evidence. The
  weight is NOT stored here (see review_rungs).

- **`comment`** · `TEXT`

  The endorser's free-text comment. Moderating it is one of the two
  writes allowed after insert.

- **`created_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the endorsement was made. Brigading evidence, so it is frozen.

- **`retracted_at`** · `TEXT`

  Set when the endorser retracts. The row stays; retraction is final and
  frees the one-live-endorsement slot.

**Constraints**

```sql
CHECK (uid GLOB 'end_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
           || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
           || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]')
```

**Indexes**

- <a id="idx_endorsement_one_per_person"></a>`idx_endorsement_one_per_person`: unique on `option_uid`, `contributor_id` where `retracted_at IS NULL`

  One person, one live endorsement per option. Retraction frees the slot, so
  the table stays append-only AND double-voting stays impossible.

- <a id="idx_endorsement_option"></a>`idx_endorsement_option`: on `option_uid`

- <a id="idx_endorsement_contributor"></a>`idx_endorsement_contributor`: on `contributor_id`

**Triggers**

<a id="trg_endorsements_append_only"></a>

- **`trg_endorsements_append_only`** · BEFORE UPDATE OF uid, option_uid, contributor_id, method, rung_at_endorsement, created_at

  An endorsement is immutable evidence: WHO said WHICH word, at WHAT rung, WHEN.
  Retraction (and moderating the free-text comment) are the only writes. This is
  what makes `rung_at_endorsement` a snapshot rather than a mutable weight,
  the property the PR body claims and, until now, did not have.

  Refuses with: `endorsements are append-only: retract the row and add a new one, do not edit it`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_endorsements_append_only
  BEFORE UPDATE OF uid, option_uid, contributor_id, method, rung_at_endorsement, created_at
  ON endorsements
  BEGIN
      SELECT RAISE(ABORT,
          'endorsements are append-only: retract the row and add a new one, do not edit it');
  END
  ```

  </details>

<a id="trg_endorsements_retraction_is_final"></a>

- **`trg_endorsements_retraction_is_final`** · BEFORE UPDATE OF retracted_at · conditional

  A retraction cannot be undone: re-endorsing is a new row.

  Refuses with: `endorsements are append-only: a retraction cannot be reversed`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_endorsements_retraction_is_final
  BEFORE UPDATE OF retracted_at ON endorsements
  WHEN OLD.retracted_at IS NOT NULL AND NEW.retracted_at IS NULL
  BEGIN
      SELECT RAISE(ABORT, 'endorsements are append-only: a retraction cannot be reversed');
  END
  ```

  </details>

<a id="trg_endorsements_no_delete"></a>

- **`trg_endorsements_no_delete`** · BEFORE DELETE

  Endorsements are never deleted; retract instead.

  Refuses with: `endorsements are append-only: retract, do not delete`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_endorsements_no_delete
  BEFORE DELETE ON endorsements
  BEGIN
      SELECT RAISE(ABORT, 'endorsements are append-only: retract, do not delete');
  END
  ```

  </details>

### `option_flags`

Moderation / harm signal, deliberately NOT a downvote. A downvote on a
minority-language term invites exactly the brigading the endorsement model
exists to detect.

**Columns**

- **`id`** · `INTEGER` · primary key, autoincrement

  Internal integer key.

- **`option_uid`** · `TEXT` · not null · references [`options`](#options)`(uid)` on delete cascade

  The option flagged.

- **`contributor_id`** · `TEXT` · references [`contributors`](#contributors)`(id)` on delete set null

  Who raised the flag, when known.

- **`reason`** · `TEXT` · not null

  Why the option was flagged.

  Allowed values: `offensive`, `wrong_meaning`, `register_mismatch`, `invalid_identifier`, `transliteration`, `spam`.

- **`note`** · `TEXT`

  The flagger's free-text detail.

- **`resolved_at`** · `TEXT`

  When a maintainer resolved the flag. Open flags (NULL) count in
  [`option_standings`](#option_standings) and block promotion.

- **`resolution`** · `TEXT`

  What the resolution was.

- **`created_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the flag was raised.

**Indexes**

- <a id="idx_flags_option"></a>`idx_flags_option`: on `option_uid`

### `option_validations`

Mechanical validation, cached. DERIVED: regenerate with the audit script,
never hand-edit. Kept out of `options` so the corpus stays append-only while
validators are re-run and re-versioned (PR #256 / CORE-1318 findings become
per-row review data, per CORE-1505).

**Columns**

- **`option_uid`** · `TEXT` · primary key · references [`options`](#options)`(uid)` on delete cascade

  The option validated. One verdict row per option.

- **`validator_version`** · `TEXT` · not null

  `validator_version` names the code that produced the verdict, and the canon
  trigger REJECTS the reserved value 'migration-seed'. Without that, the
  CORE-1400 gate is circular: an earlier draft of migrate_to_v2.py stamped all
  5,136 canon-bound rows `identifier_valid = 1, nfkc_stable = 1` WITHOUT
  RUNNING A VALIDATOR, and the trigger then dutifully passed them, including
  1 surface that is not a valid Python identifier (Amharic `ከቀረ*`, a literal
  asterisk, from `except*`) and 25 that are NFKC-unstable (all Thai, the
  U+0E33 class). "pack_export reproduces all 5,136" was true only because the
  gate had been bypassed. A seeded row must never be mistaken for a validated
  one; the migration now runs the real check and reports what fails.

- **`identifier_valid`** · `INTEGER` · not null

  1 when the rendering is a valid identifier for the term (term-aware:
  `except*` keeps its mirrored `*`).

  Allowed values: `0`, `1`.

- **`nfkc_stable`** · `INTEGER` · not null

  1 when NFKC normalization leaves the rendering unchanged.

  Allowed values: `0`, `1`.

- **`nfkc_delta_class`** · `TEXT`

  WHY the value is NFKC-unstable, recorded as a FACT (CORE-1514). NULL when
  stable. 'sara-am-only' = the delta is exclusively U+0E33 (Thai SARA AM),
  which CPython itself NFKC-normalizes in identifiers (PEP 3131), so both
  spellings are one identifier at runtime and there is no spoofing surface.
  'other' is any other instability and stays a hard block. The fact stays a
  fact: the ALLOWANCE for 'sara-am-only' is explicit policy in
  trg_canon_requires_valid_identifier, not a weakening of nfkc_stable.

  Allowed values: `sara-am-only`, `other`.

- **`script_consistent`** · `INTEGER` · not null

  1 when every character belongs to the locale's expected scripts
  (per-character, locale-aware classification, CORE-1514).

  Allowed values: `0`, `1`.

- **`collides_en_keyword`** · `INTEGER` · not null · default `0`

  1 when the rendering would shadow an English keyword.

  Allowed values: `0`, `1`.

- **`min_interpreter_ok`** · `INTEGER` · not null · default `1`

  1 when the rendering uses no character that only became valid in
  identifiers in CPython 3.13, so it runs on the oldest supported
  interpreter.

  Allowed values: `0`, `1`.

- **`format_chars_clean`** · `INTEGER`

  The CORE-2029 format-char net: no forbidden format / Default_Ignorable
  character outside the locale's allowed_format_chars policy: the intake
  half of the CORE-1591 pack gate. U+034F, the Hangul fillers, variation
  selectors and tatweel are invisible, `.isidentifier()`-True, NFKC-stable
  and script-Inherited, so every OTHER column here reads clean on them.
  Nullable ON PURPOSE, and nullable in a fresh build too (ALTER TABLE on a
  carried-forward database cannot add NOT NULL, and the two shapes must
  not diverge): NULL means "never scanned", and the canon gate refuses
  NULL exactly like 0. A default would be a stamp, and a stamped row must
  never pass for a scanned one (the migration-seed lesson above).

  Allowed values: `0`, `1`.

- **`checked_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the verdict was computed.

**Constraints**

```sql
CHECK (validator_version <> '' AND validator_version = TRIM(validator_version))
```

**Triggers**

<a id="trg_validations_frozen_under_canon"></a>

- **`trg_validations_frozen_under_canon`** · BEFORE UPDATE · conditional

  option_validations is a derived cache and is meant to be regenerated, but
  NOT under a live canon row. Flipping `identifier_valid` to 1, or deleting the
  row, while a canon selection depends on it re-opens exactly the hole the
  canon trigger closes (it only fires on the canon INSERT). Re-validating a
  shipped word is legitimate; the order of operations is: drop the canon rows,
  re-run the validator, re-load the canon (which re-checks on INSERT).

  Refuses with: `option_validations: this option is canon-selected; drop the canon row before revalidating`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_validations_frozen_under_canon
  BEFORE UPDATE ON option_validations
  WHEN EXISTS (SELECT 1 FROM canon_selections cs WHERE cs.option_uid = OLD.option_uid)
  BEGIN
      SELECT RAISE(ABORT,
          'option_validations: this option is canon-selected; drop the canon row before revalidating');
  END
  ```

  </details>

<a id="trg_validations_no_delete_under_canon"></a>

- **`trg_validations_no_delete_under_canon`** · BEFORE DELETE · conditional

  The DELETE half of [`trg_validations_frozen_under_canon`](#trg_validations_frozen_under_canon): a verdict a
  canon selection depends on cannot be deleted either.

  Refuses with: `option_validations: this option is canon-selected; drop the canon row first`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_validations_no_delete_under_canon
  BEFORE DELETE ON option_validations
  WHEN EXISTS (SELECT 1 FROM canon_selections cs WHERE cs.option_uid = OLD.option_uid)
  BEGIN
      SELECT RAISE(ABORT,
          'option_validations: this option is canon-selected; drop the canon row first');
  END
  ```

  </details>

### `option_screenings`

Moderation screening verdicts, one row per screening EVENT (CORE-1828;
the verdict shape CORE-1797's automated gate will later write). Sibling to
option_validations by design: validations cache what a machine measured,
screenings record what a screen DECIDED. And the interim screen is a
human (quarantine-by-default, decision 2026-08-11).

Semantics: the LATEST row per option wins (option_screening_status).
'quarantined' is written by the importer for every community-sourced option
it CREATES; 'cleared' / 'held' are maintainer verdicts from the import
ritual. ABSENCE of any row means "predates the intake path" and changes
nothing: the published corpus and every migrated row are unaffected.

Append-only: clearing a cleared row, or re-quarantining after a report,
is a NEW event; the audit trail is the point. screened_by is required
because an anonymous moderation decision is unauditable.

**Columns**

- **`id`** · `INTEGER` · primary key, autoincrement

  Integer key. Also the event order: the highest id per option is the
  current verdict.

- **`option_uid`** · `TEXT` · not null · references [`options`](#options)`(uid)` on delete restrict

  The option screened.

- **`verdict`** · `TEXT` · not null

  What the screen decided.

  Allowed values:

  - `quarantined`: Default on arrival.
  - `cleared`: Competes and exports.
  - `held`: Needs a reviewer with knowledge the screener lacks.
  - `rejected`: Harmful / spam / injection.

- **`screened_by`** · `TEXT` · not null

  Maintainer handle, or 'importer' for the default.

- **`screen_version`** · `TEXT` · not null

  'manual-interim-v1' now; CORE-1797 versions later.

- **`note`** · `TEXT`

  The screener's free-text note.

- **`screened_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the verdict was recorded.

**Constraints**

```sql
CHECK (screened_by <> '' AND screen_version <> '')
```

**Indexes**

- <a id="idx_screenings_option"></a>`idx_screenings_option`: on `option_uid`, `id`

**Triggers**

<a id="trg_screenings_append_only"></a>

- **`trg_screenings_append_only`** · BEFORE UPDATE

  A verdict is never edited; a change of mind is a new screening event.

  Refuses with: `option_screenings are append-only: write a new verdict`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_screenings_append_only
  BEFORE UPDATE ON option_screenings
  BEGIN SELECT RAISE(ABORT, 'option_screenings are append-only: write a new verdict'); END
  ```

  </details>

<a id="trg_screenings_no_delete"></a>

- **`trg_screenings_no_delete`** · BEFORE DELETE

  Screening events are never deleted: the audit trail stays.

  Refuses with: `option_screenings are append-only: the audit trail stays`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_screenings_no_delete
  BEFORE DELETE ON option_screenings
  BEGIN SELECT RAISE(ABORT, 'option_screenings are append-only: the audit trail stays'); END
  ```

  </details>

<a id="trg_screenings_no_quarantine_while_canon"></a>

- **`trg_screenings_no_quarantine_while_canon`** · BEFORE INSERT · conditional

  The inverse hazard, mirroring trg_options_no_withdraw_while_canon: a shipped
  word may not be quarantined in place. Pull it from the canon file first, so
  the demotion is a reviewed text change, not a database side effect.

  Refuses with: `option_screenings: option is canon-selected; remove it from the canon file first`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_screenings_no_quarantine_while_canon
  BEFORE INSERT ON option_screenings
  WHEN NEW.verdict <> 'cleared'
   AND EXISTS (SELECT 1 FROM canon_selections cs WHERE cs.option_uid = NEW.option_uid)
  BEGIN
      SELECT RAISE(ABORT,
          'option_screenings: option is canon-selected; remove it from the canon file first');
  END
  ```

  </details>

### `option_screening_status`

*View.*

The current verdict per option: the latest event wins.

<details><summary>Definition</summary>

```sql
CREATE VIEW option_screening_status AS
SELECT s.option_uid, s.verdict, s.screened_by, s.screen_version, s.note, s.screened_at
FROM option_screenings s
WHERE s.id = (SELECT MAX(s2.id) FROM option_screenings s2
               WHERE s2.option_uid = s.option_uid)
```

</details>

### `option_withheld`

*View.*

THE screening predicate, in one place. Every gate, view and export asks this
view rather than repeating a verdict list, so re-cutting the rule (or adding
a verdict) is one edit instead of ten.

Stated as "not cleared" rather than "quarantined or held" on purpose: a
verdict added later is withheld until someone deliberately decides otherwise,
which is the safe direction for a moderation gate. An option with NO
screening row is absent from this view and therefore visible. That is the
pre-intake default, and it is what keeps migrated rows unaffected.

<details><summary>Definition</summary>

```sql
CREATE VIEW option_withheld AS
SELECT option_uid, verdict FROM option_screening_status WHERE verdict <> 'cleared'
```

</details>

## Canon

CANON: the maintainer decision. Source of truth is TEXT IN THE MONOREPO.

### `canon_selections`

This table is a projection of `libs/i18n/canon/<locale>.toml`, loaded by
`make canon-load`. It is structurally impossible to have a canon row that is
not backed by a reviewed file: source_file is NOT NULL, and a CI drift test
re-loads the files and asserts this table reproduces exactly (the CORE-611
languages.json precedent).

Two invariants enforced by triggers below:

1. You may only select a rendering that EXISTS IN THE CORPUS (option_uid is
   NOT NULL, composite-FK'd to the option's concept + locale). Every shipped
   word is traceable to an offered option, its provenance, and its
   endorsements. A maintainer who wants a word nobody offered must first
   add it as an option with source='legesher'.
2. You may not ship an invalid identifier. The trigger rejects any option
   that fails identifier_valid / nfkc_stable. This is CORE-1400's real
   requirement: gate the SELECTION, not the corpus.

**Columns**

- **`id`** · `INTEGER` · primary key, autoincrement

  Internal integer key.

- **`concept_id`** · `INTEGER` · not null · references [`concepts`](#concepts)`(id)` on delete restrict

  The concept decided.

- **`locale`** · `TEXT` · not null · references [`locales`](#locales)`(tag)` on delete restrict

  The locale the decision is for.

- **`programming_language`** · `TEXT` · references [`programming_languages`](#programming_languages)`(code)` on delete restrict

  programming_language NULL = concept-wide (the default, and the payoff:
  one decision serves every PL that uses the concept). Non-NULL = a deliberate
  per-PL override, taken only when a locale genuinely needs a different word
  for that PL's use of the concept.

- **`pl_scope`** · `TEXT` · not null · generated `COALESCE(programming_language, '*')` STORED

  `'*'` when `programming_language` is NULL, otherwise the PL code. The
  key column, for the same reason as [`options.pl_scope`](#options).

- **`option_uid`** · `TEXT` · not null

  The corpus option ratified. Composite-FK'd with `concept_id` and
  `locale` to [`options`](#options), so the option must render this concept in this
  locale.

- **`surface_form`** · `TEXT` · not null

  Denormalized from the option for a readable diff.

- **`status`** · `TEXT` · not null · default `'machine'`

  The CORE-1466 ladder. 'community' from the v2 draft is gone: a community
  submission is an OPTION, never a canon status.

  Allowed values:

  - `machine`: Auto-picked, unreviewed.
  - `experimental`: Maintainer/ambassador pick.
  - `reviewed`: Native sign-off.
  - `official`: Certified review + term screening.

- **`identity_ok`** · `INTEGER` · not null · default `0`

  Deliberate cognate/loanword equal to the English
  term (policy 2026-07-05); NOT "never translated".

  Allowed values: `0`, `1`.

- **`decided_by`** · `TEXT`

  Who made the call.

- **`decided_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the decision was made.

- **`decision_reason`** · `TEXT`

  Why this rendering was chosen.

- **`source_file`** · `TEXT` · not null

  Proof this row came from reviewed text, not from someone poking the DB.
  For example 'libs/i18n/canon/ar.toml'.

- **`source_revision`** · `TEXT`

  Git sha of the file at load time.

**Constraints**

```sql
UNIQUE (concept_id, locale, pl_scope)
FOREIGN KEY (option_uid, concept_id, locale)
    REFERENCES options(uid, concept_id, locale) ON DELETE RESTRICT
```

**Indexes**

- <a id="idx_canon_locale"></a>`idx_canon_locale`: on `locale`, `status`

- <a id="idx_canon_concept"></a>`idx_canon_concept`: on `concept_id`

**Triggers**

<a id="trg_canon_scope_compatible"></a>

- **`trg_canon_scope_compatible`** · BEFORE INSERT · conditional

  A PL-scoped option cannot be selected for a different PL. A concept-wide
  option ('*') may be selected either concept-wide or as a PL override.

  Refuses with: `canon: option pl_scope does not cover this selection`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_canon_scope_compatible
  BEFORE INSERT ON canon_selections
  WHEN (SELECT o.pl_scope FROM options o WHERE o.uid = NEW.option_uid)
       NOT IN ('*', COALESCE(NEW.programming_language, '*'))
  BEGIN
      SELECT RAISE(ABORT, 'canon: option pl_scope does not cover this selection');
  END
  ```

  </details>

<a id="trg_canon_requires_valid_identifier"></a>

- **`trg_canon_requires_valid_identifier`** · BEFORE INSERT · conditional

  The selection rule (CORE-1400), corrected in both directions by the Q7 triage
  (CORE-1514): never ship an option that fails mechanical validation, but do not
  refuse a legitimate one either. Unvalidated is a reject (silence is not a
  pass), and a 'migration-seed' row is unvalidated: a stamp, not a verdict.
  Four real checks gate the SELECTION:

  - identifier_valid: term-aware (`except*` keeps its mirrored '*'), so a
    faithful rendering is no longer refused for structure.
  - script_consistent: real per-character, locale-aware script classification,
    so a Cyrillic-in-Thai confusable (NFKC-stable, a valid
    identifier) no longer ships.
  - NFKC: stable, OR unstable for exactly one reason: SARA-AM.
    U+0E33 is legitimate Thai orthography that CPython
    normalizes in identifiers (PEP 3131); accepting the
    'sara-am-only' class is explicit policy, and it rides on
    identifier_valid + script_consistent, so the accepted
    NFKC form is itself an identifier-valid single script.
  - format_chars_clean: the CORE-2029 net. Requires = 1, so a NULL (a row
    validated before the net existed, never scanned)
    refuses too: an invisible-character payload the other
    three checks cannot see must not ship on the
    strength of predating the check.

  Refuses with: `canon: option is unvalidated or fails identifier/NFKC/script/format-char validation`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_canon_requires_valid_identifier
  BEFORE INSERT ON canon_selections
  WHEN NOT EXISTS (
      SELECT 1 FROM option_validations v
      WHERE v.option_uid = NEW.option_uid
        AND v.identifier_valid = 1
        AND v.script_consistent = 1
        AND (v.nfkc_stable = 1 OR v.nfkc_delta_class = 'sara-am-only')
        AND v.format_chars_clean = 1
        AND v.validator_version <> 'migration-seed'
  )
  BEGIN
      SELECT RAISE(ABORT, 'canon: option is unvalidated or fails identifier/NFKC/script/format-char validation');
  END
  ```

  </details>

<a id="trg_canon_surface_matches_option"></a>

- **`trg_canon_surface_matches_option`** · BEFORE INSERT · conditional

  The denormalized surface_form must match the option it claims to ratify.

  Refuses with: `canon: surface_form does not match the selected option`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_canon_surface_matches_option
  BEFORE INSERT ON canon_selections
  WHEN NEW.surface_form <> (SELECT o.surface_form FROM options o WHERE o.uid = NEW.option_uid)
  BEGIN
      SELECT RAISE(ABORT, 'canon: surface_form does not match the selected option');
  END
  ```

  </details>

<a id="trg_canon_no_withdrawn_option"></a>

- **`trg_canon_no_withdrawn_option`** · BEFORE INSERT · conditional

  A withdrawn option may not be shipped.

  Refuses with: `canon: option has been withdrawn`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_canon_no_withdrawn_option
  BEFORE INSERT ON canon_selections
  WHEN (SELECT o.withdrawn_at FROM options o WHERE o.uid = NEW.option_uid) IS NOT NULL
  BEGIN
      SELECT RAISE(ABORT, 'canon: option has been withdrawn');
  END
  ```

  </details>

<a id="trg_canon_no_quarantined_option"></a>

- **`trg_canon_no_quarantined_option`** · BEFORE INSERT · conditional

  A quarantined option may not be shipped (CORE-1828): community submissions
  are canon-INELIGIBLE until a maintainer clears them. Clearing is the
  distinct, audited act recorded in option_screenings.

  Refuses with: `canon: option is quarantined pending moderation (CORE-1828); clear it first`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_canon_no_quarantined_option
  BEFORE INSERT ON canon_selections
  WHEN EXISTS (
      SELECT 1 FROM option_withheld q WHERE q.option_uid = NEW.option_uid
  )
  BEGIN
      SELECT RAISE(ABORT,
          'canon: option is quarantined pending moderation (CORE-1828); clear it first');
  END
  ```

  </details>

<a id="trg_canon_no_update"></a>

- **`trg_canon_no_update`** · BEFORE UPDATE

  No UPDATE, ever. The canon is a LOADED PROJECTION of
  `libs/i18n/canon/<locale>.toml`, replaced wholesale on each load, so there is
  no legitimate in-place edit, and mirroring each INSERT trigger with a weaker
  UPDATE equivalent would only invite one. Editing the canon means editing the
  text file and reloading; the INSERT triggers then re-check every invariant.
  (DELETE stays open: it is half of "replace wholesale".)

  Refuses with: `canon_selections is a loaded projection: edit libs/i18n/canon/<locale>.toml and reload`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_canon_no_update
  BEFORE UPDATE ON canon_selections
  BEGIN
      SELECT RAISE(ABORT,
          'canon_selections is a loaded projection: edit libs/i18n/canon/<locale>.toml and reload');
  END
  ```

  </details>

## Triggers

TRIGGERS: the invariants that a FK cannot express.

EVERY invariant here is enforced on INSERT *and* on UPDATE *and* on DELETE.
An INSERT-only trigger is not an invariant, it is a speed bump: each of the
rules below was previously defeated by a one-line UPDATE or DELETE that
re-entered the state the INSERT trigger exists to forbid:

```text
UPDATE canon_selections SET surface_form = …   -> ship a word no option offered
UPDATE option_validations SET identifier_valid = 1
                                              -> ship 'de f!'
UPDATE options SET withdrawn_at = …           -> withdrawn option still exports
DELETE FROM options                           -> cascade away every endorsement
UPDATE endorsements SET rung_at_endorsement = 'maintainer'
                                              -> move a vote's weight 0.0 -> 8.0
UPDATE endorsements SET option_uid = …        -> move a vote to another word
```

The SQL declares these in three groups: CORPUS: append-only; VALIDATION
CACHE; CANON: only ever a loaded projection. Each trigger is documented
with the table it guards.

Triggers declared in this part of the SQL, each documented with its table: [`trg_options_append_only`](#trg_options_append_only), [`trg_options_withdrawal_is_final`](#trg_options_withdrawal_is_final), [`trg_options_no_delete`](#trg_options_no_delete), [`trg_provenance_append_only`](#trg_provenance_append_only), [`trg_provenance_no_delete`](#trg_provenance_no_delete), [`trg_endorsements_append_only`](#trg_endorsements_append_only), [`trg_endorsements_retraction_is_final`](#trg_endorsements_retraction_is_final), [`trg_endorsements_no_delete`](#trg_endorsements_no_delete), [`trg_contributor_id_is_immutable`](#trg_contributor_id_is_immutable), [`trg_validations_frozen_under_canon`](#trg_validations_frozen_under_canon), [`trg_validations_no_delete_under_canon`](#trg_validations_no_delete_under_canon), [`trg_canon_scope_compatible`](#trg_canon_scope_compatible), [`trg_canon_requires_valid_identifier`](#trg_canon_requires_valid_identifier), [`trg_canon_surface_matches_option`](#trg_canon_surface_matches_option), [`trg_canon_no_withdrawn_option`](#trg_canon_no_withdrawn_option), [`trg_canon_no_quarantined_option`](#trg_canon_no_quarantined_option), [`trg_screenings_no_quarantine_while_canon`](#trg_screenings_no_quarantine_while_canon), [`trg_canon_no_update`](#trg_canon_no_update), [`trg_options_no_withdraw_while_canon`](#trg_options_no_withdraw_while_canon).

## Views

The derived read models: counts, standings, precedence, the pack export and
the review dashboards. Every number the corpus reports is computed here at
query time rather than stored.

### `locale_fallback`

*View.*

RFC 4647 Lookup. For every locale, the chain of tags to try, nearest first.
depth 0 = the locale itself.

<details><summary>Definition</summary>

```sql
CREATE VIEW locale_fallback AS
WITH RECURSIVE chain(request_tag, resolved_tag, depth) AS (
    SELECT tag, tag, 0 FROM locales
    UNION ALL
    SELECT c.request_tag, l.parent_tag, c.depth + 1
    FROM chain c
    JOIN locales l ON l.tag = c.resolved_tag
    WHERE l.parent_tag IS NOT NULL
)
SELECT request_tag, resolved_tag, depth FROM chain
```

</details>

### `endorsement_counts`

*View.*

THE derived count: endorsements per option, as a GROUP BY.
`endorsements` and `endorsers` are equal by construction (the partial unique
index); if they ever diverge, the dedupe invariant has been violated.

Policy lives in review_rungs.counts_as_native, not in a `rank >= 3` magic
number here: inserting a rung in the middle of the ladder would otherwise
silently re-define this number across the whole published corpus.

<details><summary>Definition</summary>

```sql
CREATE VIEW endorsement_counts AS
SELECT
    o.uid                                        AS option_uid,
    COUNT(e.uid)                                 AS endorsements,
    COUNT(DISTINCT e.contributor_id)             AS endorsers,
    COALESCE(SUM(r.weight), 0.0)                 AS weighted_endorsement,
    COUNT(CASE WHEN r.counts_as_native = 1 THEN 1 END) AS native_verified_or_above,
    MIN(e.created_at)                            AS first_endorsed_at,
    MAX(e.created_at)                            AS last_endorsed_at
FROM options o
LEFT JOIN endorsements e
       ON e.option_uid = o.uid AND e.retracted_at IS NULL
LEFT JOIN review_rungs r
       ON r.rung = e.rung_at_endorsement
GROUP BY o.uid
```

</details>

### `option_standings`

*View.*

"`true` may have four candidate words with a count each." One row per
candidate rendering, ranked within its (concept x locale x pl_scope).

The other predicates the canon gate (trg_canon_requires_valid_
identifier) actually tests, so this view mirrors canon-eligibility rather
than a stale subset: an identifier-valid, NFKC-stable option can still be
refused for a foreign script (CORE-1514) or an invisible format
character (CORE-2029). A NULL format_chars_clean (never scanned)
reads 0 here for the same reason the trigger refuses it.

Quarantined community submissions do not COMPETE (CORE-1828): they are
invisible to standings, and to everything built on standings, until a
maintainer clears them. The quarantine_queue view is the maintainer lens.

<details><summary>Definition</summary>

```sql
CREATE VIEW option_standings AS
SELECT
    c.slug                       AS concept_slug,
    o.locale,
    o.pl_scope,
    o.uid                        AS option_uid,
    o.surface_form,
    ec.endorsements,
    ec.weighted_endorsement,
    ec.native_verified_or_above,
    o.withdrawn_at,
    (SELECT GROUP_CONCAT(DISTINCT p.source)
       FROM option_provenance p WHERE p.option_uid = o.uid) AS sources,
    (SELECT COUNT(*) FROM option_flags f
      WHERE f.option_uid = o.uid AND f.resolved_at IS NULL)  AS open_flags,
    COALESCE(v.identifier_valid, 0)  AS identifier_valid,
    COALESCE(v.nfkc_stable, 0)       AS nfkc_stable,
    COALESCE(v.script_consistent, 0) AS script_consistent,
    COALESCE(v.format_chars_clean, 0) AS format_chars_clean,
    v.nfkc_delta_class,
    RANK() OVER (
        PARTITION BY o.concept_id, o.locale, o.pl_scope
        ORDER BY ec.weighted_endorsement DESC, ec.endorsements DESC, o.surface_form ASC
    )                            AS standing
FROM options o
JOIN concepts c            ON c.id = o.concept_id
JOIN endorsement_counts ec ON ec.option_uid = o.uid
LEFT JOIN option_validations v ON v.option_uid = o.uid
WHERE NOT EXISTS (
    SELECT 1 FROM option_withheld q WHERE q.option_uid = o.uid
)
```

</details>

### `canon_resolution`

*View.*

Canon resolved through the locale fallback chain.

<details><summary>Definition</summary>

```sql
CREATE VIEW canon_resolution AS
SELECT
    f.request_tag   AS locale,
    f.resolved_tag  AS resolved_locale,
    f.depth         AS locale_distance,
    cs.concept_id,
    cs.pl_scope,
    cs.surface_form,
    cs.status,
    cs.option_uid,
    cs.identity_ok
FROM locale_fallback f
JOIN canon_selections cs ON cs.locale = f.resolved_tag
```

</details>

### `term_resolution`

*View.*

THE precedence rule, in exactly one place. Every term (primary AND secondary)
resolved to the ONE word it renders as, in one locale:

1. locale specificity: the nearest locale in the fallback chain wins
2. PL specificity: within that locale, a PL override beats concept-wide

(documented in design.md, open question Q2)

pack_export and pack_export_conflicts BOTH read from here, which is the point:
a conflict view that re-derives the join without the precedence rule reports a
conflict for every legitimate PL override (see below).

<details><summary>Definition</summary>

```sql
CREATE VIEW term_resolution AS
WITH ranked AS (
    SELECT
        t.id              AS term_id,
        t.export_role,
        t.programming_language,
        r.locale,
        t.name            AS english_term,
        t.category,
        t.subcategory,
        t.version_added,
        t.version_removed,
        c.slug            AS concept_slug,
        r.surface_form    AS translation,
        r.status,
        r.identity_ok,
        r.option_uid,
        r.resolved_locale,
        r.locale_distance,
        CASE WHEN r.pl_scope = t.programming_language
             THEN 'pl_override' ELSE 'concept_wide' END AS scope,
        ROW_NUMBER() OVER (
            PARTITION BY t.programming_language, r.locale, t.id
            ORDER BY r.locale_distance ASC,
                     CASE WHEN r.pl_scope = t.programming_language THEN 0 ELSE 1 END ASC
        ) AS rk
    FROM terms t
    JOIN concepts c ON c.id = t.concept_id
    JOIN canon_resolution r
      ON r.concept_id = t.concept_id
     AND r.pl_scope IN ('*', t.programming_language)
)
SELECT term_id, export_role, programming_language, locale, english_term, category,
       subcategory, concept_slug, translation, status, identity_ok, option_uid,
       resolved_locale, locale_distance, scope, version_added, version_removed
FROM ranked
WHERE rk = 1
```

</details>

### `pack_export`

*View.*

Direction 1, a developer pulls a pack: every term of one PL in one locale.
Exactly one row per (pl, locale, english_term): one `primary` term row per
(pl, name), resolved to one word by term_resolution.

<details><summary>Definition</summary>

```sql
CREATE VIEW pack_export AS
SELECT programming_language, locale, english_term, category, subcategory,
       concept_slug, translation, status, identity_ok, option_uid,
       resolved_locale, locale_distance, scope, version_added, version_removed
FROM term_resolution
WHERE export_role = 'primary'
```

</details>

### `canon_coverage`

*View.*

Coverage split (CORE-1355): deliberate cognates/loanwords (identity_ok = 1,
policy 2026-07-05) are their own class, never "untranslated gaps". Anything
reporting coverage numbers (README counts, corpus cards) reads the split
from here instead of re-deriving key == value at the pack layer.

<details><summary>Definition</summary>

```sql
CREATE VIEW canon_coverage AS
SELECT
    locale,
    pl_scope,
    COUNT(*)                    AS canon_terms,
    SUM(identity_ok)            AS identity_cognates,
    COUNT(*) - SUM(identity_ok) AS translated_terms
FROM canon_selections
GROUP BY locale, pl_scope
```

</details>

### `pack_export_conflicts`

*View.*

The export hazard made visible: one (pl, spelling) mapping to two CONCEPTS
whose canon renderings differ (Python `type`: builtin AND 3.12 soft keyword).
The pack is keyed by the English token, so the two concepts cannot both be
rendered; `export_role` picks the primary and this view surfaces the
divergence for a maintainer to adjudicate instead of dropping it silently.

IT MUST READ POST-PRECEDENCE. The previous version joined canon_selections
directly with `cs.pl_scope IN ('*', t.programming_language)` and no ranking,
so a concept that has BOTH a concept-wide word and a legitimate PL override
produced two rows and was reported as a conflict. That is a false positive on
every use of the PL-override feature. And since this view's contract is
"must be empty, or the pack is ambiguous", a CI gate on it would have made the
feature unusable. Grouping term_resolution (one row per term) reports only a
real cross-concept divergence.

<details><summary>Definition</summary>

```sql
CREATE VIEW pack_export_conflicts AS
SELECT
    programming_language,
    locale,
    english_term,
    COUNT(DISTINCT translation) AS distinct_renderings,
    GROUP_CONCAT(DISTINCT translation) AS renderings
FROM term_resolution
GROUP BY programming_language, locale, english_term
HAVING COUNT(DISTINCT translation) > 1
```

</details>

### `canon_collisions`

*View.*

v1's find_collisions(), re-keyed by concept: within one locale and one PL,
two DISTINCT concepts shipping the SAME word. Cross-PL reuse of a word is now
a feature (same concept, same word), so it is correctly not flagged here.

<details><summary>Definition</summary>

```sql
CREATE VIEW canon_collisions AS
SELECT
    p1.programming_language,
    p1.locale,
    p1.translation,
    GROUP_CONCAT(DISTINCT p1.english_term) AS english_terms,
    COUNT(DISTINCT p1.concept_slug)        AS concepts
FROM pack_export p1
GROUP BY p1.programming_language, p1.locale, p1.translation
HAVING COUNT(DISTINCT p1.concept_slug) > 1
```

</details>

### `review_queue`

*View.*

Direction 2, the native-speaker review queue: concepts in one locale with no
reviewed canon, the definition attached as the review anchor, and every
candidate with its endorsement count.

`total_endorsements` uses the same denominator as candidate_options: live
(non-withdrawn) options only, so the two numbers in this row describe the
same population.

<details><summary>Definition</summary>

```sql
CREATE VIEW review_queue AS
SELECT
    l.tag                 AS locale,
    c.slug                AS concept_slug,
    c.definition_en,
    c.category            AS concept_category,
    cs.surface_form       AS current_selection,
    COALESCE(cs.status, 'none') AS status,
    (SELECT COUNT(*) FROM options o
      WHERE o.concept_id = c.id AND o.locale = l.tag AND o.withdrawn_at IS NULL)
                          AS candidate_options,
    (SELECT COALESCE(SUM(ec.endorsements), 0)
       FROM options o JOIN endorsement_counts ec ON ec.option_uid = o.uid
      WHERE o.concept_id = c.id AND o.locale = l.tag AND o.withdrawn_at IS NULL)
                          AS total_endorsements,
    (SELECT GROUP_CONCAT(DISTINCT t.programming_language)
       FROM terms t WHERE t.concept_id = c.id) AS used_by,
    (SELECT GROUP_CONCAT(DISTINCT t.name)
       FROM terms t WHERE t.concept_id = c.id) AS surface_forms
FROM concepts c
CROSS JOIN locales l
LEFT JOIN canon_selections cs
       ON cs.concept_id = c.id AND cs.locale = l.tag AND cs.pl_scope = '*'
WHERE l.in_registry = 1
  AND (cs.status IS NULL OR cs.status IN ('machine', 'experimental'))
```

</details>

### `locale_progress`

*View.*

The experimental -> official dashboard, per (PL x locale).

<details><summary>Definition</summary>

```sql
CREATE VIEW locale_progress AS
SELECT
    t.programming_language,
    l.tag                                          AS locale,
    l.name                                         AS locale_name,
    COUNT(DISTINCT t.concept_id)                   AS concepts_needed,
    COUNT(DISTINCT cs.concept_id)                  AS concepts_selected,
    COUNT(DISTINCT CASE WHEN cs.status IN ('reviewed', 'official')
                        THEN cs.concept_id END)    AS concepts_reviewed,
    COUNT(DISTINCT CASE WHEN cs.status = 'official'
                        THEN cs.concept_id END)    AS concepts_official
FROM terms t
CROSS JOIN locales l
LEFT JOIN canon_selections cs
       ON cs.concept_id = t.concept_id
      AND cs.locale = l.tag
      AND cs.pl_scope IN ('*', t.programming_language)
WHERE t.export_role = 'primary'
GROUP BY t.programming_language, l.tag
```

</details>

### `new_pl_reuse`

*View.*

Onboarding a new PL: how much arrives already-translated. The number to put
in front of reviewers ("your Turkish review of `break` just shipped in 10
programming languages").

<details><summary>Definition</summary>

```sql
CREATE VIEW new_pl_reuse AS
SELECT
    t.programming_language,
    cs.locale,
    COUNT(DISTINCT t.concept_id)   AS concepts_total,
    COUNT(DISTINCT cs.concept_id)  AS concepts_already_selected,
    COUNT(DISTINCT CASE WHEN cs.status IN ('reviewed', 'official')
                        THEN cs.concept_id END) AS concepts_already_reviewed
FROM terms t
LEFT JOIN canon_selections cs
       ON cs.concept_id = t.concept_id AND cs.pl_scope = '*'
WHERE t.export_role = 'primary'
GROUP BY t.programming_language, cs.locale
```

</details>

## Deferred

DEFERRED (created, inert, NOT part of the HF corpus one-way door)
Error message STRINGS are sentences with grammar, not vocabulary. Keyed by
(implementation, version, key), so CPython 3.12's rewordings do not
invalidate 3.11's translations. See proposal doc 06 / 09.

### `message_templates`

One English error-message template per (implementation, key,
version_added). A reworded message is a new row under a new
`version_added`, never an edit.

**Columns**

- **`id`** · `INTEGER` · primary key, autoincrement

  Internal integer key.

- **`implementation`** · `TEXT` · not null

  'cpython', 'v8', 'rustc'.

- **`key`** · `TEXT` · not null

  'ZeroDivisionError.division_by_zero'.

- **`template_en`** · `TEXT` · not null

  'division by zero'.

- **`placeholders`** · `TEXT`

  JSON: `[{"name":"obj_type","example":"str"}]`.

- **`matcher`** · `TEXT`

  Regex/fingerprint for runtime interception.

- **`concept_id`** · `INTEGER` · references [`concepts`](#concepts)`(id)` on delete set null

  The concept the message is about, when there is one.

- **`version_added`** · `TEXT`

  The implementation version that introduced this wording.

- **`version_removed`** · `TEXT`

  The implementation version that dropped this wording. NULL while
  current.

**Constraints**

```sql
UNIQUE (implementation, key, version_added)
```

### `message_translations`

One localized rendering of a message template per locale.

**Columns**

- **`id`** · `INTEGER` · primary key, autoincrement

  Internal integer key. Not content-addressed, which is why
  [`message_endorsements`](#message_endorsements) must not be published yet.

- **`template_id`** · `INTEGER` · not null · references [`message_templates`](#message_templates)`(id)` on delete cascade

  The template translated.

- **`locale`** · `TEXT` · not null · references [`locales`](#locales)`(tag)` on delete restrict

  The locale of the translation.

- **`template`** · `TEXT` · not null

  Localized, placeholders preserved.

- **`status`** · `TEXT` · not null · default `'machine'`

  Maturity of the translation, on the same ladder as
  [`canon_selections.status`](#canon_selections).

  Allowed values: `machine`, `experimental`, `reviewed`, `official`.

- **`source`** · `TEXT`

  Provenance (CORE-1881), mirroring the terms-side `translations` columns:
  where a rendering came from ('seed', 'claude_agent', 'community', ...),
  which model produced it, and which tool wrote it. NULL means "not
  recorded" (rows predating the columns; see
  scripts/add_message_provenance.py). Write paths record all applicable
  fields and refuse a database missing the columns.

- **`model_version`** · `TEXT`

  Which model produced the rendering (CORE-1881 provenance). NULL means
  not recorded.

- **`created_by`** · `TEXT`

  Which tool wrote the row (CORE-1881 provenance). NULL means not
  recorded.

**Constraints**

```sql
UNIQUE (template_id, locale)
```

## Review Intake

REVIEW INTAKE (CORE-1538): sessions, rankings, annotations, expansions,
commentary, style ratifications, import-source registry.

The intake layer over the corpus: how structured native review arrives
(review bundles),
with the same discipline as the corpus itself: append-only community
tables (full UPDATE/DELETE trigger mirrors), content-addressed uids
(formulae in schema_v2.py: session_uid, annotation_uid, expansion_uid,
commentary_uid, style_uid; deterministic, so re-importing a bundle is
INSERT-idempotent), pl_scope as the `'*'` STORED generated column, and
policy expressed in views so thresholds re-cut in one place.

Layers: review_sessions + junctions + session_rankings +
option_annotations + option_expansions + concept_commentary are
CORPUS-ADJACENT (community-writable, append-only, publish-eligible);
commentary_moderation is DERIVED (mutable, regenerable);
import_sources is REFERENCE; message_endorsements is DEFERRED/inert
like the message tables above.

The views at the end of this section are the REVIEW-INTAKE VIEWS.

### `import_sources`

REFERENCE: every non-human candidate stream, so license posture and
attribution are data, not lore. `redistributable` gates whether terms from
this source may be STORED as options / exported in the CC BY 4.0 corpus,
or only DISPLAYED as attributed references in the review kit.
option_provenance.source_detail carries this id for
source='model' / source='upstream' (CORE-1720).

**Columns**

- **`id`** · `TEXT` · primary key

  'model:aya-expanse-32b', 'initiative:hedy'. Lowercase, no spaces.

- **`kind`** · `TEXT` · not null

  What sort of stream this is.

  Allowed values: `model`, `initiative`, `dataset`.

- **`name`** · `TEXT` · not null

  Display name of the source.

- **`url`** · `TEXT`

  Where the source lives.

- **`license_spdx`** · `TEXT`

  'Apache-2.0', 'EUPL-1.2'; NULL = none found.

- **`redistributable`** · `INTEGER` · not null · default `0`

  1 when terms from this source may be stored as options and exported.
  Requires a recorded licence.

  Allowed values: `0`, `1`.

- **`attribution`** · `TEXT`

  Credit line required when displayed/exported.

- **`fetched_ref`** · `TEXT`

  Commit sha / dataset revision imported from.

- **`notes`** · `TEXT`

  Free-text maintainer notes on the source.

- **`created_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the row was inserted.

**Constraints**

```sql
CHECK (id = LOWER(id) AND id NOT LIKE '% %' AND instr(id, char(31)) = 0)
CHECK (redistributable = 0 OR license_spdx IS NOT NULL)
```

Redistribution is a verified license posture, never a default.

### `review_sessions`

One completed sitting of the review app (or an imported issue-form
response): the provenance + verification anchor for everything a reviewer
produced in it. uid = 'ses_' + sha256(canonical bundle)[:24], so re-import
is idempotent. The ONE intake table with a workflow: append-only EXCEPT
status / verification_report / notes.

**Columns**

- **`uid`** · `TEXT` · primary key

  'ses_' + the first 24 hex characters of `bundle_digest`.

- **`contributor_id`** · `TEXT` · not null · references [`contributors`](#contributors)`(id)` on delete restrict

  The reviewer.

- **`locale`** · `TEXT` · not null · references [`locales`](#locales)`(tag)` on delete restrict

  The locale reviewed.

- **`track`** · `TEXT` · not null

  Which body of work the reviewer sat for.

  Allowed values: `reserved_words`, `messages`, `style_profile`.

- **`programming_language`** · `TEXT` · references [`programming_languages`](#programming_languages)`(code)` on delete restrict

  The programming language reviewed. Must be NULL on a style-profile
  session.

- **`pl_scope`** · `TEXT` · not null · generated `COALESCE(programming_language, '*')` STORED

  `'*'` when `programming_language` is NULL, otherwise the PL code.

- **`method`** · `TEXT` · not null

  Same vocabulary as endorsements.method.

  Allowed values: `portal`, `survey`, `workshop`, `github`, `interview`, `import`.

- **`kit_version`** · `TEXT` · not null

  Review-kit build the reviewer saw.

- **`app_version`** · `TEXT`

  Version of the review app that produced the bundle.

- **`rung_at_session`** · `TEXT` · not null · references [`review_rungs`](#review_rungs)`(rung)`

  Snapshot, immutable.

- **`bundle_digest`** · `TEXT` · not null

  Full sha256 (64 hex); uid is its truncation.

- **`contact_captured`** · `INTEGER` · not null · default `0`

  Email reached the PRIVATE channel; the address
  itself lives in contributor_identities only.

  Allowed values: `0`, `1`.

- **`started_at`** · `TEXT`

  Client-reported; advisory evidence.

- **`submitted_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the bundle was submitted.

- **`status`** · `TEXT` · not null · default `'submitted'`

  Where the session is in verification. `accepted` and `rejected` are
  terminal.

  Allowed values: `submitted`, `verifying`, `accepted`, `returned`, `rejected`.

- **`verification_report`** · `TEXT`

  JSON, one entry per pipeline stage.

- **`notes`** · `TEXT`

  Maintainer notes on the session.

**Constraints**

```sql
CHECK (uid GLOB 'ses_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
           || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
           || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]')
CHECK (bundle_digest NOT GLOB '*[^0-9a-f]*' AND length(bundle_digest) = 64)
CHECK (uid = 'ses_' || substr(bundle_digest, 1, 24))
CHECK (track <> 'style_profile' OR programming_language IS NULL)
```

Every character hex, not just the first: GLOB '[0-9a-f]*' anchors only
position 1, so the negated class over the whole string is the real check.

The uid IS the digest's truncation (schema_v2.session_uid); a hand-written
INSERT must not be able to pair a well-formed uid with an unrelated digest,
or re-import idempotency and bundle re-verification silently break.

A style-profile session is locale-wide by definition.

**Indexes**

- <a id="idx_sessions_locale"></a>`idx_sessions_locale`: on `locale`, `track`, `status`

- <a id="idx_sessions_contributor"></a>`idx_sessions_contributor`: on `contributor_id`

**Triggers**

<a id="trg_sessions_evidence_frozen"></a>

- **`trg_sessions_evidence_frozen`** · BEFORE UPDATE OF uid, contributor_id, locale, track, programming_language, method, kit_version, app_version, rung_at_session, bundle_digest, contact_captured, started_at, submitted_at

  Evidence columns are frozen; only the workflow columns may move.

  Refuses with: `review_sessions: evidence is append-only; only status/verification_report/notes may change`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_sessions_evidence_frozen
  BEFORE UPDATE OF uid, contributor_id, locale, track, programming_language, method,
                   kit_version, app_version, rung_at_session, bundle_digest,
                   contact_captured, started_at, submitted_at ON review_sessions
  BEGIN
      SELECT RAISE(ABORT,
          'review_sessions: evidence is append-only; only status/verification_report/notes may change');
  END
  ```

  </details>

<a id="trg_sessions_terminal_states"></a>

- **`trg_sessions_terminal_states`** · BEFORE UPDATE OF status · conditional

  Terminal states stay terminal: an accepted session has been ingested
  (un-accepting would orphan corpus rows); a rejection is a moderation
  decision with its own record. A returned session resubmits as a NEW
  bundle (new content -> new uid), never mutates back.

  Refuses with: `review_sessions: accepted/rejected are terminal; resubmit as a new bundle`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_sessions_terminal_states
  BEFORE UPDATE OF status ON review_sessions
  WHEN OLD.status IN ('accepted', 'rejected') AND NEW.status <> OLD.status
  BEGIN
      SELECT RAISE(ABORT, 'review_sessions: accepted/rejected are terminal; resubmit as a new bundle');
  END
  ```

  </details>

<a id="trg_sessions_no_delete"></a>

- **`trg_sessions_no_delete`** · BEFORE DELETE

  Sessions are never deleted: they anchor everything a reviewer produced.

  Refuses with: `review_sessions are append-only`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_sessions_no_delete
  BEFORE DELETE ON review_sessions
  BEGIN
      SELECT RAISE(ABORT, 'review_sessions are append-only');
  END
  ```

  </details>

<a id="trg_sessions_report_frozen_when_terminal"></a>

- **`trg_sessions_report_frozen_when_terminal`** · BEFORE UPDATE OF verification_report, notes · conditional

  Once a session is terminal, its verification report and notes are part of
  the record: rewriting the audit trail after acceptance/rejection is the
  same attack as editing evidence. (The transition INTO the terminal state
  writes the report in the same UPDATE, which passes because OLD.status is not yet
  terminal.)

  Refuses with: `review_sessions: the verification report is frozen once the session is terminal`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_sessions_report_frozen_when_terminal
  BEFORE UPDATE OF verification_report, notes ON review_sessions
  WHEN OLD.status IN ('accepted', 'rejected') AND NEW.status = OLD.status
  BEGIN
      SELECT RAISE(ABORT,
          'review_sessions: the verification report is frozen once the session is terminal');
  END
  ```

  </details>

### `session_options`

*`WITHOUT ROWID` table.*

Junctions: which corpus rows a session produced. options/endorsements stay
exactly as above (no new columns on frozen shapes); linkage lives here.
`elicited` preserves the blind-first ordering, the research signal the
structured flow exists to collect. Fully frozen.

**Columns**

- **`session_uid`** · `TEXT` · part of the primary key · not null · references [`review_sessions`](#review_sessions)`(uid)` on delete restrict

  The session that produced the option.

- **`option_uid`** · `TEXT` · part of the primary key · not null · references [`options`](#options)`(uid)` on delete restrict

  The option produced.

- **`elicited`** · `TEXT` · not null

  When in the session the option was offered.

  Allowed values:

  - `blind`: Before candidates shown.
  - `after_reveal`: After seeing candidates.
  - `quick`: Non-session path (issue form).

**Constraints**

```sql
PRIMARY KEY (session_uid, option_uid)
```

**Triggers**

<a id="trg_session_options_frozen"></a>

- **`trg_session_options_frozen`** · BEFORE UPDATE

  Session linkage is never edited.

  Refuses with: `session_options is append-only`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_session_options_frozen
  BEFORE UPDATE ON session_options
  BEGIN SELECT RAISE(ABORT, 'session_options is append-only'); END
  ```

  </details>

<a id="trg_session_options_no_delete"></a>

- **`trg_session_options_no_delete`** · BEFORE DELETE

  Session linkage is never deleted.

  Refuses with: `session_options is append-only`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_session_options_no_delete
  BEFORE DELETE ON session_options
  BEGIN SELECT RAISE(ABORT, 'session_options is append-only'); END
  ```

  </details>

### `session_endorsements`

*`WITHOUT ROWID` table.*

The second junction: which endorsements a session produced. Fully frozen,
and a session may only claim its own contributor's endorsements.

**Columns**

- **`session_uid`** · `TEXT` · part of the primary key · not null · references [`review_sessions`](#review_sessions)`(uid)` on delete restrict

  The session that produced the endorsement.

- **`endorsement_uid`** · `TEXT` · part of the primary key · not null · references [`endorsements`](#endorsements)`(uid)` on delete restrict

  The endorsement produced.

**Constraints**

```sql
PRIMARY KEY (session_uid, endorsement_uid)
```

**Triggers**

<a id="trg_session_endorsements_frozen"></a>

- **`trg_session_endorsements_frozen`** · BEFORE UPDATE

  Session linkage is never edited.

  Refuses with: `session_endorsements is append-only`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_session_endorsements_frozen
  BEFORE UPDATE ON session_endorsements
  BEGIN SELECT RAISE(ABORT, 'session_endorsements is append-only'); END
  ```

  </details>

<a id="trg_session_endorsements_no_delete"></a>

- **`trg_session_endorsements_no_delete`** · BEFORE DELETE

  Session linkage is never deleted.

  Refuses with: `session_endorsements is append-only`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_session_endorsements_no_delete
  BEFORE DELETE ON session_endorsements
  BEGIN SELECT RAISE(ABORT, 'session_endorsements is append-only'); END
  ```

  </details>

<a id="trg_session_endorsements_same_contributor"></a>

- **`trg_session_endorsements_same_contributor`** · BEFORE INSERT · conditional

  A session may only claim endorsements its OWN contributor made. Linking
  someone else's endorsement to a session would misattribute evidence.

  Refuses with: `session_endorsements: endorsement belongs to a different contributor than the session`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_session_endorsements_same_contributor
  BEFORE INSERT ON session_endorsements
  WHEN (SELECT e.contributor_id FROM endorsements e WHERE e.uid = NEW.endorsement_uid)
    <> (SELECT s.contributor_id FROM review_sessions s WHERE s.uid = NEW.session_uid)
  BEGIN
      SELECT RAISE(ABORT,
          'session_endorsements: endorsement belongs to a different contributor than the session');
  END
  ```

  </details>

### `session_rankings`

Session-scoped preference order. Separate from endorsements on purpose:

- endorsement = "I would teach this word"   (positive, at-most-one per person)
- ranking     = "among those, this order"   (re-elicitable, session-scoped)

Append-only across sessions; aggregation reads each contributor's LATEST
accepted session via latest_rankings. No downvotes anywhere: an unranked,
unendorsed option is simply "passed".

**Columns**

- **`session_uid`** · `TEXT` · not null · references [`review_sessions`](#review_sessions)`(uid)` on delete restrict

  The session the ranking came from.

- **`concept_id`** · `INTEGER` · not null · references [`concepts`](#concepts)`(id)` on delete restrict

  The concept ranked.

- **`locale`** · `TEXT` · not null · references [`locales`](#locales)`(tag)` on delete restrict

  The locale ranked. Must equal the session's locale.

- **`programming_language`** · `TEXT` · references [`programming_languages`](#programming_languages)`(code)` on delete restrict

  The programming language the ranking is scoped to, or NULL for
  concept-wide.

- **`pl_scope`** · `TEXT` · not null · generated `COALESCE(programming_language, '*')` STORED

  `'*'` when `programming_language` is NULL, otherwise the PL code.

- **`option_uid`** · `TEXT` · not null · references [`options`](#options)`(uid)` on delete restrict

  The option placed at `rank`.

- **`rank`** · `INTEGER` · not null · check `rank >= 1`

  1 = "ship this".

- **`revised_after_reveal`** · `INTEGER` · not null · default `0`

  1 when the reviewer changed this ranking after the candidates were
  revealed.

  Allowed values: `0`, `1`.

- **`comment`** · `TEXT`

  The reviewer's free-text comment.

**Constraints**

```sql
UNIQUE (session_uid, concept_id, locale, pl_scope, option_uid)
```

A generated column may sit in a UNIQUE constraint but not in a PRIMARY
KEY (SQLite rule; canon_selections uses the same pattern).

**Indexes**

- <a id="uq_ranking_slot"></a>`uq_ranking_slot`: unique on `session_uid`, `concept_id`, `locale`, `pl_scope`, `rank`

  One option per rank slot within a session's view of a concept. pl_scope is
  never NULL (it is the '*' sentinel), so this index needs no IFNULL gymnastics,
  which is the reason the sentinel exists rather than a nullable column.

- <a id="idx_rankings_option"></a>`idx_rankings_option`: on `option_uid`

**Triggers**

<a id="trg_ranking_requires_endorsement"></a>

- **`trg_ranking_requires_endorsement`** · BEFORE INSERT · conditional

  You may only rank a word you endorsed (live, yours). The importer enforces
  this at the bundle level; this trigger is the DB floor. A LATER retraction
  legitimately strands the ranking row: it stays as evidence; aggregation
  joins live endorsements and ignores it.

  Refuses with: `session_rankings: rank only options this contributor has endorsed`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_ranking_requires_endorsement
  BEFORE INSERT ON session_rankings
  WHEN NOT EXISTS (
      SELECT 1
      FROM endorsements e
      JOIN review_sessions s ON s.uid = NEW.session_uid
      WHERE e.option_uid = NEW.option_uid
        AND e.contributor_id = s.contributor_id
        AND e.retracted_at IS NULL
  )
  BEGIN
      SELECT RAISE(ABORT, 'session_rankings: rank only options this contributor has endorsed');
  END
  ```

  </details>

<a id="trg_ranking_option_matches_concept"></a>

- **`trg_ranking_option_matches_concept`** · BEFORE INSERT · conditional

  The ranked option must render the concept/locale the row claims. A
  mis-keyed ranking would silently poison aggregation.

  Refuses with: `session_rankings: option does not render this concept/locale/scope`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_ranking_option_matches_concept
  BEFORE INSERT ON session_rankings
  WHEN NOT EXISTS (
      SELECT 1 FROM options o
      WHERE o.uid = NEW.option_uid
        AND o.concept_id = NEW.concept_id
        AND o.locale = NEW.locale
        AND o.pl_scope IN ('*', NEW.pl_scope)
  )
  BEGIN
      SELECT RAISE(ABORT, 'session_rankings: option does not render this concept/locale/scope');
  END
  ```

  </details>

<a id="trg_ranking_locale_matches_session"></a>

- **`trg_ranking_locale_matches_session`** · BEFORE INSERT · conditional

  And the ranking's locale must be the session's locale: an Urdu ranking
  filed under a Spanish session is mis-keyed evidence.

  Refuses with: `session_rankings: locale does not match the session locale`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_ranking_locale_matches_session
  BEFORE INSERT ON session_rankings
  WHEN NEW.locale <> (SELECT s.locale FROM review_sessions s WHERE s.uid = NEW.session_uid)
  BEGIN
      SELECT RAISE(ABORT, 'session_rankings: locale does not match the session locale');
  END
  ```

  </details>

<a id="trg_rankings_append_only"></a>

- **`trg_rankings_append_only`** · BEFORE UPDATE

  Rankings are never edited; a new session supersedes them.

  Refuses with: `session_rankings are append-only: a new session supersedes them`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_rankings_append_only
  BEFORE UPDATE ON session_rankings
  BEGIN SELECT RAISE(ABORT, 'session_rankings are append-only: a new session supersedes them'); END
  ```

  </details>

<a id="trg_rankings_no_delete"></a>

- **`trg_rankings_no_delete`** · BEFORE DELETE

  Rankings are never deleted.

  Refuses with: `session_rankings are append-only`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_rankings_no_delete
  BEFORE DELETE ON session_rankings
  BEGIN SELECT RAISE(ABORT, 'session_rankings are append-only'); END
  ```

  </details>

### `option_annotations`

Neutral, crowd-attestable DESCRIPTORS of an option, distinct from
option_flags (moderation/harm): no resolution workflow, no negative
charge. This is the transliteration checkbox: transliteration popularity
per locale is revealed preference feeding locales.terminology_policy
(a Bengali-style community preferring transliteration is legitimate, not a
defect), while option_flags(reason='transliteration') stays reserved for the
model-policy violation (2026-07-05 rule). Vocabulary is a CHECK, matching
the house style for flags/methods; adding a `kind` rides a migration like
any other vocabulary change.

**Columns**

- **`uid`** · `TEXT` · primary key

  'ann_' + 24 hex, content-addressed (schema_v2.annotation_uid).

- **`option_uid`** · `TEXT` · not null · references [`options`](#options)`(uid)` on delete restrict

  The option described.

- **`contributor_id`** · `TEXT` · not null · references [`contributors`](#contributors)`(id)` on delete restrict

  Who attested the descriptor.

- **`session_uid`** · `TEXT` · references [`review_sessions`](#review_sessions)`(uid)` on delete restrict

  The session it came from, when it came from one.

- **`kind`** · `TEXT` · not null

  The descriptor attested.

  Allowed values:

  - `transliteration`: Phonetic copy of the English term.
  - `cognate_loanword`: Genuine cognate / established loan.
  - `established_term`: Existing classroom/textbook usage.
  - `coined_neologism`: New coinage for this concept.
  - `register_formal`: Formal register.
  - `register_informal`: Informal register.
  - `regional`: Locale-specific; locale-split signal.

- **`comment`** · `TEXT`

  The contributor's free-text comment.

- **`created_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the descriptor was attested.

- **`retracted_at`** · `TEXT`

  Set when the contributor retracts. Final; frees the slot in
  `uq_annotation_once`.

**Constraints**

```sql
CHECK (uid GLOB 'ann_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
           || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
           || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]')
```

**Indexes**

- <a id="uq_annotation_once"></a>`uq_annotation_once`: unique on `option_uid`, `contributor_id`, `kind` where `retracted_at IS NULL`

- <a id="idx_annotations_option"></a>`idx_annotations_option`: on `option_uid`

**Triggers**

<a id="trg_annotations_contributor_matches_session"></a>

- **`trg_annotations_contributor_matches_session`** · BEFORE INSERT · conditional

  A session-linked row must belong to the session's contributor: the uid
  formula binds them, but the formula lives in application code and this
  floor must hold against a hand-written INSERT. Same rule on expansions,
  commentary, and style ratifications below.

  Refuses with: `option_annotations: contributor does not match the session contributor`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_annotations_contributor_matches_session
  BEFORE INSERT ON option_annotations
  WHEN NEW.session_uid IS NOT NULL
   AND NEW.contributor_id <> (SELECT s.contributor_id FROM review_sessions s
                               WHERE s.uid = NEW.session_uid)
  BEGIN
      SELECT RAISE(ABORT, 'option_annotations: contributor does not match the session contributor');
  END
  ```

  </details>

<a id="trg_annotations_append_only"></a>

- **`trg_annotations_append_only`** · BEFORE UPDATE OF uid, option_uid, contributor_id, session_uid, kind, created_at

  Annotations are never edited; retract instead.

  Refuses with: `option_annotations are append-only: retract, do not edit`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_annotations_append_only
  BEFORE UPDATE OF uid, option_uid, contributor_id, session_uid, kind, created_at
  ON option_annotations
  BEGIN SELECT RAISE(ABORT, 'option_annotations are append-only: retract, do not edit'); END
  ```

  </details>

<a id="trg_annotations_retraction_is_final"></a>

- **`trg_annotations_retraction_is_final`** · BEFORE UPDATE OF retracted_at · conditional

  A retraction cannot be undone.

  Refuses with: `option_annotations: a retraction cannot be reversed`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_annotations_retraction_is_final
  BEFORE UPDATE OF retracted_at ON option_annotations
  WHEN OLD.retracted_at IS NOT NULL AND NEW.retracted_at IS NULL
  BEGIN SELECT RAISE(ABORT, 'option_annotations: a retraction cannot be reversed'); END
  ```

  </details>

<a id="trg_annotations_no_delete"></a>

- **`trg_annotations_no_delete`** · BEFORE DELETE

  Annotations are never deleted; retract instead.

  Refuses with: `option_annotations are append-only: retract, do not delete`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_annotations_no_delete
  BEFORE DELETE ON option_annotations
  BEGIN SELECT RAISE(ABORT, 'option_annotations are append-only: retract, do not delete'); END
  ```

  </details>

### `option_expansions`

The phrase layer (elif-class concepts). The reviewed agreement has TWO
layers: (1) the expanded phrase in the target language (prose; spaces
welcome), which is this table; (2) the contracted surface form that becomes the
identifier, which is the option it attaches to. The canon TOML gains an optional
`expansion` per entry, copied from the winning option's most-attested
expansion at selection time.

**Columns**

- **`uid`** · `TEXT` · primary key

  'exp_' + 24 hex, content-addressed (schema_v2.expansion_uid).

- **`option_uid`** · `TEXT` · not null · references [`options`](#options)`(uid)` on delete restrict

  The contracted option the phrase expands.

- **`contributor_id`** · `TEXT` · not null · references [`contributors`](#contributors)`(id)` on delete restrict

  Who offered the expansion.

- **`session_uid`** · `TEXT` · references [`review_sessions`](#review_sessions)`(uid)` on delete restrict

  The session it came from, when it came from one.

- **`expansion`** · `TEXT` · not null

  Stored NFC, like surface_form.

- **`formation_note`** · `TEXT`

  How the expansion contracts to the token.

- **`created_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the expansion was offered.

- **`retracted_at`** · `TEXT`

  Set when the contributor retracts. Final.

**Constraints**

```sql
CHECK (uid GLOB 'exp_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
           || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
           || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]')
CHECK (expansion <> '' AND instr(expansion, char(31)) = 0)
```

**Indexes**

- <a id="idx_expansions_option"></a>`idx_expansions_option`: on `option_uid`

**Triggers**

<a id="trg_expansions_contributor_matches_session"></a>

- **`trg_expansions_contributor_matches_session`** · BEFORE INSERT · conditional

  The same session-contributor floor as
  [`trg_annotations_contributor_matches_session`](#trg_annotations_contributor_matches_session).

  Refuses with: `option_expansions: contributor does not match the session contributor`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_expansions_contributor_matches_session
  BEFORE INSERT ON option_expansions
  WHEN NEW.session_uid IS NOT NULL
   AND NEW.contributor_id <> (SELECT s.contributor_id FROM review_sessions s
                               WHERE s.uid = NEW.session_uid)
  BEGIN
      SELECT RAISE(ABORT, 'option_expansions: contributor does not match the session contributor');
  END
  ```

  </details>

<a id="trg_expansions_append_only"></a>

- **`trg_expansions_append_only`** · BEFORE UPDATE OF uid, option_uid, contributor_id, session_uid, expansion, formation_note, created_at

  Expansions are never edited; retract instead.

  Refuses with: `option_expansions are append-only: retract, do not edit`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_expansions_append_only
  BEFORE UPDATE OF uid, option_uid, contributor_id, session_uid, expansion,
                   formation_note, created_at ON option_expansions
  BEGIN SELECT RAISE(ABORT, 'option_expansions are append-only: retract, do not edit'); END
  ```

  </details>

<a id="trg_expansions_retraction_is_final"></a>

- **`trg_expansions_retraction_is_final`** · BEFORE UPDATE OF retracted_at · conditional

  A retraction cannot be undone.

  Refuses with: `option_expansions: a retraction cannot be reversed`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_expansions_retraction_is_final
  BEFORE UPDATE OF retracted_at ON option_expansions
  WHEN OLD.retracted_at IS NOT NULL AND NEW.retracted_at IS NULL
  BEGIN SELECT RAISE(ABORT, 'option_expansions: a retraction cannot be reversed'); END
  ```

  </details>

<a id="trg_expansions_no_delete"></a>

- **`trg_expansions_no_delete`** · BEFORE DELETE

  Expansions are never deleted; retract instead.

  Refuses with: `option_expansions are append-only: retract, do not delete`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_expansions_no_delete
  BEFORE DELETE ON option_expansions
  BEGIN SELECT RAISE(ABORT, 'option_expansions are append-only: retract, do not delete'); END
  ```

  </details>

### `concept_commentary`

Free-text community knowledge that belongs to a CONCEPT (or the locale as
a whole), not to one option: the terminology feedstock for
`legesher translate` beyond the packed word. The community row is
append-only and carries NO workflow; publishability is a MODERATION
verdict in commentary_moderation (the option_validations pattern).
Export includes a row only when its moderation row says 'published'.

**Columns**

- **`uid`** · `TEXT` · primary key

  'com_' + 24 hex, content-addressed (schema_v2.commentary_uid).

- **`contributor_id`** · `TEXT` · not null · references [`contributors`](#contributors)`(id)` on delete restrict

  Who wrote the commentary.

- **`session_uid`** · `TEXT` · references [`review_sessions`](#review_sessions)`(uid)` on delete restrict

  The session it came from, when it came from one.

- **`concept_id`** · `INTEGER` · references [`concepts`](#concepts)`(id)` on delete restrict

  NULL = locale-level commentary. Export keys by slug;
  the INTEGER id never leaves this database.

- **`locale`** · `TEXT` · not null · references [`locales`](#locales)`(tag)` on delete restrict

  The locale the commentary is about.

- **`topic`** · `TEXT` · not null

  What the commentary is about.

  Allowed values: `word_formation`, `expansion`, `register`, `pedagogy`, `style`, `general`.

- **`body`** · `TEXT` · not null

  The commentary itself. Never empty.

- **`created_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the commentary was written.

- **`retracted_at`** · `TEXT`

  Set when the contributor retracts. Final.

**Constraints**

```sql
CHECK (uid GLOB 'com_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
           || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
           || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]')
CHECK (body <> '')
```

**Indexes**

- <a id="idx_commentary_concept"></a>`idx_commentary_concept`: on `concept_id`, `locale`

- <a id="idx_commentary_locale"></a>`idx_commentary_locale`: on `locale`, `topic`

**Triggers**

<a id="trg_commentary_contributor_matches_session"></a>

- **`trg_commentary_contributor_matches_session`** · BEFORE INSERT · conditional

  The same session-contributor floor as
  [`trg_annotations_contributor_matches_session`](#trg_annotations_contributor_matches_session).

  Refuses with: `concept_commentary: contributor does not match the session contributor`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_commentary_contributor_matches_session
  BEFORE INSERT ON concept_commentary
  WHEN NEW.session_uid IS NOT NULL
   AND NEW.contributor_id <> (SELECT s.contributor_id FROM review_sessions s
                               WHERE s.uid = NEW.session_uid)
  BEGIN
      SELECT RAISE(ABORT, 'concept_commentary: contributor does not match the session contributor');
  END
  ```

  </details>

<a id="trg_commentary_append_only"></a>

- **`trg_commentary_append_only`** · BEFORE UPDATE OF uid, contributor_id, session_uid, concept_id, locale, topic, body, created_at

  Commentary is never edited; retract instead.

  Refuses with: `concept_commentary is append-only: retract, do not edit`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_commentary_append_only
  BEFORE UPDATE OF uid, contributor_id, session_uid, concept_id, locale, topic,
                   body, created_at ON concept_commentary
  BEGIN SELECT RAISE(ABORT, 'concept_commentary is append-only: retract, do not edit'); END
  ```

  </details>

<a id="trg_commentary_retraction_is_final"></a>

- **`trg_commentary_retraction_is_final`** · BEFORE UPDATE OF retracted_at · conditional

  A retraction cannot be undone.

  Refuses with: `concept_commentary: a retraction cannot be reversed`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_commentary_retraction_is_final
  BEFORE UPDATE OF retracted_at ON concept_commentary
  WHEN OLD.retracted_at IS NOT NULL AND NEW.retracted_at IS NULL
  BEGIN SELECT RAISE(ABORT, 'concept_commentary: a retraction cannot be reversed'); END
  ```

  </details>

<a id="trg_commentary_no_delete"></a>

- **`trg_commentary_no_delete`** · BEFORE DELETE

  Commentary is never deleted; retract instead.

  Refuses with: `concept_commentary is append-only: retract, do not delete`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_commentary_no_delete
  BEFORE DELETE ON concept_commentary
  BEGIN SELECT RAISE(ABORT, 'concept_commentary is append-only: retract, do not delete'); END
  ```

  </details>

### `commentary_moderation`

DERIVED moderation verdict, 1:1, regenerable: the mutable table.

**Columns**

- **`commentary_uid`** · `TEXT` · primary key · references [`concept_commentary`](#concept_commentary)`(uid)` on delete restrict

  The commentary moderated.

- **`status`** · `TEXT` · not null · default `'pending'`

  The verdict. Only `published` rows are exported.

  Allowed values: `pending`, `published`, `withheld`.

- **`moderated_by`** · `TEXT`

  Who moderated.

- **`moderated_at`** · `TEXT`

  When.

- **`note`** · `TEXT`

  The moderator's note.

### `style_ratifications`

Track 3: one reviewer's answer to one named style-profile question for a
locale. The style-guides/`<locale>`.yml generator aggregates these exactly
as canon aggregates endorsements: evidence rows here, the shipped guide is
a generated artifact, promotion is a query. Style guides remain
SUGGESTIONS; ratification records community preference, not law.

**Columns**

- **`uid`** · `TEXT` · primary key

  'sty_' + 24 hex, content-addressed (schema_v2.style_uid).

- **`contributor_id`** · `TEXT` · not null · references [`contributors`](#contributors)`(id)` on delete restrict

  The reviewer answering.

- **`session_uid`** · `TEXT` · references [`review_sessions`](#review_sessions)`(uid)` on delete restrict

  The session it came from, when it came from one.

- **`locale`** · `TEXT` · not null · references [`locales`](#locales)`(tag)` on delete restrict

  The locale the answer is for.

- **`field`** · `TEXT` · not null

  The style-profile question answered.

  Allowed values: `word_boundaries`, `constants_strategy`, `class_marker`, `modifier_order`, `abbreviation_granularity`, `identifier_length_max`, `numerals_policy`, `docstring_mood`, `terminology_policy`, `zen_preamble`.

- **`value`** · `TEXT` · not null

  The answer. Never empty.

- **`rationale`** · `TEXT`

  Why the reviewer answered this way.

- **`created_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the answer was given.

- **`retracted_at`** · `TEXT`

  Set when the reviewer retracts. Final; frees the slot in
  `uq_style_vote`.

**Constraints**

```sql
CHECK (uid GLOB 'sty_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
           || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
           || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]')
CHECK (value <> '')
```

**Indexes**

- <a id="uq_style_vote"></a>`uq_style_vote`: unique on `locale`, `field`, `contributor_id` where `retracted_at IS NULL`

  One LIVE answer per person per (locale, field); retraction frees the slot
  for a changed mind, exactly like endorsements.

**Triggers**

<a id="trg_style_contributor_matches_session"></a>

- **`trg_style_contributor_matches_session`** · BEFORE INSERT · conditional

  The same session-contributor floor as
  [`trg_annotations_contributor_matches_session`](#trg_annotations_contributor_matches_session).

  Refuses with: `style_ratifications: contributor does not match the session contributor`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_style_contributor_matches_session
  BEFORE INSERT ON style_ratifications
  WHEN NEW.session_uid IS NOT NULL
   AND NEW.contributor_id <> (SELECT s.contributor_id FROM review_sessions s
                               WHERE s.uid = NEW.session_uid)
  BEGIN
      SELECT RAISE(ABORT, 'style_ratifications: contributor does not match the session contributor');
  END
  ```

  </details>

<a id="trg_style_append_only"></a>

- **`trg_style_append_only`** · BEFORE UPDATE OF uid, contributor_id, session_uid, locale, field, value, rationale, created_at

  Ratifications are never edited; retract instead.

  Refuses with: `style_ratifications are append-only: retract, do not edit`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_style_append_only
  BEFORE UPDATE OF uid, contributor_id, session_uid, locale, field, value,
                   rationale, created_at ON style_ratifications
  BEGIN SELECT RAISE(ABORT, 'style_ratifications are append-only: retract, do not edit'); END
  ```

  </details>

<a id="trg_style_retraction_is_final"></a>

- **`trg_style_retraction_is_final`** · BEFORE UPDATE OF retracted_at · conditional

  A retraction cannot be undone.

  Refuses with: `style_ratifications: a retraction cannot be reversed`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_style_retraction_is_final
  BEFORE UPDATE OF retracted_at ON style_ratifications
  WHEN OLD.retracted_at IS NOT NULL AND NEW.retracted_at IS NULL
  BEGIN SELECT RAISE(ABORT, 'style_ratifications: a retraction cannot be reversed'); END
  ```

  </details>

<a id="trg_style_no_delete"></a>

- **`trg_style_no_delete`** · BEFORE DELETE

  Ratifications are never deleted; retract instead.

  Refuses with: `style_ratifications are append-only: retract, do not delete`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_style_no_delete
  BEFORE DELETE ON style_ratifications
  BEGIN SELECT RAISE(ABORT, 'style_ratifications are append-only: retract, do not delete'); END
  ```

  </details>

### `message_endorsements`

DEFERRED (like the message tables above): endorsements for message
translations, activated with the messages track. Before these are ever
PUBLISHED, message_translations must first gain content-addressed keys:
its AUTOINCREMENT id has exactly the rebuild-renumbering hazard options.uid
exists to prevent.

**Columns**

- **`uid`** · `TEXT` · primary key

  'men_' + 24 hex.

- **`message_translation_id`** · `INTEGER` · not null · references [`message_translations`](#message_translations)`(id)` on delete restrict

  The message translation endorsed.

- **`contributor_id`** · `TEXT` · not null · references [`contributors`](#contributors)`(id)` on delete restrict

  Who endorsed it.

- **`session_uid`** · `TEXT` · references [`review_sessions`](#review_sessions)`(uid)` on delete restrict

  The session it came from, when it came from one.

- **`method`** · `TEXT` · not null

  How the endorsement reached us; same vocabulary as
  [`endorsements.method`](#endorsements).

  Allowed values: `portal`, `survey`, `workshop`, `github`, `interview`, `import`.

- **`rung_at_endorsement`** · `TEXT` · not null · references [`review_rungs`](#review_rungs)`(rung)`

  Snapshot of the endorser's rung at the time. Immutable evidence.

- **`comment`** · `TEXT`

  The endorser's free-text comment.

- **`created_at`** · `TEXT` · not null · default `(datetime('now'))`

  When the endorsement was made.

- **`retracted_at`** · `TEXT`

  Set when the endorser retracts. Final.

**Constraints**

```sql
CHECK (uid GLOB 'men_[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
           || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'
           || '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]')
```

**Indexes**

- <a id="uq_message_endorsement_once"></a>`uq_message_endorsement_once`: unique on `message_translation_id`, `contributor_id` where `retracted_at IS NULL`

**Triggers**

<a id="trg_message_endorsements_append_only"></a>

- **`trg_message_endorsements_append_only`** · BEFORE UPDATE OF uid, message_translation_id, contributor_id, session_uid, method, rung_at_endorsement, created_at

  Message endorsements are never edited; retract instead.

  Refuses with: `message_endorsements are append-only: retract, do not edit`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_message_endorsements_append_only
  BEFORE UPDATE OF uid, message_translation_id, contributor_id, session_uid,
                   method, rung_at_endorsement, created_at ON message_endorsements
  BEGIN SELECT RAISE(ABORT, 'message_endorsements are append-only: retract, do not edit'); END
  ```

  </details>

<a id="trg_message_endorsements_retraction_is_final"></a>

- **`trg_message_endorsements_retraction_is_final`** · BEFORE UPDATE OF retracted_at · conditional

  A retraction cannot be undone.

  Refuses with: `message_endorsements: a retraction cannot be reversed`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_message_endorsements_retraction_is_final
  BEFORE UPDATE OF retracted_at ON message_endorsements
  WHEN OLD.retracted_at IS NOT NULL AND NEW.retracted_at IS NULL
  BEGIN SELECT RAISE(ABORT, 'message_endorsements: a retraction cannot be reversed'); END
  ```

  </details>

<a id="trg_message_endorsements_no_delete"></a>

- **`trg_message_endorsements_no_delete`** · BEFORE DELETE

  Message endorsements are never deleted; retract instead.

  Refuses with: `message_endorsements are append-only: retract, do not delete`

  <details><summary>Definition</summary>

  ```sql
  CREATE TRIGGER trg_message_endorsements_no_delete
  BEFORE DELETE ON message_endorsements
  BEGIN SELECT RAISE(ABORT, 'message_endorsements are append-only: retract, do not delete'); END
  ```

  </details>

### `latest_rankings`

*View.*

Each contributor's LATEST accepted session per (concept, locale, pl_scope):
the ranking set that counts. Deterministic on ties (submitted_at, then
uid). Enforces its own contract: a ranking whose endorsement was later
retracted is stranded evidence and is excluded here, not left for every
consumer to remember to filter.

<details><summary>Definition</summary>

```sql
CREATE VIEW latest_rankings AS
WITH scoped AS (
    SELECT
        r.session_uid, r.concept_id, r.locale, r.pl_scope, r.option_uid,
        r.rank, r.revised_after_reveal, r.comment,
        s.contributor_id, s.submitted_at,
        DENSE_RANK() OVER (
            PARTITION BY s.contributor_id, r.concept_id, r.locale, r.pl_scope
            ORDER BY s.submitted_at DESC, s.uid DESC
        ) AS session_recency
    FROM session_rankings r
    JOIN review_sessions s ON s.uid = r.session_uid
    WHERE s.status = 'accepted'
      AND EXISTS (
          SELECT 1 FROM endorsements e
          WHERE e.option_uid = r.option_uid
            AND e.contributor_id = s.contributor_id
            AND e.retracted_at IS NULL
      )
)
SELECT session_uid, contributor_id, concept_id, locale, pl_scope,
       option_uid, rank, revised_after_reveal, comment, submitted_at
FROM scoped
WHERE session_recency = 1
```

</details>

### `option_promotion_status`

*View.*

Promotion check per option: a THIN layer over option_standings, adding
exactly two things: the native-endorser threshold and canon-eligibility
mirrored from trg_canon_requires_valid_identifier (identifier_valid AND
script_consistent AND format_chars_clean AND (nfkc_stable OR
sara-am-only)). Thresholds live here, in one place (Q5 recommendation:
>=2 native, zero open flags).

<details><summary>Definition</summary>

```sql
CREATE VIEW option_promotion_status AS
SELECT
    s.concept_slug,
    s.locale,
    s.pl_scope,
    s.option_uid,
    s.surface_form,
    s.endorsements,
    s.weighted_endorsement,
    s.native_verified_or_above,
    s.open_flags,
    s.standing,
    (s.identifier_valid = 1
     AND s.script_consistent = 1
     AND s.format_chars_clean = 1
     AND (s.nfkc_stable = 1 OR s.nfkc_delta_class = 'sara-am-only'))
                                        AS canon_eligible,
    (s.withdrawn_at IS NULL
     AND s.native_verified_or_above >= 2
     AND s.open_flags = 0
     AND s.identifier_valid = 1
     AND s.script_consistent = 1
     AND s.format_chars_clean = 1
     AND (s.nfkc_stable = 1 OR s.nfkc_delta_class = 'sara-am-only'))
                                        AS reviewed_eligible
FROM option_standings s
```

</details>

### `second_endorsement_queue`

*View.*

The one-endorsement-away queue: what the app shows a locale's NEXT
reviewer first. Live, canon-eligible options one native endorsement short
of the reviewed bar.

<details><summary>Definition</summary>

```sql
CREATE VIEW second_endorsement_queue AS
SELECT concept_slug, locale, pl_scope, option_uid, surface_form,
       native_verified_or_above, endorsements
FROM option_promotion_status
WHERE reviewed_eligible = 0
  AND canon_eligible = 1
  AND open_flags = 0
  AND native_verified_or_above = 1
```

</details>

### `quarantine_queue`

*View.*

The maintainer lens on quarantine (CORE-1828): what the import ritual walks.
Standings deliberately cannot see these rows; this view is where they wait.

<details><summary>Definition</summary>

```sql
CREATE VIEW quarantine_queue AS
SELECT
    q.option_uid,
    c.slug          AS concept_slug,
    o.locale,
    o.pl_scope,
    o.surface_form,
    q.verdict,
    q.screened_by,
    q.screen_version,
    q.note,
    q.screened_at
FROM option_screening_status q
JOIN options o  ON o.uid = q.option_uid
JOIN concepts c ON c.id = o.concept_id
WHERE q.verdict <> 'cleared'
```

</details>

### `pack_promotion_status`

*View.*

The experimental -> official gate per (PL x locale) as a query. Threshold
numbers pending ratification; the gate reads THIS view so re-cutting is
one place.

<details><summary>Definition</summary>

```sql
CREATE VIEW pack_promotion_status AS
SELECT
    lp.programming_language,
    lp.locale,
    lp.concepts_needed,
    lp.concepts_selected,
    lp.concepts_reviewed,
    lp.concepts_official,
    (SELECT COUNT(DISTINCT s.contributor_id)
       FROM review_sessions s
       JOIN review_rungs rr ON rr.rung = s.rung_at_session
      WHERE s.locale = lp.locale
        AND s.track = 'reserved_words'
        AND s.status = 'accepted'
        AND rr.counts_as_native = 1)                          AS native_reviewers,
    (SELECT COUNT(DISTINCT s.contributor_id)
       FROM review_sessions s
      WHERE s.locale = lp.locale
        AND s.track = 'reserved_words'
        AND s.status = 'accepted')                            AS total_reviewers,
    (SELECT COUNT(DISTINCT sr.field)
       FROM style_ratifications sr
      WHERE sr.locale = lp.locale AND sr.retracted_at IS NULL) AS style_fields_answered,
    (lp.concepts_selected = lp.concepts_needed)               AS fully_selected,
    CAST(lp.concepts_reviewed AS REAL) / NULLIF(lp.concepts_needed, 0) AS reviewed_ratio
FROM locale_progress lp
```

</details>

### `terminology_export`

*View.*

Terminology export for `legesher translate`: per (concept x locale), the
canon word plus alternates, descriptors, and the most-attested expansion:
the "how else is this concept expressed" layer prompt assembly injects.
Published commentary joins by concept slug in the exporter. Rows whose
ONLY provenance is a non-redistributable import_source are excluded by the
EXPORTER (this view is also the maintainers' internal lens, so it stays
unfiltered).

Quarantined submissions must not surface as terminology alternates either
(CORE-1828): this view feeds `legesher translate` prompt assembly.

<details><summary>Definition</summary>

```sql
CREATE VIEW terminology_export AS
SELECT
    c.slug                        AS concept_slug,
    o.locale,
    o.pl_scope,
    o.surface_form,
    (cs.option_uid = o.uid)       AS is_canon,
    cs.status                     AS canon_status,
    ec.endorsements,
    ec.native_verified_or_above,
    (SELECT GROUP_CONCAT(a.kind)
       FROM option_annotations a
      WHERE a.option_uid = o.uid AND a.retracted_at IS NULL)  AS descriptors,
    (SELECT x.expansion
       FROM option_expansions x
      WHERE x.option_uid = o.uid AND x.retracted_at IS NULL
      GROUP BY x.expansion
      ORDER BY COUNT(*) DESC, MIN(x.created_at) ASC
      LIMIT 1)                                                AS expansion
FROM options o
JOIN concepts c             ON c.id = o.concept_id
LEFT JOIN endorsement_counts ec ON ec.option_uid = o.uid
LEFT JOIN canon_selections cs
       ON cs.concept_id = o.concept_id
      AND cs.locale = o.locale
      AND cs.pl_scope = o.pl_scope
WHERE o.withdrawn_at IS NULL
  AND NOT EXISTS (
      SELECT 1 FROM option_withheld q WHERE q.option_uid = o.uid
  )
```

</details>

### `transliteration_preference`

*View.*

Transliteration revealed-preference per locale: the aggregate the
annotation exists to measure, and the input to a terminology_policy
conversation with that locale's community.

<details><summary>Definition</summary>

```sql
CREATE VIEW transliteration_preference AS
SELECT
    o.locale,
    COUNT(DISTINCT o.uid)                                     AS live_options,
    COUNT(DISTINCT a.option_uid)                              AS options_tagged_translit,
    COUNT(DISTINCT CASE WHEN e.retracted_at IS NULL
                        THEN e.uid END)                       AS endorsements_on_translit
FROM options o
LEFT JOIN option_annotations a
       ON a.option_uid = o.uid AND a.retracted_at IS NULL AND a.kind = 'transliteration'
LEFT JOIN endorsements e
       ON e.option_uid = a.option_uid
WHERE o.withdrawn_at IS NULL
GROUP BY o.locale
```

</details>

## The SQL file's header

The only prose `schema_v2.sql` may carry besides its section banners,
reproduced so that nothing the SQL says is missing from this page.

~~~~text
===========================================================================
Legesher translations schema v2 (CORE-1501): concept-centric, with an
endorsement corpus.

Structure only. What every table, column, trigger and view is for lives in
schema_v2.descriptions.yml beside this file; the two are rendered together
into libs/i18n/docs/schema-v2-reference.md by `make generate-schema-reference`,
which fails when they disagree or when a comment appears here outside this
header and the section banners.

Requires SQLite >= 3.31 (STORED generated columns). Verified on 3.51.
===========================================================================
~~~~
