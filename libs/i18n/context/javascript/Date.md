# JavaScript Builtin: `Date` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** object (global constructor)
**Target:** JavaScript (JEJ subset)
**Binding:** standalone (Rule 1 + Rule 2 — one concept ↔ one native term)
**Ships in JEJ:** yes
**Difficulty:** MEDIUM

---

## Quick Summary

`Date` is the global constructor for date-and-time values. Called as `new Date()`, it captures the current moment (or a moment you specify) as an object you can read and format. In JEJ it names the calendar/clock facility a program uses to work with dates and times.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```javascript
// Capture the current date and time
let now = new Date();
```

**What this does:** Calls the `Date` constructor with no arguments, producing an object that holds the moment the line ran.

### Example 2: Common Pattern

```javascript
// Read a part of a date
let today = new Date();
console.log(today.getFullYear());   // e.g. 2026
```

**What this does:** Uses a `Date` object to answer questions about a moment — here, which year it is.

### Example 3: Edge Case

```javascript
// Date carries time as well as the calendar day
let d = new Date();
console.log(d.getHours());   // hour of day, 0–23
```

**What this shows:** Despite the name, a `Date` is really a *point in time* — it includes hours, minutes, seconds, not only the calendar day. The translation must cover date *and* time.

---

## Pattern Classification

**This term is:** TYPE CONSTRUCTOR (global object name)

**Similar terms in this pattern:**

1. `RegExp` - Also a global constructor built with `new`, naming a value type
2. `BigInt` - Also a global naming a specialized value type
3. `console` / `Math` - Also global object names, though facilities rather than value constructors

**Pattern rule:** Global constructors (`Date`, `RegExp`, `BigInt`) are *names of the kinds of value you create*. Translate them as nouns naming the thing, consistent with each other, never as verbs.

---

## Etymology (Brief)

**English Origin:** Latin → Old French

**Root meaning:** From Latin *data* ("given"), as in *data littera* — "letter given" at a certain time and place, the dating clause of a document. It came to mean the point in time something is marked with.

**Why JavaScript uses this:** JS needed a name for its time-point value type and took the everyday word "date." Although the object also carries the time of day, "Date" was the conventional short label already familiar from other languages and libraries.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`Date` is a global constructor that creates objects representing a single point in time — a calendar day *and* a time of day, down to milliseconds. `new Date()` captures the current moment; passing arguments builds a specific moment. Once created, a `Date` object answers questions (which year, which hour) and can be formatted into human-readable text.

In the JEJ teaching subset, `Date` names the facility for working with time. Learners meet it to timestamp events, compute ages or durations, or display the current day. It is one of the object-like globals: a *thing you construct and inspect*, unlike the dialog verbs (`alert`, `confirm`, `prompt`).

Conceptually, `Date` is a *noun naming a value type*. A subtlety worth carrying into the translation: the English word "date" suggests only the calendar day, but the object is a full moment in time. A native word that means strictly "calendar date" (and excludes time-of-day) understates the concept; a word covering "date/time" or "moment" fits better.

**Key behaviors:**

1. **Names a value type:** A `Date` object *is* a moment; it is a thing, not an action.
2. **Date and time together:** It carries time-of-day, not only the calendar day.
3. **Constructed with `new`:** `new Date()` yields the current moment; arguments give a specific one.

---

## Linguistic Form Recommendation

### Part of Speech

**In JavaScript context:**

- **Grammatical role:** Proper-noun-like name for the date/time value type
- **Action vs State:** STATE/thing - names a kind of value, does not perform an action
- **Temporal aspect:** None grammatically - it *names* time but is itself a persistent type label

### Recommended Form

**Primary recommendation:** Translate as a noun naming "date (and time) / moment" — the calendar-clock value. Prefer a word broad enough to include time-of-day, and keep it consistent in register with the other global constructors (`RegExp`, `BigInt`).

**Forms to AVOID:**

- ❌ A verb like "to date / schedule" - `Date` names a value, it does not act
- ❌ The romantic "a date / an outing" sense - wrong meaning (see Ambiguity Resolution)
- ❌ A word meaning strictly "calendar day" if it excludes time-of-day - understates the object

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for JavaScript:**

- ❌ Meaning 1: "A date" as a social/romantic outing
- ❌ Meaning 2: "Date" the fruit (from the palm tree)
- ✅ Meaning 3: **"A POINT IN TIME — CALENDAR DATE AND TIME OF DAY"**

**Example:**

English "date" can mean:

1. "We went on a **date**" (a social outing) ❌
2. "A box of **dates**" (the fruit) ❌
3. "Record the **date** and time of each order" (a point in time) ✅ **This is the JavaScript meaning**

**Your translation should capture meaning #3: a moment in time including the time of day, NOT the outing or the fruit — and ideally not a word limited to the bare calendar day.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `Date`, check these translations:**

- [ ] `RegExp` - Also a global constructor noun; keep both as type-naming nouns of one register
- [ ] `BigInt` - Also a global constructor for a value type; consistent noun treatment
- [ ] `console` / `Math` - Other global object names; same technical register

**Consistency rule:**

`Date`, `RegExp`, and `BigInt` are all names of value types the program creates. Treat them as one consistent set of technical nouns. Do not translate `Date` as an everyday casual word while `RegExp`/`BigInt` stay formal — match the register across the set.

### Functional relationships

**This term works WITH:**

1. **`Date` + `new`**: Constructing a moment

```javascript
let now = new Date();
```

**Common pairing:**

```javascript
// A Date read for display
let d = new Date();
console.log(d.getFullYear());
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:** "Date" as a calendar concept exists in every language, so a base noun is easy to find. The complication is that the JS object is really a *moment* (date + time), and some languages split "date" and "time" into words that would understate the object. Choosing a noun broad enough, and avoiding the outing/fruit senses, is a modest but real judgment call for a native reviewer.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the JAVASCRIPT CONCEPT (a point in time: date and time of day)
- [ ] Would a native speaker read this as a calendar/clock value, not an outing or fruit?
- [ ] Avoids a word limited to the bare calendar day if that excludes time?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun naming a type, not a verb)?
- [ ] Correct form (technical noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct for this language (`Date` capital preserved in JS)?

### 3. Consistency

- [ ] Matches the pattern of other global constructors (`RegExp`, `BigInt`)?
- [ ] Same technical register as similar builtins?
- [ ] Aligns with related terms (checked cross-references)?

### 4. Usability

- [ ] Short enough (1-2 words)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional?
- [ ] Respects regional sensitivities (calendar conventions)?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs (especially RTL scripts)?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: Date
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term names a point in time (date and time of day) in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution — and note whether the chosen noun includes time-of-day.

**Alternatives considered:**

List the candidate terms weighed and why each was rejected or kept, especially any rejected for meaning only the calendar day or the outing/fruit senses.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (date-only vs date+time scope) so review can prioritize it.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2026-07-21
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive version
