# Translation Comparison Report: ES

**Generated**: 11 terms analyzed

---

## Summary Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Terms** | 11 | 100% |
| Perfect Agreement | 4 | 36.4% |
| High Agreement (75%+) | 5 | 45.5% |
| Medium Agreement (50-75%) | 0 | 0.0% |
| Low Agreement (<50%) | 2 | 18.2% |
| **Needs Review** | 3 | 27.3% |

**Average Agreement Score**: 0.758

---

## Source Coverage

| Source | Terms Covered |
|--------|---------------|
| community | 11 |
| claude | 11 |
| gpt4o | 11 |
| aya23 | 10 |

---

## Conflict Analysis

| Conflict Type | Count |
|---------------|-------|
| Word Type Conflicts | 4 |
| Form Conflicts | 1 |
| Length Conflicts | 4 |
| Semantic Conflicts | 2 |
| **Total with Conflicts** | 7 |

---

## Top Disagreements

### 1. **return** (Agreement: 25.0%)

**Unique Translations**: 4

| Source | Translation | Word Type | Form | Confidence |
|--------|-------------|-----------|------|------------|
| community | retornar | verb | infinitive | 1.00 |
| claude | devolver | verb | infinitive | 0.92 |
| gpt4o | regresar | verb | infinitive | 0.88 |
| aya23 | volver | verb | infinitive | 0.85 |

**Analysis**:
- Word types differ: No
- Forms differ: No
- Significant length variation: No
- Completely different words: Yes

**Recommendation**: No agreement - all 4 sources differ. Requires human review and semantic analysis.

**Translation Rationales**:
- **claude**: 'devolver' is more natural in Spanish

---

### 2. **yield** (Agreement: 33.3%)

**Unique Translations**: 3

| Source | Translation | Word Type | Form | Confidence |
|--------|-------------|-----------|------|------------|
| community | producir | verb | infinitive | 0.90 |
| claude | ceder | verb | infinitive | 0.87 |
| gpt4o | generar | verb | infinitive | 0.85 |

**Analysis**:
- Word types differ: No
- Forms differ: No
- Significant length variation: No
- Completely different words: Yes

**Recommendation**: No agreement - all 3 sources differ. Requires human review and semantic analysis.


---

### 3. **def** (Agreement: 75.0%)

**Unique Translations**: 2

| Source | Translation | Word Type | Form | Confidence |
|--------|-------------|-----------|------|------------|
| community | definir | verb | infinitive | 1.00 |
| claude | definir | verb | infinitive | 0.95 |
| gpt4o | función | noun | N/A | 0.85 |
| aya23 | definir | verb | infinitive | 0.90 |

**Analysis**:
- Word types differ: Yes
- Forms differ: No
- Significant length variation: No
- Completely different words: No

**Recommendation**: High agreement - use 'definir' (agreed by community, claude, aya23)

**Translation Rationales**:
- **claude**: Infinitive verb form is standard for Python keywords
- **gpt4o**: Chose noun form instead of verb

---

### 4. **lambda** (Agreement: 75.0%)

**Unique Translations**: 2

| Source | Translation | Word Type | Form | Confidence |
|--------|-------------|-----------|------|------------|
| community | lambda | N/A | N/A | 0.80 |
| claude | función anónima | noun phrase | N/A | 0.75 |
| gpt4o | lambda | N/A | N/A | 0.85 |
| aya23 | lambda | N/A | N/A | 0.90 |

**Analysis**:
- Word types differ: No
- Forms differ: No
- Significant length variation: Yes
- Completely different words: No

**Recommendation**: High agreement - use 'lambda' (agreed by community, gpt4o, aya23)

**Translation Rationales**:
- **community**: Commonly kept as 'lambda' in Spanish
- **claude**: Descriptive translation

---

### 5. **class** (Agreement: 75.0%)

**Unique Translations**: 2

| Source | Translation | Word Type | Form | Confidence |
|--------|-------------|-----------|------|------------|
| community | clase | noun | singular | 1.00 |
| claude | clase | noun | singular | 0.98 |
| gpt4o | clasificar | verb | infinitive | 0.70 |
| aya23 | clase | noun | singular | 0.95 |

