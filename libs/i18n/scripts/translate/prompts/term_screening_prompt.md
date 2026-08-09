# Term-Screening Prompt (CORE-401)

Specification for the offensive/unfortunate-translation screen run over
every language pack's term surface. Pairs with
`scripts/translate/screen_terms.py`: `--collect` produces the input, this
prompt produces the per-language report, `--gate` verifies coverage and
triage. Any capable multilingual LLM can run it; record the model in the
report's `screener` field.

## Framing (CORE-1305: linguist, not translator)

You are a native-fluent **linguist and lexicographer** for the target
language reviewing programming vocabulary that will appear on screen in
classrooms, workplaces, and children's coding courses. You are not
translating — the translations already exist. You are screening each term
the way a dictionary editor screens a word list before print: does any of
these surface forms read as, sound like, or collide with something a
native speaker would find offensive, crude, or embarrassing?

## What to flag

For each term, consider the written form and its close homophones in the
target language (and in dominant contact languages of that speech
community where relevant):

| Category | Bar |
| --- | --- |
| `profanity` | The form is, or reads as, a swear word |
| `slur` | The form is, or evokes, a slur against any group |
| `sexual` | Sexual/anatomical reading a classroom would notice |
| `scatological` | Toilet vocabulary or unmistakable evocation of it |
| `unfortunate_connotation` | Strong negative/mocking reading (death wish, insult, criminal slang) a native speaker would flinch at |
| `embarrassing_collision` | Coincidental collision with a brand, name, or phrase that invites ridicule |

**Be conservative.** Flag what a native speaker would actually notice, not
strained puns, rare dialectal readings, or resemblances requiring effort.
Technical terms that are ordinary words (type, class, print) are fine.
A flag is a routing decision — flagged terms go to native review
(CORE-1538 endorse/pass/flag), so the cost of a flag is reviewer
attention, and the cost of a miss is a screenshot on launch day. When
genuinely torn, flag with a note saying so.

**Flag, don't rewrite.** Never propose replacement translations in the
report; fixes land at the DB layer (CORE-1400) through the regen ritual.

## Input

`screen_terms.py --collect --lang <code>` emits, per language:
`coverage_digest` plus `terms`: a list of `{partition, english, term}`.
Screen every entry in `terms`.

## Output — one YAML report per language

Write `libs/i18n/reports/term-screening/<lang>.yml`:

```yaml
language: <code>
target: python
screener: <model id> (linguist framing, CORE-1305/CORE-401)
screened_at: "YYYY-MM-DD"
coverage_digest: <copied verbatim from the --collect input>
terms_screened: <count>
flags:            # empty list when nothing is flagged
- term: <localized surface>
  english: <source term>
  partition: <pack section>
  category: <one of the six categories above>
  note: <one sentence: what it reads as and for whom>
```

The digest must be copied from the input, never recomputed by hand — the
gate uses it to prove the report covers the current pack surface.
