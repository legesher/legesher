# Corpus publish runbook — `legesher/language-corpus` (CORE-1312)

> **Maintainer-only.** This is not a contributor workflow — it is the sequence
> a repository maintainer with publish rights walks once, to create the corpus
> dataset. Nothing here is required to build Legesher, run the test suite, or
> contribute a translation. If you are looking for how to contribute, start
> with `CONTRIBUTING.md`.
>
> It is published openly on purpose: the gates below are the technical basis
> for the consent and privacy commitments the dataset card makes, and those
> claims should be auditable rather than taken on trust.

The operator sequence from the working v1 database to the PRIVATE Hugging
Face corpus dataset. Every one-way door has a blocking gate in code; this
document is the order you walk through them, not a checklist you must hold
in your head.

The publish surface is the CORPUS layer only (concepts / terms / options /
endorsements / contributors). The canon, contributor identities, and the
whole review-intake layer are structurally excluded (`NEVER_EXPORT` in
`scripts/export_corpus.py`).

## 0. One-time: mint and escrow the salt

Contributor ids are `c_ + HMAC-SHA256(key=salt, msg=github_username)[:16]`.
The salt is a **primary-key ingredient, not a rotatable credential**: after
the first push it can never change without forking every contributor id.

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

It is never committed and never rotated. Store it durably in at least two
independent places before building anything — the escrow procedure itself is
maintainer-operational and is recorded on CORE-1502, not here.

Every gate below verifies against its **fingerprint**
(`schema_v2.salt_fingerprint`, `sha256(salt)[:16]`) rather than the salt
itself, so provenance can be checked without any step handling the secret.
Note the fingerprint is a key-check value only — it is not the contributor-id
formula above, and it never leaves the private `build_meta` table.

## 1. Build the publish-grade v2 database

```bash
cd libs/i18n
# NEVER paste the salt on a command line or in a plain `export` — it lands in
# shell history and in `ps`, and this secret can never be rotated. Read it
# without echo (or pipe it in from your secret manager's CLI):
read -rs LEGESHER_CONTRIBUTOR_SALT && export LEGESHER_CONTRIBUTOR_SALT
# The --contributor-salt CLI flag must NOT be used for the real salt (argv is
# visible to every process on the machine).
uv run python scripts/migrate_to_v2.py \
    --source legesher_i18n/db/translations.db \
    --target build/translations_v2.db \
    --publish
```

`--publish` refuses, before creating anything: a missing/dev/short salt, and
any unresolved contributor identity. The build stamps `build_meta` with
`publish_build = 1` and the salt fingerprint — the push gate reads both.

The migration is multi-target aware: concepts dedupe by slug across
programming languages, terms stay per-PL, canon selections carry their
term's PL scope, and `definition_en` seeds from the `context/python/`
briefs (the ledger reports `definitions_seeded` / `definitions_todo`).

## 2. Dry export — review before anything leaves the machine

```bash
uv run python scripts/export_corpus.py \
    --db build/translations_v2.db --out build/hf-corpus
```

No network library is touched. Review:

- `build/hf-corpus/reconciliation.json` — row counts must reconcile (the
  export hard-fails if not);
- `build/hf-corpus/README.md` — the dataset card (license section stays a
  placeholder until the CORE-1502 license decision);
- `build/hf-corpus/data/*.parquet` — five configs, pinned Arrow schemas.

## 3. The private push (double-keyed + provenance-verified)

```bash
huggingface-cli login        # or export HF_TOKEN=...
LEGESHER_HF_PUSH_APPROVED=1 uv run python scripts/export_corpus.py \
    --db build/translations_v2.db --out build/hf-corpus \
    --target-repo legesher/language-corpus \
    --push --governance-signoff CORE-1502
```

Gate order, all BEFORE the export runs:

1. `--governance-signoff CORE-1502` **and** `LEGESHER_HF_PUSH_APPROVED=1`
   (two keys; a typo cannot publish);
2. intended target: a `--target-repo` other than `legesher/language-corpus`
   must be repeated verbatim in `LEGESHER_HF_TARGET_OVERRIDE` — a typo'd
   repo id cannot mint frozen keys against the wrong namespace;
3. `build_meta` provenance: the DB must be a `--publish` build and its salt
   fingerprint must match `$LEGESHER_CONTRIBUTOR_SALT` in the pushing shell
   — a dev-salt or wrong-salt artifact is refused in code, not by checklist.
   Note this reads the *pushing* shell: if the build and the push happen in
   different sessions, re-read the salt into the environment first or the
   gate fails;
4. Hub auth preflight (`whoami`) — an unauthenticated run fails before the
   export, not mid-upload.

The upload itself is allowlisted to exactly what the exporter writes
(`README.md`, `reconciliation.json`, `data/*.parquet`) — a stray file in the
output directory never reaches the Hub.

The repo is created **PRIVATE** (`private=True`) and this tooling never
flips visibility. Going public is a separate deliberate act on the Hub,
gated on the remaining CORE-1502 decisions (license, credit, withdrawal).
The salt freezes at this first private push.

## 4. After the push

- Record the HF revision SHA on CORE-1312 and close out the publish build.
- Phase 2 (CORE-1506): release sync + revision pin + drop the DB from the
  wheel. Phase 3 (CORE-1507): community ingest. Promotion job: CORE-1504.
- The canon packs dataset (`legesher-keywords`, CORE-1043) is a separate,
  per-release artifact — not this corpus.
