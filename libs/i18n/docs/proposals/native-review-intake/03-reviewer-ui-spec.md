# Reviewer UI spec — the native-review app

The Stage-1 static app (doc 01 §2): client-only, loads a review kit, emits
a review bundle. Same screens mount on the Stage-2 portal unchanged. This
spec covers every view, the interaction contract per view, and the
onboarding copy. Mockup: see the published design mockup (session artifact)
— screens track this spec 1:1.

Design-system notes (canonical DS: Cowork/Legesher Design System —
`colors_and_type.css` is the token source): brand poles cyan `#6cc5e0` /
coral `#ec6756`, yellow `#F6F16F` accent, warm-grey neutrals on white/
`#f6f6f6`; **square gradient-filled buttons** (the DS signature; hover
scale 1.05 / press 0.95 over 700ms), cards white with 8px radius + hairline
border + hover-lift (never the colored-left-border trope); code samples on
the DS editor surface (`#1E1E1E` + its syntax tokens); Noto Sans / Noto
Sans Display / Noto Sans Mono / Noto Sans Arabic (all-Noto so text renders
in any language); Title Case headings, "we + you" voice, real multilingual
strings, emoji as sparing accents. The app is bilingual by construction:
chrome renders in the reviewer's language where localized (falling back to
English), concept material renders English + target side by side.

## 0. Principles the UI must express (not just permit)

1. **The reviewer is the linguist.** Models and prior projects supply
   *material*; the reviewer supplies *judgment*. Copy never says "verify
   the AI translation" — it says "what should this concept be called?"
2. **Blind first.** Their own answer is captured before any candidate is
   visible. No skipping ahead; "I don't have a word for this" is a valid
   blind answer and is recorded as such.
3. **No downvotes.** Verbs in the UI: *endorse*, *pass*, *flag*, *rank*.
   Nothing is phrased as rejection of a person or a community's word.
4. **Source-blind judging.** Candidate provenance (which model, which
   initiative, the current pack) is hidden until the reviewer locks a
   ranking for that concept, then always visible. Their own suggestion is
   the one visible exception.
5. **Creativity is welcome; the gates are mechanical.** Identifier
   validity runs live in the editor (immediate red on a space or an
   NFKC-unstable character, with the reason in plain language) so the only
   "rejections" a reviewer ever sees are physics, not taste.
6. **RTL is first-class.** Direction flips from the locale profile; code
   samples render mixed-run correctly (storage order shown on demand);
   the app itself is the reference implementation of the `_rtl.yml` rules.

## 1. View: Onboarding — the perspective shift

Full-screen, three panels, shown once per locale (revisitable from the
header). Panel copy (EN master; localize with the kit):

> **Panel 1 — The question.**
> If computer science had grown up in your language first — how would these
> ideas be taught? What would the textbook say? What word would a teacher
> write on the board for *"do this only when that is true"*?
>
> That word — not the English one — is what you're here to find.

> **Panel 2 — What we're NOT doing.**
> We are not transcribing English sounds into your script. `الفور` for
> `for` teaches nothing; a learner deserves the word their language would
> have chosen on its own. Some concepts *will* already have a real word —
> classroom terms, textbook terms, words your community genuinely uses
> (including genuine loanwords: if your language really says «كمبيوتر»,
> that's your word, and that's legitimate). Where no word exists yet, you
> get to coin one — that is not cheating; it is how every language built
> its scientific vocabulary. If a phonetic borrowing truly is what your
> community uses, mark it with the *transliteration* tag so the data says
> so honestly.

> **Panel 3 — How it works.**
> For each concept: first *your* word, from your own head — then every
> candidate we've collected (from models, from other localization
> projects, from earlier contributors), which you endorse, rank, tag, and
> comment on. You can't get it "wrong": the only hard rules are mechanical
> (a keyword can't contain spaces, and must survive Unicode
> normalization), and the tool checks those for you as you type.
> Your review ships credited to you (if you want), and because concepts are
> shared across programming languages, the word you choose for `break` in
> Python ships everywhere `break` exists.

