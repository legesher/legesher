/**
 * Integration tests for what the client does when the connection to its
 * server closes (CORE-2316).
 *
 * The close handler returned `{ action: 2 }`, meant as "do not restart". In
 * vscode-languageclient 2 is `CloseAction.Restart`, so every unexpected close
 * started the server again from inside the client, where the extension's state
 * machine could not see it. A binary that died on the handshake was relaunched
 * in a loop for the life of the window, and a server that crashed was brought
 * back with whatever languages its client had been created with. The restart
 * lives inside vscode-languageclient, so only a real editor shows it: each stub
 * below records every launch, and the tests count them.
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
}

const EXTENSION_ID = 'legesher.legesher-vscode';
const ENGLISH_FIXTURE = 'sample.py';

/**
 * How long to watch for a launch nobody asked for.
 *
 * The loop this guards against relaunched as soon as each process exited, over
 * four thousand times in a three-minute run, so a few seconds always hold one.
 * A correct client launches nothing in that time however slow the machine is:
 * a longer wait can only make a failure more likely to show, never make a pass
 * flaky.
 */
const QUIET_MS = 3_000;

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

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

async function waitUntil(describe: string, condition: () => boolean, timeoutMs = 45_000): Promise<void> {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
        if (condition()) {
            return;
        }
        await sleep(250);
    }
    assert.fail(`timed out after ${timeoutMs}ms waiting for ${describe}`);
}

function api(): LegesherApi {
    const extension = vscode.extensions.getExtension<LegesherApi>(EXTENSION_ID);
    assert.ok(extension?.exports, `${EXTENSION_ID} should export its diagnostic API`);
    return extension!.exports;
}

/** Wait for the change to `identity` to finish with `outcome`. */
async function transitionEnds(identity: string, outcome: string): Promise<void> {
    await waitUntil(
        `the change to ${identity} to be recorded as ${outcome}`,
        () => api().getLastTransition()?.to === identity
            && api().getLastTransition()?.outcome === outcome
    );
}

/** Every file a stub wrote, removed once the suite is done. */
const written: string[] = [];

/** A server command that records its launches, and how to read the count. */
interface CountingServer {
    command: string;
    launches(): number;
}

/** How many lines `file` holds: one per recorded event, none if it does not exist. */
function linesIn(file: string): number {
    return fs.existsSync(file)
        ? fs.readFileSync(file, 'utf8').split('\n').filter(line => line !== '').length
        : 0;
}

/**
 * Write an executable server stub that appends a line to its own log on every
 * launch, then runs `body`.
 *
 * The availability probe (`--version`) answers and exits before anything is
 * recorded, so only launches that open a connection are counted. The files go
 * under the OS temp directory, named with this process's id so concurrent runs
 * cannot share a log. The name contains `legesher`, which isServerAvailable()
 * looks for before it runs a command.
 */
function countingServer(label: string, body: string): CountingServer {
    const base = path.join(os.tmpdir(), `legesher-core-2316-${process.pid}-${label}`);
    const log = `${base}.log`;
    const command = `${base}-lsp`;
    fs.rmSync(log, { force: true });
    fs.writeFileSync(
        command,
        [
            '#!/bin/sh',
            'if [ "$1" = "--version" ]; then echo "0.0.0"; exit 0; fi',
            `echo "$$" >> ${shellQuoted(log)}`,
            body,
        ].join('\n') + '\n',
        { mode: 0o755 }
    );
    written.push(command, log);
    return { command, launches: () => linesIn(log) };
}

