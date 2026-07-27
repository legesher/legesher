# JavaScript Member: `log` - Translation Brief (Tier 1)

**Category:** member
**Type:** method (verb, output action)
**Target:** JavaScript (JEJ subset)
**Binding:** qualified (Rule 2 only — bounded by its receiver)
**Ships in JEJ:** yes (CORE-1571 widening; reference.md § Logs & Assertions › Logging)
**Difficulty:** MEDIUM

---

## Quick Summary

`log` is the member called as `console.log(value)` — **write a value to the console** so a human can read it. It is the workhorse output call of JEJ: happy-path tracing, inspecting variables, and showing results all go through `console.log`. As a member it is a *qualified* term: it exists after a dot, bounded by its receiver, and is translated as a short action verb meaning "record / write out."

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Show a value in the console
const total = 3 + 4;
console.log(total); // 7
```

**What this does:** `console.log` takes a value and writes it to the console — the program's window for talking to its author. Nothing in the program changes; it is pure output.

### Example 2: Common Pattern

```javascript
// Label your output; log accepts several values at once
let x = 2;
let y = 5;
console.log("x:", x); // x: 2
console.log("y:", y); // y: 5
```

**What this does:** Passing several arguments prints them on one line, separated by spaces. Labeling values is the standard debugging habit the reference teaches ("happy-path tracing").

### Example 3: Edge Case

```javascript
// log is a MEMBER: it exists after a dot, bounded by its receiver
console.log("recorded");   // the member — translates
let log = "a variable";    // a learner identifier — NEVER translated
console.log(log);          // both on one line: member dot-side, identifier inside
```

**What this shows:** The member `log` and an identifier spelled `log` are different things. The engine decides by AST position (a non-computed member property), so a learner may freely name a variable after it — only the dotted member carries the pack translation.

---

## Pattern Classification

**This term is:** OUTPUT/RECORD ACTION (verb)

**Similar terms in this pattern:**

1. `alert` (builtin) - Also shows a value to a human, but interrupts with a popup; `log` is the quiet, continuous channel
2. `toString` (member) - Produces text from a value but *returns* it instead of displaying it
3. The held `console.*` family (`warn`, `error`, `table`, …) - Same receiver, different channels; NOT in the surface yet (CORE-1609 Q1)

**Pattern rule:** An output-action member should be a short verb a teacher would say for "write this down where we can see it": record / register / note. It should read naturally right after the `console` translation.

---

## Etymology (Brief)

**English Origin:** From *logbook* — via nautical *log*

**Root meaning:** Sailors measured a ship's speed with a wooden *log* thrown overboard and recorded the readings in the *log-book*; "to log" became "to write a chronological record."

**Why JavaScript uses this:** The console keeps a running, timestamp-ordered record of everything a program says — a ship's log for the program. `console.log` appends one entry to that record. The name is about *record-keeping*, not about tree trunks and not (here) about logarithms.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`console.log(...values)` writes its arguments to the console in order, then returns nothing. It is the JEJ program's primary voice: the reference's tracing, inspection, and communication patterns are all built on it. The call never changes program state — removing a `console.log` never changes what a program computes, only what a human sees.

Two framing facts matter for translation:

1. **Qualified binding.** Members are bounded by their receiver, and one native word may serve several receivers — that is correct, not a collision (Rule 2 only). English itself reuses this spelling: full JavaScript has `Math.log` (the natural logarithm). A native word chosen for "record/write out" simply won't mean logarithm — and that is *fine*: the receiver disambiguates, exactly as English relies on `console.` versus `Math.` context. Do not contort the choice to cover the logarithm sense; equally, do not pick a mathematics-only word.
2. **Cross-target kinship.** Python's `print` names the same teaching concept — "show the learner a value." The concepts are keyed together across targets rather than re-translated, but the JavaScript word is chosen for *this* language's idiom: an entry in a running record, not a page sent to a printer.

**Key behaviors:**

1. **Pure output:** no return value, no state change — communication only.
2. **Variadic:** several arguments print space-separated on one line.
3. **Member position only:** translates as the property in `console.log(...)`; an identifier spelled `log` is untouched.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Verb (imperative action) in member position
- **Action vs State:** ACTION - performs a visible act of recording
- **Temporal aspect:** Instantaneous - one entry per call, effect immediate

### Recommended Form

**Primary recommendation:** A short, everyday verb meaning "record / write down / register" — the word a teacher uses for "note this where we can see it." It must read naturally immediately after the `console` translation, as one spoken phrase.

**Forms to AVOID:**

- ❌ A logarithm/mathematics word — wrong concept for the console receiver
- ❌ A heavy formal verb ("document", "archive") when a light "record/note" exists
- ❌ A noun ("record" as a thing) where the language distinguishes noun from verb forms — this is an action

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: A tree trunk ("a log on the fire")
- ✅ Meaning 2: **APPEND TO A RUNNING RECORD** — write an entry where a human can read it
- ⚠️ Meaning 3: Logarithm (`Math.log`) — a REAL member in full JavaScript sharing this spelling; the receiver disambiguates, and your word need not cover it
- ❌ Meaning 4: "Log in / log out" (authentication) — unrelated

**Example:**

English "log" can mean:

1. "Throw another log on the fire" (wood) ❌
2. "`console.log(x)`" (append x to the console's record) ✅ **This is the JavaScript meaning**
3. "`Math.log(x)`" (natural logarithm) ⚠️ — same spelling, different receiver; English tolerates this ambiguity and so may your pack
4. "Log in to the site" (authentication) ❌

**Your translation should capture meaning #2: writing an entry into a visible running record.**

If the natural "record" verb in your language also happens to be usable for logarithms, that mirrors English and is acceptable. If not — the far more common case — that is equally acceptable under qualified binding. Never sacrifice the record/write sense to chase the mathematical one.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `log`, check these translations:**

- [ ] `console` (builtin) - The pair is spoken as one phrase: "console.record(x)" must sound natural
- [ ] `alert` (builtin) - Both show values to a human; keep them distinguishable (quiet record vs interrupting popup)
- [ ] `toString` (member) - Produces text without displaying it; the reader should never confuse the two

**Consistency rule:**

Read `console.log("hello")` aloud with both translations in place. It should sound like an instruction a teacher gives ("console, record 'hello'"). Then check the held `console.*` family: when `warn`/`error` are eventually added (CORE-1609 Q1), your `log` choice should leave natural room for sibling verbs.

### Functional relationships

**This term works WITH:**

1. **Tracing a loop**:

```javascript
for (const item of [1, 2, 3]) {
  console.log(item);
}
```

2. **Labeled inspection**:

```javascript
let count = 5;
console.log("count:", count);
```

**Common pairing:**

```javascript
// log (quiet record) vs alert (interrupting popup) — different channels
console.log("saved");   // appears in the console record
alert("saved");         // interrupts the learner with a popup
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Everyday "record/write down" verbs exist in every language (the easy part)
- English polysemy (record vs logarithm vs firewood) invites the wrong sense
- Must compose fluently with the `console` translation as a spoken phrase
- **AI confidence should be MEDIUM — verify the record/write sense explicitly**

