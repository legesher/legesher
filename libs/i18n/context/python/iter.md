# Python Builtin Function: `iter` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** verb/noun
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

The `iter` function creates an iterator object from an iterable (list, tuple, string, etc.) or calls a function repeatedly until a sentinel value is reached. It's the starting point for iteration - converting collections into iterators that can be traversed one element at a time with `next()`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Create iterator from list
numbers = [1, 2, 3]
iterator = iter(numbers)
print(next(iterator))  # Output: 1
print(next(iterator))  # Output: 2
```

**What this does:** `iter()` converts an iterable (like a list) into an iterator object. The iterator can then be traversed with `next()`, retrieving one element at a time.

### Example 2: Common Pattern

```python
# Manual iteration
data = [10, 20, 30]
it = iter(data)
for value in it:
    print(value)

# String iteration
text = "abc"
chars = iter(text)
print(next(chars))  # 'a'
print(next(chars))  # 'b'
```

**What this does:** While for loops create iterators automatically, `iter()` lets you create them explicitly. This gives manual control over iteration. Works with any iterable type.

### Example 3: Edge Case

```python
# Callable with sentinel
from random import randint
def roll_die():
    return randint(1, 6)

# Roll until we get 6
rolls = iter(roll_die, 6)
for roll in rolls:
    print(roll)  # Prints rolls until 6 appears (6 stops iteration)

# File reading until empty line
with open('file.txt') as f:
    for line in iter(f.readline, '\n'):
        print(line, end='')
```

**What this shows:** `iter()` has a two-argument form: `iter(callable, sentinel)` repeatedly calls the function until it returns the sentinel value. Advanced technique for creating iterators from functions.

---

## Pattern Classification

**This term is:** ACTION FUNCTION (Iterator Creation)

**Similar terms in this pattern:**

1. `next` - Gets items from iterator (iter creates, next retrieves)
2. `enumerate` - Wraps iterator with indices (uses iter internally)
3. `zip` - Combines iterators (creates from multiple iterables)

**Pattern rule:** Iterator protocol functions should use terms related to repetition, traversal, or cycling. "Iterate" means to repeat or go through sequentially.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `next` | siguiente | التالي | 下一个 | अगला |
| `range` | rango | نطاق | 范围 | परिसर |
| `iter` | **iterar** | **تكرار** | **迭代** | **पुनरावृत्ति** |

---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** Latin "iterare" meant "to repeat, do again," from "iterum" (again). "Iterate" means to perform repeatedly, to go through step by step.

**Why Python uses this:** "Iter" abbreviates "iterate," the computing term for traversing a collection element by element. Iteration is fundamental to programming - repeating operations on each item in a sequence. Python uses "iter" for brevity while maintaining clarity.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `iter()` function is Python's gateway to the iterator protocol. It takes an iterable (any object with `__iter__()` method) and returns an iterator (object with `__next__()` method). The iterator maintains state, remembering its position in the sequence, allowing you to traverse it with repeated `next()` calls.

For loops use `iter()` internally - when you write `for x in items`, Python calls `iter(items)` to get an iterator, then repeatedly calls `next()` until `StopIteration`. Using `iter()` explicitly gives you manual control over this process, useful for advanced iteration patterns.

The two-argument form `iter(callable, sentinel)` creates an iterator that repeatedly calls the function until it returns the sentinel value. This enables creative iteration patterns - reading file chunks, generating values until a condition, etc. - without writing custom iterator classes.

**Key behaviors:**

1. **Creates iterator:** Converts iterables (lists, strings, dicts) into iterators. Returns the iterator object, not the original collection. Multiple calls create independent iterators.

2. **Lazy evaluation:** Iterator doesn't compute all values upfront. Values are generated on-demand as `next()` is called. Efficient for large or infinite sequences.

3. **Two forms:** Standard `iter(iterable)` and sentinel `iter(callable, sentinel)`. Sentinel form enables function-based iteration without explicit loop control.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Verb (to iterate) or noun (iterator/iteration)
- **Action vs State:** ACTION - creates iterator, initiates iteration
- **Temporal aspect:** Initiates process of repeated traversal

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Infinitive verb | "iterar", "itérer" - to iterate |
| Germanic (de, nl, sv) | Infinitive or noun | "iterieren", "Iterator" |
| Slavic (ru, pl, uk) | Infinitive verb | "итерировать" - to iterate |
| Arabic | Verbal noun (masdar) | "تكرار" - iteration/repeating |
| Chinese | Verb | "迭代" - iterate/repeat |
| Hindi | Verbal noun | "पुनरावृत्ति" - iteration/repetition |

**Primary recommendation:** Use infinitive verb form meaning "to iterate" or "to repeat." This is an action that initiates iteration.

**Forms to AVOID:**

- ❌ Using "loop" alone - iteration is broader than loops
- ❌ Using "repeat" without technical context - too general

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `iterar`
- **Form:** Infinitive verb
- **Why it works:** Direct Spanish cognate of "iterate." Used in computing and mathematics. Clear, professional, universally understood in Spanish technical contexts.

**Arabic:**

- **Translation:** `تكرار` (takrār)
- **Form:** Verbal noun (masdar)
- **Why it works:** Standard Arabic for repetition/iteration. Form II verbal noun from root ك-ر-ر (k-r-r) meaning "to repeat." Used in computing contexts.

**Chinese:**

- **Translation:** `迭代` (dièdài)
- **Form:** Verb compound
- **Why it works:** Two characters: 迭 (repeatedly) + 代 (replace/generation). Standard Chinese computing term for iteration. Used in algorithms, loops, iterator discussions.

**Hindi:**

- **Translation:** `पुनरावृत्ति` (punarāvṛtti)
- **Form:** Verbal noun
- **Why it works:** Sanskrit compound: "पुनः" (again) + "आवृत्ति" (return/repetition). Formal term for iteration. Standard in Indian CS education.

### ❌ Common Translation Mistakes

**Mistake 1: Using "loop" instead of "iterate"**

- **Wrong:** `bucle` (Spanish - "loop")
- **Why wrong:** Loops use iterators, but iteration is more fundamental. `iter()` creates iterator objects; loops are one use of iterators. Different concepts.
- **Right:** `iterar` (to iterate - more fundamental)

**Mistake 2: Using generic "repeat"**

- **Wrong:** `repetir` (Spanish - "to repeat")
- **Why wrong:** Too general. "Repeat" doesn't convey the sequential traversal aspect. "Iterate" specifically means traversing through items one by one.
- **Right:** `iterar` (technical iteration concept)

**Mistake 3: Using "traverse" or "walk through"**

- **Wrong:** `recorrer` (Spanish - "to traverse/go through")
- **Why wrong:** While related, "iterate" is a specific technical term in computing. Most languages have computing-specific iteration terminology.
- **Right:** `iterar` (technical term, not general traversal)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO (specific technical term)

**"Iterate" in computing context:**

✅ **Traverse sequence element-by-element** - create iterator for sequential access

The term is unambiguous in programming contexts. It specifically refers to the iteration protocol and creating iterator objects.

**Your translation should:** Capture the technical computing concept of iteration (sequential traversal), not general repetition.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `iter`, check these translations:**

- [ ] `next` - Retrieves from iterators; iter creates, next retrieves
- [ ] `for` - Uses iter internally; should feel related
- [ ] `enumerate`, `zip`, `map` - Create/wrap iterators; all part of iteration ecosystem

**Consistency rule:**

Iterator protocol functions (`iter`, `next`, `enumerate`, `zip`) should use compatible terminology. They're all part of Python's iteration framework.

**Example:**

Spanish: `iterar` (iter), `siguiente` (next) - compatible iteration vocabulary ✅
Chinese: `迭代` (iter), `下一个` (next) - consistent sequential processing concepts ✅

### Functional relationships

**This term works WITH:**

1. **`iter` + `next`**: Manual iteration control

```python
it = iter([1, 2, 3])
print(next(it))  # 1
```

2. **`iter` with sentinel**: Function-based iteration

```python
from random import randint
dice = iter(lambda: randint(1, 6), 6)
```

**Common pairing:**

```python
# Basic iterator creation
numbers = [1, 2, 3, 4, 5]
it = iter(numbers)
print(next(it))  # 1
print(next(it))  # 2

