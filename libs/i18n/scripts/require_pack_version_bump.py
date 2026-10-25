#!/usr/bin/env python3
"""Refuse a pack content change that does not move the pack's version.

For a language pack, the content IS the API. A consumer who pins
``legesher-i18n-python-ar==0.0.4`` is pinning a vocabulary, so shipping two
different vocabularies under one version is the same class of breakage as
changing a function signature without a major bump -- except silent, because
nothing about the install looks different.

Nothing enforced this until now. The `while` correction (CORE-1655's origin)
changed Arabic pack content while `pyproject.toml` stayed at 0.0.4.

Two properties, not one
-----------------------
The obvious rule -- "content changed, so the version must change" -- is half
of it, and the missing half is how 50 of 51 packs ended up declaring two
different versions (CORE-2058). Each pack states its version twice, and a bump
that moves only ``pyproject.toml`` satisfies "the version changed" while
leaving ``__init__.py`` behind. So:

1. **Moved** -- the pack's ``pyproject.toml`` version differs from HEAD
2. **Agreed** -- ``pyproject.toml`` and ``__init__.py:__version__`` state the
   same version after the change

Property 2 is checked on every pack the commit touches whether or not its
content moved, because a commit editing only the version files can desync them
just as easily as one editing YAML.

A third copy the gate does NOT own
----------------------------------
``uv.lock`` also records every pack's version, so a bump leaves it stale until
uv regenerates it. That is not checked here: uv rewrites the lock on its next
run, and the hooks in this repo invoke ``uv run``, so it heals as a side effect
rather than staying wrong. Worth knowing when a bump shows up as an unstaged
``uv.lock`` change -- stage it, it is not spurious.

Why a pre-commit hook and not CI
--------------------------------
The failure this prevents is a commit that looks complete. Catching it after
the fact means a published version already means two things, and the repair is
a third version rather than an amendment. Locally it is one more line in the
commit you are already writing.

Usage:
    python scripts/require_pack_version_bump.py <staged pack files>
    python scripts/require_pack_version_bump.py --fix <staged pack files>
    python scripts/require_pack_version_bump.py --all

``--fix`` applies the patch bump to both files, so a regeneration touching every
pack is one command rather than one hand edit per pack. ``--all`` checks property 2
across the whole tree, ignoring git state -- the repo-wide invariant, which the
test suite runs.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_I18N_ROOT = _SCRIPT_DIR.parent
PACKS_ROOT = _I18N_ROOT / "language-packs"

#: A pack's content lives under ``<target>/<locale>/<package>/packs/*.yml``.
#: Anchored on the ``packs`` directory rather than "any yml under the locale",
#: so a README or a style guide sitting beside it does not demand a version
#: bump it has no business demanding.
PACK_CONTENT = re.compile(
    r"libs/i18n/language-packs/(?P<target>[^/]+)/(?P<locale>[^/]+)/[^/]+/packs/[^/]+\.yml$"
)

VERSION_IN_PYPROJECT = re.compile(r'^version\s*=\s*"(?P<version>[^"]+)"', re.M)
VERSION_IN_INIT = re.compile(r'^__version__\s*=\s*"(?P<version>[^"]+)"', re.M)


class PackVersionError(Exception):
    """A pack's versions are missing, unreadable, or disagree."""


def pack_dir(target: str, locale: str) -> Path:
    return PACKS_ROOT / target / locale


def _read(path: Path, pattern: re.Pattern[str], label: str) -> str:
    if not path.exists():
        raise PackVersionError(f"{path} does not exist, so {label} is unreadable")
    match = pattern.search(path.read_text(encoding="utf-8"))
    if not match:
        raise PackVersionError(f"{path} declares no {label}")
    return match.group("version")


