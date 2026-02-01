# Python Keyword: `import` - Translation Brief (Tier 1)

**Category:** keyword
**Type:** module_system (import statement)
**Python Version:** 3.x+
**Difficulty:** EASY

---

## Quick Summary

The `import` keyword loads external modules, packages, or specific objects into the current namespace, making their functionality available for use. It's Python's mechanism for code reuse and accessing the standard library or third-party packages.

---

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
# Import entire module
import math
print(math.pi)  # 3.14159...

# Import with alias
import numpy as np
array = np.array([1, 2, 3])
```

**What this does:** `import` loads a module (file or package) into current namespace. Access module's contents using dot notation: `module.name`. Modules can be aliased with `as` for shorter names.

### Example 2: Common Pattern

```python
# Multiple imports
import os
import sys
import json

# Import from module
from math import pi, sqrt
print(pi)  # No need for math.pi

# Import all from module (discouraged)
from collections import *

# Import submodule
import os.path
print(os.path.exists("file.txt"))
```

**What this does:** Can import multiple modules with separate `import` statements. `from module import name` imports specific items. `import module.submodule` accesses nested packages. `from module import *` imports everything (usually discouraged).

### Example 3: Edge Case

```python
# Conditional import
if platform == "windows":
    import winsound
else:
    import ossaudiodev

# Import in function
def process_data():
    import pandas as pd  # Local import
    return pd.DataFrame(data)

