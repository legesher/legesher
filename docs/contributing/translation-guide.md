# Translation Contribution Guide

Welcome to the Legesher translation community! This guide will help you bring Python programming to developers who speak
your language.

## Why Your Language Matters

Every language added to Legesher opens programming to millions of developers worldwide. Whether you're a native speaker
passionate about making code accessible, or a linguist interested in technical translation, your contribution helps
break down language barriers in technology.

You don't need to be a programmer to contribute - we need your linguistic expertise more than your coding skills.

## Understanding Language Packs

Language packs are YAML files that map Python keywords and built-in functions to your language. When a developer writes
code in Spanish, Arabic, or any supported language, Legesher uses these packs to translate the code into executable
Python.

### File Structure

A language pack follows this structure:

```yaml
# Pack metadata
metadata:
  language: "Spanish"
  language_code: "es"
  python_version: "3.10"
  extends: null
  version: "1.0.0"
  contributors:
    - name: "Your Name"
      email: "your.email@example.com"

# Python keywords
keywords:
  # Control flow
  if: "si"
  else: "sino"
  elif: "osino"
  while: "mientras"
  for: "para"
  break: "romper"
  continue: "continuar"

# Built-in functions
builtins:
  print: "imprimir"
  len: "longitud"
  range: "rango"
  input: "entrada"
```

### Required Fields

Every language pack must include:

1. **Metadata**: Language info, Python version, contributors
2. **Keywords**: All 35 Python keywords translated
3. **Builtins**: Common built-in functions (minimum 20 recommended)

### Pack Inheritance System

Legesher uses version-aware language packs that inherit from each other:

- **Base Pack (3.10)**: Contains all translations
- **Extension Packs (3.11, 3.12, 3.13)**: Only define new keywords introduced in that Python version

Example of an extension pack:

```yaml
metadata:
  language: "Spanish"
  language_code: "es"
  python_version: "3.11"
  extends: "es-3.10"
  version: "1.0.0"

# Only new keywords in Python 3.11
keywords:
  match: "coincidir"
  case: "caso"
  _: "cualquiera"
```

This system means you only translate new features once, not duplicate all translations for each Python version.

## Before You Start

### Check If Your Language Exists

