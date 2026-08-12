"""Shared I/O and versioning primitives for the ``.legesher/`` artifacts.

The artifact family (register map, translation memory, mapping log,
identifier map) shares two concerns that were previously duplicated per
artifact:

- **Durable writes.** ``Path.write_text`` truncates the destination
  before writing a byte, so a crash mid-write leaves a truncated,
  unparseable artifact where a valid one used to be — and two concurrent
  writers interleave into corruption rather than losing cleanly.
  :func:`atomic_write_text` writes a sibling temp file, fsyncs it, and
  ``os.replace``\\ s it over the destination: a reader sees either the
  whole old artifact or the whole new one, never a partial file.
- **Schema version parsing.** One parser, one error message, one place
  to change when the envelope grows.

Pure stdlib; importable without any optional extra.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

__all__ = ["atomic_write_text", "parse_semver"]


def _fsync_directory(directory: Path) -> None:
    """Best-effort fsync of a directory so the rename itself is durable.

    A file's contents can be durable while the directory entry pointing
    at it is not, which would resurrect the pre-rename artifact after a
    power loss. Not every platform allows opening a directory (Windows)
    or supports fsync on one; the write is already crash-*consistent*
    without it, so failure here is non-fatal.
    """
    try:
        fd = os.open(directory, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def _default_file_mode() -> int:
    """0666 masked by the process umask — what ``open`` would create."""
    umask = os.umask(0)
    os.umask(umask)
    return 0o666 & ~umask


def _restore_mode(temp_path: Path, destination: Path) -> None:
    """Give the temp file the mode the destination should end up with.

    Best-effort: a filesystem that does not support chmod (or a
    destination that vanished) is not a reason to fail a write whose
    contents are already durable.
    """
    try:
        mode = destination.stat().st_mode & 0o7777
    except OSError:
        mode = _default_file_mode()
    try:
        os.chmod(temp_path, mode)
    except OSError:
        pass


def atomic_write_text(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    """Write ``content`` to ``path`` atomically (temp file + ``os.replace``).

    The temp file is created in the destination's own directory because
    ``os.replace`` is only atomic within a filesystem — a temp file in
    the system temp dir may be on a different one, degrading the rename
    to a copy. It is prefixed with a dot and cleaned up on failure, so a
    crashed write leaves the previous artifact untouched and no stray
    file in a tracked tree.

    ``newline="\\n"`` is explicit: the default translates ``\\n`` to
    ``\\r\\n`` on Windows, which would make the committed artifact differ
    byte-for-byte by the platform that wrote it. The artifact family
    stores LF, everywhere (see ``node_identity.normalize_text``).

    File mode is preserved across the replace. ``mkstemp`` creates at
    0600 and ``os.replace`` carries the temp file's mode onto the
    destination, so a plain temp+replace would silently tighten a 0644
    artifact to owner-only on its first save — breaking any cross-user
    CI or container that reads it. An existing file's mode is reused; a
    new one gets the process umask's default, as ``open`` would give.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    handle_fd, temp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(handle_fd, "w", encoding=encoding, newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        _restore_mode(temp_path, path)
        os.replace(temp_path, path)
    except BaseException:
        # Includes KeyboardInterrupt/SystemExit on purpose: an abandoned
        # temp file in .legesher/ would show up in git status.
        temp_path.unlink(missing_ok=True)
        raise
    _fsync_directory(path.parent)


def parse_semver(version: str) -> tuple[int, int, int]:
    """Parse a ``MAJOR.MINOR.PATCH`` schema version into a comparable tuple.

    Raises ``ValueError`` with the offending value for anything else —
    every artifact in the family reports a malformed envelope the same
    way.
    """
    try:
        major, minor, patch = (int(part) for part in version.split("."))
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Invalid schema_version {version!r}: {exc}") from exc
    return major, minor, patch