# Import order matters for circular dependencies
import a  # If a imports b, and b imports a = circular dependency
```

**What this shows:** Imports can appear anywhere (typically at top of file). Conditional imports load different modules based on runtime conditions. Local imports (inside functions) delay loading. Circular imports can cause errors if not handled carefully.

---

## Pattern Classification

**This term is:** MODULE SYSTEM KEYWORD (Import Mechanism)

**Similar terms in this pattern:**

1. `from` - Often paired with `import` to import specific items
2. `as` - Aliases imports for shorter names
3. `__import__()` - Built-in function for dynamic imports

**Pattern rule:** Import/module keywords should use verbs expressing bringing in or loading external code. "Import" means to bring in from outside.

**Existing translations (for consistency):**

| Term | Spanish | Arabic | Chinese | Hindi |
|------|---------|--------|---------|-------|
| `from` | desde | من | 从 | से |
| `as` | como | كـ | 作为 | के_रूप_में |
| `import` | **importar** | **استيراد** | **导入** | **आयात** |

---

## Etymology (Brief)

**English Origin:** Latin via French

**Root meaning:** Latin "importare" meant "bring in, convey" (from "in-" + "portare" to carry). Through French "importer," it became English "import" - to bring goods from foreign countries. In programming, adapted to mean bringing in external code modules.

**Why Python uses this:** "Import" naturally expresses bringing external functionality into your program. Metaphor of importing goods from other countries maps to importing code from other modules. Standard across many programming languages (Java, JavaScript, Go).

---

## Concept Explanation (Intermediate Level)

**What it does:**

The `import` statement loads Python modules (files containing Python code) and makes their contents accessible. When you `import math`, Python searches for `math.py` in the standard library, executes it once (if not already loaded), and creates a namespace object `math` containing the module's functions and variables.

Imports enable code reuse: instead of writing everything yourself, import standard library modules (`os`, `sys`, `math`) or third-party packages (`numpy`, `pandas`, `requests`). Python's "batteries included" philosophy means the standard library has extensive functionality accessible via imports.

Import mechanism: Python maintains `sys.modules` cache of loaded modules. First import of a module executes its code; subsequent imports return cached object. This prevents re-execution. Import searches directories in `sys.path` to find modules.

**Key behaviors:**

1. **Executes module code once:** First time a module is imported, Python executes its code top-to-bottom. Subsequent imports return cached module object. Module-level code runs once per interpreter session.

2. **Creates namespace:** `import math` creates name `math` in current namespace, bound to the module object. Access contents via dot notation: `math.pi`, `math.sqrt()`. Keeps module contents organized and prevents name conflicts.

3. **Search path:** Python searches `sys.path` directories to find modules. This includes: current directory, PYTHONPATH environment variable, standard library directories, and site-packages (third-party packages).

4. **Different import styles:** `import module` imports whole module. `from module import name` imports specific items into current namespace. `import module as alias` creates alias. `from module import *` imports all public names (discouraged - pollutes namespace).

---

## Linguistic Form Recommendation

### Part of Speech

**In Python context:**

- **Grammatical role:** Verb (imperative - command to import/load)
- **Action vs State:** ACTION - command to load external code
- **Temporal aspect:** Instantaneous - immediate loading (or cached retrieval)

### Recommended Form by Language Family

| Language Family | Recommended Form | Rationale |
|-----------------|------------------|-----------|
| Romance (es, fr, pt, it) | Verb (imperative/infinitive) | "importar", "importer" - to import |
| Germanic (de, nl, sv) | Verb (infinitive) | "importieren", "importeren" - to import |
| Slavic (ru, pl, uk) | Verb (imperative) | "импортировать", "importować" - to import |
| Arabic | Verb (imperative) | "استيراد" - istīrād (import) |
| Chinese | Verb compound | "导入" - dǎorù (lead in/import) |
| Hindi | Verb/noun | "आयात" - āyāt (import) |

**Primary recommendation:** Use verb form meaning "to import" or "to bring in" (imperative or infinitive). This should convey loading external resources.

**Forms to AVOID:**

- ❌ Using "include" (C/C++ term - different semantics)
- ❌ Using "require" (Ruby/JavaScript term - while similar, maintain "import")
- ❌ Using "load" when "import" is more specific

---

## Translation Examples (Good & Bad)

### ✅ Good Translations

**Spanish:**

- **Translation:** `importar`
- **Form:** Verb (infinitive)
- **Why it works:** "Importar" means "to import" in Spanish (bring in from outside). Direct translation of import metaphor. Standard in Spanish programming. Natural verb form.

**Arabic:**

- **Translation:** `استيراد` (istīrād)
- **Form:** Verb (infinitive/noun)
- **Why it works:** "Istīrād" means "import/importation." Standard Arabic term for bringing in from outside. Used in Arabic programming and technical contexts. Clear meaning.

**Chinese:**

- **Translation:** `导入` (dǎorù)
- **Form:** Verb compound
- **Why it works:** `导入` means "lead in/import." Standard Chinese term for importing. Two characters. Used in Chinese programming universally. Clear meaning of bringing external content in.

**Hindi:**

- **Translation:** `आयात` (āyāt)
- **Form:** Noun/verb
- **Why it works:** "Āyāt" means "import/importation." Standard Hindi term (from Sanskrit). Used in Hindi programming. Can function as command. Alternative: `लाओ` (lāo - bring) but `आयात` more technical.

### ❌ Common Translation Mistakes

**Mistake 1: Using "include" (C terminology)**

- **Wrong:** `incluir` (Spanish - "to include")
- **Why wrong:** "Include" is C/C++ preprocessor term with different semantics (textual inclusion). Python uses "import" (module loading). Different concepts need different words.
- **Right:** `importar` (import, not include)

**Mistake 2: Using "require" (other language's term)**

- **Wrong:** `requerir` (Spanish - "to require")
- **Why wrong:** "Require" is Ruby/JavaScript term. While similar, Python uses "import." Maintain language-specific terminology for consistency across Python translations.
- **Right:** `importar` (Python's term)

**Mistake 3: Using generic "load"**

- **Wrong:** `cargar` (Spanish - "to load")
- **Why wrong:** While "load" captures the concept, "import" is more specific - it's not just loading, it's bringing in external modules. "Import" is established programming terminology.
- **Right:** `importar` (more specific than load)

---

## Ambiguity Resolution

**Does the English term have multiple meanings?**

YES

**If YES, identify the CORRECT meaning for Python:**

- ❌ Meaning 1: "Import goods" (international trade - physical goods)
- ✅ Meaning 2: **LOAD MODULE** (bring external code into program namespace)
- ❌ Meaning 3: "Have significance" (that imports greatly - archaic)

**Example:**

English "import" can mean:

1. "Import coffee from Colombia" (trade - physical goods) ❌ Related metaphor
2. "import math" in code (load module) ✅ **This is the Python meaning**
3. "A matter of great import" (significance - archaic) ❌

**Your translation should capture meaning #2: loading external code modules into the program's namespace.**

Use the word for importing or bringing in from external sources (the trade/goods meaning often extends naturally to code modules).

---

## Cross-References (Consistency Requirements)

### Terms that MUST align linguistically

**If translating `import`, check these translations:**

- [ ] `from` - Paired with import; should work grammatically together
- [ ] `as` - Aliases imports; should work grammatically with import
- [ ] `def`/`class` - Define internal code; contrast with importing external
- [ ] Package/module terminology in documentation

**Consistency rule:**

`import`, `from`, and `as` work together syntactically. Translations should form grammatical phrases: `from module import name as alias` should read naturally in target language.

**Example:**

Spanish: `desde modulo importar nombre como alias` - grammatically coherent ✅

### Functional relationships

**This term works WITH:**

1. **`import` alone**:

```python
import module
module.function()
```

2. **`from ... import ...`**:

```python
from module import name
name()
```

**Common pairing:**

```python
# Basic import
import math
import os
import sys

