# Python Reserved Word: `self` - Translation Brief (Tier 1)

**Category:** implicit_param
**Type:** pronoun (reflexive)
**Python Version:** all (naming convention; codified in PEP 8, not enforced by the parser)
**Difficulty:** HARD

---

## Quick Summary

`self` is NOT a Python keyword. It is the CONVENTIONAL name for the first parameter of instance methods, referring to the instance the method was called on - "the object itself." The parser accepts any name; the convention is enforced by community practice (PEP 8), linters, and every tutorial ever written. Legesher translates it anyway because it appears in virtually every class body a learner reads: linguistically it is a reflexive pronoun, and most languages have strong native reflexive forms that beat any coined noun.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# self refers to the instance the method is called on
class Dog:
    def __init__(self, name):
        self.name = name              # store data on THIS instance

    def bark(self):
        print(f"{self.name} says woof")

rex = Dog("Rex")
rex.bark()   # Output: Rex says woof
```

**What this does:** When `rex.bark()` runs, Python passes `rex` as the first argument, so inside the method `self` IS `rex`. `self.name` reads the `name` attribute stored on that particular instance. Every instance method receives the instance this way - `self` is how a method talks about "the object itself."

### Example 2: Common Pattern

```python
# self separates instance state from local variables,
# and lets methods call other methods on the same object
class BankAccount:
    def __init__(self, owner, balance=0):
        self.owner = owner            # instance attribute
        self.balance = balance        # instance attribute

    def deposit(self, amount):
        self.balance += amount        # update THIS account's state
        self._log(amount)             # call another method on itself

    def _log(self, amount):
        print(f"{self.owner}: +{amount}, balance={self.balance}")

a = BankAccount("Ada")
b = BankAccount("Grace", 100)
a.deposit(50)    # Ada: +50, balance=50
b.deposit(25)    # Grace: +25, balance=125
```

**What this does:** Two accounts hold independent state because `self` is a different object in each call: `a.deposit(50)` binds `self` to `a`; `b.deposit(25)` binds it to `b`. Inside a method, `amount` is a local variable that vanishes when the method returns, while `self.balance` persists on the object. `self._log(...)` shows the object invoking its own behavior - the reflexive relationship in action.

### Example 3: Edge Case

```python
# 'self' is convention, not syntax - any name works (but do not do this)
class Counter:
    def increment(this):              # legal Python; violates PEP 8
        this.count = getattr(this, "count", 0) + 1

c = Counter()
c.increment()
print(c.count)   # 1

# A method call is sugar for passing the instance explicitly
class Dog:
    def bark(self):
        print("woof")

