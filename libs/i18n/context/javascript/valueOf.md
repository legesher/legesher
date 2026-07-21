# JavaScript Member: `valueOf` - Translation Brief (Tier 1)

**Category:** member
**Type:** method (verb)
**Target:** JavaScript (JEJ subset)
**Binding:** qualified (Rule 2 only — a label bounded by its receiver; repetition across receivers is correct, never a collision)
**Receivers (full JS):** String, Number, Boolean, Date, Object
**Receivers (live in JEJ today):** String, Number — Boolean, Date, and Object are not in the JEJ subset yet
**Ships in JEJ:** yes (member; String + Number today, but choose a word that survives widening)
**Difficulty:** HARD

---

## Quick Summary

`valueOf` is a member method that returns the **primitive value** underlying its receiver — the raw number, string, or boolean that a value reduces to when JavaScript needs a primitive (for arithmetic, comparison, or coercion). It is called as `value.valueOf()`. **This term is flagged for native review:** the concept is abstract (the "underlying primitive" of an object) and has no everyday-English anchor, so the native word is easy to get subtly wrong.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Get the primitive number behind a value
let n = 42;
let prim = n.valueOf();   // 42 (the primitive number)
```

**What this does:** Calls `valueOf` on `42`, returning the primitive number `42`. The method is invoked with a dot and parentheses.

### Example 2: Common Pattern

```javascript
// valueOf is what coercion calls under the hood
let a = 10;
let b = 5;
let sum = a.valueOf() + b.valueOf();   // 15
```

**What this does:** Retrieves each value's primitive form before adding. In practice JavaScript calls `valueOf` *automatically* during arithmetic — this member is the hook that makes `a + b` work on wrapped values.

### Example 3: Edge Case

```javascript
// A bare `valueOf` is NOT this member — only `x.valueOf()` is
let valueOf = "label";       // an ordinary variable named valueOf
let real = (42).valueOf();   // THIS is the member
```

**What this shows:** `valueOf` counts as this member **only** in property position before the call (`(42).valueOf()`). A standalone variable happening to be named `valueOf` is a different thing entirely — the AST decides, not the spelling.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `toString` - The mirror member: returns the *text form* rather than the primitive value
2. `charAt` - Also a String member
3. `slice` - Also a member that widens beyond String

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (and syntactically by the dot), **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Compound — "value" + "of"

**Root meaning:** "The value *of* this thing" — the essential quantity or content a value stands for. "Value" from Latin *valere*, "to be worth."

**Why JavaScript uses this:** Objects in JavaScript can wrap a primitive (a number, string, or boolean). `valueOf` is the standard hook that answers "what primitive are you, really?" so the engine can do arithmetic and comparison. It is the counterpart to `toString`: one asks for the *primitive value*, the other for the *text form*.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`valueOf` is a method read from a value with the `receiver.valueOf()` shape. It returns the **primitive value** the receiver represents: for a number, the raw number; for a string, the raw string; for a boolean, `true`/`false`; for a date, its numeric timestamp. JavaScript invokes it automatically whenever it needs to coerce an object to a primitive.

Critically, `valueOf` is a **member**: it only means this concept when it sits in property position after a dot and is then called. `(42).valueOf()` is the member; a learner's own variable named `valueOf` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

Because a member is bounded by its receiver, a single native word can serve every receiver `valueOf` attaches to. That is a feature — English uses one word for all of them. The difficulty here is that the concept is **abstract**: "the underlying primitive value of an object" is a language-internal notion with no direct everyday-life referent, unlike "the character at position 3." The translator is naming a mechanism, not a familiar object, so the reviewer must confirm the chosen word reads as "the essential/primitive value of," not merely "worth" or "price."

**Key behaviors:**

1. **Method, not property:** called as `x.valueOf()` with `()`.
2. **Qualified binding:** identified by receiver + dot position; repetition across receivers is expected and correct.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `valueOf` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb / verb phrase — an action returning the primitive value
- **Action vs State:** ACTION - it retrieves and returns a value
- **Temporal aspect:** None - a single imperative operation

### Recommended Form

**Primary recommendation:** Use a verb (or short verb phrase) meaning **"give the primitive/underlying value of"** — a word that reads for a number, a string, and a boolean alike. Prefer "underlying value / primitive value" phrasing over "price / worth."

**Forms to AVOID:**

- ❌ A word meaning **monetary "value / price / worth"** - the commercial sense, wrong for a programming primitive
- ❌ A word meaning **"text form"** - that is `toString`; keep them distinct
- ❌ A noun form - `valueOf` is an action (a method call), not a thing

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Monetary worth / price" ("the value of the house")
- ❌ Meaning 2: "Moral values / principles"
- ✅ Meaning 3: **"THE PRIMITIVE VALUE AN OBJECT REDUCES TO"** — the raw number/string/boolean

**Example:**

English "value" can mean:

1. "the market **value** of the car" (price) ❌
2. "family **values**" (principles) ❌
3. "the primitive **value** of this wrapped number" (the raw datum) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: the underlying primitive datum, NOT price or principles** — because `valueOf` exists so the engine can extract the raw value for arithmetic and comparison.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `valueOf`, check these translations:**

- [ ] `toString` - Its mirror; must be a DISTINCT native word (primitive value vs text form) or reversibility breaks
- [ ] `charAt` - Another String member; keep clearly different
- [ ] `charCodeAt` - Returns a numeric code — keep clearly different from `valueOf`

**Consistency rule:**

`valueOf` and `toString` are a matched pair and both live in JEJ today. Under Rule 2 (reversibility within the members partition) they must map to two clearly different native words — one for "primitive value," one for "text form." Do not let them collapse into the same word.

### Functional relationships

**This term works WITH:**

1. **`valueOf` + arithmetic / comparison**: coercion to a primitive

```javascript
let a = 10;
let doubled = a.valueOf() * 2;   // 20
```

**Common pairing:**

```javascript
// valueOf underlies implicit coercion
let x = 3;
let y = x + 1;   // JS calls x.valueOf() behind the scenes
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

**For this term:** HARD — flagged for native review

**Rationale:** The concept is abstract and language-internal ("the primitive an object reduces to"), with no concrete everyday referent, and it must stay clearly distinct from its mirror member `toString`. The English word "value" is heavily polysemous (price, principles, magnitude), so a naive native choice risks the commercial reading. The translator must name a mechanism precisely, and the reviewer should confirm both the sense and the `toString` contrast.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (underlying primitive value)?
- [ ] Reads correctly for the live receivers (String, Number) AND survives widening (Boolean, Date, Object)?
- [ ] Avoids the "price / monetary worth" trap?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb / verb phrase)?
- [ ] Correct form ("give the primitive value of")?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] DISTINCT from `toString` (primitive value vs text form)?
- [ ] Chosen for the full receiver set, not numbers alone?
- [ ] Aligns with related terms (checked cross-references)?

### 4. Usability

- [ ] Short enough (max ~3 words for members)?
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
term: valueOf
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [String, Number, Boolean, Date, Object]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "the underlying primitive value" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it reads for every receiver in the set and stays distinct from `toString`.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any that leaned toward monetary "value / price."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (abstract concept, polysemous "value," mirror-pair contrast) so review can prioritize it. This term is pre-flagged for native review.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
