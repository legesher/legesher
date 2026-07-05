# Python Builtin: `TimeoutError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.3+
**Difficulty:** MEDIUM

---

## Quick Summary

`TimeoutError` is a built-in exception raised when a system function or operation times out — the allotted waiting time expires before the operation completes. It is a subclass of `OSError`, introduced by PEP 3151 in Python 3.3, and corresponds to the OS error code `ETIMEDOUT`. It has since unified Python's timeout exceptions: `socket.timeout` became an alias of it in Python 3.10, and `asyncio.TimeoutError` followed in Python 3.11, so from 3.11 onward those names all refer to this one class.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# A socket read that waits longer than its timeout raises TimeoutError
import socket

a, b = socket.socketpair()
a.settimeout(0.5)

try:
    a.recv(1024)  # nothing is ever sent; the 0.5 s allowance expires
except TimeoutError as exc:
    print(f"Timed out: {exc}")  # 'timed out'
finally:
    a.close()
    b.close()
```

**What this does:** `settimeout(0.5)` gives every operation on the socket half a second to finish. No data arrives, the allowance runs out, and the read fails with `TimeoutError`. (On Python 3.10+ the socket module raises this builtin directly; on 3.9 and earlier it raised the separate `socket.timeout` class, so this `except` clause requires 3.10+.)

### Example 2: Common Pattern

```python
# asyncio: bounding how long you are willing to await something (Python 3.11+)
import asyncio

async def main():
    try:
        await asyncio.wait_for(asyncio.sleep(10), timeout=0.5)
    except TimeoutError:
        print("Coroutine took too long; moving on")

asyncio.run(main())
```

**What this does:** `asyncio.wait_for` cancels the awaited coroutine when the deadline passes and raises a timeout. Since Python 3.11, `asyncio.TimeoutError` is an alias of the builtin `TimeoutError`, so one `except TimeoutError:` clause now covers socket timeouts, asyncio deadlines, and OS-level `ETIMEDOUT` alike.

### Example 3: Edge Case

```python
# The aliases, and the errno mapping, in one place
import asyncio
import errno
import os
import socket

print(socket.timeout is TimeoutError)        # True on Python 3.10+
print(asyncio.TimeoutError is TimeoutError)  # True on Python 3.11+

# OS-level ETIMEDOUT maps to TimeoutError automatically
try:
    raise OSError(errno.ETIMEDOUT, os.strerror(errno.ETIMEDOUT))
except TimeoutError as exc:
    print(type(exc).__name__)  # TimeoutError
    print(exc.errno == errno.ETIMEDOUT)  # True

# Note: socket-layer timeouts carry no errno (the OS never assigned one)
try:
    a, b = socket.socketpair()
    a.settimeout(0.01)
    a.recv(1)
except TimeoutError as exc:
    print(exc.errno)  # None -- raised by Python's socket layer, not the kernel
