# Python Builtin: `eval` - Translation Brief (Tier 1)

**Category:** builtin
**Type:** function
**Python Version:** 3.x+
**Difficulty:** HIGH

---

## Quick Summary

`eval()` evaluates a Python expression string and returns the result, powerful but dangerous as it executes arbitrary code - use only with trusted input.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Basic expression evaluation
result = eval("2 + 3 * 4")
print(result)  # Output: 14

# Evaluate variable expressions
x = 10
result = eval("x * 2 + 5")
print(result)  # Output: 25
```

**What this does:** `eval()` takes a string containing a Python expression, evaluates it, and returns the result. Can access variables from the current scope.

### Example 2: Common Pattern

```python
# User input evaluation (DANGEROUS!)
# DON'T DO THIS with untrusted input
expression = input("Enter a math expression: ")
# User enters: 3 * 7 + 2
result = eval(expression)
print(f"Result: {result}")  # Output: Result: 23

# Safer: restricted namespace
safe_dict = {"x": 10, "y": 20}
result = eval("x + y", {"__builtins__": {}}, safe_dict)
print(result)  # Output: 30
# Can only access x and y, no builtins
```

**What this does:** Shows both dangerous unrestricted eval() and safer restricted eval() with custom namespace. Restricting builtins prevents access to dangerous functions like `__import__`, `open`, etc.

### Example 3: Edge Case

```python
# SECURITY WARNING: eval is dangerous
dangerous_input = "__import__('os').system('ls')"
# eval(dangerous_input)  # DON'T RUN - executes system command!

# eval vs exec
eval_result = eval("2 + 2")  # Returns value: 4
# exec_result = exec("2 + 2")  # Returns None, can run statements

# eval only works with expressions, not statements
try:
eval("x = 5")  # SyntaxError!
except SyntaxError:
print("eval only handles expressions")

# Use exec for statements
exec("x = 5")  # Works
print(x)  # Output: 5

# Alternative to eval: ast.literal_eval (safe for literals)
import ast
safe_data = ast.literal_eval("{'key': [1, 2, 3]}")
print(safe_data)  # Output: {'key': [1, 2, 3]}
# ast.literal_eval can't execute code, only parse literals
```

**What this shows:** `eval()` is a major security risk with untrusted input. It can execute arbitrary code, access the filesystem, import modules, etc. Use `ast.literal_eval()` for safe parsing of literal data structures, or avoid eval entirely. `eval()` is for expressions only; `exec()` is for statements.

---

## Pattern Classification

**This term is:** CODE EVALUATION FUNCTION (Dynamic execution)

**Similar terms in this pattern:**

1. `exec` - Executes Python statements (not expressions)
2. `compile` - Compiles code to bytecode
3. `__import__` - Dynamic module importing

**Pattern rule:** Dynamic code execution functions should clearly indicate they execute or evaluate code. These are advanced and potentially dangerous functions.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `exec` | ejecutar | تنفيذ | 执行 | निष्पादन |
| `compile` | compilar | تجميع | 编译 | संकलन |
| `eval` | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** | **YOUR TRANSLATION** |

---

## Etymology (Brief)

**English Origin:** Short for "evaluate"

**Root meaning:** From Latin "valere" (to be strong, be worth). "Evaluate" means to determine the value or worth of something.

**Why Python uses this:** In programming, "eval" means to evaluate an expression to determine its value. The term comes from Lisp and other languages where evaluating code dynamically is fundamental. Python's `eval()` evaluates a string as a Python expression and returns its value.

---

## Concept Explanation (Intermediate Level)

**What it does:**

`eval()` takes a string containing a Python expression, parses it, compiles it to bytecode, executes it, and returns the result. It's like typing code into the Python REPL - the string is evaluated as if it were actual Python code.

The function has access to the current scope by default, meaning it can read and use variables from where it's called. You can restrict this by passing custom global and local namespaces, limiting what code can access. This is crucial for security.

`eval()` is extremely dangerous with untrusted input. A malicious user can inject code that deletes files, steals data, or compromises your system. Modern Python applications avoid eval() or use heavily restricted namespaces. Alternatives include `ast.literal_eval()` for safe data parsing or proper parsing libraries for domain-specific languages.

**Key behaviors:**

1. **Expressions only:** Can only evaluate expressions (that return values), not statements (like assignments, loops). For statements, use `exec()`.
2. **Returns value:** Returns the result of evaluating the expression, unlike `exec()` which returns None.
3. **Security hazard:** Executes arbitrary code with full Python capabilities unless namespace is restricted. Never use with untrusted input without heavy sandboxing.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Function name (action verb)
- **Action vs State:** ACTION - performs evaluation
- **Temporal aspect:** Instantaneous action (evaluates and returns)

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Infinitive verb | evaluar, évaluer (to evaluate) |
| Germanic (de, nl, sv) | Infinitive verb | evaluieren, evalueren |
| Slavic (ru, pl, uk) | Infinitive verb | вычислить, оценить |
| Arabic | Verbal noun (masdar) | تقييم (taqyīm - evaluation) |
| Chinese | Verb | 求值 (qiúzhí - evaluate value) |
| Hindi | Infinitive verb | मूल्यांकन (mūlyāṅkan - evaluate) |

**Primary recommendation:** Use a verb meaning "to evaluate," "to assess value," or "to compute value." Should convey the act of determining the value of an expression.

**Forms to AVOID:**

- ❌ Noun forms - this is an action (function), not a thing
- ❌ "Run" or "execute" - those imply statements; eval is for expressions/values
- ❌ Too generic terms that don't convey "finding the value"

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `eval` (borrowed) or `evaluar`
- **Form:** Infinitive verb
- **Why it works:** "Evaluar" means "to evaluate" in Spanish; "eval" is also widely recognized in programming. Either works depending on language pack philosophy.

**Arabic:**

- **Translation:** `تقييم` (taqyīm - evaluation/assess)
- **Form:** Verbal noun (masdar)
- **Why it works:** Technical term for evaluation, appropriate for computing value of expression

**Chinese:**

- **Translation:** `求值` (qiúzhí - evaluate/compute value)
- **Form:** Verb compound
- **Why it works:** Standard CS term, literally "seek value" - captures the concept of determining expression value

**Hindi:**

- **Translation:** `मूल्यांकन` (mūlyāṅkan - evaluate) or `गणना` (gaṇanā - compute)
- **Form:** Verbal noun/infinitive
- **Why it works:** Formal term for evaluation, appropriate for computing expression values

### ❌ Common Translation Mistakes

**Mistake 1: Using "execute" instead of "evaluate"**

- **Wrong:** `ejecutar` (Spanish - execute)
- **Why wrong:** "Execute" is for `exec()` (statements); "eval" is for expressions (finding values)
- **Right:** `evaluar` (evaluate - finding value)

**Mistake 2: Too vague or generic**

- **Wrong:** `hacer` (Spanish - "to do/make")
- **Why wrong:** Too generic, doesn't capture the specific concept of evaluating to find value
- **Right:** `evaluar` (evaluate specifically)

**Mistake 3: Using noun instead of verb**

- **Wrong:** `evaluación` (Spanish - "evaluation" noun)
- **Why wrong:** Function names should be verbs (infinitive), not nouns
- **Right:** `evaluar` (infinitive verb)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (in broader context), but Python meaning is specific

**Python-specific meaning:**

✅ **Python meaning:** Evaluate a Python expression string and return its computed value.

In general English, "evaluate" can mean assess, judge, or appraise in many contexts. In Python/programming, it specifically means "compute the value of an expression." Your translation should use the technical computing sense.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `eval`, check these translations:**

- [ ] `exec` - Related function, should be distinguishable (eval=expressions, exec=statements)
- [ ] `compile` - Related to code compilation/execution
- [ ] `return` - Both relate to producing values

**Consistency rule:**

While `eval` and `exec` are related, they should be distinguishable:

- `eval` = evaluate expression to get value (returns result)
- `exec` = execute statements (returns None)

If using "evaluate" for eval, consider "execute" for exec to maintain the distinction.

**Example:**

✅ **Consistent and distinguishable:**

- `eval` → `evaluar` (evaluate)
- `exec` → `ejecutar` (execute)
- Clear distinction ✅

❌ **Not distinguishable:**

- `eval` → `ejecutar` (execute)
- `exec` → `ejecutar` (execute)
- Same translation for different concepts ❌

### Functional relationships

**This term works WITH:**

1. **`eval` + string expression**: Evaluates string as code
2. **`eval` vs `exec`**: eval for expressions, exec for statements
3. **`compile` + `eval`**: Can eval compiled code objects

**Common pairing:**

```python
# eval for expressions (returns value)
result = eval("2 + 2")

