# Python Keyword: `case` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** control flow (pattern branch)
**Python Version:** 3.10+
**Difficulty:** MEDIUM

---

## Quick Summary

The `case` keyword defines pattern branches within a `match` statement in Python 3.10+. Each `case` specifies a pattern to match against; when the pattern matches, its associated code block executes. It's always used inside `match` blocks, never standalone.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Basic case patterns
match status:
case "active":
print("System is active")
case "inactive":
print("System is inactive")
case "error":
print("Error state")
```

**What this does:** Each `case` defines a pattern (here, string literals). The `match` statement tests the value against each `case` in order. When a pattern matches, that block runs.

### Example 2: Common Pattern

```python
# Case with variable capture
match point:
case (0, 0):
print("Origin")
case (0, y):  # Captures y-coordinate
print(f"On Y-axis at y={y}")
case (x, 0):  # Captures x-coordinate
print(f"On X-axis at x={x}")
case (x, y):  # Captures both
print(f"Point at ({x}, {y})")

# Case with type patterns
match value:
case int(n):
print(f"Integer: {n}")
case str(s):
print(f"String: {s}")
case list(items):
print(f"List with {len(items)} items")
case _:
print("Unknown type")
```

**What this does:** `case` patterns can destructure data (tuples, lists, objects) and bind variables. Patterns can match types, values, structures, or combinations. Variables captured in patterns are available in the case block.

### Example 3: Edge Case

```python
# Case with guards (conditional patterns)
match age:
case n if n < 0:
print("Invalid age")
case n if 0 <= n < 18:
print(f"Minor: {n} years old")
case n if 18 <= n < 65:
print(f"Adult: {n} years old")
case n:
print(f"Senior: {n} years old")

# Case with OR patterns
match http_status:
case 200 | 201 | 204:
print("Success")
case 400 | 401 | 403 | 404:
print("Client error")
case 500 | 502 | 503:
print("Server error")
case code:
print(f"Unusual status: {code}")

