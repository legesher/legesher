# Linguistic Standards for Python Translations

**Version:** 2.0
**Date:** 2025-10-28
**Purpose:** Establish consistent linguistic conventions for translating Python keywords and builtins across all languages

**Changelog:**

- **v2.0 (2025-10-28):** Added 8 comprehensive sections based on ultra-deep analysis:
  - Register & Formality Strategy
  - Transliteration vs Translation guidelines
  - Compound Term Strategy
  - Capitalization & Case Conventions (comprehensive)
  - RTL Language Practical Requirements (expanded)
  - Ambiguity Resolution Framework
  - Honorific & Politeness Levels
  - Gendered Language Rules
- **v1.0 (2025-10-28):** Initial version

---

## Overview

These standards ensure consistency and quality in Python term translations across all supported languages. They follow principles similar to git commit message conventions - establishing clear rules for word types, forms, and tenses.

## Core Principles

### 1. Concept-Based Translation

**DO:** Translate the programming CONCEPT
**DON'T:** Translate word-for-word from English

**Example:**

- `def` in Python creates a function
- Translation should capture "define/create function" concept
- Spanish: "definir" (infinitive: to define)
- Chinese: "定义" (dìngyì: define/definition)

### 2. Natural Language Flow

Translations should sound natural to native speakers while maintaining technical precision.

**Good:** Uses forms native speakers would naturally use
**Bad:** Direct English translation that sounds awkward

---

## Word Type Classification

### Action Keywords (Commands)

Keywords that perform actions or create structures.

**Examples:** `def`, `return`, `break`, `continue`, `pass`, `del`, `raise`

**Recommended Form:** Infinitive or imperative
**Rationale:** These are commands/actions, like git commit verbs

| Language Family | Recommended Form | Example (def) |
|-----------------|------------------|---------------|
| Romance (es, fr, pt, it, ro) | Infinitive (-ar, -er, -ir) | definir |
| Germanic (de, nl, sv, no, da) | Infinitive | definieren |
| Slavic (ru, pl, uk, cs) | Infinitive | определить |
| Arabic | Verbal noun (masdar) | تعريف |
| Chinese/Japanese/Korean | Dictionary form | 定义 |
| Hindi | Verb root/infinitive | परिभाषित करना |

### State Keywords (Conditions/Tests)

Keywords that test conditions or describe state.

**Examples:** `if`, `elif`, `else`, `while`, `is`, `in`

**Recommended Form:** Conjunction or present tense
**Rationale:** Describes current state or condition

| Language Family | Recommended Form | Example (if) |
|-----------------|------------------|--------------|
| Romance | Conjunction/present | si |
| Germanic | Conjunction | wenn |
| Slavic | Conjunction | если |
| Arabic | Conditional particle | إذا |
| Chinese | Conditional word | 如果 |
| Hindi | Conditional | यदि |

### Boolean Constants

**Examples:** `True`, `False`, `None`

**Recommended Form:** Adjective or noun
**Rationale:** These are values, not actions

| Language Family | Recommended Form | Example (True) |
|-----------------|------------------|----------------|
| Romance | Adjective (masculine) | Verdadero |
| Germanic | Adjective | Wahr |
| Slavic | Adjective | Истина |
| Arabic | Adjective | صحيح |
| Chinese | Adjective/noun | 真 |
| Hindi | Adjective | सत्य |

### Logical Operators

**Examples:** `and`, `or`, `not`

**Recommended Form:** Conjunction or operator
**Rationale:** These connect or modify conditions

| Language Family | Recommended Form | Example (and) |
|-----------------|------------------|---------------|
| Romance | Conjunction | y/e |
| Germanic | Conjunction | und |
| Slavic | Conjunction | и |
| Arabic | Conjunction | و |
| Chinese | Conjunction | 和 |
| Hindi | Conjunction | और |

### Type Constructors / Builtins

**Examples:** `int`, `str`, `list`, `dict`, `print`, `len`

**Recommended Form:** Noun or verb depending on function
**Rationale:**

- Type names → nouns (int = integer)
- Actions → verbs (print = to print)

---

## Compound Term Strategy

### The Challenge

Many Python builtins combine multiple concepts into one term:

- `isinstance` = "is" + "instance"
- `hasattr` = "has" + "attribute"
- `getattr` = "get" + "attribute"
- `setattr` = "set" + "attribute"

**Question:** Should translations be single compound words, two separate words, or something else?

### Translation Strategies by Language Family

#### Strategy 1: Single Compound Word

**Best for:** Germanic languages (natural compounding)

**Examples:**

- German: `isinstance` → `istInstanz`
- Dutch: `isinstance` → `isInstantie`
- Swedish: `isinstance` → `ärInstans`

**Advantages:**

- Mirrors English structure
- Single token (no spaces)
- Natural in Germanic languages

#### Strategy 2: Two Separate Words

**Best for:** Romance languages, Arabic

**Examples:**

- Spanish: `isinstance` → `es instancia` (is instance)
- French: `isinstance` → `est instance`
- Arabic: `isinstance` → `هو نموذج` (is instance)

**Advantages:**

- More natural phrasing
- Clearer meaning
- Easier to parse for learners

**Disadvantage:**

- Two tokens (spaces in keyword)
- May require special handling in parser

#### Strategy 3: Verb + Noun Construction

**Best for:** Languages with verb-noun patterns

**Examples:**

- Hindi: `isinstance` → `उदाहरण है` (instance is)
- Japanese: `isinstance` → `インスタンスである` (instance is)

**Advantages:**

- Natural word order for language
- Clear grammatical structure

#### Strategy 4: Idiomatic Rephrasing

**Best for:** Languages where literal translation sounds awkward

**Examples:**

- Chinese: `isinstance` → `属于类` (belongs to class) - more natural than literal
- Japanese: `hasattr` → `属性を持つ` (has attribute)

**Advantages:**

- Sounds most natural to native speakers
- May be clearer than literal translation

