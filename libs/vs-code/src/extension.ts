import * as vscode from 'vscode';
import { LanguageClient } from 'vscode-languageclient/node';
import { createLanguageClient } from './client';
import { isServerAvailable } from './utils';
import {
    getLanguageConfig,
    getActiveLanguages,
    getLanguageName,
    getSettingScope,
    type LanguageConfig,
    type ResolvedLanguages,
    type SettingScope,
} from './config';
import {
    buildResolvedLanguages,
    identityFileLanguage,
    isUnfamiliarFileLanguage,
    partitionByKnown,
    serverIdentityOf,
} from './languageProfile';
import { TranslationPanelManager } from './webview/panel';
import { Logger } from './logger';
import { LegesherTelemetry } from './telemetry';
import {
    LanguageServerState,
    type LanguageTrigger,
    type ResolutionSource,
    type StartResult,
    type TransitionOutcome,
    type TransitionRecord,
} from './serverState';
import { initializeFeedback, getFeedbackInstance } from './feedback';
import { initializeKeywords } from './keywords';
import { loadEnvVariables } from './env';
import { OnboardingManager } from './onboarding';
import { loadAllTranslations } from './languagePackLoader';
import { buildVocabularies, detectLanguage, PackVocabulary } from './languageDetection';
import { DetectionCache } from './detectionCache';

let client: LanguageClient | undefined;
let statusBarItem: vscode.StatusBarItem;
let languageStatusBarItem: vscode.StatusBarItem;
/**
 * The extension's log channel.
 *
 * Typed as `LogOutputChannel`, not `OutputChannel`, and that is load-bearing:
 * vscode-languageclient 10 logs through `.error`/`.warn`/`.info`, which only
 * exist on the log variant, so a plain channel makes `client.start()` throw
 * while logging and takes down every LSP feature (CORE-1733). Widening the type
 * here is what let that be a runtime explosion rather than a compile error —
 * once `src/` was actually typechecked, this was the one real mistake in the
 * package (CORE-1854).
 */
let outputChannel: vscode.LogOutputChannel;

/**
 * Everything about which language the server is serving, and the only thing
 * that changes it (CORE-1847).
 *
 * This replaces five module-level variables — the identity, the status, the
 * serialisation chain, the last transition and the failure-announcement
 * suppression — that between them described one situation and could disagree
 * about it. Every defect fixed in CORE-1776 was two of them out of step. See
 * `serverState.ts` for the invariants, which are unit-tested there rather than
 * inferred from a running editor.
 */
const server = new LanguageServerState();

/** Detection vocabularies, built once from the bundled packs. */
let vocabularies: PackVocabulary[] | undefined;
/** Detection results by (uri, document version), so editor switches are free. */
const detectionCache = new DetectionCache();

/**
 * The user action currently in flight, if any.
 *
 * Writing a setting fires the configuration listener, which runs its own sync
 * and usually wins the race — so a language chosen from the picker was recorded
 * as a hand-edited setting, and the one distinction the trigger exists to draw
 * was the one it got wrong. While an action is in flight every sync it causes,
 * directly or through the listener, is attributed to it (CORE-1776).
 */
let pendingTrigger: LanguageTrigger | undefined;

/**
 * Where the language in effect came from, for the status bar.
 *
 * The same vocabulary the telemetry uses, by construction rather than by
 * coincidence — an analytics enum that quietly diverges from the resolver's
 * would make the data describe a system that no longer exists.
 */
type LanguageSource = ResolutionSource;

interface ResolvedLanguage {
    language: string;
    source: LanguageSource;
    /**
     * The configuration read while resolving.
     *
     * Returned rather than left for the caller to read again: three call sites
     * used to pair a resolveLanguage() with their own getLanguageConfig(), and
     * a pair of reads that can disagree is what let the recorded language and
     * the running server drift apart (CORE-1776).
     */
    config: LanguageConfig;
}

function getVocabularies(context: vscode.ExtensionContext): PackVocabulary[] {
    if (!vocabularies) {
        vocabularies = buildVocabularies(loadAllTranslations(context.extensionPath));
        Logger.info(`Language detection ready: ${vocabularies.length} vocabularies`);
    }
    return vocabularies;
}

/**
 * The language roles implied by a resolution, ready for the server.
 *
 * The resolved language is the *file* language — it is what detection decides
 * — and the working language rides alongside it from the same configuration
 * read. They are carried as separate slots all the way to the server; the old
 * model collapsed them into one value here, which is why hover could only
 * ever render a file back into itself or English (CORE-1760).
 */
function languagesOf(resolved: ResolvedLanguage): ResolvedLanguages {
    return buildResolvedLanguages(
        resolved.config.sourceLanguage,
        resolved.language,
        resolved.config.workingLanguage
    );
}

/**
 * Decide which language applies to a document (CORE-1729).
 *
 * Precedence: folder / workspace setting > detected from content > user setting
 * > default.
 *
 * Detection deliberately outranks the *user* setting. A global preference is a
 * default, not a claim about the file on screen; showing Spanish keyword help
 * for a file demonstrably written in German helps nobody. A folder or workspace
 * setting is a deliberate statement about this project, so it still wins.
 */