def declared_versions(target: str, locale: str) -> tuple[str, str]:
    """Return ``(pyproject_version, init_version)`` for one pack."""
    root = pack_dir(target, locale)
    pyproject = root / "pyproject.toml"
    package = f"legesher_i18n_{target}_{locale}"
    init = root / package / "__init__.py"
    return (
        _read(pyproject, VERSION_IN_PYPROJECT, "[project] version"),
        _read(init, VERSION_IN_INIT, "__version__"),
    )


def version_at_head(target: str, locale: str) -> str | None:
    """Return the pack's committed ``pyproject.toml`` version, or None.

    None means "no committed version to compare against" -- a new pack, or a
    repository with no HEAD. Neither is a violation: a pack cannot fail to bump
    a version it did not have.
    """
    rel = f"libs/i18n/language-packs/{target}/{locale}/pyproject.toml"
    result = subprocess.run(
        ["git", "show", f"HEAD:{rel}"],
        capture_output=True,
        text=True,
        cwd=_I18N_ROOT.parent.parent,
    )
    if result.returncode != 0:
        return None
    match = VERSION_IN_PYPROJECT.search(result.stdout)
    return match.group("version") if match else None


def bump_patch(version: str) -> str:
    """Return ``version`` with its patch component incremented."""
    parts = version.split(".")
    # Zero-padding is rejected as well as non-numeric components, because
    # `2026.08.24` passes "three integers" and is a DATE. Bumping it yields
    # 2026.08.25 -- a plausible-looking number nobody chose, on an artifact
    # that just moved off date-based versioning. A refusal naming the file is
    # the better failure.
    if (
        len(parts) != 3
        or not all(p.isdigit() for p in parts)
        or any(p != str(int(p)) for p in parts)
    ):
        raise PackVersionError(
            f"{version!r} is not major.minor.patch, so it cannot be bumped "
            f"automatically -- set the intended version by hand"
        )
    major, minor, patch = (int(p) for p in parts)
    return f"{major}.{minor}.{patch + 1}"


def write_version(target: str, locale: str, version: str) -> None:
    """Set both declarations for one pack to ``version``."""
    root = pack_dir(target, locale)
    package = f"legesher_i18n_{target}_{locale}"
    for path, pattern, replacement in (
        (root / "pyproject.toml", VERSION_IN_PYPROJECT, f'version = "{version}"'),
        (root / package / "__init__.py", VERSION_IN_INIT, f'__version__ = "{version}"'),
    ):
        text = path.read_text(encoding="utf-8")
        match = pattern.search(text)
        if not match:
            raise PackVersionError(f"{path} declares no version to rewrite")
        path.write_text(
            text[: match.start()] + replacement + text[match.end() :],
            encoding="utf-8",
        )


def _normalised(raw: str) -> str:
    """A root-relative path with forward slashes, as pre-commit passes them."""
    return raw.replace("\\", "/").removeprefix("./")


def _differing_from_head(paths: list[str]) -> set[str] | None:
    """Return the subset of ``paths`` whose content differs from HEAD.

    ``paths`` are root-relative with forward slashes (see ``_normalised``),
    which is both what git takes as a pathspec here and what ``-z`` prints
    back unquoted, non-ASCII locale directories included. None means git
    could not answer: no HEAD yet (a fresh repository) or any other git
    failure. The caller then counts every path, the conservative reading.
    """
    result = subprocess.run(
        ["git", "diff", "--name-only", "-z", "HEAD", "--", *paths],
        capture_output=True,
        text=True,
        cwd=_I18N_ROOT.parent.parent,
    )
    if result.returncode != 0:
        return None
    return {name for name in result.stdout.split("\0") if name}


def content_paths(paths: list[str]) -> dict[str, tuple[str, str]]:
    """Map each pack-content path in ``paths`` to its ``(target, locale)``.

    Pure: this is the trigger pattern alone, with no look at git.
    """
    content: dict[str, tuple[str, str]] = {}
    for raw in paths:
        path = _normalised(raw)
        match = PACK_CONTENT.search(path)
        if match:
            content[path] = (match.group("target"), match.group("locale"))
    return content