```

**What this shows:** One class, several sources. The kernel produces it via `ETIMEDOUT` (e.g., an unanswered TCP connect); Python's own timeout machinery (socket allowances, asyncio deadlines) raises the same class directly, without an errno. The 3.10/3.11 alias unification means translators handle exactly one term where older Python had three.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `OSError` - Direct parent class; the root of all operating-system error exceptions
2. `ConnectionRefusedError` - The contrasting connect-failure: an active "no" versus this class's silence (`ECONNREFUSED` vs `ETIMEDOUT`)
3. `BlockingIOError` - Sibling: "cannot proceed right now" without a deadline; this class is "the deadline passed"
4. `InterruptedError` - Sibling PEP 3151 class: a call ended early by a signal rather than by an expired allowance

**Pattern rule:** Exception classes are noun compounds ending in "Error." This name is "timeout" (expiry of an allotted waiting period) + "error" — translations attach the language's established networking "timeout" term to the corpus "error" word.


---

## Etymology (Brief)

**English Origin:** Compound word (Germanic + Latin-derived)

**Root meaning:** "Timeout" fuses "time" (Old English "tīma") with "out" — time that has run out. The word entered technology from sports (a pause when play stops) but computing inverted the emphasis: not a pause you *take*, but an allowance that *expires*. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** "Timed out" is the universal networking phrase for an operation that waited its full allowance and gave up; the POSIX errno is `ETIMEDOUT` ("Connection timed out"). PEP 3151 gave the concept a builtin class, and Python 3.10/3.11 folded the older `socket.timeout` and `asyncio.TimeoutError` names into it.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`TimeoutError` is raised when an operation is given a bounded amount of time to complete and that bound expires first. Timeouts are how programs avoid waiting forever on things that may never happen: a server that will never respond, a peer that crashed silently, a lock that is never released. The exception does not mean the operation *failed* in the sense of being rejected — it means no answer arrived within the caller's patience, and the outcome is unknown.

The class has three main sources. First, the operating system: a TCP connect to an unresponsive address eventually fails with `ETIMEDOUT`, which Python maps to this class. Second, the socket layer: after `sock.settimeout(n)`, any socket operation exceeding `n` seconds raises it (with `errno` set to `None`, since Python itself, not the kernel, enforced the deadline). Third, `asyncio`: deadline utilities like `wait_for` and `asyncio.timeout` raise it when an awaited task overruns. Before Python 3.10/3.11 these were three distinct classes (`TimeoutError`, `socket.timeout`, `asyncio.TimeoutError`); the aliases merged them so one name covers all timeout semantics. One notable holdout: `subprocess.TimeoutExpired` is *not* related to this class — it subclasses `SubprocessError`.

Semantically, the exception's defining contrast is with active rejection. `ConnectionRefusedError` means the peer answered "no"; `TimeoutError` means nobody answered at all. Diagnostic code leans on that distinction (host down or filtered versus service down), so the translation must convey *expired waiting time*, not refusal, and not mere slowness.

**Key behaviors:**

1. **Maps to `ETIMEDOUT`:** Any `OSError` raised with this errno becomes a `TimeoutError` instance automatically. Timeouts enforced by Python itself (socket allowances, asyncio deadlines) raise the same class with `errno` set to `None`.

2. **Unified aliases:** `socket.timeout is TimeoutError` since Python 3.10; `asyncio.TimeoutError is TimeoutError` since Python 3.11. Code supporting older versions still catches the module-specific names; new code needs only the builtin.

3. **Means "no answer in time," not "rejected":** The operation's true outcome is unknown — the response may even arrive after the exception. Retry logic must account for possibly-duplicated effects, which is why timeout handling is more delicate than refusal handling.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (timeout event + error type)
- **Action vs State:** STATE - names an error condition, not an action
- **Temporal aspect:** Instantaneous at the deadline - the moment the waiting allowance expires

### Recommended Form

**Primary recommendation:** Compound noun built on the language's established networking term for a timeout — the word local OS messages, browsers, and CS courses already use for "connection timed out" — plus the corpus "error" word. The term must convey an *expired waiting allowance*, not a pause and not general slowness.

**Forms to AVOID:**

- ❌ Sports "timeout" vocabulary (a called pause in play) - inverts the meaning; nothing paused, time expired
- ❌ Words meaning merely "slow" or "delayed" - the operation did not complete late; it was abandoned at the deadline
- ❌ Verb forms ("use up the time" phrasings) - reads as a command to use up time

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: A called pause in a sports game ("the coach called a timeout")
- ❌ Meaning 2: A child-discipline pause ("five minutes of time-out")
- ❌ Meaning 3: A rest break ("let's take time out from work")
- ✅ Meaning 4: **EXPIRY OF AN ALLOTTED WAITING PERIOD** (an operation was given a deadline and the deadline passed with no completion; OS code `ETIMEDOUT`)

**Example:**

English "timeout" can mean:

1. "They called a timeout in the fourth quarter" (sports pause) ❌
2. "The toddler got a time-out" (discipline) ❌
3. "Take some time out and relax" (break) ❌
4. "The request timed out after 30 seconds" (deadline expired) ✅ **This is the Python meaning**

**Your translation should capture meaning #4: an expired waiting allowance with no answer received — NOT pauses, breaks, or discipline.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `TimeoutError`, check these translations:**

- [ ] `ConnectionError` (connectionerror.md) and its siblings (connectionabortederror.md, connectionrefusederror.md, connectionreseterror.md, brokenpipeerror.md) - Same `OSError` family and constant companions in `except` chains; the "error" suffix must be identical across all of them
- [ ] `ConnectionRefusedError` (connectionrefusederror.md) - The contrasting active-rejection failure; the two modifiers must be unmistakably different
- [ ] `BlockingIOError` (blockingioerror.md) - Sibling "waiting" exception; would-block vocabulary must not blur into timeout vocabulary
- [ ] `InterruptedError` (interruptederror.md) - Sibling; a call ended by a signal, not by a deadline
- [ ] `async` / `await` - This class is the standard asyncio deadline exception since 3.11; the term must sit naturally in async code

**Consistency rule:**

The "error" suffix comes verbatim from the exception corpus (anchored by connectionerror.md and its family). The timeout word should match the language's existing "connection timed out" localization and must stay distinct from the "refused," "blocking," and "interrupted" modifiers used by the sibling briefs.


### Functional relationships

**This term works WITH:**

1. **`socket.settimeout()` + `TimeoutError`**: The allowance and its expiry:

```python
sock.settimeout(5.0)
try:
    data = sock.recv(4096)
except TimeoutError:
    data = None  # nothing arrived within 5 seconds
```

2. **`asyncio.wait_for()` / `asyncio.timeout()` + `TimeoutError`**: Deadlines for coroutines (3.11+):

```python
async def fetch_with_deadline():
    async with asyncio.timeout(2.0):
        result = await slow_operation()
```

**Common pairing:**

```python
# Connect-probe triage: silence vs rejection vs success
import socket

def probe(host: str, port: int) -> str:
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return "open"
    except TimeoutError:
        return "no answer (host down, or a firewall is dropping packets)"
    except ConnectionRefusedError:
        return "host alive, port closed (it answered 'no')"
    except OSError as exc:
        return f"other failure: {exc}"

print(probe("127.0.0.1", 1))
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `TimeoutError`

- Every language localizes "connection timed out" somewhere (OS, browser), providing an anchor — but some communities just use the English loanword "timeout"
- The sports/pause senses are attractive false friends
- Must contrast cleanly with "refused" (active rejection) and "blocking" (no deadline involved)
- The 3.10/3.11 alias unification simplifies the job: one term now covers socket, asyncio, and OS timeouts

**For this term:** MEDIUM

**Rationale:** The concept is universal and most languages have a settled networking term. The judgment calls are whether to fight an entrenched English loanword and how to phrase "expired allowance" compactly — solvable with the local OS localization as evidence.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures EXPIRED WAITING ALLOWANCE (not a sports pause, break, or mere delay)?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Conveys silence/no-answer, in contrast to active refusal?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Ends with the same "error" word as the rest of the exception corpus?
- [ ] Distinct from the `ConnectionRefusedError`, `BlockingIOError`, and `InterruptedError` modifiers?
- [ ] Matches the language's established "connection timed out" localization where one exists?

### 4. Usability

- [ ] Short enough (1-3 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional (no playground "time-out" flavor)?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs (especially RTL)?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: TimeoutError
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
