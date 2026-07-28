#!/usr/bin/env python3
"""Record the curated Arabic translations for the JavaScript (JEJ) surface.

CORE-1371. This script IS the generation record: the 62-term curation table
below was produced by an in-session linguist-framed Claude run (the same
framing the pipeline's ClaudeModel encodes — the 62 Tier-1 briefs at
``context/javascript/``, the JS target GUIDE, and the ``ar`` style-guide
chain were the inputs), so provenance is ``source='claude_agent'``,
``model_version='claude-fable-5'``.

Conventions enforced here (they mirror the pack gates, fail-loud, and run
BEFORE any write):

- bare form — no harakat (U+064B..U+0652, U+0670); learners type bare
- standard Arabic block only (plus ASCII underscore for compounds);
  tatweel (U+0640), ZWJ/ZWNJ, and presentation forms are forbidden
- NFC and NFKC fixed points (store-NFC / compare-NFKC contract)
- valid identifier (the CORE-1400 selection gate re-checks at the write
  boundary; ES-side validation with acorn happens at vendor time)
- in-partition uniqueness (Rule 2 reversibility) per keyword/builtin/member

The 11 keyword pre-seeds come verbatim from the shipped Python ``ar`` pack
(cross-target concept identity); ``String`` reuses the validated showcase
choice. ``while`` selects ``طالما`` ("as long as") rather than the
previously shipped Python value ``حتى`` ("until") — the brief forbids an
"until" word and ``do…while`` must read coherently. Madison approved the
correction cross-target (2026-07-28), so ``PYTHON_CORRECTIONS`` below
applies the same fix to the Python ``ar`` row; the superseded value stays
in the suggestions pool as a low-confidence candidate for the decision
trail. Regen the Python pack YAML afterwards (``verify_pack_regen`` +
``YAMLExporter.export_language('ar', overwrite=True)``).

Usage:
    uv run python scripts/record_js_ar_terms.py [--db-path PATH] [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from legesher_i18n.db.database import TranslationDatabase  # noqa: E402

LANGUAGE = "ar"
TARGET = "javascript"
SOURCE = "claude_agent"
MODEL_VERSION = "claude-fable-5"
CREATED_BY = "CORE-1371 in-session linguist run (2026-07-28)"

# (term, category, translation, confidence, origin, rationale)
# origin: preseed-python-ar | showcase-reuse | root-reuse-python-ar | new
TERMS: list[tuple[str, str, str, str, str, str]] = [
    # ── keywords (17) ──────────────────────────────────────────────
    (
        "break",
        "keyword",
        "كسر",
        "high",
        "preseed-python-ar",
        "Shipped Python ar keyword; forceful loop-exit verb, distinct from إرجاع (return).",
    ),
    (
        "const",
        "keyword",
        "ثابت",
        "high",
        "new",
        "'Fixed/constant' active participle; matched pair with متغير (let) — same form, opposite mutability. Standard Arabic CS pedagogy term.",
    ),
    (
        "continue",
        "keyword",
        "يستمر",
        "high",
        "preseed-python-ar",
        "Shipped Python ar keyword; 'proceeds/continues', clearly distinct from كسر.",
    ),
    (
        "do",
        "keyword",
        "افعل",
        "high",
        "new",
        "Imperative 'do/perform'. Reads as one construct with طالما: افعل {…} طالما (شرط) = 'do … as long as (cond)'. Alt considered: نفذ (execute).",
    ),
    (
        "else",
        "keyword",
        "إلا",
        "high",
        "preseed-python-ar",
        "Shipped Python ar keyword; إلا إذا composes naturally for else-if, mirroring Python elif=إلّاإذا.",
    ),
    (
        "false",
        "keyword",
        "كاذب",
        "high",
        "preseed-python-ar",
        "Shipped Python ar False; antonym pair with صحيح, same adjectival form.",
    ),
    (
        "for",
        "keyword",
        "لكل",
        "high",
        "preseed-python-ar",
        "Shipped Python ar keyword; 'for each' loop-introducer, composes with من (of): لكل س من العناصر.",
    ),
    (
        "if",
        "keyword",
        "إذا",
        "high",
        "preseed-python-ar",
        "Shipped Python ar keyword; the natural conditional particle.",
    ),
    (
        "in",
        "keyword",
        "في",
        "high",
        "preseed-python-ar",
        "Shipped Python ar keyword; locative 'in' fits JS key-presence test, distinct from من (of).",
    ),
    (
        "let",
        "keyword",
        "متغير",
        "high",
        "new",
        "'Variable/changeable' active participle; matched pair with ثابت (const). متغير عمر = ٥ is exactly how Arabic CS texts declare. Alt: ليكن (algebraic 'let it be') lacks a natural const-counterpart.",
    ),
    (
        "new",
        "keyword",
        "أنشئ",
        "high",
        "new",
        "Imperative 'create/construct' (standard software Arabic إنشاء). Avoids the adjective جديد ('recent') trap the brief flags.",
    ),
    (
        "null",
        "keyword",
        "لاشيء",
        "high",
        "preseed-python-ar",
        "Shipped Python ar None; 'nothing' as deliberate absence, distinct from غير_معرف (undefined = unset).",
    ),
    (
        "of",
        "keyword",
        "من",
        "high",
        "new",
        "Partitive 'from/of': لكل عنصر من العناصر reads 'for each item of the items'. Distinct from في (in) as the brief requires.",
    ),
    (
        "return",
        "keyword",
        "إرجاع",
        "high",
        "preseed-python-ar",
        "Shipped Python ar keyword; masdar of 'give back' — the value-transfer sense.",
    ),
    (
        "true",
        "keyword",
        "صحيح",
        "high",
        "preseed-python-ar",
        "Shipped Python ar True; logical 'correct/true', antonym pair with كاذب.",
    ),
    (
        "typeof",
        "keyword",
        "نوع",
        "high",
        "root-reuse-python-ar",
        "Same root as shipped Python type=نوع (same concept, cross-target identity). Idafa carries the 'of': نوع س = 'type of x'.",
    ),
    (
        "while",
        "keyword",
        "طالما",
        "high",
        "new",
        "'As long as' — the conditional-durative the brief requires. The previously shipped Python ar while=حتى ('until') inverts the truth sense and breaks do…while coherence; Madison approved correcting BOTH targets to طالما (2026-07-28).",
    ),
    # ── builtins (16) ──────────────────────────────────────────────
    (
        "BigInt",
        "builtin",
        "عدد_صحيح_كبير",
        "medium",
        "new",
        "'Big integer' keeping BOTH halves per the brief (عدد_صحيح = integer, mirroring Python int=العددالصحيح; كبير = big). Long but rare in JEJ.",
    ),
    (
        "Boolean",
        "builtin",
        "منطقي",
        "high",
        "root-reuse-python-ar",
        "'Logical' — Arabic CS-education standard; root-reuse of shipped Python bool=المنطقي (bare, article-free per JS convention).",
    ),
    (
        "Date",
        "builtin",
        "تاريخ",
        "high",
        "new",
        "Standard Arabic CS term for the date/time value; broad enough to include time-of-day.",
    ),
    (
        "Infinity",
        "builtin",
        "لانهاية",
        "high",
        "new",
        "'No-end' — the school-math infinity (اللانهاية), bare form. Register-matched with ليس_عدد (NaN).",
    ),
    (
        "Math",
        "builtin",
        "رياضيات",
        "high",
        "new",
        "'Mathematics' — the school-subject noun, the facility name a learner already knows.",
    ),
    (
        "NaN",
        "builtin",
        "ليس_عدد",
        "high",
        "new",
        "'Not a-number' native gloss (a Latin NaN token would fail the Arabic script policy). Coherent with عدد (Number) vocabulary.",
    ),
    (
        "Number",
        "builtin",
        "عدد",
        "high",
        "new",
        "The broad quantity word — NOT رقم (digit-glyph, the brief's trap) and not integer/decimal-specific; JS has one number type.",
    ),
    (
        "RegExp",
        "builtin",
        "تعبير_نمطي",
        "medium",
        "new",
        "تعبير نمطي is the established Arabic CS compound for 'regular expression'; underscore-joined per GUIDE.",
    ),
    (
        "String",
        "builtin",
        "سلسلةالأحرف",
        "high",
        "showcase-reuse",
        "Mandated reuse of the validated showcase choice (Python str=سلسلةالأحرف); joined form kept verbatim (internal idafa ال is grammatical).",
    ),
    (
        "alert",
        "builtin",
        "تنبيه",
        "high",
        "new",
        "Masdar 'notifying' — dialog trio family with تأكيد/إدخال; masdar is the shipped-pack register for callables (cf. Python استيراد/إرجاع).",
    ),
    (
        "confirm",
        "builtin",
        "تأكيد",
        "high",
        "new",
        "Masdar 'confirming/asking approval' — the OK/Cancel ask. Distinct from Python assert=التأكيد by bare form and target.",
    ),
    (
        "console",
        "builtin",
        "طرفية",
        "medium",
        "new",
        "'Terminal' — short, recognizable, learner-typed constantly (طرفية.سجل reads 'terminal, record'). MDN-style وحدة_التحكم recorded as candidate; Madison's call.",
    ),
    (
        "parseFloat",
        "builtin",
        "حول_لعشري",
        "high",
        "new",
        "Matched pair with حول_لصحيح — identical parse element حول ('convert'), differing only عشري (decimal), exactly the brief's pair rule.",
    ),
    (
        "parseInt",
        "builtin",
        "حول_لصحيح",
        "high",
        "new",
        "'Convert-to-integer' — the GUIDE's canonical compound exemplar; pairs with حول_لعشري.",
    ),
    (
        "prompt",
        "builtin",
        "إدخال",
        "high",
        "root-reuse-python-ar",
        'Root-reuse of shipped Python input=الإدخال (same learner concept: get typed input). إدخال("ما اسمك؟") reads exactly like Python\'s input().',
    ),
    (
        "undefined",
        "builtin",
        "غير_معرف",
        "high",
        "new",
        "'Not-defined' — the unset/by-default absence, load-bearing contrast with لاشيء (null = deliberate absence).",
    ),
    # ── members (29) ───────────────────────────────────────────────
    (
        "abs",
        "member",
        "قيمة_مطلقة",
        "high",
        "root-reuse-python-ar",
        "School-math 'absolute value' (القيمة المطلقة); root-identical to shipped Python abs=القيمةالمطلقة, re-formed bare + underscore per JS convention.",
    ),
    (
        "ceil",
        "member",
        "سقف",
        "high",
        "new",
        "'Ceiling' — Arabic math uses the same metaphor (دالة السقف for ⌈x⌉); matched UP/DOWN pair with أرضية.",
    ),
    (
        "charAt",
        "member",
        "حرف_عند",
        "high",
        "new",
        "'Character at' — حرف (character) + عند (at-position). Distinct from رمز_حرف_عند (the code, not the character).",
    ),
    (
        "charCodeAt",
        "member",
        "رمز_حرف_عند",
        "medium",
        "new",
        "'Code-of-character-at' — the رمز (code) element is explicit so the near-pair with حرف_عند stays reversible (Rule 2). Long but rare.",
    ),
    (
        "concat",
        "member",
        "وصل",
        "high",
        "new",
        "'Join/connect' — ordered end-to-end linking, survives String→Array widening. Avoids دمج ('merge/blend', the brief's mix trap).",
    ),
    (
        "endsWith",
        "member",
        "ينتهي_ب",
        "high",
        "new",
        "'Ends-with' predicate; exact mirror of يبدأ_ب — matched front/back pair, distinct from يحتوي (anywhere).",
    ),
    (
        "floor",
        "member",
        "أرضية",
        "high",
        "new",
        "'Floor' — Arabic math metaphor (دالة الأرضية for ⌊x⌋); matched pair with سقف, distinct from أدنى (min).",
    ),
    (
        "includes",
        "member",
        "يحتوي",
        "high",
        "new",
        "'Contains' (يحتوي على) — the standard containment verb; reads for substring and future array membership.",
    ),
    (
        "indexOf",
        "member",
        "موقع",
        "high",
        "new",
        "'Position/location of' — a number, not a boolean; keeps موقع (where) ≠ يحتوي (whether) ≠ طول (how many).",
    ),
    (
        "length",
        "member",
        "طول",
        "high",
        "root-reuse-python-ar",
        "Root-reuse of shipped Python len=الطول; Arabic idiom uses طول for strings AND collections (طول المصفوفة), so the brief's spatial-length concern doesn't materialize in Arabic. Bare idafa form.",
    ),
    (
        "log",
        "member",
        "سجل",
        "high",
        "new",
        "'Record!' — the everyday record/register verb; طرفية.سجل reads as a teacher's instruction. Leaves room for future حذر/خطأ siblings (CORE-1609 Q1).",
    ),
    (
        "max",
        "member",
        "أقصى",
        "high",
        "root-reuse-python-ar",
        "'Greatest' — symmetric bare pair with أدنى (Python shipped the asymmetric الحدالأقصى/الأدنى; JS uses the balanced pair, roots preserved).",
    ),
    (
        "min",
        "member",
        "أدنى",
        "high",
        "root-reuse-python-ar",
        "'Lowest' — symmetric pair with أقصى; verbatim root of shipped Python min=الأدنى.",
    ),
    (
        "pow",
        "member",
        "أس",
        "medium",
        "root-reuse-python-ar",
        "'Exponent' — reuse of shipped Python pow=الأس. Brief notes the operation-vs-argument nuance; cross-target consistency and the school term win.",
    ),
    (
        "repeat",
        "member",
        "كرر",
        "high",
        "new",
        "Imperative 'repeat!' — produce N joined copies; naturally takes a count (كرر ٣ مرات).",
    ),
    (
        "replace",
        "member",
        "استبدل",
        "high",
        "new",
        "'Substitute!' — the Find-and-Replace verb (بحث واستبدال); base verb extends to استبدل_الكل per the brief's build rule.",
    ),
    (
        "replaceAll",
        "member",
        "استبدل_الكل",
        "high",
        "new",
        "استبدل + الكل ('all') — the same substitute verb with the load-bearing every-occurrence qualifier.",
    ),
    (
        "round",
        "member",
        "تقريب",
        "high",
        "root-reuse-python-ar",
        "'Rounding' (to nearest) — reuse of shipped Python round=التقريب, bare form; the neutral rounder beside سقف/أرضية.",
    ),
    (
        "slice",
        "member",
        "مقطع",
        "high",
        "new",
        "'Segment/section' — non-destructive extraction that reads for text and arrays (مقطع من المصفوفة); reserved the text-specific word for substring.",
    ),
    (
        "sqrt",
        "member",
        "جذر",
        "high",
        "new",
        "'Root' — الجذر التربيعي is the school term; جذر is its universal short form and sits beside أس (pow) in the same vocabulary.",
    ),
    (
        "startsWith",
        "member",
        "يبدأ_ب",
        "high",
        "new",
        "'Begins-with' predicate; mirror of ينتهي_ب.",
    ),
    (
        "substring",
        "member",
        "سلسلة_فرعية",
        "high",
        "new",
        "'Sub-chain' — the established Arabic CS term for substring; text-bound (echoes سلسلةالأحرف) and clearly distinct from مقطع (slice), the critical Rule-2 check.",
    ),
    (
        "toFixed",
        "member",
        "لمنازل_ثابتة",
        "medium",
        "new",
        "'To fixed (decimal) places' — منازل عشرية is the school term for decimal places; ل- conversion prefix matches the حول_لصحيح precedent. Avoids the repair sense of 'fixed'.",
    ),
    (
        "toLowerCase",
        "member",
        "لأحرف_صغيرة",
        "high",
        "new",
        "'To small letters' — الأحرف الصغيرة is the established Arabic descriptor for lowercase; matched pair differing only صغيرة/كبيرة.",
    ),
    (
        "toPrecision",
        "member",
        "لأرقام_معنوية",
        "medium",
        "new",
        "'To significant figures' — الأرقام المعنوية is the school term; unambiguous against لمنازل_ثابتة (decimal places), keeping the toFixed/toPrecision pair reversible.",
    ),
    (
        "toString",
        "member",
        "لنص",
        "high",
        "new",
        "'To text' — the umbrella render-as-text sense across receivers; ل- conversion family with the other to* members. Distinct from قيمة (valueOf).",
    ),
    (
        "toUpperCase",
        "member",
        "لأحرف_كبيرة",
        "high",
        "new",
        "'To capital letters' — الأحرف الكبيرة; pair with لأحرف_صغيرة.",
    ),
    (
        "trim",
        "member",
        "نظف",
        "medium",
        "new",
        "'Clean!' — everyday cleanup verb for stripping edge whitespace (ننظف الفراغات); alternatives شذب/هذب lean hedge-pruning/refining.",
    ),
    (
        "valueOf",
        "member",
        "قيمة",
        "medium",
        "new",
        "'Value' — قيمة المتغير is the standard math/CS 'value of'; idafa carries the 'of'. Distinct from لنص (text form).",
    ),
]

# Runner-up candidates worth preserving in the suggestions pool: they are
# real alternatives Madison may prefer, recorded with low confidence so the
# CORE-1400 selection rule can never pick them over the curated choice.
ALT_CANDIDATES: list[tuple[str, str, str]] = [
    (
        "while",
        "حتى",
        "Superseded Python-ar value (shipped as while=حتى until 2026-07-28). Semantically 'until' — inverts the truth sense; brief forbids an 'until' word. Kept for the decision trail.",
    ),
    (
        "console",
        "وحدة_التحكم",
        "MDN-standard Arabic for the browser console. Precise but heavy for the most-typed receiver in JEJ; طرفية selected for ergonomics.",
    ),
]

# Cross-target corrections approved by Madison (2026-07-28): the same
# concept must read the same word in every target, so fixing the JS value
# means fixing the shipped Python value too. Applied to the *python* term
# rows; the exporter regen then rewrites the pack YAML from selections.
# (term, python_category, translation, rationale)
PYTHON_CORRECTIONS: list[tuple[str, str, str, str]] = [
    (
        "while",
        "keyword",
        "طالما",
        "Correction of shipped حتى ('until'), which inverts the while sense; "
        "طالما ('as long as') is the conditional-durative. Aligned with the "
        "JS pack selection (CORE-1371, Madison-approved 2026-07-28).",
    ),
]

EXPECTED_SPLIT = {"keyword": 17, "builtin": 16, "member": 29}

_HARAKAT = {chr(c) for c in range(0x064B, 0x0653)} | {"ٰ"}
_FORBIDDEN = {"ـ", "‌", "‍"}  # tatweel, ZWNJ, ZWJ


def _validate() -> list[str]:
    """Pre-flight gates over the curation table. Returns error strings."""
    errors: list[str] = []
    split: dict[str, int] = {}
    by_partition: dict[str, dict[str, str]] = {}
    for term, category, value, confidence, origin, _rationale in TERMS:
        split[category] = split.get(category, 0) + 1
        if confidence not in {"high", "medium", "low"}:
            errors.append(f"{term}: bad confidence {confidence!r}")
        if origin not in {
            "preseed-python-ar",
            "showcase-reuse",
            "root-reuse-python-ar",
            "new",
        }:
            errors.append(f"{term}: bad origin {origin!r}")
        for ch in value:
            if ch == "_":
                continue
            if ch in _FORBIDDEN:
                errors.append(
                    f"{term}: forbidden codepoint U+{ord(ch):04X} in {value!r}"
                )
            elif ch in _HARAKAT:
                errors.append(
                    f"{term}: harakat U+{ord(ch):04X} violates bare-form in {value!r}"
                )
            elif not ("؀" <= ch <= "ۿ"):
                errors.append(
                    f"{term}: {ch!r} (U+{ord(ch):04X}) outside Arabic block in {value!r}"
                )
        if unicodedata.normalize("NFC", value) != value:
            errors.append(f"{term}: {value!r} is not an NFC fixed point")
        if unicodedata.normalize("NFKC", value) != value:
            errors.append(f"{term}: {value!r} is not an NFKC fixed point")
        if not value.isidentifier():
            errors.append(f"{term}: {value!r} is not a valid identifier")
        seen = by_partition.setdefault(category, {})
        if value in seen:
            errors.append(
                f"{category} partition collision: {value!r} for both "
                f"{seen[value]!r} and {term!r}"
            )
        seen[value] = term
    if split != EXPECTED_SPLIT:
        errors.append(f"partition split {split} != expected {EXPECTED_SPLIT}")
    alt_terms = {t for t, _, _ in ALT_CANDIDATES}
    if not alt_terms <= {t for t, *_ in TERMS}:
        errors.append(f"ALT_CANDIDATES reference unknown terms: {alt_terms}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    errors = _validate()
    if errors:
        for err in errors:
            print(f"GATE FAIL: {err}", file=sys.stderr)
        return 1
    print(f"Pre-flight gates passed for {len(TERMS)} terms ({EXPECTED_SPLIT}).")
    if args.dry_run:
        print("Dry run — nothing written.")
        return 0

    db = (
        TranslationDatabase(db_path=str(args.db_path))
        if args.db_path
        else TranslationDatabase()
    )
    try:
        if db.get_language(LANGUAGE) is None:
            print(
                f"ERROR: language {LANGUAGE!r} is not in the languages "
                f"registry table — translations.db is registry-seeded "
                f"(CORE-611); refusing to record against an unregistered "
                f"language.",
                file=sys.stderr,
            )
            return 1
        rows = db.get_terms(programming_language=TARGET)
        ids = {row["name"]: row["id"] for row in rows}
        missing = [t for t, *_ in TERMS if t not in ids]
        if missing:
            print(
                f"ERROR: {len(missing)} terms not seeded (run seed_js_terms.py "
                f"first): {missing[:5]}…",
                file=sys.stderr,
            )
            return 1
        added = selected = 0
        for term, _category, value, confidence, origin, rationale in TERMS:
            added += (
                1
                if db.add_translation(
                    term_id=ids[term],
                    language_code=LANGUAGE,
                    translation=value,
                    source=SOURCE,
                    model_version=MODEL_VERSION,
                    confidence=confidence,
                    model_rationale=rationale,
                    created_by=CREATED_BY,
                )
                else 0
            )
            db.set_selected(
                term_id=ids[term],
                language_code=LANGUAGE,
                translation=value,
                selected_by=MODEL_VERSION,
                selection_reason=f"CORE-1371 in-session curation ({origin})",
            )
            selected += 1
        for term, value, rationale in ALT_CANDIDATES:
            added += (
                1
                if db.add_translation(
                    term_id=ids[term],
                    language_code=LANGUAGE,
                    translation=value,
                    source=SOURCE,
                    model_version=MODEL_VERSION,
                    confidence="low",
                    model_rationale=rationale,
                    created_by=CREATED_BY,
                )
                else 0
            )
        print(
            f"Recorded {added} suggestion rows, {selected} selections "
            f"({LANGUAGE}/{TARGET})."
        )
        py_rows = db.get_terms(programming_language="python")
        py_ids = {(row["name"], row["category"]): row["id"] for row in py_rows}
        for term, category, value, rationale in PYTHON_CORRECTIONS:
            term_id = py_ids.get((term, category))
            if term_id is None:
                print(
                    f"ERROR: python term ({term}, {category}) not found for correction",
                    file=sys.stderr,
                )
                return 1
            db.add_translation(
                term_id=term_id,
                language_code=LANGUAGE,
                translation=value,
                source=SOURCE,
                model_version=MODEL_VERSION,
                confidence="high",
                model_rationale=rationale,
                created_by=CREATED_BY,
            )
            db.set_selected(
                term_id=term_id,
                language_code=LANGUAGE,
                translation=value,
                selected_by=MODEL_VERSION,
                selection_reason=(
                    "CORE-1371 cross-target correction, Madison-approved 2026-07-28"
                ),
            )
            print(f"Python correction: {term} ({category}) -> {value}")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
