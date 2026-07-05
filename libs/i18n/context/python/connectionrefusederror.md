# Python Builtin: `ConnectionRefusedError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.3+
**Difficulty:** MEDIUM

---

## Quick Summary

`ConnectionRefusedError` is a built-in exception raised when a connection attempt is refused by the peer — typically because nothing is listening on the target port, so the remote host actively rejects the request. It is a subclass of `ConnectionError` (and thus `OSError`), introduced by PEP 3151 in Python 3.3, and corresponds to the OS error code `ECONNREFUSED`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Connecting to a port with no listener: the host replies "refused"
import socket

try:
    socket.create_connection(("127.0.0.1", 1), timeout=2.0)
except ConnectionRefusedError as exc:
    print(f"Refused: {exc}")  # e.g. [Errno 61] Connection refused (number varies by OS)
```

**What this does:** Port 1 on localhost almost never has a server listening, so the operating system answers the connection attempt with an active rejection (a TCP RST). Python surfaces that as `ConnectionRefusedError`, carrying `errno.ECONNREFUSED` and the OS message "Connection refused."

### Example 2: Common Pattern

```python
# Waiting for a service to come up: refusal means "not ready yet"
import socket
import time

def wait_for_service(host, port, timeout=30.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return True  # server is accepting connections
        except ConnectionRefusedError:
            time.sleep(0.5)  # host is up, service not listening yet
    return False

if wait_for_service("127.0.0.1", 8080):
    print("Service ready")
else:
    print("Service never came up")
```

**What this does:** Test harnesses and deployment scripts poll a port until the server starts. `ConnectionRefusedError` is the expected signal during startup — the host is reachable but the service has not bound its port yet — so the loop sleeps and retries instead of failing.

### Example 3: Edge Case

```python
# Refusal is an ANSWER; a timeout is SILENCE -- different exceptions
import socket

def probe(host, port):
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return "open"
    except ConnectionRefusedError:
        return "closed: host reachable, port actively refused"
    except TimeoutError:
        return "filtered or unreachable: no reply at all"

print(probe("127.0.0.1", 1))  # closed: host reachable, port actively refused
```

**What this shows:** "Refused" means the peer *responded* with a rejection — proof the host is alive. When packets vanish (firewall drop, host down), no rejection ever arrives and the attempt ends in `TimeoutError` instead. Translations must preserve this active-rejection sense; a word meaning "ignored" or "unanswered" would describe the wrong exception.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `ConnectionError` - Direct parent class; base of the connection-failure family
2. `ConnectionResetError` - Sibling: established connection forcibly closed by the peer (`ECONNRESET`)
3. `ConnectionAbortedError` - Sibling: connection torn down before completing (`ECONNABORTED`)
4. `TimeoutError` - Sibling `OSError` subclass: the contrasting "no answer" failure (`ETIMEDOUT`)

**Pattern rule:** Exception classes are noun compounds ending in "Error." This name is "connection" + past participle "refused" + "error" — translations should attach a participle meaning "actively rejected" to the family's shared "connection" root.


---

## Etymology (Brief)

**English Origin:** Compound word (Latin roots via Old French)

**Root meaning:** "Refuse" comes from Old French "refuser," from Latin "refundere/recusare" — to reject, to decline to accept. The word implies an active, delivered rejection rather than mere absence of acceptance. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** The name mirrors the POSIX error string for `ECONNREFUSED`, "Connection refused" — one of the most recognizable error messages in networking. PEP 3151 promoted that errno to a dedicated class so the everyday "is the server even running?" failure gets its own catchable name.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`ConnectionRefusedError` is raised when a connection attempt reaches a host that answers, "no." At the TCP level, the client sends a SYN packet and the target machine replies with an RST because no process is listening on that port. The operating system reports `ECONNREFUSED`, and Python raises this exception from `socket.connect()`, `socket.create_connection()`, and every higher-level client built on them (`http.client`, `urllib`, `asyncio` transports).

This is usually the very first networking error a developer meets: start a client before the server, mistype a port number, or point at the wrong host, and this exception appears. Its diagnostic value is precise — the network path works and the host is alive; what is missing is a listening service. That makes it the standard signal in "wait until the server is up" polling loops.

The distinction to preserve is *active rejection versus silence*. Refusal is a delivered answer; if a firewall silently drops the packets or the host is down, the attempt instead ends in `TimeoutError`. And unlike its siblings, refusal happens before any connection exists at all — nothing was established, so there is nothing to reset or abort.

**Key behaviors:**

1. **Maps to `ECONNREFUSED`:** Any `OSError` raised with this errno becomes a `ConnectionRefusedError` instance automatically. The numeric value differs by platform (e.g., 111 on Linux, 61 on macOS); the symbolic constant `errno.ECONNREFUSED` is portable.

2. **Raised at connect time, not during a conversation:** It comes from the connection *attempt*. Once a connection is established, failures surface as `ConnectionResetError`, `BrokenPipeError`, or `TimeoutError` instead.

3. **Caught by the family handler:** `except ConnectionError:` catches it along with its siblings. Retry loops commonly catch this specific class, because a refusal often just means "try again in a moment."

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (connection + refused modifier + error type)
- **Action vs State:** STATE - names an error condition, not an action
- **Temporal aspect:** Instantaneous - describes the moment the rejection arrives

### Recommended Form

**Primary recommendation:** Compound noun that embeds the family's exact "connection" word (from `ConnectionError`) plus a participle or verbal noun meaning "actively rejected," plus the corpus "error" word. The rejection word should imply a delivered answer, not silence or neglect.

**Forms to AVOID:**

- ❌ Verb forms ("RechazarConexión") - reads as a command to refuse, not a report of refusal
- ❌ Words meaning "ignored" or "unanswered" - that is the semantics of `TimeoutError`, not refusal
- ❌ Words meaning "forbidden/denied by policy" - permission vocabulary belongs to `PermissionError`, not this class

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Decline an offer or invitation ("she refused the job")
- ❌ Meaning 2: Rubbish/waste (the noun "refuse," pronounced differently)
- ❌ Meaning 3: Denial of permission by policy ("access refused")
- ✅ Meaning 4: **ACTIVE NETWORK REJECTION** (the target host answered the connection attempt with a rejection because no service is listening; OS code `ECONNREFUSED`)

**Example:**

English "refuse(d)" can mean:

1. "He refused the invitation" (social decline) ❌
2. "Refuse collection is on Tuesdays" (garbage) ❌
3. "Entry refused without a badge" (authorization) ❌
4. "connect() failed: connection refused" (network rejection) ✅ **This is the Python meaning**

**Your translation should capture meaning #4: an active rejection of a network connection attempt, NOT social, waste, or authorization senses.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `ConnectionRefusedError`, check these translations:**

- [ ] `ConnectionError` (connectionerror.md) - Parent class; its "connection" root and "error" suffix MUST appear verbatim in this name
- [ ] `ConnectionAbortedError` (connectionabortederror.md) - Sibling; same structure, distinct modifier ("aborted" ≠ "refused")
- [ ] `ConnectionResetError` (connectionreseterror.md) - Sibling; same structure, distinct modifier ("reset" ≠ "refused")
- [ ] `BrokenPipeError` (brokenpipeerror.md) - Sibling in the same family; must share the "error" suffix even though English gives it no "connection" root
- [ ] `TimeoutError` (timeouterror.md) - The contrasting "silence" failure; must NOT share this term's rejection vocabulary

**Consistency rule:**

Take the "connection" word directly from the `ConnectionError` translation and the "error" word from the corpus-wide exception pattern; only the "refused" modifier is new. It must be distinguishable from the sibling modifiers ("aborted," "reset") and from whatever words render `TimeoutError` and `PermissionError`.


### Functional relationships

**This term works WITH:**

1. **`socket.create_connection()` + `ConnectionRefusedError`**: The canonical raise site:

```python
try:
    sock = socket.create_connection((host, port), timeout=2.0)
except ConnectionRefusedError:
    print("Server not running?")
```

2. **`except` chains with `TimeoutError`**: The two complementary connect-failure diagnoses:

```python
try:
    socket.create_connection((host, port), timeout=1.0)
except ConnectionRefusedError:
    diagnose("host alive, port closed")
except TimeoutError:
    diagnose("no response at all")
```

**Common pairing:**

```python
# Startup polling: refusal is the expected "not yet" signal
import socket
import time

def wait_until_listening(port, retries=20):
    for _ in range(retries):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1.0):
                return True
        except ConnectionRefusedError:
            time.sleep(0.25)   # service starting up; try again
        except ConnectionError:
            time.sleep(0.25)   # any other family member: also retry
    return False
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `ConnectionRefusedError`

- "Connection refused" is a famous OS message with an existing localized form in many languages — find and match it
- The modifier must convey ACTIVE rejection, not silence ("ignored") or policy denial ("forbidden")
- The "connection" root and "error" suffix are already fixed by the family
- Must contrast with three sibling modifiers plus `TimeoutError` and `PermissionError` vocabulary

**For this term:** MEDIUM

**Rationale:** Most languages have a well-worn localized string for "Connection refused" from operating systems and browsers, which anchors the modifier choice. The remaining care points are keeping the family root intact and reserving the rejection word so it does not collide with permission-denial vocabulary elsewhere in the corpus.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures ACTIVE NETWORK REJECTION (host answered "no"), not silence or policy denial?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Distinguishable from "aborted" and "reset" siblings and from `TimeoutError`?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun with participle/verbal-noun modifier)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Contains the exact "connection" word from the `ConnectionError` translation?
- [ ] Ends with the same "error" word as the rest of the exception corpus?
- [ ] Modifier differs from those in `ConnectionAbortedError`, `ConnectionResetError`, and `PermissionError`?

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
term: ConnectionRefusedError
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
