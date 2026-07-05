# Python Keyword: `for` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** conjunction/preposition
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `for` keyword in Python creates a loop that iterates over a sequence (list, string, range, etc.), executing a code block once for each element. It's Python's primary mechanism for iteration, automatically handling the mechanics of advancing through a collection.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Iterate over a list of numbers
for number in [1, 2, 3]:
    print(number)
# Output: 1, 2, 3 (each on separate line)
```

**What this does:** Takes each element from the list `[1, 2, 3]` one at a time, assigns it to the variable `number`, and executes the indented block. The loop automatically stops when all elements have been processed.

### Example 2: Common Pattern

```python
# Process each character in a string
name = "Python"
for char in name:
    print(f"Letter: {char}")
# Iterates 6 times, once per character
```

**What this does:** Demonstrates that `for` works with any iterable object, not just lists. Strings are iterable character-by-character. The loop variable `char` takes on each character's value in sequence.

### Example 3: Edge Case

```python
# Using range() to repeat an action N times
for i in range(5):
    print(f"Iteration {i}")
# Prints: Iteration 0, Iteration 1, ... Iteration 4
```

**What this shows:** The `range()` function creates a sequence of numbers, and `for` iterates over them. Note that `range(5)` produces 0-4 (5 numbers), not 1-5. This is Python's 0-indexed iteration pattern. If you don't need the loop variable, convention uses `_` as the name: `for _ in range(5):`.

---

## Pattern Classification

**This term is:** ITERATION KEYWORD

**Similar terms in this pattern:**

1. `while` - Condition-based loop (repeats while condition is true)
2. `in` - Membership test operator, also used within `for` loop syntax
3. `break` - Loop control that exits `for` or `while` loops early

**Pattern rule:** Iteration keywords may use preposition or verb forms depending on target language's natural loop phrasing. The word should suggest "going through" or "traversing" a collection.


---

## Etymology (Brief)

**English Origin:** Latin via French

**Root meaning:** Latin "pro" meant "for, on behalf of, instead of." Through Old French "por," it became English "for" with meanings including "in place of," "because of," and "in respect to." In loop contexts, "for each item" evolved from "in respect to each item."

**Why Python uses this:** The phrase "for each X in collection" is natural English for iteration. Guido van Rossum chose `for` to create readable loop syntax that mimics how English speakers would describe the process: "for each number in the list, do this." This contrasts with C-style `for(i=0; i<n; i++)` which is more mechanical.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `for` loop in Python implements iteration-based repetition. Unlike condition-based loops (`while`), `for` loops are designed to process each element in a sequence or iterable object. Python's `for` loop uses the iterator protocol: any object that implements `__iter__()` and `__next__()` can be used with `for`.

The syntax `for variable in iterable:` breaks down as: the loop variable (`variable`) is assigned each successive value from the iterable object. The indented block executes once per assignment. When the iterable is exhausted (no more elements), the loop terminates and execution continues with the next unindented line.

Python's `for` loop is fundamentally different from C/Java-style `for` loops. There is no explicit initialization, condition testing, or increment expression. Instead, Python's `for` is a "foreach" loop - it always means "for each element." To get C-style behavior, Python programmers use `range()` to generate sequences: `for i in range(10):` mimics traditional counter-based loops.

**Key behaviors:**

1. **Automatic iteration:** You never manually advance the iterator or check bounds. Python handles all iteration mechanics internally, preventing off-by-one errors.
2. **Works with any iterable:** Lists, strings, tuples, dictionaries, files, `range()` objects, custom objects - anything implementing the iterator protocol works with `for`.
3. **Loop variable scope:** The loop variable persists after the loop ends, holding the last assigned value. This is different from some languages where loop variables are block-scoped.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Preposition (in English) introducing an iteration clause, though this varies by language
- **Action vs State:** Hybrid - initiates repetitive action but frame is more prepositional ("for each")
- **Temporal aspect:** Repeated/iterative - the action happens multiple times, once per element

### Recommended Form

**Primary recommendation:** Use the target language's natural way to express "for each item" or "in respect to each element." This may be a preposition, a compound phrase, or even a verb form depending on how the language naturally expresses iteration.

**Forms to AVOID:**

- ❌ Using only "each" without "for" context - loses the iteration framing
- ❌ Using "to" instead of "for" - wrong prepositional meaning
- ❌ Overly verbose phrases (>3 words) - reduces readability

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Because, since" (causal - "I stayed home **for** I was sick")
- ❌ Meaning 2: "In favor of" (support - "Are you **for** or against?")
- ❌ Meaning 3: "Intended to benefit" (purpose - "This gift is **for** you")
- ❌ Meaning 4: "Duration" (time - "We talked **for** hours")
- ✅ Meaning 5: **DISTRIBUTIVE/ITERATIVE** - "in respect to each element" or "for every item in"

**Example:**

English "for" has many meanings:

1. "I voted **for** the proposal" (in favor) ❌
2. "I've lived here **for** ten years" (duration) ❌
3. "**For** each student, assign a locker" (distributive - iteration) ✅ **This is the Python meaning**

**Your translation should capture meaning #5: distributive iteration over a collection.**

In many languages, the word used for "duration" differs from the word for "in respect to each." Use the distributive/prepositional form, not the temporal duration form.

Example: some languages split English "for" across two prepositions (one for duration, one for purpose/distribution). For Python's `for`, use the purpose/distribution one.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `for`, check these translations:**

- [ ] `in` - The `for...in` pair must work together grammatically (preposition + preposition)
- [ ] `while` - Loop keywords should use compatible forms (both should feel like loop introducers)
- [ ] `range` - Often used with `for` loops, ensure natural phrasing

**Consistency rule:**

The `for` and `in` keywords work as a pair in Python syntax: `for item in collection`. Your translations must form a grammatically natural phrase in the target language.


### Functional relationships

**This term works WITH:**

1. **`for` + `in`**: Inseparable pair in Python's for-loop syntax

```python
my_list = [1, 2, 3]
for item in my_list:
    print(item)
