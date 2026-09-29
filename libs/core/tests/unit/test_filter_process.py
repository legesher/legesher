"""Git's long-running filter process protocol (CORE-2297).

Each test plays git's side of the protocol over in-memory streams: the
pkt-line framing, the version and capability handshake, and one or more
filter requests, then reads back exactly what the process wrote.
"""

import io

import pytest

from legesher_core.filter_process import (
    MAX_PACKET_DATA,
    FilterProcess,
    ProtocolError,
)
from legesher_core.git_filter import GitFilter

FLUSH = b"0000"


def pkt(data: bytes | str) -> bytes:
    if isinstance(data, str):
        data = data.encode()
    return f"{len(data) + 4:04x}".encode() + data


def lines(*items: str) -> bytes:
    return b"".join(pkt(item + "\n") for item in items) + FLUSH


def content(data: bytes) -> bytes:
    chunks = [
        data[i : i + MAX_PACKET_DATA] for i in range(0, len(data), MAX_PACKET_DATA)
    ]
    return b"".join(pkt(chunk) for chunk in chunks) + FLUSH


HANDSHAKE = lines("git-filter-client", "version=2") + lines(
    "capability=clean", "capability=smudge", "capability=delay"
)


def request(command: str, pathname: str, data: bytes) -> bytes:
    return lines(f"command={command}", f"pathname={pathname}") + content(data)


def packets(output: bytes) -> list[bytes | None]:
    """Every packet the process wrote, ``None`` for a flush."""
    stream = io.BytesIO(output)
    out: list[bytes | None] = []
    while header := stream.read(4):
        length = int(header, 16)
        out.append(None if length == 0 else stream.read(length - 4))
    return out


def split_lists(output: bytes) -> list[list[bytes]]:
    """Packets grouped between flushes."""
    groups: list[list[bytes]] = [[]]
    for item in packets(output):
        if item is None:
            groups.append([])
        else:
            groups[-1].append(item)
    return groups[:-1]


def serve(session: bytes, *, smudge: bool = False, stored=None, language="es") -> bytes:
    git_filter = GitFilter(
        language=language, stored_reader=stored or (lambda path: None)
    )
    stdout = io.BytesIO()
    FilterProcess(git_filter, smudge=smudge).serve(io.BytesIO(session), stdout)
    return stdout.getvalue()


def responses(output: bytes) -> list[tuple[bytes, bytes]]:
    """``(status list, content)`` for each request after the handshake."""
    groups = split_lists(output)[2:]
    out = []
    index = 0
    while index < len(groups):
        status = b"".join(groups[index])
        if status == b"status=success\n":
            body = b"".join(groups[index + 1])
            out.append((status, body))
            index += 3  # status, content, trailing (empty) list
        else:
            out.append((status, b""))
            index += 1
    return out


class TestHandshake:
    def test_answers_as_a_version_2_server_with_clean_only(self):
        groups = split_lists(serve(HANDSHAKE))
        assert groups[0] == [b"git-filter-server\n", b"version=2\n"]
        assert groups[1] == [b"capability=clean\n"]

    def test_adds_smudge_only_when_the_keyword_smudge_is_opted_in(self):
        groups = split_lists(serve(HANDSHAKE, smudge=True))
        assert groups[1] == [b"capability=clean\n", b"capability=smudge\n"]

    def test_never_claims_a_capability_git_did_not_offer(self):
        session = lines("git-filter-client", "version=2") + lines("capability=smudge")
        groups = split_lists(serve(session, smudge=True))
        assert groups[1] == [b"capability=smudge\n"]

    def test_refuses_a_client_that_is_not_git(self):
        with pytest.raises(ProtocolError):
            serve(lines("not-git", "version=2"))

    def test_refuses_a_git_that_does_not_speak_version_2(self):
        with pytest.raises(ProtocolError):
            serve(lines("git-filter-client", "version=3"))


