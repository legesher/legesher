# JavaScript Builtin: `RegExp` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** object (global constructor)
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** HARD

---

## Quick Summary

`RegExp` is the global constructor for *regular expressions* — pattern objects that describe and match text (e.g. "any run of digits"). It is invoked as `new RegExp("...")`, or via the literal form `/.../`. In JEJ it names the pattern-matching facility that scans and tests strings.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Build a pattern that matches one or more digits
let digits = new RegExp("[0-9]+");
```

**What this does:** Calls the `RegExp` constructor with a pattern string and produces a regular-expression object stored in `digits`.

### Example 2: Common Pattern

```javascript
// Test whether text matches the pattern
let pattern = new RegExp("cat");
console.log(pattern.test("concatenate"));   // true
```

**What this does:** Uses a `RegExp` object's matching behavior to check whether `"cat"` occurs inside the target string.

### Example 3: Edge Case

```javascript
// The /.../ literal builds the same kind of object as new RegExp(...)
let a = /cat/;
let b = new RegExp("cat");
// a and b are both regular-expression objects
```

**What this shows:** `RegExp` names the *type* of pattern object. The `/.../ ` literal and `new RegExp(...)` are two ways to create one — translating `RegExp` names the concept behind both.

---

## Pattern Classification

**This term is:** TYPE CONSTRUCTOR (global object name)

**Similar terms in this pattern:**

1. `Date` - Also a global constructor built with `new`, naming a value type
2. `BigInt` - Also a global naming a specialized value type
3. `console` / `Math` - Also global object names, though facilities rather than constructors

**Pattern rule:** Global constructors (`RegExp`, `Date`, `BigInt`) are *names of types/things you create*. Translate them as nouns naming the kind of object, consistent with each other, never as verbs.

---

## Etymology (Brief)

**English Origin:** Latin (compound coinage)

**Root meaning:** "Regular" from Latin *regula* ("rule"); "expression" from *exprimere* ("to press out, express"). A *regular expression* is a rule-governed way of expressing a text pattern — a term inherited from formal-language theory (Kleene, 1950s).

**Why JavaScript uses this:** JS borrowed the established computer-science term "regular expression," abbreviating the constructor to `RegExp`. The name signals "a formal pattern for matching text," carrying decades of prior art.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`RegExp` is a global constructor that creates *regular-expression* objects: compact, rule-based descriptions of text patterns. A pattern such as "one or more digits" or "starts with a capital letter" is encoded once as a `RegExp` and then used to test, search, or extract from strings. JavaScript offers two creation forms — the `/pattern/` literal and `new RegExp("pattern")` — both yielding the same kind of object.

In the JEJ teaching subset, `RegExp` names the pattern-matching facility. Learners meet it when simple string methods are not enough and they need to describe a *shape* of text rather than an exact substring. The term is technical and comes straight from formal-language theory, so it carries a precise, established meaning that predates JavaScript.

Conceptually, `RegExp` is a *noun naming a type of object* — the pattern — not an action. The verbs (`test`, `match`) live on the objects and strings that use it. Because the concept is technical and abbreviated, many languages loan the term or transliterate it rather than coining a fully native word.

**Key behaviors:**

1. **Names a value type:** A `RegExp` object *is* a pattern; it is a thing, not an operation.
2. **Two creation forms:** `/.../ ` literal and `new RegExp(...)` build the same object.
3. **Used for matching:** Its purpose is testing/searching text, but that behavior lives in its methods.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Proper-noun-like name for the regular-expression type
- **Action vs State:** STATE/thing - names a kind of object, does not perform an action
- **Temporal aspect:** None - it is a persistent type name

### Recommended Form

**Primary recommendation:** Translate as a noun naming "regular expression / text-pattern" — the established technical term. Keep it a compact technical noun consistent with the other global constructors (`Date`, `BigInt`). An accepted loan or transliteration is legitimate if the target CS community already uses one.

**Forms to AVOID:**

- ❌ A verb like "match / search" - those are the operations, not the type name
- ❌ The everyday "expression" (facial/verbal) sense - wrong meaning entirely
- ❌ A word for "regular / normal" alone - loses the "pattern" half of the compound

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Expression" as a spoken phrase or facial look
- ❌ Meaning 2: "Regular" as "normal / ordinary / recurring"
- ✅ Meaning 3: **"REGULAR EXPRESSION — A FORMAL TEXT PATTERN"** the compound technical term

**Example:**

English "expression" can mean:

1. "A cheerful **expression** on her face" (a look) ❌
2. "A common **expression** in French" (a phrase) ❌
3. "A **regular expression** matches phone numbers" (formal text pattern) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: the formal, rule-based text-matching pattern from computer science, treated as a single technical compound — not "regular" and "expression" translated separately by their everyday senses.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `RegExp`, check these translations:**

- [ ] `Date` - Also a global constructor noun; keep both as type-naming nouns of one register
- [ ] `BigInt` - Also a global constructor for a technical value type; consistent noun treatment
- [ ] `console` / `Math` - Other global object names; same technical register

**Consistency rule:**

`RegExp`, `Date`, and `BigInt` are all names of types/facilities created or used by the program. Treat them as a consistent set of technical nouns. If `Date` gets a native noun but `RegExp` a raw English loan with no rationale, the register is inconsistent — decide loan-vs-native per the community norm and apply it evenly.

### Functional relationships

**This term works WITH:**

1. **`RegExp` + `new`**: Constructing a pattern object

```javascript
let p = new RegExp("[a-z]+");
```

**Common pairing:**

```javascript
// A RegExp used to test a string
let hasDigit = new RegExp("[0-9]");
console.log(hasDigit.test("a1b"));   // true
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

**For this term:** HARD

**Rationale:** "Regular expression" is a technical compound from formal-language theory with no everyday equivalent; translating "regular" and "expression" by their common senses would be badly misleading. Many languages loan or transliterate the term, and CS communities differ on the accepted form. Choosing between an established loan and a native compound is a genuine judgment call — flag for a native reviewer familiar with the local CS vocabulary.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (a formal text-matching pattern)
- [ ] Would a native speaker read this as the CS "regular expression," not "a facial expression"?
- [ ] Avoids splitting the compound into everyday "regular" + "expression"?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun naming a type, not a verb)?
- [ ] Correct form (technical noun / accepted loan)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language (`RegExp` case preserved in JS)?

### 3. Consistency

- [ ] Matches the pattern of other global constructors (`Date`, `BigInt`)?
- [ ] Same technical register as similar builtins?
- [ ] Aligns with related terms (checked cross-references)?

### 4. Usability

- [ ] Short enough (1-2 words, or an accepted abbreviation)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember for learners?

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
term: RegExp
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term names the "regular expression" text-pattern type in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and note whether you chose an established loan/transliteration or a native compound.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any rejected for using everyday "expression."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (technical compound, loan-vs-native, community variation) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
