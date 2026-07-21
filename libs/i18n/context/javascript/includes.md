# JavaScript Member: `includes` - Translation Brief (Tier 1)

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

`includes` is a member method that answers a yes/no question: does this value contain the thing I am asking about? On a string it tests whether a substring appears; on an array (once arrays are taught) it tests whether an element is present. It is called as `value.includes(x)` and returns a boolean.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Does this string contain "ell"?
let word = "hello";
let has = word.includes("ell");
```

**What this does:** Calls the `includes` method on `"hello"`, asking whether `"ell"` appears inside it. Returns `true`.

### Example 2: Common Pattern

```javascript
// Gate on the presence of a substring
let email = "user@example.com";
if (email.includes("@")) {
  // looks like it has an at-sign
}
```

**What this does:** Uses `includes` as a containment test — the everyday "does this appear anywhere inside?" check that drives a branch.

### Example 3: Edge Case

```javascript
// A bare `includes` is NOT this member — only `x.includes(...)` is
let includes = true;              // an ordinary variable named includes
let found = "hi".includes("h");   // THIS is the member
```

**What this shows:** `includes` counts as this member **only** in property position (`"hi".includes(...)`). A standalone variable that happens to be named `includes` is a different thing entirely — the AST decides, not the spelling.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `indexOf` - Also a String/Array member; reports *where* rather than *whether*
2. `concat` - Also a String/Array member that widens as the subset grows
3. `slice` - Also a member that widens from String to Array

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (and syntactically by the dot), **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Latin (via Old French)

**Root meaning:** Latin *includere* — "to shut in, enclose" (*in-* "in" + *claudere* "to close"). In modern English "include" means "to have as a part; to contain."

**Why JavaScript uses this:** JavaScript names the containment test `includes` — "does the collection *include* this value?" The reading is *contains / has as a member*, not *encloses physically*.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`includes` is a method read from a value with the `receiver.includes(x)` shape. On a string it returns `true` when the argument appears as a substring; on an array (outside the current JEJ subset) it returns `true` when the argument is one of the elements. It always yields a boolean — a yes/no answer.

Critically, `includes` is a **member**: it only means this concept when it sits in property position after a dot. `"abc".includes("b")` is the member; a learner's own variable named `includes` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

Because a member is bounded by its receiver, a single native word can serve every receiver `includes` attaches to. That is a feature: English uses one word "includes" for strings and arrays alike, and the native translation should too — *provided the chosen word reads correctly for both*, not just the substring case the translator happens to picture first.

**Key behaviors:**

1. **Returns a boolean:** it answers a yes/no containment question.
2. **Qualified binding:** it is identified by receiver + dot position; repetition across receivers is expected and correct.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `includes` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb (a predicate — it asks "does it contain?")
- **Action vs State:** TEST - it queries containment and returns true/false
- **Temporal aspect:** Present-tense query — "does it contain this now?"

### Recommended Form

**Primary recommendation:** Use a verb (or verb phrase) meaning **contains / has-within** — a word that reads correctly for a substring inside a string *and* an element inside an array. Frame it as a yes/no test: "does it contain X?"

**Forms to AVOID:**

- ❌ A word meaning **physically enclose / shut in** - too literal; loses the "has as a member" reading
- ❌ A word meaning **only "contains a letter/substring"** - too narrow; breaks when the same member tests array membership
- ❌ A noun form - `includes` is a test being performed, not a thing

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Physically enclose / shut in" ("the wall includes the courtyard")
- ❌ Meaning 2: "Comprise as an itemized part of a list/price"
- ✅ Meaning 3: **"CONTAINS THIS VALUE"** — does the collection have this member?

**Example:**

English "includes" can mean:

1. "The fee **includes** tax" (comprises as a part) — near, but transactional ❌
2. "The set **includes** the wall" (physically encloses) ❌
3. "The string **includes** '@'" (contains this value) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: a containment test, NOT physical enclosure** — because the *same* member tests array membership once arrays are taught, and it must read as "does it contain this element?" there too.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `includes`, check these translations (all members that widen String→Array):**

- [ ] `indexOf` - Position member across String and Array; the "where" to this "whether"
- [ ] `concat` - Joining member across String and Array
- [ ] `slice` - Extraction member across String and Array
- [ ] `length` - Count member across String and Array

**Consistency rule:**

Members that share receivers should be translated as a family, each with a word that survives receiver-widening. Choose the "contains" verb for `includes` knowing that `indexOf`, `concat`, and `slice` face the same String→Array widening — do not optimize any of them for strings alone.

### Functional relationships

**This term works WITH:**

1. **`includes` + condition**: The presence gate

```javascript
let tags = "urgent,new,sale";
if (tags.includes("sale")) {
  // apply discount
}
```

**Common pairing:**

```javascript
// includes returns a boolean, then drives a branch or is negated
let name = "readme.md";
let is_markdown = name.includes(".md");
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The concept (a containment test) is universal, but English "include" carries an "itemize / comprise" flavor that can drift from the plain "contains" reading, and the member widens from String to Array — so the chosen verb must read for both substring and element membership. A word that only fits substrings breaks the day arrays are taught.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (containment test returning true/false)
- [ ] Reads correctly for ALL receivers (String, Array), not just String?
- [ ] Avoids the "physically enclose / itemize" connotations?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb, not noun)?
- [ ] Correct form (a "contains" predicate)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] Matches the family of widening members (`indexOf`, `concat`, `slice`, `length`)?
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
term: includes
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [String, Array]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "contains this value" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it reads for both String and Array receivers, not String alone.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any that leaned toward "enclose" or "itemize."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (enclose/itemize drift, receiver-widening risk) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
