# Python Builtin Function: `enumerate` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** verb (iteration utility)
**Python Version:** 3.x+
**Difficulty:** LOW

---

## Quick Summary

The `enumerate` function in Python adds a counter to an iterable, returning an enumerate object that yields pairs of (index, item). It's used to get both the position and value when looping, avoiding manual counter management.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Loop with index and item
names = ["Alice", "Bob", "Charlie"]
for index, name in enumerate(names):
    print(f"{index}: {name}")
# Output:
# 0: Alice
# 1: Bob
# 2: Charlie
```

**What this does:** Provides both index (0, 1, 2...) and item value automatically. Much cleaner than manually tracking a counter variable.

### Example 2: Common Pattern

```python
# Start counting from 1 instead of 0
names = ["Alice", "Bob", "Charlie"]
for num, name in enumerate(names, start=1):
    print(f"{num}. {name}")
# Output:
# 1. Alice
# 2. Bob
# 3. Charlie

# Convert to list of tuples
items = ["apple", "banana", "cherry"]
indexed = list(enumerate(items))
print(indexed)
# [(0, 'apple'), (1, 'banana'), (2, 'cherry')]
```

**What this does:** `start` parameter customizes the starting index. `enumerate()` returns an iterator, but can be converted to list to see all pairs.

### Example 3: Edge Case

```python
# Works with any iterable
for i, char in enumerate("Python"):
    print(f"Character {i}: {char}")
# 0: P, 1: y, 2: t, 3: h, 4: o, 5: n

# Enumerate with zip (multiple iterables)
names = ["Alice", "Bob"]
ages = [25, 30]
for i, (name, age) in enumerate(zip(names, ages)):
    print(f"Person {i}: {name}, age {age}")

# Empty iterable
for i, item in enumerate([]):
    print(i, item)  # Never executes
