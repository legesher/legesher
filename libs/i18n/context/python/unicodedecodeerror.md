# Python Builtin: `UnicodeDecodeError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`UnicodeDecodeError` is a built-in exception raised when **decoding fails: converting bytes into text (bytes → str)** — for example, reading a UTF-8 file as ASCII. It is the Unicode error users hit most often, and it carries `encoding`, `object`, `start`, `end`, and `reason` attributes pinpointing exactly which bytes could not be decoded.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Decoding bytes with the wrong codec raises UnicodeDecodeError
data = b'caf\xe9'        # "café" encoded as Latin-1
data.decode('utf-8')     # Raises UnicodeDecodeError: 'utf-8' codec
                         # can't decode byte 0xe9 in position 3
```

**What this does:** The byte `0xe9` is how Latin-1 stores "é", but it is not a valid UTF-8 sequence. Asking the UTF-8 codec to decode it fails: the bytes cannot be interpreted as text under that encoding, so Python raises `UnicodeDecodeError`.

### Example 2: Common Pattern

```python
# The classic case: reading a file with the wrong assumed encoding
raw = open("data.txt", "rb").read()

try:
    text = raw.decode("utf-8")
except UnicodeDecodeError:
    # Fallback strategy 1: try a legacy encoding
    # (latin-1 maps every possible byte, so it never raises —
    #  but it may produce wrong characters if the guess is wrong)
    text = raw.decode("latin-1")

# Fallback strategy 2: keep the right codec, substitute bad bytes
text = raw.decode("utf-8", errors="replace")   # bad bytes become U+FFFD �
```

**What this does:** Files carry no encoding label, so programs guess — and a wrong guess raises `UnicodeDecodeError` at the first offending byte. The two standard recoveries are trying another codec or passing an `errors=` handler (`"replace"`, `"ignore"`, `"backslashreplace"`) that substitutes instead of raising. The real fix is always to learn the file's true encoding.

### Example 3: Edge Case

```python
# The exception's attributes pinpoint the failure
try:
    b'caf\xe9 au lait'.decode('ascii')
except UnicodeDecodeError as exc:
    print(exc.encoding)   # 'ascii'      — the codec that failed
    print(exc.object)     # b'caf\xe9 au lait'  — the BYTES being decoded
    print(exc.start)      # 3            — index of the first bad byte
    print(exc.end)        # 4            — one past the last bad byte
    print(exc.reason)     # 'ordinal not in range(128)'
