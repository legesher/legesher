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
import { getActiveLanguages, getLanguageConfig } from '../../src/config';
import { partitionByKnown } from '../../src/languageProfile';

/**
 * The extension's diagnostic API, restated rather than imported.
 *
 * Importing it from `src/extension` would pull vscode-languageclient into this
 * compilation, which the integration tsconfig cannot resolve. Restating it is
 * also the more honest test: this is the contract as a consumer sees it, and it
 * fails loudly here if the real shape drifts.
 */
interface LanguageTransition {
    from: string;
    to: string;
    trigger: string;
    source: string;
    outcome: 'applied' | 'unchanged' | 'failed' | 'serverUnavailable';
}

interface LegesherApi {
    getServerLanguage(): string | undefined;
    getLastTransition(): LanguageTransition | undefined;
}

const EXTENSION_ID = 'legesher.legesher-vscode';
const ENGLISH_FIXTURE = 'sample.py';
/** A second file to switch to: re-opening the active editor fires no editor change. */
const GERMAN_FIXTURE = 'sample_de.py';

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

/**
 * How long a test gives a no-op re-sync to misbehave.
 *
 * One of two waits here that cannot poll; the other is the picker's render wait
 * in `pickLanguageAt`. A re-sync that resolves to the language already running
 * records no transition and changes no state, by design, so "nothing happened"
 * has no observable end. Everything else waits on what it needs to see instead
 * (CORE-2323): a fixed sleep raced the restart queue, and failed in 3 of 5 full
 * runs.
 */
const QUIET_MS = 6_000;

/**
 * How long a test waits for a restart it asked for.
 *
 * Only a failing run pays it: every wait returns as soon as its condition
 * holds. At a load average near 200 a restart took about 25 s, and the longest
 * wait here spans two of them.
 */
const RESTART_WAIT_MS = 90_000;

/** The extension's view of the server, for failure messages. */
function serverState(): string {
    const transition = api().getLastTransition();
    return `server ${api().getServerLanguage() ?? 'none'}, last transition `
        + (transition ? `${transition.from} -> ${transition.to} (${transition.outcome})` : 'none');
}

/**
 * Wait until `condition` holds, or fail saying what was still true instead.
 *
 * Preferred over a fixed sleep wherever the thing being waited for is
 * observable. A fixed sleep is a bet that the machine is not busy: too short and
 * it flakes, too long and every test pays for the worst case. Polling an actual
 * condition removes both, and a timeout here reports the state it gave up on
 * rather than failing later on an assertion that looks unrelated.
 */
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
    assert.fail(`timed out after ${timeoutMs}ms waiting for ${describe}; ${serverState()}`);
}

/** Wait until the extension reports a running server at `identity`. */
async function serverRunningAt(identity: string): Promise<void> {
    await waitUntil(
        `the server to be running at ${identity}`,
        () => api().getServerLanguage() === identity
    );
}

/**
 * Wait for a transition to `to` recorded after `before`, and return it.
 *
 * A record is written when a transition finishes, as a new object each time, so
 * comparing with the record read before a settings write cannot match one an
 * earlier test left behind with the same target.
 */
async function transitionAfter(
    before: LanguageTransition | undefined,
    to: string
): Promise<LanguageTransition> {
    await waitUntil(`a transition to ${to} to be recorded`, () => {
        const transition = api().getLastTransition();
        return transition !== before && transition?.to === to;
    });
    return api().getLastTransition()!;
}

/**
 * Hover at `token` until `accept` holds, and return the text.
 *
 * For the tests that read a hover, the hover is the end of the restart: the
 * server answers once it is up, and an empty answer before that is what the
 * fixed sleeps lost to. A timeout reports the last text seen.
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
        + `last hover: ${text.slice(0, 200) || '(empty)'}; ${serverState()}`
    );
}

/** What `cleanupSettled` gave up on, for the suite's `after` to report. */
const cleanupMisses: string[] = [];

