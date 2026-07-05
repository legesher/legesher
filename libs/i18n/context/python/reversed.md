# Python Builtin Function: `reversed` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** verb
**Python Version:** 3.x+
**Difficulty:** LOW

---

## Quick Summary

The `reversed()` function in Python returns a reverse iterator that accesses elements of a sequence in reverse order. It doesn't modify the original sequence but provides a memory-efficient way to iterate backward through lists, strings, tuples, and other reversible objects.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Reverse a list
numbers = [1, 2, 3, 4, 5]
reversed_numbers = list(reversed(numbers))
print(reversed_numbers)  # Output: [5, 4, 3, 2, 1]
print(numbers)  # Output: [1, 2, 3, 4, 5] (original unchanged)
```

**What this does:** `reversed()` creates an iterator that yields elements backward. Wrapping with `list()` converts the iterator to a list. The original sequence remains unchanged - `reversed()` is non-destructive.

### Example 2: Common Pattern

```python
# Iterate in reverse without creating new list
for num in reversed([10, 20, 30]):
    print(num)
# Output: 30, 20, 10

# Reverse a string
text = "Python"
reversed_text = "".join(reversed(text))
print(reversed_text)  # Output: nohtyP
```

**What this does:** Using `reversed()` directly in a loop is memory-efficient - it doesn't create a reversed copy. For strings, combine `reversed()` with `join()` since strings are immutable.

### Example 3: Edge Case

```python
# Works with range objects
for i in reversed(range(5)):
    print(i)  # Output: 4, 3, 2, 1, 0

# Custom objects with __reversed__ method
class Countdown:
    def __init__(self, start):
        self.start = start
    def __reversed__(self):
        return iter(range(self.start, -1, -1))

for n in reversed(Countdown(3)):
    print(n)  # Output: 3, 2, 1, 0
```

**What this shows:** `reversed()` works with any object implementing `__reversed__()` or supporting sequence protocol with `__len__()` and `__getitem__()`. Custom classes can define their own reverse iteration behavior.

---

## Pattern Classification

**This term is:** TRANSFORMATION FUNCTION (Iterator Generator)

**Similar terms in this pattern:**

1. `sorted` - Returns sorted sequence (ordering transformation)
2. `enumerate` - Adds indices to items (enumeration transformation)
3. `zip` - Combines sequences (pairing transformation)

**Pattern rule:** Iterator-generating functions should use past participle or adjective forms that describe the resulting state. "Reversed" describes how elements are accessed - in reverse order.


---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** From Latin "reversus" (past participle of "revertere"), meaning "turned back, reversed." "Re-" (back) + "vertere" (to turn). In computing, "reverse" means accessing data in opposite order from normal.

**Why Python uses this:** "Reversed" as a past participle adjective describes the state of the iteration - elements are accessed in reverse. The -ed form follows Python's pattern for functions returning transformed views (`sorted`, `reversed`), distinguishing them from in-place methods (`.reverse()`, `.sort()`).

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `reversed()` function returns a reverse iterator object that yields elements from a sequence in reverse order. Unlike the `.reverse()` method which modifies a list in-place, `reversed()` is non-destructive and works with any sequence type (lists, tuples, strings, ranges) and custom objects implementing the reverse iteration protocol.

Internally, `reversed()` first checks if the object has a `__reversed__()` method and calls it if present. If not, it uses the sequence protocol (`__len__()` and `__getitem__()`) to iterate backward by index. This makes `reversed()` flexible - it works with built-in sequences and custom classes.

The function returns an iterator, not a list, making it memory-efficient. For large sequences, you can iterate in reverse without creating a reversed copy. If you need a reversed list, convert the iterator with `list(reversed(seq))`. This lazy evaluation approach is consistent with Python's iterator protocol.

**Key behaviors:**

1. **Returns iterator:** `reversed()` returns an iterator object, not a list. This means you can iterate over it once, or convert to list/tuple/etc. Memory-efficient for large sequences.

2. **Non-destructive:** Original sequence remains unchanged. Unlike `.reverse()` method which modifies list in-place, `reversed()` creates new iteration without modifying source.

3. **Requires reversible object:** Works with sequences (list, tuple, string, range) and objects with `__reversed__()` or `__len__()`+`__getitem__()`. Raises TypeError for non-reversible objects like sets or non-sequence iterators.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Past participle / adjective (describing result state)
- **Action vs State:** STATE description - describes how iteration proceeds
- **Temporal aspect:** Completed transformation - elements are in reversed order

### Recommended Form

**Primary recommendation:** Use past participle or adjective form meaning "reversed" or "inverted." This describes the state of the iteration order, not the action of reversing. Matches Python's pattern of using -ed forms for non-destructive transformations.

**Forms to AVOID:**

- ❌ Using infinitive "to reverse" - suggests action, but this describes resulting state
- ❌ Using "backward" alone - less specific than "reversed"
- ❌ Using same form as in-place `.reverse()` method - these are different operations

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Undone/reverted" (reversed a decision)
- ✅ Meaning 2: **IN OPPOSITE ORDER** (reversed sequence)
- ❌ Meaning 3: "Turned around physically" (reversed car)

**Example:**

English "reversed" can mean:

1. "The court reversed its decision" (undo/overturn) ❌
2. "`reversed([1,2,3])` gives [3,2,1]" (opposite order) ✅ **This is the Python meaning**
3. "He reversed the car into the garage" (backward motion) ❌

**Your translation should capture meaning #2: accessing elements in opposite order from normal.**

Focus on order reversal, not physical reversal or decision reversal.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `reversed`, check these translations:**

- [ ] `sorted` - Similar non-destructive function; should use same grammatical form (past participle)
- [ ] `.reverse()` - In-place list method; should use different form to show distinction
- [ ] `enumerate` - Iterator-generating function; should have compatible pattern

**Consistency rule:**

Functions returning transformed iterators (`reversed`, `sorted`, `enumerate`, `zip`) should use consistent grammatical patterns. Past participle forms like "reversed" and "sorted" should align. Distinguish from in-place methods using verb forms.

**Example:**

If you translate `reversed` as past participle ("invertido"), then:

- `sorted` should also be past participle ("ordenado")
- `.reverse()` method should use verb form ("invertir")
- NOT: `reversed` participle + `sorted` verb (inconsistent ❌)

### Functional relationships

**This term works WITH:**

1. **`reversed` + iteration**: Memory-efficient backward iteration

```python
for item in reversed(my_list):
    print(item)
