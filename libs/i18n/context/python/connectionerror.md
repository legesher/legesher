# Python Builtin: `ConnectionError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.3+
**Difficulty:** MEDIUM

---

## Quick Summary

`ConnectionError` is the built-in base class for connection-related failures: it is a subclass of `OSError` and the parent of `BrokenPipeError`, `ConnectionAbortedError`, `ConnectionRefusedError`, and `ConnectionResetError`. It was introduced by PEP 3151 in Python 3.3, which reorganized OS and I/O errors into specific exception classes so code can catch "the connection failed" as one family.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Connecting to a port where nothing is listening raises a ConnectionError subclass
import socket

try:
    socket.create_connection(("127.0.0.1", 9), timeout=2.0)
except ConnectionError as exc:
    print(f"Connection failed: {exc}")
    print(type(exc).__name__)  # ConnectionRefusedError (a ConnectionError subclass)
```

**What this does:** The connection attempt fails because no server is listening on that port. The operating system reports the failure, Python raises the specific subclass (`ConnectionRefusedError`), and the `except ConnectionError` clause catches it because every member of the family inherits from `ConnectionError`.

### Example 2: Common Pattern

```python
# Retry loop that treats all connection failures uniformly
import socket
import time

def fetch_with_retry(host, port, attempts=3):
    for attempt in range(1, attempts + 1):
        try:
            with socket.create_connection((host, port), timeout=2.0) as conn:
                conn.sendall(b"PING\n")
                return conn.recv(1024)
        except ConnectionError as exc:
            print(f"Attempt {attempt} failed: {exc}")
            time.sleep(1.0)
    raise RuntimeError(f"Could not reach {host}:{port} after {attempts} attempts")
```

**What this does:** Network code rarely cares whether a connection was refused, reset, or aborted when deciding to retry. Catching the parent class `ConnectionError` handles all four failure modes in one clause, keeping the retry logic simple while the exception object still carries the specific subclass and `errno` for logging.

### Example 3: Edge Case

```python
# ConnectionError is a hierarchy: subclasses map OS errno values to Python classes
print(issubclass(ConnectionRefusedError, ConnectionError))  # True
print(issubclass(ConnectionResetError, ConnectionError))    # True
print(issubclass(ConnectionAbortedError, ConnectionError))  # True
print(issubclass(BrokenPipeError, ConnectionError))         # True
print(issubclass(ConnectionError, OSError))                 # True

# Raising OSError with a connection errno produces the specific subclass
import errno
try:
    raise OSError(errno.ECONNRESET, "simulated reset")
except ConnectionError as exc:
    print(type(exc).__name__)  # ConnectionResetError
