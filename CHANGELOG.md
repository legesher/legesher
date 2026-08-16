# Changelog - Legesher Monorepo

All notable changes to the Legesher project are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## [Unreleased]

### Fixed

- **i18n**, **cli**: both shipped CLIs and the language-pack validator crashed
  on Windows while reporting their own results. Windows Python does not default
  `sys.stdout` to UTF-8; piped — which is what a pre-commit hook, a subprocess
  and a CI step all hand it — it falls back to the machine's ANSI code page,
  where the status markers these tools print (`✅`, `❌`, `→`) have no mapping.
  `legesher-i18n validate` and the pack validator therefore ran every check,
  passed, then died on the line that says so. A valid pack exited 1 with an
  empty stdout, so the commit hook reported it invalid; an invalid one printed
  no errors at all, because the same crash landed on the line that prints them
  — leaving a contributor with a traceback about a code page instead of the
  collision they needed to fix. Entry points now reconfigure stdio to UTF-8
  with `errors="replace"`, so a console that genuinely cannot render a glyph
  degrades to `?` rather than aborting: no output statement should ever be the
  thing that kills the process. [CORE-1927]

## [0.23.0] - 2026-08-16

> **On the version number.** This release carries breaking changes and is
> still a minor bump. The foundation is pre-1.0 and stays there until 1.0 is
> declared deliberately — `major_on_zero = false` on the foundation and on
> `libs/mcp`, though not on the packs, which version independently. A 1.0
> foundation is a coordinated 56-package change: all 51 language packs pin
> `legesher-i18n<1.0.0`, and so do `core`, `legesher`, `mcp`,
> `language-server` and `runtime`. Never an incidental consequence of a
> commit marker. Breaking items are called out in place below.

### Added

- **mcp**: `legesher-mcp` releases on its own train — own semantic-release
  config, `mcp-v{version}` tags, and `release-mcp.yml` on `libs/mcp/**` —
  instead of having no versioning at all. Pre-1.0 breaking changes bump the
  minor rather than jumping to 1.0.0. The release-tier suites gate the
  version step, so the clean-environment wheel spawn test now blocks a
  release rather than living in a checklist. `libs/mcp` tests also join the
  CI test job, which had never run them. [CORE-1851]
- **core**: `legesher map compact` garbage-collects translation-memory
  segments whose register-map node is gone. Such segments could never be
  returned by an exact lookup (node IDs are never reused) but stayed in the
  artifact forever, surfacing in fuzzy suggestions and growing the committed
  file over a repo's life. They are now demoted to history rather than
  deleted — a deleted docstring often returns, and its old translation is
  then the best suggestion available — and the history is capped
  (`--keep-history`, default 200), which is what actually bounds the file.
  Live segments are untouched, so replay output is unchanged. `--dry-run`
  reports without writing. [CORE-1708]
- **core**: `legesher map edit --dry-run` prints the full would-edit report
  and writes nothing. Bulk-by-name is the default — passing an identifier
  edits every entry with that source text across every file — so there is
  now a way to see the blast radius first. [CORE-1771]
- **core**: the mapping log emits `deprecate` when a node dies. Reconcile
  dropped nodes silently, so the lineage changelog recorded every birth and
  no ending; `lineage()` now shows a node's full life. `lineage_for_term`
  also follows rename chains end-to-end, so a term's history is reachable
  from any name it has held. [CORE-1770]
- **mcp**: pre-remote hardening of the stdio server. Pack availability is
  refreshable (TTL plus an explicit `refresh_packs()`) instead of computed
  once per process; the `python_version` enum published in every tool schema
  is derived from the installed packs' version index rather than
  hand-maintained; the English pivot is computed once per file in
  `explain_in_language` and `map_existing_codebase` instead of twice on
  non-English input; and `legesher://languages/{lang}/terms/{python_version}`
  exposes a dictionary at a chosen grammar [CORE-1806]. All five tools now
  declare `readOnlyHint` / `idempotentHint` / `openWorldHint: false`
  annotations matching their actual posture, locked by a surface test
  [CORE-1814].
- **mcp**: argument-validation failures speak in the server's own voice
  (`invalid_arguments: <field> — <constraint>`) rather than the SDK's raw
  pydantic dump, which quoted the rejected value back — for the `source`
  fields that meant a prefix of the caller's code appeared in the error.
  Unexpected failures collapse to a generic `internal_error` instead of an
  exception message that can carry filesystem paths. [CORE-1744]
- **mcp**: release-tier test suites behind `make test-mcp-scheduled` — an
  all-packs round-trip sweep through an MCP session [CORE-1745] and a
  clean-environment spawn test that installs locally built wheels into a
  fresh virtualenv and drives a stdio session with a stripped environment,
  which is the publish gate for the artifact [CORE-1746]. Also direct
  `LocalEngine` unit tests covering the defensive and sanitization branches,
  plus concurrency coverage for the translator cache and the engine
  singleton [CORE-1815], and a protocol edge sweep [CORE-1744].
- **i18n**: style guides can declare how terms are *coined*, not just how
  they are cased. The new optional `naming.word_formation` list carries
  word-formation rules (compounding, clipping, which roots stay distinct)
  and renders into the translation prompt's Naming Conventions section.
  First user is the Sinhala guide at 0.2.0, harvested from the first
  native-speaker review of the si pack: four word-formation rules plus two
  script-profile lines covering spaceless-compound garden-path risk and
  Sinhala's SOV/postpositional word order. Rules only — vocabulary stays in
  the packs. [CORE-1706]
- **docs**: shareable playground — playground state now lives in the URL
  (`?code=<base64url>&src=en&tgt=<lang>&sample=<slug>`, with a Copy link
  button), so any language × example combination is a pasteable link,
  sample context included; a Show English toggle
  renders the canonical view with true two-way translation (untouched round
  trips restore the localized source byte-for-byte); six curated samples on
  a difficulty ladder (hello world → async/await) generated from canonical
  sources, with localized identifiers for es/fr/de/pt/it/tr/id pending
  native review (other languages keep English identifiers); localized
  buffers now highlight exactly like English — keywords, builtins and
  definition names take the same colors via pack-driven decoration, all 51
  packs, no per-language theming. [CORE-1696]

- **mcp**: agent-session artifacts for localized code — the
  `AGENTS-template.md` language-policy declaration (copy into a repo as
  `AGENTS.md`; read by Codex, Cursor, Claude Code, Antigravity, Windsurf)
  and the `legesher-localized-code` skill (Agent Skills format, portable
  across Claude surfaces) carrying the stable playbook: canonical ↔ native
  mental model, tool selection, write → round-trip → validate workflow,
  and one-concept-one-term naming backed by a project glossary. The policy
  file and skill are the declaration/playbook half; the server's
  deterministic tools remain the guarantee.
- **mcp**: new `legesher-mcp` package (`libs/mcp`, Apache-2.0) — the engine's
  translation capability as a Model Context Protocol stdio server, per the
  CORE-1165 architecture design. Five coarse tools (`translate_to_native`,
  `translate_to_source`, `explain_in_language`, `lookup_keyword_mapping`,
  `map_existing_codebase`), `legesher://` resources for the language catalog
  and per-language dictionaries, and three prompt templates. Runs entirely
  against the local engine: no network calls, no account, no telemetry.
  X→Y translation pivots through English and reports `pivoted`; validation
  is `compile()`-only; tool errors are machine-coded and content-free.
  `uvx legesher-mcp` / `uv run legesher-mcp` start it; official `mcp` SDK
  pinned; 36 tests through the MCP layer. [CORE-1175]
- **i18n**: client-shape pack emitter — `scripts/emit_js_client_pack.py`
  renders a locale's canonical selections into the `@legesher/core`
  `LanguagePack` TypeScript artifact for vendoring into `js-engine-repo`.
  Registry-driven metadata, fail-loud completeness (partial packs are never
  emitted), deterministic byte-identical output with the source commit
  pinned in the generated header. [CORE-1371]
- **i18n**: Arabic translations for the full 62-term JavaScript (JEJ)
  surface — 17 keywords, 16 builtins, 29 members — recorded in
  `translations.db` with per-term rationale and selected through the
  publish gate. Bare-form convention; 11 keywords pre-seeded from the
  shipped Python `ar` pack for cross-target consistency; the curation
  table and its pre-write gates live in `scripts/record_js_ar_terms.py`.
  Includes one cross-target correction: Python `ar` `while` becomes
  `طالما` ("as long as", was `حتى` "until"). [CORE-1371]
- **i18n**: the translation pipeline is target-aware and the JavaScript
  inventory is seedable. `scripts/seed_js_terms.py` materializes the 62-term
  JEJ surface from the context-corpus index into `translations.db`
  (`programming_language='javascript'`, target-neutral `keyword`/`builtin`/
  `member` categories; validates the 17/16/29 split before writing, refuses
  re-seeding, `--dry-run`). `run_pipeline.py --target javascript` sources
  its inventory from the seeded DB (python keeps the term_classifier path
  byte-for-byte), threads the target into the PromptBuilder so the
  CORE-1608 Target Guide fires, and writes term rows only for pre-seeded
  terms — the pipeline never invents a term for a non-python target.
  `TERM_TYPE_YAML_SECTIONS` maps the new categories (`member` → the
  CORE-1582 `members` partition). [CORE-1371]
