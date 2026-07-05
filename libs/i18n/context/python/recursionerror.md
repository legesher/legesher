# Python Builtin: `RecursionError` - Translation Brief (Tier 1)

**Category:** builtin_type
**Type:** exception class
**Python Version:** 3.5+
**Difficulty:** MEDIUM-HARD

---

## Quick Summary

`RecursionError` is a built-in exception raised when the maximum recursion depth is exceeded - typically when a function keeps calling itself without reaching a base case, exhausting Python's call-stack limit. Introduced in Python 3.5, it subclasses `RuntimeError`, so older code catching `RuntimeError` for this condition still works.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Recursion without a base case exceeds the depth limit
def countdown(n):
    return countdown(n - 1)  # never stops

countdown(10)
# Raises RecursionError: maximum recursion depth exceeded
```

**What this does:** Each call to `countdown` makes another call before returning, so stack frames pile up without limit. When the depth passes Python's recursion limit (1000 by default), the interpreter raises `RecursionError` instead of letting the process crash with a real stack overflow.

### Example 2: Common Pattern

```python
# A correct base case prevents the error; the limit is inspectable
import sys

def factorial(n):
    if n <= 1:          # base case: recursion stops here
        return 1
    return n * factorial(n - 1)

print(factorial(10))               # 3628800
print(sys.getrecursionlimit())     # 1000 (default)

try:
    factorial(100_000)             # correct code, but too deep
except RecursionError:
    print("too deep - use a loop for inputs this large")
```

**What this does:** `factorial` is logically correct, yet still raises `RecursionError` for large inputs because every level of recursion consumes a stack frame. `sys.getrecursionlimit()` shows the ceiling. Catching `RecursionError` lets the program report the problem or switch to an iterative strategy.

### Example 3: Edge Case

```python
# Indirect recursion, the RuntimeError relationship, and the limit knob
import sys

def ping(n):
    return pong(n + 1)   # ping calls pong...

def pong(n):
    return ping(n + 1)   # ...and pong calls ping: mutual recursion

try:
    ping(0)
except RecursionError:
    print("mutual recursion also hits the limit")

print(issubclass(RecursionError, RuntimeError))  # True (3.5+ subclass)

