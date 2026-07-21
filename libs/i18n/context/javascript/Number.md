# JavaScript Builtin: `Number` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** object (global constructor / type name)
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** MEDIUM

---

## Quick Summary

`Number` is the global object that names JavaScript's single numeric type and, called as `Number(x)`, converts a value into a number. JavaScript has no separate integer and floating-point types — `Number` covers both whole numbers and decimals.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Convert text to a number
let n = Number("42"); // 42
```

**What this does:** Calls the global `Number` object as a function to turn the text `"42"` into the numeric value `42`, ready for arithmetic.

### Example 2: Common Pattern

```javascript
// Both whole and decimal values are the same type
let count = Number("7");      // 7
let price = Number("3.14");   // 3.14
let total = count * price;    // 21.98
```

**What this does:** Shows that `Number` produces one numeric type covering whole numbers and decimals alike — there is no int/float split. The results mix freely in arithmetic.

### Example 3: Edge Case

```javascript
// Number names the type; it is NOT a parser that stops at bad characters
Number("42px"); // NaN  — the whole value must be numeric
Number("");     // 0
```

**What this shows:** `Number(x)` converts the *entire* value; if any part is non-numeric it yields `NaN` (not-a-number). This distinguishes it from `parseInt`/`parseFloat`, which read as many leading digits as they can and ignore the rest.

---

## Pattern Classification

**This term is:** GLOBAL OBJECT (type name / constructor)

**Similar terms in this pattern:**

1. `String` - Also a capitalized global naming a primitive type and converting to it (`String(x)`)
2. `Boolean` - Also a capitalized global naming a primitive type and converting to it (`Boolean(x)`)
3. `Math` - Also a capitalized global object, though a namespace of math methods rather than a type

**Pattern rule:** Capitalized global type objects (`Number`, `String`, `Boolean`) name value *categories*. Translate them as nouns naming the type, kept consistent with each other in noun form and register.

---

## Etymology (Brief)

**English Origin:** Latin → French

**Root meaning:** From Latin *numerus* ("number, quantity"), via Old French *nombre*. The plainest possible word for a counted or measured quantity.

**Why JavaScript uses this:** Because JavaScript has only one numeric type, it names it with the broadest term — `Number` — rather than splitting into `int`/`float` as many languages do. The single name signals "any numeric value, whole or fractional."

---

## Concept Explanation (Intermediate Level)

**What it does:**

`Number` names JavaScript's numeric type. Crucially, JavaScript does **not** separate integers from floating-point numbers the way Python (`int` vs `float`) or C do. There is one type — `Number` — and `7`, `-3`, and `3.14` are all values of it. Internally every number is an IEEE 754 double-precision float, but the learner simply sees "numbers."

As a converter, `Number(x)` turns a value into a number: `Number("42")` → `42`, `Number("3.14")` → `3.14`, `Number(true)` → `1`, `Number("")` → `0`. Unlike `parseInt`/`parseFloat`, it converts the value *as a whole* — `Number("42px")` is `NaN` because the whole text is not a clean number. This all-or-nothing behavior is the key contrast a learner must grasp.

Conceptually, `Number` names a *category of values* (numbers) and, secondarily, the *tool that produces a number from another value*. It is capitalized because it is a global object, one of the small family (`Number`, `String`, `Boolean`) naming JavaScript's primitive types.

**Key behaviors:**

1. **One numeric type:** No int/float split — whole numbers and decimals are both `Number`. This differs from languages with separate integer and float types.
2. **Whole-value conversion:** `Number(x)` converts the entire value; any non-numeric part yields `NaN`. It is not a lenient parser.
3. **Capitalized global:** `Number` (uppercase) is the global object; it is distinct from the lowercase numeric values it describes and produces.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Noun naming a value type (and the converter that yields it)
- **Action vs State:** STATE/CATEGORY — names what a value IS (a number), not an action
- **Temporal aspect:** Timeless — a type is a permanent classification

### Recommended Form

**Primary recommendation:** Use your target language's general mathematical noun for "number" — the everyday, unqualified word for a numeric quantity. Because JavaScript has no int/float split, do **not** pick a word that means specifically "integer" or specifically "decimal"; choose the broad term that covers both. Keep it a noun, consistent with `String` and `Boolean`.

**Forms to AVOID:**

- ❌ A verb form ("to count / to number") — this names a type, not an action
- ❌ A word meaning specifically "integer / whole number" — too narrow; `Number` includes decimals
- ❌ A word meaning specifically "decimal / floating-point" — too narrow; `Number` includes whole numbers

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (mild)

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: A numeral/digit glyph (the written symbol "7")
- ❌ Meaning 2: "A number of things" (a vague quantity/amount, as in "a number of people")
- ✅ Meaning 3: **A NUMERIC VALUE** — the mathematical quantity a program computes with (whole or fractional)

**Example:**

English "number" can mean:

1. "Write the number 7" (the digit glyph) ⚠️ (related but this is the symbol)
2. "A number of guests arrived" (a vague count) ❌
3. "Store the total as a number" (a numeric value for computation) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: a numeric value used in computation, covering both whole numbers and decimals.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `Number`, check these translations:**

- [ ] `String` - Also a capitalized global type name; keep both as type nouns of one register
- [ ] `Boolean` - Also a capitalized global type name; consistent noun treatment
- [ ] `parseInt` / `parseFloat` - Produce `Number` values from text; the "number" idea should align

**Consistency rule:**

All capitalized global type objects (`Number`, `String`, `Boolean`) name value categories and should read as nouns of one consistent technical register. Because `parseInt` and `parseFloat` both produce a `Number`, the numeric noun chosen here should be recognizable in those parsers' briefs. Do not encode "integer" into `Number`; keep it the broad numeric noun.

### Functional relationships

**This term works WITH:**

1. **`Number` + a value**: converting a value to a number

```javascript
Number("3.14"); // 3.14
```

**Common pairing:**

```javascript
// Convert user text to a number before arithmetic
let entered = "20";
let doubled = Number(entered) * 2; // 40
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** "Number" as a concept is universal, but the JavaScript twist raises the difficulty: it is one type covering both whole and fractional values, so a translator must resist words meaning specifically "integer" or "decimal" and choose the broad numeric noun. Some languages' most natural math word leans toward one sense; getting the *unqualified* term right is a real judgment worth a native reviewer's eye.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures a NUMERIC VALUE (whole *and* fractional), not just "integer"?
- [ ] Would a native speaker understand this names the number type / number converter?
- [ ] Avoids the "digit glyph" and "vague quantity" senses?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun, not verb)?
- [ ] Correct form (broad numeric noun, not narrowed to int or decimal)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization sense preserved (`Number` is a global object)?

### 3. Consistency

- [ ] Matches the pattern of other type names (`String`, `Boolean`)?
- [ ] Same noun register as similar builtins?
- [ ] Aligns with the "number" produced by `parseInt`/`parseFloat`?

### 4. Usability

- [ ] Short enough (1-2 words)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (standard math term)?

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
term: Number
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term names the single numeric type — covering whole and fractional values — in the target language, grounded in this brief's Concept Explanation and Ambiguity Resolution. Confirm it is the broad numeric noun, not a word for "integer" or "decimal."

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept — especially any that leaned too narrowly toward integer or decimal.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (breadth of the numeric noun, int/float neutrality) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
