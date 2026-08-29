"""Round-trip verification - the owning implementation.

Native -> canonical -> native returning byte-identical source is the claim
this project rests on. This module owns that check so it is not re-derived
per caller. See ``libs/core/docs/round-trip-verification.md``.

**Raw ``==`` / byte comparison is correct here, and only here.** The repo's
general rule is that comparison over user-visible text goes through
``compare_key`` (NFKC + casefold, storage NFC). Round-trip fidelity is the
inverse question: byte-identical means byte-identical. Normalising would let
a pack that flipped NFC to NFD pass as a clean round trip - the exact defect
this check exists to catch.

The walk uses ``splitlines(keepends=True)``. Without ``keepends``,
``str.splitlines`` discards terminators and splits on eight boundaries
beyond ``\\n`` - a comparator built on it reported CRLF-vs-LF input as a
clean round trip. Terminators are compared as bytes like everything else.
"""

from __future__ import annotations

import io
import tokenize
from collections.abc import Callable, Iterator
from dataclasses import dataclass, replace
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol

from legesher_core.utils import merge_exception_translations

if TYPE_CHECKING:
    from legesher_i18n.pack_loader import LanguagePack

__all__ = [
    "Divergence",
    "DivergenceKind",
    "Layer",
    "PACK_LAYERS",
    "RoundTripReport",
    "SCHEMA_VERSION",
    "SCOPE_TICKET",
    "TranslateFn",
    "all_divergences",
    "classified",
    "classify_divergence",
    "first_divergence",
    "verify_round_trip",
]


class DivergenceKind(str, Enum):
    """How two renderings failed to match."""

    CONTENT = "content"
    LINE_COUNT = "line_count"
    TRAILING_WHITESPACE = "trailing_whitespace"


class Layer(str, Enum):
    """The token layer a divergence sits in.

    The first four are the pack's own section vocabulary
    (``legesher_i18n.term_definitions.YAML_SECTION_CATEGORIES``). The rest
    are outside the deterministic layer's responsibility: ``IDENTIFIERS``,
    ``COMMENTS`` and ``STRINGS`` are the writer's fuzzy layer, and
    ``COLLISION`` is an identifier spelled like a pack rendering
    (CORE-1840's ``e``/``and``) - a known class, not a pack defect, and the
    distinction routes readers to entirely different fixes.
    """

    KEYWORDS = "keywords"
    BUILTINS = "builtins"
    EXCEPTIONS = "exceptions"
    IMPLICIT_PARAMS = "implicit_params"
    IDENTIFIERS = "identifiers"
    COMMENTS = "comments"
    STRINGS = "strings"
    COLLISION = "collision"


@dataclass(frozen=True)
class Divergence:
    """One located difference between two renderings.

    ``line`` and ``offset`` are 1-based. For ``TRAILING_WHITESPACE`` the
    ``expected``/``actual`` fields hold the differing terminator runs;
    otherwise the terminator-stripped line text. The invariant
    ``expected != actual`` holds for every constructed instance.
    """

    line: int
    offset: int | None
    expected: str
    actual: str
    kind: DivergenceKind
    layer: Layer | None = None

    def __str__(self) -> str:
        return (
            f"line {self.line}:\n"
            f"  expected: {self.expected!r}\n"
            f"  actual:   {self.actual!r}"
        )


def _first_differing_column(expected: str, actual: str) -> int:
    """1-based index of the first character that differs."""
    for index, (left, right) in enumerate(zip(expected, actual), start=1):
        if left != right:
            return index
    return min(len(expected), len(actual)) + 1


def _strip_terminator(line: str) -> str:
    return line.rstrip("\r\n\v\f\x1c\x1d\x1e\x85\u2028\u2029")


def _line_divergence(number: int, before: str, after: str) -> Divergence | None:
    """One divergence for a keepends line pair, or None when identical."""
    if before == after:
        return None
    text_before = _strip_terminator(before)
    text_after = _strip_terminator(after)
    if text_before == text_after:
        # Same visible text; only the terminator run differs.
        return Divergence(
            line=number,
            offset=None,
            expected=before[len(text_before) :],
            actual=after[len(text_after) :],
            kind=DivergenceKind.TRAILING_WHITESPACE,
        )
    return Divergence(
        line=number,
        offset=_first_differing_column(text_before, text_after),
        expected=text_before,
        actual=text_after,
        kind=DivergenceKind.CONTENT,
    )


