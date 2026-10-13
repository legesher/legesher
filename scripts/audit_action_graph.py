#!/usr/bin/env python3
"""Walk the transitive GitHub Actions graph and fail on any unpinned reference.

zizmor's ``unpinned-uses`` audit covers every ``uses:`` line in files we own.
What it cannot do is look *inside* a third party's composite action. Given
``pre-commit/action`` pinned to a full SHA, whose own ``action.yml`` carries an
unpinned ``actions/cache@v4``, zizmor reports nothing — confirmed against
v1.29.0 both offline and online on 2026-08-16.

That blind spot is not hypothetical. It is exactly the shape that took
``Lint & Validate`` down on every run of this repository and needed CORE-1926 to
fix, while the pinning gate reported green the entire time. A gate that is
silent about the failure we actually had is the one worth building (CORE-1922).

Only composite actions can nest others — JavaScript and Docker actions declare
a single entry point — so ``using: composite`` is the only shape to walk.

A pinned SHA is immutable, so a reference that resolves clean once cannot rot.
This is therefore a *change-triggered* check: it belongs on ``.github/**``
diffs, not on every commit.

Exit codes are three-valued on purpose. A walk that could not reach the network
is **not** a pass — reporting "clean" for a graph it never read is the failure
mode this script exists to prevent.

    0   every reference is SHA-pinned, at every depth
    1   at least one unpinned reference
    2   the walk could not be completed (no network, no token, API refusal)

Usage:

    uv run python scripts/audit_action_graph.py                 # .github/workflows
    uv run python scripts/audit_action_graph.py path/to/wf.yml  # specific files
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable, Iterable, Iterator

import yaml

FULL_SHA = re.compile(r"^[0-9a-f]{40}$")

#: Returns the file's text, or None when the repository has no such file at
#: that ref (a 404 — an action with no ``action.yml`` is a normal leaf, not a
#: failure). Raises :class:`FetchError` for anything that means "we did not
#: find out", which must never be mistaken for "nothing there".
Fetcher = Callable[[str, str, str], "str | None"]


class FetchError(RuntimeError):
    """The walk could not be completed, as distinct from finding nothing."""


@dataclass(frozen=True)
class Ref:
    """A parsed ``uses:`` value: ``owner/repo[/subpath]@version``."""

    owner: str
    repo: str
    subpath: str
    version: str

    @property
    def pinned(self) -> bool:
        return bool(FULL_SHA.match(self.version))

    @property
    def slug(self) -> str:
        path = f"/{self.subpath}" if self.subpath else ""
        return f"{self.owner}/{self.repo}{path}@{self.version}"

    def manifest_paths(self) -> list[str]:
        """Where this action's manifest lives, most likely spelling first.

        A reusable *workflow* is referenced by its own path and is already the
        file we want; an *action* is a directory containing ``action.yml``.
        """
        base = self.subpath
        if base.endswith((".yml", ".yaml")):
            return [base]
        prefix = f"{base}/" if base else ""
        return [f"{prefix}action.yml", f"{prefix}action.yaml"]


@dataclass(frozen=True)
class Violation:
    """An unpinned reference, and the chain of pins that led to it."""

    ref: str
    chain: tuple[str, ...]

    def render(self) -> str:
        head = f"{self.chain[0]}: not SHA-pinned -> {self.ref}"
        if len(self.chain) == 1:
            return head
        # chain[0] is already named above; only the pins between it and the
        # violation belong on the `via` lines.
        return head + "\n      via " + "\n      via ".join(self.chain[1:])


def parse_ref(value: str) -> Ref | None:
    """Parse a ``uses:`` value, or return None when there is nothing to pin.

    ``./``-relative and ``docker://`` references resolve outside the Actions
    marketplace, so they have no tag to repoint and no manifest to walk.
    """
    value = value.strip()
    if not value or value.startswith(("./", ".\\", "docker://")):
        return None
    path, sep, version = value.partition("@")
    if not sep:
        # A marketplace reference with no version at all. Unpinned by
        # definition, and there is no ref to fetch a manifest at.
        parts = path.split("/")
        if len(parts) < 2:
            return None
        return Ref(parts[0], parts[1], "/".join(parts[2:]), "")
    parts = path.split("/")
    if len(parts) < 2:
        return None
    return Ref(parts[0], parts[1], "/".join(parts[2:]), version)


def iter_uses(document: object) -> Iterator[str]:
    """Yield every ``uses:`` string anywhere in a parsed YAML document.

    Deliberately schema-agnostic. Workflows carry them at
    ``jobs.<id>.steps[].uses`` and ``jobs.<id>.uses``; composite actions at
    ``runs.steps[].uses``. Walking structurally covers all three, and any
    shape GitHub adds later, without a schema to keep current.
    """
    if isinstance(document, dict):
        for key, value in document.items():
            if key == "uses" and isinstance(value, str):
                yield value
            else:
                yield from iter_uses(value)
    elif isinstance(document, list):
        for item in document:
            yield from iter_uses(item)


def gh_fetch(owner_repo: str, path: str, ref: str) -> str | None:
    """Fetch a file's raw text via ``gh api``.

    ``gh`` is already the authenticated path in this repo's tooling, so this
    avoids both a new dependency and a second place tokens can be configured.
    """
    result = subprocess.run(
        [
            "gh",
            "api",
            "-H",
            "Accept: application/vnd.github.raw",
            f"repos/{owner_repo}/contents/{path}?ref={ref}",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout
    stderr = result.stderr.lower()
    if "404" in stderr or "not found" in stderr:
        return None
    raise FetchError(
        f"gh api failed for {owner_repo}/{path}@{ref}: {result.stderr.strip()}"
    )


def _manifest_for(ref: Ref, fetch: Fetcher) -> str | None:
    for candidate in ref.manifest_paths():
        text = fetch(f"{ref.owner}/{ref.repo}", candidate, ref.version)
        if text is not None:
            return text
    return None


def walk(
    seeds: Iterable[tuple[str, str]],
    fetch: Fetcher,
) -> list[Violation]:
    """Resolve *seeds* and everything they pull in, reporting unpinned refs.

    *seeds* are ``(origin_label, uses_value)`` pairs — the origin is carried
    only so a violation can say which of our files started the chain.

    Verified SHAs are memoised: content at a SHA is immutable, so a reference
    resolved once in this run never needs fetching again.
    """
    violations: list[Violation] = []
    seen: set[str] = set()
    queue: list[tuple[Ref, tuple[str, ...]]] = []

    for origin, value in seeds:
        ref = parse_ref(value)
        if ref is None:
            continue
        if not ref.pinned:
            violations.append(Violation(value, (origin,)))
            continue
        queue.append((ref, (origin,)))

    while queue:
        ref, chain = queue.pop()
        if ref.slug in seen:
            continue
        seen.add(ref.slug)

        manifest = _manifest_for(ref, fetch)
        if manifest is None:
            # No manifest at this ref: a Docker or JavaScript action whose
            # file we could not name, or a path that is not an action at all.
            # Neither can nest another action, so the branch ends here.
            continue

        document = yaml.safe_load(manifest)
        if not isinstance(document, dict):
            continue

        runs = document.get("runs")
        is_composite = isinstance(runs, dict) and runs.get("using") == "composite"
        is_workflow = "jobs" in document
        if not (is_composite or is_workflow):
            # A JavaScript or Docker action. It declares one entry point and
            # cannot reference another action, so there is nothing to walk.
            continue

        for value in iter_uses(document):
            nested = parse_ref(value)
            if nested is None:
                continue
            if not nested.pinned:
                violations.append(Violation(value, chain + (ref.slug,)))
                continue
            queue.append((nested, chain + (ref.slug,)))

    return violations


def collect_seeds(paths: Iterable[Path]) -> list[tuple[str, str]]:
    seeds: list[tuple[str, str]] = []
    for path in paths:
        try:
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise FetchError(f"{path}: not parseable as YAML: {exc}") from exc
        for value in iter_uses(document):
            seeds.append((str(path), value))
    return seeds


def default_paths(root: Path) -> list[Path]:
    workflows = sorted(
        p
        for pattern in ("*.yml", "*.yaml")
        for p in (root / ".github" / "workflows").glob(pattern)
    )
    actions = sorted(
        p
        for pattern in ("action.yml", "action.yaml")
        for p in (root / ".github" / "actions").rglob(pattern)
    )
    return workflows + actions


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Fail on any unpinned GitHub Actions reference, including "
        "references nested inside a third party's composite action."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="workflow or action files; defaults to .github/workflows and .github/actions",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="repository root used to discover default paths",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit findings as JSON rather than text",
    )
    args = parser.parse_args(argv)

    if args.paths:
        # A named path that is not there is a mistake, not an empty result.
        # Passing over it silently would be this script's own failure mode:
        # exiting 0 for files it never read.
        missing = [p for p in args.paths if not p.is_file()]
        if missing:
            print(
                "Not found: " + ", ".join(str(p) for p in missing),
                file=sys.stderr,
            )
            print("Refusing to report on files that were not read.", file=sys.stderr)
            return 2
        paths = list(args.paths)
    else:
        paths = default_paths(args.root)
        if not paths:
            # A repository with no workflows genuinely has nothing to pin.
            print("No workflow or action files found.")
            return 0

    try:
        seeds = collect_seeds(paths)
        violations = walk(seeds, gh_fetch)
    except FetchError as exc:
        # Exit 2, never 0. A walk that did not happen is not a clean walk.
        print(f"Could not complete the action-graph walk: {exc}", file=sys.stderr)
        print(
            "This is not a pass. Re-run with network access and an "
            "authenticated `gh`, or run this check in CI.",
            file=sys.stderr,
        )
        return 2

    if args.json:
        print(
            json.dumps(
                [{"ref": v.ref, "chain": list(v.chain)} for v in violations], indent=2
            )
        )
        return 1 if violations else 0

    if not violations:
        print(
            f"All action references are SHA-pinned transitively ({len(paths)} files)."
        )
        return 0

    print("GitHub Actions must be SHA-pinned, including inside composite actions.\n")
    for violation in violations:
        print(f"  {violation.render()}")
    print(
        "\nA `via` chain means the unpinned reference is inside a third party's\n"
        "composite action, not in our file. Pinning our own reference does not\n"
        "fix it — the job still dies at `Set up job`. Options: inline the action\n"
        "(as CORE-1926 did), or move to a release of it that pins its own deps.\n"
        "\nResolve a tag to its SHA with:\n"
        "    gh api repos/<owner>/<repo>/git/ref/tags/<tag> --jq .object.sha"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
