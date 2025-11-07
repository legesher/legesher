# Test Case 01: `def` → Spanish

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

- **Think like a native speaker developer** - This keyword will be used by developers writing code in Spanish, not just reading English code
- **Optimize for daily use** - Developers will type this hundreds of times per day, so it needs to be natural, memorable, and comfortable
- **Consider the learning experience** - New programmers learning to code in Spanish should understand this term intuitively
- **Imagine code review discussions** - Developers will speak this term out loud when discussing code with teammates
- **Full native experience** - The entire codebase will be in Spanish, not a mix of English and Spanish

**Example of full localization:**

Instead of writing mixed code like:

```python
def calculate_total(price, tax):  # Mix of English keywords
    return price + tax
```

Developers will write fully localized code:

```python
{spanish_def} calcular_total(precio, impuesto):  # Fully in Spanish
    {spanish_return} precio + impuesto
```

This is not about translating documentation or comments - this is about making Python itself speak Spanish.

---

## Translation Task

<task>
Translate the Python keyword **`def`** into **Spanish**.

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

# Python Keyword: `def` - Translation Brief (Tier 1)

**Difficulty:** EASY
**Pattern:** ACTION_KEYWORD
**Python Version:** 3.10+

## Code Examples FIRST (Learn by Seeing)

### Example 1: Minimal Usage

```python
def greet():
    print("Hello!")
```

### Example 2: Common Pattern

```python
def calculate_total(price, tax_rate):
    tax = price * tax_rate
    total = price + tax
    return total
```

### Example 3: Edge Case

```python
def outer():
    def inner():  # Nested function definition
        return "inner"
    return inner
```

## What This Term DOES in Python

The `def` keyword **defines a function**. It tells Python "I am about to establish a new function with this name and these parameters."

**Key concept:** This is about DEFINING/ESTABLISHING a function, not just creating something generic. The term captures the specific programming concept of "function definition."

## Pattern Classification

**This term is:** ACTION KEYWORD

**Similar terms in this pattern:**

1. `class` - Defines a class
2. `return` - Returns a value from function
3. `lambda` - Defines anonymous function

**Consistency requirement:** All ACTION keywords should use the same grammatical form (typically infinitive verbs in Romance languages).

## Translation Guidance

### Good Translation Characteristics

- ✅ Captures the "defining/establishing" concept
- ✅ Infinitive verb form (for Romance languages like Spanish)
- ✅ Short (1 word ideally)
- ✅ Used in CS education in target language
- ✅ Matches form of other ACTION keywords

### Common Mistakes to Avoid

- ❌ Using a noun instead of verb ("función" = function)
- ❌ Too generic ("crear" = create - too broad)
- ❌ Wrong verb tense (should be infinitive, not conjugated)
- ❌ Too long (more than 2 words for a keyword)

</context>

<linguistic_standards>

## Key Linguistic Standards for Spanish

**Register:** Technical/formal (CS education vocabulary)

- NOT academic stuffy (avoid archaic terms)
- NOT colloquial slang (avoid regional dialects)
- TARGET: Professional technical register used in CS textbooks

**Form for ACTION keywords:** Infinitive verb

- Spanish infinitives end in -ar, -er, or -ir
- Examples: definir (to define), retornar (to return), romper (to break)

**Pattern:** This is an ACTION keyword

- ACTION keywords perform an operation
- Should use infinitive verb form in Spanish
- Must be consistent with other ACTION keywords

**Consistency:** Must align with translations of similar terms

- `return` → "retornar" (infinitive)
- `break` → "romper" (infinitive)
- `continue` → "continuar" (infinitive)
- Therefore `def` should also use infinitive form

**Length limits:** 1-2 words maximum for keywords

**Capitalization:** All lowercase (Python keywords are lowercase)

</linguistic_standards>

<existing_translations>

Related terms already translated in Spanish:

| Term | Translation | Form |
|------|-------------|------|
| return | retornar | infinitive |
| break | romper | infinitive |
| continue | continuar | infinitive |
| class | clase | noun (but special case - "class" is itself a noun) |

</existing_translations>

---

## Reasoning Process

Please think through this translation step-by-step using the following framework:

<reasoning_framework>

### Step 1: Concept Analysis

<concept_analysis>

- What does this term DO in Python? (not what the English word means)
- Is this an ACTION (something you do) or STATE (something that is)?
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

- What term appears in Spanish CS textbooks?
- What term appears in Spanish Python tutorials?
- What term would students already know?
- Winner: {term} because {reason}

