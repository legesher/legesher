# JavaScript Builtin: `console` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** object (global namespace)
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes (builtin 1 of 16)
**Difficulty:** MEDIUM

---

## Quick Summary

`console` is the global object that gives access to the environment's debugging output — the panel where a program prints text for the developer to read. In JEJ it is the receiver of the output call learners use first: `console.log(...)`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Print a message to the output panel
console.log("Hello");
```

**What this does:** Reaches the `console` object and calls its `log` method to display `"Hello"` in the developer output.

### Example 2: Common Pattern

```javascript
// Show a computed value while learning
let price = 10;
let tax = price * 0.2;
console.log(tax);
```

**What this does:** Uses `console` as the destination for inspecting a value mid-program — the beginner's primary feedback loop.

### Example 3: Edge Case

```javascript
// console is the receiver; log is a separate member on it
console.log("a", "b", "c");
```

**What this shows:** `console` names the object; the thing done to it (`log`) is a *member* (see Cross-References). Translating `console` does not by itself translate `log`.

---

## Pattern Classification

**This term is:** GLOBAL OBJECT (namespace)

**Similar terms in this pattern:**

1. `Math` - Also a global namespace object accessed by name then dotted into (`Math.floor`)
2. `Date` - Also a global accessed by name, though also constructed with `new`
3. `RegExp` - Also a global object name in the builtin surface

**Pattern rule:** Global namespace objects (`console`, `Math`) are named things — translate them as nouns naming the facility, not as verbs. Keep them consistent with each other in noun form.

---

## Etymology (Brief)

**English Origin:** Latin → French

**Root meaning:** Latin *consolari* ("to comfort"); the computing sense comes from the "console" as the control panel/terminal of a mainframe — the operator's station. It came to mean the text terminal where a system reports to its operator.

**Why JavaScript uses this:** Browsers and Node expose developer output through a "console" — the modern descendant of the operator's terminal. The name signals "the place where the machine talks back to the developer."

---

## Concept Explanation (Intermediate Level)

**What it does:**

`console` is a global object always available to a JavaScript program. It is not created by the learner; it exists as part of the environment. Its members (methods) send text and values to a developer-facing output area — the browser devtools console, or the terminal in Node.

In the JEJ teaching subset, `console` matters almost entirely as the receiver of `console.log(...)`, which is how a beginner first sees the result of their code. The learner types the name `console`, a dot, and the operation they want performed on it.

Conceptually, `console` names a *destination for output*, not an action. The action lives in the member that follows the dot. This split — a named object plus a member operation — is the first example a learner meets of JavaScript's `receiver.member(...)` shape.

**Key behaviors:**

1. **Always available:** `console` is a global; it need not be declared or imported.
2. **A receiver, not an action:** it names *where* output goes; the *what* (`log`) is a separate member.
3. **Output, not computation:** using `console` does not change program values; it reports them.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Proper-noun-like name for the output facility
- **Action vs State:** STATE/thing - names an object, does not perform an action
- **Temporal aspect:** None - it is a persistent, always-present facility

### Recommended Form

**Primary recommendation:** Translate as a noun naming the developer output area / terminal — the "console" as a place the program writes to. Keep it a short, recognizable technical noun, consistent in form with the other global objects (`Math`, `Date`).

**Forms to AVOID:**

- ❌ A verb form - `console` names a thing, it does not command
- ❌ The "comfort / console someone" sense - wrong meaning (see Ambiguity Resolution)
- ❌ A word for the *action* of printing - that belongs to the member `log`, not to `console`

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "To console / comfort a person" (verb, emotional)
- ❌ Meaning 2: "A cabinet / console table" (furniture)
- ✅ Meaning 3: **"THE OPERATOR'S TERMINAL / OUTPUT PANEL"** — the place the program reports to the developer

**Example:**

English "console" can mean:

1. "She tried to **console** her friend" (comfort) ❌
2. "A **console** table in the hallway" (furniture) ❌
3. "Check the **console** for the error" (developer output terminal) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: the developer output terminal, NOT comfort or furniture.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `console`, check these translations:**

- [ ] `Math` - Also a global namespace noun; keep both as facility nouns of the same register
- [ ] `Date` - Also a global object name; consistent noun treatment
- [ ] `RegExp` - Also a global object name in the surface

**Consistency rule:**

All global objects (`console`, `Math`, `Date`, `RegExp`) are names of facilities and should read as nouns of one consistent technical register. Do not translate one as a plain everyday word and another as a formal coinage.

**Note on `log`:** `console.log` is *two* terms — the object `console` and the member `log`. `log` is **not** in the shipping member surface (it is held pending the partner decision on CORE-1529), so `console.*` renders with `console` translated and the member left canonical for now. Do not fold "log/print" meaning into the `console` translation to compensate.

### Functional relationships

**This term works WITH:**

1. **`console` + member**: The `receiver.member(...)` output call

```javascript
console.log("shown to the developer");
```

**Common pairing:**

```javascript
// console is how beginners inspect values as they learn
let result = 2 + 2;
console.log(result);
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** The developer-terminal sense of "console" may not have a single settled native word in every language, and the everyday senses ("comfort," "furniture") are distractors. Many languages loan the English/technical term. Choosing between an established loan and a native coinage is a judgment call worth flagging to a native reviewer.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (developer output terminal, not comfort/furniture)
- [ ] Would a native speaker understand this names where output appears?
- [ ] Avoids misleading connotations?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun, not verb)?
- [ ] Correct form (facility noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language (lowercase `console` in JS)?

### 3. Consistency

- [ ] Matches the pattern of other global objects (`Math`, `Date`)?
- [ ] Same noun register as similar builtins?
- [ ] Aligns with related terms (checked cross-references)?

### 4. Usability

- [ ] Short enough (1-2 words)?
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
term: console
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term names the developer output terminal in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and note whether you chose an established loan or a native coinage.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (no settled native word, loan-vs-coinage choice) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
