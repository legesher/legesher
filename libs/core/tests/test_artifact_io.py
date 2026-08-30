"""Shared artifact I/O primitives (CORE-1710).

Covers the family-level acceptance criteria: a write killed mid-flight
leaves the PREVIOUS valid artifact intact, and there is exactly one
semver parser behind every artifact's version envelope.
"""

import json
import os
from pathlib import Path

import pytest

from legesher_core.artifact_io import (
    atomic_write_text,
    parse_semver,
    replace_with_retry,
)
from legesher_core.translation_memory import TranslationMemoryDocument


class TestAtomicWrite:
    def test_writes_content(self, tmp_path):
        target = tmp_path / "artifact.json"
        atomic_write_text(target, '{"a": 1}\n')
        assert target.read_text(encoding="utf-8") == '{"a": 1}\n'

    def test_creates_parent_directories(self, tmp_path):
        target = tmp_path / ".legesher" / "nested" / "artifact.json"
        atomic_write_text(target, "x\n")
        assert target.read_text(encoding="utf-8") == "x\n"

    def test_failed_write_leaves_previous_artifact_intact(self, tmp_path, monkeypatch):
        """The whole point: a crash mid-write must not destroy the file.

        ``Path.write_text`` truncates first, so the old artifact is gone
        the instant the write begins. The temp+replace path keeps it
        until the replace succeeds.
        """
        target = tmp_path / "artifact.json"
        original = '{"valid": true}\n'
        target.write_text(original, encoding="utf-8")

        def explode(*args, **kwargs):
            raise OSError("disk full")

        monkeypatch.setattr(os, "fsync", explode)
        with pytest.raises(OSError):
            atomic_write_text(target, '{"replacement": true}\n')

        assert target.read_text(encoding="utf-8") == original
        assert json.loads(target.read_text(encoding="utf-8")) == {"valid": True}

    def test_failed_write_leaves_no_temp_file_behind(self, tmp_path, monkeypatch):
        """A stray temp file in .legesher/ would show up in git status."""
        target = tmp_path / "artifact.json"
        target.write_text("old\n", encoding="utf-8")

        def explode(*args, **kwargs):
            raise OSError("disk full")

        monkeypatch.setattr(os, "fsync", explode)
        with pytest.raises(OSError):
            atomic_write_text(target, "new\n")
        assert [p.name for p in tmp_path.iterdir()] == ["artifact.json"]

    def test_temp_file_is_a_sibling(self, tmp_path):
        """os.replace is only atomic within a filesystem, so the temp
        file must live in the destination's own directory."""
        target = tmp_path / "artifact.json"
        seen: list[Path] = []
        real_replace = os.replace

        def spy(src, dst):
            seen.append(Path(src))
            return real_replace(src, dst)

        import legesher_core.artifact_io as module

        original = module.os.replace
        module.os.replace = spy
        try:
            atomic_write_text(target, "x\n")
        finally:
            module.os.replace = original
        assert seen and seen[0].parent == tmp_path

    def test_writes_lf_regardless_of_platform_default(self, tmp_path):
        """The committed artifact must not differ by who wrote it."""
        target = tmp_path / "artifact.json"
        atomic_write_text(target, "line1\nline2\n")
        assert target.read_bytes() == b"line1\nline2\n"


class TestAtomicSaveAcrossTheFamily:
    """Every artifact writer routes through the atomic helper."""

    def test_translation_memory_save_survives_a_killed_write(
        self, tmp_path, monkeypatch
    ):
        path = tmp_path / ".legesher" / "translation_memory.json"
        document = TranslationMemoryDocument()
        document.get_or_create("src/tax.py").add(
            "n000001", "# a comment", "es", "# un comentario", minted_by="model"
        )
        document.save(path)
        before = path.read_text(encoding="utf-8")

        def explode(*args, **kwargs):
            raise OSError("killed mid-write")

        monkeypatch.setattr(os, "fsync", explode)
        with pytest.raises(OSError):
            document.save(path)
        assert path.read_text(encoding="utf-8") == before
        TranslationMemoryDocument.load(path)  # still parses


