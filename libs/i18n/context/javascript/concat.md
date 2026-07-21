# JavaScript Member: `concat` - Translation Brief (Tier 1)

**Category:** member
**Type:** method (verb)
**Target:** JavaScript (JEJ subset)
**Binding:** qualified (Rule 2 only — a label bounded by its receiver; repetition across receivers is correct, never a collision)
**Receivers (full JS):** String, Array
**Receivers (live in JEJ today):** String — arrays are not in the JEJ subset yet
**Ships in JEJ:** yes (member; String-only today, but choose a word that survives widening to Array)
**Difficulty:** MEDIUM

---

## Quick Summary

`concat` is a member method that joins values end-to-end to produce a **new** value. On a string it appends one or more strings to make a longer string; on an array (once arrays are taught) it appends elements/arrays to make a longer array. It is called as `value.concat(...)` and the original is unchanged.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Join two strings end-to-end
let greeting = "hello";
let full = greeting.concat(" world");   // "hello world"
```

**What this does:** Calls the `concat` method on `"hello"`, returning a new string with `" world"` appended.

### Example 2: Common Pattern

```javascript
// Assemble a label from parts
let first = "Ada";
let last = "Lovelace";
let name = first.concat(" ", last);   // "Ada Lovelace"
```

**What this does:** Uses `concat` to stitch several strings into one — the everyday "glue these pieces together" pattern.

### Example 3: Edge Case

```javascript
// A bare `concat` is NOT this member — only `x.concat(...)` is
let concat = true;                    // an ordinary variable named concat
let joined = "a".concat("b");         // THIS is the member
```

**What this shows:** `concat` counts as this member **only** in property position (`"a".concat(...)`). A standalone variable that happens to be named `concat` is a different thing entirely — the AST decides, not the spelling.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `slice` - Also a String/Array member; extracts a piece rather than joining
2. `includes` - Also a String/Array member that widens as the subset grows
3. `repeat` - Also builds a new string by joining copies (String-only sibling)

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (and syntactically by the dot), **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** Latin *concatenare* — "to chain together" (*con-* "together" + *catena* "chain"). "Concatenate" means "link items in a series, end to end."

**Why JavaScript uses this:** JavaScript abbreviates *concatenate* to `concat` — "chain these values together into one." The reading is *join end-to-end to make a new whole*, applicable to both strings and arrays.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`concat` is a method read from a value with the `receiver.concat(...)` shape. On a string it returns a **new** string that is the receiver followed by each argument; on an array (outside the current JEJ subset) it returns a **new** array that is the receiver followed by each argument's elements. It never mutates the receiver — it produces a fresh joined value.

Critically, `concat` is a **member**: it only means this concept when it sits in property position after a dot. `"a".concat("b")` is the member; a learner's own variable named `concat` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

Because a member is bounded by its receiver, a single native word can serve every receiver `concat` attaches to. That is a feature: English uses one word "concat" for strings and arrays alike, and the native translation should too — *provided the chosen word reads correctly for both*, i.e., "join text" and "join lists" are the same operation to a reader.

**Key behaviors:**

1. **Returns a new value:** the receiver is not changed; a fresh joined value comes back.
2. **Order-preserving join:** the result is receiver-first, then the arguments, in order.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `concat` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb naming a join transform
- **Action vs State:** ACTION - it joins values and returns a new one
- **Temporal aspect:** Present-tense operation — "join these together, now"

### Recommended Form

**Primary recommendation:** Use a verb meaning **join / append end-to-end** — a word that reads correctly for gluing strings together *and* linking arrays together. Prefer a neutral "join / combine in order" sense over "add up" (arithmetic) or "mix."

**Forms to AVOID:**

- ❌ A word meaning **arithmetic "add / sum"** - `concat` joins in sequence, it does not compute a total
- ❌ A word meaning **only "join words/text"** - too narrow; breaks the day the same member joins arrays
- ❌ A noun form ("a concatenation") - `concat` is the joining action

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Add / sum numerically" ("concatenate the totals")
- ❌ Meaning 2: "Mix / blend together" (loses the ordered end-to-end sense)
- ✅ Meaning 3: **"JOIN END-TO-END INTO A NEW VALUE"** — chain the pieces in order

**Example:**

"Join" can be read as:

1. "**Add** 2 and 3" (arithmetic sum) ❌
2. "**Mix** the ingredients" (unordered blend) ❌
3. "`'a'.concat('b')` → `'ab'`" (chain in order) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: an ordered end-to-end join, NOT arithmetic addition or mixing** — because the *same* member joins array elements once arrays are taught, and it must read as "link these lists in order" there too.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `concat`, check these translations (members that widen String→Array):**

- [ ] `slice` - The inverse-ish operation (take a piece); keep the String/Array framing consistent
- [ ] `includes` - Containment member across String and Array
- [ ] `indexOf` - Position member across String and Array
- [ ] `length` - Count member across String and Array
- [ ] `repeat` - String-only sibling that also joins copies to build a new string

**Consistency rule:**

Members that share receivers should be translated as a family, each with a word that survives receiver-widening. Choose the "join end-to-end" verb for `concat` knowing that `slice`, `includes`, and `indexOf` face the same String→Array widening — do not optimize any of them for strings alone.

### Functional relationships

**This term works WITH:**

1. **`concat` + pieces**: The assembler

```javascript
let path = "/users".concat("/", "42");   // "/users/42"
```

**Common pairing:**

```javascript
// concat builds a value that is then used elsewhere
let greeting = "Hi, ".concat(name, "!");
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The concept (join end-to-end) is universal, but two things raise the bar: (1) "join" in many languages can slide toward arithmetic "add" or unordered "mix," neither of which fits; (2) the member widens from String to Array, so the chosen verb must read for joining lists as naturally as joining text. A word tuned only for text breaks when arrays arrive.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (ordered end-to-end join, new value)
- [ ] Reads correctly for ALL receivers (String, Array), not just String?
- [ ] Avoids the "arithmetic add / mix" connotations?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb, not noun)?
- [ ] Correct form (a "join end-to-end" transform)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] Matches the family of widening members (`slice`, `includes`, `indexOf`, `length`)?
- [ ] Chosen for the full receiver set, not strings alone?
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
term: concat
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [String, Array]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "join end-to-end into a new value" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it reads for both String and Array receivers, not String alone.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any that leaned toward arithmetic "add" or "mix."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (add/mix drift, receiver-widening risk) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
