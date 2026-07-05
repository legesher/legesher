# Python Builtin: `UnicodeError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`UnicodeError` is the built-in base class for exceptions raised when Unicode encoding, decoding, or translating fails. It subclasses `ValueError`, and in practice you almost always see one of its three specific subclasses — `UnicodeDecodeError` (bytes → text failed), `UnicodeEncodeError` (text → bytes failed), or `UnicodeTranslateError` (character mapping failed) — which carry `encoding`, `object`, `start`, `end`, and `reason` attributes describing exactly what went wrong.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Catching UnicodeError catches its specific subclasses
data = b'\xff\xfe'
try:
    data.decode('utf-8')
except UnicodeError as exc:
    print(type(exc).__name__)  # UnicodeDecodeError
```

**What this does:** The invalid byte `0xff` cannot start a UTF-8 sequence, so decoding raises `UnicodeDecodeError` — and the `except UnicodeError` clause catches it because the specific error is a subclass. This is how `UnicodeError` appears in real code: as the family-level handler.

### Example 2: Common Pattern

```python
# One handler for both directions of text conversion
def transcode(raw: bytes, source: str, target: str) -> bytes:
    try:
        return raw.decode(source).encode(target)
    except UnicodeError as exc:
        print(f"Transcoding failed: {exc}")
        return b""

transcode(b'caf\xc3\xa9', 'utf-8', 'ascii')  # encode step fails ('é' not in ASCII)
transcode(b'caf\xe9', 'utf-8', 'latin-1')    # decode step fails (invalid UTF-8)
```

**What this does:** A transcoding pipeline can fail in either direction: while decoding bytes into text or while encoding text back into bytes. Catching `UnicodeError` handles both with one clause — useful when the recovery (log and skip, substitute, abort) is the same regardless of direction.

### Example 3: Edge Case

```python
# The hierarchy: UnicodeError sits under ValueError
print(issubclass(UnicodeError, ValueError))          # True
print(issubclass(UnicodeDecodeError, UnicodeError))  # True
print(issubclass(UnicodeEncodeError, UnicodeError))  # True
print(issubclass(UnicodeTranslateError, UnicodeError))  # True

# So an except ValueError clause catches Unicode failures too
try:
    b'\x80abc'.decode('utf-8')
except ValueError as exc:
    print(f"caught as ValueError: {type(exc).__name__}")  # UnicodeDecodeError

# The subclasses carry structured details
try:
    b'caf\xe9'.decode('utf-8')
except UnicodeError as exc:
    print(exc.encoding, exc.start, exc.end, exc.reason)
