"""Public-tree sweep guard (CORE-1992).

The repository ships whole when it goes public, and the publish gates that
protect the datasets do not read the source tree. This module is the general
form of the per-script checks: it reads every tracked text file once and fails
on the classes of private pointer that the pre-flip sweeps keep finding again
after generators and new documents reintroduce them.

- the names of the two private repositories whose names must never appear
  (the working-memory repo and the archive this tree was cut from); the
  organisation's other private repositories ride the external wordlist below,
  because a public test file is the wrong place to enumerate them,
- paths and URLs that descend into a personal GitHub account (a bare profile
  link is public credit and is allowed),
- issue-tracker and workspace URLs (plain ``CORE-###`` is the permitted form),
- personal email domains,
- tracked database files,
- and, when ``LEGESHER_SWEEP_WORDLIST`` names a file, every term listed in it,
  one per line, matched case-insensitively. The wordlist holds the names that
  must not appear in a public tree, so it lives outside the tree; without it
  that one check is skipped by name rather than passing vacuously.

The denied strings below are assembled from fragments so that this file
passes its own check and a plain ``git grep`` for any of them stays at zero.
"""

from __future__ import annotations

import functools
import os
import subprocess
from pathlib import Path, PurePosixPath

import pytest

WORDLIST_ENV = "LEGESHER_SWEEP_WORDLIST"

PRIVATE_REPO_NAMES: tuple[str, ...] = (
    "legesher-" + "brain",
    "legesher-" + "next",
)
PERSONAL_PATHS: tuple[str, ...] = (
    "madiedgar" + "/",
    "MadiEdgar" + "/",
)
TRACKER_URLS: tuple[str, ...] = (
    "linear." + "app/legesher",
    "notion." + "so/",
    "notion." + "site/",
    "claude.ai/" + "artifact",
    "claude.ai/code/" + "artifact",
)
PERSONAL_EMAIL_DOMAINS: tuple[str, ...] = (
    "@gmail" + ".",
    "@proton" + ".me",
    "@protonmail" + ".",
    "@hotmail" + ".",
    "@yahoo" + ".",
    "@icloud" + ".",
    "@outlook" + ".",
)
DATABASE_SUFFIXES = frozenset({".db", ".sqlite", ".sqlite3"})

#: Tracked files the text scan does not read: lockfiles and binary assets.
SKIP_SUFFIXES = frozenset(
    {
        ".lock",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".ico",
        ".svg",
        ".webp",
        ".woff",
        ".woff2",
        ".ttf",
        ".otf",
        ".whl",
        ".parquet",
        ".arrow",
        ".pdf",
        ".zip",
        ".gz",
    }
)
SKIP_NAMES = frozenset({"uv.lock", "pnpm-lock.yaml", "package-lock.json"})
MAX_SCAN_BYTES = 4 * 1024 * 1024


def _repo_root() -> Path:
    """The work tree containing this file; skips the module outside git."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=Path(__file__).resolve().parent,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        proc = None
    if proc is None or proc.returncode != 0:
        pytest.skip(
            "public-tree sweep needs a git work tree: `git rev-parse --show-toplevel`"
            " failed from the test directory",
            allow_module_level=True,
        )
    return Path(proc.stdout.strip())


REPO: Path = _repo_root()


def _tracked_files() -> tuple[str, ...]:
    out = subprocess.run(
        ["git", "-C", str(REPO), "ls-files", "-z"],
        capture_output=True,
        check=True,
    ).stdout
    return tuple(p.decode("utf-8") for p in out.split(b"\0") if p)


TRACKED = _tracked_files()


def _scannable(path: str) -> bool:
    posix = PurePosixPath(path)
    if posix.name in SKIP_NAMES or posix.suffix.lower() in SKIP_SUFFIXES:
        return False
    full = REPO / path
    try:
        return full.is_file() and full.stat().st_size <= MAX_SCAN_BYTES
    except OSError:
        return False


@functools.lru_cache(maxsize=None)
def _lines(path: str) -> list[str]:
    try:
        text = (REPO / path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return text.splitlines()


def _hits(needles: tuple[str, ...], *, fold_case: bool = False) -> list[str]:
    """``path:line: needle`` for every tracked text line containing a needle."""
    found: list[str] = []
    probes = tuple(n.lower() for n in needles) if fold_case else needles
    for path in TRACKED:
        if not _scannable(path):
            continue
        for number, line in enumerate(_lines(path), start=1):
            haystack = line.lower() if fold_case else line
            for needle, probe in zip(needles, probes, strict=True):
                if probe in haystack:
                    found.append(f"{path}:{number}: {needle}")
    return found


def _assert_clean(hits: list[str], what: str) -> None:
    assert not hits, f"{what} in tracked files:\n  " + "\n  ".join(hits)


def test_no_private_repository_names() -> None:
    """The private working-memory and archive repositories are never named."""
    _assert_clean(_hits(PRIVATE_REPO_NAMES), "private repository names")


def test_no_personal_github_paths() -> None:
    """No path or URL descends into a personal GitHub account's repositories."""
    _assert_clean(_hits(PERSONAL_PATHS), "personal GitHub paths")


def test_no_tracker_or_workspace_urls() -> None:
    """Tickets are cited as plain identifiers, never as workspace links."""
    _assert_clean(_hits(TRACKER_URLS), "tracker or workspace URLs")


def test_no_personal_email_domains() -> None:
    """Contact addresses are role aliases or noreply addresses."""
    _assert_clean(_hits(PERSONAL_EMAIL_DOMAINS, fold_case=True), "personal email addresses")


def test_no_tracked_database_files() -> None:
    """A tracked database is the unredacted superset of whatever it exports."""
    tracked = [p for p in TRACKED if PurePosixPath(p).suffix.lower() in DATABASE_SUFFIXES]
    _assert_clean(tracked, "database files")


def test_no_wordlist_terms() -> None:
    """Every term in the external wordlist is absent, case-insensitively."""
    wordlist: str = os.environ.get(WORDLIST_ENV, "")
    if not wordlist:
        pytest.skip(f"{WORDLIST_ENV} is unset; the private wordlist check did not run")
    terms = tuple(
        line.strip()
        for line in Path(wordlist).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    assert terms, f"{WORDLIST_ENV} names an empty wordlist"
    _assert_clean(_hits(terms, fold_case=True), "wordlist terms")
