# Python Builtin: `StopIteration` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.x+
**Difficulty:** MEDIUM

---

## Quick Summary

`StopIteration` is a special exception raised by iterator objects to signal that there are no more items to iterate over. It's the mechanism Python uses internally to end loops when using iterators and generators, converting iteration exhaustion into a catchable signal.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Iterator raises StopIteration when exhausted
numbers = iter([1, 2, 3])
print(next(numbers))  # 1
print(next(numbers))  # 2
print(next(numbers))  # 3
print(next(numbers))  # Raises StopIteration
```

**What this does:** When you call `next()` on an iterator that has no more items, Python raises `StopIteration`. This signals the iteration is complete and causes `for` loops to terminate gracefully.

### Example 2: Common Pattern

```python
# Catching StopIteration explicitly
numbers = iter([1, 2, 3])
try:
while True:
print(next(numbers))
except StopIteration:
print("No more items")
```

**What this does:** Demonstrates how `for` loops work internally—they keep calling `next()` and catch `StopIteration` to know when to stop. You rarely catch this exception explicitly, but this shows the underlying mechanism.

### Example 3: Edge Case

```python
# Custom iterator using StopIteration
class Countdown:
def __init__(self, start):
self.current = start
def __iter__(self):
return self
def __next__(self):
if self.current <= 0:
raise StopIteration
self.current -= 1
return self.current + 1

