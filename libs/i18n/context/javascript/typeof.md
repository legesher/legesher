# JavaScript Keyword: `typeof` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** operator (unary)
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** MEDIUM

---

## Quick Summary

The `typeof` keyword is a unary operator that returns a *string* naming the type of a value — `"string"`, `"number"`, `"boolean"`, `"object"`, `"undefined"`, and so on. It inspects a value and reports its type; it never changes or converts anything.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Ask for the type of a value; get back a string
typeof 42;        // "number"
typeof "hello";   // "string"
typeof true;      // "boolean"
```

**What this does:** `typeof` looks at each value and returns a string that names its type. The value itself is untouched.

### Example 2: Common Pattern

```javascript
// Guard: only proceed if x is a string
function greet(x) {
  if (typeof x === "string") {
    return "Hi, " + x;
  }
  return "Not a name";
}
```

**What this does:** `typeof x === "string"` checks the type of `x` before using it. `typeof` reports; the `if` decides.

### Example 3: Edge Case

```javascript
// typeof INSPECTS — it does not convert or modify the value
let n = 7;
let t = typeof n;   // t is the string "number"
// n is still the number 7, unchanged
```

**What this shows:** `typeof` produces a *description* of the value's type as a string. It reads, it never writes: `n` remains the number `7`.

---

## Pattern Classification

**This term is:** TYPE-INSPECTION OPERATOR KEYWORD

**Similar terms in this pattern:**

1. `new` - Also a unary prefix operator, but it *constructs* an object; `typeof` merely *inspects*
2. `let` - Appears in the same code; `typeof` reads a value while `let` names one
3. `const` - Like `let`, introduces a name; `typeof` reports on a value's type without altering it

**Pattern rule:** `typeof` is an *inspection* operator — a verb-or-phrase meaning "the type of / what type is." Its translation must convey *querying/reporting a type*, never *setting* or *converting* one. It is a prefix operator applied to the value that follows it.

---

## Etymology (Brief)

**English Origin:** Compound — "type" (Latin/Greek *typus/typos*, "impression, form, kind") + "of" (Germanic, possessive/relational particle).

**Root meaning:** "the type of ___" — the kind or category that a thing belongs to. "Type" here means classification (string, number, …); "of" links it to the value being classified.

**Why JavaScript uses this:** `typeof x` reads directly as English "the type of x." The compound keyword asks the language to report which category a value belongs to and hands back that category's name as a string. It is a question, not a command.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`typeof` is a unary prefix operator that evaluates the expression to its right and returns a *string* naming that expression's type. The possible strings are a small fixed set — `"number"`, `"string"`, `"boolean"`, `"undefined"`, `"object"`, `"function"`, and a couple of others. The result is always a string, and the operand is never modified.

The defining behavior is *inspection without side effects*. `typeof` does not convert a value from one type to another, and it does not change the value it examines. It only reports. This is the crucial distinction for translation: the word must read as "query / report the type," not as "cast / convert / set the type." A learner who reads it as a conversion will misunderstand the code.

Because the result is a plain string, `typeof` is most often used in comparisons — `typeof x === "string"` — to branch on what kind of value is in hand. The keyword answers a question ("what type is this?"); it never performs an action on the value beyond looking at it.

**Key behaviors:**

1. **Returns a string:** The result is a string naming the type, e.g. `"number"`.
2. **Inspects only:** It reads the value's type; it never converts or mutates the value.
3. **Prefix operator:** It attaches to the value that follows it (`typeof value`).
4. **One historic quirk:** `typeof null` yields `"object"` — a long-standing JavaScript oddity, not a statement about what `null` means. The translation should not try to encode or repair this; it is behavior, not vocabulary.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Unary inspection operator (prefix) — "the type of the following value"
- **Action vs State:** ACTION (a query action) - it reports a type, but performs no change
- **Temporal aspect:** One-time evaluation — a single lookup that yields a string

### Recommended Form

**Primary recommendation:** Use a short phrase or compound meaning "type-of" or "kind-of" — a *querying* form that reads as "what type is this value." Prefer a noun-relational compound ("type of") or an inspecting verb ("get-type"), matched to how the language would phrase "the category of a thing."

**Forms to AVOID:**

- ❌ A *converting* sense ("cast to type / make it a …") - `typeof` never converts (see Ambiguity Resolution)
- ❌ A *setting* sense ("assign the type") - it reads, it does not write
- ❌ Rendering only "type" and dropping the "of" relation, if that loses the "type *of this value*" meaning in the target grammar

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Type" as in *typing on a keyboard* (entering characters)
- ❌ Meaning 2: "Type" as a verb meaning *convert/cast* to a type (set the type)
- ✅ Meaning 3: **"THE TYPE / KIND OF a value"** — inspect and report its category as a string

**Example:**

English "type" can mean:

1. "**Type** your password" (press keys — verb) ❌
2. "**Type** the value as a number" (convert/cast — verb) ❌
3. "What is the **type of** this value?" (its category — the `typeof` sense) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: querying the *kind/category* of a value and returning its name, NOT keyboard-typing and NOT converting.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `typeof`, check these translations:**

- [ ] `new` - The other unary prefix operator; `new` constructs, `typeof` inspects — keep the contrast clear
- [ ] `let` - Appears alongside in guards; ensure `typeof` reads as *query*, not *declare*
- [ ] `const` - Same: `typeof` reports a type, it does not name or fix a binding

**Consistency rule:**

`typeof` is an *inspection* operator and must be distinct from operators that *act on* values. `new` builds, `let`/`const` name, `typeof` merely reports. If the "type of" query blurs into a "convert" or "set" verb, code that only inspects will read as code that changes data. Keep the querying sense sharp.

**Example:**

If you translate `new` as a construction verb ("build-instance"), then:

- `typeof` should be an inspecting phrase ("type-of / kind-of"), clearly a *question*, not a construction or conversion
- NOT: `typeof` rendered as "convert to type," which implies an action on the value (❌)

### Functional relationships

**This term works WITH:**

1. **`typeof` + comparison**: The canonical type guard

```javascript
if (typeof x === "number") {
  // x is safe to use as a number
}
```

2. **`typeof` + a variable**: Report a value's type into a name

```javascript
const kind = typeof value; // e.g. "boolean"
```

**Common pairing:**

```javascript
// typeof reports; let/const hold the reported string
const t = typeof 3.14; // "number"
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The concept (report a value's type as a string) is clear, but two traps exist: the word "type" also means keyboard-typing and can suggest type *conversion*. The translator must choose an *inspection* sense ("the type/kind of") and render the "of" relation so it reads as "the type of this value." The risk is a converting or keyboard sense sneaking in, or dropping the relational "of."

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (inspect and report a value's type as a string)
- [ ] Would a native speaker read it as "the type/kind of this value"?
- [ ] Avoids the "keyboard-typing" and "convert/cast" senses?

### 2. Linguistic Correctness

- [ ] Correct part of speech (inspecting query, not a converting verb)?
- [ ] Correct form (prefix operator; preserves the "of" relation if needed)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language (lowercase for JS keywords)?

### 3. Consistency

- [ ] Distinct from construction/declaration keywords (`new`, `let`, `const`)?
- [ ] Reads as *inspect/report*, not *set* or *convert*?
- [ ] Aligns with related terms (checked cross-references)?

### 4. Usability

- [ ] Short enough (ideally one compact word/compound)?
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
term: typeof
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries the "the type/kind of a value, returned as a string" concept in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and why it reads as inspection, not conversion.

**Alternatives considered:**

List the candidate terms weighed in the target language and why each was rejected or kept, noting any that drifted toward the keyboard-typing or convert/cast senses.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (keyboard-vs-category ambiguity, convert-sense risk, the "of" relation, competing regional conventions) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