- **i18n**: the pack schema gains a first-class `members` partition (MLCP
  extended field) — member/property-name translations, labels bounded by
  their receiver, for member-bearing targets such as JavaScript. Members
  ride every safety check (they joined `_TRANSLATION_SECTIONS`), enforce
  in-partition uniqueness in the duplicate audit, and are deliberately
  EXCLUDED from the cross-section collision pass: a member value matching a
  keyword value is a legal homonym (the receiver disambiguates), not a
  reversibility break. The loader carries `members` through construction and
  `extends` inheritance; Python packs load with an empty mapping, behavior
  unchanged (full suite 1516 green). Unblocks populating the Arabic
  JavaScript pack's members in generation. [CORE-1582]
- **i18n**: `of` and `log` join the JavaScript/JEJ context corpus — 60 → 62
  Tier-1 briefs, following the engine-side surface widening to 17 keywords /
  29 members (js-engine-repo, CORE-1571) now that the key-set is Legesher-owned.
  Each brief encodes its term's load-bearing constraint: `of` must stay
  distinct from `in` (Python spells value-iteration with "in," while
  JavaScript's `in` is key presence, and both live in the collision-gated
  keywords partition), and `log` is the record/write verb, never the
  logarithm (`Math.log` shares the spelling; the receiver disambiguates,
  mirroring English). `index.json` and the corpus README move to the
  Legesher-owned 17/16/29 accounting with the remaining `console.*` methods
  documented as held pending the trial module's confirmed usage (CORE-1609).
  [CORE-1571]
- **i18n**: generation prompts are target-aware. `spec/targets/javascript/`
  ships the first per-programming-language profile — `profile.json` (version
  grammar `^es\d{4}$`, the keywords/builtins/members partitions, identifier
  grammar including Arabic script, contextual keywords) plus a `GUIDE.md`
  rendered into prompts as a "Target Guide" section — loaded by the new
  `TargetProfileLoader` and consumed by `PromptBuilder` through an optional
  `target=` parameter. Substitution is pure data (display name, identifier
  rule, casing rule); no `if target ==` branch exists anywhere, and a target
  without a spec directory keeps the historical wording byte-for-byte —
  verified empirically at 154/154 prompt pairs across all 51 languages for
  the default python target. Unblocks Arabic JavaScript pack generation from
  inheriting Python-flavoured guidance (snake_case instincts, Python's
  exception taxonomy, no notion of members). [CORE-1608]
- **i18n**: concept-centric v2 translations schema. The unit of translation
  becomes a concept rather than a spelling in one language, so a new
  programming language maps its words onto existing concepts and inherits every
  reviewed translation across all 56 locales instead of re-running translation
  and review from scratch. `db/schema_v2.sql` / `schema_v2.py` add a corpus
  layer — every term a native speaker offers, one row per endorsement, counts
  derived — held structurally apart from the canon, which may only ratify an
  option the corpus already carries. Identity is content-addressed rather than
  autoincrement: `option_uid` is a truncated SHA-256 over concept, locale, PL
  scope, and the NFC surface form, so rebuilding the database from files cannot
  re-key the endorsements a speaker attached to a published dataset.
  `contributor_id` is `c_` + HMAC-SHA256(salt, GitHub username); the username
  lives only in the never-exported `contributor_identities` table, and
  `--publish` refuses a missing, short, or dev salt before it builds anything.
  `connect()` enables `PRAGMA foreign_keys` and `PRAGMA recursive_triggers`,
  the latter being what stops `INSERT OR REPLACE` slipping past the
  append-only triggers. `scripts/migrate_to_v2.py` reads v1 read-only: 16,710
  translations become 11,335 options plus 16,710 provenance rows, with
  `translations.db` unchanged (MD5 verified). [CORE-1501]
- **i18n**: HF corpus exporter. `scripts/export_corpus.py` renders a v2
  database into the five Parquet configs of the `legesher/language-corpus`
  dataset — `concepts`, `terms`, `options`, `endorsements`, `contributors` —
  plus a dataset card and a `reconciliation.json` ledger. It reads the corpus
  layer only: `canon_selections` and `contributor_identities` are excluded
  structurally, with a `NEVER_EXPORT` gate asserted against every config's SQL
  and a post-write audit that reopens each Parquet file and unlinks it if a
  `source_detail`, `source_key`, `display_name`, or `comment` column shipped.
  `options` carries its validation findings as columns, turning the audit into
  per-row review data. Arrow schemas are pinned per config so an all-NULL
  column cannot export as type `null` and change type on a later revision.
  Endorsement counts stay derived, never stored, and the ledger cross-checks
  per-config row counts against the `endorsement_counts` view, exiting nonzero
  on mismatch. Nothing is pushed here or in CI: `--push` requires both
  `--governance-signoff CORE-1502` and `LEGESHER_HF_PUSH_APPROVED=1`, and
  creates the repo with `private=True`, never flipping visibility. [CORE-1505]
- **i18n**: JavaScript/JEJ term-context corpus — one Tier-1 translation brief
  per term of the JEJ teaching surface at `context/javascript/`, mirroring the
  existing `context/python/` corpus: 60 briefs (16 keywords, 16 builtins, 28
  members, matching the upstream courseware surface at `0fca239`), plus
  `index.json` and a corpus README. Each brief records the uniqueness rule that
  governs its term — standalone for the 32 keywords and builtins, qualified for
  the 28 members — and every member brief carries the term's full receiver set
  with an AST-decided definition (non-computed `MemberExpression.property`, not
  dot-adjacency), so a chosen word survives String→Array widening. `toString`
  and `valueOf` are pre-flagged for native review (English hides the
  radix-conversion vs date-text gap); `log` and `of` are deliberately absent,
  held pending the partner decision. [CORE-1370]
- **i18n**: JEJ message-template seed and append-once seeder — the v2
  `message_templates` / `message_translations` tables shipped empty, and this
  is their fill path. `db/seeds/v8_jej_messages.json` carries a 35-template JEJ
  learner-facing catalog across 10 consistency clusters, with generic
  `jej.<id>` keys (English is never the key), the DDL's full identity tuple,
  declared placeholder contracts, and draft Arabic entering at
  `status='machine'` pending native review. `scripts/seed_message_templates.py`
  validates before any write — placeholder parity on every surface, zero stored
  bidi controls (isolation is render-time), locales must pre-exist rather than
  being created as a side effect — and refuses to re-seed an existing
  (`implementation`, `version_added`) set, so a reworded template lands as a new
  `version_added` instead of invalidating shipped translations. [CORE-1378]
- **docs**: localized documentation site — Spanish (`/es/`) and Arabic (`/ar/`)
  locales with translated prose, RTL layout for `ar`, and a language picker.
  Code samples are generated from the language packs at build time via
  span-driven highlighting, so every snippet shows the reader's own keywords
  instead of a hand-maintained copy. [CORE-1548, CORE-1549, CORE-1553]
- **docs**: in-browser Python playground — edit and run localized code from the
  docs, via a Pyodide web worker with a CodeMirror editor island. [CORE-1551]

### Changed

- **language-server**: enhanced Python intelligence no longer calls itself
  Pylance. The proxy has never launched Microsoft's Pylance and never will —
  its licence grants use only with Microsoft products and forbids standalone
  redistribution, and its bundled server does not speak plain `--stdio` in any
  case. The backend is `pyright-langserver` (Apache-2.0). Naming it after a
  product we deliberately do not run was misleading to anyone reading the code
  or the settings, so the configuration is renamed to say what it does:
  `pylance_enabled` becomes `enhanced_intelligence_enabled`, `pylance_path`
  becomes `language_server_path`, and the environment variables
  `LEGESHER_PYLANCE_ENABLED` / `LEGESHER_PYLANCE_PATH` become
  `LEGESHER_ENHANCED_INTELLIGENCE_ENABLED` / `LEGESHER_LANGUAGE_SERVER_PATH`.
  `PylanceProxy` is now `EnhancedIntelligenceProxy`, in
  `legesher_language_server.enhanced_intelligence`. Diagnostics produced by the
  backend are now sourced as `pyright` rather than `pylance`, which is what
  actually produced them. **These are breaking renames with no aliases**: the
  package has not been published, so nothing external can depend on the old
  names and carrying a deprecation layer for them would be debt with no
  debtor. [CORE-1890]

- **i18n**: the Hugging Face corpus dataset publishes to
  `legesher/language-corpus`. It was `legesher/translations`, and briefly
  `legesher/language-packs` before that name was reserved for the other
  artifact: the corpus is the *evidence* — every term a speaker offered, with
  endorsements and provenance, including the ones that were not chosen — while
  the canon dataset is the *decision*, the words that actually ship. Someone
  fetching `legesher/language-packs` should get shipped vocabulary, not the
  11,335 candidate options the corpus carries, so the pair now reads
  `language-corpus` / `language-packs`. **A breaking rename with nothing to
  migrate**: no artifact was ever pushed under any prior name. Scoped to the
  `legesher/` prefix, so the `libs/i18n/language-packs/` source directory and
  the local `~/.legesher/translations.db` path are untouched. [CORE-1312]
- **i18n**: `options.sources` is cut on **obligation** rather than pipeline
  origin. It is the only provenance column the corpus publishes —
  `source_detail` stays private — so its vocabulary is a public promise, and
  the old cut put 13,650 rows in an `import` grab-bag holding our own packs,
  curated corrections, superseded pack words *and* two other projects' work.
  Nothing in the published data said "someone else's licence applies here",
  which is how UniversalPython (24 rows) and Latino (11 rows) sat unattributed.
  Each bucket now answers what we owe for a row: `legesher` (our own work —
  nothing beyond the licence), `upstream` (another open-source project — retain
  their notice, credit them), `community` (an individual via native review —
  credit and withdrawal on request), `model` (machine-generated — disclose
  which model). Two reassignments worth knowing: `machine-composed` rows go to
  `legesher`, not `model`, because a human assembled them from existing pack
  material; and 2,169 legacy `community` rows become `upstream`, because what
  is owed there is a repository's notice rather than a person's credit — and a
  licence notice is not ours to drop on request. **A breaking change to the
  published `sources` vocabulary, with nothing yet published to break.**
  Per-bucket row counts are deliberately omitted: they are a snapshot of an
  uncommitted build and drift between rebuilds, and a changelog is permanent.
  [CORE-1720]
