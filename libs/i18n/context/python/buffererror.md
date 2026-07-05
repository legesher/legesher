# Python Builtin: `BufferError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Subcategory:** memory
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`BufferError` is a built-in exception raised when an operation on a buffer - a raw block of memory exposed through Python's buffer protocol - cannot be performed. The classic trigger is trying to resize a `bytearray` while a `memoryview` still holds (exports) its underlying memory.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Resizing a bytearray while a memoryview exports its buffer
data = bytearray(b"hello")
view = memoryview(data)

data.extend(b" world")
# Raises BufferError: Existing exports of data: object cannot be re-sized
```

**What this does:** `memoryview(data)` takes out a live export of the `bytearray`'s memory. While that export exists, the `bytearray` must not move or resize its buffer - the view would be left pointing at freed memory - so any size-changing operation raises `BufferError`.

### Example 2: Common Pattern

```python
# Release the view before resizing - or scope it with a with-statement
data = bytearray(b"hello")

view = memoryview(data)
print(view[0])       # 104 (the byte value of 'h')
view.release()       # Explicitly free the export
data.extend(b" world")  # Works now

# The with-statement releases automatically
buffer = bytearray(b"abc")
with memoryview(buffer) as v:
    print(bytes(v))  # b'abc'
buffer.append(ord("d"))  # Safe: the view was released at block exit
```

**What this does:** Calling `.release()` (or leaving a `with memoryview(...)` block) ends the export, after which the `bytearray` is free to resize again. This release-before-resize discipline is the standard way to avoid `BufferError`.

### Example 3: Edge Case

```python
# Modifying THROUGH the view is fine; only resizing is forbidden
data = bytearray(b"hello")
view = memoryview(data)

view[0] = ord("H")     # Allowed: changes a byte in place, size unchanged
print(data)            # bytearray(b'Hello')

data[1] = ord("E")     # Also allowed: in-place write, no resize
print(data)            # bytearray(b'HEllo')

try:
    del data[0]        # Deleting shrinks the buffer -> resize
except BufferError:
    print("cannot resize while a view is exported")
