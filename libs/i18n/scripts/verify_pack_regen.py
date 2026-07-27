#!/usr/bin/env python3
"""Value-aware verification that pack regeneration is safe (CORE-1400).

Regenerates every shipped language pack from the canonical selection
layer (``selected_translations``) into a scratch copy of the pack tree,
then diffs the result against the shipped packs and CLASSIFIES every
difference.

Blocking classes:

- ``value_changed``    — a term's translation differs
- ``key_added``        — regen emits a term the shipped pack lacks
- ``key_removed``      — regen drops a term the shipped pack carries
- ``section_changed``  — a top-level section appears/disappears
- ``unknown_section``  — a top-level key this gate does not know how to
  compare. ``_write_yaml_pack`` rebuilds the YAML from a fixed set of
  keys, so anything else is silently dropped on regen — and, worse,
  would not be diffed even if both sides carried it. Adding a new pack
  layer (e.g. MLCP ``members``) must therefore extend :data:`SECTIONS`
  here AND ``_PACK_SECTIONS`` in ``yaml_exporter``; this class is what
  forces that. Reported once per key per run, not once per pack file.
- ``metadata_changed`` — metadata block differs
- ``header_changed``   — leading comment block differs
- ``not_regenerated``  — the export left the seeded copy of a shipped
  file untouched, so "regeneration" produced nothing for it. The scratch
  tree MUST be seeded with the shipped YAMLs (``_write_yaml_pack``
  preserves their header, key order and curated metadata), which means an
  export that writes nothing leaves the seed to be compared against
  itself and every file "matches". Zeroing each seeded file's mtime turns
  that silent pass into this finding.
- ``file_missing``     — regen did not produce a shipped pack file
- ``file_added``       — regen produced a file the shipped tree lacks
- ``not_compared``     — a (language, version) pair the registry says
  must exist was never compared at all
- ``unexpected_pack``  — a pack file was compared that nothing expects:
  a language absent from ``languages.json`` or a version outside
  :data:`EXPECTED_VERSIONS`. Evidence must not contain files outside the
  matrix it claims to cover.
- ``export_failed``    — regenerating a language raised. The export is
  per language and this script's whole product is the report, so an
  uncaught exception would abort the run with no report file and no
  findings for the other 50 languages — an early-alphabet failure
  (``am``) would blank the entire matrix. Failures are recorded as this
  blocking class and the run continues.

Informational (non-blocking) classes:

- ``comment_lost``     — a comment line present in the shipped pack is
  absent from the regenerated one. Non-blocking *today* because the
  exporter genuinely loses interior and trailing comments (it round-trips
  only the leading header block), and three shipped ``en`` packs hit it.
  Promote this to blocking once ``yaml_exporter._write_yaml_pack``
  preserves interior comments; until then, curator notes lost to a regen
  are reported loudly rather than laundered into ``not_byte_identical``.
- ``not_byte_identical`` — file bytes differ although values match
  (YAML representation only)

The gate PASSES only when every blocking class is empty — i.e. a full
regeneration of all registry languages reproduces the shipped, curated
packs value-for-value, with nothing missing on either side.

Counting note (the reason this script exists): the "files compared"
figure is the number of ``compare_file`` calls actually made, checked
against the (language, version) matrix the registry demands. It is never
derived by arithmetic — a count of comparisons that were never run is
exactly the evidence failure this gate is supposed to prevent.

Run it in CI or before any regen-and-commit workflow:

    uv run python scripts/verify_pack_regen.py [--report OUT.md]

Exits 0 on a clean verification, 1 otherwise.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from collections import Counter
from collections.abc import Collection
from pathlib import Path

import yaml

_SCRIPT_DIR = Path(__file__).resolve().parent
_I18N_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_I18N_ROOT))
sys.path.insert(0, str(_SCRIPT_DIR))
sys.path.insert(0, str(_SCRIPT_DIR / "translate"))

# Reuse the collision audit's registry reader so both gates agree on
# "which languages must have packs" (languages.json, not whatever
# happens to be on disk).
from audit_collisions import (  # type: ignore[import-not-found]  # noqa: E402
    _expected_pack_codes,
)
from legesher_i18n.db import TranslationDatabase  # noqa: E402
from yaml_exporter import YAMLExporter  # type: ignore[import-not-found]  # noqa: E402

DB_PATH = _I18N_ROOT / "legesher_i18n" / "db" / "translations.db"
PACKS_DIR = _I18N_ROOT / "language-packs" / "python"

SECTIONS = ("keywords", "builtins", "exceptions", "reserved_words")
SCALAR_FIELDS = ("language", "target", "version", "extends")

#: Every top-level key this gate knows how to diff. Anything outside it
#: raises ``unknown_section`` rather than passing unexamined.
KNOWN_TOP_LEVEL = frozenset(SECTIONS) | frozenset(SCALAR_FIELDS) | {"metadata"}

#: Pack versions the exporter emits per language. Mirrors the explicit
#: ``_write_yaml_pack`` calls in ``yaml_exporter.export_language``; when a
#: new interpreter version is added there, add it here too. Forgetting is
#: loud, not silent: the new file lands as ``file_added`` for every
#: language.
EXPECTED_VERSIONS = ("3.10", "3.11", "3.12", "3.13", "3.14")

#: Difference classes that do not fail the gate.
INFORMATIONAL_KINDS = frozenset({"not_byte_identical", "comment_lost"})

#: Report order.
FINDING_KINDS = (
    "value_changed",
    "key_added",
    "key_removed",
    "section_changed",
    "unknown_section",
    "metadata_changed",
    "header_changed",
    "not_regenerated",
    "file_missing",
    "file_added",
    "not_compared",
    "unexpected_pack",
    "export_failed",
    "comment_lost",
    "not_byte_identical",
)

#: mtime stamped onto every seeded scratch copy before the export runs.
#: A file still carrying it afterwards was never rewritten.
_UNREGENERATED_SENTINEL = (0, 0)

#: ``version`` recorded for a finding about a whole language rather than
#: one pack file. Never a real version, so it can never be mistaken for
#: coverage of one.
_ALL_VERSIONS = "(all)"


def pack_languages() -> list[str]:
    """Return the language codes that actually have a pack tree on disk.

    This drives what gets regenerated. It is deliberately NOT the
    expected set — see :func:`check_expected_matrix`.
    """
    return sorted(
        d.name
        for d in PACKS_DIR.iterdir()
        if d.is_dir() and (d / f"legesher_i18n_python_{d.name}").exists()
    )


def _show(value: object) -> str:
    """Render a value so confusables/normalization differences are visible.

    ``repr`` prints non-ASCII literally, so a Cyrillic U+043E swapped for
    a Latin ``o`` renders as two identical-looking strings. Append the
    escaped form whenever it differs, so a reviewer sees codepoints.
    """
    literal = repr(value)
    escaped = ascii(value)
    return literal if escaped == literal else f"{literal} ({escaped})"


def _one_line(exc: Exception, limit: int = 400) -> str:
    """Render an exception message as one bounded, list-item-safe line.

    ``IncompleteSelectionError`` names up to ten missing slots and the
    report is a markdown bullet list, so an unflattened message would
    break out of its own bullet.
    """
    text = " ".join(str(exc).split()) or repr(exc)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _header_of(text: str) -> str:
    """Return the leading comment block (stops at the first content line)."""
    lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("#") or (lines and not line.strip()):
            lines.append(line)
        else:
            break
    return "\n".join(lines).strip()


def _ends_token(line: str, index: int) -> bool:
    """Does the character at ``index`` end a YAML token?

    Only the indicators that genuinely separate tokens count, so the
    hyphen in ``well-known`` and the colon in ``https://example.com`` do
    not restart one:

    - ``:`` only when followed by whitespace or end of line (``key: v``)
    - ``-`` only as a block-sequence indicator: line-initial, then space
    - ``,``, ``[``, ``{`` always (flow collections)
    """
    char = line[index]
    after = line[index + 1] if index + 1 < len(line) else ""
    if char == ":":
        return after in ("", " ", "\t")
    if char == "-":
        return after in (" ", "\t") and not line[:index].strip()
    return char in ",[{"


def _scan_comment(line: str) -> str | None:
    """Return the comment on one line, or ``None`` if it carries none.

    Per YAML, an inline comment must be preceded by whitespace (or start
    the line), and a ``#`` inside a quoted scalar is not a comment.

    A quote character only OPENS a quoted scalar where a token may begin
    — the start of the line, or the first non-space character after a
    token separator (see :func:`_ends_token`). Anywhere else it is
    ordinary text, because a plain YAML scalar may contain quotes:
    ``note: don't`` and ``author: O'Brien`` are plain scalars, not the
    start of quoted ones. Counting quotes and only distrusting an odd
    count is not equivalent — it goes blind on ``note: don't # won't``,
    where two stray apostrophes happen to balance and hide a real
    comment, laundering a ``comment_lost`` into ``not_byte_identical``.
    Escapes inside double-quoted scalars are not modelled.
    """
    quote: str | None = None
    at_token_start = True
    for index, char in enumerate(line):
        if quote is not None:
            if char == quote:
                quote = None
                at_token_start = False
            continue
        if char == "#" and (index == 0 or line[index - 1] in " \t"):
            return line[index:].strip()
        if char in " \t":
            continue  # whitespace neither opens nor closes a token
        if at_token_start and char in "\"'":
            quote = char
        at_token_start = _ends_token(line, index)
    return None


def _comments_of(text: str) -> list[str]:
    """Return every comment in ``text``, header and interior alike."""
    return [
        comment
        for comment in (_scan_comment(line) for line in text.splitlines())
        if comment is not None
    ]


def compare_file(
    shipped: Path,
    regen: Path,
    findings: list[dict],
    lang: str,
    seen_unknown: set[str] | None = None,
) -> None:
    """Diff one shipped pack file against its regenerated counterpart.

    ``seen_unknown`` collapses ``unknown_section`` to one finding per key
    across a whole run: a new pack layer lands in every pack file at
    once, so per-file reporting buries the run in 255 identical lines.
    Pass ``None`` (the default) to report per file.
    """
    version = shipped.stem
    shipped_text = shipped.read_text(encoding="utf-8")
    regen_text = regen.read_text(encoding="utf-8")
    shipped_data = yaml.safe_load(shipped_text) or {}
    regen_data = yaml.safe_load(regen_text) or {}
    start = len(findings)
    collapsed = 0  # content differences found here but reported elsewhere

    def add(kind: str, detail: str) -> None:
        findings.append(
            {"lang": lang, "version": version, "kind": kind, "detail": detail}
        )

    # Any top-level key outside KNOWN_TOP_LEVEL is dropped by the
    # exporter AND invisible to every check below it, so flag it before
    # reporting a clean diff over the keys we do understand.
    for key in sorted((set(shipped_data) | set(regen_data)) - KNOWN_TOP_LEVEL):
        if seen_unknown is not None:
            if key in seen_unknown:
                collapsed += 1
                continue
            seen_unknown.add(key)
        value = shipped_data.get(key, regen_data.get(key))
        register = (
            "add it to SECTIONS here and to _PACK_SECTIONS in "
            "scripts/translate/yaml_exporter.py"
            if isinstance(value, dict)
            else "add it to SCALAR_FIELDS here and teach "
            "scripts/translate/yaml_exporter.py::_write_yaml_pack to emit it"
        )
        add(
            "unknown_section",
            f"{key}: shipped={'present' if key in shipped_data else 'absent'} "
            f"regen={'present' if key in regen_data else 'absent'} — this gate "
            f"does not compare this key and the exporter drops it; "
            f"{register} (reported once per key per run)",
        )

    for section in SECTIONS:
        in_shipped = section in shipped_data
        in_regen = section in regen_data
        if in_shipped != in_regen:
            # Empty-section presence differences are structural.
            add(
                "section_changed",
                f"{section}: shipped={'present' if in_shipped else 'absent'} "
                f"regen={'present' if in_regen else 'absent'}",
            )
        s_map = shipped_data.get(section) or {}
        r_map = regen_data.get(section) or {}
        s_keys = {k for k, v in s_map.items() if v is not None}
        r_keys = {k for k, v in r_map.items() if v is not None}
        for key in sorted(s_keys - r_keys):
            add("key_removed", f"{section}.{key} (shipped {_show(s_map[key])})")
        for key in sorted(r_keys - s_keys):
            add("key_added", f"{section}.{key} (regen {_show(r_map[key])})")
        for key in sorted(s_keys & r_keys):
            if s_map[key] != r_map[key]:
                add(
                    "value_changed",
                    f"{section}.{key}: shipped {_show(s_map[key])} -> "
                    f"regen {_show(r_map[key])}",
                )

    for field in SCALAR_FIELDS:
        if shipped_data.get(field) != regen_data.get(field):
            add(
                "section_changed",
                f"{field}: {_show(shipped_data.get(field))} -> "
                f"{_show(regen_data.get(field))}",
            )

    if (shipped_data.get("metadata") or {}) != (regen_data.get("metadata") or {}):
        s_meta = shipped_data.get("metadata") or {}
        r_meta = regen_data.get("metadata") or {}
        delta = {
            k: (s_meta.get(k), r_meta.get(k))
            for k in sorted(set(s_meta) | set(r_meta))
            if s_meta.get(k) != r_meta.get(k)
        }
        # Metadata is curator free text (author, license, hand-added
        # keys), so render it through _show too — str() would print a
        # Cyrillic confusable identically to its Latin twin.
        add(
            "metadata_changed",
            "{"
            + ", ".join(
                f"{_show(key)}: {_show(was)} -> {_show(now)}"
                for key, (was, now) in delta.items()
            )
            + "}",
        )

    if _header_of(shipped_text) != _header_of(regen_text):
        add("header_changed", "leading comment block differs")

    # Curator comments are content, not formatting. The header block is
    # round-tripped by the exporter; interior and trailing comments are
    # not, so name each one that a regen would delete.
    lost = sorted(set(_comments_of(shipped_text)) - set(_comments_of(regen_text)))
    for comment in lost:
        add("comment_lost", f"regen drops {comment!r}")

    if shipped_text != regen_text:
        # "(values match)" is only true when nothing else fired for this
        # file; claiming it next to a value_changed line would be a false
        # statement inside the evidence artifact.
        content = len(findings) - start + collapsed
        add(
            "not_byte_identical",
            "YAML representation differs (values match)"
            if content == 0
            else f"YAML representation differs, and {content} content "
            f"difference(s) were found in this file",
        )


def compare_language(
    lang: str,
    shipped_dir: Path,
    regen_dir: Path,
    findings: list[dict],
    skip_versions: Collection[str] = (),
    seen_unknown: set[str] | None = None,
) -> set[str]:
    """Compare one language's pack directory; return versions compared.

    Iterates the UNION of both sides: iterating only the shipped files
    means a file the shipped tree is missing is never looked at, which is
    how "0 differences over 0 comparisons" used to pass.

    ``skip_versions`` names versions already reported as
    ``not_regenerated``: their scratch file is the seeded copy of the
    shipped file, so comparing it would compare a file against itself and
    inflate the "files compared" count with a comparison that proves
    nothing. One root cause, one blocking line.
    """
    shipped_files = (
        {f.name: f for f in shipped_dir.glob("*.yml")} if shipped_dir.is_dir() else {}
    )
    regen_files = (
        {f.name: f for f in regen_dir.glob("*.yml")} if regen_dir.is_dir() else {}
    )

    compared: set[str] = set()
    for name in sorted(set(shipped_files) | set(regen_files)):
        version = Path(name).stem
        if version in skip_versions:
            continue
        if name not in regen_files:
            findings.append(
                {
                    "lang": lang,
                    "version": version,
                    "kind": "file_missing",
                    "detail": "regen did not produce this file",
                }
            )
            continue
        if name not in shipped_files:
            findings.append(
                {
                    "lang": lang,
                    "version": version,
                    "kind": "file_added",
                    "detail": "regen produced a file the shipped tree lacks",
                }
            )
            continue
        compare_file(
            shipped_files[name], regen_files[name], findings, lang, seen_unknown
        )
        compared.add(version)
    return compared


def check_expected_matrix(
    expected_langs: list[str],
    compared: set[tuple[str, str]],
    findings: list[dict],
) -> set[tuple[str, str]]:
    """Assert the compared set and the registry-mandated matrix agree.

    Both directions matter. ``expected - compared`` is a pack the
    registry demands that this run never looked at. ``compared -
    expected`` is the mirror image and is just as much an evidence
    failure: it is how a run reported "260 of 255" — a coverage claim
    that contradicts itself — and passed. The set is live, not
    hypothetical: ``translations.db`` carries more languages than
    ``languages.json`` does, and more are queued.

    Returns the expected pair set so the summary can report coverage as
    "N of M", not as arithmetic over the language count.
    """
    expected = {(lang, v) for lang in expected_langs for v in EXPECTED_VERSIONS}
    # A pair already explained by a file-level finding does not need a
    # second, redundant blocking line.
    accounted = {
        (f["lang"], f["version"])
        for f in findings
        if f["kind"] in ("file_missing", "file_added", "not_regenerated")
    }
    for lang, version in sorted(expected - compared - accounted):
        findings.append(
            {
                "lang": lang,
                "version": version,
                "kind": "not_compared",
                "detail": (
                    "languages.json expects this pack but it was never "
                    "compared (missing pack directory or pack tree)"
                ),
            }
        )
    for lang, version in sorted(compared - expected):
        findings.append(
            {
                "lang": lang,
                "version": version,
                "kind": "unexpected_pack",
                "detail": (
                    "this pack file was compared but nothing expects it: "
                    "languages.json does not list this language, or "
                    "EXPECTED_VERSIONS does not list this version. Register "
                    "it or remove the file — the coverage claim must cover "
                    "exactly the matrix it names"
                ),
            }
        )
    return expected


def seed_scratch(langs: list[str], scratch: Path) -> None:
    """Copy the shipped pack YAMLs into the scratch tree, mtime-zeroed.

    The copies are required: ``_write_yaml_pack`` reads the existing file
    to preserve its header, key order and curated metadata, so an export
    into an empty tree would diff every file on presentation alone. The
    zeroed mtime is the sentinel that keeps the seed from being mistaken
    for a regeneration (see :func:`find_not_regenerated`).
    """
    for lang in langs:
        src = PACKS_DIR / lang / f"legesher_i18n_python_{lang}" / "packs"
        dst = scratch / lang / f"legesher_i18n_python_{lang}" / "packs"
        dst.mkdir(parents=True, exist_ok=True)
        for f in src.glob("*.yml"):
            copy = dst / f.name
            shutil.copy2(f, copy)
            os.utime(copy, _UNREGENERATED_SENTINEL)
            if copy.stat().st_mtime_ns != 0:
                # A sentinel that does not stick would silently restore
                # the very bug this closes: seed compared against itself.
                raise RuntimeError(
                    f"Could not stamp the regeneration sentinel on {copy}: "
                    f"the filesystem ignored os.utime. Run the gate on a "
                    f"filesystem that honours it — without the sentinel a "
                    f"silent export skip passes as a clean regeneration."
                )


def find_not_regenerated(
    langs: list[str], scratch: Path, findings: list[dict]
) -> set[tuple[str, str]]:
    """Report every seeded pack copy the export did not rewrite.

    This is the failure the seeding makes possible and nothing else
    catches. ``export_language`` returns ``None`` and writes nothing when
    a language has no canonical selections — a log line, not an exception
    — so the seeded copies survive and get compared against themselves.
    Every file "matches", the gate reports full coverage and exits 0, and
    the certification is of the shipped tree against itself.

    An mtime sentinel is used rather than ``export_language``'s return
    value because it is per FILE: a language that exports but drops one
    of its five version files fails here too, and ``_write_yaml_pack``
    rewrites unconditionally, so a real export always advances the mtime.
    """
    stale: set[tuple[str, str]] = set()
    for lang in langs:
        packs = scratch / lang / f"legesher_i18n_python_{lang}" / "packs"
        for f in sorted(packs.glob("*.yml")):
            if f.stat().st_mtime_ns != 0:
                continue
            stale.add((lang, f.stem))
            findings.append(
                {
                    "lang": lang,
                    "version": f.stem,
                    "kind": "not_regenerated",
                    "detail": (
                        "the export left the seeded copy of this shipped file "
                        "untouched, so regeneration produced nothing to "
                        "compare — the language has no canonical selections, "
                        "or this is not a file the exporter emits"
                    ),
                }
            )
    return stale


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, help="Write a markdown report here")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()

    expected_langs = _expected_pack_codes()
    if not expected_langs:
        print("FAIL: could not read the expected language set from languages.json")
        return 1

    langs = pack_languages()
    findings: list[dict] = []
    compared: set[tuple[str, str]] = set()

    with tempfile.TemporaryDirectory(prefix="core1400-regen-") as tmp:
        scratch = Path(tmp) / "python"
        seed_scratch(langs, scratch)

        db = TranslationDatabase(db_path=str(args.db))
        exporter = YAMLExporter(db=db, output_dir=scratch)
        for lang in langs:
            try:
                exporter.export_language(lang, overwrite=True, strict=True)
            except Exception as exc:  # noqa: BLE001 - reported, not raised
                # One unexportable language must not cost the other 50
                # their evidence: an uncaught exception here aborts
                # before the report is written, and the earlier the
                # language sorts, the more of the matrix it blanks.
                findings.append(
                    {
                        "lang": lang,
                        "version": _ALL_VERSIONS,
                        "kind": "export_failed",
                        "detail": (
                            f"regenerating this language raised "
                            f"{type(exc).__name__}: {_one_line(exc)} — its "
                            f"packs were not regenerated; the remaining "
                            f"languages were still verified"
                        ),
                    }
                )

        # Before any diffing: which "regenerated" files are just the seed?
        stale = find_not_regenerated(langs, scratch, findings)

        seen_unknown: set[str] = set()
        for lang in langs:
            shipped_dir = PACKS_DIR / lang / f"legesher_i18n_python_{lang}" / "packs"
            regen_dir = scratch / lang / f"legesher_i18n_python_{lang}" / "packs"
            compared |= {
                (lang, version)
                for version in compare_language(
                    lang,
                    shipped_dir,
                    regen_dir,
                    findings,
                    skip_versions={v for stale_lang, v in stale if stale_lang == lang},
                    seen_unknown=seen_unknown,
                )
            }

    expected = check_expected_matrix(expected_langs, compared, findings)
    # Report coverage over the expected matrix only. Pairs outside it are
    # already blocking (``unexpected_pack``) and must never inflate the
    # numerator into "260 of 255".
    covered = compared & expected
    unexpected = compared - expected

    blocking = [f for f in findings if f["kind"] not in INFORMATIONAL_KINDS]
    info = [f for f in findings if f["kind"] in INFORMATIONAL_KINDS]
    counts = Counter(f["kind"] for f in findings)

    lines = [
        "# CORE-1400 pack regeneration verification",
        "",
        f"- Languages expected (languages.json): {len(expected_langs)}",
        f"- Languages regenerated: {len(langs)}",
        f"- Pack files compared: {len(covered)} of {len(expected)} expected",
    ]
    if unexpected:
        lines.append(
            f"- Pack files compared that nothing expects: {len(unexpected)} "
            f"(see unexpected_pack below)"
        )
    lines += [
        f"- Blocking differences: {len(blocking)}",
        f"- Informational differences: {len(info)}",
        "",
        "## Difference counts by class",
        "",
    ]
    for kind in FINDING_KINDS:
        suffix = " (informational)" if kind in INFORMATIONAL_KINDS else ""
        lines.append(f"- {kind}: {counts.get(kind, 0)}{suffix}")
    if blocking:
        lines += ["", "## Blocking differences", ""]
        for finding in blocking:
            lines.append(
                f"- {finding['lang']} {finding['version']}: "
                f"{finding['kind']} — {finding['detail']}"
            )
    if info:
        lines += ["", "## Informational differences", ""]
        for finding in info:
            lines.append(
                f"- {finding['lang']} {finding['version']}: "
                f"{finding['kind']} — {finding['detail']}"
            )
    report = "\n".join(lines) + "\n"

    print(report)
    if args.report:
        args.report.write_text(report, encoding="utf-8")
        print(f"Report written to {args.report}")

    if blocking:
        print(f"FAIL: {len(blocking)} blocking difference(s)")
        return 1
    print(
        f"PASS: regeneration reproduces all {len(covered)} shipped pack file(s) "
        f"value-for-value"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
