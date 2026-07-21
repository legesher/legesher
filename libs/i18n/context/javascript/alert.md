# JavaScript Builtin: `alert` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** function (browser global)
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** MEDIUM

---

## Quick Summary

`alert` is a browser global function that pops up a small modal box showing a message to the user and pausing the page until they click "OK". In JEJ it is the simplest way a program speaks directly to a person on screen, as opposed to `console.log`, which speaks to the developer.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Pop up a message for the user
alert("Saved!");
```

**What this does:** Displays a modal box containing `"Saved!"` with an OK button, and blocks the page until the user dismisses it.

### Example 2: Common Pattern

```javascript
// Tell the user the result of an action
let score = 8;
alert("Your score is " + score);
```

**What this does:** Uses `alert` to surface a computed value to the person using the page — a visible, on-screen notice rather than developer output.

### Example 3: Edge Case

```javascript
// alert always shows text; non-strings are converted first
alert(42);        // shows "42"
alert(true);      // shows "true"
```

**What this shows:** `alert` takes one message and coerces it to text before displaying. It returns nothing useful (`undefined`) — its whole purpose is the side effect of showing the box, not producing a value.

---

## Pattern Classification

**This term is:** OUTPUT ACTION (verb-like global function)

**Similar terms in this pattern:**

1. `confirm` - Also a browser dialog global, but asks a yes/no question and returns a boolean
2. `prompt` - Also a browser dialog global, but asks for typed input and returns a string
3. `console` - Also carries program output, but to the developer panel rather than a user-facing box

**Pattern rule:** The dialog globals (`alert`, `confirm`, `prompt`) are actions the program performs on the user's screen. Translate them as verbs of the same register — commands that *do* something — and keep them consistent as a trio.

---

## Etymology (Brief)

**English Origin:** Old French → Italian

**Root meaning:** From Italian *all'erta* ("on the watch / to the lookout"), which became French *alerte*. It carries the sense of "call attention, warn, raise notice."

**Why JavaScript uses this:** Early browsers needed a way for a script to interrupt the user and show a message. "Alert" captured "get the user's attention right now" — an attention-grabbing notice that stops everything until acknowledged.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`alert` is a global function provided by the browser environment (it is not part of core language mechanics and is absent in plain Node). Calling it with a message opens a small modal dialog containing that message and a single OK button. The dialog is *blocking*: the rest of the page halts until the user clicks OK.

In the JEJ teaching subset, `alert` is a learner's first way to make a program communicate with a person rather than with the developer console. It is deliberately simple — one message in, one box out — which makes it a natural teaching companion to `console.log`. Where `console.log` writes quietly to a hidden panel, `alert` interrupts and demands acknowledgment.

Conceptually, `alert` names an *action performed toward the user*: "show this notice." It produces no meaningful return value; the point is the visible side effect. This makes it a verb-like builtin, distinct from the object-like globals (`Date`, `RegExp`) that name things.

**Key behaviors:**

1. **Blocking notice:** The page pauses until the user dismisses the box.
2. **One-way:** It only shows a message; it collects no answer (that is what `confirm` and `prompt` add).
3. **Coerces to text:** Any argument is converted to a string before being shown.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Command / action the program issues to notify the user
- **Action vs State:** ACTION - it *does* something (shows a box), it does not name a thing
- **Temporal aspect:** One-time, immediate — fires once each call

### Recommended Form

**Primary recommendation:** Translate as a verb meaning "warn / notify / raise a notice to the user" — an imperative-flavored action word. Keep it in the same verb form and register as `confirm` and `prompt` so the three dialog actions read as a set.

**Forms to AVOID:**

- ❌ A noun for "an alert / a warning" - `alert` here is the *act* of notifying, not the notice object
- ❌ The military "alert level / state of alert" sense - too heavy, wrong register
- ❌ A word implying danger or emergency - `alert` shows any message, not only warnings

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "On alert / a state of watchfulness" (adjective/noun, readiness)
- ❌ Meaning 2: "An alert" as a noun — the notice itself, a stored warning object
- ✅ Meaning 3: **"NOTIFY THE USER NOW"** — the act of popping a message box on screen

**Example:**

English "alert" can mean:

1. "The guards were on **alert**" (state of readiness) ❌
2. "She got a weather **alert**" (a notice, a noun) ❌
3. "**alert** the user that the file saved" (perform the act of notifying) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: the action of showing the user a message, not a state of readiness or a notice-object.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `alert`, check these translations:**

- [ ] `confirm` - Sibling dialog action; must share verb form and register
- [ ] `prompt` - Sibling dialog action; must share verb form and register
- [ ] `console` - Related output facility; keep `alert` distinct as user-facing, not developer-facing

**Consistency rule:**

`alert`, `confirm`, and `prompt` are the three user-dialog actions. Translate all three as verbs of one consistent register. If `alert` becomes a verb but `confirm` becomes a noun, the set breaks. They should feel like a matched family of on-screen actions.

### Functional relationships

**This term works WITH:**

1. **`alert` + a message string**: The notice shown to the user

```javascript
alert("Upload complete");
```

**Common pairing:**

```javascript
// alert reports an outcome the user should see
let name = "Ada";
alert("Welcome, " + name);
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** Most languages have a clear verb for "warn / notify," so the core action translates well. The difficulty is register: `alert` in JS is neutral (any message), not only danger, so a translator must avoid a word that implies emergency. Keeping it a verb consistent with `confirm`/`prompt` is the main judgment call worth a native reviewer's eye.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (show a message box to the user)
- [ ] Would a native speaker read this as "notify the user," not "a state of alert"?
- [ ] Avoids implying danger/emergency only?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb, not noun)?
- [ ] Correct form (action/imperative register)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language (lowercase `alert` in JS)?

### 3. Consistency

- [ ] Matches verb form of `confirm` and `prompt`?
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
term: alert
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term names the action of notifying the user on screen in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it shares a verb form with `confirm` and `prompt`.

**Alternatives considered:**

List the candidate verbs weighed and why each was rejected or kept, especially any rejected for implying danger/emergency.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (register, verb-vs-noun choice) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
