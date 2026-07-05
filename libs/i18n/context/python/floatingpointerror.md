# Python Builtin: `FloatingPointError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`FloatingPointError` is a built-in exception reserved for floating-point operation failures — but modern CPython almost never raises it. Ordinary float operations return `inf` or `nan` (or raise `ZeroDivisionError`/`OverflowError`) instead. The class survives largely for historical reasons (the long-removed `fpectl` module) and because third-party numeric libraries such as NumPy raise it when configured to treat floating-point faults as errors.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Normal float operations do NOT raise FloatingPointError
print(1e308 * 10)                    # inf  — overflow returns infinity
print(1e-323 / 10)                   # 0.0  — underflow rounds to zero
print(float('inf') - float('inf'))   # nan  — invalid operation returns nan

try:
    1.0 / 0.0
except ZeroDivisionError:
    print("float division by zero raises ZeroDivisionError, "
          "not FloatingPointError")
```

**What this does:** This example demonstrates the honest core fact about `FloatingPointError`: the situations its name suggests (overflow, underflow, invalid operation, division by zero on floats) are handled by other means in Python. The class exists, but CPython's own float arithmetic does not raise it.

### Example 2: Common Pattern

```python
# Where FloatingPointError actually appears: NumPy in "raise" mode
# (numpy is a third-party library: pip install numpy)
import numpy as np

np.seterr(all="raise")  # promote silent IEEE faults to exceptions

try:
    np.float64(1e308) * np.float64(10)
except FloatingPointError as exc:
    print(f"caught: {exc}")  # caught: overflow encountered in scalar multiply
```

**What this does:** NumPy normally follows IEEE 754 semantics (returning `inf`/`nan` with a warning), but `np.seterr(all="raise")` tells it to raise Python's built-in `FloatingPointError` instead. This is the main place working programmers actually encounter the exception today.

### Example 3: Edge Case

```python
# The class remains a full member of the arithmetic family
print(issubclass(FloatingPointError, ArithmeticError))  # True

# It can be raised and caught like any exception
try:
    raise FloatingPointError("manually raised — CPython itself "
                             "almost never does this")
except ArithmeticError as exc:
    print(type(exc).__name__)  # FloatingPointError

