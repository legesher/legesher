# Python Builtin: `ArithmeticError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

`ArithmeticError` is the built-in base class for exceptions raised when a numeric calculation fails. Python almost never raises it directly; instead it raises one of its subclasses — `ZeroDivisionError`, `OverflowError`, or `FloatingPointError` — and `ArithmeticError` exists so code can catch the whole family of arithmetic failures with one handler.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Catching ArithmeticError catches its subclasses
try:
    result = 10 / 0
except ArithmeticError as exc:
    print(type(exc).__name__)  # ZeroDivisionError
```

**What this does:** The division by zero raises `ZeroDivisionError`, but the `except ArithmeticError` clause catches it because `ZeroDivisionError` is a subclass of `ArithmeticError`. This is the main way `ArithmeticError` appears in real code: as a catch-all for numeric failures.

### Example 2: Common Pattern

```python
# One handler for the whole family of numeric failures
import math

def safe_compute(x):
    try:
        return math.exp(x) / (x - 1)
    except ArithmeticError as exc:
        print(f"Numeric failure: {exc}")
        return None

safe_compute(1)     # Division by zero -> caught (ZeroDivisionError)
safe_compute(1000)  # math.exp(1000) too large -> caught (OverflowError)
```

**What this does:** Two different numeric failures — division by zero and floating-point overflow — raise two different exception classes, and a single `except ArithmeticError` handler catches both. This is exactly what a base class is for: grouping related failures so callers don't have to enumerate every specific case.

### Example 3: Edge Case

```python
# ArithmeticError sits above the numeric family in the hierarchy
print(issubclass(ZeroDivisionError, ArithmeticError))   # True
print(issubclass(OverflowError, ArithmeticError))       # True
print(issubclass(FloatingPointError, ArithmeticError))  # True

# The decimal module's exceptions also plug into this family
import decimal
print(issubclass(decimal.DecimalException, ArithmeticError))  # True

# It can be raised directly, but Python itself rarely does
raise ArithmeticError("custom numeric failure")
```

**What this shows:** `ArithmeticError` is a hierarchy node, not an error you normally see in a traceback. Built-in operations raise the specific subclasses, and even the standard library's `decimal` module hooks its own exception tree under `ArithmeticError`. Raising it directly is legal but uncommon — its job is classification.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `ZeroDivisionError` - Subclass raised for division or modulo by zero
2. `OverflowError` - Subclass raised when a result is too large to represent
3. `FloatingPointError` - Subclass reserved for floating-point failures (rarely raised)
4. `Exception` - The general base class one level above `ArithmeticError`

**Pattern rule:** Exception classes should use noun forms, typically ending with "Error" in English. Translations should convey both the error type and the specific problem domain (here: arithmetic, the branch of mathematics covering basic numeric operations).


---

## Etymology (Brief)

**English Origin:** Compound word (Greek + Latin)

**Root meaning:** "Arithmetic" comes from Greek "arithmos" (number) via "arithmetike techne," the art of counting. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** Python groups numeric-calculation failures under one base class, and "arithmetic" is the precise English name for the domain of basic numeric operations (addition, division, powers). The name follows Python's convention of combining a problem domain with "Error" to build a descriptive exception hierarchy.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`ArithmeticError` is the parent class for exceptions that signal a failed numeric calculation. Python's exception system is a class hierarchy, and this class sits between the general `Exception` and the three specific numeric failures: `ZeroDivisionError` (dividing by zero), `OverflowError` (result too large to represent), and `FloatingPointError` (a mostly historical placeholder for floating-point faults).

In practice, you interact with `ArithmeticError` in two ways. First, as a catch-all: `except ArithmeticError:` handles any of the numeric failures without listing them individually, which is useful in calculation-heavy code where the recovery strategy is the same regardless of which specific failure occurred. Second, as a base class for your own numeric exceptions: libraries that define custom calculation errors (the standard library's `decimal` module is the canonical example) subclass `ArithmeticError` so their errors participate in the same family.

What you will almost never see is `ArithmeticError` itself in a traceback. Built-in operations raise the specific subclasses, so the base class name shows up in `except` clauses and `issubclass` checks rather than in error messages. Translators should treat it as the family name for numeric errors, parallel to how the subclass names identify individual members.

**Key behaviors:**

1. **Catches the whole numeric family:** An `except ArithmeticError:` clause handles `ZeroDivisionError`, `OverflowError`, and `FloatingPointError` (and any user-defined subclasses), because exception matching follows the class hierarchy.

2. **Rarely raised directly:** Built-in operations raise the specific subclasses. `ArithmeticError` appears in handlers and hierarchy checks, not in the tracebacks Python produces on its own.

3. **Extension point for numeric libraries:** Code that defines its own calculation failures subclasses `ArithmeticError` — the `decimal` module's `DecimalException` does exactly this — so downstream handlers written against the base class keep working.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (problem domain + error type), naming a category of error conditions
- **Action vs State:** STATE - describes an error condition, not an action
- **Temporal aspect:** Instantaneous - marks the moment a numeric calculation fails

### Recommended Form

**Primary recommendation:** Use a compound noun built from the native word for "arithmetic" plus the established word for "error." Arithmetic is core school-mathematics vocabulary — nearly every language has a strong native term learned in primary education, so native math vocabulary should win over any transliteration of the English word. Maintain capitalization matching Python's PascalCase convention for exception classes.

**Forms to AVOID:**

- ❌ Verb forms ("CalculationFailed") - exceptions are nouns, not actions
- ❌ The broader word for "mathematics" - arithmetic is the narrower domain of basic numeric operations; using "math" over-widens the scope
- ❌ Transliterating "arithmetic" from English - native math vocabulary exists everywhere and is more recognizable

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO

"Arithmetic" has one dominant meaning: the branch of mathematics covering basic numeric operations (addition, subtraction, multiplication, division, powers). The one subtlety is scope, not polysemy:

- ❌ Too wide: "mathematics" in general (geometry, algebra, logic)
- ✅ Correct: **arithmetic — basic numeric calculation** (this is what fails when `ArithmeticError` is raised)

**Example:**

`10 / 0` and `math.exp(1000)` are arithmetic operations — plain numeric calculations. A wrong geometric construction or a failed logical proof would be "mathematical" in the broad sense but has nothing to do with this exception.

**Your translation should use the specific word for arithmetic/calculation taught in school mathematics, NOT the broader word for mathematics as a discipline.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `ArithmeticError`, check these translations:**

- [ ] `ZeroDivisionError` - Direct subclass; must share the same error suffix and family pattern
- [ ] `OverflowError` - Direct subclass; same requirement
- [ ] `FloatingPointError` - Direct subclass; same requirement
- [ ] `Exception` - Parent class; the hierarchy should read coherently top to bottom
- [ ] `ValueError` / `TypeError` - Sibling exception families; the "...Error" structure must match

**Consistency rule:**

The base class and its three subclasses form one visible family. Whatever word you choose for "error" and whatever compound structure you choose (error word leading the compound or trailing it) must be identical across `ArithmeticError`, `ZeroDivisionError`, `OverflowError`, and `FloatingPointError`.


### Functional relationships

**This term works WITH:**

1. **`try`/`except` + `ArithmeticError`**: The primary usage — one handler for all numeric failures.

```python
try:
    value = numerator / denominator