**Analysis**:
- Word types differ: Yes
- Forms differ: Yes
- Significant length variation: Yes
- Completely different words: No

**Recommendation**: High agreement - use 'clase' (agreed by community, claude, aya23)

**Translation Rationales**:
- **gpt4o**: Misunderstood as verb instead of noun

---

### 6. **is** (Agreement: 75.0%)

**Unique Translations**: 2

| Source | Translation | Word Type | Form | Confidence |
|--------|-------------|-----------|------|------------|
| community | es | verb | present | 1.00 |
| claude | es | verb | present | 0.99 |
| gpt4o | esexactamente | verb phrase | N/A | 0.60 |
| aya23 | es | verb | present | 0.97 |

**Analysis**:
- Word types differ: Yes
- Forms differ: No
- Significant length variation: Yes
- Completely different words: No

**Recommendation**: High agreement - use 'es' (agreed by community, claude, aya23)

**Translation Rationales**:
- **gpt4o**: Overly verbose translation

---

### 7. **else** (Agreement: 75.0%)

**Unique Translations**: 2

| Source | Translation | Word Type | Form | Confidence |
|--------|-------------|-----------|------|------------|
| community | sino | conjunction | N/A | 1.00 |
| claude | sino | conjunction | N/A | 0.95 |
| gpt4o | de lo contrario | phrase | N/A | 0.75 |
| aya23 | sino | conjunction | N/A | 0.92 |

**Analysis**:
- Word types differ: Yes
- Forms differ: No
- Significant length variation: Yes
- Completely different words: No

**Recommendation**: High agreement - use 'sino' (agreed by community, claude, aya23)


---

### 8. **print** (Agreement: 100.0%)

**Unique Translations**: 1

| Source | Translation | Word Type | Form | Confidence |
|--------|-------------|-----------|------|------------|
| community | imprimir | verb | infinitive | 1.00 |
| claude | imprimir | verb | infinitive | 0.98 |
| gpt4o | imprimir | verb | infinitive | 0.97 |
| aya23 | imprimir | verb | infinitive | 0.95 |

**Analysis**:
- Word types differ: No
- Forms differ: No
- Significant length variation: No
- Completely different words: No

**Recommendation**: Perfect agreement across all sources - use 'imprimir' with confidence


---

### 9. **if** (Agreement: 100.0%)

**Unique Translations**: 1

| Source | Translation | Word Type | Form | Confidence |
|--------|-------------|-----------|------|------------|
| community | si | conjunction | N/A | 1.00 |
| claude | si | conjunction | N/A | 0.99 |
| gpt4o | si | conjunction | N/A | 0.98 |
| aya23 | si | conjunction | N/A | 0.97 |

**Analysis**:
- Word types differ: No
- Forms differ: No
- Significant length variation: No
- Completely different words: No

**Recommendation**: Perfect agreement across all sources - use 'si' with confidence


---

### 10. **for** (Agreement: 100.0%)

**Unique Translations**: 1

| Source | Translation | Word Type | Form | Confidence |
|--------|-------------|-----------|------|------------|
| community | para | preposition | N/A | 1.00 |
| claude | para | preposition | N/A | 0.98 |
| gpt4o | para | preposition | N/A | 0.96 |
| aya23 | para | preposition | N/A | 0.94 |

**Analysis**:
- Word types differ: No
- Forms differ: No
- Significant length variation: No
- Completely different words: No

**Recommendation**: Perfect agreement across all sources - use 'para' with confidence


---


## Terms Needing Human Review

**Total**: 3 terms require human review

- **return**: 4 different translations (25.0% agreement)
- **yield**: 3 different translations (33.3% agreement)
- **class**: 2 different translations (75.0% agreement)

---

## Recommendations

**Good translation consistency** overall. Focus review efforts on the 3 terms with lower agreement.

### Priority Actions

1. **Word Type Alignment**: Review 4 terms with word type conflicts to establish grammatical standards.
2. **Form Standardization**: Resolve 1 terms with form conflicts (e.g., infinitive vs. conjugated).
3. **Semantic Review**: Analyze 2 terms with completely different translations for semantic equivalence.
4. **Manual Review Queue**: 3 terms flagged for human expert review.

---

*Report generated by Legesher Translation Comparison System*