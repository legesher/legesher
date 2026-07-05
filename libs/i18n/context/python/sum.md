# Python Builtin Function: `sum` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** noun/verb (aggregation)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `sum` function in Python adds all numeric elements in an iterable and returns the total. Optionally accepts a start value (default 0). Works with integers, floats, and any objects supporting the `+` operator.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Sum a list of numbers
numbers = [1, 2, 3, 4, 5]
total = sum(numbers)
print(total)  # Output: 15
```

**What this does:** `sum()` adds all elements in the list: 1+2+3+4+5 = 15. Returns an integer when all inputs are integers.

### Example 2: Common Pattern

```python
# Sum with start value
prices = [10.50, 5.25, 3.00]
total_with_tax = sum(prices, 2.00)  # Adds 2.00 to result
print(total_with_tax)  # Output: 20.75 (18.75 + 2.00)

# Empty iterable
empty = []
print(sum(empty))  # Output: 0 (default start)
print(sum(empty, 100))  # Output: 100 (custom start)
```

**What this does:** Second parameter is start value (added to sum). Default start is 0. For empty iterables, returns the start value.

### Example 3: Edge Case

```python
# Mixed int and float
mixed = [1, 2.5, 3, 4.0]
print(sum(mixed))  # Output: 10.5 (float result)

# Generator expression
squares_sum = sum(x**2 for x in range(5))
print(squares_sum)  # Output: 30 (0+1+4+9+16)

# Don't use for strings - use join instead
# sum(['a', 'b', 'c'], '')  # TypeError - sum is for numbers
''.join(['a', 'b', 'c'])  # Correct way for strings
```

**What this shows:** Mixing int and float returns float. Works with generators (lazy evaluation). For concatenating strings, use `str.join()` not `sum()` - `sum()` is specifically for numeric addition.

---

## Pattern Classification

**This term is:** AGGREGATION FUNCTION (Reduction)

**Similar terms in this pattern:**

1. `max` - Returns largest value (aggregation/reduction)
2. `min` - Returns smallest value (aggregation/reduction)
3. `len` - Returns count (aggregation/measurement)

**Pattern rule:** Aggregation functions should use noun forms naming the result. "Sum" is the total/result of addition.


---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** Latin "summa" meant "highest, top" (from "summus" - highest). In mathematics, "sum" came to mean the result of addition - the total when numbers are combined. Related to "summit" (highest point).

**Why Python uses this:** "Sum" is the universal mathematical term for addition result. Every programming language and mathematics curriculum uses "sum" for totaling numbers. Clear, concise, universally understood.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `sum()` function performs left-to-right addition of all elements in an iterable. It's equivalent to repeatedly applying the `+` operator: `start + items[0] + items[1] + ... + items[n]`. The function takes two parameters: the iterable (required) and a start value (optional, defaults to 0).

Internally, `sum()` initializes with the start value, then iterates through each element, accumulating the total. For numeric types (int, float), this is straightforward arithmetic. The function works with any objects that support the `+` operator via `__add__()` method, though it's optimized for numbers.

Python specifically prohibits using `sum()` for string concatenation (`sum(['a','b'], '')` raises TypeError) because string concatenation via repeated `+` is O(n²) complexity - each addition creates a new string. Use `''.join()` instead (O(n)). This design decision guides users toward efficient patterns.

**Key behaviors:**

1. **Numeric-optimized:** Works best with int/float. Returns int if all elements are int (and start is int). Returns float if any element is float. Uses efficient C-level arithmetic for built-in numeric types.

2. **Start parameter:** Second argument initializes the sum. `sum([1,2,3], 10)` returns 16 (10+1+2+3). For empty iterable, returns start value. Default start is 0, making `sum([])` return 0.

3. **Left-to-right:** Evaluates in sequence: `(((start + a) + b) + c)`. Order matters for floating-point due to rounding. Not optimized for precision like `math.fsum()` which uses different algorithm.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (result of addition)
- **Action vs State:** RESULT - names the output
- **Temporal aspect:** Completed action (the total after adding)

### Recommended Form

**Primary recommendation:** Use noun form meaning "sum" or "total." This names the mathematical result, not the action of adding.

**Forms to AVOID:**

- ❌ Using verb "to add" - `sum` names the result, not the action
- ❌ Using "addition" when "sum" is more concise
- ❌ Using "total" alone if "sum" is the standard math term

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (minimal)

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Sum" as verb ("sum it up" - summarize)
- ✅ Meaning 2: **MATHEMATICAL TOTAL** - result of adding numbers
- ❌ Meaning 3: "Sum" in phrase "in sum" (meaning "in summary")

**Example:**

English "sum" can mean:

1. "To sum up the presentation" (summarize) ❌
2. "`sum([1,2,3])` returns 6" (mathematical total) ✅ **This is the Python meaning**
3. "In sum, we agreed" (in summary) ❌

**Your translation should capture meaning #2: the mathematical total/result of addition.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `sum`, check these translations:**

- [ ] `min`/`max` - Similar aggregation functions; should use same noun pattern
- [ ] `len` - Measurement function; related pattern
- [ ] `int`/`float` - Numeric types; `sum` works with these
- [ ] `+` operator - Addition; `sum` is repeated addition

**Consistency rule:**

Aggregation functions (`sum`, `min`, `max`) should all use noun forms naming their result. They reduce a collection to a single value.


### Functional relationships

**This term works WITH:**

1. **`sum` + numeric iterables**: Add numbers

```python
total = sum([1, 2, 3, 4, 5])
price_total = sum(prices)
```

2. **`sum` + generator expressions**: Lazy evaluation

```python
even_sum = sum(x for x in range(10) if x % 2 == 0)
```

**Common pairing:**

```python
# Basic summation
numbers = [10, 20, 30, 40]
total = sum(numbers)  # 100

# With start value
sum([1, 2, 3], 10)  # 16 (10+1+2+3)

# Generator expression
squares = sum(x**2 for x in range(5))  # 30

# List comprehension
values = [1, 2, 3, 4, 5]
even_sum = sum([x for x in values if x % 2 == 0])  # 6

# Empty iterable
sum([])  # 0
sum([], 100)  # 100

# Mixed types
sum([1, 2.5, 3])  # 6.5 (float)

# Calculate average
numbers = [10, 20, 30]
average = sum(numbers) / len(numbers)  # 20.0
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `sum`

- Universal mathematical concept (all cultures use addition)
- "Sum" is basic arithmetic term taught globally
- Well-established in all languages
- Clear semantic mapping

**For this term:** EASY

**Rationale:** The concept of sum (total of addition) is universal across all mathematical traditions. Every language has a standard word for the result of adding numbers. Translation is straightforward: use the mathematical term for sum/total.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Minor consideration: Ensure you use noun form (the result) rather than verb form (the action), to match Python's pattern for aggregation functions.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures SUM/TOTAL concept (result of addition)?
- [ ] Understood as mathematical aggregation?
- [ ] Distinguished from "add" (verb) vs "sum" (result)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun preferred for result)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Matches pattern of other aggregation functions (`min`, `max`)?
- [ ] Uses noun form like other result-naming functions?
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
term: sum
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
