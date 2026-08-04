---
name: legesher-localized-code
description: Use when writing, editing, or reviewing code in a repository with a Legesher language policy (an AGENTS.md language declaration, a .legesher/ directory, or Legesher MCP tools available) — the stable playbook for producing fully localized code that round-trips deterministically.
---

# Writing localized code with Legesher

## The mental model

Legesher lets people program Python in their own natural language. Every
file has two renderings of the **same program**:

- **Canonical form** — English keywords. What the interpreter, the
  toolchain, and upstream collaborators consume.
- **Native form** — the declared language's keywords (from a Legesher
  language pack), with identifiers, comments, and docstrings in that
  language too.

The language pack is a reviewed dictionary, not a model: keyword and
builtin translation is **deterministic** and reversible. Translation
between two non-English languages pivots through English — results say
`pivoted: true` when that happened.

The division of labor: **you** (the model) do the fuzzy layer —
identifiers, comments, docstrings, explanations. **The Legesher tools** do
the deterministic layer — keywords, builtins, exceptions, validation,
round-trip. Never swap those roles: hand-translating a keyword or guessing
a builtin's rendering is how localized code silently breaks.

## Which tool, when

| You need | Call |
| --- | --- |
| Native rendering of canonical code | `translate_to_native` |
| Canonical form of native code (to run, diff, or ship upstream) | `translate_to_source` |
| Engine facts to explain code or an error in the user's language | `explain_in_language` — it returns construct mappings + a static validation result; you write the prose |
| How specific terms render in a language | `lookup_keyword_mapping` |
| The full dictionary for a language | resource `legesher://languages/{lang}/terms` |
| Coverage picture of an existing repo | `map_existing_codebase` |

Everything is static and local: code is parsed, never executed, and the
stdio server makes no network calls.

## The writing workflow

1. **Find the declaration.** The repository's `AGENTS.md` language policy
   names the declared language; a `.legesher/` directory or pack config
   confirms it. No declaration → ask, don't assume.
2. **Write natively from the start** — pack keywords, in-language
   identifiers, comments, docstrings. Look terms up rather than guessing
   (`lookup_keyword_mapping` for keywords/builtins; the project glossary
   for identifiers).
3. **Round-trip before you finish.** `translate_to_source` on the file,
   then `translate_to_native` on the result. Byte-identical output is the
   guarantee holding; anything else means stop and report which construct
   broke it.
4. **Validate.** `explain_in_language` includes the static validation
   verdict for the code you touched (compile-level, never executed).

## Naming discipline (the part models get wrong)

- **One concept, one term.** A concept translated two ways is a defect.
  Check the project glossary (in `AGENTS.md`) and
  `.legesher/identifier_map.json` (when present) before naming; record
  every NEW identifier translation in the glossary in the same change.
- **Pack terms are reserved.** Never use a word the pack claims for a
  keyword, builtin, or exception as an identifier — shadowing is silent
  and valid-looking. When in doubt, `lookup_keyword_mapping` the candidate.
- **Never "correct" localized names to English.** Localized identifiers
  are the repository working as intended.

## Cross-language collaboration

- The canonical form is the interchange format: upstream PRs, published
  packages, and cross-team diffs travel as canonical unless the receiving
  repository declares otherwise.
- Two contributors in two languages are editing the same program — the
  deterministic layer keeps their renderings equivalent; the glossary
  keeps each language's identifier vocabulary internally consistent.

## Long-session discipline

Rules files and prompts get evicted from context as sessions grow — that
is exactly when code drifts back to English. The policy file is the hint;
the deterministic tools are the guarantee. If you notice English keywords
or identifiers creeping into your output (or cannot recall the declared
language), stop, re-read `AGENTS.md`, and round-trip what you just wrote
before continuing.

## When something doesn't map

A missing pack term, an untranslatable construct, a round-trip mismatch:
flag it explicitly in your response and keep the affected code canonical
rather than improvising a translation. That is a pack-gap signal the
Legesher project collects — not a rule you may quietly relax.
