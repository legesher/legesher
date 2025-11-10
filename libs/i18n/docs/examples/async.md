# Python Keyword: `async` - Comprehensive Reference (Tier 2)

**Category:** keyword (modifier/prefix)
**Type:** adjective/modifier (transforms function into coroutine)
**Python Version:** 3.5+ (introduced in PEP 492)
**Related Terms:** `await`, `async def`, `async for`, `async with`, `asyncio`

**Note:** This is the Tier 2 comprehensive reference example demonstrating a **complex modern keyword** with
contextual usage patterns.

**Purpose:** Complete reference for human translators, beta testers, and future educational content
(legesher.io/learn).

---

## Quick Summary

The `async` keyword is used to declare asynchronous functions (coroutines), context managers, and iterators in
Python. When placed before `def`, `with`, or `for`, it transforms them into asynchronous versions that can pause
execution and resume later, enabling concurrent programming.

---

## Etymology & History

### English Etymology

**Origin:** Greek prefix
**Root Words:** From Greek *asyn-* (not) + *chronos* (time), meaning "not at the same time"
**Meaning Evolution:** "Asynchronous" means operations that don't happen in a synchronized, sequential order.
In programming, async operations can start, pause, and resume independently.

**Example:**
> "Asynchronous" comes from Greek: *a-* (not) + *syn-* (together) + *chronos* (time). It describes operations
> that don't need to happen at the same moment — they can overlap or happen out of sequence.

**Modern Computing Usage:**
In computer science, "async" became shorthand for "asynchronous" in the 1990s-2000s with the rise of
event-driven and concurrent programming models (AJAX, Node.js callback hell, etc.).

### Why Python Chose This Term

**Designer Intent:**
Python 3.5 (PEP 492, 2015) introduced `async`/`await` syntax to make asynchronous programming more explicit and
readable. The keyword `async` clearly marks that a function will not execute synchronously.

**Alternatives Considered:**

