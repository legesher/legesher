/**
 * Integration tests for language resolution (CORE-1754).
 *
 * These cover the parts of the detection work that unit tests cannot reach: the
 * precedence between detection and configuration, and whether a settings change
 * actually reaches the running server. Both are contracts about the extension's
 * behaviour inside a real editor, not about the scoring function.
 */

import * as assert from 'assert';
import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';

/** The part of the extension's diagnostic API these tests read (see languageScopes.test.ts). */
interface LegesherApi {
    getServerLanguage(): string | undefined;
    getDocumentLanguage(uri: vscode.Uri): string | undefined;
}

const EXTENSION_ID = 'legesher.legesher-vscode';
const GERMAN_FIXTURE = 'sample_de.py';
const ENGLISH_FIXTURE = 'sample.py';

function findLanguageServer(): string | undefined {
    let dir = __dirname;
    for (let depth = 0; depth < 10; depth++) {
        const candidate = path.join(dir, '.venv', 'bin', 'legesher-lsp');
        if (fs.existsSync(candidate)) {
            return candidate;
        }
        const parent = path.dirname(dir);
        if (parent === dir) {
            break;
        }
        dir = parent;
    }
    return undefined;
}

async function openFixture(name: string): Promise<vscode.TextDocument> {
    const folder = vscode.workspace.workspaceFolders?.[0];
    assert.ok(folder, 'integration tests need the test/fixtures workspace folder');
    const uri = vscode.Uri.file(path.join(folder!.uri.fsPath, name));
    const document = await vscode.workspace.openTextDocument(uri);
    await vscode.window.showTextDocument(document);
    return document;
}

/** Concatenated hover text at the first occurrence of `token`. */
async function hoverTextAt(document: vscode.TextDocument, token: string): Promise<string> {
    const index = document.getText().indexOf(token);
    assert.notStrictEqual(index, -1, `fixture should contain ${token}`);
    const position = document.positionAt(index + 1);

    const hovers = await vscode.commands.executeCommand<vscode.Hover[]>(
        'vscode.executeHoverProvider',
        document.uri,
        position
    );

    return (hovers ?? [])
        .flatMap(hover => hover.contents)
        .map(content => (typeof content === 'string' ? content : content.value))
        .join('\n');
}

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * How long a test waits for a restart it asked for. Only a failing run pays it:
 * every wait returns as soon as its condition holds. At a load average near 200
 * a restart took about 25 s.
 */
const RESTART_WAIT_MS = 90_000;

function api(): LegesherApi {
    const extension = vscode.extensions.getExtension<LegesherApi>(EXTENSION_ID);
    assert.ok(extension?.exports, `${EXTENSION_ID} should export its diagnostic API`);
    return extension!.exports;
}

/**
 * Wait until the extension reports a running server at `identity`.
 *
 * Polled rather than slept (CORE-2323). A settings write restarts the server,
 * so a fixed 5 s wait sometimes hovered before the server was answering and
 * read an empty hover.
 */
async function serverRunningAt(identity: string): Promise<void> {
    await waitUntil(
        `the server to be running at ${identity}`,
        () => api().getServerLanguage() === identity
    );
}

/** What `cleanupSettled` gave up on, for the suite's `after` to report. */
const cleanupMisses: string[] = [];

/**
 * Wait for the restarts a test's cleanup asked for, so the next test's own
 * restarts do not queue behind them (CORE-2323). The server's identity
 * follows only the source and working languages, not the open document, and
 * cleanup only returns settings to their defaults, so the queue is done once
 * it runs at en->en.
 *
 * A miss is collected rather than asserted here, because failing an
 * `afterEach` skips every test after it. `after` fails the suite on it once
 * every test has run.
 */
async function cleanupSettled(): Promise<void> {
    const deadline = Date.now() + RESTART_WAIT_MS;
    while (Date.now() < deadline) {
        if (api().getServerLanguage() === 'en->en') {
            return;
        }
        await sleep(250);
    }
    const miss = `cleanup did not reach en->en within ${RESTART_WAIT_MS}ms; `
        + `server at ${api().getServerLanguage() ?? 'none'}`;
    console.warn(miss);
    cleanupMisses.push(miss);
}

/** Wait until `condition` holds, or fail naming it and the server's state. */
async function waitUntil(
    describe: string,
    condition: () => boolean,
    timeoutMs = RESTART_WAIT_MS
): Promise<void> {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
        if (condition()) {
            return;
        }
        await sleep(250);
    }
    assert.fail(
        `timed out after ${timeoutMs}ms waiting for ${describe}; `
        + `server at ${api().getServerLanguage() ?? 'none'}`
    );
}

/**
 * Hover at `token` until `accept` holds, and return the text.
 *
 * The hover is the end of the restart these tests wait for: the server answers
 * once it is up. A timeout reports the last text seen.
 */
