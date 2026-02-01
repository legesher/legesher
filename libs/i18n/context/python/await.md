# Python Keyword: `await` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** verb
**Python Version:** 3.5+
**Difficulty:** HARD

---

## Quick Summary

The `await` keyword in Python pauses an async function until an awaitable object (coroutine, task, or future) completes, allowing other async operations to run concurrently. It can only be used inside `async def` functions and enables non-blocking asynchronous programming.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
import asyncio

# Async function that pauses
async def fetch_data():
    print("Fetching...")
    await asyncio.sleep(1)  # Pause for 1 second (non-blocking)
    print("Data fetched!")
    return {"data": "example"}

# Run the async function
asyncio.run(fetch_data())
```

**What this does:** The `await asyncio.sleep(1)` pauses the `fetch_data()` coroutine for 1 second, but doesn't block the entire program. While waiting, the event loop can run other async tasks. `await` releases control to the event loop until the awaited operation completes.

### Example 2: Common Pattern

```python
import asyncio

async def fetch_user(user_id):
    await asyncio.sleep(0.5)  # Simulate API call
    return f"User {user_id}"

async def fetch_posts(user_id):
    await asyncio.sleep(0.5)  # Simulate API call
    return f"Posts for {user_id}"

async def get_user_data(user_id):
    # Sequential awaits
    user = await fetch_user(user_id)
    posts = await fetch_posts(user_id)
    return user, posts

# Concurrent awaits (faster)
async def get_user_data_concurrent(user_id):
    user_task = fetch_user(user_id)
    posts_task = fetch_posts(user_id)
    user, posts = await asyncio.gather(user_task, posts_task)
    return user, posts

asyncio.run(get_user_data_concurrent(123))
```

**What this does:** `await` can be used sequentially (one after another, total 1 second) or concurrently with `asyncio.gather()` (runs together, total 0.5 seconds). Each `await` pauses the current coroutine but allows the event loop to switch to other tasks, enabling concurrency.

### Example 3: Edge Case

```python
import asyncio

# await can only be used in async functions
async def valid_await():
    result = await some_coroutine()  # Valid ✅
    return result

# This causes SyntaxError
def invalid_await():
    result = await some_coroutine()  # SyntaxError ❌
    return result

# Multiple awaits in loops
async def fetch_all(ids):
    results = []
    for id in ids:
        result = await fetch_data(id)  # Sequential
        results.append(result)
    return results

# await with exception handling
async def safe_fetch():
    try:
        data = await fetch_data()
        return data
    except Exception as e:
        print(f"Error: {e}")
        return None
