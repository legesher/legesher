# Python Builtin: `RuntimeError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`RuntimeError` is a built-in exception raised when an error is detected that doesn't fall into any other specific exception category. It serves as a generic runtime error for situations that don't fit more specific exception types, often used in custom code or when the exact error category is unclear.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Raising RuntimeError manually
def process_data(data):
    if not data:
        raise RuntimeError("Data cannot be empty")

process_data([])  # Raises RuntimeError: Data cannot be empty
```

**What this does:** `RuntimeError` can be raised explicitly when an unexpected condition occurs that doesn't fit other exception types. It's often used in custom functions to signal general runtime problems.

### Example 2: Common Pattern

```python
# RuntimeError with recursion depth
import sys

def infinite_recursion(n):
    return infinite_recursion(n + 1)

try:
    infinite_recursion(0)
except RecursionError as e:  # RecursionError is subclass of RuntimeError
    print(f"Recursion limit exceeded: {e}")

# RuntimeError in custom validation
def validate_config(config):
    if "required_field" not in config:
        raise RuntimeError("Configuration missing required field")
    if config["required_field"] < 0:
        raise RuntimeError("Required field must be positive")

# Catching RuntimeError
try:
    validate_config({"other_field": 10})
except RuntimeError as e:
    print(f"Configuration error: {e}")
```

**What this does:** `RuntimeError` and its subclasses (like `RecursionError`) indicate runtime problems. Custom code often raises `RuntimeError` for validation failures or unexpected states that don't have more specific exception types.

### Example 3: Edge Case

```python
# RuntimeError vs more specific exceptions
def problematic_function(value):
    if not isinstance(value, int):
        # Better: raise TypeError (more specific)
        raise RuntimeError("Expected integer")
    if value < 0:
        # Better: raise ValueError (more specific)
        raise RuntimeError("Expected positive value")
    # RuntimeError appropriate for unexpected internal state
    if some_internal_state_is_invalid():
        raise RuntimeError("Internal state corruption detected")

# RuntimeError in generators
def limited_generator():
    count = 0
    while True:
        if count >= 10:
            raise RuntimeError("Generator limit exceeded")
        yield count
        count += 1

gen = limited_generator()
for i in gen:
    print(i)  # Eventually raises RuntimeError

# Catching any RuntimeError (including subclasses)
try:
    risky_operation()
except RuntimeError:
    print("A runtime error occurred")
