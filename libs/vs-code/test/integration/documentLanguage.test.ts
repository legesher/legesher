/**
 * Integration tests for per-document languages (CORE-1976).
 *
 * The case the ticket was filed from: one session, a server started in
 * Amharic, and files open beside each other in several languages. The server
 * used to highlight its own language and English and return nothing for every
 * other file, and focusing one restarted the server. These drive the real
 * editor: the fixtures are detected the way a user's files are, and the
 * semantic tokens are the ones VS Code itself asks the server for.
 */

import * as assert from 'assert';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import * as vscode from 'vscode';

/** The extension's diagnostic API, restated as a consumer sees it (see languageScopes.test.ts). */
interface LegesherApi {
    getServerLanguage(): string | undefined;
    getLastTransition(): { from: string; to: string; trigger: string; source: string; outcome: string } | undefined;
    getDocumentLanguage(uri: vscode.Uri): string | undefined;
}

const EXTENSION_ID = 'legesher.legesher-vscode';

/** One file per language, each written with its pack's own spellings. */
const FIXTURES: Record<string, string> = {
    fr: 'sample_fr.py',
    ar: 'sample_ar.py',
    de: 'sample_de.py',
    am: 'sample_am.py',
};

/** The language the server is started in, as in the ticket's log. */
const CONFIGURED = 'am';

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

function api(): LegesherApi {
    const extension = vscode.extensions.getExtension<LegesherApi>(EXTENSION_ID);
    assert.ok(extension?.exports, `${EXTENSION_ID} should export its diagnostic API`);
    return extension!.exports;
}

function fixtureUri(name: string): vscode.Uri {
    const folder = vscode.workspace.workspaceFolders?.[0];
    assert.ok(folder, 'integration tests need the test/fixtures workspace folder');
    return vscode.Uri.file(path.join(folder!.uri.fsPath, name));
}

async function openFixture(name: string): Promise<vscode.TextDocument> {
    const document = await vscode.workspace.openTextDocument(fixtureUri(name));
    await vscode.window.showTextDocument(document);
    return document;
}

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

async function waitUntil(describe: string, condition: () => boolean, timeoutMs = 30_000): Promise<void> {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
        if (condition()) {
            return;
        }
        await sleep(250);
    }
    assert.fail(`timed out after ${timeoutMs}ms waiting for ${describe}`);
}

/** The first code line's first word: each fixture opens with its `def` keyword. */
function firstKeyword(document: vscode.TextDocument): { line: number; word: string } {
    for (let line = 0; line < document.lineCount; line++) {
        const text = document.lineAt(line).text;
        if (text.trim() !== '' && !text.startsWith('#')) {
            return { line, word: text.split(' ')[0] };
        }
    }
    assert.fail(`${document.uri.fsPath} has no code`);
}

/** The document's semantic tokens, decoded to (line, start, text, type). */
async function highlighted(document: vscode.TextDocument) {
    const legend = await vscode.commands.executeCommand<vscode.SemanticTokensLegend>(
        'vscode.provideDocumentSemanticTokensLegend',
        document.uri
    );
    const tokens = await vscode.commands.executeCommand<vscode.SemanticTokens>(
        'vscode.provideDocumentSemanticTokens',
        document.uri
    );
    const decoded: Array<{ line: number; start: number; text: string; type: string }> = [];
    if (!legend || !tokens) {
        return decoded;
    }
    let line = 0;
    let start = 0;
    for (let i = 0; i < tokens.data.length; i += 5) {
        const [deltaLine, deltaStart, length, type] = tokens.data.slice(i, i + 4);
        line += deltaLine;
        start = deltaLine === 0 ? start + deltaStart : deltaStart;
        decoded.push({
            line,
            start,
            text: document.getText(new vscode.Range(line, start, line, start + length)),
            type: legend.tokenTypes[type],
        });
    }
    return decoded;
}