/**
 * Wait for the restarts a test's cleanup asked for, so the next test's own
 * restarts do not queue behind them.
 *
 * Restarts run one at a time, and a test that leaves some queued hands them to
 * the next test, whose waits then pay for both. Under load, one slow test
 * failed the three after it that way (CORE-2323). The server's identity
 * follows only the source and working languages, and cleanup only returns
 * settings to their defaults, so the queue is done once it runs at en->en.
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
    const miss = `cleanup did not reach en->en within ${RESTART_WAIT_MS}ms; ${serverState()}`;
    console.warn(miss);
    cleanupMisses.push(miss);
}

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
 * assert on what landed. The items are `Auto` followed by known languages and
 * then the rest (CORE-1760) — reproduced here by `pickerOrder()`, since
 * separators are not focusable and cost no keystrokes — and the widget opens
 * with `Auto` active.
 */

/** The selectable languages in the order the picker presents them. */
function pickerOrder(): Array<{ code: string }> {
    const { known, others } = partitionByKnown(
        getActiveLanguages(),
        getLanguageConfig().knownLanguages
    );
    return [...known, ...others];
}

async function pickLanguageAt(offset: number): Promise<string> {
    const languages = pickerOrder();
    assert.ok(offset < languages.length, `offset ${offset} should exist in the language list`);
    const expected = languages[offset].code;

    const picked = vscode.commands.executeCommand('legesher.selectLanguage');
    // Let the widget render before sending keys. Not polled: no extension API
    // reports that a quick pick is open. A miss is caught below, where the
    // pick's result is polled for (CORE-1847).
    await sleep(3_000);

    for (let i = 0; i <= offset; i++) { // +1 to step past the leading "Auto" item
        await vscode.commands.executeCommand('workbench.action.quickOpenSelectNext');
    }
    await vscode.commands.executeCommand('workbench.action.acceptSelectedQuickOpenItem');
    await picked;

    // Fail here, on the pick, rather than three assertions later on a language
    // that never changed. Driving a widget with blind keystrokes can miss — the
    // keys land before it renders and the pick is silently cancelled — and that
    // failure used to surface as a confusing mismatch in whatever the test was
    // really about (CORE-1847).
    await waitUntil(
        `the picker to select ${expected}`,
        () => legesherConfig().get<string>('workingLanguage') === expected,
        20_000
    );

    return expected;
}

/** A language near the top of the picker that is not `avoid`. */
function nearbyLanguageOffset(avoid: string): number {
    const offset = pickerOrder().findIndex(lang => lang.code !== avoid);
    assert.notStrictEqual(offset, -1, 'the picker should offer at least one other language');
    return offset;
}