Footer: rung explanation in one line ("you're reviewing as
*native (claimed)* — each endorsement carries the rung you hold when you
make it; after verification, one tap re-affirms your earlier endorsements
at your new rung"), CoC link, estimated time ("a full keyword pass is
~2–3 hours; you can stop and resume — partial sessions submit cleanly").

## 2. View: Session dashboard

- Locale + track picker (reserved words / error messages / style profile),
  resume card for a saved draft (drafts autosave to browser storage;
  export/import draft file for machine moves).
- Progress: concepts done / total, grouped by consistency group; the
  **second-endorsement queue first** badge ("11 words are one endorsement
  away from *reviewed* — start here").
- Locale status strip: current ladder position (experimental → official
  progress bar built from `locale_progress`), reviewers so far,
  "your Turkish `break` would ship in 10 programming languages" reuse line.
- **Re-affirmation card** (appears once, after a rung promotion): "You're
  now *native (verified)* — re-affirm your N earlier endorsements at your
  new rung?" One tap; produces a new session that retracts + re-endorses
  (the history stays). This is what makes "verification can come after"
  true in the data, not just the copy.

## 3. View: Concept review — Phase A (blind)

Layout: concept card left (or top on narrow), entry panel right.

Concept card (from kit): definition_en; brief Quick Summary; ONE code
sample (DS editor surface) with the term highlighted — code shown in **English
form** in Phase A; semantic components ("production + pause + iteration",
from the brief); consistency-group strip (sibling concepts + the
reviewer's earlier answers for them, greyed if unanswered); pattern class
("action keyword — usually a verb form in your language"); phrase badge if
compound (elif → "this is a contraction of a phrase").

Entry panel:

- The prompt: "**What would you call this?** Your first instinct, before
  seeing anyone else's answer."
- Term input: live mechanical validation (identifier rules, NFKC check,
  live collision check against the reviewer's own earlier answers in this
  session and current canon — collision shows *which* concept owns the
  word, since round-trip requires distinct words).
- Word-form select (from the brief's family recommendation, pre-filtered
  per locale family; free entry allowed).
- "Is this an established term?" — `established / my coinage / unsure`.
- Self-tags (optional checkboxes): *transliteration* · *cognate/loanword*
  · *regional*. Transliteration tooltip: "a sound-copy of the English
  word. Legal to submit — just label it, so the community can see how
  common that preference is."
- One-line rationale (optional but nudged).
- Actions: **Lock & see candidates** · **I don't have a word** (records
  the blank blind, proceeds).

Locking is one-way (that's the point); the reviewer's term is minted into
the candidate set for Phase B, visibly badged "yours".

## 4. View: Concept review — Phase B (candidates)

The reveal: deduplicated candidate cards, source-blind (badge slots render
"?"), the reviewer's own card marked. Each card: the word (large, target
script), word-form, expansion if phrase-class, live validation state
(a mechanical failure renders the card dimmed with the reason — still
flaggable/commentable, not endorsable), existing endorsement count as a
dot-cluster (not a number — reduce herding), annotation chips already
attached by others (translit/cognate/…).

Interactions per card:

- **Endorse** (toggle; square button): "I would teach this word."
- **Tag** (chips): transliteration · cognate/loanword · established ·
  coinage · formal · informal · regional.
- **Flag** (overflow menu, deliberate friction): offensive / wrong meaning
  / register mismatch / spam — requires a comment; copy reminds that
  "prefer another word" is expressed by endorsing the other word, not by
  flagging this one.
- **Comment** (thread per card; seeds the corpus commentary).
- **Pass** = doing nothing. Explicitly legitimate; footer says so.

Ranking bar (appears once ≥1 endorsement): drag endorsed cards into order;
slot 1 labeled "**ship this**". On lock: provenance reveals (model names,
initiative badges with attribution + "used in classrooms" note where true,
"current pack" badge, other contributors' as "community"), and a
post-reveal edit window allows one reorder with a recorded
`revised_after_reveal` note — provenance is information too; measure how
often it changes minds rather than pretending it doesn't.

Then: optional concept commentary box ("how would you *explain* this
concept to a student, in your language?" — topic-tagged), and **Next**
(auto-advances along the consistency group).

## 5. View: Phrase concepts (elif-class)

Phase A gains a two-step: (1) "Say it in full — how does *'otherwise, if'*
read in your language?" (expansion, free text, spaces welcome — this is
prose, not identifier); (2) "Now make it a single token" (contraction
input, mechanical validation on). The contraction strategies panel shows
the locale's word-boundary rule from the style profile (e.g. "Urdu:
underscore-joins; CJK: concatenate") with the reviewer able to dissent via
a style comment.

Phase B ranks (expansion, contraction) pairs; two candidates sharing an
expansion group visually. Commentary prompt targets formation: "should
compounds like this join with `_`, fuse, or abbreviate? What would feel
natural in a textbook index?"

## 6. View: Error-message review (track 2)

Per template: English template with placeholders locked as chips
(`{name}`, `{obj_type}` — cannot be deleted, can be reordered), current
localized draft editable inline, placeholder integrity validated live,
length meter tuned to "short beats long" (the SIGCSE result quoted in one
line), original-alongside preview exactly as the runtime dual-display will
render it. Endorse / suggest-new / tag / comment as in Phase B. Grammar
notes field (plural rules, agreement) feeds `message_translations` review
metadata.

## 7. View: Style profile (track 3)

A ten-question survey, one screen per field (doc 02 field list), each
question shown with live previews rendered in the reviewer's script — e.g.
constants strategy shows the same constant as `ثابت_حد_أقصى` vs `حد__أقصى`
vs positional, as real code cards. Modifier-order question uses a worked
compound ("value error": noun+noun order, adjective placement). Every
answer takes a rationale; "no preference / defer" is an explicit option.
Closing screen restates: **style guides are suggestions** — this records
your community's preference, it never becomes a lint law.

## 8. View: Submit & verification

Pre-submit summary (counts per phase, unanswered list with jump-links),
attestation checklist (native/fluent; original work; Apache-2.0 grant for
submitted terms; CoC; DCO line preview), consent toggle for public credit
(name as it should appear; default = opaque id only), then bundle
download + one-click "open PR" (prefilled) or "submit via issue" fallback.
Post-submit screen mirrors the verification pipeline stages with live CI
status when reachable, and states plainly what each outcome means
(`returned` = fixable, nothing lost; rows with mechanical failures still
enter the corpus as evidence, they just can't ship).

## 9. View: Recognition & locale dashboard (public, read-only)

Per locale: ladder progress, reviewer credits (consented names + opaque
ids), founding-reviewer marker, per-PL reuse table ("reviewed once, ships
in N packs"), open second-endorsement count as the call-to-action. This
page is the shareable artifact for reviewer recruitment.

## 10. Accessibility & internationalization requirements

- Full keyboard operation; ranking has button-based reorder (drag is an
  enhancement); screen-reader labels carry the English token + target term
  with correct `lang`/`dir` attributes per element.
- Mixed-direction layout tested per `_rtl.yml`; storage-vs-display order
  toggle on code samples.
- Font stack per script family with graceful fallback + a "missing glyph"
  detector that warns rather than tofu-ing.
- Every mechanical rejection message states the rule in plain language +
  the failing character (`"ب‌ت" contains U+200C ZERO WIDTH NON-JOINER —
  invisible characters aren't allowed in identifiers`).
- Offline-capable (kit + app cache); bundle never leaves the machine until
  the reviewer submits.