- **i18n**: provider prices are now **operator-configured, never shipped**.
  Every provider carried a hardcoded rate — `$3`/`$15` per million tokens for
  Anthropic, `$20` per million characters for Google and DeepL, and so on —
  which is wrong the moment a provider updates a price list, quietly and by a
  ratio nobody notices. Prices also differ by contract and region, so there is
  no figure that is right for everyone. Rates now come from
  `LEGESHER_RATES_FILE` or `LEGESHER_RATE_<PROVIDER>_<UNIT>` environment
  variables, and **an unconfigured rate reports `None`, not `0.0`** — a
  confident wrong number is worse than an absent one, because absent invites
  you to go look. A half-configured rate (input price but no output price)
  also reports unknown rather than under-reporting, which is the failure a
  budget guard can least afford. Usage itself — requests, characters, tokens —
  is measured exactly as before; only the price is withheld.
  `UsageStats.cost_estimate_usd` and `UsageRecord.cost_usd` are now optional,
  and the usage table's `cost_usd` column is nullable. [CORE-1863]

- **core**: `.legesher/` artifacts normalize text to **LF line endings, then
  NFC** at extraction (contract change). Previously NFC alone was applied,
  and since it does not touch line endings, `content_hash("a\nb")` differed
  from `content_hash("a\r\nb")` — so a Windows checkout with
  `core.autocrlf=true` missed every multi-line translation-memory segment
  and re-anchored every multi-line map node, silently, on files nobody had
  edited. Node identity is now a property of content rather than of the
  checkout, and the committed artifact is byte-identical whoever wrote it.
  Artifacts holding CRLF text re-anchor once on the next reconcile, keeping
  their IDs and translations, and are stable after. U+2028/U+2029/U+0085 are
  treated as content and survive verbatim. [CORE-1710]
- **core**: artifact writes are atomic (temp file + `os.replace`). Every
  writer previously truncated the destination before writing, so a crash
  mid-write left a truncated, unparseable artifact where a valid one had
  been. [CORE-1710]
- **core**: the deterministic emission path decides whether a stored
  translation is its own stale leftover from **entry-level provenance**
  (`written_by`) rather than by inspecting the value. The previous heuristic
  held only while every identifier-layer translation was pack-validated,
  which is not guaranteed: it could delete an identifier translation that
  merely resembled a reserved word, and could leave a genuinely stale one in
  place when re-emitting through a translator with no reserved-word map.
  Register-map schema `1.1.0 → 1.2.0` (additive; older artifacts migrate on
  load). [CORE-1767]
- **core**: `suggest()` is ~12.5× faster at 10k segments (495 ms → 40 ms per
  call) via a length-band and `quick_ratio()` cascade. Both gates are exact
  upper bounds on the similarity score, so results are unchanged. Very short
  segments now need a higher score to be suggested, which drops noise like
  `# step 1` vs `# step 2` while keeping genuine typo fixes. [CORE-1709]
- **core**: `legesher map edit --lang` is validated — an unknown code is
  rejected instead of minting a rendering for a language that does not
  exist. Editing a comment/docstring/string entry now requires `--prose`,
  making the weaker prose validation explicit rather than silently inherited
  from the node's class. Pack `members` joined the collision domain. [CORE-1771]

- **i18n**: the tooling that could silently corrupt translated terms is retired.
  Two orphaned "fixer" scripts rewrote pack values in place with *contradictory*
  conventions — one deleted spaces, the other replaced them with underscores —
  and both had run, which is the mechanical origin of the mixed joining
  convention still visible in the packs (`ar` 3 underscore / 67 bare in
  exceptions; `he` 18 / 52). Neither was referenced by CI, pre-commit, or any
  Makefile; both are deleted rather than deprecated. The guidance that
  reproduced the damage is corrected in the same pass: the space error in
  `scripts/translate/validators.py` interpolated `translation.replace(' ', '')`
  and handed the caller a finished concatenated string, so anyone following it
  recreated the corruption exactly — it now states the constraint and points at
  the language's declared convention without prescribing a remedy, and the test
  that asserted on the concatenated output (pinning the destructive behavior) is
  inverted to reject it. `validate_language_pack_yaml.py` no longer claims that
  "RTL scripts (ar, he): Concatenate without separators (Arabic/Hebrew naturally
  connect)" — Arabic and Hebrew letters join *within* a word as a rendering
  property, which says nothing about deleting boundaries *between* words, and
  the false premise had been used to justify destroying word separation in the
  two worst-affected languages. Validation *behavior* is unchanged; no pack
  value is touched. Five standing constraints on agent-run data migrations are
  recorded in `libs/i18n/CLAUDE.md`. [CORE-1713]

- **i18n**: every `languages.bcp47` row now carries a registry-canonical tag.
  The reviewed backfill is applied — three corrections (`sr` → `sr-Cyrl`,
  `uz` → `uz-Latn`, `mn` → `mn-Cyrl`, each matching the script the pack
  actually uses) and five NULL-fills (`ne`, `sw`, `uk`, `xh` bare tags,
  `tl` → `fil`) — leaving zero NULLs across the 56 rows. It lands before the
  publish-grade corpus build because the v2 migration derives each option's
  locale from this column, so a wrong tag would freeze into the published
  dataset. Applied by `scripts/apply_bcp47_backfill.py`: dry-run unless
  `--apply`, re-validates every TSV tag against the vendored IANA registry,
  refuses `needs_review=yes` rows, writes in one transaction, and audits the DB
  against the TSV afterwards; a full `.dump` diff confirms exactly 8 `bcp47`
  cells changed and nothing else. `languages.json` and the VS Code
  `languages.ts` are regenerated, the `mn`/`sr`/`uz` pack `REFERENCE.md`
  language tables are corrected to match, and new `TestBackfillApplied` guards
  pin DB against TSV and every pack's "BCP 47 Tag" row against the DB column.
  The language key (`code`) is unchanged. [CORE-1512]
- **i18n**: the pack audit gates are target-aware. `audit_packs.py` and
  `audit_collisions.py` take a `--target` flag (`python`/`javascript`, default
  `python`) and no longer hard-code `language-packs/python` — packs root,
  discovery glob, and package-dir name all follow the target. The two
  Python-only checks are switched off for other targets: the cross-partition
  collision pass (CPython's `tokenize` dispatches flat, so a value shared across
  partitions round-trips to the wrong token) and the CPython-XID
  `check_min_interpreter_identifier`. `validate_pack_strict` takes neutral
  `run_min_interpreter` / `run_cross_section` toggles and never branches on the
  target itself — the caller supplies them. Intra-partition reversibility still
  runs for every target, and the Python audit is unchanged (255 packs, 0 errors;
  51 packs, 0 collisions). Keyword and identifier profiles stay Python-shaped
  until CORE-1503. [CORE-1372]
- **i18n**: the Sinhala packs are re-tiered so `si` runs on Python 3.10–3.12.
  Sinhala conjuncts are written `consonant + virama + ZWJ (U+200D) +
  consonant`, and ZWJ is a valid identifier character only on CPython 3.13+
  (Unicode 15.1) — on 3.10–3.12 it is a hard `SyntaxError` at parse time, which
  held `si` at a 3.13 floor. The base `3.10.yml` now carries the 17 affected
  values as a no-ZWJ variant (non-conjunct spelling) with its floor back at
  3.10, `3.11.yml` / `3.12.yml` likewise, and the `3.13.yml` overlay restores
  the ZWJ conjunct spellings at the 3.13 floor. `translations.db` keeps the
  canonical conjunct forms; the lower-tier variant is a pack-layer
  compatibility downgrade that renders the virama visibly instead of the fused
  ligature, and stays pending Sinhala native review. A new general guard test
  rejects any pack value carrying a 3.13-only identifier character below its
  declared floor. [CORE-1521]

### Fixed

- **language-server**: enhanced Python intelligence has never actually run.
  The proxy searched for `pyright` — the command-line type checker, which does
  not speak LSP and closes the stream — rather than `pyright-langserver`, the
  language server that ships beside it in the same npm package. Pointed at a
  correct server it then hung anyway: the response reader performed blocking
  reads from inside an async task, pinning the event loop thread, so the
  handshake completed but its answer could never be delivered and the timeout
  meant to rescue it could never fire. The transport is rebuilt on asyncio
  streams, `Content-Length` now counts encoded bytes rather than characters
  (localized code and translated diagnostics are exactly the non-ASCII payloads
  that desynchronised the stream), and the server's stderr is drained so a
  chatty language server cannot stall behind a full pipe. Discovery prefers
  `pyright-langserver`, searches Homebrew's Apple Silicon prefix, and treats a
  CLI-only installation as nothing found rather than launching a process that
  exits on contact. **If you relied on this feature, install it with
  `npm install -g pyright` — the `pyright` binary alone is not enough.**
  [CORE-1886]