class TestParseSemver:
    def test_parses(self):
        assert parse_semver("1.2.3") == (1, 2, 3)

    @pytest.mark.parametrize("bad", ["1.2", "1.2.3.4", "x.y.z", "", "1.2.x"])
    def test_rejects_malformed(self, bad):
        with pytest.raises(ValueError, match="Invalid schema_version"):
            parse_semver(bad)

    def test_rejects_non_string(self):
        with pytest.raises(ValueError, match="Invalid schema_version"):
            parse_semver(None)  # type: ignore[arg-type]

    def test_is_the_only_parser(self):
        """One parser, both consumers — the duplication CORE-1710 removed."""
        import legesher_core.translation_memory.model as tm_model

        assert tm_model.parse_semver is parse_semver
        assert not hasattr(tm_model, "_parse_semver")


#: Windows has no Unix permission bits. ``os.chmod`` there honours exactly
#: one thing — the read-only attribute — so every writable file reports
#: ``0o666`` back through ``stat()`` and a ``chmod(0o644)`` is a no-op the
#: following assertion cannot survive. The *behaviour* these tests cover is
#: POSIX-only too: there is no mode on Windows for a temp+replace to
#: tighten. The Windows-meaningful half is asserted separately below
#: (CORE-1919).
posix_modes_only = pytest.mark.skipif(
    os.name == "nt",
    reason="Windows os.chmod only honours the read-only bit; there are no "
    "permission bits to preserve",
)


class TestFileMode:
    """mkstemp creates 0600 and os.replace carries the temp file's mode
    onto the destination — a plain temp+replace silently tightens a
    world-readable artifact to owner-only on its first save."""

    @posix_modes_only
    def test_existing_mode_is_preserved(self, tmp_path):
        target = tmp_path / "artifact.json"
        target.write_text("old\n", encoding="utf-8")
        os.chmod(target, 0o644)
        atomic_write_text(target, "new\n")
        assert target.stat().st_mode & 0o777 == 0o644

    @posix_modes_only
    def test_an_unusual_existing_mode_is_preserved(self, tmp_path):
        target = tmp_path / "artifact.json"
        target.write_text("old\n", encoding="utf-8")
        os.chmod(target, 0o664)
        atomic_write_text(target, "new\n")
        assert target.stat().st_mode & 0o777 == 0o664

    def test_a_new_file_gets_the_umask_default_not_0600(self, tmp_path):
        """Unguarded deliberately — this one already passes on Windows,
        where a new file reports 0o666 and the umask is 0."""
        target = tmp_path / "artifact.json"
        atomic_write_text(target, "x\n")
        umask = os.umask(0)
        os.umask(umask)
        assert target.stat().st_mode & 0o777 == 0o666 & ~umask

    def test_replacing_an_existing_artifact_works(self, tmp_path):
        """``os.replace`` over a destination that already exists.

        Narrow on purpose. An earlier draft of this test asserted
        ``os.access(target, os.W_OK)`` and claimed to cover the Windows half
        of "does not tighten permissions" — it did not. ``mkstemp`` opens at
        ``0o600``, which still has the owner-write bit, so the assertion
        holds even when the mode-restoring code is deleted outright. Two
        mutations proved it green: removing ``_restore_mode``, and actively
        tightening to ``0o600`` on every write. A test that cannot fail for
        the bug it names is worse than no test, because it reads as coverage.

        What is left is the one thing here with real platform signal, and it
        is not about permissions: ``TestAtomicWrite.test_writes_content``
        only ever writes to a fresh path, and on Windows replacing an
        *existing* file is the case that separates ``os.replace`` from
        ``os.rename`` — the latter fails there.
        """
        target = tmp_path / "artifact.json"
        atomic_write_text(target, "first\n")
        atomic_write_text(target, "second\n")
        assert target.read_text(encoding="utf-8") == "second\n"


