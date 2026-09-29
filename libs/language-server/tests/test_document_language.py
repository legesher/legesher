"""Each document is served in its own language (CORE-1976).

The server used to read one language at ``initialize`` and answer every request
with it, so a file in any other language matched nothing and came back as a
successful, empty answer. Started in Amharic, the server returned 185
semantic-token integers for the Amharic file and none at all for the French and
Arabic files open beside it, and hover and diagnostics were in the same state.

The client now names each document's language with a
``legesher/documentLanguage`` notification. These tests decode that
notification with pygls's own JSON hook, hand it to the handler registered
under its wire name, and then ask the providers what they answer, which is the
path a client's message takes.

Documents are assembled from each pack's own vocabulary rather than typed out,
so a pack correction cannot leave these tests asserting stale spellings. The
languages that carry the non-empty assertions (French, vocalised Arabic,
Ethiopic) are ones whose words the pure-Python tokenizer on CPython 3.10 and
3.11 still reads whole, so those assertions mean the same on every interpreter
CI runs.
"""

import functools
import json

import pytest
from legesher_i18n import LanguagePackLoader, get_active_language_codes
from lsprotocol.types import (
    ClientCapabilities,
    CompletionParams,
    DiagnosticWorkspaceClientCapabilities,
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    DocumentDiagnosticParams,
    HoverParams,
    MessageType,
    Position,
    SemanticTokensParams,
    SemanticTokensWorkspaceClientCapabilities,
    TextDocumentContentChangeWholeDocument,
    TextDocumentIdentifier,
    TextDocumentItem,
    VersionedTextDocumentIdentifier,
    WorkspaceClientCapabilities,
)

from legesher_language_server.config import LanguageServerConfig
from legesher_language_server.enhanced_intelligence import EnhancedIntelligenceProxy
from legesher_language_server.server import LegesherLanguageServer

# The language the server is started with, as in the log the ticket was filed
# from: `en->am`, with French and Arabic files open beside the Amharic one.
CONFIGURED = "am"

# One loader for the test's own reads. Its cache is per instance, so a fresh
# loader per read would re-parse the pack every time.
_LOADER = LanguagePackLoader()


def _pack(language: str):
    return _LOADER.load(language=language, target="python", version="3.10")


@functools.cache
def lesson(language: str) -> str:
    """A short program written in ``language``, spelled from its own pack.

    Every recognisable word in it is translated. It deliberately calls no
    builtin under its English name: English builtins are highlighted whatever
    pack is loaded, so one would make a document in the wrong language look
    served.
    """
    pack = _pack(language)
    kw, builtins = pack.keywords, pack.builtins
    return (
        f"{kw['def']} average(scores):\n"
        f"    {kw['if']} {kw['not']} scores:\n"
        f"        {kw['return']} {kw['None']}\n"
        f"    {builtins['print']}(scores)\n"
        f"    {kw['return']} scores\n"
    )


def make_server(language: str = CONFIGURED) -> LegesherLanguageServer:
    config = LanguageServerConfig(
        source_language="en",
        target_language=language,
        file_language=language,
        working_language=language,
        python_version="3.10",
        enhanced_intelligence_enabled=False,
    )
    return LegesherLanguageServer(config)


@pytest.fixture
def server() -> LegesherLanguageServer:
    return make_server()


@pytest.fixture
def shown_messages(monkeypatch):
    """Capture outbound window/showMessage notifications, the user-visible surface."""
    captured = []

    def record(self, params):
        captured.append(params)

    monkeypatch.setattr(LegesherLanguageServer, "window_show_message", record)
    return captured


async def notify(server: LegesherLanguageServer, params: object) -> None:
    """Deliver a `legesher/documentLanguage` message the way one arrives off the wire.

    The JSON is decoded by pygls's own object hook, which hands a custom
    method's params over as a namedtuple rather than a dict, and the message
    goes to the handler registered under the literal wire name. Calling the
    handler with a dict would test a shape no client message has, and a test
    that skipped the registration would pass with it missing.
    """
    raw = json.dumps({"jsonrpc": "2.0", "method": "legesher/documentLanguage", "params": params})
    message = json.loads(raw, object_hook=server.protocol.structure_message)
    handler = server.protocol._get_handler(message.method)
    await handler(message.params)


