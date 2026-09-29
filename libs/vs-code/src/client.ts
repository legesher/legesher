import * as vscode from 'vscode';
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
    Executable,
} from 'vscode-languageclient/node';
import { type ResolvedLanguages } from './config';
import { connectionErrorHandler } from './connectionErrorHandler';
import { DOCUMENT_LANGUAGE_NOTIFICATION, DocumentLanguageSync } from './documentLanguage';
import { Logger } from './logger';
import { LegesherTelemetry } from './telemetry';

/**
 * The documents the server is sent. Shared with the per-document language
 * reports, so the server is never told the language of a document it will
 * never see opened or closed. Left to inference: the literal satisfies both
 * VS Code's selector type and the protocol's, which differ.
 */
const DOCUMENT_SELECTOR = [
    { scheme: 'file', language: 'python' },
    { scheme: 'untitled', language: 'python' },
];

/** A language client, and the channel that names each document's language to its server. */
export interface LegesherClient {
    readonly client: LanguageClient;
    /**
     * Tell this client's server which language `document` is written in, if
     * that changed since it was last told (CORE-1976). A no-op for a document
     * the server does not see, and for one whose language it already has.
     * Never rejects: a report that could not be sent is logged and retried by
     * the next one.
     */
    reportDocumentLanguage(document: vscode.TextDocument): Promise<void>;
    /** The language last sent for the document at `uri`, if any. */
    sentLanguageOf(uri: vscode.Uri): string | undefined;
}

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
 *
 * `languages` is what the server is started with. Each document's own
 * language is resolved by `languageOf`, the same resolution the rest of the
 * extension uses, and sent to the server per document (CORE-1976).
 */
export function createLanguageClient(
    context: vscode.ExtensionContext,
    // A LogOutputChannel specifically. vscode-languageclient logs through
    // .error/.warn/.info, which a plain OutputChannel does not have, so passing
    // one makes start() throw while logging and every LSP feature dies
    // (CORE-1733). Stating the requirement in the signature is what makes that
    // a compile error rather than a startup failure.
    outputChannel: vscode.LogOutputChannel,
    languages: ResolvedLanguages,
    resource: vscode.Uri | undefined,
    languageOf: (document: vscode.TextDocument) => string
): LegesherClient {
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

    // These closures reach `client`, which is constructed at the end of this
    // function. None of them runs before then: the middleware fires only after
    // start(), and the reports only through the object returned below.
    const documentLanguages = new DocumentLanguageSync(async params => {
        await client.sendNotification(DOCUMENT_LANGUAGE_NOTIFICATION, params);
    });

    // The URI exactly as the client writes it into didOpen, so the server's
    // language map and its open documents agree on every key.
    const protocolUri = (uri: vscode.Uri): string => client.code2ProtocolConverter.asUri(uri);

    const report = async (document: vscode.TextDocument, force: boolean): Promise<void> => {
        // A closed document's didClose may already be out; naming it after
        // that would leave the server an entry nothing ever clears.
        if (document.isClosed || vscode.languages.match(DOCUMENT_SELECTOR, document) === 0) {
            return;
        }
        try {
            await documentLanguages.report(protocolUri(document.uri), languageOf(document), {
                force,
            });
        } catch (error) {
            // Logged, not surfaced: the next report retries, and meanwhile the
            // server serves the document in the configured language rather
            // than not at all.
            Logger.warn("Could not send a document's language to the language server", error);
        }
    };

    // Configure client options
    const clientOptions: LanguageClientOptions = {
        // Register the server for Python documents
        documentSelector: DOCUMENT_SELECTOR,

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
            // Name each document's language as it opens, on the same
            // connection, so the server normally has it before any request
            // about that document arrives (CORE-1976). Forced, because the
            // server forgot the document when it last closed.
            //
            // Both sends are started here, back to back. Waiting for the first
            // to be written before starting the second let the diagnostic pull
            // the client issues while starting reach the server between them:
            // answered empty for a document not yet open, and never repeated.
            // The order is still not guaranteed: when the client holds a
            // deferred open for another document, the first send flushes it,
            // and this didOpen can overtake the name. The server then answers
            // once in its configured language and, when the name arrives, asks
            // the client to refresh.
            didOpen: async (document, next) => {
                const named = report(document, true);
                const opened = next(document);
                await named;
                return opened;
            },
            didClose: async (document, next) => {
                documentLanguages.forget(protocolUri(document.uri));
                return next(document);
            },
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
            // The full language profile, roles kept separate (CORE-1760):
            // sourceLanguage (canonical), fileLanguage (what the file is
            // written in), workingLanguage (what the user reads in), and the
            // deprecated targetLanguage compat slot mirroring fileLanguage
            // for servers that predate the split. Collapsing file and working
            // into one value here is exactly the defect the vocabulary
            // exists to prevent — the server cannot un-collapse them.
            ...languages,
            trace: traceLevel,
        },

        // A closed connection stays closed: only the extension's state
        // machine starts servers (CORE-2316).
        errorHandler: connectionErrorHandler({
            error: (error, message, count) => {
                Logger.error('Language server error', { error, message, count });
                LegesherTelemetry.trackError('serverError', String(message));
            },
            closed: () => {
                Logger.warn('Language server connection closed');
                LegesherTelemetry.trackError('serverConnectionClosed');
            },
        }),
    };

    // Create and return the language client
    const client = new LanguageClient(
        'legesher',                          // Client ID
        'Legesher Language Server',         // Client name (displayed in UI)
        serverOptions,
        clientOptions
    );

    Logger.info('Language client created successfully');

    return {
        client,
        reportDocumentLanguage: document => report(document, false),
        sentLanguageOf: uri => documentLanguages.sentFor(protocolUri(uri)),
    };
}