for num in Countdown(3):
print(num)  # Prints: 3, 2, 1
```

**What this shows:** Custom iterators use `raise StopIteration` to signal completion. When `__next__()` raises `StopIteration`, the `for` loop automatically terminates. This is the standard protocol for implementing iterators.

---

## Pattern Classification

**This term is:** TYPE CONSTRUCTOR (Control Flow Exception)

**Similar terms in this pattern:**

1. `StopAsyncIteration` - Similar exception for asynchronous iterators
2. `GeneratorExit` - Raised when generator's `close()` is called
3. `KeyboardInterrupt` - Another control flow exception (not error-based)

**Pattern rule:** Control flow exceptions should use compound noun form combining the action ("Stop") with the concept ("Iteration"), following Python's class naming conventions.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `Exception` | Excepción | استثناء | 异常 | अपवाद |
| `KeyboardInterrupt` | InterrupciónTeclado | مقاطعة_لوحة_المفاتيح | 键盘中断 | कुंजीपटल_बाधा |
| `StopIteration` | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** |

---

## Etymology (Brief)

**English Origin:** English "stop" (Germanic) + "iteration" (Latin "iterare")

**Root meaning:** "Stop" comes from Old English "stoppian" meaning "to block or close up." "Iteration" comes from Latin "iterare" meaning "to repeat" or "to do again," from "iterum" (again).

**Why Python uses this:** Python adopted iterator protocol from functional programming languages. `StopIteration` clearly describes what's happening: the iteration process is stopping. The name was chosen to be explicit and descriptive rather than using more abstract terms like "Exhausted" or "EndOfSequence."

---

## Concept Explanation (Intermediate Level)

**What it does:**

`StopIteration` is Python's signal mechanism for ending iteration. Unlike most exceptions that indicate errors, `StopIteration` is a normal control flow exception that communicates "I've finished iterating" from an iterator to the code using it. When you write a `for` loop, Python internally catches `StopIteration` to know when to exit the loop.

The iterator protocol in Python works through two special methods: `__iter__()` returns the iterator object, and `__next__()` returns the next item or raises `StopIteration` when exhausted. This design separates the "how to iterate" logic (inside `__next__`) from the "what to do with items" logic (in your `for` loop body).

Generators use `StopIteration` implicitly—when a generator function returns (reaches the end or explicit `return`), Python automatically raises `StopIteration` behind the scenes. This is why generator functions don't need explicit `raise StopIteration` statements; the return automatically triggers it.

**Key behaviors:**

1. **Automatic in For Loops:** You never need to catch `StopIteration` when using `for` loops because Python catches it internally. The exception is transparent to normal iteration.

2. **Required for Custom Iterators:** When implementing custom iterators via `__next__()`, you must raise `StopIteration` when there are no more items. This is the protocol contract.

3. **Carries Optional Value:** `StopIteration` can carry a return value (accessed via `exception.value`). This is used primarily with generators to return a final value when the generator completes.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun - imperative verb ("stop") + abstract noun ("iteration")
- **Action vs State:** Action/Command - represents the act of stopping iteration
- **Temporal aspect:** Point-in-time event - marks the moment iteration ends

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Compound Noun | Verb-derived noun + "iteration" noun |
| Germanic (de, nl, sv) | Compound Noun | Natural compounding: "StopIteration" pattern |
| Slavic (ru, pl, uk) | Compound Noun | Action noun + "iteration" concept |
| Arabic | Compound Noun/Phrase | Verbal noun + "iteration" noun |
| Chinese | Compound Noun | Action + iteration (verb-object pattern) |
| Hindi | Compound Noun | Sanskrit compound or verb + noun |

**Primary recommendation:** Compound noun combining imperative/action concept ("stop") with iteration concept, maintaining the command-like nature of signaling iteration termination.

**Forms to AVOID:**

- ❌ Pure verb form - This names an exception class, not just an action
- ❌ Separating into unconnected words - Should maintain compound structure

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `DetenerIteración` or `PararIteración`
- **Form:** Compound noun (infinitive verb + noun)
- **Why it works:** "Detener/Parar" (to stop) + "Iteración" (iteration), maintains action + concept structure, follows Python's compound class naming pattern

**Arabic:**

- **Translation:** `إيقاف_التكرار` (eeqaaf al-takraar)
- **Form:** Verbal noun + noun compound
- **Why it works:** "إيقاف" (stopping/halt) + "التكرار" (the iteration), clear technical meaning combining action with iteration concept

**Chinese:**

- **Translation:** `停止迭代` (tíngzhǐ diédài)
- **Form:** Verb + noun compound
- **Why it works:** "停止" (stop/halt) + "迭代" (iteration), natural Chinese verb-object structure, established CS terminology

**Hindi:**

- **Translation:** `पुनरावृत्ति_रोकें` (punaravritti rokein) or `रोकपुनरावृत्ति`
- **Form:** Compound noun
- **Why it works:** "रोक" (stop) + "पुनरावृत्ति" (iteration/repetition), Sanskrit-derived compound maintains both action and concept

### ❌ Common Translation Mistakes

**Mistake 1: Using only "stop" without "iteration"**

- **Wrong:** `Detener` (Spanish - just "stop")
- **Why wrong:** Loses critical context of WHAT is being stopped; too vague for class name
- **Right:** `DetenerIteración`

**Mistake 2: Over-explaining instead of compounding**

- **Wrong:** `ExcepciónParaCuandoLaIteraciónTermina` (Spanish - "exception for when iteration ends")
- **Why wrong:** Too verbose, should be concise compound following Python's naming conventions
- **Right:** `DetenerIteración`

**Mistake 3: Using passive form**

- **Wrong:** `IteraciónDetenida` (Spanish - "iteration stopped" - passive)
- **Why wrong:** Should maintain active/imperative quality of the signal to stop
- **Right:** `DetenerIteración` (active form)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Stop" as in physically halting motion
- ❌ Meaning 2: "Iteration" as a single pass through a loop
- ✅ Meaning 3: Signal to stop the iteration process (CORRECT - control flow exception)
- ❌ Meaning 4: Error indicating iteration failed

**Example:**

English "stop" can mean:

1. Physically halt movement ("stop the car") ❌
2. Cease an activity ("stop talking") ✅ Related concept
3. A signal/exception indicating iteration is complete ✅ **This is the Python meaning**

English "iteration" can mean:

1. A single pass through a loop ("first iteration") ❌
2. The process of repeating ("iteration over a list") ✅ **This is the Python meaning**

**Your translation should capture the concept of signaling/commanding the iteration process to terminate, NOT indicating an error.**

Important: `StopIteration` is NOT an error exception—it's a normal control flow mechanism. Translations should not imply failure.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `StopIteration`, check these translations:**

- [ ] `Exception` - Base class, should share "exception" component
- [ ] `StopAsyncIteration` - Must use same "stop" and similar "iteration" concepts
- [ ] `GeneratorExit` - Similar control flow exception, may inform translation
- [ ] `next()` - Function that triggers `StopIteration`, should relate linguistically
- [ ] `__next__()` - Method that raises `StopIteration`
- [ ] `for` loop - The construct that catches `StopIteration` internally

**Consistency rule:**

The word chosen for "stop" should align with command/imperative vocabulary. The "iteration" component must match how iteration is translated throughout the language pack.

**Example:**

If iteration-related terms are translated:

- `StopIteration` → `停止迭代` (stop + iteration)
- `StopAsyncIteration` → `停止异步迭代` (stop + async + iteration)
- `next()` → `下一个` (next)
- These should form a coherent semantic family

### Functional relationships

**This term works WITH:**

1. **`next()` + `StopIteration`**: `next()` raises `StopIteration` when iterator exhausted
2. **`for` loop catches `StopIteration`**: Implicitly caught to end loops
3. **`__next__()` raises `StopIteration`**: Iterator protocol requires this

**Common pairing:**

```python
# StopIteration appears in iterator protocol
class MyIterator:
def __next__(self):
if no_more_items:
raise StopIteration
return next_item
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

