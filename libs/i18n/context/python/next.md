# Python Builtin Function: `next` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** verb/adjective
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

The `next` function retrieves the next item from an iterator. It calls the iterator's `__next__()` method and returns the next value in the sequence. When the iterator is exhausted, it raises `StopIteration` (or returns a default value if provided). Core function for manual iteration.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Get next item from iterator
numbers = iter([1, 2, 3])
print(next(numbers))  # Output: 1
print(next(numbers))  # Output: 2
print(next(numbers))  # Output: 3
```

**What this does:** `next()` retrieves the next item from an iterator. Each call advances the iterator forward. The iterator "remembers" its position.

### Example 2: Common Pattern

```python
# Read file line by line
file = open('data.txt')
first_line = next(file)
second_line = next(file)

# With default value (avoid StopIteration)
numbers = iter([1, 2])
print(next(numbers, 'done'))  # Output: 1
print(next(numbers, 'done'))  # Output: 2
print(next(numbers, 'done'))  # Output: 'done' (no error)
```

**What this does:** Common for reading file lines manually. The default parameter prevents `StopIteration` exception when iterator is exhausted, returning the default instead.

### Example 3: Edge Case

```python
# Manual iteration vs for loop
items = [1, 2, 3]

# Using next() manually
it = iter(items)
while True:
    try:
        item = next(it)
        print(item)
    except StopIteration:
        break

# Equivalent for loop (preferred)
for item in items:
    print(item)
```

**What this shows:** `next()` enables manual iteration control. For loops use `next()` internally. Manual `next()` gives finer control but for loops are usually cleaner.

---

## Pattern Classification

**This term is:** ACTION FUNCTION (Iterator Control)

**Similar terms in this pattern:**

1. `iter` - Creates iterator (next gets items from it)
2. `enumerate` - Wraps iterator with indices (uses next internally)
3. `zip` - Combines iterators (uses next internally)

**Pattern rule:** Iterator control functions should use terms indicating progression or retrieval. "Next" indicates moving forward in a sequence.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `iter` | iterar | تكرار | 迭代 | पुनरावृत्ति |
| `range` | rango | نطاق | 范围 | परिसर |
| `next` | **siguiente** | **التالي** | **下一个** | **अगला** |

---

## Etymology (Brief)

**English Origin:** Old English

**Root meaning:** Old English "nēhsta" meant "nearest, closest." "Next" indicates what comes immediately after in sequence or time.

**Why Python uses this:** "Next" clearly describes the function's purpose - getting the next item in sequence. It's intuitive: you're asking for the next value from an iterator. The term is universally understood across languages for sequential progression.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `next()` function is Python's built-in for manual iterator control. It calls an iterator's `__next__()` method, returning the next value in the sequence and advancing the iterator's position. When no more values remain, it raises `StopIteration` exception (unless you provide a default value).

Iterators maintain state - they "remember" where they are in the sequence. Each `next()` call moves forward one position. This is how for loops work internally: they repeatedly call `next()` until `StopIteration`, making iteration automatic. Using `next()` directly gives you manual control for situations where you need finer-grained iteration logic.

The optional second argument provides a default value to return when the iterator is exhausted, preventing `StopIteration`. This is useful for sentinel-based loops or when you want to handle exhaustion gracefully without exceptions. Many iterator protocols and patterns rely on `next()` under the hood.

**Key behaviors:**

1. **Advances iterator:** Each call moves iterator forward one position. State is maintained in iterator object. Cannot go backward - iterators are forward-only.

2. **Raises StopIteration:** When iterator exhausted, raises exception (if no default). This signals "no more items." For loops catch this internally to stop iteration.

3. **Optional default:** Second argument `next(it, default)` returns default instead of raising exception when exhausted. Useful for graceful handling without try/except.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Adjective (next item) or verb (get next)
- **Action vs State:** Can be ACTION (retrieve next) or DESCRIPTION (the next one)
- **Temporal aspect:** Indicates progression to subsequent item

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Adjective | "siguiente", "suivant" - the next one |
| Germanic (de, nl, sv) | Adjective | "nächste" - next |
| Slavic (ru, pl, uk) | Adjective | "следующий", "następny" - next/following |
| Arabic | Adjective | "التالي" (al-tālī) - the next/following |
| Chinese | Adjective/verb | "下一个" - next one |
| Hindi | Adjective | "अगला" - next/following |

**Primary recommendation:** Use adjective form meaning "next" or "following." While `next()` performs an action, the focus is on which item (the next one), not the action of getting.

**Forms to AVOID:**

- ❌ Using "advance" or "move forward" - too action-focused
- ❌ Using "continue" - different concept in programming

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `siguiente`
- **Form:** Adjective
- **Why it works:** "Siguiente" means next/following in Spanish. Natural, clear, universally understood. Captures the "next in sequence" concept perfectly.

**Arabic:**

- **Translation:** `التالي` (al-tālī)
- **Form:** Adjective with definite article
- **Why it works:** Standard Arabic for "the next/following." Used in sequential contexts. Clear and natural.

**Chinese:**

- **Translation:** `下一个` (xià yīgè)
- **Form:** Adjective phrase
- **Why it works:** Literally "down one" or "next one." Standard Chinese for next item in sequence. Clear temporal progression meaning.

**Hindi:**

- **Translation:** `अगला` (aglā)
- **Form:** Adjective
- **Why it works:** Common Hindi word for next/following. Natural in sequential contexts. Clear progression meaning.

### ❌ Common Translation Mistakes

**Mistake 1: Using "continue" concept**

- **Wrong:** `continuar` (Spanish - "to continue")
- **Why wrong:** "Continue" means keep going, not get next item. In programming, "continue" is a different keyword (skip to next loop iteration).
- **Right:** `siguiente` (next - indicates which item)

**Mistake 2: Using "advance" or "forward"**

- **Wrong:** `avanzar` (Spanish - "to advance")
- **Why wrong:** Too focused on the action of moving forward. "Next" focuses on the item you're getting, not the movement.
- **Right:** `siguiente` (the next item)

**Mistake 3: Using "after" instead of "next"**

- **Wrong:** `después` (Spanish - "after" or "later")
- **Why wrong:** "After" is too general and doesn't strongly indicate immediate sequence. "Next" is specifically the immediately following item.
- **Right:** `siguiente` (next - immediately following)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Next to" (beside, adjacent in space)
- ✅ Meaning 2: **IMMEDIATELY FOLLOWING IN SEQUENCE** (next item in order)
- ❌ Meaning 3: "Next time" (future occasion)

**Example:**

English "next" can mean:

1. "Sit next to me" (beside spatially) ❌
2. "`next(iter([1,2]))` returns 1, then 2" (sequential) ✅ **This is the Python meaning**
3. "Next time I'll remember" (future occasion) ⚠️ Related but too vague

**Your translation should capture meaning #2: the immediately following item in a sequence/iteration.**

Most languages distinguish between spatial "next to" and temporal/sequential "next in order." Use the sequential meaning.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `next`, check these translations:**

- [ ] `iter` - Creates iterators that next() operates on; should feel related
- [ ] `enumerate` - Iterator wrapper; uses next internally
- [ ] `range` - Creates iterables; next() retrieves values from them

**Consistency rule:**

Iterator-related functions (`next`, `iter`, `enumerate`) should use compatible terminology. They're all part of Python's iteration protocol.

**Example:**

Spanish: `siguiente` (next), `iterar` (iter) - compatible sequential/iteration concepts ✅
Chinese: `下一个` (next), `迭代` (iter) - consistent iteration vocabulary ✅

### Functional relationships

**This term works WITH:**

1. **`next` with `iter`**: Manual iteration

```python
it = iter([1, 2, 3])
print(next(it))  # 1
```

2. **`next` with default**: Avoid exceptions

```python
it = iter([1])
print(next(it, 'done'))  # 1
print(next(it, 'done'))  # 'done'
```

**Common pairing:**

```python
# Basic usage
numbers = iter([1, 2, 3])
print(next(numbers))  # 1
print(next(numbers))  # 2

