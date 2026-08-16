# Pack maturity ladder

What each maturity stamp on a language pack means, what it does **not** mean,
and which parts are still open.

This is the shippable slice of CORE-1513. That spike asks a larger question —
how language-preservation and localization efforts measure quality, and what a
"variety of voices" threshold should be — and it is not answered here. What is
settled here is the part every public surface needs to agree on: the names of
the stages, what each one asserts, and an explicit statement of what has not
been decided. The survey and the promotion thresholds remain CORE-1513's.

## The three stages

| Stage | Asserts | Does not assert |
| --- | --- | --- |
| `experimental` | Machine-drafted, curated by maintainers, and passed through the mechanical gates: identifier validity (PEP 3131), cross-section collision audit, Unicode normalization, schema validation, and `verify_pack_regen` proving the shipped pack matches its source of truth. | That any native speaker has seen it. |
| `reviewed` | A native speaker of the language has reviewed the pack and signed off. | That the terminology has been screened for offensive or unfortunate readings. |
| `official` | Certified review plus term screening. | — |

The stamp lives at the **locale** level (`languages.json` → `status`, generated
from the database) and is mirrored per pack in `metadata.review_status`
(`schema_validator.py`, CORE-1453). `LanguagePackLoader.load(strict=True)`
warns on any pack that is not `official`.

As of the first published canon revision, **all 51 shipped locales are
`experimental`.** Nothing has been promoted, so no promotion criterion has yet
been exercised in production.

## What `experimental` is not

It is not "unchecked". The mechanical gates are real and they are the reason
the packs are shippable at all: a fabricated English keyword was caught and
removed by them (CORE-1317), ten corruption-class terms were replaced at the
database layer (CORE-1763), and nine packs carrying a syntactically invalid
`except*` rendering were corrected (CORE-1839).

It is also not "reviewed by the community". Every one of those gates is
mechanical or maintainer-driven. A gate can prove a term is a valid identifier
that collides with nothing; it cannot tell you whether a developer who speaks
the language would ever say it. That is the distinction the ladder exists to
carry, and it is why `experimental` is the honest stamp today.

## Open: what promotes a pack

Undecided, and deliberately not invented here:

1. **How many endorsements**, and from how varied a set of voices — distinct
   contributors, distinct recruitment channels (`endorsements.method` already
   records portal / survey / workshop / github / interview), regional spread.
2. **Granularity.** The per-term ladder (`canon_selections.status`, CORE-1466)
   and the per-locale stamp are different objects. A pack is ~184 terms; how
   many reviewed terms make a reviewed pack is unanswered.
3. **Who certifies `official`**, and what "term screening" must cover
   (CORE-401 is the screening work).

Until those land, any public surface should say that promotion criteria are
being defined rather than imply a threshold exists.

## A naming inconsistency to resolve

Four ladders exist in the tree today and they do not use the same words:

| Where | Values |
| --- | --- |
| pack `metadata.review_status` (CORE-1453) | `experimental` → `reviewed` → `official` |
| `locales.status` (v2 schema) and v1 `languages.status` | `experimental` → **`in_review`** → `official` |
| `canon_selections.status` (CORE-1466, per term) | `machine` → `experimental` → `reviewed` → `official` |
| `message_translations.status` | `machine` → `experimental` → `reviewed` → `official` |

The middle rung is `reviewed` in three of them and `in_review` in the one that
actually stamps the published artifact. This is latent rather than live — every
locale is `experimental`, so no surface renders the middle rung yet — but it
becomes visible the first time a language is promoted, and the dataset card,
the language-support page and the announcement copy all explain the ladder as
`experimental → reviewed → official`.

Resolving it is cheap now and awkward later. `reviewed` is the better name: it
describes a state the pack has reached, where `in_review` describes work in
flight, and three of the four ladders already use it.

The `machine` rung in the per-term ladders has no locale-level equivalent, which
is correct — a locale whose terms are all machine-picked is `experimental` at
the locale level, because a maintainer has curated and gated the pack as a
whole even where individual terms have not been touched.
