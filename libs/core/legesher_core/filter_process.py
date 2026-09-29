"""Git's long-running filter process for the clean filter (CORE-2297).

With ``filter.legesher.process`` configured, git starts one
``legesher-filter --process`` per git command and streams every file through
it, instead of starting Python, importing the engine and loading a pack once
per file. Git prefers the process whenever it is configured; the single-file
``filter.legesher.clean`` command stays as the fallback for git older than
2.11, which does not know the protocol.

The protocol (gitattributes, "Long Running Filter Process") frames everything
as pkt-lines: four hex digits of total length, then the payload, with
``0000`` as a flush that ends a list or a file's content. After a version and
capability handshake, git sends each file as a list of ``key=value`` lines
(``command=clean``, ``pathname=...``) followed by its content, and the filter
answers ``status=success`` with the filtered content, or ``status=error`` for
that file alone, or ``status=abort`` to stop filtering for the rest of the
command. With ``filter.legesher.required`` false, git keeps a file's content
unchanged whenever the filter reports an error.
"""

from __future__ import annotations

import logging
import subprocess
from collections.abc import Iterable
from typing import BinaryIO

from .git_filter import GitFilter, read_stored_blob
from .stored_form import clean_text, smudge_text

logger = logging.getLogger(__name__)

#: The largest payload one pkt-line carries (65520 bytes, less the header).
MAX_PACKET_DATA = 65516

_FLUSH = b"0000"


class ProtocolError(Exception):
    """The other side did not speak the long-running filter protocol."""


def _read_packet(stream: BinaryIO) -> bytes | None:
    """One packet's payload, ``None`` for a flush; ``EOFError`` at a clean end."""
    header = stream.read(4)
    if not header:
        raise EOFError
    if len(header) != 4:
        raise ProtocolError("truncated packet header")
    try:
        length = int(header, 16)
    except ValueError as exc:
        raise ProtocolError(f"bad packet header {header!r}") from exc
    if length == 0:
        return None
    if length < 5 or length > MAX_PACKET_DATA + 4:
        raise ProtocolError(f"bad packet length {length}")
    data = stream.read(length - 4)
    if len(data) != length - 4:
        raise ProtocolError("truncated packet")
    return data


def _write_packet(stream: BinaryIO, data: bytes) -> None:
    stream.write(f"{len(data) + 4:04x}".encode("ascii") + data)


def _read_list(stream: BinaryIO, *, at_boundary: bool = False) -> list[str]:
    """Text packets up to a flush, newline stripped.

    ``at_boundary`` lets the stream end cleanly before the first packet, which
    is how git closes the process after its last file.
    """
    items: list[str] = []
    while True:
        try:
            packet = _read_packet(stream)
        except EOFError:
            if at_boundary and not items:
                raise
            raise ProtocolError("the stream ended inside a list") from None
        if packet is None:
            return items
        items.append(packet.decode("utf-8", "surrogateescape").removesuffix("\n"))


def _write_list(stream: BinaryIO, items: Iterable[str]) -> None:
    for item in items:
        _write_packet(stream, item.encode("utf-8", "surrogateescape") + b"\n")
    stream.write(_FLUSH)


def _read_content(stream: BinaryIO) -> bytes:
    chunks: list[bytes] = []
    while True:
        try:
            packet = _read_packet(stream)
        except EOFError:
            raise ProtocolError("the stream ended inside a file's content") from None
        if packet is None:
            return b"".join(chunks)
        chunks.append(packet)


def _write_content(stream: BinaryIO, data: bytes) -> None:
    for start in range(0, len(data), MAX_PACKET_DATA):
        _write_packet(stream, data[start : start + MAX_PACKET_DATA])
    stream.write(_FLUSH)


