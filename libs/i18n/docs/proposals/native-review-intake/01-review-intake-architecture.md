# Native-review intake architecture

How native-speaker review is collected, verified, stored, aggregated, and
turned into pack promotion — from the reviewer's first keystroke to the
`experimental → reviewed → official` ladder and the terminology corpus that
feeds `legesher translate`.

Ground truth this builds on (verified 2026-07-18):

- **Committed:** `libs/i18n/legesher_i18n/db/schema_v2.sql` (CORE-1501) —
  concepts, options (content-addressed `opt_` uids), positive-only
  endorsements with `method='portal'` seams, `option_flags`,
  `option_validations`, `canon_selections` + validation triggers,
  `review_queue` / `locale_progress` views, `review_rungs` ladder
  (CORE-1466), `contributors` / `contributor_identities` split (CORE-1502).
- **Live but v1:** `translations.db` (terms/languages/translations/
  selected_translations). The v2 migration is the gate on the HF publish
  (CORE-1312).
- **Missing (this proposal fills):** canon TOML files + loader
  (`libs/i18n/canon/<locale>.toml`, `make canon-load` — specified, not
  built), any review surface beyond the GitHub issue form
  (`.github/issue_template/language_pack_review.yml`), session/ranking/
  annotation structure, the importer, promotion automation, and exports.

## 1. Decided constraints (not re-opened here)

| constraint | source |
| --- | --- |
| Native reviews are iterative and **non-blocking**; mechanical gates are the quality floor | decision 2026-07-09 |
| Options-collection model: keep every candidate with provenance; distill options → experimental → official; deliberately unlike Crowdin/Weblate one-truth-per-term | decision 2026-07-12 |
| Endorsements are positive-only; disagreement = endorse a different option; harm = flag; **no downvotes** | CORE-1501 design |
| A model proposes; **only a person endorses** | CORE-1501 design |
| Best-effort NATIVE translation; target-script over loanwords; coining native words is legitimate (ISO 704); gate blocks on ERRORS only | CORE-1318 |
| Transliteration is never an acceptable **generation** fallback; genuine cognates/loanwords are fully legitimate | decision 2026-07-05 |
| Corpus is append-only, published ids are content-addressed, PII never exports | CORE-1501/1502 |
| Pack data (glossaries) are Apache-2.0; hosted operations are the commercial layer | collaboration decisions 2026-07-10 |
| Style guides are suggestions, never mandates | standing feedback |

One reconciliation this proposal makes explicit: Madison asked for
"approve/disapprove + rank." Under the no-downvote model that maps to
**endorse** (approve), **pass** (no action — the quiet default),
**flag** (structured objection: offensive / wrong meaning / register
mismatch / invalid identifier / spam), and **rank** (session-scoped
preference among the options the reviewer endorsed). "Disapprove" as a
first-class negative vote is deliberately absent — it invites brigading of
minority-language terms and corrupts the "how many people said this word"
number (CORE-1501 §2 rationale). The UI copy owns this framing (doc 03).

## 2. Topology: three intake stages, one contract

```text
Stage 0 (today)     GitHub issue form (emoji notation) ──┐
Stage 1 (build now) Static review app → review bundle ───┼→ importer → corpus
                    (client-only; submitted via PR)      │   (one pipeline)
Stage 2 (CORE-1412) Hosted portal (Turso/Supabase) ──────┘
```

**Stage 0 — keep the issue form, add the importer.** The existing
`language_pack_review.yml` form stays open (zero-friction, good-first-issue).
A maintainer command (`legesher-i18n import-issue <url>`) parses the emoji
notation into corpus rows: ✅ → endorsement (`method='github'`), ❓ → new
option + endorsement of the alternative, 🤔 → commentary. Sessions minted
with `method='github'`, `elicited='quick'`. Nothing about Stage 1 obsoletes
this lane; it is where drive-by reviewers start.

