# Python Builtin: `BrokenPipeError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.3+
**Difficulty:** HARD

---

## Quick Summary

`BrokenPipeError` is a built-in exception raised when writing to a pipe whose reading end has been closed, or to a socket that has been shut down for writing — the data has nowhere to go because the other end is gone. It is a subclass of `ConnectionError` (and thus `OSError`), introduced by PEP 3151 in Python 3.3, and corresponds to the OS error codes `EPIPE` and `ESHUTDOWN`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Writing to a pipe after its read end closed raises BrokenPipeError
import os

r, w = os.pipe()
os.close(r)  # nobody will ever read from this pipe again

try:
    os.write(w, b"data")
except BrokenPipeError as exc:
    print(f"No reader on the pipe: {exc}")  # errno EPIPE
finally:
    os.close(w)
```

**What this does:** A pipe is a one-way byte channel with a write end and a read end. Once the read end is closed, writes can never be consumed, so the OS reports `EPIPE`. Python installs a SIGPIPE-ignore at startup, so instead of the process being killed (the default C behavior), the write raises a catchable `BrokenPipeError`.

### Example 2: Common Pattern

```python
# Writing to a socket after the peer closed it
import socket

a, b = socket.socketpair()
b.close()  # the peer is gone

try:
    a.sendall(b"first")
    a.sendall(b"second")  # a write after the peer closed raises BrokenPipeError
except BrokenPipeError as exc:
    print(f"Peer no longer reading: {exc}")
finally:
    a.close()
```

**What this does:** Sending to a socket whose peer has closed raises `BrokenPipeError` — immediately on some platforms, or on the write after the teardown is processed on others (that is why both `sendall` calls sit inside the `try`). Servers hit this constantly when clients disconnect mid-response; the standard handling is to abandon that client quietly.

### Example 3: Edge Case

```python
# The classic case: your script's stdout is a pipe and the reader exits early
# Save as emit.py and run:  python emit.py | head -n 1
import sys

try:
    for i in range(100_000):
        print(i)
except BrokenPipeError:
    # head took one line and exited; our stdout pipe lost its reader
    sys.stderr.write("Downstream reader exited early\n")
    sys.exit(0)  # conventional success exit for a truncated pipeline