rex = Dog()
rex.bark()       # normal call
Dog.bark(rex)    # identical: rex is passed as self
```

**What this shows:** The parser does not treat `self` specially - `this` (or any identifier) works, which proves `self` is a reserved word by CONVENTION, not a keyword. The second half exposes the mechanism: `rex.bark()` is equivalent to `Dog.bark(rex)`. The instance is simply the first argument, and `self` is the name the community agreed to give it (PEP 8: "Always use `self` for the first argument to instance methods").

---

## Pattern Classification

**This term is:** RESERVED WORD (Convention - Instance Self-Reference)

**Similar terms in this pattern:**

1. `cls` - Sibling convention: first parameter of classmethods, referring to the class object (as `self` refers to the instance)
2. `class` - The keyword whose bodies `self` lives in; `self` refers to an instance of a class
3. `def` - Defines the methods whose first parameter `self` names

**Pattern rule:** Self-reference conventions should use the target language's natural REFLEXIVE pronoun or reflexive root - the word for "itself/oneself" - kept short, because `self` is among the most frequently typed identifiers in any class body. It must remain clearly distinct from the translations of `class`, `object`, and `cls`.


---

## Etymology (Brief)

**English Origin:** Old English (Germanic)

**Root meaning:** Old English "self" - an intensive and reflexive pronoun ("the king himself," "know thyself"). Proto-Germanic \*selbaz. It has always meant "this very one, and not another" - identity turned back on itself.

**Why Python uses this:** Python inherited `self` from Smalltalk and Modula-3, the languages that shaped its object model. Where C++ and Java hide the instance behind an implicit `this`, Python makes it an explicit first parameter - "explicit is better than implicit" - and names it with the reflexive pronoun: a method's body describes what the object does to and with ITSELF. Guido has defended explicit `self` repeatedly; it makes the instance visible in every attribute access (`self.x`), so readers never wonder where a name comes from.

---

## Concept Explanation (Intermediate Level)

**What it does:**

Every instance method in Python secretly takes the instance as its first argument. `rex.bark()` is syntactic sugar for `Dog.bark(rex)`: Python looks up `bark` on the class, then calls it with `rex` in the first slot. By convention that first parameter is named `self`, so inside the method `self` is the specific object the call went through. `self.name = value` writes an attribute onto that object; `self.other_method()` invokes more of the object's own behavior. Two instances calling the same method get different `self` bindings - which is exactly why they keep separate state.

Crucially, none of this is parser magic. `self` is an ordinary parameter name; the language would accept `this`, `me`, or `x`. What makes it a "reserved word" in the practical sense is the ecosystem: PEP 8 mandates it, every IDE auto-inserts it, every error message, tutorial, and Stack Overflow answer assumes it. A learner who cannot read `self` cannot read Python classes - which is why Legesher translates a word the parser itself never checks.

Linguistically, `self` is a THIRD-PERSON REFLEXIVE PRONOUN. The method speaks about the object turning actions back on itself - "the object updates ITS OWN balance." It is not first person ("I/me"): the programmer is not the referent, the object is. This distinction matters for translation, because most languages mark reflexivity with dedicated grammar - a native form meaning "the object itself" - and those native reflexive forms almost always read more naturally than coined nouns like "instance" or "the object."

**Key behaviors:**

1. **Explicit instance binding:** `obj.method(args)` calls `Class.method(obj, args)`. The instance arrives as the first parameter, conventionally named `self`. Nothing is implicit: the object is right there in the signature, and every attribute access spells it out (`self.x`, never bare `x`).

2. **Instance attribute namespace:** `self.attr` reads and writes attributes on the specific instance, distinct from local variables (which die with the call) and class attributes (shared by all instances). `self` is the handle that makes per-object state possible.

3. **Convention, not syntax:** The parser accepts any first-parameter name; PEP 8, linters, and IDE tooling enforce `self`. Related conventions: classmethods use `cls` for the class object, and static methods (`@staticmethod`) take no instance parameter at all.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Reflexive pronoun (third person) - names the object as seen from inside its own methods
- **Action vs State:** REFERENT - neither action nor state; it is a name that points at "this very object"
- **Temporal aspect:** None - a stable reference valid for the duration of each method call

### Recommended Form

**Primary recommendation:** Use the language's natural reflexive/intensive pronoun - the word in "the object ITSELF" - in a FREE-STANDING form that can survive alone as an identifier. This is the honest complication: many languages express reflexivity with bound morphology (clitics, suffixes, case-bound forms) that cannot stand alone as a word. In those languages, prefer the intensive pronoun ("itself"-style emphasis) or a reflexive noun. Where a strong free reflexive exists, it is nearly always the right answer and beats any noun coinage. Keep it to ONE short word: `self` is typed on almost every line of a method body.

**Forms to AVOID:**

- ❌ Nouns like "instance" or "object" - names the category, loses the reflexive meaning, and collides with the `object` builtin's translation
- ❌ First-person pronouns ("I"/"me" equivalents) - `self` is third-person reflexive; the OBJECT is the referent, not the programmer or a speaking "I"
- ❌ Multi-word reflexive phrases - too long for the single most-typed identifier in class bodies

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: The psychological self ("sense of self," identity, ego)
- ❌ Meaning 2: The prefix "self-" ("self-service," "self-taught" - autonomous/automatic)
- ❌ Meaning 3: First-person reference ("myself" as the speaker)
- ✅ Meaning 4: **THIRD-PERSON REFLEXIVE REFERENCE** - "the object itself," the thing referring back to itself

**Example:**

English "self" can mean:

1. "Her true self emerged" (identity/psychology) ❌
2. "Self-cleaning oven" (autonomous prefix) ❌
3. "I did it myself" (first-person emphasis) ❌ Related grammar, wrong person
4. "The object itself updates its own state" (reflexive reference) ✅ **This is the Python meaning**

**Your translation should capture meaning #4: the third-person reflexive - the word your language uses in "the object ITSELF."**

Also resolve the category ambiguity explicitly: `self` is NOT a keyword. It is a parameter NAME sustained by convention (PEP 8). The translation therefore does not need to fit keyword grammar (no verb form, no imperative); it needs to work as a short, natural, frequently typed identifier that reads as "itself" everywhere it appears.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `self`, check these translations:**

- [ ] `cls` - Sibling convention (class object in classmethods); the two must be clearly distinct at a glance, and `cls` - not `self` - is the one that must visibly relate to the `class` translation
- [ ] `class` - `self` lives inside class bodies; the `class` translation and the `self` rendering must not resemble each other
- [ ] `def` - Methods are defined with `def`; a translated method signature with the `self` rendering in first position must read naturally in the target language
- [ ] `object` - `self` refers to an instance, but must NOT reuse the `object` builtin's translation

**Consistency rule:**

Maintain the three-way distinction **class / cls / self**: the `class` keyword names the category; `cls` is the abbreviated class-reference (visibly derived from the `class` translation - see `cls.md`); `self` is the instance-reference (a reflexive pronoun, visibly UNRELATED to the `class` word). If the `self` translation starts to look like an abbreviation or derivative of the `class` word, it has stolen `cls`'s job - pick a different reflexive.


### Functional relationships

**This term works WITH:**

1. **`def` + `self`:** Every instance method's first parameter

```python
class Point:
    def move(self, dx, dy):
        self.x += dx
        self.y += dy
