/**
 * Integration tests for scope-aware language resolution (CORE-1776).
 *
 * These are the cases that only exist inside a real editor, because they are
 * about VS Code's own configuration precedence and about a running server
 * process. A unit test with a mocked configuration cannot reach either: the
 * mock resolves precedence the way the test author believes it works, which is
 * exactly the belief that was wrong.
 *
 * The first test is the shape a project repository actually has — a
 * `legesher.targetLanguage` committed in `.vscode/settings.json` — and drives
 * the real quick-pick widget rather than calling the handler, because the bug
 * was that the picker's write went somewhere the picker's own resolution
 * ignored.
 */

import * as assert from 'assert';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import * as vscode from 'vscode';
import { getActiveLanguages } from '../../src/config';

/**
 * The extension's diagnostic API, restated rather than imported.
 *
 * Importing it from `src/extension` would pull vscode-languageclient into this
 * compilation, which the integration tsconfig cannot resolve. Restating it is
 * also the more honest test: this is the contract as a consumer sees it, and it
 * fails loudly here if the real shape drifts.
 */
interface LegesherApi {
    getServerLanguage(): string | undefined;
}

const EXTENSION_ID = 'legesher.legesher-vscode';
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

function workspaceFolder(): vscode.WorkspaceFolder {
    const folder = vscode.workspace.workspaceFolders?.[0];
    assert.ok(folder, 'integration tests need the test/fixtures workspace folder');
    return folder!;
}

/** Configuration scoped to the fixture folder, so folder/workspace values resolve. */
function legesherConfig(): vscode.WorkspaceConfiguration {
    return vscode.workspace.getConfiguration('legesher', workspaceFolder().uri);
}

async function openFixture(name: string): Promise<vscode.TextDocument> {
    const uri = vscode.Uri.file(path.join(workspaceFolder().uri.fsPath, name));
    const document = await vscode.workspace.openTextDocument(uri);
    await vscode.window.showTextDocument(document);
    return document;
}

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
/** Long enough for a server process to stop, respawn and complete a handshake. */
const settle = () => sleep(6_000);

function api(): LegesherApi {
    const extension = vscode.extensions.getExtension<LegesherApi>(EXTENSION_ID);
    assert.ok(extension?.exports, `${EXTENSION_ID} should export its diagnostic API`);
    return extension!.exports;
}

/**
 * Choose the language at `offset` in the picker's language list, through the
 * real quick-pick widget.
 *
 * Fires `legesher.selectLanguage` without awaiting — the command does not
 * resolve until the pick closes — then drives the widget with the same
 * workbench commands a keyboard user does, and returns the code that should
 * have been chosen.
 *
 * Offsets are counted from the start of the list rather than searched for by
 * language code: every keystroke sent blind at a widget is a chance to be sent
 * before it has rendered, so the tests below choose languages near the top and
 * assert on what landed. The items are `Auto` followed by getActiveLanguages()
 * in order, and the widget opens with `Auto` active.
 */
async function pickLanguageAt(offset: number): Promise<string> {
    const languages = getActiveLanguages();
    assert.ok(offset < languages.length, `offset ${offset} should exist in the language list`);

    const picked = vscode.commands.executeCommand('legesher.selectLanguage');
    await sleep(3_000); // let the widget render before sending keys

    for (let i = 0; i <= offset; i++) { // +1 to step past the leading "Auto" item
        await vscode.commands.executeCommand('workbench.action.quickOpenSelectNext');
    }
    await vscode.commands.executeCommand('workbench.action.acceptSelectedQuickOpenItem');
    await picked;

    return languages[offset].code;
}

/** A language near the top of the picker that is not `avoid`. */
function nearbyLanguageOffset(avoid: string): number {
    const offset = getActiveLanguages().findIndex(lang => lang.code !== avoid);
    assert.notStrictEqual(offset, -1, 'the picker should offer at least one other language');
    return offset;
}

