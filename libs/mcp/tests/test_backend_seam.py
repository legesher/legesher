"""The tool-level backend seam (CORE-1420).

The MCP layer is transport + schema; everything a tool call or resource
read *does* happens behind the ``Backend`` protocol. These tests drive a
fake backend through a real MCP session to pin the seam's contract:

- every tool renders exactly what the backend returned (the tool bodies
  add nothing);
- argument validation still runs in front of the backend — a bad request
  is rejected before the backend is ever called;
- resource reads route through the backend too, with the version gate
  staying on the server side of the seam.

``LocalBackend``'s orchestration semantics are pinned by the existing
per-tool suites, which exercise the default server end to end.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from mcp import ClientSession, McpError
from mcp.shared.memory import create_connected_server_and_client_session
from pydantic import AnyUrl

from legesher_mcp.backend import Backend, LanguageTerms, LocalBackend
from legesher_mcp.engine import EngineError, LanguageInfo
from legesher_mcp.schemas import (
    CodebaseMapResult,
    CodebaseMapSummary,
    ConstructMapping,
    ExplainMaterial,
    FileMapEntry,
    IdentifierProposal,
    IdentifierValidationResult,
    IdentifierVerdict,
    KeywordMappings,
    LookupResult,
    SourceFile,
    TranslationResult,
    ValidationInfo,
)
from legesher_mcp.server import create_server
from tests.conftest import call_err, call_ok

pytestmark = pytest.mark.anyio


class FakeBackend:
    """A canned backend that records every call it receives."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def translate_to_native(
        self,
        *,
        source: str,
        source_lang: str,
        target_lang: str,
        python_version: str,
        verify_round_trip: bool,
    ) -> TranslationResult:
        self.calls.append(
            (
                "translate_to_native",
                {
                    "source": source,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "python_version": python_version,
                    "verify_round_trip": verify_round_trip,
                },
            )
        )
        return TranslationResult(
            translated_source="<fake native rendering>",
            source_lang=source_lang,
            target_lang=target_lang,
            python_version=python_version,
            pivoted=True,
        )

    async def translate_to_source(
        self,
        *,
        source: str,
        source_lang: str,
        python_version: str,
        verify_round_trip: bool,
    ) -> TranslationResult:
        self.calls.append(
            (
                "translate_to_source",
                {
                    "source": source,
                    "source_lang": source_lang,
                    "python_version": python_version,
                    "verify_round_trip": verify_round_trip,
                },
            )
        )
        return TranslationResult(
            translated_source="<fake source rendering>",
            source_lang=source_lang,
            target_lang="en",
            python_version=python_version,
            pivoted=False,
        )

    async def explain_in_language(
        self,
        *,
        source: str,
        explain_in: str,
        code_lang: str,
        python_version: str,
        include_translation: bool,
    ) -> ExplainMaterial:
        self.calls.append(
            (
                "explain_in_language",
                {
                    "source": source,
                    "explain_in": explain_in,
                    "code_lang": code_lang,
                    "python_version": python_version,
                    "include_translation": include_translation,
                },
            )
        )
        return ExplainMaterial(
            code_lang=code_lang,
            explain_in=explain_in,
            python_version=python_version,
            constructs=[
                ConstructMapping(
                    construct="def",
                    in_code_lang="def",
                    in_explain_lang="<fake term>",
                    category="keywords",
                )
            ],
            validation=ValidationInfo(valid=True),
        )

    async def lookup_keyword_mapping(
        self,
        *,
        language: str,
        terms: list[str] | None,
        python_version: str,
    ) -> LookupResult:
        self.calls.append(
            (
                "lookup_keyword_mapping",
                {"language": language, "terms": terms, "python_version": python_version},
            )
        )
        return LookupResult(
            language=language,
            python_version=python_version,
            mappings=KeywordMappings(keywords={"def": "<fake term>"}),
            unmatched_terms=["<fake unmatched>"],
        )

    async def validate_identifier_translations(
        self,
        *,
        proposals: list[IdentifierProposal],
        target_lang: str,
        glossary: dict[str, str] | None,
        python_version: str,
    ) -> IdentifierValidationResult:
        self.calls.append(
            (
                "validate_identifier_translations",
                {
                    "proposals": proposals,
                    "target_lang": target_lang,
                    "glossary": glossary,
                    "python_version": python_version,
                },
            )
        )
        return IdentifierValidationResult(
            target_lang=target_lang,
            python_version=python_version,
            results=[IdentifierVerdict(source="greet", translation="<fake rendering>", ok=True)],
            accepted={"greet": "<fake rendering>"},
        )

    async def map_existing_codebase(
        self,
        *,
        files: list[SourceFile],
        target_lang: str,
        source_lang: str,
        python_version: str,
        include_translations: bool,
    ) -> CodebaseMapResult:
        self.calls.append(
            (
                "map_existing_codebase",
                {
                    "files": files,
                    "target_lang": target_lang,
                    "source_lang": source_lang,
                    "python_version": python_version,
                    "include_translations": include_translations,
                },
            )
        )
        return CodebaseMapResult(
            source_lang=source_lang,
            target_lang=target_lang,
            python_version=python_version,
            files=[FileMapEntry(path=files[0].path, translatable=True)],
            summary=CodebaseMapSummary(
                files_total=len(files),
                files_translatable=1,
                constructs_found=0,
                constructs_mapped=0,
                coverage_ratio=None,
                pivoted=False,
            ),
        )

    async def list_languages(self) -> list[LanguageInfo]:
        self.calls.append(("list_languages", {}))
        return [
            LanguageInfo(
                code="qx",
                name="Fake",
                native="Fake",
                rtl=False,
                status="experimental",
                pack_available=True,
            )
        ]

    async def language_terms(self, *, language: str, python_version: str) -> LanguageTerms:
        self.calls.append(
            ("language_terms", {"language": language, "python_version": python_version})
        )
        if language == "zz":
            raise EngineError("unsupported_language", "Unsupported language code: 'zz'.")
        return LanguageTerms(
            language=language,
            python_version=python_version,
            keywords={"def": "<fake term>"},
            builtins={},
            exceptions={},
            implicit_params={},
        )


