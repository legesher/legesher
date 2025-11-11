# Python Keyword: `from` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** module_system (selective import)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `from` keyword is used with `import` to specify selective importing from a module - bringing specific names into the current namespace without importing the entire module. Syntax: `from module import name` loads only `name` from `module`.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Import specific function
from math import sqrt
print(sqrt(16))  # 4.0 - no need for math.sqrt()

# Import multiple items
from math import pi, sqrt, cos
print(pi)  # Direct access
```

**What this does:** `from module import name` imports specific items directly into current namespace. Access them without module prefix. `from math import sqrt` lets you use `sqrt()` instead of `math.sqrt()`.

### Example 2: Common Pattern

```python
# Import from package
from os.path import exists, join
if exists("file.txt"):
    path = join("dir", "file.txt")

# Import with alias
from collections import OrderedDict as OD
my_dict = OD()

# Import everything (discouraged)
from math import *  # Imports all public names

# Import from local module
from mymodule import MyClass, my_function
```

**What this does:** `from` allows importing from nested packages (`os.path`). Can combine with `as` for aliasing. `from module import *` imports all public names (discouraged - pollutes namespace). Can import from local modules in your project.

### Example 3: Edge Case

```python
# Relative imports (in packages)
from . import sibling  # From current package
from .. import parent  # From parent package
from ..sibling import module  # From sibling package

# from with multiple names
from collections import (
    defaultdict,
    Counter,
    OrderedDict
)

# from doesn't execute module multiple times
from math import pi  # Executes math module
from math import sqrt  # Uses cached module, just imports sqrt
```

**What this shows:** `from .` enables relative imports within packages (`.` = current, `..` = parent). Can use parentheses for multi-line imports. Module is still executed only once - `from` just selects what to import from it.

---

## Pattern Classification

**This term is:** MODULE SYSTEM KEYWORD (Selective Import)

**Similar terms in this pattern:**

1. `import` - Import entire module (paired with `from`)
2. `as` - Alias imported names (often used with `from...import`)
3. `.` (dot) - Used in relative imports (`from . import`)

**Pattern rule:** Module system keywords should express source/origin (from) or destination/identity (as). "From" indicates the source location of imported code.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `import` | importar | استيراد | 导入 | आयात |
| `as` | como | كـ | 作为 | के_रूप_में |
| `from` | **desde** | **من** | **从** | **से** |

---

## Etymology (Brief)

**English Origin:** Old English/Germanic

**Root meaning:** Old English "fram" (from, away, forth) from Proto-Germanic "fram" (forward, from). Preposition indicating source, origin, or starting point. "From" answers "where did it come from?" In programming, adapted to indicate source module for imports.

**Why Python uses this:** "From" naturally indicates source/origin of imported code. Reading `from math import sqrt` as "from the math module, import sqrt" is intuitive English. Alternative phrasings would be more verbose. Paired with `import` to create readable import statements.

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `from` keyword specifies the source module for selective importing. While `import math` imports the entire module as object `math`, `from math import sqrt` imports only `sqrt` directly into the current namespace. This provides direct access without module prefix.

Selective importing is useful for: convenience (shorter names - `sqrt()` vs `math.sqrt()`), clarity (shows exactly what's used from module), and namespace control (import only what's needed). However, importing specific names can make dependencies less obvious compared to seeing `module.name` usage.

`from` is required for: importing specific items from modules, relative imports within packages (`from . import`), and the `from module import *` pattern (which imports all public names - generally discouraged except in interactive use).

**Key behaviors:**

1. **Selective namespace population:** `from module import name` adds only `name` to current namespace, not `module`. After `from math import sqrt`, `sqrt` exists but `math` doesn't (unless separately imported).

2. **Still executes full module:** Even though importing selectively, Python still executes the entire source module once (or retrieves from cache). `from` doesn't change execution, only what names are imported.

3. **Enables relative imports:** `from . import sibling` imports from same package. `from .. import parent` imports from parent package. Relative imports only work within packages (directories with `__init__.py`).

4. **Works with `as` for aliasing:** `from collections import OrderedDict as OD` imports and immediately aliases. Combines `from` (source) with `as` (alias) for selective renamed import.

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Preposition (indicating source/origin)
- **Action vs State:** RELATION - indicates source location
- **Temporal aspect:** N/A - spatial/conceptual relation

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Preposition | "desde", "de", "de" - from |
| Germanic (de, nl, sv) | Preposition | "von", "van", "från" - from |
| Slavic (ru, pl, uk) | Preposition | "из", "z", "з" - from |
| Arabic | Preposition | "من" - min (from) |
| Chinese | Preposition | "从" - cóng (from) |
| Hindi | Postposition | "से" - se (from) |

**Primary recommendation:** Use the target language's preposition meaning "from" - indicating source, origin, or starting point. This should be the most common word for expressing origin.

**Forms to AVOID:**

- ❌ Using "out of" when simpler "from" exists
- ❌ Using "originating from" - too verbose
- ❌ Using "within" (wrong direction/meaning)

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `desde`
- **Form:** Preposition
- **Why it works:** "Desde" means "from" in Spanish (indicating origin/source). Natural for expressing source module. Works grammatically: "desde math importar sqrt". Standard in Spanish programming.

**Arabic:**

- **Translation:** `من` (min)
- **Form:** Preposition
- **Why it works:** "Min" means "from" in Arabic (indicating source). Universal Arabic preposition for origin. Natural for expressing module source. "من math استيراد sqrt" reads naturally.

**Chinese:**

- **Translation:** `从` (cóng)
- **Form:** Preposition
- **Why it works:** "Cóng" means "from" in Chinese (indicating source/origin). Single character. Standard Chinese preposition. "从 math 导入 sqrt" natural word order.

**Hindi:**

- **Translation:** `से` (se)
- **Form:** Postposition
- **Why it works:** "Se" means "from" in Hindi (indicating source). Standard Hindi postposition. Note: Hindi uses postpositions (after noun) not prepositions (before). "math से आयात sqrt" follows Hindi grammar.

### ❌ Common Translation Mistakes

**Mistake 1: Using compound "out of" instead of simple "from"**

- **Wrong:** `fuera_de` (Spanish - "out of")
- **Why wrong:** Too verbose. Python's `from` is short, simple preposition. "Fuera de" is compound phrase. Use simple one-word preposition.
- **Right:** `desde` (or `de` - simple from)

**Mistake 2: Using "origin" (noun) instead of "from" (preposition)**

- **Wrong:** `origen` (Spanish - "origin")
- **Why wrong:** Need preposition, not noun. "From" is preposition in phrase `from X import Y`. Can't replace preposition with noun.
- **Right:** `desde` (preposition)

**Mistake 3: Using "within" (wrong direction)**

- **Wrong:** `dentro` (Spanish - "within/inside")
- **Why wrong:** "Within" indicates location inside something. "From" indicates movement/source from something. Opposite directions. Need source preposition.
- **Right:** `desde` (indicating source)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES (minor)

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "From this point forward" (time - from now on)
- ✅ Meaning 2: **SOURCE/ORIGIN** (indicating where something comes from)
- ❌ Meaning 3: "Made from" (material composition - statue from marble)

**Example:**

English "from" can mean:
1. "From this point forward" (temporal) ❌
2. "from math import sqrt" (source module) ✅ **This is the Python meaning**
3. "Made from wood" (material) ❌ Related concept

**Your translation should capture meaning #2: indicating the source or origin module from which items are imported.**

Use the preposition for source/origin - the word answering "where does this come from?"

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `from`, check these translations:**

- [ ] `import` - Paired with from; must work grammatically together
- [ ] `as` - Often used together: `from X import Y as Z`
- [ ] Prepositions like `in` - Should use consistent grammatical forms
- [ ] Relative import dots (`.`, `..`)

**Consistency rule:**

`from module import name` should read as grammatical phrase in target language. Word order may need adjustment for target language grammar, but meaning should be clear.

**Example:**

Spanish: `desde math importar sqrt` - grammatically coherent phrase ✅
Alternative word order if more natural: `importar sqrt desde math`

### Functional relationships

**This term works WITH:**

1. **`from ... import ...`**:
```python
from module import name
```

2. **`from ... import ... as ...`**:
```python
from module import name as alias
```

**Common pairing:**

```python
# Basic from import
from math import sqrt
from os import getcwd