```

**What this shows:** Works with strings, tuples, or any iterable. Combines well with `zip()` for multiple sequences. Handles empty iterables gracefully.

---

## Pattern Classification

**This term is:** ITERATION UTILITY (Enhancement Function)

**Similar terms in this pattern:**

1. `zip` - Combines multiple iterables element-wise
2. `map` - Applies function to each item in iterable
3. `filter` - Selects items based on condition

**Pattern rule:** Iteration utility functions should use verb forms (infinitive or present tense) describing what they do to sequences. They process iterables and return iterators.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `zip` | comprimir/empaquetar | ضغط | 压缩 | ज़िप |
| `map` | mapear | خريطة | 映射 | मैप |
| `enumerate` | **enumerar** | **تعداد** | **枚举** | **गिनती** |

---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** From Latin "enumerare" (to count out, reckon up). From "e-" (out) + "numerare" (to count, from "numerus" = number). Means to list items one by one or to count/name individually.

**Why Python uses this:** "Enumerate" means to count or list items systematically. The function literally enumerates (counts and names) each item in a sequence by pairing it with its position number. The term conveys both counting and listing aspects.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `enumerate()` function wraps an iterable and returns an iterator of tuples, where each tuple contains (index, item). It solves the common problem of needing both the position and value when iterating. Instead of manually maintaining a counter variable that you increment each loop, `enumerate()` provides the index automatically.

The function accepts a `start` parameter (default 0) to customize where counting begins. This is useful for 1-based numbering (like printing a numbered list for humans) or continuing from a specific index. The returned object is an enumerate iterator, which is memory-efficient—it generates pairs on-demand rather than creating a list of all pairs.

Common use cases include: numbering output for users (`"1. First item"`), tracking position while processing data, finding indices where conditions are met, and any scenario where you need "which item am I on?" while looping. It's more Pythonic than `for i in range(len(items))` pattern.

**Key behaviors:**

1. **Returns iterator of tuples:** Yields `(index, item)` pairs. Not a list—it's an iterator that generates pairs as needed. Convert with `list(enumerate(items))` if you need all pairs at once.

2. **Customizable start:** `start` parameter sets initial counter value. `enumerate(items, start=1)` begins at 1 instead of 0. Useful for human-readable numbering or continuing from a specific index.

3. **Works with any iterable:** Accepts lists, tuples, strings, sets, files, generators—anything iterable. Returns the same iterator type regardless of input type.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Verb (action of counting/listing items)
- **Action vs State:** ACTION - actively pairs items with numbers
- **Temporal aspect:** Progressive/Iterative - processes items one by one

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Infinitive | "enumerar", "énumérer" - to enumerate |
| Germanic (de, nl, sv) | Infinitive | "aufzählen", "opsommen" - to count/list |
| Slavic (ru, pl, uk) | Infinitive | "перечислить" - to enumerate |
| Arabic | Verbal noun (masdar) | "تعداد" - counting/enumeration |
| Chinese | Verb compound | "枚举" - enumerate/list items |
| Hindi | Infinitive/Verbal noun | "गिनती करना" - to count/enumerate |

**Primary recommendation:** Use infinitive verb form meaning "to enumerate," "to count," or "to list." This is an action function that does something to an iterable (adds counting).

**Forms to AVOID:**

- ❌ Using past participle "enumerated" (function performs action, not result)
- ❌ Using noun "enumeration" (function is the action, not the result)
- ❌ Using "number" without counting connotation

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `enumerar`
- **Form:** Infinitive verb
- **Why it works:** Standard Spanish verb meaning "to enumerate/count/list items one by one." Used in computing contexts for enumeration. Clear action verb that conveys adding numbers to items.

**Arabic:**

- **Translation:** `تعداد` (taʿdād)
- **Form:** Verbal noun (masdar)
- **Why it works:** Masdar from عدّ (to count). Means counting, enumeration, or tallying. Used in Arabic computing for enumeration operations. Conveys the counting aspect clearly.

**Chinese:**

- **Translation:** `枚举` (méijǔ)
- **Form:** Verb compound
- **Why it works:** Two characters: 枚 (count/enumerate one by one) + 举 (lift/list/enumerate). Standard Chinese computing term for enumeration. Used in programming contexts for listing items systematically.

**Hindi:**

- **Translation:** `गिनती` (ginatī) or `गणना` (gaṇanā)
- **Form:** Verbal noun
- **Why it works:** "गिनती" means counting/enumeration. "गणना" is more formal Sanskrit term meaning calculation/counting. Both convey the systematic counting concept. Choose based on formality preference.

### ❌ Common Translation Mistakes

**Mistake 1: Using "number" as noun**

- **Wrong:** `número` (Spanish - "number")
- **Why wrong:** This is a noun meaning a number, not the action of numbering/counting. "Enumerar" (to enumerate/count) is the verb describing the action.
- **Right:** `enumerar` (to enumerate/count)

**Mistake 2: Using past participle**

- **Wrong:** `enumerado` (Spanish - "enumerated")
- **Why wrong:** Past participle suggests a completed state. Function performs ongoing action (enumerating), not describing a result. Use infinitive verb form.
- **Right:** `enumerar` (infinitive: to enumerate)

**Mistake 3: Using generic "count" without systematic connotation**

- **Wrong:** `contar` (Spanish - "to count")
- **Why wrong:** "Contar" is generic counting. "Enumerar" specifically means to list/count items systematically, one by one—more precise for this operation.
- **Right:** `enumerar` (to enumerate systematically)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO (in modern usage)

"Enumerate" has a single clear meaning: to count/list items one by one or to mention items individually. In computing, it specifically means pairing items with sequential numbers.

**The meaning for Python:**

✅ **To list items systematically with numbers** - pairing each item in a sequence with its index/position number.

**Your translation should capture: the systematic counting and listing of items, assigning a number to each one in sequence.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `enumerate`, check these translations:**

- [ ] `range` - Related to counting/indexing; conceptual relationship
- [ ] `zip` - Similar iteration utility; should use compatible verb form
- [ ] `map` - Similar iteration utility; should feel related
- [ ] `for` loop - Used together constantly; should read naturally

**Consistency rule:**

Iteration utility functions (`enumerate`, `zip`, `map`, `filter`) should use verb forms (infinitive) describing the transformation/enhancement they apply to iterables.

**Example:**

Spanish: `enumerar`, `empaquetar`, `mapear`, `filtrar` - all infinitive verbs ✅
NOT: `enumerar` (verb) + `empaquetado` (participle) ❌

### Functional relationships

**This term works WITH:**

1. **For loops**: Primary usage context
```python
for i, item in enumerate(items):
    print(i, item)
