# Translation Documentation

> **Maintainer notes — not newcomer documentation.** Written for someone already
> working in this code: it assumes repo context, uses internal vocabulary, and
> may cite work-tracker ids (`CORE-####`) an outside reader cannot resolve.
> Public on purpose, but not part of the documentation site and not localized —
> newcomer-facing documentation lives at [docs.legesher.io](https://docs.legesher.io).
> <!-- disposition: MAINTAINER (CORE-1724 audit, 2026-08-11) -->

This directory contains the foundation documents for creating high-quality Python translations.

## Contents

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

### [database-schema.md](./database-schema.md)

Reference for the translations database schema (v1 operational layout).

### [linguistic-standards.md](./linguistic-standards.md)

Establishes consistent linguistic conventions for translating Python terms:

- Word type classification (verb, noun, adjective, etc.)
- Form recommendations by language family
- Examples from existing language packs
- Translation checklist

**Use this for:** Understanding what form translations should take

### [context-template-tier1.md](./context-template-tier1.md) / [context-template-tier2.md](./context-template-tier2.md)

Templates for creating comprehensive context documents for each Python term:

- Etymology & history
- Multi-level explanations (5yo → expert)
- Linguistic recommendations
- Syntax roles & examples
- Translation guidance for non-English speakers

**Use this for:** Creating context documents that AI models and human translators use

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
