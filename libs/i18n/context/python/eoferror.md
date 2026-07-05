# Python Builtin: `EOFError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`EOFError` is a built-in exception raised when `input()` hits end-of-file (EOF) without reading any data - the input stream ended before a line could be read. It signals "there is no more input," typically because the user pressed Ctrl-D (Unix) or Ctrl-Z+Enter (Windows), or because piped/redirected input ran out.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# input() raises EOFError when the input stream ends with no data
# Trigger it interactively with Ctrl-D (Unix) or Ctrl-Z then Enter (Windows),
# or by piping empty input:  echo -n "" | python script.py
try:
    line = input("Enter text: ")
except EOFError:
    print("No more input available")
```

**What this does:** `input()` normally waits for a line of text. If the stream ends before any data arrives - the user signals end-of-input, or redirected input is exhausted - Python raises `EOFError` instead of returning a value.

### Example 2: Common Pattern

```python
# Read all lines from standard input until EOF
lines = []
while True:
    try:
        lines.append(input())
    except EOFError:
        break  # Input exhausted - this is the normal way the loop ends

print(f"Read {len(lines)} lines")
```

**What this does:** Programs that consume piped input (`cat data.txt | python tool.py`) loop over `input()` until `EOFError` says the stream is finished. Here the exception acts as an expected end-of-data signal that cleanly terminates the loop, not as a malfunction.

### Example 3: Edge Case

```python
# File reads do NOT raise EOFError - they return empty results
with open("data.txt") as f:
    f.read()                 # Consume the whole file
    print(repr(f.read()))    # '' - empty string at EOF, no exception
    print(repr(f.readline()))  # '' - same for readline()

# But pickle raises EOFError on a truncated or empty stream
import io
import pickle

pickle.load(io.BytesIO(b""))  # Raises EOFError: Ran out of input
```

**What this shows:** The asymmetry that confuses beginners: `read()` and `readline()` on file objects signal EOF by returning empty strings, never by raising `EOFError`. The exception is reserved for operations that *need* data to make progress - `input()` needs a line, `pickle.load()` needs a complete serialized object - and cannot express "nothing" as a return value.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `KeyboardInterrupt` - The other exception commonly raised while waiting at an `input()` prompt (user pressed Ctrl-C instead of Ctrl-D)
2. `StopIteration` - Similar "no more items" signal, but for iterators rather than input streams
3. `ValueError` - Raised when `input()` data arrives but fails a later conversion like `int()`
4. `OSError` - Raised for actual I/O failures (disk, permissions), distinct from a stream simply ending

**Pattern rule:** Exception classes should use noun forms, typically ending with "Error" in English. Translations should convey both the error type and the specific problem domain (end-of-file, key, index, etc.).


---

## Etymology (Brief)

**English Origin:** Acronym + Latin-derived

**Root meaning:** "EOF" abbreviates "End Of File," a term inherited from early operating systems and the C language, where a special marker or sentinel value indicates that a data stream has no more content. "File" traces to Latin "filum" (thread) - documents strung on a wire for keeping. "Error" derives from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** Python inherited the EOF acronym from the C/Unix tradition its I/O model is built on. `EOFError` names the condition precisely: an operation expected more data, but the stream had reached its end. The acronym is kept because "EOF" is universal systems vocabulary - the same condition Ctrl-D produces in a Unix terminal.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`EOFError` is raised when an operation that requires data reaches the end of its input stream without obtaining any. The primary source is `input()`: it reads one line from standard input, and if the stream ends before any character arrives - the user pressed Ctrl-D/Ctrl-Z, or a pipe or redirected file ran out - there is no line to return, so Python raises `EOFError`. A few other consumers of framed data behave the same way; most notably, `pickle.load()` raises `EOFError` ("Ran out of input") when its stream ends mid-object or is empty.

The key distinction to internalize is *when EOF is an exception versus a value*. Plain file reads (`f.read()`, `f.readline()`) can represent "no more data" in-band: they return an empty string (or empty bytes), and callers check for it. `input()` cannot - an empty string is a legitimate result (the user pressed Enter on a blank line) - so end-of-stream must be signaled out-of-band, as an exception. This is why the same physical event (a stream ending) surfaces as `''` in one API and as `EOFError` in another.

In practice, `EOFError` is often *expected* rather than exceptional. Command-line filters loop on `input()` and treat the exception as the natural end of their work. Interactive programs catch it alongside `KeyboardInterrupt` to exit politely when the user closes the input. Treating it as a normal boundary condition - and never confusing it with file corruption or an I/O failure - is the mark of idiomatic Python.

**Key behaviors:**

1. **Raised by `input()` at end of stream:** If standard input ends before any data is read, `input()` raises `EOFError`. If the user types characters and then the stream ends, behavior differs from an ordinary blank line - the exception fires only when *no* data was read for that call.

2. **Not raised by ordinary file reads:** `f.read()` and `f.readline()` return `''` (or `b''`) at end of file instead of raising. Code that expects `EOFError` from file objects has a bug; check for empty results instead.

3. **Raised by framed-data readers like `pickle`:** `pickle.load()` (and similar protocols that need complete records) raise `EOFError` when the stream ends before a full object could be read - covering both empty and truncated input.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (error type + problem domain: end of the data stream)
- **Action vs State:** STATE - describes a condition (input exhausted), not an action
- **Temporal aspect:** Instantaneous - occurs at the moment a read finds no data

### Recommended Form

**Primary recommendation:** Expand the acronym: translate "end of file" fully rather than transliterating "EOF," then append your language's standard "error" word used across the exception family. "EOF" is opaque outside English-centric systems culture; "end of file/input" is self-explanatory.

**Forms to AVOID:**

- ❌ Transliterating the acronym ("ErrorEOF"-style compounds keeping "EOF" verbatim) - meaningless to readers who don't know Unix lore; acronyms rarely survive translation
- ❌ "File error" without "end" - suggests a broken or unreadable file; the file/stream is fine, it simply ended
- ❌ Verb forms ("the file ended" as a participle phrase) - exceptions are noun compounds, and this also loses the error-family pattern

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: The end/purpose of something abstract ("to what end?")
- ❌ Meaning 2: The program ending or being terminated
- ❌ Meaning 3: A damaged, missing, or unreadable file (that's `OSError`/`FileNotFoundError` territory)
- ✅ Meaning 4: **INPUT STREAM EXHAUSTED** - a read needed data, but the file/stream had reached its end

**Example:**

English "end of file" in context:

1. "The end justifies the means" (purpose) ❌
2. "The program ended" (termination - that's `SystemExit`) ❌
3. "The file is corrupted" (damage - that's an I/O error) ❌
4. `input()` at an exhausted stream raises `EOFError` ✅ **This is the Python meaning**

**Your translation should capture meaning #4: the data ran out. Nothing is broken - the stream simply has no more content, and an operation that required data must report that. Note that "file" here really means any input stream, including a terminal or pipe.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `EOFError`, check these translations:**

- [ ] `input` - The builtin that raises `EOFError`; their documentation vocabulary must match
- [ ] `open` - File terminology ("file", "stream") must be consistent across I/O terms
- [ ] `KeyboardInterrupt` - Commonly caught alongside `EOFError` at input prompts; both must be recognizable event/error names
- [ ] `StopIteration` - The parallel "no more items" signal; keep "exhaustion" vocabulary coherent
- [ ] `ValueError` - The error family pattern (same error word, same compound order) must match

**Consistency rule:**

All exception classes ending in "Error" should use the same structure in translations. Whatever compound pattern `EOFError` uses must match `ValueError` and `TypeError` - same error word, same compound order. The word chosen for "file" must be the same one used in `open()` documentation.


### Functional relationships

**This term works WITH:**

1. **`input()` + `EOFError`**: The canonical producer of this exception

```python
try:
    line = input()
