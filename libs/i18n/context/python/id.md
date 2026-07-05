# Python Builtin Function: `id` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** noun
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

The `id` function returns the unique identity (memory address) of an object. Every object in Python has a unique identifier that remains constant for its lifetime, which Python uses internally to track object identity.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Get object identity
x = [1, 2, 3]
print(id(x))  # Output: 140234567890123 (example address)
```

**What this does:** `id()` returns a unique integer representing the object's identity. This number is typically the memory address where the object is stored.

### Example 2: Common Pattern

```python
# Compare identities vs values
a = [1, 2, 3]
b = [1, 2, 3]
c = a

print(a == b)      # True (same values)
print(a is b)      # False (different objects)
print(id(a) == id(b))  # False (different identities)

print(a is c)      # True (same object)
print(id(a) == id(c))  # True (same identity)
```

**What this does:** Shows difference between value equality (`==`) and identity (`is`). Two lists with same values are equal but have different identities. Variables pointing to same object share identity.

### Example 3: Edge Case

```python
# Small integers are cached (identity may be shared)
x = 100
y = 100
print(id(x) == id(y))  # Often True (Python caches small ints)

# Large integers are not cached
a = 1000000
b = 1000000
print(id(a) == id(b))  # Usually False (different objects)

# Strings may be interned
s1 = "hello"
s2 = "hello"
print(id(s1) == id(s2))  # Often True (string interning)
```

**What this shows:** Python optimizes by caching small integers (-5 to 256) and sometimes interns strings, so seemingly different literals may share identity. This is implementation detail, not guaranteed behavior.

---

## Pattern Classification

**This term is:** INTROSPECTION FUNCTION (Object Identity)

**Similar terms in this pattern:**

1. `type` - Returns object's type (introspection)
2. `hash` - Returns object's hash value (identity-related)
3. `isinstance` - Checks object type (introspection)

**Pattern rule:** Introspection functions should use nouns that represent properties or identifiers you're querying about objects.


---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** From Latin "idem" meaning "the same." In computing, "ID" is abbreviation for "identifier" or "identity" - a unique label distinguishing one object from another.

**Why Python uses this:** "ID" is universal computing terminology for unique identifiers. Python chose this short, recognizable abbreviation for a function that returns an object's unique identity/identifier.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `id()` function returns an integer that uniquely identifies an object during its lifetime. In CPython (standard Python implementation), this is the object's memory address, but other implementations may use different schemes. The key guarantee: two objects with non-overlapping lifetimes may have the same `id()`, but no two objects existing simultaneously will share an `id()`.

This identity is what the `is` operator compares - `a is b` checks if `id(a) == id(b)`. Identity differs from equality: two objects can be equal (`==`) with different values but have different identities because they're separate objects in memory. Identity is fundamental to Python's object model.

The identity never changes once an object is created. When an object is destroyed and its memory reused, a new object might get the same identity value, but never while both exist simultaneously.

**Key behaviors:**

1. **Unique during lifetime:** Every live object has a unique identity. Two objects existing at the same time never share `id()` values. This makes identity useful for debugging and tracking specific object instances.

2. **Implementation-dependent:** The actual integer returned depends on Python implementation. CPython uses memory addresses, but this isn't guaranteed. Don't rely on `id()` for anything except identity comparison.

3. **Used by `is` operator:** `a is b` is equivalent to `id(a) == id(b)`. Identity comparison is faster than value comparison because it only checks a single integer, not object contents.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (identifier/identity property)
- **Action vs State:** STATE/PROPERTY - an intrinsic attribute of objects
- **Temporal aspect:** Permanent (for object's lifetime)

### Recommended Form

**Primary recommendation:** Use noun meaning "identifier" or "identity." This is a property that uniquely identifies objects. Many languages might keep the abbreviation "id" as it's universal in computing.

**Forms to AVOID:**

- ❌ Verb forms like "identify" - `id` is the identifier itself, not the action
- ❌ "Number" or "address" alone - too generic, doesn't capture uniqueness

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Identification document" (passport, driver's license)
- ❌ Meaning 2: "Ego/psychological identity" (Freudian psychology)
- ✅ Meaning 3: **UNIQUE IDENTIFIER/IDENTITY NUMBER** (computing/database concept)

**Example:**

English "id" can mean:

1. "Show me your ID" (identification document) ❌
2. "Id, ego, superego" (psychology) ❌
3. "`id(obj)` returns unique identifier" (computing) ✅ **This is the Python meaning**

**Your translation should capture meaning #3: a unique system-generated identifier that distinguishes one object from all others.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `id`, check these translations:**

- [ ] `type` - Similar introspection function; should use compatible noun forms
- [ ] `hash` - Identity-related function; should feel related
- [ ] `is` - Identity comparison operator; linguistic connection helpful

**Consistency rule:**

Introspection functions that query object properties (`id`, `type`, `hash`) should use noun forms representing the property being queried. They're all "what is this object's X?" functions.


### Functional relationships

**This term works WITH:**

1. **`id` + `is` operator**: Identity comparison

```python
a = [1, 2]
b = [1, 2]
print(a is b)          # False (different identity)
print(id(a) == id(b))  # False (explicitly compare IDs)
```

2. **`id` + debugging**: Track object instances

```python
def process(data):
    print(f"Processing object {id(data)}")
    # Later: verify you're working with same object
```

**Common pairing:**

```python
# Identity vs equality
x = [1, 2, 3]
y = [1, 2, 3]
z = x

print(id(x), id(y), id(z))  # x and z same ID, y different

# Checking if variables reference same object
if id(a) == id(b):
    print("Same object")
else:
    print("Different objects")

# Debugging object lifecycle
cache = {}
cache[id(obj)] = obj  # Use ID as key to track objects
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `id`

- "ID" is universal abbreviation in computing
- But "identifier" vs "identity" nuance exists
- Some languages might keep English "id", others translate
- Need to balance technical accuracy with local conventions

**For this term:** MEDIUM

**Rationale:** While unique identifiers are universal in computing, the choice between keeping "id" (universal abbreviation) vs translating to "identifier" or "identity" varies by language. Both approaches valid, depends on language's treatment of technical abbreviations.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures UNIQUE IDENTIFIER concept (not just any label)?
- [ ] Implies system-generated, permanent-during-lifetime property?
- [ ] Distinguished from human-readable names or labels?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun for property)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Matches pattern of other introspection functions (`type`, `hash`)?
- [ ] Uses noun form like other property-query functions?
- [ ] Aligns with computing terminology in target language?

### 4. Usability

- [ ] Short enough (1-2 words or abbreviation)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Recognizable to programmers in target language?

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
term: id
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
