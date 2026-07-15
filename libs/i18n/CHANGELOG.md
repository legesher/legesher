# Changelog - legesher-i18n

All notable changes to legesher-i18n are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--next-version-placeholder-->

## [Unreleased]

## [0.22.0] - 2026-07-15

### Added

- **BCP 47 locale validator + audited backfill proposal (CORE-1500).** Prepares
  the language key to move from a 2-letter ISO 639-1 `code` to a BCP 47 locale
  tag. Additive only: `translations.db` is untouched, the primary key is not
  flipped, and no pack directory moves.
  - `legesher_i18n/bcp47.py` — parse / validate / canonicalize, in three
    strictness layers (well-formed, valid, canonical), plus `fallback_chain()`
    implementing RFC 4647 "Lookup" (`ar-EG` → `ar`).
  - `legesher_i18n/data/iana-language-subtag-registry.tsv` — a vendored IANA
    snapshot (File-Date `2026-06-14`, 9,296 records) so validation is offline
    and deterministic. Pinned in tests by record count **and** a SHA-256 of the
    data rows, so a truncated or silently-edited snapshot fails CI.
  - `legesher_i18n/db/migrations/bcp47_backfill.tsv` — the 56-row proposal.
    6 tags change, each script case decided from shipped pack content:
    `zh` → `zh-Hans`, `sr` → `sr-Cyrl`, `uz` → `uz-Latn`, `mn` → `mn-Cyrl`, and
    `no` → `nb`, `tl` → `fil` (all six confirmed by Madison 2026-07-15, along
    with `su` keeping the bare tag). The other 50 are unchanged; 48
    carry a registry `Suppress-Script`, so the bare tag is provably canonical.
  - A pack's locale is what its YAML `language:` field declares, **not** what
    its directory is called — so `no/` and `zh/` keep their directories, Python
    module names, and published dist names. The TSV records
    `current_pack_dir` and `default_slug_if_new` separately for exactly this
    reason.
  - `legesher_i18n/scripts/propose_bcp47_backfill.py` now **raises** rather than
    stamping a bare tag with an unverified "no script contrast" rationale when a
    language has no `Suppress-Script` and no editorial decision — the failure
    mode that would otherwise mis-tag `az`, `ku`, `sd`, `ha`, `ky`, `tg`, `ff`
    during the 103-language expansion.
  - `canonicalize()` validates and canonicalizes **variant** subtags like every
    other subtag (review fix): an unregistered variant (`en-foobar`) raises
    `ValueError` instead of passing through, and a deprecated variant with a
    registered replacement is substituted (`ja-Latn-hepburn-heploc` →
    `ja-Latn-hepburn-alalc97`), restoring the `is_canonical(canonicalize(x))`
    invariant.

## [0.21.3] - 2026-07-12

### Fixed

- **Four small database/provider quick wins (2026-07-12 Phase C review):**
  `TranslationDatabase.close()` previously closed only the calling thread's
  connection, leaking any opened from other threads — every connection is now
  tracked under a `threading.Lock` and closed together, and the class
  supports the context-manager protocol (`with TranslationDatabase() as db:`)
  [CORE-610]; `get_stats()` builds its four count queries as explicit
  literals instead of f-string table-name interpolation (defensive — the
  names were hardcoded) [CORE-609]; the default `db_path` resolves via
  `default_db_path()`, which detects the install location — a source
  checkout / editable install (no `site-packages`/`dist-packages` path
  component, `pyproject.toml` marker above the module) keeps the in-repo
  `legesher_i18n/db/translations.db` (unchanged behavior), while installed
  environments get `~/.legesher/translations.db`, seeded once from the
  bundled copy, so the bundled database is never mutated in place (CLI
  `db init`/`db stats`/`db vacuum` resolve the same default at command time
  instead of import time; `--db-path` overrides unchanged) [CORE-601]; and
  `api/providers/anthropic.py` passes mypy with 0 errors (was 10:
  `union-attr` on `context`/`_prompt_builder`/`client`, a `call-overload` on
  the kwargs dict, and a `no-any-return` in `_parse_json_response`) via local
  bindings that survive closure boundaries and an `isinstance` guard on the
  parsed JSON — no `type: ignore` suppressions [CORE-816].

## [0.21.2] - 2026-07-12

### Fixed

- **Three garbled pack translations caught while building the showcase cards:**
  `de` `str` shipped as `diestrTypKonvertierung` — a literal mash of "die str
  Typ Konvertierung" and, at 22 chars, the longest token across all 51 packs —
  now `Zeichenkette` (the ticket-specified standard German CS term, pending
  native review); `de` and `da` `repr` both shipped the *French*
  `représentation` (copy-paste leak), now `repräsentation` (de) /
  `repræsentation` (da). Fixed surgically in each pack's `3.10.yml` and
  `REFERENCE.md`; `translations.db` gets the corrections as new candidate rows
  plus flipped `selected_translations` (tagged `core-1303`, pending native
  review), mirroring the CORE-1317 pattern — no pack regeneration. [CORE-1303]

## [0.21.1] - 2026-07-12

## [0.21.0] - 2026-07-11

### Added

- **Selected translations for 5 under-covered core terms across all 51 Python
  language packs** — `__import__`, `type`, `encodingwarning`, `exceptiongroup`,
  and `baseexceptiongroup`, each previously present in only 0–5 languages in
  `selected_translations` despite mostly already shipping in the packs. This
  reconciles the DB to the shipped packs and adds the missing `__import__`
  builtin (generated as `__<word>__`, dunder-wrapped; experimental, pending
  native review) plus the missing `type` builtins in 22 packs. Driven by an
  idempotent, collision-guarded backfill script (`scripts/translate/backfill_core606.py`)
  that makes surgical, additive YAML edits — no full pack regeneration. [CORE-606]

### Fixed

- **Two pre-existing pack translation bugs surfaced by the collision guard:**
  `fi` shipped `exception` and `exceptiongroup` both as `ohje` (a round-trip
  collision) — `exceptiongroup` is now `poikkeusryhmä`; `de`
  `baseexceptiongroup` was the untranslated identity `BaseExceptionGroup`, now
  `Basisausnahmegruppe`. [CORE-606]

## [0.20.0] - 2026-07-09

## [0.19.0] - 2026-07-09

## [0.18.1] - 2026-07-09

## [0.18.0] - 2026-07-09

### Changed

