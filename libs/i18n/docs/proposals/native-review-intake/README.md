# Native-review intake — proposal

Architecture, data model, reviewer UI, and contributor guidelines for taking
language packs from **experimental** to **official** through structured native
review. Companion to the multi-pl-reserved-words analysis (maintained
separately — see CORE-1531) and built
directly on the committed schema v2
(`libs/i18n/legesher_i18n/db/schema_v2.sql`, CORE-1501) — this proposal adds
the intake layer that schema left as seams (`endorsements.method='portal'`,
the `review_queue` view) and does not re-design anything the schema already
decided.

| file | contents |
| --- | --- |
| `01-review-intake-architecture.md` | goals, decided constraints, three-stage intake topology, review kit + bundle contract, verification pipeline, aggregation + promotion queries, data organization and exports |
| `02-review-extensions.sql` | additive DDL: sessions, rankings, annotations, expansions, commentary, style ratifications, import-source registry, promotion/terminology views |
| `03-reviewer-ui-spec.md` | the reviewer-facing app: every view, the two-phase (blind → candidates) flow, phrase and style flows, onboarding mindset copy, RTL/a11y requirements |
| `04-contributor-guidelines.md` | draft public guidelines: the perspective shift, three contribution tracks, reviewer ladder, quality gates, recognition, experimental → official criteria |
| `05-candidate-sources.md` | where candidates come from: the model panel, prior-art initiatives (Hedy, UniversalPython, UniPy, Scratch), license classes, import mechanics |
| `scripts/probe_review_extensions.py` | proposal-side smoke probe of the folded-in DDL; superseded by `libs/i18n/tests/test_review_extensions.py`, kept as the design-record artifact |

Headline decisions this proposal takes (rationale in doc 01):

1. **Three intake stages, one contract.** Stage 0 = today's GitHub issue form,
   kept. Stage 1 = a static, client-only review app producing a signed
   **review bundle** file submitted by PR. Stage 2 = the hosted portal
   (CORE-1412 graduation), same bundle semantics server-side. One importer
   ingests all three.
2. **Review = endorse / pass / flag, never downvote** — inherited from schema
   v2's positive-only endorsement model. The UI's "disapprove" maps to *not
   endorsing* plus an optional structured flag; ranking is a separate,
   session-scoped signal.
3. **Blind-first elicitation.** The reviewer records their own term before any
   candidate is revealed; that ordering is stored (`elicited='blind'`) and is
   the highest-value signal the corpus collects.
4. **Transliteration is a descriptor, not a sin.** Model-generated candidates
   may never fall back to transliteration (2026-07-05 policy), but a
   community-offered transliteration is a legal option carrying a transparent
   annotation; its popularity per locale is measured, surfaced, and feeds
   `terminology_policy`.
5. **Creativity is protected structurally.** No gate compares a human term
   against model output. Only mechanical checks (identifier validity, NFKC,
   collision, conduct) block; novel coinages route to *more human review*,
   never to rejection.

Status: the additive DDL from doc 02 is **folded into the committed schema**
(`libs/i18n/legesher_i18n/db/schema_v2.sql`) alongside this proposal; doc 02
remains as the annotated rationale. Nothing here modifies the live database or
shipped packs. Timing note: schema v2 is the gate on the HF corpus publish
(CORE-1312); the review-extension tables ride that migration **before** the
first publish so session/ranking evidence never needs a post-freeze migration.
