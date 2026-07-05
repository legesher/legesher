# Python Builtin: `BlockingIOError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.3+
**Difficulty:** HARD

---

## Quick Summary

`BlockingIOError` is a built-in exception raised when an operation on an object set to non-blocking mode would have to block — for example, reading from a non-blocking socket that has no data yet. It is a subclass of `OSError`, introduced by PEP 3151 in Python 3.3, corresponds to the OS error codes `EAGAIN`, `EALREADY`, `EWOULDBLOCK`, and `EINPROGRESS`, and (when raised from the buffered I/O classes in the `io` module) carries a `characters_written` attribute.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Reading a non-blocking socket with no data available "would block"
import socket

a, b = socket.socketpair()
a.setblocking(False)

try:
    a.recv(1024)  # nothing has been sent yet
except BlockingIOError as exc:
    print(f"Would block: {exc}")  # errno EAGAIN/EWOULDBLOCK
finally:
    a.close()
    b.close()
```

**What this does:** In blocking mode, `recv()` would simply wait for data. In non-blocking mode, waiting is forbidden — so instead of pausing, the call raises `BlockingIOError` to say "this operation *would* block; there is nothing for you right now." The exception is a scheduling signal, not a failure of the socket.

### Example 2: Common Pattern

```python
# Non-blocking read guarded by select(): only read when data is ready
import select
import socket

a, b = socket.socketpair()
a.setblocking(False)

b.sendall(b"payload")
ready, _, _ = select.select([a], [], [], 1.0)
if ready:
    print(a.recv(1024))  # safe: select() said data is waiting

try:
    a.recv(1024)  # queue is empty again
except BlockingIOError:
    print("No data yet; do other work instead of waiting")

a.close()
b.close()
```

**What this does:** This is the heart of event-driven I/O: use a readiness API (`select`, `poll`, or an event loop) to learn when a non-blocking file descriptor has data, and treat `BlockingIOError` as the routine "not ready" answer when you probe anyway. Event loops like `asyncio` catch this exception internally thousands of times per second.

### Example 3: Edge Case

```python
# characters_written: how much of a buffered write succeeded before blocking
import io
import os

r, w = os.pipe()
os.set_blocking(w, False)
writer = io.BufferedWriter(io.FileIO(w, "wb"))

try:
    writer.write(b"x" * (1 << 20))  # 1 MiB into a pipe that holds far less
except BlockingIOError as exc:
    print(f"Accepted {exc.characters_written} bytes before blocking")
finally:
    os.close(r)
    try:
        writer.close()  # flushing the leftover buffer would block/fail; discard it
    except (BlockingIOError, BrokenPipeError):
        pass
