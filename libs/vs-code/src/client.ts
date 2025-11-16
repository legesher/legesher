import * as vscode from 'vscode';
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
    Executable,
} from 'vscode-languageclient/node';
import { getLanguageConfig } from './config';
import { Logger } from './logger';

/**
 * Create and configure the Language Server Protocol client
 *
 * This client connects to the legesher-language-server and enables
 * LSP features like hover, completion, diagnostics, etc.
 */
export function createLanguageClient(
    context: vscode.ExtensionContext,
    outputChannel: vscode.OutputChannel
): LanguageClient {
    // Get configuration
    const config = vscode.workspace.getConfiguration('legesher');
    const serverCommand = config.get<string>('serverCommand', 'legesher-lsp');
    const traceLevel = config.get<string>('trace.server', 'off');
    const languageConfig = getLanguageConfig();

    Logger.info(`Creating language client with command: ${serverCommand}`);
    Logger.debug('Language configuration', languageConfig);

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

        // Reuse existing output channel instead of creating new ones
        outputChannel: outputChannel,

        // Trace configuration - don't create trace channel (causes duplicates)
        // Users can enable trace in the main output channel if needed
        traceOutputChannel: undefined,

        // Middleware to customize LSP behavior (can be extended later)
        middleware: {
            // Semantic tokens middleware (CORE-450)
            // Automatically enabled when server advertises semantic tokens capability
            provideDocumentSemanticTokens: async (document, token, next) => {
                Logger.debug(`Semantic tokens requested for: ${document.uri.toString()}`);
                const result = await next(document, token);
                if (result) {
                    Logger.debug(`Semantic tokens received: ${result.data.length} integers`);
                }
                return result;
            },
        },

        // Initialization options passed to the server
        initializationOptions: {
            // These options are sent to the server during initialization
            // Include language configuration for translation
            ...languageConfig,
            trace: traceLevel,
        },

        // Error handler
        errorHandler: {
            error: (error, message, count) => {
                Logger.error('Language server error', { error, message, count });
                // Return ErrorAction.Continue to keep trying
                return { action: 1 }; // ErrorAction.Continue = 1
            },
            closed: () => {
                Logger.warn('Language server connection closed');
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

    Logger.info('Language client created successfully');

    return client;
}
