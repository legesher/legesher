# Python Builtin: `UnicodeTranslateError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** HARD

---

## Quick Summary

`UnicodeTranslateError` is a built-in exception raised when an error occurs during character translation — the `str.translate()` style of mapping characters to other characters within text (str → str), not natural-language translation and not encoding/decoding. It is the rarest member of the Unicode error family: the standard library almost never raises it, and its constructor takes `(object, start, end, reason)` with no encoding argument, since no codec is involved.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Constructing the exception shows its shape (no encoding argument)
err = UnicodeTranslateError("café", 3, 4, "no mapping for character")
print(err)  # can't translate character '\xe9' in position 3: no mapping for character
raise err
```

**What this does:** Unlike its encode/decode siblings, `UnicodeTranslateError` is built from just the text, the failing range, and a reason — there is no codec name because character translation happens entirely within text (str → str). Constructing one directly is the simplest honest demonstration, because ordinary Python code rarely triggers it.

### Example 2: Common Pattern

```python
# A strict translation table that refuses unmapped characters
class StrictTable(dict):
    def __missing__(self, code_point):
        raise UnicodeTranslateError(
            chr(code_point), 0, 1, "no mapping defined"
        )

table = StrictTable({ord('a'): ord('@')})

print("aaa".translate(table))  # '@@@'
"abc".translate(table)         # Raises UnicodeTranslateError on 'b'
```

**What this does:** `str.translate()` looks up each character's code point in the table. A `dict` subclass with `__missing__` can enforce completeness: any character without a mapping raises `UnicodeTranslateError`, aborting the translation. (By default, `str.translate()` silently copies unmapped characters through — strictness must be built, which is exactly when this exception becomes useful.)

### Example 3: Edge Case

```python
# Hierarchy and the missing-encoding quirk
print(issubclass(UnicodeTranslateError, UnicodeError))  # True
print(issubclass(UnicodeTranslateError, ValueError))    # True

try:
    "abc".translate(StrictTable({ord('a'): ord('@')}))
except UnicodeTranslateError as exc:
    print(repr(exc.object))  # 'b' — the text involved (a str)
    print(exc.start, exc.end)  # 0 1
    print(exc.reason)        # 'no mapping defined'
    print(exc.encoding)      # None — no codec participates in translation

# Contrast: LookupError from a table is swallowed, not propagated
class LenientTable(dict):
    def __missing__(self, code_point):
        raise LookupError(code_point)