```

**What this shows:** `UnicodeDecodeError` is diagnostic, not just a failure signal. `object` holds the original bytes (note: bytes, not text — decoding is the bytes → str direction), and `start`/`end` bracket the exact failing range, which is what custom error handlers and repair tools use.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `UnicodeError` - Direct parent class; base of the Unicode error family
2. `UnicodeEncodeError` - Mirror twin; the OPPOSITE direction (text → bytes failed)
3. `UnicodeTranslateError` - Sibling; character-mapping translation failed
4. `ValueError` - Grandparent class; general "right type, bad value" error

**Pattern rule:** Exception classes should use noun forms, typically ending with "Error" in English. Translations should convey the error type, the Unicode domain (a proper noun, kept as a name), and the direction qualifier — decoding, the bytes → text direction.


---

## Etymology (Brief)

**English Origin:** Coined proper noun + Latin compound

**Root meaning:** "Unicode" is the coined name (circa 1987, from "unique, universal, uniform" encoding) of the character standard. "Decode" is Latin "de-" (reversal, undoing) + "code" (from "codex") — literally to un-code, to recover the original meaning from an encoded form. "Error" derives from Latin "error" (wandering, mistake).

**Why Python uses this:** Decoding is the established term for interpreting stored or transmitted bytes back into characters. The name states the failing operation exactly: a Unicode decode — bytes into text — did not succeed.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`UnicodeDecodeError` is raised when Python cannot convert a byte sequence into a text string. The direction is the defining fact: **decoding goes from bytes to str** — from raw octets on disk or the network to Unicode characters a program can treat as text. Every call to `bytes.decode()`, every text-mode `open()` read, and every implicit decode in libraries funnels through a codec, and when that codec meets bytes that are invalid for it, this exception stops the conversion.

It is the Unicode error programmers meet most, because the world's data is full of mislabeled and legacy-encoded files. The canonical scenario: a file written as UTF-8 (or Windows cp1252, or Latin-1) is read with a different assumed encoding. The codec hits a byte or byte sequence that has no interpretation under its rules — `0xe9` alone is not UTF-8; `0xff` cannot start a UTF-8 sequence — and raises with the codec name, the offending range, and a reason string.

Recovery options are well-trodden. `errors="replace"` substitutes U+FFFD (�) for undecodable bytes; `errors="ignore"` drops them; `"backslashreplace"` keeps them visible as escapes. Trying a fallback codec is common, with one important asymmetry worth knowing: Latin-1 assigns a character to every possible byte, so decoding as Latin-1 never raises — it just may produce the wrong characters (mojibake) if the guess is wrong. The exception's attributes (`encoding`, `object` — the bytes, `start`, `end`, `reason`) make precise reporting and custom repair possible.

**Key behaviors:**

1. **Direction is bytes → str:** Raised only while decoding — interpreting bytes as text. The mirror exception for the opposite direction (str → bytes) is `UnicodeEncodeError`. Confusing the two directions is the single most common mistake in this family.

2. **Carries the failing bytes and range:** `object` is the `bytes` being decoded; `start`/`end` index the invalid range; `encoding` and `reason` say which codec failed and why. Error handlers registered via `codecs.register_error` receive these to implement custom substitution.

3. **Avoidable with `errors=` handlers:** `decode(..., errors="replace"/"ignore"/"backslashreplace")` converts the failure into substitution instead of an exception — a pragmatic tool, though identifying the true encoding is the real fix.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (proper noun domain + operation qualifier + error type)
- **Action vs State:** STATE - describes an error condition, not an action
- **Temporal aspect:** Instantaneous - occurs at the first undecodable byte

### Recommended Form

**Primary recommendation:** Keep "Unicode" exactly as the base class `UnicodeError` renders it (proper noun: untranslated or established transliteration), translate "decode" with the target language's standard decoding term, and keep the family's error word. The decode word must unambiguously mean the **bytes → text** direction and must be the exact counterpart of the encode word used in `UnicodeEncodeError` — most languages express decode as "un-encode" via a reversal prefix or particle, which keeps the pair visibly linked.

**Forms to AVOID:**

- ❌ The encode word, or any word implying text → bytes - this reverses the direction and is the classic error
- ❌ Semantic translation of "Unicode" - it is a proper noun; see the base class brief
- ❌ Generic "conversion error" - loses both the direction and the domain

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES — two issues: the proper noun, and the direction of "decode."

**Identify the CORRECT treatment for Python:**

- ❌ Treatment 1: Translating "Unicode" semantically ("universal code") - it is the PROPER NOUN naming the character standard; keep it untranslated or transliterated, exactly as in `UnicodeError`
- ❌ Meaning 2: "Decode" as deciphering secrets or interpreting hidden meaning ("decode her expression")
- ✅ Meaning 3: **"Decode" as the technical operation converting BYTES INTO TEXT** (bytes → str), the reverse of encoding

**Example:**

English "decode" can mean:

1. "The spy decoded the secret message" (cryptography, everyday) ❌
2. "I can't decode his intentions" (figurative interpretation) ❌
3. `b'caf\xc3\xa9'.decode('utf-8')` returns `'café'` ✅ **This is the Python meaning: bytes in, text out**

**Your translation must (a) keep "Unicode" as a name, and (b) use a decode word that unmistakably means bytes → text and mirrors the encode word chosen for `UnicodeEncodeError`. If your language builds decode as "un-encode," use it — the visible pairing prevents direction confusion.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `UnicodeDecodeError`, check these translations:**

- [ ] `UnicodeError` - Parent class; the Unicode form and error word must match exactly
- [ ] `UnicodeEncodeError` - Mirror twin; decode/encode words must be an unmistakable directional pair
- [ ] `UnicodeTranslateError` - Sibling; same Unicode anchor and error suffix
- [ ] `bytes` - The source type of decoding; documentation vocabulary should align
- [ ] `str` - The result type of decoding; same requirement

**Consistency rule:**

Three locks: (1) the Unicode form is byte-for-byte identical to the base class; (2) the decode word is the exact directional counterpart of the encode word in `UnicodeEncodeError` — ideally the same root with an "undo" marker; (3) the error word and structure match the whole exception family.


### Functional relationships

**This term works WITH:**

1. **`bytes.decode()` + `UnicodeDecodeError`**: The operation that raises it.

```python
text = raw.decode('utf-8')  # may raise UnicodeDecodeError
```

2. **`open()` in text mode + `UnicodeDecodeError`**: The most common real-world source.

```python
with open("legacy.txt", encoding="utf-8") as f:
    content = f.read()  # may raise UnicodeDecodeError mid-read
```

**Common pairing:**

```python
# UnicodeDecodeError in a robust file reader
def read_text(path):
    raw = open(path, "rb").read()
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError as exc:
        print(f"not UTF-8: byte at {exc.start} ({exc.reason})")
        return raw.decode("cp1252"), "cp1252"   # common Windows fallback

# Direction check: decode is bytes -> str
assert isinstance(b'abc'.decode('ascii'), str)

# The errors= escape hatch
b'caf\xe9'.decode('utf-8', errors='replace')          # 'caf�'
b'caf\xe9'.decode('utf-8', errors='backslashreplace') # 'caf\\xe9'

# Caught by both ancestors
try:
    b'\xff'.decode('utf-8')
except UnicodeError:
    pass  # parent catches it
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `UnicodeDecodeError`

- The decode/encode direction pair is reversed by translators constantly — the single highest-risk error in this family
- The decode word choice must coordinate with three other terms (base class, encode twin, translate sibling)
- Some languages split between a transliterated decode word (developer usage) and a native coinage (official glossaries)

**For this term:** MEDIUM

**Rationale:** Every component has an established rendering; the difficulty is coordination and direction. Verify the direction mechanically — decode is what `bytes.decode()` does, bytes in, text out — and lock the decode word as the mirror of the encode word before finalizing either.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Decode word means bytes → text (the `bytes.decode()` direction), not the reverse?
- [ ] "Unicode" treated as a proper noun, identical to the base class form?
- [ ] Clearly indicates an ERROR occurred?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Unicode form byte-for-byte identical across all four Unicode exceptions?
- [ ] Decode word is the visible mirror of the encode word in `UnicodeEncodeError`?
- [ ] Same error word and structure as the rest of the exception family?

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
term: UnicodeDecodeError
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
