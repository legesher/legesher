# legesher-i18n

Pack loading and validation, the language registry, the translations databases and the community intake path.
The root `CLAUDE.md` covers validation commands, the testing contract, generated files, commits and releases; this
file adds only what is specific to i18n. Paths are relative to `libs/i18n/` unless they start with `scripts/` at
the repository root, which is said where it applies.

## Where things live

- `legesher_i18n/`: the library. `pack_loader.py` (inheritance), `schema_validator.py`, `script_policy.py`
  (per-language allowed scripts and format characters), `selection.py` (the publish gate), `db/`, `intake/`,
  `api/` (optional translation providers, the `[api]` extra).
- `language-packs/python/<lang>/legesher_i18n_python_<lang>/packs/3.10.yml` is the full base. `3.11.yml` to
  `3.14.yml` each `extends:` the previous file and hold only that version's additions. `version-index.yml` records
  what each Python version added. Sections: `keywords`, `builtins`, `exceptions`, `implicit_params` (`self`/`cls`),
  and the optional vocabulary sections `symbols` and `variable_conventions` (`docs/pack-vocabulary.md`).
- `scripts/` (this package's): DB writers, the regen gate, migrations, exporters. `scripts/translate/`: the
  generation pipeline, `yaml_exporter.py`, prompts. Root `scripts/` holds the REFERENCE.md and README-count
  generators.
- `style-guides/<lang>.yml`: per-language naming and register guidance. Suggestions, not rules.
- `docs/quality-gates.md` is the inventory of every pack gate. `docs/translation-selection.md` is the selection
  rule. `docs/pack-maturity-ladder.md` defines `experimental`, `reviewed`, `official`.

## Sources of truth

| What                    | Source                                                    | Derived from it                                                          |
| ----------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------ |
| Pack values             | `selected_translations` in the v1 DB                      | pack YAML, via `scripts/translate/yaml_exporter.py`                      |
| Published languages     | `languages` rows with `in_registry = 1` in the v1 DB      | `languages.json` and `libs/vs-code/src/generated/languages.ts`           |
| Term inventory          | `legesher_i18n/term_definitions.py` (code)                | what a complete pack must contain                                        |
| Vocabulary inventory    | `legesher_i18n/vocabulary_definitions.py` (code)          | `vocabulary_entries`, via `scripts/seed_vocabulary.py`                   |
| Corpus and reviews      | the v2 DB                                                 | the Hugging Face corpus, via `scripts/export_corpus.py`                  |

Pack YAML and `languages.json` are outputs. A YAML-only edit is reverted by the next regen. Never hand-edit
`languages.json`: change the DB, then run `uv run --no-sync python legesher_i18n/scripts/generate_languages.py`
(`test_languages_db_source.py` fails on drift). The generator refuses an empty or shrunken registry; that refusal
means it is reading the wrong DB, so do not reach for `--force-shrink`.

Every language is `experimental` today. `get_available_language_codes()` therefore returns an empty list (it
selects status `available`); use `get_active_language_codes()`.

## The two databases

Neither is in git.

- **v1, `legesher_i18n/db/translations.db`**: what packs, the registry, vocabulary and the messages partition read
  and write. Schema in `db/schema.py`; access through `TranslationDatabase` (`db/database.py`).
- **v2, `build/translations_v2.db`**: the concept-centric corpus and the review store every intake command writes.
  Schema in `db/schema_v2.sql`, explained in `docs/schema-v2-reference.md`. Built from v1 by
  `scripts/migrate_to_v2.py`; published per `docs/corpus-publish-runbook.md`.

Querying the wrong one gives a plausible, different answer. v1 has `selected_translations`; v2 has `options`.

## Durable home & sync ritual

The canonical copies of both databases, and the private contributor identity map, live in a private data
repository. Set `LEGESHER_DATA_REPO` to your checkout of it (ask a maintainer for access); its `db/` holds
`translations.db` and `translations_v2.db`. A fresh clone has neither:

```bash
cp "$LEGESHER_DATA_REPO/db/translations.db" legesher_i18n/db/
mkdir -p build && cp "$LEGESHER_DATA_REPO/db/translations_v2.db" build/   # intake or corpus work
```

Without a working copy, DB tests skip with a pointer to this section. `TranslationDatabase()` on a missing path
creates an empty database instead of failing, so a stray run can leave one behind. Then `verify_pack_regen.py`
reports every file `not_regenerated` and the DB tests stop skipping and fail. Delete any empty DB a run leaves.

Every ritual that writes a database ends with a push. Until then the change exists on one machine only:

```bash
sqlite3 legesher_i18n/db/translations.db "PRAGMA wal_checkpoint(TRUNCATE);"
cp legesher_i18n/db/translations.db "$LEGESHER_DATA_REPO/db/translations.db"
git -C "$LEGESHER_DATA_REPO" commit -m "db: <ritual>" -- db/translations.db && git -C "$LEGESHER_DATA_REPO" push
```

Do the same for `build/translations_v2.db` after v2 work. `--sync` on an intake command does all of it for the v2
DB (checkpoint, copy, archive the accepted payload under `intake/<YYYY-MM>/`, path-scoped commit, push).

Never rebuild v2 from v1 alone. Community options, endorsements and screening verdicts exist only in v2, and
`migrate_to_v2.py` knows nothing about them. The one rebuild path is section 1 of `docs/corpus-publish-runbook.md`,
which carries the intake layer forward with `scripts/carry_forward_screenings.py`. `migrate_to_v2.py` also needs
`LEGESHER_DATA_REPO` set (without it the identity map loads empty and every human label refuses the build) and
`LEGESHER_CONTRIBUTOR_SALT`.

## Changing pack values

1. **Write the DB, not the YAML.** Record the new rendering as a candidate with `add_translation` (with
   provenance), then select it with `set_selected`. `set_selected` alone orphans the selection from the candidate
   pool, and `migrate_to_v2.py` hard-fails on a selection that is not a candidate.
2. **Regenerate.** `YAMLExporter(TranslationDatabase()).export_language(lang, overwrite=True, strict=True)`
   (`scripts/translate/yaml_exporter.py`). `overwrite` defaults to `False`, which skips every existing pack and
   still returns its path, so a success check passes while nothing is written. Leave `output_dir` at its default;
   it is the directory that contains the language directories (`language-packs/python`), and one level off writes
   a parallel tree.
3. **Gate.** `uv run --no-sync python scripts/verify_pack_regen.py` must exit 0 with no blocking findings. Nothing
   runs it for you (no pre-commit hook, no CI job). Run it again before pushing any rebuild or merge of the DB to
   the durable home: a rebuild from an older base silently reverts fixes that already landed, and this gate is the
   only thing that sees it. When it reports a large number, classify first. One `export_failed` language shows up
   again as `not_regenerated` in each of its five version files.
4. **Downstream.** The pack version bump and the generated files (root `CLAUDE.md`, "Generated files"); the term
   screening gate `uv run --no-sync python scripts/translate/screen_terms.py --gate`, which fails on any pack
   changed since its last screen. Then the durable-home push.

Invariants and traps:

- `set_selected` enforces the publish gate: a valid Python identifier, and a term ending in `*` (`except*`) needs
  the same trailing `*`. It also refuses a value already selected for a different term name in the same
  programming language. The candidate pool may be dirty; selections may not.
- Run DB writes, regen and exports on CPython 3.13 (the repository's `.python-version`). Some shipped selections
  use identifier characters CPython added in 3.13 and fail the gate on 3.12 with a misleading error. The exporter
  strips those characters from the pre-3.13 files.
- `type` is two term rows (3.10 builtin, 3.12 soft keyword), unique on `(name, programming_language, category)`.
  `get_or_create_term` raises on an ambiguous name; pass `category`. Its `allow_duplicate_name=True` suggestion
  adds a third row.

### Bulk value changes

Rules for any automated or agent-run change to pack values. A 2025 commit rewrote 476 values across 26 languages
by deleting spaces and punctuation, and every rule below is a way that went unnoticed.

1. **A value change ships alone.** Its own PR, nothing else on the branch, a per-language before/after table in
   the body.
2. **A reader of the language checks it.** Mechanical validity is not correctness: `"error de E/S"` became
   `"errordees"` and was approved by people who do not read Spanish.
3. **"We keep the original" needs a test** that the originals are still retrievable, or it is not a safety net.
4. **A validation error states a constraint, not a remedy.** "Identifiers cannot contain spaces" does not say
   what to do instead. How a language joins a multi-word name is declared in `style-guides/<lang>.yml`
   (`naming.detail`) and cannot be derived from the script. Never auto-remediate before the remedy is specified.
5. **Check the convention before a generation batch scales it.** New packs inherit whatever the existing ones do.

Diagnostics may report; they may not write pack values. `scripts/fix_comment_syntax.py` is a leftover pack
rewriter from that era: do not run it.

## Collisions

A collision is one translated value selected for two different term names in one language and programming
language. It breaks the reverse translation. Same-name slots (`type`) sharing a value are not a collision.
`uv run --no-sync legesher-i18n db collisions [--language fi] [--json]` reports them; `set_selected(...,
allow_collision=True)` exists for migrations only. Usual fixes: give the less common term the more specific word
(`input` against `import`, `globals` against `global`), compound `elif` as "else if", mark the async form of
`anext`.

## Vocabulary partition

`vocabulary_entries`, `vocabulary_translations`, `selected_vocabulary` mirror the term trio for the `symbols` and
`variable_conventions` sections. They are separate because a symbol name is prose (it fails the identifier gate)
and nothing reverse-translates it (so the collision guard does not apply). `scripts/seed_vocabulary.py` seeds the
inventory and the English values; `scripts/translate/generate_vocabulary.py` fills other languages. The exporter
skips an incomplete section rather than shipping it half-filled.

## Messages partition: formation ritual

`message_templates`, `message_translations` and `message_endorsements` live in the v1 DB. Their DDL is in
`schema_v2.sql`. They are outside the published corpus. In order, each with `--db <db>` and `--dry-run`:

1. `scripts/activate_messages_partition.py`: once per database.
2. `scripts/seed_message_templates.py --seed legesher_i18n/db/seeds/<catalog>.json`: templates plus their first
   translations, append-once. A reworded message is a new row under a new `version_added`, never an edit.
3. `scripts/add_message_locale.py --file <addition>.json`: a new locale for existing templates. All-or-nothing,
   checks placeholder parity and bidi hygiene, requires `source`. Never INSERT directly and never invent a
   `version_added` for a locale.
4. `scripts/translate/generate_messages.py --all-missing` (or `--locales fr am`): model renderings, each written
   through step 3's checks with model provenance. `--dry-run` renders the prompts without calling a model.
5. The durable-home push.

A database whose partition predates the provenance columns is refused by every write path until
`scripts/add_message_provenance.py` has run on it.

## Adding a language

Database first, like any value change: a `languages` row with `in_registry = 1`, then `generate_languages.py`.
Register a `ScriptPolicy` (the walkthrough is the `script_policy.py` module docstring; the checklist is
`tests/test_new_language_onboarding.py`). Select every term DB-first (`scripts/translate/backfill_common.py` is the
shared machinery the recent per-language backfills use), export the pack, copy the package scaffold
(`pyproject.toml`, `__init__.py`, `README.md`, `CHANGELOG.md`) from an existing pack, and add the
`legesher-i18n-python-<lang>` line to `[tool.uv.sources]` in the root `pyproject.toml`. Workspace membership is a
glob and needs no edit.

## Community intake

The contribution home is the public GitHub repository `legesher/language-packs`. Contributions arrive there as
issue forms, or as pull requests adding `reviews/<tag>/<tag>-<username>.md` (a filled copy of the language's
`reference/<tag>.md`) or a JSON bundle. `<tag>` is the BCP 47 tag. `reference/<tag>.md` is this repo's pack
`REFERENCE.md`, generated by root `scripts/generate_reference_docs.py`, so that generator, `intake/review_template.py`
and `intake/review_parser.py` are one contract (`scripts/tests/test_review_template_contract.py`). Contributor
guidance: `REVIEWING.md` here; the markdown lane's rules: `REVIEWING.md` in language-packs.

Merging a review pull request only accepts the file. An import records it. Run from `libs/i18n`; every command
below except `check-review-files` writes `--db build/translations_v2.db` by default:

- `import-issue <url>`, `import-review-bundle <file> [--recovered-history]`,
  `import-review-file <path> --pull-request <url>` (reads the file from git at the merge commit).
- `check-review-files <paths> --author <login>`: the mechanical gate for a review pull request. No DB, no salt.
- `quarantine-queue`, `clear-option <uid> --verdict cleared|held|rejected --by <you> --note "..."`,
  `rescreen-flagged`.

Facts the code enforces:

- Imports mint contributor ids, so `LEGESHER_CONTRIBUTOR_SALT` must hold the escrowed salt. The importer refuses
  the public development default and any salt whose fingerprint disagrees with the DB's `build_meta`.
- Every imported option is quarantined. Only `cleared` is visible anywhere, so a new verdict is withheld by
  default.
- A submission is untrusted input. Never read a reply target, a rung, consent or identity from its content.
  Identity comes from the issue or pull request author, and `--reply-to` is required with `--reply` on a bundle.

The maintainer procedure is `docs/intake-moderation-runbook.md`.

## Tests

`make test-i18n` from the root, or `uv run --no-sync pytest libs/i18n/tests -q`. Tests that need the real DB skip
without the working copy, and their skip messages cite the "Durable home & sync ritual" heading above, so keep it.