async def tell(server: LegesherLanguageServer, uri: str, language: object) -> None:
    """Name a document's language, as the client does."""
    await notify(server, {"uri": uri, "language": language})


async def open_document(server: LegesherLanguageServer, uri: str, text: str) -> None:
    await server.on_did_open(
        DidOpenTextDocumentParams(
            text_document=TextDocumentItem(uri=uri, language_id="python", version=1, text=text)
        )
    )


async def change_document(
    server: LegesherLanguageServer, uri: str, text: str, version: int = 2
) -> None:
    await server.on_did_change(
        DidChangeTextDocumentParams(
            text_document=VersionedTextDocumentIdentifier(uri=uri, version=version),
            content_changes=[TextDocumentContentChangeWholeDocument(text=text)],
        )
    )


async def close_document(server: LegesherLanguageServer, uri: str) -> None:
    await server.on_did_close(
        DidCloseTextDocumentParams(text_document=TextDocumentIdentifier(uri=uri))
    )


async def tokens_of(server: LegesherLanguageServer, uri: str):
    """The semantic-token response exactly as the server returns it."""
    return await server.on_semantic_tokens_full(
        SemanticTokensParams(text_document=TextDocumentIdentifier(uri=uri))
    )


async def token_data(server: LegesherLanguageServer, uri: str) -> list[int]:
    result = await tokens_of(server, uri)
    assert result is not None, f"no semantic-token response for {uri}"
    return list(result.data)


_OWN_LANGUAGE_TOKENS: dict[str, list[int]] = {}


async def own_language_tokens(language: str) -> list[int]:
    """What a server started in ``language`` itself returns for its lesson.

    The reference every per-document answer is held to: a document the client
    has named must be served exactly as if the server had been started in its
    language, which is the only configuration that ever worked before. Kept
    per language, since it depends on nothing but the pack.
    """
    if language not in _OWN_LANGUAGE_TOKENS:
        reference = make_server(language)
        uri = f"file:///reference/{language}.py"
        await open_document(reference, uri, lesson(language))
        _OWN_LANGUAGE_TOKENS[language] = await token_data(reference, uri)
    return _OWN_LANGUAGE_TOKENS[language]


async def hover_text(server: LegesherLanguageServer, uri: str, line: int, character: int):
    hover = await server.on_hover(
        HoverParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=line, character=character),
        )
    )
    return None if hover is None else hover.contents.value


class TestTwoLanguagesOneServer:
    """The ticket's scenario: one server, files in languages it was not started in."""

    async def test_documents_in_two_languages_both_highlight(self, server):
        """Acceptance: two languages, one server, both return non-empty tokens.

        French and Arabic are the two files the ticket's log shows returning
        zero integers on a server started in Amharic.
        """
        for language in ("fr", "ar"):
            uri = f"file:///class/{language}.py"
            await tell(server, uri, language)
            await open_document(server, uri, lesson(language))

        for language in ("fr", "ar"):
            data = await token_data(server, f"file:///class/{language}.py")
            assert data, (
                f"the {language} document returned no semantic tokens on a server "
                f"started in {CONFIGURED}; highlighting is still session-scoped"
            )
            assert data == await own_language_tokens(language), (
                f"the {language} document is not highlighted the way a server "
                f"started in {language} highlights it"
            )

    async def test_a_document_not_named_is_still_served_in_the_configured_language(self, server):
        """The guard that makes the test above mean something.

        Without the notification the French document falls back to the
        configured Amharic and matches nothing, which is the defect. If this
        ever returned French tokens, the test above could pass with the
        notification ignored.
        """
        uri = "file:///class/unnamed.py"
        await open_document(server, uri, lesson("fr"))

        assert await token_data(server, uri) == [], (
            "a French document the client never named was highlighted on a server "
            f"started in {CONFIGURED}; the fallback is not the configured language"
        )

    async def test_interleaved_requests_do_not_share_a_language(self, server):
        """The decisive pair in the ticket was two requests 33ms apart on one server.

        Serving one document must leave nothing behind that the next request,
        for a document in another language, picks up.
        """
        documents = {language: f"file:///class/{language}.py" for language in ("fr", "ar", "am")}
        for language, uri in documents.items():
            await tell(server, uri, language)
            await open_document(server, uri, lesson(language))

        expected = {language: await own_language_tokens(language) for language in documents}
        for language in ("fr", "am", "ar", "fr", "ar", "am"):
            assert await token_data(server, documents[language]) == expected[language], (
                f"the {language} document changed answer depending on what was served before it"
            )

    @pytest.mark.parametrize("language", sorted(get_active_language_codes()))
    async def test_every_pack_is_served_on_a_server_started_in_another_language(self, language):
        """Every shipped pack routes to its own vocabulary, not only the few used above.

        Equality with the pack's own server is asserted rather than
        non-emptiness: it holds on every interpreter, including the ones whose
        tokenizer splits some scripts' words, and it is what "served in its own
        language" means.
        """
        server = make_server("fr" if language == CONFIGURED else CONFIGURED)
        uri = f"file:///sweep/{language}.py"
        await tell(server, uri, language)
        await open_document(server, uri, lesson(language))

        assert server.document_language(uri) == language
        assert await token_data(server, uri) == await own_language_tokens(language), (
            f"a {language} document on a server started in "
            f"{server.config.file_language} is not served in {language}"
        )


