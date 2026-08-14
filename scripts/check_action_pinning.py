#!/usr/bin/env python3
"""Fail if any GitHub Actions `uses:` reference is not pinned to a full SHA.

The org-level "require actions to be pinned to a full-length commit SHA"
policy enforces this too, but only when a job is dispatched: every job dies
during "Set up job" before a line of project code runs, which reads like a CI
outage rather than a lint failure. This hook moves the failure onto the
laptop, where the message says what to do about it (2026-08-14).

A pinned reference looks like:

    uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6

The trailing `# v6` comment is convention, not requirement — it is what lets
Dependabot keep the pin current, so keep it when adding new actions.

Local `./`-relative and `docker://` references are exempt: neither resolves
through the Actions marketplace, so there is no tag to repoint.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# `uses:` value, ignoring surrounding quotes and any trailing comment.
USES = re.compile(r"^\s*-?\s*uses:\s*['\"]?([^'\"#\s]+)['\"]?")
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


def unpinned(path: Path) -> list[tuple[int, str]]:
    """Return (line_number, reference) for every unpinned `uses:` in *path*."""
    found: list[tuple[int, str]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = USES.match(line)
        if not match:
            continue
        ref = match.group(1)
        if ref.startswith("./") or ref.startswith("docker://"):
            continue
        _, sep, version = ref.partition("@")
        if not sep or not FULL_SHA.match(version):
            found.append((lineno, ref))
    return found


def main(argv: list[str]) -> int:
    failures: list[str] = []
    for name in argv:
        path = Path(name)
        if not path.is_file():
            continue
        for lineno, ref in unpinned(path):
            failures.append(f"{path}:{lineno}: not SHA-pinned -> {ref}")

    if not failures:
        return 0

    print("GitHub Actions must be pinned to a full 40-character commit SHA.\n")
    print("\n".join(failures))
    print(
        "\nResolve a tag to its SHA with:\n"
        "    gh api repos/<owner>/<repo>/git/ref/tags/<tag> --jq .object.sha\n"
        "then write it as:  uses: <owner>/<repo>@<sha> # <tag>\n"
        "\n(If the tag is annotated, dereference once more via\n"
        " gh api repos/<owner>/<repo>/git/tags/<sha> --jq .object.sha)"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