**Priority 3: Naturalness (among remaining options)**

- Is it easy to say out loud?
- Is it memorable?
- Does it feel natural to native speakers?

**Priority 4: Consistency (check pattern alignment)**

- Does this match the form of related terms?
- If `return` uses infinitive, this should too
- Check cross-references for consistency requirements

</priority_filtering>

### Step 4: Validate

<validation>
Run through checklist:
- [ ] Captures the PYTHON CONCEPT (not just English word)?
- [ ] Correct part of speech (verb/noun/adjective)?
- [ ] Correct form (infinitive for ACTION keywords)?
- [ ] Matches pattern of similar keywords?
- [ ] Short enough (1-2 words for keywords)?
- [ ] Easy to pronounce and type?
- [ ] No offensive or misleading meanings?
- [ ] Will render properly in IDEs?
- [ ] Aligns with CS education in target language?
- [ ] Consistent with related term translations?
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
  <term>def</term>
  <target_language>Spanish</target_language>

  <recommended_translation>
    <translation>{your_translation}</translation>
    <form>{infinitive|noun|adjective|etc}</form>
    <confidence>{HIGH|MEDIUM|LOW}</confidence>
  </recommended_translation>

  <reasoning>
    <concept_analysis>
      {What this term DOES in Python, not what the English word means}
    </concept_analysis>

    <translation_options>
      <option priority="1">
        <translation>{option_1}</translation>
        <form>{form}</form>
        <rationale>{why you considered this}</rationale>
        <eliminated>{yes|no}</eliminated>
        <elimination_reason>{if eliminated, why}</elimination_reason>
      </option>
      <option priority="2">
        <translation>{option_2}</translation>
        <form>{form}</form>
        <rationale>{why you considered this}</rationale>
        <eliminated>{yes|no}</eliminated>
        <elimination_reason>{if eliminated, why}</elimination_reason>
      </option>
      <!-- Add 3-5 options total -->
    </translation_options>

    <priority_filtering>
      <technical_accuracy>
        {Which options are technically accurate? Which are wrong? Why?}
      </technical_accuracy>

      <cs_education_alignment>
        {What did you find about how this concept is taught in Spanish?}
        {What terms appear in textbooks/tutorials?}
      </cs_education_alignment>

      <naturalness>
        {Among technically correct options, which is most natural?}
      </naturalness>

      <consistency_check>
        {Does this align with related term translations?}
        {Does it follow the pattern classification?}
      </consistency_check>
    </priority_filtering>

    <final_decision>
      {Why you chose this specific translation over the alternatives}
    </final_decision>
  </reasoning>

  <alternatives_considered>
    <alternative rank="2">
      <translation>{second_best_option}</translation>
      <form>{form}</form>
      <why_not_chosen>{explanation}</why_not_chosen>
    </alternative>
    <alternative rank="3">
      <translation>{third_best_option}</translation>
      <form>{form}</form>
      <why_not_chosen>{explanation}</why_not_chosen>
    </alternative>
  </alternatives_considered>

  <validation_checklist>
    <item checked="true">Captures Python concept</item>
    <item checked="true">Correct part of speech</item>
    <item checked="true">Correct form</item>
    <item checked="true">Matches pattern</item>
    <item checked="true">Short enough</item>
    <item checked="true">Easy to pronounce</item>
    <item checked="true">No offensive meanings</item>
    <item checked="true">Renders in IDEs</item>
    <item checked="true">CS education aligned</item>
    <item checked="true">Consistent with related terms</item>
  </validation_checklist>

  <human_review_notes>
    {If confidence is not HIGH, what should human reviewers verify?}
    {Any cultural/regional considerations?}
    {Any ambiguity that needs native speaker input?}
  </human_review_notes>

  <metadata>
    <difficulty>EASY</difficulty>
    <pattern>ACTION_KEYWORD</pattern>
    <python_version>3.10+</python_version>
  </metadata>
</translation_result>
```

---

## Important Reminders

1. **Think step-by-step** - Don't jump to the first translation that comes to mind
2. **Show your work** - Fill out ALL reasoning sections so human reviewers understand your logic
3. **Research CS education** - Consider how this concept is taught in Spanish-speaking regions
4. **Check consistency** - Look at related term translations (retornar, romper, continuar)
5. **Be honest about confidence** - If you're unsure, say so and explain why
6. **Consider the learner** - Will a Spanish-speaking student understand this? Can they remember it? Can they pronounce it?

---

**Now translate:** `def` → Spanish