class TestHoverInAnotherLanguage:
    """Acceptance: hover answers for a file in a language other than the configured one."""

    async def test_hover_explains_a_keyword_in_a_language_the_server_was_not_started_in(
        self, server
    ):
        uri = "file:///class/ar.py"
        await tell(server, uri, "ar")
        await open_document(server, uri, lesson("ar"))

        text = await hover_text(server, uri, line=0, character=1)

        assert text is not None, (
            f"hover returned nothing for an Arabic keyword on a server started in {CONFIGURED}"
        )
        assert _pack("ar").keywords["def"] in text and "`def`" in text, (
            f"hover does not name the Arabic keyword and its English equivalent: {text[:200]!r}"
        )

    async def test_hover_explains_a_translated_builtin(self, server):
        uri = "file:///class/fr.py"
        await tell(server, uri, "fr")
        await open_document(server, uri, lesson("fr"))

        text = await hover_text(server, uri, line=3, character=5)

        assert text is not None, "hover returned nothing for a French builtin"
        assert _pack("fr").builtins["print"] in text and "print" in text, (
            f"hover does not explain the French builtin: {text[:200]!r}"
        )

    async def test_hover_says_nothing_for_a_document_left_in_the_configured_language(self, server):
        """The guard: the same hover without the notification is the defect."""
        uri = "file:///class/unnamed.py"
        await open_document(server, uri, lesson("ar"))

        assert await hover_text(server, uri, line=0, character=1) is None


class TestOtherProviders:
    """Diagnostics and completion take the document's language too."""

    async def test_diagnostics_parse_the_document_in_its_own_language(self, server):
        uri = "file:///class/fr.py"
        await tell(server, uri, "fr")
        await open_document(server, uri, lesson("fr"))

        report = await server.on_diagnostic(
            DocumentDiagnosticParams(text_document=TextDocumentIdentifier(uri=uri))
        )

        assert report.items == [], (
            "a valid French program was reported as broken: "
            f"{[item.message for item in report.items]}"
        )

    async def test_diagnostics_report_the_defect_without_the_notification(self, server):
        """The guard: parsed as Amharic, the French keywords are a syntax error."""
        uri = "file:///class/unnamed.py"
        await open_document(server, uri, lesson("fr"))

        report = await server.on_diagnostic(
            DocumentDiagnosticParams(text_document=TextDocumentIdentifier(uri=uri))
        )

        assert report.items, "French parsed cleanly as Amharic; the guard is not guarding"

    async def test_completion_offers_the_document_languages_keywords(self, server):
        uri = "file:///class/fr.py"
        await tell(server, uri, "fr")
        await open_document(server, uri, lesson("fr"))

        result = await server.on_completion(
            CompletionParams(
                text_document=TextDocumentIdentifier(uri=uri),
                position=Position(line=4, character=0),
            )
        )
        labels = {item.label for item in result.items}

        assert _pack("fr").keywords["def"] in labels, "French keywords were not offered"
        assert _pack(CONFIGURED).keywords["def"] not in labels, (
            "the configured language's keywords were offered in a French document"
        )