function resolveLanguage(
    context: vscode.ExtensionContext,
    document?: vscode.TextDocument
): ResolvedLanguage {
    const config = getLanguageConfig(document?.uri);

    if (config.scope === 'folder' || config.scope === 'workspace') {
        return { language: config.workingLanguage, source: config.scope, config };
    }

    // An explicit pick turns detection off, so the chosen language survives
    // switching to a file that would detect as something else. Detection
    // outranking a global *preference* is right — a default is not a claim about
    // the file on screen — but it must not override a deliberate choice
    // (CORE-1754).
    const detectionEnabled = vscode.workspace
        .getConfiguration('legesher', document?.uri)
        .get<string>('languageDetection', 'auto') === 'auto';

    if (detectionEnabled && document && document.languageId === 'python') {
        // Memoized on (uri, version): this runs on every editor switch, and the
        // result only changes when the text does (CORE-1776).
        const detected = detectionCache.get(
            document.uri.toString(),
            document.version,
            () => {
                const result = detectLanguage(document.getText(), getVocabularies(context));
                // Recorded on the compute path only, so the memo keeps this to
                // one event per document version rather than one per switch.
                // Declines are recorded too: a detector that never fires and one
                // that fires constantly are different problems, and only the
                // scores tell them apart (CORE-1776).
                LegesherTelemetry.trackLanguageDetection(
                    result ? 'detected' : 'declined',
                    result
                        ? {
                            language: result.language,
                            score: result.score,
                            runnerUpScore: result.runnerUp?.score,
                        }
                        : {}
                );
                return result;
            }
        );
        if (detected) {
            Logger.debug(
                `Detected ${detected.language} (score ${detected.score}` +
                `${detected.runnerUp ? `, runner-up ${detected.runnerUp.language} ${detected.runnerUp.score}` : ''})`
            );
            return { language: detected.language, source: 'detected', config };
        }
    }

    return {
        language: config.workingLanguage,
        source: config.scope === 'user' ? 'user' : 'default',
        config,
    };
}

/**
 * Bring the running server in line with `languages`.
 *
 * Idempotent and serialised: if the server already speaks that pair this is a
 * no-op, and concurrent callers queue rather than restarting on top of each
 * other. That is what makes it safe to re-enable the configuration listener —
 * whichever trigger arrives first performs the restart and the rest collapse
 * into no-ops, instead of racing as the old auto-restart did (CORE-1728).
 */
function ensureServerLanguage(
    context: vscode.ExtensionContext,
    languages: ResolvedLanguages,
    options: { resource?: vscode.Uri; trigger: LanguageTrigger; source: ResolutionSource }
): Promise<TransitionOutcome> {
    // The server reads its languages once, in on_initialize, and has no
    // didChangeConfiguration handler — so its identity is everything it read,
    // not the target alone. Keying on fewer slots than the server consumes is
    // how a sourceLanguage change fired the listener, matched the cached
    // value, and silently did nothing (CORE-1754).
    const identity = serverIdentityOf(languages);

    // The bookkeeping this used to do inline — serialising, deciding what
    // counts as a change, remembering what is running, suppressing duplicate
    // announcements — belongs to the state machine now. What is left here is
    // only the part that needs the editor: how to actually start a server, and
    // how to tell the user when that failed (CORE-1847).
    return server.transition(identity, options, {
        start: () => {
            Logger.info(`Applying language ${identity}; restarting server`);
            return restartServer(context, languages, options.resource);
        },
        onRecord: (record, durationMs) => {
            LegesherTelemetry.trackLanguageTransition({ ...record, durationMs });
        },
        onFailure: (failed, error) => {
            Logger.error('Failed to apply language change', error);
            announceTransitionFailure(context, failed, error);
        },
        now: () => Date.now(),
    });
}

/**
 * Tell the user a language change did not take.
 *
 * Every failure mode in this subsystem used to be silent — the log recorded it
 * and every visible surface went on claiming success. Whether this should fire
 * at all is the state machine's call; by the time it is reached the failure is
 * already known to be one worth showing.
 */
function announceTransitionFailure(
    context: vscode.ExtensionContext,
    identity: string,
    error: unknown
): void {
    const message = error instanceof Error ? error.message : String(error);

    // Deliberately not awaited: this runs inside the transition queue, and an
    // unanswered notification would block every later language change.
    void vscode.window.showErrorMessage(
        `Legesher could not switch to ${identityFileLanguage(identity)}: ${message}. ` +
        'The editor is not translating in that language.',
        'View Output',
        'Retry'
    ).then(action => {
        if (action === 'View Output') {
            outputChannel.show();
        } else if (action === 'Retry') {
            // Re-enters through the queue rather than nesting inside it.
            void ensureRestart(context);
        }
    });
}

/**
 * Re-resolve the language for the active editor and apply it everywhere.
 *
 * Non-Python editors are ignored rather than treated as "no document". Focusing
 * a settings file or a README would otherwise resolve back to the configured
 * language and restart the server, then restart it again on the way back — a
 * restart per editor switch, for files Legesher does not act on anyway.
 */
async function syncActiveLanguage(
    context: vscode.ExtensionContext,
    options: { requirePythonEditor?: boolean; trigger?: LanguageTrigger } = {}
): Promise<void> {
    const document = vscode.window.activeTextEditor?.document;
    const pythonDocument = document?.languageId === 'python' ? document : undefined;

    // Editor-driven syncs skip non-Python editors (see above). Explicit actions —
    // the language picker, a settings edit — must still apply with a README or
    // nothing focused, or they silently do nothing while claiming success.
    if (options.requirePythonEditor !== false && !pythonDocument) {
        return;
    }

    // One resolution, one configuration read, used by every surface below.
    const resolved = resolveLanguage(context, pythonDocument);

    // Painted twice, deliberately. The first paint is optimistic so the bar
    // responds immediately; the second paints what actually happened. Painting
    // only the first is how the bar came to advertise a language the server had
    // failed to load — intent rendered as fact (CORE-1776).
    updateLanguageStatusBar(resolved);
    await ensureServerLanguage(context, languagesOf(resolved), {
        resource: pythonDocument?.uri,
        // An action in flight outranks the caller's own label: the listener that
        // a picker write woke up would otherwise report itself as a settings
        // edit, hiding the picker behind its own side effect.
        trigger: pendingTrigger ?? options.trigger ?? 'editor',
        source: resolved.source,
    });
    updateLanguageStatusBar(resolved);
}

/**
 * What `activate()` hands back to anything holding this extension.
 *
 * A narrow, read-only view of the language actually in effect. It exists
 * because "which language is really running" is precisely what the surfaces in
 * this file kept disagreeing about, and an answer that can be asserted from
 * outside the extension host is the only way to test that they agree
 * (CORE-1776).
 */
