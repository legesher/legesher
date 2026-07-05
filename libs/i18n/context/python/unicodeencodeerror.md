# Python Builtin: `UnicodeEncodeError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`UnicodeEncodeError` is a built-in exception raised when **encoding fails: converting text into bytes (str → bytes)** — for example, encoding "café" to ASCII, which has no byte for "é". It is the mirror of `UnicodeDecodeError` (the bytes → text direction) and carries `encoding`, `object`, `start`, `end`, and `reason` attributes pinpointing exactly which characters could not be encoded.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Encoding a character the target codec cannot represent
text = "café"
text.encode('ascii')  # Raises UnicodeEncodeError: 'ascii' codec
                      # can't encode character '\xe9' in position 3
```

**What this does:** ASCII defines bytes only for 128 characters, and "é" (U+00E9) is not one of them. Converting the string to ASCII bytes therefore fails at position 3, and Python raises `UnicodeEncodeError` naming the codec, the character, and the position.

### Example 2: Common Pattern

```python
# Producing output for a system that only accepts a narrow encoding
text = "naïve café"

try:
    payload = text.encode('ascii')
except UnicodeEncodeError:
    # Choose a lossy-but-explicit fallback
    payload = text.encode('ascii', errors='replace')

print(payload)  # b'na?ve caf?'  — unencodable characters became '?'

# Other handlers, other trade-offs:
text.encode('ascii', errors='ignore')            # b'nave caf'  (drops them)
text.encode('ascii', errors='xmlcharrefreplace') # b'na&#239;ve caf&#233;'
```

**What this does:** When a legacy protocol, database column, or filename rule demands a narrow encoding, characters outside it must be substituted, dropped, or escaped. The `errors=` handlers make that policy explicit; without one, `UnicodeEncodeError` stops the conversion at the first unencodable character.

### Example 3: Edge Case

```python
# The attributes pinpoint the failure — object is the STR being encoded
try:
    "π = 3.14159".encode('latin-1')
except UnicodeEncodeError as exc:
    print(exc.encoding)  # 'latin-1'
    print(exc.object)    # 'π = 3.14159'   — the text (str), not bytes
    print(exc.start)     # 0
    print(exc.end)       # 1
    print(exc.reason)    # 'ordinal not in range(256)'

