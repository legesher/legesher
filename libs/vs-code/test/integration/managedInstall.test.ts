/**
 * End to end: the extension installs its own language server, in a real VS
 * Code, and hover and keyword highlighting then work through it.
 *
 * This downloads uv, Python and the server's packages from the internet, so it
 * runs only when asked:
 *
 *     LEGESHER_E2E_INSTALL=1 npx vscode-test --grep "installs its own language server"
 *
 * Run it alone (the --grep), on a machine with no `legesher-lsp` on PATH: the
 * other integration tests point `legesher.serverCommand` at the repository's
 * own server, and this one needs the default. Set
 * LEGESHER_TEST_USER_DATA_DIR to a short folder name with a space and a
 * non-Latin script in it to put the install there (see .vscode-test.mjs).
 */

import * as assert from 'assert';
import { spawnSync } from 'child_process';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import * as vscode from 'vscode';

interface LegesherApi {
    getServerLanguage(): string | undefined;
}

const EXTENSION_ID = 'legesher.legesher-vscode';
const GERMAN_FIXTURE = 'sample_de.py';
const INSTALL_TIMEOUT_MS = 10 * 60_000;

async function openFixture(name: string): Promise<vscode.TextDocument> {
    const folder = vscode.workspace.workspaceFolders?.[0];
    assert.ok(folder, 'the test instance should open test/fixtures as its workspace');
    const document = await vscode.workspace.openTextDocument(path.join(folder.uri.fsPath, name));
    await vscode.window.showTextDocument(document);
    return document;
}

async function poll<T>(probe: () => Promise<T | undefined>, deadlineMs: number): Promise<T | undefined> {
    const deadline = Date.now() + deadlineMs;
    do {
        const value = await probe();
        if (value !== undefined) {
            return value;
        }
        await new Promise(resolve => setTimeout(resolve, 250));
    } while (Date.now() < deadline);
    return undefined;
}

(process.env.LEGESHER_E2E_INSTALL === '1' ? describe : describe.skip)(
    "The extension installs its own language server (set LEGESHER_E2E_INSTALL=1)",
    function () {
        this.timeout(INSTALL_TIMEOUT_MS);
        let api: LegesherApi;

        before(async () => {
            const onPath = spawnSync('legesher-lsp', ['--version'], { encoding: 'utf8' });
            assert.ok(onPath.error, 'legesher-lsp is on PATH, so the extension would use it instead of installing');

            const legesher = vscode.workspace.getConfiguration('legesher');
            await legesher.update('serverCommand', undefined, vscode.ConfigurationTarget.Global);
            await legesher.update('targetLanguage', 'de', vscode.ConfigurationTarget.Global);

            const extension = vscode.extensions.getExtension<LegesherApi>(EXTENSION_ID);
            assert.ok(extension, `${EXTENSION_ID} should be present in the test instance`);
            api = await extension.activate();
            await openFixture(GERMAN_FIXTURE);
        });

        after(async () => {
            await vscode.workspace.getConfiguration('legesher')
                .update('targetLanguage', undefined, vscode.ConfigurationTarget.Global);
        });

        it('installs its own language server, then hover and highlighting work', async () => {
            assert.strictEqual(api.getServerLanguage(), undefined, 'a server is already running before the install');

            const started = Date.now();
            await vscode.commands.executeCommand('legesher.installLanguageServer');
            console.log(`    install and restart took ${((Date.now() - started) / 1000).toFixed(1)} s`);

            const language = await poll(async () => api.getServerLanguage(), 30_000);
            assert.ok(language, 'no server is running after the install');

            const document = await openFixture(GERMAN_FIXTURE);
            const text = document.getText();
            const position = document.positionAt(text.indexOf('drucken') + 1);
            const hoverText = await poll(async () => {
                const hovers = await vscode.commands.executeCommand<vscode.Hover[]>(
                    'vscode.executeHoverProvider', document.uri, position
                );
                const joined = (hovers ?? [])
                    .flatMap(hover => hover.contents)
                    .map(content => (typeof content === 'string' ? content : content.value))
                    .join('\n');
                return joined.includes('print') ? joined : undefined;
            }, 45_000);
            assert.ok(hoverText, 'hover on "drucken" never mapped back to "print"');

            const tokens = await poll(async () => {
                const result = await vscode.commands.executeCommand<vscode.SemanticTokens>(
                    'vscode.provideDocumentSemanticTokens', document.uri
                );
                return result && result.data.length > 0 ? result : undefined;
            }, 45_000);
            assert.ok(tokens, 'the installed server returned no semantic tokens, so no keyword highlighting');
            console.log(`    hover answered, ${tokens.data.length / 5} semantic tokens`);
        });
    }
);

