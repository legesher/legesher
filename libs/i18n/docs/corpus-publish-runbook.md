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

The source database is an untracked working copy (CORE-1794) — if
`legesher_i18n/db/translations.db` is absent (fresh clone, new machine), copy
it in from the durable data home first:
`cp "$LEGESHER_DATA_REPO/db/translations.db" legesher_i18n/db/`.

```bash
cd libs/i18n
# REBUILDING? The migration refuses outright if the target file already exists
# ("refusing to overwrite build/translations_v2.db") and has no force flag —
# it will not clobber a publish-grade artifact. Move the old one aside rather
# than deleting it: until the new build is pushed, it is the only local copy
# of what is currently live, and the two are worth diffing.
[ -f build/translations_v2.db ] && \
    mv build/translations_v2.db "build/translations_v2.superseded.db"
# The private identity map lives in the durable data home, not in this tree
# (CORE-1794). Point the build at your checkout of the private data repository
# — without it the map loads EMPTY and the migration refuses every human label:
export LEGESHER_DATA_REPO=<path-to-your-checkout-of-the-private-data-repository>
# NEVER paste the salt on a command line or in a plain `export` — it lands in
# shell history and in `ps`, and this secret can never be rotated. Read it
# without echo (or pipe it in from your secret manager's CLI):
read -rs LEGESHER_CONTRIBUTOR_SALT && export LEGESHER_CONTRIBUTOR_SALT
# The --contributor-salt CLI flag must NOT be used for the real salt (argv is
# visible to every process on the machine).
uv run python scripts/migrate_to_v2.py \
    --source legesher_i18n/db/translations.db \
    --target build/translations_v2.db \
    --publish --acknowledge-message-rows-not-migrated
```

`--publish` refuses, before creating anything: a missing/dev/short salt, and
any unresolved contributor identity. The build stamps `build_meta` with
`publish_build = 1` and the salt fingerprint — the push gate reads both.

Confirm the build is the one you think it is before exporting:

```bash
sqlite3 build/translations_v2.db \
    "select source, count(*) from option_provenance group by 1 order by 2 desc;"
```

It must print `legesher` / `upstream` / `model` / `community`. Anything else —
`import` in particular — means the export is about to run against an older
database, and the card it generates will describe a vocabulary the data does
not carry. Nothing downstream catches that: the card comes from the code and
the data comes from this file, and no gate compares them.

`--acknowledge-message-rows-not-migrated` answers a separate refusal. The
source database carries the `message_templates` partition (CORE-1679), which
this migration does not carry over, so a v2 build would silently start with
none. The flag says you know that; re-seed afterwards with
`scripts/seed_message_templates.py` from `legesher_i18n/db/seeds/`. Dropping
the partition from the source first is the other way through. Either is fine
for the corpus — `message_templates` is not one of the five exported configs
and never reaches the Hub — but it changes what the local v2 database holds,
so pick deliberately rather than reaching for the flag to clear the error.

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
- `build/hf-corpus/README.md` — the dataset card. Check the frontmatter reads
  `license: cc-by-4.0` and that the Licence and attribution section carries
  all three upstream projects, including the changes-were-made statement
  Apache-2.0 requires (CORE-1720). A card that still says `license: other`
  means the build ran against a stale checkout;
- `build/hf-corpus/data/*.parquet` — five configs, pinned Arrow schemas.

## 3. The private push (double-keyed + provenance-verified)

```bash
hf auth whoami               # already authenticated? then skip the login
hf auth login                # or export HF_TOKEN=...
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
   export, not mid-upload. It also confirms org membership: publishing to
   `legesher/*` needs the account to be in that org, which is the one thing
   a rehearsal against a personal namespace cannot prove.

Note the CLI is `hf`, not `huggingface-cli` — the latter was renamed and no
longer works. `hf auth login` replaces `huggingface-cli login`.

The upload itself is allowlisted to exactly what the exporter writes
(`README.md`, `reconciliation.json`, `data/*.parquet`) — a stray file in the
output directory never reaches the Hub.

The repo is created **PRIVATE** (`private=True`) and this tooling never
flips visibility. Going public is a separate deliberate act on the Hub, and
the published revision must carry the current attribution and licence
(CORE-1761). The licence itself is settled — CC BY 4.0, decided 2026-07-15.

What we promise contributors is in `CONTRIBUTOR_PRIVACY.md`, and honouring a
withdrawal request is `docs/contributor-withdrawal-runbook.md` — a private-side
erasure that never touches a published revision, because no export has ever
carried an identity.

The salt freezes at this first private push.

## 4. After the push

- Record the HF revision SHA on CORE-1312 and close out the publish build.
- Phase 2 (CORE-1506): release sync + revision pin + drop the DB from the
  wheel. Phase 3 (CORE-1507): community ingest. Promotion job: CORE-1504.
- The canon packs dataset (`legesher-keywords`, CORE-1043) is a separate,
  per-release artifact — not this corpus.