```

**What this shows:** `await` can only appear inside `async def` functions. Using it in regular functions is a syntax error. You can use `await` in loops, conditionals, try-except blocks—anywhere inside an async function. Each `await` is a potential pause point where control can switch to other tasks.

---

## Pattern Classification

**This term is:** ACTION KEYWORD (Async Control Flow)

**Similar terms in this pattern:**

1. `async` - Declares async function (await works inside async functions)
2. `yield` - Pauses sync generators (await pauses async coroutines)
3. `return` - Exits function with value (await waits for value)

**Pattern rule:** Async control flow keywords should use verb forms. `await` performs an action: pause the coroutine until the awaited operation completes. It's a verb commanding the runtime to wait asynchronously.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `async` | asíncrono | غير متزامن | 异步 | अतुल्यकालिक |
| `yield` | ceder | ينتج | 产出 | उपज देना |
| `await` | **esperar** | **انتظار** | **等待** | **प्रतीक्षा** |

---

## Etymology (Brief)

**English Origin:** Old Norse via Middle English

**Root meaning:** Old Norse "bíða" (to wait) influenced Middle English "awaiten" (a- prefix "at/toward" + wait). "Await" means "to wait for something," emphasizing expectation of a specific event. More formal/active than simple "wait."

**Why Python uses this:** "Await" captures asynchronous waiting perfectly: the coroutine actively waits for a result without blocking the thread. "Await" suggests purposeful waiting for a specific completion, not passive idleness. JavaScript uses `await` (introduced 2017), making it familiar to web developers. The term emphasizes that execution pauses at this point until the awaited operation finishes, but the program continues running other tasks concurrently.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `await` keyword pauses the execution of an `async` function (coroutine) at a specific point until an awaitable object completes. Awaitable objects include coroutines (other `async def` functions), Tasks, and Futures. While paused at an `await`, the Python event loop can switch to running other coroutines, enabling concurrency.

Crucially, `await` doesn't block the thread. Traditional blocking operations (like `time.sleep()`) freeze the entire program. `await asyncio.sleep()` pauses only the current coroutine, allowing other coroutines to run. This cooperative multitasking enables thousands of concurrent operations on a single thread.

`Await` can only be used inside `async def` functions. Using `await` in regular (non-async) functions causes a SyntaxError. This restriction ensures that the event loop controls coroutine scheduling. When you `await` an expression, Python suspends the coroutine, returns control to the event loop, and resumes the coroutine when the awaited result is ready.

**Key behaviors:**

1. **Non-blocking pause:** `await` pauses the current coroutine but not the thread or event loop. Other coroutines can run while this one waits. This enables concurrency: thousands of concurrent I/O operations (network requests, file reads, database queries) on a single thread.

2. **Requires async context:** `await` can only appear inside `async def` functions. This syntactic restriction ensures proper event loop integration. You can't accidentally `await` in synchronous code, which would break the execution model.

3. **Returns awaited value:** When the awaited operation completes, `await` returns its result. `result = await fetch_data()` pauses until `fetch_data()` completes, then assigns its return value to `result`. This makes async code look synchronous while remaining non-blocking.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Transitive verb (takes object - what to await)
- **Action vs State:** ACTION - actively waiting (not passive)
- **Temporal aspect:** Durative - waiting spans time until completion

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Infinitive verb | "esperar", "attendre" - to wait/await |
| Germanic (de, nl, sv) | Infinitive verb | "warten", "wachten" - to wait/await |
| Slavic (ru, pl, uk) | Infinitive verb | "ждать", "czekać" - to wait/await |
| Arabic | Masdar (verbal noun) | "انتظار" (intiẓār) - waiting/awaiting |
| Chinese | Verb | "等待" (děngdài) - to wait/await |
| Hindi | Infinitive verb | "प्रतीक्षा करना" (pratīkṣā karnā) - to wait/await |

**Primary recommendation:** Use infinitive verb meaning "to await" or "to wait." Emphasize active waiting for a specific result, not passive idleness. The term should convey purposeful waiting for an asynchronous operation to complete.

**Forms to AVOID:**

- ❌ Using "pause" - describes mechanism but not purpose (waiting for result)
- ❌ Using "sleep" - implies inactivity, not active waiting
- ❌ Using "block" - opposite of await's non-blocking nature

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `esperar`
- **Form:** Infinitive verb
- **Why it works:** "Esperar" means "to wait, to expect, to await." Standard verb for waiting. Used in Spanish async programming contexts. Natural and clear. Conveys active waiting for result.

**Arabic:**

- **Translation:** `انتظار` (intiẓār)
- **Form:** Masdar (verbal noun)
- **Why it works:** Root ن-ظ-ر (n-ẓ-r) means wait/expect. `انتظار` is verbal noun "waiting/awaiting." Standard Arabic for waiting. Fits async context well. Professional and clear.

**Chinese:**

- **Translation:** `等待` (děngdài)
- **Form:** Verb compound
- **Why it works:** 等 (wait) + 待 (await) = "to wait, to await." Standard Chinese for waiting. Used in Chinese async programming. Clear temporal semantics. Natural compound.

**Hindi:**

- **Translation:** `प्रतीक्षा करना` (pratīkṣā karnā)
- **Form:** Infinitive verb phrase
- **Why it works:** प्रतीक्षा (expectation/waiting) + करना (to do) = "to wait/await." Formal and professional. Used in Hindi technical writing. Sanskrit-derived, appropriate for technical context.

### ❌ Common Translation Mistakes

**Mistake 1: Using "pause" or "stop"**

- **Wrong:** `pausar` (Spanish - "to pause")
- **Why wrong:** While `await` does pause execution, "pause" doesn't convey waiting for a result. "Await" is specifically about waiting for something to complete. "Esperar" captures both pause and expectation.
- **Right:** `esperar` (wait/await with expectation)

**Mistake 2: Using "sleep" or "rest"**

- **Wrong:** `dormir` (Spanish - "to sleep")
- **Why wrong:** "Sleep" suggests inactivity or idleness. `await` is active waiting for a specific event. `asyncio.sleep()` is a function you can await, but `await` itself means "wait for," not "sleep."
- **Right:** `esperar` (active waiting)

**Mistake 3: Using "block"**

- **Wrong:** `bloquear` (Spanish - "to block")
- **Why wrong:** "Block" is the opposite of what `await` does. Blocking operations freeze the thread. `await` is non-blocking—it pauses the coroutine but allows the event loop to run other tasks. Critical distinction.
- **Right:** `esperar` (non-blocking wait)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (but similar meanings)

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Be in store for" ("A surprise awaits you") - Passive, future-focused
- ✅ Meaning 2: **"WAIT FOR (something to happen)"** - Active, expectant waiting

**Example:**

English "await" can mean:

1. "Danger awaits in the forest" (be in store for - passive future) ❌
2. "I await your response" (actively wait for specific event) ✅ **Similar to Python meaning**
3. "`await fetch()` pauses until fetch completes" (async wait for result) ✅ **This is the Python meaning**

**Your translation should capture meaning #2-3: actively waiting for a specific asynchronous operation to complete, pausing the coroutine non-blockingly until the awaited result is ready.**

Key semantic components:

- **Active waiting:** Not passive, but purposeful expectation
- **Specific target:** Waiting for a particular operation to complete
- **Non-blocking:** Doesn't freeze the thread, allows concurrency
- **Resumption:** After waiting completes, execution resumes

**Comparison with "wait":**

"Await" is more formal and active than "wait." In English:

- "Wait" = general waiting (can be aimless)
- "Await" = waiting for a specific expected event

Python chose "await" over "wait" to emphasize purposeful waiting for async results.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `await`, check these translations:**

- [ ] `async` - Declares async functions; `await` works inside async functions; paired keywords
- [ ] `yield` - Pauses sync generators; `await` pauses async coroutines; similar pause/resume
- [ ] `return` - Returns value and exits; `await` waits for value; both handle function results

**Consistency rule:**

Async keywords (`async`, `await`) should work together linguistically. If `async` is an adjective, `await` is the verb that acts within async contexts. `await` and `yield` both do pause/resume, so similar verb forms help. All action keywords should be verbs.

**Example:**

Spanish:

- `asíncrono` (async - adjective: asynchronous)
- `esperar` (await - verb: to await)
- `ceder` (yield - verb: to yield)

Adjective + verbs. ✅ Works together

**Pairing:** "async defines context, await acts within it."

### Functional relationships

**This term works WITH:**

1. **`async def`:** Async functions where await can be used

```python
async def example():
    result = await some_coroutine()