1. Browse the `libs/i18n-python-{code}` directories
2. Check the [Legesher Language Registry](https://github.com/legesher/legesher-org)
3. Ask in the community Discord or GitHub Discussions

If your language exists but has issues, you can improve it. If it doesn't exist, you'll create something new!

### Linguistic Considerations

Before translating, consider:

1. **Formality Level**: Should keywords be formal or informal?
   - Spanish: Use informal "tu" form or formal "usted"?
   - Decision: Be consistent with what feels natural to developers

2. **Regional Variations**: Choose the most widely understood variant
   - Spanish: "computadora" (Latin America) vs "ordenador" (Spain)
   - Decision: Consider your primary audience or use neutral terms

3. **Technical Terms**: Some terms might already have accepted translations in your tech community
   - Research how your language community discusses programming concepts
   - Don't reinvent terms that already exist and work well

### Translation Philosophy

#### Literal vs Natural Translation

Choose translations that:

- Feel natural to native speakers
- Are concise (1-2 words preferred)
- Are unambiguous in technical context
- Don't conflict with common variable names

Example (Spanish):

- `if` could be "si" (natural, short) vs "si_entonces" (overly literal)
- Choose "si" - it's how speakers naturally express conditionals

**Balance**: Sometimes literal translations work best, other times you need idiomatic equivalents. Trust your
linguistic intuition.

## Creating Your First Language Pack

### Step 1: Create Base Pack (3.10)

1. Create a new directory:

   ```text
   libs/i18n-python-{code}/
   ```

   Replace `{code}` with your language's ISO 639-1 code (e.g., `fr` for French, `de` for German).

2. Create the base pack file:

   ```text
   libs/i18n-python-{code}/packs/python-{code}-3.10.yaml
   ```

3. Start with this template:

```yaml
metadata:
  language: "Your Language Name"
  language_code: "xx"  # ISO 639-1 code
  python_version: "3.10"
  extends: null
  version: "1.0.0"
  contributors:
    - name: "Your Name"
      email: "your.email@example.com"
  description: "Python 3.10 keywords and built-ins in Your Language"

keywords:
  # Control Flow
  if: ""
  else: ""
  elif: ""
  while: ""
  for: ""
  break: ""
  continue: ""
  pass: ""
  return: ""
  # Definitions
  def: ""
  class: ""
  lambda: ""
  # Boolean & Logical
  True: ""
  False: ""
  None: ""
  and: ""
  or: ""
  not: ""
  is: ""
  in: ""
  # Exception Handling
  try: ""
  except: ""
  finally: ""
  raise: ""
  assert: ""
  # Import & Scope
  import: ""
  from: ""
  as: ""
  global: ""
  nonlocal: ""
  # Context Managers
  with: ""
  # Async (Python 3.5+)
  async: ""
  await: ""
  # Other
  del: ""
  yield: ""

builtins:
  # Essential I/O
  print: ""
  input: ""
  # Type Conversions
  int: ""
  float: ""
  str: ""
  bool: ""
  list: ""
  tuple: ""
  dict: ""
  set: ""
  # Utility Functions
  len: ""
  range: ""
  enumerate: ""
  zip: ""
  map: ""
  filter: ""
  sum: ""
  min: ""
  max: ""
  sorted: ""
  reversed: ""
  # Object Inspection
  type: ""
  isinstance: ""
  hasattr: ""
  getattr: ""
  setattr: ""
  # File Operations
  open: ""
  # Advanced
  help: ""
  dir: ""
  vars: ""
```

1. Fill in translations for each keyword and built-in function.

### Step 2: Test Your Translations

Create a simple test file to verify your translations work naturally:

```text
# test-{code}.py - Python code in your language

# If your "if" = "si", "else" = "sino", "print" = "imprimir"
si edad >= 18:
    imprimir("You are an adult")
sino:
    imprimir("You are a minor")
```

Ask yourself:

- Does this read naturally to a native speaker?
- Would a beginner understand what this code does?
- Are any translations confusing or ambiguous?

## Step 3: Create Inherited Packs (3.11, 3.12, 3.13)

For Python 3.11 (adds match/case statements):

```yaml
metadata:
  language: "Your Language Name"
  language_code: "xx"
  python_version: "3.11"
  extends: "xx-3.10"
  version: "1.0.0"
  contributors:
    - name: "Your Name"
      email: "your.email@example.com"

keywords:
  match: ""
  case: ""
  _: ""  # wildcard pattern
```

For Python 3.12 and 3.13 (no new keywords currently):

```yaml
metadata:
  language: "Your Language Name"
  language_code: "xx"
  python_version: "3.12"
  extends: "xx-3.11"
  version: "1.0.0"
  contributors:
    - name: "Your Name"
      email: "your.email@example.com"

# No new keywords - this pack inherits everything from 3.11
keywords: {}
builtins: {}
```

### Step 4: Validation

Run the validation command (once tooling is available):

```bash
legesher-i18n validate --pack python-xx-3.10.yaml
```

Manual validation checklist:

- [ ] All 35 keywords are translated
- [ ] At least 20 built-in functions are translated
- [ ] No duplicate translations (two keywords map to same word)
- [ ] Metadata is complete and accurate
- [ ] YAML syntax is valid
- [ ] Translations use appropriate character encoding

## Translation Guidelines

### Keyword Translation Best Practices

1. **Consistency**: Use the same grammatical form across similar keywords
   - If "if" is a verb form, "while" should also be a verb form

2. **Brevity**: Prefer short translations
   - Good: "si" (if)
   - Avoid: "en_caso_de_que" (overly long)

3. **Uniqueness**: Each translation must be distinct
   - Don't translate both "break" and "continue" to similar words

4. **Reserved Words**: Avoid common variable names in your language
   - If "data" is a common variable name, don't use it for a keyword

5. **Special Characters**: Language packs support full Unicode
   - Arabic: Use actual Arabic script, not transliteration
   - Chinese: Use traditional or simplified based on your audience
   - Accented characters: Always include proper diacritics

### Built-in Function Naming

Built-in functions have more flexibility than keywords:

1. **Descriptive Names**: Can be slightly longer if more clear
   - `print` might be "imprimir" (Spanish) or "طباعة" (Arabic)

2. **Cultural Appropriateness**: Use terms familiar to your tech community
   - Research how your language's programming community already discusses these concepts

3. **Type Names**: Consider whether type names should be nouns or verbs
   - `int` as "entero" (noun: integer) vs "entificar" (verb: to make integer)
   - Generally, nouns work better

### Consistency Rules

Create consistency within your language pack:

1. **Verb Forms**: If using imperatives, use them throughout
2. **Capitalization**: Follow your language's capitalization rules
3. **Compound Words**: Use consistent separators (spaces, hyphens, or concatenation)
4. **Abbreviations**: Avoid unless universally understood in your language

### Cultural Sensitivity

1. **Inclusive Language**: Avoid gender-specific terms unless grammatically required
2. **Regional Neutrality**: Choose terms that work across regional dialects when possible
3. **Technical Accessibility**: Avoid slang or colloquialisms
4. **Community Input**: Consider surveying your language community for feedback

## Testing Your Pack

### Using the Validation Command

Once available, the validation command checks:

- YAML syntax correctness
- Required field presence
- Duplicate detection
- Character encoding validity
- Inheritance chain integrity

```bash
legesher-i18n validate --pack python-fr-3.10.yaml --verbose
```

### Manual Testing With Real Code

Create sample programs in your language:

```python
# Example: loops-test.py
para numero in rango(10):
    si numero % 2 == 0:
        imprimir(numero)
```

Verify:

1. Code reads naturally to native speakers
2. Keywords don't conflict with variable names
3. Beginners can understand the code flow
4. Syntax highlighting works (once IDE support exists)

### Common Issues to Check

1. **Encoding Issues**:
   - Ensure file is saved as UTF-8
   - Verify special characters display correctly

2. **Ambiguous Translations**:
   - Check if any translations could mean multiple things in technical context

3. **Typos and Consistency**:
   - Use consistent spelling throughout (e.g., American vs British English conventions in metadata)

4. **Inheritance Errors**:
   - Verify `extends` field points to correct parent pack
   - Ensure Python versions are in correct order (3.10 -> 3.11 -> 3.12 -> 3.13)

## Submitting Your Pack

### PR Process

1. **Fork the Repository**: Fork `legesher/legesher` on GitHub

2. **Create Your Branch**:

   ```bash
   git checkout -b add-language-pack-{code}
   ```

3. **Add Your Files**:
   - Language pack YAML files
   - README.md in your language pack directory
   - Update main documentation to list your language

4. **Commit With Clear Message**:

   ```bash
   git commit -m "feat(i18n): Add {Language} language pack for Python 3.10-3.13"
   ```

5. **Open Pull Request**:
   - Title: "Add {Language} Language Pack"
   - Description: Explain your translation choices, any regional considerations, and testing you performed

### What Reviewers Look For

Reviewers (many are linguists or native speakers) will check:

1. **Linguistic Quality**:
   - Natural, idiomatic translations
   - Consistency in grammatical forms
   - Appropriate formality level

2. **Technical Correctness**:
   - All required keywords present
   - No duplicate mappings
   - Valid YAML syntax
   - Correct inheritance structure

3. **Cultural Appropriateness**:
   - Inclusive language
   - Regional sensitivity
   - Technical community alignment

4. **Documentation**:
   - Clear explanation of translation choices
   - README in the language pack directory
   - Contributor information complete

### Iteration and Feedback

Translation is collaborative:

1. **Expect Discussion**: Reviewers may suggest alternatives
2. **Regional Variations**: Other speakers might prefer different terms
3. **Community Input**: We may gather feedback from broader community
4. **Compromise**: Sometimes we choose "good enough for everyone" over "perfect for some"

Be open to feedback and remember: we're all working toward making coding accessible.

## Linguistic Standards

### Formality Level

Choose a formality level appropriate for technical documentation in your language:

- **Formal Languages**: Use formal register (e.g., German "Sie" contexts)
- **Informal Languages**: Use natural, conversational tone (e.g., Spanish "tu" form)
- **Mixed**: Some languages require formal technical terms but informal grammar

**Recommendation**: Match how programming is taught in your language's educational system.

### Regional Variations

When regional variations exist:

1. **Document Your Choice**: Explain in PR which region/dialect you're targeting
2. **Consider Neutrality**: Can you choose terms that work everywhere?
3. **Create Variants**: For major regional differences, we can support multiple packs (e.g., `pt-BR` vs `pt-PT`)

### RTL Language Support

For right-to-left languages (Arabic, Hebrew, Farsi, Urdu):

1. **Text Direction**: Language packs store text in logical order, not display order
2. **Punctuation**: Use appropriate punctuation for your language
3. **Mixed Text**: Code often mixes RTL keywords with LTR identifiers - this is expected
4. **IDE Support**: Note any RTL display issues for future IDE work

Example (Arabic):

```yaml
keywords:
  if: "اذا"
  else: "والا"
  elif: "اذاكان"
  while: "بينما"
  for: "لكل"
```

## Examples

### Complete Pack Example (Simplified French)

```yaml
metadata:
  language: "French"
  language_code: "fr"
  python_version: "3.10"
  extends: null
  version: "1.0.0"
  contributors:
    - name: "Marie Dubois"
      email: "marie@example.com"
  description: "Python 3.10 keywords and built-ins in French"

keywords:
  # Control Flow
  if: "si"
  else: "sinon"
  elif: "sinonsi"
  while: "tantque"
  for: "pour"
  break: "arreter"
  continue: "continuer"
  pass: "passer"
  return: "retourner"

  # Definitions
  def: "def"  # Keeping 'def' as is - widely recognized
  class: "classe"
  lambda: "lambda"  # Mathematical term, keep as is

  # Boolean & Logical
  True: "Vrai"
  False: "Faux"
  None: "Rien"
  and: "et"
  or: "ou"
  not: "non"
  is: "est"
  in: "dans"

  # Exception Handling
  try: "essayer"
  except: "sauf"
  finally: "finalement"
  raise: "lever"
  assert: "affirmer"

  # Import & Scope
  import: "importer"
  from: "depuis"
  as: "comme"
  global: "global"  # Technical term, widely understood
  nonlocal: "nonlocal"  # Technical term

  # Context Managers
  with: "avec"

  # Async
  async: "async"  # Technical term
  await: "attendre"

  # Other
  del: "supprimer"
  yield: "ceder"

builtins:
  print: "afficher"
  input: "saisir"
  int: "entier"
  float: "reel"
  str: "chaine"
  bool: "booleen"
  list: "liste"
  tuple: "tuple"
  dict: "dictionnaire"
  set: "ensemble"
  len: "longueur"
  range: "intervalle"
  enumerate: "enumerer"
  zip: "zipper"
  map: "mapper"
  filter: "filtrer"
  sum: "somme"
  min: "min"
  max: "max"
  sorted: "trie"
  reversed: "inverse"
  type: "type"
  isinstance: "estinstance"
  open: "ouvrir"
  help: "aide"
```

### Common Pitfalls and Solutions

#### Pitfall 1: Over-literal Translation

```yaml
# Problematic
if: "dans_le_cas_ou"  # Too verbose

# Better
if: "si"  # Natural and concise
```

#### Pitfall 2: Duplicate Translations

```yaml
# Problematic
break: "parar"
continue: "parar"  # Same as break!

# Better
break: "romper"
continue: "continuar"  # Distinct meanings
```

#### Pitfall 3: Using Common Variable Names

```yaml
# Problematic
data: "data"  # Too common as variable name

# Better
# (This isn't actually a keyword, but shows the principle)
```

**Pitfall 4: Inconsistent Grammatical Forms**

```yaml
# Problematic
if: "si"  # Conjunction
while: "durante"  # Preposition
for: "iterar"  # Verb

# Better - All conjunctions/prepositions
if: "si"
while: "mientras"
for: "para"
```

#### Pitfall 5: Missing Metadata

```yaml
# Problematic
metadata:
  language: "German"
  # Missing language_code, version, etc.

# Better
metadata:
  language: "German"
  language_code: "de"
  python_version: "3.10"
  extends: null
  version: "1.0.0"
  contributors:
    - name: "Your Name"
```

## Resources

### Python Reference Materials

- **Python Keywords List**: [Python 3.10 Keywords](https://docs.python.org/3.10/reference/lexical_analysis.html#keywords)
- **Built-in Functions**: [Python Built-ins](https://docs.python.org/3/library/functions.html)
- **Python 3.11 Changes**: [What's New in 3.11](https://docs.python.org/3/whatsnew/3.11.html)
- **Python 3.12 Changes**: [What's New in 3.12](https://docs.python.org/3/whatsnew/3.12.html)
- **Python 3.13 Changes**: [What's New in 3.13](https://docs.python.org/3/whatsnew/3.13.html)

### Language Pack Examples

Study existing language packs for inspiration:

- **Spanish (es)**: `libs/i18n-python-es/`
- **Arabic (ar)**: `libs/i18n-python-ar/`

### Translation Tools

- **ISO 639-1 Codes**: [Language Code Lookup](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)
- **Unicode Character Tables**: For special character support
- **YAML Validator**: [YAML Lint](http://www.yamllint.com/)

### Community Help

Need guidance or want to discuss translation choices?

- **GitHub Discussions**: Ask questions in the Legesher repository
- **Discord Community**: Join for real-time conversation (link in main README)
- **Translation Review**: Request feedback before submitting PR
- **Language Coordinators**: Some languages have dedicated coordinators who can help

### Contributing Beyond Translation

Once your language pack exists, you can also:

1. **Create Tutorials**: Write "Learn Python in {Your Language}" tutorials
2. **Translation Tests**: Add test cases for your language
3. **Documentation**: Translate Legesher documentation
4. **Community Building**: Help grow the community of developers using your language

## Getting Started Checklist

Ready to contribute? Here's your checklist:

- [ ] Verify my language doesn't already exist
- [ ] Research how my tech community discusses programming concepts
- [ ] Choose appropriate formality level and regional variant
- [ ] Create base pack (3.10) with all keywords and built-ins
- [ ] Test translations for natural reading
- [ ] Create extension packs (3.11, 3.12, 3.13)
- [ ] Validate YAML syntax
- [ ] Document translation choices
- [ ] Fork repository and create branch
- [ ] Submit pull request with clear description
- [ ] Respond to reviewer feedback
- [ ] Celebrate making programming accessible in my language!

## Thank You

Your contribution helps developers worldwide learn and create in their native language. Every language pack represents
countless hours of thoughtful linguistic work, and we deeply appreciate your expertise and time.

Welcome to the Legesher community!

---

**Questions?** Open an issue or discussion in the [Legesher repository](https://github.com/legesher/legesher).

**Found an error in this guide?** Submit a PR to improve it!

**Want to help beyond translation?** Check out our [main contributing guide](../CONTRIBUTING.md).
