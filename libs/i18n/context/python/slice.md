# Python Builtin Type: `slice` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** noun/verb
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

The `slice` type creates slice objects that represent ranges for indexing sequences. While you usually use slice notation (`[start:stop:step]`), the `slice()` function creates explicit slice objects that can be stored, reused, and passed around. Used for programmatic slicing of sequences.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Create slice object
s = slice(1, 4)
numbers = [0, 1, 2, 3, 4, 5]
print(numbers[s])  # Output: [1, 2, 3]
```

**What this does:** `slice()` creates a slice object representing a range. Using it with indexing (`numbers[s]`) is equivalent to `numbers[1:4]` - extracts elements from index 1 up to (but not including) 4.

### Example 2: Common Pattern

```python
# Slice with start, stop, step
every_other = slice(0, 10, 2)  # Every 2nd element
numbers = list(range(20))
print(numbers[every_other])  # Output: [0, 2, 4, 6, 8]

# Reusable slice
first_three = slice(3)  # Same as [:3]
data1 = [1, 2, 3, 4, 5]
data2 = [10, 20, 30, 40, 50]
print(data1[first_three])  # [1, 2, 3]
print(data2[first_three])  # [10, 20, 30]
```

**What this does:** Slice objects can include step parameter for skipping elements. Once created, slice objects can be reused on different sequences, making code more maintainable and readable.

### Example 3: Edge Case

```python
# Slice with None (unbounded)
all_but_first = slice(1, None)  # Same as [1:]
numbers = [0, 1, 2, 3, 4]
print(numbers[all_but_first])  # Output: [1, 2, 3, 4]

# Negative indices
last_three = slice(-3, None)  # Last 3 elements
print(numbers[last_three])  # Output: [2, 3, 4]