class TestTheLanguageMap:
    """What the server remembers, and when it forgets."""

    async def test_a_document_never_named_uses_the_configured_file_language(self, server):
        assert server.document_language("file:///never-named.py") == CONFIGURED

    async def test_the_language_can_arrive_before_the_document_opens(self, server):
        """The client names a document just before its didOpen, so both orders must work."""
        uri = "file:///class/fr.py"
        await tell(server, uri, "fr")
        await open_document(server, uri, lesson("fr"))

        assert server.document_language(uri) == "fr"
        assert await token_data(server, uri) == await own_language_tokens("fr")

    async def test_a_later_report_replaces_the_earlier_one(self, server):
        uri = "file:///class/doc.py"
        await tell(server, uri, "fr")
        await open_document(server, uri, lesson("ar"))
        await tell(server, uri, "ar")

        assert server.document_language(uri) == "ar"
        assert await token_data(server, uri) == await own_language_tokens("ar")

    async def test_closing_a_document_forgets_its_language(self, server):
        uri = "file:///class/fr.py"
        await tell(server, uri, "fr")
        await open_document(server, uri, lesson("fr"))

        await close_document(server, uri)

        assert server.document_language(uri) == CONFIGURED, (
            "a closed document kept its language; a reopened file would be served "
            "in whatever it was last, not what the client says now"
        )

    async def test_the_configured_file_language_is_read_at_request_time(self, server):
        """The fallback follows initialize, not whatever it was at construction."""
        server.config.file_language = "fr"
        server.config.target_language = "fr"

        assert server.document_language("file:///never-named.py") == "fr"


class TestRefreshAfterALanguageChange:
    """An editor holds on to the answers it already has, so a change has to be announced."""

    @pytest.fixture
    def refreshes(self, server, monkeypatch):
        server.protocol.client_capabilities = ClientCapabilities(
            workspace=WorkspaceClientCapabilities(
                semantic_tokens=SemanticTokensWorkspaceClientCapabilities(refresh_support=True),
                diagnostics=DiagnosticWorkspaceClientCapabilities(refresh_support=True),
            )
        )
        sent: list[str] = []
        monkeypatch.setattr(
            LegesherLanguageServer,
            "workspace_semantic_tokens_refresh",
            lambda self, params, callback=None: sent.append("semanticTokens"),
        )
        monkeypatch.setattr(
            LegesherLanguageServer,
            "workspace_diagnostic_refresh",
            lambda self, params, callback=None: sent.append("diagnostic"),
        )
        return sent

    async def test_a_new_language_for_an_open_document_asks_the_client_to_refresh(
        self, server, refreshes
    ):
        uri = "file:///class/doc.py"
        await open_document(server, uri, lesson("fr"))

        await tell(server, uri, "fr")

        assert sorted(refreshes) == ["diagnostic", "semanticTokens"], (
            "the language of an open document changed and the editor was not asked "
            f"to re-request what it had already drawn: {refreshes}"
        )

    async def test_naming_a_document_before_it_opens_needs_no_refresh(self, server, refreshes):
        """The usual order: nothing has been drawn yet, so there is nothing to redraw."""
        uri = "file:///class/doc.py"
        await tell(server, uri, "fr")
        await open_document(server, uri, lesson("fr"))

        assert refreshes == []

    async def test_repeating_the_same_language_does_not_refresh(self, server, refreshes):
        uri = "file:///class/doc.py"
        await tell(server, uri, "fr")
        await open_document(server, uri, lesson("fr"))

        await tell(server, uri, "fr")

        assert refreshes == []

    async def test_a_client_without_refresh_support_is_not_sent_one(self, server, monkeypatch):
        sent: list[str] = []
        monkeypatch.setattr(
            LegesherLanguageServer,
            "workspace_semantic_tokens_refresh",
            lambda self, params, callback=None: sent.append("semanticTokens"),
        )
        server.protocol.client_capabilities = ClientCapabilities()
        uri = "file:///class/doc.py"
        await open_document(server, uri, lesson("fr"))

        await tell(server, uri, "fr")

        assert sent == []


