# Python Builtin: `StopAsyncIteration` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class (control flow signal)
**Python Version:** 3.5+
**Difficulty:** MEDIUM

---

## Quick Summary

`StopAsyncIteration` (Python 3.5, PEP 492) is a control-flow signal, not an error: it is raised by an asynchronous iterator's `__anext__()` method to tell an `async for` loop that there are no more items. It is the async twin of `StopIteration` - same meaning, same non-error nature, delivered through the asynchronous iteration protocol.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# A custom async iterator ends the loop by raising StopAsyncIteration
import asyncio

class Countdown:
    def __init__(self, start):
        self.current = start

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.current <= 0:
            raise StopAsyncIteration   # signal: no more items
        self.current -= 1
        return self.current + 1

async def main():
    async for n in Countdown(3):
        print(n)   # 3, 2, 1

asyncio.run(main())
```

**What this does:** The `async for` loop repeatedly awaits `__anext__()`. When the countdown reaches zero, `__anext__` raises `StopAsyncIteration`, and the loop terminates gracefully - exactly how `StopIteration` ends a plain `for` loop, but through the awaitable protocol.

### Example 2: Common Pattern

```python
# Async generators raise it implicitly; anext() surfaces it explicitly
import asyncio

async def fetch_pages():
    yield "page 1"      # an async generator: async def + yield
    yield "page 2"      # returning ends it - StopAsyncIteration is automatic

async def main():
    gen = fetch_pages()
    print(await anext(gen))   # page 1   (anext() builtin: Python 3.10+)
    print(await anext(gen))   # page 2
    try:
        await anext(gen)
    except StopAsyncIteration:
        print("no more pages")

asyncio.run(main())
```

**What this does:** Async generator functions never mention `StopAsyncIteration`; when the function returns, Python raises it behind the scenes from `__anext__`. Driving the generator manually with `anext()` (the async counterpart of `next()`, added in 3.10) exposes the signal, which `async for` would otherwise catch invisibly.

### Example 3: Edge Case

```python
# The signal must come from the protocol, not from inside your own async generator
import asyncio

async def numbers():
    yield 1
    raise StopAsyncIteration   # WRONG inside an async generator

async def main():
    try:
        async for n in numbers():
            print(n)
    except RuntimeError as e:
        print(f"converted: {type(e).__name__}")   # PEP 525 protection

    # anext() with a default: no exception handling needed (3.10+)
    async def two():
        yield "a"
    gen = two()
    print(await anext(gen, "done"))   # a
    print(await anext(gen, "done"))   # done  (signal absorbed into the default)