print("abc".translate(LenientTable({ord('a'): ord('@')})))  # '@bc'
```

**What this shows:** The exception has the family's diagnostic attributes (`object`, `start`, `end`, `reason`) but its `encoding` attribute is `None` — structural proof that translation is not an encoding operation. The contrast case shows why the class exists: `str.translate()` treats `LookupError` as "no mapping, copy the character through," so a table that wants to *fail* must raise something else — this exception is the designated choice.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `UnicodeError` - Direct parent class; base of the Unicode error family
2. `UnicodeDecodeError` - Sibling; bytes → text conversion failed
3. `UnicodeEncodeError` - Sibling; text → bytes conversion failed
4. `ValueError` - Grandparent class; general "right type, bad value" error

**Pattern rule:** Exception classes should use noun forms, typically ending with "Error" in English. Translations should convey the error type, the Unicode domain (a proper noun, kept as a name), and the operation qualifier — character translation, meaning str → str mapping, not natural-language translation.


---

## Etymology (Brief)

**English Origin:** Coined proper noun + Latin compound

**Root meaning:** "Unicode" is the coined name (circa 1987, from "unique, universal, uniform" encoding) of the character standard. "Translate" comes from Latin "translatus," past participle of "transferre" — "carried across." In computing it retains the general carrying-across sense: mapping items from one form to another (address translation, character translation), not specifically between human languages. "Error" derives from Latin "error" (wandering, mistake).

**Why Python uses this:** The operation `str.translate()` maps each character to a replacement (another character, a string, or deletion). Python names its failure with the same verb: an error during Unicode character translation.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`UnicodeTranslateError` signals a failure during character translation: the `str.translate()` operation that maps characters to other characters (or to strings, or to deletion) within text. Unlike encoding and decoding, no bytes and no codec are involved — the operation is str → str throughout. That is visible in the exception's own structure: its constructor takes `(object, start, end, reason)` with no encoding argument, and its `encoding` attribute is `None`.

Honesty requires saying how rare this exception is. `str.translate()` is deliberately lenient — characters missing from the table are copied through unchanged, and even a table whose lookup raises `LookupError` is treated as "no mapping" rather than an error. CPython's standard library has essentially no ordinary code path that raises `UnicodeTranslateError`; it exists as part of the codec error-handling machinery (custom error handlers registered with `codecs.register_error` can receive it) and as the designated exception for strict translation tables that programmers build themselves. Most Python developers will never see it in a traceback.

It still needs a careful translation, for two reasons. First, it is a documented member of the family, and its name must slot consistently under the `UnicodeError` anchor. Second — and this is the linguistic trap — "translate" here does *not* mean natural-language translation. A word choice implying human-language translation would be actively misleading in a product whose entire purpose is natural-language translation of programming vocabulary: the reader would assume the exception concerns translating between human languages. It concerns mapping characters within one text.

**Key behaviors:**

1. **str → str, no codec:** Character translation maps code points to replacements inside text. No encoding participates — the constructor takes four arguments (`object, start, end, reason`) and `encoding` is `None`, unlike both siblings.

2. **Rare by design:** `str.translate()` copies unmapped characters through and swallows `LookupError` from the table. The exception appears only when raised deliberately — by strict custom tables, custom codec error handlers, or C-level translation machinery with strict error handling.

3. **Full family member:** It subclasses `UnicodeError` (and thus `ValueError`), so family-level and value-level handlers catch it, and it carries the family's `object`/`start`/`end`/`reason` diagnostics over the failing character range.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (proper noun domain + operation qualifier + error type)
- **Action vs State:** STATE - describes an error condition, not an action
- **Temporal aspect:** Instantaneous - occurs at the character that cannot be mapped

### Recommended Form

**Primary recommendation:** Keep "Unicode" exactly as the base class renders it, keep the family's error word, and choose the operation word by this rule: **it must match the pack's translation of `str.translate()`, and it should carry the technical mapping/conversion sense, not the human-language sense.** Where a language has a dedicated technical word distinct from its everyday translation word, use it for both the method and this exception. Where the everyday translation word also has established technical mapping usage (as in "address translation"), it is acceptable — but verify, per language, that readers will not parse the exception as "error translating between human languages."

**Forms to AVOID:**

- ❌ A word that ONLY means human-language translation - in a native-language-programming product this is uniquely confusing: users will think the tool's own translation layer failed
- ❌ Encode or decode vocabulary - translation is str → str; no codec or bytes are involved
- ❌ Semantic translation of "Unicode" - it is a proper noun; see the base class brief

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES — this file has the sharpest ambiguity in the Unicode family, plus the proper-noun rule.

**Identify the CORRECT treatment for Python:**

- ❌ Treatment 1: Translating "Unicode" semantically ("universal code") - it is the PROPER NOUN naming the character standard; keep it untranslated or transliterated, exactly as in `UnicodeError`
- ❌ Meaning 2: "Translate" as converting between human languages ("translate a novel into another language") — the dominant everyday meaning, and precisely the WRONG one here
- ❌ Meaning 3: "Translate" as physical displacement (geometry: translating a shape)
- ✅ Meaning 4: **"Translate" as MAPPING CHARACTERS to replacements within text** (str → str, the `str.translate()` operation)

**Example:**

English "translate" can mean:

1. "She translated the novel from its original language" (human languages) ❌
2. "Translate the triangle three units right" (geometry) ❌
3. `'abc'.translate({ord('a'): ord('@')})` returns `'@bc'` ✅ **This is the Python meaning: per-character mapping**

**Your translation must capture meaning #4. This matters doubly in this project: the product's own purpose is human-language translation, so a word meaning "language translation error" would collide with the product's core vocabulary. Choose the technical mapping/conversion word, keep it aligned with `str.translate()`, and keep "Unicode" as a name.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `UnicodeTranslateError`, check these translations:**

- [ ] `str.translate` - The operation this exception belongs to; MUST share the same root
- [ ] `str.maketrans` - Builds the tables `str.translate` consumes; vocabulary should align
- [ ] `UnicodeError` - Parent class; the Unicode form and error word must match exactly
- [ ] `UnicodeDecodeError` / `UnicodeEncodeError` - Siblings; same anchor and suffix, but their direction words must remain clearly distinct from this operation word
- [ ] `ValueError` - Grandparent class; family error word and structure

**Consistency rule:**

The operation word is locked to `str.translate()`: whatever root renders the method must render this exception. The Unicode anchor is locked to the base class. The error word is locked to the family. The one degree of freedom — which root to use — should be spent on the technical mapping sense, not the human-language sense.


### Functional relationships

**This term works WITH:**

1. **`str.translate()` + `UnicodeTranslateError`**: The operation and its designated failure.

```python
"text".translate(table)  # strict tables raise UnicodeTranslateError
```

2. **`str.maketrans()` + `str.translate()`**: Building the mapping.

```python
table = str.maketrans({"é": "e", "ñ": "n"})
```

**Common pairing:**

```python
# A strict ASCII-fold that fails loudly on unmapped characters
FOLD = {ord("é"): ord("e"), ord("ñ"): ord("n"), ord("ü"): ord("u")}