class TestALanguageThatCannotBeServed:
    """Acceptance: where a language cannot be served, that is visible, not an empty success."""

    async def test_no_pack_means_no_answer_rather_than_an_empty_one(self, server, shown_messages):
        uri = "file:///class/xx.py"
        await tell(server, uri, "xx")
        await open_document(server, uri, lesson("fr"))

        assert await tokens_of(server, uri) is None, (
            "a document in a language with no pack came back as a successful, empty "
            "token set, which reads as a working file with nothing to highlight"
        )

    async def test_the_user_is_told_once_per_language(self, server, shown_messages):
        for name in ("one", "two"):
            uri = f"file:///class/{name}.py"
            await tell(server, uri, "xx")
            await open_document(server, uri, lesson("fr"))
            await tokens_of(server, uri)
        await tell(server, "file:///class/three.py", "zz")
        await open_document(server, "file:///class/three.py", lesson("fr"))

        warnings = [m for m in shown_messages if m.type == MessageType.Warning]
        assert len(warnings) == 2, (
            f"expected one notice for each unservable language, got {len(warnings)}: "
            f"{[m.message for m in warnings]}"
        )
        assert "'xx'" in warnings[0].message and "'zz'" in warnings[1].message, (
            f"the notices do not name the language: {[m.message for m in warnings]}"
        )

    async def test_naming_documents_that_never_open_warns_nobody(self, server, shown_messages):
        """The notice is for documents in front of the user, so it waits for the open.

        A client that names documents it never opens, in languages no pack can
        serve, would otherwise raise one warning per bogus language.
        """
        for index in range(20):
            await tell(server, f"file:///never/{index}.py", f"q{chr(ord('a') + index)}")

        class RunningProxy:
            def is_running(self):
                return True

            async def forward_hover(self, params):
                return None

            async def forward_diagnostic(self, uri, content, language=None):
                return []

        # Asking about a document that never opened is not opening it either.
        server.intelligence_proxy = RunningProxy()
        await hover_text(server, "file:///never/1.py", line=0, character=1)
        await server.on_diagnostic(
            DocumentDiagnosticParams(text_document=TextDocumentIdentifier(uri="file:///never/2.py"))
        )

        assert shown_messages == [], [m.message for m in shown_messages]

        await open_document(server, "file:///never/0.py", lesson("fr"))

        assert len(shown_messages) == 1 and "'qa'" in shown_messages[0].message, [
            m.message for m in shown_messages
        ]

    async def test_status_names_the_document_it_cannot_serve(self, server, shown_messages):
        served, unserved = "file:///class/fr.py", "file:///class/xx.py"
        await tell(server, served, "fr")
        await open_document(server, served, lesson("fr"))
        await tell(server, unserved, "xx")
        await open_document(server, unserved, lesson("fr"))

        payload = await server.protocol._get_handler("legesher/status")(None)
        documents = {entry["uri"]: entry for entry in payload["documents"]}

        assert documents[served]["language"] == "fr"
        assert documents[served]["served"] is True
        assert documents[unserved]["language"] == "xx"
        assert documents[unserved]["served"] is False
        assert "'xx'" in documents[unserved]["detail"], documents[unserved]
        # The enhanced-intelligence answer the status already carried is intact.
        assert "enabled" in payload and "running" in payload and "serverPath" in payload

    async def test_status_says_where_each_language_came_from(self, server):
        named, unnamed = "file:///class/fr.py", "file:///class/unnamed.py"
        await tell(server, named, "fr")
        await open_document(server, named, lesson("fr"))
        await open_document(server, unnamed, lesson("am"))

        payload = await server.protocol._get_handler("legesher/status")(None)
        documents = {entry["uri"]: entry for entry in payload["documents"]}

        assert documents[named]["source"] == "client"
        assert documents[unnamed]["source"] == "configured"
        assert documents[unnamed]["language"] == CONFIGURED

    async def test_a_pack_that_will_not_load_is_reported_the_same_way(
        self, server, shown_messages, monkeypatch
    ):
        """A registered language whose pack is missing, as when it is not installed."""
        from legesher_i18n import PackNotFoundError

        text = lesson("fr")  # spelled while the pack still loads
        real_load = LanguagePackLoader.load

        def load(self, language, *args, **kwargs):
            if language == "fr":
                raise PackNotFoundError("fr", "python", "3.10", "/nowhere/3.10.yml")
            return real_load(self, language, *args, **kwargs)

        monkeypatch.setattr(LanguagePackLoader, "load", load)
        uri = "file:///class/fr.py"
        await tell(server, uri, "fr")
        await open_document(server, uri, text)

        assert await tokens_of(server, uri) is None
        assert any("'fr'" in m.message for m in shown_messages), (
            f"a pack that failed to load was not reported: {[m.message for m in shown_messages]}"
        )

    async def test_no_other_provider_answers_for_it_either(self, server, shown_messages):
        """Diagnostics in particular: parsing untranslated keywords reports bogus syntax errors."""
        uri = "file:///class/xx.py"
        await tell(server, uri, "xx")
        await open_document(server, uri, lesson("fr"))

        report = await server.on_diagnostic(
            DocumentDiagnosticParams(text_document=TextDocumentIdentifier(uri=uri))
        )
        completion = await server.on_completion(
            CompletionParams(
                text_document=TextDocumentIdentifier(uri=uri),
                position=Position(line=0, character=0),
            )
        )

        assert report.items == [], (
            "syntax errors were reported for a language the server cannot read"
        )
        assert completion.items == []
        assert await hover_text(server, uri, line=0, character=1) is None

    async def test_a_language_notice_does_not_use_up_the_enhanced_intelligence_one(
        self, server, shown_messages
    ):
        """Two different problems each get their one notice."""
        server._notify_degraded_once("enhanced intelligence is not running")
        await tell(server, "file:///class/xx.py", "xx")
        await open_document(server, "file:///class/xx.py", lesson("fr"))

        assert len(shown_messages) == 2, [m.message for m in shown_messages]

    async def test_a_malformed_language_is_unservable_and_not_echoed_whole(
        self, server, shown_messages
    ):
        uri = "file:///class/odd.py"
        await tell(server, uri, "x" * 5000)
        await open_document(server, uri, lesson("fr"))

        assert await tokens_of(server, uri) is None
        assert shown_messages and len(shown_messages[0].message) < 500, (
            "a malformed language value was echoed into the user's notice whole"
        )