```

2. **Zip function**: Combining enumerations
```python
for i, (a, b) in enumerate(zip(list1, list2)):
    print(f"Pair {i}: {a}, {b}")
```

**Common pairing:**

```python
# Basic enumeration (starts at 0)
items = ["apple", "banana", "cherry"]
for index, fruit in enumerate(items):
    print(f"{index}: {fruit}")
# 0: apple, 1: banana, 2: cherry

# Start counting from 1
for number, fruit in enumerate(items, start=1):
    print(f"{number}. {fruit}")
# 1. apple, 2. banana, 3. cherry

# Convert to list to see all pairs
pairs = list(enumerate(items))
print(pairs)
# [(0, 'apple'), (1, 'banana'), (2, 'cherry')]

# Enumerate with custom start
for i, fruit in enumerate(items, start=10):
    print(f"Item {i}: {fruit}")
# Item 10: apple, Item 11: banana, Item 12: cherry

# Find indices where condition is true
numbers = [10, 5, 8, 12, 3, 15]
large_indices = [i for i, n in enumerate(numbers) if n > 10]
print(large_indices)  # [3, 5] (indices where value > 10)

# Enumerate strings
for i, char in enumerate("Python"):
    print(f"char[{i}] = '{char}'")

# Enumerate with zip
names = ["Alice", "Bob", "Charlie"]
ages = [25, 30, 35]
for i, (name, age) in enumerate(zip(names, ages)):
    print(f"{i+1}. {name} is {age} years old")

# Replace items at specific indices
items = ["a", "b", "c", "d"]
for i, item in enumerate(items):
    if i % 2 == 0:  # Even indices
        items[i] = item.upper()
print(items)  # ['A', 'b', 'C', 'd']

# Enumerate dict (gets keys)
data = {"x": 10, "y": 20, "z": 30}
for i, key in enumerate(data):
    print(f"{i}: {key} = {data[key]}")

# Better than range(len(...))
# Bad (C-style):
for i in range(len(items)):
    print(i, items[i])

# Good (Pythonic):
for i, item in enumerate(items):
    print(i, item)
```

---

## Confidence Calibration

**Translation Difficulty: LOW**

### LOW

- Clear action concept (counting/listing)
- Most languages have verb for "enumerate"
- Standard computing terminology
- **AI confidence should be HIGH**

**For this term:** LOW

**Rationale:** "Enumerate" is a standard computing term used globally in programming. The concept (pairing items with sequential numbers) is universal, and most languages have a verb meaning "to enumerate," "to count," or "to list systematically." The linguistic form (infinitive verb) is also clear across language families.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures SYSTEMATIC COUNTING/LISTING concept?
- [ ] Would a native speaker understand "numbering items one by one"?
- [ ] Conveys both counting and listing aspects?

### 2. Linguistic Correctness

- [ ] Correct part of speech (infinitive verb)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Matches pattern of other iteration utilities (`zip`, `map`, `filter`)?
- [ ] Uses infinitive verb form like related functions?
- [ ] Aligns with computing terminology in target language?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (clear action verb)?

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
term: enumerate
language: es
translation: enumerar
form: infinitive_verb
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "enumerar" is the standard verb meaning "to enumerate, to list, or to count items one by one." It's used in Spanish computing contexts for enumeration operations and clearly conveys the systematic counting/listing action that the function performs. The infinitive form aligns with other Python iteration utilities.

**Alternatives considered:**

1. `contar` (to count) - Too generic; doesn't convey the systematic listing aspect
2. `numerar` (to number) - Valid but "enumerar" is more precise and standard in computing
3. `listar` (to list) - Focuses on listing without emphasizing the counting/numbering

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH. "Enumerar" is a clear, standard term across Spanish computing contexts and precisely captures the function's purpose.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
