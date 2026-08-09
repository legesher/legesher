import * as vscode from 'vscode';
import { LanguageClient } from 'vscode-languageclient/node';
import { createLanguageClient } from './client';
import { isServerAvailable } from './utils';
import { getLanguageConfig, getActiveLanguages, getLanguageName } from './config';
import { TranslationPanelManager } from './webview/panel';
import { Logger } from './logger';
import { LegesherTelemetry } from './telemetry';
import { initializeFeedback, getFeedbackInstance } from './feedback';
import { initializeKeywords } from './keywords';
import { loadEnvVariables } from './env';
import { OnboardingManager } from './onboarding';
import { loadAllTranslations } from './languagePackLoader';
import { buildVocabularies, detectLanguage, PackVocabulary } from './languageDetection';

let client: LanguageClient | undefined;
let statusBarItem: vscode.StatusBarItem;
let languageStatusBarItem: vscode.StatusBarItem;
let outputChannel: vscode.OutputChannel;

/** Language the running server was started with, so restarts stay idempotent. */
let serverLanguage: string | undefined;
/** Serialises language changes so overlapping triggers can't race (CORE-1728). */
let languageSync: Promise<void> = Promise.resolve();
/** Detection vocabularies, built once from the bundled packs. */
let vocabularies: PackVocabulary[] | undefined;

/** Where the language in effect came from, for the status bar. */
type LanguageSource = 'folder' | 'workspace' | 'detected' | 'user' | 'default';

interface ResolvedLanguage {
    language: string;
    source: LanguageSource;
}

function getVocabularies(context: vscode.ExtensionContext): PackVocabulary[] {
    if (!vocabularies) {
        vocabularies = buildVocabularies(loadAllTranslations(context.extensionPath));
        Logger.info(`Language detection ready: ${vocabularies.length} vocabularies`);
    }
    return vocabularies;
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
        return { language: config.targetLanguage, source: config.scope };
    }

    if (document && document.languageId === 'python') {
        const detected = detectLanguage(document.getText(), getVocabularies(context));
        if (detected) {
            Logger.debug(
                `Detected ${detected.language} (score ${detected.score}` +
                `${detected.runnerUp ? `, runner-up ${detected.runnerUp.language} ${detected.runnerUp.score}` : ''})`
            );
            return { language: detected.language, source: 'detected' };
        }
    }

    return { language: config.targetLanguage, source: config.scope === 'user' ? 'user' : 'default' };
}

/**
 * Bring the running server in line with `language`.
 *
 * Idempotent and serialised: if the server already speaks `language` this is a
 * no-op, and concurrent callers queue rather than restarting on top of each
 * other. That is what makes it safe to re-enable the configuration listener —
 * whichever trigger arrives first performs the restart and the rest collapse
 * into no-ops, instead of racing as the old auto-restart did (CORE-1728).
 */
function ensureServerLanguage(
    context: vscode.ExtensionContext,
    language: string
): Promise<void> {
    languageSync = languageSync
        .then(async () => {
            if (serverLanguage === language) {
                return;
            }
            Logger.info(`Language changed: ${serverLanguage ?? '(none)'} -> ${language}; restarting server`);
            // Record the language only once the restart has actually succeeded.
            // Assigning first means a failed restart leaves the state claiming
            // success, and every later attempt at the same language collapses
            // into a no-op that never retries.
            await restartServer(context, language);
            serverLanguage = language;
        })
        .catch(error => {
            Logger.error('Failed to apply language change', error);
        });
    return languageSync;
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
    options: { requirePythonEditor?: boolean } = {}
): Promise<void> {
    const document = vscode.window.activeTextEditor?.document;
    const pythonDocument = document?.languageId === 'python' ? document : undefined;

    // Editor-driven syncs skip non-Python editors (see above). Explicit actions —
    // the language picker, a settings edit — must still apply with a README or
    // nothing focused, or they silently do nothing while claiming success.
    if (options.requirePythonEditor !== false && !pythonDocument) {
        return;
    }

    const resolved = resolveLanguage(context, pythonDocument);
    updateLanguageStatusBar(resolved);
    await ensureServerLanguage(context, resolved.language);
}

/**
 * Extension activation entry point
 * Called when the extension is activated (when a Python file is opened)
 */