class TestTheNotificationContract:
    """What a client that is not VS Code can rely on."""

    async def test_a_notification_without_a_uri_changes_nothing(self, server):
        await notify(server, {"language": "fr"})
        await notify(server, None)

        payload = await server.protocol._get_handler("legesher/status")(None)
        assert payload["documents"] == []

    async def test_params_handed_over_as_a_plain_dict_are_read_too(self, server):
        """pygls decodes params into a namedtuple today; a dict must work as well."""
        handler = server.protocol._get_handler("legesher/documentLanguage")

        await handler({"uri": "file:///class/fr.py", "language": "fr"})

        assert server.document_language("file:///class/fr.py") == "fr"

    async def test_a_language_that_is_not_a_string_is_unservable(self, server, shown_messages):
        uri = "file:///class/odd.py"
        await tell(server, uri, 42)
        await open_document(server, uri, lesson("fr"))

        assert await tokens_of(server, uri) is None


class TestEnhancedIntelligenceForwarding:
    """The external type checker is sent each document translated with its own keywords."""

    @pytest.fixture
    def proxy(self):
        config = LanguageServerConfig(
            source_language="en",
            target_language=CONFIGURED,
            file_language=CONFIGURED,
            enhanced_intelligence_enabled=True,
        )
        return EnhancedIntelligenceProxy(config)

    async def test_each_document_is_translated_with_its_own_languages_keywords(self, proxy):
        for language in ("fr", "ar"):
            uri = f"file:///class/{language}.py"
            translated = await proxy.translate_document_for_server(uri, lesson(language), language)

            assert translated is not None
            assert translated.startswith("def average"), (
                f"the {language} document reached the type checker untranslated: "
                f"{translated.splitlines()[0]!r}"
            )

    async def test_one_text_in_two_languages_is_not_answered_from_one_cache_entry(self, proxy):
        """The translation cache is keyed by content, so it must also be per language.

        A French word that is an ordinary name in Spanish translates in one
        language and not the other; a single shared cache would answer the
        second request with the first language's translation.
        """
        text = lesson("fr")

        as_french = await proxy.translate_document_for_server("file:///a.py", text, "fr")
        as_spanish = await proxy.translate_document_for_server("file:///b.py", text, "es")

        assert as_french != as_spanish, (
            "the Spanish translation of a French document was served from the French cache entry"
        )

    async def test_the_server_forwards_each_documents_language(self, server):
        calls: list[tuple[str, str, str | None]] = []

        class RecordingProxy:
            def is_running(self):
                return True

            async def translate_document_for_server(self, uri, content, language=None):
                calls.append(("translate", uri, language))
                return content

            async def forward_diagnostic(self, uri, content, language=None):
                calls.append(("diagnostic", uri, language))
                return []

            async def forward_hover(self, params):
                return None

        server.intelligence_proxy = RecordingProxy()
        uri = "file:///class/fr.py"
        await tell(server, uri, "fr")
        await open_document(server, uri, lesson("fr"))
        await server.on_diagnostic(
            DocumentDiagnosticParams(text_document=TextDocumentIdentifier(uri=uri))
        )
        await tell(server, uri, "ar")

        assert calls == [
            ("translate", uri, "fr"),
            ("diagnostic", uri, "fr"),
            ("translate", uri, "ar"),
        ], calls

    async def test_an_edit_is_forwarded_in_the_documents_own_language(self, server, shown_messages):
        """Each edit reaches the type checker translated with the document's keywords.

        And an edit to a document no pack can serve is not sent at all, like its open.
        """
        forwarded: list[tuple[str, str | None]] = []

        class RecordingProxy:
            def is_running(self):
                return True

            async def translate_document_for_server(self, uri, content, language=None):
                forwarded.append((uri, language))
                return content

        server.intelligence_proxy = RecordingProxy()
        french, unknown = "file:///class/fr.py", "file:///class/xx.py"
        await tell(server, french, "fr")
        await open_document(server, french, lesson("fr"))
        await tell(server, unknown, "xx")
        await open_document(server, unknown, lesson("fr"))

        await change_document(server, french, lesson("fr") + "\n")
        await change_document(server, unknown, lesson("fr") + "\n")

        assert forwarded == [(french, "fr"), (french, "fr")], forwarded

    async def test_hover_does_not_ask_the_proxy_about_an_unservable_document(
        self, server, shown_messages
    ):
        """Renamed to a language with no pack, a document's proxy translation is stale."""
        asked: list[str] = []

        class RecordingProxy:
            def is_running(self):
                return True

            async def translate_document_for_server(self, uri, content, language=None):
                return content

            async def forward_hover(self, params):
                asked.append(params.text_document.uri)
                return None

        server.intelligence_proxy = RecordingProxy()
        uri = "file:///class/doc.py"
        await tell(server, uri, "fr")
        await open_document(server, uri, lesson("fr"))
        await hover_text(server, uri, line=0, character=1)
        await tell(server, uri, "xx")

        assert await hover_text(server, uri, line=0, character=1) is None
        assert asked == [uri], f"the proxy was asked about an unservable document: {asked}"

    async def test_an_unservable_document_is_not_forwarded(self, server, shown_messages):
        """Untranslated keywords are exactly what made the backend report garbage."""
        forwarded: list[str] = []

        class RecordingProxy:
            def is_running(self):
                return True

            async def translate_document_for_server(self, uri, content, language=None):
                forwarded.append(uri)
                return content

            async def forward_diagnostic(self, uri, content, language=None):
                forwarded.append(uri)
                return []

        server.intelligence_proxy = RecordingProxy()
        uri = "file:///class/xx.py"
        await tell(server, uri, "xx")
        await open_document(server, uri, lesson("fr"))
        await server.on_diagnostic(
            DocumentDiagnosticParams(text_document=TextDocumentIdentifier(uri=uri))
        )

        assert forwarded == []
