# Test Case 02: `True` → Spanish

**Ready to copy/paste into Claude Desktop**

---

You are an expert linguist and computer science educator specializing in translating programming language keywords and builtins for multilingual developers. Your task is to translate Python keywords and builtins into target languages while preserving technical accuracy, consistency, and learnability.

**Critical Principles:**

1. **Translate the CONCEPT, not the English word**
2. **Prioritize technical accuracy over literal translation**
3. **Ensure consistency with related terms in the same pattern**
4. **Consider how this term is taught in CS education in target regions**
5. **Balance naturalness with international consistency**

**Project Goal: Full Localization**

This translation is part of the **Legesher** project, which enables developers to code in their native language instead of English. The goal is **full localization** - allowing developers to write Python code entirely in their native language, making programming accessible to non-English speakers worldwide.

**What this means for your translation:**

- **Think like a native speaker developer** - This constant will be used by developers writing code in Spanish, not just reading English code
- **Optimize for daily use** - Developers will type this many times per day, so it needs to be natural, memorable, and comfortable
- **Consider the learning experience** - New programmers learning to code in Spanish should understand this term intuitively
- **Imagine code review discussions** - Developers will speak this term out loud when discussing boolean logic with teammates
- **Full native experience** - The entire codebase will be in Spanish, not a mix of English and Spanish

This is not about translating documentation or comments - this is about making Python itself speak Spanish.

---

## Translation Task

<task>
Translate the Python keyword **`True`** into **Spanish**.

You will be provided with:

- Complete context document (Tier 1 translation brief)
- Linguistic standards for consistency
- Pattern classification for this term
- Examples of good and bad translations
- Cross-references to related terms
</task>

---

## Input Context

<context>

# Python Keyword: `True` - Translation Brief (Tier 1)

**Difficulty:** EASY
**Pattern:** VALUE_CONSTANT
**Python Version:** 3.10+

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
is_active = True
```

### Example 2: Common Pattern

```python
def is_valid(value):
    if value > 0:
        return True
    else:
        return False
```

### Example 3: Boolean Logic

```python
has_permission = True
is_admin = False

if has_permission and not is_admin:
    print("Regular user with permission")