except EOFError:
    line = None  # No more input
```

2. **`while` loops + `EOFError`**: Stream-consuming loops end via this exception

```python
while True:
    try:
        process(input())
    except EOFError:
        break
```

**Common pairing:**

```python
# Reading numbers from piped input until it runs out
total = 0
while True:
    try:
        total += int(input())
    except EOFError:
        break          # Normal end of data
    except ValueError:
        continue       # A line that wasn't a number - different problem

print(f"total = {total}")

# Interactive prompt: handle both ways a user can bail out
try:
    answer = input("Continue? [y/n] ")
except EOFError:
    answer = "n"       # Ctrl-D: treat as "no"
except KeyboardInterrupt:
    raise SystemExit(130)  # Ctrl-C: exit immediately

# Contrast: file objects signal EOF with empty results, not exceptions
with open("log.txt") as f:
    while True:
        line = f.readline()
        if line == "":   # EOF reached - no EOFError here
            break
        handle(line)
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `EOFError`

- The source term is an acronym, which must be expanded, not transliterated
- Three-part compound (end + file + error) can grow long in some languages
- "File" vs "input/stream" vocabulary choice needs care - the stream is often a terminal, not a file
- Must maintain consistency with the rest of the "Error" family and with `input`/`open` terminology

**For this term:** MEDIUM

**Rationale:** Every language can express "end of file" - most already have an established rendering from OS documentation - so the concept transfers well. The work is structural: expanding the acronym gracefully, keeping the compound short enough to type, and not drifting into "broken file" or "program ended" meanings.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures INPUT EXHAUSTED / STREAM ENDED (not file damage, not program termination)?
- [ ] Clearly indicates an ERROR-family exception (contains the family's error word)?
- [ ] Acronym expanded into real words of the target language?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Matches pattern of other exception translations (`ValueError`, `TypeError`)?
- [ ] "File" word matches `open()` documentation vocabulary?
- [ ] Coherent with `input` and `StopIteration` exhaustion vocabulary?

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
term: EOFError
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