```

**What this shows:** The export does not freeze the buffer's contents - in-place writes through either the view or the `bytearray` are legal. Only operations that change the buffer's SIZE (`extend`, `append`, `del`, `clear`, slice-assignment of a different length) raise `BufferError` while exports exist.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `MemoryError` - The other memory-family exception (allocation failure)
2. `ValueError` - Raised for right-type, wrong-value problems
3. `TypeError` - Raised when an operation is applied to the wrong type
4. `OSError` - Raised for system-level operation failures

**Pattern rule:** Exception classes are noun compounds, typically ending with "Error" in English. Translations should combine the problem domain ("buffer") with the same "error" word used by every other exception in the pack.


---

## Etymology (Brief)

**English Origin:** English "buffer" + Latin-derived "error"

**Root meaning:** "Buffer" originally named a device that absorbs shocks (from "buff," to soften a blow); computing borrowed it in the 1950s for a memory area that absorbs data between producer and consumer. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** Python's buffer protocol lets objects like `bytes`, `bytearray`, and `memoryview` share raw memory without copying. When a buffer-protocol operation cannot be completed safely - most often resizing memory that another object still references - Python raises `BufferError`, following its convention of naming the problem domain ("Buffer") plus "Error."

---

## Concept Explanation (Intermediate Level)

**What it does:**

`BufferError` guards Python's buffer protocol, the C-level mechanism by which objects expose their internal memory to other objects. When you create a `memoryview` over a `bytearray`, no bytes are copied: the view holds a direct reference (an "export") into the `bytearray`'s buffer. That zero-copy sharing is the feature - and also the hazard. If the `bytearray` were allowed to resize while exported, its buffer might be reallocated elsewhere in memory, leaving the view dangling over freed bytes.

Python prevents that scenario by refusing the resize: `extend`, `append`, `del`, `clear`, `+=`, and length-changing slice assignment on an exported `bytearray` all raise `BufferError`. The error is not about the data being wrong; it is about a structural conflict between two objects sharing one block of memory. The fix is lifecycle management, not data correction: release the view (`view.release()` or a `with` block) before resizing, or restructure the code so views are short-lived.

Most Python programmers meet `BufferError` rarely, and almost always through the `bytearray`/`memoryview` pair. It also appears in extension modules and libraries built on the buffer protocol (NumPy-style arrays, I/O frameworks) when a buffer cannot be exported or released as requested. It belongs to the memory family of exceptions alongside `MemoryError`, but the two differ sharply: `MemoryError` means allocation failed; `BufferError` means a live memory-sharing arrangement forbids the requested operation.

**Key behaviors:**

1. **Raised on resize with live exports:** Any size-changing operation on a `bytearray` (or other resizable buffer provider) raises `BufferError` while a `memoryview` or other consumer holds its buffer. In-place writes that keep the size constant remain legal.

2. **Cleared by releasing the export:** `memoryview.release()`, exiting a `with memoryview(...)` block, or letting the view be garbage-collected ends the export; the same resize then succeeds. The error therefore signals "not now," not "never."

3. **A buffer-protocol error, not an allocation error:** `BufferError` is a direct `Exception` subclass, unrelated to `MemoryError`. It reports a protocol violation between memory-sharing objects, not that the system ran out of memory.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (problem domain + error type)
- **Action vs State:** STATE - names an error condition, not an action
- **Temporal aspect:** Instantaneous - occurs at the moment the forbidden buffer operation is attempted

### Recommended Form

**Primary recommendation:** Use a compound noun combining the language's established computing term for "buffer" with the standard "error" word. In many languages the computing sense of "buffer" is a loanword or a fixed technical calque - prefer that established term over inventing a native paraphrase.

**Forms to AVOID:**

- ❌ Verb forms - exception classes are noun compounds, never actions
- ❌ Translating "buffer" by its shock-absorber or chemistry sense - wrong domain entirely
- ❌ Substituting the "memory" word (making it look like `MemoryError`) - the two exceptions are distinct and both exist

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: A physical shock absorber or protective cushion
- ❌ Meaning 2: A chemistry buffer (solution resisting pH change)
- ❌ Meaning 3: A person or thing that shields against impact ("a buffer between rivals")
- ✅ Meaning 4: **A RAW BLOCK OF MEMORY shared between objects via the buffer protocol**

**Example:**

English "buffer" can mean:

1. "Railway buffer stops" (mechanical cushion) ❌
2. "A pH buffer solution" (chemistry) ❌
3. "He acted as a buffer between them" (mediator) ❌
4. `memoryview(bytearray(...))` (a shared memory area) ✅ **This is the Python meaning**

**Your translation should capture meaning #4: the computing memory-area sense, using the term your language's CS community already uses for I/O and memory buffers.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `BufferError`, check these translations:**

- [ ] `memoryview` - The object whose exports trigger this error; "buffer" and "view" vocabulary should cohere
- [ ] `bytearray` - The resizable buffer provider in the canonical example
- [ ] `bytes` - The immutable sibling buffer type
- [ ] `MemoryError` - Same memory family, but a DIFFERENT exception; the two names must not blur together
- [ ] `ValueError` / `TypeError` - Same `...Error` compound pattern must be followed

**Consistency rule:**

Use the same "buffer" term that your language's documentation for `memoryview` and I/O buffering uses, and the same "error" word as every other exception class. Keep `BufferError` and `MemoryError` clearly distinct: one names the buffer concept, the other the memory concept, even though both belong to the memory subcategory.


### Functional relationships

**This term works WITH:**

1. **`memoryview` + `bytearray`**: The export that makes resizing illegal

```python
view = memoryview(data)   # export begins
data.extend(b"x")         # BufferError while export lives
```

2. **Exception handling**:

```python
try:
    data.extend(b"x")
except BufferError:
    view.release()
    data.extend(b"x")
```

**Common pairing:**

```python
# BufferError and the memoryview lifecycle
data = bytearray(b"stream")

# 1. Export the buffer (zero-copy)
view = memoryview(data)

# 2. In-place work through the view is fine
view[0:2] = b"ST"
print(data)  # bytearray(b'STream')

# 3. Resizing while exported fails
try:
    data.clear()
except BufferError as e:
    print(f"blocked: {e}")

# 4. Release, then resize freely
view.release()
data.clear()
print(data)  # bytearray(b'')

# Scoped alternative: the with-statement guarantees release
with memoryview(data) as v:
    pass
data.extend(b"ok")  # safe
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `BufferError`

- "Buffer" is heavily polysemous in general language (mechanical, chemical, social senses)
- Most languages have an established computing term for buffer - but it may be a loanword, a calque, or both, requiring a choice
- Must stay clearly distinct from `MemoryError` while remaining in the same family
- The buffer protocol itself is a niche concept, so translators may not recognize the context

**For this term:** MEDIUM

**Rationale:** The compound structure is routine and the "error" half is fixed by the pack's pattern. The judgment calls are picking the right computing sense of "buffer" (loanword vs. native calque varies by language and region) and keeping the term visibly different from the `MemoryError` translation. The underlying concept is obscure enough that a translator without the code examples could plausibly reach for a wrong sense of "buffer."

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures the MEMORY-AREA sense of buffer (not mechanical/chemical/social)?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Would a developer connect this to `memoryview`/`bytearray` operations?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Uses the same "buffer" term as `memoryview`/I-O documentation in this language?
- [ ] Same "error" word as `ValueError`, `TypeError`, `MemoryError`?
- [ ] Clearly distinct from the `MemoryError` translation?

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
term: BufferError
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
