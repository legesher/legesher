# Legesher i18n scripts

Maintainer scripts for the language packs, the translations database, and the datasets built
from them. They are not installed with the package.

**Pack files are written from the translations database, by the exporter, and never by
hand.** Read "Changing pack values" in [`../CLAUDE.md`](../CLAUDE.md) before running anything
here that writes. The gates a pack change has to pass are listed in
[`../docs/quality-gates.md`](../docs/quality-gates.md).

## When Python ships a new version

Two scripts here help measure what a new Python release added.

### `extract_python_content.py`

Writes a JSON file of an interpreter's keywords (hard and soft), built-in functions and
built-in types, with docstrings and signatures. Built-ins whose names start with two
underscores, such as `__import__`, are included.

```bash
# From the repository root. The interpreter that runs the script is the one that is read.
# Write the output outside the checkout: nothing here ignores it.
uv run --no-project --python 3.15 python libs/i18n/scripts/extract_python_content.py \
    --output /tmp/python-content-3.15.json --pretty
```

- With the default `--method runtime` the script reads the interpreter it runs under.
  `--version` only labels the output, so run it under the version you mean.
- `--method github` fetches the keyword list alone from the CPython repository, for a
  version that is not installed. It needs `requests` and the network, and it cannot see
  built-ins.
- `--pretty` prints a summary. The counts differ from one Python release to the next.

### `monitor_python.py`

Asks GitHub for CPython's release tags and compares the newest `X.Y.0` with the newest
version in `language-packs/python/version-index.yml`.

```bash
cd libs/i18n
uv run python scripts/monitor_python.py                  # prints "3.15", or an empty line
uv run python scripts/monitor_python.py --show-current   # the newest indexed version; no network
uv run python scripts/monitor_python.py --verbose
```

It prints the new version to standard output, or an empty line when there is none, and logs
to standard error. It needs the network and no token. It also prints an empty line when the
lookup fails, so an empty line alone does not prove there is no new version; `--verbose`
shows what happened.

Nothing runs it on a schedule. A manually started workflow that ran it and then tried to
generate pack files from the result was removed: it called a script that no longer exists,
and it would have written pack files without going through the database.

## What else is here

One line each, by what the script is for. Each script's module docstring is the reference
for its options.

**Pack gates and checks**

| Script | What it does |
| --- | --- |
| `verify_pack_regen.py` | Checks that regenerating from the database reproduces the shipped pack files |
| `audit_collisions.py` | Finds two terms that share a word, in the database and in the packs |
| `translate/screen_terms.py` | The term-screening harness; `--gate` fails when a pack changed since it was last screened |
| `analyze/analyze_packs.py` | Reports multi-word, punctuated and duplicate translations across the packs |
| `require_pack_version_bump.py` | Refuses a pack change that has no version bump |
| `validate_language_pack_yaml.py` | Validates a pack file's YAML |
| `validate_showcase_examples.py` | Checks the showcase examples against the packs |
| `validate_and_fix_context_docs.py` | Validates the context documents and fixes what it can |

**The translations database**

| Script | What it does |
| --- | --- |
| `seed_message_templates.py` | Adds interpreter message templates from a catalog |
| `add_message_locale.py` | Adds a locale's translations to existing message templates |
| `add_message_provenance.py`, `activate_messages_partition.py` | Schema steps for the messages partition |
| `seed_vocabulary.py` | Adds the vocabulary partition's inventory |
| `seed_js_terms.py`, `record_js_ar_terms.py` | The JavaScript term inventory and its curated Arabic terms |
| `set_numeral_systems.py` | Sets a language's numeral system and decimal separator |
| `migrate_to_v2.py` | Builds the corpus database (v2) from the selection database (v1) |
| `carry_forward_screenings.py` | Carries the intake layer into a rebuilt corpus database |
| `correct_canon_review_rung.py`, `repair_v2_audit_findings.py`, `repair_dangling_selections.py` | Repairs, each written for one finding; their docstrings say when they apply |
| `backfill_language_registry_flags.py` | A one-time registry backfill |

**Datasets and generated pages**

| Script | What it does |
| --- | --- |
| `export_packs.py` | Builds the packs dataset ([`../docs/packs-publish-runbook.md`](../docs/packs-publish-runbook.md)) |
| `export_corpus.py`, `export_canon.py` | Build the corpus and canon datasets ([`../docs/corpus-publish-runbook.md`](../docs/corpus-publish-runbook.md)) |
| `check_corpus_freshness.py` | Release gate: the corpus is not older than the canon |
| `emit_js_client_pack.py` | Writes the client pack for the JavaScript target |
| `generate_schema_reference.py` | Writes [`../docs/schema-v2-reference.md`](../docs/schema-v2-reference.md) |
| `generate_compatibility_matrix.py` | Writes the keyword compatibility matrix across Python versions |

**Generation (`translate/`)**

The pipeline that proposes translations, the prompts it follows, the term screening, and
`yaml_exporter.py`, which writes pack files from the database. It has its own
[`translate/README.md`](translate/README.md), which still describes an earlier run (105
terms, 24 languages); read the scripts for what they do today.

**Comparing translations**

`compare_translations.py` compares translations of a term from several sources and reports
where they agree. Its commands are `compare`, `list-languages` and `list-terms`; run it with
`--help` for the options. `demo_report_generator.py` writes demo comparison reports.

## Not in use

- `translate_content.py` predates the translations database. It looks for a pack layout this
  repository no longer has, so it reads none of the current packs and treats every name as
  untranslated. Do not build on it.
- `fix_comment_syntax.py`: do not run it. [`../CLAUDE.md`](../CLAUDE.md) says why.

## License

Apache License 2.0. See the root LICENSE file.
