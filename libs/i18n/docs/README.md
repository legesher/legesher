# Translation Documentation

> **Audience:** Maintainers, who run releases, regenerate packs and write to the translations database.

This directory contains the foundation documents for creating high-quality Python translations. The entries
below are grouped by who they are for.

## For maintainers

### [schema-v2-reference.md](./schema-v2-reference.md)

Every table, column, index, trigger and view in the translations schema v2
(`schema_v2.sql`), with what each is for. Generated: the structure is parsed
from the SQL and the descriptions come from `schema_v2.descriptions.yml`, so
edit those and run `make generate-schema-reference`. `make check-generated`
fails when the page is stale or when the SQL and the descriptions disagree.
Covers v2 only; the v1 pack database (`schema.py`) is not described there.

**Use this for:** Looking up what a v2 table or column means before querying or changing it (CORE-2232)

### [corpus-publish-runbook.md](./corpus-publish-runbook.md)

The operator sequence from the working database to the published corpus dataset:
salt escrow, the publish-grade build, the dry export, and the double-keyed push.

**Use this for:** Publishing or re-pushing the language corpus (CORE-1312)

### [intake-moderation-runbook.md](./intake-moderation-runbook.md)

The interim screening ritual for community submissions: triage the intake queue,
import, screen each new rendering by hand, clear or hold with a recorded
decision, reply on the issue, push to the durable data home. Quarantine is the
default until a person clears it.

**Use this for:** Walking the community intake queue, weekly at minimum (CORE-1828)

### [contributor-withdrawal-runbook.md](./contributor-withdrawal-runbook.md)

How a contributor's request to be forgotten is honoured: confirming the request
is theirs, redacting the identity while keeping the tombstone, the three
verification queries, and the rule a future review-bundle importer must follow
so a rebuild cannot undo the erasure. No published dataset changes.

**Use this for:** Responding to a privacy or withdrawal request (CORE-1780)

### [context-template-tier1.md](./context-template-tier1.md) / [context-template-tier2.md](./context-template-tier2.md)

Templates for creating comprehensive context documents for each Python term:

- Etymology & history
- Multi-level explanations (5yo → expert)
- Linguistic recommendations
- Syntax roles & examples
- Translation guidance for non-English speakers

**Use this for:** Creating context documents that AI models and human translators use

## For contributors

> **Audience:** Contributors, who change the code, tests and docs, or offer and review the words in a language pack.

### [pack-messages.md](./pack-messages.md)

The `messages` section of a pack: localized traceback and error-message
templates, what a pack load checks, how the section merges across Python
versions, and which `legesher-i18n` releases can read it.

**Use this for:** Reading or changing how packs carry error messages (CORE-2630)

### [linguistic-standards.md](./linguistic-standards.md)

Establishes consistent linguistic conventions for translating Python terms:

- Word type classification (verb, noun, adjective, etc.)
- Form recommendations by language family
- Examples from existing language packs
- Translation checklist

**Use this for:** Understanding what form translations should take

## Translation Workflow

1. **Create Context** - Use template to create deep context for each Python term
2. **Generate Translation** - Feed context to AI model (Claude/GPT-4o) for translation
3. **Review** - Native speakers review AI translations
4. **Integrate** - Add approved translations to language packs

## Current Status

- ✅ Linguistic standards defined
- ✅ Deep context template created
- ⏳ Context generation in progress (105 terms total)

## Related Issues

- CORE-354 — Create 4 Initial Language Packs
- CORE-391 — Translation Migration Epic
- CORE-392 — Linguistic Standards
- CORE-393 — Deep Context Documents

---

**Last Updated:** 2025-10-28
**Maintained by:** Legesher Team