def _iter_divergences(expected: str, actual: str) -> Iterator[Divergence]:
    """Every differing line, in order. The single walk both public
    functions share, so they cannot disagree - two comparators drifting
    apart is the failure class this module exists to end.
    """
    expected_raw = expected.splitlines(keepends=True)
    actual_raw = actual.splitlines(keepends=True)

    for number, (before, after) in enumerate(zip(expected_raw, actual_raw), start=1):
        divergence = _line_divergence(number, before, after)
        if divergence is not None:
            yield divergence

    if len(expected_raw) != len(actual_raw):
        shorter = min(len(expected_raw), len(actual_raw))
        expected_text = (
            _strip_terminator(expected_raw[shorter])
            if shorter < len(expected_raw)
            else ""
        )
        actual_text = (
            _strip_terminator(actual_raw[shorter]) if shorter < len(actual_raw) else ""
        )
        if expected_text == actual_text:
            # The sides differ only in trailing terminator lines
            # (``"a\n\n\n"`` vs ``"a\n"``): both stripped texts are empty,
            # and a LINE_COUNT row would show two identical values. Report
            # the RAW terminator lines instead, which differ and say what
            # actually happened.
            yield Divergence(
                line=shorter + 1,
                offset=None,
                expected=(expected_raw[shorter] if shorter < len(expected_raw) else ""),
                actual=actual_raw[shorter] if shorter < len(actual_raw) else "",
                kind=DivergenceKind.TRAILING_WHITESPACE,
            )
        else:
            yield Divergence(
                line=shorter + 1,
                offset=None,
                expected=expected_text,
                actual=actual_text,
                kind=DivergenceKind.LINE_COUNT,
            )


def first_divergence(expected: str, actual: str) -> Divergence | None:
    """Locate where two renderings stop matching, or ``None`` if identical."""
    if expected == actual:
        return None
    return next(_iter_divergences(expected, actual), None)


def all_divergences(expected: str, actual: str, *, limit: int = 50) -> list[Divergence]:
    """Differing lines in order, bounded by ``limit``.

    Non-vacuity invariant: non-empty whenever ``expected != actual``.
    Callers needing the unbounded total count past the limit without
    materialising (see ``verify_round_trip``).
    """
    if expected == actual:
        return []
    found: list[Divergence] = []
    for divergence in _iter_divergences(expected, actual):
        found.append(divergence)
        if len(found) >= limit:
            break
    return found


def _string_token_layers() -> dict[int, Layer]:
    """String-ish token types, including the 3.12+ f-string family.

    getattr-guarded: FSTRING_* landed in 3.12, TSTRING_* in 3.14, and the
    packages declare a 3.10 floor.
    """
    layers = {tokenize.COMMENT: Layer.COMMENTS, tokenize.STRING: Layer.STRINGS}
    for name in (
        "FSTRING_START",
        "FSTRING_MIDDLE",
        "FSTRING_END",
        "TSTRING_START",
        "TSTRING_MIDDLE",
        "TSTRING_END",
    ):
        token_type = getattr(tokenize, name, None)
        if token_type is not None:
            layers[token_type] = Layer.STRINGS
    return layers


_LAYER_BY_TOKEN_TYPE = _string_token_layers()

#: Tokenization failures are results, not exceptions. Matches the engine's
#: own catch lists (scan_constructs, compile_check): ValueError covers the
#: lone-surrogate UnicodeEncodeError; RecursionError/MemoryError cover
#: pathological nesting on hostile input.
_TOKENIZE_FAILURES = (
    tokenize.TokenError,
    IndentationError,
    SyntaxError,
    ValueError,
    RecursionError,
    MemoryError,
)


def _tokens_by_line(source: str) -> dict[int, list[tokenize.TokenInfo]]:
    """Group tokens by every line they SPAN, not just where they start.

    A triple-quoted string covering lines 1-3 must be findable from line 2,
    or a docstring divergence has no token to classify. On tokenizer
    failure, whatever was read before the failure is kept - classification
    is advisory and every caller treats ``None`` as a legal answer.
    """
    grouped: dict[int, list[tokenize.TokenInfo]] = {}
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            for line in range(token.start[0], token.end[0] + 1):
                grouped.setdefault(line, []).append(token)
    except _TOKENIZE_FAILURES:
        pass
    return grouped


