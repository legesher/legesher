# Python Builtin: `IndexError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`IndexError` is a built-in exception raised when attempting to access a sequence (list, tuple, string) using an index that is out of range. It signals that the requested position doesn't exist in the sequence, typically because the index is negative beyond the sequence start or positive beyond its end.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Accessing out-of-range index raises IndexError
numbers = [10, 20, 30]
print(numbers[5])  # Raises IndexError: list index out of range
```

**What this does:** Attempting to access an index that doesn't exist in a list raises an `IndexError` exception. The list has indices 0, 1, 2, but index 5 is beyond the list's bounds.

### Example 2: Common Pattern

```python
# Catching IndexError with try-except
numbers = [10, 20, 30]

try:
    value = numbers[10]
except IndexError:
    print("Index out of range, using default")
    value = 0

# Safe access with length check
if len(numbers) > 5:
    value = numbers[5]
else:
    value = 0  # Default value

# IndexError with negative indices
print(numbers[-10])  # Raises IndexError (too negative)
```

**What this does:** `try-except` blocks catch `IndexError` to handle out-of-range access gracefully. Checking length before accessing prevents `IndexError`. Negative indices can also cause `IndexError` if they exceed the sequence start.

### Example 3: Edge Case

```python
# IndexError with different sequence types
text = "Hello"
print(text[10])  # Raises IndexError: string index out of range

# IndexError with tuples
coordinates = (5, 10, 15)
print(coordinates[5])  # Raises IndexError: tuple index out of range

# IndexError when removing from list during iteration
numbers = [1, 2, 3, 4, 5]
numbers.pop()  # Removes last element
print(numbers[4])  # Raises IndexError: was valid, now out of range

