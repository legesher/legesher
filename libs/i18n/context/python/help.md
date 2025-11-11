# Python Builtin Function: `help` - Translation Brief (Tier 1)

**Category:** builtin_function
**Type:** noun/verb (documentation access)
**Python Version:** 3.x+
**Difficulty:** LOW

---

## Quick Summary

The `help` function in Python displays documentation for objects, modules, functions, and classes. It's an interactive documentation system that shows docstrings and usage information, essential for learning and exploring Python code.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Get help on a builtin function
help(print)
# Displays documentation about print() function

# Get help on a type
help(str)
# Shows all string methods and documentation
```

**What this does:** Displays formatted documentation for the given object. Shows description, parameters, return values, and examples when available.

### Example 2: Common Pattern

```python
# Help on modules
import math
help(math)  # Shows all math module functions

# Help on your own functions
def greet(name):
    """Say hello to someone.

    Args:
        name: The person's name
    """
    print(f"Hello, {name}!")

help(greet)  # Displays your docstring

# Help without arguments opens interactive help
# help()  # Opens interactive help system
```

**What this does:** Works with any Python object. Your own functions' docstrings appear in help. Without arguments, `help()` enters interactive mode.

### Example 3: Edge Case

```python
# Help on methods
help(list.append)  # Documentation for list.append method

# Help on keywords (as strings)
help('if')  # Shows documentation about if statements
help('for')  # Shows for loop documentation