sys.setrecursionlimit(3000)  # raise the ceiling - use with care:
# too high a limit can crash the interpreter with a real stack overflow
```

**What this shows:** The error is about call DEPTH, not about a function literally calling itself - mutually recursive functions trigger it too, as can deeply nested data passed to `repr()` or `json` serializers. Because `RecursionError` subclasses `RuntimeError`, pre-3.5 handlers still catch it. `sys.setrecursionlimit()` moves the guard rail but cannot remove the underlying finite stack.

---

## Pattern Classification

**This term is:** EXCEPTION CLASS

**Similar terms in this pattern:**

1. `RuntimeError` - The direct parent class; `RecursionError` is its specialized child
2. `MemoryError` - The heap-side resource-exhaustion sibling (this one is stack-side)
3. `OverflowError` - Another "limit exceeded" exception (numeric range)
4. `StackOverflow` (other languages) - The concept's name in C#/Java ecosystems; useful for recognizing established local terminology

**Pattern rule:** Exception classes are noun compounds ending with the pack's "error" word. `RecursionError` = the language's established CS term for "recursion" + "error," using the same recursion word taught in local CS courses.


---

## Etymology (Brief)

**English Origin:** Latin compounds

**Root meaning:** "Recursion" from Latin "recurrere" meaning "to run back" (re- "back" + currere "to run") - a process that runs back into itself. "Error" from Latin "error" meaning "wandering, mistake."

**Why Python uses this:** Before 3.5, exceeding the recursion limit raised a bare `RuntimeError` with a message string, which was awkward to catch specifically. Python 3.5 gave the condition its own class named after the mechanism at fault: recursion - the self-referential call pattern - exceeding its allowed depth. Subclassing `RuntimeError` preserved backward compatibility.

---

## Concept Explanation (Intermediate Level)

**What it does:**

Every function call in Python consumes a stack frame that lives until the call returns. Recursion - a function calling itself, directly or through intermediaries - stacks these frames up. Because CPython's frames live on a finite C stack and an unbounded pile of frames would crash the whole process, the interpreter enforces an artificial ceiling (default 1000, adjustable via `sys.setrecursionlimit()`). Exceeding it raises `RecursionError` - a catchable Python exception standing in for what would otherwise be an uncatchable, process-killing stack overflow.

The error appears in two quite different situations. The first is a bug: a missing or unreachable base case, so the recursion never terminates - no limit would be high enough, and the fix is correcting the logic. The second is a capacity problem: the algorithm is correct but the input is deeper than the limit - a 100,000-element linked list walked recursively, deeply nested JSON, or a `__repr__` that recurses into itself via a cyclic structure. There the fixes are rewriting iteratively, using explicit stacks, or (cautiously) raising the limit. Distinguishing the two cases is the core diagnostic skill this exception teaches.

`RecursionError` was added in Python 3.5 as a subclass of `RuntimeError`, so `except RuntimeError:` continues to catch it - a compatibility detail worth knowing when reading older code. It is also somewhat special among exceptions: it can be raised at almost any call site once depth is nearly exhausted, including inside handlers, so robust handling frees stack (returns) before doing real work. Note the conceptual neighbors: `MemoryError` is heap exhaustion, `RecursionError` is stack-depth exhaustion; other language ecosystems call the same phenomenon "stack overflow."

**Key behaviors:**

1. **Raised when depth passes the limit:** Any call - recursive or not - that would exceed `sys.getrecursionlimit()` raises `RecursionError`. In practice, recursion is what gets there, directly or mutually.

2. **Subclasses `RuntimeError` (3.5+):** `issubclass(RecursionError, RuntimeError)` is `True`. Code written for older Pythons that catches `RuntimeError` for deep recursion continues to work unchanged.

3. **The limit is a guard rail, not the resource:** `sys.setrecursionlimit(n)` changes the Python-level ceiling, but the real C stack is still finite - setting the limit too high trades a clean `RecursionError` for a hard interpreter crash. CPython also performs no tail-call optimization, so "clever" tail recursion does not avoid the limit.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Compound noun (problem domain + error type)
- **Action vs State:** STATE - names an error condition, not an action
- **Temporal aspect:** Instantaneous - occurs at the call that would exceed the depth limit

### Recommended Form

**Primary recommendation:** Use the recursion term your language's CS education actually teaches - in many languages that is a latinate borrowing, in others a native mathematical coinage - plus the pack's standard "error" word. Do not invent a new descriptive phrase when an established term exists.

**Forms to AVOID:**

- ❌ Paraphrases like "self-call-too-deep error" - recursion is a first-class CS concept with its own name in most traditions
- ❌ The pack's "iteration/repetition" word - recursion and iteration are contrasted concepts in every CS curriculum; borrowing the iteration term erases a distinction the language pack needs
- ❌ Verb forms - exception classes are noun compounds

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Recursion as mere repetition or recurrence of an event ("recurring payments")
- ❌ Meaning 2: Recursion in linguistics (nested clauses in grammar)
- ❌ Meaning 3: Iteration - looping over items WITHOUT self-reference
- ✅ Meaning 4: **A FUNCTION CALLING ITSELF (directly or mutually), consuming call-stack depth**

**Example:**

English "recursion" and its neighbors:

1. "The recurring theme of the novel" (recurrence/repetition) ❌
2. "Recursion lets grammars nest clauses infinitely" (linguistics) ❌
3. `for item in items:` (iteration - no self-call, bounded stack) ❌
4. `def f(n): return f(n - 1)` (self-referential call) ✅ **This is the Python meaning**

**Your translation should capture meaning #4: self-referential function calls. It must NOT reuse the word your pack chose for iteration - recursion vs. iteration is a contrast every CS curriculum teaches, and the exception names (`RecursionError` vs `StopIteration`) sit on opposite sides of it.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `RecursionError`, check these translations:**

- [ ] `RuntimeError` - The parent class; must share the same "error" word (and older code catches this for deep recursion)
- [ ] `StopIteration` - Uses the pack's ITERATION word; verify your recursion word is clearly distinct from it
- [ ] `MemoryError` - The heap-side resource sibling; the stack/heap contrast should survive translation
- [ ] `OverflowError` - Adjacent "exceeded a limit" concept; keep "overflow" vocabulary out of this term
- [ ] `def` / `return` - The keywords that appear in every recursive definition; prose about recursion should read naturally with them

**Consistency rule:**

Use your language's established CS term for recursion - the one taught alongside iteration in local curricula - plus the standard "error" word. Then verify the recursion term and the iteration term (used in `StopIteration`, `iter`, `for` documentation) are unmistakably different words.


### Functional relationships

**This term works WITH:**

1. **Recursive functions + `RecursionError`**: The code shape that raises it

```python
def walk(node):
    return walk(node.child)   # unbounded depth -> RecursionError