# Empty sequence always raises IndexError
empty = []
print(empty[0])  # Raises IndexError: list index out of range
```

**What this shows:** `IndexError` occurs with all sequence types (lists, tuples, strings). Empty sequences always raise `IndexError` for any index. Modifying sequences during access can cause previously valid indices to become invalid.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `KeyError` - Raised when dictionary key doesn't exist
2. `AttributeError` - Raised when attribute access fails
3. `ValueError` - Raised when argument has wrong value
4. `TypeError` - Raised when operation applied to wrong type

**Pattern rule:** Exception classes should use noun forms, typically ending with "Error" in English. Translations should convey both the error type and the specific problem domain (index, key, attribute, etc.).


---

## Etymology (Brief)

**English Origin:** Compound word (Latin + Latin-derived)

**Root meaning:** "Index" comes from Latin "index" meaning "pointer, indicator, forefinger." In computing, an "index" is the numeric position used to access elements in ordered sequences. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** `IndexError` clearly identifies the problem: a sequence index access failed because the position doesn't exist. The name follows Python's convention of combining the problem domain ("Index") with "Error" to create descriptive exception names that help developers quickly understand what went wrong.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`IndexError` is raised by Python when code attempts to access a sequence element using an invalid index. Sequences (lists, tuples, strings, and other ordered collections) store elements in positions numbered from 0 to length-1. When you use bracket notation (`sequence[index]`) with an index outside this valid range, Python raises `IndexError` to signal the access failed.

This exception is a subclass of `LookupError`, which is the parent class for all exceptions raised when a lookup or indexing operation fails. `IndexError` is specific to sequence operations with numeric indices, distinguishing it from `KeyError` (for dictionary keys) and other lookup failures.

Understanding `IndexError` is fundamental because sequences are core to Python programming. Lists store collections of items, strings are sequences of characters, and tuples hold immutable data. Learning to anticipate potential `IndexError` situations (through length checks, proper loop bounds, or exception handling) is essential for writing robust Python code.

**Key behaviors:**

1. **Raised on out-of-bounds access:** The primary trigger is using bracket notation with an index that's either negative beyond the sequence start or positive beyond the sequence end. Valid indices range from `-len(sequence)` to `len(sequence)-1`.

2. **Applies to all sequence types:** Lists, tuples, strings, ranges, and any custom sequence types all raise `IndexError` for invalid indices. The error message indicates which sequence type caused the error (e.g., "list index out of range" vs "string index out of range").

3. **Empty sequences always error:** An empty sequence (length 0) has no valid indices, so any index access raises `IndexError`. This is a common edge case that requires checking `if len(sequence) > 0` before accessing.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (error type + problem domain)
- **Action vs State:** STATE - describes an error condition, not an action
- **Temporal aspect:** Instantaneous - occurs at moment of failed access

### Recommended Form

**Primary recommendation:** Use compound noun combining the concept of "index" with "error." Maintain capitalization that matches Python's convention (PascalCase for exception classes in English).

**Forms to AVOID:**

- ❌ Using verb forms ("IndexOutOfBounds") - exceptions are nouns, not actions
- ❌ Generic "error" without specifying "index" - loses important context
- ❌ Overly long descriptions - should be concise, 1-3 words maximum

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Book index (alphabetical listing at end of book)
- ❌ Meaning 2: Economic index (S&P 500, cost of living index)
- ❌ Meaning 3: Finger (index finger)
- ✅ Meaning 4: **SEQUENCE POSITION** (numeric position in ordered collection)

**Example:**

English "index" can mean:

1. "Check the book's index for page numbers" (book index) ❌
2. "The stock market index rose today" (economic indicator) ❌
3. "Point with your index finger" (anatomy) ❌
4. `numbers[5]` where 5 is the index ✅ **This is the Python meaning**

**Your translation should capture meaning #4: a numeric position in a sequence, NOT alphabetical listings, economic indicators, or anatomy.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `IndexError`, check these translations:**

- [ ] `list` - The list type that uses indices
- [ ] `tuple` - The tuple type that uses indices
- [ ] `KeyError` - Similar exception for dictionaries (should follow same error naming pattern)
- [ ] `LookupError` - Parent exception class for lookup failures

**Consistency rule:**

All exception classes ending in "Error" should use the same structure in translations. Whatever compound pattern `IndexError` uses, `KeyError` and `AttributeError` should follow it with the same error word and the same compound order - maintaining consistent pattern.


### Functional relationships

**This term works WITH:**

1. **Sequence access operations**:

```python
items = [10, 20, 30]
value = items[5]  # Raises IndexError
```

2. **Exception handling**:

```python
try:
    value = items[index]
except IndexError:
    print("Index out of range")
```

**Common pairing:**

```python
# IndexError with lists
numbers = [1, 2, 3]
print(numbers[10])  # Raises IndexError

# IndexError with strings
text = "Hello"
print(text[20])  # Raises IndexError

# Catching IndexError
try:
    value = numbers[10]
except IndexError:
    value = None
    print("Index not found")

# Preventing IndexError with bounds checking
if 0 <= index < len(numbers):
    value = numbers[index]
else:
    value = None

# IndexError with negative indices
print(numbers[-10])  # Raises IndexError (too negative)

# IndexError with empty sequences
empty = []
print(empty[0])  # Raises IndexError
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `IndexError`

- "Index" has multiple meanings (book index, economic index, anatomy, position)
- Need to convey compound concept (index + error)
- Must maintain consistency with other exception names
- Technical term that may vary by region's CS education

**For this term:** MEDIUM

**Rationale:** While the concept is well-established in computer science, translating "index" requires understanding the sequence/position context. Different languages may use different words for numeric positions. The compound structure needs to feel natural while maintaining technical clarity and consistency with other exception translations.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures SEQUENCE INDEX concept (not book index or economic index)?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Would a developer understand this is about out-of-range sequence access?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Matches pattern of other exception translations?
- [ ] Same structure as `KeyError`, `AttributeError` translations?
- [ ] Aligns with `list`, `tuple` type terminology?

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
term: IndexError
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
