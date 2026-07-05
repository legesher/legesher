# Python Builtin: `MemoryError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`MemoryError` is a built-in exception raised when an operation runs out of memory - an allocation request that the system cannot satisfy. It is recoverable in principle: the interpreter state survives, so a program can catch it, free or avoid the oversized allocation, and continue (typically by deleting objects or switching to a smaller/streaming approach).

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# An impossible allocation raises MemoryError
try:
    huge = bytearray(2 ** 62)  # Request ~4 exbibytes
except MemoryError:
    print("allocation failed - program still running")
```

**What this does:** Creating a `bytearray` of 2^62 bytes requests vastly more memory than any machine has. The allocation fails, Python raises `MemoryError`, and the `except` block runs - demonstrating that the interpreter itself survives the failure and execution continues normally.

### Example 2: Common Pattern

```python
# Fall back to a streaming strategy when materializing is too big
def total_from_list(n):
    return sum(list(range(n)))       # fast, but needs the whole list in memory

def total(n):
    try:
        return total_from_list(n)
    except MemoryError:
        print("too large to materialize; streaming instead")
        return sum(range(n))         # lazy: constant memory

print(total(1_000_000))  # small: list strategy works
```

**What this does:** The function first tries the memory-hungry approach and catches `MemoryError` to fall back to a lazy, constant-memory computation. This catch-and-degrade pattern works precisely because `MemoryError` from one oversized allocation leaves the rest of the process intact.

### Example 3: Edge Case

```python
# One giant allocation fails cleanly; gradual exhaustion is messier
try:
    matrix = [[0.0] * 1_000_000 for _ in range(10_000_000)]
except MemoryError:
    # The partially built rows are discarded; memory is reclaimed
    print("could not build the matrix")

# CPython pre-allocates MemoryError instances so the exception
# can still be raised when almost no free memory remains.
print(issubclass(MemoryError, Exception))  # True - ordinary except blocks catch it
```

**What this shows:** A single huge request fails cleanly and early - the safest form of `MemoryError`. When memory is exhausted gradually by many small allocations, the error can strike anywhere and the handler itself has little memory to work with; CPython mitigates this by keeping pre-allocated `MemoryError` instances ready. Recovery is possible, but handlers should do minimal work: free references, log briefly, degrade.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `BufferError` - The other memory-family exception (buffer-protocol conflict)
2. `OverflowError` - Arithmetic result too large to represent
3. `RecursionError` - A resource-limit sibling (call-stack depth instead of heap memory)
4. `OSError` - System-resource failures more generally

**Pattern rule:** Exception classes are noun compounds, typically ending with "Error" in English. Translations should combine the problem domain ("memory") with the same "error" word used by every other exception in the pack.


---

## Etymology (Brief)

**English Origin:** Latin compounds

**Root meaning:** "Memory" from Latin "memoria" (remembrance, the faculty of remembering); computing adopted it in the 1940s for the hardware that stores data. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** When the memory allocator cannot satisfy a request, the problem domain is memory itself, so Python names the exception accordingly. The name follows the standard convention - problem domain ("Memory") + "Error" - and matches the equivalent condition in other languages (e.g., C's `malloc` returning NULL, Java's `OutOfMemoryError`).

---

## Concept Explanation (Intermediate Level)

**What it does:**

`MemoryError` is raised when Python asks the system for memory and the request cannot be fulfilled. This most often happens on a single oversized allocation: building an enormous list, reading a multi-gigabyte file into one string, or multiplying a sequence by a huge factor. The allocation fails as a unit, nothing is partially constructed from the caller's perspective, and the exception propagates like any other - which is why the docs describe it as recoverable in principle: the interpreter's own state is intact, so a `try/except MemoryError` can genuinely rescue the program.

Recovery quality depends on how the memory ran out. The clean case is the single huge request that fails while plenty of memory remains for everything else; catching it and switching to a chunked or streaming strategy is safe and idiomatic. The messy case is gradual exhaustion, where thousands of small allocations have consumed nearly everything; then `MemoryError` can be raised at almost any allocation site, and the handler itself may struggle to run (CPython keeps pre-allocated `MemoryError` instances precisely so raising it does not itself require fresh memory). Handlers should therefore be frugal: drop references to large objects, log a short message, and degrade or exit gracefully.

Two boundaries help place the term. First, `MemoryError` concerns dynamic allocation (heap memory), not the call stack - runaway recursion raises `RecursionError` instead. Second, on systems with an OOM (out-of-memory) killer such as Linux, the operating system may terminate the whole process before Python ever sees a failed allocation; `MemoryError` is only raised when the allocator reports failure to Python. It subclasses `Exception`, so ordinary `except Exception:` handlers catch it.

**Key behaviors:**

1. **Raised on failed allocation:** Any operation needing memory the system cannot provide - `bytearray(n)`, `[0] * n`, string concatenation, `list(range(n))` - raises `MemoryError` at the point of allocation, with the requesting operation cleanly abandoned.

2. **Recoverable in principle:** Because interpreter state survives, catching `MemoryError` and continuing is legitimate - the basis of fallback-to-streaming patterns. Handlers should free references and avoid new large allocations while handling it.

3. **Heap, not stack; Python-visible, not OS-guaranteed:** Stack exhaustion is `RecursionError`'s domain, and an OS out-of-memory killer may kill the process without any Python exception. `MemoryError` specifically means "the allocator said no, and Python is telling you."

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (problem domain + error type)
- **Action vs State:** STATE - names an error condition, not an action
- **Temporal aspect:** Instantaneous - occurs at the moment an allocation fails

### Recommended Form

**Primary recommendation:** Use a compound noun combining the language's standard computing term for "memory" (the RAM/storage sense, the same word used in `memoryview` and hardware documentation) with the pack's standard "error" word.

**Forms to AVOID:**

- ❌ Verb forms - exception classes are noun compounds, never actions
- ❌ The cognitive/human sense of memory ("remembrance," "recollection") where the language distinguishes it from computer memory
- ❌ Terms implying permanent fatality ("crash," "death") - the condition is catchable and recoverable

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Human memory, the faculty of remembering ("a good memory for names")
- ❌ Meaning 2: A remembered experience ("childhood memories")
- ❌ Meaning 3: Commemoration ("in memory of")
- ✅ Meaning 4: **COMPUTER MEMORY (RAM/heap) - the storage a program allocates from**

**Example:**

English "memory" can mean:

1. "She has an excellent memory" (cognitive faculty) ❌
2. "Fond memories of summer" (recollections) ❌
3. "A plaque in memory of the founders" (commemoration) ❌
4. "The process ran out of memory" (RAM/heap) ✅ **This is the Python meaning**

**Your translation should capture meaning #4: the hardware/allocation sense of memory - the same word your language uses for RAM and for `memoryview`.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `MemoryError`, check these translations:**

- [ ] `memoryview` - Must use the same "memory" word
- [ ] `BufferError` - Same memory subcategory but a DIFFERENT exception; domain words must stay distinct
- [ ] `RecursionError` - The stack-side resource-limit sibling; both are resource exhaustion, different resources
- [ ] `OverflowError` - Adjacent "too big" concept (numeric range, not allocation); must not blur together
- [ ] `ValueError` / `TypeError` - Same `...Error` compound pattern must be followed

**Consistency rule:**

Use the identical "memory" word everywhere memory concepts appear (`MemoryError`, `memoryview`, and any documentation prose), and the pack's standard "error" word. Verify the memory-family triangle stays distinct: memory/allocation (`MemoryError`), buffer/sharing (`BufferError`), stack/depth (`RecursionError`).


### Functional relationships

**This term works WITH:**

1. **Large allocations + `MemoryError`**: The operations that raise it

```python
data = [0] * n          # raises MemoryError if n is too large
```

2. **Exception handling + fallback**:

```python
try:
    result = build_in_memory(dataset)