```

**What this shows:** When the buffered I/O classes in the `io` module hit a non-blocking raw stream that cannot take more data, they raise `BlockingIOError` with `characters_written` — an integer reporting how many characters/bytes were consumed before blocking. This partial-progress report is unique in the `OSError` family and lets callers resume the write later without losing or duplicating data. The attribute is documented as available when the exception comes from buffered I/O; it is not set on instances raised by plain socket operations.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `OSError` - Direct parent class; the root of all operating-system error exceptions
2. `InterruptedError` - Sibling PEP 3151 class: a system call interrupted by a signal (`EINTR`)
3. `TimeoutError` - Sibling: the time-limited cousin of "would block" (`ETIMEDOUT`)
4. `ConnectionError` - Sibling family: connection failures on the same sockets that raise this class

**Pattern rule:** Exception classes are noun compounds ending in "Error." This name is participle "blocking" + domain "IO" (input/output) + "error" — translations need a modifier meaning "would-block/blocking" attached to the language's standard input-output term, plus the corpus "error" word.


---

## Etymology (Brief)

**English Origin:** Compound word (Germanic + initialism + Latin-derived)

**Root meaning:** "Block" comes from Old French "bloc" (log, lump), giving the sense of an obstacle that halts movement; in computing, a "blocking" call halts the thread until it can proceed. "IO" abbreviates "input/output," the movement of data in and out of a program. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** PEP 3151 merged the pre-3.3 `io.BlockingIOError` and the socket-level `EAGAIN`/`EWOULDBLOCK` errors into one builtin. The name reads as "an I/O operation that would need to block (but was not allowed to)" — domain plus "Error," in Python's standard exception style.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`BlockingIOError` is raised when an operation on a non-blocking object cannot complete immediately. Normally, I/O calls *block*: `recv()` waits for data, `write()` waits for buffer space. When a socket or file descriptor is switched to non-blocking mode (`setblocking(False)`, `os.set_blocking(fd, False)`), waiting is no longer permitted — so the operating system answers "try again later" (`EAGAIN`/`EWOULDBLOCK`), and Python raises this exception instead of pausing the thread.

Crucially, the name describes what *would have happened*, not what went wrong. Nothing is broken: the data simply has not arrived, or the outgoing buffer is full, or a non-blocking `connect()` is still in progress (`EINPROGRESS`/`EALREADY`). Event loops treat this exception as ordinary control flow — the cue to go serve other work and come back when a readiness API says the descriptor is ready. Application code using `asyncio` rarely sees it, because the loop catches it internally.

The exception has one member no `OSError` sibling has: `characters_written`. When buffered I/O classes from the `io` module raise it, this integer records how many characters or bytes were consumed before blocking, so the caller can resume exactly where the write stopped. Translations do not need to encode this attribute, but the brief's readers should understand it to explain the class's role in partial-write recovery.

**Key behaviors:**

1. **Maps to four errno values:** `EAGAIN`, `EALREADY`, `EWOULDBLOCK`, and `EINPROGRESS` all become `BlockingIOError`. On most platforms `EAGAIN` and `EWOULDBLOCK` are the same number; the class unifies them regardless.

2. **Signals "not ready," not "failed":** The socket or file remains perfectly usable. Retrying after a readiness notification (or a short wait) is the intended response — this is the only `OSError` subclass whose normal handling is "expected, continue."

3. **Carries `characters_written` from buffered I/O:** When raised by `io.BufferedWriter` and friends over a non-blocking raw stream, the attribute reports partial progress so callers can resume the write without data loss.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (blocking modifier + I/O domain + error type)
- **Action vs State:** STATE - names a condition ("would block"), not an action
- **Temporal aspect:** Instantaneous but transient - the condition typically clears once data arrives or buffers drain

### Recommended Form

**Primary recommendation:** Compound noun combining the language's standard technical term for input/output (often an abbreviation or a native compound) with a "blocking / would-block" modifier, plus the corpus "error" word. Reuse whatever the corpus already uses for "input" and "output" in the `input`/`print` briefs where applicable.

**Forms to AVOID:**

- ❌ Words meaning "blocked/forbidden by policy" (like a blocked account) - this is a scheduling condition, not a prohibition
- ❌ Dropping the I/O component ("BlockingError") - loses the domain and reads like a generic freeze
- ❌ Verb forms ("BloquearES") - reads as a command to block, not a would-block condition

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Physically obstructing a path ("blocking the doorway")
- ❌ Meaning 2: Banning or restricting access ("blocking a user")
- ❌ Meaning 3: Sports defense ("blocking a shot")
- ✅ Meaning 4: **A CALL THAT WOULD SUSPEND THE THREAD** (the operation on a non-blocking object could not complete without waiting; OS codes `EAGAIN`/`EWOULDBLOCK`/`EALREADY`/`EINPROGRESS`)

**Example:**

English "blocking" can mean:

1. "A truck is blocking the street" (physical obstruction) ❌
2. "She blocked him on social media" (access ban) ❌
3. "Great blocking by the defense" (sports) ❌
4. "recv() is a blocking call unless the socket is non-blocking" (thread suspension) ✅ **This is the Python meaning**

**Your translation should capture meaning #4: an I/O operation that would have to wait, on an object configured never to wait — NOT physical, social, or sports blocking.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `BlockingIOError`, check these translations:**

- [ ] `ConnectionError` (connectionerror.md) and its siblings (connectionabortederror.md, connectionrefusederror.md, connectionreseterror.md, brokenpipeerror.md) - Same `OSError` family; the "error" suffix must be identical across all of them
- [ ] `TimeoutError` (timeouterror.md) - The time-bounded cousin; both describe waiting, and their vocabularies must stay distinct
- [ ] `InterruptedError` (interruptederror.md) - Sibling PEP 3151 class; parallel compound structure
- [ ] `input` - The corpus term for input; reuse its word inside the I/O compound if the corpus has one
- [ ] `print` / output vocabulary - Likewise for the output half of the compound

**Consistency rule:**

The "error" word must match the entire exception corpus (anchored by connectionerror.md and its siblings). The I/O compound should reuse the corpus's existing input/output vocabulary rather than inventing a new pair, and the "blocking" modifier must not collide with words already used for `PermissionError`-style denial.


### Functional relationships

**This term works WITH:**

1. **`socket.setblocking(False)` + `BlockingIOError`**: The mode switch that makes the exception possible:

```python
sock.setblocking(False)
try:
    data = sock.recv(1024)
except BlockingIOError:
    data = None  # nothing available right now
```

2. **`select.select()` + `BlockingIOError`**: Readiness polling that makes the exception rare:

```python
ready, _, _ = select.select([sock], [], [], timeout)
if ready:
    data = sock.recv(1024)  # will not raise BlockingIOError now
```

**Common pairing:**

```python
# Minimal event-loop step: drain a non-blocking socket without ever waiting
import socket

def drain(sock: socket.socket) -> bytes:
    """Read whatever is available right now; never block."""
    chunks = []
    while True:
        try:
            chunk = sock.recv(4096)
        except BlockingIOError:
            break  # buffer empty -- normal, not an error
        if not chunk:
            break  # peer closed
        chunks.append(chunk)
    return b"".join(chunks)

a, b = socket.socketpair()
a.setblocking(False)
b.sendall(b"hello")
print(drain(a))  # b'hello'
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

### HARD

- No direct equivalent in some languages
- May need compound term or explanation
- Concept doesn't exist universally
- **AI confidence should be MEDIUM, human review recommended**

### Why HARD for `BlockingIOError`

- Three-part compound (blocking + I/O + error) fights the 1-3 word usability limit in most languages
- "Blocking" is a systems-programming term of art; everyday "block" words suggest prohibition or obstruction
- The I/O component may be an abbreviation (E/S, E/A), a native compound, or a loanword depending on language
- Semantically inverted for an exception: it reports a *retryable condition*, not a failure

**For this term:** HARD

**Rationale:** Every component demands a choice — which I/O rendering the corpus uses, which "blocking" word carries the would-block sense, and how to keep the result short enough to type. The concept itself (non-blocking mode) is unfamiliar outside systems programming, so mistranslations that read as "forbidden" or "failed" are likely without review.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures WOULD-BLOCK CONDITION on non-blocking I/O (not prohibition, obstruction, or failure)?
- [ ] Keeps the INPUT/OUTPUT domain visible?
- [ ] Would a developer understand this is routine and retryable?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun with adjective/participle modifier)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Ends with the same "error" word as the rest of the exception corpus?
- [ ] I/O vocabulary matches the corpus terms for input and output?
- [ ] "Blocking" word distinct from `PermissionError`-style denial vocabulary?

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
- [ ] No special characters that break syntax highlighting (avoid "/" inside identifiers)?

---

## Translation Output Format

**Your translation:**

```yaml
term: BlockingIOError
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
