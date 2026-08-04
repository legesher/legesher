<!--
  Legesher language-policy template (CORE-1422).

  Copy this file into your repository root as `AGENTS.md`, replace
  {{DECLARED_LANGUAGE}} with your language name + ISO code (e.g.
  "Arabic (`ar`)"), and delete this comment. Codex, Cursor, Claude Code,
  Antigravity, and Windsurf all read `AGENTS.md` — one file, every agent.
  If your repository already has an `AGENTS.md`, paste everything below
  the comment into it as a section.

  Positioning: this file is the *declaration*; the Legesher tools are the
  *guarantee*. Rules files get evicted from context in long sessions —
  when that happens, the deterministic tools (and the round-trip rule)
  still hold the line.
-->

# Language policy (Legesher)

This repository is written in **{{DECLARED_LANGUAGE}}**.
Canonical form: Python (English keywords). The Legesher language pack and
tools translate between the two; both forms are the same program.

## Rules for agents

1. **Write all new and modified code in {{DECLARED_LANGUAGE}}** — keywords
   via the Legesher language pack, identifiers, comments, and docstrings in
   {{DECLARED_LANGUAGE}}. This applies to every edit, not just new files.
2. **Never drift back to English mid-session.** If you are unsure of a
   term, look it up (`lookup_keyword_mapping`, the pack's term dictionary
   via `legesher://languages/{lang}/terms`, or the project glossary below).
   Do not guess and do not silently fall back to English.
3. **Keywords are never hand-translated.** Run changed code through the
   deterministic Legesher tools (`translate_to_native` /
   `translate_to_source`); the language pack is the source of truth for
   reserved words, builtins, and exceptions. Use `explain_in_language` for
   the engine's construct-by-construct facts and its static validation
   result.
4. **Identifiers: one concept, one term.** Before naming anything, check
   the project glossary (and `.legesher/identifier_map.json` if this
   repository has one) and reuse the existing translation. When you
   introduce a new identifier translation, add it to the glossary in the
   same change — never invent a synonym for a concept that already has a
   term, and never reuse a word the language pack already claims for a
   keyword or builtin.
5. **Do not "fix" non-English identifiers to English.** Localized code is
   this repository working as intended, not a defect.
6. **Comments and docstrings** follow the declared language. User-facing
   strings follow the application's own i18n system, not this policy.
7. **If a rule cannot be satisfied** (a missing pack term, an
   untranslatable construct), flag it explicitly rather than improvising —
   that is a pack-gap signal the Legesher project wants to hear about.
8. **Round-trip guarantee:** any file you touch must survive
   native → canonical → native byte-identically through the deterministic
   tools (`translate_to_source`, then `translate_to_native`). If it does
   not, stop and report rather than committing.

## Project glossary

One concept, one term. Add a row whenever you introduce a new identifier
translation; agents and reviewers treat this table as binding.

| Concept (canonical / English) | {{DECLARED_LANGUAGE}} term | Notes |
| --- | --- | --- |
| <!-- e.g. `user_account` --> | <!-- the term used in code --> | |
