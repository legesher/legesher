"""Adversarial sweep at the protocol surface (CORE-1744).

The happy paths live in the per-tool modules. This one is the systematic
edge pass: what every tool does with hostile, malformed, boundary, and
concurrent input, and — the part that matters most for a server that hands
errors to a model — that no failure text ever carries a filesystem path, a
stack trace, or a piece of the caller's source.

Failures here should read as behavior specs, so each test names the rule it
pins rather than the input it happens to use.
"""

from __future__ import annotations

import json
from datetime import timedelta

import anyio
import pytest
from mcp import ClientSession, McpError
from mcp.shared.memory import create_connected_server_and_client_session
from pydantic import AnyUrl

from legesher_mcp import server as server_module
from legesher_mcp.schemas import SOURCE_MAX_CHARS, SourceFile
from tests.conftest import assert_sanitized, call_err, call_ok
from tests.interpreter_gaps import IDENTIFIER_RULES_ARE_UNICODE_15_1

pytestmark = pytest.mark.anyio

#: A recognizable secret: if any of it appears in an error, the error leaked.
CANARY = "CANARY_SECRET_a1b2c3 = 'private value'"

#: Tools that take a single `source` string, with their other required args.
CODE_TOOLS: list[tuple[str, dict[str, str]]] = [
    ("translate_to_native", {"target_lang": "es"}),
    ("translate_to_source", {"source_lang": "es"}),
    ("explain_in_language", {"explain_in": "es"}),
]

#: Language codes that must never resolve, and why each is interesting.
BAD_LANGUAGES = [
    "zz",  # well-formed, absent from the registry
    "qqq",  # three letters, absent
    "EN",  # uppercase — the pattern is lowercase-only
    "e",  # too short
    "toolongcode",  # too long
    "es_MX",  # underscore, not the hyphen the pattern allows
    "../etc",  # path traversal
    "es/../..",  # traversal behind a valid prefix
    "",  # empty
]


def _map_args(source: str, **overrides: object) -> dict[str, object]:
    args: dict[str, object] = {
        "files": [{"path": "a.py", "source": source}],
        "target_lang": "es",
    }
    args.update(overrides)
    return args


# -- language-code edges ---------------------------------------------------


@pytest.mark.parametrize("language", BAD_LANGUAGES)
async def test_bad_target_language_is_rejected_cleanly(
    client: ClientSession, language: str
) -> None:
    message = await call_err(
        client, "translate_to_native", {"source": "x = 1\n", "target_lang": language}
    )
    assert_sanitized(message)


@pytest.mark.parametrize("language", BAD_LANGUAGES)
async def test_bad_language_rejected_by_every_tool(client: ClientSession, language: str) -> None:
    """No tool has its own, looser idea of what a language code is."""
    for tool, extra in CODE_TOOLS:
        args: dict[str, object] = {"source": "x = 1\n", **extra}
        # Point the language-bearing argument of each tool at the bad value.
        key = next(iter(extra))
        args[key] = language
        assert_sanitized(await call_err(client, tool, args))
    assert_sanitized(await call_err(client, "lookup_keyword_mapping", {"language": language}))
    assert_sanitized(
        await call_err(client, "map_existing_codebase", _map_args("x = 1\n", target_lang=language))
    )


async def test_unknown_language_names_the_catalog_resource(client: ClientSession) -> None:
    """The error tells the model where to find the real answer."""
    message = await call_err(
        client, "translate_to_native", {"source": "x = 1\n", "target_lang": "zz"}
    )
    assert "unsupported_language" in message
    assert "legesher://languages" in message


async def test_language_code_pattern_blocks_traversal_before_the_filesystem(
    client: ClientSession,
) -> None:
    """A traversal attempt is a schema rejection, not a pack-load failure."""
    message = await call_err(client, "lookup_keyword_mapping", {"language": "../../../etc/passwd"})
    assert "language_pack_not_found" not in message
    assert_sanitized(message)


