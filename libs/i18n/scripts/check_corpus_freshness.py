"""Release gate: the published corpus must not predate the canon shipping (CORE-1800).

The corpus (``legesher/language-corpus``) is the evidence layer behind the
canon packs. Its export used to be a free-floating manual step, so the
published dataset was a snapshot of whenever an operator last ran it — it
could silently lag the canon by weeks. This check turns the sequencing rule
into code the release ritual runs (packs-publish-runbook.md, preconditions):

    a release cannot complete with a published corpus revision older than
    the canon state it ships.

What is compared
================

* **Canon state shipping** — the committer timestamp of the last commit that
  touched the canon pack tree (``language-packs/``, the source the canon
  dataset is built from) as of ``HEAD``. The runbook already requires a
  clean, tagged tree, so HEAD *is* the state being shipped.
* **Published corpus revision** — the Hub's last-modified timestamp for the
  corpus dataset repository (its latest revision).

``published >= canon`` passes. Timestamps are a sequencing proxy, not a
content diff: the check proves the export ran *after* the canon last moved,
which is exactly the ordering the ritual guarantees (land canon → re-export
corpus → pin the packs revision). It cannot prove the export read a fresh
database — the corpus runbook's provenance review (§1) still covers that.

This script is read-only everywhere: one anonymous metadata read from the
Hub, one local ``git log``. It never pushes and holds none of the CORE-1502
push gates — those stay in ``export_corpus.py``, untouched. When the check
fails, the fix is to walk corpus-publish-runbook.md §§1-3
(``migrate_to_v2.py --publish`` → ``export_corpus.py --push``) and re-run.

Usage (from ``libs/i18n``)::

    uv run python scripts/check_corpus_freshness.py

Exit status: 0 fresh, 1 stale (or any refusal).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_TARGET_REPO = "legesher/language-corpus"

#: The canon source tree, relative to ``libs/i18n``. The canon dataset is
#: built from this YAML tree (packs-publish-runbook.md, "Why not the
#: database"), so its last commit IS the canon state a release ships.
DEFAULT_CANON_PATH = "language-packs"

_I18N_ROOT = Path(__file__).resolve().parent.parent


def canon_state_timestamp(repo_dir: Path, canon_path: str) -> datetime:
    """Committer timestamp of the last commit touching the canon tree.

    Args:
        repo_dir: Directory inside the git repository (``libs/i18n``).
        canon_path: Pathspec of the canon source tree, relative to repo_dir.

    Raises:
        SystemExit: when git fails or no commit touches the pathspec —
            either way there is no canon state to compare, and guessing
            "fresh" would defeat the gate.
    """
    result = subprocess.run(  # noqa: S603 - fixed argv, no shell
        ["git", "log", "-1", "--format=%cI", "--", canon_path],  # noqa: S607
        cwd=repo_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(
            f"FRESHNESS CHECK REFUSED: `git log` failed in {repo_dir}: "
            f"{result.stderr.strip()}"
        )
    stamp = result.stdout.strip()
    if not stamp:
        raise SystemExit(
            f"FRESHNESS CHECK REFUSED: no commit touches {canon_path!r} under "
            f"{repo_dir} — wrong --canon-path or wrong working directory."
        )
    # git 2.47+ prints a UTC offset in strict ISO form as "Z"; Python's
    # fromisoformat only accepts that spelling from 3.11 (CORE-2542).
    if stamp.endswith("Z"):
        stamp = stamp[:-1] + "+00:00"
    return datetime.fromisoformat(stamp)


def published_corpus_state(repo_id: str) -> tuple[datetime, str]:
    """Last-modified timestamp and revision sha of the published corpus.

    A metadata read only — nothing is downloaded and nothing is pushed.

    Raises:
        SystemExit: when the Hub metadata cannot be read (network, missing
            repo, or a repo that reports no last-modified). A gate that
            cannot see the published state must refuse, not pass.
    """
    try:
        from huggingface_hub import HfApi
    except ImportError:
        raise SystemExit(
            "FRESHNESS CHECK REFUSED: huggingface_hub is not installed. "
            "`uv add --package legesher-i18n --dev huggingface_hub`."
        ) from None
    try:
        info: Any = HfApi().dataset_info(repo_id)
    except Exception as exc:  # noqa: BLE001 - any Hub failure is a refusal
        raise SystemExit(
            f"FRESHNESS CHECK REFUSED: could not read Hub metadata for {repo_id}: {exc}"
        ) from None
    if info.last_modified is None:
        raise SystemExit(
            f"FRESHNESS CHECK REFUSED: the Hub reports no last-modified "
            f"timestamp for {repo_id}."
        )
    return info.last_modified, info.sha or "unknown"


def freshness_verdict(
    corpus_ts: datetime,
    canon_ts: datetime,
    *,
    repo_id: str,
    canon_path: str,
    corpus_revision: str = "unknown",
) -> tuple[bool, str]:
    """Decide fresh vs stale and render the operator-facing message.

    Pure — all IO stays in the callers, so the rule itself is unit-testable.
    Equality passes: a corpus pushed in the same second as the canon commit
    still reflects that state.
    """
    if corpus_ts >= canon_ts:
        return True, (
            f"FRESH: {repo_id} revision {corpus_revision} "
            f"({corpus_ts.isoformat()}) is not older than the last "
            f"{canon_path} change ({canon_ts.isoformat()}). The release may "
            "proceed."
        )
    return False, (
        f"STALE: {repo_id} was last pushed {corpus_ts.isoformat()} "
        f"(revision {corpus_revision}), but {canon_path} last changed "
        f"{canon_ts.isoformat()} — the published evidence predates the canon "
        "state this release ships. Re-export before completing the release: "
        "corpus-publish-runbook.md §§1-3 (migrate_to_v2.py --publish, then "
        "export_corpus.py --push), then re-run this check."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Release gate: fail when the published corpus revision predates "
            "the canon state shipping (CORE-1800). Read-only."
        )
    )
    parser.add_argument(
        "--target-repo",
        default=DEFAULT_TARGET_REPO,
        help=f"Hub dataset to check (default: {DEFAULT_TARGET_REPO})",
    )
    parser.add_argument(
        "--canon-path",
        default=DEFAULT_CANON_PATH,
        help=(
            f"canon source tree, relative to libs/i18n (default: {DEFAULT_CANON_PATH})"
        ),
    )
    parser.add_argument(
        "--repo-dir",
        type=Path,
        default=_I18N_ROOT,
        help="directory inside the git checkout to run git from (default: libs/i18n)",
    )
    args = parser.parse_args(argv)

    canon_ts = canon_state_timestamp(args.repo_dir, args.canon_path)
    corpus_ts, revision = published_corpus_state(args.target_repo)
    fresh, message = freshness_verdict(
        corpus_ts,
        canon_ts,
        repo_id=args.target_repo,
        canon_path=args.canon_path,
        corpus_revision=revision,
    )
    print(message)
    return 0 if fresh else 1


if __name__ == "__main__":
    sys.exit(main())