asyncio.run(main())
```

**What this shows:** Explicitly raising `StopAsyncIteration` inside an async generator body does not end iteration cleanly - PEP 525 converts it to `RuntimeError`, exactly as PEP 479 does for `StopIteration` in plain generators. The signal belongs to `__anext__` implementations in class-based iterators; async generators end by returning. `anext(gen, default)` absorbs the signal into a default value.

---

## Pattern Classification

**This term is:** CONTROL FLOW SIGNAL (Exception Class)

**Similar terms in this pattern:**

1. `StopIteration` - The synchronous twin; identical meaning for plain iterators
2. `GeneratorExit` - The other generator-side control signal (shutdown request)
3. `KeyboardInterrupt` - Another non-error exception (though on the `BaseException` side)

**Pattern rule:** Control-flow exceptions are compounds naming an event, and their translations must NOT contain the pack's "error/failure" word. `StopAsyncIteration` = the existing `StopIteration` translation with the pack's "async" modifier inserted - the same three components as the English, assembled in the target language's natural order.


---

## Etymology (Brief)

**English Origin:** Germanic + Greek + Latin compound

**Root meaning:** "Stop" from Old English "stoppian" (to block, close up). "Async" abbreviates "asynchronous," from Greek "a-" (not) + "syn" (together) + "chronos" (time) - not sharing the same time. "Iteration" from Latin "iterare" (to repeat).

**Why Python uses this:** PEP 492 (Python 3.5) introduced `async`/`await` and needed an asynchronous iterator protocol parallel to the existing one. Rather than invent new semantics, it mirrored them: `__aiter__`/`__anext__` mirror `__iter__`/`__next__`, and `StopAsyncIteration` mirrors `StopIteration` with "Async" spliced into the name. The name is deliberately derivative - it tells you it is the same signal, transposed to async code.

---

## Concept Explanation (Intermediate Level)

**What it does:**

Asynchronous iteration lets a loop await each item: `async for item in source` calls `source.__aiter__()` once, then awaits `source.__anext__()` for every element. The protocol needs a way for `__anext__` to say "there is no next item," and `StopAsyncIteration` is that message. The `async for` loop catches it internally and terminates - the programmer usually never sees the exception at all, just as `for` loops silently absorb `StopIteration`.

Like its synchronous twin, `StopAsyncIteration` is a normal, expected event, not a failure. Nothing has gone wrong when it is raised; a data source has simply been exhausted - the last page fetched, the stream closed, the queue drained. This non-error nature must survive translation: the name describes stopping the (asynchronous) iteration, and any rendering that borrows error/failure vocabulary teaches users to fear ordinary loop termination.

Who raises it depends on the iterator style. Class-based async iterators raise it explicitly in `__anext__` (Example 1). Async generator functions (`async def` with `yield`) never raise it themselves: when the function returns, Python raises `StopAsyncIteration` on their behalf - and if the body tries to raise it explicitly, PEP 525 converts that into `RuntimeError` to prevent the signal from leaking through the wrong layer (the same guard PEP 479 applies to `StopIteration` in plain generators). A separate exception class is necessary because in async code, `StopIteration` already has a job: coroutines use it internally to deliver return values, so exhaustion of an ASYNC iterator needed a distinct, unambiguous signal.

**Key behaviors:**

1. **Raised by `__anext__` to end `async for`:** The awaitable returned by `__anext__()` raises `StopAsyncIteration` when no items remain; the `async for` loop catches it and exits. Manual iteration with `await anext(gen)` (3.10+) surfaces it, and `anext(gen, default)` absorbs it.

2. **Automatic for async generators:** An async generator that returns triggers `StopAsyncIteration` implicitly. Explicitly raising it inside an async generator body is converted to `RuntimeError` (PEP 525) - the signal must come from the protocol layer, not through it.

3. **A signal, not an error - and distinct from `StopIteration`:** It subclasses `Exception` (unlike `GeneratorExit`), but semantically it reports normal exhaustion. It exists separately from `StopIteration` because the coroutine machinery reserves `StopIteration` for delivering awaited results.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun - action concept ("stop") + modifier ("async") + process noun ("iteration")
- **Action vs State:** EVENT/SIGNAL - marks the moment asynchronous iteration ends; not an error state
- **Temporal aspect:** Point-in-time - the boundary event at exhaustion

### Recommended Form

**Primary recommendation:** Derive mechanically from the existing `StopIteration` translation: insert the pack's established "async" term (the one used for the `async` keyword) at the position your language's grammar puts the modifier. The reader must see `StopIteration` inside `StopAsyncIteration`, exactly as in English.

**Forms to AVOID:**

- ❌ ANY word meaning "error," "failure," or "fault" - this is normal loop termination, nothing failed
- ❌ A different "stop" or "iteration" word than the `StopIteration` translation - the twin relationship must stay visible
- ❌ A different "async" word than the `async`/`await` keyword family - async vocabulary must be uniform across the pack

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: An ERROR that occurred during asynchronous iteration
- ❌ Meaning 2: A command instructing the programmer to stop iterating
- ❌ Meaning 3: Stopping asynchronously (i.e., "a stop that happens asynchronously")
- ✅ Meaning 4: **The SIGNAL that an ASYNCHRONOUS ITERATION has no more items - normal exhaustion of an async data source**

**Example:**

Parsing the compound "Stop-Async-Iteration":

1. "Something went wrong in the async loop" (error reading) ❌
2. "Stop! Async iteration!" (imperative to the reader) ❌
3. "(Stop-async) iteration" - a stop that is itself async ❌
4. "Stop (async-iteration)" - the async iteration is what stops ✅ **This is the Python meaning**

**Your translation should capture meaning #4: the modifier "async" attaches to "iteration," not to "stop." And as with `StopIteration`, this is NOT an error - the translation must not imply failure. It ends every `async for` loop that completes normally.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `StopAsyncIteration`, check these translations:**

- [ ] `StopIteration` - The twin: this term must be that translation plus the async modifier, nothing else changed
- [ ] `async` - The modifier must be the `async` keyword's established translation
- [ ] `await` - The async family verb; `await anext(...)` prose must read naturally
- [ ] `GeneratorExit` - Fellow control-flow signal; the signal family must stay uniformly free of error vocabulary
- [ ] `anext` / `aiter` - The async builtins that surface and drive this signal
- [ ] `for` - The `async for` construct that consumes the signal invisibly

**Consistency rule:**

Three vocabularies meet in this one name - the stop/iteration pair from `StopIteration`, and the async family from `async`/`await`. All three components must be reused verbatim from their existing translations; only the grammatical assembly (word order, agreement) is this term's own decision.


### Functional relationships

**This term works WITH:**

1. **`async for` + `StopAsyncIteration`**: The loop that catches it internally

```python
async def consume(stream):
    async for chunk in stream:
        process(chunk)
    # loop ended: StopAsyncIteration was raised and absorbed