def _pack_sections(pack: LanguagePack) -> tuple[tuple[Layer, dict[str, str]], ...]:
    """Section lookups in the pack's own precedence order.

    Exceptions go through ``merge_exception_translations`` because packs
    store them lowercase (``valueerror``) while Python spells them
    ``ValueError`` - the same remap the engine does at translator-build
    time. Re-deriving the lookup without it was right on the native side
    and wrong on the canonical side.
    """
    return (
        (Layer.KEYWORDS, pack.keywords),
        (Layer.BUILTINS, pack.builtins),
        (Layer.EXCEPTIONS, merge_exception_translations({}, pack.exceptions)),
        (Layer.IMPLICIT_PARAMS, pack.implicit_params),
    )


#: The per-layer section lookups, built once per batch by the entry points
#: (``classified``, ``_layers_exercised``) - ``_pack_sections`` merges the
#: exception-case remap, and rebuilding that per token lookup was measured
#: as the dominant classification cost.
_PackSections = tuple[tuple[Layer, dict[str, str]], ...]


def _pack_layer(
    term: str, sections: _PackSections, *, native_side: bool
) -> Layer | None:
    """Which layer claims ``term``, honouring which side it SHOULD match.

    The pack maps canonical keys to native renderings. A term matching the
    side the source is written in is a genuine pack-layer term; a term
    matching only the OTHER side is an identifier spelled like one -
    CORE-1840's ``e``/``and`` - and that distinction routes readers to
    entirely different fixes, so it gets its own layer.
    """
    cross_match = False
    for layer, mapping in sections:
        own = mapping.values() if native_side else mapping.keys()
        other = mapping.keys() if native_side else mapping.values()
        if term in own:
            return layer
        if term in other:
            cross_match = True
    return Layer.COLLISION if cross_match else None


def _first_differing_index(
    expected: list[tokenize.TokenInfo], actual: list[tokenize.TokenInfo]
) -> int | None:
    for index, (before, after) in enumerate(zip(expected, actual)):
        if before.string != after.string:
            return index
    if len(expected) != len(actual):
        return min(len(expected), len(actual))
    return None


def _classify(
    divergence: Divergence,
    expected_lines: dict[int, list[tokenize.TokenInfo]],
    actual_lines: dict[int, list[tokenize.TokenInfo]],
    sections: _PackSections,
    *,
    native_side: bool,
) -> Layer | None:
    if divergence.offset is None:
        return None
    expected_line = expected_lines.get(divergence.line, [])
    actual_line = actual_lines.get(divergence.line, [])
    if not expected_line:
        return None
    index = _first_differing_index(expected_line, actual_line)
    if index is None:
        return None
    # Walk back from the first differing token to the nearest one that
    # names a layer: in ``except*`` -> ``except**`` the differing char is
    # an operator but the responsible term is the keyword before it.
    for token in reversed(expected_line[: index + 1]):
        named = _LAYER_BY_TOKEN_TYPE.get(token.type)
        if named is not None:
            return named
        if token.type == tokenize.NAME:
            return (
                _pack_layer(token.string, sections, native_side=native_side)
                or Layer.IDENTIFIERS
            )
    return None


def classify_divergence(
    divergence: Divergence,
    expected_source: str,
    actual_source: str,
    pack: LanguagePack,
    *,
    native_side: bool,
) -> Layer | None:
    """Name the token layer one divergence sits in, or ``None``.

    Thin wrapper over the batch path; classifying many divergences goes
    through ``classified``, which tokenizes each source once.
    """
    return _classify(
        divergence,
        _tokens_by_line(expected_source),
        _tokens_by_line(actual_source),
        _pack_sections(pack),
        native_side=native_side,
    )


def classified(
    divergences: list[Divergence],
    expected_source: str,
    actual_source: str,
    pack: LanguagePack,
    *,
    native_side: bool,
) -> list[Divergence]:
    """Copies with ``layer`` filled in. Tokenizes each source ONCE for the
    whole batch - per-divergence re-tokenization measured quadratic
    (~24 CPU-hours at SOURCE_MAX_CHARS with every line differing).
    """
    expected_lines = _tokens_by_line(expected_source)
    actual_lines = _tokens_by_line(actual_source)
    sections = _pack_sections(pack)
    return [
        replace(
            d,
            layer=_classify(
                d, expected_lines, actual_lines, sections, native_side=native_side
            ),
        )
        for d in divergences
    ]