```

**What this shows:** `ConnectionError` itself has no single `errno`; instead, each subclass corresponds to one OS error code (`ECONNABORTED`, `ECONNREFUSED`, `ECONNRESET`, `EPIPE`/`ESHUTDOWN`). Constructing `OSError` with one of those codes automatically yields the matching subclass — the errno-to-class mapping is built into the exception machinery.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `OSError` - Direct parent class; the root of all operating-system error exceptions
2. `ConnectionRefusedError` - Child class: the peer actively refused the connection attempt
3. `ConnectionResetError` - Child class: the peer abruptly tore down an established connection
4. `TimeoutError` - Sibling `OSError` subclass; a frequent companion in the same `except` chains

**Pattern rule:** Exception classes are noun compounds ending in "Error." Translations must convey the problem domain ("connection") plus "error," never a verb form. Because this class names an entire family, its translation of "connection" becomes the mandatory root for all four subclasses.


---

## Etymology (Brief)

**English Origin:** Compound word (Latin + Latin-derived)

**Root meaning:** "Connection" comes from Latin "connectere" (con- "together" + nectere "to bind, tie"), meaning to link things together. In networking, a connection is an established communication channel between two endpoints. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** Before PEP 3151 (Python 3.3), connection failures surfaced as generic `OSError`/`socket.error` values that had to be told apart by inspecting `errno` codes. `ConnectionError` gives the whole failure family one catchable name, following Python's convention of combining the problem domain ("Connection") with "Error."

---

## Concept Explanation (Intermediate Level)

**What it does:**

`ConnectionError` is raised — almost always as one of its four subclasses — when a communication channel between two endpoints fails: the peer refuses a new connection, an established connection is reset or aborted, or a write lands on a pipe or socket whose other end has gone away. It inherits from `OSError`, so it carries the standard `errno`, `strerror`, and `filename` attributes describing what the operating system reported.

The class exists primarily as a *catch target*. Application code seldom raises `ConnectionError` directly; instead, the socket layer, `http.client`, `urllib`, `asyncio`, and similar libraries let the OS-level failure propagate as the precise subclass, while callers write `except ConnectionError:` to handle "the network path failed" as a single condition. This mirrors how `LookupError` groups `KeyError` and `IndexError`.

Understanding the hierarchy matters for robust network code: catching `ConnectionError` is usually correct for retry/reconnect logic, while catching a specific subclass is correct when the failure modes need different responses (for example, "refused" often means the service is down, while "reset" often means it crashed mid-conversation). Catching `OSError` instead would be too broad, sweeping in permission errors and file-system failures.

**Key behaviors:**

1. **Family base class:** `except ConnectionError:` catches `BrokenPipeError`, `ConnectionAbortedError`, `ConnectionRefusedError`, and `ConnectionResetError`. The exception instance is still the specific subclass, so its identity and `errno` survive for logging.

2. **Errno mapping lives in the subclasses:** `ConnectionError` has no dedicated `errno` of its own. The OS codes map to children: `ECONNABORTED` → `ConnectionAbortedError`, `ECONNREFUSED` → `ConnectionRefusedError`, `ECONNRESET` → `ConnectionResetError`, `EPIPE`/`ESHUTDOWN` → `BrokenPipeError`.

3. **Raised throughout the networking stack:** Socket operations, HTTP clients, and async transports all surface these exceptions. Any `OSError` constructed with one of the mapped errno values becomes the corresponding subclass automatically.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (problem domain "connection" + error type)
- **Action vs State:** STATE - names an error condition, not an action
- **Temporal aspect:** Instantaneous - describes the moment a connection operation fails

### Recommended Form

**Primary recommendation:** Use a compound noun combining the target language's standard word for a network "connection" with the established word for "error." This translation is the anchor for the whole family: whatever word is chosen for "connection" here MUST reappear in `ConnectionAbortedError`, `ConnectionRefusedError`, and `ConnectionResetError`.

**Forms to AVOID:**

- ❌ Verb forms ("FailToConnect" style) - exceptions are nouns, not actions
- ❌ Words meaning personal or emotional connection - this is a network transport link
- ❌ Generic "network error" - loses the specific connection concept and breaks alignment with the subclasses

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Personal or emotional bond ("we have a real connection")
- ❌ Meaning 2: Physical junction ("the hose connection is leaking")
- ❌ Meaning 3: Transport transfer ("a connection in Frankfurt")
- ✅ Meaning 4: **NETWORK COMMUNICATION CHANNEL** (an established link between two endpoints, e.g. a TCP connection)

**Example:**

English "connection" can mean:

1. "They felt an instant connection" (emotional bond) ❌
2. "Tighten the pipe connection" (physical junction) ❌
3. "I missed my connection at the airport" (transfer) ❌
4. "The server dropped the connection" (network channel) ✅ **This is the Python meaning**

**Your translation should capture meaning #4: a network communication channel, NOT emotional, physical, or travel senses.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `ConnectionError`, check these translations:**

- [ ] `ConnectionAbortedError` (connectionabortederror.md) - Child class; must reuse this "connection" root and "error" suffix
- [ ] `ConnectionRefusedError` (connectionrefusederror.md) - Child class; must reuse this "connection" root and "error" suffix
- [ ] `ConnectionResetError` (connectionreseterror.md) - Child class; must reuse this "connection" root and "error" suffix
- [ ] `BrokenPipeError` (brokenpipeerror.md) - Child class; English drops the "connection" root here, but the "error" suffix must still match the family
- [ ] `TimeoutError` (timeouterror.md) - Sibling `OSError` subclass often caught alongside this family; "error" suffix must match
- [ ] `KeyError`, `TypeError`, `ValueError` - The corpus-wide exception pattern this translation must follow

**Consistency rule:**

The word chosen here for "connection" is the family anchor. Every `ConnectionX` subclass translation must contain it verbatim, and every family member must end with the same "error" word used across the exception corpus. Translate the parent first, then derive the children.


### Functional relationships

**This term works WITH:**

1. **`try`/`except` + `ConnectionError`**: The standard way to guard any socket or HTTP operation:

```python
try:
    sock.sendall(data)
except ConnectionError:
    reconnect()
```

2. **`OSError` + `ConnectionError`**: Ordering matters in multi-clause handlers — the subclass must be listed before the parent:

```python
try:
    sock.recv(1024)
except ConnectionError:
    handle_connection_loss()   # specific family first
except OSError:
    handle_other_os_error()    # broader fallback second
```

**Common pairing:**

```python
# Client that distinguishes family members while retrying on any of them
import socket
import time

def send_message(host, port, payload, retries=3):
    for attempt in range(retries):
        try:
            with socket.create_connection((host, port), timeout=2.0) as conn:
                conn.sendall(payload)
                return conn.recv(1024)
        except ConnectionRefusedError:
            print("Server not accepting connections yet; waiting...")
            time.sleep(2.0)
        except ConnectionError as exc:
            print(f"Connection lost ({type(exc).__name__}); retrying...")
            time.sleep(0.5)
    raise RuntimeError("giving up")
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `ConnectionError`

- "Connection" has strong non-technical senses (emotional, physical, travel) that must be excluded
- Most languages have an established networking term for "connection," so the choice is usually clear
- The real difficulty is architectural: this translation constrains four subclass translations
- Must match the corpus-wide exception naming pattern

**For this term:** MEDIUM

**Rationale:** The networking sense of "connection" is well established in technical vocabularies, so finding a word is not hard. The care point is that this is the family-anchor translation: an imprecise or unpopular choice here propagates into every `ConnectionX` subclass and cannot be changed later without breaking four other terms.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures NETWORK CONNECTION (not emotional, physical, or travel senses)?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Would a developer recognize this as the base class for connection failures?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Matches pattern of other exception translations (`KeyError`, `TypeError`)?
- [ ] "Connection" root is reusable verbatim in all four subclass names?
- [ ] "Error" word identical to the rest of the exception corpus?

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
term: ConnectionError
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