# Exit help with quit
# In interactive help mode, type 'quit' to exit
```

**What this shows:** Can get help on methods, keywords (as strings), and any Python object. Interactive mode allows exploring documentation conversationally.

---

## Pattern Classification

**This term is:** UTILITY FUNCTION (Documentation/Information Access)

**Similar terms in this pattern:**

1. `dir` - Lists attributes and methods of an object
2. `vars` - Returns __dict__ attribute of an object
3. `id` - Returns unique identifier of object
4. `isinstance` - Checks object type

**Pattern rule:** Utility/introspection functions can be either nouns (describing what they provide) or verbs (describing what action they perform). "Help" works as both.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `dir` | directorio | دليل | 目录 | निर्देशिका |
| `print` | imprimir | طباعة | 打印 | प्रिंट |
| `help` | **ayuda** | **مساعدة** | **帮助** | **सहायता** |

---

## Etymology (Brief)

**English Origin:** Germanic

**Root meaning:** From Old English "helpan" meaning "to assist, support, succor." The noun "help" means assistance or aid. In computing, "help" universally refers to documentation, assistance systems, or support features.

**Why Python uses this:** "Help" is the universal term across all software for documentation and assistance systems. Every operating system, application, and programming environment uses "help" or its translation. Python's `help()` provides interactive assistance, making the choice natural and intuitive.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `help()` function provides access to Python's interactive documentation system. It displays docstrings (documentation strings) embedded in Python objects—functions, classes, modules, and methods. When called with an object, it formats and displays that object's `__doc__` attribute along with other useful information.

Without arguments, `help()` enters interactive mode where you can type names to explore documentation conversationally. This is particularly useful for beginners exploring Python or learning new libraries. The system uses Python's pager (like `less` on Unix) for long documentation.

Help displays information from multiple sources: built-in docstrings, automatically generated descriptions of objects, and formatted output showing inheritance hierarchies, method lists, and parameter information. It's essentially an interactive version of reading documentation, accessible from within Python itself.

**Key behaviors:**

1. **Reads docstrings:** Displays the `__doc__` attribute of objects. If you write docstrings for your functions/classes, they appear in `help()`. This encourages documentation as part of code.

2. **Interactive mode:** `help()` without arguments enters interactive help where you can explore by typing object names. Type `quit` to exit. This mode is great for exploration and learning.

3. **Works on everything:** Can get help on modules, functions, classes, methods, built-in types, keywords (as strings), and even packages. If it exists in Python, you can probably `help()` it.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Noun/Imperative verb (both interpretations valid)
- **Action vs State:** ACTION - provides assistance/documentation
- **Temporal aspect:** Instantaneous - retrieves and displays help immediately

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Noun | "ayuda", "aide" - assistance/help |
| Germanic (de, nl, sv) | Noun | "Hilfe", "hulp" - help/assistance |
| Slavic (ru, pl, uk) | Noun | "помощь", "pomoc" - help |
| Arabic | Noun (masdar) | "مساعدة" - help/assistance |
| Chinese | Noun/Verb | "帮助" - help (works as both) |
| Hindi | Noun | "सहायता" - help/assistance |

**Primary recommendation:** Use noun form meaning "help" or "assistance." While "help" can be verb or noun in English, most languages prefer noun form for function names (represents what the function provides).

**Forms to AVOID:**

- ❌ Using "manual" or "documentation" (too specific; help is broader)
- ❌ Using "support" when "help" is more common
- ❌ Using imperative verb form if target language has clear noun preference

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `ayuda`
- **Form:** Noun (feminine)
- **Why it works:** Standard Spanish word for help/assistance. Used universally in Spanish software interfaces for help systems. Clear, concise, immediately understood. Natural in "obtener ayuda" (get help).

**Arabic:**

- **Translation:** `مساعدة` (musāʿada)
- **Form:** Masdar/verbal noun (feminine)
- **Why it works:** Standard Arabic word for help/assistance. Used in all Arabic software interfaces for help menus and documentation access. Clear and universally recognized.

**Chinese:**

- **Translation:** `帮助` (bāngzhù)
- **Form:** Verb-complement compound (works as noun/verb)
- **Why it works:** Two characters: 帮 (help/assist) + 助 (aid/assist). Standard Chinese term for help systems in software. Used universally in Chinese computing interfaces.

**Hindi:**

- **Translation:** `सहायता` (sahāytā)
- **Form:** Noun (feminine)
- **Why it works:** Sanskrit-derived Hindi word meaning help/assistance. Formal technical term used in Hindi software interfaces. Clear and professional. Aligns with formal Hindi computing vocabulary.

### ❌ Common Translation Mistakes

**Mistake 1: Using "manual" or "documentation"**

- **Wrong:** `manual` (Spanish)
- **Why wrong:** "Manual" is too specific (implies a comprehensive manual/book). "Help" is broader—immediate assistance. Software uses "ayuda" for help systems, not "manual."
- **Right:** `ayuda` (help/assistance)

**Mistake 2: Using imperative verb form**

- **Wrong:** `ayudar` (Spanish infinitive - "to help")
- **Why wrong:** While grammatically an infinitive, function names should typically be nouns naming what they provide, not infinitive verbs. "Ayuda" (help noun) is standard in Spanish computing.
- **Right:** `ayuda` (help as noun)

**Mistake 3: Using "support"**

- **Wrong:** `soporte` (Spanish - "support")
- **Why wrong:** "Support" implies technical support/customer service. "Help" specifically means documentation/assistance system. "Ayuda" is the standard term in Spanish software.
- **Right:** `ayuda` (help/assistance)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (minor ambiguity)

**If YES, identify the CORRECT meaning for Python:**

- ⚠️ Meaning 1: "To help someone" (verb: provide assistance)
- ✅ Meaning 2: **HELP SYSTEM/DOCUMENTATION** (noun: assistance system)
- ❌ Meaning 3: "Hired help" (noun: employee/servant - archaic)

**Example:**

English "help" can mean:

1. "Can you help me?" (verb: assist) ⚠️ Related but verb form
2. "Click the Help menu" (noun: documentation system) ✅ **This is the Python meaning**
3. "We need to hire help" (noun: workers) ❌ Archaic

**Your translation should capture meaning #2: a documentation/assistance system—the noun form referring to the help facility, not the verb "to help."**

Note: Meanings 1 and 2 are closely related (one is verb, one is noun of same concept). Choose the form your language uses for software help systems.

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `help`, check these translations:**

- [ ] `dir` - Related introspection function; should feel related
- [ ] `print` - Common utility function; check grammatical consistency
- [ ] `input` - User interaction function; should use compatible form
- [ ] `type` - Introspection function; alignment in style

**Consistency rule:**

Utility functions can mix nouns and verbs depending on what they do. `help` is typically noun (what it provides), while `print` might be verb (what it does). Follow natural usage in target language's software interfaces.

**Example:**

Spanish: `ayuda` (noun), `imprimir` (verb), `entrada` (noun), `tipo` (noun) ✅
This mix is fine—follow what each represents

### Functional relationships

**This term works WITH:**

1. **Learning and exploration**: Discovering Python features
```python
help(str)  # What can strings do?
help(list.append)  # How does append work?
```

2. **Documenting your code**: Displaying your docstrings
```python
def my_func():
    """This is my function."""
    pass

