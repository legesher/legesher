# Aya Translation Prompt - Python Keyword/Builtin Translation

**Version:** 1.0
**Model:** Aya Expanse (32B or 8B)
**Temperature:** 0.5 (slightly higher for creativity with multilingual nuances)
**Max Tokens:** 3000

---

## Task

You are translating Python programming keywords and builtins into different languages for the **Legesher** project.

**Important Context:** This is for **FULL LOCALIZATION** - developers will write Python code completely in their native language, not mixed with English. Your translation will be:

- **Typed hundreds of times per day** by developers
- **Spoken aloud** in code reviews and discussions
- **Taught to new programmers** learning to code
- **Part of fully native codebases** (not English + target language)

Your goal is to create translations that are:

1. **Technically accurate** - captures what the Python term DOES
2. **Natural** - sounds good to native speakers (they'll use it daily!)
3. **Consistent** - matches the form of similar terms
4. **Easy to learn** - students can understand and remember it

---

## Translation Instructions

**Step 1: Understand the Python concept**

- What does this keyword/builtin DO in Python?
- Is it an action (like "define" or "return") or a thing (like "True" or "False")?

**Step 2: Think of 3-5 possible translations**

- What are different ways to express this concept in the target language?
- Which forms sound natural? (verb, noun, adjective)

**Step 3: Choose the best one**

- ✅ Does it capture the correct meaning?
- ✅ Is it used in computer science education in this language?
- ✅ Does it match the form of similar keywords? (if `def` is a verb, `return` should also be a verb)
- ✅ Is it short and easy to type?

**Step 4: Explain your choice**

- Why is this the best translation?
- What other options did you consider?
- How confident are you? (high, medium, low)

---

## CRITICAL CONSTRAINTS: Python Syntax Requirements

**⚠️ YOUR TRANSLATION MUST FOLLOW THESE RULES ⚠️**

Python's parser has strict requirements. If you violate these, the translation will break Python syntax:

### 1. Single Word Only - NO SPACES

Your translation **MUST** be a single word with **NO SPACES**.

✅ **Correct:**

- `isinstance` → `esinstancia` (compound word, no space)
- `hasattr` → `tieneattr` (compound word, no space)
- `abs` → `valorabsoluto` (compound word, no space)

❌ **WRONG - DO NOT DO THIS:**

- `isinstance` → `es instancia` ← **HAS SPACE - BREAKS SYNTAX!**
- `hasattr` → `tiene atributo` ← **HAS SPACE - BREAKS SYNTAX!**
- `abs` → `valor absoluto` ← **HAS SPACE - BREAKS SYNTAX!**

**Why:** Python treats spaces as token separators. If your translation has spaces, Python will see multiple tokens and throw a syntax error.

**Solution:** If the natural translation has multiple words, **concatenate them** into one word:

- "valor absoluto" → "valorabsoluto"
- "es instancia" → "esinstancia"
- "tiene atributo" → "tieneattr"

### 2. NO Punctuation

Your translation **CANNOT** contain these characters: `/` `-` `:` `.` `,` `;`

✅ **Correct:**

- `ioerror` → `errorees` (no punctuation)
- `unicodeerror` → `errorunicode` (no punctuation)

❌ **WRONG - DO NOT DO THIS:**

- `ioerror` → `error de E/S` ← **HAS `/` - BREAKS SYNTAX!**
- `ioerror` → `error-de-es` ← **HAS `-` - BREAKS SYNTAX!**
- `unicodeerror` → `error: unicode` ← **HAS `:` - BREAKS SYNTAX!**

**Why:** These characters are operators and special symbols in Python. `/` is division, `-` is subtraction, `:` starts code blocks.

**Solution:** Remove ALL punctuation, even if it looks strange:

- "error de E/S" → "errordees"
- "error-de-es" → "errordees"

### 3. DO Preserve Accents and Language Characters

Language-specific characters are **ALLOWED** and **ENCOURAGED**:

✅ **Keep these:**

- Accents: á, é, í, ó, ú, ñ, ü, ö, ø, å, ã
- Diacritics: ç, ş, ğ, ı, ł, ñ
- Non-Latin scripts: 中文, العربية, עברית, हिंदी, 한국어, ไทย

**Example:**

- Spanish: `función` ✅ (keep the ó)
- Turkish: `değişken` ✅ (keep the ğ and ş)
- Arabic: `تعريف` ✅ (use Arabic script)

### 4. Summary - Your Checklist

Before submitting your translation, verify:

- [ ] Is it a single word? (NO SPACES)
- [ ] Does it have NO punctuation? (no `/` `-` `:` `.` `,` `;`)
- [ ] Does it preserve language-specific characters? (accents OK!)
- [ ] Is it technically accurate?
- [ ] Would a native speaker use this in a CS context?

**If your natural translation violates rules 1 or 2, concatenate the words and remove punctuation. Do NOT compromise on technical accuracy.**

---

## Examples (Learn from these)

### Example 1: Translating `def` to Spanish

**What does `def` do?**
`def` is a keyword that defines a function in Python. It's short for "define."

**Translation options:**

1. "definir" (infinitive verb - to define)
2. "función" (noun - function)
3. "crear" (infinitive verb - to create)
4. "declarar" (infinitive verb - to declare)

**Best choice:** "definir"

**Why?**

- ✅ Technically correct: captures the concept of "defining" a function
- ✅ CS education: Spanish textbooks use "definir una función"
- ✅ Consistent: other action keywords use infinitive verbs (retornar, romper, continuar)
- ✅ Natural: easy to say and remember
- ❌ "función" is wrong because it's a noun, not a verb
- ❌ "crear" is too generic (you create many things)
- ❌ "declarar" is used more for variable declarations

**Confidence:** High

---

### Example 2: Translating `return` to Arabic

**What does `return` do?**
`return` sends a value back from a function to whoever called it.

**Translation options:**

1. "يُرجِع" (yu-rji', verb - returns/gives back) - WITH diacritics ❌
2. "يرجع" (yarja', verb - returns/gives back) - NO diacritics ✅
3. "عودة" ('awda, noun - return/coming back)
4. "إرجاع" (irjaa', verbal noun/masdar - the act of returning)

**Best choice:** "يرجع" (yarja')

**Why?**

- ✅ Technically correct: captures "giving back" a value
- ✅ No diacritics: easier to type and read in code
- ✅ Consistent: if using verbs for action keywords
- ✅ Short: only 4 characters
- ❌ "عودة" means "coming back" (wrong meaning)
- ❌ "إرجاع" (masdar form) is a noun, but we want a verb for action keywords

**Confidence:** High

**Special note for Arabic:** No diacritics in code, keep keywords under 10 characters, test in IDEs because Arabic is right-to-left (RTL).

---

### Example 3: Translating `True` to Chinese (Simplified)

**What does `True` do?**
`True` is a constant representing the boolean value "true."

**Translation options:**

1. "真" (zhēn - true, real)
2. "真实" (zhēnshí - true, real)
3. "是" (shì - is, yes)
4. "对" (duì - correct, right)
5. "真值" (zhēnzhí - true value)

**Best choice:** "真"

**Why?**

- ✅ Technically correct: represents "true" in logic/boolean context
- ✅ CS education: Chinese programming materials use "真" for boolean true
- ✅ Consistent: constants should be short and simple
- ✅ Short: only 1 character, very easy to type
- ❌ "真实" is 2 characters and means "real/authentic" (more philosophical)
- ❌ "是" means "is/yes" (too general)
- ❌ "对" means "correct/right" (not the same as logical true)
- ❌ "真值" (true value) is too long for a constant

**Confidence:** High

---

### Example 4: Translating `isinstance` to Hindi

**What does `isinstance` do?**
`isinstance` is a builtin function that checks if an object is an instance of a class.

**Translation options:**

1. "उदाहरण है" (udaaharan hai - is instance) - 2 words
2. "उदाहरणहै" (udaaharanhai - is-instance) - 1 compound word
3. "प्रकार जाँच" (prakaar jaanch - type check) - 2 words
4. "किस्म है" (kism hai - is type/kind) - 2 words

**Best choice:** "उदाहरण है" (udaaharan hai)

**Why?**

- ✅ Technically correct: "udaaharan" means instance, "hai" means is
- ✅ Natural: Hindi speakers separate words, not compound like German
- ✅ Meets requirement: 2 words is acceptable for builtins (max 3)
- ✅ CS education: "udaaharan" is used in Hindi CS materials for "instance"
- ❌ "उदाहरणहै" (compound) doesn't follow Hindi word patterns
- ❌ "प्रकार जाँच" changes the meaning to "type check" (not the same)
- ❌ "किस्म है" uses "kind/sort" instead of technical term "instance"

**Confidence:** Medium

**Why medium?** Need native speaker to confirm whether "उदाहरण है" or "किस्म है" sounds better in actual code. Both are technically correct.

---

## Your Translation Task

**Translate:** `{TERM}` (Python {keyword|builtin})
**To:** {TARGET_LANGUAGE}

**Context about this term:**
{TIER_1_CONTEXT_SUMMARY}

**Related terms already translated:**
{EXISTING_TRANSLATIONS}

**Linguistic guidance:**

- **Recommended form:** {recommended_form} (for {language_family} languages)
- **Pattern:** This is a {ACTION|STATE|VALUE} term
- **Consistency:** Should match the form of {related_terms}

---

## Your Answer Format

Please provide your translation in this format:

```
TRANSLATION: {your_translation}
FORM: {infinitive|noun|adjective|masdar|etc}
CONFIDENCE: {high|medium|low}

OPTIONS CONSIDERED:
1. {option_1} - {why you thought about this}
2. {option_2} - {why you thought about this}
3. {option_3} - {why you thought about this}

WHY THIS IS BEST:
{2-3 sentences explaining your choice}
- Does it capture the Python concept? Yes/No - {explain}
- Is it used in CS education? Yes/No - {explain}
- Does it match the pattern of similar terms? Yes/No - {explain}
- Is it short and easy to type? Yes/No - {explain}

ALTERNATIVES:
- Second best: {alternative} - {why not chosen}
- Third best: {alternative} - {why not chosen}

NOTES FOR REVIEWERS:
{If confidence is not high, what should human reviewers check? Any regional differences?}
```

---

## Important Reminders

**For ALL languages:**

- Translate the CONCEPT, not just the English word
- Keep it short (1-2 words for keywords, max 3 for builtins)
- Match the form of similar terms (if `def` is a verb, `return` should also be a verb)
- Think about students - can they learn and remember this?

**For Arabic/Hebrew (RTL languages):**

- NO diacritics in keywords
- Maximum 10 characters
- Test that it works in code editors (RTL + LTR mixed)

**For Chinese:**

- Prefer single characters for simple concepts
- Use terms from CS education (check Chinese Python tutorials)
- Simplified Chinese characters only

**For Hindi:**

- Use infinitive verb forms (करना ending) for action keywords
- Avoid overly formal Sanskrit terms if simpler Hindi words exist
- Use Devanagari script, not romanization

**For Spanish/Romance languages:**

- Use infinitive verbs for action keywords (definir, retornar, romper)
- Technical/formal register (CS education vocabulary)
- Check that it's used across different regions (Spain, Latin America)

**For gendered languages:**

- Constants (True, False, None) use masculine form
- Nouns follow the natural gender of the word

---

**Now translate `{TERM}` to {TARGET_LANGUAGE}**