```

2. **`for` + `range()`**: Common pattern for counting loops

```python
for i in range(10):
    print(i)
```

3. **`for` + `break`/`continue`**: Loop control statements

```python
data = [1, 2, -3, 4]
for x in data:
    if x < 0:
        break  # exit loop early
```

**Common pairing:**

```python
# for works with many iterable types
for item in [1, 2, 3]:        # list
    pass
for char in "hello":          # string
    pass
for key in {"a": 1, "b": 2}:  # dictionary keys
    pass
for i in range(5):            # range object
    pass
for x, y in [(1, 2), (3, 4)]: # unpacking tuples
    pass
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `for`

- Universal iteration concept
- Most languages have "for each" constructions
- Well-established in programming across languages
- Minor complexity: ensuring `for` and `in` pair naturally

**For this term:** EASY (with one caveat)

**Rationale:** While every language can express iteration, the specific grammatical construction varies. The challenge is ensuring `for` and `in` form a natural phrase together. However, this is well-documented in existing programming language translations, so there are clear precedents.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

The main question to ask: "Does `for X in Y` translate to a natural phrase in the target language using standard prepositions?" If yes, confidence should be HIGH.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures ITERATION concept (going through elements one by one)
- [ ] Conveys "for each" or distributive meaning
- [ ] Avoids temporal "during" or causal "because" meanings?

### 2. Linguistic Correctness

- [ ] Correct part of speech (preposition or appropriate equivalent)?
- [ ] Correct form (distributive/iterative, not temporal/causal)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python keywords)?

### 3. Consistency

- [ ] Pairs naturally with `in` translation (`for X in Y` reads naturally)?
- [ ] Matches pattern of loop keywords (`while`, etc.)?
- [ ] Aligns with how iteration is expressed in target language programming?

### 4. Usability

- [ ] Short enough (1-3 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember?

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
term: for
language: <target-language-code>
translation: <recommended-term>
form: <word-form>
confidence: <high|medium|low>
```

**Rationale (2-3 sentences):**

Explain why the recommended term carries this concept's semantic components in the target language — grounded in this brief's Concept Explanation and Ambiguity Resolution, never in another language's choice.

**Alternatives considered:**

List the candidate terms weighed in the target language and why each was rejected or kept.

**If confidence is not HIGH, explain:**

State what makes this term uncertain (no established native term, competing regional conventions, semantic gap) so review can prioritize it.


---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-10
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