describe('Language-resolution scopes (CORE-1776)', function () {
    // Long enough for every wait in the slowest test to reach its own deadline,
    // so a failure reports the poll's message rather than a bare mocha timeout.
    this.timeout(360_000);

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
        for (const key of [
            'targetLanguage', 'workingLanguage', 'knownLanguages',
            'sourceLanguage', 'languageDetection',
        ]) {
            const inspected = legesherConfig().inspect(key);
            if (inspected?.workspaceValue !== undefined) {
                await legesherConfig().update(key, undefined, vscode.ConfigurationTarget.Workspace);
            }
            if (inspected?.globalValue !== undefined) {
                await legesherConfig().update(key, undefined, vscode.ConfigurationTarget.Global);
            }
        }

        await cleanupSettled();
    });

    after(async () => {
        await legesherConfig().update('serverCommand', undefined, vscode.ConfigurationTarget.Global);
        assert.deepStrictEqual(
            cleanupMisses, [], 'every cleanup should bring the server back to en->en'
        );
    });

    it('applies a pick when a workspace setting supplies the language', async () => {
        // The demo-repo configuration, and the reason this issue is urgent. The
        // picker wrote Global while resolution honoured the workspace value, so
        // the language never changed and the notification said it had.
        const config = legesherConfig();
        await config.update('targetLanguage', 'de', vscode.ConfigurationTarget.Workspace);
        await config.update('languageDetection', 'off', vscode.ConfigurationTarget.Workspace);

        const document = await openFixture(ENGLISH_FIXTURE);
        const before = await hoverWhen(
            document, 'print', 'a German hover before the pick', text => text.includes('drucken')
        );
        assert.ok(
            before.includes('drucken'),
            `expected German before the pick, got: ${before.slice(0, 200)}`
        );

        const chosen = await pickLanguageAt(nearbyLanguageOffset('de'));

        // The write has to land where it can win, not merely be written. The
        // pick writes the new setting, but at the scope the deprecated alias
        // supplied — Global would lose to the alias's workspace value
        // (CORE-1760).
        const inspected = legesherConfig().inspect<string>('workingLanguage');
        assert.strictEqual(
            inspected?.workspaceValue,
            chosen,
            'the pick should be written at the scope that supplies the value'
        );
        assert.strictEqual(
            legesherConfig().get<string>('workingLanguage'),
            chosen,
            'the effective setting should be the picked language'
        );

        // And it has to reach the server, not just the settings file.
        await serverRunningAt(`en->${chosen}`);
        assert.strictEqual(
            api().getServerLanguage(),
            `en->${chosen}`,
            'the running server should have been restarted at the picked language'
        );

        // A non-empty hover is the restarted server answering; an empty one
        // would pass the check below without testing anything.
        const after = await hoverWhen(
            document, 'print', `a hover from the server at ${chosen}`, text => text.length > 0
        );
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
        await serverRunningAt('en->de');

        const chosen = await pickLanguageAt(nearbyLanguageOffset('de'));

        const inspected = legesherConfig().inspect<string>('workingLanguage');
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
        // Polled, not slept (CORE-2323): a fixed wait read the identity
        // mid-restart, when it is undefined.
        await serverRunningAt('es->de');

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
        // Polled rather than slept: a fixed sleep is a bet on how long the
        // restarts ahead of this one take, a bet this test lost once the
        // picker tests before it started completing real picks.
        await waitUntil(
            'the server to be running at en->de',
            () => api().getServerLanguage() === 'en->de'
        );

        // A binary that answers --version but dies on the LSP handshake, which
        // is what a broken install or a version mismatch looks like in practice.
        await config.update('serverCommand', brokenServerPath(), vscode.ConfigurationTarget.Global);
        await config.update('targetLanguage', 'fr', vscode.ConfigurationTarget.Global);
        // The observable end of the failed change is its recorded outcome; the
        // identity check below is the claim under test, made once the
        // transition has actually finished.
        await waitUntil(
            'the change to fr to be recorded as failed',
            () => api().getLastTransition()?.to === 'en->fr'
                && api().getLastTransition()?.outcome === 'failed'
        );

        assert.strictEqual(
            api().getServerLanguage(),
            undefined,
            'a failed start must not leave an identity claiming a running server'
        );

        // And the previous language must be reachable again rather than being
        // swallowed as a no-op against a stale cache entry.
        await config.update('serverCommand', serverPath, vscode.ConfigurationTarget.Global);
        await config.update('targetLanguage', 'de', vscode.ConfigurationTarget.Global);
        await waitUntil(
            'the server to be running at en->de again',
            () => api().getServerLanguage() === 'en->de'
        );

        assert.strictEqual(
            api().getServerLanguage(),
            'en->de',
            'switching back to the previous language should restart, not no-op'
        );
    });

    describe('transitions are reported rather than swallowed (CORE-1776)', () => {
        // Every failure in this subsystem used to end in a log line while the
        // status bar and the notifications went on claiming success. These pin
        // the outcome each transition actually reached.

        it('reports an applied transition, with what triggered it', async () => {
            await legesherConfig().update('targetLanguage', 'de', vscode.ConfigurationTarget.Global);
            await legesherConfig().update('languageDetection', 'off', vscode.ConfigurationTarget.Global);
            await openFixture(ENGLISH_FIXTURE);
            await serverRunningAt('en->de');

            const beforePick = api().getLastTransition();
            const chosen = await pickLanguageAt(nearbyLanguageOffset('de'));
            const transition = await transitionAfter(beforePick, `en->${chosen}`);
            assert.ok(transition, 'a transition should have been recorded');
            assert.strictEqual(transition!.outcome, 'applied');
            assert.strictEqual(transition!.to, `en->${chosen}`);
            assert.strictEqual(transition!.trigger, 'picker');
        });

        it('reports a failed transition instead of logging and moving on', async () => {
            const config = legesherConfig();
            await config.update('languageDetection', 'off', vscode.ConfigurationTarget.Global);
            await config.update('targetLanguage', 'de', vscode.ConfigurationTarget.Global);
            await openFixture(ENGLISH_FIXTURE);
            await serverRunningAt('en->de');

            const beforeChange = api().getLastTransition();
            await config.update('serverCommand', brokenServerPath(), vscode.ConfigurationTarget.Global);
            await config.update('targetLanguage', 'fr', vscode.ConfigurationTarget.Global);

            const transition = await transitionAfter(beforeChange, 'en->fr');
            assert.ok(transition, 'a failed transition should still be recorded');
            assert.strictEqual(
                transition!.outcome,
                'failed',
                'a language the server never reached must not report as applied'
            );
            assert.strictEqual(transition!.to, 'en->fr');
            assert.strictEqual(transition!.trigger, 'settings');
        });

        it('keeps reporting no server when the binary is missing', async () => {
            // The missing-binary case still records an identity, so that the
            // availability check is not re-run on every editor switch. That made
            // the next sync match the cache and call itself unchanged — and
            // anything painting from that outcome put the healthy badge back
            // over the warning, which is the signal it was covering up.
            const config = legesherConfig();
            const beforeChange = api().getLastTransition();
            await config.update('languageDetection', 'off', vscode.ConfigurationTarget.Global);
            await config.update(
                'serverCommand', '/nonexistent/legesher-lsp', vscode.ConfigurationTarget.Global
            );
            await config.update('targetLanguage', 'de', vscode.ConfigurationTarget.Global);
            await openFixture(ENGLISH_FIXTURE);
            await transitionAfter(beforeChange, 'en->de');

            assert.strictEqual(
                api().getLastTransition()!.outcome,
                'serverUnavailable',
                'a missing binary is not an applied language change'
            );
            assert.strictEqual(api().getServerLanguage(), undefined, 'no server should be running');

            // A re-sync that resolves to the same language, which is the no-op
            // that used to erase the signal. Re-opening the active editor fires
            // no editor change, so switch to another file and back: with
            // detection off, both resolve to the language already asked for.
            // They change nothing when correct, so there is nothing to poll
            // for: give them QUIET_MS to misbehave.
            await openFixture(GERMAN_FIXTURE);
            await openFixture(ENGLISH_FIXTURE);
            await sleep(QUIET_MS);

            assert.strictEqual(
                api().getServerLanguage(),
                undefined,
                'a no-op re-sync must not start reporting a server that never ran'
            );
            assert.strictEqual(
                api().getLastTransition()!.outcome,
                'serverUnavailable',
                'the unavailable outcome must survive the no-ops that follow it'
            );
        });

        it('does not let a redundant re-sync overwrite the real outcome', async () => {
            // A pick fires its own sync *and* the configuration listener, so one
            // user action produces an `applied` followed by an `unchanged`
            // (CORE-1728). Recording the second would report every successful
            // change as a no-op — and every editor switch, which re-resolves to
            // the language already running, would emit one too.
            const config = legesherConfig();
            const beforeChange = api().getLastTransition();
            await config.update('languageDetection', 'off', vscode.ConfigurationTarget.Global);
            await config.update('targetLanguage', 'de', vscode.ConfigurationTarget.Global);
            await openFixture(ENGLISH_FIXTURE);

            const applied = await transitionAfter(beforeChange, 'en->de');
            assert.ok(applied, 'the change to de should have been recorded');
            assert.strictEqual(applied!.outcome, 'applied');
            assert.strictEqual(applied!.to, 'en->de');

            // Switch to another file and back: full re-syncs that resolve to
            // the same language and must leave the record alone. Re-opening the
            // active editor alone would fire no editor change. Nothing to poll
            // for, as above: give them QUIET_MS to misbehave.
            await openFixture(GERMAN_FIXTURE);
            await openFixture(ENGLISH_FIXTURE);
            await sleep(QUIET_MS);

            const after = api().getLastTransition();
            assert.strictEqual(
                after!.outcome,
                'applied',
                'a no-op re-sync must not overwrite the outcome that actually happened'
            );
            assert.strictEqual(after!.to, 'en->de');
        });
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
