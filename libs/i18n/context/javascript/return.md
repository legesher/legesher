# JavaScript Keyword: `return` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** verb
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** EASY

---

## Quick Summary

The `return` keyword exits a function and optionally sends a value back to the caller. It marks the end of function execution and specifies what result (if any) the function produces. A function that reaches its end without a `return`, or hits a bare `return`, yields `undefined`.

> **JEJ note:** `return` is part of the JEJ keyword surface, but in valid JEJ programs it is effectively **unreachable** — the JEJ allowlist contains no function declarations, so there is no function body for a `return` to sit in. It is still translated for surface completeness and forward compatibility, so a future JEJ that admits functions has a native word ready.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Return a calculated value (illustrative — functions are outside valid JEJ today)
function add(a, b) {
  return a + b;
}
let result = add(5, 3); // result = 8
```

**What this does:** The `return` statement sends the value `a + b` back to the caller. Function execution stops immediately at `return`, and the returned value becomes the result of the call expression.

### Example 2: Common Pattern

```javascript
// Early return for validation
function divide(a, b) {
  if (b === 0) {
    return null; // early exit on error
  }
  return a / b;
}
let answer = divide(10, 0); // answer = null
```

**What this does:** Demonstrates multiple return points. If `b` is zero, the function returns early; otherwise it continues to the division. Only one `return` executes per call.

### Example 3: Edge Case

```javascript
// Bare return, and implicit undefined
function greet(name) {
  console.log("Hello, " + name);
  return; // bare return: yields undefined
}

function noReturn() {
  console.log("Message");
} // reaching the end also yields undefined
```

**What this shows:** `return` with no value yields `undefined`. A function whose body ends without any `return` also yields `undefined`. A bare `return` is a way to exit early from a function called only for its side effects.

---

## Pattern Classification

**This term is:** ACTION KEYWORD (Function Control)

**Similar terms in this pattern:**

1. `break` - Exits a loop early (the loop analogue of `return`)
2. `continue` - Skips to the next loop pass
3. `if` - Frequently guards an early `return`

**Pattern rule:** Function/loop exit keywords should use verb forms. They perform actions that alter control flow by terminating execution.

---

## Etymology (Brief)

**English Origin:** Latin via French

**Root meaning:** Latin *re-* (back) + *tornare* (to turn). Through Old French *retourner* it became English "return," meaning "to turn back, go back, give back." In programming, `return` metaphorically gives a value back to the caller.

**Why JavaScript uses this:** "Return" captures both actions cleanly: (1) going back to the caller and (2) giving back a value. JavaScript inherited it from the C family, where the same keyword serves the same dual role. It is more precise than alternatives like "send" (one-way) or "result" (a noun).

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `return` statement performs two related actions: it terminates the current function immediately and optionally sends a value back to the calling code. When the engine reaches `return`, it stops executing the function, discards its local scope, and transfers control back to where the function was called.

`return expression` evaluates the expression and sends its value to the caller. With no expression (a bare `return`), the function yields `undefined`. A function that runs off its end without a `return` also yields `undefined` — JavaScript's default "no meaningful result" value, distinct from the deliberate-absence value `null`.

Functions can have several `return` statements across different branches, but only one runs per call. This enables the early-return pattern: validate inputs and return an error value early, avoiding deeply nested conditionals. The returned value may be any JavaScript value — numbers, strings, arrays, objects, even other functions.

> Because valid JEJ programs contain no functions, none of the above is reachable in JEJ today. This brief documents the concept so the surface stays complete and a native word is ready if JEJ later admits functions.

**Key behaviors:**

1. **Immediate termination:** Code after `return` in the same block never runs, which makes `return` ideal for early exits.
2. **A single value:** JavaScript returns exactly one value. To return several pieces of data you wrap them in an array or object and return that.
3. **`undefined` as default:** A bare `return` or an implicit fall-off the end yields `undefined` — not `null`. `undefined` is the engine's "no value provided" marker; `null` is a deliberate "empty" a programmer sets on purpose.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Transitive verb (takes an object — what to return)
- **Action vs State:** Pure ACTION - performs termination and value-sending
- **Temporal aspect:** Instantaneous/completive - happens immediately and ends the function

### Recommended Form

**Primary recommendation:** Use an infinitive verb meaning "to return" or "to give back." Focus on the "giving a value back" sense, not just "going back to a place."

**Forms to AVOID:**

- ❌ A noun like "the return" — should be the verb "to return"
- ❌ "come back" (movement) versus "give back" (value transfer)
- ❌ Past tense "returned" — should be present/infinitive

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Come back to a place" (physical movement — "return home")
- ❌ Meaning 2: "Give back a borrowed item" (restore possession — "return the book")
- ✅ Meaning 3: **GIVE A VALUE BACK TO THE CALLER** (function-result transfer)

**Example:**

English "return" can mean:

1. "I'll return to Paris next year" (go back to a place) ❌
2. "Please return my pen" (give back a borrowed item) ⚠️ (closer — involves giving back)
3. "`return result` sends the value to the caller" (function value transfer) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: terminating the function and sending a value back to the calling code.**

Many languages distinguish "return to a place" (movement) from "return something" (give back). Use the "give back a value" word. Where one word covers both, that is acceptable, but favor the value-giving sense.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `return`, check these translations:**

- [ ] `break` - Exits a loop; `return` exits a function; both should use verb forms
- [ ] `continue` - Another control-flow verb; keep register consistent
- [ ] `null` - The deliberate-absence value often used with early `return`; keep it distinct from `undefined`

**Consistency rule:**

All action/control-flow keywords (`return`, `break`, `continue`) should use verb forms. Do not mix verb and noun forms across them.

### Functional relationships

**This term works WITH:**

1. **`return` + expression**: Returns a computed value

```javascript
function square(n) {
  return n * n;
}
```

2. **`if` + early `return`**: Guard clause

```javascript
function validate(data) {
  if (!data) {
    return false;
  }
  return check(data);
}
```

**Common pairing:**

```javascript
// return a bundled result
function getPoint() {
  return { x: 1, y: 2 }; // one object holds both values
}
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have a direct equivalent
- No ambiguity in the programming sense
- **AI confidence should be HIGH**

### Why EASY for `return`

- Universal programming concept (all languages with functions have a return)
- Clear semantic mapping in most languages
- Well-documented globally
- The "give back a value" versus "go back to a place" distinction is usually clear in technical contexts

**For this term:** EASY

**Rationale:** Function return is fundamental to programming; every language with functions has a return mechanism, with standard translations across CS education. The only nuance is choosing between a "return" verb and a "give back" verb — check which is more common in that language's programming register. (The JEJ unreachability does not change the linguistic difficulty.)

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures FUNCTION RETURN (giving a value back to the caller)?
- [ ] Emphasizes value transfer, not just physical return to a place?
- [ ] Understood as terminating function execution?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb, not noun)?
- [ ] Correct form (infinitive, not past tense)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for JS keywords)?

### 3. Consistency

- [ ] Matches the pattern of the other action keywords (`break`, `continue`)?
- [ ] Uses a verb form like the other control-flow keywords?
- [ ] Kept distinct from `null` (the deliberate-absence value)?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on a standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common verb)?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: return
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries the "give a value back to the caller" concept in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution, never in another language's choice.

**Alternatives considered:**

List the candidate terms weighed in the target language and why each was rejected or kept, noting any that drifted toward "go back to a place."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (no established native term, competing regional conventions, semantic gap) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