describe('Language-resolution scopes (CORE-1776)', function () {
    this.timeout(120_000);

    let serverPath: string;

    before(async () => {
        const found = findLanguageServer();
        assert.ok(
            found,
            'legesher-lsp not found in any parent .venv — run `uv sync --all-packages` at the repo root'
        );
        serverPath = found!;
        await legesherConfig().update('serverCommand', serverPath, vscode.ConfigurationTarget.Global);

        const extension = vscode.extensions.getExtension(EXTENSION_ID);
        assert.ok(extension, `${EXTENSION_ID} should be present`);
        await extension!.activate();
    });

    afterEach(async () => {
        // Restore the working server first: every write below fires the
        // configuration listener, and letting those restarts run against a
        // deliberately broken binary makes cleanup cost seconds per key.
        if (legesherConfig().get<string>('serverCommand') !== serverPath) {
            await legesherConfig().update(
                'serverCommand', serverPath, vscode.ConfigurationTarget.Global
            );
        }

        // Clear both scopes: a value left at workspace scope outranks the next
        // test's global setup and would fail it for the wrong reason. Only what
        // is actually set is written, so cleanup does not trigger a restart per
        // key that was never touched.
        for (const key of ['targetLanguage', 'sourceLanguage', 'languageDetection']) {
            const inspected = legesherConfig().inspect(key);
            if (inspected?.workspaceValue !== undefined) {
                await legesherConfig().update(key, undefined, vscode.ConfigurationTarget.Workspace);
            }
            if (inspected?.globalValue !== undefined) {
                await legesherConfig().update(key, undefined, vscode.ConfigurationTarget.Global);
            }
        }
    });

    after(async () => {
        await legesherConfig().update('serverCommand', undefined, vscode.ConfigurationTarget.Global);
    });

    it('applies a pick when a workspace setting supplies the language', async () => {
        // The demo-repo configuration, and the reason this issue is urgent. The
        // picker wrote Global while resolution honoured the workspace value, so
        // the language never changed and the notification said it had.
        const config = legesherConfig();
        await config.update('targetLanguage', 'de', vscode.ConfigurationTarget.Workspace);
        await config.update('languageDetection', 'off', vscode.ConfigurationTarget.Workspace);

        const document = await openFixture(ENGLISH_FIXTURE);
        await settle();

        const before = await hoverTextAt(document, 'print');
        assert.ok(
            before.includes('drucken'),
            `expected German before the pick, got: ${before.slice(0, 200)}`
        );

        const chosen = await pickLanguageAt(nearbyLanguageOffset('de'));

        // The write has to land where it can win, not merely be written.
        const inspected = legesherConfig().inspect<string>('targetLanguage');
        assert.strictEqual(
            inspected?.workspaceValue,
            chosen,
            'the pick should be written at the scope that supplies the value'
        );
        assert.strictEqual(
            legesherConfig().get<string>('targetLanguage'),
            chosen,
            'the effective setting should be the picked language'
        );

        await settle();

        // And it has to reach the server, not just the settings file.
        assert.strictEqual(
            api().getServerLanguage(),
            `en->${chosen}`,
            'the running server should have been restarted at the picked language'
        );

        const after = await hoverTextAt(document, 'print');
        assert.ok(
            !after.includes('drucken'),
            `hover should no longer answer in German after the pick, got: ${after.slice(0, 200)}`
        );
    });

    it('writes a pick to user settings when no narrower scope is set', async () => {
        // The ordinary case must not regress into writing project files: with
        // nothing committed at workspace scope, a pick is the user's own choice.
        await legesherConfig().update('targetLanguage', 'de', vscode.ConfigurationTarget.Global);
        await legesherConfig().update('languageDetection', 'off', vscode.ConfigurationTarget.Global);

        await openFixture(ENGLISH_FIXTURE);
        await settle();

        const chosen = await pickLanguageAt(nearbyLanguageOffset('de'));

        const inspected = legesherConfig().inspect<string>('targetLanguage');
        assert.strictEqual(inspected?.globalValue, chosen, 'should write user settings');
        assert.strictEqual(
            inspected?.workspaceValue,
            undefined,
            'should not create a workspace setting that was never there'
        );
    });

    it('records the server identity with the workspace-scoped source language', async () => {
        // createLanguageClient used to re-read the configuration without the
        // document URI, so a folder- or workspace-scoped sourceLanguage never
        // reached the server while the recorded identity claimed it had.
        const config = legesherConfig();
        await config.update('sourceLanguage', 'es', vscode.ConfigurationTarget.Workspace);
        await config.update('targetLanguage', 'de', vscode.ConfigurationTarget.Workspace);
        await config.update('languageDetection', 'off', vscode.ConfigurationTarget.Workspace);

        await openFixture(ENGLISH_FIXTURE);
        await settle();

        assert.strictEqual(
            api().getServerLanguage(),
            'es->de',
            'the identity must be the pair the server was actually started with'
        );
    });

    it('clears the recorded identity when the server fails to start', async () => {
        // A failed restart used to leave the old pair in place, so switching
        // back to it matched the cache and no-opped forever: no server running,
        // status bar claiming one was.
        const config = legesherConfig();
        await config.update('languageDetection', 'off', vscode.ConfigurationTarget.Global);
        await config.update('targetLanguage', 'de', vscode.ConfigurationTarget.Global);

        await openFixture(ENGLISH_FIXTURE);
        await settle();
        assert.strictEqual(api().getServerLanguage(), 'en->de', 'precondition: server running');

        // A binary that answers --version but dies on the LSP handshake, which
        // is what a broken install or a version mismatch looks like in practice.
        await config.update('serverCommand', brokenServerPath(), vscode.ConfigurationTarget.Global);
        await config.update('targetLanguage', 'fr', vscode.ConfigurationTarget.Global);
        await settle();

        assert.strictEqual(
            api().getServerLanguage(),
            undefined,
            'a failed start must not leave an identity claiming a running server'
        );

        // And the previous language must be reachable again rather than being
        // swallowed as a no-op against a stale cache entry.
        await config.update('serverCommand', serverPath, vscode.ConfigurationTarget.Global);
        await config.update('targetLanguage', 'de', vscode.ConfigurationTarget.Global);
        await settle();

        assert.strictEqual(
            api().getServerLanguage(),
            'en->de',
            'switching back to the previous language should restart, not no-op'
        );
    });
});

/**
 * Path to a stub that passes the availability check and then exits.
 *
 * Written under the OS temp directory rather than the fixtures folder so it
 * cannot be mistaken for a checked-in fixture. The name ends in `lsp` because
 * isServerAvailable() refuses to execute anything that does not look like a
 * Legesher binary.
 */
function brokenServerPath(): string {
    const file = path.join(os.tmpdir(), 'legesher-broken-lsp');
    fs.writeFileSync(
        file,
        '#!/bin/sh\nif [ "$1" = "--version" ]; then echo "0.0.0"; exit 0; fi\nexit 1\n',
        { mode: 0o755 }
    );
    return file;
}