async function hoverWhen(
    document: vscode.TextDocument,
    token: string,
    describe: string,
    accept: (text: string) => boolean,
    timeoutMs = RESTART_WAIT_MS
): Promise<string> {
    const deadline = Date.now() + timeoutMs;
    let text = '';
    while (Date.now() < deadline) {
        text = await hoverTextAt(document, token);
        if (accept(text)) {
            return text;
        }
        await sleep(250);
    }
    assert.fail(
        `timed out after ${timeoutMs}ms waiting for ${describe}; `
        + `last hover: ${text.slice(0, 200) || '(empty)'}; `
        + `server at ${api().getServerLanguage() ?? 'none'}`
    );
}

describe('Language resolution (CORE-1754)', function () {
    // Two full waits fit in one test, so a failure reports the poll's message
    // rather than a bare mocha timeout.
    this.timeout(240_000);

    before(async () => {
        const serverPath = findLanguageServer();
        assert.ok(
            serverPath,
            'legesher-lsp not found in any parent .venv — run `uv sync --all-packages` at the repo root'
        );
        await vscode.workspace.getConfiguration('legesher')
            .update('serverCommand', serverPath, vscode.ConfigurationTarget.Global);

        const extension = vscode.extensions.getExtension(EXTENSION_ID);
        assert.ok(extension, `${EXTENSION_ID} should be present`);
        await extension!.activate();
    });

    afterEach(async () => {
        const config = vscode.workspace.getConfiguration('legesher');
        await config.update('targetLanguage', undefined, vscode.ConfigurationTarget.Global);
        await config.update('workingLanguage', undefined, vscode.ConfigurationTarget.Global);
        await config.update('knownLanguages', undefined, vscode.ConfigurationTarget.Global);
        await config.update('languageDetection', undefined, vscode.ConfigurationTarget.Global);
        await cleanupSettled();
    });

    after(async () => {
        await vscode.workspace.getConfiguration('legesher')
            .update('serverCommand', undefined, vscode.ConfigurationTarget.Global);
        assert.deepStrictEqual(
            cleanupMisses, [], 'every cleanup should bring the server back to en->en'
        );
    });

    it('detects the file language over a conflicting user setting', async () => {
        // The case that motivated detection: the user's global preference says
        // one language, the file in front of them is written in another. The
        // file wins, and hover answers in the language it is actually written in.
        await vscode.workspace.getConfiguration('legesher')
            .update('targetLanguage', 'pt', vscode.ConfigurationTarget.Global);

        const document = await openFixture(GERMAN_FIXTURE);
        const text = await hoverWhen(
            document, 'drucken', 'a German hover despite a Portuguese setting',
            hover => hover.includes('drucken') && hover.includes('print')
        );

        assert.ok(
            text.includes('drucken') && text.includes('print'),
            `expected German hover despite a Portuguese setting, got: ${text.slice(0, 200)}`
        );
    });

    it('honours an explicit pick over detection when detection is off', async () => {
        // What selectLanguage does when a language is chosen explicitly: pin it
        // and turn detection off, so it survives a file that detects otherwise.
        const config = vscode.workspace.getConfiguration('legesher');
        await config.update('targetLanguage', 'es', vscode.ConfigurationTarget.Global);
        await config.update('languageDetection', 'off', vscode.ConfigurationTarget.Global);

        const document = await openFixture(GERMAN_FIXTURE);
        // Wait until the server runs at the pinned language and the document
        // is named Spanish before reading the hover. The hover is then empty or
        // Spanish, and the check below passes either way; what the waits rule
        // out is reading it while the document is still named German, which is
        // how German leaked through.
        await serverRunningAt('en->es');
        await waitUntil(
            'the document to be named es',
            () => api().getDocumentLanguage(document.uri) === 'es'
        );

        const text = await hoverTextAt(document, 'drucken');

        assert.ok(
            !text.includes('(`print`)'),
            `German hover should not resolve while pinned to Spanish, got: ${text.slice(0, 200)}`
        );
    });

    it('applies a settings change to the running server without a reload', async () => {
        // The CORE-1728 contract: editing the language in settings has to reach
        // the server, not just the status bar. English source gives detection
        // nothing to go on, so configuration decides.
        const config = vscode.workspace.getConfiguration('legesher');
        await config.update('targetLanguage', 'de', vscode.ConfigurationTarget.Global);

        const document = await openFixture(ENGLISH_FIXTURE);
        const before = await hoverWhen(
            document, 'print', 'the German equivalent while set to de',
            hover => hover.includes('drucken')
        );
        assert.ok(
            before.includes('drucken'),
            `expected the German equivalent while set to de, got: ${before.slice(0, 200)}`
        );

        await config.update('targetLanguage', 'es', vscode.ConfigurationTarget.Global);
        const after = await hoverWhen(
            document, 'print', 'the Spanish equivalent after the change',
            hover => hover.includes('imprimir')
        );
        assert.ok(
            after.includes('imprimir'),
            `expected the Spanish equivalent after the change, got: ${after.slice(0, 200)}`
        );
    });
});
