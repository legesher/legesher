# Python Keyword: `while` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** conjunction
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `while` keyword in Python creates a loop that repeatedly executes a code block as long as a condition remains `True`. It's condition-based iteration, continuing until the condition evaluates to `False`, making it ideal for loops where the number of iterations isn't known in advance.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Count down from 5
count = 5
while count > 0:
    print(count)
    count -= 1
# Output: 5, 4, 3, 2, 1
```

**What this does:** Tests the condition `count > 0` before each iteration. If true, executes the block (print and decrement). When count reaches 0, the condition becomes false and the loop exits.

### Example 2: Common Pattern

```python
# Process user input until valid
user_input = ""
while user_input != "quit":
    user_input = input("Enter command (or 'quit'): ")
    if user_input != "quit":
        print(f"You entered: {user_input}")
```

**What this does:** Creates an interactive loop that continues until the user types "quit". The condition is checked at the start of each iteration, allowing the loop to exit gracefully when the condition becomes false.

### Example 3: Edge Case

```python
# Infinite loop with break
while True:
    response = input("Continue? (y/n): ")
    if response.lower() == 'n':
        break
    print("Continuing...")
```

**What this shows:** `while True:` creates an intentional infinite loop - the condition is always true. The loop exits via `break` statement based on internal logic. This pattern is common when the exit condition is complex or checked mid-loop.

---

## Pattern Classification

**This term is:** STATE KEYWORD (Conditional Loop)

**Similar terms in this pattern:**

1. `if` - Tests condition once, executes block if true (no repetition)
2. `for` - Iterates over sequence elements (iteration-based, not condition-based)
3. `break` - Exits `while` or `for` loops early

**Pattern rule:** Loop control keywords should use conjunction or verb forms suggesting ongoing/repeated action. "While" expresses duration - "during the time that" - making it a temporal conjunction.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `if` | si | إذا | 如果 | यदि |
| `for` | para | لكل | 对于 | प्रत्येक_के_लिए |
| `while` | **mientras** | **بينما** | **当** | **जबकि** |

---

## Etymology (Brief)

**English Origin:** Germanic

**Root meaning:** Old English "hwīl" meant "a period of time." The conjunction "while" evolved to mean "during the time that" or "as long as." It expresses temporal duration with a condition.

**Why Python uses this:** "While" naturally expresses condition-based repetition in English: "while X is true, do Y." Guido van Rossum chose this over alternatives like "until" (negative condition) or "loop" (no condition specified). "While" clearly communicates both the conditional nature and the repetition.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `while` loop implements condition-based repetition in Python. Unlike `for` loops that iterate over sequences, `while` loops continue executing as long as a boolean condition remains `True`. The condition is evaluated before each iteration (pre-test loop). If the condition is initially false, the loop body never executes.

The syntax `while condition:` evaluates the expression after `while` and converts it to a boolean. Python's truthiness rules apply: `0`, `None`, `False`, empty collections all evaluate to `False`. When the condition becomes false, the loop terminates and execution continues with the next statement after the indented block.

`while` loops are ideal when the number of iterations is unknown or depends on runtime conditions: waiting for user input, processing data until a sentinel value, implementing game loops, or retrying operations. The loop can exit early with `break`, skip to the next iteration with `continue`, or include an `else` clause that executes when the loop completes normally (without `break`).

**Key behaviors:**

1. **Pre-condition testing:** The condition is checked before each iteration, including the first. If false initially, the loop body never runs. This differs from do-while loops in other languages that execute at least once.

2. **Infinite loop risk:** If the condition never becomes false, the loop runs forever. Common mistake: forgetting to update variables that affect the condition. Always ensure the loop progresses toward the exit condition.

3. **Optional else clause:** `while` can have an `else` block that executes when the loop condition becomes false naturally (not via `break`). This is useful for "search failed" scenarios or cleanup after successful loop completion.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Temporal/conditional conjunction
- **Action vs State:** STATE - expresses ongoing condition during a duration
- **Temporal aspect:** Continuous/durative - "during the time that" or "as long as"

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Temporal conjunction | "mientras", "pendant que" - natural duration word |
| Germanic (de, nl, sv) | Temporal conjunction | "während", "terwijl" - while/during |
| Slavic (ru, pl, uk) | Temporal conjunction | "пока", "podczas" - while/during |
| Arabic | Temporal particle | "بينما" - during/while |
| Chinese | Temporal particle | "当" or "当...时" - when/while |
| Hindi | Temporal conjunction | "जबकि" - while/whereas |

**Primary recommendation:** Use the target language's natural word for "while" or "during the time that." This should be a temporal conjunction expressing duration with a condition, not a simple conditional like "if."

**Forms to AVOID:**

- ❌ Using same word as "if" - `while` has temporal duration that "if" lacks
- ❌ Using word meaning "until" (negative condition) - `while` continues while true, not until true
- ❌ Verb form - `while` is not an action command

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `mientras`
- **Form:** Temporal conjunction
- **Why it works:** Standard Spanish for "while." Perfectly captures the duration + condition meaning. "Mientras X sea verdad, hacer Y" is natural Spanish. Universally understood in educational and technical contexts.

**Arabic:**

- **Translation:** `بينما` (baynamā)
- **Form:** Temporal particle
- **Why it works:** Standard Modern Arabic for "while/whereas." Expresses simultaneity and duration. Used in formal and technical writing. Clear conditional-temporal meaning.

**Chinese:**

- **Translation:** `当` (dāng) or `当...时` (dāng...shí)
- **Form:** Temporal particle
- **Why it works:** `当` means "when/while" - standard for temporal conditions. Can be used alone or in full form `当...时` (when...time). Established in Chinese programming education.

**Hindi:**

- **Translation:** `जबकि` (jabaki)
- **Form:** Temporal conjunction
- **Why it works:** Sanskrit-derived conjunction meaning "while/whereas." Formal register appropriate for programming. Expresses duration with condition clearly. Alternative: `जब_तक` (jab tak = as long as).

### ❌ Common Translation Mistakes

**Mistake 1: Using the same word as "if"**

- **Wrong:** `si` (Spanish for "if")
- **Why wrong:** While "if" tests condition once, "while" implies repeated testing over duration. Spanish distinguishes: `si` (if) vs. `mientras` (while). Don't conflate them.
- **Right:** `mientras`

**Mistake 2: Using "until" instead of "while"**

- **Wrong:** `hasta` (Spanish - "until")
- **Why wrong:** "Until" expresses opposite logic: loop until condition becomes true (negative condition). "While" continues while condition is true (positive condition). Different meanings.
- **Right:** `mientras`

**Mistake 3: Using only "when" without duration aspect**

- **Wrong:** `cuando` (Spanish - "when")
- **Why wrong:** "When" can express one-time event ("when X happens"). "While" emphasizes duration ("during the time that X is true"). Need temporal duration aspect.
- **Right:** `mientras` (explicitly durative)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "A period of time" (noun - "wait a while")
- ❌ Meaning 2: "Whereas, although" (contrastive - "I like tea while she likes coffee")
- ✅ Meaning 3: **TEMPORAL-CONDITIONAL** - "during the time that [condition is true]"

**Example:**

English "while" can mean:

1. "Let's rest for a while" (duration - noun) ❌
2. "I work while you sleep" (simultaneous actions - contrast) ⚠️
3. "While count > 0, print count" (conditional duration - loop) ✅ **This is the Python meaning**

**Your translation should capture meaning #3: continuous repetition during the time that a condition is true.**

Some languages distinguish:

- Temporal simultaneous "while" (two things happening at once)
- Conditional durative "while" (repeat as long as condition holds)

Use the CONDITIONAL DURATIVE form. In many languages, these are the same word (like Spanish "mientras"), which is fine.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `while`, check these translations:**

- [ ] `if` - Should use related conditional form, but `while` adds temporal duration
- [ ] `for` - Both are loop keywords; should use compatible forms
- [ ] `break`/`continue` - Loop control keywords that work with `while`

**Consistency rule:**

All loop keywords (`for`, `while`) and conditional keywords (`if`, `elif`, `else`) should use grammatically compatible forms. They're all control flow structures, so they should feel cohesive.

**Example:**

Spanish: `mientras`, `para`, `si` - all conjunctions/particles ✅
NOT: `mientras` (conjunction) + `iterar` (verb for "for") ❌

### Functional relationships

**This term works WITH:**

1. **`while` + condition + `break`**: Infinite loops with internal exit

```python
while True:
    if should_exit:
        break