# Slice attributes
s = slice(1, 10, 2)
print(s.start, s.stop, s.step)  # Output: 1 10 2
```

**What this shows:** `None` in slice means "to the end." Negative indices count from the end. Slice objects have `.start`, `.stop`, and `.step` attributes for introspection.

---

## Pattern Classification

**This term is:** TYPE CONSTRUCTOR (Indexing Tool)

**Similar terms in this pattern:**

1. `range` - Creates ranges of numbers (similar concept, different purpose)
2. `enumerate` - Adds indices to iteration (related to indexing)
3. `zip` - Combines sequences (related to sequence manipulation)

**Pattern rule:** Sequence manipulation types should use terms indicating their action or result. "Slice" describes both cutting and the resulting piece.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `range` | rango | نطاق | 范围 | परिसर |
| `list` | lista | قائمة | 列表 | सूची |
| `slice` | **porción** | **شريحة** | **切片** | **खंड** |

---

## Etymology (Brief)

**English Origin:** Germanic

**Root meaning:** Old English "slītan" meant "to split, tear, rend." "Slice" as noun means a thin piece cut from something. As verb, means to cut into pieces.

**Why Python uses this:** "Slice" in programming means extracting a portion of a sequence, like slicing a piece from a loaf. The term captures both the action (slicing/cutting) and result (the piece extracted). Python's slice notation `[start:stop]` mimics cutting from one point to another.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `slice` type creates objects that represent index ranges for extracting portions of sequences. When you write `list[1:4]`, Python internally creates a slice object `slice(1, 4, None)`. The `slice()` function lets you create these objects explicitly, which is useful for storing, naming, and reusing slice specifications.

A slice object has three attributes: `start` (where to begin), `stop` (where to end, exclusive), and `step` (how many to skip). Any can be `None` for defaults. The `slice()` function takes 1-3 arguments: `slice(stop)`, `slice(start, stop)`, or `slice(start, stop, step)`.

Explicit slice objects make code more readable when you have meaningful slice patterns. Instead of `data[5:10]` scattered in code, you can write `data[middle_section]` where `middle_section = slice(5, 10)`. This is especially useful for numpy arrays, pandas dataframes, or any custom classes implementing `__getitem__`.

**Key behaviors:**

1. **Three parameters:** Start (inclusive), stop (exclusive), step (increment). All optional, default to `None`. `slice(5)` is `slice(None, 5, None)` equivalent to `[:5]`.

2. **Returns slice object:** Can be stored in variables, passed as arguments, used multiple times. Object has `.start`, `.stop`, `.step` attributes for introspection.

3. **Works with **getitem**:** Any object implementing `__getitem__` can accept slice objects. This makes slicing work uniformly across lists, tuples, strings, numpy arrays, and custom classes.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (the slice object) or verb (to slice)
- **Action vs State:** Can be ACTION (slicing) or RESULT (the slice)
- **Temporal aspect:** Creates object representing range

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Noun | "porción", "tranche" - the piece/portion |
| Germanic (de, nl, sv) | Noun | "Scheibe", "schijf" - slice/piece |
| Slavic (ru, pl, uk) | Noun | "срез", "plasterek" - cut/slice |
| Arabic | Noun | "شريحة" (sharīḥa) - slice/section |
| Chinese | Verb-noun | "切片" - cut-piece/slice |
| Hindi | Noun | "खंड" - section/piece |

**Primary recommendation:** Use noun form meaning "slice" or "portion." While slicing is an action, the `slice()` function creates an object (the slice itself), so noun is more appropriate.

**Forms to AVOID:**

- ❌ Using "cut" alone without indicating the result
- ❌ Using "index" - too specific, slice is a range

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `porción` or `rebanada`
- **Form:** Noun
- **Why it works:** "Porción" means portion/piece, clear for programming context. "Rebanada" means slice (like bread slice), more literal. Both work; "porción" more general.

**Arabic:**

- **Translation:** `شريحة` (sharīḥa)
- **Form:** Noun
- **Why it works:** Standard Arabic word for slice/section. Used in computing contexts. Natural noun form indicating a piece or segment.

**Chinese:**

- **Translation:** `切片` (qiēpiàn)
- **Form:** Verb-noun compound
- **Why it works:** 切 (cut) + 片 (piece/slice). Standard Chinese computing term for slicing. Used in numpy, pandas documentation. Clear action-result meaning.

**Hindi:**

- **Translation:** `खंड` (khaṇḍ) or `स्लाइस`
- **Form:** Noun or transliteration
- **Why it works:** "खंड" means section/fragment, formal Sanskrit-derived term. Can also transliterate "स्लाइस" (slice) as technical loanword.

### ❌ Common Translation Mistakes

**Mistake 1: Using "cut" verb without indicating result**

- **Wrong:** `cortar` (Spanish - "to cut" verb)
- **Why wrong:** Python builtins are typically nouns (types/objects) or infinitive verbs. "Cortar" is conjugated verb or infinitive but doesn't indicate the result object.
- **Right:** `porción` (the slice/portion - noun)

**Mistake 2: Using "index" instead of "slice"**

- **Wrong:** `índice` (Spanish - "index")
- **Why wrong:** An index is a single position (0, 1, 2), a slice is a range (1:4). Different concepts.
- **Right:** `porción` or `rebanada` (indicates range/portion)

**Mistake 3: Using "part" too generically**

- **Wrong:** `parte` (Spanish - "part")
- **Why wrong:** Too generic. "Part" doesn't convey the specific slicing/range extraction concept. "Slice" is more specific.
- **Right:** `porción` or `rebanada` (specifically a sliced portion)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Slice of pizza" (physical piece of food)
- ✅ Meaning 2: **RANGE/PORTION OF SEQUENCE** (extract part of list/string)
- ❌ Meaning 3: "Slice in golf" (curved ball path)

**Example:**

English "slice" can mean:

1. "A slice of bread" (physical piece) ❌
2. "`list[1:4]` extracts a slice" (range from sequence) ✅ **This is the Python meaning**
3. "The ball sliced to the right" (golf term) ❌

**Your translation should capture meaning #2: a portion/range extracted from a sequence, not a physical cutting or sports term.**

In programming, "slice" specifically means extracting a contiguous range from a sequence.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `slice`, check these translations:**

- [ ] `range` - Similar concept of defining ranges; should feel related
- [ ] `list`, `tuple`, `str` - Objects that are sliced; relationship should be clear
- [ ] `enumerate` - Related iteration tool; similar sequence manipulation theme

**Consistency rule:**

Sequence manipulation tools (`slice`, `range`, `enumerate`) should use compatible terminology indicating sequence operations. If `range` uses a noun form, `slice` should too.

**Example:**

Spanish: `porción` (slice), `rango` (range) - both nouns, related concepts ✅
Chinese: `切片` (slice), `范围` (range) - consistent noun/compound forms ✅

### Functional relationships

**This term works WITH:**

1. **`slice` for indexing**: Extract portions

```python
s = slice(1, 4)
print([0,1,2,3,4][s])  # [1, 2, 3]
```

2. **`slice` with step**: Skip elements

```python
every_two = slice(None, None, 2)
print([0,1,2,3,4,5][every_two])  # [0, 2, 4]
```

**Common pairing:**

```python
# Create slice objects
first_five = slice(5)          # [:5]
from_five = slice(5, None)     # [5:]
middle = slice(2, 5)           # [2:5]
every_other = slice(None, None, 2)  # [::2]