describe('Per-document languages (CORE-1976)', function () {
    this.timeout(120_000);

    before(async () => {
        const serverPath = findLanguageServer();
        assert.ok(
            serverPath,
            'legesher-lsp not found in any parent .venv: run `uv sync --all-packages` at the repo root'
        );
        const config = vscode.workspace.getConfiguration('legesher');
        await config.update('serverCommand', serverPath, vscode.ConfigurationTarget.Global);

        const extension = vscode.extensions.getExtension(EXTENSION_ID);
        assert.ok(extension, `${EXTENSION_ID} should be present`);
        await extension!.activate();
    });

    after(async () => {
        await vscode.workspace.getConfiguration('legesher')
            .update('serverCommand', undefined, vscode.ConfigurationTarget.Global);
    });

    describe('a document is named as it opens', () => {
        // Kept first and free of settings changes on purpose. A settings change
        // re-reports every open document once the resulting sync finishes, and
        // focusing a document names it too, so either would mask an open that
        // named nothing. Restarting through the command changes no setting.
        before(async () => {
            await vscode.commands.executeCommand('legesher.restartServer');
            await waitUntil(
                'a running server',
                () => api().getServerLanguage() !== undefined,
                45_000
            );
        });

        it('names a document before any editor shows it', async () => {
            // An untitled document is always a fresh open, never one already
            // open from an earlier test.
            const content = fs.readFileSync(fixtureUri(FIXTURES.ar).fsPath, 'utf8');
            const document = await vscode.workspace.openTextDocument({ language: 'python', content });
            try {
                await waitUntil(
                    'the server to be told an unfocused Arabic document is ar',
                    () => api().getDocumentLanguage(document.uri) === 'ar',
                    15_000
                );

                const tokens = await highlighted(document);
                const { line, word } = firstKeyword(document);
                assert.ok(
                    tokens.some(token => token.line === line && token.text === word
                        && token.type === 'keyword'),
                    'the unfocused Arabic document is not highlighted: ' +
                    JSON.stringify(tokens.slice(0, 3))
                );
            } finally {
                await vscode.window.showTextDocument(document);
                await vscode.commands.executeCommand('workbench.action.revertAndCloseActiveEditor');
            }
        });

        it('shows a visible document\'s diagnostics again after a restart', async () => {
            // While it starts, the client pulls diagnostics for every visible
            // document. The server must have the document open by then: a pull
            // for a document it has not seen is answered empty, and the client
            // does not ask again until the text changes.
            //
            // A file of its own, outside the workspace, rather than a second
            // untitled document: an untitled URI is reused once the first one
            // closes, and the client can still be tracking a pull for it.
            const french = fs.readFileSync(fixtureUri(FIXTURES.fr).fsPath, 'utf8');
            const broken = french.replace('greet(name):', 'greet(name)');
            assert.notStrictEqual(broken, french, 'the French fixture should have a colon to remove');
            const file = path.join(os.tmpdir(), `legesher-core-1976-${process.pid}.py`);
            fs.writeFileSync(file, broken, 'utf8');
            const document = await vscode.workspace.openTextDocument(vscode.Uri.file(file));
            await vscode.window.showTextDocument(document);
            try {
                await waitUntil(
                    'the French syntax error to be reported',
                    () => vscode.languages.getDiagnostics(document.uri).length > 0,
                    15_000
                );

                await vscode.commands.executeCommand('legesher.restartServer');

                await waitUntil(
                    'the French syntax error to be reported again after a restart',
                    () => vscode.languages.getDiagnostics(document.uri).length > 0,
                    15_000
                );
            } finally {
                await vscode.window.showTextDocument(document);
                await vscode.commands.executeCommand('workbench.action.closeActiveEditor');
                fs.rmSync(file, { force: true });
            }
        });
    });

    describe('files in several languages in one session', () => {
        beforeEach(async () => {
            const config = vscode.workspace.getConfiguration('legesher');
            await config.update('workingLanguage', CONFIGURED, vscode.ConfigurationTarget.Global);
            await waitUntil(
                `the server to be running at en->${CONFIGURED}`,
                () => api().getServerLanguage() === `en->${CONFIGURED}`,
                45_000
            );
        });

        afterEach(async () => {
            await vscode.commands.executeCommand('workbench.action.closeAllEditors');
            const config = vscode.workspace.getConfiguration('legesher');
            await config.update('workingLanguage', undefined, vscode.ConfigurationTarget.Global);
            await config.update('languageDetection', undefined, vscode.ConfigurationTarget.Global);
        });

        it('highlights four files in four languages without a restart or a settings change', async () => {
            const before = api().getLastTransition();

            for (const [language, name] of Object.entries(FIXTURES)) {
                const document = await openFixture(name);
                await waitUntil(
                    `the server to be told ${name} is ${language}`,
                    () => api().getDocumentLanguage(document.uri) === language
                );

                const tokens = await highlighted(document);
                const { line, word } = firstKeyword(document);

                assert.ok(
                    tokens.length > 0,
                    `${name} returned no semantic tokens on a server started in ${CONFIGURED}`
                );
                assert.ok(
                    tokens.some(token => token.line === line && token.start === 0
                        && token.text === word && token.type === 'keyword'),
                    `${name}: '${word}' on line ${line + 1} is not highlighted as a keyword; ` +
                    `got ${JSON.stringify(tokens.slice(0, 3))}`
                );
            }

            assert.strictEqual(
                api().getServerLanguage(),
                `en->${CONFIGURED}`,
                'switching between the files changed the language the server runs'
            );
            assert.deepStrictEqual(
                api().getLastTransition(),
                before,
                'switching between the files restarted the server'
            );
        });

        it('answers hover for a file in a language the server was not started in', async () => {
            const document = await openFixture(FIXTURES.ar);
            await waitUntil(
                'the server to be told the Arabic file is ar',
                () => api().getDocumentLanguage(document.uri) === 'ar'
            );
            const { line, word } = firstKeyword(document);

            const hovers = await vscode.commands.executeCommand<vscode.Hover[]>(
                'vscode.executeHoverProvider',
                document.uri,
                new vscode.Position(line, 1)
            );
            const text = (hovers ?? [])
                .flatMap(hover => hover.contents)
                .map(content => (typeof content === 'string' ? content : content.value))
                .join('\n');

            assert.ok(
                text.includes(word) && text.includes('`def`'),
                `hover on the Arabic keyword did not explain it: ${text.slice(0, 200)}`
            );
        });

        it('renames every open file when detection is turned off, without a restart', async () => {
            // A settings change can move files other than the focused one.
            const french = await openFixture(FIXTURES.fr);
            const arabic = await openFixture(FIXTURES.ar);
            await waitUntil(
                'both files to be named in their own languages',
                () => api().getDocumentLanguage(french.uri) === 'fr'
                    && api().getDocumentLanguage(arabic.uri) === 'ar'
            );
            const before = api().getLastTransition();

            await vscode.workspace.getConfiguration('legesher')
                .update('languageDetection', 'off', vscode.ConfigurationTarget.Global);

            await waitUntil(
                `both files to be named ${CONFIGURED} once detection is off`,
                () => api().getDocumentLanguage(french.uri) === CONFIGURED
                    && api().getDocumentLanguage(arabic.uri) === CONFIGURED
            );
            assert.strictEqual(api().getServerLanguage(), `en->${CONFIGURED}`);
            assert.deepStrictEqual(
                api().getLastTransition(),
                before,
                'turning detection off restarted the server; only the file languages changed'
            );
        });
    });
});
