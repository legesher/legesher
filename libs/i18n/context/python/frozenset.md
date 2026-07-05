# Python Builtin Type: `frozenset` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** noun (compound)
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

The `frozenset` type represents an immutable set - a collection of unique elements that cannot be modified after creation. Like `set` but frozen/unchangeable, making it hashable and usable as dictionary keys or elements in other sets. Used when you need an immutable collection of unique items.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Create immutable set
frozen = frozenset([1, 2, 3, 3, 2])
print(frozen)  # Output: frozenset({1, 2, 3}) - duplicates removed
```

**What this does:** `frozenset()` creates an immutable set. Like `set`, it stores unique elements with no duplicates, but once created, you cannot add or remove elements.

### Example 2: Common Pattern

```python
# Frozenset as dictionary key
cache = {}
key = frozenset(['apple', 'banana'])
cache[key] = "fruit set"

# Regular set can't be used as key
# bad_key = set(['apple', 'banana'])
# cache[bad_key] = "won't work"  # TypeError: unhashable type: 'set'

print(cache[frozenset(['apple', 'banana'])])  # Output: fruit set
```

**What this does:** Frozensets are hashable, unlike regular sets. This makes them usable as dictionary keys or elements in other sets. Regular mutable sets can't be hashed.

### Example 3: Edge Case

```python
# Set of sets (using frozenset)
set_of_sets = {frozenset([1, 2]), frozenset([2, 3]), frozenset([1, 2])}
print(set_of_sets)  # Output: {frozenset({1, 2}), frozenset({2, 3})}
# Note: duplicate frozenset({1, 2}) was removed

# Frozenset operations
a = frozenset([1, 2, 3])
b = frozenset([2, 3, 4])
print(a | b)  # Union: frozenset({1, 2, 3, 4})
print(a & b)  # Intersection: frozenset({2, 3})
```

**What this shows:** Frozensets can be elements of sets (regular sets cannot). They support all set operations (union, intersection, difference) but no modification methods.

---

## Pattern Classification

**This term is:** TYPE CONSTRUCTOR (Immutable Collection)

**Similar terms in this pattern:**

1. `set` - Mutable set (can add/remove elements)
2. `tuple` - Immutable sequence (ordered, allows duplicates)
3. `bytes` - Immutable byte sequence (different data type)

**Pattern rule:** Immutable collection types should use compound forms combining immutability indicator + base type. "Frozen" indicates unchangeable state.


---

## Etymology (Brief)

**English Origin:** Compound (frozen + set)

**Root meaning:** "Frozen" from Old Norse "frosen" (past participle of freeze), meaning solidified, fixed, unchangeable. "Set" from Latin "secta" (following, faction), in mathematics means a collection of distinct objects.

**Why Python uses this:** "Frozen" metaphorically means "fixed in place, unchangeable." Combined with "set," it clearly indicates this is an immutable version of the set type. The name immediately tells you it can't be modified, distinguishing it from mutable `set`.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `frozenset` type is an immutable version of Python's `set`. It stores a collection of unique, unordered elements that cannot be changed after creation. You cannot add, remove, or modify elements once a frozenset is created. This immutability makes frozensets hashable, meaning they can be used as dictionary keys or as elements in other sets.

Frozensets support all set operations that don't modify the set: union (`|`), intersection (`&`), difference (`-`), symmetric difference (`^`), membership testing (`in`), and subset/superset checks. They don't have methods like `add()`, `remove()`, or `clear()` that would modify the set.

The main use cases are: (1) as dictionary keys when you need a set-like key, (2) as elements in other sets when you need sets of sets, and (3) when you want to ensure a set cannot be accidentally modified, providing safety through immutability.

**Key behaviors:**

1. **Immutable:** Once created, cannot add, remove, or change elements. Attempting to modify raises `AttributeError`. This immutability makes them safe to use as dict keys.

2. **Hashable:** Unlike mutable sets, frozensets can be hashed and used as dictionary keys or set elements. The hash is computed from the set's elements and remains constant.

3. **Unique elements:** Like sets, automatically removes duplicates. Order is undefined (sets are unordered). Provides O(1) membership testing like sets.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (frozen + set)
- **Action vs State:** STATE/THING - describes what the object is
- **Temporal aspect:** Static type, permanent immutability

### Recommended Form

**Primary recommendation:** Use compound combining "frozen/immutable" concept + "set" term. The immutability aspect should be clear.

**Forms to AVOID:**

- ❌ Using only "set" - must distinguish from mutable set
- ❌ Using "constant" alone - need to specify it's a set

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (the word "frozen" has multiple meanings)

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Physically frozen" (solid ice, very cold)
- ✅ Meaning 2: **FIXED/UNCHANGEABLE** (cannot be modified)
- ❌ Meaning 3: "Stuck/stopped" (frozen in motion)

**Example:**

English "frozen" can mean:

1. "Frozen water" (physical ice) ❌
2. "`frozenset([1,2])` cannot be modified" (immutable) ✅ **This is the Python meaning**
3. "Computer is frozen" (stopped responding) ❌

**Your translation should capture meaning #2: fixed/unchangeable/immutable state, not physical freezing.**

Most languages distinguish between physical freezing and metaphorical "frozen" (unchangeable). Use the immutable/fixed meaning.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `frozenset`, check these translations:**

- [ ] `set` - Mutable version; should share "set" root with clear mutability difference
- [ ] `tuple` - Also immutable sequence; similar immutability concept
- [ ] `bytes` - Also immutable; consistency in expressing immutability

**Consistency rule:**

Immutable types (`frozenset`, `tuple`, `bytes`) should use consistent terminology for expressing immutability. If using "immutable" for frozenset, consider alignment with how other immutable types are described.


### Functional relationships

**This term works WITH:**

1. **`frozenset` as dict key**: Immutability enables hashing

```python
cache = {frozenset([1, 2]): "result"}
```

2. **`frozenset` in sets**: Set of sets

```python
set_of_sets = {frozenset([1, 2]), frozenset([3, 4])}
```

**Common pairing:**

```python
# Create frozenset
frozen1 = frozenset([1, 2, 3])
frozen2 = frozenset([2, 3, 4])