SCHEMA_VERSION = "1.0.0"

#: The ticket that widens coverage; referenced in every verdict line, so a
#: constant rather than a string scattered through f-strings.
SCOPE_TICKET = "CORE-1841"

PACK_LAYERS: frozenset[Layer] = frozenset(
    {Layer.KEYWORDS, Layer.BUILTINS, Layer.EXCEPTIONS, Layer.IMPLICIT_PARAMS}
)


class TranslateFn(Protocol):
    def __call__(
        self, source: str, source_lang: str, target_lang: str, python_version: str
    ) -> tuple[str, bool]: ...


def _layers_exercised(
    source: str, pack: LanguagePack, *, native_side: bool
) -> frozenset[Layer]:
    """Pack layers with at least one term present in ``source``'s tokens.

    ``verified`` is earned: a layer the source never exercises cannot be
    claimed, however clean the trip. Uses the same token index and pack
    lookup as classification so the two cannot disagree about membership.
    """
    present: set[Layer] = set()
    names = {
        token.string
        for tokens in _tokens_by_line(source).values()
        for token in tokens
        if token.type == tokenize.NAME
    }
    for layer, mapping in _pack_sections(pack):
        own: set[str] = set(mapping.values() if native_side else mapping.keys())
        if names & own:
            present.add(layer)
    return frozenset(present)


