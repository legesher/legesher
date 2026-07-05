# Python Builtin: `GeneratorExit` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class (control flow signal)
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`GeneratorExit` is a control-flow signal, not an error: it is raised INSIDE a generator at its paused `yield` point when the generator's `close()` method is called (or the generator is garbage-collected), telling it to finish up and exit. It subclasses `BaseException` - deliberately not `Exception` - and a generator should run its cleanup and stop, never catch it and continue yielding.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# close() raises GeneratorExit inside the generator
def worker():
    try:
        yield 1
        yield 2
    except GeneratorExit:
        print("closing down")
        raise  # let the close complete

g = worker()
print(next(g))  # 1
g.close()       # Prints "closing down"; the generator is now finished
```

**What this does:** `g.close()` resumes the suspended generator by raising `GeneratorExit` at the `yield` where it was paused. The generator observes the signal, prints its message, and re-raises so the close completes. After `close()`, the generator is exhausted.

### Example 2: Common Pattern

```python
# try/finally cleanup - the idiomatic way to honor GeneratorExit
def read_lines(path):
    f = open(path)
    try:
        for line in f:
            yield line.rstrip("\n")
    finally:
        f.close()
        print("file closed")

lines = read_lines("data.txt")
print(next(lines))   # first line
lines.close()        # Prints "file closed" - finally block ran
```

**What this does:** Most generators never name `GeneratorExit` at all. A `try/finally` around the `yield` loop is enough: when `close()` raises `GeneratorExit` at the paused `yield`, the `finally` block runs, releasing the file handle. The same cleanup runs if the generator is simply garbage-collected.

### Example 3: Edge Case

```python
# A generator must NOT swallow GeneratorExit and keep yielding
def stubborn():
    while True:
        try:
            yield "value"
        except GeneratorExit:
            pass  # WRONG: ignores the shutdown signal

g = stubborn()
print(next(g))  # value
g.close()       # Raises RuntimeError: generator ignored GeneratorExit

# Also note: GeneratorExit slips past except Exception
print(issubclass(GeneratorExit, Exception))      # False
print(issubclass(GeneratorExit, BaseException))  # True
```

**What this shows:** Catching `GeneratorExit` and yielding again violates the protocol: Python detects that the generator ignored the shutdown request and raises `RuntimeError` in the caller. Because `GeneratorExit` subclasses `BaseException` rather than `Exception`, a broad `except Exception:` inside a generator does not accidentally trap the signal - that is exactly why it lives on the `BaseException` side.

---

## Pattern Classification

**This term is:** CONTROL FLOW SIGNAL (Exception Class)

**Similar terms in this pattern:**

1. `StopIteration` - The other generator/iterator control signal (natural exhaustion)
2. `StopAsyncIteration` - The async twin of `StopIteration`
3. `KeyboardInterrupt` - Another `BaseException`-side signal that is not a program error
4. `SystemExit` - The "exit" sibling: also a non-error shutdown signal on the `BaseException` side

**Pattern rule:** Control-flow exceptions are noun compounds naming an event, and their translations must NOT contain the pack's "error/failure" word. `GeneratorExit` = the "generator" concept (from the `yield` vocabulary family) + a neutral noun for "exit/departure."


---

## Etymology (Brief)

**English Origin:** Latin compounds via French/English

**Root meaning:** "Generator" from Latin "generare" meaning "to beget, produce" - a generator is a producer of values. "Exit" from Latin "exire" meaning "to go out" (ex- "out" + ire "to go"); as an English noun, the way out or the act of leaving.

**Why Python uses this:** PEP 342 (Python 2.5) gave generators a `close()` method and needed a way to tell a suspended generator "you are being shut down - run your cleanup." The name states exactly that event: the generator's exit. It is deliberately not named with "Error" because nothing has gone wrong; it is the normal, orderly way a generator is asked to leave.

---

## Concept Explanation (Intermediate Level)

**What it does:**

A generator can be suspended mid-execution at a `yield` for an arbitrarily long time, possibly holding resources - open files, network connections, locks. `GeneratorExit` is the mechanism that lets Python end such a generator cleanly before it is naturally exhausted. When code calls `generator.close()`, or when an unfinished generator is garbage-collected, Python resumes the generator one last time by raising `GeneratorExit` at the paused `yield` expression. From the generator's point of view, the `yield` it was sleeping on suddenly raises.

The intended responses are narrow: let the exception propagate (running any `try/finally` blocks on the way out), or catch it, do cleanup, and then `return` or re-raise. What a generator must not do is catch `GeneratorExit` and yield another value - Python treats that as ignoring the shutdown request and raises `RuntimeError("generator ignored GeneratorExit")` in the caller. In practice, well-written generators rarely mention `GeneratorExit` by name; a `try/finally` expresses "clean up no matter how I end" and handles closure, exhaustion, and errors alike.

Its position in the hierarchy is the giveaway that this is a signal and not a failure: `GeneratorExit` inherits directly from `BaseException`, alongside `SystemExit` and `KeyboardInterrupt`, specifically so that `except Exception:` inside a generator body cannot accidentally swallow it. It is the shutdown-side complement to `StopIteration`: `StopIteration` flows OUT of a generator to say "I have no more values"; `GeneratorExit` flows INTO a generator to say "stop producing values now."

**Key behaviors:**

1. **Injected at the paused `yield` by `close()`:** `generator.close()` raises `GeneratorExit` inside the generator at its suspension point. If the generator then exits (returns or lets the signal propagate), `close()` returns quietly. Garbage collection of an unfinished generator triggers the same mechanism.

2. **Must not be survived:** Catching `GeneratorExit` and yielding again causes `RuntimeError` in the caller. The only legitimate follow-ups to catching it are cleanup then `return`, or cleanup then `raise`.

3. **Lives on the `BaseException` side:** `issubclass(GeneratorExit, Exception)` is `False`. Broad `except Exception:` handlers inside generator bodies therefore let the shutdown signal through - by design. Async generators use the same signal via `aclose()`.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (agent noun "generator" + event noun "exit")
- **Action vs State:** EVENT/SIGNAL - names an orderly shutdown event, not an error state and not a command
- **Temporal aspect:** Point-in-time - marks the moment the generator is told to finish

### Recommended Form

**Primary recommendation:** Compound noun: the language's term for "generator" (which must belong to the same word family as the `yield` translation - a generator is "the thing that yields") plus a neutral noun for "exit/leaving." The result should read like an event name, the way "SystemExit" does.

**Forms to AVOID:**

- ❌ ANY word meaning "error," "failure," or "fault" - this is an orderly shutdown signal, nothing failed
- ❌ Words meaning "death," "kill," or "abort" - too violent; the semantics are a polite request to finish
- ❌ Imperative verb forms ("ExitTheGenerator!") - the class names the event, not a command to the reader

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Generator" as an electrical machine producing power
- ❌ Meaning 2: "Exit" as a physical doorway ("emergency exit")
- ❌ Meaning 3: An ERROR that occurred while exiting a generator
- ✅ Meaning 4: **The SIGNAL delivered inside a generator function telling it to finish and exit**

**Example:**

English "exit" can mean:

1. "The exit is on the left" (a physical door) ❌
2. "His exit from politics" (departure from a role) ✅ Related concept
3. `g.close()` raising inside the generator (the shutdown signal) ✅ **This is the Python meaning**

**Your translation should capture meaning #4: an orderly departure event. It is emphatically NOT an error - align it with `SystemExit`-style shutdown vocabulary, never with the `...Error` family. A generator receiving it should clean up and stop, not treat it as a failure to recover from.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `GeneratorExit`, check these translations:**

- [ ] `yield` - The keyword that defines generators; the "generator" component must belong to this word family
- [ ] `StopIteration` - The other generator control signal; both must read as signals, not errors
- [ ] `StopAsyncIteration` - Same signal family, async side
- [ ] `BaseException` - The actual parent class; do NOT borrow vocabulary from `Exception`-side error names
- [ ] `SystemExit` - Shares the "exit" concept; the two should use the same "exit" noun
- [ ] `return` - What a generator does after receiving the signal; cleanup-then-return phrasing should read naturally

**Consistency rule:**

Keep the control-flow signals (`StopIteration`, `StopAsyncIteration`, `GeneratorExit`) free of the pack's "error" word, and keep the "generator" noun consistent everywhere generator concepts appear. If your language renders `yield` with a production verb, "generator" should be the agent noun of that same semantic family.


### Functional relationships

**This term works WITH:**

1. **`close()` + `GeneratorExit`**: The method that injects the signal

```python
g = worker()
next(g)
g.close()  # raises GeneratorExit inside worker()
```

2. **`try/finally` + `yield`**: The idiomatic cleanup that honors the signal

```python
def gen():
    try:
        yield item
    finally:
        release_resources()