# exec for statements (no return value)
exec("x = 5")
```

---

## Confidence Calibration

**Translation Difficulty: HIGH**

### HIGH

- Security-critical function
- Must distinguish from `exec`
- Technical concept (expression evaluation)
- **AI confidence should be MEDIUM, human review recommended**

**For this term:** HIGH

**Rationale:** While "evaluate" is a common word, using it correctly in the technical sense (computing expression values) and distinguishing it from `exec` (executing statements) requires understanding of Python's execution model. The security implications also make this a high-stakes translation.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Conveys "evaluate expression to get value"?
- [ ] Distinguishable from `exec` (statements)?
- [ ] Would programmers understand this computes values?

### 2. Linguistic Correctness

- [ ] Verb form (infinitive)?
- [ ] Appropriate for "finding/computing value"?
- [ ] Technical register?

### 3. Consistency

- [ ] Distinguishable from `exec` translation?
- [ ] Compatible with related code execution terms?
- [ ] Matches CS terminology in target language?

### 4. Usability

- [ ] Concise (1 word preferred)?
- [ ] Clear meaning?
- [ ] Recognizable to programmers?

### 5. Cultural Appropriateness

- [ ] Professional register?
- [ ] No offensive meanings?

### 6. Technical Compatibility

- [ ] Renders properly in IDEs?
- [ ] No syntax issues?

---

## Translation Output Format

**Your translation:**

```yaml
term: eval
language: {es|ar|zh|hi}
translation: {your_translation}
form: {infinitive_verb}
confidence: {high|medium|low}
```

**Rationale (2-3 sentences):**

{Explain that you chose a verb meaning "evaluate" or "compute value," emphasizing expression evaluation (not statement execution). Mention distinction from `exec` if relevant.}

**Alternatives considered:**

1. `{alternative_1}` - {Why you didn't choose this}
2. `{alternative_2}` - {Why you didn't choose this}

**If confidence is not HIGH, explain:**

{Need to verify distinction from `exec`, check CS terminology for "evaluate expression"}

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