- **language-server**: a failure to start enhanced intelligence is no longer
  silent. The feature defaults to enabled, so a failed start used to leave you
  with plain Legesher features and no indication the richer ones were meant to
  be there. The server now says so once through a client notification, and
  answers a `legesher/status` request reporting whether enhanced intelligence
  is enabled, whether it is actually running, and which language server is in
  use — enabled and running are reported separately, because a feature turned
  off deliberately and one that tried and failed call for different responses.
  The status stays honest if the language server exits or its stream breaks
  mid-session, rather than continuing to report a transport that can no longer
  carry anything. A reconnecting client also no longer starts a second language
  server and orphans the first. [CORE-1886]
- **cli**: `--llm-model` had no effect on the `anthropic` and `cohere-aya`
  backends — it was forwarded only to `openai-compat`, so the other two were
  pinned to their provider defaults no matter what you passed. It now applies
  to every backend, which is what makes models like `tiny-aya-global`
  reachable: `cohere-aya` was fixed to `c4ai-aya-expanse-32b`, whose 23
  languages exclude Amharic. The flag is still optional — omitting it leaves
  each provider's own default in place rather than the CLI asserting one.
  `--llm-base-url` remains `openai-compat`-only, which it genuinely is.
  [CORE-1858]
- **i18n**: `except*` reverse-translated to `except**` in nine language packs
  (`da`, `de`, `fi`, `hi`, `mk`, `pt`, `ru`, `te`, `th`), producing output
  that does not parse. Their stored translation omitted the trailing `*` the
  compound-keyword path re-emits, so reverse translation appended a second
  one. Fixed at the selection layer and re-exported — the translated word is
  unchanged, only the syntax marker was added — and the identifier check now
  requires the mirror instead of merely allowing it — in both directions and
  exactly once — rejecting an unmirrored value at schema construction. Found by the all-packs round-trip sweep
  added in CORE-1745. Note the failure mode changed: an unmirrored value now
  fails the whole pack load rather than one entry, so a new engine paired
  with an old independently-versioned pack disables that language outright
  instead of mistranslating one keyword. [CORE-1839]

- **core**: a mapping-log append could destroy a concurrent writer's event. The
  torn-tail repair used a byte count measured when the log was *read*, which is
  stale as soon as another process appends — applying it later truncated from
  the new end, cutting that process's record in half and leaving mid-file
  corruption that then failed every subsequent load. The tail is now repaired
  from the file's state at write time, under an exclusive advisory lock that
  covers the whole repair-and-write sequence. A tail that still parses is
  recognized as a complete record that merely lost its newline and is kept
  rather than cut. [CORE-1770]
- **core**: mapping-log events are written in batches — one append and one
  fsync for a whole build instead of one of each per node (~5× faster on a
  3000-node file). [CORE-1770]
- **core**: an unknown mapping-log event kind from a newer client no longer
  fails the whole log load. The per-record `"v"` now dispatches: unknown
  kinds from a higher version are preserved and skipped, so a newer client's
  history cannot brick an older one. Rebuilding a map into an existing log
  no longer duplicates `mint` events. [CORE-1770]
- **core**: `legesher map edit` is all-or-nothing across entries — a failure
  part-way through a multi-file edit previously left the in-memory document
  half-mutated for library callers. A corrupt `identifier_map.json` now
  surfaces as an actionable error instead of a bare traceback. [CORE-1771]

- **mcp**: the stdio server now identifies itself truthfully and quietly —
  the MCP `initialize` handshake reports `legesher-mcp`'s own package version
  instead of the SDK's [CORE-1737], and the default log level is WARNING so a
  normal session writes nothing to stderr; set `LEGESHER_MCP_LOG_LEVEL`
  (DEBUG…CRITICAL) to restore verbose logging for troubleshooting [CORE-1738].
- **i18n**: the v2 canon gate was wrong in both directions — it refused 25
  legitimate Thai SARA-AM selections and every locale's `except*`, while
  passing 12 of 15 mixed-script confusables. Three corrections in
  `schema_v2.sql` and `migrate_to_v2.py`: `option_validations` now records a
  `nfkc_delta_class` fact (`sara-am-only` when the only NFKC-unstable character
  is U+0E33, which CPython itself normalizes per PEP 3131; `other` stays a hard
  block); identifier validation is term-aware, so `except*` validates its stem
  and requires the mirrored `*`, with no blanket `*` allowance elsewhere; and
  script consistency is a real per-character check against the shared
  `script_policy` allowlist instead of a `len(scripts) <= 1` heuristic, so the
  pack audit and the canon gate agree on what "foreign script" means.
  Re-running the migration lifts the 25 SARA-AM selections and `am except*`
  into canon and newly refuses 46 cross-script values that had already shipped
  — real corruptions, untranslated English, and loanwords (canon refusals
  26 → 49, selections 5,110 → 5,087); the validator version bumps
  `py-identifier-v1` → `py-identifier-v2`. [CORE-1514]
- **i18n**: all 609 pack-audit findings across 23 languages (166 distinct once
  collapsed across version packs) are corrected at the generation layer, and the
  pack-audit gate flips from report-mode to blocking. 87 target-script
  corrections land surgically in `translations.db` and in the pack YAMLs in
  lockstep — no regeneration, which stays unsafe until CORE-1400 — replacing
  corruptions (`pl bool` `布尔` → `logiczny`), untranslated English
  (`de ValueError` → `Wertfehler`), and embedded-Latin renderings (`th for`
  `เทคนิคfor` → `วนรอบ`); the old values stay as non-selected corpus options.
  Two systemic fixes clear the rest: `except*` carries its mirrored `*` in 14
  locales, resolving every `except`/`except*` duplicate-target and collision,
  and the Sinhala packs declare `python_version_min: '3.13'`, clearing all 51
  min-interpreter findings — a floor `LanguagePackLoader.load()` now enforces
  with `UnsupportedInterpreterError` rather than serving a pack the running
  interpreter cannot parse. `check_normalization` accepts the same
  `sara-am-only` NFKC class as the canon gate, a new `check_term_length` rule
  warns on sentence-length values (≥40 code points), and `audit_packs.py`
  separates blocking errors from advisory warnings, so `validate-packs.yml`
  drops `continue-on-error` and fails CI on errors only. The canon gate now
  refuses 0 selections (was 49); 22 `REFERENCE.md` files regenerated.
  [CORE-1318, CORE-1517]
- **core**: `import legesher_core` required the `tree_sitter` /
  `tree_sitter_python` C extensions. `legesher_core/__init__.py` re-exported
  `LLMTranslator` and `TreeSitterTranslator` eagerly, so the pure-stdlib
  `TokenTranslator` path could not import at all in environments without the
  extensions (minimal installs, browser Python runtimes). Those two exports, and
  the five parser-backed exports in `legesher_core.tree_sitter`, now resolve
  lazily through module-level `__getattr__` (PEP 562); `__all__` and `dir()` are
  unchanged, and the pure components (`IdentifierMap`, `IdentifierValidator`,
  `TranslationLogger`) stay eager. The tree-sitter dependencies move to an
  optional `treesitter` extra: accessing a guarded export or calling
  `create_translator(..., use_tree_sitter=True)` without it raises an
  `ImportError` naming `pip install legesher-core[treesitter]`, and only
  ImportErrors whose root cause is `tree_sitter` / `tree_sitter_python` are
  re-labelled. The monorepo root and the `legesher` CLI depend on
  `legesher-core[treesitter]`, so CI and dev environments keep the backend under
  a plain `uv sync`. [CORE-1555]
- **legesher-vscode**: RTL code panes used the pre-Unicode-6.3
  `unicode-bidi: embed`. `.pane.rtl pre` / `.pane.rtl code` in the webview
  stylesheet now use `unicode-bidi: isolate`, which prevents bidi from bleeding
  across the pane boundary. Container direction only — the per-placeholder
  message isolation governed by the bidi display-prose policy is unchanged.
  [CORE-1537]
- **docs**: the docs site could not deploy. Snippet generation ran inside the
  Astro build, which needs a Python 3.10+ interpreter with the pack deps that
  Vercel's Node-only build image does not provide, so production stayed frozen
  on the pre-localization deploy with `/es/` and `/ar/` returning 404. The
  generated artifacts are now committed under `docs/generated/` and copied in by
  a pure-Node integration; the Python generator runs only on demand via
  `pnpm generate:snippets`, and reports an actionable error naming
  `LEGESHER_PYTHON` and `docs/scripts/requirements.txt` when the interpreter it
  needs is missing. All generator file I/O is explicitly utf-8, so non-ASCII
  pack values no longer depend on the build machine's locale.
  [CORE-1574, CORE-1577]

### Security

- **core**: an interior U+FEFF slipped through the git clean filter into
  canonical storage. `scan_text` short-circuited every U+FEFF to the advisory
  `bom` kind, but the filter blocks only `bidi` / `invisible` / `tatweel` — and
  because a leading BOM is stripped before the scan, any U+FEFF still present at
  scan time is an interior zero-width invisible (category `Cf`) that desyncs
  offsets and can smuggle a hidden identifier distinction. The short-circuit is
  now gated on `offset == 0`: a leading BOM stays advisory, an interior U+FEFF
  is reported as a blocking `invisible` and honors the per-call allowlist for
  parity with the general `Cf` branch, so the clean filter rejects the input
  (exit 1, nothing written). [CORE-1557]

## [0.22.0] - 2026-07-15

## [0.21.3] - 2026-07-12

### Fixed

