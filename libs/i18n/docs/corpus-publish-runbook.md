# Corpus publish runbook — `legesher/language-corpus` (CORE-1312)

<!-- disposition: MAINTAINER (CORE-1724 audit, 2026-08-11) -->

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

Since CORE-1800 this export is no longer free-floating: it is a named step of
the canon packs release ([`packs-publish-runbook.md`](packs-publish-runbook.md),
precondition 4). Every tier-transition release runs
`scripts/check_corpus_freshness.py`, and the release fails while the published
corpus revision predates the canon state it ships — when that gate says
`STALE`, sections 1–3 below are the remedy. The freshness gate is read-only
and separate from the four CORE-1502 push gates in section 3, which are
unchanged.

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

## 1. Build the publish-grade v2 database — the rebuild-integrity sequence

The source database is an untracked working copy (CORE-1794) — if
`legesher_i18n/db/translations.db` is absent (fresh clone, new machine), copy
it in from the durable data home first:
`cp "$LEGESHER_DATA_REPO/db/translations.db" legesher_i18n/db/`.

A rebuild REPLACES a database that carries state the v1 source knows nothing
about, and the migration reconstructs none of it (CORE-2052):

- **the intake layer** — the community wrote it straight into v2: most
  screened community options do not exist in v1 at all, and with them their
  provenance, validations, endorsements, contributors, review sessions,
  commentary and the `option_screenings` verdicts (CORE-1828). The
  intake-moderation runbook's push step has always warned that a
  from-scratch rebuild does not recover clearing decisions
  ([intake-moderation-runbook.md](intake-moderation-runbook.md), step 6);
  without the carry-forward below the rebuilt corpus is simply missing the
  community's contributions — with no error anywhere;
- **canon rung state** — a fresh build regresses every canon selection to
  `machine`, erasing the CORE-1985 corrections.

So a rebuild is the whole sequence below, in order — build, carry the
intake layer forward, re-apply the rung corrections, verify counts against
the durable copy — and none of it is optional. Section 2's dry export runs
only after the verification agrees.

```bash
cd libs/i18n
# REBUILDING? The migration refuses outright if the target file already exists
# ("refusing to overwrite build/translations_v2.db") and has no force flag —
# it will not clobber a publish-grade artifact. Move the old one aside rather
# than deleting it: until the new build is pushed, it is the only local copy
# of what is currently live, and the two are worth diffing — the
# verification at the end of this section leans on it as a third witness.
# NEVER let a retry overwrite it: a failed migration leaves a PARTIAL
# build/translations_v2.db behind, and looping back here with a bare `mv`
# would replace the real superseded build with that fragment. The guard is
# one mechanical command — the mv happens ONLY when no superseded build
# exists, so a whole-block paste on a retry moves nothing, leaves the
# partial build in place, and the migration's own refusal to overwrite an
# existing target stops the sequence right there. Inspect and remove the
# superseded build yourself before rebuilding again.
[ ! -e build/translations_v2.superseded.db ] && [ -f build/translations_v2.db ] && \
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

Now carry the intake layer forward. The carry-forward's `--source` is never
the durable file itself: take a scratch COPY and bring the copy up to the
current screening schema first. The durable copy predates whatever schema
upgrades landed since it was cut (as of CORE-2029 it does), a fresh build
carries the new DDL, and the carry-forward refuses to move rows between the
two versions. Upgrading the scratch copy closes that gap — and computes real
verdicts for any column the upgrade backfills, so the carried rows arrive
whole rather than defaulted:

```bash
cp "$LEGESHER_DATA_REPO/db/translations_v2.db" build/carry-source.db
uv run python -c "
from legesher_i18n.db.schema_v2 import connect, ensure_intake_screening
ensure_intake_screening(connect('build/carry-source.db'))"
uv run python scripts/carry_forward_screenings.py \
    --source build/carry-source.db \
    --target build/translations_v2.db
