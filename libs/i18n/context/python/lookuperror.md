# Python Builtin: `LookupError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`LookupError` is the base class for exceptions raised when a lookup - retrieving a value by key or index from a mapping or sequence - fails because the key or index is invalid. Its two everyday subclasses are `KeyError` (dictionary keys) and `IndexError` (sequence positions); catching `LookupError` catches both.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# LookupError catches its subclasses KeyError and IndexError
data = {"name": "Alice"}

try:
    value = data["missing"]  # Raises KeyError - a LookupError subclass
except LookupError as e:
    print(f"Lookup failed: {e!r}")  # Lookup failed: KeyError('missing')
```

**What this does:** Accessing a missing dictionary key raises `KeyError`, but because `KeyError` inherits from `LookupError`, an `except LookupError:` handler catches it. The same handler would also catch an `IndexError` from a list access.

### Example 2: Common Pattern

```python
# One handler for both kinds of container lookup
def fetch(container, key):
    """Return container[key], or None if the key/index is invalid."""
    try:
        return container[key]
    except LookupError:  # Catches KeyError AND IndexError
        return None

print(fetch({"a": 1}, "b"))   # None (KeyError absorbed)
print(fetch([10, 20], 5))     # None (IndexError absorbed)
print(fetch([10, 20], 1))     # 20
```

**What this does:** Code that works generically over mappings *and* sequences would otherwise need `except (KeyError, IndexError):`. Catching the shared parent `LookupError` expresses the intent directly: "the subscript was invalid for this container, whatever kind it is."

### Example 3: Edge Case

```python
# The standard library raises LookupError directly for unknown codecs
import codecs

codecs.lookup("no-such-encoding")
# Raises LookupError: unknown encoding: no-such-encoding

"text".encode("no-such-codec")
# Also raises LookupError - encoding names are looked up in a registry

# Verifying the hierarchy
print(issubclass(KeyError, LookupError))    # True
print(issubclass(IndexError, LookupError))  # True
print(issubclass(LookupError, Exception))   # True
```

**What this shows:** `LookupError` is not only an abstract parent: the codec registry raises it directly when an encoding name cannot be found (another failed lookup by name). The `issubclass()` checks make the hierarchy concrete - `LookupError` sits between `Exception` and the specific lookup failures.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS (category/base class)

**Similar terms in this pattern:**

1. `KeyError` - Subclass: lookup by dictionary key failed
2. `IndexError` - Subclass: lookup by sequence index failed
3. `ArithmeticError` - Parallel category class grouping numeric errors (`ZeroDivisionError`, `OverflowError`)
4. `Exception` - Parent class of `LookupError` itself

**Pattern rule:** Exception classes should use noun forms, typically ending with "Error" in English. Category (base) classes name the *kind of operation* that failed - here, the lookup operation - rather than a specific domain object, and their translations must use the operation word their subclasses' documentation already relies on.


---

## Etymology (Brief)

**English Origin:** Germanic phrasal verb + Latin-derived

**Root meaning:** "Look up" is an English phrasal verb meaning "to search for an entry in a reference work" - as in looking a word up in a dictionary. Fused into the noun "lookup," it became standard computing vocabulary for retrieving a value by key or position from a table. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** Python needed one name for the shared failure mode of `dict[key]` and `sequence[index]`: you asked a container for an entry it does not have. "Lookup" is exactly that retrieval act - fittingly, Python's `dict` is even named after the reference book you look things up in. The class gives `except` clauses a way to speak about the whole category at once.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`LookupError` is the parent class for exceptions raised when a key or index used on a mapping or sequence is invalid. It sits one level above the two exceptions every Python programmer meets early: `KeyError`, raised when a dictionary lookup fails, and `IndexError`, raised when a sequence index is out of range. Both briefs for those terms describe them as "lookup operations" failing - `LookupError` is the class that makes that shared description literal in the type system.

You will rarely see Python raise a bare `LookupError` from ordinary subscription; concrete containers raise their specific subclass. Its everyday value is in `except` clauses: `except LookupError:` handles "the subscript was invalid" for any container kind, which is exactly right for generic code that accepts either a mapping or a sequence. Writing `except (KeyError, IndexError):` is equivalent for the common cases, but the base class states the intent and automatically covers user-defined subclasses.

The standard library does raise it directly in one notable place: the codec registry. `codecs.lookup("bad-name")` - and therefore `"x".encode("bad-name")` - raises `LookupError` when the encoding name is not registered, which is a failed lookup by name in a registry rather than in a container. As a base class, `LookupError` also serves as an extension point: a custom container type can define its own lookup failure as a `LookupError` subclass so that generic handlers keep working.

**Key behaviors:**

1. **Catches both `KeyError` and `IndexError`:** Because both inherit from it, `except LookupError:` is the one-line way to guard any subscription `container[subscript]` regardless of container type. This is the class's primary practical use.

2. **Rarely raised directly by containers:** `dict` raises `KeyError`, sequences raise `IndexError`. The base class appears directly mainly from `codecs.lookup()` for unknown encodings, and from libraries defining their own lookup failures.

3. **Sits mid-hierarchy:** `LookupError` inherits from `Exception`, so `except Exception:` catches it and all its subclasses. Handler ordering matters: an `except LookupError:` placed before `except KeyError:` makes the latter unreachable.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (error type + failed operation: the lookup)
- **Action vs State:** STATE - describes an error condition (a retrieval that failed), not an action
- **Temporal aspect:** Instantaneous - occurs at the moment of the failed retrieval

### Recommended Form

**Primary recommendation:** Use a compound noun combining your language's word for "looking something up" (searching a reference by key/position - a dictionary-consultation word if one exists) with the family's "error" word. The word must name the *operation*, because this class is the category above `KeyError` and `IndexError` - their translations name the domain objects (key, index); this one names what you were doing with them.

**Forms to AVOID:**

- ❌ Reusing "key" or "index" words ("ErrorDeClaveEÍndice") - the base class must not name specific subclass domains; that erases the hierarchy
- ❌ A physical "looking/gazing" word - the sense is consulting a reference for an entry, not directing your eyes upward
- ❌ Verb forms ("BuscarError") or overly long descriptions - exception names are concise noun compounds, 1-3 words maximum

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Physically looking upward ("look up at the sky")
- ❌ Meaning 2: Improvement ("things are looking up")
- ❌ Meaning 3: Visiting someone ("look me up when you're in town")
- ✅ Meaning 4: **RETRIEVING AN ENTRY BY KEY OR INDEX** (consulting a mapping/sequence for a stored value)

**Example:**

English "look up" can mean:

1. "Look up at the stars" (direction of gaze) ❌
2. "Business is looking up" (improving) ❌
3. "Look up an old friend" (visit) ❌
4. `data["email"]` or `items[5]` - retrieving by key or index ✅ **This is the Python meaning**

**Your translation should capture meaning #4: the act of consulting a container or registry for an entry - the same act as looking up a word in a dictionary. The exception means that consultation failed because the key or index was invalid.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `LookupError`, check these translations:**

- [ ] `KeyError` - Subclass; its brief describes dictionary access as a "lookup" - use the same operation word
- [ ] `IndexError` - Subclass; same requirement for sequence access
- [ ] `dict` - The mapping type whose failed lookups raise `KeyError`
- [ ] `Exception` - Parent class; hierarchy vocabulary must be coherent up and down
- [ ] `get` (dict method, in documentation) - The "safe lookup" alternative; documentation phrasing should reuse the lookup word

**Consistency rule:**

The word you choose for "lookup" here becomes the canonical operation word for the whole subtree. `KeyError` and `IndexError` documentation in your language will say "a lookup failed" - that sentence must use this class's word. Keep the same error word as the subclasses so the family reads as one hierarchy.


### Functional relationships

**This term works WITH:**

1. **Subscription + `LookupError`**: Any `container[subscript]` failure lands in this category

```python
value = container[subscript]  # KeyError or IndexError - both are LookupError
```

2. **`except` + `LookupError`**: The category handler

```python
try:
    value = container[subscript]
