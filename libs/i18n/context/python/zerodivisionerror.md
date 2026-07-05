# Python Builtin: `ZeroDivisionError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

`ZeroDivisionError` is a built-in exception raised when the second argument of a division or modulo operation is zero. It applies to `/`, `//`, `%`, `divmod()`, and raising zero to a negative power — and, unlike some languages that return infinity for floats, Python raises this exception for both integer and floating-point division by zero.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Dividing by zero raises ZeroDivisionError
result = 10 / 0  # Raises ZeroDivisionError: division by zero
```

**What this does:** Any division where the divisor is zero raises `ZeroDivisionError` immediately. The operation has no mathematically defined result, so Python refuses to produce one.

### Example 2: Common Pattern

```python
# Guarding a calculation that may divide by zero
def average(values):
    try:
        return sum(values) / len(values)
    except ZeroDivisionError:
        return 0.0  # empty list -> defined fallback instead of a crash

print(average([2, 4, 6]))  # 4.0
print(average([]))         # 0.0

# Alternative: check before dividing
def rate(hits, total):
    if total == 0:
        return 0.0
    return hits / total
```

**What this does:** The `try`/`except` form computes first and handles the failure if it happens; the explicit check avoids the division entirely. Both are idiomatic — the exception-based version is common in Python because the zero case is usually rare.

### Example 3: Edge Case

```python
# Every division-family operation raises it, floats included
1.0 / 0.0      # Raises ZeroDivisionError (no IEEE infinity here)
10 % 0         # Raises ZeroDivisionError (modulo counts as division)
divmod(1, 0)   # Raises ZeroDivisionError
0 ** -1        # Raises ZeroDivisionError (zero to a negative power)

# The decimal module hooks into the same family
import decimal
print(issubclass(decimal.DivisionByZero, ZeroDivisionError))  # True

# But float('inf') exists — Python just never produces it from x / 0
```

**What this shows:** `ZeroDivisionError` covers the whole division family: true division, floor division, modulo, `divmod()`, and negative powers of zero. The float case matters most: many languages return IEEE infinity for `1.0 / 0.0`, but Python raises instead. (Third-party numeric libraries like NumPy follow IEEE semantics and differ here.)

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `ArithmeticError` - Direct parent class; base of the numeric error family
2. `OverflowError` - Sibling; raised when a result is too large to represent
3. `FloatingPointError` - Sibling; reserved for floating-point failures (rarely raised)
4. `ValueError` - Raised when an argument has the right type but an invalid value

**Pattern rule:** Exception classes should use noun forms, typically ending with "Error" in English. Translations should convey both the error type and the specific problem domain (here: dividing by zero).


---

## Etymology (Brief)

**English Origin:** Compound word (Arabic-derived + Latin)

**Root meaning:** "Zero" reached English through Arabic "ṣifr" (empty, nothing) via Italian "zefiro" — the concept itself entered European mathematics through Arabic scholarship. "Division" comes from Latin "dividere" (to split apart). "Error" derives from Latin "error" (wandering, mistake).

**Why Python uses this:** Dividing by zero has no defined result in ordinary arithmetic, and Python names the failure after exactly what happened: a zero division. Note the word order — English puts the cause first ("zero division"), matching Python's convention of problem domain + "Error."

---

## Concept Explanation (Intermediate Level)

**What it does:**

`ZeroDivisionError` is raised when the right-hand operand of a division-family operation is zero. This covers true division (`/`), floor division (`//`), modulo (`%`), the combined `divmod()` function, and `0 ** negative_exponent` (which is mathematically a division by zero). The mathematics is undefined, so Python stops the operation and raises rather than inventing a value.

The behavior that surprises programmers coming from other languages is the float case. IEEE 754 floating-point arithmetic defines `1.0 / 0.0` as infinity, and languages like JavaScript or C follow that. Python deliberately raises `ZeroDivisionError` for floats too, on the principle that a silent infinity propagating through a program usually hides a bug. (Python floats *can* hold infinity — `float('inf')` — Python just never produces it from division by zero. NumPy and other IEEE-faithful libraries behave differently.)

Handling is straightforward: either check the divisor before dividing, or wrap the division in `try`/`except ZeroDivisionError`. The exception is a subclass of `ArithmeticError`, so handlers written against the base class catch it as well, and the standard library's `decimal.DivisionByZero` subclasses it so decimal arithmetic participates in the same family.

**Key behaviors:**

1. **Raised by the whole division family:** `/`, `//`, `%`, `divmod()`, and zero raised to a negative power all raise it when the divisor (or base) is zero. The message varies slightly by operation ("division by zero", "integer division or modulo by zero").

2. **Applies to floats as well as ints:** `1.0 / 0.0` raises rather than returning IEEE infinity. This is a deliberate Python design choice that differs from many other languages and from NumPy.