# String iteration
text = "Hello"
chars = iter(text)
print(list(chars))  # ['H', 'e', 'l', 'l', 'o']

# Manual loop with iter and next
data = [10, 20, 30]
iterator = iter(data)
while True:
    try:
        value = next(iterator)
        print(value)
    except StopIteration:
        break

# Sentinel pattern
def read_chunk():
    # Returns data or '' when done
    pass

chunks = iter(read_chunk, '')
for chunk in chunks:
    process(chunk)

# Multiple independent iterators
numbers = [1, 2, 3]
it1 = iter(numbers)
it2 = iter(numbers)
print(next(it1))  # 1
print(next(it2))  # 1 (independent)
print(next(it1))  # 2

# Dict iteration (keys by default)
data = {'a': 1, 'b': 2}
keys = iter(data)
values = iter(data.values())
items = iter(data.items())

# Generator to iterator (already iterator)
def gen():
    yield 1
    yield 2

g = gen()
it = iter(g)  # Returns g itself
print(it is g)  # True (generators are iterators)
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `iter`

- "Iterate" is a technical term with established translations
- Some languages have multiple terms (iterate vs repeat vs traverse)
- Need computing-specific term, not general repetition
- Latin root gives cognates in Romance languages

**For this term:** MEDIUM

**Rationale:** The concept of iteration is fundamental in computing and most languages have technical terminology for it. However, choosing between "iterate," "repeat," "traverse," and other related terms requires understanding the technical distinction. Latin-based languages have cognates making this easier.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Key consideration: Need technical computing term for iteration protocol, not general repetition or traversal verbs.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures ITERATION protocol concept?
- [ ] Indicates creating iterator, not just repeating?
- [ ] Understood in computing/algorithm context?

### 2. Linguistic Correctness

- [ ] Correct part of speech (infinitive verb)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python functions)?

### 3. Consistency

- [ ] Compatible with `next` and iteration concepts?
- [ ] Matches how iteration is discussed in CS education?
- [ ] Aligns with programming terminology?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Clear technical meaning?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Professional technical term?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: iter
language: es
translation: iterar
form: infinitive_verb
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "iterar" is the direct cognate of "iterate," universally used in Spanish computing and mathematics. It clearly conveys the technical concept of traversing sequences element-by-element. Standard in Spanish CS education and programming communities.

**Alternatives considered:**

1. `repetir` (to repeat) - Too general, doesn't convey sequential traversal
2. `recorrer` (to traverse) - Valid but "iterar" more technical/precise
3. `iter` (keep English abbreviation) - Works but "iterar" is clearer

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH. "Iterate" is a well-established technical term with clear cognates in Romance languages and standard translations in other language families.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
