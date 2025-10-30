# Arabic Translation Review - Conciseness Improvements

**Status:** Recommendations for CORE-354 follow-up
**Priority:** Medium
**Reviewer:** Claude Code

## Overview

The current Arabic translations (migrated from legesher-translations) are
functional but some are overly verbose. This document proposes more concise
alternatives that maintain meaning while improving code readability.

## Recommended Changes

### High Priority (Very Verbose)

| Keyword | Current Translation | Length | Suggested | Length | Reasoning |
|---------|-------------------|--------|-----------|--------|-----------|
| `None` | متغير لا يحمل أي قيمة | 20 chars | فارغ | 4 chars | "Empty" is concise and semantically accurate |
| `as` | كلمة مفتاحية بمعنى كاف التشبية تستخدم لاعطاء اسم بديل للموديل عند تضمينها | 79 chars | كـ | 2 chars | Simple preposition equivalent |
| `assert` | تصريح تأكيد صحة قيمة | 19 chars | تأكيد | 5 chars | "Assert/Confirm" captures the essence |
| `async` | تشغيل كتلتين أو أكثر بشكل متوازي بدلا من متسلسل | 48 chars | غير_متزامن | 9 chars | "Asynchronous" is standard |
| `break` | خروج من الحلقة | 13 chars | كسر | 3 chars | "Break" is widely used |
| `elif` | في حال ‫(‬الشرط‫)‬ | 17 chars | وإن | 3 chars | "And if" - concise conditional |
| `else` | في حال أي شيء آخر | 17 chars | وإلا | 4 chars | "Otherwise" - standard usage |

### Medium Priority (Moderately Verbose)

| Keyword | Current | Suggested | Notes |
|---------|---------|-----------|-------|
| `continue` | استمرار | متابعة | Shorter, means "continue/proceed" |
| `return` | إرجاع قيمة | إرجاع | "Return" without "value" |
| `yield` | توليد | إنتاج | "Produce/yield" - shorter |

### Low Priority (Acceptable but could improve)

| Keyword | Current | Suggested | Notes |
|---------|---------|-----------|-------|
| `class` | ظبقة | صنف | "Class" - more modern term |
| `import` | تضمين | استيراد | "Import" - more precise |

## Implementation Notes

### Translation Philosophy

**Before (Descriptive):**

```python
# 79 characters for 'as'
كلمة مفتاحية بمعنى كاف التشبية تستخدم لاعطاء اسم بديل للموديل عند تضمينها
```

**After (Concise):**

```python
# 2 characters for 'as'
كـ
```

### Benefits

1. **Readability:** Shorter keywords make code easier to scan
2. **Consistency:** Aligns with other language packs (Spanish uses short forms)
3. **Ergonomics:** Less typing for developers
4. **Standard Practice:** Most programming languages use short keywords

### Comparison with Spanish

Spanish translations are concise and practical:

- `None` → `Ninguno` (7 chars) vs Arabic `متغير لا يحمل أي قيمة` (20 chars)
- `as` → `como` (4 chars) vs Arabic 79 chars
- `break` → `romper` (6 chars) vs Arabic `خروج من الحلقة` (13 chars)

## Testing Impact

These changes would improve:

- **Round-trip translation tests:** Less token manipulation
- **Performance:** Smaller translation maps
- **Developer experience:** More natural coding flow

## Recommended Action Plan

1. **Create GitHub issue** for Arabic translation refinement
2. **Consult Arabic-speaking developers** for validation
3. **Update language pack** with community approval
4. **Re-run validation tests** (CORE-435)
5. **Update documentation** with rationale

## Cultural Considerations

- Short forms should still be clear to Arabic speakers
- Consider regional variations (Egyptian vs. Gulf vs. Levantine)
- Maintain formal Modern Standard Arabic (MSA) where appropriate
- Some developers may prefer longer, more explicit translations

## References

- Current pack: `libs/i18n/language-packs/ar/keywords.yml`
- Spanish pack (for comparison): `libs/i18n/language-packs/es/keywords.yml`
- CORE-354: Translation Migration Strategy
- CORE-435: Validation Results

---

**Next Steps:**

1. Share with Arabic-speaking community for feedback
2. Create follow-up issue for implementation
3. Consider A/B testing with developer focus groups