```

2. **Coroutines and Tasks:** Objects that can be awaited

```python
await my_coroutine()
await asyncio.create_task(my_coroutine())
```

**Common pairing:**

```python
# Basic await
async def fetch():
    data = await get_data()
    return data

# Multiple sequential awaits
async def process():
    data = await fetch()
    result = await transform(data)
    await save(result)

# Concurrent awaits with gather
async def fetch_all():
    results = await asyncio.gather(
        fetch_user(),
        fetch_posts(),
        fetch_comments()
    )
    return results

# await in loop
async def fetch_many(urls):
    results = []
    for url in urls:
        data = await fetch(url)  # Sequential
        results.append(data)
    return results

# await with exception handling
async def safe_fetch():
    try:
        return await fetch()
    except TimeoutError:
        return None

# await with timeout
async def fetch_with_timeout():
    try:
        return await asyncio.wait_for(fetch(), timeout=5.0)
    except asyncio.TimeoutError:
        print("Timeout!")
        return None

# Nested awaits
async def outer():
    result = await inner()
    return result

async def inner():
    data = await fetch()
    return process(data)

# await in comprehension
async def fetch_all_ids(ids):
    # Note: Need to gather for true concurrency
    results = [await fetch(id) for id in ids]  # Sequential
    return results

# await with asyncio.sleep (non-blocking)
async def delayed_action():
    print("Starting")
    await asyncio.sleep(1)  # Pause 1 second (non-blocking)
    print("Done")
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

### HARD

- No direct equivalent in some languages
- May need compound term or explanation
- Concept doesn't exist universally
- **AI confidence should be MEDIUM, human review recommended**

### Why HARD for `await`

- Relatively new concept (Python 3.5+, 2015)
- Async programming is advanced topic
- Not all languages have async/await (though increasingly common)
- Concept of non-blocking cooperative multitasking is sophisticated
- Must distinguish from blocking "wait" or "sleep"
- Some languages may not have established async terminology yet

**For this term:** HARD

**Rationale:** Async/await is modern, advanced Python feature. While "wait" is universal, async non-blocking wait is specific to concurrent programming. Translators must understand the difference between blocking wait (bad) and non-blocking await (good). CS education in some languages may not yet have established async/await translations. The term must be clearly distinguished from synchronous waiting. Human review recommended to ensure chosen term captures non-blocking async semantics.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures ACTIVE WAITING concept (not passive)?
- [ ] Conveys NON-BLOCKING nature (allows concurrency)?
- [ ] Distinguishes from blocking "sleep" or "pause"?
- [ ] Implies waiting for specific async operation to complete?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb, not noun)?
- [ ] Correct form (infinitive)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python keywords)?

### 3. Consistency

- [ ] Matches pattern with `async` (adjective + verb pair)?
- [ ] Similar form to `yield` (both pause/resume verbs)?
- [ ] Uses verb form like other action keywords?
- [ ] Aligns with async terminology in target language CS education?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Conveys waiting/expectation concept?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional?
- [ ] Formal enough for technical context?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: await
language: es
translation: esperar
form: infinitive_verb
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "esperar" means "to wait, to expect, to await," perfectly capturing the async waiting concept. It's the standard verb for waiting in Spanish and is used in async programming contexts. Natural, professional, and clearly conveys active waiting for a result.

**Alternatives considered:**

1. `aguardar` (to await) - More formal synonym of esperar, but less common in everyday use
2. `pausar` (to pause) - Describes mechanism but misses waiting-for-result aspect
3. `dormir` (to sleep) - Wrong concept (implies inactivity, not awaiting result)
4. `esperar` (to wait/await) - Best captures active waiting for async result ✅

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH for Spanish. "Esperar" is the natural verb for waiting/awaiting. For languages new to async programming, verify that CS education has established async/await terminology. Some languages may still be developing standard translations as async programming becomes more common. Native speaker review valuable for emerging async terminology.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