```

## What This Term DOES in Python

`True` is a **boolean constant** representing logical truth. It's one of two possible boolean values (the other being `False`).

**Key concept:** This represents the logical/boolean concept of "true" in computer science, not truth in a philosophical or everyday sense. It's a fixed constant value, not a verb or action.

## Pattern Classification

**This term is:** VALUE_CONSTANT

**Similar terms in this pattern:**

1. `False` - Boolean false value
2. `None` - Null/empty value
3. (Constants are values, not actions)

**Consistency requirement:** All VALUE_CONSTANT keywords should use the same form (typically nouns or adjectives, not verbs). For gendered languages, constants typically use masculine form for consistency.

## Translation Guidance

### Good Translation Characteristics

- ✅ Captures the boolean "true" concept
- ✅ Noun or adjective form (NOT a verb)
- ✅ Short (1 word ideally)
- ✅ Used in CS/logic education in target language
- ✅ Matches form of `False` (should be grammatically parallel)

### Common Mistakes to Avoid

- ❌ Using a verb form ("es verdad" = is true)
- ❌ Philosophical "truth" instead of logical "true"
- ❌ Too colloquial ("sí" = yes - not the same as true)
- ❌ Wrong gender (should match pattern with False/None)

</context>

<linguistic_standards>

## Key Linguistic Standards for Spanish

**Register:** Technical/formal (CS education vocabulary)

- NOT everyday conversational Spanish
- NOT philosophical concepts
- TARGET: Boolean/logical terminology from CS education

**Form for VALUE_CONSTANT:** Noun or adjective

- Should represent a STATE or VALUE, not an action
- Examples: verdadero (true), falso (false), ninguno (none)

**Pattern:** This is a VALUE_CONSTANT keyword

- VALUE constants represent fixed values
- Should use noun/adjective forms, NOT verbs
- Must be grammatically parallel with other constants

**Gendered Language Rule for Constants:**

- Use masculine form for consistency
- Spanish: verdadero (masc) not verdadera (fem)
- Rationale: Constants should be consistent, masculine is default/generic

**Consistency:** Must align with translations of similar terms

- `False` should be grammatically parallel (same gender, same form type)
- `None` should also follow same pattern

**Capitalization for Constants:**

- First letter capitalized, rest lowercase
- Example: Verdadero (not VERDADERO, not verdadero)
- Matches Python pattern (True not TRUE or true)

**Length limits:** 1 word for simple constants

</linguistic_standards>

<existing_translations>

Related terms that should be translated in Spanish:

| Term | Expected Pattern | Form Type |
|------|------------------|-----------|
| True | ??? | noun/adjective (masculine) |
| False | (parallel to True) | noun/adjective (masculine) |
| None | (parallel to True/False) | noun/adjective (masculine) |

**Note:** Since these are the first constants being translated, your choice sets the pattern for all other constants.

</existing_translations>

---

## Reasoning Process

Please think through this translation step-by-step using the following framework:

<reasoning_framework>

### Step 1: Concept Analysis

<concept_analysis>

- What does this term DO in Python? (not what the English word means)
- Is this an ACTION (something you do) or STATE/VALUE (something that is)?
- What programming concept does it represent?
- Which meaning of the English word applies to Python? (if ambiguous)
</concept_analysis>

### Step 2: Generate Options

<translation_options>
Generate 3-5 possible translations:

1. {option_1} - {rationale}
2. {option_2} - {rationale}
3. {option_3} - {rationale}
4. {option_4} - {rationale}
5. {option_5} - {rationale}
</translation_options>

### Step 3: Apply Priority Framework

<priority_filtering>

**Priority 1: Technical Accuracy (eliminate incorrect meanings)**

- ❌ {option_x} - wrong meaning because {reason}
- ✅ {option_y} - correct meaning
- ✅ {option_z} - correct meaning

**Priority 2: CS Education Alignment (research regional usage)**

- What term appears in Spanish CS/logic textbooks for boolean true?
- What term appears in Spanish Python tutorials?
- What term would students already know from logic/boolean algebra?
- Winner: {term} because {reason}

**Priority 3: Naturalness (among remaining options)**

- Is it easy to say out loud?
- Is it memorable?
- Does it feel natural to native speakers?

**Priority 4: Consistency (check pattern alignment)**

- Does this match the form expected for VALUE_CONSTANT?
- Is it grammatically parallel with `False` (opposite concept)?
- Does it set a good pattern for other constants like `None`?

</priority_filtering>

### Step 4: Validate

<validation>
Run through checklist:
- [ ] Captures the PYTHON CONCEPT (boolean true, not philosophical truth)?
- [ ] Correct part of speech (noun/adjective, NOT verb)?
- [ ] Correct form (masculine gender for consistency)?
- [ ] Matches pattern of VALUE_CONSTANT keywords?
- [ ] Short enough (1 word for simple constant)?
- [ ] Easy to pronounce and type?
- [ ] No offensive or misleading meanings?
- [ ] Will render properly in IDEs?
- [ ] Aligns with CS education (logic/boolean terminology)?
- [ ] Sets good pattern for False/None translations?
</validation>

### Step 5: Confidence Assessment

<confidence>
Rate your confidence: HIGH | MEDIUM | LOW

**If MEDIUM or LOW, explain why:**

- What concerns do you have?
- What would you want a human reviewer to verify?
- Are there multiple equally valid options?
- Is this a culturally/linguistically complex case?
</confidence>

</reasoning_framework>

---

## Output Format

Provide your translation in the following XML structure:

```xml
<translation_result>
  <term>True</term>
  <target_language>Spanish</target_language>

  <recommended_translation>
    <translation>{your_translation}</translation>
    <form>{noun|adjective|etc}</form>
    <confidence>{HIGH|MEDIUM|LOW}</confidence>
  </recommended_translation>

  <reasoning>
    <concept_analysis>
      {What this term represents in Python - boolean logical value}
    </concept_analysis>

    <translation_options>
      <option priority="1">
        <translation>{option_1}</translation>
        <form>{form}</form>
        <rationale>{why you considered this}</rationale>
        <eliminated>{yes|no}</eliminated>
        <elimination_reason>{if eliminated, why}</elimination_reason>
      </option>
      <!-- Add 3-5 options total -->
    </translation_options>

    <priority_filtering>
      <technical_accuracy>
        {Which options capture boolean true? Which are wrong meanings?}
      </technical_accuracy>

      <cs_education_alignment>
        {What term appears in Spanish CS/logic textbooks?}
      </cs_education_alignment>

      <naturalness>
        {Which option is most natural for Spanish speakers?}
      </naturalness>

      <consistency_check>
        {Does this set a good pattern for False/None?}
        {Is it grammatically parallel with False?}
      </consistency_check>
    </priority_filtering>

    <final_decision>
      {Why you chose this specific translation}
    </final_decision>
  </reasoning>

  <alternatives_considered>
    <alternative rank="2">
      <translation>{second_best_option}</translation>
      <form>{form}</form>
      <why_not_chosen>{explanation}</why_not_chosen>
    </alternative>
  </alternatives_considered>

  <validation_checklist>
    <item checked="true">Captures Python concept (boolean true)</item>
    <item checked="true">Correct part of speech (noun/adjective)</item>
    <item checked="true">Correct form (masculine gender)</item>
    <item checked="true">Matches VALUE_CONSTANT pattern</item>
    <item checked="true">Short enough (1 word)</item>
    <item checked="true">Easy to pronounce</item>
    <item checked="true">No offensive meanings</item>
    <item checked="true">Renders in IDEs</item>
    <item checked="true">CS education aligned</item>
    <item checked="true">Sets good pattern for other constants</item>
  </validation_checklist>

  <human_review_notes>
    {Any concerns or regional considerations?}
  </human_review_notes>

  <metadata>
    <difficulty>EASY</difficulty>
    <pattern>VALUE_CONSTANT</pattern>
    <python_version>3.10+</python_version>
  </metadata>
</translation_result>
```

---

## Important Reminders

1. **Think step-by-step** - Consider multiple options
2. **Boolean logic term** - This is CS terminology, not everyday language
3. **Research CS education** - What do Spanish logic/CS textbooks use?
4. **Set the pattern** - Your choice affects `False` and `None` translations
5. **Gender consistency** - Use masculine form for all constants
6. **Capitalization** - First letter cap, rest lowercase (Verdadero not VERDADERO)

---

**Now translate:** `True` → Spanish
