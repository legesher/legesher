# JavaScript Builtin: `undefined` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** constant (primitive value)
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** HARD

---

## Quick Summary

`undefined` is the value a variable holds before anything is assigned to it, and the value you get for a property or return that was never set. It means "not yet given a value" — the default *absence-by-default*, to be kept distinct from `null` (which is a *deliberately* empty value).

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// A declared but unassigned variable is undefined
let x;
console.log(x);   // undefined
```

**What this does:** Declaring `x` without assigning gives it `undefined` — the "nothing has been put here yet" default.

### Example 2: Common Pattern

```javascript
// Missing object properties read as undefined
let user = { name: "Ada" };
console.log(user.age);   // undefined (no such property)
```

**What this does:** Reading a property that was never set returns `undefined`, signaling "this was never given a value," not an error.

### Example 3: Edge Case

```javascript
// undefined (not set) vs null (deliberately empty)
let a;            // undefined — never assigned
let b = null;     // null — explicitly set to "empty"
console.log(a === b);   // false — different concepts
console.log(a == b);    // true  — loose equality treats both as "no value"
```

**What this shows:** `undefined` and `null` both mean "no value," but `undefined` is the *default absence* and `null` is an *intentional* emptiness. They are distinct values (`===` says false); only loose `==` blurs them.

---

## Pattern Classification

**This term is:** VALUE CONSTANT (absence-by-default)

**Similar terms in this pattern:**

1. `null` - The *other* "no value"; deliberately-empty, set by the programmer
2. `NaN` - Also a special constant value in the number domain
3. `Infinity` - Also a special constant value in the number domain

**Pattern rule:** The special value constants (`undefined`, `null`, `NaN`, `Infinity`) are *names of particular values*. Translate them as nouns/labels for the value, and keep `undefined` and `null` clearly *different* words, since they name different kinds of absence.

---

## Etymology (Brief)

**English Origin:** Latin prefix *un-* + *definire*

**Root meaning:** "Un-" (not) + Latin *definire* ("to bound, to set limits, to define"). "Undefined" means "not (yet) given a definition / not set / without an assigned value."

**Why JavaScript uses this:** JS needed a value for "a slot that exists but has never been given a value." "Undefined" says exactly that — the variable is defined to exist but its value is *not yet defined*. It contrasts with `null`, the value you assign on purpose.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`undefined` is a primitive value that JavaScript uses automatically wherever a value is expected but none has been supplied: an uninitialized variable, a missing object property, a function parameter left out, or a function that returns nothing. The program does not raise an error — it fills the gap with `undefined`, meaning "no value has been given here."

In the JEJ teaching subset, `undefined` is central to understanding how JS handles "nothing is here yet." The crucial teaching point is its contrast with `null`. Both mean "no value," but they answer different questions: `undefined` = "was a value ever set? No, by default." `null` = "is this empty? Yes, on purpose, someone set it to empty." A beginner who conflates them will misread code, so the two must translate to *distinct* words.

Conceptually, `undefined` is a *noun-like label for a specific value* — the absence that arises by default. It is not an action and not a boolean. It represents the *unset* state, whereas `null` represents the *intentionally-emptied* state.

**Key behaviors:**

1. **The default absence:** Unassigned variables, missing properties, and value-less returns are `undefined` automatically.
2. **Distinct from `null`:** `undefined === null` is false; they are different values for different kinds of "no value."
3. **A value, not an error:** Reading something unset yields `undefined` rather than crashing.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Name/label for the "not-yet-set" value
- **Action vs State:** STATE - names an absence/condition, does not perform an action
- **Temporal aspect:** Suggests "not yet" — the default state before assignment

### Recommended Form

**Primary recommendation:** Translate as a term meaning "undefined / unset / not-yet-given" — the *default* absence. It should read as a value label and, critically, must be a *different* word from whatever you choose for `null`. Favor wording that carries the "not yet assigned / by default absent" nuance over generic "empty."

**Forms to AVOID:**

- ❌ The same word you use for `null` - the two concepts must stay distinct
- ❌ A word meaning "empty container/zero" - that is emptiness of contents, not "never set"
- ❌ A verb ("to undefine") - `undefined` names a value, it does not act

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Vague / unclear" (an undefined feeling, blurry outline)
- ❌ Meaning 2: "Undefined" in math (e.g. division by zero has no defined result)
- ✅ Meaning 3: **"A SLOT THAT HAS NOT YET BEEN GIVEN A VALUE"** — absence by default

**Example:**

English "undefined" can mean:

1. "An **undefined** sense of unease" (vague, unclear) ❌
2. "1/0 is **undefined**" (mathematically has no value) ❌ *(related but not this)*
3. "The variable is **undefined** until you assign it" (no value set yet) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: a real, specific value meaning "not yet assigned / absent by default" — and it must differ from the word chosen for `null` (deliberately empty).**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `undefined`, check these translations:**

- [ ] `null` - MUST be a *different* word; `undefined` = absent-by-default, `null` = deliberately-empty
- [ ] `NaN` - Fellow special value constant; keep the value-label register consistent
- [ ] `Infinity` - Fellow special value constant; consistent value-label register

**Consistency rule:**

`undefined` and `null` are the load-bearing contrast. Choose two clearly distinct native words: one for "never set / default absence" (`undefined`) and one for "intentionally empty" (`null`). If a language has only one natural word for "nothing," add a qualifier so learners can still tell the two apart. Do NOT collapse them into the same translation.

### Functional relationships

**This term works WITH:**

1. **`undefined` from unassigned variables**:

```javascript
let x;
if (x === undefined) {
  // x was never given a value
}
```

**Common pairing:**

```javascript
// undefined (unset) contrasted with null (emptied on purpose)
let notSet;              // undefined
let clearedOut = null;   // null
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM-HARD**

**For this term:** MEDIUM-HARD

**Rationale:** Many languages have one everyday word for "nothing / empty," but JavaScript needs `undefined` and `null` to stay *distinct* — absence-by-default vs deliberate-emptiness. Preserving that contrast, without a natural second word, is the core difficulty and forces a coinage or qualifier in some languages. This is exactly the kind of subtle two-value distinction a native reviewer should confirm.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (a value meaning "not yet set / absent by default")
- [ ] Would a native speaker read it as "never assigned," not "vague/unclear"?
- [ ] Is it clearly DIFFERENT from the `null` translation?

### 2. Linguistic Correctness

- [ ] Correct part of speech (value label, not a verb)?
- [ ] Correct form (state/value noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language (lowercase `undefined` in JS)?

### 3. Consistency

- [ ] Distinct from `null`, with the default-vs-deliberate nuance preserved?
- [ ] Same value-label register as `NaN` / `Infinity`?
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
term: undefined
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term names the "not-yet-set / absent-by-default" value in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and state explicitly how it differs from the `null` translation.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any rejected for colliding with `null` or meaning "empty container."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (undefined-vs-null distinction, single native word for "nothing") so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