```

**What this shows:** In a shell pipeline, `head` closes the pipe after reading what it needs. The next `print()` then raises `BrokenPipeError` inside the Python process. This is the most common real-world encounter with the exception — command-line tools should catch it and exit cleanly rather than dumping a traceback into the user's terminal.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `ConnectionError` - Direct parent class; base of the connection-failure family
2. `ConnectionResetError` - Sibling: peer forcibly tore down an established connection (`ECONNRESET`)
3. `ConnectionAbortedError` - Sibling: connection torn down before completing (`ECONNABORTED`)
4. `ConnectionRefusedError` - Sibling: connection attempt rejected outright (`ECONNREFUSED`)

**Pattern rule:** Exception classes are noun compounds ending in "Error." This name is adjective "broken" + noun "pipe" + "error" — the only family member whose English name omits the "connection" root. Translations keep a "damaged conduit" noun phrase plus the corpus "error" word.


---

## Etymology (Brief)

**English Origin:** Compound word (Germanic + Latin-derived)

**Root meaning:** "Pipe" comes from Latin "pipare" via Old English "pīpe," originally a musical tube, later any tube that carries something. Unix adopted the plumbing metaphor in 1973: a "pipe" carries a stream of bytes from one process to another. "Broken" (Old English "brecan") means fractured — a broken pipe leaks its contents; nothing arrives at the far end.

**Why Python uses this:** The name quotes the POSIX error string for `EPIPE`, "Broken pipe," inherited from decades of Unix tradition (and the shell's `|` operator). PEP 3151 turned the errno into a class so pipeline and socket code can catch "the reader disappeared" by name.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`BrokenPipeError` is raised when a process writes into a communication channel whose consuming end no longer exists: a pipe whose read end was closed, or a socket the peer has shut down for reading. The write cannot ever be delivered, so the operating system fails it with `EPIPE` (or `ESHUTDOWN` for writes on a socket already shut down). It is a write-side error by nature — reading from an abandoned channel returns end-of-file instead.

The exception is inseparable from Unix history. In C programs, writing to a broken pipe delivers the SIGPIPE signal, which kills the process by default — that is why `grep pattern bigfile | head` terminates `grep` silently. Python instead ignores SIGPIPE at interpreter startup so the failure arrives as this catchable exception. A subtlety follows: after catching it for `sys.stdout`, the interpreter may still emit a "BrokenPipeError ignored" message at shutdown when it tries to flush stdout; command-line tools often redirect or close stdout defensively in the handler.

Although "pipe" sounds local, the class belongs to the `ConnectionError` family because sockets raise it too: writing to a peer-closed TCP connection is morally the same event — your bytes have no destination. The metaphor is the translation challenge: languages without the Unix plumbing tradition need a word for a byte *conduit*, not a smoking pipe and not necessarily a plumbing term.

**Key behaviors:**

1. **Maps to `EPIPE` and `ESHUTDOWN`:** Any `OSError` raised with either errno becomes a `BrokenPipeError` instance automatically. `EPIPE` is by far the more common in practice.

2. **Write-side only:** Triggered by `write()`/`send()` variants when the consuming end is gone. The corresponding read-side event is not an error at all — reads simply return `b""` (end-of-file).

3. **Suppressed SIGPIPE:** Python ignores SIGPIPE at startup, converting the C-world process-killing signal into this exception. In shell pipelines, catching it and exiting quietly is the expected etiquette for command-line tools.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (broken modifier + conduit noun + error type)
- **Action vs State:** STATE - names an error condition, not an action
- **Temporal aspect:** Instantaneous - describes the moment a write hits the dead channel

### Recommended Form

**Primary recommendation:** Compound noun using the target language's established rendering of the Unix "pipe" concept (conduit, channel, tube) plus a "broken/severed" modifier, plus the corpus "error" word. Check how the language's Unix/Linux documentation translates "broken pipe" and prefer that term — this error string has fifty years of localization history.

**Forms to AVOID:**

- ❌ Words for a smoking pipe or musical pipe - wrong object entirely
- ❌ Forcing the family's "connection" word into the name - English deliberately says "pipe," not "connection"; mirror that
- ❌ Verb forms (a "break the pipe" imperative compound) - reads as a command to break the pipe, not a report that it broke

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Smoking pipe (tobacco)
- ❌ Meaning 2: Musical pipe (organ pipe, bagpipes)
- ❌ Meaning 3: Physical plumbing that leaks water ("a burst pipe flooded the kitchen")
- ✅ Meaning 4: **INTERPROCESS BYTE CHANNEL WHOSE READER IS GONE** (a Unix pipe or socket write channel severed by the closed far end; OS codes `EPIPE`/`ESHUTDOWN`)

**Example:**

English "pipe" can mean:

1. "He lit his pipe" (smoking) ❌
2. "The organ has 4,000 pipes" (music) ❌
3. "A frozen pipe burst in the basement" (plumbing, the metaphor's source) ❌
4. "`ls | head` connects two processes with a pipe" (byte channel) ✅ **This is the Python meaning**

**Your translation should capture meaning #4: a data conduit between processes or endpoints, using the plumbing metaphor only as imagery — NOT tobacco, music, or literal waterworks.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `BrokenPipeError`, check these translations:**

- [ ] `ConnectionError` (connectionerror.md) - Parent class; this term must share its "error" suffix (though NOT its "connection" root — English omits it here deliberately)
- [ ] `ConnectionAbortedError` (connectionabortederror.md) - Sibling; same family "error" suffix
- [ ] `ConnectionRefusedError` (connectionrefusederror.md) - Sibling; same family "error" suffix
- [ ] `ConnectionResetError` (connectionreseterror.md) - Closest sibling in meaning (peer gone); modifiers must remain distinct
- [ ] `open` / file-object vocabulary - The "pipe" word should sit comfortably beside the language's file/stream terminology

**Consistency rule:**

This is the one `ConnectionError` family member without the "connection" root in English — preserve that asymmetry rather than "fixing" it. The binding requirements are: the "error" word must be identical to `ConnectionError` and the whole exception corpus, and the "pipe" word must match how the target language's Unix/Linux literature names the shell pipe.


### Functional relationships

**This term works WITH:**

1. **`os.pipe()` / `subprocess` pipes + `BrokenPipeError`**: Writing after the reader exits:

```python
proc.stdin.write(data)  # raises BrokenPipeError if the child already exited
```

2. **`socket.sendall()` + `BrokenPipeError`**: The write-side twin of `ConnectionResetError`:

```python
try:
    conn.sendall(response)
except BrokenPipeError:
    pass  # client hung up; nothing to send to
```

**Common pairing:**

```python
# Feeding a child process that may stop reading at any time
import subprocess

proc = subprocess.Popen(
    ["head", "-n", "1"],
    stdin=subprocess.PIPE,
    text=True,
)

try:
    for line in ("alpha\n", "beta\n", "gamma\n"):
        proc.stdin.write(line)
        proc.stdin.flush()
except BrokenPipeError:
    print("Child stopped reading; that's fine")
finally:
    try:
        proc.stdin.close()
    except BrokenPipeError:
        pass
    proc.wait()
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

### HARD

- No direct equivalent in some languages
- May need compound term or explanation
- Concept doesn't exist universally
- **AI confidence should be MEDIUM, human review recommended**

### Why HARD for `BrokenPipeError`

- "Pipe" is a Unix cultural metaphor; languages without a localized Unix tradition have no obvious canonical word
- Most languages have several tube/conduit/channel words, and the wrong one (smoking pipe) is ridiculous
- Unique family position: must share the "error" suffix but must NOT adopt the "connection" root
- The established localization (if any) lives in each language's Unix/Linux documentation, which must be consulted

**For this term:** HARD

**Rationale:** Unlike its siblings, both content words ("broken," "pipe") are open choices, and the central noun is a borrowed metaphor rather than a plain technical term. Where a language community already localizes "broken pipe," match it; where it does not, a human linguist should choose the conduit word deliberately.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures SEVERED DATA CONDUIT (write channel with no reader), not smoking/music/literal plumbing?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Recognizable to developers who know the language's Unix "pipe" terminology?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun with adjective/participle)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Ends with the same "error" word as `ConnectionError` and the whole exception corpus?
- [ ] Does NOT import the family's "connection" root (mirrors English's deliberate omission)?
- [ ] "Pipe" word matches the language's rendering of the shell pipe concept?

### 4. Usability

- [ ] Short enough (1-3 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional (no comical smoking-pipe imagery)?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs (especially RTL)?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: BrokenPipeError
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