- **i18n**: four small `pkg:i18n` quick wins from the 2026-07-12 Phase C
  review. `TranslationDatabase.close()` now closes connections opened from
  every thread (tracked under a lock), and the class supports
  `with TranslationDatabase() as db:` [CORE-610]; `get_stats()` count queries
  are written out per table, eliminating the f-string-table-name SQL pattern
  [CORE-609]; the default `db_path` now detects the install location — a
  source checkout / editable install keeps the in-repo db, while installed
  environments (site-packages/dist-packages) get `~/.legesher/translations.db`
  seeded once from the bundled copy (CLI defaults resolve at command time,
  `--db-path` override unchanged) [CORE-601]; and
  `api/providers/anthropic.py` is mypy-clean — 10 `union-attr` /
  `call-overload` / `no-any-return` errors fixed via proper `None` narrowing,
  no `type: ignore` [CORE-816].

## [0.21.2] - 2026-07-12

### Fixed

- **i18n**: three garbled pack translations — `de` `str` was
  `diestrTypKonvertierung` (a mashed-together "die str Typ Konvertierung",
  also the longest token across all 51 packs), now `Zeichenkette`; `de` and
  `da` `repr` both carried the French `représentation` (copy-paste leak), now
  `repräsentation` (de) / `repræsentation` (da). Applied surgically to the
  `3.10.yml` packs, `REFERENCE.md`, and `translations.db`
  (candidates + selected, tagged pending native review). [CORE-1303]

## [0.21.1] - 2026-07-12

### Fixed

- **core**: metadata writes raced under concurrency — every writer staged
  through the same shared temp file (`.<name>.tmp`) before the atomic rename,
  so parallel writers could rename each other's half-written file or crash
  with `FileNotFoundError`, and the unserialized read-modify-write in
  `record_translation`/`add_history_entry`/`update_metadata` silently dropped
  concurrent history entries. Temp names are now unique per process and
  thread (removed on any write failure), and a per-path `threading.Lock`
  serializes each metadata file's read-modify-write cycle, so concurrent
  appends all land. Root cause of the `test_concurrent_tracking` CI
  flake. [CORE-1319]

## [0.21.0] - 2026-07-11

### Added

- **legesher**: `--global` flag for `legesher config set`, writing values to
  the user-level config (`~/.legesher/config.yml`) instead of the project
  config; `config get`/`list` now read the user-level config merged with the
  project config (top-level merge matching runtime precedence: a project
  section replaces the user section of the same name), `config set` reports
  which config file it wrote, and a config file whose YAML root is not a
  mapping produces a clear CLI error instead of a crash. [CORE-574]
- **i18n**: selected translations for 5 under-covered core terms (`__import__`,
  `type`, `encodingwarning`, `exceptiongroup`, `baseexceptiongroup`) across all
  51 Python language packs — reconciling `selected_translations` to the shipped
  packs and filling the missing `__import__`/`type` builtins (`__import__`
  generated dunder-wrapped, experimental pending native review). [CORE-606]

### Fixed

- **i18n**: two pre-existing pack translation bugs — `fi` `exceptiongroup`
  collision (`ohje` → `poikkeusryhmä`) and `de` `baseexceptiongroup` identity
  (`BaseExceptionGroup` → `Basisausnahmegruppe`). [CORE-606]

## [0.20.0] - 2026-07-09

## [0.19.0] - 2026-07-09

## [0.18.1] - 2026-07-09

## [0.18.0] - 2026-07-09

### Changed

- **i18n**: `PromptBuilder` renders the resolved style guide's rules/profile
  into the translation system prompt — the naming case-substitute strategy and
  the conventions the script can express, the script identity + constraints, and
  the formatting rules. It no longer emits a vocabulary / translation-conventions
  block (word choices live in the language packs), activating the previously
  inert guides.

## [0.17.1] - 2026-07-09

### Fixed

