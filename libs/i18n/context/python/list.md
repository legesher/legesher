# Python Builtin Type: `list` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** noun (type constructor)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `list` type in Python represents an ordered, mutable collection of items. Lists can contain any mix of types, support indexing and slicing, and can grow or shrink dynamically. They're one of Python's most fundamental and versatile data structures.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Create a list
numbers = [1, 2, 3, 4, 5]
print(numbers[0])  # Output: 1 (first element)
print(len(numbers))  # Output: 5
```

**What this does:** Square brackets `[]` create a list. Lists are zero-indexed: first element is index 0. You can access elements by index and get the list's length with `len()`.

### Example 2: Common Pattern

```python
# Mutable - can be modified
fruits = ["apple", "banana"]
fruits.append("orange")  # Add to end
fruits[0] = "grape"      # Change first element
print(fruits)  # Output: ['grape', 'banana', 'orange']

# Mixed types allowed
mixed = [1, "hello", 3.14, True]
```

**What this does:** Lists are mutable - you can change them after creation. Methods like `.append()`, `.remove()`, `.insert()` modify the list in-place. Lists can contain different types mixed together.

### Example 3: Edge Case

```python
# Empty list
empty = []
also_empty = list()

# List comprehension (common creation pattern)
squares = [x**2 for x in range(5)]
print(squares)  # Output: [0, 1, 4, 9, 16]

# Nested lists
matrix = [[1, 2], [3, 4], [5, 6]]
print(matrix[0][1])  # Output: 2
```

**What this shows:** Create empty lists with `[]` or `list()`. List comprehensions provide concise creation syntax. Lists can contain other lists (nested structures). Each element accessed by index can itself be a list.

---

## Pattern Classification

**This term is:** TYPE CONSTRUCTOR / COLLECTION TYPE

**Similar terms in this pattern:**

1. `tuple` - Immutable ordered collection (like list but can't change)
2. `dict` - Key-value mapping collection
3. `set` - Unordered collection of unique items

**Pattern rule:** Collection type constructors should use noun forms naming the container. For `list`, use the word for "list" or "array" depending on language conventions.


---

## Etymology (Brief)

**English Origin:** Germanic

**Root meaning:** Old English "līste" meant "border, hem, strip of cloth." Through Old French "liste" (list, roll of names), it became English "list" - an ordered series of items. In computing, extended to ordered collection of data.

**Why Python uses this:** "List" is the common English term for ordered collections. Most programming languages use "list" or "array" for sequential data structures. Python chose "list" specifically for dynamic, mutable sequences (as opposed to "array" which suggests fixed-size in some languages).

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `list` type represents a dynamic, ordered, mutable sequence of elements. Lists maintain insertion order - elements stay in the order they were added. They're implemented as dynamic arrays internally, providing fast index access (O(1)) and efficient appending (amortized O(1)).

Lists can hold any Python objects: numbers, strings, other lists, functions, class instances, etc. Mixed types are allowed in a single list. Lists support slicing (`mylist[1:3]`), iteration (`for item in mylist`), and many built-in methods like `.append()`, `.extend()`, `.pop()`, `.remove()`, `.sort()`.

As mutable objects, lists can be modified in-place. This means `mylist.append(4)` changes the existing list rather than creating a new one. Lists are passed by reference - modifying a list inside a function affects the original. For immutable ordered collections, Python provides `tuple` type.

**Key behaviors:**

1. **Ordered and indexed:** Elements have a specific position. Index 0 is first element, index -1 is last. Slicing `[start:stop:step]` extracts sublists. Order is preserved across operations.

2. **Mutable:** Lists can grow (`.append()`, `.extend()`, `.insert()`) or shrink (`.pop()`, `.remove()`, `del list[i]`). Elements can be reassigned. This mutability makes lists efficient but requires caution when passing them between functions.

3. **Dynamic sizing:** Lists automatically grow to accommodate new elements. No need to pre-declare size. Behind the scenes, Python allocates extra space and reallocates when needed, keeping append operations fast on average.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (names a container type)
- **Action vs State:** STATE/CONTAINER - describes what holds data
- **Temporal aspect:** Timeless - a type is a permanent category

### Recommended Form

**Primary recommendation:** Use noun form meaning "list" or "array" (depending on CS conventions in your language). This should be the same word used for shopping lists, to-do lists, etc. - an ordered series of items.

**Forms to AVOID:**

- ❌ Using verb "to list" - should be noun naming the container
- ❌ Using "array" when "list" is more specific (depends on language conventions)
- ❌ Using overly technical terms not in common use

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Ship leaning to one side" (nautical)
- ✅ Meaning 2: **ORDERED SERIES OF ITEMS** (enumeration/collection)
- ❌ Meaning 3: "To enumerate verbally" (verb - "list the options")

**Example:**

English "list" can mean:

1. "The ship has a list to starboard" (tilt/lean) ❌
2. "A shopping list of groceries" (ordered series) ✅ **This is the Python meaning**
3. "Please list all requirements" (verb - to enumerate) ❌

**Your translation should capture meaning #2: an ordered collection or series of items.**

In most languages, context makes this clear - the data structure meaning dominates in programming contexts.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `list`, check these translations:**

- [ ] `tuple` - Similar ordered collection; should feel related
- [ ] `dict` - Different collection type; should use similar noun forms
- [ ] `set` - Another collection; should be consistent
- [ ] `append` - Common list method; should feel cohesive

**Consistency rule:**

All collection type constructors (`list`, `tuple`, `dict`, `set`) should use noun forms. They name containers/data structures, not actions.


### Functional relationships

**This term works WITH:**

1. **`list` + indexing**: Access elements

```python
items = [10, 20, 30]
print(items[0])  # 10
items[1] = 25    # modify
```

2. **`list` + methods**: Modify collections

```python
numbers = [1, 2]
numbers.append(3)
numbers.extend([4, 5])
```

**Common pairing:**

```python
# list creation
nums = [1, 2, 3]
empty = []
converted = list("abc")  # ['a', 'b', 'c']

# list methods
items = [1, 2, 3]
items.append(4)
items.pop()
items.insert(0, 0)

# list iteration
for item in items:
    print(item)

# list comprehension
squares = [x**2 for x in range(5)]

# list slicing
subset = items[1:3]
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity in technical context
- **AI confidence should be HIGH**

### Why EASY for `list`

- Universal concept (ordered collections exist everywhere)
- "List" is common everyday word in most languages
- Well-established in programming globally
- Clear semantic mapping

**For this term:** EASY

**Rationale:** The concept of a list (ordered series of items) is universal - shopping lists, to-do lists, etc. Every language has a word for this. In programming, "list" or "array" are standard terms. Translation is straightforward: use the common word for ordered collection.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Minor consideration: some languages distinguish "list" (dynamic) from "array" (fixed). Check CS education conventions for which term is standard for Python's dynamic lists.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures ORDERED COLLECTION concept?
- [ ] Understood as mutable, dynamic container?
- [ ] Distinguishes from tuple (immutable) and dict (key-value)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Matches pattern of other collection types (`tuple`, `dict`, `set`)?
- [ ] All collection types use noun forms?
- [ ] Aligns with how lists are discussed in target language CS?

### 4. Usability

- [ ] Short enough (1 word ideal)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common everyday word)?

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
term: list
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
