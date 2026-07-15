#!/usr/bin/env python3
"""Refresh the vendored IANA Language Subtag Registry snapshot.

CORE-1500. :mod:`legesher_i18n.bcp47` validates locale tags against the IANA
Language Subtag Registry — the normative subtag list behind BCP 47 (RFC 5646).
Validation must be *offline and deterministic*: CI, the pack gate, and the
language-registry drift test cannot depend on a network fetch. So the registry
is vendored as a trimmed, git-tracked TSV snapshot and refreshed by hand with
this script.

The upstream file is a ~730 KB record-jar document with prose descriptions and
per-record change history. We keep only the fields the validator actually
decides on:

    type, subtag, scope, suppress_script, deprecated, preferred_value,
    macrolanguage, description

Everything else (Added, Comments, extra Descriptions) is dropped.

Refresh cadence: IANA publishes updates a few times a year. Re-run this script,
inspect the diff (a subtag going ``Deprecated`` is the interesting case), and
commit. ``tests/test_bcp47.py`` pins the snapshot's ``File-Date`` header, its
record count, **and a SHA-256 of its data rows**, so a partial refresh cannot
pass CI on the strength of an intact header. This script refuses to write a
materially smaller snapshot for the same reason (see :data:`MIN_RECORD_RATIO`).

Usage:
    uv run python libs/i18n/legesher_i18n/scripts/refresh_iana_subtags.py
    uv run python .../refresh_iana_subtags.py --force   # accept a shrunken registry
"""

from __future__ import annotations

import sys
import urllib.request
from collections.abc import Sequence
from pathlib import Path

REGISTRY_URL = (
    "https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry"
)

SCRIPT_DIR = Path(__file__).resolve().parent
I18N_PKG = SCRIPT_DIR.parent
SNAPSHOT = I18N_PKG / "data" / "iana-language-subtag-registry.tsv"

# Record types we retain. The validator resolves only ``language``, ``script``,
# ``region``, and ``variant`` — those are the four positions RFC 5646 allows in a
# Legesher key, and the only types ``bcp47._lookup()`` is ever called with.
#
# ``extlang``, ``grandfathered``, and ``redundant`` are kept as *evidence*, not as
# lookup tables: they are how a reviewer checks, offline, that a proposed tag like
# ``zh-Hans`` or ``sr-Cyrl`` is a registered, non-deprecated tag form (the registry
# files those under ``redundant``, with no ``Preferred-Value``). Legacy tags are
# rejected structurally, not by consulting these rows — ``no-bok`` never reaches a
# registry lookup because ``bcp47.parse()`` rejects its extlang shape first.
KEPT_TYPES = frozenset(
    {"language", "extlang", "script", "region", "variant", "grandfathered", "redundant"}
)

# A refresh must never *shrink* the registry. IANA adds subtags and deprecates
# them in place; it does not delete records. So a materially smaller snapshot means
# a truncated fetch, not an upstream change — and truncation is silent by default:
# ``File-Date`` is the first line, so a short read keeps the pinned date intact
# while ``is_valid("zh-Hant")`` quietly becomes False. Refuse to write it.
MIN_RECORD_RATIO = 0.99

COLUMNS = (
    "type",
    "subtag",
    "scope",
    "suppress_script",
    "deprecated",
    "preferred_value",
    "macrolanguage",
    "description",
)

_TIMEOUT_SECONDS = 60


def fetch_registry(url: str = REGISTRY_URL) -> str:
    """Download the IANA registry as text.

    Args:
        url: Registry URL. Overridable for testing; defaults to the IANA one.

    Returns:
        The raw registry document (UTF-8 decoded).
    """
    if not url.startswith("https://"):
        raise ValueError(f"registry URL must be https://, got {url!r}")
    # B310: the scheme is pinned to https:// on the line above, so this cannot be
    # coerced into a file:// or custom-scheme read.
    with urllib.request.urlopen(url, timeout=_TIMEOUT_SECONDS) as response:  # nosec B310
        # urlopen follows redirects, and a redirect may downgrade the scheme —
        # the pin above only covers the URL we *asked* for.
        final_url = response.url or url
        if not final_url.startswith("https://"):
            raise ValueError(
                f"registry fetch was redirected off https:// (landed on {final_url!r})"
            )
        return response.read().decode("utf-8")


def parse_records(text: str) -> tuple[str, list[dict[str, list[str]]]]:
    """Parse the record-jar document into a file-date plus a list of records.

    The format (RFC 5646 section 3.1.1) separates records with a ``%%`` line and
    folds long field values onto continuation lines that start with whitespace.
    A field may repeat (notably ``Description``), so values are collected into
    lists.

    Args:
        text: The raw registry document.

    Returns:
        Tuple of (``File-Date`` value, records). Each record maps a field name
        to its list of values.

    Raises:
        ValueError: If the document carries no ``File-Date`` header.
    """
    file_date = ""
    records: list[dict[str, list[str]]] = []

    for block in text.split("\n%%\n"):
        # Unfold continuation lines before splitting fields.
        unfolded: list[str] = []
        for line in block.split("\n"):
            if line[:1] in (" ", "\t") and unfolded:
                unfolded[-1] += " " + line.strip()
            elif line.strip():
                unfolded.append(line)

        record: dict[str, list[str]] = {}
        for line in unfolded:
            field, separator, value = line.partition(":")
            if not separator:
                continue
            record.setdefault(field.strip(), []).append(value.strip())

        if "File-Date" in record:
            file_date = record["File-Date"][0]
        if "Type" in record:
            records.append(record)

    if not file_date:
        raise ValueError("registry document has no File-Date header")
    return file_date, records


