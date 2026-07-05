# Python Builtin: `ConnectionResetError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.3+
**Difficulty:** HARD

---

## Quick Summary

`ConnectionResetError` is a built-in exception raised when an established connection is reset by the peer — the other side abruptly tears down the conversation, typically via a TCP RST packet, instead of closing it gracefully. It is a subclass of `ConnectionError` (and thus `OSError`), introduced by PEP 3151 in Python 3.3, and corresponds to the OS error code `ECONNRESET` ("Connection reset by peer").

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Force a genuine TCP reset with SO_LINGER, then read from the victim side
import socket
import struct

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("127.0.0.1", 0))
server.listen(1)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(server.getsockname())
conn, _ = server.accept()

# SO_LINGER with timeout 0 makes close() send an RST instead of FIN
conn.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
conn.close()

try:
    client.recv(1024)
except ConnectionResetError as exc:
    print(f"Peer reset the connection: {exc}")  # errno ECONNRESET
```

**What this does:** The server side closes with `SO_LINGER` set to zero, which sends a TCP RST — a forcible teardown — instead of the normal FIN handshake. The client's next `recv()` then raises `ConnectionResetError`, exactly as it would if a real server crashed or a proxy killed the connection.

### Example 2: Common Pattern

```python
# Client loop that treats a reset as "server went away; reconnect"
import socket
import time

def request(host, port, payload, retries=3):
    for attempt in range(1, retries + 1):
        try:
            with socket.create_connection((host, port), timeout=5.0) as conn:
                conn.sendall(payload)
                return conn.recv(4096)
        except ConnectionResetError:
            print(f"Connection reset mid-request (attempt {attempt}); reconnecting")
            time.sleep(0.5 * attempt)
    raise RuntimeError("server keeps resetting the connection")
```

**What this does:** A reset in the middle of a request usually means the server process crashed, restarted, or an intermediary (load balancer, proxy) dropped the session. Because the failure hit an *established* connection, the standard recovery is to open a fresh connection and retry — unlike `ConnectionRefusedError`, where no connection ever existed.

### Example 3: Edge Case

```python
# A write after the peer resets may "succeed" -- the reset surfaces on the NEXT call
import socket
import struct

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("127.0.0.1", 0))
server.listen(1)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(server.getsockname())
conn, _ = server.accept()
conn.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
conn.close()  # RST is on its way

try:
    client.sendall(b"first write")   # may be accepted into the local buffer
    client.recv(1024)                # the reset surfaces here
except ConnectionResetError as exc:
    print(f"Reset detected on a later call: {exc}")
except BrokenPipeError as exc:
    print(f"Or, if the RST won the race, the pending write fails: {exc}")
