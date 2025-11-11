# Python Builtin: `NotImplemented` - Translation Brief (Tier 1)

**Category:** builtin constant
**Type:** constant / singleton
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`NotImplemented` is a special singleton constant returned by binary operator methods (like `__add__`, `__eq__`) to indicate that the operation is not supported for the given operand types. It triggers Python's reflection mechanism to try the reverse operation.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Returning NotImplemented from a comparison method
class MyClass:
    def __eq__(self, other):
        if not isinstance(other, MyClass):
            return NotImplemented
        return True
```

**What this does:** When comparing `MyClass` to an incompatible type, the method returns `NotImplemented`, which tells Python to try the other object's comparison method instead.

### Example 2: Common Pattern

```python
# Using NotImplemented in arithmetic operations
class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x + other.x, self.y + other.y)
        return NotImplemented
```

**What this does:** If you try to add a `Vector` to something that isn't a `Vector`, it returns `NotImplemented`, giving the other object's `__radd__` method a chance to handle the operation.

### Example 3: Edge Case

```python
# NotImplemented is a singleton, not an exception
x = NotImplemented
print(type(x))  # Output: <class 'NotImplementedType'>
print(x is NotImplemented)  # Output: True
# Don't raise it like NotImplementedError
# raise NotImplemented  # TypeError: exceptions must derive from BaseException
```

**What this shows:** `NotImplemented` is a special singleton value, not an exception. It's distinct from `NotImplementedError` which is an exception class.

---

## Pattern Classification

**This term is:** VALUE CONSTANT (Protocol Marker)

**Similar terms in this pattern:**

1. `None` - Represents absence of value
2. `Ellipsis` (`...`) - Placeholder or continuation marker
3. `True` / `False` - Boolean constants

**Pattern rule:** All singleton constants should use noun or past participle form in target language. They represent fixed sentinel values, not actions.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `None` | Ninguno | لا شيء | 空 | कुछ नहीं |
| `Ellipsis` | Elipsis | علامة_الحذف | 省略号 | लोप_चिह्न |
| `True` | Verdadero | صحيح | 真 | सत्य |
| `NotImplemented` | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** |

---

## Etymology (Brief)

**English Origin:** Germanic/Latin compound

**Root meaning:** "not" (negation) + "implemented" (from Latin "implere" = to fill up, fulfill, carry out)

**Why Python uses this:** Python's operator overloading uses a reflection protocol - if one object can't perform an operation, it returns `NotImplemented` to give the other object a chance. The name explicitly states "this operation is not implemented for these types."

---

## Concept Explanation (Intermediate Level)

**What it does:**

`NotImplemented` is a singleton constant that serves as a sentinel value in Python's binary operation protocol. When you implement special methods like `__add__`, `__eq__`, or `__lt__`, you should return `NotImplemented` (not raise an exception) when the operation doesn't make sense for the given operand types.

This triggers Python's reflection mechanism. For example, if `a + b` causes `a.__add__(b)` to return `NotImplemented`, Python automatically tries `b.__radd__(a)` (the reflected/reversed operation). This allows the right-hand operand to handle the operation if it knows how.

This design is crucial for Python's polymorphism and interoperability between different types. It allows third-party classes to work with built-in types and each other, even when the original implementers never anticipated the combination.

The key distinction: `NotImplemented` is a return value (for operator methods), while `NotImplementedError` is an exception (for abstract methods or stub implementations). They serve different purposes despite similar names.

**Key behaviors:**

1. **Return Value, Not Exception:** You return `NotImplemented` from operator methods; you don't raise it. Raising `NotImplemented` causes a `TypeError`.

2. **Triggers Reflection:** When an operator method returns `NotImplemented`, Python tries the reflected operation (e.g., `__radd__` after `__add__` fails).

3. **Fallback to Exception:** If both operands return `NotImplemented`, Python raises `TypeError: unsupported operand type(s)`.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Past participle / adjective + negation - describes a state
- **Action vs State:** STATE - describes that something "is not implemented"
- **Temporal aspect:** Permanent state - the operation is fundamentally not supported

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Negation + past participle | "Not implemented" = "No implementado" |
| Germanic (de, nl, sv) | Negation + past participle | "Not implemented" = "Nicht implementiert" |
| Slavic (ru, pl, uk) | Negation + past participle | "Not implemented" = "Не реализовано" |
| Arabic | Negation + past participle or noun | Technical computing term |
| Chinese | Negation + noun/verb phrase | "未实现" (not realized/implemented) |
| Hindi | Negation + past participle | Sanskrit-derived technical term |

**Primary recommendation:** Use negated past participle form to match the English "NotImplemented" structure. This conveys "the state of not being implemented" rather than an action.

**Forms to AVOID:**

- ❌ Verb forms (infinitive/imperative) - This describes a state, not a command
- ❌ Noun forms like "NoImplementation" - Loses the participial quality

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `NoImplementado`
- **Form:** Negation + past participle (masculine)
- **Why it works:** Direct translation of structure, matches pattern of `NotImplemented` as state description

**Arabic:**

- **Translation:** `غير_منفذ` (ghayr munaffadh - not implemented/executed)
- **Form:** Negation + passive participle
- **Why it works:** Technical computing term structure, clear state description

**Chinese:**

- **Translation:** `未实现` (wèi shíxiàn)
- **Form:** Negation + verb (not yet realized)
- **Why it works:** Standard Chinese computing terminology for "not implemented"

**Hindi:**

- **Translation:** `लागू_नहीं` (laagoo nahīn - not implemented/applied)
- **Form:** Past participle + negation
- **Why it works:** Technical term commonly used in Hindi CS education

### ❌ Common Translation Mistakes

**Mistake 1: Using "Error" or "Exception"**

- **Wrong:** `NoImplementadoError` (Spanish - NotImplementedError)
- **Why wrong:** Confuses `NotImplemented` (singleton value) with `NotImplementedError` (exception class)
- **Right:** `NoImplementado`

**Mistake 2: Using Verb/Infinitive Form**

- **Wrong:** `NoImplementar` (Spanish - "to not implement")
- **Why wrong:** This is a state description, not an action/command
- **Right:** `NoImplementado` (past participle - "not implemented")

**Mistake 3: Adding "Operator" or "Method"**

- **Wrong:** `OperaciónNoImplementada` (Spanish - operation not implemented)
- **Why wrong:** Too verbose, adds unnecessary context
- **Right:** `NoImplementado` (concise, matches Python's convention)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Do not implement this" (command/instruction)
- ✅ Meaning 2: **"This is in a state of not being implemented" (state description/past participle)**
- ❌ Meaning 3: "Implementation error" (exception)

**Example:**

"NotImplemented" structure can be interpreted as:

1. An imperative ("Don't implement!") ❌
2. A state description ("is not implemented") ✅ **This is the Python meaning**
3. An error/exception class ❌ (that's `NotImplementedError`, different thing)

**Your translation should capture meaning #2: a state/condition marker indicating an operation is not supported, NOT a command or exception.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `NotImplemented`, check these translations:**

- [ ] `NotImplementedError` - Exception class with similar name, BUT different purpose and form
- [ ] `None` - Both are singleton constants, follow same naming pattern (but `NotImplemented` is compound)
- [ ] `True` / `False` - Other singleton constants, verify capitalization pattern
- [ ] `Ellipsis` - Another singleton constant

**Consistency rule:**

All singleton constants should use first-letter capitalization (following Python's convention) and noun/adjective form. However, `NotImplemented` is compound (negation + participle) while others are simple nouns/adjectives.

**Example:**

If you translate `None` as capitalized noun:

- `None` → `Ninguno` (Spanish - capitalized)
- `NotImplemented` → `NoImplementado` (Spanish - capitalized compound)
- NOT: `None` → `Ninguno` + `NotImplemented` → `no_implementado` ← Inconsistent capitalization ❌

### Functional relationships

**This term works WITH:**

1. **Binary operator methods**: `__add__`, `__eq__`, `__lt__`, etc. - these return `NotImplemented`
2. **Reflection protocol**: When returned, triggers `__radd__`, `__req__`, etc.

**Common pairing:**

```python
# NotImplemented commonly appears in operator overloading
class CustomType:
    def __eq__(self, other):
        if not isinstance(other, CustomType):
            return NotImplemented
        # comparison logic
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:**

