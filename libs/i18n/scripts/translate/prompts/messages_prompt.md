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
  string, not an invented message.

Exception class names are not part of the templates: `ZeroDivisionError:`
is scaffolding rendered elsewhere, so the prompt neither asks for nor
accepts a policy on translating class names.

## Economics

One call per locale, all templates together (55 short sentences fit one
response). A per-message call is the leak (CORE-1805). All-or-nothing per
locale: a response with any invalid rendering writes nothing, because the
half-written locale is the state the coverage rule exists to prevent.

## Provenance

Rows enter at the `machine` rung with `source='claude_agent'` (the
linguist-framed-agent trust rung), `model_version` = the model id, and
`created_by='generate_messages.py'`. Review posture is the standing
policy: best-effort native, non-blocking; the gate blocks on mechanical
errors only.
