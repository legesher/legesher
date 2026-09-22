import * as vscode from 'vscode';
import * as path from 'path';
import { randomBytes } from 'crypto';
import { translateDocument } from './translator';
// [Copilot Review Fix] Removed unused import getAvailableLanguages
import { getLanguageNativeName, getLanguageConfig, getRtlLanguageCodes } from '../config';
import { getTranslations, getEnglishKeywordsSet, getEnglishBuiltinsSet } from '../keywords';
import { LegesherTelemetry } from '../telemetry';

/**
 * Message types sent from webview to extension
 */
type WebviewMessage =
    | { type: 'copy'; data: { text: string } }
    | { type: 'refresh' }
    | { type: 'error'; data: { message: string } };

/**
 * Manages the translation panel webview.
 * Singleton pattern ensures only one panel exists at a time.
 */
/**
 * Resolves the languages in effect for a document, including a language
 * detected from its contents.
 *
 * Injected rather than imported so the panel does not depend on the extension
 * entry point. Reading configuration directly meant the panel rendered the
 * configured language while the status bar and the running server both used the
 * detected one — the same file, described two different ways (CORE-1754).
 */
export type PanelLanguageResolver = (
    document: vscode.TextDocument
) => { sourceLanguage: string; targetLanguage: string };

export class TranslationPanelManager {
    private static instance: TranslationPanelManager | undefined;
    private static languageResolver: PanelLanguageResolver | undefined;

    /** Register how the panel should resolve a document's languages. */
    public static setLanguageResolver(resolver: PanelLanguageResolver): void {
        TranslationPanelManager.languageResolver = resolver;
    }
    private panel: vscode.WebviewPanel | undefined;
    private disposables: vscode.Disposable[] = [];

    private constructor(private readonly context: vscode.ExtensionContext) {}

    /**
     * Get or create the singleton instance of the translation panel manager.
     */
    public static getInstance(context: vscode.ExtensionContext): TranslationPanelManager {
        if (!TranslationPanelManager.instance) {
            TranslationPanelManager.instance = new TranslationPanelManager(context);
        }
        return TranslationPanelManager.instance;
    }

    /**
     * Show the translation panel for the given document.
     * If panel already exists, reveal it. Otherwise, create a new one.
     */
    public async show(document: vscode.TextDocument): Promise<void> {
        const column = vscode.ViewColumn.Beside;

        if (this.panel) {
            // Panel already exists, just reveal it
            this.panel.reveal(column);
        } else {
            // Create new panel
            this.panel = vscode.window.createWebviewPanel(
                'legesherTranslation',
                'Translation View',
                column,
                {
                    enableScripts: true,
                    retainContextWhenHidden: true,
                    localResourceRoots: [
                        vscode.Uri.joinPath(this.context.extensionUri, 'media'),
                        vscode.Uri.joinPath(this.context.extensionUri, 'out', 'webview'),
                        vscode.Uri.joinPath(this.context.extensionUri, 'out', 'prismjs')
                    ]
                }
            );

            // Set up panel lifecycle handlers
            this.panel.onDidDispose(() => this.dispose(), null, this.disposables);

            // Handle messages from webview
            this.panel.webview.onDidReceiveMessage(
                async (message) => await this.handleMessage(message),
                null,
                this.disposables
            );

            // Set initial HTML
            this.panel.webview.html = this.getWebviewContent();

            // Track panel opened
            LegesherTelemetry.trackPanelOpened();
            LegesherTelemetry.trackFeatureUsed('panel');
        }

        // Load and display translation
        await this.updateTranslation(document);
    }

    /**
     * Update the panel with a new translation for the given document.
     */
    private async updateTranslation(document: vscode.TextDocument): Promise<void> {
        if (!this.panel) {
            return;
        }

        try {
            // Show loading state
            this.panel.webview.postMessage({
                type: 'loading',
                data: { isLoading: true }
            });

            // Get original code
            const originalCode = document.getText();

            // Prefer the resolver, which accounts for a language detected from
            // the document's contents. Fall back to raw configuration only if
            // no resolver has been registered — rendering into the working
            // language, which is what the old single setting meant here.
            let sourceLanguage: string;
            let targetLanguage: string;
            if (TranslationPanelManager.languageResolver) {
                ({ sourceLanguage, targetLanguage } =
                    TranslationPanelManager.languageResolver(document));
            } else {
                const languageConfig = getLanguageConfig(document.uri);
                sourceLanguage = languageConfig.sourceLanguage;
                targetLanguage = languageConfig.workingLanguage;
            }

            // Translate document
            const translatedCode = await translateDocument(document, targetLanguage);

            // Get language display names
            const sourceLanguageName = getLanguageNativeName(sourceLanguage);
            const targetLanguageName = getLanguageNativeName(targetLanguage);

            // RTL languages from centralized language registry (single source of truth)
            const rtlLanguages = getRtlLanguageCodes();

            // Get translations for custom syntax highlighting of translated keywords
            const translations = getTranslations(targetLanguage) || {};

            // Get English keywords and builtins from source of truth (language packs)
            const pythonKeywords = Array.from(getEnglishKeywordsSet());
            const pythonBuiltins = Array.from(getEnglishBuiltinsSet());

            // Update panel with translation
            this.panel.webview.postMessage({
                type: 'update',
                data: {
                    originalCode,
                    translatedCode,
                    sourceLanguage,
                    targetLanguage,
                    sourceLanguageName,
                    targetLanguageName,
                    // Basename only: the full path would expose the OS username and
                    // directory structure to the webview context (CORE-597).
                    fileName: path.basename(document.fileName),
                    rtlLanguages,
                    translations,  // Pass translations for syntax highlighting
                    pythonKeywords,  // Pass keywords from source of truth
                    pythonBuiltins   // Pass builtins from source of truth
                }
            });
        } catch (error) {
            // Show error in panel
            const errorMessage = error instanceof Error ? error.message : String(error);
            this.panel.webview.postMessage({
                type: 'error',
                data: { message: errorMessage }
            });

            LegesherTelemetry.trackError('translationFailed', errorMessage);
            vscode.window.showErrorMessage(`Translation failed: ${errorMessage}`);
        }
    }

