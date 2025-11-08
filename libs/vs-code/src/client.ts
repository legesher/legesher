import * as vscode from 'vscode';
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
    Executable,
} from 'vscode-languageclient/node';
import { isServerAvailable } from './utils';

/**
 * Create and configure the Language Server Protocol client
 *
 * This client connects to the legesher-language-server and enables
 * LSP features like hover, completion, diagnostics, etc.
 */
export function createLanguageClient(
    context: vscode.ExtensionContext
): LanguageClient {
    // Get configuration
    const config = vscode.workspace.getConfiguration('legesher');
    const serverCommand = config.get<string>('serverCommand', 'legesher-lsp');
    const traceLevel = config.get<string>('trace.server', 'off');

    console.log(`Creating language client with command: ${serverCommand}`);

    // Configure server executable
    const serverOptions: ServerOptions = {
        command: serverCommand,
        args: ['--stdio'],
        options: {
            env: {
                ...process.env,
                // Pass any environment variables the server might need
                PYTHONUNBUFFERED: '1', // Ensure Python output is unbuffered
            }
        }
    } as Executable;

    // Configure client options
    const clientOptions: LanguageClientOptions = {
        // Register the server for Python documents
        documentSelector: [
            { scheme: 'file', language: 'python' },
            { scheme: 'untitled', language: 'python' }
        ],

        // Synchronize file events with the server
        synchronize: {
            // Notify the server about file changes to Python files
            fileEvents: vscode.workspace.createFileSystemWatcher('**/*.py')
        },

        // Output channel for server communication logs
        outputChannelName: 'Legesher Language Server',

        // Trace configuration
        traceOutputChannel: traceLevel !== 'off' ? vscode.window.createOutputChannel('Legesher Language Server Trace') : undefined,

        // Middleware to customize LSP behavior (can be extended later)
        middleware: {
            // We can add custom middleware here in future iterations
            // For example, to customize how hover information is displayed
        },

        // Initialization options passed to the server
        initializationOptions: {
            // These options are sent to the server during initialization
            // Can be extended to pass user preferences, language settings, etc.
            trace: traceLevel,
        },

        // Error handler
        errorHandler: {
            error: (error, message, count) => {
                console.error('Language server error:', error, message, count);
                // Return ErrorAction.Continue to keep trying
                return { action: 1 }; // ErrorAction.Continue = 1
            },
            closed: () => {
                console.warn('Language server connection closed');
                // Return CloseAction.Restart to automatically restart
                return { action: 1 }; // CloseAction.Restart = 1
            }
        }
    };

    // Create and return the language client
    const client = new LanguageClient(
        'legesher',                          // Client ID
        'Legesher Language Server',         // Client name (displayed in UI)
        serverOptions,
        clientOptions
    );

    console.log('Language client created successfully');

    return client;
}
