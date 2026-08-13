# Legesher Roadmap

**Vision:** you should be able to write and read code in your heart language.

Programming today assumes English. Legesher removes that assumption: the code you write in your
language and the canonical English form stay in lossless correspondence, so you work in your
language and collaborate with anyone. The mission horizon is every language people actually speak,
7,000+ of them; the roadmap below is the honest path from where we are.

**Current version:** v0.22.0 (Foundation Suite)

---

## Where We Are Today

Shipped and working now:

- **Two translation engines.** A token-based translator and a tree-sitter, grammar-aware
  translator, with bidirectional (native ↔ English) translation and source mapping.
- **51 Python language packs**, covering Python 3.10 through 3.14. All 51 are available today,
  with community validation in progress.
- **A concept-centric translations database.** Every translation offered for every term is
  collected as an option with provenance (who or what proposed it, how, when); packs are exports
  of the current best picks. Disagreement is data here, not conflict.
- **Safety gates at generation.** Identifier validity, Unicode normalization stability, and
  collision checks (two concepts can never share one translated word in a language) run before a
  pack ships.
- **The developer toolchain.** CLI suite (init, translate, run, metadata), git integration with
  clean/smudge filters so repositories store canonical English, a language server (hover,
  completion, diagnostics, semantic tokens), and a VS Code extension.
- **Per-language style profiles.** How compounds join, what replaces uppercase in caseless
  scripts, digit policy, docstring register: 51 style guides, always suggestions, never laws.

## How This Roadmap Is Ordered

Not by quarters. Each stage below unlocks the next, and dates would pretend a certainty we don't
have. The order is the commitment; a stage ships when its gate criteria hold.

### Stage 1 | Open the corpus

The translations database becomes a public dataset that communities can build on.

- Publish the terminology corpus (concepts, options, endorsements) as a public dataset
- Land the review-intake data model first, so every future endorsement carries its review context
  from day one
- Corpus governance: contributors appear as opaque ids, with a per-contributor choice of public
  credit (anonymous, handle, or name); contact details never enter the dataset

### Stage 2 | Open the doors

The repositories go public and contribution becomes self-serve.

- Contributor onboarding set: CONTRIBUTING, Community Guidelines, AI-assisted-work policy
- Good-first-issue pipeline seeded across engine, docs, and localization work
- Format-and-changelog bot for contributor PRs, with CI hardening designed in before the first bot
  runs (untrusted code never executes with privileges)
- Per-language term screening at PR time, feeding native review

### Stage 3 | Native review at scale

Review stops being a maintainer bottleneck and becomes a community practice.

- A reviewer surface a linguist can use without git: your word first, then the candidates;
  endorse, rank, tag, comment; no downvotes; RTL as a first-class citizen
- Public promotion criteria: packs climb from experimental to reviewed to official through native
  endorsements, visible as queries anyone can run
- Language ambassadors: per-language leads who own intake and pack-level decisions, with a ladder
  toward certified-reviewer recognition

### Stage 4 | 103 languages

Coverage grows from 51 packs to 103, prioritized by the languages major multilingual models serve
well and by what our community asks for.

- Expansion generation runs against the published corpus, so community options and native review
  apply from each pack's first day
- Version-tiered compatibility packs for scripts whose identifiers need newer Unicode support
- Native-digit handling where writing systems use their own numerals

### Stage 5 | Beyond Python

The same shared map, more runtimes.

- JavaScript/TypeScript engine and packs, developed as a sibling engine against the same
  concept-keyed database, so a community's review of a concept ships everywhere that concept
  exists
- Editor support built engine-neutral (one integration serving multiple runtimes), including RTL
  rendering
- Library API packs: reversible, per-library glossaries so the libraries you import can speak your
  language too

### Stage 6 | The platform

Legesher meets people where they already work.

- A hosted translation API for tools and platforms that want translation as a service
- An MCP server so AI assistants can work with you in your language and your pack's terms
- A hosted review portal, lowering the barrier for reviewers beyond GitHub entirely
- Localized documentation, generated and reviewed through the same pipeline as the packs

## What Unlocks What

| This | Unlocks |
| --- | --- |
| Review-intake data model | Corpus publish (review context can't be retrofitted later) |
| Corpus publish | Community options and endorsements at scale |
| Contributor docs + CI hardening | Repos public, first community PRs |
| First community PRs | The bots get built (they exist to serve real contributor volume) |
| Reviewer surface | Packs reaching reviewed and official status |
| Review ladder | Ambassador program, certified reviewers, the 103 expansion landing reviewed |
| Python engine patterns | JavaScript/TypeScript engine |
| Corpus + engines | Hosted API, MCP server, review portal |

## How to Help

Every stage above has community-shaped work in it, and most of it does not require Python
expertise. Start with [CONTRIBUTING.md](CONTRIBUTING.md) and its Ways to Contribute map: offer a
better word for your language, review as a native speaker, pick up a `good first issue`, localize
a doc, or answer a Context Call about how your language is really written.

## Version History

| Version | Date | What it proved |
| --- | --- | --- |
| v0.1.0 | 2025-11-07 | The concept: token-based translation engine, first two packs (Spanish, Arabic), CLI, git clean/smudge integration, LSP foundation |
| v0.22.0 | current | The system: two engines, 51 packs, concept-centric database with options and provenance, full toolchain, safety gates |

The full record lives in the [changelogs](CHANGELOG.md).

## Questions or Feedback?

- **Issues:** [github.com/legesher/legesher/issues](https://github.com/legesher/legesher/issues)
- **Discussions:** [github.com/legesher/legesher/discussions](https://github.com/legesher/legesher/discussions)
- **Email:** <hello@legesher.com>

---

**Last updated:** 2026-07-28

**Maintained by:** Madison Edgar and the Legesher community

**License:** see [LICENSING.md](LICENSING.md)
