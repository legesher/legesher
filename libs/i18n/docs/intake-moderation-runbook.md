# Intake moderation runbook: screening community submissions (CORE-1828)

<!-- disposition: MAINTAINER (CORE-1724 audit, 2026-08-11) -->

> **Maintainer-only.** This is not a contributor workflow. It is the sequence a
> maintainer walks over the community intake queue, on a cadence rather than
> per submission. If you are looking for how to contribute a translation, start
> with [`REVIEWING.md`](../REVIEWING.md).
>
> It is published openly on purpose: `REVIEWING.md` and the issue forms promise
> contributors that a human screens every submission before it becomes visible,
> and that promise should be auditable rather than taken on trust.

Automated submission screening does not exist yet. Until it does, **the
maintainer is the screen**, and this document is what that means in practice.
Everything a stranger submits is quarantined on arrival: the mechanical
validators run, but nothing becomes ranking-visible or corpus-exportable until
a person has read it and cleared it.

**Cadence:** weekly at minimum while volume is low. That is the number the
contributor-facing copy states, so it is a commitment, not an aspiration. A
week with an empty queue still ends with the queue checked.

## The queue

Community submissions arrive as GitHub issues from four forms, each carrying
`contrib:localization`:

| form | what lands | intake shape |
| --- | --- | --- |
| Propose a Translation Option | one option, with rationale and descriptors | one option + one endorsement |
| Review a Language Pack | many terms in the emoji notation | one session, many options and endorsements |
| Native Reviewer Signup | a reviewer, a language, a credit choice | an identity, no corpus rows |
| Pack Feedback or Term Flag | a flag against an existing option | one flag, routed to review |

Everything below applies to the first two. Signups mint an identity and never
write corpus rows, so they need consent recorded and a reply, nothing more.
Flags write no options; they route to native review and are tracked to a
resolution on the option.

## 1. Triage the queue

Read the open issues carrying `contrib:localization` that you have not yet
imported. For each one, decide only whether it is intake-shaped:

- **Import it** if it has a term, a language, a word, and the consent checkbox
  ticked.
- **Ask a question on the issue** if a field is missing or ambiguous. A
  submission you do not understand well enough to screen is not one to import.
- **Close it** if it is spam or plainly not a translation submission. Say why.

Consent is not a judgment call: **no consent checkbox, no import.** Reply and
ask, do not infer it.

## 2. Import

Run the intake importer over the triaged issues. It mints or resolves the
contributor identity, records the consent version and date, writes the options
and endorsements, and stamps every new row as **quarantined**.

**Export the escrowed contributor salt first.** The importer refuses the public
development salt, and refuses a salt whose fingerprint disagrees with the target
database's `build_meta`. Both refusals exist because `contributor_id` is an
ingredient of a primary key: importing under the wrong salt forks every id it
writes, and the push in step 6 would carry the fork to the durable home.

```bash
read -rs LEGESHER_CONTRIBUTOR_SALT && export LEGESHER_CONTRIBUTOR_SALT
uv run legesher-i18n import-issue <issue-url> --db build/translations_v2.db
uv run legesher-i18n import-review-bundle <file> --db build/translations_v2.db
```

Read the per-stage report each run prints. Three outcomes need a decision:

- **`returned`** — a rule was broken; the printed report is what you send back.
  A return is not fatal: once you have fixed the cause (registered a missing
  concept, added a locale), re-run the import on the *same* file and the session
  resumes and completes, one row, same session uid.
- **`halted`** — the withdrawal rule fired: someone who asked to be forgotten
  appears to have submitted again. **That decision is yours, never the
  importer's.** Reply by hand, and do not quote the report — it names the
  withdrawal.
- **`accepted`** — go to step 3.

Conduct wordlists (the per-locale slur/epithet lists the screen checks free text
against) live in the durable data home, never in this repository — publishing a
curated slur list under the project's name is its own harm, and a published
filter is one an adversary can read around. Pass one with
`--wordlist "$LEGESHER_DATA_REPO/screening/wordlists/<locale>.txt"`. A hit is a
triage sort key, not a verdict: everything is quarantined either way.

What matters beyond the flags is the contract the importer honours:

- Import is idempotent. Re-running over the same issue writes nothing new
  (bundle digests are content-addressed).
- Nothing it writes is visible to rankings, and nothing it writes is included
  in a corpus export, until step 4 clears it.
- Contact details never enter the database from a public issue. Contributors
  who want to be reachable write to the contribute address; that is the only
  path an email takes into the private identity table.

## 3. Screen each new rendering

This is the step no tool does for you. Read every newly imported word and ask,
in this order:

1. **Is it harmful?** A slur, sexualized, degrading, or unusable in a room full
   of students, in the language it claims to be. If you cannot judge that in the
   language, you cannot clear it: hold it for a native reviewer (step 4).
2. **Is it an injection attempt?** A "word" carrying markup, control characters,
   invisible characters, or anything shaped like an instruction to a downstream
   tool rather than a term. The validators catch most of this; you are the
   backstop for what they do not.
