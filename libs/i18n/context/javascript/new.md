# JavaScript Keyword: `new` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** operator (construction)
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** HARD

---

## Quick Summary

The `new` keyword constructs an instance from a constructor: `new Date()` builds a fresh Date object, `new RegExp(...)` builds a regular expression. It is the *action of creating/instantiating* an object, not the adjective "new" meaning recent or novel.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Construct a new Date instance representing "now"
const today = new Date();
```

**What this does:** `new Date()` invokes the `Date` constructor and produces a fresh Date object. `new` performs the construction.

### Example 2: Common Pattern

```javascript
// Construct a RegExp from a pattern string
const pattern = new RegExp("\\d+");
const hasDigits = pattern.test("abc123"); // true
```

**What this does:** `new RegExp(...)` builds a regular-expression object from arguments. `new` turns the constructor call into an instance.

### Example 3: Edge Case

```javascript
// WITHOUT new, some constructors misbehave or return the wrong thing.
const a = new Date();   // a Date object
const b = Date();       // a STRING, not a Date — no construction happened
```

**What this shows:** `new` is what triggers construction. Calling the same name without `new` does something entirely different — here it returns a string instead of building an object. The keyword *is* the instantiate action.

---

## Pattern Classification

**This term is:** CONSTRUCTION OPERATOR KEYWORD

**Similar terms in this pattern:**

1. `let` - Also introduces a value into code, but declares a name rather than building an object
2. `const` - Also brings a value into being, but fixes a binding rather than constructing an instance
3. `typeof` - Also a unary operator applied to what follows, but inspects rather than constructs

**Pattern rule:** `new` is a construction verb: "build / create / instantiate an instance of." Its translation must be an *action of making an object*, clearly distinct from the everyday adjective "new" (recent, novel). It is a prefix operator applied to a constructor call.

---

## Etymology (Brief)

**English Origin:** Germanic

**Root meaning:** Old English *nīwe* — "fresh, recently made, not existing before." As an adjective it describes something newly come into being.

**Why JavaScript uses this:** `new` reads as "make a **new** one of these": `new Date()` ≈ "produce a new Date." Though the English word is grammatically an adjective, in JavaScript it functions as a *verb of construction* — the act of bringing a fresh instance into existence. The adjective sense ("freshly made") motivates the keyword, but the operator *does* the making.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`new` is a unary prefix operator placed before a constructor call. It creates a brand-new object, links it to the constructor's prototype, runs the constructor to initialize the object, and evaluates to that object. In short: `new Foo(args)` builds and returns a fresh instance of `Foo`.

The defining behavior is *construction*. Without `new`, the same identifier is just a function call and typically produces something other than an instance (a string, `undefined`, or a thrown error, depending on the constructor). With `new`, JavaScript allocates a new object and hands it back. This is why `new` must be translated as an *action* — it is the verb that performs instantiation.

The translation challenge is that the English word `new` is most familiar as an adjective meaning "recent" or "novel." That is the wrong sense here. In JavaScript, `new` never describes a noun as fresh; it commands the language to *construct* an object. Translators must choose the "create / build / instantiate" verb sense, not the "recent / brand-new" adjective sense.

**Key behaviors:**

1. **Constructs:** It allocates and returns a fresh object instance.
2. **Prefix operator:** It attaches to the constructor call that follows it (`new Date()`).
3. **Action, not description:** It *does* instantiation; it does not describe something as recent.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Unary construction operator (prefix) — "instantiate the following constructor"
- **Action vs State:** ACTION - it builds/creates an object
- **Temporal aspect:** One-time at the point of use — a single construction event

### Recommended Form

**Primary recommendation:** Use a short verb meaning "create / construct / instantiate / make." The word must read as an *action performed on a constructor*, producing a fresh object. Prefer the "bring into being" verb sense over any adjective.

**Forms to AVOID:**

- ❌ The adjective "new / recent / fresh" (describing something as novel) - wrong grammatical role (see Ambiguity Resolution)
- ❌ "New" as in "newest / latest version" - a comparative descriptor, unrelated
- ❌ A noun ("a novelty / a newcomer") - `new` is the act of constructing, not a thing

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: Adjective "new" = recent, not old ("a **new** phone")
- ❌ Meaning 2: Adjective "new" = novel, never seen before ("a **new** idea")
- ✅ Meaning 3: **"CONSTRUCT / INSTANTIATE a fresh object"** — the verb of making an instance

**Example:**

English "new" can mean:

1. "I bought a **new** car" (recently made — adjective) ❌
2. "That's a **new** approach" (novel — adjective) ❌
3. "**new** Date()" (construct a fresh Date instance — action) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: the action of constructing/instantiating an object, NOT the adjective "recent/novel."** This is the central trap for this term — most languages' word for the adjective "new" will be WRONG here.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `new`, check these translations:**

- [ ] `let` - Another value-introducing keyword; keep construction distinct from declaration
- [ ] `const` - Value-introducing keyword; `new` builds, `const`/`let` name
- [ ] `typeof` - Another unary prefix operator; keep operator register consistent

**Consistency rule:**

`new` introduces objects the way `let`/`const` introduce names, but its verb must clearly mean *construct/build*, not *declare* and not *describe as recent*. Keep it distinct from the declaration keywords: they name a binding, `new` fabricates an instance. All three sit in the same beginner code, so the verbs should not blur together.

**Example:**

If you translate `let` as "allow-to-be" (a declaring verb), then:

- `new` should be a *constructing* verb ("build/create-instance"), clearly different in meaning
- NOT: `new` rendered with the adjective "recent," which reads as a description, not an action (❌)

### Functional relationships

**This term works WITH:**

1. **`new` + a constructor**: The core pattern — build an instance

```javascript
const now = new Date();
```

2. **`new` + arguments**: Pass initialization data to the constructor

```javascript
const re = new RegExp("^a", "i");
```

**Common pairing:**

```javascript
// new produces the object; a declaration keyword names it
const stamp = new Date();
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM-HARD**

**For this term:** MEDIUM-HARD

**Rationale:** The concept (construct an instance) is universal, but the English word is grammatically an adjective whose everyday meaning ("recent, novel") is exactly wrong. Many languages have a very common adjective for "new" that a translator will reach for reflexively — and it will be incorrect. The translator must override that instinct and choose a construction *verb*. This adjective-vs-action mismatch is what raises the difficulty above the other three keywords in this batch.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (construct/instantiate an object)
- [ ] Would a native speaker read it as "build a fresh instance," not "recent"?
- [ ] Avoids the adjective "new / recent / novel" sense?

### 2. Linguistic Correctness

- [ ] Correct part of speech (construction verb, not adjective or noun)?
- [ ] Correct form (prefix operator applied to a constructor)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language (lowercase for JS keywords)?

### 3. Consistency

- [ ] Distinct from the declaration keywords (`let`/`const`)?
- [ ] Reads as *construct*, not *declare* or *describe*?
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
term: new
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries the "construct / instantiate a fresh object" concept in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and why it avoids the adjective "recent/novel" sense.

**Alternatives considered:**

List the candidate terms weighed in the target language and why each was rejected or kept, explicitly noting any that drifted toward the adjective "new/recent" sense.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (adjective-vs-action mismatch, reflexive pull toward the everyday "new," competing regional conventions) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
