# JavaScript Context Documents

Per-term translation-context briefs for the JavaScript terms Legesher localizes,
mirroring `context/python/`. Each document guides an AI translation model (and a
human reviewer) toward an accurate, consistent native-language term.

## Overview

- **Total Documents**: 62
- **Template Version**: Tier 1 (Concise Translation Brief) — see `../../docs/context-template-tier1.md`
- **Target**: the **JEJ** ("Just Enough JavaScript") teaching subset
- **Source of truth**: the surface is **Legesher-owned** (CORE-1581), exported by `@legesher/jej` with every post-transcription addition citing its `reference.md` section — last verified against the upstream courseware repository at `c1deb12` (its enumerated `lib/completing` constants did not survive its greenfield rewrite). Counts: **17 keywords, 16 builtins, 29 members** (`of` and `log` joined via CORE-1571).

## Partitions (62 terms)

| Partition | Count | Binding | Rules |
|---|---|---|---|
| `keywords` | 17 | standalone | Rule 1 (one concept ↔ one term) **and** Rule 2 (reversible) |
| `builtins` | 16 | standalone | Rule 1 **and** Rule 2 |
| `members` | 29 | qualified | **Rule 2 only** — a member is bounded by its receiver; one native word may serve several receivers, and that is correct, not a collision |

### Keywords (17)
`let, const, if, else, for, while, do, break, continue, return, true, false, null, new, typeof, in, of`

### Builtins (16)
`console, alert, confirm, prompt, String, Number, Boolean, Math, RegExp, Date, BigInt, parseInt, parseFloat, undefined, NaN, Infinity`
(`allowedGlobals` minus `eval`, which is suppressed via `SUPPRESSED_GLOBALS`.)

### Members (29)
`length, toString, valueOf, charAt, charCodeAt, slice, substring, toUpperCase, toLowerCase, indexOf, includes, startsWith, endsWith, repeat, trim, concat, replace, replaceAll, toFixed, toPrecision, abs, floor, ceil, round, max, min, pow, sqrt, log`

## Key conventions

- **Members are AST-decided.** A member is a non-computed `MemberExpression.property` — `"hi".length` is the member; a bare variable named `length` is not. The AST guard, not the spelling, decides. (Members are **not** dot-adjacency.)
- **Receiver widening.** Several members (`length, toString, valueOf, slice, indexOf, includes, concat`) attach to more than one receiver in full JS but are String/Number-only in JEJ today. Their briefs instruct choosing a word that survives widening (e.g. `length` = count, not spatial length), so the term is still correct the day arrays are taught.
- **Native-review flags.** `toString` and `valueOf` carry a genuine cross-receiver semantic gap (e.g. `Number.toString(2)` radix vs `Date.toString()` date-text) and are pre-flagged for the native reviewer rather than resolved in the prompt.

## Held terms (NOT in this corpus)

- **The remaining `console.*` methods** (`table`, `assert`, `trace`, `count`, `time`/`timeEnd`/`timeLog`, `group`/`groupEnd`/`groupCollapsed`, `error`, `warn`, `info`, `debug`, `dir`, `clear`, `countReset`) — taught by `reference.md` and admitted by the upstream member blocklist, but held until the trial module's actual usage is confirmed (**CORE-1609** Q1). Until then, `console.<held>` renders with `console` translated and the member left canonical.
- *(Historical: `of` and `log` were held here pending an upstream widening that could never land; they joined the surface via **CORE-1571** once the key-set became Legesher-owned.)*

## Cross-target notes

Concepts shared with Python are keyed to the same concept, not re-translated: `length`/`len`
is one concept with different bindings per target; `console.log`/`print` is one concept split
across two JS partitions. The final cross-target keying model is pending the CORE-1529
granularity decision; these docs use the safe per-concept default (divergences flagged, nothing lost).

---

**Last Updated:** 2026-07-27
**Maintained by:** Legesher (CORE-1370; `of`/`log` widening CORE-1571)