```

**Common pairing:**

```python
# The full lifecycle of a generator shutdown
def pump(connection):
    try:
        while True:
            yield connection.read_packet()
    except GeneratorExit:
        # Optional: observe the shutdown explicitly
        connection.send_goodbye()
        raise  # ...but always let the exit complete
    finally:
        connection.close()

stream = pump(conn)
packet = next(stream)
stream.close()  # goodbye sent, connection closed, generator finished

# What NOT to do:
# except GeneratorExit:
#     yield "one more"   # RuntimeError: generator ignored GeneratorExit
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `GeneratorExit`

- Both components ("generator," "exit") have established translations in most CS vocabularies
- The trap is categorical, not lexical: translators who assume every exception is an error will add error vocabulary
- The "generator" component is constrained by the `yield` word family already chosen for the pack
- "Exit" must be the neutral, orderly-departure noun, coordinated with `SystemExit`

**For this term:** MEDIUM

**Rationale:** Lexically this is a routine compound; conceptually it demands understanding that Python has non-error exceptions. The two failure modes - adding an "error" word, or picking a "generator" word disconnected from the `yield` family - are both consistency failures rather than vocabulary gaps. With the signal-not-error rule stated, a careful translator should land this reliably; without it, error-vocabulary contamination is likely.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Reads as an ORDERLY SHUTDOWN EVENT, not a failure?
- [ ] Contains NO word meaning error/failure/fault?
- [ ] Would a developer understand this arrives via `close()`?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun naming an event)?
- [ ] Follows target language grammar rules for compounds?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] "Generator" component matches the `yield`-family generator vocabulary?
- [ ] "Exit" noun coordinated with `SystemExit` (same word)?
- [ ] Signal family (`StopIteration`, `StopAsyncIteration`, this term) uniformly error-free?

### 4. Usability

- [ ] Short enough (1-3 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember?

### 5. Cultural Appropriateness

- [ ] No violent or morbid connotations (kill/death vocabulary avoided)?
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
term: GeneratorExit
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