# UTF-8 can encode every character — with one exception: lone surrogates
"any text: ñ, 中, नमस्ते".encode('utf-8')  # always succeeds
"\ud800".encode('utf-8')  # Raises UnicodeEncodeError: surrogates not allowed
```

**What this shows:** In the encode direction, `object` holds the source *string* (contrast the decode twin, where it holds bytes). The second half corrects a common overstatement: UTF-8 encodes all valid Unicode text, so `UnicodeEncodeError` with a UTF-8 target is nearly impossible — except for lone surrogate code points, which are not valid in any UTF-8 byte stream.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `UnicodeError` - Direct parent class; base of the Unicode error family
2. `UnicodeDecodeError` - Mirror twin; the OPPOSITE direction (bytes → text failed)
3. `UnicodeTranslateError` - Sibling; character-mapping translation failed
4. `ValueError` - Grandparent class; general "right type, bad value" error

**Pattern rule:** Exception classes should use noun forms, typically ending with "Error" in English. Translations should convey the error type, the Unicode domain (a proper noun, kept as a name), and the direction qualifier — encoding, the text → bytes direction.


---

## Etymology (Brief)

**English Origin:** Coined proper noun + Latin compound

**Root meaning:** "Unicode" is the coined name (circa 1987, from "unique, universal, uniform" encoding) of the character standard. "Encode" is "en-" (to put into) + "code" (from Latin "codex") — to put information into coded form. "Error" derives from Latin "error" (wandering, mistake).

**Why Python uses this:** Encoding is the established term for representing characters as bytes for storage or transmission. The name states the failing operation exactly: a Unicode encode — text into bytes — did not succeed.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`UnicodeEncodeError` is raised when Python cannot convert a text string into bytes under a given codec. The direction is the defining fact: **encoding goes from str to bytes** — from Unicode characters in memory to the raw octets that files, sockets, and databases actually store. Every `str.encode()` call and every text-mode write funnels through a codec, and when the codec meets a character it has no byte representation for, this exception stops the conversion.

The failure is always about a narrow target. Unicode defines more than 150,000 characters; ASCII has bytes for 128, Latin-1 for 256, and the many national codecs (cp1252, shift_jis, gbk) each cover their own slice. Encode "café" to ASCII and the codec fails at "é"; encode "π" to Latin-1 and it fails at position 0. UTF-8, by design, can encode all valid Unicode text — which is why modern code that standardizes on UTF-8 rarely sees this exception (the corner case: lone surrogate code points like U+D800, which are invalid in interchange and refused even by UTF-8).

Like its decode twin, the exception is diagnostic: `encoding` names the codec, `object` holds the source string (a `str` here — the twin holds `bytes`), `start`/`end` bracket the unencodable characters, and `reason` explains. The `errors=` handlers (`"replace"`, `"ignore"`, `"xmlcharrefreplace"`, `"backslashreplace"`) convert the failure into an explicit substitution policy when lossy output is acceptable.

**Key behaviors:**

1. **Direction is str → bytes:** Raised only while encoding — representing text as bytes. The mirror exception for the opposite direction (bytes → str) is `UnicodeDecodeError`. Keeping the two directions straight is the critical translation requirement.

2. **Raised by narrow target codecs:** ASCII, Latin-1, and national codecs cover subsets of Unicode; characters outside the subset raise. UTF-8 encodes everything except lone surrogates, so standardizing on UTF-8 nearly eliminates this exception.

3. **Carries the failing text and range:** `object` is the source `str`; `start`/`end` index the unencodable characters; `encoding` and `reason` complete the diagnosis. Custom handlers registered with `codecs.register_error` receive these to implement application-specific substitution.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (proper noun domain + operation qualifier + error type)
- **Action vs State:** STATE - describes an error condition, not an action
- **Temporal aspect:** Instantaneous - occurs at the first unencodable character

### Recommended Form

**Primary recommendation:** Keep "Unicode" exactly as the base class `UnicodeError` renders it (proper noun: untranslated or established transliteration), translate "encode" with the target language's standard encoding term, and keep the family's error word. The encode word must unambiguously mean the **text → bytes** direction and must be the exact counterpart of the decode word used in `UnicodeDecodeError` — ideally the plain root of which decode is the "undo" form.

**Forms to AVOID:**

- ❌ The decode word, or any word implying bytes → text - this reverses the direction and is the classic error
- ❌ Semantic translation of "Unicode" - it is a proper noun; see the base class brief
- ❌ Words meaning "encrypt" - encoding is representation, not secrecy; several languages have distinct terms and mixing them is a real technical error

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES — two issues: the proper noun, and what "encode" does (and does not) mean.

**Identify the CORRECT treatment for Python:**

- ❌ Treatment 1: Translating "Unicode" semantically ("universal code") - it is the PROPER NOUN naming the character standard; keep it untranslated or transliterated, exactly as in `UnicodeError`
- ❌ Meaning 2: "Encode" as encrypting or hiding information (secrecy)
- ✅ Meaning 3: **"Encode" as the technical operation converting TEXT INTO BYTES** (str → bytes) — an open, reversible representation, the reverse of decoding

**Example:**

English "encode" can suggest:

1. "The message was encoded so enemies couldn't read it" (encryption) ❌
2. "Cultural values are encoded in the ritual" (figurative embedding) ❌
3. `'café'.encode('utf-8')` returns `b'caf\xc3\xa9'` ✅ **This is the Python meaning: text in, bytes out**

**Your translation must (a) keep "Unicode" as a name, (b) use an encode word that unmistakably means text → bytes and is the visible counterpart of the decode word in `UnicodeDecodeError`, and (c) avoid encryption vocabulary.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `UnicodeEncodeError`, check these translations:**

- [ ] `UnicodeError` - Parent class; the Unicode form and error word must match exactly
- [ ] `UnicodeDecodeError` - Mirror twin; encode/decode words must be an unmistakable directional pair
- [ ] `UnicodeTranslateError` - Sibling; same Unicode anchor and error suffix
- [ ] `str` - The source type of encoding; documentation vocabulary should align
- [ ] `bytes` - The result type of encoding; same requirement

**Consistency rule:**

Three locks: (1) the Unicode form is byte-for-byte identical to the base class; (2) the encode word is the exact directional counterpart of the decode word in `UnicodeDecodeError` — ideally the plain root of which decode is the marked "undo" form; (3) the error word and structure match the whole exception family.


### Functional relationships

**This term works WITH:**

1. **`str.encode()` + `UnicodeEncodeError`**: The operation that raises it.

```python
payload = text.encode('ascii')  # may raise UnicodeEncodeError
```

2. **Text-mode writes + `UnicodeEncodeError`**: Encoding happens implicitly on output.

```python
with open("out.txt", "w", encoding="ascii") as f:
    f.write("café")  # raises UnicodeEncodeError at the write
```

**Common pairing:**

```python
# UnicodeEncodeError when interfacing with a narrow legacy system
def to_legacy_bytes(text: str) -> bytes:
    try:
        return text.encode("cp1252")
    except UnicodeEncodeError as exc:
        bad = exc.object[exc.start:exc.end]
        print(f"cannot represent {bad!r} in cp1252 ({exc.reason})")
        return text.encode("cp1252", errors="replace")

print(to_legacy_bytes("café"))   # b'caf\xe9' — fits in cp1252
print(to_legacy_bytes("café 中")) # replacement path for '中'

# Direction check: encode is str -> bytes
assert isinstance("abc".encode("ascii"), bytes)

# Round trip: encode and decode are inverse directions
original = "naïve"
assert original.encode("utf-8").decode("utf-8") == original

# Caught by both ancestors
try:
    "é".encode("ascii")
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

### Why MEDIUM for `UnicodeEncodeError`

- The encode/decode direction pair is reversed by translators constantly — the single highest-risk error in this family
- Several languages have adjacent encryption vocabulary that must be kept out
- The encode word choice must coordinate with three other terms (base class, decode twin, translate sibling)

**For this term:** MEDIUM

**Rationale:** Every component has an established rendering; the difficulty is coordination and direction. Verify the direction mechanically — encode is what `str.encode()` does, text in, bytes out — and finalize the encode and decode words together as a pair, never separately.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Encode word means text → bytes (the `str.encode()` direction), not the reverse?
- [ ] "Unicode" treated as a proper noun, identical to the base class form?
- [ ] No encryption/secrecy connotation in the encode word?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Unicode form byte-for-byte identical across all four Unicode exceptions?
- [ ] Encode word is the visible mirror of the decode word in `UnicodeDecodeError`?
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
term: UnicodeEncodeError
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