export interface LegesherApi {
    /**
     * The `source->target` pair the running server was started with, or
     * undefined when no server is running — including after a failed start.
     */
    getServerLanguage(): string | undefined;

    /**
     * How the most recent language change actually ended.
     *
     * The counterpart to the user-facing signals: a failure that is visible in
     * the UI but unassertable from outside is still one nobody can write a test
     * against, which is how this subsystem accumulated three tickets' worth of
     * silent bugs (CORE-1776).
     */
    getLastTransition(): LanguageTransition | undefined;
}

/**
 * A completed language change, whatever became of it.
 *
 * The state machine's own record type, re-exported so consumers of this API do
 * not have to reach past it.
 */
export type LanguageTransition = TransitionRecord;

const extensionApi: LegesherApi = {
    // Both answers come straight from the state machine, which is what makes
    // them consistent with each other by construction. `activeIdentity` is
    // undefined unless something is really serving that pair — the remembered
    // request outlives a missing binary on purpose, and reporting *that* as a
    // running server is precisely the confusion this API exists to detect.
    getServerLanguage: () => server.activeIdentity,
    getLastTransition: () => server.lastTransition,
};

/**
 * Extension activation entry point
 * Called when the extension is activated (when a Python file is opened)
 */
export async function activate(context: vscode.ExtensionContext): Promise<LegesherApi> {
    // Load environment variables from .env file (development only)
    loadEnvVariables(context.extensionPath);

    // Create reusable output channel first.
    //
    // Must be a LogOutputChannel ({ log: true }). vscode-languageclient 10 calls
    // outputChannel.error/.warn/.info, which exist only on LogOutputChannel — a
    // plain OutputChannel makes the client throw "this.outputChannel.error is
    // not a function" the first time it logs, which is during startup. That
    // aborts client.start() and takes down every LSP feature, while masking
    // whatever the client was actually trying to report.
    outputChannel = vscode.window.createOutputChannel('Legesher Language Server', { log: true });
    context.subscriptions.push(outputChannel);

    // Initialize logger
    Logger.init(outputChannel);
    Logger.info('Legesher extension activating...');

    // Initialize keywords module (loads language packs for translations)
    initializeKeywords(context.extensionPath);

    // Let the translation panel resolve languages the same way everything else
    // does, so a detected language does not leave it disagreeing with the status
    // bar and the running server (CORE-1754).
    TranslationPanelManager.setLanguageResolver(
        document => languagesOf(resolveLanguage(context, document))
    );

    // Initialize telemetry (respects user settings)
    LegesherTelemetry.initialize(context);
    Logger.info(`Telemetry: Active = ${LegesherTelemetry.isActive()}`);

    // Initialize feedback system (two-stage: first session + 7 days)
    initializeFeedback(context);

    // Show onboarding for first-time users (welcome + ML consent)
    // Note: This runs async but doesn't block extension activation
    OnboardingManager.showOnboarding(context).catch(error => {
        Logger.error('Onboarding error:', error);
    });

    // Register onboarding reset command (for testing)
    OnboardingManager.registerResetCommand(context);

    // Create status bar item to show connection status
    statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );
    statusBarItem.text = "$(globe) Legesher";
    statusBarItem.tooltip = "Legesher Language Server";
    context.subscriptions.push(statusBarItem);
    statusBarItem.show();

    // Create language selector status bar item
    languageStatusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        99  // Just to the left of the main status bar item
    );
    languageStatusBarItem.command = 'legesher.selectLanguage';
    context.subscriptions.push(languageStatusBarItem);
    const initial = resolveLanguage(context, vscode.window.activeTextEditor?.document);
    updateLanguageStatusBar(initial);
    languageStatusBarItem.show();

    // Check if extension is enabled
    const config = vscode.workspace.getConfiguration('legesher');
    const enabled = config.get<boolean>('enabled', true);

    if (!enabled) {
        statusBarItem.text = "$(circle-slash) Legesher";
        statusBarItem.tooltip = "Legesher: Disabled";
        Logger.info('Legesher extension is disabled via configuration');
        return extensionApi;
    }

    // Register restart command
    context.subscriptions.push(
        vscode.commands.registerCommand('legesher.restartServer', async () => {
            LegesherTelemetry.trackCommand('restartServer');
            await ensureRestart(context);
        })
    );

    // Register language selection command
    context.subscriptions.push(
        vscode.commands.registerCommand('legesher.selectLanguage', async () => {
            LegesherTelemetry.trackCommand('selectLanguage');
            await selectLanguage(context);
        })
    );

    // Register known-languages management command (CORE-1760)
    context.subscriptions.push(
        vscode.commands.registerCommand('legesher.manageMyLanguages', async () => {
            LegesherTelemetry.trackCommand('manageMyLanguages');
            await manageKnownLanguages(context);
        })
    );

    // Register translation panel command
    context.subscriptions.push(
        vscode.commands.registerCommand('legesher.showTranslationPanel', async () => {
            LegesherTelemetry.trackCommand('showTranslationPanel');
            await showTranslationPanel(context);
        })
    );

    // Register "Try Translation Panel" command (for walkthrough/demo)
    context.subscriptions.push(
        vscode.commands.registerCommand('legesher.tryTranslationPanel', async () => {
            LegesherTelemetry.trackCommand('tryTranslationPanel');
            await tryTranslationPanel(context);
        })
    );

    // Register feedback command
    context.subscriptions.push(
        vscode.commands.registerCommand('legesher.giveFeedback', async () => {
            LegesherTelemetry.trackCommand('giveFeedback');
            const feedback = getFeedbackInstance();
            if (feedback) {
                await feedback.promptNow();
            }
        })
    );

    // DEBUG: Reset feedback state (for testing)
    context.subscriptions.push(
        vscode.commands.registerCommand('legesher.resetFeedbackState', async () => {
            const feedback = getFeedbackInstance();
            if (feedback) {
                await feedback.resetState();
                vscode.window.showInformationMessage('Feedback state reset! Restart the extension to see the prompt.');
            }
        })
    );

    // Watch for configuration changes (CORE-1728).
    //
    // Previously disabled because auto-restart raced with selectLanguage's own
    // restart. That race is now handled in ensureServerLanguage(), which is
    // idempotent and serialised, so both paths can safely converge here. With
    // the listener off, editing the setting by hand left the status bar and the
    // running server on the old language with no indication anything was stale.
    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration(async (event) => {
            if (event.affectsConfiguration('legesher.workingLanguage') ||
                // Deprecated alias for workingLanguage: still watched, because
                // an existing configuration edits the old key (CORE-1760).
                event.affectsConfiguration('legesher.targetLanguage') ||
                event.affectsConfiguration('legesher.sourceLanguage') ||
                // The known set changes no server identity, but it decides
                // whether the status bar signals a mismatch, and the repaint
                // rides the same sync.
                event.affectsConfiguration('legesher.knownLanguages') ||
                // Toggling detection changes which language is in effect without
                // either language setting changing, so it has to be watched too.
                event.affectsConfiguration('legesher.languageDetection')) {
                // A settings edit is explicit, so apply it even with no Python
                // editor focused.
                await syncActiveLanguage(context, {
                    requirePythonEditor: false, trigger: 'settings'
                });
            }
        })
    );

    // Re-resolve when the user switches files: a different file may be written
    // in a different language (CORE-1729).
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor(async () => {
            await syncActiveLanguage(context);
        })
    );

    // Forget a closed document's detection result. Version numbers restart at 1
    // when a document is reopened, so a surviving entry could be matched by a
    // revision it was never computed from — a file edited on disk while closed
    // would resolve to the language its *previous* contents implied.
    context.subscriptions.push(
        vscode.workspace.onDidCloseTextDocument(document => {
            detectionCache.forget(document.uri.toString());
        })
    );

    // Start the language server through the same serialised path the listeners
    // use. Calling startServer() directly here would run concurrently with an
    // onDidChangeActiveTextEditor firing during activation: both would assign
    // the module-level `client` and one legesher-lsp process would be orphaned.
    await syncActiveLanguage(context, { requirePythonEditor: false, trigger: 'activation' });

    // Track activation with the language actually in effect, which is not always
    // the configured one — it may have been detected from the open file.
    LegesherTelemetry.trackActivation(
        resolveLanguage(context, vscode.window.activeTextEditor?.document).language
    );

    return extensionApi;
}

