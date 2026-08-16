# Canon packs publish runbook (`legesher/language-packs`)

How a pinned revision of the canon dataset is built and published. The
counterpart for the evidence layer is [`corpus-publish-runbook.md`](corpus-publish-runbook.md).

The export is automated; **publishing is not**. `export_packs.py` has no
`--push` and never touches the Hub. Pushing a revision is a maintainer action
against a release ticket.

## What this artifact is

The decision layer: the vocabulary Legesher actually ships. Built from the YAML
pack tree at a release commit, never from `canon_selections` — see
[Why not the database](#why-not-the-database).

## Preconditions

1. **`verify_pack_regen` is green.** This is the gate, not a formality: it
   proves the shipped packs still regenerate from their source of truth. A red
   gate means the packs and the database disagree, and a pinned revision built
   over that drift is a revision nothing can reproduce.

   ```sh
   cd libs/i18n
   uv run python scripts/verify_pack_regen.py --db legesher_i18n/db/translations.db
   ```

   Expect `PASS: regeneration reproduces all 255 shipped pack file(s)`.
   Informational findings (`comment_lost`, `not_byte_identical`) do not block.

2. **The working tree is clean and tagged.** The manifest records the commit
   and reports `worktree: dirty` otherwise, which makes the revision
   unreproducible from the commit it names.

3. **`audit_packs` and `audit_collisions` are clean** — the mechanical gates
   behind the `experimental` stamp.

## Build

```sh
cd libs/i18n
uv run python scripts/export_packs.py --out build/hf-packs --verify-deterministic
```

`--verify-deterministic` exports a second time into a sibling directory and
compares every checksum. It should always be used for a revision that will be
published.

Check the summary before going further:

* `locales` — **51**. Not 52: `language-packs/python` also contains
  `version-index.yml`, a file, and a plain directory listing counts it. The
  database's python selection layer likewise spans 52 locale codes, but the
  52nd is `uk`, a six-row stub with no pack tree and no registry entry. The
  exporter refuses to run if the registry and the pack tree disagree.
* `tiers present` — `experimental` for every locale, until the ladder in
  [`pack-maturity-ladder.md`](pack-maturity-ladder.md) promotes one.
* Any `WARNING:` line. The licence warning is expected until the in-pack
  `metadata.license` field is reconciled.

## Outputs

```text
build/hf-packs/
  README.md          the dataset card — generated, never hand-edited
  manifest.json      commit, toolchain, counts, SHA-256 per file
  data/vocabulary.parquet
  data/locales.parquet
  json/<locale>/<version>.json
```

Regeneration is byte-identical for a pinned toolchain; `manifest.json` records
the pyarrow and Python versions that produced the Parquet files, because
Parquet embeds a writer string. The JSON and the manifest are byte-identical
across machines.

## Publish

Not scripted, deliberately. A maintainer uploads `build/hf-packs/` to
`legesher/language-packs` and pins the revision against the release ticket.
The first push freezes the layout for every consumer that pins it.

Before pushing, confirm the card's figures match the artifact rather than any
milestone or release description — several still say 51 locales where they
mean something else, and several say 52 where the answer is 51.

## Why not the database

`canon_selections` (v2) and `selected_translations` (v1) both carry selections
for targets other than Python: 62 Arabic JavaScript rows, where
`programming_language` is a real populated column. Exporting from either would
publish unreviewed Arabic JavaScript terminology *labelled by target*,
asserting a level of review that population has not had.

The pack tree cannot carry them: `yaml_exporter.py` drops every selection whose
`programming_language` is not `NULL` or `python` before a pack is written, and
Arabic is the only locale with JavaScript selections at all. `export_packs.py`
reads the pack tree for vocabulary and re-proves the property on the emitted
rows (`assert_python_only`).

Note that there are **two live databases** and they answer different questions:
the packs read v1 `translations.db`, the corpus reads v2 `translations_v2.db`.
Pointing a pack tool at the v2 file fails quietly rather than loudly.

## Related

* CORE-1043 — this artifact
* CORE-1905 — the release that publishes the first revision
* CORE-1513 — the maturity ladder the `experimental` stamp refers to
