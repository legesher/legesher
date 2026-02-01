# Python Builtin Function: `range` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** noun (sequence generator)
**Python Version:** 3.x+
**Difficulty:** LOW

---

## Quick Summary

The `range` function in Python generates a sequence of numbers, commonly used for looping a specific number of times. It returns an immutable sequence object that produces numbers on demand rather than storing them all in memory.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Generate numbers 0 through 4
for i in range(5):
    print(i)
# Output: 0, 1, 2, 3, 4
```

**What this does:** Creates a sequence of 5 numbers starting from 0 (default) up to but not including 5. Most common usage for counting iterations.

### Example 2: Common Pattern

```python
# Range with start and stop
for num in range(3, 8):
    print(num)
# Output: 3, 4, 5, 6, 7

# Range with step
for even in range(0, 10, 2):
    print(even)
# Output: 0, 2, 4, 6, 8
```

**What this does:** First example shows range from 3 to 7 (8 not included). Second example shows counting by 2s using a step value. Step can be any integer.

### Example 3: Edge Case

```python
# Negative step (count backwards)
for countdown in range(10, 0, -1):
    print(countdown)
# Output: 10, 9, 8, 7, 6, 5, 4, 3, 2, 1

# Convert to list to see all values
numbers = list(range(3))
print(numbers)  # Output: [0, 1, 2]
```

**What this shows:** Can count backwards with negative step. Range is lazy (doesn't generate all values until needed), but can convert to list to see all values at once.

---

## Pattern Classification

**This term is:** SEQUENCE GENERATOR (Type Constructor)

**Similar terms in this pattern:**

1. `list` - Creates a mutable sequence collection
2. `tuple` - Creates an immutable sequence collection
3. `set` - Creates an unordered collection of unique items

**Pattern rule:** Sequence/collection constructors should use noun forms representing the type of object being created. These are type names, not verbs.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `list` | lista | قائمة | 列表 | सूची |
| `tuple` | tupla | مجموعة | 元组 | टपल |
| `range` | **rango** | **نطاق** | **范围** | **श्रेणी** |

---

## Etymology (Brief)

**English Origin:** French/Latin

**Root meaning:** From Old French "range" meaning "row, line, rank." From Latin "ordinare" (to arrange in rows). In mathematics and computing, "range" means an interval or span of values.

**Why Python uses this:** "Range" naturally describes a span of numbers from a starting point to an ending point. The term is widely used in mathematics (e.g., "range of values") and programming to describe numerical sequences or intervals.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `range()` function creates an immutable sequence of numbers following an arithmetic progression. Unlike Python 2's `range()` which created a list, Python 3's `range()` returns a range object that generates numbers on demand (lazy evaluation). This makes it memory-efficient for large sequences.

Range takes 1-3 arguments: `range(stop)`, `range(start, stop)`, or `range(start, stop, step)`. Start defaults to 0, step defaults to 1. The sequence includes start but excludes stop. Step can be positive (count up) or negative (count down), but cannot be zero.

Range objects support all common sequence operations like indexing, slicing, length checking, and membership testing. However, they don't store all values in memory—they calculate values on-the-fly, making `range(1000000)` just as memory-efficient as `range(10)`.

**Key behaviors:**

1. **Lazy evaluation:** Range doesn't pre-generate all numbers. It calculates each value only when requested. This makes it extremely memory-efficient for iteration and enables working with astronomically large ranges.

2. **Immutable sequence:** Range objects are immutable (can't be modified) and implement the full sequence protocol. You can index them `range(10)[5]`, slice them `range(10)[2:7]`, and check length `len(range(10))`.

3. **Exclusive end:** The stop value is never included in the sequence. `range(5)` produces 0,1,2,3,4 but not 5. This aligns with Python's zero-indexing and makes `range(len(items))` work perfectly for indexing.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (represents a type of sequence object)
- **Action vs State:** STATE - describes what kind of object it is, not an action
- **Temporal aspect:** Instantaneous - creates the range object immediately

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Noun | "rango", "plage" - interval/span |
| Germanic (de, nl, sv) | Noun | "Bereich", "bereik" - range/domain |
| Slavic (ru, pl, uk) | Noun | "диапазон", "zakres" - range/span |
| Arabic | Noun | "نطاق" - range/scope |
| Chinese | Noun compound | "范围" - range/scope |
| Hindi | Noun | "श्रेणी" - series/range |

**Primary recommendation:** Use noun form meaning "range," "interval," "span," or "series" depending on the target language's mathematical terminology. This represents a mathematical concept (set of consecutive numbers).

**Forms to AVOID:**

- ❌ Using verb "to range" or "to span" - this is a noun/type, not an action
- ❌ Using "interval" in languages where it implies continuous real numbers vs integers
- ❌ Using colloquial terms when mathematical terminology exists

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `rango`
- **Form:** Noun (masculine)
- **Why it works:** Standard Spanish mathematical term for range/interval. Used in mathematics education and programming. Clear and concise. Natural in "crear un rango" (create a range).

**Arabic:**

- **Translation:** `نطاق` (niṭāq)
- **Form:** Noun (masculine)
- **Why it works:** Modern Standard Arabic word for range/scope/domain. Used in technical contexts. Short and clear. Alternative: "مدى" (madá) but نطاق is more technical.

**Chinese:**

- **Translation:** `范围` (fànwéi)
- **Form:** Noun compound
- **Why it works:** Two characters: 范 (scope/limit) + 围 (surround/range). Standard Chinese term for range in mathematics and computing. Widely recognized and used in Chinese Python documentation.

**Hindi:**

- **Translation:** `श्रेणी` (śreṇī)
- **Form:** Noun
- **Why it works:** Sanskrit-derived word meaning series/sequence/range. Used in Hindi mathematics education. Clear technical term. Aligns with formal Hindi computer science vocabulary.

### ❌ Common Translation Mistakes

**Mistake 1: Using verb form**

- **Wrong:** `extender` (Spanish - "to extend/span")
- **Why wrong:** Range is a type/noun, not an action. It names the object being created, not the action of creating it.
- **Right:** `rango` (the range object itself)

**Mistake 2: Using overly colloquial terms**

- **Wrong:** `serie de números` (Spanish - "series of numbers")
- **Why wrong:** Too verbose and descriptive. Python terms should be concise. While accurate, it's a phrase rather than a standard technical term.
- **Right:** `rango` (concise technical term)

**Mistake 3: Confusing with English "rank" or "arrange"**

- **Wrong:** `clasificación` (Spanish - "ranking/classification")
- **Why wrong:** This translates the "rank" meaning of range, not the "numerical interval" meaning. Wrong concept entirely.
- **Right:** `rango` (numerical span, not ranking)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Cooking range/stove" (appliance)
- ❌ Meaning 2: "Mountain range" (geographic feature)
- ❌ Meaning 3: "Shooting range" (practice area)
- ❌ Meaning 4: "Range of motion" (physical extent)
- ✅ Meaning 5: **NUMERICAL INTERVAL/SEQUENCE** (mathematical concept)

**Example:**

English "range" can mean:

1. "We cooked on the range" (stove) ❌
2. "The Rocky Mountain range" (mountains) ❌
3. "Practice at the firing range" (location) ❌
4. "Range of motion in the shoulder" (extent) ❌
5. "`range(1, 10)` generates numbers 1 through 9" ✅ **This is the Python meaning**

**Your translation should capture meaning #5: a sequence or interval of consecutive numbers, NOT physical ranges, ranks, or locations.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `range`, check these translations:**

- [ ] `list` - Related sequence type; should use compatible noun forms
- [ ] `tuple` - Related sequence type; should use compatible noun forms
- [ ] `enumerate` - Works with range to provide indexed iteration
- [ ] `zip` - Often used alongside range for parallel iteration

**Consistency rule:**

All sequence type constructors (`range`, `list`, `tuple`, `set`) should be nouns. They create objects of specific types. If you translate one as a noun, translate all as nouns (not mixing with verbs).

**Example:**

Spanish: `rango`, `lista`, `tupla`, `conjunto` - all nouns ✅
NOT: `rango` (noun) + `crear_lista` (verb phrase) ❌

### Functional relationships

**This term works WITH:**

1. **`for` loop + `range`**: Most common usage pattern

```python
for i in range(10):
    print(i)