/**
 * Start the language server and create LSP client
 *
 * Returns `unavailable` rather than throwing when the binary is missing: that
 * is a supported state, not an error. It is reported as a distinct outcome so
 * callers can tell "no server, as expected" from "no server, and it broke" —
 * conflating the two is how a language nothing could translate was rendered as
 * a successfully applied one (CORE-1776).
 */
async function startServer(
    context: vscode.ExtensionContext,
    languages: ResolvedLanguages,
    resource?: vscode.Uri
): Promise<StartResult> {
    const startTime = Date.now();

    try {
        statusBarItem.text = "$(sync~spin) Legesher";
        statusBarItem.tooltip = "Legesher: Connecting...";

        // Check if server is available
        const config = vscode.workspace.getConfiguration('legesher', resource);
        const serverCommand = config.get<string>('serverCommand', 'legesher-lsp');

        const serverAvailable = await isServerAvailable(serverCommand);

        if (!serverAvailable) {
            // Server not available - this is expected in early development
            const durationMs = Date.now() - startTime;
            LegesherTelemetry.trackServerConnection(false, durationMs);
            LegesherTelemetry.trackError('serverNotInstalled');
            statusBarItem.text = "$(warning) Legesher";
            statusBarItem.tooltip = "Legesher: Language server not installed (extension features limited)";
            Logger.warn(`Language server '${serverCommand}' not found. Extension will run with limited functionality.`);
            Logger.warn('This is expected during early development. The language server package is planned for future implementation.');
            return 'unavailable';
        }

        // Start with the pair the caller resolved: the target may be detected
        // from the document's contents rather than configured (CORE-1729), and
        // the source may come from a folder-scoped setting the client could not
        // see when it read the configuration itself (CORE-1776).
        Logger.info(`Starting language server with languages: ${serverIdentityOf(languages)}`);

        client = createLanguageClient(context, outputChannel, languages, resource);

        // Handle client state changes
        client.onDidChangeState((event) => {
            Logger.debug('Language server state changed', event);
        });

        // Start the client (this also launches the server)
        await client.start();

        // Track successful connection
        const durationMs = Date.now() - startTime;
        LegesherTelemetry.trackServerConnection(true, durationMs);

        // Update status after successful start
        statusBarItem.text = "$(check) Legesher";
        statusBarItem.tooltip = "Legesher: Connected";
        Logger.info('Legesher language server started and connected successfully');
        return 'started';
    } catch (error) {
        // Drop the client that failed to start. It never reached Running, so
        // there is nothing to stop — and vscode-languageclient rejects stop()
        // outright in the startFailed state, which is what the *next* restart
        // would call it in. Left in place, one failed start wedged every
        // subsequent language change behind an un-stoppable client (CORE-1776).
        client = undefined;

        // Track failed connection
        const durationMs = Date.now() - startTime;
        LegesherTelemetry.trackServerConnection(false, durationMs);
        LegesherTelemetry.trackError('serverStartFailed');

        statusBarItem.text = "$(error) Legesher";
        statusBarItem.tooltip = `Legesher: Error - ${error}`;

        const errorMessage = error instanceof Error ? error.message : String(error);
        Logger.error('Failed to start Legesher language server', errorMessage);

        // Rethrow rather than notifying here. Every failed language change now
        // surfaces from one place — ensureServerLanguage — which also sees the
        // failures this function never had a view of, and which can name the
        // language the user is not getting rather than only the exception.
        throw error instanceof Error ? error : new Error(errorMessage);
    }
}