**Stage 1 — the review app + bundle (the build target of this proposal).**
A static, client-only web app (no backend, hostable on legesher.io or
runnable from a local file) that:

1. loads a **review kit** for a locale — a JSON artifact built from the DB;
2. runs the structured flow (doc 03): onboarding → blind elicitation →
   candidate endorsement/ranking → phrase expansion → commentary → style
   questionnaire (optional track) → attestation;
3. emits a **review bundle** — one canonical-JSON file the reviewer submits
   by opening a PR into `libs/i18n/reviews/incoming/<locale>/` (the app
   deep-links a prefilled GitHub PR/issue; reviewers without git accounts
   can attach the file to an issue or email it to a maintainer, who commits
   it — attribution then flows through the bundle's contributor block, not
   git authorship).

Why this shape: it honors the hosting decision (no live infrastructure
before reviewer traffic justifies it — CORE-1412 deferred), it gives
non-developer linguists a real UI instead of raw YAML editing (the
PR-friction concern), it keeps every submission PR-reviewable text (the
2026-07-10 guardrail), and the bundle becomes the wire format Stage 2
reuses verbatim server-side. CI runs the importer in `--check` mode on
bundle PRs, so verification results appear as PR checks; merge = ingest.

**Stage 2 — hosted portal.** When reviewer traffic is real, the same app
mounts on the graduated DB (Turso/Supabase per the deferred decision);
bundles post to an API instead of a PR, sessions verify synchronously,
and Certified-lane features (assignment, payment for the education
fair-wage lane, org dashboards) attach here. The commercial surface sells
operations — certification workflow, uptime, analytics — never the data.

## 3. The review kit (what the app loads)

Built per locale by `legesher-i18n build-review-kit <locale>`, versioned by
DB snapshot (`kit_version` = schema rev + build date + content hash).
Contents:

- **concept cards**, ordered by consistency group then category — never
  alphabetically (return/yield/await review as a set; elif adjacent to
  if/else): slug, `definition_en`, brief excerpts (Quick Summary, Concept
  Explanation, Linguistic Form Recommendation, consistency rules from the
  182 tier-1 briefs), code example with the term highlighted, PL surface
  forms + `used_by` list, version span, `pattern_class`, phrase-concept
  marker (elif-class compounds), culturally-loaded-vocabulary notes where
  the brief carries them.
- **current canon** for the locale (word + status + `identity_ok`).
- **candidates** per concept, deduplicated by NFC surface form (the
  content-addressed option identity guarantees the same word from three
  sources renders once, with badges):
  - existing corpus options with endorsement counts and validation state;
  - model-panel candidates (doc 05 §2) with `word_form`, confidence, and
    rationale;
  - initiative reference terms (doc 05 §3): Hedy / UniversalPython / UniPy /
    Scratch renderings with attribution. Non-redistributable sources are
    marked `reference_only: true` — the kit displays them; the importer
    never persists them as options unless a human independently submits or
    endorses the same word (which is that human's attestation, recorded with
    `source='community'` provenance plus a `matches_reference` note).
- **locale profile**: script, direction, keyboard notes, `terminology_policy`
  if set, style-profile answers to date.
- **kit manifest**: kit_version, locale, concept count, license/attribution
  block for every source shown.

**The kit is pre-moderated before it reaches a reviewer.** The conduct
screen protects the corpus; this protects the *reviewer*: candidates run
through the moderation wordlists and the open-flag ledger at kit build, and
a candidate with an unresolved `offensive` flag (or a wordlist hit pending
human review) ships in the kit only as a "withheld pending moderation"
placeholder. Native reviewers volunteering their language must not be the
mechanism by which model-generated slurs are discovered.

Candidate presentation is **source-blind by default**: during endorsement
the reviewer sees the words, not who proposed them (a Hedy badge would halo;
a model badge would repel). Provenance reveals after the reviewer locks
their ranking for that concept — and is always visible afterward. (Their own
blind suggestion is the exception: it is visibly theirs, pre-endorsed.)