```

The durable original is never opened for writing by any of this, and the
carry-forward opens its `--source` read-only besides. The carry moves the
whole intake layer — the community options v1 has never held, with their
provenance, validations, endorsements, contributors, sessions, commentary
and the screening verdicts (verdict rows travel with their original ids,
because the latest row per option IS the verdict). It is idempotent (a
re-run reports "already carried forward" and writes nothing) and it refuses
rather than papers over: a screening-schema version mismatch, a
contributor-salt mismatch, a screened option absent from both the rebuild
and the carried set, a target with a conflicting screening history, and a
source table it has no carry policy for all stop the run. Every refusal
means investigate the rebuild — a carry-forward that silently skips rows is
the exact failure this step exists to close. Read the count report it
prints; those are the numbers the verification below must reproduce.

One refusal needs an operator decision rather than an investigation: once
community options are canon-selected, replaying their quarantine history
would trip the `trg_screenings_no_quarantine_while_canon` trigger, and the
carry-forward refuses up front, naming the options. That is the trigger's
doctrine working as designed — a shipped word is not demoted as a database
side effect. Pull the named selections (DELETE is the sanctioned half of
"replace wholesale"), re-run the carry-forward, then re-insert the
selections so the INSERT triggers re-check them against the carried
verdicts; `correct_canon_review_rung.py` below re-derives their rung
either way.

Then re-apply the canon rung corrections (CORE-1985). The fresh build has
every canon selection back at `machine`; the script re-derives which rows a
person actually reviewed from the endorsements and deciders already in the
database, and is idempotent:

```bash
uv run python scripts/correct_canon_review_rung.py --db build/translations_v2.db
```

Last, verify the rebuilt file against the durable copy — BEFORE section 2:

```bash
for db in "$LEGESHER_DATA_REPO/db/translations_v2.db" build/translations_v2.db; do
    echo "== $db"
    sqlite3 "file:$db?mode=ro" \
        "select 'screenings', verdict, count(*) from option_screenings group by 2
         union all
         select 'canon', status, count(*) from canon_selections group by 2;"
done
```

The screening verdict counts must MATCH the durable copy exactly. The canon
rung counts must match unless the v1 source gained or lost selections since
the durable copy was cut — in which case say, out loud, why each difference
exists before proceeding. The superseded build moved aside at the top of
this section is the third witness: `sqlite3` the same query against
`build/translations_v2.superseded.db` when the other two disagree. A
difference nobody can explain is a stop, not a footnote — data-repo
history already records one rebuild that silently reverted durable state
(the CORE-1866 incident), and this verification is what makes that class of
loss loud.

If a crash left a `-journal` file beside any of these databases, even the
read-only opens above will refuse until the journal is rolled back — and
rolling it back requires a read-WRITE open. For the build files that is one
harmless command (`sqlite3 build/translations_v2.db "PRAGMA
integrity_check;"`), then re-run the check. For the durable file, never
roll back in place: delete your local copy and re-pull it from the data
repo, so the recovery is a fresh checkout rather than a write to the one
copy everything else verifies against.

## 2. Dry export — review before anything leaves the machine

```bash
uv run python scripts/export_corpus.py \
    --db build/translations_v2.db --out build/hf-corpus
```

No network library is touched. `--out` names a directory the export takes
over entirely, so it refuses up front on a `README.md` that is not a
dataset card — pointing it at a package directory would overwrite that
package's README. Review:

- `build/hf-corpus/reconciliation.json` — row counts must reconcile (the
  export hard-fails if not). Since CORE-1828 the invariant is
  `db_rows == parquet_rows + quarantined_rows`, not equality: every config
  carries a `quarantined_rows` count of the community submissions held back
  for screening. A non-zero value is normal and is the number to sanity-check
  against `quarantine-queue` — an exclusion the ledger could not see would be
  a silent cap;
- `build/hf-corpus/README.md` — the dataset card. Check the frontmatter reads
  `license: cc-by-4.0` and that Upstream projects lists all three projects. A
  card that still says `license: other` means the build ran against a stale
  checkout. Check too that the `language:` header and the `## Languages` list
  name the locales you expect: both render from the options actually being
  published, so a locale missing there is quarantine holding back everything
  in it;
- `build/hf-corpus/NOTICE` — the three upstream licence notices, including the
  changes-were-made statement Apache-2.0 requires;
- `build/hf-corpus/PRIVACY.md` — the privacy posture the card links;
- `build/hf-corpus/assets/*.png` — the card's banner, and nothing else beside
  it;
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
(`README.md`, `NOTICE`, `PRIVACY.md`, `reconciliation.json`,
`data/*.parquet`, `assets/*.png`) — a stray file in the output directory never
reaches the Hub.

Three of those are the card's companions rather than data, and each is on the
allowlist for a reason:

- `assets/*.png` is the card's banner. The card links it relatively, so it has
  to ride along or the public page opens on a broken image. The exporter
  refuses to start without it. It also refuses if any OTHER image is sitting
  in `<out>/assets`, rather than deleting it: everything there is published,
  and no sweep can tell a renamed banner from a file that simply lives in that
  directory. If you renamed the banner, delete the old one yourself. The push
  removes the superseded remote copy for you (`delete_patterns`).
- `NOTICE` carries the upstream licence text. It is off the card by choice —
  the card describes *this* dataset's licence — but the retention obligation
  attaches to the data, so the notices travel with it.
- `PRIVACY.md` is the privacy posture, likewise moved off the card and linked
  from it.

Dropping any of the three from the allowlist does not fail the push; it
publishes a card whose links resolve to nothing.

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
