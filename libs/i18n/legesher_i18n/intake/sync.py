"""Durable-home write-through: every import run ends with a push (CORE-1794).

The operational database's canonical copy lives in a PRIVATE data repository
the monorepo never names — it is resolved via ``$LEGESHER_DATA_REPO``. An
unpushed import exists only on one workstation, which is exactly the failure
mode the durable home exists to prevent, so the sync is loud: no data home,
no silent skip.

Accepted raw payloads (bundle files, issue JSON) are archived alongside the
database. They are the rebuild source: ``migrate_to_v2.py`` reconstructs the
v2 database from scratch, and re-running the importer over the archived
payloads is what re-derives the intake layer (usernames inside raw payloads
are fine there — the repository is private, and the importer's withdrawal
rule keeps a replay from resurrecting an erased identity).
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

__all__ = ["sync_to_durable_home"]


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(  # nosec B603 B607 - fixed argv, no shell
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def sync_to_durable_home(
    db_path: Path,
    payloads: list[tuple[str, bytes]],
    *,
    ritual: str,
    repo: Path | None = None,
    push: bool = True,
) -> str | None:
    """Checkpoint, copy, archive, commit, push.

    Args:
        db_path: The operational v2 database that was just written.
        payloads: ``(filename, raw bytes)`` of every ACCEPTED submission this
            run ingested, archived under ``intake/<YYYY-MM>/``.
        ritual: Human-readable ritual name for the commit message
            (e.g. ``"review import [CORE-1688]"``).
        repo: The data-home checkout; defaults to ``$LEGESHER_DATA_REPO``.
        push: Push after committing. Disable only in tests.

    Returns:
        The commit sha, or ``None`` if there was nothing new to commit.

    Raises:
        RuntimeError: if no data home is configured or it is not a checkout.
        subprocess.CalledProcessError: if a git step fails — a failed push is
            an error, never a warning.
    """
    if repo is None:
        env = os.environ.get("LEGESHER_DATA_REPO")
        if not env:
            raise RuntimeError(
                "LEGESHER_DATA_REPO is not set. Every import run must end with "
                "a push to the durable data home (CORE-1794); set the variable "
                "to your data-repository checkout and re-run the sync."
            )
        repo = Path(env)
    if not (repo / ".git").exists():
        raise RuntimeError(f"{repo} is not a git checkout; refusing to sync")

    # Fold the WAL into the main file so the copy is complete and consistent.
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        conn.close()

    rel_paths: list[str] = []
    db_dir = repo / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(db_path, db_dir / db_path.name)
    rel_paths.append(f"db/{db_path.name}")

    month = datetime.now(timezone.utc).strftime("%Y-%m")
    for name, raw in payloads:
        target_dir = repo / "intake" / month
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / name).write_bytes(raw)
        rel_paths.append(f"intake/{month}/{name}")

    _git(repo, "add", "--", *rel_paths)
    status = _git(repo, "status", "--porcelain", "--", *rel_paths)
    if not status:
        return None
    # Path-scoped: `git commit` without pathspecs would sweep up anything else
    # the maintainer had staged in the data repo (a half-finished identity-map
    # edit is the realistic case) and push it under an import's message.
    _git(repo, "commit", "-q", "-m", f"db: {ritual}", "--", *rel_paths)
    sha = _git(repo, "rev-parse", "HEAD")
    if push:
        _git(repo, "push", "-q")
    return sha