## 4. The review bundle (the wire contract)

Canonical JSON (RFC 8785-style canonicalization → the bytes that mint
`ses_<24hex>`), one file per session:

```jsonc
{
  "bundle_version": "1.0",
  "kit_version": "v2@2026-07-18+a1b2c3",
  "locale": "ur",
  "track": "reserved_words",
  "contributor": {
    "source_key": "github:whoever",        // → contributors salted mint (CORE-1502)
    "claimed_rung": "native_claimed",
    "consent": { "credit_preference": "name",   // anonymous | handle | name (decided 2026-07-21)
                 "credit_text": "مدیحہ خان",     // required for 'name'; ignored otherwise
                 "consent_version": "2026-07" },
    "contact_captured": true               // email reached the PRIVATE channel — see §4a;
                                           // the address itself is NEVER in this file
  },
  "attestations": {
    "native_or_fluent": true, "original_work": true,
    "license_grant": "Apache-2.0", "coc_agreed": true, "dco": true,
    "research_use": true      // contribution DATA (terms, endorsements, tags,
                              // expansions, published commentary — never
                              // identity or private durations) may appear in
                              // research datasets and publications
  },
  "responses": [{
    "concept": "elif-compound-conditional",
    "blind": { "surface_form": "ورنہ_اگر", "word_form": "conjunction_compound",
               "established_term": "coined", "rationale": "…",
               "self_annotations": [] },
    "endorsements": [
      { "surface_form": "ورنہ_اگر", "annotations": [], "comment": null },
      { "surface_form": "ورنہاگر", "annotations": ["cognate_loanword"], "comment": "…" }
    ],
    "ranking": ["ورنہ_اگر", "ورنہاگر"],
    "flags": [{ "surface_form": "ایلف", "reason": "transliteration", "comment": "…" }],
    "expansion": { "for": "ورنہ_اگر", "text": "ورنہ اگر", "formation_note": "…" },
    "commentary": [{ "topic": "word_formation", "body": "…" }]
  }],
  "style_answers": [{ "field": "constants_strategy", "value": "marker_affix:ثابت_", "rationale": "…" }],
  "session": { "started_at": "…", "app_version": "…", "durations_ms": { "elif-…": 74000 } }
}
```

Notes: options are referenced by **surface form** (the bundle is written by
a client that may not know uids); the importer computes `option_uid` from
`(concept_slug, locale, pl_scope, NFC(surface_form))` exactly as schema v2
mints them, creating options that don't exist yet with
`source='community'` provenance. Flagging a candidate the reviewer also
ranked is a bundle-level validation error. Per-concept durations feed
brigading forensics only; they never export.

### 4a. Contact email — collected at every submission, never in the bundle

Decided 2026-07-21: every submission captures a contact email, validated.
Two constraints shape the mechanism:

1. **The bundle is a public artifact.** Stage-1 bundles land in a public
   repo by PR; an email inside the bundle would be published to git history
   forever. So the bundle carries only `contact_captured: true`, and the
   address lives exclusively in `contributor_identities.email` — the
   private table that never exports (CORE-1502 boundary).
2. **Validation is tiered, and never blocks.** At intake: syntax check
   (one `@`, dotted domain, no whitespace — mirrored by the DB CHECK as a
   floor) plus common-typo prompts (`gamil.com` → "did you mean…"), stored
   trimmed with the domain lowercased. Deliverability verification is a
   magic-link flow recorded in `email_verified_at` — it exists once the
   portal (or any endpoint) can receive the click; an unverified email
   never blocks a submission, it just stays unverified.

Transport per lane:

- **Stage-2 portal**: a native form field + the magic link. The end state.
- **Email lane** (non-GitHub reviewers): inherent — the submission *is*
  the email; the importer records the sender address.