```

2. **`__init__` + `self`:** Storing constructor arguments as instance state

```python
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
```

**Common pairing:**

```python
# self in initialization
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email

# self distinguishing instance attribute from parameter (same name!)
class Circle:
    def __init__(self, radius):
        self.radius = radius        # left: attribute, right: parameter

# self calling other methods
class Report:
    def render(self):
        return self._header() + self._body()

    def _header(self):
        return "== Report ==\n"

    def _body(self):
        return "..."

# self with properties
class Celsius:
    def __init__(self, degrees):
        self._degrees = degrees

    @property
    def fahrenheit(self):
        return self._degrees * 9 / 5 + 32

# self returned for method chaining
class QueryBuilder:
    def where(self, cond):
        self.conditions.append(cond)
        return self                  # returning "itself" enables chaining

# self vs cls side by side
class Config:
    defaults = {"debug": False}

    def __init__(self, **overrides):
        self.values = {**self.defaults, **overrides}   # instance state

    @classmethod
    def default(cls):
        return cls()                 # cls: the class; self: an instance
```

---

## Confidence Calibration

**Translation Difficulty: HARD**

### HARD

- No direct equivalent in some languages
- May need compound term or explanation
- Concept doesn't exist universally
- **AI confidence should be MEDIUM, human review recommended**

### Why HARD for `self`

- The CONCEPT maps well: nearly every language has reflexive grammar, and "the object itself" is universally expressible
- The hard part is FORM selection: many languages mark reflexivity with bound morphology (clitics, suffixes, case-bound forms) that cannot stand alone as an identifier - the translator must find a free-standing reflexive (intensive pronoun, reflexive noun) without drifting into category nouns
- Register and person must be right: third-person reflexive, not first-person, not psychological "self"
- Frequency raises the stakes: `self` is typed more than any other identifier in class-based code, so a slightly-wrong choice is felt constantly

**For this term:** HARD

**Rationale:** Languages with a strong free reflexive translate `self` beautifully - confidence there is genuinely high. Languages whose reflexives are clitics or affixes force a choice among imperfect free-standing forms, where native-speaker judgment about what reads naturally as an identifier is essential. Human review recommended for any language where the reflexive is not a free word.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Reads as THIRD-PERSON REFLEXIVE ("the object itself")?
- [ ] Not first-person ("I/me"), not psychological identity, not the "self-" prefix?
- [ ] Preserves the not-a-keyword framing (works as an ordinary identifier)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (pronoun/reflexive form, not verb or category noun)?
- [ ] Free-standing word (not a bound clitic or affix)?
- [ ] Follows target language grammar when read in the first-parameter position of a method signature?
- [ ] Lowercase (parameter names are lowercase per PEP 8)?

### 3. Consistency

- [ ] Clearly distinct from the `class` keyword translation?
- [ ] Clearly distinct from the `cls` translation (see `cls.md`)?
- [ ] Does not reuse the `object` builtin's translation?

### 4. Usability

- [ ] ONE short word (this is the most-typed identifier in class code)?
- [ ] Easy to type on the language's standard keyboard layout?
- [ ] Easy to pronounce when reading code aloud in class?
- [ ] Instantly recognizable as self-reference?

### 5. Cultural Appropriateness

- [ ] No religious/spiritual connotations that distort meaning (e.g., soul-words)?
- [ ] Not childish or unprofessional?
- [ ] Register matches technical writing in the target language?

### 6. Technical Compatibility

- [ ] Valid identifier characters in Python 3 (Unicode identifiers allowed)?
- [ ] Renders properly in IDEs (especially RTL scripts)?
- [ ] No characters that break syntax highlighting or tooling?

---

## Translation Output Format

**Your translation:**

```yaml
term: self
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
