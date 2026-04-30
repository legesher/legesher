# Reserved Words Translation Prompt (CORE-710)

Specification for translating Python's `self` and `cls` conventions into
the 51 supported language packs. Used during the CORE-710 generation pass
and intended as the canonical reference for any future re-generation or
expansion of the reserved-word category.

## Conceptual framing

`self` is a **reflexive pronoun** — the entity referring to its own being.
Grammatically distinct from:

| Type          | Example (English)                   | What it points to                         |
| ------------- | ----------------------------------- | ----------------------------------------- |
| First-person  | "I", "me"                           | The speaker (subject's POV)               |
| Demonstrative | "this", "that"                      | Something nearby being pointed at         |
| **Reflexive** | **"oneself", "itself", "the self"** | **The entity referring to its own being** |

When a method runs in Python, the object is passed in and called `self`
because the object is referring to ITSELF — not "this thing here"
(demonstrative) and not "I" (first-person). The convention came from
Smalltalk's notion of "the receiver of the message" (1970s) and Modula-3.

Python deliberately chose `self` over `this` because reflexive better
captures the relationship: the object isn't "this thing over here", it's
"the entity itself, viewed from inside its own method."

`cls` is the **same reflexive concept applied to the class itself** rather
than an instance. Inside a `@classmethod`, the class is referring to
itself — not "a class" abstractly (which would be the keyword `class`),
but THIS specific class referring to its own being.

## Reference reflexive equivalents

These are well-resourced languages where the natural reflexive pronoun is
unambiguous and serves as a calibration anchor for the LLM:

- **French**: `soi` (oneself), NOT `ceci` (this) or `je` (I)
- **German**: `selbst` (self-emphatic) or `sich` (reflexive marker), NOT
  `dieses` (this) or `ich` (I)
- **Spanish**: `propio` (one's own) or `mismo` (self-emphatic)
- **Russian**: `себя` (oneself, reflexive accusative)
- **Hindi**: `स्वयं` (svayam, oneself)
- **Japanese**: `自身` (self-body) or `自己` (oneself)
- **Arabic**: `نفس` (nafs, the genuine reflexive — note `ذاتي` is a
  first-person possessive flavor, less correct)

## Five hard invariants

Every translation must pass all five:

1. **One-for-one** — exactly one translation value per term in the pack.
   Never a set or list of options.
2. **Single word** — `len(value.split()) == 1`. No whitespace.
   (Compounds joined with `_` are OK.)
3. **Valid Python identifier** — `value.isidentifier()` per Python 3
   Unicode-aware identifier rules (PEP 3131).
4. **No collision** — must not match any existing keyword, builtin, or
   exception translation in that language pack.
5. **Non-trivial** — must differ from the English source word (with one
   exception: the `en` pack uses identity mapping `self → self`, `cls → cls`
   since English is the source language).

## Prompt template (v3 — agent reasoning version)

This is the prompt sent to each translation agent. The agent reads the
target language's pack file directly to inspect existing translations and
avoid collisions, then picks a candidate with explicit reasoning.

````text
You're generating Python `self` and `cls` reserved-word translations for
{N} language packs. Write your batch result to {output_path}.

## Conceptual background

`self` is a REFLEXIVE PRONOUN — the entity referring to its own being.
Grammatically distinct from first-person pronouns (`I`, `me`) and from
demonstratives (`this`, `that`).

The right concept: "oneself / itself / one's own self / the self". When a
method runs in Python, the object is passed in and called `self` because
the object is referring to ITSELF — not "this thing here" (demonstrative)
and not "I" (first-person). The convention came from Smalltalk's notion
of "the receiver of the message".

Reflexive equivalents in well-resourced languages:
  - French: `soi` (oneself), NOT `ceci` (this) or `je` (I)
  - German: `selbst` or `sich` (reflexive marker), NOT `dieses` (this) or `ich` (I)
  - Spanish: `propio` or `mismo`
  - Russian: `себя` (oneself, reflexive accusative)
  - Hindi: `स्वयं` (svayam, oneself)
  - Japanese: `自身` (self-body) or `自己` (oneself)
  - Arabic: `ذاتي` (one's own essence)

DO NOT pick: first-person pronouns ("I", "me"), demonstratives ("this",
"that"), time/place words ("now", "here"), unrelated nouns. Pick the
closest reflexive-pronoun equivalent in the target language.

`cls` is the SAME REFLEXIVE concept applied to the CLASS ITSELF rather
than an instance. Inside a @classmethod, the class is referring to
itself — not "a class" abstractly, but THIS specific class referring to
its own being. Common patterns: a noun for "class" combined with a
reflexive marker, OR a more specific word meaning "the class itself".
AVOID plain transliterations of "class" that would collide with the
keyword translation.

## Five hard invariants per translation

[as above]

## Workflow

For each assigned language:

1. Read the pack file:
   `libs/i18n/language-packs/python/{lang}/legesher_i18n_python_{lang}/packs/3.10.yml`
2. Note existing values in `keywords:`, `builtins:`, `exceptions:` —
   forbidden values for collision purposes.
3. For `self`: pick the closest single-word reflexive equivalent in the
   target language.
4. For `cls`: pick the natural way the language expresses "the class
   itself" — usually a compound of class-noun + reflexive marker.
5. Validate against all five invariants.
6. On collision, iterate using disambiguation patterns: prefix/suffix the
   natural word with a reflexive marker, use a more specific synonym, or
   form a compound.

## Output format

```json
{
  "<lang_code>": {
    "self": "<word>",
    "cls": "<word>",
    "reasoning": "<one-sentence explanation>"
  },
  ...
}
```

The `reasoning` field documents WHY a particular word was chosen, which
helps human reviewers audit linguistic judgment.

````

## Language-specific notes

### Urdu (`ur`) — empirical convergence

The Urdu pack maps the Python keyword `in` to `میں`. Earlier AYA-213
Cond-5 pilot work showed local LLMs (qwen2.5, gemma3, Tiny Aya)
independently converged on `خود` ("oneself") for `self` — which avoids
the `میں` collision. Honor that signal when re-generating Urdu
translations.

### English (`en`) — identity mapping

English is the source language. `self` and `cls` map to themselves
(identity mapping). The translator's dispatch order short-circuits when
`value == source_word`, so the substitution is a no-op at runtime, but
the entries are present for symmetry with other packs.

## Provenance

- v1 (haiku, weak prompt): `claude-haiku-4-5` with "instance reference"
  framing — produced semantically wrong picks for several low-resource
  languages (e.g., Burmese `ကျွန်ုပ်` "I", Mongolian `одоо` "now").
- v2 (sonnet, refined prompt): `claude-sonnet-4-6` with the reflexive-
  pronoun framing above — fixed 7 of 7 concerning v1 picks.
- v3 (agent batches, full reasoning): six parallel agents each handling
  ~9 languages, reading pack files directly and reasoning about each
  pick. Caught additional issues that v2 missed:
  - Swedish: v2 had `klassig` which actually means "classy/stylish" in
    Swedish — completely wrong meaning. Corrected to `klass_själv`.
  - Sundanese: v2 `kelasna` is just "its class" (3rd-person possessive),
    not reflexive. Corrected to `kelas_sorangan`.
  - Hebrew: v2 `מחלקתי` reads as "my class" (1st-person possessive
    suffix). Corrected to `מחלקהעצמה` (3rd-person reflexive `עצמה`).
  - Vietnamese: v2 `lớpnày` is "this class" (demonstrative — explicitly
    forbidden by spec). Corrected to `lớpbảnthân`.

The v3 picks are the canonical values stored in the translations DB and
written to YAML packs.

## Future regeneration

If reserved words ever expand beyond `self`/`cls` (e.g., adding
language-specific conventions), use this same prompt template. Update
the canonical `RESERVED_WORDS` list in
`libs/i18n/legesher_i18n/term_definitions.py` first, then run the agent
batches with the expanded set.