def _escape(value: str) -> str:
    """Make a value safe for a TSV cell (no tabs, no line breaks of any kind)."""
    return value.replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()


def render_snapshot(file_date: str, records: list[dict[str, list[str]]]) -> str:
    """Render the trimmed TSV snapshot.

    Args:
        file_date: The registry's ``File-Date``, preserved as a comment header
            so the snapshot's provenance is auditable.
        records: Parsed registry records.

    Returns:
        The TSV document, ready to write.
    """
    lines = [
        "# IANA Language Subtag Registry — trimmed snapshot (BCP 47 / RFC 5646).",
        f"# File-Date: {file_date}",
        f"# Source: {REGISTRY_URL}",
        "# AUTO-GENERATED. Refresh with:",
        "#   uv run python libs/i18n/legesher_i18n/scripts/refresh_iana_subtags.py",
        "\t".join(COLUMNS),
    ]

    for record in records:
        record_type = record["Type"][0]
        if record_type not in KEPT_TYPES:
            continue
        # grandfathered/redundant records are keyed by ``Tag``; the rest by ``Subtag``.
        key = (record.get("Subtag") or record.get("Tag") or [""])[0]
        if not key:
            continue
        lines.append(
            "\t".join(
                _escape(value)
                for value in (
                    record_type,
                    key,
                    (record.get("Scope") or [""])[0],
                    (record.get("Suppress-Script") or [""])[0],
                    (record.get("Deprecated") or [""])[0],
                    (record.get("Preferred-Value") or [""])[0],
                    (record.get("Macrolanguage") or [""])[0],
                    (record.get("Description") or [""])[0],
                )
            )
        )

    return "\n".join(lines) + "\n"


class TruncatedRegistryError(RuntimeError):
    """The fetched registry has materially fewer records than the vendored one."""


def snapshot_record_count(snapshot: str) -> int:
    """Count the data rows in a rendered snapshot.

    Comments and the column header are not data. Counting rows — rather than
    trusting the ``File-Date`` comment — is what makes a truncated document
    detectable at all.

    Args:
        snapshot: A rendered TSV snapshot (or the vendored file's contents).

    Returns:
        The number of subtag records in *snapshot*.
    """
    return sum(
        1
        for line in snapshot.splitlines()
        if line and not line.startswith("#") and not line.startswith("type\t")
    )


def check_not_truncated(
    new_count: int, previous_count: int, ratio: float = MIN_RECORD_RATIO
) -> None:
    """Refuse a refresh that would materially shrink the vendored snapshot.

    Args:
        new_count: Record count of the snapshot about to be written.
        previous_count: Record count of the snapshot on disk.
        ratio: The floor, as a fraction of *previous_count*.

    Raises:
        TruncatedRegistryError: If *new_count* falls below the floor.
    """
    floor = int(previous_count * ratio)
    if new_count < floor:
        raise TruncatedRegistryError(
            f"the fetched registry has {new_count} records, but the vendored "
            f"snapshot has {previous_count} (floor: {floor}). IANA does not delete "
            f"subtag records, so this is almost certainly a truncated or failed "
            f"fetch. Nothing was written. Re-run, and pass --force only if you have "
            f"confirmed upstream really did shrink."
        )


def main(argv: Sequence[str] | None = None) -> int:
    """Fetch the registry and rewrite the vendored snapshot."""
    args = list(sys.argv[1:] if argv is None else argv)
    force = "--force" in args

    print(f"Fetching {REGISTRY_URL} ...")
    try:
        text = fetch_registry()
    except OSError as exc:  # URLError and friends all subclass OSError
        print(f"error: could not fetch the IANA registry: {exc}", file=sys.stderr)
        return 1

    file_date, records = parse_records(text)
    snapshot = render_snapshot(file_date, records)
    kept = snapshot_record_count(snapshot)

    if SNAPSHOT.exists():
        previous = snapshot_record_count(SNAPSHOT.read_text(encoding="utf-8"))
        try:
            check_not_truncated(kept, previous)
        except TruncatedRegistryError as exc:
            if not force:
                print(f"error: {exc}", file=sys.stderr)
                return 1
            print(f"warning (--force): {exc}", file=sys.stderr)

    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(snapshot, encoding="utf-8")

    print(f"File-Date: {file_date}")
    print(f"Wrote {kept} subtag records to {SNAPSHOT}")
    print(
        "The snapshot's File-Date, record count, and content digest are all pinned in "
        "tests/test_bcp47.py. Run the suite; it will print the new values to paste in."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