```

2. **`enumerate` + `range`**: Getting both index and value

```python
items = ['a', 'b', 'c']
for i in range(len(items)):
    print(i, items[i])
# Better: for i, item in enumerate(items):
```

**Common pairing:**

```python
# Basic iteration
for i in range(5):
    print(f"Iteration {i}")

# List indices
items = ['a', 'b', 'c', 'd']
for i in range(len(items)):
    print(items[i])

# Custom step
for n in range(0, 100, 10):
    print(n)

# Reverse iteration
for i in range(10, 0, -1):
    print(i)

# Convert to list
numbers = list(range(1, 6))  # [1, 2, 3, 4, 5]

# With list comprehension
squares = [x**2 for x in range(10)]
```

---

## Confidence Calibration

**Translation Difficulty: LOW**

### LOW

- Common mathematical concept
- Most languages have established technical term
- Minimal ambiguity in technical contexts
- **AI confidence should be HIGH**

**For this term:** LOW

**Rationale:** "Range" as a mathematical interval/sequence is a universal concept taught in mathematics education worldwide. Most languages have a standard technical term for this concept. The main consideration is ensuring you're translating the mathematical meaning (number sequence) rather than colloquial meanings (stove, mountains, etc.).

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures NUMERICAL SEQUENCE concept (not physical range or rank)?
- [ ] Would a native speaker understand this generates numbers?
- [ ] Avoids ambiguity with non-mathematical meanings?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun for type name)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Matches pattern of other sequence types (`list`, `tuple`, `set`)?
- [ ] Uses noun form like other type constructors?
- [ ] Aligns with mathematical terminology in target language?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (standard math term)?

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
term: range
language: es
translation: rango
form: noun
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "rango" is the standard mathematical term for an interval or range of values. It's used consistently in mathematics education and programming contexts throughout Spanish-speaking regions. The term is concise, unambiguous in technical contexts, and aligns with how computer science is taught in Spanish.

**Alternatives considered:**

1. `intervalo` (interval) - Valid but implies continuous values; range is discrete integers
2. `serie` (series) - Too general; doesn't specifically mean a range of numbers
3. `secuencia` (sequence) - Correct meaning but "rango" is more standard for Python's range

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH. "Range" as a mathematical interval is a universal concept with clear translations in all major languages used in mathematics education.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