Translating `NotImplemented` requires understanding several nuances:

1. **Compound Structure:** Translators must preserve the "Negation + Past Participle" structure across languages
2. **State vs Action:** Must convey a state/condition, not a command or error
3. **Distinguish from NotImplementedError:** The translation shouldn't imply exception/error
4. **Technical Context:** Understanding Python's operator protocol helps choose the right linguistic form

The difficulty is MEDIUM because:
- The compound structure translates relatively directly across most languages
- The past participle form exists in Indo-European languages
- BUT requires understanding the subtle difference between return value vs exception
- AND requires correct grammatical form (past participle, not infinitive)

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the "not implemented state" concept (not command or exception)?
- [ ] Would a native speaker understand this indicates unsupported operation?
- [ ] Clearly distinct from `NotImplementedError` translation?

### 2. Linguistic Correctness

- [ ] Uses past participle or equivalent state-describing form?
- [ ] Negation properly placed for target language?
- [ ] Capitalization matches Python's constant pattern (first letter capitalized)?

### 3. Consistency

- [ ] Matches the pattern of other singleton constants?
- [ ] Same capitalization as `None`, `True`, `False`?
- [ ] Compound structure if target language supports it?

### 4. Usability

- [ ] Not confused with `NotImplementedError`?
- [ ] Reasonable length (2-3 words acceptable for compound)?
- [ ] Easy to distinguish from other constants?

### 5. Cultural Appropriateness

- [ ] Professional/technical register?
- [ ] No ambiguous meanings in target language?
- [ ] Follows computing terminology conventions?

### 6. Technical Compatibility

- [ ] Renders properly in IDEs?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: NotImplemented
language: {es|ar|zh|hi|your_language}
translation: {your_translation}
form: {negation_plus_past_participle|compound_adjective}
confidence: {high|medium|low}
```

**Rationale (2-3 sentences):**

{Why you chose this translation. Address: How does your language express "not implemented" as a state? Did you use past participle + negation? Does it clearly differ from the exception class `NotImplementedError`? How does this align with technical terminology in your language?}

**Alternatives considered:**

1. `{alternative_1}` - {Why you didn't choose this}
2. `{alternative_2}` - {Why you didn't choose this}

**If confidence is not HIGH, explain:**

{Are you uncertain about past participle form? Is there ambiguity between state and command? Does compound negation work naturally in your language?}

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