# -- python_version edges --------------------------------------------------


@pytest.mark.parametrize("version", ["2.7", "3.9", "4.0", "3.13.1", "default", "", "../3.13"])
async def test_unsupported_python_version_is_rejected(client: ClientSession, version: str) -> None:
    message = await call_err(
        client,
        "lookup_keyword_mapping",
        {"language": "es", "python_version": version},
    )
    assert "invalid_arguments" in message
    assert_sanitized(message)


# -- source-length boundary ------------------------------------------------


async def test_source_at_the_maximum_is_accepted(client: ClientSession) -> None:
    """SOURCE_MAX_CHARS is inclusive — the boundary value is legal input.

    Uses a same-language request so the engine short-circuits: this test is
    about the schema bound, not about translating two million characters.
    """
    at_limit = "# " + "p" * (SOURCE_MAX_CHARS - 2)
    assert len(at_limit) == SOURCE_MAX_CHARS
    result = await call_ok(
        client,
        "translate_to_native",
        {"source": at_limit, "target_lang": "es", "source_lang": "es"},
    )
    assert result["translated_source"] == at_limit


async def test_source_over_the_maximum_is_rejected_without_echoing_it(
    client: ClientSession,
) -> None:
    """The rejection must not quote the source back — it is the caller's code."""
    over_limit = CANARY + "x" * SOURCE_MAX_CHARS
    message = await call_err(
        client, "translate_to_native", {"source": over_limit, "target_lang": "es"}
    )
    assert "invalid_arguments" in message
    assert "CANARY_SECRET" not in message
    assert len(message) < 500, "the error grew with the input"
    assert_sanitized(message)


async def test_oversized_file_in_a_batch_does_not_echo_its_source(
    client: ClientSession,
) -> None:
    """Same rule one level down, inside map_existing_codebase's file list."""
    over_limit = CANARY + "x" * SOURCE_MAX_CHARS
    message = await call_err(client, "map_existing_codebase", _map_args(over_limit))
    assert "CANARY_SECRET" not in message
    assert "files.0.source" in message, "the caller still learns which file was rejected"
    assert_sanitized(message)


@pytest.mark.parametrize("tool,extra", CODE_TOOLS)
async def test_empty_source_is_rejected(
    client: ClientSession, tool: str, extra: dict[str, str]
) -> None:
    message = await call_err(client, tool, {"source": "", **extra})
    assert "invalid_arguments" in message
    assert_sanitized(message)


@pytest.mark.parametrize("source", ["   ", "\n\n", "\t\n  \n"])
async def test_whitespace_only_source_is_valid_input(client: ClientSession, source: str) -> None:
    """Whitespace is a legal (if empty) Python file, not an error."""
    result = await call_ok(client, "translate_to_native", {"source": source, "target_lang": "es"})
    assert result["translated_source"] == source


# -- untokenizable source --------------------------------------------------

UNTOKENIZABLE = [
    "def broken(\n",
    "x = 'unterminated\n",
    "x = 1\x00\n",
    "((((\n",
]


@pytest.mark.parametrize("source", UNTOKENIZABLE)
async def test_translation_passes_untokenizable_source_through_unchanged(
    client: ClientSession, source: str
) -> None:
    """Translation never mangles input it cannot lex — it returns it as-is.

    The deliberate division of labor: `translate_*` is lossless or a no-op,
    and `explain_in_language` is the tool that tells you the code is broken.
    """
    result = await call_ok(client, "translate_to_native", {"source": source, "target_lang": "es"})
    assert result["translated_source"] == source


@pytest.mark.parametrize("source", UNTOKENIZABLE)
async def test_explain_reports_broken_source_as_a_verdict_not_an_error(
    client: ClientSession, source: str
) -> None:
    result = await call_ok(client, "explain_in_language", {"source": source, "explain_in": "es"})
    assert result["validation"]["valid"] is False
    assert result["validation"]["issue"]["message"]


