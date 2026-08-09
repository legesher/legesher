# Legesher style guides

A **style guide** is a set of rules (currently in English) plus a language/script
**profile** proposing best-practice Python for one target language — how identifiers are
formed, which naming conventions the script can express, and the constraints its
characters impose. The point is consistency and *reverse-engineerability*: to
move code between languages (say Arabic → Swahili) a tool can read both guides
and know what changes — whether casing exists, how words separate, how functions
are shaped.

Guides are **rules, not vocabulary**. Word choices (what `def` becomes),
booleans, symbol names, and idiomatic variable names live in the **language
packs**, not here. Key/value pairs are written in **English**, except where a
value must be in the target script (e.g. a native-digit sample).

## How the files fit together

```text
python.yml            base PEP 8 rules (all languages)
  └─ _ltr.yml / _rtl.yml    text-direction layer
       └─ _cjk.yml, _arabic.yml, _brahmic.yml, _cyrillic.yml,
          _ethiopic.yml, _sea-spaceless.yml   script-family overlays
            └─ {code}.yml   per-language guide  ← this schema
```

Each `{code}.yml` declares an `extends` chain; the loader resolves it in full —
base → direction → script-family → language (the transitive `extends` resolution
is implemented in the loader and lands with the loader/validation work,
CORE-1394). `python.yml` and the `_*.yml` overlays are building blocks and are
**not** validated against this schema — only per-language guides are.

## Field reference

| Field | Meaning | Allowed values | Consumer | Set at |
|---|---|---|---|---|
| `language` | ISO 639-1 code | `^[a-z]{2,3}$`, in languages.json | loader, validator | language |
| `extends` | ancestor chain to merge | list of `*.yml` filenames | loader | language |
| `status` | maturity | `experimental` \| `reviewed` \| `stable` | human | language |
| `supports.case_distinction` | script has upper/lower case | bool (== languages.json) | validator, transfer | derived |
| `supports.snake_case` | words joinable with `_` | bool (usually true) | transfer | derived |
| `supports.upper_snake_case` | constants as `ALL_CAPS` | bool (requires case) | transfer, validator | derived |
| `supports.pascal_case` | `CapWords` classes | bool (requires case) | transfer, validator | derived |
| `supports.camel_case` | `camelCase` | bool (requires case) | transfer, validator | derived |
| `supports.native_digits` | language has its own numerals | bool | transfer, Legesher | profile |
| `supports.combining_marks` | chars compose from base + marks | bool | validator (grapheme length) | profile |
| `supports.requires_word_separator` | `_` mandatory (spaceless scripts) | bool | transfer | profile |
| `supports.diacritics_in_identifiers` | diacritics / tone marks are part of identifier spelling (e.g. Yoruba, Vietnamese) | bool | transfer, validator | profile |
| `supports.cursive_joining` | letters connect contextually (Arabic-script) | bool | transfer | profile |
| `naming.case_substitute` | what replaces case | `morphology` \| `not_needed` | prompt‡, transfer | family/lang |
| `naming.word_formation` | how terms are coined (compounding, clipping, which roots stay distinct) — optional, usually added after a native review | list of strings | prompt‡, human | language |
| `script.name` | writing-system identity | string | prompt‡, human | language |
| `script.direction` | text direction | `ltr` \| `rtl` | prompt‡, editor, transfer | direction overlay |
| `script.constraints` | script-specific rules (incl. a digits line) | list of strings | prompt‡, human, transfer | family + lang |
| `formatting.comment_prefix` | comment marker | string (`#`) | prompt‡ | base |
| `formatting.programming_punctuation` | punctuation policy in code | `ascii_only` | prompt‡ | base |
| `rendering.noto_font` | editor rendering font | string | VS Code extension | language |

**derived** = computed from `languages.json.has_case_distinction` (single source
of truth), so you can't get it wrong when adding a language: the case-dependent
flags all equal `case_distinction`. **profile** = a script fact. **‡** = consumed
by the translation prompt *once the PromptBuilder ticket lands* (CORE-1395);
inert until then.

### The digits line

Legesher owns the logic for whether code uses native or ASCII digits. The guide
only **profiles** it: if a language natively writes digits in its own script,
note that (with a sample), e.g.

```yaml
- "Digits: Hindi natively uses Devanagari १२३; code uses ASCII 0-9 today
   (native-digit support is a planned Legesher feature, currently disabled)."
```

Set `supports.native_digits` accordingly. Do not put enable/convert logic here.

## Adding a language

1. Add the language to `languages.json` (the source of truth for `rtl` and
   `has_case_distinction`).
2. Copy `_template.yml` to `{code}.yml`. Set `extends` (pick the script-family
   overlay, or just the direction layer), `script.name`, any `script.constraints`
   quirks, and `rendering.noto_font`. Set the `supports` flags to match
   `languages.json` (the case-dependent ones equal `case_distinction`).
3. Run the validator:

   ```bash
   uv run python -m legesher_i18n.scripts.validate_style_guides
   ```

   Green means the guide is well-formed and consistent with `languages.json`.

Most of the rules are inherited from the family overlay, so a same-family
language is a handful of lines. A brand-new script means writing one overlay
first; its languages are then trivial.