# Historical note: the fpectl module that could make CPython raise it
# was removed in Python 3.7
```

**What this shows:** `FloatingPointError` is structurally alive — a proper subclass of `ArithmeticError`, catchable by family-level handlers — even though CPython no longer has a supported mechanism (`fpectl`, removed in 3.7) for generating it from its own float operations. It must still be translated consistently because the class is documented, importable, and used by third-party code.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `ArithmeticError` - Direct parent class; base of the numeric error family
2. `OverflowError` - Sibling; what Python actually raises for too-large float results
3. `ZeroDivisionError` - Sibling; what Python actually raises for float division by zero
4. `ValueError` - Raised when an argument has the right type but an invalid value

**Pattern rule:** Exception classes should use noun forms, typically ending with "Error" in English. Translations should convey both the error type and the specific problem domain (here: floating-point arithmetic).


---

## Etymology (Brief)

**English Origin:** Compound word (Germanic + Latin)

**Root meaning:** "Float" comes from Old English "flotian" (to rest on water); "point" from Latin "punctum" (a dot, a prick). "Floating point" describes number representation where the radix point "floats" — its position is encoded by an exponent rather than fixed. "Error" derives from Latin "error" (wandering, mistake).

**Why Python uses this:** The name was inherited from C's floating-point exception (FPE) machinery — Unix signals like SIGFPE. Python defined the class so those hardware-level faults could surface as a Python exception via the optional `fpectl` module; the module is gone (removed in 3.7), but the class remains for compatibility and third-party use.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`FloatingPointError` names the category of hardware-level floating-point faults: overflow, underflow, invalid operation, division by zero. In most languages' runtimes these faults are silent by default under IEEE 754 rules — operations return `inf` or `nan` rather than stopping the program. Python's class was created so that programmers who *wanted* those faults to stop the program (via the compile-time-optional `fpectl` module) had an exception to catch.

Modern reality, which any documentation translation should reflect honestly: CPython's own float arithmetic does not raise `FloatingPointError`. Overflow in plain arithmetic returns `inf`; underflow rounds toward zero; invalid operations return `nan`; division by zero raises `ZeroDivisionError`; and `math` module functions raise `OverflowError` or `ValueError`. The `fpectl` module that could change this was never enabled by default and was removed entirely in Python 3.7. The class survives for backward compatibility and as a documented hook.

That hook is genuinely used: NumPy raises the built-in `FloatingPointError` when the programmer opts into strict mode with `np.seterr(all="raise")`, which is how most working Python developers meet this exception today. So the term still needs a careful, consistent translation — it is a real, documented member of the `ArithmeticError` family — but translators should not describe it as something ordinary Python code triggers.

**Key behaviors:**

1. **Almost never raised by CPython itself:** Plain float operations return `inf`/`nan` or raise `ZeroDivisionError`/`OverflowError`. There is no supported switch in modern CPython that makes core float arithmetic raise `FloatingPointError`.

2. **Raised by third-party numeric libraries on request:** NumPy's `np.seterr(all="raise")` promotes IEEE faults (overflow, underflow, invalid, divide) to `FloatingPointError` — the exception's main contemporary habitat.

3. **Full member of the arithmetic family:** It subclasses `ArithmeticError`, so `except ArithmeticError:` catches it, and it can be raised manually or subclassed like any exception. Its existence is historical (`fpectl`, removed in 3.7), but its behavior as a class is entirely ordinary.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (number-representation domain + error type)
- **Action vs State:** STATE - describes an error condition, not an action
- **Temporal aspect:** Instantaneous - marks the moment a floating-point fault is reported

### Recommended Form

**Primary recommendation:** Use the target language's established computer-science term for "floating point" plus the family's error word. Note that many languages localized the *separator*, not the word "point": communities whose number notation uses a decimal comma say "floating comma" instead. Follow the local convention — do not force "point" on comma-notation languages.

**Forms to AVOID:**

- ❌ Verb forms - exceptions are nouns, not actions
- ❌ Literal water imagery ("buoyant dot") - "floating" here is the technical radix-point sense, not swimming
- ❌ Substituting the general word for "decimal number" - floating point is a specific representation; the established CS term should be used

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Physically floating ("a floating dock," buoyancy)
- ❌ Meaning 2: Unsettled or movable in the everyday sense ("floating holiday," "floating voter")
- ❌ Meaning 3: "Point" as a location, opinion, or score ("she has a point")
- ✅ Meaning 4: **FLOATING-POINT REPRESENTATION** (numbers stored with a radix point whose position is set by an exponent — the technical CS term)

**Example:**

English "floating point" can suggest:

1. "The buoy is floating" (buoyancy) ❌
2. "A floating deadline" (movable, informal) ❌
3. "That's a fair point" (argument) ❌
4. `3.14` is stored as a floating-point number ✅ **This is the Python meaning**

**Your translation should use the target language's established CS term for floating-point representation — including its localized separator word ("comma" languages say floating comma) — NOT literal buoyancy or everyday "point" words.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `FloatingPointError`, check these translations:**

- [ ] `ArithmeticError` - Parent class; must share the same error word and compound structure
- [ ] `OverflowError` - Sibling; what Python actually raises for float overflow
- [ ] `ZeroDivisionError` - Sibling; what Python actually raises for float division by zero
- [ ] `float` - The type; its translation must use the same floating-point root
- [ ] `complex` - Sibling numeric type; numeric vocabulary should read as one system

**Consistency rule:**

The floating-point term used here must be identical to the one used for the `float` type — whichever "floating point/comma" vocabulary the type uses, this exception cannot switch to a rival form. The error word and structure must match the whole `ArithmeticError` family.


### Functional relationships

**This term works WITH:**

1. **`float` operations (contrast)**: The operations its name suggests mostly do NOT raise it.

```python
1e308 * 10  # inf, not FloatingPointError
```

2. **`try`/`except` + third-party strict modes**: Where it is genuinely caught.

```python
import numpy as np
np.seterr(all="raise")
try:
    np.exp(np.float64(1000))
except FloatingPointError:
    print("IEEE fault promoted to an exception")
```

**Common pairing:**

```python
# FloatingPointError in a strict numeric pipeline (NumPy)
import numpy as np

def strict_normalize(values):
    with np.errstate(all="raise"):        # scoped strict mode
        arr = np.asarray(values, dtype=np.float64)
        try:
            return arr / arr.sum()
        except FloatingPointError as exc:
            raise ValueError(f"normalization failed: {exc}") from exc

print(strict_normalize([1.0, 3.0]))  # [0.25 0.75]

# Family membership means base-class handlers still work
try:
    raise FloatingPointError("demo")
except ArithmeticError:
    print("caught by the family handler")
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `FloatingPointError`

- "Floating point" has a settled CS term in every major language, but the term varies structurally (point vs comma) by regional number notation
- Must stay locked to the translation of the `float` type — a cross-reference constraint tighter than most exceptions
- The rarely-raised semantics do not change the translation, but translators must resist "improving" the name to describe what Python actually does

**For this term:** MEDIUM

**Rationale:** The vocabulary is established everywhere, which rules out HARD; the difficulty is coordination — matching the `float` type's rendering, choosing the correct regional separator word, and keeping the family's error suffix. Translate the name the class has, not the behavior it rarely exhibits.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Uses the established CS term for floating-point representation?
- [ ] Respects the target language's separator convention (point vs comma)?
- [ ] Clearly indicates an ERROR occurred?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Identical floating-point vocabulary to the `float` type translation?
- [ ] Same error word and structure as `ArithmeticError`, `OverflowError`, `ZeroDivisionError`?
- [ ] Native CS vocabulary preferred over transliteration?

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
term: FloatingPointError
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