@pytest.fixture
def backend() -> FakeBackend:
    return FakeBackend()


@pytest.fixture
async def fake_client(backend: FakeBackend) -> Any:
    async with create_connected_server_and_client_session(
        create_server(backend=backend)
    ) as session:
        yield session


def _only_call(backend: FakeBackend, expected_method: str) -> dict[str, Any]:
    assert [method for method, _ in backend.calls] == [expected_method]
    return backend.calls[0][1]


# -- tools render the backend's result, verbatim ---------------------------


async def test_translate_to_native_renders_the_backend_result(
    fake_client: ClientSession, backend: FakeBackend
) -> None:
    result = await call_ok(
        fake_client, "translate_to_native", {"source": "x = 1\n", "target_lang": "es"}
    )
    assert result["translated_source"] == "<fake native rendering>"
    assert result["pivoted"] is True
    # Defaults were resolved by the schema layer before the backend saw them.
    assert _only_call(backend, "translate_to_native") == {
        "source": "x = 1\n",
        "source_lang": "en",
        "target_lang": "es",
        "python_version": "3.13",
        "verify_round_trip": False,
    }


async def test_translate_to_source_renders_the_backend_result(
    fake_client: ClientSession, backend: FakeBackend
) -> None:
    result = await call_ok(
        fake_client, "translate_to_source", {"source": "x = 1\n", "source_lang": "es"}
    )
    assert result["translated_source"] == "<fake source rendering>"
    assert result["target_lang"] == "en"
    assert _only_call(backend, "translate_to_source") == {
        "source": "x = 1\n",
        "source_lang": "es",
        "python_version": "3.13",
        "verify_round_trip": False,
    }


async def test_explain_in_language_renders_the_backend_result(
    fake_client: ClientSession, backend: FakeBackend
) -> None:
    result = await call_ok(
        fake_client, "explain_in_language", {"source": "def f(): pass\n", "explain_in": "es"}
    )
    assert result["constructs"][0]["in_explain_lang"] == "<fake term>"
    assert _only_call(backend, "explain_in_language") == {
        "source": "def f(): pass\n",
        "explain_in": "es",
        "code_lang": "en",
        "python_version": "3.13",
        "include_translation": False,
    }


