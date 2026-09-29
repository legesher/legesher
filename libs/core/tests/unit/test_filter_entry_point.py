"""``legesher-filter`` as git runs it: bytes in, bytes out, exit 0 (CORE-1841)."""

import subprocess
import sys


def run_filter(*args: str, stdin: bytes, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "legesher_core", *args],
        input=stdin,
        capture_output=True,
        cwd=cwd,
        check=False,
        timeout=60,
    )


def test_crlf_line_endings_survive_and_strays_are_normalized(tmp_path):
    result = run_filter(
        "--clean",
        "--language",
        "es",
        "--path",
        "m.py",
        stdin="definir f(x):\r\n    si x:\r\n        return 1\r\n".encode(),
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert (
        result.stdout == "definir f(x):\r\n    si x:\r\n        devolver 1\r\n".encode()
    )


def test_bytes_that_are_not_utf8_pass_through_unchanged(tmp_path):
    payload = b"x = '\xff\xfe'\nif x:\n    pass\n"
    result = run_filter("--clean", "--language", "es", stdin=payload, cwd=tmp_path)
    assert (result.returncode, result.stdout) == (0, payload)


def test_an_unknown_language_passes_through_and_exits_zero(tmp_path):
    payload = "definir f():\n    return 1\n".encode()
    result = run_filter("--clean", "--language", "xx-nope", stdin=payload, cwd=tmp_path)
    assert (result.returncode, result.stdout) == (0, payload)


def test_the_smudge_is_keyword_only(tmp_path):
    result = run_filter(
        "--smudge",
        "--language",
        "es",
        stdin="def f(x):\n    return len(x)\n".encode(),
        cwd=tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "definir f(x):\n    devolver len(x)\n".encode()