```

2. **`sys` + the recursion limit**:

```python
import sys
sys.getrecursionlimit()   # inspect the ceiling
sys.setrecursionlimit(n)  # move it (carefully)
```

**Common pairing:**

```python
import sys

# Diagnosing: bug vs. capacity
def depth(node):
    if node is None:          # base case present: capacity problem if it fails
        return 0
    return 1 + depth(node.left)

# Converting recursion to iteration - the standard fix
def depth_iterative(node):
    d = 0
    while node is not None:
        d += 1
        node = node.left
    return d

# Catching it defensively around untrusted structures
def safe_repr(obj):
    try:
        return repr(obj)       # cyclic objects can recurse inside repr
    except RecursionError:
        return "<unrepresentable: too deep>"

# Compatibility: both handlers catch the same failure
try:
    depth(pathological_tree)
except RuntimeError:           # pre-3.5 style - still works (parent class)
    pass
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM-HARD**

### Between MEDIUM and HARD

- The concept is universal, but the WORD for it is not: some languages borrowed the latinate term, others coined native mathematical vocabulary, and some communities use both in competition
- Similar-sounding "repetition/iteration" words create genuine collision risk in languages where the recursion and iteration terms share a root
- **AI confidence should be MEDIUM; human review recommended for the recursion term choice**

### Why MEDIUM-HARD for `RecursionError`

- Recursion is an abstract, self-referential concept with no everyday-language equivalent; every language solved the naming problem differently
- Languages with a settled latinate borrowing are near-MEDIUM: the term is settled
- Languages with native coinages or competing terms are near-HARD: the choice affects recognizability
- Must remain clearly distinct from the pack's iteration vocabulary
- The compound itself ("X error") is trivial once the recursion word is fixed

**For this term:** MEDIUM-HARD

**Rationale:** The difficulty is honest and lopsided: everything except the recursion word is mechanical, and the recursion word is genuinely hard in some languages. Where an unambiguous established term exists, confidence can be MEDIUM-HIGH; where the language has competing native and borrowed terms, or where the recursion and iteration words share a root, human review by someone who knows the local CS teaching tradition is strongly recommended.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures SELF-REFERENTIAL CALLS (not general repetition, not iteration)?
- [ ] Clearly indicates an ERROR occurred?
- [ ] Uses the recursion term local CS courses actually teach?

### 2. Linguistic Correctness

- [ ] Correct part of speech (compound noun)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization appropriate for exception class names?

### 3. Consistency

- [ ] Recursion word clearly DISTINCT from the iteration word in `StopIteration`?
- [ ] Same "error" word as `RuntimeError` (its parent) and siblings?
- [ ] No "overflow" vocabulary borrowed from `OverflowError`?

### 4. Usability

- [ ] Short enough (1-3 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Recognizable to someone who learned recursion in this language?

### 5. Cultural Appropriateness

- [ ] Preferred register chosen (native coinage vs. borrowed term) per local CS convention?
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
term: RecursionError
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
