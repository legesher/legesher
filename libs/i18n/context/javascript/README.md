# JavaScript Context Documents

Per-term translation-context briefs for the JavaScript terms Legesher localizes,
mirroring `context/python/`. Each document guides an AI translation model (and a
human reviewer) toward an accurate, consistent native-language term.

## Overview

- **Total Documents**: 60
- **Template Version**: Tier 1 (Concise Translation Brief) — see `../../docs/context-template-tier1.md`
- **Target**: the **JEJ** ("Just Enough JavaScript") teaching subset
- **Source of truth**: `upstream-courseware` @ `0fca239` — `KEYWORDS` (16), `CURATED_MEMBERS` (28), and `allowedGlobals` (17 → 16 in the pack surface, `eval` suppressed). The `LanguagePack` doc comment there states the counts: *"16 keywords, 16 builtins, 28 members."*

## Partitions (60 terms)

| Partition | Count | Binding | Rules |
|---|---|---|---|
| `keywords` | 16 | standalone | Rule 1 (one concept ↔ one term) **and** Rule 2 (reversible) |
| `builtins` | 16 | standalone | Rule 1 **and** Rule 2 |
| `members` | 28 | qualified | **Rule 2 only** — a member is bounded by its receiver; one native word may serve several receivers, and that is correct, not a collision |

### Keywords (16)
`let, const, if, else, for, while, do, break, continue, return, true, false, null, new, typeof, in`

### Builtins (16)
`console, alert, confirm, prompt, String, Number, Boolean, Math, RegExp, Date, BigInt, parseInt, parseFloat, undefined, NaN, Infinity`
(`allowedGlobals` minus `eval`, which is suppressed via `SUPPRESSED_GLOBALS`.)

### Members (28)
`length, toString, valueOf, charAt, charCodeAt, slice, substring, toUpperCase, toLowerCase, indexOf, includes, startsWith, endsWith, repeat, trim, concat, replace, replaceAll, toFixed, toPrecision, abs, floor, ceil, round, max, min, pow, sqrt`

## Key conventions

- **Members are AST-decided.** A member is a non-computed `MemberExpression.property` — `"hi".length` is the member; a bare variable named `length` is not. The AST guard, not the spelling, decides. (Members are **not** dot-adjacency.)
- **Receiver widening.** Several members (`length, toString, valueOf, slice, indexOf, includes, concat`) attach to more than one receiver in full JS but are String/Number-only in JEJ today. Their briefs instruct choosing a word that survives widening (e.g. `length` = count, not spatial length), so the term is still correct the day arrays are taught.
- **Native-review flags.** `toString` and `valueOf` carry a genuine cross-receiver semantic gap (e.g. `Number.toString(2)` radix vs `Date.toString()` date-text) and are pre-flagged for the native reviewer rather than resolved in the prompt.

## Held terms (NOT in this corpus)

- **`log`** — appears as `console.log` but is not in `CURATED_MEMBERS`; the ask to add it is on **CORE-1529**. Until decided, `console.*` renders with `console` translated and the member left canonical.
- **`of`** — a real JEJ feature (`for…of`) that is not translatable yet; widening tracked on **CORE-1529**. Not shipped unilaterally (the client drift guard asserts set equality).

## Cross-target notes

Concepts shared with Python are keyed to the same concept, not re-translated: `length`/`len`
is one concept with different bindings per target; `console.log`/`print` is one concept split
across two JS partitions. The final cross-target keying model is pending the CORE-1529
granularity decision; these docs use the safe per-concept default (divergences flagged, nothing lost).

---

**Last Updated:** 2026-07-21
**Maintained by:** Legesher (CORE-1370)