**For this term:** MEDIUM

**Rationale:**

Translating `StopIteration` involves moderate complexity:

**Moderate aspects:**
- Compound term requires understanding both components
- "Stop" has clear translations across languages (command/imperative)
- "Iteration" is established CS vocabulary in most languages
- Need to maintain compound structure without becoming too verbose

**Challenges:**
- Must convey control flow signal, not error condition
- Some languages may prefer different word orders for compounds
- Balance between literal translation and idiomatic phrasing
- Must work as class name (capitalization, compound rules)

The difficulty is MEDIUM because while individual components translate straightforwardly, creating a natural compound that maintains the signal/command nature while following target language class naming conventions requires careful consideration.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures signal to stop iteration (not an error)?
- [ ] Would native speaker understand this as iteration completion?
- [ ] Avoids implying failure or error condition?

### 2. Linguistic Correctness

- [ ] Compound noun structure appropriate?
- [ ] "Stop" component maintains command/imperative quality?
- [ ] "Iteration" component uses established CS term?
- [ ] Capitalization follows class naming conventions?

### 3. Consistency

- [ ] Matches pattern of other control flow exceptions?
- [ ] Uses same "iteration" term as `iter()`, `for` loop?
- [ ] Aligns with `StopAsyncIteration` translation?

### 4. Usability

- [ ] Concise compound (not overly long phrase)?
- [ ] Easy to recognize as iteration-related?
- [ ] Distinguishable from error exceptions?

### 5. Cultural Appropriateness

- [ ] Uses technical/professional vocabulary?
- [ ] No confusing connotations?
- [ ] Respects CS education terminology?

### 6. Technical Compatibility

- [ ] Renders properly in IDEs?
- [ ] Works in error messages and stack traces?
- [ ] No special characters that break code?

---

## Translation Output Format

**Your translation:**

```yaml
term: StopIteration
language: {es|ar|zh|hi|your_language}
translation: {your_translation}
form: {compound_noun}
confidence: {medium|medium-high|high}
```

**Rationale (2-3 sentences):**

{Why you chose this translation. Address: How did you translate "stop" (command/imperative concept)? How did you translate "iteration" (established CS term)? How did you combine them into a natural compound? Does it clearly signal control flow rather than error?}

**Alternatives considered:**

1. `{alternative_1}` - {Why you didn't choose this}
2. `{alternative_2}` - {Why you didn't choose this}

**If confidence is not HIGH, explain:**

{Uncertainty about compound word order? Multiple valid translations for "stop"? Concerns about length or naturalness?}

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
