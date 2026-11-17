# Error-Message Template Prompt (CORE-1881)

Specification for generating localized error-message templates — the
`message_translations` rows behind localized tracebacks (CORE-1679).
Companion to `vocabulary_prompt.md` and shaped the same way: conceptual
framing first, hard invariants second, template third, provenance last.

`scripts/translate/generate_messages.py` renders the template below; this
file is the specification the script implements, and the place to change
the framing.

## Conceptual framing

Messages are **sentences with grammar**, not identifiers — the second data
class of the corpus, and the reason the term lane does not carry over. The
audience is a learner reading their own traceback: clarity for a beginner
outranks literal fidelity to the English wording. The model is localizing
running prose, so the linguist-not-translator framing of the term lane
relaxes to "translate this sentence idiomatically", with one mechanical
contract on top.

## The mechanical contract

The Scratch localization pipeline's CI insight (CORE-1356 prior-art
review): placeholder preservation is a **machine check, not a review
item**. The prompt states the contract; `add_message_locale.py` enforces
it on every write, whatever the source:

- Every `{slot}` placeholder survives byte-for-byte — same braces, same
  English slot name. `{name}` stays `{name}` in every script, including
  RTL text. A translated, renamed, or dropped slot breaks substitution
  silently, and the failure surfaces only in a learner's traceback.
- A slot may MOVE within the sentence as the grammar requires. Slots are
  named and the renderer substitutes by name, so order is free — the
  "reorder" failure class belongs to positional systems (`%1`-style);
  requiring source order here would wrongly reject correct grammar.
- Brace characters that are not declared placeholders are literal text.
  CPython messages legitimately talk about braces (`f-string: valid
  expression required before '}'`); the renderer uses literal replacement,
  never `str.format`, precisely so these survive.
- No bidirectional control characters in stored strings — display
  isolation is a render-time concern (the ratified code-vs-display
  policy); stored strings stay clean and reviewable.
- An empty English template (`KeyboardInterrupt`) renders as an empty
  string, not an invented message. `add_message_locale.py` enforces both
  directions: a translation is empty exactly when its English template is.

Exception class names are not part of the templates: `ZeroDivisionError:`
is scaffolding rendered elsewhere, so the prompt neither asks for nor
accepts a policy on translating class names.

## Sentences are spelled as sentences

The style guides under `style-guides/` describe **identifiers**: no
zero-width joiner in a Sinhala name, no zero-width non-joiner in a Persian
one, underscores between the words of a Thai, Burmese or Persian one. Each
of those is a spelling mistake in a sentence. The prompt therefore:

- takes only the script, direction, letter-case and digit lines from the
  guide, and none of its rules for writing a name: neither the
  identifier-formation rule nor the script constraints. The constraints
  cannot be filtered one by one, because several are naming rules worded as
  requirements;
- states that the templates are sentences in the language's normal
  orthography: usual spacing and punctuation with no underscores, the
  standard letters rather than presentation forms, every mark and joiner
  the standard spelling uses, and vowel points only where ordinary prose
  uses them (Hebrew and Arabic-script prose is normally unpointed, like the
  Arabic pack's renderings).

Joiners are not directional controls. The write path refuses the
directional controls listed above and accepts ZWJ and ZWNJ.

## Code stays code

Python names, operators and literal syntax inside a template (`'print'`,
`print(...)`, `'=='`, `int()`, `str`, `StopIteration`, `0o`, `f-string`,
`[Errno {errno}]`) are kept exactly as written; the words around them are
translated. This is what the Spanish and Arabic pack renderings do.

## Economics

One call per locale, all templates together (55 short sentences fit one
response). A per-message call is the leak (CORE-1805). All-or-nothing per
locale: a response with any invalid rendering writes nothing, because the
half-written locale is the state the coverage rule exists to prevent.

The response has its own output ceiling (`MAX_OUTPUT_TOKENS` in the script).
Current models think before they answer, and that thinking counts against
the ceiling, so the vocabulary lane's ceiling is too small for 55 sentences.
A response the model did not finish, cut off at the ceiling
(`stop_reason=max_tokens`) or declined (`stop_reason=refusal`), is reported
by that reason, writes nothing, and still counts against the run's budget:
it was billed.

## Provenance

Rows enter at the `machine` rung with `source='claude_agent'` (the
linguist-framed-agent trust rung), `model_version` = the model id, and
`created_by='generate_messages.py'`. Review posture is the standing
policy: best-effort native, non-blocking; the gate blocks on mechanical
errors only.