/**
 * Queue a restart at the current resolved language, from outside the sync chain.
 */
function ensureRestart(context: vscode.ExtensionContext): Promise<void> {
    // Forget what is running so the next transition restarts even at the same
    // language, and let the next failure be announced even if it repeats one
    // already shown — an explicit retry always deserves an answer. Both are
    // queued rather than applied now, so a transition already in flight cannot
    // assign its identity afterwards and swallow this (CORE-1776).
    server.invalidate();

    return syncActiveLanguage(context, { requirePythonEditor: false, trigger: 'restart' });
}

/**
 * Restart the language server
 */
async function restartServer(
    context: vscode.ExtensionContext,
    languages: ResolvedLanguages,
    resource?: vscode.Uri
): Promise<StartResult> {
    Logger.info('Restarting Legesher language server...');

    if (client) {
        try {
            await client.stop();
        } catch (error) {
            Logger.error('Error stopping language server', error);
        } finally {
            client = undefined;
        }
    }

    // Nothing to invalidate here: this runs inside a transition, which already
    // cleared the remembered request before calling us — precisely because this
    // next step is the one that can fail (CORE-1776).
    return startServer(context, languages, resource);
}

/**
 * Update the language status bar item to show the language actually in effect.
 *
 * The icon distinguishes where that language came from, so a detected language
 * is never mistaken for a configured one.
 */
function updateLanguageStatusBar(resolved: ResolvedLanguage): void {
    // The language the user works in, as distinct from the one resolved for
    // this file. It comes from the same read that produced `resolved`, so the
    // two can no longer describe different moments (CORE-1776).
    const preferredLanguage = resolved.config.workingLanguage;
    const langCode = resolved.language.toUpperCase();
    const langName = getLanguageName(resolved.language);

    // A language the server never reached is shown as such. Every other branch
    // below describes where the language came from — useful, but all of them
    // assume it is actually in effect, which is the assumption that made these
    // failures invisible.
    //
    // Read from the persistent server status rather than a single transition's
    // outcome: the transition that failed is followed by no-ops that know
    // nothing about it, and painting from those puts the healthy badge back.
    if (server.status === 'failed' || server.status === 'unavailable') {
        const reason = server.status === 'failed'
            ? 'the language server failed to start'
            : 'the language server is not installed';
        languageStatusBarItem.text = `$(error) ${langCode} (inactive)`;
        languageStatusBarItem.tooltip =
            `Legesher: ${langName} is selected but not active — ${reason}. ` +
            'Translation features are unavailable. Click to change language.';
        return;
    }

    // Folder and workspace are shown identically, on purpose. Every `legesher.*`
    // setting is declared `window`-scoped, for which VS Code never applies a
    // per-folder value — and in a single-root workspace, which is the shape we
    // actually target, `.vscode/settings.json` *is* the workspace file and
    // inspect() reports it at both scopes. Advertising a distinct "folder
    // setting" therefore names something that cannot differ from the workspace
    // one, which is a claim the editor does not support (CORE-1847).
    const icons: Record<LanguageSource, string> = {
        folder: '$(root-folder)',
        workspace: '$(root-folder)',
        detected: '$(search)',
        user: '$(globe)',
        default: '$(globe)',
    };
    const origins: Record<LanguageSource, string> = {
        folder: 'project setting',
        workspace: 'project setting',
        detected: 'detected from file contents',
        user: 'your setting',
        default: 'default',
    };

    // When a detected language differs from the one the user works in, show the
    // mismatch rather than only the detected language (CORE-1755). Without this
    // the override is invisible: the bar reads "PT" and nothing indicates that
    // the user's own language was set aside for this file. Surfacing it here
    // keeps the signal ambient — no notification, no interruption.
    //
    // A file in a language the user already knows is not a mismatch worth
    // signalling: opening a Farsi file is only noteworthy to someone who does
    // not read Farsi (CORE-1760). Known files fall through to the plain
    // "detected" rendering below — correct, and quiet.
    const isMismatch = resolved.source === 'detected'
        && isUnfamiliarFileLanguage(
            resolved.language,
            preferredLanguage,
            resolved.config.knownLanguages
        );

    if (isMismatch) {
        const preferredCode = preferredLanguage.toUpperCase();
        const preferredName = getLanguageName(preferredLanguage);
        languageStatusBarItem.text = `${icons.detected} ${langCode} → ${preferredCode}`;
        languageStatusBarItem.tooltip =
            `Legesher: this file is ${langName} (detected from its contents). ` +
            `You work in ${preferredName}. Click to change language.`;
        return;
    }

    languageStatusBarItem.text = `${icons[resolved.source]} ${langCode}`;
    languageStatusBarItem.tooltip =
        `Legesher: ${langName} (${origins[resolved.source]}) - Click to change language`;
}

/**
 * Where a setting must be written for the write to actually take effect.
 *
 * Resolution honours VS Code's precedence — folder > workspace > user > default
 * — so a write has to land at the scope that currently wins, or a narrower one
 * shadows it and the setting appears not to change at all. When nothing is set
 * anywhere, Global is the right home for a user's choice.
 *
 * A reported folder scope maps to Workspace, not WorkspaceFolder. Every
 * `legesher.*` setting is declared `window`-scoped in package.json, and VS Code
 * refuses a WorkspaceFolder write for those outright — "does not support the
 * folder resource scope". The folder value is still reported in a single-root
 * workspace because there `.vscode/settings.json` *is* the workspace file, so
 * Workspace writes the very file the value came from. Making per-folder
 * languages genuinely work in a multi-root workspace means redeclaring these as
 * `resource`-scoped, which is a larger change than this fix.
 */
