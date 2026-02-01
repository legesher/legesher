# Python Builtin: `KeyError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`KeyError` is a built-in exception raised when attempting to access a
dictionary key that doesn't exist. It's one of Python's most common
exceptions, signaling that a lookup operation failed because the
requested key is not present in the dictionary.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Accessing non-existent key raises KeyError
user_data = {"name": "Alice", "age": 30}
print(user_data["email"])  # Raises KeyError: 'email'
```

**What this does:** Attempting to access a dictionary key that doesn't
exist raises a `KeyError` exception. The error message shows which
key was not found.

### Example 2: Common Pattern

```python
# Catching KeyError with try-except
user_data = {"name": "Alice", "age": 30}

try:
    email = user_data["email"]
except KeyError:
    email = "not provided"
    print(f"Email not found, using default: {email}")

# Better approach: use .get() to avoid KeyError
email = user_data.get("email", "not provided")
```

**What this does:** `try-except` blocks catch `KeyError` exceptions
to handle missing keys gracefully. Alternatively, the `.get()` method
returns a default value instead of raising an exception.

### Example 3: Edge Case

```python
# KeyError with nested dictionaries
config = {
    "database": {"host": "localhost", "port": 5432}
}

try:
    # KeyError if 'cache' key doesn't exist
    cache_host = config["cache"]["host"]
except KeyError as e:
    print(f"Missing key: {e}")  # Output: Missing key: 'cache'

# KeyError in dictionary operations
data = {"a": 1, "b": 2}
del data["c"]  # Raises KeyError: 'c'
```

**What this shows:** `KeyError` can occur in nested dictionary access
and deletion operations. The exception object contains the missing
key, accessible in the `except` clause.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `IndexError` - Raised when sequence index is out of range
2. `AttributeError` - Raised when attribute access fails
3. `ValueError` - Raised when argument has wrong value
4. `TypeError` - Raised when operation applied to wrong type

**Pattern rule:** Exception classes should use noun forms, typically
ending with "Error" in English. Translations should convey both the
error type and the specific problem domain (key, index, attribute,
etc.).

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `TypeError` | ErrorDeTipo | خطأنوع | 类型错误 | प्रकारत्रुटि |
| `ValueError` | ErrorDeValor | خطأقيمة | 值错误 | मानत्रुटि |
| `KeyError` | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** |

---

## Etymology (Brief)

**English Origin:** Compound word (Germanic + Latin-derived)

**Root meaning:** "Key" comes from Old English "cǣg" meaning an
instrument to open locks. In computing, a "key" is the lookup value
used to access data in key-value pairs (dictionaries/maps). "Error"
derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** `KeyError` clearly identifies the problem:
a dictionary key lookup failed. The name follows Python's convention
of combining the problem domain ("Key") with "Error" to create
descriptive exception names that immediately tell developers what
went wrong.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`KeyError` is raised by Python when code attempts to access a
dictionary key that doesn't exist in that dictionary. Dictionaries
(the `dict` type) are key-value mappings where you look up values
using unique keys. When you use bracket notation (`dict[key]`) and
the key isn't present, Python raises `KeyError` to signal the
lookup failed.

This exception is a subclass of `LookupError`, which is the parent
class for all exceptions raised when a lookup or indexing operation
fails. `KeyError` is specific to dictionary operations, making it
easy to catch and handle dictionary-related errors separately from
other types of failures.

Understanding `KeyError` is crucial because dictionaries are
fundamental to Python programming. They're used for configuration,
caching, counting, grouping data, and countless other tasks.
Learning to anticipate and handle `KeyError` (either through
exception handling or by using safer methods like `.get()` or
`.setdefault()`) is a key skill for Python developers.

**Key behaviors:**

1. **Raised on missing key access:** The primary trigger is using
   bracket notation (`dict[key]`) when the key doesn't exist. This
   is distinct from `.get()`, which returns `None` (or a default)
   instead of raising an exception.

2. **Contains the missing key:** The `KeyError` exception object
   stores the missing key as its first argument. When caught, you
   can access this via `except KeyError as e:` and examine
   `e.args[0]` to see which key was missing.

3. **Occurs in various operations:** Beyond simple access, `KeyError`
   can occur with `del dict[key]` (deleting non-existent keys) and
   when using dictionary methods that expect keys to exist.
   Understanding all these scenarios helps prevent unexpected errors.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (error type + problem domain)
- **Action vs State:** STATE - describes an error condition, not
  an action
- **Temporal aspect:** Instantaneous - occurs at moment of failed
  lookup

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Compound noun or noun phrase | "ErrorDeClave" - clear structure |
| Germanic (de, nl, sv) | Compound noun | "Schlüsselfehler" - natural compounds |
| Slavic (ru, pl, uk) | Compound noun | "КлючОшибка" - describes error type |
| Arabic | Noun phrase or compound | "خطأمفتاح" - key error |
| Chinese | Compound noun | "键错误" - key + error |
| Hindi | Compound noun | "कुंजीत्रुटि" - key + error |

**Primary recommendation:** Use compound noun combining the concept
of "key" with "error." Maintain capitalization that matches Python's
convention (PascalCase for exception classes in English).

**Forms to AVOID:**

- ❌ Using verb forms ("KeyMissing") - exceptions are nouns, not
  actions
- ❌ Generic "error" without specifying "key" - loses important
  context
- ❌ Overly long descriptions - should be concise, 1-3 words maximum

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `ErrorDeClave` or `ErrorDeKey`
- **Form:** Compound noun
- **Why it works:** "Clave" or "Key" for dictionary keys + "Error"
  is clear. "De" preposition connects them naturally. Follows
  Spanish CS conventions for exception names.

**Arabic:**

- **Translation:** `خطأمفتاح` (khata' miftaah)
- **Form:** Compound noun
- **Why it works:** "خطأ" (error) + "مفتاح" (key) creates clear
  compound. Standard Arabic technical terminology. Concise and
  unambiguous.

**Chinese:**

- **Translation:** `键错误` (jiàn cuòwù)
- **Form:** Compound noun
- **Why it works:** "键" (key) + "错误" (error) is natural Chinese
  structure. Used in Chinese programming documentation. Clear and
  concise.

**Hindi:**

- **Translation:** `कुंजीत्रुटि` (kunjee truti)
- **Form:** Compound noun
- **Why it works:** "कुंजी" (key) + "त्रुटि" (error) follows
  Sanskrit compound rules. Technical but accessible. Used in Hindi
  CS education.

### ❌ Common Translation Mistakes

**Mistake 1: Using generic "error" without "key"**

- **Wrong:** `Error` (Spanish)
- **Why wrong:** Too generic - doesn't specify this is about
  dictionary keys. Loses critical information about the error type.
- **Right:** `ErrorDeClave` (specifies key error)

**Mistake 2: Over-explaining in the name**

- **Wrong:** `ErrorLaClaveNoExiste` (Spanish - "the key doesn't
  exist")
- **Why wrong:** Exception names should be concise identifiers, not
  full sentences. Too long for practical use in code.
- **Right:** `ErrorDeClave` (concise but clear)

**Mistake 3: Using verb forms**

- **Wrong:** `ClaveFaltante` (Spanish - "missing key" as adjective)
- **Why wrong:** Exception names in Python are nouns representing
  error types, not descriptions of state. Should follow same
  pattern as other exceptions.
- **Right:** `ErrorDeClave` (noun form)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Physical key for locks (house key, car key)
- ❌ Meaning 2: Musical key (key of C major)
- ❌ Meaning 3: Important/crucial element (key to success)
- ✅ Meaning 4: **DICTIONARY LOOKUP KEY** (unique identifier in
  key-value mapping)

**Example:**

English "key" can mean:

1. "I lost my house key" (physical key) ❌
2. "This song is in the key of G" (musical key) ❌
3. "Education is key to success" (crucial element) ❌
4. `user_data["email"]` where "email" is the key ✅
   **This is the Python meaning**

**Your translation should capture meaning #4: a lookup key in a
dictionary/map data structure, NOT physical keys or metaphorical
importance.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `KeyError`, check these translations:**

- [ ] `dict` - The dictionary type where keys are used
- [ ] `IndexError` - Similar exception for sequences (should follow
  same error naming pattern)
- [ ] `AttributeError` - Similar exception for attributes (same
  pattern)
- [ ] `LookupError` - Parent exception class for lookup failures

**Consistency rule:**

All exception classes ending in "Error" should use the same structure
in translations. If `KeyError` translates as "ErrorDeClave" (Spanish),
then `IndexError` should be "ErrorDeÍndice" - maintaining consistent
pattern.

**Example:**

Spanish exception pattern:

- `KeyError` → `ErrorDeClave` ✅
- `IndexError` → `ErrorDeÍndice` ✅
- `AttributeError` → `ErrorDeAtributo` ✅

NOT: `KeyError` → `ErrorDeClave` but `IndexError` →
`ÍndiceIncorrecto` ❌ (inconsistent pattern)

### Functional relationships

**This term works WITH:**

1. **Dictionary access operations**:

```python
data = {"name": "Alice"}
value = data["age"]  # Raises KeyError
```

1. **Exception handling**:

```python
try:
    value = data[key]