# Case with complex patterns
match event:
case {"type": "click", "button": "left", "position": (x, y)}:
handle_left_click(x, y)
case {"type": "click", "button": "right"}:
show_context_menu()
case {"type": "keypress", "key": key} if key in ["Enter", "Space"]:
handle_activation(key)
case _:
ignore_event()
```

**What this shows:** `case` supports guards (`if` conditions after pattern), OR patterns with `|`, nested destructuring in dictionaries and sequences, and combining multiple pattern features. Patterns are checked top-to-bottom; first match wins.

---

## Pattern Classification

**This term is:** CONTROL FLOW KEYWORD (Pattern Branch)

**Similar terms in this pattern:**

1. `elif` - Alternative conditional branch (but for boolean conditions only)
2. `except` - Exception handling branch (similar structure, different purpose)
3. `match` - Pattern matching entry point (always paired with `case`)

**Pattern rule:** Branch keywords that introduce alternatives should use noun or conditional forms in target language—they represent "situations," "instances," or "alternatives" to check.


---

## Etymology (Brief)

**English Origin:** Latin

**Root meaning:** From Latin "casus" meaning "fall, occurrence, event, situation"—from "cadere" (to fall). In grammar, "case" refers to noun forms (nominative, accusative, etc.). In general use, "case" means "instance," "situation," or "circumstance."

**Why Python uses this:** "Case" conveys "in the case that this pattern matches" or "in this particular instance." Borrowed from law terminology ("in the case of X") and from `switch/case` syntax in C-family languages. However, Python's `case` is more powerful—it's not just matching values but matching structural patterns.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `case` keyword, introduced with `match` in Python 3.10 via PEP 634, defines individual pattern branches within a pattern matching block. Each `case` specifies a pattern that the subject (the value after `match`) is tested against. When a pattern matches, Python executes that case's block and then exits the entire `match` statement—there's no fall-through.

`case` patterns range from simple literal values (`case 42:`) to complex structural patterns that destructure data and bind variables. You can match sequences (`case [x, y, z]:`), mappings (`case {"key": value}:`), class instances (`case Point(x=0, y=y):`), or combine patterns with OR (`case 1 | 2 | 3:`). Guards add conditional refinement: `case x if x > 0:` only matches positive values.

The power of `case` lies in pattern expressiveness. Unlike `if-elif` chains that only test boolean conditions, `case` patterns simultaneously check types, destructure data, bind variables, and validate structure. This makes code clearer for parsing inputs, handling multiple formats, implementing state machines, or processing tree-like data.

**Key behaviors:**

1. **Order matters—first match wins:** Python tests `case` patterns top-to-bottom. The first matching pattern executes; remaining cases are skipped. Put specific patterns before general ones: `case (0, 0):` before `case (x, y):`. A bare `case _:` (wildcard) matches everything, so it's typically last as a default/catch-all.

2. **Variable binding and scoping:** Patterns can capture parts of the matched value: `case (x, y):` binds tuple elements to variables `x` and `y` available within that case block. These are fresh bindings—they don't clash with outer scope variables. Names in patterns are always new captures, except for `_` which is a wildcard.

3. **Guards refine matches:** Add `if condition` after pattern: `case x if x > 0:`. The guard evaluates after the pattern matches, providing fine-grained control. Without guards, you'd need nested `if` statements inside case blocks. Guards keep conditions close to patterns for readability.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun (represents a situation/instance/alternative)
- **Action vs State:** STATE/INSTANCE - describes a particular scenario
- **Temporal aspect:** Static - each case is a possibility to check

### Recommended Form

**Primary recommendation:** Use noun form meaning "case," "instance," "situation," or "alternative" in target language. Should pair naturally with `match` (verb): "match against these cases."

**Forms to AVOID:**

- ❌ Verb form ("to case") - `case` is a noun, not action
- ❌ Adjective form - doesn't capture "instance" meaning
- ❌ Same word as other keywords - must be distinct

---


## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**Identify the CORRECT meaning for Python:**

- ❌ Meaning 1: Container/box (suitcase, briefcase)
- ❌ Meaning 2: Grammatical case (nominative, accusative)
- ❌ Meaning 3: Medical case (patient)
- ✅ Meaning 4: **Instance/situation/scenario** (in the case of...) ← CORRECT

**In programming context, "case" means:**

A particular instance, situation, or alternative to check. "In the case that this pattern matches, do this." Similar to legal terminology: "in the case of X vs Y" or "if this is the case."

**Your translation should capture meaning #4 (instance/situation), NOT the other meanings.**

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `case`, check these translations:**

- [ ] `match` - Entry point; `case` always used inside `match` blocks
- [ ] `if` - Basic conditional; `case` is pattern-based alternative
- [ ] `elif` - Chained conditional; similar concept but different syntax

**Consistency rule:**

`match` and `case` are syntactically inseparable—you cannot have `case` without `match`. The pairing should feel natural: `match` (verb: perform matching) against `case` (noun: instances/patterns). Think grammatically: "match [value] against these cases."


### Functional relationships

**This term works WITH:**

1. **`match` + `case` (required pairing)**:

```python
match value:
case pattern1:
action1()
case pattern2:
action2()
case _:
default_action()
```

2. **`case` with guards**:

```python
match score:
case n if n >= 90:
grade = "A"
case n if n >= 80:
grade = "B"
```

**Common pairing:**

```python
# Typical match/case structure
def describe_point(point):
match point:
case (0, 0):
return "Origin"
case (0, y):
return f"Y-axis at {y}"
case (x, 0):
return f"X-axis at {x}"
case (x, y):
return f"Point ({x}, {y})"
case _:
return "Not a point"

# Case with OR patterns
match command:
case "quit" | "exit" | "q":
exit_program()
case "help" | "h" | "?":
show_help()
case cmd:
execute_command(cmd)

# Case with nested patterns
match event:
case {"type": "mouse", "action": "click", "pos": (x, y)}:
handle_click(x, y)
case {"type": "keyboard", "key": key} if key.isprintable():
insert_char(key)
case _:
pass  # Ignore other events
```

---

## Confidence Calibration

**Translation Difficulty: MEDIUM**

### Why MEDIUM for `case`

- Relatively new feature (Python 3.10+, introduced 2021)
- Must distinguish from older `switch/case` in other languages
- English word has multiple meanings (requires disambiguation)
- Pattern matching concepts may not be established in all languages
- Must pair naturally with `match` translation

**For this term:** MEDIUM

**Rationale:** While "case" as a noun is straightforward, choosing the correct meaning (instance/situation rather than container/box) requires understanding the pattern matching context. Additionally, `case` must pair grammatically with `match`, so translations are interdependent. Some languages may not have established conventions for pattern matching terminology yet.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures "instance/situation" meaning (not box/container)?
- [ ] Conveys pattern branch concept?
- [ ] Works within pattern matching context?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun)?
- [ ] Natural in target language?
- [ ] Proper gender/number if applicable?
- [ ] Capitalization correct (lowercase for keywords)?

### 3. Consistency

- [ ] Pairs naturally with `match` translation?
- [ ] Distinct from `if`, `elif`, `except`?
- [ ] Consistent with control flow keyword patterns?

### 4. Usability

- [ ] Reasonably short (1-2 words)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Memorable?

### 5. Cultural Appropriateness

- [ ] No offensive meanings?
- [ ] Professional terminology?
- [ ] Suitable for technical documentation?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Renders properly in IDEs?
- [ ] No syntax highlighting conflicts?

---

## Translation Output Format

**Your translation:**

```yaml
term: case
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
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