3. **Subclass of `ArithmeticError`:** `except ArithmeticError:` catches it, and `decimal.DivisionByZero` extends it, keeping all division-by-zero failures in one catchable family.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (cause + error type)
- **Action vs State:** STATE - describes an error condition, not an action
- **Temporal aspect:** Instantaneous - occurs at the moment of the failed division

### Recommended Form

**Primary recommendation:** Use a compound noun built from the native school-mathematics words for "division" and "zero" plus the established word for "error." Both concepts are taught in primary school everywhere — this is a case where native math vocabulary should always win over transliteration. Keep both cause words: the exception is specifically about division *by zero*, not division problems in general.

**Forms to AVOID:**

- ❌ Verb phrases ("DividedByZero" as a past-tense clause) - exceptions are nouns, not actions
- ❌ Dropping "zero" ("DivisionError") - loses the specific cause; division itself is not the problem
- ❌ Transliterating "zero" or "division" from English - native math words exist in every language

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Division as an organizational unit (a company division, an army division)
- ❌ Meaning 2: Division as separation or disagreement ("deep divisions in the committee")
- ❌ Meaning 3: Division as partitioning objects into groups (everyday splitting-up)
- ✅ Meaning 4: **ARITHMETIC DIVISION** (the `/` operation; finding how many times one number contains another)

**Example:**

English "division" can mean:

1. "She works in the sales division" (organizational unit) ❌
2. "The vote revealed a division in the party" (disagreement) ❌
3. "The division of the estate among heirs" (partitioning) ❌
4. `10 / 2` computes the division of ten by two ✅ **This is the Python meaning**

**Your translation should capture meaning #4 — the arithmetic operation taught in school — NOT organizational, social, or partitioning senses. "Zero" is unambiguous: use the standard native math word for 0.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `ZeroDivisionError`, check these translations:**

- [ ] `ArithmeticError` - Parent class; must share the same error word and compound structure
- [ ] `OverflowError` - Sibling in the arithmetic family; same requirement
- [ ] `FloatingPointError` - Sibling in the arithmetic family; same requirement
- [ ] `divmod` - Built-in function whose translation should use the same "division" root
- [ ] `int` / `float` - The numeric types whose division raises this exception

**Consistency rule:**

The word chosen for "division" here must match the division vocabulary used anywhere else in the language pack (e.g., the `divmod` builtin, documentation of `/` and `//`). The error word and compound structure must be identical across the whole `ArithmeticError` family.


### Functional relationships

**This term works WITH:**

1. **Division operators + `ZeroDivisionError`**: The operators that can raise it.

```python
quotient = a / b   # raises ZeroDivisionError if b == 0
remainder = a % b  # same
```

2. **`try`/`except` + `ZeroDivisionError`**: The standard handling pattern.

```python
try:
    ratio = hits / total
except ZeroDivisionError:
    ratio = 0.0
```

**Common pairing:**

```python
# ZeroDivisionError in a realistic calculation
def per_capita(amount, population):
    try:
        return amount / population
    except ZeroDivisionError:
        return None  # uninhabited region: no meaningful per-capita value

print(per_capita(1000, 250))  # 4.0
print(per_capita(1000, 0))    # None

# All division-family operations participate
for op in ("10 / 0", "10 // 0", "10 % 0", "divmod(10, 0)", "0 ** -1"):
    try:
        eval(op)
    except ZeroDivisionError as exc:
        print(f"{op}: {exc}")

# Caught by the family base class too
try:
    1 / 0
except ArithmeticError:
    print("caught via ArithmeticError")
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `ZeroDivisionError`

- "Zero" and "division" are primary-school vocabulary with strong native equivalents in essentially every language
- The concept (dividing by zero is undefined) is taught worldwide, so the compound is self-explanatory
- The only choices are word order and which division word to use where a language distinguishes arithmetic division from everyday splitting

**For this term:** EASY

**Rationale:** This is the clearest case in the exception family for native math vocabulary: every target language has established school words for zero and division, and the failure they name is universally taught. The compound may run longer than sibling exception names in some languages — prefer completeness (keep both "zero" and "division") over brevity.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures ARITHMETIC DIVISION (not organizational or social division)?
- [ ] Includes "zero" — the specific cause of the failure?
- [ ] Clearly indicates an ERROR occurred?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Same error word and structure as `ArithmeticError`, `OverflowError`, `FloatingPointError`?
- [ ] Division vocabulary matches `divmod` and operator documentation?
- [ ] Uses native school-mathematics words for zero and division?

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
- [ ] Will render properly in IDEs (especially RTL)?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: ZeroDivisionError
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
**Last Updated:** 2026-07-04
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