```

2. **`__anext__` + `raise StopAsyncIteration`**: The protocol method that produces it

```python
async def __anext__(self):
    if self.exhausted:
        raise StopAsyncIteration
    return await self.fetch_next()
```

**Common pairing:**

```python
import asyncio

# A class-based async iterator over a paginated API (simulated)
class Paginated:
    def __init__(self, pages):
        self._pages = list(pages)

    def __aiter__(self):
        return self

    async def __anext__(self):
        await asyncio.sleep(0)          # yield control (simulated I/O)
        if not self._pages:
            raise StopAsyncIteration    # normal exhaustion - not an error
        return self._pages.pop(0)

async def main():
    # Invisible: async for absorbs the signal
    async for page in Paginated(["a", "b"]):
        print(page)

    # Visible: manual driving surfaces it
    it = Paginated(["x"]).__aiter__()
    print(await it.__anext__())         # x
    try:
        await it.__anext__()
    except StopAsyncIteration:
        print("exhausted")

asyncio.run(main())
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `StopAsyncIteration`

- Almost fully determined by prior decisions: `StopIteration` fixes two components, the `async` keyword fixes the third
- The remaining work is grammatical: modifier placement and agreement in a three-part compound
- Length is a genuine concern in some languages (renderings can run long, but so does the English)
- The signal-not-error rule must be maintained, but it was already established for `StopIteration`

**For this term:** MEDIUM

**Rationale:** `StopIteration` was rated MEDIUM, and this term inherits its solution wholesale - the only new decision is where the async modifier sits and how it agrees. That keeps it MEDIUM rather than easier: three-component compounds strain some languages' class-naming conventions, and the temptation to shorten by swapping components (breaking the twin relationship) is real. Translate it in the same pass as `StopIteration` and the `async` keyword whenever possible.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Reads as NORMAL EXHAUSTION of an async source (not a failure)?
- [ ] Contains NO word meaning error/failure/fault?
- [ ] "Async" modifies "iteration" (not "stop") in your rendering?

### 2. Linguistic Correctness

- [ ] Compound structure grammatical (agreement, word order)?
- [ ] Correct part of speech (event-naming compound noun)?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Contains the `StopIteration` translation's stop and iteration components verbatim?
- [ ] Uses the `async` keyword's established translation for the modifier?
- [ ] Signal family (`StopIteration`, `GeneratorExit`, this term) uniformly error-free?

### 4. Usability

- [ ] As short as the three-part concept allows?
- [ ] Recognizable at a glance as "async + StopIteration"?
- [ ] Easy to type on standard keyboard?

### 5. Cultural Appropriateness

- [ ] Uses technical/professional vocabulary?
- [ ] No confusing connotations?
- [ ] Respects CS education terminology?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs (especially RTL)?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: StopAsyncIteration
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