- **legesher**: `legesher init --git` configured git filters as the nonexistent
  `legesher git clean/smudge` subcommands, so repos onboarded through `init`
  looked configured but silently never translated. It now delegates to the same
  helpers as `legesher git setup`, wiring the real `legesher-filter` console
  script (`--clean`/`--smudge`) plus `filter.legesher.required=false` — both
  entry points configure identically and can no longer drift. The README's
  matching phantom `legesher git clean/smudge` reference is corrected to
  `legesher-filter`. (CORE-1344, #1)

## [0.17.0] - 2026-07-09

### Changed

- **i18n**: `StyleGuideLoader` resolves the full script-family `extends` chain
  (base → direction → family → language) with cycle detection, so overlays are
  merged into member languages; parsed files are cached and unsafe `extends`
  targets (path separators / `..`) are rejected. The pack validation gate gained
  an ASCII-digit check and stays safety-only — identifier length and other
  stylistic preferences are guidance for the translation prompt (CORE-1395),
  not pack warnings.

## [0.16.0] - 2026-07-09

### Added

- **i18n**: Per-language Python style guides for all 51 languages on the
  rules/profile schema — capability flags, script constraints, and a
  native-digit profile per language; rules only (vocabulary lives in the packs),
  validated against the schema and `languages.json`.
- **i18n**: Base and family style-guide overlays reduced to minimal structural
  nodes on the rules/profile schema, so legacy vocabulary no longer leaks into a
  merged guide through the `extends` chain.

## [0.15.0] - 2026-07-09

### Added

- **i18n**: Style-guide schema + template + validator + README — the canonical,
  documented format for per-language Python style guides (capability flags, a
  script profile, and a validator that checks consistency with `languages.json`).

## [0.14.0] - 2026-07-05

### Added

- **i18n**: Script-family style-guide overlays (CJK, Brahmic, Arabic-script,
  Cyrillic, Ethiopic, and Southeast-Asian spaceless scripts) encoding naming
  rules for caseless scripts, per-language symbol vocabulary (what `_`, `:`,
  parentheses are called), and Noto font rendering hints for the editor.
  See `libs/i18n/CHANGELOG.md` (#4).

## [0.13.1] - 2026-07-05

### Changed

- **i18n**: Translation context briefs now cover every database term (183
  briefs — 61 new, spanning the exception families plus `except*`, `self`,
  `cls`) and describe only the English term: per-language translation samples
  and language-family prescription tables are removed from the canonical
  briefs, with live pack context injected at prompt-assembly time instead.
  See `libs/i18n/CHANGELOG.md` for full details (#2).

### Fixed

- **i18n**: The fabricated `basegeneratorexit` "exception" (never a real
  Python name) is removed from the translations database, the term
  definitions, and all 51 language packs. See `libs/i18n/CHANGELOG.md` (#3).

## [0.13.0] - 2026-06-11

### Added

- **i18n**: Unicode/script safety validation layer for language packs, ahead of
  the 51 → 103 expansion. A per-language `script_policy.py` plus new
  `SchemaValidator` checks (NFKC stability, foreign-script bleed-through,
  bidi/format controls, live-keyword collisions, the Sinhala-ZWJ
  min-interpreter trap) aggregated by `validate_pack_strict`, an
  `audit_packs.py` CLI, a non-blocking `validate-packs` CI job, and 8 new test
  suites. See `libs/i18n/CHANGELOG.md` for full details (PR #256).

### Fixed

- **i18n**: Path-traversal guard in `LanguagePackLoader.load` — the `version`
  argument is validated against `^(\d+\.\d+|default)$` before any filesystem
  access. See `libs/i18n/CHANGELOG.md` (PR #256).

### Security

- **i18n**: Pack validation gate detects Unicode/script attack classes across
  all packs in report mode — Trojan-source bidi controls (CVE-2021-42574),
  invisible-character / fullwidth keyword spoofs, and NFKC round-trip
  corruption. See `libs/i18n/CHANGELOG.md` (PR #256).

## [0.12.0] - 2026-06-11

## [0.11.3] - 2026-06-11

## [0.11.2] - 2026-05-14

### Changed

- **i18n**: `CohereAyaProvider` error logs and raised `TranslationError`
  bodies now include the exception class name, fall back to `repr(e)`
  when `str(e)` is empty, and surface `status_code` / `code` /
  `x-debug-trace-id` when the SDK exception carries them ([CORE-870]).
  Observability fix — does not change API success rate, request volume,
  or cost. Surfaced 429s that had been masked as empty error messages
  during AYA-213 cond5 diagnostic work. See `libs/i18n/CHANGELOG.md` for
  full details.

## [0.11.1] - 2026-05-07

## [0.11.0] - 2026-05-03

### Added

- **PromptBuilder no-structured-format rule** ([CORE-1048]): Second,
  narrower bullet appended to `_CRITICAL_RULES` that forbids wrapping a
  translation in any structured key/value, label, JSON, or paired format,
  and forbids joining the original identifier to the translation with
  separators like `original_name_X_translated_name_Y`. Follow-up to
  CORE-950: smaller models (`tiny-aya-global` 3.35B, observed on cond5 ur)
  follow the "no explanation" rule but still emit labeled mappings — a
  distinct prompt-following failure that the prior wording buried in a
  single multi-clause bullet. Two distinct list items in the rendered
  Markdown system prompt materially improve prompt-following salience for
  small models. Universal rule (no per-model override). Touches
  `libs/i18n/legesher_i18n/prompt_builder.py` plus a new
  `libs/i18n/tests/test_prompt_builder_no_structured_format.py`.

## [0.10.1] - 2026-05-01

### Fixed

- **Stale CI tests** ([CORE-1126]): re-aligned two integration test
  classes that had drifted from the features they were testing. The
  legesher CLI test for class translation was asserting the
  pre-CORE-710 contract (`self` preserved verbatim); tightened to the
  post-CORE-710 contract (Spanish pack translates `self -> mismo` via
  `reserved_words`). The i18n cross-section collision
  gate tests were silently failing on Windows because
  `pack_yml.write_text(...)` defaulted to the system codepage
  (cp1252) and couldn't encode Arabic/Urdu pack content; added
  explicit `encoding="utf-8"` to all three writes. No product
  behavior change.

## [0.10.0] - 2026-05-01

### Added

- **Reserved Words category** ([CORE-710]): Python conventions like `self`
  and `cls` are now translated deterministically per language pack via a new
  `reserved_words:` YAML section. Closes the AYA-213 Cycle-4 Urdu collision
  failure mode (`self → میں` colliding with keyword `in → میں`).
  - Touches: `term_definitions.py`, `schema_validator.py`, `pack_loader.py`,
    `token_mapper.py`, `transformer.py`, `tree_sitter/translator.py`,
    `tree_sitter/extractor.py`, `tree_sitter/identifier_map.py`,
    `language_interface.py`, `semantic_tokens.py`, all 51 pack `3.10.yml`
    files, plus 80+ new tests.
  - Performance: <5% regression on translator hot path (gated by
    `--benchmark-compare-fail=median:5%` in CI).
- **Prompt-builder hardening + collision audit** ([CORE-950]): Closes the
  systemic LLM trace-format pollution surfaced during the AYA-213 Cond-5
  backend pilot (gemma3:12b emitted
  `__original_X_translation_Y_Explanation_<essay>` markers on zh+ur; Tiny
  Aya GGUF emitted `____translated_identifier_X____` residue). Also wires
  the deferred CORE-710 pack-aware-collision plumbing end-to-end.
  - **PromptBuilder API extensions**: new `forbidden_values` and `examples`
    kwargs on `build_identifier_prompt` / `build_text_prompt`; new
    `preserve_module_names` flag on `__init__`; new
    `_CRITICAL_RULES.script_aware` substitute rule for non-cased scripts
    (Arabic family, CJK, Brahmic, SE-Asian, Ge'ez — 17 supported languages).
  - **`languages.json` schema**: `has_case_distinction: bool` field added
    next to `rtl` for all 51 supported languages; canonical source of
    truth for language script properties.
  - **LLMTranslator collision recovery**: pack-aware `IdentifierMap` raises
    `ValueError` on reserved-value collisions; `_translate_identifiers`
    catches and applies numeric-suffix recovery, falling back to
    SHA-256-derived suffixes (deterministic across runs). Empirically
    fired in production on `ValueError → قدرغلطی → قدرغلطی_2` during
    end-to-end gemma3:12b validation.
  - **Cross-section collision guardrail**: extends pre-commit
    `validate-language-pack-yaml` hook with
    `SchemaValidator.check_duplicates()['cross_section_collisions']` (also
    deduplicates intra-section findings); new
    `libs/i18n/scripts/audit_collisions.py` runs both DB-level and
    pack-level audits across the canonical pack list derived from
    `languages.json`; new `lint`-job step in `.github/workflows/ci.yml`.
  - **Hidden bug fix**: `LLMTranslator.__init__` previously silently
    discarded caller-provided empty `IdentifierMap`s because
    `IdentifierMap.__len__` evaluates to 0 for fresh instances and the
    `or IdentifierMap()` fallback fired. Replaced with `is None` check.
  - **Cohere V2 SDK token-count fix**: defensive multi-path read covers
    SDK build variants; fixes `tokens_in/tokens_out=0` regression.
  - Touches: `prompt_builder.py`, `style_guides.py`, `languages.json`,
    `languages.schema.json`, `_rtl.yml`, `zh.yml`, three i18n providers
    (`anthropic`, `cohere_aya`, `openai_compat`),
    `tree_sitter/llm_translator.py`, `validate_language_pack_yaml.py`,
    new `audit_collisions.py`, `.github/workflows/ci.yml`, plus 50+ new
    tests across i18n + core.
  - Empirical validation: end-to-end `gemma3:12b` translation of a
    sample file to `ur` produces zero trace markers, 59.5% native-script
    ratio, layer-2 collision recovery firing as designed.

### Package Versions

| Package                  | Version | Changed? |
| ------------------------ | ------- | -------- |
| legesher-core            | 0.23.0  | Yes      |
| legesher-i18n            | 0.23.0  | Yes      |
| legesher (CLI)           | 0.23.0  | —        |
| legesher-language-server | 0.1.3   | Yes      |
| legesher-vscode          | 0.1.5   | —        |

### Removed

- **home**: Delete the empty `legesher-home` package scaffold (`libs/home/`) and
  its license-boundary enforcement machinery from the monorepo. The package was
  originally renamed from `legesher-pride` (CORE-515) as a placeholder for a
  future "digital home and community platform," but never received an
  implementation beyond a `__version__` string. Any future commercial or
  community-platform work will be built outside this open-core monorepo so the
  main repo stays cleanly Apache-2.0. Removes `libs/home/`,
  `scripts/check_license_boundary.py`, the `[tool.importlinter]` contract, the
  `check-license-boundary` pre-commit hook, the `home` commitizen scope, the
  Tier 4 tier and License Boundary sections in `CLAUDE.md`, the proprietary
  license section in `LICENSING.md` and `README.md`, and the `home` option in
  `.github/workflows/publish-pypi.yml`. (CORE-1189)

### Changed

- **core + i18n**: `mypy --strict` now passes on the public API surface (19 files
  across `legesher_core`, `legesher_i18n`, and `legesher-language-server`). Closed
  ANN201/ANN001 gaps on public signatures, added precise `dict[str, Any]` /
  `list[tuple[str, str]]` annotations, and typed the lazy-import factory helpers
  in `language_interface.py` via `TYPE_CHECKING` imports. Tightened
  `create_translator`'s and `create_translator_from_config`'s `builtin_map`
  parameter from `BuiltinMap | None = None` to required `BuiltinMap` — the
  previous Optional annotation was a lie, since `TokenMapper` explicitly
  rejects both `None` and `{}`, so every caller would eventually raise at
  runtime. Added `py.typed` markers to `legesher_core` and `legesher_i18n`
  (plus the required `[tool.pdm.build]` config in `libs/core/pyproject.toml`
  so the marker ships in the wheel) for PEP 561 support. Internal helpers
  (`tree_sitter/` extractor/parser/identifier_validator) and body-level
  `translator.py` issues remain out of scope per the issue description.
  (CORE-1183)
- **core**: Declare `pyyaml>=6.0` as a direct dependency of `legesher-core`.
  `legesher_core.metadata` imports `yaml` but `pyyaml` was only reaching the
  installed environment transitively via `legesher-i18n`. Making the
  dependency direct tightens the declared contract so `legesher-core`
  doesn't break if that transitive path ever changes. No lockfile
  additions. (CORE-1183, PR #226 review)
- **language-server**: Loosen the 1.2× threshold in
  `TestCompletionProviderPerformance::test_completion_caching_performance` to
  2.0×. The test measures microsecond-scale durations where `perf_counter()`
  resolution and GC jitter dominate on shared CI runners; the tighter
  threshold flaked intermittently on GitHub Actions. 2.0× still captures the
  intent ("caching does not make things slower") without the noise.
  (CORE-1183, PR #226 CI unblock)
- **docs**: Google-style docstrings filled in for the public API surface that PyPI
  consumers encounter via `help(symbol)` and IDE hover — `legesher_core` classes
  (`TranslationScope`, `TranslatorBackend` type alias), `legesher_i18n` classes
  (`LanguagePackLoader`, `PromptBuilder`, `StyleGuideLoader`, `LanguagePackMetadata`,
  `LanguagePackSchema`, `SchemaValidator`, `PythonVersionDetector`, `PythonVersionInfo`,
  `VersionIndex`), and the `legesher-language-server` module docstring. Each public
  symbol now has structured `Args`, `Returns`, `Raises`, `Attributes`, and `Example`
  sections where applicable, with translation-ready prose suitable for the future
  multilingual API reference pipeline. Docstring-only — no behavior changes.
  (CORE-1173, #225)

## [0.9.2] - 2026-04-20

### Fixed

- **i18n**: Collapse duplicate `__all__` assignment in `legesher_i18n/__init__.py`.
  Python was re-binding on the second assignment so the first list was dead code, and
  the two lists had silently drifted — `PromptBuilder` and `StyleGuideLoader` were
  missing from the live `__all__`, and `load_language_pack` was missing from the dead
  one. `from legesher_i18n import *` now correctly includes all 30 exported names.
  Direct imports (`from legesher_i18n import PromptBuilder`) were unaffected.
  (CORE-1174, #224)

## [0.9.1] - 2026-04-17

### Changed

- **ci**: Split lint and test jobs out of `release-foundation.yml` and
  `release-language-packs.yml` into a new unified `.github/workflows/ci.yml`
  (CORE-1122). The new workflow runs on `pull_request` and `push` to main, giving
  contributors fast automated feedback on PRs for the first time. Release
  workflows now only handle the release pipeline. PR runs use a tiered matrix
  (ubuntu-only) to save credits; push-to-main keeps the full matrix as a
  pre-merge safety net. Concurrency control cancels stale PR runs on new pushes
  but never cancels main runs. Unblocks PR #207 (CORE-388/389/390) — its
  Codecov integration can activate once rebased on new main.

### Fixed

- **legesher**: `ruff format` drift on `libs/legesher/tests/unit/test_cli_translate.py`
  cleared to keep the new PR-triggered CI green on its first run (CORE-1122).

## [0.9.0] - 2026-04-10

### Added

- **language-server**: Context-aware semantic tokens for class names, function names, and
  first parameter (self/cls) in translated code — adds a state machine to the tokenizer
  that colors `ListaCompleta` as a class name after `clase`, `__init__` as a function name
  after `definir`, and `propio` as a parameter after `(` (CORE-895, #199)

### Security

- **repo**: Pre-open-source security audit remediations (CORE-721, #206) — harden
  `.gitignore` with crypto/credential file patterns (`*.key`, `*.pem`, `*.p12`, `*.pfx`,
  `credentials.json`, `secrets/`), re-enable CodeQL workflow with push/PR/weekly triggers
  (was `workflow_dispatch` only), and remove private Linear workspace URLs from source
  code and documentation. Full audit found no secrets in git history, clean OWASP review,
  and license boundary intact.

## [0.8.1] - 2026-04-03

## [0.8.0] - 2026-04-02

### Added

- **language-server**: Extend semantic tokens to highlight translated builtins and exceptions —
  builtin types (`int`/`str`/`float`) colored as teal, builtin functions (`print`/`input`/`len`)
  as yellow, exceptions (`ValueError`/`errordevalor`) as green (CORE-709, #194)
- **i18n**: Per-language style guides and PromptBuilder for context-aware LLM translation
  prompts (CORE-706, #193)
- **core**: Full LLM-powered code translation — translate identifiers, comments, docstrings,
  and string literals via pluggable LLM backends (AYA-191, #189)
  - `LLMTranslator`: composes TreeSitterTranslator (keywords/builtins) with LLM backend
  - `TranslatableExtractor`: AST walker extracting all translatable elements with context
  - `IdentifierMap`: cross-file/cross-language translation glossary with JSON persistence
  - `IdentifierValidator`: Python identifier validation with RTL/Unicode support
  - `TranslationLogger`: JSONL training data collection for future model fine-tuning
  - `TextTranslationBackend` protocol: dependency inversion for LLM backends
  - `TranslationScope`: toggle translation of identifiers/comments/docstrings/strings
- **i18n**: Cohere Aya API translation provider for hosted Aya models (AYA-191)
- **i18n**: OpenAI-compatible translation provider for local models — works with vLLM,
  Ollama, llama.cpp, LocalAI, or any `/v1/chat/completions` endpoint (AYA-191)
- **i18n**: `ProviderBackendAdapter` bridging async TranslationCoordinator to sync
  TextTranslationBackend protocol (AYA-191)
- **cli**: `--full` flag for `legesher translate` enabling LLM translation (AYA-191)
- **cli**: `--llm-backend` option (anthropic, cohere-aya, openai-compat) (AYA-191)
- **cli**: `--llm-base-url` for custom OpenAI-compatible endpoints (AYA-191)
- **cli**: `--identifier-map` for cross-file translation consistency (AYA-191)
- **cli**: `--checkpoint` for resuming interrupted batch translation jobs (AYA-191)

### Fixed

- **core**: Escape closing quote sequences in LLM string/docstring translations to prevent
  breaking out of string literals (AYA-191)
- **core**: Handle multi-line LLM comment responses by prefixing each line with `#` (AYA-191)
- **core**: F-string `string_content` nodes reconstructed as raw text instead of
  re-wrapping in quotes (AYA-191, #191)
- **core**: Comment text sent to LLM without `#` prefix, preventing double `##` in output (AYA-191, #191)
- **i18n**: Cohere/OpenAI-compat provider exceptions wrapped in `TranslationError` for
  coordinator fallback handling (AYA-191)
- **i18n**: OpenAI-compat provider handles `base_url` with or without `/v1` suffix (AYA-191)
- **i18n**: Batch adapter returns original text for failed translations, preventing
  IdentifierMap poisoning with empty strings (AYA-191)
- **cli**: `--full` mode enforces English source (`--from en`) with clear error (AYA-191)
- **cli**: Provider name mapping for `--llm-backend` CLI values (AYA-191)

## [0.7.3] - 2026-03-19

### Language Pack Versions

| Pack           | Version | Changed? |
| -------------- | ------- | -------- |
| i18n-python-zh | 0.0.4   | Yes      |
| i18n-python-es | 0.0.3   | Yes      |
| i18n-python-ur | 0.0.2   | Yes      |

### Fixed

- **i18n-python-zh**: 33 translation corrections from native speaker review
  ([@NextME14](https://github.com/NextME14)) — removed
  English words (`elseif`, `ValueError`, `Nosuchfileordirectory`), fixed meaningless characters
  (`玪抑` for lambda), standardized Unicode exceptions to use `统一码` (AYA-160)
- **i18n-python-es**: 5 quality fixes — replaced placeholder text (`eltérminotraducido`),
  non-words (`ipsislo`), and verbose descriptions with proper Spanish translations (AYA-160)
- **i18n-python-ur**: Applied 2 native speaker ([@rafaym1](https://github.com/rafaym1))
  suggestions — `type` and `userwarning` translations updated (AYA-160)

### Added

- Community review translation suggestions added to translations.db for zh, ur, and es
  with source `community_review` ([@NextME14](https://github.com/NextME14) zh review,
  [@sarr266](https://github.com/sarr266)/[@rafaym1](https://github.com/rafaym1)
  ur reviews, Universal Python ur alternatives, Latino es alternatives)

## [0.7.2] - 2026-03-18

### Package Versions

| Package                  | Version | Changed? |
| ------------------------ | ------- | -------- |
| legesher-core            | 0.9.2   | Yes      |
| legesher-i18n            | 0.9.2   | —        |
| legesher (CLI)           | 0.9.2   | —        |
| legesher-language-server | 0.1.2   | —        |
| legesher-vscode          | 0.1.5   | —        |
| legesher-home            | 0.1.0   | —        |

### Fixed

- **legesher-core**: Fix TreeSitterTranslator crashing on ~0.6% of Python files with
  non-UTF-8 bytes in string literals when translating to multi-byte languages (CORE-799)

## [0.7.1] - 2026-03-16

## [0.7.0] - 2026-03-16

### Added

- **legesher-i18n**: 22 new language packs — expanding Legesher from 29 → 51
  supported languages (CORE-675, CORE-707)
  - Bengali, Bosnian, Catalan, Croatian, Czech, Galician, Gujarati, Irish,
    Kannada, Latvian, Macedonian, Malayalam, Mongolian, Burmese, Persian,
    Romanian, Scottish Gaelic, Serbian, Sundanese, Telugu, Uzbek, Welsh
  - 3,850 new translations with zero collisions across all 51 languages
  - Each pack: 37 keywords, 72 builtins, 66 exceptions (Python 3.10–3.14)
  - Translation sources: Aya-101 AI Model (21 packs), Claude AI (Bosnian)
  - Persian (fa) is the 4th RTL language; 3 Celtic languages added (ga, gd, cy)

### Changed

- Updated all documentation, tests, and configuration references from 29 → 51
  languages across root CLAUDE.md, README.md, libs/i18n, libs/legesher,
  libs/vs-code, and docs site

## [0.6.0] - 2026-03-11

### Added

- **legesher-i18n**: 3 new language packs — Amharic (am), Sinhala (si), and Urdu (ur),
  expanding Legesher from 26 → 29 supported languages (CORE-687)
  - **Amharic (አማርኛ)**: First Ge'ez-script language in Legesher — 37 keywords,
    72 builtins, 66 exceptions across Python 3.10–3.14 (CORE-690)
  - **Sinhala (සිංහල)**: First South Asian script language — 37 keywords,
    72 builtins, 66 exceptions across Python 3.10–3.14 (CORE-1128)
  - **Urdu (اردو)**: Third RTL language (joining Arabic and Hebrew) — 37 keywords,
    72 builtins, 66 exceptions across Python 3.10–3.14 (CORE-1071)
  - Zero translation collisions across all 29 languages
  - 540 new translations added to the translation database
- **legesher-i18n**: Generic HuggingFace translation engine with pluggable model profiles,
  enabling new AI translation models to be added with ~10 lines of config (CORE-686)
  - Local inference engine with lazy model loading and device auto-detection
    (CUDA/MPS/CPU)
  - HF Inference API engine with rate limiting for cloud-based translation
  - 4 pre-registered Tiny Aya (3.35B) profiles for underserved languages
  - New CLI flags: `--models hf|hf-api|tiny-aya|tiny-aya-api`,
    `--hf-profile <name>`, `--tiny-aya-variant earth|fire|water|global`
- **docs**: Vercel deployment for docs.legesher.io with Astro adapter (CORE-1194)

## [0.5.1] - 2026-03-01

> Includes changes from individually-released packages since v0.5.0:
> vs-code 0.1.2–0.1.5, language-server 0.1.2.

### Package Versions

| Package                  | Version | Changed? |
| ------------------------ | ------- | -------- |
| legesher-core            | 0.7.1   | Yes      |
| legesher-i18n            | 0.7.1   | Yes      |
| legesher (CLI)           | 0.7.1   | —        |
| legesher-language-server | 0.1.2   | Yes      |
| legesher-vscode          | 0.1.5   | Yes      |
| legesher-home            | 0.1.0   | —        |

### Added

- **legesher-i18n**: Consolidate 3 translation databases into normalized
  4-table schema with `selected_translations` tracking (CORE-594)
- **legesher-language-server**: Bilingual hover format showing English docs
  first, then target language translation

### Fixed

- **legesher-core**: Replace `datetime.UTC` with `timezone.utc` for
  Python 3.10 compatibility (CORE-662)
- **legesher-i18n**: Resolve 41 translation collisions across 17 languages
  where the same translated word mapped to 2+ Python terms, breaking
  round-trip translation (CORE-605)
  - Add `find_collisions()` API and `db collisions` CLI command
  - Add collision guard to `set_selected()` preventing future collisions
  - Upgrade pre-commit YAML validator from warnings to errors for duplicates
  - Bump affected language packs to v0.0.3: ar, el, fi, he, hi, hu, it,
    ko, no, pl, pt, ru, sv, th, tr, vi, zh
- **legesher-language-server**: Add MIT LICENSE file (CORE-622)
- **legesher-language-server**: Fix invalid author email domain (CORE-665)
- **legesher-vscode**: Fix Translation View showing English on both
  panels — bundle language pack YAML files in VSIX (CORE-602)
- **legesher-vscode**: Fix telemetry pipeline — zero events reaching
  Azure Application Insights (CORE-590)
  - Bundle `@vscode/extension-telemetry` instead of externalizing it
  - Add try/catch error handling to all 11 telemetry methods, PII
    sanitization, type-safe union types
  - Add missing telemetry to LSP errors, translation failures, feedback
    responses, server-not-installed path
  - Remove `/tmp/env-debug.log` security artifact, filesystem paths from
    log messages
  - Add feedback `Logger.info` calls, telemetry diagnostic logging,
    build validation in preview script
  - Remove dead code (`trackWalkthroughStep`, unused feature values) —
    tracked in CORE-591, CORE-592

### Changed

- **CI**: Auto-stamp changelogs on foundation release (CORE-608)
  - Add `scripts/stamp-changelog-release.py` to stamp `[Unreleased]`
    headings and update Package Versions table
  - Add stamp step to `release-foundation.yml` workflow
- **legesher-vscode**: Release v0.1.2 with marketplace improvements
  (CORE-558)
  - Add extension icon for better visibility
  - Inject telemetry connection string at build time
  - Fix security issue: remove connection string from logs
  - Update README and marketplace metadata
- **legesher-vscode**: Update dependencies — `@vscode/extension-telemetry`
  1.5.0 → 1.5.1, `@vscode/vsce` 2.32.0 → 3.7.1, eslint 8 → 10
- **legesher-language-server**: Consolidate hover provider
  `LanguagePackLoader.load()` calls (4 → 1)

## [0.5.0] - 2026-02-01

### Package Versions

| Package                  | Version | Changed? |
| ------------------------ | ------- | -------- |
| legesher-core            | 0.5.0   | Yes      |
| legesher-i18n            | 0.5.0   | Yes      |
| legesher (CLI)           | 0.5.0   | Yes      |
| legesher-language-server | 0.1.1   | Yes      |
| legesher-vscode          | 0.1.1   | —        |
| legesher-home            | 0.1.0   | —        |

### Fixed

- **legesher-i18n**: Fix 33 mixed-script translations across Greek,
  Hebrew, Russian, Arabic, Finnish packs (CORE-531)
- **legesher-i18n**: Fix Japanese `in` keyword invalid identifier, add
  missing `type` builtin to es/ar (CORE-531)
- **legesher-core**: Fix `TokenTranslator` compound keyword (`except*`)
  lookahead handling (CORE-531)

### Changed

- **legesher-language-server**: Bump to 0.1.1 for pygls 2.0 migration
  (CORE-448)
- **legesher-i18n**: Bundle all 26 language pack YAML files directly in
  the i18n wheel (CORE-559)
- **legesher CLI**: Add `legesher config` command (CORE-563),
  non-interactive `legesher init` (CORE-562), fix `--version`
  (CORE-560), dynamic language help text (CORE-561)
- **Docs**: Fix CLI flags `--from`/`--to`, remove non-existent commands,
  update config references (CORE-564–566)
- **CI**: Add cross-platform lint and test workflows

## [0.4.0] - 2026-01-27

### Package Versions

| Package                  | Version | Changed? |
| ------------------------ | ------- | -------- |
| legesher-core            | 0.4.0   | —        |
| legesher-i18n            | 0.4.0   | —        |
| legesher (CLI)           | 0.4.0   | —        |
| legesher-language-server | 0.1.0   | —        |
| legesher-vscode          | 0.1.1   | —        |
| legesher-home            | 0.1.0   | Yes      |

### Changed

- **legesher-home**: Renamed from `legesher-pride` to `legesher-home` (CORE-515)
- Version bump across all foundation packages to 0.4.0

## [0.3.0] - 2026-01-26

### Package Versions

| Package                  | Version       | Changed? |
| ------------------------ | ------------- | -------- |
| legesher-core            | 0.3.0         | —        |
| legesher-i18n            | 0.3.0 (0.2.1) | Yes      |
| legesher (CLI)           | 0.3.0         | —        |
| legesher-language-server | 0.1.0         | —        |
| legesher-vscode          | 0.1.1         | —        |
| legesher-home            | 0.1.0         | —        |

### Added

- **legesher-i18n**: Keyword Registry CLI Tool with export, validate, and REFERENCE.md auto-generation (CORE-555)

## [0.2.0] - 2026-01-26

### Package Versions

| Package                  | Version | Changed? |
| ------------------------ | ------- | -------- |
| legesher-core            | 0.2.0   | —        |
| legesher-i18n            | 0.2.0   | Yes      |
| legesher (CLI)           | 0.2.0   | —        |
| legesher-language-server | 0.1.0   | —        |
| legesher-vscode          | 0.1.1   | —        |
| legesher-home            | 0.1.0   | —        |

### Added

- **legesher-i18n**: Complete all 26 language translations via Aya AI Model pipeline (CORE-530)
- **legesher-i18n**: Python 3.14 language pack support, Spanish YAML boolean fix

## [0.1.1] - 2026-01-23

### Package Versions

| Package                  | Version | Changed? |
| ------------------------ | ------- | -------- |
| legesher-core            | 0.1.1   | —        |
| legesher-i18n            | 0.1.1   | Yes      |
| legesher (CLI)           | 0.1.1   | —        |
| legesher-language-server | 0.1.0   | —        |
| legesher-vscode          | 0.1.1   | Yes      |
| legesher-home            | 0.1.0   | —        |

### Fixed

- **legesher-i18n**: Fix YAML exporter term_type from database (CORE-460)

### Added

- **legesher-i18n**: REFERENCE.md quick guides for all 25 language packs
- **legesher-vscode**: Onboarding dialog, translation panel, language selection, telemetry, feedback system (CORE-477)
- **legesher-vscode**: CI build pipeline with esbuild

### Removed

- **legesher-i18n**: Legacy language pack archives

## [0.1.0] - 2025-11-07

### First Public Release

The inaugural release of Legesher as a unified monorepo, enabling developers to code
in their native language instead of English.

### Package Versions

| Package                  | Version | Changed? |
| ------------------------ | ------- | -------- |
| legesher-core            | 0.1.0   | Yes      |
| legesher-i18n            | 0.1.0   | Yes      |
| legesher (CLI)           | 0.1.0   | Yes      |
| legesher-language-server | 0.1.0   | Yes      |
| legesher-vscode          | 0.1.0   | Yes      |

See individual package changelogs for full details:

- [legesher-core](libs/core/CHANGELOG.md) — Translation engine, git filters, metadata tracking
- [legesher-i18n](libs/i18n/CHANGELOG.md) — Language pack system, translation API, validation CLI
- [legesher (CLI)](libs/legesher/CHANGELOG.md) — translate, git, metadata commands
- [legesher-language-server](libs/language-server/CHANGELOG.md) — LSP with hover, completion, diagnostics
- [legesher-vscode](libs/vs-code/CHANGELOG.md) — VS Code extension with LSP client

---

## Project Overview

### Language Support

- **29 Languages**: am, ar, da, de, el, en, es, fi, fr, he, hi, hu, id, it,
  ja, ko, ms, nl, no, pl, pt, ru, si, sv, th, tr, ur, vi, zh
- **RTL Support**: Full right-to-left text handling for Arabic, Hebrew, and Urdu
- **Version-Aware**: Python 3.10, 3.11, 3.12, 3.13, 3.14 with pack inheritance

### Translation Engine

- **Token-Based Translator**: Preserves all formatting and comments (<2ms per file)
- **Tree-sitter Translator**: AST-based, production-ready (~160us for medium files)
- **Round-Trip Fidelity**: 100% (EN to ES to EN is byte-identical)
- **Git Filters**: Canonical English storage with automatic translation on checkout

### IDE Integration

- **Language Server**: Full LSP with hover, completion, diagnostics, semantic tokens
- **VS Code Extension**: Onboarding, translation panel, language selection, telemetry
- **Editor-Agnostic**: LSP design supports any compatible editor

### CLI Tools

- `legesher translate` — file, directory, and stdin/stdout translation
- `legesher run` — execute native-language Python directly
- `legesher git setup/status` — configure git filter integration
- `legesher config` — project configuration management
- `legesher init` — interactive and non-interactive project setup
- `legesher metadata` — translation history and audit trail

### Infrastructure

- **Monorepo**: UV workspace with 6 packages and pdm-backend builds
- **CI/CD**: Cross-platform lint and test workflows, semantic release
- **Pre-commit**: ruff, markdownlint, YAML validation, changelog enforcement
- **Testing**: 1,686+ automated tests across all packages

---

## Contributors

- **Madison Edgar** ([@madiedgar](https://github.com/madiedgar)) — Lead developer
- **Historical Contributors**: All contributors from the original
  Legesher repositories (2019-2024)

---

## Links

- [GitHub Repository](https://github.com/legesher/legesher)
- [Issue Tracker](https://github.com/legesher/legesher/issues)
- [Documentation](https://docs.legesher.io)

---

**Format**: [Keep a Changelog](https://keepachangelog.com/)
**Versioning**: [Semantic Versioning](https://semver.org/)
**License**: Multi-license (MIT for core packages, see [LICENSE](LICENSE))