- **Stage-1 PR/issue lane** (the gap): the app cannot write a private
  store without a backend. Two options, in order:
  - *Now, zero infra:* after the bundle downloads, the app opens a
    prefilled `mailto:` to the reviews inbox containing the session uid,
    a **contact nonce**, and the reviewer's address as sender; the
    importer matches on (session uid, nonce) and merges the address into
    `contributor_identities`.

    The nonce is load-bearing: the session uid alone is NOT a secret —
    it is `sha256(canonical bundle)[:24]` and the bundle is a public PR
    artifact, so anyone can compute any session's uid and mail the inbox
    claiming it. Deliverability verification proves inbox control, not
    bundle authorship. So the app mints a random nonce per session,
    shows it only in the app (never in the bundle), and the importer
    binds an address only when the nonce matches. A uid-only claim, an
    unknown nonce, or a claim conflicting with an already-bound address
    is HELD for manual reconciliation, never merged. (CORE-1568 carries
    the implementation.)
  - *When volume justifies:* one serverless endpoint (single POST of
    `{session_uid, contact_nonce, email, credit_preference}` into a
    private store the importer reads). Minimal, but it is
    infrastructure — flagged as its own decision in §12 rather than
    assumed.

`review_sessions.contact_captured` records the assertion; the verification
pipeline warns (never blocks) when a session arrives with
`contact_captured: false` or an address that never turns up on the private
channel. Unsolicited or conflicting address claims are held, not merged
(see the nonce rule above).

## 5. The importer + verification pipeline

`legesher-i18n import-review-bundle <file>` (same code path invoked by CI
on bundle PRs and by the Stage-2 API). Stages, in order, all recorded in
`review_sessions.verification_report`:

1. **Schema + integrity** — bundle validates against the JSON Schema;
   kit_version compatible with current DB (stale kits degrade gracefully:
   concepts that changed re-queue rather than fail); every referenced
   concept exists; ranking ⊆ endorsements; no flag∩ranking overlap.
   Failure → `returned`.
2. **Conduct screen** — comments/rationales/coinages scanned (wordlist +
   model-assisted, human-escalated; never auto-reject on model output
   alone) for CoC violations and PII in free text. Failure → `returned`
   (fixable) or `rejected` (violation). This is the only stage that reads
   *content* as content.
3. **Identity + attestation** — contributor minted/resolved via the salted
   pipeline (CORE-1502); DCO/CLA + license grant present; rung snapshot
   taken (`rung_at_session`). Claimed nativeness is recorded, not verified
   here — verification moves rungs, not sessions (doc 04 §4).
4. **Mechanical term gates** (ERRORS block the *row*, never the session):
   every new surface form runs the committed validator suite —
   `identifier_valid`, `nfkc_stable` (Thai sara-am carve-out per
   CORE-1514), `script_consistent`, `collides_en_keyword`,
   `min_interpreter_ok` — plus locale-internal collision (two concepts, one
   word → both recorded, collision surfaced to the selection step; recall
   cross-partition legality differs by PL family) and length-budget
   warnings from the locale's style profile. An invalid identifier still
   enters the corpus (append-only: evidence, not garbage) with its failed
   validation cached — it is simply **canon-ineligible**, exactly as the
   CORE-1400 reframe treats the 183 dirty exceptions.
5. **Quality signals (WARN, never block)** — the creativity-protection
   layer, stated as policy: *no stage compares a human submission against
   model output, and disagreement with the model panel is not a signal at
   all.* Warnings are: consistency-group form drift (return/yield/await
   mixing verb forms), transliteration-annotation missing on a form that
   trips the phonetic-similarity heuristic (suggest the checkbox, don't
   force it), novel coinage with no established-term sibling (routes the
   option into the second-reviewer queue with priority — more human eyes,
   not machine judgment).
6. **Ingest** — rows written append-only in one transaction: options →
   provenance → endorsements (+ session junctions) → rankings →
   annotations → expansions → flags → commentary (moderation_status
   respected) → style ratifications. Session → `accepted`. Idempotent by
   session uid.