except KeyError:
    print("Key not found")
```

**Common pairing:**

```python
# KeyError in dictionary operations
data = {"a": 1, "b": 2}

# Raises KeyError
value = data["c"]

# Catching KeyError
try:
    value = data["c"]
except KeyError:
    value = None

# Avoiding KeyError with .get()
value = data.get("c", None)

# KeyError with del
del data["c"]  # Raises KeyError if 'c' not present

# KeyError with dictionary methods
data.pop("c")  # Raises KeyError (unless default provided)
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `KeyError`

- "Key" has multiple meanings (physical, metaphorical, computational)
- Need to convey compound concept (key + error)
- Must maintain consistency with other exception names
- Technical term that may vary by region's CS education

**For this term:** MEDIUM

**Rationale:** While the concept is well-established in computer
science, translating "key" requires understanding the
dictionary/mapping context. Different languages may use different
words for dictionary keys (clave, clé, Schlüssel, مفتاح, 键, कुंजी).
The compound structure also needs to feel natural in the target
language while maintaining technical clarity.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN
REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures DICTIONARY KEY concept (not physical key)?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Would a developer understand this is about missing dictionary
  keys?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Matches pattern of other exception translations?
- [ ] Same structure as `IndexError`, `AttributeError` translations?
- [ ] Aligns with `dict` type terminology?

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
term: KeyError
language: es
translation: ErrorDeClave
form: compound_noun
confidence: medium-high
```

**Rationale (2-3 sentences):**

Spanish "ErrorDeClave" combines "Error" (error) with "Clave" (key
in computing context), connected by "De" preposition. Follows
Spanish programming convention for exception names. Maintains
consistency with other exception translations like `ErrorDeValor`
(ValueError).

**Alternatives considered:**

1. `ErrorDeKey` - Using English "Key" - valid in some Spanish CS
   contexts
2. `ExcepciónDeClave` - Using "Excepción" instead of "Error" - too
   verbose
3. `ClaveError` - Direct compound - less natural in Spanish

**If confidence is not HIGH, explain:**

Confidence is MEDIUM-HIGH because while "clave" is standard for
dictionary keys in Spanish programming, some regions use English
"key" in technical contexts. Regional variation exists in CS
terminology.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive
5000-word version
