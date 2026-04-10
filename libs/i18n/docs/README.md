# Translation Documentation

This directory contains the foundation documents for creating high-quality Python translations.

## Contents

### [linguistic-standards.md](./linguistic-standards.md)

Establishes consistent linguistic conventions for translating Python terms:

- Word type classification (verb, noun, adjective, etc.)
- Form recommendations by language family
- Examples from existing language packs
- Translation checklist

**Use this for:** Understanding what form translations should take

### [deep-context-template.md](./deep-context-template.md)

Template for creating comprehensive context documents for each Python term:

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