# With default value
it = iter([1, 2])
print(next(it, None))  # 1
print(next(it, None))  # 2
print(next(it, None))  # None (no StopIteration)

# Manual iteration loop
data = iter([10, 20, 30])
while True:
    try:
        value = next(data)
        print(value)
    except StopIteration:
        break

# File reading
with open('file.txt') as f:
    first = next(f, '')  # First line or empty string
    second = next(f, '')  # Second line or empty string

# Generator usage
def countdown(n):
    while n > 0:
        yield n
        n -= 1

counter = countdown(3)
print(next(counter))  # 3
print(next(counter))  # 2
print(next(counter))  # 1
# print(next(counter))  # StopIteration

# Peek at first element
items = iter([1, 2, 3, 4])
first = next(items)
print(f"First: {first}")
print(f"Rest: {list(items)}")  # [2, 3, 4]
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `next`

- "Next" has multiple meanings (spatial, temporal, sequential)
- Need to distinguish from "continue," "after," "forward"
- Some languages have different terms for different "next" concepts
- Balance between adjective (next item) and verb (get next) forms

**For this term:** MEDIUM

**Rationale:** The concept of "next in sequence" is universal, but "next" in English is overloaded. Need to select translation specifically meaning "immediately following in order," not spatial "next to" or vague "future next." Most languages have clear terms for sequential next.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Key consideration: Translation should indicate immediate sequential progression, not spatial proximity or distant future.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures SEQUENTIAL NEXT concept?
- [ ] Indicates immediate following item, not distant future?
- [ ] Understood in iteration/sequence context?

### 2. Linguistic Correctness

- [ ] Correct part of speech (adjective or appropriate form)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python functions)?

### 3. Consistency

- [ ] Compatible with `iter` and iterator concepts?
- [ ] Natural in sequential/temporal contexts?
- [ ] Aligns with CS iteration terminology?

### 4. Usability

- [ ] Short (1 word preferred)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Immediately clear meaning?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Natural and professional?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: next
language: es
translation: siguiente
form: adjective
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "siguiente" means next/following and is the standard term for sequential progression. It naturally fits in iteration contexts and is universally understood. Matches Python's focus on which item (the next one) rather than the action.

**Alternatives considered:**

1. `próximo` (next/proximate) - Also valid but "siguiente" more common
2. `avanzar` (advance) - Too action-focused, not about which item
3. `next` (keep English) - Works but loses semantic clarity

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH. "Next" in sequential contexts is straightforward across languages. The concept of immediate sequential progression has clear equivalents everywhere.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