class TestClean:
    def test_normalizes_like_the_single_file_filter(self):
        text = "definir f(x):\n    si x:\n        return 1\n".encode()
        (reply,) = responses(serve(HANDSHAKE + request("clean", "m.py", text)))
        assert reply == (
            b"status=success\n",
            "definir f(x):\n    si x:\n        devolver 1\n".encode(),
        )

    def test_many_files_through_one_process_each_read_against_its_own_path(self):
        seen = []

        def stored(path):
            seen.append(path)
            return {"en.py": "def f(x):\n    return x\n"}.get(path)

        session = HANDSHAKE
        session += request(
            "clean", "en.py", b"def f(x):\n    si x:\n        return x\n"
        )
        session += request(
            "clean", "es.py", "definir f(x):\n    si x:\n        return 1\n".encode()
        )
        session += request("clean", "plain.py", b"x = 1\n")
        replies = responses(serve(session, stored=stored))
        assert [body for _, body in replies] == [
            b"def f(x):\n    if x:\n        return x\n",
            "definir f(x):\n    si x:\n        devolver 1\n".encode(),
            b"x = 1\n",
        ]
        assert seen == ["en.py", "es.py", "plain.py"]

    def test_content_longer_than_one_packet(self):
        body = "definir f(x):\n    si x:\n        return 1\n".encode() * 4000
        assert len(body) > 2 * MAX_PACKET_DATA
        output = serve(HANDSHAKE + request("clean", "big.py", body))
        (reply,) = responses(output)
        assert reply[1] == body.replace(b"return", "devolver".encode())
        assert all(len(p) <= MAX_PACKET_DATA for p in packets(output) if p is not None)

    def test_empty_content(self):
        assert responses(serve(HANDSHAKE + request("clean", "e.py", b""))) == [
            (b"status=success\n", b"")
        ]

    def test_bytes_that_are_not_utf8_come_back_unchanged(self):
        data = b"x = '\xff'\nif x:\n    pass\n"
        assert responses(serve(HANDSHAKE + request("clean", "b.py", data))) == [
            (b"status=success\n", data)
        ]


class TestFailures:
    def test_a_failure_on_one_file_is_an_error_for_that_file_only(self, monkeypatch):
        from legesher_core import filter_process

        real = filter_process.clean_text

        def flaky(text, *, local, stored=None):
            if "boom" in text:
                raise RuntimeError("boom")
            return real(text, local=local, stored=stored)

        monkeypatch.setattr(filter_process, "clean_text", flaky)
        session = HANDSHAKE
        session += request("clean", "a.py", b"boom = 1\n")
        session += request(
            "clean", "b.py", "definir f(x):\n    si x:\n        return 1\n".encode()
        )
        replies = responses(serve(session))
        assert replies[0] == (b"status=error\n", b"")
        assert replies[1][0] == b"status=success\n"

    def test_an_unknown_command_is_an_error_and_the_process_keeps_serving(self):
        session = HANDSHAKE + request("frobnicate", "a.py", b"x = 1\n")
        session += request("clean", "b.py", b"x = 1\n")
        replies = responses(serve(session))
        assert replies == [(b"status=error\n", b""), (b"status=success\n", b"x = 1\n")]

    def test_smudge_without_the_opt_in_is_an_error(self):
        replies = responses(
            serve(HANDSHAKE + request("smudge", "a.py", b"def f(): pass\n"))
        )
        assert replies == [(b"status=error\n", b"")]

    def test_an_unloadable_language_aborts_for_the_whole_command(self):
        stdout = io.BytesIO()
        FilterProcess(None, smudge=False).serve(
            io.BytesIO(HANDSHAKE + request("clean", "a.py", b"x = 1\n")), stdout
        )
        groups = split_lists(stdout.getvalue())
        assert groups[1] == [b"capability=clean\n"]
        assert groups[2] == [b"status=abort\n"]


class TestAfterAHandshakeTheLauncherAnswered:
    """The launcher answers the handshake, then starts the process
    (review of CORE-2297), so the process serves requests straight away."""

    def test_serves_requests_without_a_handshake(self):
        git_filter = GitFilter(language="es", stored_reader=lambda path: None)
        stdout = io.BytesIO()
        session = request(
            "clean", "m.py", "definir f(x):\n    si x:\n        return 1\n".encode()
        )
        FilterProcess(git_filter, smudge=False).serve(
            io.BytesIO(session), stdout, handshake=False
        )
        groups = split_lists(stdout.getvalue())
        assert groups[0] == [b"status=success\n"]
        assert (
            b"".join(groups[1])
            == "definir f(x):\n    si x:\n        devolver 1\n".encode()
        )


class TestSmudge:
    def test_renders_keywords_when_opted_in(self):
        replies = responses(
            serve(
                HANDSHAKE + request("smudge", "a.py", b"def f(x):\n    return x\n"),
                smudge=True,
            )
        )
        assert replies == [(b"status=success\n", b"definir f(x):\n    devolver x\n")]