class StrictFold(dict):
    def __missing__(self, code_point):
        if code_point < 128:
            return code_point            # ASCII passes through
        raise UnicodeTranslateError(
            chr(code_point), 0, 1, "character has no ASCII fold"
        )

print("señor".translate(StrictFold(FOLD)))  # 'senor'

try:
    "café ☕".translate(StrictFold(FOLD))
except UnicodeTranslateError as exc:
    print(f"unmappable: {exc.object!r} ({exc.reason})")

# Family handlers catch it at every level
try:
    raise UnicodeTranslateError("x", 0, 1, "demo")
except UnicodeError:
    pass
except ValueError:
    pass  # would also have caught it
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

### HARD

- No direct equivalent in some languages
- May need compound term or explanation
- Concept doesn't exist universally
- **AI confidence should be MEDIUM, human review recommended**

### Why HARD for `UnicodeTranslateError`

- "Translate" is a false friend at maximum strength: the everyday word means human-language translation, which is exactly wrong here — and doubly dangerous in a product about human-language translation of code
- The correct word is language-dependent: some languages have a dedicated technical term, some reuse the everyday word technically, some need a conversion/transformation word instead
- The choice is locked to `str.translate()`, so it cannot be made for this term alone
- The exception's rarity means little real-world usage exists to validate against

**For this term:** HARD

**Rationale:** This is the family's genuinely difficult term. The proper-noun anchor and error suffix are mechanical, but the operation word requires a per-language judgment call between the everyday translation word (sometimes technically established, sometimes misleading) and a mapping/conversion word — made jointly with the `str.translate()` rendering. Human review by a linguist familiar with the language's CS vocabulary is recommended.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Operation word means character mapping (str → str), not human-language translation?
- [ ] "Unicode" treated as a proper noun, identical to the base class form?
- [ ] No encode/decode vocabulary (no codec is involved)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Same root as the pack's rendering of `str.translate` and `str.maketrans`?
- [ ] Unicode form byte-for-byte identical across all four Unicode exceptions?
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
term: UnicodeTranslateError
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
