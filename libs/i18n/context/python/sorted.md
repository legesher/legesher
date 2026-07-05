# Python Builtin Function: `sorted` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** adjective/participle (ordering function)
**Python Version:** 3.x+
**Difficulty:** LOW

---

## Quick Summary

The `sorted` function in Python returns a new sorted list from any iterable. Unlike the `.sort()` method that modifies lists in-place, `sorted()` creates a new list leaving the original unchanged, and works with any iterable (lists, tuples, strings, etc.).

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Sort a list of numbers
numbers = [3, 1, 4, 1, 5, 9, 2]
result = sorted(numbers)
print(result)  # [1, 1, 2, 3, 4, 5, 9]
print(numbers)  # [3, 1, 4, 1, 5, 9, 2] (original unchanged)
```

**What this does:** Returns a new sorted list. The original list remains unchanged because `sorted()` creates a new list rather than modifying the original.

### Example 2: Common Pattern

```python
# Sort strings alphabetically
names = ["Charlie", "Alice", "Bob"]
sorted_names = sorted(names)
print(sorted_names)  # ['Alice', 'Bob', 'Charlie']

# Sort in reverse order
numbers = [3, 1, 4, 1, 5]
descending = sorted(numbers, reverse=True)
print(descending)  # [5, 4, 3, 1, 1]

# Sort with custom key function
words = ["apple", "pie", "zoo", "a"]
by_length = sorted(words, key=len)
print(by_length)  # ['a', 'pie', 'zoo', 'apple']
```

**What this does:** Demonstrates sorting strings, reverse sorting with `reverse=True`, and custom sorting with `key` parameter. Key function specifies what to sort by (here, length of strings).

### Example 3: Edge Case

```python
# Sort any iterable (not just lists)
tuple_data = (3, 1, 4, 1, 5)
result = sorted(tuple_data)  # Returns list: [1, 1, 3, 4, 5]

string = "python"
result = sorted(string)  # Returns list: ['h', 'n', 'o', 'p', 't', 'y']

# Sort complex objects
students = [
    {"name": "Alice", "grade": 85},
    {"name": "Bob", "grade": 92},
    {"name": "Charlie", "grade": 78}
]
by_grade = sorted(students, key=lambda s: s["grade"])
# Sorted by grade: Charlie(78), Alice(85), Bob(92)
```

**What this shows:** `sorted()` works on any iterable (tuples, strings, etc.) but always returns a list. Can sort complex objects using key functions or lambdas.

---

## Pattern Classification

**This term is:** TRANSFORMATION FUNCTION (Ordering/Rearranging)

**Similar terms in this pattern:**

1. `reversed` - Returns iterator with items in reverse order
2. `filter` - Returns filtered items based on condition
3. `map` - Returns transformed items based on function

**Pattern rule:** These transformation functions take iterables and return new sequences/iterators. They're named with past participles (sorted, reversed, filtered) suggesting the result of an action.


---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** From Latin "sors" (lot, fate, rank). "Sort" originally meant to separate by type or rank. "Sorted" is the past participle meaning "having been arranged in order."

**Why Python uses this:** "Sorted" is the past participle indicating the result of sorting action. The function name emphasizes that it returns a sorted result (like "filtered" returns filtered results). This distinguishes it from `.sort()` method which sorts in-place.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `sorted()` function takes any iterable and returns a new list with items arranged in ascending order. It implements a stable sorting algorithm (Timsort), meaning items that compare equal maintain their original relative order. Unlike the list method `.sort()` which modifies the list in-place, `sorted()` creates a new list leaving the original unchanged.

The function accepts optional parameters: `reverse=True` for descending order, and `key` for custom sorting logic. The key parameter takes a function that extracts a comparison key from each item (e.g., `key=len` sorts by length, `key=str.lower` for case-insensitive sorting).

`sorted()` works with any iterable—lists, tuples, strings, sets, dictionaries (sorts keys), files, generators—but always returns a list. For sorting items that aren't naturally comparable (like dicts), you must provide a key function. The function uses Python's comparison operators (`<`, `>`) to order items.

**Key behaviors:**

1. **Returns new list:** Always creates a new list, never modifies the original. This makes it safe to use on immutable types (tuples, strings) and preserves your original data. `sorted(my_tuple)` works even though tuples can't be sorted in-place.

2. **Works on any iterable:** Unlike `.sort()` which only works on lists, `sorted()` accepts any iterable input. `sorted("hello")`, `sorted({3,1,2})`, `sorted(range(5, 0, -1))` all work, producing sorted lists.

3. **Stable sort:** Equal items maintain their original relative order. If sorting `[(1, 'a'), (2, 'b'), (1, 'c')]` by first element, items with `1` will keep their relative order `('a')` before `('c')`.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Past participle/adjective (describes state of result)
- **Action vs State:** STATE - describes the resulting order, not the action
- **Temporal aspect:** Perfect/Completed - indicates sorting has been done

### Recommended Form

**Primary recommendation:** Use past participle or adjective form meaning "sorted," "ordered," or "arranged." This emphasizes the result (a sorted collection) rather than the action of sorting.

**Forms to AVOID:**

- ❌ Using infinitive "to sort" (function returns result, not action)
- ❌ Using noun "sort" or "order" (ambiguous)
- ❌ Using imperative "sort!" (this isn't a command, returns sorted result)

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "I sorted the mail" (past tense verb: did the action of sorting)
- ✅ Meaning 2: **"A sorted list"** (past participle/adjective: in sorted state)
- ❌ Meaning 3: "Things got sorted out" (idiom: resolved/fixed)
- ❌ Meaning 4: "He's sorted" (British slang: prepared/organized)

**Example:**

English "sorted" can mean:

1. "I sorted the papers yesterday" (past tense action) ❌
2. "Here's the sorted list" (adjective describing state) ✅ **This is the Python meaning**
3. "We sorted out our differences" (idiom: resolved) ❌
4. "I'm all sorted" (British slang: ready/prepared) ❌

**Your translation should capture meaning #2: describing something in a sorted/ordered state—the result of sorting, not the action of sorting.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `sorted`, check these translations:**

- [ ] `reversed` - Similar transformation function; should use compatible form
- [ ] `filter` - Similar transformation function; alignment in pattern
- [ ] `map` - Similar transformation function; should feel related
- [ ] `.sort()` method - Related but different (in-place vs new list)

**Consistency rule:**

Transformation functions that return results (`sorted`, `reversed`, `filter`) should use past participle or adjective forms indicating the result state. They describe what you get back, not the action.


### Functional relationships

**This term works WITH:**

1. **List sorting**: Primary use case

```python
numbers = [3, 1, 4]
result = sorted(numbers)  # New sorted list
```

2. **Custom sorting with key**: Advanced sorting

```python
words = ["apple", "pie", "zoo"]
by_length = sorted(words, key=len)
```

**Common pairing:**

```python
# Basic sorting
numbers = [3, 1, 4, 1, 5, 9, 2, 6]
ascending = sorted(numbers)  # [1, 1, 2, 3, 4, 5, 6, 9]

