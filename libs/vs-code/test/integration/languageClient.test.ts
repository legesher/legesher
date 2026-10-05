/**
 * Integration tests for the language client (CORE-1733).
 *
 * These run inside a real VS Code instance, which is the only place the failure
 * this guards against can occur: vscode-languageclient logs through
 * LogOutputChannel methods, so a plain OutputChannel makes client.start() throw
 * "this.outputChannel.error is not a function" and every LSP feature dies. No
 * unit test can catch that — it needs a real editor host and a real client.
 *
 * Requires the workspace language server, which `uv sync` installs into the
 * repository's .venv. The tests fail loudly rather than skipping if it is
 * missing: silently skipping is how a broken LSP shipped green in the first
 * place.
 */

import * as assert from 'assert';
import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';

const EXTENSION_ID = 'legesher.legesher-vscode';
const GERMAN_FIXTURE = 'sample_de.py';

/** Walk up from this file to find the monorepo's .venv/bin/legesher-lsp. */
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

/** Position of the first occurrence of `token`, or fail. */
function positionOf(document: vscode.TextDocument, token: string): vscode.Position {
    const index = document.getText().indexOf(token);
    assert.notStrictEqual(index, -1, `fixture should contain ${token}`);
    return document.positionAt(index + 1);
}

describe('Language client (CORE-1733)', function () {
    // A real server process has to spawn and complete an LSP handshake.
    this.timeout(60_000);

    before(async () => {
        const serverPath = findLanguageServer();
        assert.ok(
            serverPath,
            'legesher-lsp not found in any parent .venv — run `uv sync --all-packages` at the repo root'
        );

        await vscode.workspace.getConfiguration('legesher')
            .update('serverCommand', serverPath, vscode.ConfigurationTarget.Global);
        await vscode.workspace.getConfiguration('legesher')
            .update('targetLanguage', 'de', vscode.ConfigurationTarget.Global);

        const extension = vscode.extensions.getExtension(EXTENSION_ID);
        assert.ok(extension, `${EXTENSION_ID} should be present in the test instance`);
        await extension!.activate();
    });

    after(async () => {
        await vscode.workspace.getConfiguration('legesher')
            .update('serverCommand', undefined, vscode.ConfigurationTarget.Global);
        await vscode.workspace.getConfiguration('legesher')
            .update('targetLanguage', undefined, vscode.ConfigurationTarget.Global);
    });

    it('activates without throwing', async () => {
        const extension = vscode.extensions.getExtension(EXTENSION_ID);

        assert.strictEqual(extension!.isActive, true);
    });

    it('answers hover on a translated file', async () => {
        // The regression test for CORE-1733. With a plain OutputChannel the
        // client throws while logging during start(), so no hover provider is
        // ever registered and this returns nothing.
        const document = await openFixture(GERMAN_FIXTURE);
        const position = positionOf(document, 'drucken');

        // Poll until the client has started and synchronised the document,
        // rather than sleeping a fixed 5 s (CORE-2323). The regression this
        // guards produces no hover at all, so it still fails, at the deadline.
        const deadline = Date.now() + 45_000;
        let hovers: vscode.Hover[] | undefined;
        do {
            hovers = await vscode.commands.executeCommand<vscode.Hover[]>(
                'vscode.executeHoverProvider',
                document.uri,
                position
            );
            if (hovers && hovers.length > 0) {
                break;
            }
            await new Promise(resolve => setTimeout(resolve, 250));
        } while (Date.now() < deadline);

        assert.ok(hovers && hovers.length > 0, 'expected at least one hover result');

        const text = hovers
            .flatMap(hover => hover.contents)
            .map(content => (typeof content === 'string' ? content : content.value))
            .join('\n');

        assert.ok(
            text.includes('drucken'),
            `hover should describe the translated keyword, got: ${text.slice(0, 200)}`
        );
        assert.ok(
            text.includes('print'),
            `hover should map back to the canonical term, got: ${text.slice(0, 200)}`
        );
    });
});