export async function activate(context: vscode.ExtensionContext): Promise<void> {
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
    updateLanguageStatusBar(resolveLanguage(context, vscode.window.activeTextEditor?.document));
    languageStatusBarItem.show();

    // Check if extension is enabled
    const config = vscode.workspace.getConfiguration('legesher');
    const enabled = config.get<boolean>('enabled', true);

    if (!enabled) {
        statusBarItem.text = "$(circle-slash) Legesher";
        statusBarItem.tooltip = "Legesher: Disabled";
        Logger.info('Legesher extension is disabled via configuration');
        return;
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
            if (event.affectsConfiguration('legesher.targetLanguage') ||
                event.affectsConfiguration('legesher.sourceLanguage')) {
                // A settings edit is explicit, so apply it even with no Python
                // editor focused.
                await syncActiveLanguage(context, { requirePythonEditor: false });
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

    // Start the language server through the same serialised path the listeners
    // use. Calling startServer() directly here would run concurrently with an
    // onDidChangeActiveTextEditor firing during activation: both would assign
    // the module-level `client` and one legesher-lsp process would be orphaned.
    await syncActiveLanguage(context, { requirePythonEditor: false });

    // Track activation with current language
    const languageConfig = getLanguageConfig();
    LegesherTelemetry.trackActivation(languageConfig.targetLanguage);
}

/**
 * Start the language server and create LSP client
 */
async function startServer(
    context: vscode.ExtensionContext,
    language?: string
): Promise<void> {
    const startTime = Date.now();

    try {
        statusBarItem.text = "$(sync~spin) Legesher";
        statusBarItem.tooltip = "Legesher: Connecting...";

        // Check if server is available
        const config = vscode.workspace.getConfiguration('legesher');
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
            return;
        }

        // Start with the language the caller resolved, which may be detected
        // from the document's contents rather than configured (CORE-1729).
        // Passed in rather than read from module state so a failed start never
        // leaves `serverLanguage` claiming a language the server is not running.
        const targetLanguage = language
            ?? resolveLanguage(context, vscode.window.activeTextEditor?.document).language;
        Logger.info(`Starting language server with target language: ${targetLanguage}`);

        client = createLanguageClient(context, outputChannel, targetLanguage);

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
    } catch (error) {
        // Track failed connection
        const durationMs = Date.now() - startTime;
        LegesherTelemetry.trackServerConnection(false, durationMs);
        LegesherTelemetry.trackError('serverStartFailed');

        statusBarItem.text = "$(error) Legesher";
        statusBarItem.tooltip = `Legesher: Error - ${error}`;

        const errorMessage = error instanceof Error ? error.message : String(error);
        Logger.error('Failed to start Legesher language server', errorMessage);

        // Deliberately not awaited. startServer runs inside the languageSync
        // chain, and an unanswered notification would block every later language
        // change indefinitely; awaiting "Retry" would also re-enter restartServer
        // from inside the chain entry that is still executing.
        void vscode.window.showErrorMessage(
            `Failed to start Legesher language server: ${errorMessage}`,
            'View Output',
            'Retry'
        ).then(action => {
            if (action === 'View Output') {
                client?.outputChannel.show();
            } else if (action === 'Retry') {
                // Re-enters through the queue rather than nesting inside it.
                void ensureRestart(context);
            }
        });

        throw error instanceof Error ? error : new Error(errorMessage);
    }
}

/**
 * Queue a restart at the current resolved language, from outside the sync chain.
 */
function ensureRestart(context: vscode.ExtensionContext): Promise<void> {
    serverLanguage = undefined;
    return syncActiveLanguage(context, { requirePythonEditor: false });
}

/**
 * Restart the language server
 */
async function restartServer(
    context: vscode.ExtensionContext,
    language?: string
): Promise<void> {
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

    await startServer(context, language);
}

/**
 * Update the language status bar item to show the language actually in effect.
 *
 * The icon distinguishes where that language came from, so a detected language
 * is never mistaken for a configured one.
 */
function updateLanguageStatusBar(resolved: ResolvedLanguage): void {
    const langCode = resolved.language.toUpperCase();
    const langName = getLanguageName(resolved.language);

    const icons: Record<LanguageSource, string> = {
        folder: '$(folder)',
        workspace: '$(root-folder)',
        detected: '$(search)',
        user: '$(globe)',
        default: '$(globe)',
    };
    const origins: Record<LanguageSource, string> = {
        folder: 'folder setting',
        workspace: 'workspace setting',
        detected: 'detected from file contents',
        user: 'user setting',
        default: 'default',
    };

    languageStatusBarItem.text = `${icons[resolved.source]} ${langCode}`;
    languageStatusBarItem.tooltip =
        `Legesher: ${langName} (${origins[resolved.source]}) - Click to change language`;
}

/**
 * Show language selection quick-pick and handle selection
 */
async function selectLanguage(context: vscode.ExtensionContext): Promise<void> {
    const currentConfig = getLanguageConfig();
    const languages = getActiveLanguages();

    // Create quick-pick items with native names
    const items = languages.map(lang => ({
        label: lang.code === currentConfig.targetLanguage ? `$(check) ${lang.nativeName}` : lang.nativeName,
        description: lang.name,
        detail: lang.code === currentConfig.targetLanguage ? 'Currently selected' : undefined,
        languageCode: lang.code
    }));

    const selected = await vscode.window.showQuickPick(items, {
        placeHolder: 'Select target language for code translation'
    });

    if (!selected) {
        return; // User cancelled
    }

    // Don't restart if same language selected
    if (selected.languageCode === currentConfig.targetLanguage) {
        return;
    }

    // Track language change in telemetry
    LegesherTelemetry.trackLanguageChange(currentConfig.targetLanguage, selected.languageCode);

    // Update configuration (user-level / global)
    const config = vscode.workspace.getConfiguration('legesher');
    await config.update('targetLanguage', selected.languageCode, vscode.ConfigurationTarget.Global);

    // Show notification
    const langName = getLanguageName(selected.languageCode);
    vscode.window.showInformationMessage(
        `Legesher language changed to ${langName}. Reloading language server...`
    );

    // Apply through the same idempotent path the configuration listener uses.
    // The listener will also fire for this update; whichever arrives first does
    // the restart and the other collapses to a no-op, so there is no race and
    // no double restart (CORE-1728). An explicit pick applies even with no
    // Python editor focused.
    await syncActiveLanguage(context, { requirePythonEditor: false });
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
    const langName = getLanguageName(config.targetLanguage);

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
        await client.stop();
        Logger.info('Legesher language server stopped');
    }

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
