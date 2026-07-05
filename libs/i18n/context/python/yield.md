# Python Keyword: `yield` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** verb
**Python Version:** 2.2+ (generators), 3.3+ (yield from)
**Difficulty:** HARD

---

## Quick Summary

The `yield` keyword in Python creates generator functions that produce values lazily one at a time, pausing execution after each value and resuming when the next value is requested. Unlike `return` which exits a function, `yield` suspends the function and remembers its state for later resumption.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Simple generator function
def count_up_to(n):
    i = 1
    while i <= n:
        yield i  # Pause and return i
        i += 1   # Resume here on next call

counter = count_up_to(3)
print(next(counter))  # 1
print(next(counter))  # 2
print(next(counter))  # 3
```

**What this does:** The `yield i` statement pauses the function and returns `i` to the caller. When `next()` is called again, execution resumes right after the `yield`, increments `i`, and loops back. The function remembers its state (variable values, execution position) between yields.

### Example 2: Common Pattern

```python
# Generator for large sequences (memory efficient)
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# Use only what you need
fib = fibonacci()
for i in range(10):
    print(next(fib), end=" ")
# Prints: 0 1 1 2 3 5 8 13 21 34

# Generator in for loop
def squares(n):
    for i in range(n):
        yield i ** 2

for square in squares(5):
    print(square)  # 0, 1, 4, 9, 16
```

**What this does:** Generators are memory-efficient for large or infinite sequences. Instead of creating a full list in memory, `yield` produces values on-demand. The `fibonacci()` generator is infinite but consumes minimal memory because values are generated as needed.

### Example 3: Edge Case

```python
# Multiple yields in one function
def step_counter():
    print("Starting")
    yield 1
    print("After first yield")
    yield 2
    print("After second yield")
    yield 3
    print("Done")

gen = step_counter()
print(next(gen))  # Prints: Starting, then returns 1
print(next(gen))  # Prints: After first yield, then returns 2
print(next(gen))  # Prints: After second yield, then returns 3
# next(gen)       # Would print: Done, then raise StopIteration

# yield from (Python 3.3+)
def delegate():
    yield from range(3)  # Delegate to another generator
    yield from [10, 20]

list(delegate())  # [0, 1, 2, 10, 20]
```

**What this shows:** A function can have multiple `yield` statements. Each `next()` call runs until the next `yield`. When the function ends naturally, `StopIteration` is raised. `yield from` (Python 3.3+) delegates to another iterable, yielding all its values.

---

## Pattern Classification

**This term is:** ACTION KEYWORD (Generator Control)

**Similar terms in this pattern:**

1. `return` - Exits function and returns value (yield pauses and returns)
2. `break` - Exits loop (yield doesn't exit, it pauses)
3. `await` - Pauses async function (similar pause/resume, but for async)

**Pattern rule:** Function control keywords that affect execution flow should use verb forms (infinitive). `yield` performs an action: pause function, return value, and enable resumption. It's a control flow verb.


---

## Etymology (Brief)

**English Origin:** Old English via Germanic

**Root meaning:** Old English "gieldan" (to pay, give, render) became Middle English "yelden," then modern "yield." Meanings include: produce/bear (crops), give way/surrender, produce output. In programming, "yield" means "produce/give a value" (like crops yielding harvest).

**Why Python uses this:** "Yield" captures the generator concept perfectly: producing values (like a field yields crops) without fully expending the source. A generator yields values over time, not all at once. The agricultural metaphor fits: gradual production. "Yield" also suggests temporary surrender of control—the function yields control back to the caller, then resumes later. The term comes from CLU (1970s), which pioneered iterators with yield semantics.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `yield` keyword transforms an ordinary function into a generator function. When you call a generator function, it doesn't execute immediately. Instead, it returns a generator object (iterator). Each time you call `next()` on the generator (or loop over it with `for`), the function executes until it hits a `yield` statement, which pauses execution and returns the yielded value.

The function's state (local variables, execution position) is frozen at the `yield` point. When `next()` is called again, execution resumes immediately after the `yield`, as if the function never stopped. This continues until the function ends naturally (implicitly returns `None`, which raises `StopIteration`) or executes a `return` statement.

Generators are powerful for memory efficiency (large/infinite sequences), lazy evaluation (compute only when needed), and pipeline processing (chain multiple generators). Unlike functions that return lists, generators compute values on-demand, avoiding memory overhead of storing entire sequences.

**Key behaviors:**

1. **Pause and resume:** Unlike `return` which exits the function permanently, `yield` pauses the function, retaining all local state. The next `next()` call resumes from the exact `yield` point. This enables generators to remember where they are in a loop or computation.

2. **Creates generator object:** Any function containing `yield` becomes a generator function. Calling it returns a generator object (iterator), not the function's return value. You must iterate or call `next()` to get values. This is fundamentally different from normal functions.

3. **Memory efficiency:** Generators evaluate lazily—values are produced one at a time, not stored in memory all at once. An infinite sequence (`while True: yield x`) is possible because values are generated as requested. This makes generators ideal for large datasets, streams, or infinite sequences.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Intransitive verb (can take object - what to yield)
- **Action vs State:** ACTION - produces/gives value and pauses
- **Temporal aspect:** Iterative/repeated - happens multiple times, not once

### Recommended Form

**Primary recommendation:** Use infinitive verb meaning "to yield," "to produce," or "to give." Focus on the production/giving aspect, suggesting iterative delivery of values, not one-time return. The term should convey gradual output over time.

**Forms to AVOID:**

- ❌ Using "surrender" - too militaristic, misses production aspect
- ❌ Using "pause" - describes mechanism but not purpose (producing values)
- ❌ Using "harvest" - too agricultural, not technical enough

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Surrender/give up" (admit defeat - "yield to pressure")
- ❌ Meaning 2: "Give way" (traffic - "yield to oncoming traffic")
- ✅ Meaning 3: **"PRODUCE VALUES ITERATIVELY"** (generate output gradually)

**Example:**

English "yield" can mean:

1. "Yield to enemy forces" (surrender/give up) ❌
2. "Yield at the intersection" (give way to traffic) ❌
3. "The field yields crops" (produce output) ✅ Similar to Python meaning
4. "The function yields values" (generator produces values iteratively) ✅ **This is the Python meaning**

**Your translation should capture meaning #3-4: iteratively producing values, pausing between productions, enabling lazy evaluation and memory-efficient sequences.**

Key semantic components:

- **Production:** Creating/giving values
- **Iterative:** Multiple times, not once
- **Pause/resume:** Temporary suspension with state retention
- **Lazy:** Values produced on-demand, not all at once

The agricultural metaphor is apt: fields yield crops over time (harvest season), not all at once instantly. Similarly, generators yield values over time (iteration), not all values instantly (like `return [list]`).

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `yield`, check these translations:**

- [ ] `return` - Both produce function output; yield pauses, return exits; should use similar verb forms
- [ ] `await` - Similar pause/resume for async (yield for sync generators, await for async)
- [ ] `def` - Defines functions; yield makes them generators; related function concepts
- [ ] `GeneratorExit` - Raised inside generators on `close()`; shares generator vocabulary, no error word

**Consistency rule:**

Function output keywords (`return`, `yield`) should both use verb forms (infinitive). They perform actions that produce values from functions. `yield` and `await` both do pause/resume, so similar linguistic structure helps (both verbs).


### Functional relationships

**This term works WITH:**

1. **Generator iteration:** `next()`, `for` loop

```python
def gen():
    yield 1
    yield 2

