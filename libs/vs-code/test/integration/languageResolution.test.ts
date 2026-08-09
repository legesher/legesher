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

const settle = () => new Promise(resolve => setTimeout(resolve, 5_000));

describe('Language resolution (CORE-1754)', function () {
    this.timeout(90_000);

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
        await config.update('languageDetection', undefined, vscode.ConfigurationTarget.Global);
    });

    after(async () => {
        await vscode.workspace.getConfiguration('legesher')
            .update('serverCommand', undefined, vscode.ConfigurationTarget.Global);
    });

    it('detects the file language over a conflicting user setting', async () => {
        // The case that motivated detection: the user's global preference says
        // one language, the file in front of them is written in another. The
        // file wins, and hover answers in the language it is actually written in.
        await vscode.workspace.getConfiguration('legesher')
            .update('targetLanguage', 'pt', vscode.ConfigurationTarget.Global);

        const document = await openFixture(GERMAN_FIXTURE);
        await settle();

        const text = await hoverTextAt(document, 'drucken');

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
        await settle();

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
        await settle();

        const before = await hoverTextAt(document, 'print');
        assert.ok(
            before.includes('drucken'),
            `expected the German equivalent while set to de, got: ${before.slice(0, 200)}`
        );

        await config.update('targetLanguage', 'es', vscode.ConfigurationTarget.Global);
        await settle();

        const after = await hoverTextAt(document, 'print');
        assert.ok(
            after.includes('imprimir'),
            `expected the Spanish equivalent after the change, got: ${after.slice(0, 200)}`
        );
    });
});
