# Intake import runbook — the interim moderation ritual

<!-- disposition: MAINTAINER (CORE-1828, decision 2026-08-11) -->

> **Maintainer-only.** How community submissions become corpus rows while the
> automated moderation gate (CORE-1797) does not yet exist: **the maintainer is
> the screen** — openly, as this documented ritual, not as an unstated gap.
> What contributors are promised is in
> [CONTRIBUTOR_PRIVACY.md](../../../CONTRIBUTOR_PRIVACY.md); this is how the
> promise is kept at import time.

## The rule

Every community submission is **quarantine-by-default**. The importer
(CORE-1688) runs the mechanical validators, but nothing a stranger submits
becomes ranking-visible or corpus-exportable until a maintainer clears it
during this ritual. "Submissions are screened before they compete" — with a
human as the screen.

Mechanics, so you can trust them:

- New community options land with a `quarantined` verdict in
  `option_screenings` (append-only; the latest verdict per option wins).
- A quarantined option is invisible to `option_standings` and everything built
  on it, refused by the canon gate, and held out of the corpus export (the
  export ledger counts what was held back — `quarantined_rows`).
- Clearing is a **distinct, attributed act**: `clear-option … --by <you>`
  writes the auditable per-option record CORE-1797's automated gate will later
  write in the same shape.

## The ritual

Run from `libs/i18n`, with the operational database copied in from the durable
data home (`$LEGESHER_DATA_REPO`, CORE-1794):

1. **Triage the intake queue** — open submissions:
   bundle PRs into `reviews/incoming/`, `language_pack_review` issues, and
   anything forwarded from the reviews inbox.

2. **Run the import** (per submission). **Export the escrowed contributor salt
   first** — the importer refuses the public dev salt, and refuses a salt whose
   fingerprint disagrees with the database's `build_meta`. Both refusals exist
   because `contributor_id` is a primary-key ingredient: importing under the
   wrong salt forks every id it writes, and `--sync` would push the fork.

   ```bash
   read -rs LEGESHER_CONTRIBUTOR_SALT && export LEGESHER_CONTRIBUTOR_SALT
   uv run legesher-i18n import-issue <issue-url> --db build/translations_v2.db
   uv run legesher-i18n import-review-bundle <file> --db build/translations_v2.db
   ```

   Read the per-stage report. `returned` prints an actionable report to send
   back; **`halted` means the withdrawal rule fired — a person who withdrew has
   apparently come back. That decision is yours, never the importer's.**

   A `returned` submission is not dead: once you have fixed the cause (registered
   a missing concept, added a locale), re-run the import on the *same* file. The
   session resumes and completes — same bytes, same session uid, one row.

3. **Eyeball every new rendering** — the human screen (slur / injection / spam
   judgment, in the language or with a speaker's help):

   ```bash
   uv run legesher-i18n quarantine-queue --db build/translations_v2.db
   ```

   Pay attention to `[warn]` conduct findings in the import report — they are
   escalations to you, not verdicts.

   **Conduct wordlists live in the durable data home, not here** (decision
   2026-08-11). Pass one per locale:

   ```bash
   uv run legesher-i18n import-review-bundle <file> \
       --wordlist "$LEGESHER_DATA_REPO/screening/wordlists/<locale>.txt"
   ```

   Two reasons the list is not in this repository. It is a curated register of
   slurs and epithets, and this repository is going public — publishing it
   under the project's name is its own harm. And a published filter is a filter
   an adversary can read and walk around, which is an open CORE-1797
   sub-decision, not something to settle by accident.

   What the list is *for* is narrower than it looks: every community submission
   is quarantined regardless, so a hit changes nothing about what ships. It is a
   **triage sort key** — it decides what you read first in the queue. So keep it
   high-signal rather than exhaustive; a list that flags a third of submissions
   tells you nothing. Sourcing is a native-speaker job, not a model's.

4. **Clear or hold**, per option, attributed:

   ```bash
   uv run legesher-i18n clear-option <opt_uid> --verdict cleared --by <you> \
       --note "import ritual $(date +%F)"
   # or --verdict held --note "why it stays back"
   ```

5. **Reply on the source issue** — the contributor must SEE that it landed.
   The import prints a ready-to-post reply (session + option uids, what
   happens next); `--reply` posts it, labels `contrib:imported`, and closes.

   **You name the issue, never the submission.** `import-issue <url>` replies on
   the URL you typed; for a bundle file, pass `--reply-to <issue url>`. The
   target is validated as a real GitHub issue URL and is never read from the
   bundle — a submitter who could set it would have `gh` comment on, label and
   **close** any issue your token can write to.

   **A `halted` import replies with nothing.** The reason names a withdrawal,
   and posting it on the contributor's own public issue would re-associate that
   account with the erasure they asked for. Write to them yourself, and do not
   quote the report.

6. **Push to the durable data home** — the run is not over until this
   happens (`--sync` on the import does it, or re-run after clearing):
   database + accepted raw payloads land in `$LEGESHER_DATA_REPO`
   (`db/`, `intake/<YYYY-MM>/`). An unpushed import exists only on one
   workstation.

Cadence: **weekly at minimum** while volume is low. The forms and REVIEWING.md
say so to contributors (CORE-1466/CORE-397) — honesty about the screen is part
of the design.

## Rebuilds

`migrate_to_v2.py` rebuilds `build/translations_v2.db` from scratch and does
not know about intake sessions. The archived raw payloads in the data home are
the rebuild source: re-run the importer over them (oldest first) after a
rebuild. Re-import is idempotent — content-addressed uids make a replayed
payload a no-op against rows that already exist — and the withdrawal rule
keeps a replay from resurrecting an erased identity. Cleared verdicts live in
`option_screenings` inside the database copy in the data home; a from-scratch
rebuild replays imports into quarantine, and your clearing decisions are
re-applied from the previous database copy or re-made at the next ritual.

## Exit

Retiring this ritual is a deliberate act recorded on CORE-1797 when the
automated gate ships — not a side effect.
