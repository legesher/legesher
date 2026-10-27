---
name: legesher-localized-code
description: Use when writing, editing, or reviewing code in a repository with a Legesher language policy (an AGENTS.md language declaration, a .legesher/ directory, or Legesher MCP tools available) — the stable playbook for producing fully localized code that round-trips deterministically.
---

# Writing localized code with Legesher

## The mental model

Legesher lets people program Python in their own natural language. Every
file has two renderings of the **same program**:

- **Run form** — English keywords, which CPython requires. What the
  interpreter consumes; produced on demand, never the stored original.
- **Native form** — the declared language's keywords (from a Legesher
  language pack), with identifiers, comments, and docstrings in that
  language too. This is the original: a file's canonical form is
  whatever its author wrote, and it is what git stores.

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
| Native rendering of run-form code | `translate_to_native` |
| Run form of native code (to run, or to diff against an English project) | `translate_to_source` |
| Proof that a file round-trips | either translate tool with `verify_round_trip: true` |
| Engine facts to explain code or an error in the user's language | `explain_in_language` — it returns construct mappings + a static validation result; you write the prose |
| How specific terms render in a language | `lookup_keyword_mapping` |
| Whether the identifier names you invented are safe to use | `validate_identifier_translations` — before you write them, not after |
| The full dictionary for a language | resource `legesher://languages/{lang}/terms` |
| Coverage picture of an existing repo | `map_existing_codebase` |

Everything is static and local: code is parsed, never executed, and no
tool call makes a network request.

## The writing workflow

1. **Find the declaration.** The repository's `AGENTS.md` language policy
   names the declared language; a `.legesher/` directory or pack config
   confirms it. No declaration → ask, don't assume.
2. **Write natively from the start** — pack keywords, in-language
   identifiers, comments, docstrings. Look terms up rather than guessing
   (`lookup_keyword_mapping` for keywords/builtins; the project glossary
   for identifiers).
3. **Round-trip before you finish.** Call `translate_to_source` on the file
   with `verify_round_trip: true`. The engine translates back, compares
   byte-for-byte, and checks the run form compiles; you do not.
   Quote the returned `verdict_line` and do not restate the verdict in your
   own words — the line states what was verified and what was not.
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
- **Don't check by eye — call the tool.** Pass every new name to
  `validate_identifier_translations` along with the existing glossary. It
  catches five failures at once: a malformed identifier, unsafe text
  (invisibles, bidi controls), a reserved pack term, *drift* (this concept
  already has a different term) and *collision* (this term already belongs
  to another concept). Case variants and decomposed forms count as the
  same term, so `DEFINIR` collides with `definir`. Batch the whole file's
  new names into one call. What comes back in `accepted` is what you write
  into the glossary — already normalized, and the tool does not save it for
  you, because the server never writes. Anything with a conflict gets
  renamed and re-checked, never recorded.
- **Never "correct" localized names to English.** Localized identifiers
  are the repository working as intended.

## Cross-language collaboration

- A file travels in the language it was written in; its canonical form is
  the author's own. Translate to the run form only when the receiving
  repository declares English, as an upstream English project does.
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

A round-trip failure names the `layer` that broke it, and the layer decides
the move:

- **`keywords`, `builtins`, `exceptions`, `implicit_params`** — the
  deterministic layer failed: a pack or engine defect. Report it with the
  verdict line and keep the affected code in Python's own keywords.
- **`collision`** — an identifier is spelled like a pack rendering
  (a known class: CORE-1840). Rename the identifier; the pack is correct.
- **`identifiers`** — expected today; the run form retains native
  identifiers, which are the original names. Disclosed residue, not a
  failure. Carry on.
- **`comments`, `strings`** — your own layer drifted. Fix it and re-verify.

A missing pack term or an untranslatable construct: flag it explicitly and
keep the affected code in Python's own keywords rather than improvising a
translation. That is a pack-gap signal the Legesher project collects, not a
rule you may quietly relax.