function shellQuoted(text: string): string {
    return `'${text.replace(/'/g, `'\\''`)}'`;
}

/**
 * A server that completes the handshake and then exits: a crash after the
 * session is up, rather than a failure to start.
 *
 * Just enough of the protocol to be taken for a running server: it answers
 * `initialize` with no capabilities, and exits half a second after the client
 * sends `initialized`, which is after the extension has recorded the change as
 * applied. Each exit is recorded too, so a test can wait for the crash rather
 * than assume it. It runs on the editor's own Node runtime rather than on
 * whatever `node` the PATH offers, the way vscode-languageclient runs Node
 * servers.
 */
function crashingServer(): CountingServer & { exits(): number } {
    const base = path.join(os.tmpdir(), `legesher-core-2316-${process.pid}-crashing`);
    const script = `${base}-server.js`;
    const exitLog = `${base}-exits.log`;
    fs.rmSync(exitLog, { force: true });
    fs.writeFileSync(script, `
const fs = require('fs');
let buffer = Buffer.alloc(0);
process.stdin.on('data', chunk => {
    buffer = Buffer.concat([buffer, chunk]);
    for (;;) {
        const end = buffer.indexOf('\\r\\n\\r\\n');
        if (end < 0) {
            return;
        }
        const length = Number(/Content-Length: *(\\d+)/i.exec(buffer.subarray(0, end).toString('ascii'))[1]);
        if (buffer.length < end + 4 + length) {
            return;
        }
        const message = JSON.parse(buffer.subarray(end + 4, end + 4 + length).toString('utf8'));
        buffer = buffer.subarray(end + 4 + length);
        if (message.method === 'initialize') {
            const body = JSON.stringify({ jsonrpc: '2.0', id: message.id, result: { capabilities: {} } });
            process.stdout.write('Content-Length: ' + Buffer.byteLength(body) + '\\r\\n\\r\\n' + body);
        } else if (message.method === 'initialized') {
            setTimeout(() => {
                fs.appendFileSync(${JSON.stringify(exitLog)}, process.pid + '\\n');
                process.exit(1);
            }, 500);
        }
    }
});
`);
    written.push(script, exitLog);
    const server = countingServer(
        'crashing',
        `ELECTRON_RUN_AS_NODE=1 exec ${shellQuoted(process.execPath)} ${shellQuoted(script)}`
    );
    return { ...server, exits: () => linesIn(exitLog) };
}

describe('A closed connection is not reopened by the client (CORE-2316)', function () {
    this.timeout(120_000);

    let serverPath: string;

    before(async () => {
        const found = findLanguageServer();
        assert.ok(
            found,
            'legesher-lsp not found in any parent .venv: run `uv sync --all-packages` at the repo root'
        );
        serverPath = found!;
        await legesherConfig().update('serverCommand', serverPath, vscode.ConfigurationTarget.Global);

        const extension = vscode.extensions.getExtension(EXTENSION_ID);
        assert.ok(extension, `${EXTENSION_ID} should be present`);
        await extension!.activate();
    });

    beforeEach(async () => {
        // Each test starts from a running server at a known pair, so the first
        // change it asks for is a real change that needs a new process.
        const config = legesherConfig();
        await config.update('languageDetection', 'off', vscode.ConfigurationTarget.Global);
        await config.update('targetLanguage', 'de', vscode.ConfigurationTarget.Global);
        await openFixture(ENGLISH_FIXTURE);
        await waitUntil('the server to be running at en->de', () => api().getServerLanguage() === 'en->de');
    });

    afterEach(async () => {
        // The working server first, so the settings cleared below restart onto
        // it rather than onto a stub.
        await legesherConfig().update('serverCommand', serverPath, vscode.ConfigurationTarget.Global);
        for (const key of ['targetLanguage', 'workingLanguage', 'languageDetection']) {
            if (legesherConfig().inspect(key)?.globalValue !== undefined) {
                await legesherConfig().update(key, undefined, vscode.ConfigurationTarget.Global);
            }
        }
    });

    after(async () => {
        await legesherConfig().update('serverCommand', undefined, vscode.ConfigurationTarget.Global);
        for (const file of written) {
            fs.rmSync(file, { force: true });
        }
    });

    it('launches a binary that dies on the handshake once per requested change', async () => {
        // What a broken install or a version mismatch looks like: the binary
        // answers --version, then exits before the handshake completes.
        const broken = countingServer('broken', 'exit 1');
        await legesherConfig().update('serverCommand', broken.command, vscode.ConfigurationTarget.Global);

        for (const [requested, language] of [[1, 'fr'], [2, 'es']] as const) {
            await legesherConfig().update('targetLanguage', language, vscode.ConfigurationTarget.Global);
            await transitionEnds(`en->${language}`, 'failed');
            await sleep(QUIET_MS);
            assert.strictEqual(
                broken.launches(),
                requested,
                `${requested} language change(s) launched the broken server ${broken.launches()} times: ` +
                'the client relaunched it after the connection closed'
            );
        }
    });

    it('does not bring back a server that crashes after starting', async () => {
        const crashing = crashingServer();
        await legesherConfig().update('serverCommand', crashing.command, vscode.ConfigurationTarget.Global);

        await legesherConfig().update('targetLanguage', 'fr', vscode.ConfigurationTarget.Global);
        await transitionEnds('en->fr', 'applied');
        // Seen, not assumed: a stub that never crashed would pass the count
        // below without testing anything.
        await waitUntil('the crashing server to exit', () => crashing.exits() >= 1);
        await sleep(QUIET_MS);

        assert.strictEqual(
            crashing.launches(),
            1,
            `one language change launched the crashing server ${crashing.launches()} times: ` +
            'the client relaunched it after the connection closed'
        );
    });
});