except ArithmeticError:
    value = float("nan")
```

2. **`class` + `ArithmeticError`**: Base class for custom numeric exceptions.

```python
class ConvergenceError(ArithmeticError):
    """Raised when an iterative calculation fails to converge."""
```

**Common pairing:**

```python
# ArithmeticError as the family catch-all
import math

def evaluate(x):
    try:
        return math.exp(x) / x
    except ZeroDivisionError:
        return float("inf")        # specific case handled specifically
    except ArithmeticError as exc:
        print(f"other numeric failure: {exc}")
        return None                # everything else in the family

evaluate(0)     # ZeroDivisionError branch
evaluate(1000)  # OverflowError caught by the ArithmeticError branch

# Hierarchy checks
print(issubclass(OverflowError, ArithmeticError))  # True
print(issubclass(ArithmeticError, Exception))      # True
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear one-to-one mapping
- Most languages have direct equivalent
- No ambiguity
- **AI confidence should be HIGH**

### Why EASY for `ArithmeticError`

- "Arithmetic" is taught in primary school in every language; strong native equivalents exist universally
- The compound structure (domain + error) is already established by sibling exceptions
- No competing meanings to disambiguate
- The only real risk is scope drift ("mathematics" instead of "arithmetic")

**For this term:** EASY

**Rationale:** Arithmetic is among the most universally shared technical vocabularies — native words for it exist in every school system, so translators do not need to invent or transliterate anything. The compound follows the same pattern as other exception classes. The main check is keeping the family consistent: the same error word and structure must appear in all three subclasses.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures ARITHMETIC (basic numeric calculation), not mathematics in general?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Would a developer recognize this as the base class for numeric failures?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Same error word and structure as `ZeroDivisionError`, `OverflowError`, `FloatingPointError`?
- [ ] Matches pattern of `ValueError`, `TypeError` translations?
- [ ] Uses native school-mathematics vocabulary for "arithmetic"?

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
term: ArithmeticError
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