- **`PromptBuilder` consumes the rules/profile style guide.**
  `_build_style_guide_section` now renders the fields the field reference marks
  as prompt-consumed: `naming.case_substitute` (plus the conventions the script
  can express, read from the `supports` flags), `script.name` /
  `script.direction` / `script.constraints`, and the `formatting` rules. It no
  longer reads the removed `translation` block — word choices, symbol names, and
  boolean constants come from the language packs, not the style guide. This
  activates the guides that were inert: CORE-1392/1393/1394 built the schema,
  the guides, and the loader; this is the consumer that puts them into the
  prompt.

## [0.17.1] - 2026-07-09

## [0.17.0] - 2026-07-09

### Changed

- **`StyleGuideLoader` now resolves the full `extends` chain; the pack gate
  gained an ASCII-digit check.** The loader follows each guide's declared
  `extends` list transitively (base → direction → script-family → language) with
  de-duplication and cycle detection, so the script-family overlays are
  consulted for their member languages — this supersedes the 0.14.0 note that
  the chain was "declarative for now." Parsed files are cached (each was read
  2–3× per load) and unsafe `extends` targets (path separators / `..`) are
  rejected. `SchemaValidator.validate_pack_strict` gained `check_ascii_digits`
  (identifiers must use ASCII digits 0-9) and stays safety-only: stylistic
  preferences such as identifier length are guidance for the translation prompt
  (CORE-1395), not pack warnings.

## [0.16.0] - 2026-07-09

### Added

- **Per-language style guides for all 51 languages, on the rules/profile schema.**
  Every language in `languages.json` now has a guide built on the schema shipped
  in 0.15.0: the `supports` capability flags (case conventions plus script
  profile — `native_digits`, `combining_marks`, `requires_word_separator`,
  `diacritics_in_identifiers`, `cursive_joining`), `naming` rules,
  `script.constraints` (including a per-language native-digit profile), and a
  rendering font. Rules only — the word choices, symbol names, and boolean
  vocabulary live in the language packs, not here. The capability flags are
  derived from / consistent with `languages.json`, and every guide passes
  `validate_style_guides.py`. es/zh/ur were migrated onto the same schema.
  These are structured first drafts; native review is on the rules (iterative,
  non-blocking), not per-term.
- **Base and family overlays aligned to the rules/profile schema.** The
  `python.yml` base and the eight family overlays (`_ltr`, `_rtl`, `_cjk`,
  `_arabic`, `_brahmic`, `_cyrillic`, `_ethiopic`, `_sea-spaceless`) were reduced
  to minimal structural nodes — `language`, `extends`, `version`, `status`, and
  documentation only. They previously carried old-schema content (`translation`,
  `symbol_vocabulary`, `register`, `text_direction`, …) that leaked into every
  merged language guide through the `extends` chain; with the overlays now
  content-free, a merged guide contains exactly the leaf language's rules. The
  loader-facing tests were migrated to assert the rules/profile shape.

## [0.15.0] - 2026-07-09

### Added

- **Style-guide schema, template, validator, and README.** The canonical,
  documented format for per-language Python style guides: `_schema.json` (the
  `supports` capability flags plus the `naming` / `script` / `formatting` /
  `rendering` structure and enums), a copy-to-add-a-language `_template.yml`, a
  `validate_style_guides.py` that checks structure and consistency with
  `languages.json` (the case flags match `has_case_distinction`, the direction
  matches `rtl`, the extends chain resolves), and a `README.md` field reference.
  Establishes a style guide as a set of English rules plus a language/script
  profile — the foundation the per-language guides are regenerated onto.

## [0.14.0] - 2026-07-05

### Added

