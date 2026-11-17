/**
 * The editor side of the extension's own server install: the offer to install,
 * the `Legesher: Install Language Server` command, progress, the automatic
 * update when an extension release ships a new lock, and clearing out what an
 * update replaced. The install itself is `managedServer.ts`.
 */

import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';
import { Logger } from './logger';
import {
    type InstalledServer,
    type InstallStep,
    type ManagedServerDeps,
    type ResolvedServerCommand,
    SERVER_LOCK_PATH,
    SERVER_PYTHON,
    type ServerLock,
    installManagedServer,
    isolatedPythonEnv,
    managedServerState,
    parseServerLock,
    removeOtherInstalls,
    resolveServerCommand,
    serverLayout,
    takeLease,
} from './managedServer';
import { isMusl, nodeManagedServerDeps } from './managedServerNode';
import { DEFAULT_SERVER_COMMAND, INSTALL_COMMAND_TITLE, MANUAL_STEPS_URL } from './serverInstall';
import { isServerAvailable } from './utils';
import { UV_VERSION, uvTargetFor, uvTargetKey } from './uvRelease';

/** Set when someone answers the offer with "Don't Ask Again". */
const DECLINED_KEY = 'legesher.serverInstall.declined';

const INSTALL = 'Install';
const MANUAL_STEPS = 'Manual Steps';
const DONT_ASK = "Don't Ask Again";
const RETRY = 'Retry';
const VIEW_OUTPUT = 'View Output';

/** Offered at most once per window, however many times the server is looked for. */
let offered = false;
/**
 * Starts the server again and says whether it is running. Supplied by
 * `extension.ts`, which owns the server's state.
 */
export type Restart = () => Promise<boolean>;

/** The install in flight in this window, so a second request joins it. */
let inFlight: Promise<InstallOutcome> | undefined;
/** The background update is tried at most once per window. */
let updateTried = false;

/** How an install attempt ended: the install, or why it did not finish. */
type InstallOutcome = { installed: InstalledServer } | { reason: string };

function lockPathOf(context: vscode.ExtensionContext): string {
    return path.join(context.extensionPath, ...SERVER_LOCK_PATH);
}

function readLock(context: vscode.ExtensionContext): ServerLock {
    return parseServerLock(fs.readFileSync(lockPathOf(context), 'utf8'));
}

function deps(): ManagedServerDeps {
    const proxy = vscode.workspace.getConfiguration('http').get<string>('proxy') || undefined;
    return nodeManagedServerDeps({ log: message => Logger.info(message), proxy });
}

function layoutOf(context: vscode.ExtensionContext) {
    return serverLayout(path.join(context.globalStorageUri.fsPath, 'language-server'), process.platform);
}

/**
 * The server command to start for `configured` (`legesher.serverCommand`), or
 * undefined when nothing that answers is available. See `resolveServerCommand`
 * for the order.
 */
export async function resolveServer(
    context: vscode.ExtensionContext,
    configured: string
): Promise<ResolvedServerCommand | undefined> {
    let state = {};
    try {
        state = await managedServerState(layoutOf(context), readLock(context), deps());
    } catch (error) {
        Logger.warn("Could not read the extension's own language server install", error);
    }
    return resolveServerCommand(configured, state, (command, isolated) =>
        isServerAvailable(command, isolated ? isolatedPythonEnv(process.env) : undefined)
    );
}

function openManualSteps(): void {
    void vscode.env.openExternal(vscode.Uri.parse(MANUAL_STEPS_URL));
}

const STEP_MESSAGES: Record<InstallStep, string> = {
    uv: `Downloading uv ${UV_VERSION}`,
    server: `Installing Python ${SERVER_PYTHON} and the server`,
    check: 'Checking the server',
};

/** One install attempt with progress, and no message that waits on a person. */
async function attemptInstall(context: vscode.ExtensionContext, mode: 'first' | 'update'): Promise<InstallOutcome> {
    const musl = isMusl(process.platform);
    try {
        const lock = readLock(context);
        const installed = await vscode.window.withProgress(
            {
                location: mode === 'first' ? vscode.ProgressLocation.Notification : vscode.ProgressLocation.Window,
                title: mode === 'first' ? 'Legesher: installing the language server' : 'Legesher: updating the language server',
            },
            progress => installManagedServer(
                {
                    layout: layoutOf(context),
                    lock,
                    lockPath: lockPathOf(context),
                    target: uvTargetFor(process.platform, process.arch, musl),
                    platformKey: uvTargetKey(process.platform, process.arch, musl),
                    onStep: step => progress.report({ message: STEP_MESSAGES[step] }),
                },
                deps()
            )
        );
        return { installed };
    } catch (error) {
        const reason = error instanceof Error ? error.message : String(error);
        Logger.error('Language server install failed', reason);
        return { reason };
    }
}

/**
 * Install the server for this extension's lock, with progress, and say how it
 * went. Resolves to the install, or undefined when it failed (already told to
 * the user, by the caller that started it). Concurrent calls in one window
 * share one attempt.
 *
 * The attempt in flight is cleared before any message is shown, because a
 * notification with buttons can wait in the notification centre indefinitely,
 * and the Install command and the offer must not wait behind it.
 *
 * @param mode `first` shows progress as a notification and announces the
 *   result; `update` shows progress in the status bar and announces only the
 *   new version, since the old server keeps working meanwhile.
 * @param restart Starts the server again once the install is done.
 */