```

2. **`while` + `else`**: Loop with success/failure handling

```python
attempts = 0
while attempts < 3:
    if try_operation():
        break
    attempts += 1
else:
    print("Failed after 3 attempts")
```

**Common pairing:**

```python
# while with counters
i = 0
while i < 10:
    print(i)
    i += 1

# while with user input
response = ""
while response != "exit":
    response = input("Command: ")

# while with conditions
while not done:
    process()
    done = check_status()
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `while`

- Universal programming concept
- Every language has temporal-conditional expressions
- Well-established translations globally
- Clear distinction from "if" and "for" in most languages

**For this term:** EASY

**Rationale:** The concept of "repeat while condition is true" exists in all programming languages and natural languages. Every language can express "during the time that X, do Y." Translation is straightforward: use the temporal conjunction for "while."

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

The only consideration: ensuring your translation captures the DURATIVE aspect (ongoing repetition), not just a single conditional test like "if."

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures REPEATED EXECUTION while condition is true?
- [ ] Expresses DURATION/CONTINUITY (not just single test)?
- [ ] Clearly different from "if" (single test) and "for" (iteration)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (temporal conjunction)?
- [ ] Expresses duration + condition (not just condition)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python keywords)?

### 3. Consistency

- [ ] Distinct from `if` translation (different words for different concepts)?
- [ ] Compatible with other loop keywords (`for`, `break`)?
- [ ] Aligns with how loops are expressed in target language?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common temporal word)?

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
term: while
language: es
translation: mientras
form: temporal_conjunction
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "mientras" is the standard temporal conjunction for "while" - expressing duration with condition. It clearly distinguishes from `si` (if - single test) and captures the repeated nature of the loop. Universally used in Spanish programming education.

**Alternatives considered:**

1. `durante` (during) - Too focused on duration, loses conditional aspect
2. `cuando` (when) - Too focused on timing, less clearly durative
3. `hasta` (until) - Opposite logic (negative condition)

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH for this term. Temporal-conditional "while" loops are universal, and all languages have natural expressions for this concept.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-10
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