3. **Is it spam or nonsense?** Keyboard mash, advertising, a copy of the English
   word with no rendering attempted.
4. **Is it plausibly a serious contribution?** That is the whole bar. Screening
   is not review. A word you personally doubt, disagree with, or would not have
   chosen still clears: deciding whether it is the *right* word is the
   community's job, not yours, and the whole point of the options model is that
   you do not have to be right about it.

Judge the rendering, never the contributor. A weak first submission from
someone learning is cleared, then reviewed.

## 4. Clear or hold

Every screened option gets a recorded decision, per option, so the record is
auditable and so the automated gate can inherit the same shape later:

- **Clear** — the option becomes ranking-visible and export-eligible. Record who
  cleared it and when.
- **Hold** — the option stays quarantined pending a native speaker's judgment.
  Record the reason. A hold is not a rejection and is not a moderation verdict;
  it says *this needs eyes I do not have*.
- **Reject** — harmful, spam, or an injection attempt. Record the reason. The row
  stays (the corpus is append-only) and stays out of every export.

```bash
uv run legesher-i18n quarantine-queue --db build/translations_v2.db
uv run legesher-i18n clear-option <opt_uid> --verdict cleared --by <you> \
    --note "import ritual $(date +%F)"
# or --verdict held / --verdict rejected, each with a --note saying why
```

`--by` is required: an unattributed moderation decision is not auditable. Every
verdict is appended, never overwritten, so the sequence of decisions on an
option stays readable. Only `cleared` is visible anywhere — held and rejected
are withheld by the same predicate, so nothing depends on the difference except
the record of what you judged.

An option that is currently canon-selected cannot be withheld in place: pull it
from `libs/i18n/canon/<locale>.toml` and reload first, so a demotion is always a
reviewed text change.

A hold that no native reviewer can resolve stays a hold. Time does not clear
anything by itself.

## 5. Reply on the issue

Every imported issue gets a reply saying what actually landed: which terms were
recorded, which are held and why, and what happens next. Then close it.

This is the visible half of the promise. A contributor whose word disappeared
into a database without a word back has no reason to send a second one. Keep it
short, name the specific terms, and do not thank people in a way that implies
their word was chosen: it was recorded, which is a different and more honest
thing.

If a submission was rejected, say which guideline it failed and how an appeal
works. If it was held for native review, say so plainly rather than leaving it
sounding accepted.

Every import prints a ready-to-post reply naming the session and option uids.
`--reply` posts it, labels `contrib:imported` and closes — for accepted
submissions only. Two rules the flag enforces for you:

- **You name the issue, never the submission.** `import-issue <url>` replies on
  the URL you typed; a bundle file needs `--reply-to <issue url>`. The target is
  validated and never read from submission content, because a submitter who
  controlled it could have `gh` comment on, label and close any issue your token
  can reach.
- **A halted import replies with nothing at all**, for the reason in step 2.

## 6. Push to the durable data home

The working database is untracked. A ritual that ends on your laptop has not
happened:

`--sync` on the import does this for you — WAL checkpoint, database copy, raw
payload archived under `intake/<YYYY-MM>/`, path-scoped commit, push — or do it
by hand after clearing:

```bash
cp libs/i18n/legesher_i18n/db/translations.db "$LEGESHER_DATA_REPO/db/"
cd "$LEGESHER_DATA_REPO" && git add db/translations.db && git commit && git push
```

The pushed database copy is the rebuild source. `migrate_to_v2.py` rebuilds
from v1 and knows nothing about the intake layer — not the sessions, not the
community options (most exist in no v1 table), and not your clearing
decisions, which live in `option_screenings` inside the database itself.
What restores all of it after a rebuild is the intake-layer carry-forward
from the durable copy — `scripts/carry_forward_screenings.py`, run as part
of the rebuild-integrity sequence in
[`corpus-publish-runbook.md`](corpus-publish-runbook.md) section 1
(CORE-2052). That sequence is the one rebuild path: the `--sync` payload
archive under `intake/<YYYY-MM>/` is a raw record for audits, not a rebuild
mechanism, and the durable home currently holds no such archive — nothing
may assume one exists. If this push step is skipped, the carry-forward has
nothing to carry from, which is one more reason a ritual that ends on your
laptop has not happened.

Commit message names the date and what the run took in ("intake: 2026-08-18, 4
issues, 31 options, 2 held"). That message is the run log.

## Exiting this ritual

This ritual is interim. It retires when the automated screening gate ships, and
retiring it is a deliberate act recorded on **CORE-1797**, not a side effect of
the gate landing. Two things change at that point and nothing else does:
clearing becomes automatic for submissions the gate passes, and this document
plus the screening paragraph in `REVIEWING.md` are rewritten in the same change,
so the contributor-facing promise never describes a process that is no longer
what happens.

Until then, if a week is missed, the honest fix is to walk the queue late, not
to quietly widen the cadence the forms promise.
