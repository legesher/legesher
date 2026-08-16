"""The action-graph walk must see what zizmor structurally cannot (CORE-1922).

The case that matters is CORE-1926: ``pre-commit/action`` pinned to a full SHA,
whose own ``action.yml`` carries an unpinned ``actions/cache@v4``. Every gate we
had reported green while that reference took ``Lint & Validate`` down on every
run. zizmor v1.29.0 does not report it either, offline or online.

The fetcher is injected throughout, so these run offline and deterministically.
One opt-in test hits the real API to confirm the fixture still matches
upstream; it is skipped by default rather than making the suite need a network.

Run with:  uv run pytest scripts/tests -q
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from audit_action_graph import (  # noqa: E402
    FetchError,
    collect_seeds,
    iter_uses,
    main,
    parse_ref,
    walk,
)

PINNED = "a" * 40
OTHER_PINNED = "b" * 40

#: The real shape of the action that caused CORE-1926: itself correctly
#: pinned, pulling in a reference that is not.
PRE_COMMIT_ACTION_YML = """
name: pre-commit
runs:
  using: composite
  steps:
    - uses: actions/cache@v4
      with:
        path: ~/.cache/pre-commit
"""

JS_ACTION_YML = """
name: setup-node
runs:
  using: node20
  main: dist/index.js
