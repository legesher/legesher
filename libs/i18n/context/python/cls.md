# Python Reserved Word: `cls` - Translation Brief (Tier 1)

**Category:** implicit_param
**Type:** noun (abbreviation of "class")
**Python Version:** all (naming convention; codified in PEP 8, not enforced by the parser)
**Difficulty:** HARD

---

## Quick Summary

`cls` is NOT a Python keyword. It is the CONVENTIONAL name for the first parameter of classmethods (methods decorated with `@classmethod`), referring to the CLASS object itself rather than an instance. The abbreviation exists because `class` is a reserved keyword and literally cannot be used as a parameter name; PEP 8 codifies `cls` as its stand-in. Legesher translates it because it appears in every `@classmethod` a learner reads - and its translation must be visibly RELATED to the language's `class` translation, yet distinguishable from both it and the `self` translation.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# cls refers to the class object, not an instance
class Dog:
    species = "Canis familiaris"      # class attribute

    @classmethod
    def describe(cls):
        print(f"All dogs are {cls.species}")

Dog.describe()   # Output: All dogs are Canis familiaris

# 'class' itself is a keyword, so it cannot be the parameter name:
# def describe(class):   # SyntaxError - hence the abbreviation 'cls'
```

**What this does:** `@classmethod` makes Python pass the CLASS (`Dog`) as the first argument instead of an instance, and by convention that parameter is named `cls`. `cls.species` reads a class attribute shared by all dogs. No instance is needed - `Dog.describe()` works without ever creating a `Dog`. The comment shows WHY the abbreviation exists: the obvious name `class` is a reserved keyword and would be a `SyntaxError`.

### Example 2: Common Pattern

```python
# Alternative constructor - the classic @classmethod use case
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @classmethod
    def from_string(cls, text):
        x, y = text.split(",")
        return cls(float(x), float(y))   # cls(...) constructs an instance

p = Point.from_string("3.5,7.2")
print(p.x, p.y)   # Output: 3.5 7.2
```

**What this does:** `from_string` is an ALTERNATIVE CONSTRUCTOR: a second way to build a `Point`, from a text form instead of two numbers. Inside it, `cls` is the `Point` class itself, so `cls(float(x), float(y))` is the same as calling `Point(...)` - but written through `cls`, not hard-coded. This "parse, then `return cls(...)`" pattern is the single most common reason learners meet `cls` (compare `dict.fromkeys`, `datetime.fromtimestamp` in the standard library).

### Example 3: Edge Case

```python
# With inheritance, cls is whichever class the call went through
class Animal:
    @classmethod
    def create(cls):
        return cls()          # builds an instance of the ACTUAL class

class Cat(Animal):
    pass

