# Pack Vocabulary Prompt (CORE-1396)

Specification for filling the two vocabulary sections of a language pack —
`symbols` and `variable_conventions` — for every supported language.
Companion to `reserved_words_prompt.md`, and deliberately shaped the same
way: conceptual framing first, hard invariants second, template third,
provenance last.

`scripts/translate/generate_vocabulary.py` renders the template below; this
file is the specification the script implements, and the place to change
the framing.

## Conceptual framing

The house framing is **you are a linguist, not a translator**, and it
matters more here than anywhere else in the pipeline, because both sections
have an answer that is *linguistically correct and useless*.

### Symbols

The question is **"what do speakers of this language CALL this mark?"** —
not "what is the English name of this mark in this language's words."

Those come apart constantly:

- English calls `#` a *hash sign* (and Americans often *pound sign*).
  Speakers of many languages call it by a word meaning *grid*, *lattice*,
  or *sharp* (the musical accidental). A translator produces a calque of
  "hash". A linguist reports what people say.
- `_` is *underscore* in English — a typewriter word, from the underlining
  key. Spanish says *guion bajo* ("low dash"), French *tiret bas*, German
  *Unterstrich*. Each is a native compound, none is a loan of "underscore".
- `@` has famously local names across languages, many of them animals
  (*little snail*, *monkey tail*, *elephant's trunk*). A translator would
  never produce those; they are exactly what a linguist reports.

Where a language genuinely uses the English loanword, **say the loanword**.
That is a real answer, not a failure — programmers borrow, and a fabricated
"native-sounding" coinage that nobody uses is worse than an honest loan.

Three of the entries have no glyph at all — `indentation`, `newline`,
`space`. These are named constantly in error messages and in teaching
("check your indentation"), which is why they are in the inventory.

### Variable conventions

The question is **"what short name does a programmer who thinks in this
language actually type?"** — an ethnographic question about habit, not a
translation task.

The single most important thing to understand: **`i` is frequently the
right answer, and answering `i` is not a failure.** The loop counter `i`
descends from mathematical index notation (and from FORTRAN's implicit
integer typing), not from the English word "index". Programmers writing
Japanese, Arabic and Russian code overwhelmingly write `i`. Reporting that
is the correct linguistic finding.

What we are looking for is the roles where a language *does* diverge —
where the local habit is a different letter, an abbreviation of a native
word, or a different convention entirely. A response that renames all
fifteen roles into native abbreviations is a warning sign: it is what a
translator produces, and it describes no real codebase.

Scripts matter here in a way they do not for symbols. A recommended name is
an identifier a developer types, and:

- Non-Latin scripts *may* be used — Python identifiers are Unicode (PEP
  3131) — but only if that is genuinely what programmers in that language
  write. For most languages it is not.
- The name must parse on CPython 3.10, the oldest interpreter Legesher
  packs support — see the "parses on CPython 3.10" invariant below.

## Hard invariants

Every value must pass all of these; `generate_vocabulary.py` enforces them
before anything is written, and `TranslationDatabase.set_selected_vocabulary`
enforces them again at the write boundary.

**Symbols** (`symbols`):

- **A name, not a definition.** "guion bajo", not "the mark used to join
  words inside an identifier". Cap: 60 code points.
- **Complete.** Every slug in the inventory gets a value. A vocabulary
  section ships whole or not at all — a half-filled one puts English
  fallbacks inside localized teaching text with nothing to signal it.
- **No control or format characters.** Ordinary spaces are fine and
  expected (most names are multi-word); bidi controls, the BOM and the
  like are not.

**Variable conventions** (`variable_conventions`):

- **A valid Python identifier** per PEP 3131 — this is a name someone will
  type into real code.
- **Parses on CPython 3.10.** No character that only became
  identifier-legal in CPython 3.13 (Unicode 15.1 XID). Unlike a pack
  translation, a recommended name has no version-overlay file to be tiered
  into, so the constraint is absolute rather than managed.
- **Not a Python keyword.** `for`, `class`, `in` are SyntaxErrors as
  variable names. (`_` is fine and is the expected answer for
  `throwaway`.)
- **Not a surface this language's pack already translates a term to** —
  the engine rewrites that token, so a variable named it would not survive
  translation.
- **Short.** These are the names for which brevity is the point; a
  descriptive name is the *opposite* of what the section records.

## Prompt template

Rendered per language by `generate_vocabulary.py`. `{…}` are substituted;
the inventory block is generated from
`legesher_i18n/vocabulary_definitions.py` so the prompt can never disagree
with the schema.

````text
You are a linguist documenting how programmers who speak {language_name}
({native_name}) talk about Python code. You are not translating: you are
reporting what speakers of this language actually say and write.

Two questions, answered for {language_name}.

## Question 1 — what these symbols are CALLED

For each symbol below, give the name speakers of {language_name} use for
that mark when reading code or prose aloud.

Report what people SAY. Do not calque the English name. English calls '#'
a "hash sign"; many languages call it a grid, a lattice, or the musical
sharp. English calls '_' an "underscore" (a typewriter word); Spanish says
"guion bajo", German "Unterstrich".

If {language_name} genuinely uses the English loanword for a symbol, give
the loanword. An honest loan is a real answer; an invented native-sounding
coinage that nobody uses is not.

Give a NAME, not a definition — a short noun phrase, at most 60
characters. The 'role' column is context for you, never the answer.

{symbol_inventory}

## Question 2 — the short variable names programmers actually type

For each ROLE below, give the short variable name a programmer writing
{language_name} would habitually type.

'i' is very often the correct answer and you should say so when it is: the
loop counter 'i' comes from mathematical index notation, not from the
English word "index", and programmers in most languages use it. We are
looking for the roles where {language_name} genuinely DIVERGES. Renaming
all fifteen roles into native abbreviations would describe no real
codebase.

Each value must be a valid Python identifier, must not be a Python
keyword, and must parse on CPython 3.10 (avoid characters that only became
identifier-legal in CPython 3.13). Keep them short — brevity is the whole
point of these names.

{convention_inventory}

## Script and formatting profile for {language_name}

{style_profile}

## Output format

Return ONE JSON object and nothing else:

{
  "symbols": {"<slug>": "<name in {language_name}>", ...},
  "variable_conventions": {"<slug>": "<identifier>", ...},
  "notes": "<2-3 sentences: which answers you were least sure of, and any
            role where the language genuinely diverges from 'i'/'x'/'n'>"
}

Every slug listed above must appear exactly once in its section. Do not add
slugs that were not listed.
````

## What the script does with the response

1. Validates every value against the invariants above; a language with any
   invalid value is reported and **not** written (partial writes are the
   failure mode the all-or-nothing rule exists to prevent).
2. Writes each value to `vocabulary_translations` (source `claude_agent`,
   with the model's `notes` as the rationale) — the dirty-tolerant
   candidate pool.
3. Selects each value into `selected_vocabulary`, which re-runs the publish
   gate at the write boundary.

Packs are NOT written by the generation script. Regeneration is a separate,
deliberate step (`scripts/export_packs.py`), because pack writes are
authoritative.

## Review status

Values generated this way enter at the **experimental** tier, which is
where every shipped language pack sits today and where model generation is the
norm. Native review rides the standing review queue; it is not a
precondition for the values existing, and it is not part of CORE-1396.

The `notes` field is the thing to read first at review time: it is where a
model records the answers it was least sure of, which is a better triage
signal than confidence scores.

## Provenance

- v1 (CORE-1396): linguist-framed, one call per language covering both
  sections together. Batching the two is deliberate — they share the
  script/formatting profile, and batching keeps the run at one call per
  language rather than one per entry.