"""


def fetcher(files: dict[tuple[str, str], str]):
    """Build a Fetcher over ``{(owner_repo, path): text}``.

    Anything absent is a 404 — a normal leaf, not a failure.
    """

    def fetch(owner_repo: str, path: str, ref: str) -> str | None:
        return files.get((owner_repo, path))

    return fetch


class TestParseRef:
    @pytest.mark.parametrize(
        "value",
        ["./.github/actions/local", "docker://alpine:3", ".\\windows\\style", ""],
    )
    def test_references_with_nothing_to_pin_are_skipped(self, value: str) -> None:
        """Local and Docker references resolve outside the marketplace, so
        there is no tag to repoint and no manifest to walk."""
        assert parse_ref(value) is None

    def test_a_sha_is_pinned_and_a_tag_is_not(self) -> None:
        assert parse_ref(f"actions/checkout@{PINNED}").pinned
        assert not parse_ref("actions/checkout@v4").pinned

    def test_a_subpath_action_keeps_its_path(self) -> None:
        ref = parse_ref(f"github/codeql-action/analyze@{PINNED}")
        assert (ref.owner, ref.repo, ref.subpath) == (
            "github",
            "codeql-action",
            "analyze",
        )
        assert ref.manifest_paths()[0] == "analyze/action.yml"

    def test_a_bare_reference_with_no_version_is_unpinned(self) -> None:
        """`uses: actions/checkout` with no `@` at all still fails the gate."""
        ref = parse_ref("actions/checkout")
        assert ref is not None and not ref.pinned

    def test_a_reusable_workflow_is_fetched_at_its_own_path(self) -> None:
        ref = parse_ref(f"org/repo/.github/workflows/ci.yml@{PINNED}")
        assert ref.manifest_paths() == [".github/workflows/ci.yml"]


class TestIterUses:
    def test_it_finds_uses_at_every_workflow_position(self) -> None:
        """Steps, job-level reusable workflows and composite steps all count,
        which is why the walk is structural rather than schema-driven."""
        document = {
            "jobs": {
                "a": {"steps": [{"uses": "one@x"}, {"run": "echo"}]},
                "b": {"uses": "two@y"},
            },
            "runs": {"using": "composite", "steps": [{"uses": "three@z"}]},
        }
        assert set(iter_uses(document)) == {"one@x", "two@y", "three@z"}

    def test_a_non_string_uses_is_ignored(self) -> None:
        assert list(iter_uses({"uses": {"not": "a string"}})) == []


class TestWalk:
    def test_an_unpinned_reference_in_our_own_file_is_reported(self) -> None:
        violations = walk([("ci.yml", "actions/checkout@v4")], fetcher({}))
        assert [v.ref for v in violations] == ["actions/checkout@v4"]
        assert violations[0].chain == ("ci.yml",)

    def test_the_core_1926_case_the_whole_script_exists_for(self) -> None:
        """Our reference is correctly pinned; the one inside it is not.

        This is the exact shape that took `Lint & Validate` down while every
        gate reported green.
        """
        violations = walk(
            [("ci.yml", f"pre-commit/action@{PINNED}")],
            fetcher({("pre-commit/action", "action.yml"): PRE_COMMIT_ACTION_YML}),
        )

        assert len(violations) == 1, "the nested unpinned reference was not seen"
        assert violations[0].ref == "actions/cache@v4"
        assert violations[0].chain == ("ci.yml", f"pre-commit/action@{PINNED}")
        rendered = violations[0].render()
        assert "via" in rendered, (
            "a nested violation must say it is nested — pinning our own "
            "reference does not fix it"
        )
        assert rendered.count("ci.yml") == 1, (
            "the origin file is named in the headline; repeating it on a `via` "
            "line makes a two-hop chain read as three"
        )
        assert rendered.count("via") == 1, "one hop between origin and violation"

    def test_a_fully_pinned_graph_passes(self) -> None:
        composite = f"""
        runs:
          using: composite
          steps:
            - uses: actions/cache@{OTHER_PINNED}
        """
        violations = walk(
            [("ci.yml", f"pre-commit/action@{PINNED}")],
            fetcher({("pre-commit/action", "action.yml"): composite}),
        )
        assert violations == []

    def test_it_recurses_past_the_first_level(self) -> None:
        """Composite actions may nest composite actions."""
        outer = (
            f"runs:\n  using: composite\n  steps:\n    - uses: mid/act@{OTHER_PINNED}\n"
        )
        middle = "runs:\n  using: composite\n  steps:\n    - uses: deep/act@v1\n"
        violations = walk(
            [("ci.yml", f"outer/act@{PINNED}")],
            fetcher(
                {
                    ("outer/act", "action.yml"): outer,
                    ("mid/act", "action.yml"): middle,
                }
            ),
        )
        assert [v.ref for v in violations] == ["deep/act@v1"]
        assert len(violations[0].chain) == 3, "the full chain should be reported"

    def test_a_javascript_action_is_a_leaf(self) -> None:
        """JS and Docker actions declare one entry point and cannot reference
        another action, so walking them would only cost API calls."""
        calls: list[str] = []

        def counting_fetch(owner_repo: str, path: str, ref: str) -> str | None:
            calls.append(path)
            return JS_ACTION_YML if path == "action.yml" else None

        assert walk([("ci.yml", f"actions/setup-node@{PINNED}")], counting_fetch) == []
        assert calls == ["action.yml"]

    def test_action_yaml_spelling_is_tried_too(self) -> None:
        violations = walk(
            [("ci.yml", f"some/act@{PINNED}")],
            fetcher({("some/act", "action.yaml"): PRE_COMMIT_ACTION_YML}),
        )
        assert [v.ref for v in violations] == ["actions/cache@v4"]

    def test_each_sha_is_fetched_once(self) -> None:
        """Content at a SHA is immutable, so a reference resolved once never
        needs fetching again — including when two workflows share it."""
        calls: list[tuple[str, str]] = []

        def counting_fetch(owner_repo: str, path: str, ref: str) -> str | None:
            calls.append((owner_repo, path))
            return JS_ACTION_YML if path == "action.yml" else None

        walk(
            [
                ("ci.yml", f"actions/setup-node@{PINNED}"),
                ("docs.yml", f"actions/setup-node@{PINNED}"),
            ],
            counting_fetch,
        )
        assert calls == [("actions/setup-node", "action.yml")]

    def test_a_cycle_terminates(self) -> None:
        looping = f"runs:\n  using: composite\n  steps:\n    - uses: a/b@{PINNED}\n"
        assert (
            walk(
                [("ci.yml", f"a/b@{PINNED}")],
                fetcher({("a/b", "action.yml"): looping}),
            )
            == []
        )


class TestFailureIsNotSilence:
    def test_a_fetch_failure_propagates_rather_than_reporting_clean(self) -> None:
        """The whole point of this script is that a gate reported green over a
        graph it could not see. It must never do that itself."""

        def broken_fetch(owner_repo: str, path: str, ref: str) -> str | None:
            raise FetchError("no network")

        with pytest.raises(FetchError):
            walk([("ci.yml", f"pre-commit/action@{PINNED}")], broken_fetch)

    def test_unparseable_yaml_raises_rather_than_yielding_nothing(
        self, tmp_path: Path
    ) -> None:
        bad = tmp_path / "broken.yml"
        bad.write_text("jobs: [unclosed\n", encoding="utf-8")
        with pytest.raises(FetchError):
            collect_seeds([bad])

    def test_a_named_path_that_does_not_exist_is_not_a_pass(
        self, tmp_path: Path
    ) -> None:
        """A typo'd path, or the right path from the wrong directory, must not
        exit 0. Reporting clean over files it never opened is exactly the
        failure this script was written to stop doing."""
        assert main([str(tmp_path / "nope.yml")]) == 2

    def test_one_missing_path_among_several_still_fails(self, tmp_path: Path) -> None:
        present = tmp_path / "wf.yml"
        present.write_text("jobs: {}\n", encoding="utf-8")
        assert main([str(present), str(tmp_path / "nope.yml")]) == 2

    def test_a_repository_with_no_workflows_is_genuinely_clean(
        self, tmp_path: Path
    ) -> None:
        """Distinct from the case above: nothing was named, and discovery
        found nothing, so there is honestly nothing to pin."""
        assert main(["--root", str(tmp_path)]) == 0


class TestAgainstThisRepository:
    def test_every_workflow_here_parses_and_yields_pinned_seeds(self) -> None:
        """No network: confirms our own files are clean at the direct level,
        which is the part zizmor also covers."""
        root = Path(__file__).resolve().parents[2]
        paths = sorted((root / ".github" / "workflows").glob("*.yml"))
        assert paths, "no workflows found — the test is pointing at the wrong root"

        unpinned = [
            (origin, value)
            for origin, value in collect_seeds(paths)
            if (ref := parse_ref(value)) is not None and not ref.pinned
        ]
        assert unpinned == []


@pytest.mark.skipif(
    os.environ.get("LEGESHER_NETWORK_TESTS") != "1",
    reason="set LEGESHER_NETWORK_TESTS=1 to check the fixture against the real API",
)
def test_the_core_1926_fixture_still_matches_upstream() -> None:
    """Guards the fixture above from drifting away from what it models."""
    from audit_action_graph import gh_fetch

    sha = "2c7b3805fd2a0fd8c1884dcaebf91fc102a13ecd"  # pre-commit/action v3.0.1
    manifest = gh_fetch("pre-commit/action", "action.yml", sha)
    assert manifest is not None
    assert "actions/cache@v4" in manifest, (
        "upstream changed; the CORE-1926 fixture no longer models a real case"
    )