```

**What this shows:** Resets are asynchronous. The kernel may accept one more write into its buffer before the RST is processed, so the exception often appears one operation *after* the peer actually vanished. Robust code cannot assume the failing call is the one that "caused" the reset — and depending on timing and platform, the queued write itself can fail instead, surfacing as the sibling `BrokenPipeError`, which is why the handler covers both.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `ConnectionError` - Direct parent class; base of the connection-failure family
2. `ConnectionAbortedError` - Sibling: connection torn down before completing (`ECONNABORTED`)
3. `ConnectionRefusedError` - Sibling: connection attempt rejected outright (`ECONNREFUSED`)
4. `BrokenPipeError` - Sibling: write to a pipe or socket whose other end is gone (`EPIPE`)

**Pattern rule:** Exception classes are noun compounds ending in "Error." This name is "connection" + past participle "reset" + "error" — translations should attach a modifier meaning "forcibly torn down" to the family's shared "connection" root.


---

## Etymology (Brief)

**English Origin:** Compound word (Latin roots + Germanic "set")

**Root meaning:** "Reset" is re- (Latin "again") + "set" (Old English "settan," to place): to put back to an initial state. In TCP, the RST ("reset") flag orders both ends to discard the connection state immediately — the connection is wiped back to nonexistence, not restarted.

**Why Python uses this:** The name quotes the POSIX error string for `ECONNRESET`, "Connection reset by peer" — networking's most famous error message. PEP 3151 gave that errno its own class so code can catch "the peer abruptly dropped an established connection" by name.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`ConnectionResetError` is raised when the peer forcibly terminates an *established* connection. At the TCP level, the peer (or something between — a crashed process's kernel, a NAT box, a load balancer) sends an RST packet, which instantly invalidates the connection state on both sides. The next read or write on the local socket then fails with `ECONNRESET`, which Python surfaces as this exception.

The critical nuance — and the translation trap — is that "reset" here does NOT mean "restored" or "re-established." A reset connection is destroyed, not refreshed. The word comes from TCP's RST flag, which resets the connection state *to nothing*. Several official localizations have historically mistranslated "Connection reset by peer" with words meaning "re-established," inverting the meaning; translators of this term must not repeat that mistake.

Timing separates it from its siblings: `ConnectionRefusedError` happens before a connection exists, `ConnectionAbortedError` while it is coming into existence, and `ConnectionResetError` after it is fully established. In practice it is the signature of a server crash, a process kill, a dropped NAT mapping, or a peer that closed with pending data — and the standard recovery is to reconnect from scratch.

**Key behaviors:**

1. **Maps to `ECONNRESET`:** Any `OSError` raised with this errno becomes a `ConnectionResetError` instance automatically. The numeric value differs by platform (e.g., 104 on Linux, 54 on macOS); the symbolic constant `errno.ECONNRESET` is portable.

2. **Strikes established connections:** It appears on `recv()`/`send()` of a connection that previously worked — never on the initial connect attempt (that would be refused or timed out instead).

3. **Surfaces asynchronously:** The RST may arrive between operations, so an intervening write can appear to succeed and the exception fires on a later call. Code should treat the whole connection as dead, not just the failing operation.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (connection + reset modifier + error type)
- **Action vs State:** STATE - names an error condition, not an action
- **Temporal aspect:** Instantaneous - describes the moment the teardown is detected

### Recommended Form

**Primary recommendation:** Compound noun that embeds the family's exact "connection" word plus the target language's established term for a TCP/network "reset," plus the corpus "error" word. Check how the OS or browser in that language renders "Connection reset by peer" and prefer that vocabulary — unless the localization itself uses a "re-established" word, which must be rejected.

**Forms to AVOID:**

- ❌ Words meaning "re-established" or "restored" - the exact inversion of the meaning; the connection is destroyed
- ❌ Words meaning "restarted" as in rebooted successfully - the connection does not come back
- ❌ Verb forms ("ReiniciarConexión") - reads as a command to reset, not a report that a reset happened

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Restore to factory/default settings ("reset your password," "factory reset")
- ❌ Meaning 2: Restart a device so it works again ("reset the router")
- ❌ Meaning 3: Set again/reposition ("reset a broken bone")
- ✅ Meaning 4: **FORCIBLE CONNECTION TEARDOWN** (the peer sent a TCP RST, instantly destroying the established connection; OS code `ECONNRESET`)

**Example:**

English "reset" can mean:

1. "Reset your password" (restore to a fresh value) ❌
2. "Reset the router and try again" (reboot to recover) ❌
3. "The surgeon reset the bone" (reposition) ❌
4. "Connection reset by peer" (the other side destroyed the connection) ✅ **This is the Python meaning**

**Your translation should capture meaning #4: an abrupt, destructive teardown of an established connection — emphatically NOT restoration, recovery, or re-establishment.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `ConnectionResetError`, check these translations:**

- [ ] `ConnectionError` (connectionerror.md) - Parent class; its "connection" root and "error" suffix MUST appear verbatim in this name
- [ ] `ConnectionAbortedError` (connectionabortederror.md) - Sibling; same structure, distinct modifier ("aborted" ≠ "reset")
- [ ] `ConnectionRefusedError` (connectionrefusederror.md) - Sibling; same structure, distinct modifier ("refused" ≠ "reset")
- [ ] `BrokenPipeError` (brokenpipeerror.md) - Sibling in the same family; must share the "error" suffix even though English gives it no "connection" root
- [ ] `TimeoutError` (timeouterror.md) - Frequently caught alongside this family; "error" suffix must match

**Consistency rule:**

Take the "connection" word directly from the `ConnectionError` translation and the "error" word from the corpus-wide exception pattern; only the "reset" modifier is new. Verify the modifier is (a) destructive in sense, (b) distinct from the "aborted" and "refused" modifiers, and (c) not a "restore/re-establish" word.


### Functional relationships

**This term works WITH:**

1. **`socket.recv()` / `socket.send()` + `ConnectionResetError`**: The canonical raise sites on an established connection:

```python
try:
    data = conn.recv(4096)
except ConnectionResetError:
    reconnect()
```

2. **`except ConnectionError` + subclass ordering**: Specific handler first, family fallback second:

```python
try:
    conn.sendall(payload)
except ConnectionResetError:
    log("peer crashed mid-conversation")
except ConnectionError:
    log("other connection failure")
```

**Common pairing:**

```python
# Long-lived client: reset means rebuild the session from scratch
import socket
import time

def run_session(host, port):
    while True:
        try:
            with socket.create_connection((host, port), timeout=5.0) as conn:
                while True:
                    conn.sendall(b"HEARTBEAT\n")
                    conn.recv(64)
                    time.sleep(1.0)
        except ConnectionResetError:
            print("Session reset by peer; reconnecting")
            time.sleep(1.0)  # then loop opens a brand-new connection
        except ConnectionRefusedError:
            print("Server down; waiting longer")
            time.sleep(5.0)
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

### HARD

- No direct equivalent in some languages
- May need compound term or explanation
- Concept doesn't exist universally
- **AI confidence should be MEDIUM, human review recommended**

### Why HARD for `ConnectionResetError`

- "Reset" is highly polysemous, and its most common everyday senses (restore, reboot, refresh) are the OPPOSITE of the TCP meaning
- Real-world localizations have shipped the "re-established" mistranslation, so existing local strings cannot be trusted blindly
- Some languages have no destructive "reset" word and fall back to loanwords
- The modifier must stay distinct from "aborted" and "refused" siblings

**For this term:** HARD

**Rationale:** The family root and error suffix are inherited, but the "reset" modifier is a genuine trap: most candidate words in most languages lean toward "restore/restart," which inverts the semantics of a destroyed connection. Human review of the chosen modifier against the language's actual networking literature is strongly recommended.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures FORCIBLE TEARDOWN of an established connection (TCP RST)?
- [ ] Absolutely does NOT read as "restored" or "re-established"?
- [ ] Clearly indicates an ERROR occurred?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Contains the exact "connection" word from the `ConnectionError` translation?
- [ ] Ends with the same "error" word as the rest of the exception corpus?
- [ ] Modifier differs from those in `ConnectionAbortedError` and `ConnectionRefusedError`?

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
term: ConnectionResetError
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