# Set operations (non-modifying)
print(frozen1 | frozen2)  # Union: frozenset({1, 2, 3, 4})
print(frozen1 & frozen2)  # Intersection: frozenset({2, 3})
print(frozen1 - frozen2)  # Difference: frozenset({1})
print(frozen1 ^ frozen2)  # Symmetric difference: frozenset({1, 4})

# Cannot modify
# frozen1.add(5)  # AttributeError: 'frozenset' object has no attribute 'add'
# frozen1.remove(1)  # AttributeError

# As dictionary key
graph = {}
edge = frozenset(['A', 'B'])
graph[edge] = 10  # Edge weight

# Set of sets
matrix = {
frozenset([1, 2]),
frozenset([2, 3]),
frozenset([3, 4])
}

# Convert between set and frozenset
mutable = {1, 2, 3}
immutable = frozenset(mutable)
back_to_mutable = set(immutable)

# Frozenset in set
nested = {frozenset([1, 2]), frozenset([3, 4])}
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `frozenset`

- "Frozen" metaphor may not translate directly
- Need to decide: use "frozen" literally or "immutable" conceptually
- Compound structure requires combining two concepts
- Balance between literal translation and conceptual clarity

**For this term:** MEDIUM

**Rationale:** The "frozen" metaphor (unchangeable) is culturally dependent. Some languages may prefer "immutable" or "constant" to "frozen." The compound nature adds complexity. Understanding that "frozen" means "unchangeable" (not physically cold) is important for correct translation.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Key consideration: Metaphorical "frozen" (unchangeable) vs literal "frozen" (ice). Most languages have terms for immutability that work better than literal freezing.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures IMMUTABLE SET concept?
- [ ] Clearly distinct from mutable `set`?
- [ ] Indicates unchangeability, not physical freezing?

### 2. Linguistic Correctness

- [ ] Correct compound form for target language?
- [ ] Natural word order (frozen-set vs set-frozen)?
- [ ] Capitalization correct (lowercase for Python types)?

### 3. Consistency

- [ ] Shares root with `set` translation?
- [ ] Immutability expressed compatibly with other immutable types?
- [ ] Aligns with CS terminology for immutability?

### 4. Usability

- [ ] Short enough (2-3 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Clear immutable + set meaning?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Professional technical term?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: frozenset
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