# Use with sequences
text = "Hello, World!"
print(text[first_five])   # "Hello"
print(text[from_five])    # ", World!"

# Reusable slices
data_slice = slice(10, 20)
dataset1 = list(range(100))
dataset2 = list(range(200, 300))
print(dataset1[data_slice])  # [10-19]
print(dataset2[data_slice])  # [210-219]

# Slice attributes
s = slice(1, 10, 2)
print(s.start)   # 1
print(s.stop)    # 10
print(s.step)    # 2

# Negative indices
last_three = slice(-3, None)
numbers = [1, 2, 3, 4, 5]
print(numbers[last_three])  # [3, 4, 5]

# Named slices for readability
HEADER = slice(0, 10)
DATA = slice(10, None)
record = list(range(100))
header = record[HEADER]
data = record[DATA]
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### MEDIUM

- Multiple options, context helps decide
- Common concept across languages
- May need to choose between synonyms
- **AI confidence should be MEDIUM-HIGH with context**

### Why MEDIUM for `slice`

- "Slice" has physical meanings (food) and programming meanings
- Need to choose between "slice," "portion," "section," "segment"
- Balance between literal cutting metaphor and range/portion concept
- Some languages may have specific computing term for slicing

**For this term:** MEDIUM

**Rationale:** The concept of extracting portions from sequences is universal, but "slice" as a term has multiple meanings. Need to select translation that conveys range extraction, not physical cutting. Some languages have established computing terms for slicing, others may need to adapt physical slicing terms.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

Key consideration: Translation should suggest extracting a range/portion from a sequence, distinct from indexing single elements.

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures RANGE EXTRACTION concept?
- [ ] Distinct from single-element indexing?
- [ ] Indicates portion/section of sequence?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun preferred)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python types)?

### 3. Consistency

- [ ] Compatible with `range` and sequence types?
- [ ] Matches programming terminology conventions?
- [ ] Aligns with CS education terminology?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Clear meaning in sequence context?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Professional technical term?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: slice
language: es
translation: porción
form: noun
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "porción" means portion/section, clearly indicating a piece of a sequence. It's more general than "rebanada" (bread slice) and works well in programming contexts. Natural noun form matching Python's type constructor pattern.

**Alternatives considered:**

1. `rebanada` (slice of bread) - More literal but less general
2. `segmento` (segment) - Valid but "porción" more natural
3. `slice` (keep English) - Works but loses semantic meaning

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH. The concept of extracting portions from sequences is straightforward. "Slice" as range extraction has clear equivalents in most languages (portion, section, piece).

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