g = gen()
next(g)  # 1
next(g)  # 2
```

2. **`yield from`:** Delegate to sub-generator (Python 3.3+)

```python
def sub():
    yield from range(5)
```

**Common pairing:**

```python
# Infinite sequence
def infinite_counter():
    n = 0
    while True:
        yield n
        n += 1

# Generator expression (similar to yield)
squares = (x**2 for x in range(10))  # Generator, not list

# Generator pipeline
def numbers():
    for i in range(10):
        yield i

def squares(nums):
    for n in nums:
        yield n ** 2

def evens(nums):
    for n in nums:
        if n % 2 == 0:
            yield n

# Chain generators
result = evens(squares(numbers()))

# File reading (memory efficient)
def read_large_file(path):
    with open(path) as f:
        for line in f:
            yield line.strip()

# Fibonacci generator
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

# yield from delegation
def flatten(nested_list):
    for item in nested_list:
        if isinstance(item, list):
            yield from flatten(item)  # Recursive delegation
        else:
            yield item

# Generator with send() (advanced)
def echo():
    while True:
        value = (yield)
        print(f"Received: {value}")
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

### HARD

- No direct equivalent in some languages
- May need compound term or explanation
- Concept doesn't exist universally
- **AI confidence should be MEDIUM, human review recommended**

### Why HARD for `yield`

- Advanced Python feature (generators are intermediate/advanced)
- Not all languages have generator/yield concept
- Multiple English meanings create ambiguity
- Must distinguish from "return" (similar but different)
- "Yield" metaphor (agriculture → programming) may not translate well
- Concept of pause/resume with state retention is sophisticated

**For this term:** HARD

**Rationale:** Generators are an advanced feature. While "yield" has clear agricultural/production meanings, translating the programming concept requires understanding pause/resume semantics. Some languages may not have established generator terminology in CS education. Translation must capture both "produce value" and "pause execution" aspects. Human review recommended to ensure chosen term resonates with native speakers familiar with generators.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures ITERATIVE PRODUCTION concept (produce values over time)?
- [ ] Suggests PAUSE/RESUME mechanism?
- [ ] Distinguishes from `return` (one-time exit)?
- [ ] Emphasizes lazy/on-demand generation?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb, not noun)?
- [ ] Correct form (infinitive)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python keywords)?

### 3. Consistency

- [ ] Matches pattern of other function output keywords (`return`)?
- [ ] Uses verb form like other action keywords?
- [ ] Aligns with generator terminology in target language CS education?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Conveys production/generation concept?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional?
- [ ] Avoids overly agricultural metaphors (unless natural)?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: yield
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
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