## 6. Aggregation: from evidence to selection

Selection stays a **curation act with evidence attached** — automation
proposes, a maintainer (or, later, a language steward rung) commits the
canon TOML change; the DB trigger enforces that the chosen word is a
validated corpus option.

- **Option standing** = weighted endorsements (weights from `review_rungs`,
  policy-versioned) + latest-session rankings (Borda within each reviewer's
  ranked set — approval-first, rank as tiebreak). Views:
  `option_promotion_status` (per option), `latest_rankings`.
- **Reviewed rung** (Q5 recommendation, encoded as the
  `reviewed_eligible` query): ≥2 live endorsements at `counts_as_native`
  rungs, zero unresolved flags, mechanical validations green.
- **Disagreement** is data: two options splitting native endorsements with
  a `regional` annotation pattern → surface a locale-split suggestion
  (BCP 47 child locale) instead of averaging dialects (CORE-1501 §5).
- **Small-n reality**: one thorough native reviewer yields `reviewed`
  nothing — their top choice ships as `experimental` canon immediately
  (non-blocking principle) and the concept sits in the
  second-endorsement queue that the app surfaces first to the *next*
  reviewer of that locale.

## 7. Promotion: experimental → official as queries

Ladder per canon row (CORE-1466): `machine → experimental → reviewed →
official`. Pack-level status derives from row-level status —
`pack_promotion_status` is the dashboard; proposed gates (numbers are
Madison's to cut, doc 04 §7 carries the same table):

| pack status | criteria (all required) |
| --- | --- |
| experimental | mechanical gates green; ships immediately; banner + `metadata.community_reviewed: false` |
| reviewed | 100% canon coverage; ≥80% of canon rows at `reviewed`+; ≥1 native_verified reviewer covered the full surface; zero open ERROR-class flags |
| official | 100% coverage; ≥95% rows `reviewed`+; ≥2 distinct `native_verified`+ reviewers across the pack; style profile ratified (all 10 fields answered, majority agreement); zero open flags; stable one full release cycle |

Demotion is real: a verified defect report (wrong meaning, collision found
in the wild) drops the row to `experimental` and the pack re-derives; the
history stays (append-only).

Status fan-out on change (one generator run): `languages.json` status field
→ REFERENCE.md badge → pack YAML `metadata` → pack manifest — all generated
from `canon_selections`/`locale_progress`, ending today's four-surface
fragmentation (v1 `languages.status`, `community_reviewed`, badges, v2
ladder).

## 8. Data organization: where everything lands

```text
libs/i18n/
  canon/<locale>.toml           ← THE reviewed truth (word + option_uid + expansion
                                   + status per concept); loaded → canon_selections;
                                   drift-tested (CORE-611 precedent). Q3: carries BOTH
                                   readable word and uid.
  reviews/incoming/<locale>/    ← bundle files as submitted (append-only archive;
                                   ses_<uid>.json; PR-reviewable)
  legesher_i18n/db/             ← workbench SQLite (schema v2 + doc-02 extensions)
  language-packs/python/<lang>/ ← generated artifacts (pack_export), never hand-edited
  style-guides/<locale>.yml     ← generated from style_ratifications + family overlays
```

Exports (all generated, versioned per release):

- **HF corpus dataset** (frozen shape per `hf-corpus-dataset.md`, private
  until the public flip): options + provenance + endorsements (opaque
  contributor ids pending Q1) + annotations + expansions + published
  commentary. The review corpus IS the research dataset.
- **Terminology corpus for `legesher translate`** (`terminology_export`
  view + published commentary): per concept × locale — canon word, ranked
  alternates, descriptors (transliteration/cognate/established/coined),
  expansion, word-formation commentary. Prompt assembly layers it as: pack
  (the words) + brief (the meaning) + style guide (the shape) +
  **terminology alternates (the vocabulary space)** — giving the model
  native ways to express concepts beyond the packed word, which is the
  entire second goal of collecting commentary.
- **Credits**: per-locale CONTRIBUTORS section + `.all-contributorsrc`
  entries for consented identities (doc 04 §8).

## 9. Signal loop (what keeps non-blocking honest)

Prior-art lesson (doc 10): non-blocking review converges only if use
generates signal. Three channels close the loop:

1. **Second-endorsement queue** — every single-endorser canon row is the
   next reviewer's first screen.
2. **In-product report** — the VS Code extension/LSP "suggest a better
   word" action files a Stage-0 issue prefilled with concept + locale
   (same importer lane).
3. **Override telemetry (later, opt-in)** — packs loaded with local
   overrides report the overridden keys (never the replacement words) —
   the "this term gets swapped out" signal that flags weak canon.

## 10. Threat model (abbreviated)

- **Brigading** → positive-only endorsements, rung weights, per-row
  `created_at`/`method`/rung distribution, session durations, flags
  instead of downvotes; anonymous weight 0. Sockpuppets: the private side
  can see what the corpus cannot — the same contact email behind multiple
  contributor ids is a first-class duplicate-account signal, checked at
  import (privately; never exported, never auto-punitive — it queues a
  human look).
- **PII** → contributor split (CORE-1502): bundles carry `source_key` only
  into the private identities table; corpus exports opaque ids (Q1 open);
  free-text PII scrubbed at stage 2; withdrawal deletes identity, keeps
  endorsement.
- **License contamination** → `import_sources.redistributable` gate;
  reference-only initiative terms never persist without independent human
  attestation (doc 05 §4).
- **Poisoned bundles** → canonical-JSON hashing, schema validation,
  append-only ingest, idempotent session uids, CI-visible verification
  report on every bundle PR.

## 11. Build order

1. `02-review-extensions.sql` reconciled into the CORE-1501 migration
   (before HF publish — session linkage cannot be retrofitted).
2. Canon TOML materializer + loader (`make canon-load`) — the committed
   schema's missing half; unblocks everything downstream.
3. Importer with Stage-0 issue parsing (immediate value: existing review
   issues become corpus rows).
4. Review-kit builder + model-panel/initiative fetchers (doc 05).
5. The static review app (doc 03) + bundle PR flow + CI check.
6. Promotion dashboard + status fan-out generator.
7. Stage 2 portal only on real traffic (CORE-1412 decision point).

## 12. Open decisions for Madison

Carried (and sharpened) from CORE-1501 §8 plus new ones this design adds:

1. **Q1 (identity publishing) — DECIDED 2026-07-21**: the corpus publishes
   opaque contributor ids (option a). Public credit is a separate,
   per-contributor choice — `credit_preference ∈ anonymous | handle |
   name` — and every submission captures a validated contact email on the
   private side (§4a). Remaining sub-decision: none; implementation rides
   the doc-02 identity deltas.
2. **Q4/rungs** — how `native_claimed → native_verified` actually happens:
   proposal in doc 04 §4 (vouching + video + institutional lanes).
3. **Q5 threshold** — `reviewed_eligible` encodes ≥2 native + zero flags;
   confirm or re-cut.
4. **Official-gate numbers** (§7 table) — 80/95/2 are proposals.
5. **Source-blind candidate display** (§3) — default-blind until ranking
   locks; confirm.
6. **Annotation vocabulary** (doc 02) — especially `transliteration` as
   neutral descriptor vs `option_flags` reserved for model-policy
   violations.
7. **Stage-1 submission lane for non-GitHub reviewers** — maintainer-
   proxied email/issue upload acceptable? (PII + DCO implications noted in
   doc 04 §6.)
8. **Style-profile ratification threshold** — majority of ≥3 native
   answers per field, or steward sign-off at small n?
9. **Email transport for the Stage-1 PR lane** (§4a) — start with the
   zero-infra `mailto:` match-by-session-uid flow, or stand up the single
   serverless intake endpoint from day one?