a = Animal.create()
c = Cat.create()
print(type(a).__name__)   # Animal
print(type(c).__name__)   # Cat   <- not Animal!
```

**What this shows:** `cls` is not frozen to the class where the method is written. `Cat.create()` passes `Cat` as `cls`, so `cls()` builds a `Cat`. This is why alternative constructors use `return cls(...)` instead of `return Animal(...)`: subclasses inherit them and get instances of the right type for free. `cls` means "the class this call came through" - the class referring to itself, polymorphically.

---

## Pattern Classification

**This term is:** RESERVED WORD (Convention - Class Self-Reference)

**Similar terms in this pattern:**

1. `self` - Sibling convention: first parameter of instance methods, referring to the instance (where `cls` refers to the class)
2. `class` - The keyword `cls` abbreviates; `cls` IS the class object created by a `class` statement
3. `classmethod` - The builtin/decorator that makes Python pass the class as the first argument

**Pattern rule:** Class-reference conventions must be a SHORT, VISIBLY DERIVED form of the language's `class` translation - an abbreviation, initial, or compact compound containing it - while remaining distinguishable from both the full `class` keyword rendering and the `self` translation. The kinship is the point: English readers see `cls` and think "class"; target-language readers must get the same flash of recognition.


---

## Etymology (Brief)

**English Origin:** Modern abbreviation (English "class," from Latin "classis")

**Root meaning:** `cls` is "class" with the vowels deleted - the consonant skeleton c-l-s. It has no independent meaning; its entire semantic content is "the word class, shortened." (See `class.md` for the full etymology of the parent word.)

**Why Python uses this:** Because `class` is a reserved keyword, `def method(class):` is a `SyntaxError` - the natural name is grammatically off-limits, so the community needed a stand-in. Early Python code also used `klass` (misspelling strategy); PEP 8 settled the question: "Always use `cls` for the first argument to class methods." The abbreviation strategy (drop vowels, keep the recognizable skeleton) is a common English convention, like "pkg" for package or "src" for source.

---

## Concept Explanation (Intermediate Level)

**What it does:**

A classmethod is a method that belongs to the class rather than to any single instance. Decorating a method with `@classmethod` changes what Python passes as the first argument: instead of an instance (`self`), it passes the CLASS OBJECT itself - and by convention that parameter is named `cls`. Inside the method, `cls` is a real object (classes are objects in Python, instances of `type`): you can read class attributes (`cls.species`), call other classmethods, and - most importantly - call `cls(...)` to construct instances.

That last ability powers the dominant use case: alternative constructors. `__init__` gives a class one construction signature; classmethods like `from_string`, `from_dict`, or `from_config` give it others, each ending in `return cls(...)`. Writing `cls(...)` rather than naming the class directly keeps constructors polymorphic: a subclass inheriting the classmethod gets instances of the SUBCLASS, because `cls` is bound to whichever class the call actually went through.

Like `self`, none of this naming is parser-enforced. The decorator machinery passes the class no matter what the parameter is called; `cls` is convention, codified by PEP 8 and assumed by every linter, IDE, and tutorial. Unlike `self`, though, the convention has a hard motivation: the obvious name is impossible, because `class` is a keyword. This exact collision recurs in Legesher: whatever a language pack renders the `class` keyword as, the `cls` rendering must NOT be identical to it, or translated code would contain a parameter spelled like a keyword.

**Key behaviors:**

1. **Receives the class object:** In a `@classmethod`, the first parameter is the class itself (an instance of `type`), not an instance of the class. `cls.attr` reads class attributes; `cls(...)` constructs new instances; no instance need exist for the call to work (`Dog.describe()`).

2. **Polymorphic through inheritance:** `cls` is bound to the class the call went THROUGH, not the class where the method was defined. `Cat.create()` gives `cls = Cat` even if `create` lives on `Animal` - which is why alternative constructors written with `return cls(...)` automatically produce correct subclass instances.

3. **Convention with a forced abbreviation:** The parser does not check the name, but the natural name `class` is a keyword and therefore a `SyntaxError` as a parameter. PEP 8 codifies `cls`; the ecosystem (IDEs, linters, error messages, tutorials) assumes it, making it a reserved word in practice.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (abbreviated) - a name referring to the class object from inside its own classmethods
- **Action vs State:** REFERENT - neither action nor state; it points at "this class"
- **Temporal aspect:** None - a stable reference valid for the duration of each classmethod call

### Recommended Form

**Primary recommendation:** Derive the form FROM the language's `class` translation so the kinship is visible at a glance, using whatever shortening/marking strategy the script actually supports. Alphabetic scripts truncate well (drop vowels or keep the first syllable). Abjads are already consonant skeletons - "truncating" is meaningless - so mark the word instead (definite article, or a single-initial form if the community accepts terse forms). Logographic scripts cannot shorten a one-character word further, so build a short compound that CONTAINS it ("this class"). Syllabic scripts lose readability when letters are dropped, so a short compound containing the class word beats a mutilated fragment. The invariants across all strategies: contains-or-marks the class word, SHORTER-OR-EQUAL prominence than a full phrase, and never identical to the `class` keyword rendering.

**Forms to AVOID:**

- ❌ The `class` translation verbatim - in Legesher-translated code the keyword rendering is reserved, exactly as `class` is in English Python; the parameter must differ or the code cannot parse
- ❌ The `self` translation or anything derived from it - collapses the instance/class distinction that `@classmethod` exists to make
- ❌ Unrelated coinages (words meaning "type," "metaclass," "mold/template") - loses the visible `class`-kinship that makes `cls` self-explanatory

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (as a letter sequence, not as a word)

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: `CLS` - the DOS/Windows "clear screen" command
- ❌ Meaning 2: CLS - Common Language Specification (.NET) or other initialisms
- ✅ Meaning 3: **ABBREVIATION OF "CLASS"** - the class object itself, passed as the first parameter of a classmethod

**Example:**

The letters "cls" can mean:

1. `CLS` at a DOS prompt (clear the terminal screen) ❌
2. "CLS-compliant" (.NET Common Language Specification) ❌
3. `def from_string(cls, text):` (the class object, abbreviated from "class") ✅ **This is the Python meaning**

**Your translation should capture meaning #3, and should be built the same way: a shortened or marked form of YOUR language's word for "class."**

Do not translate `cls` as if it meant "clear," "type," or "template," and do not treat it as an opaque token to keep in English by default - the abbreviation is meaningful (class-with-vowels-dropped), and that meaning is reproducible in most languages via the script-appropriate strategy (truncation, article-marking, or compact compounding). Also resolve the category explicitly: like `self`, `cls` is NOT a keyword - it is a conventional parameter name (PEP 8), so it must work as an ordinary identifier.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `cls`, check these translations:**

- [ ] `class` - THE anchor: `cls` must be visibly derived from (or contain/mark) this translation, yet never be identical to it
- [ ] `self` - The sibling parameter: `cls` and `self` must be instantly distinguishable; `cls` derives from the class word, `self` from reflexive vocabulary - the two must never share a root the reader could confuse
- [ ] `classmethod` - The decorator/builtin that creates the binding (see `classmethod.md`); prose must connect them
- [ ] `def` - Classmethod signatures read `def nombre(cls, ...):`; must flow naturally in the target language

**Consistency rule:**

The centerpiece is the THREE-WAY RELATIONSHIP **class / cls / self**, which every language pack must reproduce:

1. `class` (keyword) names the category - the pack's chosen noun.
2. `cls` (parameter) = a shortened/marked form of that SAME noun: visibly related, never identical (identity would be a keyword collision, the very problem `cls` was invented to dodge).
3. `self` (parameter) = a reflexive pronoun, visibly UNRELATED to the class noun.

A reader glancing at a signature must be able to tell which of the three they are looking at without context.


### Functional relationships

**This term works WITH:**

1. **`@classmethod` + `cls`:** The decorator creates the class binding

```python
class Pizza:
    @classmethod
    def margherita(cls):
        return cls(["mozzarella", "tomato"])
