# Packs publish runbook (`legesher/language-packs`)

How a pinned revision of the packs dataset is built and published. The
counterpart for the evidence layer is [`corpus-publish-runbook.md`](corpus-publish-runbook.md),
and for the decision layer [`legesher/language-canon`](https://huggingface.co/datasets/legesher/language-canon).

Both the export and the push are scripted, and **the push is gated rather than
free**. `export_packs.py --push` refuses on any of six conditions; see
[Publish](#publish). Pushing a revision is still a maintainer action against a
release ticket — what changed is that the script now enforces that rather than
asking the operator to remember it.

> Until 2026-08-24 this script had no `--push` at all, on the reasoning that
> publishing is a governance act and not a script flag. The act still is. The
> mechanism was the problem: a hand-push has no gates, and the published
> artifact drifted three revisions behind the generator with nothing to notice
> (CORE-2017).

## What this artifact is

What ships: the vocabulary Legesher's Python language packs carry. Built from
the YAML pack tree at a release commit, never from `canon_selections` — see
[Why not the database](#why-not-the-database).

It is not the decision layer; that is
[`legesher/language-canon`](https://huggingface.co/datasets/legesher/language-canon),
a separate dataset since 2026-08-19. References written before then that call
this artifact "the canon" mean the packs, because that is what the word meant
when they were written.

## Preconditions

1. **`verify_pack_regen` is green.** This is the gate, not a formality: it
   proves the shipped packs still regenerate from their source of truth. A red
   gate means the packs and the database disagree, and a pinned revision built
   over that drift is a revision nothing can reproduce.

   ```sh
   cd libs/i18n
   uv run python scripts/verify_pack_regen.py --db legesher_i18n/db/translations.db
   ```

   Expect `PASS: regeneration reproduces all 280 shipped pack file(s)`.
   Informational findings (`comment_lost`, `not_byte_identical`) do not block.

2. **The working tree is clean and carries the release tag.** The manifest
   records both. On `--push` these are gates rather than preconditions — a
   dirty tree makes the revision unreproducible from the commit it names, and a
   wrongly-tagged one leaves it sharing no version string with its release.

   The tag is `language-packs-v<DATASET_VERSION>`, matching the version
   declared in `scripts/export_packs.py`: `language-packs-v0.5.0` for the
   0.5.0 release. **Semantic, not date-based** (2026-08-28): major for a breaking
   schema change, minor for new languages, terms or interpreter versions, patch
   for corrections to renderings a release already carried.

   Cutting a release therefore has two steps in one order: bump
   `DATASET_VERSION` in the exporter, commit, then tag the commit to match. The
   gate compares the two, so tagging a commit whose declared version differs is
   refused rather than published.

3. **`audit_packs` and `audit_collisions` are clean** — the mechanical gates
   behind the `experimental` stamp.

4. **Corpus export rides the release (CORE-1800).** The corpus is the evidence
   layer behind the canon; **a release cannot complete with a published corpus
   revision older than the canon state it ships**. The gate is code, not a
   checklist item:

   ```sh
   cd libs/i18n
   uv run python scripts/check_corpus_freshness.py
   ```

   `FRESH` (exit 0) — proceed. `STALE` (exit 1) — the published corpus
   predates the last change to `language-packs/`: walk the corpus export
   first — [`corpus-publish-runbook.md`](corpus-publish-runbook.md) §§1–3,
   i.e. `migrate_to_v2.py --publish` then `export_corpus.py --push` — and
   re-run the check.

   This step sequences *when* the export runs; it changes nothing about
   *whether* a push is allowed. The four CORE-1502 push gates
   (double-keyed sign-off, target-repo confirmation, `build_meta` salt
   provenance, Hub auth preflight) live in `export_corpus.py` and still
   decide that on every push. The check itself is read-only — one anonymous
   Hub metadata read, one local `git log` — and never pushes anything.

## Build

```sh
cd libs/i18n
uv run python scripts/export_packs.py --out build/hf-packs --verify-deterministic
```

`--verify-deterministic` exports a second time into a sibling directory and
compares every checksum. It should always be used for a revision that will be
published.

Check the summary before going further:

* `locales`: **56**. Not 57: `language-packs/python` also contains
  `version-index.yml`, a file, and a plain directory listing counts it. The
  exporter refuses to run if the registry and the pack tree disagree.
* `tiers present` — `experimental` for every locale, until the ladder in
  [`pack-maturity-ladder.md`](pack-maturity-ladder.md) promotes one.
* Any `WARNING:` line. There should be none. The licence check compares the
  declared compilation licence against every pack's own `metadata.license`;
  both are public, so a disagreement is surfaced here rather than discovered in
  the card after the fact. On `--push` it is a refusal, not a warning.

## Outputs

```text
build/hf-packs/
  README.md          the dataset card — generated, never hand-edited
  manifest.json      commit, toolchain, counts, SHA-256 per file
  data/vocabulary.parquet       the renderings (fact table)
  data/locales.parquet          natural-language identity
  data/pl_terminology.parquet   the target's own terminology + validity sets
  data/packs.parquet            per-(locale × target) state: tier, semver
  json/<locale>/<target>.json   the loadable form: translations alone
```

Regeneration is byte-identical for a pinned toolchain; `manifest.json` records
the pyarrow and Python versions that produced the Parquet files, because
Parquet embeds a writer string. The JSON and the manifest are byte-identical
across machines.

## Publish

**Run this from the repository root, not from `libs/i18n`.**

```sh
cd <repo root>
uv sync                    # once per checkout — see below
LEGESHER_HF_PUSH_APPROVED=1 uv run python libs/i18n/scripts/export_packs.py \
  --out build/hf-packs --push --governance-signoff CORE-1502
```

`huggingface-hub` is declared in the **root** `pyproject.toml`, not in
`libs/i18n`. Running `uv run` from inside `libs/i18n` resolves that package's
own dependencies, which do not include it, so the push dies after every gate
has passed with:

```
huggingface_hub is required to push. Install it with `uv pip install
huggingface_hub`, then `hf auth login`.
```

This bites hardest in a **fresh worktree cut for a release**, where the venv is
new and has never been synced from the root. It is also the least informative
moment to hit it: the export has already run and reported success, so the
failure reads as an auth or Hub problem rather than a missing dependency. `uv
sync` at the root fixes it.

A `VIRTUAL_ENV ... will be ignored` warning here is noise, not a problem — it
means a shell-activated venv from another checkout is being correctly bypassed
in favour of the worktree's own.

The first push freezes the layout for every consumer that pins it, so the
script refuses on any of the following. All of them read git, the registry or
the pack YAML, so all of them run **before the export writes a byte** — a
refused run leaves nothing on disk that could be mistaken for push-ready:

| Gate | Refuses when |
| --- | --- |
| `--governance-signoff CORE-1502` | the sign-off is absent or wrong |
| `LEGESHER_HF_PUSH_APPROVED=1` | the environment key is unset — the flag and the variable are two keys so a command-line typo cannot publish |
| `--target-repo` | a non-default destination is not repeated verbatim in `LEGESHER_HF_TARGET_OVERRIDE` |
| clean worktree | the tree is dirty, or git is unavailable — a revision pinned to a commit it did not come from cannot be reproduced |
| tagged commit | `HEAD` does not carry `language-packs-v<DATASET_VERSION>` — the tag is the one version string the Hub revision, the release ticket and the card all share. Checked against the **exact** tag, not the prefix: this repo also tags `v0.24.0` and `i18n-python-ar-v0.0.4`, neither of which names a revision of this dataset, and a leftover `language-packs-v*` from an earlier release would otherwise let a build publish under a version it does not declare |
| licence agreement | the declared compilation licence and the packs' own `metadata.license` disagree — both claims become public in the same revision, so "reconcile before publishing" becomes a refusal rather than a warning |
| Hub auth | no usable token |

Then `--verify-deterministic` turns itself on and the upload runs only if it
passes: a revision that does not reproduce is not one to pin consumers against.
The proof covers the card and the manifest as well as the data files.

**`--push` never changes visibility.** It creates private and uploads; going
public stays a deliberate act on the Hub. `private` and `gated` are independent
flags and a gated failure is invisible to a signed-in maintainer, so verify a
publish anonymously, never from the pushing session.

Pin the revision against the release ticket in Linear. The Hub commit message
must not name an internal ticket (`CORE-####` or `HOME-####`) — Hub commit
history is as public as the files it carries, and an issue key resolves to
nothing for a reader outside the project. A test holds this
(`test_export_packs.py`, `test_the_push_never_changes_visibility_and_cites_no_internal_ticket`),
matching the corpus exporter; it is no longer a rule the operator carries.

Before pushing, confirm the card's figures match the artifact rather than any
milestone or release description. Those are hand-written and have carried stale
locale counts in both directions; the artifact and `languages.json` are the answer.

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