class TestReplaceWithRetry:
    """A transient PermissionError on the rename is not a failed write.

    On Windows ``os.replace`` fails with "Access is denied" whenever any
    handle is open on the destination — including one opened for a few
    milliseconds by Defender, the indexer or a backup agent. The write
    succeeded; the rename lost a race (CORE-1931). In-process locking
    cannot help, because the conflicting handle is not in this process.

    These drive the retry through an injected ``os.replace``, so the
    Windows-only failure is reproduced on every platform — which is the
    point, since the Windows runners are not always available.
    """

    def test_a_replace_that_succeeds_first_time_does_not_sleep(
        self, tmp_path: Path
    ) -> None:
        source = tmp_path / "src"
        source.write_text("payload", encoding="utf-8")
        slept: list[float] = []

        replace_with_retry(source, tmp_path / "dest", sleep=slept.append)

        assert (tmp_path / "dest").read_text(encoding="utf-8") == "payload"
        assert slept == [], "the happy path must not pay for the retry"

    def test_it_recovers_from_a_transient_denial(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two scanners' worth of bad luck, then the rename lands."""
        source = tmp_path / "src"
        source.write_text("payload", encoding="utf-8")
        real_replace = os.replace
        calls = {"n": 0}

        def flaky(a, b):
            calls["n"] += 1
            if calls["n"] <= 2:
                raise PermissionError(13, "Access is denied")
            return real_replace(a, b)

        monkeypatch.setattr(os, "replace", flaky)
        slept: list[float] = []

        replace_with_retry(source, tmp_path / "dest", sleep=slept.append)

        assert (tmp_path / "dest").read_text(encoding="utf-8") == "payload"
        assert calls["n"] == 3
        assert slept == [0.05, 0.1], "backoff should double between attempts"

    def test_a_permanent_denial_still_raises_the_original_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The retry must not disguise a real permission problem, and must
        not hang trying."""
        source = tmp_path / "src"
        source.write_text("payload", encoding="utf-8")

        def always_denied(a, b):
            raise PermissionError(13, "Access is denied")

        monkeypatch.setattr(os, "replace", always_denied)
        slept: list[float] = []

        with pytest.raises(PermissionError) as caught:
            replace_with_retry(source, tmp_path / "dest", sleep=slept.append)

        assert "Access is denied" in str(caught.value)
        assert len(slept) == 4, "5 attempts means 4 waits, then re-raise"

    def test_an_error_that_is_not_a_denial_is_not_retried(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Only the scanner-race signature is transient. A missing source
        is a bug, and retrying it just delays the report."""
        calls = {"n": 0}

        def missing(a, b):
            calls["n"] += 1
            raise FileNotFoundError(2, "No such file")

        monkeypatch.setattr(os, "replace", missing)

        with pytest.raises(FileNotFoundError):
            replace_with_retry(
                tmp_path / "src", tmp_path / "dest", sleep=lambda _: None
            )

        assert calls["n"] == 1, "a non-transient error must fail fast"

    def test_atomic_write_text_goes_through_the_retry(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The shared primitive must be covered, not just the metadata
        writer — it renames into the same .legesher/ directory and is
        exposed to exactly the same scanner."""
        destination = tmp_path / "artifact.json"
        real_replace = os.replace
        calls = {"n": 0}

        def flaky(a, b):
            calls["n"] += 1
            if calls["n"] == 1:
                raise PermissionError(13, "Access is denied")
            return real_replace(a, b)

        monkeypatch.setattr(os, "replace", flaky)
        monkeypatch.setattr("legesher_core.artifact_io.time.sleep", lambda _: None)

        atomic_write_text(destination, "contents")

        assert destination.read_text(encoding="utf-8") == "contents"
        assert calls["n"] == 2