def changed_packs(paths: list[str]) -> set[tuple[str, str]]:
    """Return the ``(target, locale)`` pairs whose CONTENT changed.

    Only a path whose content differs from HEAD counts. At commit time
    pre-commit hands the hook the staged files, with unstaged edits stashed,
    so a staged change differs from HEAD and counts. Under ``--all-files``,
    which CI runs, it hands over every tracked pack file, unchanged; reading
    each as changed content made the gate refuse every pack on every run.
    """
    content = content_paths(paths)
    if not content:
        return set()
    differing = _differing_from_head(list(content))
    if differing is None:
        return set(content.values())
    return {pair for path, pair in content.items() if path in differing}


def all_packs() -> list[tuple[str, str]]:
    """Every ``(target, locale)`` pairing carrying a pyproject in the tree."""
    pairs = []
    for target_dir in sorted(p for p in PACKS_ROOT.iterdir() if p.is_dir()):
        for locale_dir in sorted(p for p in target_dir.iterdir() if p.is_dir()):
            if (locale_dir / "pyproject.toml").exists():
                pairs.append((target_dir.name, locale_dir.name))
    return pairs


def check_agreement(pairs: list[tuple[str, str]]) -> list[str]:
    """Return a problem line per pack whose two declarations disagree."""
    problems = []
    for target, locale in pairs:
        try:
            pyproject_version, init_version = declared_versions(target, locale)
        except PackVersionError as exc:
            problems.append(f"  {locale}: {exc}")
            continue
        if pyproject_version != init_version:
            problems.append(
                f"  {locale}: pyproject.toml says {pyproject_version}, "
                f"__init__.py says {init_version}"
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="staged files, from pre-commit")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="bump the patch version of every pack whose content changed",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="check version agreement across every pack, ignoring git state",
    )
    args = parser.parse_args(argv)

    if args.all:
        problems = check_agreement(all_packs())
        if problems:
            print(
                "Packs declaring two different versions:\n"
                + "\n".join(problems)
                + "\n\npyproject.toml is authoritative. Raise __init__.py to "
                + "match it.",
                file=sys.stderr,
            )
            return 1
        return 0

    packs = sorted(changed_packs(args.paths))
    if not packs:
        return 0

    if args.fix:
        for target, locale in packs:
            pyproject_version, _ = declared_versions(target, locale)
            head = version_at_head(target, locale)
            # Already moved by hand: align the pair, do not bump a second time.
            target_version = (
                pyproject_version
                if head is not None and pyproject_version != head
                else bump_patch(pyproject_version)
            )
            write_version(target, locale, target_version)
            print(f"{locale}: {pyproject_version} -> {target_version}")
        return 0

    stale = []
    for target, locale in packs:
        head = version_at_head(target, locale)
        if head is None:
            continue
        pyproject_version, _ = declared_versions(target, locale)
        if pyproject_version == head:
            stale.append(f"  {locale}: content changed, still {pyproject_version}")

    # Agreement is checked on every touched pack, not only the stale ones: a
    # commit that edits the version files alone can desync them too.
    problems = check_agreement(packs)

    if not stale and not problems:
        return 0

    message = ["Pack version gate failed.\n"]
    if stale:
        message.append(
            "These packs changed content without changing their version. For a "
            "language pack the content is the API, so two vocabularies would "
            "ship under one version:\n" + "\n".join(stale)
        )
    if problems:
        message.append(
            "\nThese packs declare two different versions (pyproject.toml is "
            "authoritative):\n" + "\n".join(problems)
        )
    message.append(
        "\nFix both with:\n"
        "  uv run python libs/i18n/scripts/require_pack_version_bump.py --fix "
        + " ".join(f"'{p}'" for p in args.paths[:3])
        + (" ..." if len(args.paths) > 3 else "")
    )
    print("\n".join(message), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
