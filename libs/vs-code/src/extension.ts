import * as vscode from 'vscode';
import { LanguageClient } from 'vscode-languageclient/node';
import { createLanguageClient } from './client';
import { isServerAvailable } from './utils';
import { getLanguageConfig, getAvailableLanguages, getLanguageName } from './config';
import { TranslationPanelManager } from './webview/panel';
import { Logger } from './logger';
import { LegesherTelemetry } from './telemetry';
import { initializeFeedback, getFeedbackInstance } from './feedback';
import { initializeKeywords } from './keywords';
import { loadEnvVariables } from './env';
import { OnboardingManager } from './onboarding';

let client: LanguageClient | undefined;
let statusBarItem: vscode.StatusBarItem;
let languageStatusBarItem: vscode.StatusBarItem;
let outputChannel: vscode.OutputChannel;

/**
 * Extension activation entry point
 * Called when the extension is activated (when a Python file is opened)
 */
export async function activate(context: vscode.ExtensionContext): Promise<void> {
    // Load environment variables from .env file (development only)
    loadEnvVariables(context.extensionPath);

    // Create reusable output channel first
    outputChannel = vscode.window.createOutputChannel('Legesher Language Server');
    context.subscriptions.push(outputChannel);

    // Initialize logger
    Logger.init(outputChannel);
    Logger.info('Legesher extension activating...');

    // Initialize keywords module (loads language packs for translations)
    initializeKeywords(context.extensionPath);

    // Initialize telemetry (respects user settings)
    LegesherTelemetry.initialize(context);

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
    updateLanguageStatusBar();
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
            await restartServer(context);
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

    // Watch for configuration changes
    // Note: This is disabled because manual language changes via selectLanguage
    // handle restarts themselves. Auto-restart was causing race conditions.
    // context.subscriptions.push(
    //     vscode.workspace.onDidChangeConfiguration(async (event) => {
    //         if (event.affectsConfiguration('legesher.targetLanguage') ||
    //             event.affectsConfiguration('legesher.sourceLanguage')) {
    //             await handleLanguageChange(context);
    //         }
    //     })
    // );

    // Start the language server (optional - server may not exist yet)
    await startServer(context);

    // Track activation with current language
    const languageConfig = getLanguageConfig();
    LegesherTelemetry.trackActivation(languageConfig.targetLanguage);
}

/**
 * Start the language server and create LSP client
 */
async function startServer(context: vscode.ExtensionContext): Promise<void> {
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
            statusBarItem.text = "$(warning) Legesher";
            statusBarItem.tooltip = "Legesher: Language server not installed (extension features limited)";
            Logger.warn(`Language server '${serverCommand}' not found. Extension will run with limited functionality.`);
            Logger.warn('This is expected during early development. The language server package is planned for future implementation.');
            return;
        }

        // Log current language configuration
        const languageConfig = getLanguageConfig();
        Logger.info('Starting language server with configuration', languageConfig);

        client = createLanguageClient(context, outputChannel);

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

        // Show error message with action buttons
        const action = await vscode.window.showErrorMessage(
            `Failed to start Legesher language server: ${errorMessage}`,
            'View Output',
            'Retry'
        );

        if (action === 'View Output') {
            client?.outputChannel.show();
        } else if (action === 'Retry') {
            await restartServer(context);
        }
    }
}

/**
 * Restart the language server
 */
async function restartServer(context: vscode.ExtensionContext): Promise<void> {
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

    await startServer(context);
}

/**
 * Update the language status bar item to show current language
 */
function updateLanguageStatusBar(): void {
    const config = getLanguageConfig();
    const langCode = config.targetLanguage.toUpperCase();
    const langName = getLanguageName(config.targetLanguage);

    languageStatusBarItem.text = `$(globe) ${langCode}`;
    languageStatusBarItem.tooltip = `Legesher: ${langName} - Click to change language`;
}

/**
 * Show language selection quick-pick and handle selection
 */
async function selectLanguage(context: vscode.ExtensionContext): Promise<void> {
    const currentConfig = getLanguageConfig();
    const languages = getAvailableLanguages();

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

    // Update status bar immediately
    updateLanguageStatusBar();

    // Wait a bit for config to propagate
    await new Promise(resolve => setTimeout(resolve, 100));

    // Restart server with new language
    await restartServer(context);
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