help(my_func)  # Shows your docstring
```

**Common pairing:**

```python
# Basic help usage
help(print)  # Documentation for print()
help(len)    # Documentation for len()
help(str)    # All string methods

# Help on modules
import math
help(math)  # All math functions and constants

# Help on your own code
def calculate_area(radius):
    """Calculate the area of a circle.

    Args:
        radius (float): The radius of the circle

    Returns:
        float: The area of the circle
    """
    return 3.14159 * radius ** 2

help(calculate_area)  # Shows your docstring formatted

# Help on methods
help(list.append)
help(str.split)
help(dict.get)

# Help on keywords (as strings)
help('if')
help('for')
help('def')

# Interactive help mode
# help()  # No argument - enters interactive mode
# Type object names to explore
# Type 'quit' to exit

# Help in IPython/Jupyter (alternative syntax)
# ?print  # Short help
# ??print  # Detailed help including source (IPython specific)

# Accessing __doc__ directly (what help uses)
print(len.__doc__)  # Same info help() displays
```

---

## Confidence Calibration

**Translation Difficulty: LOW**

### LOW

- Universal concept across all software
- Every language has standard term for help systems
- Used identically in all software interfaces
- **AI confidence should be HIGH**

**For this term:** LOW

**Rationale:** "Help" as a documentation/assistance system is universal across all software—operating systems, applications, websites, and programming environments. Every language has a standard term used consistently in software interfaces for help menus and documentation access.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures HELP/DOCUMENTATION SYSTEM concept?
- [ ] Would a native speaker recognize this from software interfaces?
- [ ] Matches how help systems are labeled in target language software?

### 2. Linguistic Correctness

- [ ] Correct part of speech (noun preferred)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python builtins)?

### 3. Consistency

- [ ] Matches how "Help" appears in software menus in target language?
- [ ] Aligns with standard software terminology?
- [ ] Compatible with other utility function translations?

### 4. Usability

- [ ] Short enough (1-2 words maximum)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (universal software term)?

### 5. Cultural Appropriateness

- [ ] No offensive meanings in target culture?
- [ ] Not childish or unprofessional?
- [ ] Respects regional sensitivities?

### 6. Technical Compatibility

- [ ] Uses correct character set for language?
- [ ] Will render properly in IDEs?
- [ ] No special characters that break syntax highlighting?

---

## Translation Output Format

**Your translation:**

```yaml
term: help
language: es
translation: ayuda
form: noun (feminine)
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "ayuda" is the universal standard term for help systems across all Spanish software interfaces—from operating systems to applications to websites. It clearly conveys access to documentation and assistance. Every Spanish-speaking computer user recognizes "ayuda" as the help/documentation menu.

**Alternatives considered:**

1. `ayudar` (infinitive verb "to help") - Grammatically possible but "ayuda" (noun) is standard in software
2. `soporte` (support) - Implies technical support team, not documentation system
3. `manual` (manual) - Too specific; implies comprehensive manual rather than context-sensitive help

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH. "Ayuda" is universally used across all Spanish software interfaces and is immediately recognized by all Spanish-speaking users as the help system.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-11
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