except LookupError:
    value = default
```

**Common pairing:**

```python
# Generic access over mappings and sequences
def get_first_match(source, *subscripts):
    for s in subscripts:
        try:
            return source[s]
        except LookupError:   # KeyError or IndexError alike
            continue
    return None

get_first_match({"b": 2}, "a", "b")   # 2
get_first_match([1, 2, 3], 10, 0)     # 1

# Handler ordering: specific before general
try:
    value = data[key]
except KeyError:        # Specific subclass first
    value = load_default(key)
except LookupError:     # Anything else in the category
    value = None

# LookupError raised directly: unknown encodings
try:
    text.encode(encoding_name)
except LookupError:
    print(f"unknown encoding: {encoding_name}")

# The hierarchy, explicitly
assert issubclass(KeyError, LookupError)
assert issubclass(IndexError, LookupError)
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `LookupError`

- "Lookup" is a phrasal-verb noun with no single-word equivalent in many languages
- Candidate words (search, consult, query, retrieve) overlap; the reference-consultation sense must win
- As a base class, its word choice constrains `KeyError`/`IndexError` documentation vocabulary
- Abstract category classes are seen less often, so learners rely more on the name being right

**For this term:** MEDIUM

**Rationale:** Every language can express "searching a reference for an entry," but few have a noun as compact as "lookup," so translators must pick among near-synonyms (search vs. query vs. consult). The deciding criterion is ecosystem fit: choose the word your language's CS materials already use for table/dictionary lookup, and verify it reads correctly as the parent of the key and index errors.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures RETRIEVAL-BY-KEY-OR-INDEX (not gazing, not improving, not visiting)?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Reads correctly as the CATEGORY above `KeyError` and `IndexError`?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Same error word as `KeyError`, `IndexError` translations?
- [ ] Operation word matches "lookup" phrasing in the `KeyError`/`IndexError` briefs?
- [ ] Coherent with `dict` and `Exception` terminology?

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
term: LookupError
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
