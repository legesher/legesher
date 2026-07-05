# Python Builtin: `anext` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** function
**Python Version:** 3.10+
**Difficulty:** HIGH

---

## Quick Summary

`anext()` retrieves the next item from an asynchronous iterator, the async equivalent of `next()` for use with async iteration protocol, must be awaited to get the value.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Basic async next
import asyncio

async def async_gen():
for i in range(3):
await asyncio.sleep(0.1)
yield i

async def main():
gen = async_gen()
value = await anext(gen)
print(value)  # Output: 0
value = await anext(gen)
print(value)  # Output: 1

asyncio.run(main())
```

**What this does:** `await anext(iterator)` gets the next value from an async iterator by calling its `__anext__()` method, similar to how `next()` works for sync iterators.

### Example 2: Common Pattern

```python
# Using anext with default value
import asyncio

async def async_gen():
yield 1
yield 2

async def main():
gen = async_gen()
print(await anext(gen))  # Output: 1
print(await anext(gen))  # Output: 2

# Would raise StopAsyncIteration without default
print(await anext(gen, "END"))  # Output: END

asyncio.run(main())
```

**What this does:** Like `next()`, `anext()` accepts a default value that's returned when the iterator is exhausted instead of raising `StopAsyncIteration`.

### Example 3: Edge Case

```python
# Manual async iteration with error handling
import asyncio

class AsyncCounter:
def __init__(self, max_count):
self.count = 0
self.max = max_count

def __aiter__(self):
return self

async def __anext__(self):
if self.count >= self.max:
raise StopAsyncIteration
await asyncio.sleep(0.1)
self.count += 1
return self.count

async def main():
counter = aiter(AsyncCounter(3))

try:
while True:
value = await anext(counter)
print(f"Count: {value}")
except StopAsyncIteration:
print("Counter exhausted")

asyncio.run(main())
```

**What this shows:** `anext()` raises `StopAsyncIteration` when the async iterator is exhausted, which is caught to end manual iteration loops, mirroring `StopIteration` behavior for sync iterators.

---

## Pattern Classification

**This term is:** ASYNC ITERATION FUNCTION

**Similar terms in this pattern:**

1. `next` - Synchronous next() function
2. `aiter` - Async iterator creation
3. `iter` - Synchronous iterator creation

**Pattern rule:** Async equivalents use 'a' prefix. `anext` is to `next` as `aiter` is to `iter`. Must maintain this parallel naming structure.


---

## Etymology (Brief)

**English Origin:** "a-" (async) + "next"

**Root meaning:** "next" from Old English "nēhst" (nearest, closest in position). The "a-" prefix signifies "asynchronous" - the async version of next.

**Why Python uses this:** Python 3.10 added `anext()` as the async counterpart to `next()`, following the established pattern of prefixing 'a' to sync functions for their async equivalents. Makes the sync/async relationship immediately clear.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`anext()` is the async equivalent of `next()`. It retrieves the next value from an asynchronous iterator by calling its `__anext__()` method. Since this operation is asynchronous, you must `await` the result.

In synchronous Python, `next(iterator)` gets the next value. In async Python, `await anext(iterator)` does the same for async iterators. When the iterator is exhausted, it raises `StopAsyncIteration` (or returns a default value if provided).

This is fundamental for manual control of async iteration. While `async for` loops handle this automatically, `anext()` gives you fine-grained control over when to fetch the next value, useful for complex async workflows.

**Key behaviors:**

1. **Must be awaited:** Returns a coroutine that must be awaited to get the actual value, unlike sync `next()` which returns immediately.
2. **Calls **anext**():** Invokes the async iterator's `__anext__()` method, which should be an async method returning the next value.
3. **Default value support:** Like `next()`, accepts optional default to return instead of raising `StopAsyncIteration` when exhausted.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Function name (action/command)
- **Action vs State:** ACTION - retrieves next value
- **Temporal aspect:** Instantaneous async action (awaited)

### Recommended Form

**Primary recommendation:** Add an async marker (prefix, compound, or adjective) to however `next` is translated. The relationship between `next` and `anext` must be immediately clear, parallel to `iter`/`aiter`.

**Forms to AVOID:**

- ❌ Completely different term from `next` - loses the parallel relationship
- ❌ No async indicator - must show it's the async version
- ❌ Confusing with `aiter` - should be based on "next" not "iter"

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO - "anext" is Python-specific technical abbreviation

**Single meaning:**

✅ **Python meaning:** Async next function, retrieves next value from async iterator.

The term is unambiguous - it's the async version of `next()` introduced in Python 3.10.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `anext`, check these translations:**

- [ ] `next` - MUST be clearly related (anext is async version of next)
- [ ] `aiter` - Parallel async function, should use same async marking pattern
- [ ] `iter` - Related sync function (for pattern understanding)
- [ ] `async`/`await` - Should use compatible async terminology

**Consistency rule:**

The sync/async pairs must form a consistent pattern:

- `iter` ↔ `aiter` (same relationship pattern)
- `next` ↔ `anext` (same relationship pattern)

Both async versions should use the same type of async marker.

**Example:**

✅ **Consistent:**

- `next` → `siguiente`
- `anext` → `asiguiente` or `siguiente_asinc`
- `iter` → `iterador`
- `aiter` → `aiterador` or `iterador_asinc`
- Same async marking pattern ✅

❌ **Inconsistent:**

- `next` → `siguiente`
- `anext` → `próximo_async` (different base word)
- Inconsistent ❌

### Functional relationships

**This term works WITH:**

1. **`aiter` + `anext`**: aiter creates async iterator, anext retrieves values from it
2. **`await` + `anext`**: anext must be awaited

**Common pairing:**

```python
# Manual async iteration
iterator = aiter(async_iterable)
value = await anext(iterator)  # Always used with await

# Implicit in async for
async for value in async_iterable:  # calls anext internally
pass
```

---

## Confidence Calibration

**Translation Difficulty: HIGH**

### HIGH

- Advanced async programming concept
- Must maintain clear relationship to `next`
- Must parallel `aiter`/`iter` pattern
- Relatively new (Python 3.10)
- **AI confidence should be MEDIUM, human review recommended**

**For this term:** HIGH

**Rationale:** Requires understanding of async iteration protocol and maintaining consistency across multiple related terms (`next`, `anext`, `iter`, `aiter`). Not all languages have standardized async programming terminology.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Clearly related to `next` translation?
- [ ] Indicates async nature?
- [ ] Conveys "get next value from async iterator"?

### 2. Linguistic Correctness

- [ ] Based on `next` translation with async marker?
- [ ] Concise enough for frequent use?
- [ ] Follows target language technical naming?

### 3. Consistency

- [ ] Parallel structure to `next`?
- [ ] Uses same async marking pattern as `aiter`?
- [ ] Compatible with async terminology?

### 4. Usability

- [ ] Short (1-2 words maximum)?
- [ ] Easy to type?
- [ ] Clearly distinguishable from sync `next`?

### 5. Cultural Appropriateness

- [ ] Professional technical register?
- [ ] No offensive meanings?

### 6. Technical Compatibility

- [ ] Renders properly in IDEs?
- [ ] No syntax issues?

---

## Translation Output Format

**Your translation:**

```yaml
term: anext
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