```

2. **`cls(...)` as constructor call:** Alternative constructors

```python
class Date:
    def __init__(self, year, month, day):
        self.year, self.month, self.day = year, month, day

    @classmethod
    def from_iso(cls, text):
        y, m, d = text.split("-")
        return cls(int(y), int(m), int(d))

d = Date.from_iso("2026-07-04")
```

**Common pairing:**

```python
# Reading class attributes through cls
class Robot:
    population = 0

    def __init__(self):
        type(self).population += 1

    @classmethod
    def census(cls):
        return f"{cls.__name__} population: {cls.population}"

# Alternative constructors (the canonical pattern)
class Temperature:
    def __init__(self, celsius):
        self.celsius = celsius

    @classmethod
    def from_fahrenheit(cls, f):
        return cls((f - 32) * 5 / 9)

    @classmethod
    def from_kelvin(cls, k):
        return cls(k - 273.15)

# cls staying polymorphic under inheritance
class Shape:
    @classmethod
    def unit(cls):
        return cls()        # Circle.unit() -> Circle, Square.unit() -> Square

class Circle(Shape):
    pass

class Square(Shape):
    pass

# The three roles side by side: class / cls / self
class Config:                      # class: defines the category
    defaults = {"debug": False}

    def __init__(self, **overrides):
        self.values = {**self.defaults, **overrides}   # self: this instance

    @classmethod
    def default(cls):
        return cls()                                   # cls: this class
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

### HARD

- No direct equivalent in some languages
- May need compound term or explanation
- Concept doesn't exist universally
- **AI confidence should be MEDIUM, human review recommended**

### Why HARD for `cls`

- The MEANING is fully determined (a shortened form of the pack's `class` translation), but the FORM requires per-script invention: alphabetic truncation, abjad article-marking, logographic compounding, syllabic prefixing - each an editorial judgment call, leaning EXPERT for logographic and abjad scripts
- The three-way distinction (class / cls / self) must survive whatever form is chosen - three constraints on one short token
- Abbreviation conventions differ sharply by language community: some accept vowel-dropped skeletons, others find them unreadable or foreign
- Learner-facing risk: a too-clever abbreviation is opaque; a too-long compound gets tedious in every classmethod signature

**For this term:** HARD

**Rationale:** Unlike `except*` (deterministic derivation) or `self` (pick the natural reflexive), `cls` demands a small act of word-formation in each language, and the right strategy depends on the writing system, not just the vocabulary. Confidence can be MEDIUM-HIGH for alphabetic-script languages where truncation is routine, but should drop to MEDIUM or LOW for abjad, logographic, and syllabic scripts, where a linguist should confirm the marked/compound form reads naturally. Always verify the result against the pack's finalized `class` and `self` renderings before shipping.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Reads as "the class (object) itself," not an instance?
- [ ] Visibly derived from / contains / marks the pack's `class` translation?
- [ ] Preserves the not-a-keyword framing (works as an ordinary identifier)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun/abbreviated noun, not verb)?
- [ ] Shortening strategy appropriate to the script (truncation vs marking vs compounding)?
- [ ] Follows target language word-formation norms?
- [ ] Lowercase (parameter names are lowercase per PEP 8)?

### 3. Consistency

- [ ] NOT identical to the `class` keyword translation (keyword collision)?
- [ ] Clearly distinct from the `self` translation - no shared confusable root?
- [ ] Three-way class / cls / self distinction legible at a glance?

### 4. Usability

- [ ] Short (ideally at or under the length of the `class` translation)?
- [ ] Easy to type on the language's standard keyboard layout?
- [ ] Pronounceable when reading a signature aloud (or an accepted initialism)?
- [ ] Recognition is instant for someone who knows the `class` translation?

### 5. Cultural Appropriateness

- [ ] Abbreviation style accepted in the target language's technical writing?
- [ ] No unfortunate meanings created by the shortened form?
- [ ] Not childish or unprofessional?

### 6. Technical Compatibility

- [ ] Valid identifier characters in Python 3 (Unicode identifiers allowed)?
- [ ] Renders properly in IDEs (especially RTL scripts and article-prefixed forms)?
- [ ] No characters that break syntax highlighting or tooling?

---

## Translation Output Format

**Your translation:**

```yaml
term: cls
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