function targetForScope(scope: SettingScope): vscode.ConfigurationTarget {
    const targets: Record<SettingScope, vscode.ConfigurationTarget> = {
        folder: vscode.ConfigurationTarget.Workspace,
        workspace: vscode.ConfigurationTarget.Workspace,
        user: vscode.ConfigurationTarget.Global,
        default: vscode.ConfigurationTarget.Global,
    };
    return targets[scope];
}

function writeTargetFor(
    config: vscode.WorkspaceConfiguration,
    key: string
): vscode.ConfigurationTarget {
    return targetForScope(getSettingScope(config, key));
}

/**
 * Name the scope a pick was written to, when it is not the user's own settings.
 *
 * Writing into a project's `.vscode/settings.json` is the only way a pick can
 * win against a value already committed there, but it edits a shared file — so
 * say so rather than letting the user discover it in a diff.
 */
function scopeSuffix(...targets: vscode.ConfigurationTarget[]): string {
    return targets.includes(vscode.ConfigurationTarget.Workspace) ? ' for this workspace' : '';
}

/**
 * Show language selection quick-pick and handle selection
 */
/**
 * Attribute everything `apply` causes — including the syncs its writes wake up
 * through the configuration listener — to the picker.
 *
 * Scoped to the writes, deliberately, and not around the quick-pick itself. The
 * widget stays open awaiting a human; holding the attribution across that window
 * would stamp `picker` on every editor switch and settings edit that happened
 * while it sat there, collapsing the one distinction the trigger draws.
 */
async function asPickerAction(apply: () => Promise<void>): Promise<void> {
    pendingTrigger = 'picker';
    try {
        await apply();
    } finally {
        pendingTrigger = undefined;
    }
}

/** A quick-pick row that may carry a language, or be a separator. */
type LanguagePickItem = vscode.QuickPickItem & { languageCode?: string };

/**
 * `Legesher: Manage My Languages` — edit the known-language set (CORE-1760).
 *
 * A multi-select over the same list the language picker offers, pre-checked
 * with the current known set. That set is seeded from the working language
 * when nothing is configured, so the dialog never opens empty — and clearing
 * every box does not empty it either: resolution falls back to the seed, so
 * the working language always counts as known.
 */
async function manageKnownLanguages(context: vscode.ExtensionContext): Promise<void> {
    const resource = vscode.window.activeTextEditor?.document.uri;
    const currentConfig = getLanguageConfig(resource);
    const config = vscode.workspace.getConfiguration('legesher', resource);

    const items = getActiveLanguages().map(lang => ({
        label: lang.nativeName,
        description: lang.name,
        picked: currentConfig.knownLanguages.includes(lang.code),
        languageCode: lang.code,
    }));

    const selected = await vscode.window.showQuickPick(items, {
        canPickMany: true,
        placeHolder: 'Select the languages you read comfortably',
    });

    if (!selected) {
        return; // User cancelled
    }

    const codes = selected.map(item => item.languageCode);
    const target = writeTargetFor(config, 'knownLanguages');

    await asPickerAction(async () => {
        if (!await applySetting(resource, 'knownLanguages', codes, target)) {
            return;
        }

        const workingName = getLanguageName(currentConfig.workingLanguage);
        vscode.window.showInformationMessage(
            codes.length > 0
                ? `Legesher will treat ${codes.map(getLanguageName).join(', ')} as ` +
                  `languages you know${scopeSuffix(target)}.`
                : 'Legesher cleared your known languages; ' +
                  `${workingName}, your working language, still counts as known.`
        );

        // The known set changes no server identity, but the status bar's
        // mismatch signal reads it — repaint through the same path everything
        // else uses.
        await syncActiveLanguage(context, { requirePythonEditor: false, trigger: 'picker' });
    });
}