/** The installs in the extension's storage, by folder, with the version each marker records. */
function installsOnDisk(): Map<string, string> {
    const userData = process.env.LEGESHER_TEST_USER_DATA_DIR || path.join(os.tmpdir(), 'legesher-vscode-test');
    const envs = path.join(userData, 'User', 'globalStorage', EXTENSION_ID, 'language-server', 'envs');
    const found = new Map<string, string>();
    for (const name of fs.existsSync(envs) ? fs.readdirSync(envs) : []) {
        try {
            const marker = JSON.parse(fs.readFileSync(path.join(envs, name, 'legesher-install.json'), 'utf8'));
            found.set(name, marker.serverVersion);
        } catch {
            found.set(name, '(unfinished)');
        }
    }
    return found;
}

/**
 * The update an extension release brings. Run it after the install test above
 * has installed an OLDER server into the same storage, from a build whose
 * server/requirements.lock pinned an older version:
 *
 *     LEGESHER_E2E_UPDATE=1 npx vscode-test --grep "updates its own language server"
 */
(process.env.LEGESHER_E2E_UPDATE === '1' ? describe : describe.skip)(
    'The extension updates its own language server (set LEGESHER_E2E_UPDATE=1)',
    function () {
        this.timeout(INSTALL_TIMEOUT_MS);

        it('starts on the old install, updates in the background, then removes the old one', async () => {
            const extension = vscode.extensions.getExtension<LegesherApi>(EXTENSION_ID);
            assert.ok(extension);
            const lock = fs.readFileSync(path.join(extension.extensionPath, 'server', 'requirements.lock'), 'utf8');
            const wanted = /^legesher-language-server==(\S+)/m.exec(lock)?.[1];
            assert.ok(wanted);

            const before = installsOnDisk();
            console.log(`    before: ${JSON.stringify([...before])}, this build wants ${wanted}`);
            assert.ok([...before.values()].some(version => version !== wanted), 'no older install to update from');
            assert.ok(![...before.values()].includes(wanted), 'the wanted version is already installed');

            await vscode.workspace.getConfiguration('legesher')
                .update('serverCommand', undefined, vscode.ConfigurationTarget.Global);
            const api = await extension.activate();
            await openFixture(GERMAN_FIXTURE);

            const updated = await poll(async () => {
                const now = installsOnDisk();
                return now.size === 1 && [...now.values()][0] === wanted && api.getServerLanguage() ? now : undefined;
            }, INSTALL_TIMEOUT_MS - 60_000);
            assert.ok(updated, `never settled on ${wanted} alone: ${JSON.stringify([...installsOnDisk()])}`);
            console.log(`    after: ${JSON.stringify([...updated])}`);

            const document = await openFixture(GERMAN_FIXTURE);
            const position = document.positionAt(document.getText().indexOf('drucken') + 1);
            const hovered = await poll(async () => {
                const hovers = await vscode.commands.executeCommand<vscode.Hover[]>(
                    'vscode.executeHoverProvider', document.uri, position
                );
                return hovers && hovers.length > 0 ? hovers : undefined;
            }, 45_000);
            assert.ok(hovered, 'no hover after the update');
        });
    }
);
