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

The importer's command surface is documented with the importer itself; this
runbook governs the order and the judgment, not the flags. What matters here is
the contract it must honour:

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

## 6. Push to the durable data home

The working database is untracked. A ritual that ends on your laptop has not
happened:

```bash
cp libs/i18n/legesher_i18n/db/translations.db "$LEGESHER_DATA_REPO/db/"
cd "$LEGESHER_DATA_REPO" && git add db/translations.db && git commit && git push
```

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
