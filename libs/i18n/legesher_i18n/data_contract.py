"""Enforcement of the "packs are data, not code" contract (CORE-1453).

Packs are pure data: YAML mappings of terms, plus descriptive metadata.
This module holds the file-level and map-level checks that make that
contract mechanical rather than aspirational:

* :func:`check_file_size` — DoS guard; a pack larger than
  :data:`MAX_PACK_FILE_BYTES` is refused before parsing.
* :func:`check_yaml_data_only` — the YAML event stream must contain no
  tags (no object construction, however the file is later loaded) and no
  anchors/aliases (no reference expansion, the billion-laughs vector).
* :func:`check_top_level_keys` — only keys the pack schema declares are
  allowed; executable-shaped extras fail closed.
* :func:`check_metadata_urls` — URLs in metadata strings must be
  http(s); ``javascript:``, ``file:``, ``data:`` etc. fail closed.
* :func:`check_map_roundtrip` — render-vs-execute consistency at the map
  layer: the localized surface a pack renders must map back to the exact
  canonical form it came from, byte-identically.

File-level checks run per pack file (pre-merge, so a malicious child
cannot hide behind a clean parent); the round-trip check runs on the
merged pack a consumer would actually get. The CLI entry point that
composes both over the shipped tree is
``legesher_i18n.scripts.enforce_data_contract``.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from .schema_validator import (
    ALLOWED_URL_SCHEMES,
    TRANSLATION_SECTIONS,
    Finding,
    LanguagePackSchema,
    find_disallowed_url_schemes,
)

__all__ = [
    "ALLOWED_TOP_LEVEL_KEYS",
    "ALLOWED_URL_SCHEMES",
    "MAX_PACK_FILE_BYTES",
    "check_file_size",
    "check_map_roundtrip",
    "check_metadata_urls",
    "check_top_level_keys",
    "check_yaml_data_only",
    "enforce_file_contract",
    "find_disallowed_url_schemes",
]

# DoS guard: the largest shipped pack is ~20 KiB; 1 MiB matches the repo's
# pre-commit ``check-added-large-files`` ceiling while leaving generous
# headroom for the 103-language expansion.
MAX_PACK_FILE_BYTES = 1024 * 1024

# The pack schema is the single source of truth for what a pack may contain.
ALLOWED_TOP_LEVEL_KEYS = frozenset(LanguagePackSchema.model_fields)

# Python execution flattens the partitions into one token namespace
# (CPython's ``tokenize`` dispatches flat, CORE-710), so the round-trip
# check merges these before inverting. Member-bearing targets (JS,
# CORE-1582) keep partitions separate and check each on its own. The full
# inventory is the schema's TRANSLATION_SECTIONS — one list, not a copy
# (post-merge review finding, 2026-08-09).
_FLAT_PARTITIONS = ("keywords", "builtins", "exceptions", "reserved_words")
_ALL_PARTITIONS = TRANSLATION_SECTIONS

# Python soft keywords whose keyword-role and builtin-role surfaces may
# legally diverge (`type` since 3.12; the engine dispatches contextually).
# Frozen rather than read from ``keyword.softkwlist`` so the gate's verdict
# is identical on every supported interpreter — on 3.10/3.11 the runtime
# list lacks ``type`` and would false-fail 22 shipped languages.
_PY_SOFT_KEYWORDS = frozenset({"_", "case", "match", "type"})


def check_file_size(pack_path: Path) -> list[Finding]:
    """Refuse pack files larger than :data:`MAX_PACK_FILE_BYTES`."""
    size = pack_path.stat().st_size
    if size > MAX_PACK_FILE_BYTES:
        return [
            Finding(
                severity="error",
                code="file-size",
                location=str(pack_path),
                message=(
                    f"Pack file is {size} bytes; the data-contract size cap is "
                    f"{MAX_PACK_FILE_BYTES} bytes (CORE-1453 DoS guard)."
                ),
            )
        ]
    return []


def check_yaml_data_only(pack_path: Path) -> list[Finding]:
    """Reject YAML constructs that go beyond plain data.

    Walks the parse-event stream (no construction happens, so this is safe
    on any input) and fails closed on:

    * any explicit tag (``!!python/...``, ``!custom``, even ``!!str``) —
      packs never need tags, and tags are the object-construction vector;
    * any anchor or alias — reference expansion is the billion-laughs
      amplification vector and shipped packs never use it.
    """
    findings: list[Finding] = []
    try:
        with open(pack_path, encoding="utf-8") as f:
            for event in yaml.parse(f, Loader=yaml.SafeLoader):
                tag = getattr(event, "tag", None)
                if tag:
                    findings.append(
                        Finding(
                            severity="error",
                            code="yaml-tag",
                            location=f"{pack_path}:{event.start_mark.line + 1}",
                            message=(
                                f"Explicit YAML tag '{tag}' — packs are data, "
                                "not code; tags are refused (CORE-1453)."
                            ),
                        )
                    )
                if isinstance(event, yaml.AliasEvent) or getattr(event, "anchor", None):
                    findings.append(
                        Finding(
                            severity="error",
                            code="yaml-anchor",
                            location=f"{pack_path}:{event.start_mark.line + 1}",
                            message=(
                                "YAML anchor/alias — reference expansion is "
                                "refused in packs (CORE-1453 DoS guard)."
                            ),
                        )
                    )
    except yaml.YAMLError as exc:
        findings.append(
            Finding(
                severity="error",
                code="yaml-parse",
                location=str(pack_path),
                message=f"Unparseable YAML: {exc}",
            )
        )
    return findings


def _load_mapping(pack_path: Path) -> dict[str, Any] | None:
    """safe_load *pack_path*; None when unparseable or not a mapping."""
    try:
        with open(pack_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def check_top_level_keys(pack_path: Path) -> list[Finding]:
    """Only keys declared by :class:`LanguagePackSchema` are allowed."""
    data = _load_mapping(pack_path)
    if data is None:
        return []  # check_yaml_data_only owns the parse failure
    return [
        Finding(
            severity="error",
            code="unknown-key",
            location=str(pack_path),
            message=(
                f"Unknown top-level key '{key}' — not part of the pack "
                "schema; packs are data, not code (CORE-1453)."
            ),
        )
        for key in data
        if key not in ALLOWED_TOP_LEVEL_KEYS
    ]


def _iter_metadata_strings(metadata: Mapping[str, Any]) -> list[tuple[str, str]]:
    """Flatten metadata into (field, string-value) pairs."""
    pairs: list[tuple[str, str]] = []
    for field, value in metadata.items():
        if isinstance(value, str):
            pairs.append((field, value))
        elif isinstance(value, list):
            pairs.extend((field, item) for item in value if isinstance(item, str))
    return pairs


def check_metadata_urls(pack_path: Path) -> list[Finding]:
    """URLs inside metadata strings must be http(s)."""
    data = _load_mapping(pack_path)
    if data is None:
        return []
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        return []
    findings: list[Finding] = []
    for field, value in _iter_metadata_strings(metadata):
        for scheme in find_disallowed_url_schemes(value):
            findings.append(
                Finding(
                    severity="error",
                    code="url-scheme",
                    location=f"{pack_path}#metadata.{field}",
                    message=(
                        f"URL scheme '{scheme}' in metadata.{field} — only "
                        "http(s) URLs are allowed in pack metadata "
                        "(CORE-1453)."
                    ),
                )
            )
    return findings


def enforce_file_contract(pack_path: Path) -> list[Finding]:
    """Run every file-level contract check on one pack file."""
    findings = check_file_size(pack_path)
    if findings:
        return findings  # don't parse a file that already failed the cap
    findings = check_yaml_data_only(pack_path)
    findings.extend(check_top_level_keys(pack_path))
    findings.extend(check_metadata_urls(pack_path))
    return findings


def _partition_items(pack: Mapping[str, Any] | Any, partition: str) -> dict[str, str]:
    """Partition mapping from a dict-like or attribute-style pack."""
    if isinstance(pack, Mapping):
        value = pack.get(partition)
    else:
        value = getattr(pack, partition, None)
    return dict(value) if value else {}


def check_map_roundtrip(pack: Mapping[str, Any] | Any, *, flat: bool) -> list[Finding]:
    """Render-vs-execute consistency: the map must invert byte-identically.

    For every canonical term ``en`` with localized surface ``loc``, the
    reverse map must restore exactly ``en`` (byte comparison, no
    normalization). That holds iff the mapping is a bijection over its
    scope, so two failure shapes exist:

    * two canonical terms sharing one localized surface (shadowing — the
      execute direction can only restore one of them);
    * one canonical term carrying two localized surfaces (the render
      direction is ambiguous, so loc→en→loc is not byte-identical) —
      EXCEPT for Python soft keywords (:data:`_PY_SOFT_KEYWORDS`): ``type``
      is both the 3.12 alias statement and a builtin, the engine
      dispatches the two roles contextually, and every shipped pack
      carries divergent surfaces for them by design. Both surfaces still
      reverse to the same canonical term, so en→loc→en stays
      byte-identical.

    ``flat=True`` merges the Python execution partitions into one scope
    (CPython tokenizes flat, CORE-710); ``flat=False`` checks each
    partition independently (member-bearing targets, where cross-partition
    homonyms are legal, CORE-1582).
    """
    scopes: list[tuple[str, tuple[str, ...]]] = (
        [("flat", _FLAT_PARTITIONS)] if flat else [(p, (p,)) for p in _ALL_PARTITIONS]
    )
    findings: list[Finding] = []
    for scope_name, partitions in scopes:
        forward: dict[str, tuple[str, str]] = {}  # en -> (loc, partition)
        inverse: dict[str, tuple[str, str]] = {}  # loc -> (en, partition)
        for partition in partitions:
            for en, loc in _partition_items(pack, partition).items():
                seen_loc = forward.get(en)
                if (
                    seen_loc is not None
                    and seen_loc[0] != loc
                    and en not in _PY_SOFT_KEYWORDS
                ):
                    findings.append(
                        Finding(
                            severity="error",
                            code="roundtrip",
                            location=f"{scope_name}:{en}",
                            message=(
                                f"'{en}' maps to '{seen_loc[0]}' "
                                f"({seen_loc[1]}) and '{loc}' ({partition}) — "
                                "render direction is ambiguous; the round "
                                "trip is not byte-identical (CORE-1453)."
                            ),
                        )
                    )
                    continue
                seen_en = inverse.get(loc)
                if seen_en is not None and seen_en[0] != en:
                    findings.append(
                        Finding(
                            severity="error",
                            code="roundtrip",
                            location=f"{scope_name}:{loc}",
                            message=(
                                f"'{loc}' is the surface for both "
                                f"'{seen_en[0]}' ({seen_en[1]}) and '{en}' "
                                f"({partition}) — execute direction cannot "
                                "restore the canonical form byte-identically "
                                "(CORE-1453)."
                            ),
                        )
                    )
                    continue
                forward[en] = (loc, partition)
                inverse[loc] = (en, partition)
    return findings