@pytest.mark.parametrize("source", UNTOKENIZABLE)
async def test_map_marks_broken_files_without_failing_the_batch(
    client: ClientSession, source: str
) -> None:
    """One bad file is a per-file verdict; the report still comes back."""
    result = await call_ok(
        client,
        "map_existing_codebase",
        {
            "files": [
                {"path": "good.py", "source": "def ok():\n    return True\n"},
                {"path": "bad.py", "source": source},
            ],
            "target_lang": "es",
        },
    )
    by_path = {entry["path"]: entry for entry in result["files"]}
    assert by_path["good.py"]["translatable"] is True
    assert result["summary"]["files_total"] == 2


async def test_broken_file_report_does_not_echo_the_source(
    client: ClientSession,
) -> None:
    result = await call_ok(
        client,
        "map_existing_codebase",
        _map_args(f"def broken(\n{CANARY}\n"),
    )
    assert "CANARY_SECRET" not in json.dumps(result)


# -- malformed and missing arguments ---------------------------------------


async def test_missing_required_argument_is_rejected(client: ClientSession) -> None:
    message = await call_err(client, "translate_to_native", {"source": "x = 1\n"})
    assert "invalid_arguments" in message
    assert "target_lang" in message
    assert_sanitized(message)


async def test_unknown_top_level_arguments_are_ignored(client: ClientSession) -> None:
    """Pinned SDK behavior: extra tool arguments are dropped, not refused.

    Worth knowing rather than assuming — a caller who misspells an optional
    argument gets the default silently, with no signal that the value was
    discarded. The nested `files[].source` shape does forbid extras (see
    below), so the leniency is only at the top level.
    """
    result = await call_ok(
        client, "lookup_keyword_mapping", {"language": "es", "nonexistent": "value"}
    )
    assert result["language"] == "es"


async def test_a_misspelled_optional_argument_silently_takes_the_default(
    client: ClientSession,
) -> None:
    """The consequence of the leniency above, stated outright."""
    result = await call_ok(
        client, "lookup_keyword_mapping", {"language": "es", "python_versio": "3.12"}
    )
    assert result["python_version"] == "3.13"


async def test_wrong_argument_type_is_rejected(client: ClientSession) -> None:
    message = await call_err(client, "translate_to_native", {"source": 12345, "target_lang": "es"})
    assert "invalid_arguments" in message
    assert_sanitized(message)


async def test_calling_an_unknown_tool_says_so(client: ClientSession) -> None:
    """The caller learns the tool does not exist, not just that something broke.

    The SDK composes this message itself (no exception is wrapped), so the
    error-voice wrapper passes it through rather than flattening it to
    `internal_error` — which would leave a model retrying a typo forever.
    """
    message = await call_err(client, "definitely_not_a_tool", {})
    assert "Unknown tool" in message
    assert "internal_error" not in message
    assert_sanitized(message)


async def test_empty_file_list_is_rejected(client: ClientSession) -> None:
    """map_existing_codebase needs at least one file to report on."""
    message = await call_err(client, "map_existing_codebase", {"files": [], "target_lang": "es"})
    assert "invalid_arguments" in message
    assert "files" in message
    assert_sanitized(message)


async def test_malformed_file_entry_is_rejected(client: ClientSession) -> None:
    message = await call_err(
        client,
        "map_existing_codebase",
        {"files": [{"path": "a.py"}], "target_lang": "es"},
    )
    assert "invalid_arguments" in message
    assert_sanitized(message)


async def test_file_entry_rejects_unknown_keys(client: ClientSession) -> None:
    """SourceFile forbids extras, so a typo'd key fails loudly, not silently."""
    message = await call_err(
        client,
        "map_existing_codebase",
        {
            "files": [{"path": "a.py", "source": "x = 1\n", "sourcee": "typo"}],
            "target_lang": "es",
        },
    )
    assert "invalid_arguments" in message
    assert_sanitized(message)


