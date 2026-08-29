# Round-trip verification — the owning implementation

**Status**: design v2, amended 2026-08-17 after adversarial review · **Ticket**: CORE-1813

Native → canonical → native returning byte-identical source is the claim this
project rests on. This document specifies the one implementation that owns
that check, the surfaces it is exposed through, and what it is allowed to
promise.

## The problem

The guarantee had no owner. It was re-derived in every place that needed it:

| Site | Layer | How it checked |
| --- | --- | --- |
| `libs/core/tests/unit/test_round_trip.py` | `TokenTranslator` + fixture maps | `assert original == back` |
| `libs/core/tests/unit/test_git_filter.py` | `GitFilter.clean` / `.smudge` | `assert original == back` |
| `libs/mcp/tests/test_roundtrip_sweep.py` | MCP client session | `assert` + a local `first_divergence` |
| `integrations-repo` `verify.py` | `legesher` CLI subprocess | `difflib` + prefix-based bucketing |
| `libs/mcp/skills/legesher-localized-code/SKILL.md` | **the agent** | *"Byte-identical output is the guarantee holding"* |

The last row is the defect. Exact string comparison over a long file is the
single judgement a model should never be handed, so in agent sessions the
guarantee was model-judged — which is to say, not a guarantee.

This is the [one contract, one implementation](../../../CLAUDE.md) guideline
applied before the divergence rather than after.

## What the adversarial review added (v2)

Three findings from the 2026-08-17 review change the design, and each is a
variant of one failure: **the check reporting VERIFIED it had not earned.**

1. **A round trip is necessary, not sufficient.** With the shipped `es` pack,
   `y = 1` (identifier `y`) forward-translates to `and = 1` — invalid Python —
   and the reverse hop cancels the collision, returning the source
   byte-identical. A verdict built on comparison alone says VERIFIED over a
   canonical form the interpreter rejects. The report therefore carries
   `forward_valid`, fed by the same compile-only validation the engine
   already owns, and the verdict cannot read VERIFIED while the canonical
   side does not compile.
2. **`verified` must be earned, not asserted.** A constant
   `verified=PACK_LAYERS` claims keyword coverage for `x = 1`, which contains
   no pack term, and for an identity trip that translated nothing. The set
   is computed from the layers actually exercised by the source.
3. **The verdict line must be safe to quote.** Embedding source lines in a
   string agents are told to reproduce verbatim is a working prompt-injection
   vector (demonstrated: a crafted string literal that always diverges and
   lands in `divergences[0]`) and moves source content into logs. The line
   carries locations, layers and counts — never content.

## Design

One module, `libs/core/legesher_core/round_trip.py`, in three layers. Lower
layers are usable without the ones above, which is what lets callers at four
different layers share one implementation.

Enums are `class X(str, Enum)`, not `StrEnum` — the packages declare
`requires-python = ">=3.10"` and `StrEnum` is 3.11+. Because the module is
re-exported from `legesher_core/__init__.py`, getting this wrong is an
import-time failure for the whole package on 3.10.

### Layer 1 — the comparator (pure)

```python
@dataclass(frozen=True)
class Divergence:
    line: int                 # 1-based
    offset: int | None        # 1-based column of the first differing character
    expected: str             # the differing line (terminator-stripped), or the terminator run
    actual: str
    kind: DivergenceKind      # content | line_count | trailing_whitespace
    layer: Layer | None       # filled by layer 2; None from the bare comparator

def first_divergence(expected: str, actual: str) -> Divergence | None
def all_divergences(expected: str, actual: str, *, limit: int = 50) -> list[Divergence]
```

**Comparison walks `splitlines(keepends=True)`.** `str.splitlines()` without
`keepends` discards terminators and splits on eight boundaries beyond `\n`
(`\v \f \x1c \x1d \x1e \x85`); a comparator built on it
reported CRLF-vs-LF input as a clean round trip. Terminator differences are
first-class `TRAILING_WHITESPACE` divergences on the line where they occur.

Two invariants, both tested:

- **Non-vacuity**: `all_divergences` returns a non-empty list whenever the
  two strings differ, for any two strings. `first_divergence` and
  `all_divergences` share one walk so they cannot disagree.
- **Self-consistency**: every returned `Divergence` has
  `expected != actual`. A located divergence showing two identical values is
  a report that denies itself.

**Raw `==` is correct here, and only here.** `CLAUDE.md` warns that reaching
for `==` over user-visible text is the bug and `compare_key` (NFKC + casefold)
is the baseline. That governs *identifier* comparison. Round-trip fidelity is
the inverse: byte-identical means byte-identical, and normalizing would let a
genuine defect — a pack flipping NFC to NFD — pass as a clean round trip. The
rule and its exception are both recorded at the comparison site so nobody
"fixes" this later.