# Multiple items
from math import pi, sqrt, cos, sin

# From import with alias
from collections import OrderedDict as OD
from datetime import datetime as dt

# From nested module
from os.path import exists, join, dirname
from xml.etree import ElementTree

# From package import module
from mypackage import mymodule
from mypackage.subpackage import utilities

# Relative imports
from . import sibling_module
from .. import parent_module
from ..sibling_package import module

# From import everything (discouraged)
from math import *

# Multi-line from import
from collections import (
    Counter,
    defaultdict,
    OrderedDict,
    namedtuple
)

# From import with different item types
from mymodule import (
    MyClass,
    my_function,
    MY_CONSTANT
)

# Common standard library patterns
from typing import List, Dict, Optional
from pathlib import Path
from dataclasses import dataclass

# Typical imports organization
from __future__ import annotations  # Special future imports

import os  # Standard library imports
import sys

from typing import Any, Optional  # From imports after regular imports
from collections import defaultdict

import numpy as np  # Third-party imports
import pandas as pd

from myapp import models  # Local application imports
from myapp.utils import helpers
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear concept (source/origin)
- Universal preposition in all languages
- Simple grammatical element
- **AI confidence should be HIGH**

### Why EASY for `from`:

- Universal concept (source/origin)
- "From" preposition exists in every language
- Fundamental grammatical element
- Clear semantic mapping

**For this term:** EASY

**Rationale:** Every language has a preposition meaning "from" to indicate source or origin. It's one of the most fundamental spatial/relational prepositions. Translation is straightforward: use the language's basic "from" preposition.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures SOURCE/ORIGIN concept?
- [ ] Works with `import` to form coherent phrase?
- [ ] Natural for indicating module source?

### 2. Linguistic Correctness

- [ ] Correct part of speech (preposition/postposition)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python keywords)?

### 3. Consistency

- [ ] Works grammatically with `import` and `as`?
- [ ] Phrase "from X import Y" reads naturally?
- [ ] Consistent with other preposition translations?

### 4. Usability

- [ ] Short enough (1 word, ideally 2-4 characters)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (most common "from" word)?

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
term: from
language: es
translation: desde
form: preposition
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "desde" means "from" (indicating source/origin). Natural preposition for expressing module source. Works grammatically with "importar" (import) and "como" (as). Standard in Spanish programming.

**Alternatives considered:**

1. `de` (from - shorter) - Also valid; "desde" more explicit about origin
2. `fuera_de` (out of) - Too verbose; need simple preposition
3. `origen` (origin - noun) - Wrong part of speech; need preposition

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH. Source/origin prepositions are universal with clear translations.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-10
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