async def test_a_large_file_list_is_reported_in_full(client: ClientSession) -> None:
    """No silent truncation: 200 files in, 200 rows out."""
    files = [
        {"path": f"mod_{i}.py", "source": f"def f{i}():\n    return {i}\n"} for i in range(200)
    ]
    result = await call_ok(client, "map_existing_codebase", {"files": files, "target_lang": "es"})
    assert result["summary"]["files_total"] == 200
    assert len(result["files"]) == 200
    assert {entry["path"] for entry in result["files"]} == {f["path"] for f in files}


# -- argument-encoding leniency (pinned SDK behavior) ----------------------


async def test_a_once_stringified_list_is_accepted(client: ClientSession) -> None:
    """FastMCP's lenient parse: '["print"]' is read as a list.

    Pinned from a real client failure (2026-08-08). Not our behavior to
    choose — the SDK's argument layer does it — but the suite should notice
    if an SDK upgrade takes it away.
    """
    result = await call_ok(
        client, "lookup_keyword_mapping", {"language": "es", "terms": '["print"]'}
    )
    assert result["mappings"]["builtins"]["print"]
    assert result["unmatched_terms"] == []


@pytest.mark.parametrize("terms", ["print", '"[\\"print\\"]"', "['print']x", "42"])
async def test_a_non_list_terms_value_is_rejected(client: ClientSession, terms: str) -> None:
    """Leniency stops at one level: a bare or double-encoded value fails."""
    message = await call_err(client, "lookup_keyword_mapping", {"language": "es", "terms": terms})
    assert "invalid_arguments" in message
    assert_sanitized(message)


async def test_argument_rejections_speak_in_the_servers_voice(
    client: ClientSession,
) -> None:
    """Decided under CORE-1744: wrap the SDK's raw pydantic dump.

    The dump quoted `input_value` — a prefix of the caller's source on the
    `source` fields — and linked to errors.pydantic.dev, which reads nothing
    like the engine's sanitized `code: message` errors. The wrapper keeps
    the useful half (which field, which constraint) and drops the value.
    """
    message = await call_err(client, "lookup_keyword_mapping", {"language": "es", "terms": "print"})
    assert message.startswith("invalid_arguments: ")
    assert "terms" in message
    assert "pydantic" not in message.lower()
    assert "validation error for" not in message
    assert "input_value" not in message


async def test_engine_failures_keep_their_machine_code(client: ClientSession) -> None:
    """The wrapper must not flatten the engine's own coded errors."""
    message = await call_err(
        client, "translate_to_native", {"source": "x = 1\n", "target_lang": "zz"}
    )
    assert message.startswith("unsupported_language: ") or "unsupported_language:" in message


# -- error hygiene on unexpected failures ----------------------------------


