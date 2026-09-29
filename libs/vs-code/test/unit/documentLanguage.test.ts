/**
 * Unit tests for naming each document's language to the server (CORE-1976).
 *
 * The server used to take one language at initialize, so every editor switch
 * to a file detected in another language restarted it, and any file the
 * restart had not caught up with came back empty. The client now sends each
 * document's language in a `legesher/documentLanguage` notification and starts
 * the server with the configured languages only.
 *
 * Two contracts are pinned here, both without an editor host: what the client
 * sends and when a send is redundant, and which languages make up the identity
 * whose change restarts the server. That the extension actually keys the
 * server on that identity is pinned by the integration suite.
 */

import * as assert from 'assert';
import {
    DOCUMENT_LANGUAGE_NOTIFICATION,
    DocumentLanguageSync,
    type DocumentLanguageParams,
} from '../../src/documentLanguage';
import {
    buildResolvedLanguages,
    serverIdentityOf,
    sessionLanguagesOf,
} from '../../src/languageProfile';
import { LanguageServerState, type TransitionHooks } from '../../src/serverState';

/** A sync whose sends are recorded instead of written to a connection. */
function recorded(fail: (params: DocumentLanguageParams) => boolean = () => false) {
    const sent: DocumentLanguageParams[] = [];
    const sync = new DocumentLanguageSync(async params => {
        if (fail(params)) {
            throw new Error('Client is not running');
        }
        sent.push(params);
    });
    return { sent, sync };
}

const FR = 'file:///class/calculateur_de_notes.py';
const AR = 'file:///class/%D8%AD%D8%A7%D8%B3%D8%A8%D8%A9.py';

describe('Naming document languages to the server (CORE-1976)', () => {
    it('uses the wire name the server registers', () => {
        // Asserted as a literal: the name is the contract with the server, and
        // a test that compared the constant with itself would pass with it
        // misspelled.
        assert.strictEqual(DOCUMENT_LANGUAGE_NOTIFICATION, 'legesher/documentLanguage');
    });

    it('sends a document the first time it is reported', async () => {
        const { sent, sync } = recorded();

        const didSend = await sync.report(FR, 'fr');

        assert.strictEqual(didSend, true);
        assert.deepStrictEqual(sent, [{ uri: FR, language: 'fr' }]);
    });

    it('does not resend a language the server already has', async () => {
        // Every editor switch re-resolves the focused document. Resending an
        // unchanged answer would make the server ask the editor to redraw on
        // every switch for nothing.
        const { sent, sync } = recorded();

        await sync.report(FR, 'fr');
        const didSend = await sync.report(FR, 'fr');

        assert.strictEqual(didSend, false);
        assert.strictEqual(sent.length, 1);
    });

    it('sends again when the resolved language changes', async () => {
        const { sent, sync } = recorded();

        await sync.report(FR, 'fr');
        await sync.report(FR, 'es');

        assert.deepStrictEqual(sent.map(params => params.language), ['fr', 'es']);
    });

    it('keeps documents apart', async () => {
        const { sent, sync } = recorded();

        await sync.report(FR, 'fr');
        await sync.report(AR, 'ar');
        await sync.report(FR, 'fr');

        assert.deepStrictEqual(sent, [
            { uri: FR, language: 'fr' },
            { uri: AR, language: 'ar' },
        ]);
        assert.strictEqual(sync.sentFor(FR), 'fr');
        assert.strictEqual(sync.sentFor(AR), 'ar');
    });

    it('sends a forced report even when nothing changed', async () => {
        // A document being opened: the server forgot it when it closed, so
        // whatever this record says, it has to be told again.
        const { sent, sync } = recorded();

        await sync.report(FR, 'fr');
        const didSend = await sync.report(FR, 'fr', { force: true });

        assert.strictEqual(didSend, true);
        assert.strictEqual(sent.length, 2);
    });

    it('names a document afresh after it is forgotten', async () => {
        const { sent, sync } = recorded();

        await sync.report(FR, 'fr');
        sync.forget(FR);
        await sync.report(FR, 'fr');

        assert.strictEqual(sync.sentFor(FR), 'fr');
        assert.strictEqual(sent.length, 2, 'a closed document was treated as still known');
    });

    it('does not record a send that failed, so the next report retries', async () => {
        // A stopped client rejects the send. Recording it anyway would make
        // the next, working report look redundant and never go out.
        let broken = true;
        const { sent, sync } = recorded(() => broken);

        await assert.rejects(sync.report(FR, 'fr'), /not running/);
        assert.strictEqual(sync.sentFor(FR), undefined);

        broken = false;
        const didSend = await sync.report(FR, 'fr');

        assert.strictEqual(didSend, true);
        assert.deepStrictEqual(sent, [{ uri: FR, language: 'fr' }]);
    });

    it('keeps what the server last received when a later send fails', async () => {
        let broken = false;
        const { sync } = recorded(() => broken);

        await sync.report(FR, 'fr');
        broken = true;
        await assert.rejects(sync.report(FR, 'ar'));

        assert.strictEqual(sync.sentFor(FR), 'fr', 'the server still has fr; the record says otherwise');
    });

    it('carries only the uri and the language, as plain JSON', async () => {
        const { sent, sync } = recorded();

        await sync.report(FR, 'fr');

        assert.deepStrictEqual(JSON.parse(JSON.stringify(sent[0])), { uri: FR, language: 'fr' });
    });
});

describe('The server is started with the configured languages only (CORE-1976)', () => {
    function counting(): { hooks: TransitionHooks; starts: () => number } {
        let starts = 0;
        return {
            hooks: {
                start: async () => { starts++; return 'started'; },
                onRecord: () => {},
                onFailure: () => {},
                now: () => 0,
            },
            starts: () => starts,
        };
    }

    it('keys the server on the canonical and working languages', () => {
        assert.strictEqual(
            serverIdentityOf(sessionLanguagesOf({ sourceLanguage: 'en', workingLanguage: 'pt' })),
            'en->pt'
        );
    });

    it('sends the working language as the fallback for documents it has not named', () => {
        // The server serves any document the client has not named in
        // `fileLanguage`. That is the configured language, never a detected
        // one: a detection result belongs to one document, not the session.
        assert.deepStrictEqual(
            sessionLanguagesOf({ sourceLanguage: 'en', workingLanguage: 'pt' }),
            buildResolvedLanguages('en', 'pt', 'pt')
        );
    });

    // That switching between files detected in different languages no longer
    // restarts the server is pinned in the editor, by the integration test
    // "highlights four files in four languages without a restart or a settings
    // change": whether the extension keys the server on these languages or on
    // a detected one is a property of extension.ts, which no unit test here
    // can load.

    it('still restarts for a working-language change', async () => {
        // The working language is read at initialize, so a pick or a settings
        // edit that changes it must still produce a new session.
        const state = new LanguageServerState();
        const { hooks, starts } = counting();

        await state.transition(
            serverIdentityOf(sessionLanguagesOf({ sourceLanguage: 'en', workingLanguage: 'pt' })),
            { trigger: 'activation', source: 'user' },
            hooks
        );
        await state.transition(
            serverIdentityOf(sessionLanguagesOf({ sourceLanguage: 'en', workingLanguage: 'fr' })),
            { trigger: 'picker', source: 'user' },
            hooks
        );

        assert.strictEqual(starts(), 2);
    });
});