async def test_lookup_keyword_mapping_renders_the_backend_result(
    fake_client: ClientSession, backend: FakeBackend
) -> None:
    result = await call_ok(
        fake_client, "lookup_keyword_mapping", {"language": "es", "terms": ["def"]}
    )
    assert result["mappings"]["keywords"] == {"def": "<fake term>"}
    assert result["unmatched_terms"] == ["<fake unmatched>"]
    assert _only_call(backend, "lookup_keyword_mapping") == {
        "language": "es",
        "terms": ["def"],
        "python_version": "3.13",
    }


async def test_validate_identifier_translations_renders_the_backend_result(
    fake_client: ClientSession, backend: FakeBackend
) -> None:
    result = await call_ok(
        fake_client,
        "validate_identifier_translations",
        {"proposals": [{"source": "greet", "translation": "saludar"}], "target_lang": "es"},
    )
    assert result["accepted"] == {"greet": "<fake rendering>"}
    args = _only_call(backend, "validate_identifier_translations")
    # The schema layer parsed the raw dicts into typed proposals already.
    assert args["proposals"] == [IdentifierProposal(source="greet", translation="saludar")]
    assert args["glossary"] is None


async def test_map_existing_codebase_renders_the_backend_result(
    fake_client: ClientSession, backend: FakeBackend
) -> None:
    result = await call_ok(
        fake_client,
        "map_existing_codebase",
        {"files": [{"path": "a.py", "source": "x = 1\n"}], "target_lang": "es"},
    )
    assert result["files"][0]["path"] == "a.py"
    assert result["summary"]["files_total"] == 1
    args = _only_call(backend, "map_existing_codebase")
    assert args["files"] == [SourceFile(path="a.py", source="x = 1\n")]
    assert args["include_translations"] is False


# -- argument validation happens in front of the backend --------------------


async def test_missing_required_argument_never_reaches_the_backend(
    fake_client: ClientSession, backend: FakeBackend
) -> None:
    message = await call_err(fake_client, "translate_to_native", {"source": "x = 1\n"})
    assert message
    assert backend.calls == []


async def test_malformed_language_code_never_reaches_the_backend(
    fake_client: ClientSession, backend: FakeBackend
) -> None:
    """The registry-pattern gate (path-traversal guard) is the server's."""
    message = await call_err(
        fake_client,
        "translate_to_native",
        {"source": "x = 1\n", "target_lang": "../../etc"},
    )
    assert message
    assert backend.calls == []


# -- resources route through the backend ------------------------------------


async def test_languages_catalog_renders_the_backend_list(
    fake_client: ClientSession, backend: FakeBackend
) -> None:
    result = await fake_client.read_resource(AnyUrl("legesher://languages"))
    content = result.contents[0]
    catalog = json.loads(getattr(content, "text", ""))
    assert catalog == [
        {
            "code": "qx",
            "name": "Fake",
            "native": "Fake",
            "rtl": False,
            "status": "experimental",
            "pack_available": True,
        }
    ]
    assert [method for method, _ in backend.calls] == ["list_languages"]


async def test_terms_resource_renders_the_backend_document(
    fake_client: ClientSession, backend: FakeBackend
) -> None:
    result = await fake_client.read_resource(AnyUrl("legesher://languages/es/terms"))
    content = result.contents[0]
    document = json.loads(getattr(content, "text", ""))
    assert document["language"] == "es"
    assert document["keywords"] == {"def": "<fake term>"}
    assert [method for method, _ in backend.calls] == ["language_terms"]


async def test_terms_resource_version_gate_stays_in_front_of_the_backend(
    fake_client: ClientSession, backend: FakeBackend
) -> None:
    """An unsupported python_version is rejected before the backend runs."""
    with pytest.raises(McpError):
        await fake_client.read_resource(AnyUrl("legesher://languages/es/terms/9.9"))
    assert backend.calls == []


async def test_terms_resource_backend_failure_surfaces_its_code(
    fake_client: ClientSession, backend: FakeBackend
) -> None:
    """An EngineError from the backend becomes the resource error, verbatim.

    The backend contract: expected failures raise EngineError with a machine
    code and a content-free message, safe to hand to the caller.
    """
    with pytest.raises(McpError) as excinfo:
        await fake_client.read_resource(AnyUrl("legesher://languages/zz/terms"))
    assert "unsupported_language" in str(excinfo.value)
    assert [method for method, _ in backend.calls] == ["language_terms"]


# -- the default backend implements the protocol ----------------------------


def test_local_backend_satisfies_the_protocol() -> None:
    assert isinstance(LocalBackend(), Backend)