async def test_an_engine_boot_failure_is_sanitized(
    client: ClientSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unexpected exception must not hand its text to the model.

    Engine construction touches the filesystem, so its failures carry paths.
    Anything that is not an EngineError collapses to a generic message.
    """

    def explode() -> None:
        raise RuntimeError(
            "cannot open /Users/someone/legesher/libs/i18n/language-packs/python/es/packs/3.13.yml"
        )

    monkeypatch.setattr(server_module, "get_engine", explode)
    message = await call_err(
        client, "translate_to_native", {"source": "x = 1\n", "target_lang": "es"}
    )
    assert "internal_error" in message
    assert "/Users/" not in message
    assert ".yml" not in message
    assert_sanitized(message)


async def test_a_server_side_validation_failure_does_not_blame_the_caller(
    client: ClientSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A ValidationError from OUR model is a bug, not a bad request.

    The SDK's error wrapping covers the tool body and the result conversion,
    not just argument parsing — so a broken output model surfaces here too.
    Labeling that `invalid_arguments` would tell a model to fix a request
    that was fine, and it would retry forever.
    """

    class Broken:
        def translate(self, **kwargs: object) -> object:
            # Whatever the caller sent, the failure is on our side of the line.
            SourceFile(path="x", source="")  # min_length=1 -> ValidationError
            raise AssertionError("unreachable")

    monkeypatch.setattr(server_module, "get_engine", Broken)
    message = await call_err(
        client, "translate_to_native", {"source": "x = 1\n", "target_lang": "es"}
    )
    assert "internal_error" in message
    assert "invalid_arguments" not in message
    assert_sanitized(message)


async def test_an_unexpected_engine_error_does_not_echo_source(
    client: ClientSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode() -> None:
        raise RuntimeError(f"failed while handling {CANARY}")

    monkeypatch.setattr(server_module, "get_engine", explode)
    message = await call_err(
        client, "translate_to_native", {"source": f"{CANARY}\n", "target_lang": "es"}
    )
    assert "CANARY_SECRET" not in message


# -- resources -------------------------------------------------------------


@pytest.mark.parametrize("language", ["zz", "qqq", "EN", "..%2F..%2Fetc"])
async def test_terms_resource_rejects_unknown_languages(
    client: ClientSession, language: str
) -> None:
    with pytest.raises(McpError) as excinfo:
        await client.read_resource(AnyUrl(f"legesher://languages/{language}/terms"))
    assert_sanitized(str(excinfo.value))


async def test_unknown_resource_uri_fails_cleanly(client: ClientSession) -> None:
    with pytest.raises(McpError) as excinfo:
        await client.read_resource(AnyUrl("legesher://nonexistent"))
    assert_sanitized(str(excinfo.value))


# -- prompts ---------------------------------------------------------------

PROMPTS = [
    ("explain-in", "language"),
    ("translate-review", "target_lang"),
    ("legibility-report", "target_lang"),
]


@pytest.mark.parametrize("name,argument", PROMPTS)
async def test_prompt_requires_its_argument(
    client: ClientSession, name: str, argument: str
) -> None:
    with pytest.raises(McpError) as excinfo:
        await client.get_prompt(name, {})
    message = str(excinfo.value)
    assert argument in message
    assert_sanitized(message)


@pytest.mark.parametrize("name,argument", PROMPTS)
async def test_prompt_rejects_unknown_arguments(
    client: ClientSession, name: str, argument: str
) -> None:
    with pytest.raises(McpError) as excinfo:
        await client.get_prompt(name, {argument: "es", "unexpected": "value"})
    assert_sanitized(str(excinfo.value))


@pytest.mark.parametrize("name,argument", PROMPTS)
async def test_prompt_renders_with_its_argument(
    client: ClientSession, name: str, argument: str
) -> None:
    result = await client.get_prompt(name, {argument: "Spanish"})
    assert result.messages
    rendered = "\n".join(
        message.content.text for message in result.messages if hasattr(message.content, "text")
    )
    assert "Spanish" in rendered


async def test_unknown_prompt_fails_cleanly(client: ClientSession) -> None:
    with pytest.raises(McpError) as excinfo:
        await client.get_prompt("no-such-prompt", {})
    assert_sanitized(str(excinfo.value))


# -- protocol behavior -----------------------------------------------------


@pytest.mark.xfail(
    not IDENTIFIER_RULES_ARE_UNICODE_15_1,
    strict=True,
    reason="CORE-2349: before Unicode 15.1 (CPython 3.13) the server cannot load the ja "
    "pack at the default 3.13 target, and reports it as not found",
)
async def test_ja_translates_at_the_default_target(client: ClientSession) -> None:
    source = "def ok():\n    return True\n"
    result = await call_ok(client, "translate_to_native", {"source": source, "target_lang": "ja"})
    assert result["translated_source"] != source


async def test_concurrent_tool_calls_on_one_session(client: ClientSession) -> None:
    """One session, many in-flight calls: no interleaving, no lost replies."""
    # Every pack here loads at the default target on every supported
    # interpreter; ja's does not before 3.13 (CORE-2349, pinned above).
    languages = ["es", "ar", "fr", "de", "hi", "ko", "pt", "ru"]
    results: dict[str, str] = {}

    async def translate(language: str) -> None:
        result = await call_ok(
            client,
            "translate_to_native",
            {"source": "def ok():\n    return True\n", "target_lang": language},
        )
        results[language] = result["translated_source"]

    async with anyio.create_task_group() as tg:
        for language in languages:
            tg.start_soon(translate, language)

    assert set(results) == set(languages)
    # Each language produced its own rendering — no reply went to the wrong call.
    assert len(set(results.values())) == len(languages)


async def test_concurrent_calls_across_different_tools(client: ClientSession) -> None:
    """Mixed traffic on one session, including a deliberate failure."""
    outcomes: list[str] = []

    async def ok_call() -> None:
        await call_ok(client, "lookup_keyword_mapping", {"language": "es", "terms": ["def"]})
        outcomes.append("lookup")

    async def explain_call() -> None:
        await call_ok(client, "explain_in_language", {"source": "x = 1\n", "explain_in": "es"})
        outcomes.append("explain")

    async def failing_call() -> None:
        await call_err(client, "translate_to_native", {"source": "x = 1\n", "target_lang": "zz"})
        outcomes.append("failure")

    async with anyio.create_task_group() as tg:
        for _ in range(4):
            tg.start_soon(ok_call)
            tg.start_soon(explain_call)
            tg.start_soon(failing_call)

    assert outcomes.count("lookup") == 4
    assert outcomes.count("explain") == 4
    assert outcomes.count("failure") == 4


async def test_a_client_that_gives_up_mid_call_gets_a_clean_timeout(
    client: ClientSession,
) -> None:
    """Abandoning a call raises McpError rather than hanging or corrupting.

    Note the scope: the in-memory transport tears the session down once a
    request is abandoned, so session-level survival is a transport property,
    not something this server controls. What the server owes — that shared
    state stays usable afterwards — is asserted in the next test.
    """
    files = [{"path": f"m{i}.py", "source": "def f():\n    return 1\n"} for i in range(400)]
    with pytest.raises(McpError):
        await client.call_tool(
            "map_existing_codebase",
            {"files": files, "target_lang": "ar"},
            read_timeout_seconds=timedelta(milliseconds=1),
        )


async def test_an_abandoned_call_does_not_corrupt_shared_server_state() -> None:
    """The process-wide engine must survive a call nobody waited for.

    The engine singleton, its translator cache, and its pack-discovery cache
    are shared across every session. A call cancelled while holding the
    engine lock would deadlock every session after it — so the real test is
    that a *fresh* session still works once an abandoned one is gone.
    """
    files = [{"path": f"m{i}.py", "source": "def f():\n    return 1\n"} for i in range(400)]
    try:
        async with create_connected_server_and_client_session(server_module.mcp) as abandoning:
            await abandoning.call_tool(
                "map_existing_codebase",
                {"files": files, "target_lang": "ar"},
                read_timeout_seconds=timedelta(milliseconds=1),
            )
    except BaseException:  # noqa: BLE001 — the abandonment is the point
        pass

    async with create_connected_server_and_client_session(server_module.mcp) as fresh:
        result = await call_ok(
            fresh, "lookup_keyword_mapping", {"language": "es", "terms": ["def"]}
        )
        assert result["mappings"]["keywords"]["def"]


async def test_repeated_identical_calls_are_stable(client: ClientSession) -> None:
    """The idempotentHint the tools advertise has to be true."""
    args = {"source": "def ok():\n    return True\n", "target_lang": "ar"}
    first = await call_ok(client, "translate_to_native", args)
    for _ in range(3):
        assert await call_ok(client, "translate_to_native", args) == first