async function selectLanguage(context: vscode.ExtensionContext): Promise<void> {
    // Scope every read and write to the active document, so a folder-level
    // setting in a multi-root workspace resolves against the right folder — and
    // so the checkmark marks the language actually in effect here, not the
    // global one (CORE-1776).
    const resource = vscode.window.activeTextEditor?.document.uri;
    const currentConfig = getLanguageConfig(resource);
    const languages = getActiveLanguages();
    const config = vscode.workspace.getConfiguration('legesher', resource);
    const detectionEnabled = config.get<string>('languageDetection', 'auto') === 'auto';

    // "Auto" is a first-class choice, not a hidden default: without it, picking
    // a language would be a one-way door out of detection (CORE-1754).
    const AUTO = '__auto__';
    const autoItem: LanguagePickItem = {
        label: detectionEnabled ? '$(check) Auto' : 'Auto',
        description: 'Detect from file contents',
        detail: detectionEnabled ? 'Currently selected' : undefined,
        languageCode: AUTO
    };

    const toItem = (lang: { code: string; name: string; nativeName: string }): LanguagePickItem => {
        const isCurrent = !detectionEnabled && lang.code === currentConfig.workingLanguage;
        return {
            label: isCurrent ? `$(check) ${lang.nativeName}` : lang.nativeName,
            description: lang.name,
            detail: isCurrent ? 'Currently selected' : undefined,
            languageCode: lang.code
        };
    };

    // Known languages first, under a separator: on a 51-language list this is
    // the difference between a picker you scan and one you search (CORE-1760).
    // The known set is seeded from the working language, so the first section
    // is never empty.
    const { known, others } = partitionByKnown(languages, currentConfig.knownLanguages);
    const items: LanguagePickItem[] = [
        autoItem,
        { label: 'Languages you know', kind: vscode.QuickPickItemKind.Separator },
        ...known.map(toItem),
        { label: 'All languages', kind: vscode.QuickPickItemKind.Separator },
        ...others.map(toItem)
    ];

    const selected = await vscode.window.showQuickPick(items, {
        placeHolder: 'Select the language for code translation'
    });

    if (!selected?.languageCode) {
        return; // User cancelled
    }

    // Captured once so the narrowing survives into the async closures below.
    const pickedCode = selected.languageCode;

    if (pickedCode === AUTO) {
        if (detectionEnabled) {
            return; // Already automatic
        }
        const autoTarget = writeTargetFor(config, 'languageDetection');
        await asPickerAction(async () => {
            if (!await applySetting(resource, 'languageDetection', 'auto', autoTarget)) {
                return;
            }

            // Turning detection on does not mean detection will run. A folder-
            // or workspace-scoped targetLanguage outranks it, and resolution
            // returns before the detection branch is ever reached — so promising
            // content detection here would be the same silent no-op this change
            // set out to remove, one setting over (CORE-1776).
            if (currentConfig.scope === 'folder' || currentConfig.scope === 'workspace') {
                void vscode.window.showWarningMessage(
                    'Legesher detection is on, but this project pins ' +
                    `${getLanguageName(currentConfig.workingLanguage)} in its ` +
                    `${currentConfig.scope} settings, which takes precedence. ` +
                    'Detection will not run until that setting is removed.',
                    'Open Settings'
                ).then(action => {
                    if (action === 'Open Settings') {
                        // Broad on purpose: the pin can live in either
                        // workingLanguage or its deprecated targetLanguage
                        // alias, and a query naming one would hide the other.
                        void vscode.commands.executeCommand(
                            'workbench.action.openSettings', 'legesher'
                        );
                    }
                });
            } else {
                vscode.window.showInformationMessage(
                    'Legesher will detect each file\'s language from its contents' +
                    `${scopeSuffix(autoTarget)}.`
                );
            }

            await syncActiveLanguage(context, { requirePythonEditor: false, trigger: 'picker' });
        });
        return;
    }

    // Nothing to do only if this language is already pinned; if detection is on,
    // an explicit pick still has to turn it off even when the codes match.
    if (!detectionEnabled && pickedCode === currentConfig.workingLanguage) {
        return;
    }

    // Track language change in telemetry
    LegesherTelemetry.trackLanguageChange(currentConfig.workingLanguage, pickedCode);

    // An explicit pick pins the language: write it and turn detection off, so it
    // survives switching to a file that would detect as something else.
    //
    // Each write goes to the scope that currently supplies that setting, which
    // is not always Global and is not always the same scope for both. Writing
    // Global unconditionally was silently lost whenever a workspace or folder
    // value outranked it — the pick did nothing while the notification below
    // claimed it had worked (CORE-1776).
    //
    // The write lands on `workingLanguage`, at the scope the *effective* value
    // came from — which for a configuration that predates the rename is the
    // scope of the deprecated `targetLanguage` alias. Writing the new key at
    // that same scope is what lets it win there: an alias pinned in the
    // project's settings would otherwise outrank a pick written to Global,
    // and the pick would silently change nothing (CORE-1760).
    const languageTarget = targetForScope(currentConfig.scope);
    const detectionTarget = writeTargetFor(config, 'languageDetection');

    await asPickerAction(async () => {
        if (!await applySetting(resource, 'workingLanguage', pickedCode, languageTarget)) {
            return;
        }

        // Retire the alias at the scope just written, so the settings file does
        // not keep a `targetLanguage` that resolution now ignores. Leaving it
        // there turns a hand-edit of the name the user recognises into a silent
        // no-op — the new key beside it wins and nothing says so (CORE-1760).
        // Best-effort: the pick has already taken effect, so a failure to tidy
        // up is not a failure of the pick, and must not be reported as one.
        await retireDeprecatedAlias(resource, languageTarget);

        // Whether detection was actually turned off decides what can honestly be
        // claimed below. If that write did not land, detection is still on and
        // will override this pick on the next file — announcing it as off would
        // leave the user to discover that themselves (CORE-1776).
        const detectionOff =
            await applySetting(resource, 'languageDetection', 'off', detectionTarget);

        const langName = getLanguageName(pickedCode);
        // The scope suffix covers both writes: the two settings can live at
        // different scopes, and a pick that edits the project's settings file
        // through *either* of them should say so.
        vscode.window.showInformationMessage(
            `Legesher language set to ${langName}${scopeSuffix(languageTarget, detectionTarget)}. ` +
            (detectionOff
                ? 'Automatic detection is off — choose Auto to re-enable it.'
                : 'Automatic detection could not be turned off, so it may override this on other files.')
        );

        // Apply through the same idempotent path the configuration listener
        // uses. The listener will also fire for this update; whichever arrives
        // first does the restart and the other collapses to a no-op, so there is
        // no race and no double restart (CORE-1728). An explicit pick applies
        // even with no Python editor focused.
        await syncActiveLanguage(context, { requirePythonEditor: false, trigger: 'picker' });
    });
}

/**
 * Clear `legesher.targetLanguage` at `target`, if it is set there.
 *
 * Only at that one scope: the alias may also be set somewhere wider, where it
 * is still the value in effect for other projects, and a pick in this one is
 * not permission to edit those.
 */
async function retireDeprecatedAlias(
    resource: vscode.Uri | undefined,
    target: vscode.ConfigurationTarget
): Promise<void> {
    const inspected = vscode.workspace
        .getConfiguration('legesher', resource)
        .inspect<string>('targetLanguage');
    const setHere = target === vscode.ConfigurationTarget.Workspace
        ? inspected?.workspaceValue
        : inspected?.globalValue;

    if (setHere === undefined) {
        return;
    }

    try {
        await vscode.workspace
            .getConfiguration('legesher', resource)
            .update('targetLanguage', undefined, target);
        Logger.info('Retired the deprecated legesher.targetLanguage in favour of workingLanguage');
    } catch (error) {
        // Logged, not surfaced: the language did change, and a notification
        // about a cleanup step would report a failure the user did not have.
        Logger.warn('Could not clear the deprecated legesher.targetLanguage', error);
    }
}

