# JavaScript Member: `replace` - Translation Brief (Tier 1)

**Category:** member
**Type:** method (verb)
**Target:** JavaScript (JEJ subset)
**Binding:** qualified (Rule 2 only — a label bounded by its receiver; repetition across receivers is correct, never a collision)
**Receivers (full JS):** String
**Receivers (live in JEJ today):** String — String-only in full JS too; there is no widening for this member
**Ships in JEJ:** yes (member; String-only)
**Difficulty:** MEDIUM

---

## Quick Summary

`replace` is a member method that returns a **new** string in which the **first** match of a target is swapped for a replacement. It is called as `value.replace(target, replacement)`; the original string is unchanged, and only the first occurrence changes. Contrast with `replaceAll`, which swaps *every* occurrence.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Swap the first "cat" for "dog"
let s = "cat cat";
let out = s.replace("cat", "dog");   // "dog cat"
```

**What this does:** Calls `replace` on `"cat cat"`, swapping only the **first** `"cat"` for `"dog"`. The second `"cat"` is left as-is.

### Example 2: Common Pattern

```javascript
// Fix one token in a template
let template = "Hello, NAME!";
let msg = template.replace("NAME", "Ada");   // "Hello, Ada!"
```

**What this does:** Uses `replace` to substitute a single placeholder — the everyday "swap this one thing for that" edit.

### Example 3: Edge Case

```javascript
// A bare `replace` is NOT this member — only `x.replace(...)` is
let replace = true;                       // an ordinary variable named replace
let out = "aaa".replace("a", "b");        // THIS is the member → "baa"
```

**What this shows:** `replace` counts as this member **only** in property position (`"aaa".replace(...)`). A standalone variable that happens to be named `replace` is a different thing entirely — the AST decides, not the spelling.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `replaceAll` - The all-occurrences counterpart; translate the two as a matched pair
2. `trim` - Also a non-mutating string-cleanup member returning a new value
3. `slice` - Also returns a new string derived from the original

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (and syntactically by the dot), **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Latin (via Old French)

**Root meaning:** Latin *replicare* → Old French *replacer*: "to place again, put back." Modern English "replace" means "to put something new in the position of the old."

**Why JavaScript uses this:** JavaScript names the substitution operation `replace` — "put this new text where that old text was." The reading is *substitute one for another*, and by default only the **first** match is affected.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`replace` is a method read from a value with the `receiver.replace(target, replacement)` shape. It returns a **new** string identical to the receiver except that the **first** occurrence of `target` is replaced by `replacement`. The receiver is not mutated, and — this is the load-bearing detail — only the first match is changed, not all of them. This member is String-only, even in full JavaScript; there is no array form, so no receiver-widening to worry about.

Critically, `replace` is a **member**: it only means this concept when it sits in property position after a dot. `"aa".replace("a","b")` is the member; a learner's own variable named `replace` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

Because a member is bounded by its receiver, repetition of the native word across receivers is never a collision; the pack scores `replace` under Rule 2 (reversibility), not Rule 1. The sharp distinction to preserve is `replace` (first match) vs `replaceAll` (every match) — if the native words for these two collapse into one, the reader loses a real behavioral difference.

**Key behaviors:**

1. **First match only:** by default replaces just the first occurrence.
2. **Returns a new string:** the original is unchanged.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `replace` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb naming a substitution transform
- **Action vs State:** ACTION - it swaps text and returns a new string
- **Temporal aspect:** Present-tense operation — "substitute this for that, now"

### Recommended Form

**Primary recommendation:** Use a verb meaning **substitute / swap one thing for another** — the sense of putting a new value where the old one was. Crucially, choose a base "replace" verb that can be minimally extended to express "replace **all**" for `replaceAll`, so the pair stays distinguishable.

**Forms to AVOID:**

- ❌ A word meaning **"put back / return to place"** (restore) - `replace` substitutes, it does not restore
- ❌ A word so total that it cannot contrast with `replaceAll` - you must keep "first" vs "all" expressible
- ❌ A noun form ("a replacement") - `replace` is the action of substituting

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Put back where it was" (restore to original position)
- ❌ Meaning 2: "Take over someone's role" ("replace the manager")
- ✅ Meaning 3: **"SUBSTITUTE THE FIRST MATCH"** — swap new text in for the first old match

**Example:**

English "replace" can mean:

1. "**Replace** the book on the shelf" (put back) ❌
2. "She will **replace** him as lead" (succeed in a role) ❌
3. "`'cat cat'.replace('cat','dog')` → `'dog cat'`" (substitute the first match) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: substituting the first matching text, NOT restoring or succeeding a role** — and it must remain contrastable with `replaceAll`.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `replace`, check these translations:**

- [ ] `replaceAll` - The all-occurrences sibling; the two MUST be a matched, distinguishable pair
- [ ] `trim` - Also a non-mutating cleanup transform; keep "returns a new string" consistent
- [ ] `slice` - Also returns a derived new string

**Consistency rule:**

`replace` and `replaceAll` are a matched pair: whatever verb expresses "substitute the first" must extend cleanly to "substitute all." Do not choose a `replace` word that already implies "all," or the distinction with `replaceAll` collapses. Keep both in the non-mutating string-transform family.

### Functional relationships

**This term works WITH:**

1. **`replace` + a target/replacement pair**: The single-swap edit

```javascript
let greeting = "Hi {user}".replace("{user}", "Sam");
```

**Common pairing:**

```javascript
// replace produces a new string that is then used
let clean = "a,b".replace(",", " and ");   // "a and b"
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The concept (substitute text) is common, but two things raise the bar: (1) "replace" in many languages overlaps with "restore / put back" or "succeed in a role," neither of which is meant; (2) the native word must stay distinguishable from `replaceAll`, since the *first-match-vs-all* difference is real behavior. Picking a substitute-verb that can carry an "all" modifier is the key constraint.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (substitute the first match, new string)
- [ ] Reads as "swap one for another," not "restore / put back"?
- [ ] Stays distinguishable from `replaceAll` (first vs all)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb, not noun)?
- [ ] Correct form (a substitution transform)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] Extends cleanly to `replaceAll` (matched pair)?
- [ ] Reads as returning a fresh value, not mutating in place?
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
term: replace
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [String]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "substitute the first match" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it stays distinguishable from `replaceAll`.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any that leaned toward "restore" or that could not contrast with "all."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (restore/role-succession drift, the `replaceAll` pairing) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