class BatchStoredReader:
    """The committed version of each path, from one ``git cat-file --batch``.

    The same lookup as :func:`~legesher_core.git_filter.read_stored_blob`
    (``HEAD`` first, then the index for a path never committed), without a
    git process per file. A path git's batch input cannot carry (one with a
    newline), or any failure of the batch process, falls back to the
    per-file lookup.
    """

    def __init__(self, cwd: str | None = None) -> None:
        self._cwd = cwd
        self._process: subprocess.Popen[bytes] | None = None
        self._broken = False

    def __call__(self, path: str) -> str | None:
        # Git's batch input is one line per object, and it strips a trailing
        # CR from each, so a path with a newline or a CR is looked up alone.
        if self._broken or "\n" in path or "\r" in path:
            return read_stored_blob(path, cwd=self._cwd)
        try:
            for revision in (f"HEAD:{path}", f":0:{path}"):
                data = self._query(revision)
                if data is not None:
                    try:
                        return data.decode("utf-8")
                    except UnicodeDecodeError:
                        return None
            return None
        except (OSError, ValueError) as exc:
            logger.warning(f"filter process: cat-file failed, reading per file: {exc}")
            self._broken = True
            self.close()
            return read_stored_blob(path, cwd=self._cwd)

    def _query(self, revision: str) -> bytes | None:
        process = self._start()
        assert process.stdin is not None and process.stdout is not None
        process.stdin.write(revision.encode("utf-8", "surrogateescape") + b"\n")
        process.stdin.flush()
        header = process.stdout.readline()
        if not header.endswith(b"\n"):
            raise OSError("git cat-file stopped answering")
        fields = header[:-1].split(b" ")
        if fields[-1] in (b"missing", b"ambiguous"):
            return None
        if len(fields) != 3:
            raise ValueError(f"unexpected cat-file header {header!r}")
        kind, size = fields[1], int(fields[2])
        body = process.stdout.read(size)
        if len(body) != size or process.stdout.read(1) != b"\n":
            raise OSError("git cat-file answer was truncated")
        return body if kind == b"blob" else None

    def _start(self) -> subprocess.Popen[bytes]:
        if self._process is None or self._process.poll() is not None:
            self._process = subprocess.Popen(
                ["git", "cat-file", "--batch"],
                cwd=self._cwd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        return self._process

    def close(self) -> None:
        process, self._process = self._process, None
        if process is None:
            return
        try:
            if process.stdin is not None:
                process.stdin.close()
            process.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            process.kill()


class FilterProcess:
    """Serve git's long-running filter protocol for one git command.

    Args:
        git_filter: The loaded filter, or ``None`` when its language pack could
            not be loaded; then every file is answered ``abort``, so git stops
            asking and keeps the files unchanged.
        smudge: Offer the keyword-only smudge (the setup opt-in).
    """

    def __init__(self, git_filter: GitFilter | None, *, smudge: bool = False) -> None:
        self.git_filter = git_filter
        self.smudge = smudge

    def serve(
        self, stdin: BinaryIO, stdout: BinaryIO, *, handshake: bool = True
    ) -> int:
        """Answer requests until git closes stdin.

        ``handshake`` false means the launcher setup writes has already
        answered git's handshake (so that a filter which cannot start fails
        after it, where git treats the failure as one file's error rather
        than the whole command's), and requests start straight away.
        """
        if handshake:
            self._handshake(stdin, stdout)
        while True:
            try:
                headers = _read_list(stdin, at_boundary=True)
            except EOFError:
                return 0
            data = _read_content(stdin)
            fields = dict(item.split("=", 1) for item in headers if "=" in item)
            status, result = self._handle(fields, data)
            if status == "success":
                _write_list(stdout, ["status=success"])
                _write_content(stdout, result)
                _write_list(stdout, [])  # an empty list keeps the status
            else:
                _write_list(stdout, [f"status={status}"])
            stdout.flush()

    def _handshake(self, stdin: BinaryIO, stdout: BinaryIO) -> None:
        try:
            welcome = _read_list(stdin)
        except EOFError as exc:
            raise ProtocolError("no handshake") from exc
        if (
            not welcome
            or welcome[0] != "git-filter-client"
            or "version=2" not in welcome
        ):
            raise ProtocolError(f"unexpected handshake {welcome!r}")
        _write_list(stdout, ["git-filter-server", "version=2"])
        stdout.flush()
        offered = {
            item.split("=", 1)[1]
            for item in _read_list(stdin)
            if item.startswith("capability=")
        }
        wanted = ["clean", "smudge"] if self.smudge else ["clean"]
        _write_list(stdout, [f"capability={c}" for c in wanted if c in offered])
        stdout.flush()

    def _handle(self, fields: dict[str, str], data: bytes) -> tuple[str, bytes]:
        if self.git_filter is None:
            return "abort", b""
        command = fields.get("command")
        if command == "clean":
            return self._filter(
                data, lambda text: self._clean(text, fields.get("pathname"))
            )
        if command == "smudge" and self.smudge:
            keywords = self.git_filter.keywords
            return self._filter(data, lambda text: smudge_text(text, reader=keywords))
        return "error", b""

    def _clean(self, text: str, path: str | None) -> str:
        assert self.git_filter is not None
        stored = self.git_filter.stored_version(path)
        return clean_text(text, local=self.git_filter.keywords, stored=stored)

    @staticmethod
    def _filter(data: bytes, transform) -> tuple[str, bytes]:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            return "success", data
        try:
            return "success", transform(text).encode("utf-8")
        except Exception as exc:
            logger.error(f"filter process: {exc}", exc_info=True)
            return "error", b""


__all__ = ["MAX_PACKET_DATA", "BatchStoredReader", "FilterProcess", "ProtocolError"]