export async function installServer(
    context: vscode.ExtensionContext,
    mode: 'first' | 'update',
    restart: Restart
): Promise<InstalledServer | undefined> {
    if (inFlight) {
        const joined = await inFlight;
        return 'installed' in joined ? joined.installed : undefined;
    }
    const attempt = attemptInstall(context, mode);
    inFlight = attempt;
    let outcome: InstallOutcome;
    try {
        outcome = await attempt;
    } finally {
        inFlight = undefined;
    }

    if (!('installed' in outcome)) {
        const action = await vscode.window.showErrorMessage(
            mode === 'first'
                ? `Legesher could not install its language server: ${outcome.reason}.`
                : `Legesher could not update its language server, and keeps using the one it has: ${outcome.reason}.`,
            RETRY,
            MANUAL_STEPS,
            VIEW_OUTPUT
        );
        if (action === RETRY) {
            return installServer(context, mode, restart);
        }
        if (action === MANUAL_STEPS) {
            openManualSteps();
        } else if (action === VIEW_OUTPUT) {
            Logger.show();
        }
        return undefined;
    }

    const { installed } = outcome;
    const running = await restart();
    // Said only when the server it installed is the one now answering. A
    // start that failed has already been reported by the state machine, and a
    // success message on top of it would contradict the status bar.
    if (running) {
        void vscode.window.showInformationMessage(
            mode === 'first'
                ? "Legesher's language server is installed. Hover, completion, diagnostics and keyword highlighting are on."
                : `Legesher updated its language server to ${installed.serverVersion}.`
        );
    }
    return installed;
}

/**
 * Offer to install the server, once per window, unless the person said not to
 * ask again. Not awaited by callers: the offer waits on a person.
 */
export async function offerServerInstall(
    context: vscode.ExtensionContext,
    restart: Restart
): Promise<void> {
    if (offered || inFlight || context.globalState.get<boolean>(DECLINED_KEY, false)) {
        return;
    }
    offered = true;
    const action = await vscode.window.showInformationMessage(
        'Legesher needs its language server for hover, completion, diagnostics and keyword highlighting. ' +
        'Install it now? The extension downloads about 60 MB into its own storage; no terminal needed.',
        INSTALL,
        MANUAL_STEPS,
        DONT_ASK
    );
    if (action === INSTALL) {
        await installServer(context, 'first', restart);
    } else if (action === MANUAL_STEPS) {
        openManualSteps();
    } else if (action === DONT_ASK) {
        await context.globalState.update(DECLINED_KEY, true);
        void vscode.window.showInformationMessage(`You can install it later with "${INSTALL_COMMAND_TITLE}".`);
    }
}

/**
 * The `Legesher: Install Language Server` command.
 *
 * Says so instead of installing when the extension already runs a server the
 * person set up themselves, because that server would still be the one used.
 * The setting is read for the focused document, as the server's start reads it.
 */
export async function installServerCommand(
    context: vscode.ExtensionContext,
    restart: Restart
): Promise<void> {
    const resource = vscode.window.activeTextEditor?.document.uri;
    const configured = vscode.workspace.getConfiguration('legesher', resource).get<string>('serverCommand', DEFAULT_SERVER_COMMAND);
    const resolved = await resolveServer(context, configured);
    if (resolved?.source === 'setting' || resolved?.source === 'path') {
        void vscode.window.showInformationMessage(
            resolved.source === 'setting'
                ? `Legesher already uses the language server in legesher.serverCommand ("${resolved.command}"), ahead of its own install.`
                : 'Legesher already uses the legesher-lsp on your PATH, ahead of its own install.'
        );
        return;
    }
    if (resolved?.source === 'managed') {
        const version = resolved.installed ? ` ${resolved.installed.serverVersion}` : '';
        void vscode.window.showInformationMessage(`Legesher's language server${version} is already installed.`);
        return;
    }
    await installServer(context, resolved?.source === 'managed-stale' ? 'update' : 'first', restart);
}

/** The installs this window has already cleared around, so a restart does not repeat it. */
const clearedAround = new Set<string>();

/**
 * After the server started: record that this window runs it, then either
 * update it (an install an older extension release made; tried once per
 * window) or clear out the installs it replaced (once per window, unless
 * another window was installing at the time). Not awaited by callers: this
 * runs from inside the server's transition queue, and the restart an update
 * ends with queues behind it.
 */
export async function serverStarted(
    context: vscode.ExtensionContext,
    resolved: ResolvedServerCommand,
    restart: Restart
): Promise<void> {
    const installed = resolved.installed;
    if (!installed) {
        return;
    }
    const layout = layoutOf(context);
    try {
        await takeLease(layout, installed.id, deps());
    } catch (error) {
        Logger.warn('Could not record which language server install this window runs', error);
    }

    if (resolved.source === 'managed-stale') {
        if (!updateTried) {
            updateTried = true;
            await installServer(context, 'update', restart);
        }
        return;
    }

    if (clearedAround.has(installed.id)) {
        return;
    }
    try {
        const removed = await removeOtherInstalls(layout, installed.id, deps());
        if (removed === undefined) {
            return; // Another window is installing; the next start tries again.
        }
        clearedAround.add(installed.id);
        if (removed.length > 0) {
            Logger.info(`Removed the replaced language server installs: ${removed.join(', ')}`);
        }
    } catch (error) {
        Logger.warn('Could not remove the replaced language server installs', error);
    }
}
