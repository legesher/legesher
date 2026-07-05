# Python Builtin Function: `repr` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** noun/verb
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

The `repr` function returns a string representation of an object that is ideally unambiguous and evaluable - meaning it should recreate the object when passed to `eval()`. Short for "representation," it's primarily used for debugging and development, showing objects in a form useful to programmers.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Get string representation
text = "Hello\nWorld"
print(repr(text))  # Output: 'Hello\nWorld' (shows escape sequences)
```

**What this does:** `repr()` returns a string showing the object's structure. For strings, it includes quotes and shows escape sequences visibly rather than interpreting them.

### Example 2: Common Pattern

```python
# repr vs str
from datetime import datetime
now = datetime(2025, 1, 15, 14, 30)

print(str(now))   # Output: 2025-01-15 14:30:00 (readable)
print(repr(now))  # Output: datetime.datetime(2025, 1, 15, 14, 30) (recreatable)
```

**What this does:** `repr()` shows how to recreate the object in code, while `str()` provides human-readable output. `repr()` output can often be passed to `eval()` to get the original object back.

### Example 3: Edge Case

```python
# repr for custom objects
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __repr__(self):
        return f"Point({self.x}, {self.y})"

p = Point(3, 4)
print(repr(p))  # Output: Point(3, 4)
```

**What this shows:** Custom classes can define `__repr__()` to control their representation. Good `repr()` output should be unambiguous and show how to recreate the object.

---

## Pattern Classification

**This term is:** QUERY FUNCTION (Object Representation)

**Similar terms in this pattern:**

1. `str` - Converts to string (human-readable vs programmer-readable)
2. `ascii` - ASCII-only representation (related to repr)
3. `format` - Formatted string output (different purpose)

**Pattern rule:** Representation/conversion functions should use noun or verb forms indicating transformation or description. "Representation" describes what you get.


---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** Latin "repraesentare" meant "to present again, to show." "Representation" means showing something in a particular form or way.

**Why Python uses this:** "repr" abbreviates "representation" - showing an object's structure in string form. The goal is to provide an unambiguous, programmer-friendly view of the object. Python uses the abbreviation "repr" for brevity, similar to "len" and "str."

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `repr()` function returns the "official" string representation of an object by calling its `__repr__()` method. The goal is to produce output that, when passed to `eval()`, recreates the object - though this isn't always possible. At minimum, `repr()` should provide an unambiguous description showing the object's type and key attributes.

`repr()` is primarily for developers and debugging. When you type an object name in the REPL (interactive shell), Python shows you its `repr()`. The `%r` format specifier and `!r` in f-strings also use `repr()`. It differs from `str()`, which provides human-friendly output for end users.

Every object has a `__repr__()` method. If not explicitly defined, objects inherit the default which shows class name and memory address (like `<__main__.MyClass object at 0x...>`). Good practice is to implement `__repr__()` for custom classes to aid debugging.

**Key behaviors:**

1. **Unambiguous output:** Should clearly show object type and state. Two different objects should have distinguishable `repr()` outputs. Priority is clarity for programmers over prettiness.

2. **Ideally evaluable:** Good `repr()` can be passed to `eval()` to recreate the object. Not always possible (objects with file handles, sockets), but aim for it when feasible.

3. **Used for debugging:** REPL displays, logging, debugging tools all use `repr()`. Makes it critical for development. Should include information developers need to understand object state.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (the representation itself) or verb (to represent)
- **Action vs State:** Can be ACTION (create representation) or STATE (the representation)
- **Temporal aspect:** Instantaneous - creates representation at moment of call

### Recommended Form

**Primary recommendation:** Use noun form meaning "representation" or "depiction." While `repr` performs an action, the focus is on the representation it produces.

**Forms to AVOID:**

- ❌ Using "string" alone - too generic, doesn't capture representation concept
- ❌ Using "display" or "show" - too focused on visual presentation

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Political representation" (delegates/representatives)
- ✅ Meaning 2: **STRING REPRESENTATION OF OBJECT** (showing structure in text)
- ❌ Meaning 3: "Artistic representation" (depiction in art)

**Example:**

English "representation" can mean:

1. "Congressional representation" (political delegates) ❌
2. "`repr([1,2,3])` returns '[1, 2, 3]'" (object as string) ✅ **This is the Python meaning**
3. "Representation in the painting" (artistic depiction) ❌

**Your translation should capture meaning #2: specifically a string showing an object's structure in evaluable/unambiguous form.**

In computing, "representation" usually means how data is encoded/shown, not political or artistic meaning.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `repr`, check these translations:**

- [ ] `str` - Related conversion; repr for devs, str for users - should be distinct
- [ ] `ascii` - Similar to repr but ASCII-only - should feel related
- [ ] `format` - String formatting - related but different purpose

**Consistency rule:**

String conversion functions (`repr`, `str`, `ascii`, `format`) should use forms that indicate transformation or description. They all produce string output but for different purposes.


### Functional relationships

**This term works WITH:**

1. **`repr` for debugging**: Show object structure

```python
print(repr("hello\n"))  # 'hello\n' (shows escape)
print(repr([1, 2, 3]))  # [1, 2, 3]
```

2. **`repr` vs `str`**: Different purposes

```python
s = "Line1\nLine2"
print(str(s))   # Shows with actual newline
print(repr(s))  # Shows 'Line1\nLine2' with visible \n
```

**Common pairing:**

```python
# repr in REPL
>>> [1, 2, 3]
[1, 2, 3]  # This is repr output

# repr for debugging
data = "Test\nData"
print(f"Data is: {data!r}")  # Uses repr

# repr vs str
from datetime import date
d = date(2025, 1, 15)
print(str(d))   # 2025-01-15
print(repr(d))  # datetime.date(2025, 1, 15)

# repr for logging
import logging
logging.debug(f"Received: {obj!r}")  # Show unambiguous form

# Custom repr
class Book:
    def __init__(self, title, author):
        self.title = title
        self.author = author
    def __repr__(self):
        return f"Book('{self.title}', '{self.author}')"
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `repr`

- "Representation" is a common word with multiple meanings
- Need computing-specific term for object representation
- Distinction from `str` must be maintained
- Some languages may use different terms for different aspects

**For this term:** MEDIUM

**Rationale:** The concept of object representation exists in all programming contexts, but the specific meaning (programmer-oriented, evaluable string form) may need clarification. Need to distinguish from general "string" or "display" and maintain distinction from `str()`.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Key consideration: Translation should suggest programmer-oriented representation, distinct from human-friendly string conversion.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures REPRESENTATION concept (showing object structure)?
- [ ] Distinct from str (programmer view vs user view)?
- [ ] Understood in programming context?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun or infinitive)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Distinct from but related to `str`?
- [ ] Compatible form with other conversion functions?
- [ ] Aligns with CS education terminology?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
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
term: repr
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
