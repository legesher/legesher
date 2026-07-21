# JavaScript Builtin: `Boolean` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** object (global constructor / type name)
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** EASY

---

## Quick Summary

`Boolean` is the global object that names JavaScript's true/false type and, called as `Boolean(x)`, converts any value into `true` or `false`. It is named after mathematician George Boole and is capitalized because it is a global object.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Convert a value to true or false
let flag = Boolean(1); // true
```

**What this does:** Calls the global `Boolean` object as a function to reduce the value `1` to the truth value `true`.

### Example 2: Common Pattern

```javascript
// Truthiness: which values count as false
Boolean(0);   // false
Boolean("");  // false
Boolean("hi"); // true
```

**What this does:** Shows JavaScript's truthiness rules through the `Boolean` converter: `0`, empty text, `null`, `undefined`, and `NaN` become `false`; almost everything else becomes `true`.

### Example 3: Edge Case

```javascript
// Boolean names the type; true and false are its two values
let a = true;            // a boolean value
let b = Boolean("x");    // Boolean() called as a converter -> true
```

**What this shows:** `Boolean` (capitalized) is the *name of the type / the converter object*, while `true` and `false` are the two actual values of that type. Translating `Boolean` names the category, not the values `true`/`false`.

---

## Pattern Classification

**This term is:** GLOBAL OBJECT (type name / constructor)

**Similar terms in this pattern:**

1. `String` - Also a capitalized global naming a primitive type and converting to it (`String(x)`)
2. `Number` - Also a capitalized global naming a primitive type and converting to it (`Number(x)`)
3. `Array` - Also a capitalized global object naming a built-in type

**Pattern rule:** Capitalized global type objects (`Boolean`, `String`, `Number`) name value *categories*. Translate them as nouns naming the type, kept consistent with each other in noun form and register.

---

## Etymology (Brief)

**English Origin:** Proper name (George Boole) + suffix

**Root meaning:** "Boolean" derives from George Boole (1815–1864), the English mathematician who founded the two-valued algebra of logic. The suffix "-ean" means "relating to" — so "Boolean" means "of Boole's logic," i.e. true/false logic.

**Why JavaScript uses this:** "Boolean" is the universal computer-science term for the true/false type, adopted from Boolean algebra. JavaScript spells it in full and capitalizes it as a global object.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`Boolean` names JavaScript's logical type — the type whose only two values are `true` and `false`. This type underlies every condition, comparison, and branch: an `if` test, a `while` loop, and comparisons like `a < b` all resolve to a boolean.

As a converter, `Boolean(x)` reduces any value to `true` or `false` using JavaScript's *truthiness* rules. The "falsy" values are few and worth memorizing: `false`, `0`, `""` (empty text), `null`, `undefined`, and `NaN`. Everything else — any non-empty text, any non-zero number, any object or array — is "truthy" and converts to `true`. Beginners use `Boolean(x)` to make this conversion explicit, though JavaScript also applies it automatically inside conditions.

Conceptually, `Boolean` names a *category of values* (the two truth values) and, secondarily, the *tool that produces a truth value from any input*. It is capitalized because it is a global object, one of the family (`Boolean`, `String`, `Number`) naming JavaScript's primitive types.

**Key behaviors:**

1. **Exactly two values:** the boolean type holds only `true` and `false`; these are the values, while `Boolean` is the type's name.
2. **Truthiness conversion:** `Boolean(x)` maps the few falsy values to `false` and everything else to `true` — the rule behind every `if`.
3. **Capitalized global:** `Boolean` (uppercase) is the global object; it is distinct from the lowercase values `true`/`false` it describes and produces.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Noun (adjective-derived) naming a value type
- **Action vs State:** STATE/CATEGORY — names what a value IS (a truth value), not an action
- **Temporal aspect:** Timeless — a type is a permanent classification

### Recommended Form

**Primary recommendation:** Use your target language's established CS term for the boolean type — commonly a transliteration of "Boolean" (honoring George Boole) or the native word for "logical." Keep it a noun, consistent with `String` and `Number`.

**Forms to AVOID:**

- ❌ Using the values "true/false" as the type name — those are the *values*, not the type
- ❌ "binary" — related but means base-2 numbers, not the logical type
- ❌ "bit" — that is a storage unit, not the logical type

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO

**"Boolean" is unambiguous:**

"Boolean" refers specifically to George Boole's two-valued logic and, in computing, to the true/false data type. It has no unrelated everyday meanings.

**Your translation should:**

- Honor George Boole's name (transliteration is common and accepted), OR
- Use the native word for "logical" if that is the CS-education standard
- Capture the two-valued (true/false) type, not just the values themselves

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `Boolean`, check these translations:**

- [ ] `String` - Also a capitalized global type name; keep both as type nouns of one register
- [ ] `Number` - Also a capitalized global type name; consistent noun treatment
- [ ] `true` / `false` - The two values of the boolean type; should feel related to it

**Consistency rule:**

All capitalized global type objects (`Boolean`, `String`, `Number`) name value categories and should read as nouns of one consistent technical register. The chosen word should relate to `true`/`false` (its values) without *being* one of them.

### Functional relationships

**This term works WITH:**

1. **`Boolean` + a value**: converting a value to `true`/`false`

```javascript
Boolean("non-empty"); // true
```

**Common pairing:**

```javascript
// Make a truthiness check explicit
let name = "";
let hasName = Boolean(name); // false
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

**For this term:** EASY

**Rationale:** Boolean logic is universal in computer science, and "Boolean" (after George Boole) is recognized worldwide. Most languages either transliterate the name or use their word for "logical," both well documented. The only minor choice is transliteration vs. native "logical," which follows local CS-education convention.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the TRUE/FALSE logical type (not the values themselves)?
- [ ] Would a native speaker understand this names the boolean type / boolean converter?
- [ ] Avoids "binary"/"bit" confusion?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun / adjective-as-noun)?
- [ ] Correct form (type noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization sense preserved (`Boolean` is a global object)?

### 3. Consistency

- [ ] Matches the pattern of other type names (`String`, `Number`)?
- [ ] Same noun register as similar builtins?
- [ ] Relates to `true`/`false` without being one of them?

### 4. Usability

- [ ] Short enough (1-2 words)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (standard CS term)?

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
term: Boolean
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term names the true/false logical type (and its converter) in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and note whether you transliterated "Boolean" or used a native word for "logical."

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (transliteration vs. native "logical," regional convention) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