# Import with alias
import numpy as np
import pandas as pd

# From import
from math import pi, sqrt
from os.path import exists, join

# From import with alias
from collections import OrderedDict as OD

# Import submodule
import xml.etree.ElementTree as ET

# Relative imports (in packages)
from . import sibling
from .. import parent
from .subpackage import module

# Import all (discouraged)
from module import *

# Multiple imports per line (discouraged but valid)
import os, sys, math

# Standard library imports (typical organization)
import os
import sys

# Third-party imports
import numpy as np
import requests

# Local application imports
from myapp import models
from myapp.utils import helper

# Conditional imports
try:
    import optional_module
except ImportError:
    optional_module = None

# Dynamic imports
module_name = "math"
math = __import__(module_name)
```

---

## Confidence Calibration

**Translation Difficulty: EASY**

### EASY

- Clear concept (load external code)
- Most languages have "import" verb
- Universal in programming
- **AI confidence should be HIGH**

### Why EASY for `import`

- Universal concept (loading external code)
- "Import" (bring in from outside) exists in most languages
- Standard programming terminology globally
- Often borrowed from English directly

**For this term:** EASY

**Rationale:** The concept of importing external code is universal in programming. Most languages have a word for "import" (bringing in from outside), often borrowed from trade/commerce terminology. Many languages borrow "import" directly from English. Translation is straightforward.

**If your confidence doesn't match this assessment, FLAG FOR HUMAN REVIEW.**

---

## Translation Validation Checklist

**Before submitting your translation, verify:**

### 1. Concept Accuracy

- [ ] Captures LOADING EXTERNAL MODULE concept?
- [ ] Conveys bringing in from outside?
- [ ] Distinguished from "include" (C) or "require" (Ruby/JS)?

### 2. Linguistic Correctness

- [ ] Correct part of speech (verb - imperative/infinitive)?
- [ ] Follows target language grammar rules?
- [ ] Capitalization correct (lowercase for Python keywords)?

### 3. Consistency

- [ ] Works grammatically with `from` and `as`?
- [ ] Phrase "from X import Y as Z" reads naturally?
- [ ] Consistent with module/package terminology?

### 4. Usability

- [ ] Short enough (1 word ideal)?
- [ ] Easy to type on standard keyboard?
- [ ] Easy to pronounce?
- [ ] Easy to remember (common word)?

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
term: import
language: es
translation: importar
form: verb
confidence: high
```

**Rationale (2-3 sentences):**

Spanish "importar" means "to import" (bring in from outside), directly translating the concept of loading external modules. Standard in Spanish programming. Works grammatically with "desde" (from) and "como" (as).

**Alternatives considered:**

1. `incluir` (include) - C terminology, not Python's
2. `requerir` (require) - Ruby/JS terminology, maintain Python's term
3. `cargar` (load) - Too generic; "import" more specific

**If confidence is not HIGH, explain:**

N/A - Confidence is HIGH. Import terminology is universal with clear translations.

---

**Document Version:** 1.0 (Tier 1 - Concise Translation Brief)
**Last Updated:** 2025-11-10
**Purpose:** Optimized for AI translation models
**Full Reference:** See `context-template-tier2.md` for comprehensive 5000-word version