```

**What this shows:** While `RuntimeError` can be used broadly, more specific exceptions (`TypeError`, `ValueError`) are preferred when they apply. `RuntimeError` is best for truly generic runtime issues or internal state problems. It's the parent class for more specific runtime exceptions.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `ValueError` - Raised when argument has wrong value
2. `TypeError` - Raised when operation applied to wrong type
3. `RecursionError` - Subclass of RuntimeError for recursion depth exceeded
4. `NotImplementedError` - Subclass of RuntimeError for unimplemented methods

**Pattern rule:** Exception classes should use noun forms, typically ending with "Error" in English. Translations should convey both the error type and the temporal aspect (runtime vs compile-time).

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `ValueError` | ErrorDeValor | خطأقيمة | 值错误 | मानत्रुटि |
| `TypeError` | ErrorDeTipo | خطأنوع | 类型错误 | प्रकारत्रुटि |
| `RuntimeError` | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** |

---

## Etymology (Brief)

**English Origin:** Compound word (Germanic + Latin-derived)

**Root meaning:** "Runtime" combines "run" (Old English "rinnan" meaning to move swiftly) with "time," referring to the period when a program is executing. In programming, "runtime" distinguishes execution time from compile time. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** `RuntimeError` clearly identifies when the problem occurs: during program execution (runtime), not during parsing or compilation. The name distinguishes this from syntax errors or import errors that occur before the code runs. It serves as a catch-all for runtime problems that don't fit more specific categories.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`RuntimeError` is raised to indicate an error that occurred during program execution (runtime) but doesn't fall into a more specific exception category. In Python's exception hierarchy, `RuntimeError` serves as a generic runtime exception - it's the fallback when the error doesn't clearly fit `TypeError`, `ValueError`, `KeyError`, or other specific types.

This exception is somewhat controversial in Python development because it's often overused. Python's philosophy encourages using specific exception types that clearly communicate what went wrong. However, `RuntimeError` remains useful for genuinely generic errors, internal state problems, or when creating custom exceptions (as a base class). Several important exceptions are subclasses of `RuntimeError`, including `RecursionError` (recursion depth exceeded) and `NotImplementedError` (method not implemented).

Understanding when to use `RuntimeError` versus more specific exceptions is an important skill. As a general rule: if a more specific exception type exists that describes your error (like `ValueError` for invalid values or `TypeError` for wrong types), use that instead. Reserve `RuntimeError` for truly generic runtime problems or internal state inconsistencies that don't fit other categories.

**Key behaviors:**

1. **Generic runtime exception:** Unlike specific exceptions (`KeyError`, `IndexError`), `RuntimeError` doesn't indicate a particular problem type. It's a catch-all for "something went wrong at runtime" without more specific categorization.

2. **Parent of specific runtime exceptions:** Several more specific exceptions inherit from `RuntimeError`, including `RecursionError` (too much recursion) and `NotImplementedError` (abstract method not implemented). Catching `RuntimeError` catches these subclasses too.

3. **Used in custom code:** Developers often raise `RuntimeError` in their own functions when encountering unexpected conditions that don't fit other exception types. However, creating custom exception classes or using more specific built-in exceptions is often better practice.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (time context + error type)
- **Action vs State:** STATE - describes an error condition, not an action
- **Temporal aspect:** Occurs during execution time (runtime) not compile time

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Compound noun or noun phrase | "ErrorDeEjecución" - clear structure |
| Germanic (de, nl, sv) | Compound noun | "Laufzeitfehler" - natural compounds |
| Slavic (ru, pl, uk) | Compound noun | "ОшибкаВремениВыполнения" - execution time error |
| Arabic | Noun phrase or compound | "خطأوقتالتشغيل" - runtime error |
| Chinese | Compound noun | "运行时错误" - runtime + error |
| Hindi | Compound noun | "क्रियान्वयनत्रुटि" - execution/runtime + error |

**Primary recommendation:** Use compound noun combining the concept of "runtime" or "execution time" with "error." Maintain capitalization that matches Python's convention (PascalCase for exception classes in English).

**Forms to AVOID:**

- ❌ Generic "error" without temporal context - loses the "runtime" distinction
- ❌ Using verb forms ("RuntimeFails") - exceptions are nouns, not actions
- ❌ Overly long descriptions - should be concise, 1-3 words maximum

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `ErrorDeEjecución` or `ErrorDeRuntime`
- **Form:** Compound noun
- **Why it works:** "Ejecución" (execution/runtime) + "Error" is clear. "De" preposition connects them naturally. Follows Spanish CS conventions. Some regions use English "Runtime."

**Arabic:**

- **Translation:** `خطأوقتالتشغيل` (khata' waqt al-tashgheel)
- **Form:** Compound noun phrase
- **Why it works:** "خطأ" (error) + "وقت التشغيل" (runtime/execution time) creates clear meaning. Standard Arabic technical terminology for runtime errors.

**Chinese:**

- **Translation:** `运行时错误` (yùnxíngshí cuòwù)
- **Form:** Compound noun
- **Why it works:** "运行时" (runtime/execution time) + "错误" (error) is standard Chinese programming terminology. Commonly used in Chinese technical documentation.

**Hindi:**

- **Translation:** `क्रियान्वयनत्रुटि` (kriyaanvayan truti)
- **Form:** Compound noun
- **Why it works:** "क्रियान्वयन" (execution/implementation) + "त्रुटि" (error) follows Sanskrit compound rules. Technical but accessible terminology.

### ❌ Common Translation Mistakes

**Mistake 1: Using generic "error" without temporal context**

- **Wrong:** `Error` (Spanish)
- **Why wrong:** Loses the critical "runtime" distinction. Doesn't indicate when the error occurs (runtime vs compile time vs import time).
- **Right:** `ErrorDeEjecución` (specifies runtime)

**Mistake 2: Overly literal translation creating awkward phrases**

- **Wrong:** `ErrorDeTiempoDeEjecución` (Spanish - "error of time of execution")
- **Why wrong:** Too verbose and awkward. Exception names should be concise. "Ejecución" alone captures the runtime concept.
- **Right:** `ErrorDeEjecución` (concise)

**Mistake 3: Missing consistency with other exceptions**

- **Wrong:** `ErrorEnEjecución` (Spanish - "error in execution")
- **Why wrong:** Inconsistent with the "ErrorDe..." pattern used for other exceptions. Preposition choice should be consistent.
- **Right:** `ErrorDeEjecución` (consistent pattern with ErrorDeValor, ErrorDeTipo, etc.)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (compound term requires careful translation)

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Movie/video runtime (duration of a film)
- ❌ Meaning 2: Program installation time (when installing software)
- ✅ Meaning 3: **PROGRAM EXECUTION TIME** (period when code is running)

**Example:**

English "runtime" can mean:

1. "The movie's runtime is 2 hours" (film duration) ❌
2. "Runtime installation files" (installation period) ❌
3. Error occurs while program executes ✅ **This is the Python meaning**

**Your translation should capture meaning #3: errors occurring during program execution, NOT film duration or installation time.**

**Additional clarification:**

"Runtime" in programming distinguishes from:
- **Compile time:** When source code is converted to executable code
- **Import time:** When Python loads modules
- **Parse time:** When Python reads and parses syntax

`RuntimeError` occurs during actual program execution.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `RuntimeError`, check these translations:**

- [ ] `RecursionError` - Subclass of RuntimeError (should show inheritance relationship)
- [ ] `NotImplementedError` - Subclass of RuntimeError
- [ ] `ValueError` - Sibling exception (should follow same pattern)
- [ ] `TypeError` - Sibling exception (same pattern)

**Consistency rule:**

All exception classes ending in "Error" should use the same structure in translations. If `RuntimeError` translates as "ErrorDeEjecución" (Spanish), then `ValueError` should be "ErrorDeValor" and `TypeError` should be "ErrorDeTipo" - maintaining consistent pattern.

**Example:**

Spanish exception pattern:
- `RuntimeError` → `ErrorDeEjecución` ✅
- `ValueError` → `ErrorDeValor` ✅
- `TypeError` → `ErrorDeTipo` ✅
NOT: `RuntimeError` → `ErrorDeEjecución` but `ValueError` → `ValorInválido` ❌ (inconsistent pattern)

### Functional relationships

**This term works WITH:**

1. **Raising RuntimeError explicitly**:

```python
raise RuntimeError("Something went wrong")
```

2. **Exception handling**:

```python
try:
    risky_operation()
