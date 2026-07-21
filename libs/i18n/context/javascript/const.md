# JavaScript Keyword: `const` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** declaration
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** MEDIUM

---

## Quick Summary

The `const` keyword declares a block-scoped binding that cannot be reassigned after it is set. It introduces a name and fixes it to a value for the life of its scope, forming the matched contrast to `let`, whose binding may be reassigned.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Declare a name and fix it to a value
const limit = 10;
// limit = 20;  // would throw: cannot reassign a const
```

**What this does:** Introduces the name `limit`, binds it to `10`, and forbids any later reassignment. `const` locks the binding.

### Example 2: Common Pattern

```javascript
// A fixed configuration value used but never reassigned
const maxAttempts = 3;
let attempts = 0;
while (attempts < maxAttempts) {
  attempts = attempts + 1;
}
```

**What this does:** `const maxAttempts` names a value that stays fixed, while `let attempts` names one that changes. The two keywords sit side by side, one fixed, one mutable.

### Example 3: Edge Case

```javascript
// const fixes the BINDING, not the contents of an object
const list = [1, 2];
list.push(3);       // allowed — the array is mutated, not rebound
// list = [4, 5];   // NOT allowed — this reassigns the binding
```

**What this shows:** `const` prevents reassigning the name, not changing the object the name points to. The binding is fixed; the value's internals may still change.

---

## Pattern Classification

**This term is:** DECLARATION KEYWORD

**Similar terms in this pattern:**

1. `let` - Also a declaration keyword; introduces a name, but permits reassignment
2. `new` - Also introduces a value, though it constructs an object rather than a binding
3. `typeof` - Operates on a value like `const` operates on a name, but inspects rather than declares

**Pattern rule:** Declaration keywords should use a verb of *fixing / setting / constant-holding* in the target language, consistent with `let`. The pair `let`/`const` must read as a matched contrast (reassignable vs. fixed), so translate them as a set, not in isolation.

---

## Etymology (Brief)

**English Origin:** Latin (via English "constant")

**Root meaning:** Latin *constāns* — "standing firm, unchanging," from *con-* ("together") + *stāre* ("to stand"). English "constant" preserves the sense of something that does not vary.

**Why JavaScript uses this:** `const` was added in ES6 (ES2015) alongside `let` to declare a binding that stays fixed. The abbreviation of "constant" signals to a reader that the name, once set, will not be reassigned — the deliberate opposite of the mutable `let`.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`const` creates a new binding in the current block scope and forbids reassigning it. The name must be given a value at declaration, and that name cannot be pointed at a different value afterward. This is the defining behavioral difference from `let`, whose binding may be reassigned freely.

The binding is scoped to the nearest enclosing `{ }` block — a function body, a loop body, an `if` branch — exactly like `let`. Outside that block the name does not exist. The only distinction between the two keywords is mutability: `const` fixes, `let` allows change.

A common point of confusion: `const` fixes the *binding*, not the *value*. If a `const` holds an array or object, that array or object may still be mutated internally; what is forbidden is reassigning the name to a new value. A good translation captures "fixed / constant name," not "frozen / immutable data."

**Key behaviors:**

1. **Not reassignable:** The name cannot be given a new value after declaration; `let` may.
2. **Block-scoped:** The binding exists only within the enclosing `{ }` block, like `let`.
3. **Must be initialized:** A `const` requires a value at the point of declaration.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Declaration operator introducing a fixed binding
- **Action vs State:** ACTION - it declares/fixes a name to hold a value
- **Temporal aspect:** One-time at the point of declaration, permanent thereafter

### Recommended Form

**Primary recommendation:** Use a short verb or verb-derived form meaning "fix / set constant / bind-unchanging," in the same grammatical form chosen for `let`. The word must read as the fixed counterpart of `let` so a learner sees the pair as two settings of one idea.

**Forms to AVOID:**

- ❌ "Immutable data / frozen" sense - `const` fixes the binding, not the value's contents (see Ambiguity Resolution)
- ❌ "Constant" as a physics/math noun disconnected from the act of declaring - keep it a declaring form matched to `let`
- ❌ A form unrelated to the `let` translation - the pair must share a family

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Immutable / frozen data" (the contents cannot change)
- ❌ Meaning 2: "Constant" as an abstract mathematical value (like π)
- ✅ Meaning 3: **"FIX (a name) TO (a value), forbidding reassignment"** — a binding that cannot be re-pointed

**Example:**

English "const(ant)" can suggest:

1. "The data is **constant** / frozen" (contents cannot change) ❌
2. "A physical **constant**" (a fixed number in a formula) ❌
3. "**const** limit = 10" (this name cannot be reassigned) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: a name whose binding is fixed, NOT the claim that the underlying data is immutable.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `const`, check these translations:**

- [ ] `let` - Must be its matched contrast; same grammatical form, opposite mutability sense
- [ ] `new` - Another value-introducing keyword; keep declaration verbs consistent
- [ ] `typeof` - Also appears in declaration-adjacent code; keep register consistent

**Consistency rule:**

`const` and `let` are a pair and must be translated together. If `let` uses a verb form, `const` uses the same verb form modified for "fixed/unchanging." A learner reads them side by side every day; a mismatch in form obscures that they are two settings of the same idea.

**Example:**

If you translate `let` as a verb "allow-to-be," then:

- `const` should be the same verb family marked as fixed ("fix-to-be" / "constant")
- NOT: `let` as a verb + `const` as an unrelated noun (inconsistent ❌)

### Functional relationships

**This term works WITH:**

1. **`const` + a fixed value**: Naming something that never changes

```javascript
const pi = 3.14159;
```

2. **`const` + object mutation**: Fixed binding, mutable contents

```javascript
const counts = [];
counts.push(1); // allowed
```

**Common pairing:**

```javascript
// let and const appear together constantly — the mutable/fixed contrast
let attempts = 0;
const maxAttempts = 3;
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The concept (a fixed binding) is universal, but two traps exist: choosing a word that implies the *data* is immutable rather than the *binding* fixed, and failing to match the form to `let`. The translator must select a "fixed name" sense and keep it paired with `let`. The risk is form drift between the two members of the pair.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (fix a binding, not "immutable data")
- [ ] Would a native speaker understand this introduces a name that cannot be reassigned?
- [ ] Avoids implying the value's contents are frozen?

### 2. Linguistic Correctness

- [ ] Correct part of speech (declaring verb/form, not a math noun)?
- [ ] Correct form (matched to `let`)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language (lowercase for JS keywords)?

### 3. Consistency

- [ ] Matches the pattern of other declaration keywords?
- [ ] Same verb form as `let`?
- [ ] Aligns with related terms (checked cross-references)?

### 4. Usability

- [ ] Short enough (1 word ideally)?
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
term: const
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries the "fix a name to a value, forbidding reassignment" concept in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution, and matched in form to `let`.

**Alternatives considered:**

List the candidate terms weighed in the target language and why each was rejected or kept, noting any that drifted toward the "immutable data / frozen" sense instead of "fixed binding."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (immutable-data confusion, form mismatch with `let`, competing regional conventions) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