```

2. **`reversed` + conversion**: Create reversed copies

```python
reversed_list = list(reversed(original))
reversed_string = "".join(reversed(text))
```

**Common pairing:**

```python
# Reverse iteration without copy
numbers = [1, 2, 3, 4, 5]
for n in reversed(numbers):
    print(n)  # 5, 4, 3, 2, 1

# Create reversed copy
reversed_numbers = list(reversed(numbers))

# Reverse string
text = "hello"
reversed_text = "".join(reversed(text))  # "olleh"

# Reverse range
for i in reversed(range(10)):
    print(i)  # 9, 8, 7, ..., 0

# Compare with in-place reverse
numbers.reverse()  # Modifies numbers in-place
print(numbers)  # [5, 4, 3, 2, 1]
```

---

## Confidence Calibration

**Translation Difficulty: LOW**

### LOW (Equivalent to EASY-MEDIUM)

- Clear concept with established translations
- Most languages have words for "reversed"
- Slight complexity in choosing right grammatical form
- **AI confidence should be HIGH**

### Why LOW for `reversed`

- Universal concept (reversing order exists in all languages)
- "Reverse" is basic spatial/order concept
- Well-established in programming terminology
- Main challenge is past participle vs infinitive distinction

**For this term:** LOW

**Rationale:** Reversing order is a universal concept with clear translations. The key is choosing past participle form (describing state) rather than infinitive (describing action), matching Python's `reversed` vs `.reverse()` distinction.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Minor consideration: Distinguish between function `reversed()` (returns iterator) and method `.reverse()` (in-place modification) in translation if language allows.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures REVERSE ORDER concept (backward iteration)?
- [ ] Understood as non-destructive (returns iterator)?
- [ ] Distinguishes from in-place `.reverse()` method?

### 2. Linguistic Correctness

- [ ] Correct part of speech (past participle/adjective)?
- [ ] Correct form (not infinitive verb)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Matches pattern of `sorted` (similar non-destructive function)?
- [ ] Uses past participle like other result-state functions?
- [ ] Different from `.reverse()` method form?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common reversal term)?

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
term: reversed
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
