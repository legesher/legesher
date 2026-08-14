#!/usr/bin/env python3
"""A minimal, deliberately misbehaving LSP server for transport tests (CORE-1886).

Depending on a real ``pyright-langserver`` gives us one happy path and nothing
else: we cannot ask it to flood stderr, to dribble a response out a few bytes at
a time, or to go silent. Those are precisely the conditions that break a naive
stdio transport, so the tests need a server that can be told to produce them.

It also means the transport has deterministic coverage on machines and CI
runners with no Node toolchain installed.

Behaviour is selected with ``STUB_MODE``:

``normal``        answer ``initialize`` and subsequent requests promptly
``chunked``       write every response in 7-byte pieces, so headers and bodies
                  straddle read boundaries
``stderr_flood``  emit ~512 KB on stderr before answering, which deadlocks any
                  client that pipes stderr without draining it
``noisy``         send unsolicited notifications before the response, so a
                  client that assumes the next message is its answer misreads
``silent``        never answer, to prove the client times out rather than hangs
``collide``       send a server→client *request* carrying the same id as the
                  client's in-flight request, just before answering it. Servers
                  number their own requests from their own counter, so this
                  collision is ordinary — a client that keys purely on ``id``
                  resolves the wrong one
``die_after_init`` answer ``initialize``, then exit, so the client must notice
                  its transport is gone rather than keep reporting it healthy
``bad_header``    answer ``initialize``, then emit an unparseable
                  ``Content-Length``, leaving the stream at an unknown offset
"""

import json
import os
import sys
import time

MODE = os.environ.get("STUB_MODE", "normal")
CHUNK = 7
STDERR_BYTES = 512 * 1024


def read_message(stream):
    """Read one Content-Length framed message, or None at end of stream."""
    headers = {}
    while True:
        line = stream.readline()
        if not line:
            return None
        text = line.decode("utf-8").strip()
        if not text:
            break
        key, _, value = text.partition(":")
        headers[key.strip().lower()] = value.strip()

    length = int(headers.get("content-length", 0))
    if length <= 0:
        return None

    body = b""
    while len(body) < length:
        piece = stream.read(length - len(body))
        if not piece:
            return None
        body += piece

    return json.loads(body.decode("utf-8"))


def write_message(stream, message):
    """Write one framed message, honouring the chunked mode."""
    body = json.dumps(message).encode("utf-8")
    data = b"Content-Length: " + str(len(body)).encode("ascii") + b"\r\n\r\n" + body

    if MODE == "chunked":
        for offset in range(0, len(data), CHUNK):
            stream.write(data[offset : offset + CHUNK])
            stream.flush()
            time.sleep(0.001)
    else:
        stream.write(data)
        stream.flush()


def notify(stream, method, params):
    write_message(stream, {"jsonrpc": "2.0", "method": method, "params": params})


def handle(request, stdout):
    """Answer a single request. Returns False when the client asked us to exit."""
    method = request.get("method")
    request_id = request.get("id")

    # Notifications carry no id and get no reply.
    if request_id is None:
        return method != "exit"

    if MODE == "noisy":
        notify(stdout, "window/logMessage", {"type": 3, "message": "warming up"})
        notify(stdout, "textDocument/publishDiagnostics", {"uri": "file:///x", "diagnostics": []})

    if MODE == "collide":
        # A request *from* the server, deliberately reusing the client's id.
        # Both sides number their requests independently, so overlap is normal.
        # Note this carries `method`, which is what distinguishes it from a
        # response — an `id` alone does not.
        write_message(
            stdout,
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "client/registerCapability",
                "params": {"registrations": []},
            },
        )

    if method == "initialize":
        if MODE == "stderr_flood":
            sys.stderr.buffer.write(b"x" * STDERR_BYTES)
            sys.stderr.buffer.flush()
        result = {"capabilities": {"hoverProvider": True}}
    elif method == "textDocument/hover":
        # Echo the request back so tests can prove the payload survived the wire
        # intact — including any non-ASCII the client sent.
        result = {"contents": request.get("params", {}).get("probe", "")}
    elif method == "shutdown":
        result = None
    else:
        result = {}

    write_message(stdout, {"jsonrpc": "2.0", "id": request_id, "result": result})

    if method == "initialize":
        if MODE == "die_after_init":
            # Handshake succeeds, then the server vanishes. The client's reader
            # hits end-of-stream; whether it notices is the point.
            return False
        if MODE == "bad_header":
            # A length the client cannot parse. There is no safe offset to
            # resynchronise to after this.
            stdout.write(b"Content-Length: not-a-number\r\n\r\n")
            stdout.flush()

    return True


def main():
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer

    while True:
        request = read_message(stdin)
        if request is None:
            return
        if MODE == "silent":
            # Stay alive and attentive, but never answer. A client that blocks
            # its event loop on the read will hang here rather than time out.
            continue
        if not handle(request, stdout):
            return


if __name__ == "__main__":
    main()