`all_divergences` stops materializing at `limit`; callers that need the true
total use the orchestrator, which counts past the bound without building
objects. `Divergence.__str__` renders the two-line
`line N: / expected: / actual:` shape the MCP sweep's assertions used, so
failure messages stay legible.

### Layer 2 — the classifier

```python
class Layer(str, Enum):
    KEYWORDS = "keywords"              # from YAML_SECTION_CATEGORIES
    BUILTINS = "builtins"
    EXCEPTIONS = "exceptions"
    IMPLICIT_PARAMS = "implicit_params"
    IDENTIFIERS = "identifiers"
    COMMENTS = "comments"
    STRINGS = "strings"
    COLLISION = "collision"            # identifier spelled like a pack term

def classify_divergence(divergence, expected_source, actual_source, pack, *, native_side) -> Layer | None
def classified(divergences, expected_source, actual_source, pack, *, native_side) -> list[Divergence]
```

Classification is by **token class**, resolved from `tokenize` plus pack
membership — not by string prefix. The first four members come from
`legesher_i18n.term_definitions.YAML_SECTION_CATEGORIES`, imported rather
than restated.

Correctness requirements the review established, each pinned by a test:

- **Tokens are indexed by every line they span**, not their start line. A
  divergence inside a triple-quoted docstring must find the `STRING` token
  that covers it; indexing by `token.start[0]` alone made every docstring
  divergence unclassifiable.
- **The f-string token family classifies as `STRINGS`.** On Python 3.12+
  f-strings tokenize as `FSTRING_START/MIDDLE/END`, none of which is
  `STRING`; a lookup keyed on `STRING` alone walks past the literal and
  misattributes its content to the preceding name. The 3.14 `TSTRING_*`
  family is handled the same way, `getattr`-guarded for older interpreters.
- **Exception lookups go through `merge_exception_translations`.** Packs
  store exception keys lowercase (`valueerror`); Python spells them
  `ValueError`. The engine already remaps at translator-build time; the
  classifier reuses that helper rather than re-deriving a lookup that is
  right on the native side and wrong on the canonical side.
- **The catch list matches the repo's own.** Tokenization failures are
  results, not exceptions:
  `(tokenize.TokenError, IndentationError, SyntaxError, ValueError, RecursionError, MemoryError)`
  — the same posture as the engine's `scan_constructs` and `compile_check`,
  including the lone-surrogate `UnicodeEncodeError` (a `ValueError`
  subclass).
- **Direction decides collisions.** The pack maps canonical keys to native
  renderings. A term that matches the side the source is written in is a
  genuine pack-layer term; a term that matches only the *other* side is an
  identifier that happens to be spelled like one — CORE-1840's `e`/`and`,
  CORE-704's `todo`/`all` — and classifies as `COLLISION`. Membership-only
  lookup misattributed those to `keywords`/`builtins`, which routed every
  downstream consumer to the wrong action: the skill filed pack bugs against
  correct packs, the demo verifier hard-failed on them, and the eval matrix
  bucketed them as hand-translated keywords.
- **Tokenization runs once per batch.** `classified()` builds both token
  indexes once and classifies every divergence against them. Re-tokenizing
  both whole sources per divergence measured quadratic — ~24 CPU-hours for a
  maximally divergent input at `SOURCE_MAX_CHARS`.

Why the classes matter — each maps to a different action:

| Layer | What a divergence there means | What it changes |
| --- | --- | --- |
| keywords / builtins / exceptions / implicit_params | the deterministic layer failed: pack or engine defect | the pack, or the engine |
| collision | an identifier is spelled like a pack rendering | known class (CORE-1840); not a pack bug |
| identifiers | expected today — canonical form retains native identifiers (CORE-1841) | nothing; disclosed, not failed |
| comments / strings | the writer's fuzzy layer drifted | the writer's own output |

### Layer 3 — the orchestrator

```python
def verify_round_trip(
    source: str,
    source_lang: str,
    through_lang: str,
    python_version: str,
    *,
    translate: TranslateFn,
    pack: LanguagePack,
    validate: Callable[[str], bool] | None = None,
    max_divergences: int = 20,
) -> RoundTripReport
```

Reads as: *round-trip `source` (written in `source_lang`) through
`through_lang` and back, then compare against `source`.* One function covers
both directions with no mode flag — `translate_to_source` passes
`through_lang="en"`, `translate_to_native` passes its target.