```

**What this shows:** `UnicodeError` subclasses `ValueError` — a malformed byte sequence is, conceptually, a bad value. Handlers written against `ValueError` therefore also catch Unicode failures, which can surprise programmers. The structured attributes (`encoding`, `object`, `start`, `end`, `reason`) let error handlers report or repair the exact failing range.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `UnicodeDecodeError` - Subclass; bytes → text conversion failed
2. `UnicodeEncodeError` - Subclass; text → bytes conversion failed
3. `UnicodeTranslateError` - Subclass; character-mapping translation failed
4. `ValueError` - Direct parent class; general "right type, bad value" error

**Pattern rule:** Exception classes should use noun forms, typically ending with "Error" in English. Translations should convey both the error type and the problem domain — here the domain is the Unicode character standard, which is a proper noun.


---

## Etymology (Brief)

**English Origin:** Coined proper noun (Latin roots) + Latin

**Root meaning:** "Unicode" was coined around 1987 (attributed to Joe Becker at Xerox) from "unique, universal, and uniform character encoding" — Latin "unus" (one) + "code" (from Latin "codex," book of laws). It is the trademarked name of the character standard maintained by the Unicode Consortium. "Error" derives from Latin "error" (wandering, mistake).

**Why Python uses this:** Python 3 text strings are sequences of Unicode code points, so failures in converting between text and bytes are literally failures involving the Unicode standard. The class names the standard directly, following the domain + "Error" convention.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`UnicodeError` is the base class for the family of exceptions raised when Python's text machinery fails: turning bytes into a string (decoding), turning a string into bytes (encoding), or mapping characters to other characters (translating). Python 3 draws a hard line between `str` (text: Unicode code points) and `bytes` (raw octets); every crossing of that line goes through a codec, and when a codec meets data it cannot handle, it raises one of the `UnicodeError` subclasses.

The hierarchy matters in both directions. Upward: `UnicodeError` subclasses `ValueError`, so generic `except ValueError:` handlers also catch Unicode failures — malformed text data is treated as a species of bad value. Downward: the three subclasses (`UnicodeDecodeError`, `UnicodeEncodeError`, `UnicodeTranslateError`) are what actually appear in tracebacks; the base class shows up mostly in `except UnicodeError:` clauses that want to handle any text-conversion failure uniformly.

The family carries structured diagnostics. The documented attributes — `encoding` (the codec name), `object` (the data being converted), `start` and `end` (the failing range), and `reason` (a human-readable explanation) — allow precise error messages and targeted recovery, and they are the interface that custom error handlers registered with `codecs.register_error` work against.

**Key behaviors:**

1. **Family base class:** `except UnicodeError:` catches `UnicodeDecodeError`, `UnicodeEncodeError`, and `UnicodeTranslateError`. Tracebacks almost always show a subclass; the base class is a handler-side name.

2. **Subclass of `ValueError`:** Handlers for `ValueError` also catch Unicode failures, since a byte sequence that cannot be decoded is a value problem, not a type problem.

3. **Structured attributes:** `encoding`, `object`, `start`, `end`, and `reason` describe the exact failure, enabling error reporting like "byte 0xe9 at position 3 is not valid ascii" and programmatic recovery over the failing range.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (proper noun domain + error type)
- **Action vs State:** STATE - describes an error condition, not an action
- **Temporal aspect:** Instantaneous - occurs at the moment a text conversion fails

### Recommended Form

**Primary recommendation:** Treat "Unicode" as a proper noun — the name of a specific standard — and keep it untranslated (Latin-script languages) or transliterated into the local script using the form already established in that language's technical writing. Translate only the error word natively. This is the opposite of the arithmetic exceptions, where native math vocabulary wins: proper nouns do not get semantic translation.

**Forms to AVOID:**

- ❌ Semantic translation of "Unicode" ("universal code" rendered word-for-word) - it is a name, not a description
- ❌ Inventing a new transliteration when the language already has one - use the established form
- ❌ Verb forms - exceptions are nouns, not actions

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES — and the central issue is proper-noun status, not polysemy.

**Identify the CORRECT treatment for Python:**

- ❌ Treatment 1: "Unicode" as a common noun meaning "a single code" (uni + code, read literally)
- ❌ Treatment 2: "Unicode" as a description to translate semantically ("universal character set" in native words)
- ✅ Treatment 3: **"Unicode" as a PROPER NOUN** — the trademarked name of the character standard maintained by the Unicode Consortium, kept untranslated or transliterated

**Example:**

The word "Unicode" in `UnicodeError`:

1. Is not "one code" as a literal phrase ❌
2. Is not a generic term for character encodings ❌
3. Names the specific standard that defines code points like U+00E9 ✅ **This is the Python meaning**

**Your translation should keep "Unicode" as a name — untranslated in Latin-script languages, transliterated with the established local form elsewhere — and translate only the "error" component natively. This rule anchors all four Unicode exception translations.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `UnicodeError`, check these translations:**

- [ ] `UnicodeDecodeError` - Subclass; must reuse this exact Unicode form + the pack's word for decoding
- [ ] `UnicodeEncodeError` - Subclass; must reuse this exact Unicode form + the pack's word for encoding
- [ ] `UnicodeTranslateError` - Subclass; must reuse this exact Unicode form + the pack's word for character translation
- [ ] `ValueError` - Parent class; the error word and structure must match
- [ ] `str` / `bytes` - The types whose boundary this family guards; documentation vocabulary should align

**Consistency rule:**

Whatever form of "Unicode" you choose (untranslated or a specific transliteration) must appear byte-for-byte identically in all four Unicode exception names. The subclass names are this name plus one qualifier word each — decode, encode, translate — so the base term is the anchor.


### Functional relationships

**This term works WITH:**

1. **`bytes.decode()` / `str.encode()` + `UnicodeError`**: The operations whose failures it groups.

```python
raw.decode('utf-8')    # may raise UnicodeDecodeError
text.encode('ascii')   # may raise UnicodeEncodeError
```

2. **`try`/`except` + `UnicodeError`**: Direction-agnostic handling.

```python
try:
    process(raw.decode(enc))
except UnicodeError:
    skip(raw)
```

**Common pairing:**

```python
# UnicodeError as the family-level guard in file handling
def read_text_lenient(path, encodings=("utf-8", "cp1252")):
    raw = open(path, "rb").read()
    for enc in encodings:
        try:
            return raw.decode(enc)
        except UnicodeError:
            continue
    return raw.decode("utf-8", errors="replace")  # last resort: substitute

# The hierarchy in one picture
for cls in (UnicodeDecodeError, UnicodeEncodeError, UnicodeTranslateError):
    print(cls.__name__, "->", cls.__mro__[1].__name__)  # all -> UnicodeError
print(UnicodeError.__mro__[1].__name__)                 # ValueError
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `UnicodeError`

- The proper-noun rule itself is simple, but applying it requires knowing each language's established transliteration (or that none exists)
- Mixed-script identifiers (Latin "Unicode" inside a non-Latin-script name) raise pack-level policy questions that need a deliberate decision
- The base term anchors three subclass names, so a wrong choice here propagates

**For this term:** MEDIUM

**Rationale:** There is no semantic translation problem — the name stays a name. The work is procedural: find the established local form of "Unicode," decide the script policy for the pack, and lock the anchor so the decode/encode/translate subclasses inherit it unchanged.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Treats "Unicode" as a proper noun (untranslated or established transliteration)?
- [ ] Direction-neutral (covers decode, encode, AND translate)?
- [ ] Clearly indicates an ERROR occurred?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Identical Unicode form reserved for all three subclasses?
- [ ] Same error word and structure as `ValueError`, `TypeError`?
- [ ] Script policy (Latin vs local script for the proper noun) matches pack-wide decisions?

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
- [ ] Mixed-script identifiers render properly in IDEs (especially RTL)?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: UnicodeError
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