except RuntimeError as e:
    print(f"Runtime error: {e}")
```

**Common pairing:**

```python
# Raising RuntimeError explicitly
def validate_state(state):
    if state < 0:
        raise RuntimeError("Invalid state detected")

# Catching RuntimeError
try:
    validate_state(-1)
except RuntimeError as e:
    print(f"Error: {e}")

# RuntimeError with custom message
def process():
    if not precondition_met():
        raise RuntimeError("Precondition failed: cannot process")

# RuntimeError subclass: RecursionError
def infinite_loop(n):
    return infinite_loop(n + 1)

try:
    infinite_loop(0)
except RecursionError:  # Subclass of RuntimeError
    print("Recursion depth exceeded")

# Using RuntimeError as base for custom exceptions
class CustomRuntimeError(RuntimeError):
    pass

raise CustomRuntimeError("Custom runtime problem")
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `RuntimeError`:

- "Runtime" is a compound technical term that may not translate directly
- Need to convey temporal aspect (execution time) + error
- Must maintain consistency with other exception names
- Some languages use English "runtime" as loanword, others translate

**For this term:** MEDIUM

**Rationale:** The concept of "runtime" (execution time) is well-established in computer science, but different languages handle this compound term differently. Some use native terms for execution time (ejecución, 运行时), while others adopt "runtime" as a technical loanword. The translation needs to clearly indicate when the error occurs (during execution) while maintaining consistency with other exception translations.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures EXECUTION TIME concept (not film duration or installation)?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Would a developer understand this is about errors during program execution?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Matches pattern of other exception translations?
- [ ] Same structure as `ValueError`, `TypeError` translations?
- [ ] Appropriate for parent class of `RecursionError`, `NotImplementedError`?

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
term: RuntimeError
language: es
translation: ErrorDeEjecución
form: compound_noun
confidence: medium-high
```

**Rationale (2-3 sentences):**

Spanish "ErrorDeEjecución" combines "Error" (error) with "Ejecución" (execution/runtime), connected by "De" preposition. "Ejecución" clearly indicates execution time (runtime) in Spanish programming contexts. Maintains consistency with other exception translations like `ErrorDeValor` (ValueError) and `ErrorDeTipo` (TypeError).

**Alternatives considered:**

1. `ErrorDeRuntime` - Using English "Runtime" - valid in some Spanish CS contexts where "runtime" is used as loanword
2. `ErrorEnTiempoDeEjecución` - "Error in execution time" - too verbose
3. `ExcepciónDeEjecución` - Using "Excepción" instead of "Error" - too verbose

**If confidence is not HIGH, explain:**

Confidence is MEDIUM-HIGH because while "ejecución" is standard for execution/runtime in Spanish programming, some technical contexts use English "runtime" as a loanword. Regional variation exists. Some Spanish-speaking developers are familiar with "runtime" as an untranslated technical term.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
