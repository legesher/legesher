# JavaScript Builtin: `Math` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** object (global namespace)
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** MEDIUM

---

## Quick Summary

`Math` is the global namespace object that holds JavaScript's mathematical functions and constants — `Math.floor(...)`, `Math.max(...)`, `Math.PI`. It is a *facility* accessed by name and dotted into; unlike `String` or `Number`, it is never built with `new`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Round a number down to a whole number
let n = Math.floor(3.7); // 3
```

**What this does:** Reaches the `Math` object and calls its `floor` method to round `3.7` down. `Math` names the toolbox; `floor` is the tool taken from it.

### Example 2: Common Pattern

```javascript
// Pick the larger of two values
let a = 8, b = 12;
let bigger = Math.max(a, b); // 12
```

**What this does:** Uses `Math` as the home of everyday math helpers a learner reaches for — here `max` to compare two values. The name `Math` groups these helpers together.

### Example 3: Edge Case

```javascript
// Math is a namespace, NOT a constructor — this is an error
// let m = new Math();  // TypeError: Math is not a constructor
let area = Math.PI * 4 * 4; // Math also holds constants
```

**What this shows:** `Math` cannot be constructed with `new` the way `Number` or `Date` can. It is a static collection — a namespace holding methods (`Math.floor`) and constants (`Math.PI`). Translating `Math` names that collection, not any one function inside it.

---

## Pattern Classification

**This term is:** GLOBAL OBJECT (namespace)

**Similar terms in this pattern:**

1. `console` - Also a global namespace object accessed by name then dotted into (`console.log`)
2. `Number` - Also a capitalized global, but a *type/constructor*, not a namespace
3. `String` - Also a capitalized global type object, contrasted with `Math`'s namespace role

**Pattern rule:** Global namespace objects (`Math`, `console`) are named facilities — translate them as nouns naming the toolbox, not as verbs. Keep `Math` consistent with `console` in noun form and register.

---

## Etymology (Brief)

**English Origin:** Greek

**Root meaning:** "Math" is short for "mathematics," from Greek *máthēma* ("that which is learnt," "science, knowledge"), from *manthánein* ("to learn").

**Why JavaScript uses this:** The name gathers arithmetic and numeric helpers under the plainest possible heading — "mathematics." It signals "the place where the standard math operations live," a static toolbox rather than a value you create.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`Math` is a global object always available to a JavaScript program. It is not created by the learner and cannot be constructed with `new`; it exists as a fixed *namespace* — a named collection of related tools. Its members are mathematical functions (`Math.floor`, `Math.ceil`, `Math.round`, `Math.abs`, `Math.max`, `Math.min`, `Math.pow`, `Math.sqrt`) and a few constants (`Math.PI`).

In the JEJ teaching subset, `Math` matters as the home a learner reaches into for common numeric operations: rounding a decimal, taking an absolute value, finding the larger of two numbers. The learner types the name `Math`, a dot, and the operation they want. `Math` itself performs nothing — it *names where the math tools are kept*; the action lives in the member after the dot.

Conceptually, `Math` names a *facility / toolbox*, not an action and not a value type. This makes it a sibling of `console`: both are named namespaces you dot into, and both should be translated as facility nouns of the same register. It is deliberately unlike `Number` — `Number` is a *type* of value, whereas `Math` is a *collection of operations* on numbers.

**Key behaviors:**

1. **Always available:** `Math` is a global; it need not be declared or imported.
2. **A namespace, not a constructor:** it groups static methods and constants; `new Math()` is an error.
3. **Names a toolbox, not an action:** `Math` names *where* the operations live; the *what* (`floor`, `max`) is a separate member.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Proper-noun-like name for the mathematics facility
- **Action vs State:** STATE/thing — names a collection of tools, does not perform an action
- **Temporal aspect:** None — it is a persistent, always-present facility

### Recommended Form

**Primary recommendation:** Translate as the noun for "mathematics" (the field/discipline) in your target language — the recognized academic word, kept short if a common short form exists. Treat it as a facility noun consistent with `console`.

**Forms to AVOID:**

- ❌ A verb form ("to calculate / to compute") — `Math` names a toolbox, it does not command
- ❌ A word for a single operation (rounding, adding) — those belong to the members, not to `Math`
- ❌ A word meaning "number" — that is the `Number` type; `Math` is the *operations*, not the value type

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO (mild scope question only)

**"Math" is essentially unambiguous:**

"Math"/"mathematics" refers to the discipline of numbers, quantities, and their operations. The only real decision is *scope*: use the general word for the field of mathematics, not a word for one branch (e.g. "arithmetic," "geometry") and not a word for a single operation.

**Your translation should:**

- Use the noun for the field of "mathematics"
- Avoid narrowing to one branch (arithmetic/algebra/geometry)
- Avoid the "a number" or "a calculation" senses — `Math` is the facility, not a value or a single act

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `Math`, check these translations:**

- [ ] `console` - Also a global namespace noun; keep both as facility nouns of the same register
- [ ] `Number` - The numeric *type*; keep it distinct from `Math` (the operations toolbox)
- [ ] `Math.floor` / `Math.max` members - The methods live *inside* `Math`; the noun should read naturally before a dotted method

**Consistency rule:**

`Math` and `console` are both names of facilities and should read as nouns of one consistent technical register. Do not translate `console` as a formal coinage and `Math` as a casual word (or vice versa). Keep `Math` clearly separate from `Number`: one is the operations toolbox, the other is the value type.

### Functional relationships

**This term works WITH:**

1. **`Math` + member**: the `receiver.member(...)` math call

```javascript
Math.round(2.5); // 3
```

**Common pairing:**

```javascript
// Math is where beginners reach for numeric helpers
let value = -9;
let magnitude = Math.abs(value); // 9
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** Every language has a settled academic word for "mathematics," so the core concept is stable. The difficulty is role-fit: `Math` is a *namespace/facility*, not the field studied in school and not the `Number` type, so the translator must keep it a facility noun consistent with `console` and distinct from `Number`. Whether to use the full academic word or a common short form is a judgment worth flagging.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the MATH TOOLBOX / namespace (not a single operation, not a number)?
- [ ] Would a native speaker understand this names where math helpers live?
- [ ] Avoids narrowing to one branch of mathematics?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun, not verb)?
- [ ] Correct form (facility noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization sense preserved (`Math` is a global object)?

### 3. Consistency

- [ ] Matches the pattern of other namespace objects (`console`)?
- [ ] Same noun register as similar builtins?
- [ ] Kept distinct from `Number` (type vs. operations toolbox)?

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
term: Math
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term names the mathematics facility/namespace in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and note that it stays distinct from the `Number` type and consistent with `console`.

**Alternatives considered:**

List the candidate terms weighed (full academic word vs. short form, any branch-specific words rejected) and why.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (full word vs. short form, facility-noun fit) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