except MemoryError:
    result = build_streaming(dataset)
```

**Common pairing:**

```python
# MemoryError with graceful degradation
def load_image_stack(paths):
    try:
        return [read_pixels(p) for p in paths]   # all at once
    except MemoryError:
        print("stack too large; processing one image at a time")
        return None

def process_lazily(paths):
    for p in paths:
        yield read_pixels(p)   # one image in memory at a time

# Frugal handler: free first, then act
cache = {}
try:
    cache["big"] = bytearray(10 ** 12)
except MemoryError:
    cache.clear()          # release what we hold
    print("cache disabled")  # minimal, allocation-light response

# Boundary: stack exhaustion is NOT MemoryError
def recurse():
    return recurse()
# recurse()  ->  RecursionError, not MemoryError
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `MemoryError`

- "Memory" has a firmly established computing translation in virtually every language - the concept itself is easy
- The synonym choice (native term vs. English loanword) must match the pack-wide decision made for `memoryview`
- Must stay distinct from `BufferError` within the same memory subcategory
- The human-recollection sense of "memory" is a real trap in languages that split the senses

**For this term:** MEDIUM

**Rationale:** This sits at the easy end of MEDIUM: the hardware sense of "memory" is standardized nearly everywhere, and the compound is mechanical. What keeps it from EASY is consistency work - the memory word must match `memoryview` exactly, the native-vs-loanword choice varies by region, and the translation must leave room for `BufferError` to remain distinct.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures COMPUTER MEMORY (RAM/heap), not human recollection?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Consistent with the condition being catchable and recoverable?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Same "memory" word as the `memoryview` translation?
- [ ] Same "error" word as `ValueError`, `TypeError`, `BufferError`?
- [ ] Clearly distinct from the `BufferError` translation?

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
term: MemoryError
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
