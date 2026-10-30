"""The corpus-freshness release gate (CORE-1800).

The rule under test: a release cannot complete with a published corpus
revision older than the canon state it ships. The decision function is pure;
the IO edges (git, Hub) are exercised only where they can run offline.
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import scripts.check_corpus_freshness as freshness
from scripts.check_corpus_freshness import (
    canon_state_timestamp,
    freshness_verdict,
)

CANON_TS = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)
I18N_ROOT = Path(__file__).resolve().parent.parent


class TestVerdict:
    def test_newer_corpus_is_fresh(self):
        fresh, message = freshness_verdict(
            CANON_TS + timedelta(hours=1),
            CANON_TS,
            repo_id="legesher/language-corpus",
            canon_path="language-packs",
            corpus_revision="abc123",
        )
        assert fresh
        assert message.startswith("FRESH")
        assert "abc123" in message

    def test_equal_timestamps_are_fresh(self):
        # A corpus pushed in the same second as the canon commit still
        # reflects that state — the boundary passes.
        fresh, _ = freshness_verdict(
            CANON_TS,
            CANON_TS,
            repo_id="r",
            canon_path="language-packs",
        )
        assert fresh

    def test_older_corpus_is_stale(self):
        fresh, message = freshness_verdict(
            CANON_TS - timedelta(days=14),
            CANON_TS,
            repo_id="legesher/language-corpus",
            canon_path="language-packs",
        )
        assert not fresh
        assert message.startswith("STALE")

    def test_stale_message_names_the_remedy(self):
        # The operator reading the failure must be handed the ritual, not
        # just the verdict: the runbook and both export steps, in order.
        _, message = freshness_verdict(
            CANON_TS - timedelta(days=1),
            CANON_TS,
            repo_id="legesher/language-corpus",
            canon_path="language-packs",
        )
        assert "corpus-publish-runbook.md" in message
        assert "migrate_to_v2.py --publish" in message
        assert "export_corpus.py --push" in message

    def test_mixed_offsets_compare_correctly(self):
        # git %cI carries the committer's local offset; the Hub reports UTC.
        # 14:00+02:00 IS 12:00Z — equal, therefore fresh.
        canon_local = datetime.fromisoformat("2026-08-15T14:00:00+02:00")
        fresh, _ = freshness_verdict(
            CANON_TS,
            canon_local,
            repo_id="r",
            canon_path="language-packs",
        )
        assert fresh


class TestCanonTimestamp:
    def test_reads_a_timezone_aware_timestamp_from_this_repo(self):
        ts = canon_state_timestamp(I18N_ROOT, "language-packs")
        assert ts.tzinfo is not None

    def test_refuses_a_pathspec_no_commit_touches(self):
        with pytest.raises(SystemExit, match="no commit touches"):
            canon_state_timestamp(I18N_ROOT, "no-such-canon-tree")

    def test_parses_the_utc_stamp_git_2_47_prints_with_a_trailing_z(self, monkeypatch):
        # A UTC committer (GitHub's pull-request merge ref, a bot, TZ=UTC)
        # makes `git log --format=%cI` print "Z"; Python 3.10 rejects it
        # unless it is normalised first (CORE-2542).
        def fake_git(argv, **kwargs):
            assert argv[:3] == ["git", "log", "-1"]
            return subprocess.CompletedProcess(
                argv, 0, stdout="2026-10-30T01:08:18Z\n", stderr=""
            )

        monkeypatch.setattr(freshness.subprocess, "run", fake_git)
        ts = canon_state_timestamp(I18N_ROOT, "language-packs")
        assert ts == datetime(2026, 10, 30, 1, 8, 18, tzinfo=timezone.utc)
        assert ts.utcoffset() == timedelta(0)


class TestMain:
    """CLI wiring only — the Hub edge is stubbed, nothing touches network."""

    def test_fresh_exits_zero(self, monkeypatch, capsys):
        monkeypatch.setattr(freshness, "canon_state_timestamp", lambda *a: CANON_TS)
        monkeypatch.setattr(
            freshness,
            "published_corpus_state",
            lambda repo: (CANON_TS + timedelta(hours=1), "abc123"),
        )
        assert freshness.main([]) == 0
        assert "FRESH" in capsys.readouterr().out

    def test_stale_exits_nonzero(self, monkeypatch, capsys):
        monkeypatch.setattr(freshness, "canon_state_timestamp", lambda *a: CANON_TS)
        monkeypatch.setattr(
            freshness,
            "published_corpus_state",
            lambda repo: (CANON_TS - timedelta(days=7), "abc123"),
        )
        assert freshness.main([]) == 1
        assert "STALE" in capsys.readouterr().out

    def test_default_target_is_the_corpus_dataset(self, monkeypatch):
        seen: dict[str, str] = {}

        def fake_published(repo_id: str):
            seen["repo"] = repo_id
            return CANON_TS, "abc123"

        monkeypatch.setattr(freshness, "canon_state_timestamp", lambda *a: CANON_TS)
        monkeypatch.setattr(freshness, "published_corpus_state", fake_published)
        freshness.main([])
        assert seen["repo"] == "legesher/language-corpus"