**Disadvantage:**

- Further from English structure
- May be harder for bilingual developers to map

### Consistency Requirements

**CRITICAL RULE: Be consistent within a language pack**

If you use Strategy 1 (single compound) for one term, use it for related terms:

✅ **Consistent (German):**

- `isinstance` → `istInstanz`
- `hasattr` → `hatAttribut`
- `getattr` → `gibAttribut`
- `setattr` → `setzAttribut`

❌ **Inconsistent (BAD):**

- `isinstance` → `istInstanz` (compound)
- `hasattr` → `hat Attribut` (two words) ← Inconsistent!
- `getattr` → `getAttribute` (camelCase) ← Different pattern!

### Specific Compound Term Patterns

#### Pattern A: "is" + Type (`isinstance`, `issubclass`)

**Recommended:**

- Verb form of "is" + noun for type
- Keep together as single concept

#### Pattern B: "has" + Property (`hasattr`)

**Recommended:**

- Verb form of "has/possess" + noun for property

#### Pattern C: "get/set" + Property (`getattr`, `setattr`, `delattr`)

**Recommended:**

- Action verb + property noun
- These three MUST use same pattern (they're related operations)

### Length Limits

**Maximum 3 words for any builtin**

Even if your language naturally produces longer phrases, keep it concise:

✅ Acceptable:

- `isinstance` → "es instancia" (2 words)
- `hasattr` → "tiene atributo" (2 words)

⚠️ Getting Long:

- `isinstance` → "es una instancia de" (4 words) - Too long!

❌ Too Long:

- `isinstance` → "comprueba si es una instancia de" (6 words) - Way too long!

**If your natural translation is >3 words:**

1. Try to abbreviate while keeping clarity
2. Consider compound word strategy
3. Consult with native speaker reviewers

### Testing Your Compound Strategy

**Ask yourself:**

1. **Is this consistent** with other compound terms in this language pack?
2. **Is it easy to type?** (No awkward character combinations?)
3. **Is it easy to read?** (Can you scan code and spot it quickly?)
4. **Does it make sense** to a native speaker learning Python?
5. **Is it ≤3 words?** (Shorter is better)

### Examples by Language

**Spanish (Two-word strategy):**

- `isinstance` → `es instancia`
- `hasattr` → `tiene atributo`
- `getattr` → `obtener atributo`
- `setattr` → `establecer atributo`

**German (Compound strategy):**

- `isinstance` → `istInstanz`
- `hasattr` → `hatAttribut`
- `getattr` → `gibAttribut`
- `setattr` → `setzAttribut`

**Chinese (Idiomatic strategy):**

- `isinstance` → `属于类` (belongs to class)
- `hasattr` → `有属性` (has attribute)
- `getattr` → `取属性` (get attribute)
- `setattr` → `设属性` (set attribute)

---

## Language-Specific Guidelines

### Romance Languages (Spanish, French, Portuguese, Italian, Romanian)

**Verb Forms:**

- Use infinitive for action keywords: `-ar`, `-er`, `-ir` endings
- ✅ `def` → `definir` (to define)
- ❌ `def` → `definiendo` (defining - gerund is too wordy)

**Register:**

- Use formal/technical register
- Avoid colloquialisms

**Translation Register Guidelines:**

See detailed register definitions in the "Register & Formality Strategy" section below.

**Capitalization Rules:**

See comprehensive capitalization guidance in the "Capitalization & Case Conventions" section below.

---

## Register & Formality Strategy

### Defining "Technical/Formal" Register

**What We Mean by "Technical/Formal":**

**NOT** academic formal (overly stuffy, archaic terms)
**NOT** colloquial informal (slang, regional dialects)

**TARGET: Professional Technical Register**

This is the register used in:

- Computer Science education (universities, textbooks)
- Tech industry (professional developers)
- Technical documentation
- Professional development environments

**Characteristics:**

- Clear and unambiguous
- Respectful but not overly formal
- Accessible to educated speakers
- Standard vocabulary for the domain
- No slang or regional colloquialisms
- No unnecessarily complex academic terms

### Language-Specific Register Definitions

#### Spanish (Español)

**Technical Formal Register:**

- ✅ Standard CS vocabulary used in education
- ✅ Example: "definir" (to define)
- ❌ NOT overly academic: "conceptuar" (too stuffy)
- ❌ NOT colloquial: "armar" (too informal, means "build/assemble")

**Tone:** Neutral/technical with slight informal feel (programming is collaborative, not academic)

#### Arabic (العربية)

**Technical Formal Register:**

- ✅ Modern Standard Arabic (MSA) technical terms
- ✅ Example: "تعريف" (ta'rīf - definition)
- ❌ NOT classical Arabic (Quranic or ancient forms)
- ❌ NOT dialectal (Egyptian, Levantine colloquialisms)

**Rationale:** MSA is the lingua franca for technical content across Arabic-speaking regions

#### Chinese Simplified (简体中文)

**Technical Formal Register:**

- ✅ Established Computer Science education terms
- ✅ Example: "定义" (dìngyì - define)
- ❌ NOT overly literary/classical: "界说" (too formal/rare)
- ❌ NOT colloquial: "弄" (too casual, means "do/get")

**Standard:** Technical terms used in Chinese CS textbooks and universities

#### Hindi (हिन्दी)

**Technical Formal Register:**

- ✅ Sanskrit-derived terms used in CS education
- ✅ Example: "परिभाषित करना" (paribhaashit karna - to define)
- ❌ NOT overly Sanskritized: "व्याख्यानित" (too archaic)
- ❌ NOT English transliteration: "डिफाइन" (difain - not translating)

**Balance:** Formal Sanskrit-derived vocabulary (aligns with CS education in India) while avoiding archaic forms

#### Japanese (日本語)

**Technical Formal Register:**

- ✅ Neutral form (dictionary form) without excessive honorifics
- ✅ Example: "定義する" (teigi suru - to define, neutral)
- ❌ NOT polite form: "定義します" (implies code is being polite)
- ❌ NOT honorific: "定義なさる" (implies hierarchy)

**Rationale:** Code should not feel hierarchical; neutral form is most flexible

#### Korean (한국어)

**Technical Formal Register:**

- ✅ Standard form (하다 hada form)
- ✅ Example: "정의하다" (jeong-uihada - to define)
- ❌ NOT polite -요 form: "정의해요" (inappropriate for code)

**Rationale:** Similar to Japanese - avoid forms that imply social hierarchy

### Testing Your Register

**Ask yourself:**

1. **Would this term appear in a CS textbook** in the target language?
2. **Would a professor use this term** when teaching programming?
3. **Would professional developers** recognize and use this term?
4. **Is it accessible** to someone learning programming (not requiring specialized linguistics knowledge)?
5. **Does it avoid** slang, regional dialects, or overly academic vocabulary?

If you answer "yes" to all five, you've likely found the right register.

---

### Germanic Languages (German, Dutch, Swedish, Norwegian, Danish)

**Verb Forms:**

- Use infinitive for action keywords
- Often longer compound words are acceptable

**Compound Words:**

- German especially uses compounds
- `dict` → `Wörterbuch` (word-book)

**Capitalization:**

- German capitalizes nouns: `Class` → `Klasse`

### Slavic Languages (Russian, Polish, Ukrainian, Czech)

**Verb Forms:**

- Use infinitive for actions
- Consider aspect (perfective vs imperfective)
- Usually prefer imperfective for ongoing actions

**Cases:**

- Nominative case for standalone terms
- Consider context where term appears

### Right-to-Left (RTL) Languages (Arabic, Hebrew, Urdu, Farsi)

**Verb Forms (Arabic):**

- Use verbal noun (masdar) for action keywords
- ✅ `def` → `تعريف` (ta'rīf - defining/definition)

**RTL-Specific Guidance:**

See comprehensive RTL guidance in the "RTL Language Practical Requirements" section below.

### Asian Languages (Chinese, Japanese, Korean)

**Chinese (Simplified):**

- Use established technical vocabulary
- Two-character compounds common
- Prefer common CS education terms
- ✅ `def` → `定义` (dìngyì - define)
- ✅ `class` → `类` (lèi - class/category)

**Script:**

- Use Simplified Chinese (简体) for mainland
- Traditional (繁體) can be dialect variant

**Japanese:**

- Can use kanji, hiragana, or katakana
- Katakana often used for loanwords
- Consider established programming terms

**Honorific Levels:**
See "Honorific & Politeness Levels" section below for Japanese-specific guidance.

**Korean:**

- Use Hangul
- Consider Sino-Korean vs native Korean words
- Technical terms often use Sino-Korean

**Honorific Levels:**
See "Honorific & Politeness Levels" section below for Korean-specific guidance.

### Indic Languages (Hindi, Bengali, Tamil)

**Hindi:**

- Use Devanagari script (देवनागरी)
- Balance Sanskrit-derived vs English loanwords
- Formal register preferred
- ✅ `def` → `परिभाषित` (paribhaashit - defined)

**Script Rendering:**

- Ensure proper conjunct rendering
- Test with various fonts

**Transliteration:**

- Some terms may use transliterated English
- When no clear Hindi equivalent exists

**Honorific Levels:**
See "Honorific & Politeness Levels" section below for Hindi-specific guidance.

---

## Consistency Rules

### Within a Language Pack

1. **Same form for same word type**
   - All action keywords use same verb form
   - All boolean constants use same structure

2. **Length consistency**
   - Keywords should be brief (1-2 words max)
   - Longer is acceptable for builtins if clear

3. **Register consistency**
   - Use same formality level throughout
   - Technical/formal is preferred

### Across Language Families

1. **Respect language patterns**
   - Don't force English structure
   - Use natural target language patterns

2. **Technical accuracy**
   - Preserve programming semantics
   - Don't sacrifice accuracy for brevity

---

## Ambiguity Resolution Framework

### When Conflicts Arise

Sometimes you'll face choices where multiple valid translations exist, or different priorities conflict. Use this framework to resolve systematically.

### Priority Hierarchy

When in doubt, apply priorities in this order:

#### Priority 1: Technical Accuracy (NEVER COMPROMISE)

**The translation MUST capture the correct programming concept.**

**Question:** Does this translation correctly represent what the term does in Python?

**Examples:**

❌ **Fails Priority 1:**

- Spanish "return" → "volver" (come back) - WRONG meaning
  - "volver" means "to come back to a place"
  - `return` means "give back a value"
  - **This fails technical accuracy** - rejected

✅ **Passes Priority 1:**

- Spanish "return" → "retornar" or "devolver" (give back) - CORRECT meaning
  - Both capture "returning a value"
  - Move to Priority 2 to choose between them

**Rule:** If a translation fails Priority 1, it's eliminated. No exceptions.

#### Priority 2: CS Education Alignment

**The translation SHOULD match how programming is taught in target regions.**

**Question:** Is this term used in CS education in the target language?

**How to check:**

1. Search "{language} Python tutorial" - what terms do they use?
2. Check university CS course pages in target language
3. Look for CS textbooks in target language
4. Check Stack Overflow in target language

**Examples:**

Between "retornar" and "devolver" (both technically accurate):

**Research findings:**

- Spanish CS tutorials: 80% use "retornar"
- University courses: "retornar" more common
- Stack Overflow español: Mixed, slight preference for "retornar"

**Winner:** "retornar" (aligns with CS education)

**Why this matters:** Students learning Python in their native language shouldn't encounter conflicting terminology with their educational materials.

#### Priority 3: Naturalness

**Among technically accurate and educationally aligned options, choose the most natural.**

**Question:** Which sounds more natural to native speakers?

**Factors:**

- **Length:** Shorter > longer (if equally clear)
- **Common usage:** Everyday word > rare/formal word
- **Pronounceability:** Easy to say > tongue-twister
- **Memorability:** Easy to remember > obscure

**Examples:**

Chinese "print":

- Option A: `打印` (dǎyìn) - common, 2 characters, widely understood
- Option B: `印刷` (yìnshuā) - means "printing" but implies physical printing (books/papers)

**Winner:** `打印` (more natural for computer context)

#### Priority 4: International Consistency

**If still tied, consider cognates or international consistency.**

**Question:** Does this help multilingual developers?

**Why this matters:** Many developers work in multiple languages. Cognates (similar words across languages) reduce cognitive load.

**Examples:**

Spanish "define":

- Option A: "definir" (cognate with English "define")
- Option B: "establecer" (means "establish" - also valid)

**Winner:** "definir" (cognate helps multilingual developers)

**Note:** Only use this as a tiebreaker. Don't force cognates if they fail Priorities 1-3.

### Application Walkthrough

**Example: Translating "return" to Spanish**

**Step 1: Generate Options**

- volver (come back)
- retornar (return/give back)
- devolver (give back/return)
- regresar (go back)

**Step 2: Apply Priority 1 (Technical Accuracy)**

- ❌ volver - wrong meaning (come back to a place)
- ✅ retornar - correct (give back value)
- ✅ devolver - correct (give back value)
- ❌ regresar - wrong meaning (go back)

**Remaining:** retornar, devolver

**Step 3: Apply Priority 2 (CS Education)**

- Research shows: "retornar" more common in CS education
- "devolver" also used but less frequent

**Winner:** retornar ✅

**Result:** `return` → `retornar` in Spanish

### Special Case: No Clear Winner

**If priorities 1-4 don't resolve it:**

1. **Document both options** in review materials
2. **Let community vote**
3. **Choose option with 60%+ support**
4. **If still tied (50/50):** Choose shorter option or alphabetically first

### Common Ambiguity Patterns

#### Pattern 1: English Word Has Multiple Meanings

**Example:** "return" (come back vs give back)

**Solution:** Identify which meaning applies to programming

- Python `return` = give back a value (not come back to a place)
- Choose translation that captures correct meaning

#### Pattern 2: Multiple Equally Valid Target Language Words

**Example:** Spanish "retornar" vs "devolver" (both mean "give back")

**Solution:** Use Priority 2 (CS Education) to decide

#### Pattern 3: Literal vs Idiomatic Translation

**Example:** Chinese "isinstance"

- Literal: "是实例" (is instance)
- Idiomatic: "属于类" (belongs to class)

**Solution:**

- Both technically accurate (Priority 1 pass)
- Check education materials (Priority 2)
- Choose more natural option (Priority 3)

### Red Flags

**Watch out for these warning signs:**

🚩 **Translation has different connotation**

- Example: Using childish/informal word for technical term
- Solution: Choose more formal equivalent

🚩 **Translation is ambiguous with another keyword**

- Example: Same word used for two different keywords
- Solution: Disambiguate or use compound

🚩 **Translation is offensive or has negative meaning**

- Example: Innocent in English, rude in target language
- Solution: Choose alternative immediately

🚩 **Translation is too long (>3 words)**

- Example: "es una instancia de" (5 words)
- Solution: Abbreviate or find shorter phrase

### Decision Documentation

**When you make a choice using this framework, document:**

```yaml
term: return
translation: retornar
rationale: |
  Priority 1 (Accuracy): ✅ Captures "give back value" concept
  Priority 2 (Education): ✅ Used in 80% of Spanish CS tutorials
  Priority 3 (Natural): ✅ Common, natural, easy to say
  Priority 4 (Consistency): ✅ Cognate with English

  Alternatives considered:
  - devolver: Also correct but less common in CS education
  - volver: Rejected - wrong meaning (come back to place)
```

---

## Capitalization & Case Conventions

### General Principles

**Python's English convention:**

- Keywords: all lowercase (`def`, `class`, `return`)
- Boolean constants: First letter capitalized (`True`, `False`, `None`)
- Builtins: all lowercase (`print`, `int`, `str`)

**Translations should match Python's capitalization pattern while respecting target language rules.**

### Constants (True, False, None)

**Capitalization Rule:** First letter capitalized, rest lowercase

**Apply this pattern unless the target language has different conventions:**

| Language | Pattern | Example (True) | Rationale |
|----------|---------|----------------|-----------|
| Spanish | First cap | `Verdadero` | Matches Python pattern |
| French | First cap | `Vrai` | Matches Python pattern |
| German | First cap | `Wahr` | German capitalizes nouns anyway |
| Portuguese | First cap | `Verdadeiro` | Matches Python pattern |
| Arabic | No caps in script | `صحيح` | Arabic doesn't have uppercase/lowercase |
| Chinese | No caps in script | `真` | Chinese doesn't have case |
| Hindi | No caps in script | `सत्य` | Devanagari doesn't have case |
| Japanese | No caps | `真` | Japanese doesn't have case |
| Russian | First cap | `Истина` | Matches Python pattern |

**Gender Note:** For gendered languages, use masculine form (see "Gendered Language Rules" section below)

### Keywords (def, return, if, etc.)

**Capitalization Rule:** All lowercase (unless language mandates otherwise)

**Examples:**

✅ **Correct (lowercase):**

- Spanish: `definir`, `retornar`, `si`
- French: `définir`, `retourner`, `si`
- German: `definieren`, `zurückgeben`, `wenn`
- Russian: `определить`, `вернуть`, `если`

❌ **Incorrect (capitalized keywords):**

- Spanish: `Definir` ❌ (Should be lowercase)
- French: `Retourner` ❌ (Should be lowercase)

**Exception: German nouns**

German capitalizes all nouns, which may affect some keywords:

- `class` → `Klasse` ✅ (noun, capitalize)
- `def` → `definieren` ✅ (verb, lowercase)
- `type` → `Typ` ✅ (noun, capitalize)

**Rule for German:** Follow German grammar - capitalize nouns, lowercase verbs

### Builtins (print, int, str, list, etc.)

**Capitalization Rule:** All lowercase

**Exceptions:**

- **German type names** may be capitalized (nouns)
  - `int` → `ganz` or `Ganzzahl` (if using noun form)
  - `str` → `zeichenkette` or `Zeichenkette` (if using noun form)

**Examples:**

✅ **Correct:**

- Spanish: `imprimir`, `entero`, `cadena`
- French: `imprimer`, `entier`, `chaîne`
- German: `drucken`, `ganz`, `zeichenkette` (or `Ganzzahl`, `Zeichenkette` if noun forms)
- Chinese: `打印`, `整数`, `字符串`

### CamelCase, snake_case, kebab-case?

**Python uses snake_case for keywords and builtins (all lowercase, underscores for compounds)**

**Translations should generally avoid case mixing:**

❌ **Avoid:**

- CamelCase: `getInstance`, `hasAttribute`
- PascalCase: `GetInstance`, `HasAttribute`
- kebab-case: `get-instance`, `has-attribute`

✅ **Preferred:**

- All lowercase: `getinstance`, `hasattribute`
- Lowercase with space (if language allows): `get instance`, `has attribute`
- Lowercase compound (Germanic): `getinstanz`, `hatattribut`

**Exception:** Some languages naturally create compounds that look like CamelCase

- German: `istInstanz` (looks like camelCase but it's German noun capitalization)
- This is acceptable if it follows language rules

### Script-Specific Considerations

#### Languages Without Case (Arabic, Hebrew, Chinese, Japanese, Hindi, Thai)

**No capitalization needed** - these scripts don't distinguish uppercase/lowercase

- Just follow standard script conventions
- Focus on correct characters, not case

#### Cyrillic Scripts (Russian, Ukrainian, Bulgarian, Serbian)

**Follow same pattern as Latin scripts:**

- Keywords: all lowercase
- Constants: First letter capitalized

#### Greek Script

- Keywords: all lowercase (γιαννα, επιστροφη)
- Constants: First letter capitalized (Αληθής)

### Testing Capitalization

**Checklist:**

1. **Does this match Python's capitalization pattern?**
   - Keyword → lowercase?
   - Constant → First cap?
   - Builtin → lowercase?

2. **Does this follow target language grammar rules?**
   - German nouns capitalized?
   - Languages without case handled appropriately?

3. **Is it consistent** across the language pack?
   - All keywords use same case pattern?
   - All constants use same case pattern?

---

## Honorific & Politeness Levels

### Languages Affected

Japanese (ja), Korean (ko), Hindi (hi), and other languages with grammatical politeness systems

### Core Principle

**Use NEUTRAL form for all keywords - NO honorifics or politeness markers in code.**

**Rationale:**

1. **Code has no social hierarchy** - functions don't have status
2. **Python's philosophy** is flat and egalitarian
3. **Honorifics imply human relationships** - inappropriate for programming constructs
4. **Consistency** - honorific levels change based on context, keywords shouldn't

### Japanese (日本語)

**Japanese has multiple politeness levels:**

| Level | Form | Example (define) | Context |
|-------|------|------------------|---------|
| Dictionary/Plain | する (suru) | 定義する (teigi suru) ✅ | Neutral, textbooks |
| Polite | します (shimasu) | 定義します (teigi shimasu) ❌ | Polite conversation |
| Honorific | なさる (nasaru) | 定義なさる (teigi nasaru) ❌ | Respect/deference |
| Humble | いたす (itasu) | 定義いたす (teigi itasu) ❌ | Self-deprecating |

**Use Dictionary Form (Plain/Neutral):**

✅ **Correct:**

- `def` → `定義する` (teigi suru) - neutral dictionary form
- `return` → `返す` (kaesu) - neutral
- `print` → `印刷する` (insatsu suru) - neutral

❌ **Incorrect (politeness markers):**

- `def` → `定義します` (teigi shimasu) - too polite, implies code is being polite to user
- `return` → `返します` (kaeshimasu) - inappropriate politeness

**Why dictionary form:**

- Used in technical writing
- Used in textbooks
- Neutral, no implied social relationship
- Most flexible (works in all contexts)

### Korean (한국어)

**Korean has formal speech levels (하십시오체, 해요체, 해체):**

| Level | Form | Example (define) | Context |
|-------|------|------------------|---------|
| Dictionary/Base | 하다 (hada) | 정의하다 (jeong-uihada) ✅ | Neutral, textbooks |
| Informal polite | 해요 (haeyo) | 정의해요 (jeong-uihaeyo) ❌ | Polite conversation |
| Formal polite | 합니다 (hamnida) | 정의합니다 (jeong-uihamnida) ❌ | Very polite/formal |

**Use Dictionary Form (하다 form):**

✅ **Correct:**

- `def` → `정의하다` (jeong-uihada) - neutral dictionary form
- `return` → `돌려주다` (dollyeojuda) - neutral
- `print` → `출력하다` (chullyeokhada) - neutral

❌ **Incorrect (politeness markers):**

- `def` → `정의해요` (jeong-uihaeyo) - polite ending, inappropriate for keywords
- `def` → `정의합니다` (jeong-uihamnida) - formal ending, not for code

**Why dictionary form:**

- Standard in technical documentation
- Neutral, no politeness implied
- Used in CS textbooks in Korea

### Hindi (हिन्दी)

**Hindi has formal vs informal address (आप vs तू/तुम):**

| Form | Example (define) | Context |
|------|------------------|---------|
| Infinitive (neutral) | परिभाषित करना (paribhaashit karna) ✅ | Neutral, dictionaries |
| Formal command | परिभाषित कीजिए (paribhaashit kijiye) ❌ | Polite command (आप form) |
| Informal command | परिभाषित करो (paribhaashit karo) ❌ | Informal command |

**Use Infinitive Form (करना ending):**

✅ **Correct:**

- `def` → `परिभाषित करना` (paribhaashit karna) - neutral infinitive
- `return` → `वापस करना` (vaapas karna) - neutral
- `print` → `छापना` (chhapna) - neutral

❌ **Incorrect (formal/informal commands):**

- `def` → `परिभाषित कीजिए` (paribhaashit kijiye) - formal command with आप (aap), too polite
- `def` → `परिभाषित करो` (paribhaashit karo) - informal command, too direct

**Why infinitive form:**

- Neutral, no implied addressee
- Standard in technical dictionaries
- Used in educational materials

### Other Languages with Honorifics

**Thai, Vietnamese, Javanese, etc.:**

Same principle - **use the neutral/dictionary form** without honorific markers or politeness levels.

### Testing Your Translation

**Ask yourself:**

1. **Does this form imply a social relationship?**
   - YES → Wrong form, use neutral
   - NO → Good

2. **Would a textbook use this form?**
   - YES → Probably correct
   - NO → Check for politeness markers

3. **Does this form change based on who you're talking to?**
   - YES → Wrong form, use form that doesn't change
   - NO → Good

4. **Can you imagine saying "print hello" with this verb form to anyone?**
   - If it feels weird saying it to a superior OR a friend → Wrong form
   - If it works for everyone → Neutral form ✅

---

## Gendered Language Rules

### Languages Affected

Romance languages (Spanish, French, Portuguese, Italian), Arabic, Hebrew, German, Slavic languages, and others with grammatical gender

### Core Challenge

Many languages assign gender to nouns and adjectives. How do we handle this for programming terms?

### Constants (True, False, None)

**Rule: Use masculine form (generic/default in most gendered languages)**

**Why masculine:**

1. In Romance languages, masculine is the generic/unmarked form
2. These are programming constants, not describing gendered entities
3. Consistency across language pack

**Examples:**

| Language | True | False | None | Gender |
|----------|------|-------|------|--------|
| Spanish | Verdadero | Falso | Ninguno | Masculine |
| French | Vrai | Faux | Nul | Masculine |
| Portuguese | Verdadeiro | Falso | Nenhum | Masculine |
| Italian | Vero | Falso | Nullo | Masculine |
| German | Wahr | Falsch | Nichts | Neuter (N/A) |
| Arabic | صحيح | خطأ | لا شيء | Masculine |
| Russian | Истина | Ложь | Ничто | Feminine* |

***Russian exception:** Some languages use feminine for abstract concepts like "truth" (истина). Follow target language conventions.

❌ **Don't alternate genders:**

- Spanish: Verdadero, Falsa, Ninguno ❌ (inconsistent gender)
- French: Vrai, Fausse, Nul ❌ (inconsistent)

✅ **Keep consistent:**

- Spanish: Verdadero, Falso, Ninguno ✅ (all masculine)
- French: Vrai, Faux, Nul ✅ (all masculine)

### Nouns with Natural Gender

**For type names that are nouns:**

**Follow the natural gender of the target language word**

**Examples:**

**German (has three genders: masculine, feminine, neuter):**

- `class` → `Klasse` (feminine - die Klasse)
- `list` → `Liste` (feminine - die Liste)
- `dict` → `Wörterbuch` (neuter - das Wörterbuch)

**Spanish:**

- `list` → `lista` (feminine - la lista)
- `dict` → `diccionario` (masculine - el diccionario)

**Rule:** Use the gender that the target language noun naturally has. Don't force all nouns to be masculine.

### Adjectives That Modify Gendered Nouns

**Adjectives must agree with the noun's gender**

This is rare for keywords (most are verbs), but may apply to some terms.

**Example (if hypothetical):**

- Spanish: "empty list" → "lista vacía" (feminine adjective matches feminine noun)
- Spanish: "empty dictionary" → "diccionario vacío" (masculine adjective matches masculine noun)

### Gender-Neutral Strategies

**If target language has gender-neutral options:**

**Example - Gendered Professions:**

- Some languages have @, x, or e endings for gender neutrality
- Example: Latin@, Latinx, Latine

**For programming terms:**

- **Avoid gender-neutral innovations** unless widely adopted
- **Reason:** Keywords should be stable and widely understood
- **Exception:** If gender-neutral form is standard in CS education, use it

### German Special Case

**German capitalizes nouns (all genders):**

- `class` → `Klasse` (feminine, capitalized)
- `str` → `Zeichenkette` or `String` (feminine if using Zeichenkette, masculine if using String)
- `type` → `Typ` (masculine)

**Follow German grammar rules** - capitalize nouns regardless of gender.

### Testing Your Gendered Translation

**Checklist:**

1. **Are all constants the same gender?** (Usually masculine)
   - ✅ Verdadero, Falso, Ninguno (all masculine)
   - ❌ Verdadero, Falsa, Ninguno (mixed)

2. **Do noun type names use their natural language gender?**
   - ✅ German "Liste" (feminine - natural gender)
   - ❌ Forcing "der Liste" (masculine - unnatural)

3. **Do adjectives agree with nouns they modify?**
   - ✅ "lista vacía" (fem. adj. + fem. noun)
   - ❌ "lista vacío" (masc. adj. + fem. noun)

---

## RTL Language Practical Requirements

### Languages Affected

Arabic (ar), Hebrew (he), Urdu (ur), Farsi/Persian (fa)

### Core Challenge

**Mixed Directionality:** Code files will mix:

- **LTR (Left-to-Right):** English symbols, punctuation, numbers, identifiers
- **RTL (Right-to-Left):** Translated keywords in Arabic/Hebrew script

**Example (Arabic Python):**

```python
تعريف greet(اسم):  # def greet(name):
    إرجاع f"مرحبا، {اسم}!"  # return f"Hello, {name}!"
```

**How Unicode handles this:** The Unicode Bidirectional Algorithm automatically handles mixed LTR/RTL text.

### Bidirectional Text Handling

**What stays LTR:**

- Punctuation: `( ) : , . ; [ ] { }`
- Operators: `+ - * / = < > !`
- Quotes: `" '`
- Numbers: `0 1 2 3`
- English identifiers: `greet`, `name`, `myFunction`

**What becomes RTL:**

- Translated keywords: `تعريف`, `إرجاع`, `إذا`
- Arabic/Hebrew comments
- Arabic/Hebrew strings

**DO NOT mirror programming symbols** - they always stay in their English form and direction.

### Keyboard Input Considerations

**Critical Requirement:** Translations must be typeable on standard keyboards

**Test:**

1. Can you type this keyword on a standard Arabic/Hebrew keyboard?
2. Does it require switching input methods mid-word?
3. Are there rare diacritics that are hard to type?

✅ **Good (easy to type):**

- Arabic: `تعريف` (ta'rīf) - common letters
- Hebrew: `הגדר` (hagder) - common letters

❌ **Bad (hard to type):**

- Arabic with excessive diacritics: `تَعْرِيف` (too many marks)
- Rare/archaic characters that require special keyboard layouts

**Guideline:** Use standard modern script without rare characters or excessive diacritics.

### Visual Clarity

**Length Preference:** Short RTL keywords preferred

**Why:** Long RTL strings embedded in mostly-LTR code can be hard to scan visually.

**Recommendation:**

- **Maximum 10 characters** for RTL keywords
- Shorter is better for readability

**Examples:**

✅ **Good length:**

- `تعريف` (4 letters) ✅
- `إرجاع` (5 letters) ✅
- `إذا` (3 letters) ✅

⚠️ **Getting long:**

- `استثناء` (7 letters) ⚠️ Acceptable but approaching limit

❌ **Too long:**

- `تعريفالوظيفة` (12+ letters) ❌ Too long, hard to scan

### Diacritics Policy

**Arabic Diacritics (تشكيل - Tashkeel):**

Diacritics include: َ ً ُ ٌ ِ ٍ ّ ْ (fatha, damma, kasra, shadda, sukun, etc.)

**General Rule: NO diacritics in keywords**

**Why:**

1. Technical text doesn't use diacritics
2. Harder to type
3. Visual clutter in code
4. Native speakers read undiacritized text easily

**Rare exception:** Only add diacritics if absolute ambiguity exists (extremely rare)

✅ **Correct (no diacritics):**

- `تعريف` (ta'rīf) - clear without diacritics

❌ **Incorrect (unnecessary diacritics):**

- `تَعْرِيف` (ta'rīf with marks) - not needed

**Hebrew Niqqud (vowel points):**

Similar principle - **NO niqqud in keywords**

- Hebrew speakers read unvoweled text in technical contexts
- Niqqud is for religious texts or children's books, not code

### Punctuation Direction

**All programming punctuation stays LTR:**

```python
# Correct - punctuation faces LTR direction
تعريف myFunc(x, y):
    إرجاع x + y

# Parentheses ( ) stay LTR
# Colon : stays LTR
# Comma , stays LTR
# Operators + stay LTR
```

**Do NOT use RTL punctuation variants:**

- Don't use Arabic comma `،` instead of `,`
- Don't use Arabic semicolon `؛` instead of `;`
- Don't use RTL question mark `؟`

**Reason:** Programming languages expect ASCII punctuation.

### IDE Testing Requirements

**Before releasing RTL language pack, test in these environments:**

#### Required Tests

1. **VS Code**
   - Install: "Arabic Support" or "RTL Support" extension
   - Test: Syntax highlighting works
   - Test: Cursor movement (arrow keys)
   - Test: Text selection (click and drag)
   - Test: Copy/paste preserves direction

2. **PyCharm / IntelliJ**
   - Built-in RTL support
   - Same tests as VS Code

3. **Terminal (Linux, macOS, Windows)**
   - Test: Code displays correctly
   - Test: Error messages readable
   - Note: Some terminals have poor RTL support, document issues

4. **Jupyter Notebook**
   - Test: RTL keywords in cells
   - Test: Output displays correctly

#### Known Issues to Document

If any IDE has problems:

- **Document the issue** in language pack README
- **Provide workaround** (e.g., "Install X extension")
- **Note limitations** (e.g., "Terminal X doesn't support RTL well")

### Example Workarounds

**VS Code users:**

```markdown
## Arabic Python Setup (VS Code)

1. Install "Arabic Support" extension
2. Enable bidirectional text:
   - Settings → "editor.bidiTextRendering": "on"
3. Recommended font: "Arial" or "Tahoma" (good Arabic rendering)
```

### Unicode Compatibility

**Ensure your translations use common Unicode blocks:**

**Arabic:**

- Use: Arabic (U+0600–U+06FF)
- Avoid: Arabic Extended-A (rare chars)
- Avoid: Arabic Presentation Forms (should be composed)

**Hebrew:**

- Use: Hebrew (U+0590–U+05FF)
- Avoid: Hebrew Presentation Forms

**Test rendering** in at least 3 common fonts:

- Windows: Arial, Tahoma
- macOS: Arial, Helvetica
- Linux: DejaVu Sans, Liberation Sans

### Fallback Plan

**If RTL proves too problematic in major IDEs:**

1. Document issues clearly
2. Consider English as interim option for that keyword
3. Re-evaluate when IDE support improves
4. Community can use English keywords while RTL support matures

**Quality over perfection:** Better to have working English keywords than broken RTL keywords.

---

## Translation Checklist

For each translation, verify:

- [ ] **Correct word type** (verb, noun, adjective, etc.)
- [ ] **Appropriate form** (infinitive, present, etc.)
- [ ] **Natural phrasing** (native speaker would use it)
- [ ] **Technical accuracy** (preserves programming meaning)
- [ ] **Reasonable length** (1-2 words for keywords, varies for builtins)
- [ ] **Consistent with other translations** (matches pattern in language pack)
- [ ] **Proper character set** (correct script for language)
- [ ] **Cultural appropriateness** (no unintended meanings)

---

## Examples from Existing Packs

### Spanish (es)

| English | Translation | Type | Form | Notes |
|---------|-------------|------|------|-------|
| def | definir | verb | infinitive | Standard CS term |
| return | retornar | verb | infinitive | Not "devolver" (different nuance) |
| if | si | conjunction | - | Standard conditional |
| True | Verdadero | adjective | masculine | Capitalized |
| print | imprimir | verb | infinitive | Standard tech term |

### Arabic (ar)

| English | Translation | Type | Form | Notes |
|---------|-------------|------|------|-------|
| def | تعريف | verbal noun | masdar | ta'rīf (definition) |
| return | إرجاع | verbal noun | masdar | irjā' (returning) |
| if | إذا | particle | - | idhā (if) |
| True | صحيح | adjective | - | ṣaḥīḥ (true/correct) |

---

## Special Cases

### Abbreviations

Some Python keywords are abbreviations:

- `def` = "define"
- `elif` = "else if"

**Guideline:** Translate the full concept, not the abbreviation

### Version-Specific Keywords

Python 3.10+:

- `match` - pattern matching (like switch)
- `case` - pattern case

Python 3.11+:

- `except*` - exception group handling

Python 3.12+:

- `type` - type alias declaration

**Guideline:** Consider how these fit into existing keyword patterns

---

## Transliteration vs Translation

### When to Transliterate vs When to Translate

**General Principle:** Translate concepts, not words. Transliteration should be rare.

### Acceptable Transliteration Cases

**1. No Native Equivalent Exists**

- **Example:** `lambda` - Greek letter representing anonymous functions
- **Solution:** Most languages keep "lambda" (Greek mathematical term, universal)
- **Rationale:** Inventing a new term would disconnect from mathematical roots

**2. Loanword is Universally Adopted**

- **Example:** "computer" in some languages has become a loanword
- **Solution:** Use established loanword if widely recognized
- **Test:** Would 90%+ of programmers in that language use the loanword?

**3. Native Term Creates Ambiguity**

- **Example:** If translation has multiple meanings that cause confusion
- **Solution:** Transliterate English term to avoid ambiguity
- **Rationale:** Clarity > linguistic purity

### Unacceptable Transliteration

**❌ When Clear Native Term Exists**

- `def` → Don't phonetically spell "def" in target script
- `return` → Don't transliterate "riturn"
- **Solution:** Translate the concept ("to define", "to return")

**❌ When Concept is Translatable**

- Most programming concepts have equivalents across languages
- Transliteration is lazy, not helpful to learners
- **Solution:** Find native term that captures the concept

### Language-Specific Loanword Policies

| Language | Loanword Strategy | Example | Rationale |
|----------|------------------|---------|-----------|
| Spanish | Minimal loanwords | ✅ "definir" ❌ "definar" | Rich technical vocabulary, translate concepts |
| French | Minimal loanwords | ✅ "définir" ❌ "definer" | Language policy favors French terms |
| Arabic | Avoid loanwords | ✅ "تعريف" ❌ "ديف" | MSA has roots to create technical terms |
| Chinese | Translate concepts | ✅ "定义" ❌ phonetic | Established CS terminology exists |
| Hindi | Balance approach | ✅ "परिभाषित" for concepts, "lambda" for Greek | Sanskrit roots available, but some universals kept |
| Japanese | Katakana acceptable | ✅ "定義" for concepts, "ラムダ" (lambda) OK | Katakana used for foreign technical terms |
| Korean | Translate preferred | ✅ "정의하다" ❌ phonetic | Sino-Korean vocabulary for technical terms |
| German | Translate concepts | ✅ "definieren" ❌ "defen" | Germanic roots for technical vocabulary |
| Russian | Translate concepts | ✅ "определить" ❌ phonetic | Slavic vocabulary for programming terms |

### Decision Framework

**For each term, ask:**

1. **Does a native word exist that captures this concept?**
   - YES → Translate (use native word)
   - NO → Continue to question 2

2. **Is this term a universal technical/mathematical concept?**
   - YES (like lambda, π) → Transliterate acceptable
   - NO → Continue to question 3

3. **Would transliteration cause confusion or look unprofessional?**
   - YES → Find creative native solution or compound term
   - NO → Transliterate acceptable (but translate preferred)

### Examples

**Good Transliteration:**

- `lambda` → "lambda" (most languages) - Greek mathematical term
- `async` → "async" (some languages) - widely adopted in tech

**Bad Transliteration:**

- `def` → "дэф" (Russian phonetic) ❌ - Should be "определить"
- `return` → "रिटर्न" (Hindi phonetic) ❌ - Should be "वापसी" or similar
- `print` → "برنت" (Arabic phonetic) ❌ - Should be "طباعة"

### Special Case: Abbreviations

Python has abbreviations (def = define, elif = else if):

**Guideline:** Translate the FULL concept, not the abbreviation itself

- `def` → Translate "define" (not "d-e-f")
- `elif` → Translate "else if" concept (compound)

---

### Cultural Sensitivity

Avoid translations that:

- Have offensive meanings in target language
- Sound childish or unprofessional
- Conflict with religious/cultural norms
- Are difficult to type on standard keyboards

---

## Review Process

All translations should be:

1. **AI-Generated with Context** - Using deep context documents
2. **Native Speaker Reviewed** - At least 2-3 reviewers per language
3. **Consensus-Based** - 75%+ agreement required
4. **Community Approved** - Marked `community_reviewed: true` after consensus

---

## References

- [Git Commit Message Conventions](https://www.conventionalcommits.org/)
- [Unicode CLDR - Language Data](https://cldr.unicode.org/)
- [Python Official Documentation](https://docs.python.org/)
- [BCP 47 - Language Tags](https://www.rfc-editor.org/rfc/bcp/bcp47.txt)

---

**Maintained by:** Legesher Team
**Last Updated:** 2025-10-28
**Version:** 2.0
