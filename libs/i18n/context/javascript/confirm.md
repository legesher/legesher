# JavaScript Builtin: `confirm` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** function (browser global)
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** MEDIUM

---

## Quick Summary

`confirm` is a browser global function that shows the user a modal box with a message and two buttons — OK and Cancel — and returns `true` if they click OK, `false` if they click Cancel. In JEJ it is how a program asks the user a yes/no question and acts on the answer.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Ask the user to approve an action
let ok = confirm("Delete this file?");
```

**What this does:** Shows a box with "Delete this file?" plus OK and Cancel buttons, then stores `true` (OK) or `false` (Cancel) in `ok`.

### Example 2: Common Pattern

```javascript
// Branch on the user's yes/no answer
if (confirm("Leave the page?")) {
  alert("Goodbye");
}
```

**What this does:** Uses the boolean returned by `confirm` directly as an `if` condition, running the block only when the user approves.

### Example 3: Edge Case

```javascript
// confirm returns a real boolean, not the button text
let answer = confirm("Continue?");
console.log(answer);   // true or false, never "OK"
```

**What this shows:** Unlike `alert` (which returns nothing) and `prompt` (which returns typed text), `confirm` returns a boolean. Its value is the *decision*, not a string.

---

## Pattern Classification

**This term is:** DIALOG QUERY (verb-like global function returning a boolean)

**Similar terms in this pattern:**

1. `alert` - Also a browser dialog global, but only shows a message and returns nothing
2. `prompt` - Also a browser dialog global, but collects typed text and returns a string
3. `console` - Also carries interaction, but developer-facing, not a user decision

**Pattern rule:** The dialog globals (`alert`, `confirm`, `prompt`) are user-facing actions. Translate them as verbs of one register. `confirm` specifically asks for approval and yields a yes/no answer — keep the "ask for confirmation" sense central.

---

## Etymology (Brief)

**English Origin:** Latin → Old French

**Root meaning:** From Latin *confirmare* ("to make firm, strengthen, establish"), via Old French *confermer*. It means "to make certain, to verify, to give assent."

**Why JavaScript uses this:** The dialog exists to have the user *confirm* — make firm — a decision before the program proceeds. The word captures "get the user to commit to yes or no."

---

## Concept Explanation (Intermediate Level)

**What it does:**

`confirm` is a global function provided by the browser environment. Called with a message, it opens a modal dialog showing that message and two buttons: OK and Cancel. Like `alert`, it is *blocking* — the page waits for the user. Unlike `alert`, it returns a value: the boolean `true` if the user clicked OK, `false` if they clicked Cancel or dismissed the box.

In the JEJ teaching subset, `confirm` is the learner's first two-way interaction with a user: the program asks, the user answers, and the code branches on that answer. It pairs naturally with `if`, since its return value is already a boolean. This is a step up from `alert` (one-way notice) and a step down from `prompt` (free-text input).

Conceptually, `confirm` names an *action that asks for approval and reports the decision*. It is verb-like — the program *does* the asking — but distinctive in that it hands back a yes/no result the code depends on.

**Key behaviors:**

1. **Two-button dialog:** Presents OK and Cancel, not free input.
2. **Returns a boolean:** `true` for OK, `false` for Cancel/dismiss — usable directly in conditions.
3. **Blocking:** The page halts until the user decides.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Command / action that asks the user to approve
- **Action vs State:** ACTION - it *does* the asking; the boolean it returns is the outcome
- **Temporal aspect:** One-time, immediate — fires once per call

### Recommended Form

**Primary recommendation:** Translate as a verb meaning "confirm / ask for approval / verify yes-or-no." Keep it in the same verb form and register as `alert` and `prompt` so the three dialog actions read as a family. The word should evoke "get a yes/no decision," not merely "agree."

**Forms to AVOID:**

- ❌ A noun for "a confirmation" - `confirm` here is the *act* of asking, not the receipt/notice
- ❌ A word meaning only "agree / accept" - it must cover *asking*, and the answer can be no
- ❌ The "confirm a reservation / booking" domain sense - too narrow

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Confirm a fact is true" (verify a statement's truth)
- ❌ Meaning 2: "A confirmation" as a noun — a receipt or notification
- ✅ Meaning 3: **"ASK THE USER TO APPROVE, GET YES/NO"** — pose an OK/Cancel decision

**Example:**

English "confirm" can mean:

1. "Tests **confirm** the theory" (verify a fact) ❌
2. "You'll get a **confirmation** email" (a notice, a noun) ❌
3. "**confirm** with the user before deleting" (ask them to approve, yes or no) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: the action of asking the user to approve and receiving a yes/no decision, not verifying a fact or a confirmation-notice.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `confirm`, check these translations:**

- [ ] `alert` - Sibling dialog action; must share verb form and register
- [ ] `prompt` - Sibling dialog action; must share verb form and register
- [ ] `if` / boolean logic - `confirm` returns a boolean; align with how true/false decisions read

**Consistency rule:**

`alert`, `confirm`, and `prompt` are the three user-dialog actions and must be one matched family of verbs. Do not translate `confirm` as a noun ("a confirmation") while `alert` is a verb. Keep register uniform.

### Functional relationships

**This term works WITH:**

1. **`confirm` + `if`**: The boolean feeds a condition

```javascript
if (confirm("Are you sure?")) {
  // user clicked OK
}
```

**Common pairing:**

```javascript
// confirm gates a destructive action
let proceed = confirm("Overwrite the file?");
if (proceed) {
  alert("Overwritten");
}
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** "Confirm" has a solid verb in most languages, but the everyday sense leans toward "agree/verify" while the JS sense is "ask for a yes/no decision." A translator must pick a verb that covers the *asking* (the answer may be no) and that stays consistent with `alert`/`prompt`. That register and scope choice is worth a native reviewer's confirmation.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (ask the user, get yes/no)
- [ ] Would a native speaker read this as "ask for approval," not "verify a fact"?
- [ ] Avoids implying the answer is always yes?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb, not noun)?
- [ ] Correct form (action register)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language (lowercase `confirm` in JS)?

### 3. Consistency

- [ ] Matches verb form of `alert` and `prompt`?
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
term: confirm
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term names the action of asking the user for a yes/no approval in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it shares a verb form with `alert` and `prompt`.

**Alternatives considered:**

List the candidate verbs weighed and why each was rejected or kept, especially any rejected for meaning only "agree" or being a noun.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (asking-vs-agreeing scope, register) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