### Why MEDIUM for `log`

- The target concept is simple and universal
- The spelling's mathematical double life (`Math.log`) tempts models toward a logarithm word, which would be wrong for the console receiver and absurd in teaching code
- The cross-target kinship with Python's `print` tempts reuse of a "print" word where the language's idiom for a console record differs

**For this term:** MEDIUM

**Rationale:** Picking a natural "record" verb is easy; resisting the logarithm and print-machine pulls, and reading naturally after `console`, is where choices go wrong. The verb must feel like note-taking, not typography and not mathematics.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures "append an entry to a visible record"?
- [ ] Action verb (not a noun, not a state)?
- [ ] Avoids the logarithm and firewood senses?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb, imperative/action form)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase member)?

### 3. Consistency

- [ ] Reads naturally directly after the `console` translation?
- [ ] Distinguishable from `alert` (popup) and `toString` (returns text)?
- [ ] Leaves room for future sibling verbs (`warn`, `error`) under CORE-1609 Q1?

### 4. Usability

- [ ] Short enough (1 word ideal)?
- [ ] Easy to type on a standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (everyday record/note verb)?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: log
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended verb carries the "append to a visible record" concept in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution, never in another language's choice. State explicitly that it is the record/write sense, not the logarithm.

**Alternatives considered:**

List the candidate verbs weighed in the target language and why each was rejected or kept — noting any that leaned toward printing machinery, mathematics, or formal archiving.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (record-verb competition, console-phrase fluency, regional register) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-27
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
