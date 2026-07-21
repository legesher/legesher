# JavaScript Builtin: `prompt` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** function (browser global)
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** MEDIUM

---

## Quick Summary

`prompt` is a browser global function that shows the user a modal box with a message and a text field, and returns the string they type (or `null` if they cancel). In JEJ it is how a program asks the user *for input* — the free-text counterpart to `confirm`'s yes/no.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Ask the user to type something
let name = prompt("What is your name?");
```

**What this does:** Shows a box with the question and an input field, then stores whatever the user types (as a string) in `name`.

### Example 2: Common Pattern

```javascript
// Use the typed answer in the program
let name = prompt("What is your name?");
alert("Hello, " + name);
```

**What this does:** Feeds the user's typed reply straight into an on-screen greeting — a full ask-then-respond loop.

### Example 3: Edge Case

```javascript
// prompt returns a STRING, even for numbers; null if cancelled
let age = prompt("Your age?");
console.log(typeof age);   // "string", even if they typed 30
// If the user clicks Cancel, age is null
```

**What this shows:** `prompt` always returns text (never a number), and returns `null` when the user cancels. The caller must convert or check the result.

---

## Pattern Classification

**This term is:** INPUT ACTION (verb-like global function returning a string)

**Similar terms in this pattern:**

1. `alert` - Also a browser dialog global, but shows a message and returns nothing
2. `confirm` - Also a browser dialog global, but returns a yes/no boolean
3. `console` - Also an interaction facility, but developer-facing, not user input

**Pattern rule:** The dialog globals (`alert`, `confirm`, `prompt`) are user-facing actions. Translate them as verbs of one register. `prompt` specifically means "ask the user to type an answer" — the "request input" sense must dominate over the noun "a prompt."

---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** From Latin *promptus* ("brought forth, ready, at hand"), from *promere* ("to bring out"). It came to mean "to move someone to speak / to cue a response," and also the noun "a cue that draws out a reply."

**Why JavaScript uses this:** The dialog *prompts* the user — cues them to supply an answer. The name captures "draw a typed response out of the user."

---

## Concept Explanation (Intermediate Level)

**What it does:**

`prompt` is a global function provided by the browser environment. Called with a message (and an optional default value), it opens a modal dialog showing the message, a single-line text field, and OK/Cancel buttons. Like the other dialog globals it is *blocking*. It returns the text the user typed if they click OK, or `null` if they click Cancel.

In the JEJ teaching subset, `prompt` completes the interaction trio: `alert` speaks, `confirm` asks yes/no, `prompt` collects free text. It is the browser analogue of a beginner "read a line from the user" step, and is often a learner's first taste of taking input, converting it, and using it. Because it always returns a string, teaching material pairs it with number conversion when the answer should be numeric.

Conceptually, `prompt` names an *action that requests typed input and hands it back*. It is verb-like — the program *does* the asking — even though English also uses "prompt" as a noun for the cue itself. In JS the term is the action.

**Key behaviors:**

1. **Returns typed text:** Always a string when confirmed, regardless of what looks like a number.
2. **`null` on cancel:** Cancelling yields `null`, so callers must guard against it.
3. **Blocking:** The page waits until the user submits or cancels.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Command / action that requests input from the user
- **Action vs State:** ACTION - it *does* the requesting; the string it returns is the outcome
- **Temporal aspect:** One-time, immediate — fires once per call

### Recommended Form

**Primary recommendation:** Translate as a verb meaning "ask for input / request that the user type an answer." Keep it in the same verb form and register as `alert` and `confirm`. The chosen word must foreground the *act of requesting input*, not the static "a prompt / a cue" noun.

**Forms to AVOID:**

- ❌ A noun for "a prompt / a cue" - `prompt` here is the *act* of requesting, not the on-screen cue object
- ❌ The theatrical "prompt an actor" sense - wrong domain, misleading
- ❌ The "prompt = quick/on-time" adjective sense - unrelated meaning

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Prompt" as a noun — a cue, a printed sign, an AI prompt string
- ❌ Meaning 2: "Prompt" as an adjective — quick, punctual ("a prompt reply")
- ✅ Meaning 3: **"ASK THE USER TO TYPE AN ANSWER"** — the act of requesting input

**Example:**

English "prompt" can mean:

1. "Type your command at the **prompt**" (a cue/sign, a noun) ❌
2. "Thank you for your **prompt** reply" (quick, adjective) ❌
3. "**prompt** the user for their name" (ask them to type an answer) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: the action of requesting typed input from the user, NOT the noun "a cue" nor the adjective "quick."**

The noun/verb split is the central trap here: many languages have distinct words, and the JS term is the *verb* (request input), not the *noun* (a cue).

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `prompt`, check these translations:**

- [ ] `alert` - Sibling dialog action; must share verb form and register
- [ ] `confirm` - Sibling dialog action; must share verb form and register
- [ ] `undefined` / `null` - `prompt` returns `null` on cancel; align with how "no value" reads

**Consistency rule:**

`alert`, `confirm`, and `prompt` are one matched family of user-dialog verbs. Translate `prompt` as a verb in the same register, not as the noun "a prompt." If the target language uses different words for the cue-noun and the request-verb, choose the verb.

### Functional relationships

**This term works WITH:**

1. **`prompt` + variable**: Store the typed answer

```javascript
let city = prompt("Which city?");
```

**Common pairing:**

```javascript
// prompt then respond
let name = prompt("Your name?");
if (name) {
  alert("Hi, " + name);
}
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The action "ask for input" translates cleanly in most languages, but "prompt" is heavily overloaded (noun cue, adjective "quick", AI-prompt). The translator must deliberately pick the *request-input verb* and keep it consistent with `alert`/`confirm`. The noun-vs-verb split is a real pitfall, so a native reviewer should confirm the verb reading.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (ask the user to type an answer)
- [ ] Would a native speaker read this as the *verb* "request input," not the noun "a cue"?
- [ ] Avoids the "quick/punctual" adjective sense?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb, not noun)?
- [ ] Correct form (action register)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language (lowercase `prompt` in JS)?

### 3. Consistency

- [ ] Matches verb form of `alert` and `confirm`?
- [ ] Same register as the sibling dialog actions?
- [ ] Aligns with related terms (checked cross-references)?

### 4. Usability

- [ ] Short enough (1-2 words)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs (especially RTL scripts)?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: prompt
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term names the *action* of requesting typed input from the user in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm you chose the verb, not the noun "a prompt," consistent with `alert` and `confirm`.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any rejected for being the noun "a cue" or the adjective "quick."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (noun-vs-verb split, overloaded meanings) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
