# Python Keyword: `async` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** adjective (modifier)
**Python Version:** 3.5+
**Difficulty:** HARD

---

## Quick Summary

The `async` keyword in Python declares asynchronous functions (coroutines), context managers, and iterators that can perform non-blocking operations. It marks code that can use `await` to pause and resume execution cooperatively, enabling concurrent I/O operations on a single thread.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
import asyncio

# Regular function (synchronous)
def sync_hello():
    return "Hello"

# Async function (coroutine)
async def async_hello():
    return "Hello"

# Calling async function
result = asyncio.run(async_hello())
print(result)  # Hello
```

**What this does:** Adding `async` before `def` transforms a regular function into a coroutine function. Calling `async_hello()` doesn't execute the function immediately—it returns a coroutine object. You must `await` it or run it with `asyncio.run()` to execute.

### Example 2: Common Pattern

```python
import asyncio

# Async function with await
async def fetch_data(source):
    print(f"Fetching from {source}...")
    await asyncio.sleep(1)  # Non-blocking wait
    return f"Data from {source}"

# Multiple concurrent operations
async def main():
    # Run three fetches concurrently
    results = await asyncio.gather(
        fetch_data("API"),
        fetch_data("Database"),
        fetch_data("Cache")
    )
    print(results)

asyncio.run(main())
# All three fetches run concurrently, total time ~1 second
```

**What this does:** `async def` functions can use `await` to pause without blocking. The event loop switches between coroutines when they `await`, enabling concurrency. Three 1-second operations run in parallel, completing in ~1 second total instead of 3 seconds sequentially.

### Example 3: Edge Case

```python
import asyncio

# Async context manager
class AsyncResource:
    async def __aenter__(self):
        print("Acquiring resource")
        await asyncio.sleep(0.1)
        return self

    async def __aexit__(self, *args):
        print("Releasing resource")
        await asyncio.sleep(0.1)

async def use_resource():
    async with AsyncResource() as resource:
        print("Using resource")

# Async iterator
class AsyncCounter:
    def __init__(self, limit):
        self.count = 0
        self.limit = limit

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.count >= self.limit:
            raise StopAsyncIteration
        self.count += 1
        await asyncio.sleep(0.1)
        return self.count

async def iterate():
    async for num in AsyncCounter(3):
        print(num)

asyncio.run(iterate())  # Prints 1, 2, 3 with pauses
```

**What this shows:** `async` isn't just for functions. `async with` creates async context managers (with `__aenter__` and `__aexit__` coroutines). `async for` iterates over async iterators (with `__aiter__` and `__anext__`). These enable asynchronous resource management and iteration.

---

## Pattern Classification

**This term is:** MODIFIER KEYWORD (Declaration Adjective)

**Similar terms in this pattern:**

1. `def` - Declares functions (async modifies def to create coroutines)
2. `with` - Context manager (async modifies with for async context managers)
3. `for` - Iteration (async modifies for for async iterators)

**Pattern rule:** Declaration modifiers should use adjective forms describing the nature/type of what's being declared. `async` describes the asynchronous nature of functions, context managers, or iterators.


---

## Etymology (Brief)

**English Origin:** Greek prefix via Latin

**Root meaning:** Greek "a-" (not/without) + "syn" (together/with) + "chronos" (time) = "not at the same time." Through Latin "asynchronus," it became English "asynchronous," meaning "not synchronized, not occurring at the same time."

**Why Python uses this:** "Async" (short for "asynchronous") perfectly captures concurrent programming: multiple operations progress independently, not synchronized to a single timeline. Async operations don't block each other—they run concurrently. Python abbreviates "asynchronous" to "async" for brevity, following JavaScript's `async/await` syntax (2017). The term is increasingly standard across languages (C#, Rust, JavaScript, Kotlin).

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `async` keyword marks functions, context managers, and iterators as asynchronous, meaning they can pause and resume execution cooperatively. An `async def` function is a coroutine function that returns a coroutine object when called. Coroutines can use `await` to pause execution, yielding control to the event loop to run other coroutines.

This enables concurrency without threads: thousands of I/O operations (network requests, file reads, database queries) can run "simultaneously" on a single thread. When one coroutine awaits I/O, the event loop switches to another coroutine. This cooperative multitasking is efficient for I/O-bound workloads.

`Async` also modifies `with` and `for` statements: `async with` creates async context managers (resource acquisition/release that can await), and `async for` iterates over async iterators (iteration steps that can await). These enable asynchronous versions of synchronous patterns.

**Key behaviors:**

1. **Creates coroutines:** `async def` functions don't execute when called. They return coroutine objects that must be awaited or scheduled on the event loop. This lazy execution enables the event loop to manage when and how coroutines run.

2. **Enables await:** Only `async def` functions can use `await`. The `async` keyword establishes an async context where `await` is valid. Regular functions can't await—attempting it causes a SyntaxError.

3. **Concurrency, not parallelism:** Async provides concurrency (multiple operations in progress) but not true parallelism (multiple operations executing simultaneously). All async code runs on one thread via cooperative multitasking. For CPU-bound work, use multiprocessing or threads. For I/O-bound work, async is ideal.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Adjective/modifier (describes nature of function/context)
- **Action vs State:** STATE descriptor - describes asynchronous property
- **Temporal aspect:** Static - the async nature doesn't change

### Recommended Form

**Primary recommendation:** Use adjective form meaning "asynchronous" or "not synchronous." The word should describe code that doesn't execute synchronously, allowing concurrent non-blocking operations. Often abbreviated like English "async" from "asynchronous."

**Forms to AVOID:**

- ❌ Using "parallel" - wrong concept (parallelism vs. concurrency)
- ❌ Using "concurrent" - close but "asynchronous" is more precise
- ❌ Using verb "to make async" - should be adjective

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

NO (in computing context)

**"Async" is an abbreviation of "asynchronous," which in computing has one clear meaning:**

**"Not synchronized; operations that proceed independently without waiting for each other, enabling concurrency through non-blocking execution."**

In non-computing contexts, "asynchronous" can mean:

- General lack of synchronization
- Not occurring at the same time (events)
- Communication that doesn't require simultaneous presence (async messaging)

But in Python, "async" specifically means: **code that uses the async/await pattern for cooperative concurrent non-blocking I/O operations managed by an event loop.**

**Key semantic components:**

- **Non-blocking:** Operations don't wait idly, blocking the thread
- **Concurrent:** Multiple operations in progress (not necessarily parallel)
- **Cooperative:** Explicit `await` points for task switching
- **Event loop managed:** Runtime schedules coroutine execution

**Translation must capture "asynchronous" concept, not generic "non-synchronous."**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `async`, check these translations:**

- [ ] `await` - Works inside async functions; both are async/await pair
- [ ] `def` - Modified by async (async def); both relate to function declaration
- [ ] `with`/`for` - Also modified by async (async with, async for)
- [ ] Conceptual opposite: "synchronous" - Should be linguistically related
- [ ] `StopAsyncIteration` - Ends `async for`; must reuse this keyword's async marker

**Consistency rule:**

Async keywords (`async`, `await`) are paired and should work together linguistically. `async` is adjective describing the context, `await` is verb acting within that context. Both should maintain the async/await pattern recognizable across languages.


### Functional relationships

**This term works WITH:**

1. **`async def`:** Declares coroutine functions

```python
async def fetch():
    return await get_data()
