# JavaScript Member: `replaceAll` - Translation Brief (Tier 1)

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

`replaceAll` is a member method that returns a **new** string in which **every** match of a target is swapped for a replacement. It is called as `value.replaceAll(target, replacement)`; the original string is unchanged, and all occurrences change. Contrast with `replace`, which swaps only the **first** occurrence.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Swap every "cat" for "dog"
let s = "cat cat";
let out = s.replaceAll("cat", "dog");   // "dog dog"
```

**What this does:** Calls `replaceAll` on `"cat cat"`, swapping **every** `"cat"` for `"dog"`. Both occurrences change.

### Example 2: Common Pattern

```javascript
// Normalize all separators at once
let csv = "a,b,c";
let spaced = csv.replaceAll(",", " ");   // "a b c"
```

**What this does:** Uses `replaceAll` to substitute every occurrence in one call — the everyday "swap all of these for that" edit.

### Example 3: Edge Case

```javascript
// A bare `replaceAll` is NOT this member — only `x.replaceAll(...)` is
let replaceAll = true;                       // an ordinary variable named replaceAll
let out = "aaa".replaceAll("a", "b");        // THIS is the member → "bbb"
```

**What this shows:** `replaceAll` counts as this member **only** in property position (`"aaa".replaceAll(...)`). A standalone variable that happens to be named `replaceAll` is a different thing entirely — the AST decides, not the spelling.

---

## Pattern Classification

**This term is:** MEMBER METHOD (qualified — Rule 2 only)

**Similar terms in this pattern:**

1. `replace` - The first-occurrence counterpart; translate the two as a matched pair
2. `trim` - Also a non-mutating string-cleanup member returning a new value
3. `slice` - Also returns a new string derived from the original

**Pattern rule:** Members are labels attached to a receiver. Because a member is disambiguated by its receiver (and syntactically by the dot), **one native word may serve several receivers** and that is correct, not lossy — English does exactly this. Rule 1 (one concept ↔ one standalone term) does **not** apply to members; only Rule 2 (reversibility within the members partition) does.

---

## Etymology (Brief)

**English Origin:** Latin (via Old French) + English "all"

**Root meaning:** "replace" (Latin *replicare* → "place again, put back") + "all" (Old English *eall*, "the whole, every one"). The compound reads "substitute in every place."

**Why JavaScript uses this:** JavaScript names the exhaustive-substitution operation `replaceAll` — "put this new text wherever that old text appears, every time." The reading is *substitute one for another at every match*, distinguished from `replace` (first only) precisely by the **All**.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`replaceAll` is a method read from a value with the `receiver.replaceAll(target, replacement)` shape. It returns a **new** string identical to the receiver except that **every** occurrence of `target` is replaced by `replacement`. The receiver is not mutated, and — this is the load-bearing detail — *all* matches change, not just the first. This member is String-only, even in full JavaScript; there is no array form, so no receiver-widening to worry about.

Critically, `replaceAll` is a **member**: it only means this concept when it sits in property position after a dot. `"aa".replaceAll("a","b")` is the member; a learner's own variable named `replaceAll` is not. The tokenizer alone cannot tell these apart — the surrounding syntax (a non-computed `MemberExpression.property`) is what identifies it. This is why the pack treats members as a separate partition from standalone keywords and builtins.

Because a member is bounded by its receiver, repetition of the native word across receivers is never a collision; the pack scores `replaceAll` under Rule 2 (reversibility), not Rule 1. The sharp distinction to preserve is `replaceAll` (every match) vs `replace` (first match). The natural strategy in most languages is a base "replace" word plus an "all / every" qualifier — keep that qualifier visible so the two never collapse into one word.

**Key behaviors:**

1. **Every match:** replaces all occurrences, not just the first.
2. **Returns a new string:** the original is unchanged.
3. **AST-decided:** only a non-computed `MemberExpression.property` is this member — a bare identifier named `replaceAll` is not.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb phrase naming an exhaustive substitution transform
- **Action vs State:** ACTION - it swaps every match and returns a new string
- **Temporal aspect:** Present-tense operation — "substitute this for that everywhere, now"

### Recommended Form

**Primary recommendation:** Use the same substitute verb chosen for `replace`, plus an **"all / every / everywhere"** qualifier — so the pair reads as "replace (first)" vs "replace-all (every)." The qualifier is the load-bearing part: it is what makes this member distinct.

**Forms to AVOID:**

- ❌ A word identical to your `replace` translation with **no** "all" marker - the two would collapse
- ❌ A word meaning **"put back everything / restore"** - `replaceAll` substitutes, it does not restore
- ❌ A noun form - `replaceAll` is the action of substituting everywhere

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "Put everything back" (restore all to place)
- ❌ Meaning 2: "Replace only the first" (that is `replace`, not this)
- ✅ Meaning 3: **"SUBSTITUTE EVERY MATCH"** — swap new text in at all occurrences

**Example:**

English "replace all" can mean:

1. "**Replace all** the books on the shelf" (put them all back) ❌
2. Substitute just the first match — that is `replace`, not `replaceAll` ❌
3. "`'cat cat'.replaceAll('cat','dog')` → `'dog dog'`" (substitute every match) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: substituting every matching occurrence, NOT restoring, and NOT the first-only behavior of `replace`** — the "all / every" marker must be unmistakable.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `replaceAll`, check these translations:**

- [ ] `replace` - The first-occurrence sibling; the two MUST be a matched, distinguishable pair
- [ ] `trim` - Also a non-mutating cleanup transform; keep "returns a new string" consistent
- [ ] `slice` - Also returns a derived new string

**Consistency rule:**

`replaceAll` must be built as `replace` + an explicit "all / every" qualifier so the pair is distinguishable at a glance. Reuse the exact substitute verb from `replace` and add the quantifier; do not invent an unrelated word for `replaceAll`, and do not let it read identically to `replace`.

### Functional relationships

**This term works WITH:**

1. **`replaceAll` + a target/replacement pair**: The sweep-all edit

```javascript
let text = "one_two_three".replaceAll("_", "-");   // "one-two-three"
```

**Common pairing:**

```javascript
// replaceAll produces a new string that is then used
let clean = "a.b.c".replaceAll(".", "/");   // "a/b/c"
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The concept (substitute every match) is common, but the whole difficulty is *relational*: the native word must be `replace` plus an unmistakable "all / every" marker, and it must not collapse into `replace` or drift toward "restore." Getting the quantifier to read naturally in the target grammar — and consistently with the `replace` choice — is the real work.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (substitute every match, new string)
- [ ] Reads as "swap all for," not "restore everything"?
- [ ] Clearly distinct from `replace` (all vs first)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb phrase, not noun)?
- [ ] Correct form (substitute verb + "all/every" qualifier)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language?

### 3. Consistency

- [ ] Built from the same base verb as `replace` (matched pair)?
- [ ] "All / every" marker unmistakable?
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
term: replaceAll
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
binding: qualified
receivers: [String]
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries "substitute every match" in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and confirm it is built from the `replace` verb plus an unmistakable "all / every" qualifier.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any that collapsed into `replace` or drifted toward "restore."

**If confidence is not HIGH, explain:**

State what makes this term uncertain (keeping the `replace`/`replaceAll` pair distinct, natural placement of the "all" quantifier) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