- Earlier Python used `@asyncio.coroutine` decorator (Python 3.4) — too verbose
- Other languages use: `async` (JavaScript, C#, Rust) — Python followed this convention
- Could have used `coroutine` or `concurrent` — too long and less clear

**Historical Context:**

- **Python 3.4 (2014):** asyncio module with decorator-based coroutines
- **Python 3.5 (2015):** PEP 492 added `async`/`await` syntax
- **Python 3.6+:** Async generators, async comprehensions
- **Python 3.7+:** `async` and `await` became reserved keywords (always)

**PEP References:**

- **[PEP 492](https://peps.python.org/pep-0492/):** Coroutines with async and await syntax (Python 3.5)
- **[PEP 525](https://peps.python.org/pep-0525/):** Asynchronous Generators (Python 3.6)
- **[PEP 530](https://peps.python.org/pep-0530/):** Asynchronous Comprehensions (Python 3.6)

### Cross-Language Comparison

How other programming languages handle asynchronous programming:

| Language | Syntax | Notes |
|----------|--------|-------|
| JavaScript | `async function` | Same keyword, similar syntax |
| C# | `async Task` | Same keyword, type-based |
| Rust | `async fn` | Same keyword, compile-time async |
| Kotlin | `suspend fun` | Uses "suspend" instead of "async" |
| Go | `go` keyword | Different model (goroutines) |
| Java | `CompletableFuture` | Library-based, no keyword |
| Swift | `async` | Same keyword (added in Swift 5.5) |

**Python's Approach:** Python followed JavaScript and C#'s lead in using `async` as a keyword prefix,
making async code visually distinct from synchronous code.

---

## Concept Explanation (Multi-Level)

### For a 5-Year-Old 🧒

Imagine you're making breakfast. Normally, you make toast, then wait for it to pop up, then make juice.

**Synchronous (regular) way:**

1. Put bread in toaster → **wait** → get toast
2. Pour juice → **wait** → get juice
3. Eat breakfast

**Asynchronous (async) way:**

1. Put bread in toaster → **DON'T WAIT**, start pouring juice
2. While toaster works, you're pouring juice at the same time!
3. Toast pops up → grab it
4. Juice is ready → grab it
5. Eat breakfast (finished faster!)

`async` tells Python: "This task can wait — go do other things while waiting!"

### For a Beginner Programmer 📚

**What it does:**
The `async` keyword creates functions that can pause and resume. Instead of blocking (waiting), async functions can
yield control to other tasks.

**Simple Example:**

```python
import asyncio

# Regular synchronous function (blocks/waits)
def greet_sync(name):
    time.sleep(1)  # Blocks for 1 second
    print(f"Hello, {name}!")

# Async function (can pause without blocking)
async def greet_async(name):
    await asyncio.sleep(1)  # Pauses, but doesn't block
    print(f"Hello, {name}!")

# Run async function
async def main():
    # Run three greetings concurrently (total ~1 second, not 3)
    await asyncio.gather(
        greet_async("Alice"),
        greet_async("Bob"),
        greet_async("Charlie")
    )

asyncio.run(main())  # All three print after ~1 second
```

**Key Points:**

- `async def` creates an async function (coroutine)
- Async functions must be called with `await` or run via `asyncio.run()`
- `await` pauses the function until the awaited operation completes
- Multiple async operations can run concurrently
- Async is **cooperative** - functions must explicitly `await` to yield control

### For Intermediate Programmers 💻

**Technical Definition:**
`async` is a keyword prefix that transforms:

- `async def` → Creates a coroutine function (returns coroutine object)
- `async with` → Creates an async context manager
- `async for` → Creates an async iterator

Async functions use cooperative multitasking - they voluntarily yield control at `await` points, allowing other async
tasks to run.

**How It Works:**

```python
async def fetch_data(url):
    """Fetch data asynchronously."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
```

**Under the hood:**

1. `async def` creates a coroutine function
2. Calling it returns a coroutine object (doesn't execute yet)
3. Coroutine must be awaited or scheduled in event loop
4. At each `await`, coroutine suspends and event loop can run other tasks
5. When awaited operation completes, coroutine resumes

**Important Behaviors:**

1. **Coroutine vs Regular Function:** Async functions don't run immediately when called

   ```python
   async def example():
       return 42

   result = example()  # Returns coroutine object, doesn't run!
   # Must await: result = await example()
   ```

2. **await Only in Async Context:** Can only use `await` inside `async` functions

   ```python
   async def valid():
       await something()  # ✅ Valid

   def invalid():
       await something()  # ❌ SyntaxError
   ```

3. **Concurrency != Parallelism:** Async runs tasks concurrently (interleaved), not parallel (simultaneously)
   - **Concurrent:** Tasks overlap in time, switching between them
   - **Parallel:** Tasks run simultaneously on multiple CPU cores

4. **Event Loop Dependency:** Async code requires an event loop
   (asyncio.run(), asyncio.get_event_loop())

**Common Patterns:**

```python
# Pattern 1: Basic async function
async def fetch_page(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

# Pattern 2: Concurrent execution
async def fetch_all_pages(urls):
    tasks = [fetch_page(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return results

# Pattern 3: Async context manager
async def process_file(filename):
    async with aiofiles.open(filename) as f:
        contents = await f.read()
        return contents

# Pattern 4: Async iteration
async def process_stream():
    async for item in async_generator():
        print(item)

# Pattern 5: Timeout handling
async def fetch_with_timeout(url, timeout=5):
    try:
        return await asyncio.wait_for(fetch_page(url), timeout=timeout)
    except asyncio.TimeoutError:
        return None
```

### For Expert Developers 🎓

**Implementation Details:**

Async functions are implemented using coroutine objects and the generator protocol. CPython's implementation:

- Coroutines are generator-like objects with `send()`, `throw()`, and `close()` methods
- Event loop schedules coroutines and manages `await` suspension points
- `await` compiles to `YIELD_FROM` bytecode (similar to `yield from`)

**Bytecode:**

```python
import dis

async def simple_async():
    await asyncio.sleep(1)
    return 42

dis.dis(simple_async)
```

Output shows coroutine-specific bytecode:

```text
GET_AWAITABLE
LOAD_CONST  None
YIELD_FROM
RETURN_VALUE
```

**Performance Considerations:**

- **Overhead:** Async has approximately 5-10% overhead vs synchronous code for CPU-bound tasks
- **Sweet Spot:** Massive gains (10-100x) for I/O-bound tasks with many concurrent operations
- **When to avoid:** CPU-bound tasks (use `multiprocessing` instead)
- **Memory:** Each coroutine is lightweight (approximately 1-2KB), can have thousands concurrently

**Advanced Usage:**

```python
# Advanced 1: Creating async iterators
class AsyncRange:
    def __init__(self, start, stop):
        self.current = start
        self.stop = stop

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.current >= self.stop:
            raise StopAsyncIteration
        await asyncio.sleep(0.1)  # Simulate async work
        value = self.current
        self.current += 1
        return value

# Usage
async for num in AsyncRange(0, 5):
    print(num)

# Advanced 2: Async context managers
class AsyncResource:
    async def __aenter__(self):
        print("Acquiring resource")
        await asyncio.sleep(0.1)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("Releasing resource")
        await asyncio.sleep(0.1)

# Usage
async with AsyncResource() as resource:
    print("Using resource")

# Advanced 3: Mixing sync and async
import concurrent.futures

async def run_sync_in_async(sync_func, *args):
    """Run synchronous code in async context."""
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, sync_func, *args)
    return result

# Advanced 4: Async generator expressions (PEP 530)
async def async_squares(n):
    result = [x**2 async for x in AsyncRange(0, n)]
    return result
```

**Related PEPs:**

- [PEP 492](https://peps.python.org/pep-0492/): Coroutines with async/await (Python 3.5)
- [PEP 525](https://peps.python.org/pep-0525/): Asynchronous Generators (Python 3.6)
- [PEP 530](https://peps.python.org/pep-0530/): Asynchronous Comprehensions (Python 3.6)
- [PEP 567](https://peps.python.org/pep-0567/): Context Variables (async context)
- [PEP 3156](https://peps.python.org/pep-3156/): Asynchronous IO Support (asyncio module)

---

## Linguistic Form Recommendation

### Part of Speech Analysis

**English Term Category:** adjective/modifier (modifies function/context/loop)

**In Python Context:**

- **Grammatical Role:** Modifier/prefix - transforms the nature of what follows
- **Action vs State:** Neither pure action nor state - it's a **transformation marker**
- **Temporal Aspect:** Indicates time-independence (asynchronous behavior)

### Recommended Translation Form

**Primary Recommendation:** Keep as transliteration "async" OR translate as adjective meaning
"asynchronous"

**Rationale:**
`async` is a unique challenge because:

1. It's a **modern technical term** (2015, post-internet era)
2. It's already abbreviated in English ("async" from "asynchronous")
3. It's a **marker/modifier**, not a standalone action
4. It's used across multiple languages (JavaScript, C#, Rust, Swift) with the same meaning
5. The concept is **new** to most languages - there may not be established terminology

**Translation Strategy Options:**

**Option A: Transliteration (Recommended for many languages)**
Keep "async" as-is because:

- It's an international technical term
- Consistent with JavaScript, C#, Rust usage
- Developers already familiar with the term from other contexts

**Option B: Translate the Concept**
Translate as adjective/modifier meaning "asynchronous":

- Spanish: "asíncrono" (adjective)
- French: "asynchrone" (adjective)
- German: "asynchron" (adjective)
- Chinese: "异步" (yìbù - asynchronous)
- Arabic: "غير متزامن" (ghayr mutazamin - not synchronized)

**Why adjective, not verb?**
`async` doesn't DO something - it DESCRIBES the nature of what follows. It's a modifier.

**Forms to Avoid:**

- ❌ **Verb form:** "asynchronize", "asincronizar" - wrong, it's not an action
- ❌ **Noun form:** "asynchrony", "asincronía" - wrong, it's not a thing
- ❌ **Adverb:** "asynchronously" - too long and wrong part of speech

### Examples Across Language Families

| Language Family | Recommended Form | Example Translation | Rationale |
|-----------------|------------------|---------------------|-----------|
| Romance (es, fr, pt) | Adjective OR keep "async" | es: asíncrono OR async | Cognate exists, but "async" widely used in tech |
| Germanic (de, nl) | Adjective OR keep "async" | de: asynchron OR async | Germanic has cognate, both valid |
| Slavic (ru, pl) | Adjective OR transliterate | ru: асинхронный OR async | Cyrillic: асинк OR keep Latin async |
| Arabic | Translate OR keep | غير متزامن OR async | "Not synchronized" OR keep tech term |
| Chinese | Translate | 异步 (yìbù) | Established CS term for "asynchronous" |
| Hindi | Translate OR transliterate | असमकालिक OR async | "Not concurrent" OR keep tech term |
| Japanese | Katakana OR translate | 非同期 (hidōki) OR アシンク | Established term 非同期 preferred |
| Korean | Translate | 비동기 (bidonggi) | Established term for "asynchronous" |

**Consistency Note:** Whatever form is chosen, apply consistently to:

- `async def` → {async} {def}
- `async with` → {async} {with}
- `async for` → {async} {for}

---

## Syntax Role in Python

### Grammar Position

**Where it appears:**
As a prefix/modifier before `def`, `with`, or `for` statements.

**Syntax Patterns:**

```python
# Pattern 1: async def (async function/coroutine)
async def <function_name>(<parameters>):
    <function_body>

# Pattern 2: async with (async context manager)
async with <expression> as <target>:
    <block>

# Pattern 3: async for (async iteration)
async for <target> in <async_iterable>:
    <block>
```

### What It Creates/Does

**Primary Function:**
Transforms a regular construct into its asynchronous equivalent:

- `async def` - Creates coroutine function (returns coroutine object)
- `async with` - Uses async context manager (`__aenter__`, `__aexit__`)
- `async for` - Iterates over async iterator (`__aiter__`, `__anext__`)

**Creates:**

- Coroutine objects (callable via `await` or event loop)
- Suspension points (where execution can pause)
- Event loop integration points
- Non-blocking I/O opportunities

### Scope Behavior

**Scope Rules:**

- `async def` creates functions with same scope rules as regular `def`
- Async functions can access enclosing scopes (closures work normally)
- `await` can only appear inside `async` functions (enforced by compiler)

**Example:**

```python
# Global scope
value = 10

async def outer():
    # Enclosing scope
    local_value = 20

    async def inner():
        # Can await here (inside async function)
        await asyncio.sleep(1)
        print(value)  # Access global
        print(local_value)  # Access enclosing (closure)

    return await inner()

# Must run in async context
asyncio.run(outer())
```

### Related Syntax Components

**Works with:**

- `await` - Suspends async function until awaited operation completes (REQUIRED together)
- `def` - `async def` defines coroutine
- `with` - `async with` for async context managers
- `for` - `async for` for async iteration
- `asyncio` module - Event loop management

**Often paired with:**

```python
# async + await (most common pairing)
async def fetch():
    data = await get_data()  # async + await always together
    return data

# async + with + for (complex async patterns)
async def process_stream():
    async with connect_to_stream() as stream:
        async for item in stream:
            await process(item)
```

---

## Related Concepts

### Similar Keywords/Builtins

**Conceptually Similar:**

- `await` - Pauses async function (always used with `async`)
- `def` - `async def` is async version of `def`
- `with` - `async with` is async version of `with`
- `for` - `async for` is async version of `for`
- `yield` - Both create suspension points (but different purposes)

**Key Differences:**

| Feature | `async def` | `def` | `yield` |
|---------|-------------|-------|---------|
| Returns | Coroutine object | Function result | Generator |
| Execution | Non-blocking (with await) | Blocking | Lazy (on demand) |
| Can use await | Yes | No | No (unless `async def`) |
| Use case | I/O-bound concurrency | Standard functions | Lazy iteration |

### Associated Keywords

**Frequently Used Together:**

- `async` + `await` - Core async/await pair (95% of async code)
- `async` + `def` - Defines coroutine functions
- `async` + `for` - Async iteration
- `async` + `with` - Async context management

**Async Ecosystem:**

```python
# Full async pattern
import asyncio
import aiohttp

async def main():
    # async def + await
    async def fetch(url):
        async with aiohttp.ClientSession() as session:  # async with
            async with session.get(url) as response:
                return await response.text()  # await

    # Concurrent execution
    urls = ["https://example.com", "https://example.org"]
    results = await asyncio.gather(*[fetch(url) for url in urls])

    # async for
    async for result in process_results(results):
        print(result)

asyncio.run(main())
```

### Common Patterns

**Pattern 1: Basic Async Function**

```python
async def hello_async():
    print("Hello")
    await asyncio.sleep(1)
    print("World")
```

**Pattern 2: Concurrent Tasks**

```python
async def concurrent_tasks():
    task1 = asyncio.create_task(operation1())
    task2 = asyncio.create_task(operation2())
    result1 = await task1
    result2 = await task2
    return result1, result2
```

**Pattern 3: Async HTTP Requests**

```python
async def fetch_multiple(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [session.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [await r.text() for r in responses]
```

**Pattern 4: Async Database Operations**

```python
async def query_database():
    async with aiosqlite.connect("db.sqlite") as db:
        async with db.execute("SELECT * FROM users") as cursor:
            async for row in cursor:
                yield row
```

---

## Common Misconceptions

### Misconception 1: "async makes code run faster"

**What People Think:**
Adding `async` automatically speeds up code.

**What Actually Happens:**
`async` enables **concurrency** (overlapping tasks), not **parallelism** (simultaneous execution). For CPU-bound
tasks, async can actually be slower due to overhead.

**Example Showing the Truth:**

```python
import time
import asyncio

# CPU-bound task (calculating)
def sync_cpu_bound():
    total = sum(i**2 for i in range(10_000_000))
    return total

async def async_cpu_bound():
    total = sum(i**2 for i in range(10_000_000))
    return total

# Sync is FASTER for CPU-bound!
start = time.time()
sync_cpu_bound()
print(f"Sync: {time.time() - start:.2f}s")  # ~0.5s

start = time.time()
asyncio.run(async_cpu_bound())
print(f"Async: {time.time() - start:.2f}s")  # ~0.5s (no improvement)
```

**When async IS faster:** I/O-bound tasks (network, disk) where waiting time can overlap.

### Misconception 2: "await runs code in the background"

**What People Think:**
`await` starts background execution like threads.

**What Actually Happens:**
`await` **pauses** the current coroutine and lets the event loop run other tasks. Nothing runs "in the
background" - it's cooperative multitasking.

**Example:**

```python
async def task():
    print("Start")
    await asyncio.sleep(1)  # PAUSES here, switches to other tasks
    print("End")

# Only ONE thing runs at a time, but they interleave
```

### Misconception 3: "async functions run automatically"

**What People Think:**
Defining `async def` makes the function run asynchronously automatically.

**What Actually Happens:**
Async functions must be explicitly awaited or scheduled in an event loop. Just calling them returns a coroutine
object (doesn't execute).

**Example:**

```python
async def greet():
    print("Hello")

# This does NOTHING (returns coroutine object)
greet()  # ❌ No output

# Must await or run
await greet()  # ✅ Inside async function
asyncio.run(greet())  # ✅ Top-level
```

### Edge Cases to Know

1. **Blocking calls break async:** Synchronous blocking operations (time.sleep, requests.get) block the
   entire event loop

   ```python
   async def bad():
       time.sleep(1)  # ❌ Blocks event loop

   async def good():
       await asyncio.sleep(1)  # ✅ Yields control
   ```

2. **async without await is useless:** Async function that never awaits gains no benefit

   ```python
   async def pointless():
       return 42  # No await = no benefit from async
   ```

3. **Mixing sync/async requires care:** Can't directly call async from sync without event loop

   ```python
   def sync_function():
       # ❌ Can't do this
       result = await async_function()

       # ✅ Must do this
       result = asyncio.run(async_function())
   ```

---

## Educational Context Research

### How is `async` taught across different regions?

#### In English-speaking countries

**Teaching approach:**
Educators typically introduce `async`/`await` as:

- Evolution from callback hell and threading complexity
- Cooperative multitasking model
- I/O-bound task optimization
- Modern Python concurrency (post-2015)

**Common analogies/metaphors:**

- Restaurant server (takes order, doesn't wait for kitchen, serves other tables)
- Web browser tabs (switching between tasks while loading)
- Multitasking human (start laundry, cook dinner, work on laptop simultaneously)

**Resources checked:**

- Real Python: "Async IO in Python: A Complete Walkthrough"
- Python.org asyncio docs: Emphasizes coroutines and event loop
- University courses (MIT, Berkeley): Introduce after covering threads/multiprocessing

#### In Spanish-speaking countries

**Research findings:**
Most Spanish programming resources keep "async" untranslated or use "asíncrono".

**Educational resources:**

- **Textbook terms:** "asíncrono" (adjective) or "async" (untranslated)
- **Spanish Python docs:** Use "asíncrono" in explanations, keep `async` in code
- **Online tutorials:** Mix of "async" and "función asíncrona"

**Regional variations:**
No significant differences. Both Spain and Latin America use:

- Code: `async def`
- Explanation: "función asíncrona" or "corrutina"

**Consensus:** Keep `async` in code, explain as "asíncrono" in documentation.

#### In Arabic-speaking countries

**Research findings:**
Programming teaching is predominantly English, especially for modern concepts like async.

**Terminology when translated:**

- غير متزامن (ghayr mutazamin) - "not synchronized"
- This is technical MSA, rarely used in code

**Reality:** Most keep "async" untranslated in code, explain concept in Arabic if needed.

#### In Chinese-speaking regions

**Research findings:**
Chinese CS education has established term for asynchronous.

**Common textbook terminology:**

- 异步 (yìbù) - "asynchronous" (异 = different, 步 = step/pace)
- This is standard CS term in Chinese

**Established translations:**

- Chinese Python docs use: `async` in code, 异步 in explanations
- University courses: Teach as "异步编程" (yìbù biānchéng - async programming)

**Consensus:** Code keeps `async`, concepts explained with 异步 (yìbù).

#### In Hindi-speaking regions (India)

**Research findings:**
CS education is English-medium. Async concepts taught in English.

**Terminology preferences:**

- असमकालिक (asamkaalik) - "not concurrent" (formal Sanskrit-derived term)
- Rarely used in practice — most keep "async"

**Reality:** Indian developers use "async" universally, even in Hindi discussions.

### Synthesis

**Most common approach across languages:**

- **Code:** Keep `async` keyword untranslated (international technical term)
- **Documentation:** Explain concept using native language adjective for "asynchronous"
- **Reason:** `async` is post-internet technical jargon, already shared across languages

**Key vocabulary alignment:**

- Spanish: "async" in code, "asíncrono" in docs
- Chinese: "async" in code, "异步" (yìbù) in docs
- Arabic: "async" in code, "غير متزامن" in docs
- Hindi: "async" in code, English explanation

**Recommendation:**
Given that `async` is:

1. Modern technical term (2015, internet era)
2. Used identically in JavaScript, C#, Rust, Swift, Python
3. Already abbreviated in English

**Two valid approaches:**

- **Approach A:** Keep `async` untranslated (recommended for consistency with other languages)
- **Approach B:** Translate to adjective form in languages with established term (Chinese: 异步)

---

## Enhanced Cross-References

### Functional Relationships

**How `async` works WITH other terms:**

#### Relationship 1: `async` + `await` (INSEPARABLE PAIR)

**Context:** Cannot use one without the other in practice

```python
async def fetch():  # async creates coroutine
    data = await get_data()  # await suspends coroutine
    return data
```

**Translation note:** These are a matched pair. If you keep `async`, strongly consider keeping `await`.
If you translate both, use related terms:

- `async` = adjective "asynchronous"
- `await` = verb "wait for" or "suspend for"

#### Relationship 2: `async` + `def`

**Context:** Most common usage — async function definition

```python
async def my_function():
    pass
```

**Translation note:** `async` modifies `def`. If translating both:

- Keep grammatical relationship clear: [async] [def]
- Spanish: "asíncrono definir" OR "async definir"

#### Relationship 3: `async` + `for` / `with`

**Context:** Async iteration and context management

```python
async for item in items:  # async modifies for
    pass

async with resource:  # async modifies with
    pass
```

**Translation note:** Same modifier relationship. Consistency is key - if you translate `async` for `async def`,
translate it the same way for `async for` and `async with`.

### Conceptual Hierarchy

**Where `async` sits in Python's mental model:**

```text
Python Concurrency Models
├── Threading (OS-level, parallel, pre-emptive)
├── Multiprocessing (process-level, parallel)
└── Async/Await (event loop, concurrent, cooperative)
    ├── async def ← async keyword here
    ├── async with
    ├── async for
    └── await
```

**What this hierarchy means for translation:**
`async` is part of Python's concurrency system. It's conceptually related to threading/multiprocessing but uses a
different model. Translations should make clear this is about concurrency, not parallelism.

### Translation Consistency Requirements

**Terms that MUST align linguistically with `async`:**

When translating `async`:

- [ ] Check your `await` translation (both are the async/await pair)
- [ ] Check your `asyncio` module naming (related ecosystem)
- [ ] Ensure `async for` and `async with` use same `async` translation
- [ ] Consider relationship with `concurrent`, `parallel` terms in docs

**Consistency rule:**
If you translate `async` in one context (async def), translate it identically in all contexts
(async with, async for).

**Good example (consistent):**

Spanish:

- `async def` → "asíncrono def" OR all `async` untranslated
- `async for` → "asíncrono for" OR all `async` untranslated
- `async with` → "asíncrono with" OR all `async` untranslated

All uses of `async` handled the same way ✅

**Bad example (inconsistent):**

Spanish:

- `async def` → "asíncrono def"
- `async for` → "async for" (untranslated) ❌
- `async with` → "con asincronía" (different form) ❌

---

## Cognitive Load & Learning Considerations

### Memory Load

**Is this translation easy to remember?**

**If keeping "async" untranslated:** Yes, it's the same across all programming languages
(JavaScript, C#, Python, etc.). Developers learning async in one language transfer knowledge easily.

**If translating:** Depends on whether target language has established term:

- Chinese 异步 (yìbù): Well-established CS term ✅
- Arabic غير متزامن: Less established, longer ⚠️

**Mnemonic potential:**
"Async" sounds like "a-sync" (not synchronized), which helps understanding even as English borrowing.

### Disambiguation

**Ambiguity in English:**
"Async" is unambiguous in programming contexts. Outside tech, rarely used.

**In other languages:**

- Spanish "asíncrono" only used in technical contexts
- Chinese "异步" primarily technical term
- Keeping "async" eliminates any potential confusion

### Pronunciation

**Can developers say this term out loud easily?**

**As "async" (English borrowing):**

- Most languages can pronounce it: "a-sink" or "a-sync"
- Already familiar from JavaScript, web development

**As translation:**

- Spanish "asíncrono" — 4 syllables, easy to say
- Chinese "异步" (yìbù) — 2 syllables, easy
- Arabic "غير متزامن" — longer, more syllables

**Test:** Try saying "async function" in target language

- English/Borrowed: "async function" — short, flows well
- Spanish: "función asíncrona" — natural
- Chinese: "异步函数" (yìbù hánshù) — natural

### Visual Recognition

**Can learners quickly spot `async` when scanning code?**

**As untranslated "async":**

- Very distinctive (5 letters, uncommon pattern)
- Always appears at start of line or before `for`/`with`
- Easy to spot: `async def`, `async with`, `async for`

**As translation:**

- Longer words may be less distinctive
- Must test visual scanning in actual code

**Recommendation:** Shorter is better for quick code scanning.

### Cross-Language Transfer

**Many programmers are multilingual:**

**Advantage of keeping "async" untranslated:**

- Developer learning Python after JavaScript: Instant recognition
- Stack Overflow, GitHub code examples: Same term
- Official Python docs: Can follow English resources
- No mental translation needed when switching languages

**Disadvantage:**

- May feel foreign to native speakers unfamiliar with term
- Less accessible to beginners learning programming for first time

**Balance:**
For `async` specifically, the international consistency benefit likely outweighs localization benefits,
especially given how recent the term is (2015).

---

## Translation Validation Criteria

### For Human Reviewers & Beta Testers

Use this checklist to evaluate the translation of `async`:

#### Concept Accuracy (CRITICAL)

- [ ] Does this translation capture what `async` DOES? (marks asynchronous behavior)
- [ ] Is it clear this is about concurrency, not parallelism?
- [ ] Does it avoid confusion with threading/multiprocessing?
- [ ] Is relationship with `await` clear?

#### Linguistic Correctness

- [ ] Is the part of speech correct? (Should be adjective/modifier)
- [ ] Does it modify the following construct correctly (`def`, `for`, `with`)?
- [ ] Is capitalization appropriate? (Should be all lowercase)
- [ ] For RTL languages: Tested in actual code?

#### Consistency with Pattern

- [ ] Same translation for `async def`, `async for`, `async with`?
- [ ] Aligns with `await` translation?
- [ ] Consistent with how other languages handle this term?

#### Usability

- [ ] Short enough? (Ideally 1 word, max 2)
- [ ] Easy to type?
- [ ] Easy to pronounce?
- [ ] Visually distinctive in code?

#### Cultural Appropriateness

- [ ] Appropriate technical register?
- [ ] Not confusing with non-technical meanings?

#### CS Education Alignment

- [ ] Matches terminology in target language async tutorials?
- [ ] Compatible with JavaScript/C# developers who know "async"?

#### Cross-Language Compatibility

- [ ] Consider: Does your community use JavaScript/C#? If yes, consistency with "async" may be valuable
- [ ] Will learners easily map to English resources?

### Severity Levels

**P0 (Blocker):**

- Doesn't convey asynchronous concept
- Confused with synchronous operations
- Breaks syntax highlighting

**P1 (High):**

- Inconsistent across `async def`, `async for`, `async with`
- Wrong part of speech (verb instead of adjective)
- Too long (>2 words)

**P2 (Medium):**

- Doesn't match established term in target language CS community
- Confusing to JavaScript developers familiar with "async"

**P3 (Low):**

- Could be slightly shorter
- Alternative pronunciation easier

---

## For Native Speakers of Non-English Languages

### Conceptual Understanding (Language-Agnostic)

**The Core Concept:**
`async` marks code that can pause and resume. Instead of waiting for slow operations (network requests, file I/O),
async code can say "I'll come back to this later" and do other work in the meantime.

**Think of it as:**
A chef preparing multiple dishes. Instead of making one dish completely before starting the next, the chef:

1. Starts dish A (put water on to boil) → doesn't wait
2. Starts dish B (put something in oven) → doesn't wait
3. Goes back to dish A (water is boiling now, add pasta)
4. Goes back to dish B (take from oven)

The chef is one person but makes multiple dishes "concurrently" by not waiting.

**What mental model should you have?**

- Async = "This can wait, do other things meanwhile"
- Sync = "Do this now, wait until done before continuing"

### Translation Considerations

**Key Aspects to Preserve:**

1. **Modifier nature:** `async` changes the nature of what follows (def → async def, for → async for)
2. **Concurrency, not speed:** It enables doing multiple things concurrently, not faster execution
3. **Modern concept:** This is post-2015 internet-era programming pattern

**Questions to Ask Yourself:**

1. Does your programming community use JavaScript, C#, or Rust? (They all use "async")
2. Is there an established CS term for "asynchronous programming" in your language?
3. Would keeping "async" untranslated help developers read international documentation?
4. Would translating make it more accessible to beginners?

**Decision Framework:**

**Keep "async" untranslated if:**

- Your community uses JavaScript/C#/Rust extensively
- No established native term exists
- International consistency is valued

**Translate to native term if:**

- Strong established CS term exists (like Chinese 异步)
- Community expects native language keywords
- Beginners struggle with English technical terms

**Action-Oriented vs Result-Oriented:**
`async` is neither action nor result - it's a **property marker**. It marks the property of being asynchronous.

**Cultural Context:**

- **English speakers think of this as:** A modern programming pattern for concurrent I/O
- **Consider translating the concept as:** Whatever adjective means "asynchronous" or "concurrent" in your
  language's CS terminology

---

**Document Version:** 1.0 (Complex Example)
**Created:** 2025-11-10
**Maintained by:** Legesher Team
**Purpose:** Demonstrates handling of modern, complex, modifier keywords

**Translation Recommendations Summary:**

| Language | Keep "async"? | If Translating | Form | Confidence |
|----------|---------------|----------------|------|------------|
| Spanish | Recommended | asíncrono | Adjective | HIGH |
| French | Recommended | asynchrone | Adjective | HIGH |
| German | Recommended | asynchron | Adjective | HIGH |
| Arabic | Recommended | غير متزامن (rare) | Phrase | MEDIUM |
| Chinese | Translate | 异步 (yìbù) | Adjective | HIGH |
| Hindi | Recommended | - | - | MEDIUM |
| Japanese | Translate | 非同期 (hidōki) | Adjective | HIGH |
| Korean | Translate | 비동기 (bidonggi) | Adjective | HIGH |

**Notes:**

- "Recommended" = keep "async" untranslated for international consistency
- Translation shown for languages with established CS terminology
- Given `async` is identical across Python/JavaScript/C#/Rust/Swift, keeping it untranslated maintains
  consistency with the broader programming ecosystem