- **Six script-family style overlays** (`_cjk`, `_brahmic`, `_arabic`,
  `_cyrillic`, `_ethiopic`, `_sea-spaceless`) extending the
  `python.yml` + `_ltr`/`_rtl` architecture, so per-language guides shrink
  to a handful of native-reviewer decisions. They encode: morphology as the
  case substitute for caseless scripts (callables are verb phrases, classes
  noun compounds), underscore as the universal separator (required for
  spaceless scripts), an explicit per-language constants strategy (no
  uppercase exists), abbreviation granularity per script (letters /
  characters / whole words), identifier length budgets, ASCII-digit policy,
  and the NFKC fixed-point rule (#4).
- **`symbol_vocabulary` sections** — what symbols are *called* in the target
  language (the underscore is universal in code; its name is not) — filled
  for es/zh/ur with slots for the remaining languages (#4).
- **`rendering.noto_font` hints** per script family so the extension renders
  packs with the right glyphs (Urdu = Noto Nastaliq Urdu, noted as needing
  taller line-height); `zh.yml`/`ur.yml` now extend their family overlays
  (#4).

  *Note:* the `extends` chain is declarative for now — `StyleGuideLoader` and
  `PromptBuilder` still merge base + direction + language directly, so the
  family overlays document intent but are not yet resolved at load time.
  Runtime resolution of the overlay chain is planned as a follow-up (#4).

## [0.13.1] - 2026-07-05

### Changed

- **Context briefs cover every term and describe only the term.** 61 new
  Tier-1 translation briefs complete coverage of the terms database (183
  files): the 58 previously missing exceptions (connection/os_io, file/OS,
  warning, arithmetic/encoding, runtime/memory/base, system/syntax/import
  families) plus `except*`, `self`, and `cls` — every runnable claim in
  their code examples executed against a live interpreter. 13 older briefs
  gained cross-references to the new siblings, and `index.json` was
  regenerated (182 entries).
- **Per-language translation content removed from all briefs.** The
  "Translation Examples (Good & Bad)" sections, es/ar/zh/hi
  existing-translation tables, and "Recommended Form by Language Family"
  prescription tables are gone (the latter retitled "Recommended Form",
  keeping the semantic form guidance and forms-to-avoid reasoning); the
  "Translation Output Format" block is a language-neutral placeholder.
  Rationale: unreviewed samples read as authoritative anchors and family
  prescriptions pre-commit what a linguist should derive — concrete examples
  now belong to prompt assembly, injected from live pack data. English
  etymology, English-meaning ambiguity analysis, and Unicode-demo code
  (`ascii`/`chr`/`ord`/`str`) are kept. The tier-1 template and the
  validator's required-section list (now 10 sections) match the new shape
  (#2).

### Fixed

- **Fabricated `basegeneratorexit` term removed everywhere.** The name is not
  a real Python exception — it originated in `term_definitions.py`
  (mislabeled "3.12+ internal") and propagated into the database and every
  shipped pack; it was flagged as a shipped-pack corruption during the
  Unicode audit. Removed from `translations.db` (1 term + 82 candidate
  translations + 27 selected translations, cascade-verified; 181 terms
  remain), the `term_definitions.py` source line, and 51 pack YAML + 50
  REFERENCE.md files. The collision audit passes on the resulting tree (#3).

## [0.13.0] - 2026-06-11

### Added

- **Unicode / script safety validation layer for language packs**
  (51 -> 103 expansion hardening). A new `legesher_i18n/script_policy.py`
  module is the single source of truth for which Unicode scripts and format
  characters are legitimate in each of the 51 shipped languages, via a
  per-language `ScriptPolicy` (allowed scripts, writing direction, allow-listed
  format chars, NFKC normalization). Script detection (`scripts_of`) is built on
  pure `unicodedata` — no new third-party dependency. `SchemaValidator` gains a
  `Finding` dataclass and six new safety checks plus an aggregator:
  - `check_normalization` — value must equal its NFC and NFKC forms (catches
    Thai SARA AM / Lao U+0EB3 instability that breaks identifier round-tripping).
  - `check_script_consistency` — rejects foreign-script bleed-through (e.g.
    Chinese `布尔` in a Polish `bool`, Cyrillic in Thai, Hangul in Hindi) against
    the per-language allowlist; default-deny for unregistered codes.
  - `check_format_chars` — rejects bidi controls (U+202A-202E / U+2066-2069 /
    U+200E / U+200F / U+061C), tatweel (U+0640), and the BOM (U+FEFF), plus any
    `Cf` format char not explicitly allow-listed (Sinhala ZWJ, Persian/Urdu
    ZWNJ).
  - `check_keyword_collisions` — a translation must not equal (nor NFKC-fold to)
    a live Python keyword/soft-keyword/builtin unless it is that key's own
    target; catches the fullwidth `ｉｆ` -> `if` spoof and active-keyword
    collisions (`globals` -> `global`, `except*` -> `except`, `print` -> `in`).
  - `check_min_interpreter_identifier` — static XID membership check flagging
    ZWJ/ZWNJ-bearing values (e.g. Sinhala conjuncts) whose pack declares a
    minimum interpreter below 3.13. The boundary is the CPython version, not a
    single Unicode version: 3.10/3.11/3.12 ship Unicode 13.0/14.0/15.0 and raise
    `SyntaxError` on these, while 3.13+ (Unicode 15.1) accepts them as XID. Never
    calls `compile()`, so the check is deterministic on any interpreter.
  - `validate_pack_strict` — runs all of the above plus the previously-dead
    `check_duplicates` and `check_identifier_validity` passes (the intentional
    `keywords.type == builtins.type` duplicate is allow-listed).
- **`legesher_i18n/scripts/audit_packs.py`** — audits every working-tree pack
  with `validate_pack_strict`, prints a report grouped by language and
  finding-code, and exits non-zero on findings. Runnable as
  `python -m legesher_i18n.scripts.audit_packs [--lang CODE] [--quiet]`.
- **`.github/workflows/validate-packs.yml`** — CI job running the audit in
  **non-blocking** (`continue-on-error`) report mode while data-correction PRs
  are still pending. Flips to blocking pre-103-expansion.
- **New test suites** under `libs/i18n/tests/` (all green, synthetic fixtures):
  `test_unicode_normalization.py`, `test_script_consistency.py`,
  `test_format_chars.py`, `test_keyword_collisions.py`, `test_path_traversal.py`,
  `test_min_interpreter_identifier.py`, `test_script_policy_coverage.py`
  (asserts all 51 codes are policied + unknown -> default-deny), and
  `test_new_language_onboarding.py` (a golden "what a new pack must satisfy"
  checklist that doubles as onboarding docs).

### Fixed

- **Path-traversal guard in `LanguagePackLoader.load`.** The `version` argument
  was joined directly into a pack filename (`{version}.yml`) with no validation,
  making it a path-traversal primitive. `load` now validates `version` against
  `^(\d+\.\d+|default)$` and raises `ValueError` for anything else, before any
  filesystem access. `version=None` (load `default.yml`) is still accepted; the
  `lru_cache` is preserved.

## [0.12.0] - 2026-06-11

## [0.11.3] - 2026-06-11

### Added

- **Database**: Seeded 6 Ukrainian (`uk`) keyword/builtin translations from the
  language-showcase work (`def`, `print`, `return`, `if`, `str`, `None`; source
  `claude`) and set them as `uk`'s provisional selected translations — `uk`
  previously had community suggestions but no selections. Drafts pending native
  review; to be reused on the next `uk` translation run. [CORE-1299]

## [0.11.2] - 2026-05-14

### Changed

- **`CohereAyaProvider` error logs now surface exception class + SDK metadata**
  ([CORE-870]). The previous `logger.error("Cohere Aya translation failed: %s", e)`
  pattern called `str(e)` directly, which returns an empty body for some
  cohere V2 SDK exceptions (notably `TooManyRequestsError`) whose message
  lives on `.body` / `.headers` attributes. Result was log lines ending in
  `Cohere Aya translation failed:` with nothing after the colon. Now every
  error log + raised `TranslationError` includes `type(e).__name__`, falls
  back to `repr(e)` when `str(e)` is empty, and surfaces `status_code` /
  `code` / `x-debug-trace-id` from response headers when present. Logging
  itself is wrapped in defensive try/except so a malformed exception can
  never break the logger. Discovered while diagnosing AYA-213 cond5
  failures: 18 of 28 logged failures rendered as empty errors that turned
  out to be 429 rate limits in disguise. Touches
  `libs/i18n/legesher_i18n/api/providers/cohere_aya.py` plus a new
  `libs/i18n/tests/test_cohere_aya_error_fidelity.py` covering empty-str,
  ApiError-shaped, non-empty-str, and broken-metadata cases.

## [0.11.1] - 2026-05-07

## [0.11.0] - 2026-05-03

### Added

- **PromptBuilder `_CRITICAL_RULES` "no structured/labeled output format"
  rule** (CORE-1048). Second, narrower bullet appended to `_CRITICAL_RULES`
  that explicitly forbids wrapping a translation in any structured
  key/value, label, JSON, or paired format, and forbids joining the
  original identifier to the translation with separators like
  `original_name_X_translated_name_Y`. Smaller models (`tiny-aya-global`
  3.35B params, observed on cond5 ur) follow the CORE-950 "no explanation"
  rule but still emit labeled mappings — distinct failure mode that the
  prior wording buried in a single multi-clause bullet. Two distinct list
  items render as two distinct constraints, which materially improve
  prompt-following salience for small models. Universal rule (no
  per-model override). [CORE-1048]

## [0.10.1] - 2026-05-01

### Fixed

- **`TestCrossSectionCollisionGate` Windows encoding bug**
  ([CORE-1126]): three `pack_yml.write_text(...)` calls in the
  CORE-950 integration tests were missing explicit
  `encoding="utf-8"`. On Windows the system codepage (cp1252)
  can't encode Arabic/Urdu pack content -> `UnicodeEncodeError`
  before the validator was even invoked. Added explicit utf-8
  encoding; tests pass cross-platform now. No product behavior
  change.

## [0.10.0] - 2026-05-01

### Added

- **PromptBuilder `forbidden_values` kwarg** on `build_identifier_prompt`.
  Renders a "Reserved Translation Values" block in the user prompt so the
  LLM is unlikely to propose a translation that collides with reserved pack
  values (`keywords` / `builtins` / `exceptions` / `reserved_words` from
  CORE-710). Caller passes the flat list; deduplication and a 500-entry cap
  happen inside the formatter. Threaded end-to-end through the three
  PromptBuilder-aware providers (`anthropic`, `cohere_aya`, `openai_compat`)
  and `LLMTranslator._translate_identifiers`. [CORE-950]
- **PromptBuilder `examples` kwarg** on `build_identifier_prompt` and
  `build_text_prompt`. Few-shot anchoring via `[{"original": str,
"translation": str}, ...]` rendered in the user prompt as a "Few-Shot
  Examples" table. Capped at 25 entries (3-10 is the research sweet spot;
  25 is generous headroom for callers anchoring on multiple term families).
  Malformed entries are skipped with a `logger.warning` so a caller with a
  typo (`origin` instead of `original`) gets a visible signal. [CORE-950]
- **PromptBuilder `preserve_module_names` flag** on `__init__` (keyword-only,
  default `False`). When `True`, the system prompt instructs the model to
  leave module/library import names (`torch`, `numpy`, etc.) literally
  unchanged. The default preserves Cond-5 full-translation behavior;
  execution-targeted use cases flip the flag. [CORE-950]
- **Script-aware `snake_case` substitute rule** (CORE-950). When the target
  language's script lacks upper/lowercase distinction, `_CRITICAL_RULES`
  emits a rule that overrides the base "PascalCase stays PascalCase"
  guidance. Two-tier lookup: per-language style guide override
  (`script.has_case_distinction`) wins; otherwise read from
  `languages.json`'s new `has_case_distinction` field; default `True`.
  Covers all 17 non-cased supported languages (Arabic family, CJK, Brahmic,
  SE-Asian, Ge'ez). Empirically validated against `gemma3:12b` on `ja`
  (clean Kanji) and `ur` (clean Urdu Nastaliq). [CORE-950]
- **`languages.json` schema field**: `has_case_distinction: bool` for all
  51 supported languages (sits next to `rtl`). Now the canonical source of
  truth for language script properties; `LANGUAGE_CASE_DISTINCTION` is
  loaded at module import. [CORE-950]
- **Cross-section collision audit script**:
  `libs/i18n/scripts/audit_collisions.py` runs both DB-level
  (`legesher-i18n db collisions`) and pack-level
  (`schema_validator.cross_section_collisions`) audits across the canonical
  pack list derived from `languages.json`. Fails on missing or misnamed
  packs (regression-protection contract). Wired into the `lint` job in
  `.github/workflows/ci.yml`. [CORE-950]

### Changed

- **`_CRITICAL_RULES` no-trace-wrapper rule**: each translation value the
  LLM emits must be the bare translation — explicitly forbids prefix /
  suffix / explanation / markup / trace-format wrappers, citing the
  `__original_X_translation_Y_Explanation_...` and
  `____translated_identifier_X____` patterns observed empirically on
  `gemma3:12b` zh+ur and Tiny Aya GGUF. Wording clarifies the rule applies
  to individual values inside the response structure, not to the JSON
  object/list output format. [CORE-950]
- **Legacy fallback prompts** in `cohere_aya.py:_SYSTEM_PROMPT` and
  `openai_compat.py:_SYSTEM_PROMPT` now carry the same no-trace-wrapper
  guidance — the path that fires when `PromptBuilder` fails to initialize
  no longer regresses to a weaker prompt. (Anthropic's legacy fallback
  uses structured-JSON output and is unaffected.) [CORE-950]
- **CohereAyaProvider token-count read path**: defensive multi-path lookup
  (`usage.tokens.X` → `usage.billed_units.X` → direct attributes) covers
  Cohere V2 SDK 6.x build variants. Fixes `tokens_in/tokens_out=0`
  regression that broke `get_usage()` totals and `cost_estimate_usd`.
  [CORE-950]
- **`validate_language_pack_yaml.py` collision detection** uses
  `SchemaValidator.check_duplicates()` as the single source of truth.
  Previously the script's own ad-hoc duplicate pass produced double error
  messages for cross-section collisions involving keyword/builtin/exception
  pairs (Copilot review on PR #237). Side benefit: extends coverage to
  reserved_words / operators / standard_library intra-section duplicates
  that the local pass missed. [CORE-950]

### Fixed

- **Pre-commit hook now blocks cross-section collisions at YAML edit time**.
  The existing `validate-language-pack-yaml` hook calls
  `SchemaValidator.check_duplicates()`'s `cross_section_collisions` output
  so a pack edit introducing the AYA-213 Cycle-4 Urdu failure mode (e.g.
  `reserved_words.self` matching `keywords.in`) fails fast before commit.
  Integration test in `tests/integration/test_validate_pack_yaml_cross_section.py`.
  [CORE-950]

## [0.9.3] - 2026-04-29

### Added

- **Reserved Words category**: New `reserved_words:` section in pack YAML
  schema for translating Python conventions like `self` and `cls`
  deterministically (CORE-710 closes the AYA-213 Cycle-4 Urdu
  `self → میں` collision failure mode). All 51 packs ship with self/cls
  translations selected via reflexive-pronoun framing. [CORE-710]
- **Schema**: `LanguagePackSchema.reserved_words` field (optional,
  defaults to empty); extended `check_duplicates`,
  `check_identifier_validity`, `get_validation_report` with
  reserved_word coverage. [CORE-710]
- **Term system**: `TermCategory` Literal extended with
  `"reserved_word"`; `RESERVED_WORDS = ["self", "cls"]` canonical list;
  `get_reserved_words_for_version()` accessor;
  `TERM_TYPE_YAML_SECTIONS` mapping includes
  `"reserved_word" → "reserved_words"`. [CORE-710]
- **Database**: `terms.category` accepts `reserved_word`; backfilled 16
  missing language rows (`bs, ca, cs, fa, gd, gl, hr, kn, lv, mk, mn,
my, ro, sr, su, uz`) into the languages table. [CORE-710]

### Changed

- `mypy --strict` now passes on public API files (`__init__.py`, `pack_loader.py`,
  `language_registry.py`, `version_detector.py`, `version_index.py`,
  `schema_validator.py`, `prompt_builder.py`, `style_guides.py`, `exceptions.py`).
  Fixes: added `dict[str, Any]` annotation to the `results` accumulator in
  `SchemaValidator.check_completeness_enhanced` so `.append()` / numeric comparisons
  on its values type-check; added `-> None` to `LanguagePackLoader.clear_cache`;
  rewrote `get_language_name`, `get_native_name`, and `is_rtl_language` in
  `language_registry.py` to narrow the TypedDict before chained `.get()` calls
  (strict mode rejects the `.get(key, default)` default-as-dict pattern on
  TypedDicts since the default must match the specific key's value type).
- Added `py.typed` marker (PEP 561) so downstream consumers type-check imports
  from `legesher_i18n` correctly. This also resolves cross-package type-check
  errors in `legesher_core` that previously surfaced when it imported
  `LanguagePackLoader`. (CORE-1183)

- Fill in Google-style docstrings on 10 public classes and the `language_registry`
  module docstring: `LanguagePackLoader`, `PromptBuilder`, `StyleGuideLoader`,
  `LanguagePackMetadata`, `LanguagePackSchema`, `SchemaValidator`,
  `PythonVersionDetector`, `PythonVersionInfo`, `VersionIndex`. Converts remaining
  NumPy-style section headers (`Parameters`/`Returns`/`Raises`) in `prompt_builder.py`
  and `style_guides.py` methods to Google-style (`Args:`/`Returns:`/`Raises:`) for
  consistency with the class-level docstrings. Document the `LANGUAGE_METADATA` and
  `CANONICAL_LANGUAGE` module-level constants in `language_registry.py` since Python
  constants cannot carry their own `__doc__`. Docstring-only; no code behavior
  changes. (CORE-1173)

## [0.9.2] - 2026-04-20

### Fixed

- Collapse duplicate `__all__` assignment in `legesher_i18n/__init__.py` into one
  canonical list of 30 exported names. The previous file declared `__all__` twice;
  Python rebinds on the second assignment, so the first list was dead code. The two
  lists had diverged — `PromptBuilder` and `StyleGuideLoader` were absent from the
  live `__all__` while `load_language_pack` was absent from the dead one.
  `from legesher_i18n import *` now includes all exported symbols. Direct imports
  (`from legesher_i18n import PromptBuilder`) were unaffected. (CORE-1174, #224)

## [0.9.1] - 2026-04-17

## [0.9.0] - 2026-04-10

## [0.8.1] - 2026-04-03

## [0.8.0] - 2026-04-02

### Added

- Per-language coding style guides (PEP 8 equivalents) for zh, es, ur with hierarchical
  YAML files: `python.yml` (base) -> `_ltr/_rtl.yml` (direction) -> `{lang}.yml` (CORE-706)
- `StyleGuideLoader`: loads and deep-merges hierarchical style guide files with in-memory caching
  and RTL auto-detection from `languages.json` (CORE-706)
- `PromptBuilder`: provider-agnostic prompt composition returning cacheable
  `(system_prompt, user_prompt)` tuples with language framing, style rules, identifier
  glossary, and string preservation rules (CORE-706)
- Shared `response_parser.parse_llm_response()` for extracting translations from
  JSON responses across all LLM providers (CORE-706)
- `context` parameter added to `TranslationProvider.translate()` base class and all
  6 provider implementations for forwarding PromptBuilder context (CORE-706)
- PromptBuilder wired into Anthropic, OpenAI-compat, and Cohere Aya providers (CORE-706)
- Cohere Aya API translation provider (`CohereAyaProvider`) for hosted Aya models (AYA-191)
- OpenAI-compatible translation provider (`OpenAICompatProvider`) for local models —
  works with vLLM, Ollama, llama.cpp, LocalAI (AYA-191)
- `ProviderBackendAdapter` bridging async `TranslationCoordinator` to sync
  `TextTranslationBackend` protocol from legesher-core (AYA-191)

### Fixed

- Backend adapter forwards per-item context to providers instead of discarding it;
  uses batch API when no context is present for performance (CORE-706)
- Coordinator skips cache when context is provided (different prompts per context) (CORE-706)
- Cohere/OpenAI-compat provider exceptions wrapped in `TranslationError` for
  coordinator fallback handling (AYA-191)
- OpenAI-compat provider handles `base_url` with or without `/v1` suffix (AYA-191)
- OpenAI-compat catches JSON decode and response shape errors as `TranslationError` (AYA-191)
- Batch adapter returns original text for failed translations instead of empty strings (AYA-191)

## [0.7.3] - 2026-03-19

## [0.7.2] - 2026-03-18

- Version bump to align with foundation suite (no functional changes)

## [0.7.1] - 2026-03-16

## [0.7.0] - 2026-03-16

### Added

- **22 new language packs** — expanding Legesher from 29 → 51 supported
  languages (CORE-675, CORE-707)
  - **Bengali (বাংলা)** (CORE-718), **Bosnian (Bosanski)** (CORE-720),
    **Catalan (Català)** (CORE-735), **Croatian (Hrvatski)** (CORE-742),
    **Czech (Čeština)** (CORE-744), **Galician (Galego)** (CORE-756),
    **Gujarati (ગુજરાતી)** (CORE-764), **Irish (Gaeilge)** (CORE-769),
    **Kannada (ಕನ್ನಡ)** (CORE-795), **Latvian (Latviešu)** (CORE-807),
    **Macedonian (Македонски)** (CORE-808)
  - **Malayalam (മലയാളം)** (CORE-837), **Mongolian (Монгол)** (CORE-848),
    **Burmese (မြန်မာ)** (CORE-853), **Persian (فارسی)** (CORE-860),
    **Romanian (Română)** (CORE-879), **Scottish Gaelic (Gàidhlig)** (CORE-905),
    **Serbian (Српски)** (CORE-906), **Sundanese (Basa Sunda)** (CORE-915),
    **Telugu (తెలుగు)** (CORE-954), **Uzbek (O'zbek)** (CORE-961),
    **Welsh (Cymraeg)** (CORE-962)
  - Each pack includes complete Python 3.10–3.14 translations (37 keywords,
    72 builtins, 66 exceptions) with version inheritance
  - 3,850 new translations (175 per language × 22 languages)
  - Zero collisions across all 51 languages
  - Translation sources: Aya-101 AI Model (21 packs), Claude AI (Bosnian)
  - Persian (fa) is the 4th RTL language (joining Arabic, Hebrew, Urdu)
  - 3 Celtic languages added: Irish, Scottish Gaelic, Welsh
- **Language registry**: 22 new entries in `languages.json` with full metadata
  (native names, ISO 639-2 codes, script/family/numeral system)
- **REFERENCE.md**: Generated translation reference docs for all 22 new packs

## [0.6.0] - 2026-03-11

### Added

- **3 new language packs** — expanding Legesher from 26 → 29 supported
  languages (CORE-687)
  - **Amharic (አማርኛ)**: First Ge'ez-script language — complete Python
    3.10–3.14 translations (37 keywords, 72 builtins, 66 exceptions) with
    zero collisions. Translation source: Claude AI Model (CORE-690)
  - **Sinhala (සිංහල)**: First South Asian script language — complete Python
    3.10–3.14 translations (37 keywords, 72 builtins, 66 exceptions) with
    zero collisions. Translation source: Claude AI Model (CORE-1128)
  - **Urdu (اردو)**: Third RTL language in Legesher (joining Arabic and
    Hebrew) — complete Python 3.10–3.14 translations (37 keywords, 72
    builtins, 66 exceptions) with zero collisions. Translation source: Tiny
    Aya AI Model (CORE-1071)
  - 540 new translations imported into the translation database (180 per
    language, 0 collisions across all 29 languages)
  - Translation database updated: 40 total languages (29 YAML packs + 11
    legacy community)
- **Generic HuggingFace translation engine** — pluggable architecture for
  AI-powered translations, making it trivial to add new models (CORE-686)
  - `HFModelProfile` dataclass + registry — adding a new HF model requires
    only ~10 lines of profile config
  - `HuggingFaceModel` — local inference engine with lazy model loading,
    device auto-detection (CUDA/MPS/CPU), and retry with exponential backoff
  - `HuggingFaceAPIModel` — cloud inference engine via HF Inference API with
    built-in rate limiting
  - 4 pre-registered Tiny Aya (3.35B) profiles: earth, fire, water, global
    (CohereLabs/tiny-aya-{variant}) targeting underserved languages
  - New CLI flags: `--models hf|hf-api|tiny-aya|tiny-aya-api`,
    `--hf-profile <name>`, `--tiny-aya-variant earth|fire|water|global`
  - `DEFAULT_LANGUAGE_NAMES` mapping with 70+ languages (ISO 639-1 and 639-3)
  - 40 unit tests covering profiles, registry, prompt builder, dry-run
    translations, and pipeline validation — all run without ML dependencies

## [0.5.1] - 2026-03-01

### Changed

- **Consolidate Translation Databases** (CORE-594)
  - Redesign from flat single-table schema to normalized 4-table schema
    (`terms`, `languages`, `translations`, `selected_translations`)
  - Consolidate 3 drifted SQLite databases into one source of truth:
    179 terms, 38 languages, 2,445 translations, 4,527 selected translations
  - Rewrite `TranslationDatabase` API to use `term_id` foreign keys with
    cascading deletes instead of string-based `term`/`term_type` columns
  - Add `selected_translations` table decoupling active translation choices from suggestion sources
  - Add `terms` table with `UNIQUE(name, programming_language)` for multi-language extensibility
  - Add `languages` table preserving all 26 YAML pack languages + 12 legacy community languages
  - Update `pipeline.py`, `import_yaml_to_db.py`, `yaml_exporter.py` for new schema
  - Add CLI `db` subcommands: `init`, `stats`, `vacuum`
  - Rewrite test suite for new schema (40 unit tests, 4 integration tests)

### Fixed

- **Resolve 41 translation collisions across 17 languages** (CORE-605)
  - Same translated word mapped to 2+ Python terms, breaking round-trip translation
  - Add `find_collisions()` API and `db collisions` CLI command
  - Add collision guard to `set_selected()` preventing future collisions
  - Upgrade pre-commit YAML validator from warnings to errors for duplicates
  - Bump affected packs to v0.0.3: ar, el, fi, he, hi, hu, it, ko, no, pl, pt,
    ru, sv, th, tr, vi, zh
- Replace `datetime.UTC` with `timezone.utc` for Python 3.10 compatibility (CORE-662)

## [0.5.0] - 2026-02-01

### Changed

- Version bumped to align with monorepo v0.5.0 release
- No functional changes beyond 0.4.1 for i18n infrastructure

## [0.4.1] - 2026-01-31

### Added

- **Bundle Language Packs in i18n Wheel** (CORE-559)
  - Language pack YAML files now included directly in the `legesher-i18n` wheel
  - Users no longer need to install separate language pack packages
  - All 26 language packs available out of the box

### Fixed

- **Fix 33 mixed-script translations across 5 language packs** (CORE-531)
  - Greek (el): 15 entries — remove Latin characters, fully translate to Greek
  - Hebrew (he): 8 entries — remove Latin/Cyrillic, fix `property` invalid identifier (had `"` quotes)
  - Russian (ru): 8 entries — remove Latin characters, fully translate to Cyrillic
  - Arabic (ar): 1 entry — fix `memoryview` mixed Latin+Arabic
  - Finnish (fi): 1 entry — fix `isadirectoryerror` mixed scripts
- **Fix Japanese `in` keyword** (CORE-531): `～が～の中にある` → `含む` (valid Python identifier)
- **Add missing `type` builtin** to Spanish (`tipo`) and Arabic (`نوع`) packs (CORE-531)

## [0.4.0] - 2026-01-27

### Changed

- Version bumped to align with monorepo release
- No functional changes beyond 0.2.1 for i18n infrastructure

## [0.2.1] - 2026-01-26

### Added

- **New CLI Export Commands** (CORE-555)
  - `export json`: Export language pack to JSON format with Python doc links
  - `export csv`: Export language pack to CSV format with examples
  - `export all`: Export all available language packs with progress bar
  - All export commands support `--output -` for stdout piping
  - All export commands support `--dry-run` for preview mode
  - All commands now support `--quiet/-q` flag for CI/script usage

- **New CLI Registry Commands** (CORE-555)
  - `registry list`: List all available language packs with status
  - `registry validate`: Validate language pack translations against English reference
  - Support for `--strict` mode that fails on warnings

- **REFERENCE.md Auto-Generation** (CORE-555)
  - `scripts/generate_reference_docs.py` generates comprehensive REFERENCE.md for all 25 languages
  - Merges all version YAML files (3.10-3.14) with proper inheritance
  - Pre-commit hook auto-regenerates when YAML files change
  - Localized example code for each language

- **GitHub Actions Sync Workflow** (CORE-555)
  - `.github/workflows/sync-reference-docs.yml` syncs REFERENCE.md to preview-repo repo
  - Triggers on REFERENCE.md changes to main branch
  - Supports manual dispatch with force-sync option

- **Language Name Fallbacks** (CORE-555)
  - Added `LANGUAGE_NAME_FALLBACKS` dictionary for 26 common languages
  - Cached `_get_language_name()` function with `@lru_cache` for performance

### Changed

- **Schema Validator Enhanced Soft Keyword Support** (CORE-555)
  - `check_identifier_validity()` now passes source_key for soft keyword translations
  - Translations of soft keywords (e.g., `excepto*` for `except*`) validate correctly

### Fixed

- **Schema Validator Soft Keywords Support** (CORE-555)
  - Added `SOFT_KEYWORDS` set to handle Python 3.11+ soft keywords like `except*`
  - `except*` now passes schema validation instead of failing as invalid identifier
  - Translations of soft keywords also validate correctly (e.g., `excepto*` for Spanish)
  - Reference: <https://docs.python.org/3/reference/lexical_analysis.html#soft-keywords>

- **CLI Test Version Assertion** (CORE-555)
  - Fixed test expecting "0.0.1" to correctly expect "0.2.0"

## [0.2.0] - 2026-01-25

### Added

- **New Language Packs** (v0.2.0)
  - English (en): 39 keywords, 71 builtins, 69 exceptions, Python 3.10-3.14 (canonical reference)
  - All 26 languages: Complete translations via Aya AI Model pipeline

- **Comprehensive Directory Structure Tests** (PR #49)
  - New test file `tests/test_directory_structure.py` with 12 tests
  - Validates directory existence, path configuration, and inheritance
  - Tests PackLoader default path, YAML exporter, and CLI validation
  - Ensures backward compatibility (old `languages/` path not used)

### Changed

- **Language Pack Reorganization into Hierarchical Structure** (CORE-530)
  - Reorganized language packs from `programming_languages/` into hierarchical `language-packs/python/{lang}/` structure
  - Each language pack is now an independently versioned package (ar, es, en, fr, zh, etc.)
  - Enables focused releases per language (e.g., `python-ar` v1.2.0 independent of `python-es` v1.0.5)
  - Refactored `LanguagePackLoader` with importlib-based package discovery
  - Updated language-server integration to use new paths
  - Renamed legacy community archive: `language-packs/` → `language-packs-archive/`

- **Language Pack Version Constraints**
  - All language packs now require `>=0.2.0,<1.0.0`
  - Added Python 3.14 support across all language packs
  - Improved translation quality using Aya AI Model pipeline

### Fixed

- **Spanish Language Pack YAML Boolean Parsing** (PR #49)
  - Fixed `not: no` being parsed as boolean `False` instead of string `"no"`
  - Used YAML `!!str` type tag to force string type: `not: !!str no`
  - Fix survives pre-commit pretty-format-yaml hook

- **Python 3.14 Language Pack Support** (PR #49)
  - Added Python 3.14 language packs for all languages
  - Updated compatibility metadata in 3.10-3.13 packs to include 3.14
  - Fixed English language pack: expanded builtins, added `except*` keyword (3.11), corrected metadata

## [0.1.0] - 2025-11-07

### Added

- **Version-Aware Language Pack System** ([#3](https://github.com/madiedgar/legesher/pull/3), [b4c01f5](https://github.com/madiedgar/legesher/commit/b4c01f5c67d3a8025b39dc6196f58646d6f8fb04))
  - Dynamic language pack loading with automatic Python version detection (3.10-3.13+)
  - Pack inheritance system where child packs extend parents by defining only new features
  - Multi-strategy Python version detection: `pyproject.toml` → `.python-version` → runtime
  - Comprehensive security: path traversal protection, circular inheritance detection
  - High-performance caching for repeated pack loads
  - Complete Spanish (es) and Arabic (ar) language packs across all Python versions
  - `LanguagePackLoader` with version awareness and inheritance resolution
  - `PythonVersionDetector` for automatic environment version detection
  - `VersionIndex` for managing pack compatibility and inheritance chains
  - `SchemaValidator` with Pydantic-based validation
  - Package structure follows PEP 8 naming conventions (legesher_i18n)
  - Dependencies: pyyaml, pydantic, packaging

- **Translation Infrastructure and Language Packs** ([#14](https://github.com/madiedgar/legesher/pull/14), [5785621](https://github.com/madiedgar/legesher/commit/5785621a18ea1aecc00fb85735798efb38b4a624))
  - Complete translation infrastructure with bidirectional keyword mapping
  - Example language packs demonstrating inheritance and version-specific features
  - Two-tier context template system for AI and human translators
  - **Tier 1 Template** (1000-1500 words): Optimized for AI translation models with examples-first approach
  - **Tier 2 Template** (5000+ words): Comprehensive reference for human translators and beta testers
  - Comprehensive linguistic standards covering 8 critical areas:
    - Register & Formality Strategy (language-specific definitions)
    - Transliteration vs Translation Rules (decision framework)
    - Compound Term Strategy (builtins like isinstance, hasattr)
    - Capitalization & Case Conventions (comprehensive cross-script)
    - RTL Language Practical Requirements (Arabic, Hebrew IDE testing)
    - Ambiguity Resolution Framework (4-priority hierarchy)
    - Honorific & Politeness Levels (Japanese, Korean, Hindi neutral forms)
    - Gendered Language Rules (Romance, Arabic, German consistency)
  - Documentation expanded from 334 to 1,468 lines for translation quality
  - Expected AI translation approval rate: 85-90%

- **Auto-Update GitHub Actions Workflow** ([#20](https://github.com/madiedgar/legesher/pull/20), [033c822](https://github.com/madiedgar/legesher/commit/033c8223a6ccc733041604e809bb6bb30c070a72))
  - Automated monitoring of CPython repository for new major releases
  - Python content extraction script for all localizable elements:
    - 39 keywords (35 hard + 4 soft) via keyword module
    - 49 built-in functions with docstrings for IDE hover support
    - Built-in types with categorization
  - Two extraction methods: runtime (default) and GitHub API fetch
  - Multi-version support with comprehensive JSON output and metadata
  - GitHub Actions workflow for detecting new Python versions within 1 week
  - Automatic issue creation for new version language pack updates
  - Zero external dependencies beyond stdlib (urllib, json, yaml)
  - Successfully tested with Python 3.14 (184 items extracted)
  - Scripts: `extract_python_content.py`, `monitor_python.py`, `generate_language_pack.py`, `translate_content.py`

- **Translation API Integration** ([#22](https://github.com/madiedgar/legesher/pull/22), [71b40dd](https://github.com/madiedgar/legesher/commit/71b40dd78dfc933bbfcc45105c78b4f649910a91))
  - Multi-provider translation API with quality-based fallback system
  - Three translation providers with unified interface:
    - **DeepL**: Premium quality for European languages (133+ languages)
    - **Google Translate**: Best for Asian languages with broad coverage
    - **LibreTranslate**: Self-hosted, open-source, privacy-focused (20+ languages)
  - Quality scoring matrix for language pair optimization
  - Intelligent provider selection based on quality scores per language pair
  - Async/await support for high-performance translation
  - Usage tracking: characters translated, request counts, cost estimation
  - Rate limiting (10 req/sec default, configurable per provider)
  - SQLite and Redis cache backends for translation caching
  - Quality validator for translation verification
  - Usage tracker with cost monitoring and analytics
  - Dashboard for monitoring translation API usage and costs
  - CLI tools: `legesher-api` for provider management and monitoring
  - Optional installation: `pip install legesher-i18n[api]`
  - Zero cost option via self-hosted LibreTranslate

- **Comprehensive Language Pack Validation** ([#23](https://github.com/madiedgar/legesher/pull/23), [aa7ff26](https://github.com/madiedgar/legesher/commit/aa7ff268a1d640376c078d3273bc2f9c0557abb7))
  - MLCP v1.0 specification conformance validation
  - Three conformance levels: core (keywords), extended (+operators), full (+stdlib)
  - Duplicate detection across all mapping types (keywords, operators, builtins)
  - Enhanced completeness checking with version-index integration
  - Extended MLCP v1.0 schema supporting:
    - Operators (arithmetic, logical, comparison, bitwise)
    - Standard library mappings
    - Cultural notes and annotations
  - ISO 639-1/639-2 language code validation (2-3 letter codes)
  - Comprehensive error reporting with actionable messages
  - VALIDATION.md documentation (comprehensive validation guide)
  - Test coverage: 25+ validation tests across conformance levels
  - Schema enhancements: +350 lines to `schema_validator.py`
  - Security: validates pack structure, prevents malformed packs

- **Language Pack Validation CLI and Compatibility Matrix** ([#24](https://github.com/madiedgar/legesher/pull/24), [bda4dc9](https://github.com/madiedgar/legesher/commit/bda4dc93a66bf9616eed76df319b4502382d1757))
  - Command-line interface for language pack validation and testing
  - Compatibility matrix generator for keyword coverage across Python versions
  - Interactive validation with rich terminal output (colors, tables, progress bars)
  - Commands:
    - `validate`: Validate language pack YAML files with MLCP conformance
    - `test`: Test pack loading and inheritance resolution
    - `matrix`: Generate keyword compatibility matrix across Python versions
    - `info`: Display detailed pack information and statistics
  - Matrix generation script: `generate_compatibility_matrix.py`
  - Markdown documentation generation for compatibility (e.g., `es-keywords.md`)
  - Pre-commit hook documentation for automated validation
  - CI/CD integration documentation for GitHub Actions
  - Entry point: `legesher-i18n` command
  - Dependencies: click (CLI framework), rich (terminal formatting)
  - CLI test coverage: 260+ lines testing all commands

### Performance

- **Translation Speed**: <2ms average per pack load (with caching)
- **Cache Hit Rate**: >95% for repeated pack loads
- **Test Coverage**: 187 passing tests, 5 skipped (99.97% passing rate)
- **Test Suite Size**: 3,657 lines across 12 test files
- **Supported Python Versions**: 3.10, 3.11, 3.12, 3.13
- **Supported Languages**: Spanish (es), Arabic (ar), English (en) reference
- **Language Packs**: 13 total (4 Python versions × 3 languages + version-index.yml)
- **API Provider Coverage**: 3 providers (DeepL, Google, LibreTranslate) with 150+ languages
- **Memory Usage**: <20MB for typical language pack operations

### Technical Details

- **Architecture**: Inheritance-based pack system with version-aware loading
- **Storage Format**: YAML for language packs with Pydantic schema validation
- **API Design**: Async-first with optional sync wrappers
- **Security**: Path traversal protection, circular inheritance detection, ISO language code validation
- **Caching Strategy**: In-memory LRU cache for pack loader, SQLite/Redis for translation API
- **Testing**: pytest with async support (pytest-asyncio) and mocking (pytest-mock, responses)
- **Documentation**: 7 markdown files covering linguistic standards, API usage, and validation
- **Scripts**: 5 automation scripts for extraction, monitoring, generation, and translation
- **Dependencies**: Minimal required (pyyaml, pydantic, packaging, click, rich)
- **Optional Dependencies**: Translation API providers (deepl, google-cloud-translate, httpx, redis)
- **API Stability**: Public API stable, internal API may change
- **MLCP Compliance**: Full v1.0 specification support
- **Breaking Changes**: None (first release)

---

## Development Info

### Running Tests

```bash
cd libs/i18n
uv run pytest tests/ -v
```

### Test Coverage

```bash
cd libs/i18n
uv run pytest tests/ --cov=legesher_i18n --cov-report=html
open htmlcov/index.html
```

### Running CLI

```bash
cd libs/i18n

# Validate a language pack
uv run legesher-i18n validate language-packs/python/es/legesher_i18n_python_es/packs/3.13.yml

# List available language packs
uv run legesher-i18n registry list

# Validate all language packs
uv run legesher-i18n registry validate --lang all
```

### Translation API Setup

```bash
# Install with API support
uv add legesher-i18n[api]

# Or for development
cd libs/i18n
uv sync --group dev
```

### Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

---

## Links

- [GitHub Repository](https://github.com/madiedgar/legesher)
- [Issue Tracker](https://github.com/madiedgar/legesher/issues)
- [Legesher Monorepo CHANGELOG](../../CHANGELOG.md)
- [Documentation](./docs/README.md)
- [Linguistic Standards](./docs/linguistic-standards.md)
- [Translation API Guide](./docs/translation-api.md)
- [Validation Guide](./docs/VALIDATION.md)
