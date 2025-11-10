import * as vscode from 'vscode';
import { LanguageClient } from 'vscode-languageclient/node';
import { createLanguageClient } from './client';
import { isServerAvailable } from './utils';
import { getLanguageConfig, getAvailableLanguages, getLanguageName } from './config';
import { TranslationPanelManager } from './webview/panel';
import { Logger } from './logger';

let client: LanguageClient | undefined;
let statusBarItem: vscode.StatusBarItem;
let languageStatusBarItem: vscode.StatusBarItem;
let outputChannel: vscode.OutputChannel;
let languageChangeTimeout: NodeJS.Timeout | undefined;

/**
 * Extension activation entry point
 * Called when the extension is activated (when a Python file is opened)
 */
export async function activate(context: vscode.ExtensionContext): Promise<void> {
    // Create reusable output channel first
    outputChannel = vscode.window.createOutputChannel('Legesher Language Server');
    context.subscriptions.push(outputChannel);

    // Initialize logger
    Logger.init(outputChannel);
    Logger.info('Legesher extension activating...');

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
            await restartServer(context);
        })
    );

    // Register language selection command
    context.subscriptions.push(
        vscode.commands.registerCommand('legesher.selectLanguage', async () => {
            await selectLanguage(context);
        })
    );

    // Register translation panel command
    context.subscriptions.push(
        vscode.commands.registerCommand('legesher.showTranslationPanel', async () => {
            await showTranslationPanel(context);
        })
    );

    // Watch for configuration changes
    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration(async (event) => {
            if (event.affectsConfiguration('legesher.targetLanguage') ||
                event.affectsConfiguration('legesher.sourceLanguage')) {
                await handleLanguageChange(context);
            }
        })
    );

    // Start the language server (optional - server may not exist yet)
    await startServer(context);
}

/**
 * Start the language server and create LSP client
 */
async function startServer(context: vscode.ExtensionContext): Promise<void> {
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

        // Update status after successful start
        statusBarItem.text = "$(check) Legesher";
        statusBarItem.tooltip = "Legesher: Connected";
        Logger.info('Legesher language server started and connected successfully');
    } catch (error) {
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
        await client.stop();
        client = undefined;
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
 * Handle language configuration changes
 *
 * Uses debouncing to prevent multiple rapid server restarts if configuration
 * changes multiple times in quick succession (e.g., during settings sync).
 */
async function handleLanguageChange(context: vscode.ExtensionContext): Promise<void> {
    Logger.info('Language configuration changed, scheduling server restart...');

    // Update status bar immediately (fast, no server interaction)
    updateLanguageStatusBar();

    // Clear any pending restart
    if (languageChangeTimeout) {
        clearTimeout(languageChangeTimeout);
    }

    // Debounce server restart (expensive operation)
    languageChangeTimeout = setTimeout(async () => {
        Logger.info('Applying language configuration change...');
        await restartServer(context);
        languageChangeTimeout = undefined;
    }, 500); // 500ms debounce
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