/**
 * Write a setting and confirm it actually took effect.
 *
 * Returns false, and tells the user why, when it did not.
 *
 * The read-back is the point. `config.update()` resolving means the value was
 * stored at the scope asked for — not that resolution now returns it, which is
 * a different claim and the one the user cares about. Trusting the former is
 * exactly how a pick could be written to user settings, shadowed by a workspace
 * value, and still announced as a success (CORE-1776). A rejected write is
 * reported too: VS Code refuses some scope/setting combinations outright, and
 * that rejection used to travel as an unhandled promise while the notification
 * claimed the language had changed.
 */
async function applySetting(
    resource: vscode.Uri | undefined,
    key: 'workingLanguage' | 'languageDetection' | 'knownLanguages',
    value: string | string[],
    target: vscode.ConfigurationTarget
): Promise<boolean> {
    const scope = getSettingScope(vscode.workspace.getConfiguration('legesher', resource), key);

    try {
        await vscode.workspace.getConfiguration('legesher', resource).update(key, value, target);
    } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        Logger.error(`Failed to write legesher.${key}`, message);
        LegesherTelemetry.trackError('languageWriteFailed', `${key}:${message}`);
        LegesherTelemetry.trackLanguageSettingWrite(key, scope, 'failed');
        void vscode.window.showErrorMessage(`Legesher could not save ${key}: ${message}`);
        return false;
    }

    // Re-read through the same resolution the rest of the extension uses.
    const effective = vscode.workspace
        .getConfiguration('legesher', resource)
        .get<string | string[]>(key);
    if (!settingValuesEqual(effective, value)) {
        Logger.error(
            `legesher.${key} was written but resolves to '${effective}', not '${value}' — ` +
            'a narrower configuration scope is overriding it'
        );
        LegesherTelemetry.trackError('languageWriteShadowed', `${key}:${scope}`);
        LegesherTelemetry.trackLanguageSettingWrite(key, scope, 'shadowed');
        void vscode.window.showWarningMessage(
            `Legesher saved ${key}, but a more specific setting is overriding it — ` +
            `'${effective}' is still in effect. Check your workspace or folder settings.`,
            'Open Settings'
        ).then(action => {
            if (action === 'Open Settings') {
                void vscode.commands.executeCommand(
                    'workbench.action.openSettings', `legesher.${key}`
                );
            }
        });
        return false;
    }

    LegesherTelemetry.trackLanguageSettingWrite(key, scope, 'applied');
    return true;
}

/**
 * Whether a read-back matches what was written — element-wise for the one
 * array-valued setting, `===` for the rest.
 */
function settingValuesEqual(
    a: string | string[] | undefined,
    b: string | string[]
): boolean {
    if (Array.isArray(a) && Array.isArray(b)) {
        return a.length === b.length && a.every((item, i) => item === b[i]);
    }
    return a === b;
}

/**
 * Show the translation panel for the active Python file
 */
async function showTranslationPanel(context: vscode.ExtensionContext): Promise<void> {
    const editor = vscode.window.activeTextEditor;

    if (!editor) {
        vscode.window.showErrorMessage('No file open. Please open a Python file to view translations.');
        return;
    }

    if (editor.document.languageId !== 'python') {
        vscode.window.showErrorMessage('Translation panel only supports Python files. Please open a Python file.');
        return;
    }

    // Get or create the panel manager and show the panel
    const panelManager = TranslationPanelManager.getInstance(context);
    await panelManager.show(editor.document);
}

/**
 * Try the translation panel with a sample Python file
 * Used in the walkthrough to give users an instant demo
 */
async function tryTranslationPanel(context: vscode.ExtensionContext): Promise<void> {
    const config = getLanguageConfig();
    const langName = getLanguageName(config.workingLanguage);

    // Sample Python code that showcases various keywords and builtins
    const sampleCode = `# Legesher Demo - See your code in ${langName}!
# Hover over keywords to see translations

def greet(name):
    """Say hello to someone."""
    if name:
        print(f"Hello, {name}!")
        return True
    else:
        print("Hello, World!")
        return False

class Calculator:
    """A simple calculator class."""

    def __init__(self):
        self.result = 0

    def add(self, x, y):
        """Add two numbers."""
        self.result = x + y
        return self.result

# Try it out!
for i in range(3):
    greet(f"User {i}")

# Error handling example
try:
    value = int("not a number")
except ValueError as e:
    print(f"Caught an error: {e}")
finally:
    print("Done!")
`;

    // Create an untitled Python document with sample code
    const doc = await vscode.workspace.openTextDocument({
        content: sampleCode,
        language: 'python'
    });

    // Show the document in the editor
    const editor = await vscode.window.showTextDocument(doc, {
        preview: false,
        viewColumn: vscode.ViewColumn.One
    });

    // Allow VS Code to render editor before opening panel
    const EDITOR_READY_DELAY_MS = 200;
    await new Promise(resolve => setTimeout(resolve, EDITOR_READY_DELAY_MS));

    // Open the translation panel
    const panelManager = TranslationPanelManager.getInstance(context);
    await panelManager.show(editor.document);
}

/**
 * Extension deactivation
 * Called when the extension is deactivated
 */
export async function deactivate(): Promise<void> {
    Logger.info('Legesher extension deactivating...');

    if (client) {
        // Guarded like the stop in restartServer: a client that never reached
        // Running rejects stop(), and letting that propagate would skip every
        // disposal below and leave the state claiming a server is running.
        try {
            await client.stop();
            Logger.info('Legesher language server stopped');
        } catch (error) {
            Logger.error('Error stopping language server', error);
        } finally {
            client = undefined;
        }
    }

    // No server runs after this, so nothing may still claim one does.
    server.markStopped();
    detectionCache.clear();

    if (statusBarItem) {
        statusBarItem.dispose();
    }

    if (languageStatusBarItem) {
        languageStatusBarItem.dispose();
    }

    if (outputChannel) {
        outputChannel.dispose();
    }

    // Dispose translation panel if open
    TranslationPanelManager.disposeInstance();
}