# Reverse sorting
descending = sorted(numbers, reverse=True)  # [9, 6, 5, 4, 3, 2, 1, 1]

# Sort strings (alphabetical)
names = ["Charlie", "Alice", "Bob", "David"]
sorted_names = sorted(names)  # ['Alice', 'Bob', 'Charlie', 'David']

# Case-insensitive sorting
words = ["Zebra", "apple", "Banana"]
sorted_words = sorted(words, key=str.lower)  # ['apple', 'Banana', 'Zebra']

# Sort by length
words = ["elephant", "dog", "cat", "butterfly"]
by_length = sorted(words, key=len)  # ['cat', 'dog', 'elephant', 'butterfly']

# Sort tuples by specific element
data = [(3, 'c'), (1, 'a'), (2, 'b')]
by_number = sorted(data, key=lambda x: x[0])  # [(1, 'a'), (2, 'b'), (3, 'c')]
by_letter = sorted(data, key=lambda x: x[1])  # [(1, 'a'), (2, 'b'), (3, 'c')]

# Sort dictionaries by value
scores = {"Alice": 85, "Bob": 92, "Charlie": 78}
by_score = sorted(scores.items(), key=lambda x: x[1])
# [('Charlie', 78), ('Alice', 85), ('Bob', 92)]

# Sort any iterable (always returns list)
sorted((3, 1, 4))  # From tuple: [1, 3, 4]
sorted("python")    # From string: ['h', 'n', 'o', 'p', 't', 'y']
sorted({3, 1, 4})   # From set: [1, 3, 4]

# Multiple sort keys
students = [
    ("Alice", 85, "A"),
    ("Bob", 85, "B"),
    ("Charlie", 90, "A")
]
# Sort by grade (descending), then name
by_grade_name = sorted(students, key=lambda s: (-s[1], s[0]))
```

---

## Confidence Calibration

**Translation Difficulty: LOW**

### LOW

- Common transformation concept
- Most languages have past participle for "sorted"
- Clear technical meaning
- **AI confidence should be HIGH**

**For this term:** LOW

**Rationale:** Sorting is a universal computing operation taught in all CS courses. The concept of a "sorted" collection exists in all languages, and most have clear past participle or adjective forms meaning "sorted," "ordered," or "arranged." The linguistic form (past participle describing result) is also universal.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures SORTED/ORDERED STATE concept (result, not action)?
- [ ] Would a native speaker understand this means "arranged in order"?
- [ ] Distinguishes from the action "to sort"?

### 2. Linguistic Correctness

- [ ] Correct part of speech (past participle/adjective)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Matches pattern of other transformation functions (`reversed`, `filter`)?
- [ ] Uses result-describing form (participle/adjective)?
- [ ] Aligns with how "sorted" is expressed in target language?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common term)?

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
term: sorted
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