@dataclass(frozen=True)
class RoundTripReport:
    """The result of one round trip. Facts only - never policy.

    Callers set policy: the MCP sweep fails on residue, the demo verifier
    warns on it, both from this one report. ``forward``/``returned`` exist
    for in-process reuse and are never serialised.
    """

    round_trips: bool
    forward_valid: bool | None
    divergences: tuple[Divergence, ...]
    divergence_count: int
    verified: frozenset[Layer]
    source_lang: str
    through_lang: str
    pivoted: bool
    grammar_version: str
    forward: str
    returned: str
    schema_version: str = SCHEMA_VERSION

    @property
    def verdict_line(self) -> str:
        """One line, safe to quote: verdict, direction, location, layer,
        counts, coverage, pivot, grammar - never source content. Source
        lines are attacker-influenced input, and this line is reproduced
        into agent prose and logs by instruction.
        """
        trip = f"{self.source_lang}→{self.through_lang}→{self.source_lang}"
        pivot = " · via pivot" if self.pivoted else ""
        grammar = f"grammar {self.grammar_version}"

        if self.forward_valid is False:
            return (
                f"legesher: round-trip FAILED — {trip} · canonical form "
                f"does not compile{pivot} · {grammar}"
            )
        if not self.round_trips:
            first = self.divergences[0] if self.divergences else None
            if first is None:
                # No divergence to show distinguishes two shapes by the
                # count: a comparison that ran but whose rows were all
                # bounded out (count > 0), and a translation hop that
                # errored before any comparison (count == 0). Conflating
                # them made the line contradict its own payload.
                if self.divergence_count:
                    return (
                        f"legesher: round-trip FAILED — {trip} · "
                        f"{self.divergence_count} divergence(s), none shown"
                        f"{pivot} · {grammar}"
                    )
                return (
                    f"legesher: round-trip FAILED — {trip} · translation hop "
                    f"errored; no comparison performed{pivot} · {grammar}"
                )
            where = f"line {first.line}"
            if first.offset is not None:
                where += f" col {first.offset}"
            layer = first.layer.value if first.layer else "unclassified"
            shown = min(len(self.divergences), self.divergence_count)
            return (
                f"legesher: round-trip FAILED — {trip} · {where} · "
                f"layer {layer} · {shown} of {self.divergence_count} "
                f"divergences shown{pivot} · {grammar}"
            )

        exercised = ", ".join(sorted(layer.value for layer in self.verified)) or "none"
        uncovered = ", ".join(
            sorted(layer.value for layer in Layer if layer not in self.verified)
        )
        return (
            f"legesher: round-trip VERIFIED — {trip} · exercised: {exercised} · "
            f"not covered: {uncovered} ({SCOPE_TICKET}){pivot} · {grammar}"
        )

    def to_dict(self) -> dict[str, Any]:
        """JSON-safe projection; omits the source bodies by design. The key
        set is pinned by a test - change it and bump SCHEMA_VERSION.
        """
        return {
            "schema_version": self.schema_version,
            "round_trips": self.round_trips,
            "forward_valid": self.forward_valid,
            "verdict_line": self.verdict_line,
            "divergence_count": self.divergence_count,
            "divergences": [
                {
                    "line": d.line,
                    "offset": d.offset,
                    "expected": d.expected,
                    "actual": d.actual,
                    "kind": d.kind.value,
                    "layer": d.layer.value if d.layer else None,
                }
                for d in self.divergences
            ],
            "verified": sorted(layer.value for layer in self.verified),
            "source_lang": self.source_lang,
            "through_lang": self.through_lang,
            "pivoted": self.pivoted,
            "grammar_version": self.grammar_version,
        }


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
) -> RoundTripReport:
    """Round-trip ``source`` through ``through_lang`` and back, compare.

    Raises ``ValueError`` iff ``source_lang == through_lang`` (the engine
    short-circuits identity, so the trip would verify nothing). Never
    raises otherwise: a failing hop IS the verdict.
    """
    if source_lang == through_lang:
        raise ValueError(
            f"round trip from {source_lang!r} through {through_lang!r} is a "
            "no-op: both hops are identity and the comparison would verify "
            "nothing"
        )

    native_side = source_lang == pack.language

    # The two hops fail independently, and the facts each one established
    # survive its neighbour's failure: a return-hop error still knows the
    # forward rendering, its pivot, and (when a validator is present)
    # whether the canonical form compiles.
    try:
        forward, forward_pivoted = translate(
            source, source_lang, through_lang, python_version
        )
    except Exception:
        return RoundTripReport(
            round_trips=False,
            forward_valid=None,
            divergences=(),
            divergence_count=0,
            verified=frozenset(),
            source_lang=source_lang,
            through_lang=through_lang,
            pivoted=False,
            grammar_version=python_version,
            forward="",
            returned="",
        )

    # The same results-not-exceptions discipline the hops get: a validator
    # that raises must not break the never-raises contract, and an unknown
    # compile fact is reported as unknown, never assumed.
    if validate is not None:
        try:
            forward_valid = validate(forward)
        except Exception:
            forward_valid = None
    else:
        forward_valid = None

    try:
        returned, return_pivoted = translate(
            forward, through_lang, source_lang, python_version
        )
    except Exception:
        return RoundTripReport(
            round_trips=False,
            forward_valid=forward_valid,
            divergences=(),
            divergence_count=0,
            verified=frozenset(),
            source_lang=source_lang,
            through_lang=through_lang,
            pivoted=forward_pivoted,
            grammar_version=python_version,
            forward=forward,
            returned="",
        )

    count = 0
    bounded: list[Divergence] = []
    for divergence in _iter_divergences(source, returned):
        if count < max_divergences:
            bounded.append(divergence)
        count += 1

    # The clean path never tokenizes for classification: there is nothing
    # to classify.
    found = (
        tuple(classified(bounded, source, returned, pack, native_side=native_side))
        if bounded
        else ()
    )

    clean = count == 0
    exercised = _layers_exercised(source, pack, native_side=native_side)
    if clean:
        verified = exercised
    elif count == len(found) and all(d.layer is not None for d in found):
        # Every divergence was seen and attributed, so layers outside the
        # broken set are genuinely clean.
        verified = frozenset(exercised - {d.layer for d in found})
    else:
        # Divergences past the bound, or ones classification could not
        # attribute (LINE_COUNT / terminator runs / untokenizable lines),
        # could sit in ANY layer. Crediting a layer we cannot prove clean
        # is the exact over-claim `verified` exists to prevent, so on an
        # incompletely-attributed failure nothing is credited.
        verified = frozenset()

    return RoundTripReport(
        round_trips=clean,
        forward_valid=forward_valid,
        divergences=found,
        divergence_count=count,
        verified=verified,
        source_lang=source_lang,
        through_lang=through_lang,
        pivoted=forward_pivoted or return_pivoted,
        grammar_version=python_version,
        forward=forward,
        returned=returned,
    )
