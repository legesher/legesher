# JavaScript Keyword: `let` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** declaration
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes (keyword 1 of 16)
**Difficulty:** MEDIUM

---

## Quick Summary

The `let` keyword declares a block-scoped variable that can be reassigned later. It introduces a name into the current block and binds it to a value, unlike `const`, whose binding cannot be reassigned after declaration.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Declare a variable and give it a starting value
let count = 0;
count = count + 1;
```

**What this does:** Introduces the name `count`, binds it to `0`, then reassigns it to `1`. `let` permits the later reassignment.

### Example 2: Common Pattern

```javascript
// A loop counter that changes on every pass
let total = 0;
for (let i = 0; i < 3; i = i + 1) {
  total = total + i;
}
```

**What this does:** `let total` holds a running sum that is rebound each iteration; `let i` declares the loop variable, scoped to the loop.

### Example 3: Edge Case

```javascript
// Block scope: the inner `let` does not leak out
let name = "outer";
if (true) {
  let name = "inner";
}
// here, name is still "outer"
```

**What this shows:** A `let` binding lives only inside the `{ }` block where it is declared. The inner `name` is a separate variable that disappears when the block ends.

---

## Pattern Classification

**This term is:** DECLARATION KEYWORD

**Similar terms in this pattern:**

1. `const` - Also a declaration keyword; introduces a name, but forbids reassignment
2. `new` - Also introduces/constructs a value, though it creates objects rather than bindings
3. `typeof` - Operates on a value like `let` operates on a name, but inspects rather than declares

**Pattern rule:** Declaration keywords should use a verb of *allowing / assigning / letting-be* in the target language, consistent with `const`. The pair `let`/`const` must read as a matched contrast (reassignable vs. fixed), so translate them as a set, not in isolation.

---

## Etymology (Brief)

**English Origin:** Germanic

**Root meaning:** Old English *lǣtan* — "to allow, to permit, to leave (something to be)." The mathematical "let x = 5" ("suppose/allow x to be 5") sense entered English through algebra and carried into programming.

**Why JavaScript uses this:** `let` was added in ES6 (ES2015) to give block scope, echoing the mathematician's "let x = …". It reads as "allow this name to stand for this value," deliberately evoking the algebraic convention rather than a command.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`let` creates a new variable binding in the current block scope. The name it introduces can be assigned an initial value and then reassigned any number of times afterward. This distinguishes it from `const`, whose binding is fixed once set.

The binding is scoped to the nearest enclosing `{ }` block — a function body, a loop body, an `if` branch. Outside that block the name does not exist. This is the defining behavioral difference from the older `var` keyword (which is not part of the JEJ subset), whose bindings escape blocks to the whole function.

Because `let` announces intent — "this value will change" — it pairs conceptually with `const` ("this value will not"). A translation that captures "allow / let stand" for `let` while capturing "fixed / constant" for `const` preserves the contrast a learner relies on when reading code.

**Key behaviors:**

1. **Reassignable:** The name may be given a new value after declaration; `const` may not.
2. **Block-scoped:** The binding exists only within the enclosing `{ }` block, and is not visible outside it.
3. **Declaration, not value:** `let` performs an action on a *name* (it declares), it does not itself evaluate to anything.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Declaration operator introducing a mutable binding
- **Action vs State:** ACTION - it declares/allows a name to exist and hold a value
- **Temporal aspect:** One-time at the point of declaration, but announces future change

### Recommended Form

**Primary recommendation:** Use a short verb meaning "let/allow (a name) to be" or "assign," in the same grammatical form chosen for `const`. Favor the algebraic "let x be" sense — permitting a name to stand for a value — over "let" as in "release."

**Forms to AVOID:**

- ❌ "Release / set free" sense of *let* - this is the wrong meaning (see Ambiguity Resolution)
- ❌ "Rent / lease" sense of *let* - unrelated homonym in some English registers
- ❌ A noun form - `let` is a declaring action, not a thing

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Allow to leave / release" ("let the dog out")
- ❌ Meaning 2: "Rent out" ("flat to let" — British usage)
- ✅ Meaning 3: **"ALLOW (a name) TO STAND FOR (a value)"** — the algebraic "let x = 5"

**Example:**

English "let" can mean:

1. "**Let** the dog out" (permit to leave) ❌
2. "Flat to **let**" (rent) ❌
3. "**Let** x = 5" (suppose/assign in mathematics) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: the mathematical "let x be," NOT release or rent.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `let`, check these translations:**

- [ ] `const` - Must be its matched contrast; same grammatical form, opposite mutability sense
- [ ] `new` - Another value-introducing keyword; keep declaration verbs consistent
- [ ] `typeof` - Also operates in declaration-adjacent code; keep register consistent

**Consistency rule:**

`let` and `const` are a pair and must be translated together. If `let` uses a verb form, `const` uses the same verb form modified for "fixed/unchanging." A learner reads them side by side every day; a mismatch in form obscures that they are two settings of the same idea.

**Example:**

If you translate `let` as a verb "allow-to-be," then:

- `const` should be the same verb family marked as fixed ("fix-to-be" / "constant")
- NOT: `let` as a verb + `const` as an unrelated noun (inconsistent ❌)

### Functional relationships

**This term works WITH:**

1. **`let` + assignment**: Declaration followed by rebinding

```javascript
let score = 0;
score = 10;
```

2. **`let` + `for`**: The canonical loop-counter declaration

```javascript
for (let i = 0; i < 5; i = i + 1) {
  // i is scoped to this loop
}
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

**Rationale:** The concept (a reassignable binding) is universal, but the English word `let` is a homonym whose everyday senses ("release," "rent") are wrong here. The translator must select the mathematical "let x be" sense and keep it paired in form with `const`. The risk is choosing a natural-but-wrong sense of "let," so context and the `const` pairing matter.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (declare a reassignable binding, not "release")
- [ ] Would a native speaker understand this introduces a changeable variable?
- [ ] Avoids the "release / rent" connotations?

### 2. Linguistic Correctness

- [ ] Correct part of speech (declaring verb, not noun)?
- [ ] Correct form (matched to `const`)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language (lowercase for JS keywords)?

### 3. Consistency

- [ ] Matches the pattern of other declaration keywords?
- [ ] Same verb form as `const`?
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
term: let
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries the "let x be / allow a name to stand for a value" concept in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution, and matched in form to `const`.

**Alternatives considered:**

List the candidate terms weighed in the target language and why each was rejected or kept, noting any that drifted toward the "release / rent" sense.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (homonym risk, no established native term, competing regional conventions) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
