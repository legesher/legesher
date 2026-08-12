import * as vscode from 'vscode';
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
    Executable,
} from 'vscode-languageclient/node';
import { type ResolvedLanguages } from './config';
import { Logger } from './logger';
import { LegesherTelemetry } from './telemetry';

/**
 * Create and configure the Language Server Protocol client
 *
 * This client connects to the legesher-language-server and enables
 * LSP features like hover, completion, diagnostics, etc.
 *
 * `languages` is resolved by the caller and passed in whole. It used to
 * re-read the configuration here, without the document's URI and with only the
 * target overridden — so a folder-scoped `sourceLanguage` never reached the
 * server and the identity the extension recorded described a server that was
 * never started (CORE-1776). There is deliberately no fallback: the caller
 * always knows the pair, and a second read is exactly how the two drifted.
 */
export function createLanguageClient(
    context: vscode.ExtensionContext,
    outputChannel: vscode.OutputChannel,
    languages: ResolvedLanguages,
    resource?: vscode.Uri
): LanguageClient {
    // Server settings resolve against the document too, so a project can pin
    // its own server binary or trace level the same way it pins a language.
    const config = vscode.workspace.getConfiguration('legesher', resource);
    const serverCommand = config.get<string>('serverCommand', 'legesher-lsp');
    const traceLevel = config.get<string>('trace.server', 'off');

    Logger.info(`Creating language client with command: ${serverCommand}`);
    Logger.debug('Language configuration', languages);

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
            provideDocumentSemanticTokens: async (document, token, next) => {
                Logger.debug(`Semantic tokens requested for: ${document.uri.toString()}`);
                const result = await next(document, token);
                if (result) {
                    Logger.debug(`Semantic tokens received: ${result.data.length} integers`);
                    LegesherTelemetry.trackFeatureUsed('semanticTokens');
                }
                return result;
            },
            // Completion middleware - track when completions are provided
            provideCompletionItem: async (document, position, context, token, next) => {
                const result = await next(document, position, context, token);
                if (result) {
                    const count = Array.isArray(result) ? result.length : result.items.length;
                    LegesherTelemetry.trackCompletionProvided(count);
                    LegesherTelemetry.trackFeatureUsed('completion');
                }
                return result;
            },
            // Hover middleware - track when hover info is provided
            provideHover: async (document, position, token, next) => {
                const result = await next(document, position, token);
                if (result) {
                    LegesherTelemetry.trackFeatureUsed('hover');
                    // Extract hovered word for keyword tracking
                    const wordRange = document.getWordRangeAtPosition(position);
                    if (wordRange) {
                        const word = document.getText(wordRange);
                        LegesherTelemetry.trackHoverProvided(word);
                    }
                }
                return result;
            },
        },

        // Initialization options passed to the server
        initializationOptions: {
            // These options are sent to the server during initialization
            // Include language configuration for translation
            ...languages,
            trace: traceLevel,
        },

        // Error handler
        errorHandler: {
            error: (error, message, count) => {
                Logger.error('Language server error', { error, message, count });
                LegesherTelemetry.trackError('serverError', String(message));
                // Return ErrorAction.Continue to keep trying
                return { action: 1 }; // ErrorAction.Continue = 1
            },
            closed: () => {
                Logger.warn('Language server connection closed');
                LegesherTelemetry.trackError('serverConnectionClosed');
                // Don't auto-restart - let manual restart handle it
                // This prevents conflicts when changing languages
                return { action: 2 }; // CloseAction.DoNotRestart = 2
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