```

2. **`async with`:** Async context managers

```python
async with aiohttp.ClientSession() as session:
    response = await session.get(url)
```

3. **`async for`:** Async iteration

```python
async for item in async_generator():
    process(item)
```

**Common pairing:**

```python
# Async function (coroutine)
async def fetch_data():
    await asyncio.sleep(1)
    return "data"

# Async context manager
async def download():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

# Async iterator
async def number_generator():
    for i in range(10):
        await asyncio.sleep(0.1)
        yield i

async def consume():
    async for num in number_generator():
        print(num)

# Multiple async functions with gather
async def main():
    results = await asyncio.gather(
        fetch_user(),
        fetch_posts(),
        fetch_comments()
    )
    return results

# Async comprehension
async def get_squares():
    return [i**2 async for i in async_range(10)]

# Async with error handling
async def safe_fetch():
    try:
        async with timeout(5):
            return await fetch_data()
    except asyncio.TimeoutError:
        return None

# Mixing sync and async (await in event loop)
def sync_caller():
    result = asyncio.run(async_function())
    return result

# Async property (Python 3.5+)
class AsyncResource:
    async def __aenter__(self):
        self.resource = await acquire()
        return self.resource

    async def __aexit__(self, *args):
        await release(self.resource)
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

### HARD

- No direct equivalent in some languages
- May need compound term or explanation
- Concept doesn't exist universally
- **AI confidence should be MEDIUM, human review recommended**

### Why HARD for `async`

- Modern concept (Python 3.5+, 2015; popularized by JavaScript 2017)
- Not all programming languages have async/await
- Requires understanding concurrency vs. parallelism distinction
- "Asynchronous" is a complex technical term
- Some languages may still be developing standard translations
- Must distinguish from threads, parallelism, synchronous non-blocking I/O

**For this term:** HARD

**Rationale:** Async/await is modern, advanced Python feature. While "asynchronous" exists in most languages as a general term, its specific async/await meaning in programming is newer. CS education in some languages may not yet have established standard async/await translations. Translators must understand the cooperative concurrency model. "Asynchronous" might be abbreviated (like "async") or kept full, requiring regional preference knowledge. Human review recommended to ensure translation aligns with emerging async programming terminology.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures ASYNCHRONOUS concept (not synchronous)?
- [ ] Conveys NON-BLOCKING, concurrent nature?
- [ ] Distinguishes from parallelism (multi-core) and threading?
- [ ] Understood as modifier for functions/context managers/iterators?

### 2. Linguistic Correctness

- [ ] Correct part of speech (adjective/modifier)?
- [ ] Describes property (async nature), not action?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python keywords)?
- [ ] Abbreviation appropriate if used (like "async" from "asynchronous")?

### 3. Consistency

- [ ] Matches pattern with `await` (adjective + verb pair)?
- [ ] Works with `def`, `with`, `for` (as modifier)?
- [ ] Opposite of "synchronous" (linguistically related)?
- [ ] Aligns with async terminology in target language CS education?

### 4. Usability

- [ ] Short enough (1-2 words, abbreviation acceptable)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Recognizable to developers familiar with async/await pattern?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional?
- [ ] Technical and formal enough?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: async
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