    /**
     * Handle messages from the webview.
     */
    private async handleMessage(message: WebviewMessage): Promise<void> {
        switch (message.type) {
            case 'copy':
                // Copy translation to clipboard
                await vscode.env.clipboard.writeText(message.data.text);
                vscode.window.showInformationMessage('Translation copied to clipboard');
                break;

            case 'refresh': {
                // Refresh translation for active editor
                const editor = vscode.window.activeTextEditor;
                if (editor) {
                    await this.updateTranslation(editor.document);
                }
                break;
            }

            case 'error':
                // Errors from webview are handled by the webview itself
                // No need to log here as they're already shown to the user
                break;
        }
    }

    /**
     * Generate the HTML content for the webview.
     */
    private getWebviewContent(): string {
        if (!this.panel) {
            return '';
        }

        const webview = this.panel.webview;

        // Get URIs for resources
        const styleUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this.context.extensionUri, 'out', 'webview', 'ui', 'styles.css')
        );
        const scriptUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this.context.extensionUri, 'out', 'webview', 'ui', 'main.js')
        );

        // Prism.js for syntax highlighting (copied to out/prismjs by esbuild)
        const prismCssUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this.context.extensionUri, 'out', 'prismjs', 'themes', 'prism-tomorrow.min.css')
        );
        const prismJsUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this.context.extensionUri, 'out', 'prismjs', 'prism.js')
        );
        const prismPythonUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this.context.extensionUri, 'out', 'prismjs', 'components', 'prism-python.min.js')
        );

        // Content Security Policy
        const cspSource = webview.cspSource;
        const nonce = this.getNonce();

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="
        default-src 'none';
        style-src ${cspSource};
        script-src ${cspSource} 'nonce-${nonce}';
        font-src ${cspSource};
    ">
    <title>Translation View</title>
    <link href="${styleUri}" rel="stylesheet">
    <link href="${prismCssUri}" rel="stylesheet">
</head>
<body>
    <div id="app">
        <div id="loading" class="loading hidden">
            <div class="spinner"></div>
            <p>Translating...</p>
        </div>

        <div id="error" class="error hidden">
            <h2>⚠️ Translation Error</h2>
            <p id="error-message"></p>
            <button id="retry-button" class="button">Retry</button>
        </div>

        <div id="content" class="content hidden">
            <header class="header">
                <div class="header-left">
                    <h2 id="source-lang-label">Original</h2>
                    <span id="file-name" class="file-name"></span>
                </div>
                <div class="header-right">
                    <h2 id="target-lang-label">Translation</h2>
                    <button id="copy-button" class="button" title="Copy translation to clipboard">
                        📋 Copy
                    </button>
                </div>
            </header>

            <div class="translation-container">
                <div class="pane left-pane">
                    <pre id="original-code"><code class="language-python"></code></pre>
                </div>
                <div class="divider"></div>
                <div class="pane right-pane">
                    <pre id="translated-code"><code class="language-python"></code></pre>
                </div>
            </div>
        </div>
    </div>

    <script src="${prismJsUri}"></script>
    <script src="${prismPythonUri}"></script>
    <script nonce="${nonce}" src="${scriptUri}"></script>
</body>
</html>`;
    }

    /**
     * Generate a nonce for Content Security Policy.
     */
    private getNonce(): string {
        // Cryptographically secure nonce for the webview CSP (base64 is a valid nonce charset).
        return randomBytes(16).toString('base64');
    }

    /**
     * Dispose of the panel and clean up resources.
     */
    private dispose(): void {
        TranslationPanelManager.instance = undefined;

        if (this.panel) {
            this.panel.dispose();
            this.panel = undefined;
        }

        // Dispose of all event listeners
        while (this.disposables.length) {
            const disposable = this.disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
    }

    /**
     * Public method to dispose the panel from outside.
     */
    public static disposeInstance(): void {
        if (TranslationPanelManager.instance) {
            TranslationPanelManager.instance.dispose();
        }
    }
}