Translation is **injected**, never re-derived: `libs/mcp`'s engine already
owns the cached, pivot-aware translator, and this module composes it.
`validate` is likewise injected (the engine's `compile_check`); when absent,
`forward_valid` is `None` — unknown, not assumed.

`source_lang == through_lang` raises `ValueError`. The engine short-circuits
identical languages to identity, so both hops would be no-ops and the
comparison `source == source` — a VERIFIED earned by translating nothing.
Callers surface it as an error (`EngineError("vacuous_round_trip")` at the
MCP boundary), never as a verdict.

```python
SCHEMA_VERSION = "1.0.0"

@dataclass(frozen=True)
class RoundTripReport:
    round_trips: bool
    forward_valid: bool | None        # canonical form compiles; None = not checked
    divergences: tuple[Divergence, ...]   # bounded by max_divergences
    divergence_count: int             # true total, counted past the bound
    verified: frozenset[Layer]        # earned: exercised by this source AND clean
    source_lang: str
    through_lang: str
    pivoted: bool
    grammar_version: str
    forward: str                      # in-process callers only — never serialized
    returned: str
    schema_version: str = SCHEMA_VERSION
```

`divergences` is a tuple: the dataclass is frozen and hashable, and a
`list` field silently broke both properties.

**`verified` is earned.** A pack layer enters the set only when the source
actually exercises it — at least one of that section's terms appears in the
source's tokens — and no divergence classified there. `x = 1` verifies
nothing; a file with keywords but no exceptions verifies `keywords` and not
`exceptions`. When CORE-1841 lands, `IDENTIFIERS` becomes *earnable* — an
addition, not a breaking change, which is why this is a set and not a
literal.

**Facts, never policy.** No raise on a failed trip, no bare bool. The MCP
sweep fails on residue, the demo verifier warns on it, and both read this
same report. A translation hop that itself errors is likewise a verdict
(`round_trips=False`, the hop-failure verdict line, and every fact the
completed hops established — the forward rendering, its pivot, its compile
check), not an exception — a pack whose
native rendering will not tokenize is the highest-value defect this
instrument can find, and it must arrive as a report.

`to_dict()` is the JSONL projection: it omits `forward`/`returned`, and its
key set is pinned by a test so any shape change fails until
`SCHEMA_VERSION` is bumped. A version nothing pins is a version that
versions nothing.

### `verdict_line` — the anti-fabrication surface

```text
legesher: round-trip VERIFIED — es→en→es · exercised: builtins, keywords ·
not covered: comments, identifiers, strings (CORE-1841) · grammar 3.13
```

```text
legesher: round-trip FAILED — es→en→es · line 12 col 8 · layer keywords ·
1 of 3 divergences shown · grammar 3.13
```

```text
legesher: round-trip FAILED — es→en→es · canonical form does not compile ·
grammar 3.13
```

One line, quoted rather than paraphrased. This is CORE-1843's recorded
mitigation — *return facts in a form that is rendered rather than restated* —
applied to the one claim most likely to be narrated away: a model that
receives `round_trips: false` and writes "verified byte-identical" has
reintroduced exactly the judgement this module removed.

The line carries **verdict, direction, location, layer, counts, coverage,
pivot and grammar — never source content**. `expected`/`actual` text lives
only in the structured `divergences` array, which no instruction tells a
model to echo. Two reasons, both demonstrated in review: a source line is
attacker-influenced input, and instructing agents to reproduce one verbatim
is a working injection vector (CORE-1423's tool-poisoning class); and a
quoted line persists into chat logs and eval JSONL, converting an ephemeral
echo of the caller's code into at-rest storage.

A pivoted trip appends `· via pivot` — four hops are weaker evidence than
two, and the line states its own limits or it states nothing.

## MCP exposure

`verify_round_trip: bool = False` on **both** `translate_to_source` and
`translate_to_native`.

A round-trip check is a property *of a translation*, not a separate task, and
the tool surface is deliberately coarse — each definition costs 200–800
context tokens in every session and clients degrade past ~40 tools. A flag
costs zero surface budget; a seventh tool costs it permanently.

The flag goes on both tools because the semantic is identical in each
direction — *confirm that translating back reproduces my input*. Honesty
note from review: the round trip alone does not catch symmetric collisions in
either direction (they cancel); `forward_valid` is what carries that case.
The two-direction exposure stands on symmetry and on asymmetric failures,
not on the collision class.

**The MCP boundary bounds everything it ships.**

- `RoundTripInfo` carries the verdict, `verdict_line`, `forward_valid`,
  bounded classified divergences, `verified`, `grammar_version`, `pivoted`,
  `schema_version` — not `forward` or `returned`.
- `DivergenceModel.expected`/`.actual` are truncated to 200 characters with
  a `truncated` flag. A "line" has no bound below `SOURCE_MAX_CHARS`
  (2 MB legally fits on one line); unbounded lines put multiple copies of
  the file on the wire through the field that exists to avoid exactly that.
- The `round_trip` field is **absent** from the serialized response when the
  flag was not set — absent, not `null`; a null field is still tokens in
  every response.
- Boundary tests assert on **content**, not key names: a distinctive marker
  string present in the source must not appear anywhere in the serialized
  `round_trip` block. (`assert "forward" not in result` cannot fail against
  a model that has no such field — it certifies nothing.)

The flagged path reuses the report's `forward` as its own
`translated_source`, so the flag never causes a second translation of the
same hop, and a parity test pins that the flag changes nothing about the
translation itself.

## Consumers

| Consumer | Uses | Change |
| --- | --- | --- |
| `test_round_trip.py` | comparator | round-trip equality asserts → `first_divergence(...) is None`. The two CRLF-normalization tests are **excluded** — they assert intentional normalization, not identity, and are the repo's only pin on that behavior. |
| `test_git_filter.py` | comparator | same, at clean/smudge level |
| `test_roundtrip_sweep.py` | comparator | delete the local `first_divergence`, import it; keep `assert_round_trips` and the xfail table |
| `verify.py` | orchestrator + comparator | round-trip check **added** as its own property; the existing authored-canonical comparison **stays** (see below) |
| `libs/mcp/evals/` | orchestrator | a round-trip task scored on hit / fidelity / contradiction against `verdict_line` (gated on PR #114) |

**The demo verifier measures two properties, not one.** Its existing check
compares the back-translation against the *authored English file* — canonical
equivalence, the number CORE-1841's "residue goes to zero" is read against.
The round trip (`fr → en → fr` idempotence) is a different property: because
identifiers pass through unchanged in both directions, it is byte-identical
whenever the pack mapping is injective, and *replacing* the first check with
it would have reported permanent success while measuring nothing. The
verifier keeps 3a (canonical equivalence, classified) and adds 3b (round
trip).

`integrations-repo` gains a `pyproject.toml` declaring `legesher-core`
with a `[tool.uv.sources]` path pin to the sibling checkout. Nothing is on
PyPI yet; when the packages publish (CORE-626) the source block is deleted
and nothing else changes.

## Agent-facing changes

`SKILL.md` step 3 and `AGENTS-template.md` rule 8 route the check through the
call. The instruction is to **render the structured result and quote the
verdict line rather than restating the verdict in the agent's own words** —
not to reproduce arbitrary returned text; the line is quotable *because* it
is content-free.

The failure path becomes a playbook keyed on `layer`: pack layer → report a
pack/engine defect; `collision` → known class, not a pack bug; `identifiers`
→ expected residue, continue; `comments`/`strings` → fix your own output and
re-verify.

Tool docstrings are the largest prompt surface this server has and the least
tested — the three `@mcp.prompt` templates have tests, the six tool
docstrings have none. The new flag's description gets a test, alongside a
tripwire pinning the tool count.

## Out of scope (tickets filed 2026-08-17)

- **X→Y classification against both packs.** A through-pack defect in an
  `es→fr→es` trip surfaces on the `es` side as a plain name and classifies
  as `identifiers`. Needs a two-pack `classify` signature.
- **Newline-normalization policy.** The comparator now reports CRLF
  normalization truthfully; whether a normalizing trip should *fail* is a
  policy question with blast radius across the sweep, the git filter and the
  demo. The comparator tells the truth; the policy ticket decides what to do
  with it.
- **`translate_via_packs` promotion.** The demo adapter is a third place
  that knows how to build a directional translator; consolidating touches
  the engine's threaded cache.
- **Round-trip aggregation for `map_existing_codebase`.** The batch tool is
  where an unverified claim covers the most files; needs a per-file verdict
  shape `RoundTripInfo` does not have.
- **The evaluation matrix itself** (CORE-1336, blocked by this ticket) and
  **`validate_source`** (CORE-1933).

## Correction riding along

`CLAUDE.md` §"Package Interdependencies" states that `legesher-core` has "no
internal dependencies" and that `legesher-i18n` depends on it. The actual
direction is the reverse: `libs/core/pyproject.toml` declares
`legesher-i18n>=0.22.0` and ten core modules import it. This is load-bearing
here — it is why a pack-loading function can live in core at all — so it is
corrected rather than left.

## Verification

CI gives no verdict, so local gates are the merge evidence:

- `libs/core` unit tests, including the rewritten round-trip and git-filter
  suites and the adversarial negative suite (every silent-success path found
  in review, asserted in the failing direction)
- `libs/mcp` per-commit sweep, plus `pytest -m scheduled` (all packs ×
  corpus) before merge — noting the scheduled sweep exercises the
  *comparator* against real packs; the classifier's native-side evidence is
  its own test class, fed RTL and non-Latin sources
- a Python 3.10 import check (`import legesher_core`) — the local
  interpreter and the budget-capped CI both run newer versions, so nothing
  else guards the declared floor
- the demo verifier run end to end against the education lesson
- a fresh adversarial review pass over the implementation, not a self-check
