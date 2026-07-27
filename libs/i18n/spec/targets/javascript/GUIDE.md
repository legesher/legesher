<!-- markdownlint-disable MD041 -->
<!--
JavaScript target guide — the prose the machine rules can't carry.
CORE-1608 (the JS-critical slice of CORE-1503). Rendered verbatim (minus
these leading comments) into the PromptBuilder's "Target Guide" section for
every target=javascript generation run, composing with the
per-natural-language style guides. Keep it model-facing prose; facts a gate
can check belong in profile.json. MD041 is disabled because the
H1-equivalent heading is supplied at render time by the PromptBuilder's
"## Target Guide" wrapper.
-->

### Vocabulary shape

- Members are property names in code (`.log`, `.length`): they appear after
  a dot, bounded by their receiver. Translate them as short labels, reading
  each in noun position (`length` — a property that IS something) or verb
  position (`repeat` — a method that DOES something) according to what the
  member does; natural translations differ between the two.
- The value literals `true` / `false` / `null` belong to the keywords
  partition; translate them as single value-words, never phrases.
- The surface is a curated teaching subset ("just-enough-JavaScript"), not
  the full language. Only translate the terms in the requested list.

### Naming and symbols

- JavaScript convention is camelCase for multi-word identifiers and
  PascalCase for constructors. Preserve the casing family of the original
  term where the target script has case; caseless scripts join words with
  underscores instead (the natural-language style guide's case-substitute
  rule wins).
- Never translate, remove, or add the symbols `$` and `_` inside given
  identifiers; they are identifier characters, not words.
- `of`, `async`, `get`, and `set` are contextual keywords — reserved only in
  specific positions. Translate each as an ordinary short word; do not avoid
  a translation because it collides with them elsewhere.

### Arabic-script note (trial scope)

- Arabic terms ship bare (unvocalized) — no harakat — matching what learners
  type on Arabic keyboards. Add a vowel mark only when a term is genuinely
  ambiguous without it.
- Compound terms join with underscores (e.g. `حول_لصحيح`), never with spaces
  or tatweel.
