import * as vscode from 'vscode';
import { LanguageClient } from 'vscode-languageclient/node';
import { createLanguageClient } from './client';
import { isServerAvailable } from './utils';

let client: LanguageClient | undefined;
let statusBarItem: vscode.StatusBarItem;

/**
 * Extension activation entry point
 * Called when the extension is activated (when a Python file is opened)
 */
export async function activate(context: vscode.ExtensionContext): Promise<void> {
    console.log('Legesher extension activating...');

    // Create status bar item to show connection status
    statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );
    statusBarItem.text = "$(globe) Legesher";
    statusBarItem.tooltip = "Legesher Language Server";
    context.subscriptions.push(statusBarItem);
    statusBarItem.show();

    // Check if extension is enabled
    const config = vscode.workspace.getConfiguration('legesher');
    const enabled = config.get<boolean>('enabled', true);

    if (!enabled) {
        statusBarItem.text = "$(circle-slash) Legesher";
        statusBarItem.tooltip = "Legesher: Disabled";
        console.log('Legesher extension is disabled via configuration');
        return;
    }

    // Register restart command
    context.subscriptions.push(
        vscode.commands.registerCommand('legesher.restartServer', async () => {
            await restartServer(context);
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
            console.warn(`Language server '${serverCommand}' not found. Extension will run with limited functionality.`);
            console.warn('This is expected during early development. The language server package is planned for future implementation.');
            return;
        }

        client = createLanguageClient(context);

        // Handle client state changes
        client.onDidChangeState((event) => {
            console.log('Language server state changed:', event);
        });

        // Start the client (this also launches the server)
        await client.start();

        // Update status after successful start
        statusBarItem.text = "$(check) Legesher";
        statusBarItem.tooltip = "Legesher: Connected";
        console.log('Legesher language server started and connected successfully');
    } catch (error) {
        statusBarItem.text = "$(error) Legesher";
        statusBarItem.tooltip = `Legesher: Error - ${error}`;

        const errorMessage = error instanceof Error ? error.message : String(error);
        console.error('Failed to start Legesher language server:', errorMessage);

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
    console.log('Restarting Legesher language server...');

    if (client) {
        await client.stop();
        client = undefined;
    }

    await startServer(context);
}

/**
 * Extension deactivation
 * Called when the extension is deactivated
 */
export async function deactivate(): Promise<void> {
    console.log('Legesher extension deactivating...');

    if (client) {
        await client.stop();
        console.log('Legesher language server stopped');
    }

    if (statusBarItem) {
        statusBarItem.dispose();
    }
}
