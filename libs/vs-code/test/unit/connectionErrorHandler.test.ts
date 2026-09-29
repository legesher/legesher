/**
 * Unit tests for the language client's answers when its connection errors or
 * closes (CORE-2316).
 *
 * Checked against vscode-languageclient's own enums, never against numbers.
 * The handler's old `{ action: 2 }`, commented as "do not restart", is
 * `CloseAction.Restart`, and a test that restated the numbers would have
 * restated that mistake with it. That the running client acts on these answers
 * is pinned by the integration suite (serverRestart.test.ts).
 */

import * as assert from 'assert';
import { withoutEditor } from './support/languageClient';

// Both need vscode-languageclient, which needs an editor to load (see
// support/languageClient.ts).
const { library, handlerModule } = withoutEditor(() => ({
    library: require('vscode-languageclient/node') as typeof import('vscode-languageclient/node'),
    handlerModule: require('../../src/connectionErrorHandler') as typeof import('../../src/connectionErrorHandler'),
}));
const { CloseAction, ErrorAction } = library;
const { connectionErrorHandler } = handlerModule;

/** A handler whose reports are counted instead of logged. */
function counted() {
    const reported = { errors: 0, closes: 0 };
    const handler = connectionErrorHandler({
        error: () => {
            reported.errors++;
        },
        closed: () => {
            reported.closes++;
        },
    });
    return { reported, handler };
}

describe('connectionErrorHandler (CORE-2316)', () => {
    it('leaves a closed connection closed', async () => {
        const { reported, handler } = counted();

        const result = await handler.closed();

        assert.strictEqual(
            result.action,
            CloseAction.DoNotRestart,
            `closed() answered CloseAction.${CloseAction[result.action]}: ` +
            'the client would start the server again by itself'
        );
        assert.strictEqual(reported.closes, 1, 'the close should still be reported');
    });

    it('keeps the connection after an error', async () => {
        const { reported, handler } = counted();

        const result = await handler.error(new Error('write EPIPE'), undefined, 1);

        assert.strictEqual(
            result.action,
            ErrorAction.Continue,
            `error() answered ErrorAction.${ErrorAction[result.action]}: ` +
            'the client would shut the server down on one bad message'
        );
        assert.strictEqual(reported.errors, 1, 'the error should still be reported');
    });
});
