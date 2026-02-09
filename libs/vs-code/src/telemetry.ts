import * as vscode from 'vscode';
import { TelemetryReporter } from '@vscode/extension-telemetry';
import { isPythonKeyword, getEnglishKeyword } from './keywords';
import { Logger } from './logger';

/**
 * Telemetry module for Legesher VS Code extension
 *
 * Collects anonymous usage data to help improve the extension.
 * Respects VS Code's telemetry settings and user preferences.
 *
 * NO PII IS COLLECTED - no file paths, code content, or personal information.
 */

// Azure Application Insights connection string
// Read at runtime to support envFile in launch.json during development
// In production, this is injected at build time by esbuild's define option
function getConnectionString(): string {
    return process.env.LEGESHER_TELEMETRY_CONNECTION_STRING || '';
}

let reporter: TelemetryReporter | undefined;
let isInitialized = false;

/** Known command names for type-safe telemetry tracking */
type TrackedCommand = 'restartServer' | 'selectLanguage' | 'showTranslationPanel' | 'tryTranslationPanel' | 'giveFeedback';

/** Known error types for type-safe error tracking */
type TrackedErrorType = 'serverError' | 'serverConnectionClosed' | 'serverNotInstalled' | 'serverStartFailed' | 'translationFailed';

/**
 * Legesher Telemetry - tracks anonymous usage to improve the extension
 */
export class LegesherTelemetry {
    /**
     * Initialize the telemetry reporter
     * Must be called during extension activation
     */
    static initialize(context: vscode.ExtensionContext): void {
        // Don't initialize if already done
        if (isInitialized) {
            return;
        }

        // Check if VS Code global telemetry is enabled
        // @vscode/extension-telemetry silently drops events when this is false
        const vscodeTelemetryEnabled = vscode.env.isTelemetryEnabled;
        Logger.info(`Telemetry: VS Code isTelemetryEnabled = ${vscodeTelemetryEnabled}`);
        if (!vscodeTelemetryEnabled) {
            Logger.warn('Telemetry: VS Code global telemetry is disabled (vscode.env.isTelemetryEnabled is false) - events will not be sent by the telemetry reporter');
        }

        // Check if telemetry is enabled in extension settings
        const config = vscode.workspace.getConfiguration('legesher');
        const telemetryEnabled = config.get<boolean>('telemetry.enabled', true);

        if (!telemetryEnabled) {
            Logger.info('Telemetry: Disabled via legesher.telemetry.enabled setting');
            return;
        }

        // Get connection string at runtime (supports envFile in launch.json)
        const connectionString = getConnectionString();
        Logger.info(`Telemetry: Connection string present = ${!!connectionString}`);

        // Don't initialize without a connection string
        if (!connectionString) {
            Logger.warn('Telemetry: No connection string configured (set LEGESHER_TELEMETRY_CONNECTION_STRING) - telemetry disabled');
            return;
        }

        try {
            reporter = new TelemetryReporter(connectionString);
            context.subscriptions.push(reporter);
            isInitialized = true;
            Logger.info('Telemetry: Initialized successfully');
        } catch (error) {
            Logger.error('Telemetry: Failed to initialize:', error);
        }
    }

    /**
     * Check if telemetry is active
     */
    static isActive(): boolean {
        return isInitialized && reporter !== undefined;
    }

    /**
     * Track extension activation
     */
    static trackActivation(language: string): void {
        if (!reporter) return;

        try {
            const props = {
                targetLanguage: language,
                vscodeVersion: vscode.version,
                extensionVersion: vscode.extensions.getExtension('legesher.legesher-vscode')?.packageJSON?.version || 'unknown'
            };
            Logger.info(`Telemetry: Sending extensionActivated event (lang=${language})`);
            reporter.sendTelemetryEvent('extensionActivated', props);
            Logger.info('Telemetry: extensionActivated event sent');
        } catch (error) {
            Logger.error('Telemetry: Error sending extensionActivated:', error);
        }
    }

    /**
     * Track language change
     */
    static trackLanguageChange(fromLanguage: string, toLanguage: string): void {
        if (!reporter) return;

        try {
            reporter.sendTelemetryEvent('languageChanged', {
                fromLanguage,
                toLanguage
            });
        } catch (error) {
            Logger.error('Telemetry: Error sending languageChanged:', error);
        }
    }

    /**
     * Track feature usage
     * @param feature - The feature used (completion, hover, panel, semanticTokens)
     */
    static trackFeatureUsed(feature: 'completion' | 'hover' | 'panel' | 'semanticTokens'): void {
        if (!reporter) return;

        try {
            reporter.sendTelemetryEvent('featureUsed', {
                feature
            });
        } catch (error) {
            Logger.error('Telemetry: Error sending featureUsed:', error);
        }
    }

    /**
     * Track command execution
     * @param command - The command executed (restricted to known commands)
     */
    static trackCommand(command: TrackedCommand): void {
        if (!reporter) return;

        try {
            reporter.sendTelemetryEvent('commandExecuted', {
                command
            });
        } catch (error) {
            Logger.error('Telemetry: Error sending commandExecuted:', error);
        }
    }

    /**
     * Track language server connection
     * @param success - Whether connection was successful
     * @param durationMs - Connection duration in milliseconds
     */
    static trackServerConnection(success: boolean, durationMs: number): void {
        if (!reporter) return;

        try {
            reporter.sendTelemetryEvent('serverConnected', {
                success: success.toString()
            }, {
                durationMs
            });
        } catch (error) {
            Logger.error('Telemetry: Error sending serverConnected:', error);
        }
    }

    /**
     * Track errors (non-PII)
     * @param errorType - Type of error (restricted to known error types)
     * @param context - Additional context (sanitized to remove potential PII)
     */
    static trackError(errorType: TrackedErrorType, context?: string): void {
        if (!reporter) return;

        // Strip potential PII: file paths and email addresses
        const safeContext = context
            ? context.replace(/\/[\w/.\\-]+/g, '<path>').replace(/[\w.-]+@[\w.-]+/g, '<email>')
            : 'none';

        try {
            reporter.sendTelemetryErrorEvent('errorOccurred', {
                errorType,
                context: safeContext
            });
        } catch (error) {
            Logger.error('Telemetry: Error sending errorOccurred:', error);
        }
    }

    /**
     * Track completion provided
     * @param count - Number of completion items provided
     */
    static trackCompletionProvided(count: number): void {
        if (!reporter) return;

        try {
            reporter.sendTelemetryEvent('completionProvided', {}, {
                itemCount: count
            });
        } catch (error) {
            Logger.error('Telemetry: Error sending completionProvided:', error);
        }
    }

    /**
     * Track hover provided
     * @param keyword - The keyword hovered (Python keyword in any supported language)
     */
    static trackHoverProvided(keyword: string): void {
        if (!reporter) return;

        // Only track Python keywords (in any supported language), not user-defined names
        // Uses shared keywords module that supports all Legesher languages
        if (isPythonKeyword(keyword)) {
            // Normalize to English keyword for consistent analytics
            const englishKeyword = getEnglishKeyword(keyword);
            try {
                reporter.sendTelemetryEvent('hoverProvided', {
                    keyword: englishKeyword,
                    originalKeyword: keyword !== englishKeyword ? keyword : undefined
                });
            } catch (error) {
                Logger.error('Telemetry: Error sending hoverProvided:', error);
            }
        }
    }

    /**
     * Track translation panel opened
     */
    static trackPanelOpened(): void {
        if (!reporter) return;

        try {
            reporter.sendTelemetryEvent('translationPanelOpened');
        } catch (error) {
            Logger.error('Telemetry: Error sending translationPanelOpened:', error);
        }
    }

    /**
     * Track feedback prompt response
     * @param promptType - Which feedback prompt was shown ('first' or 'second')
     * @param response - User's response ('gaveFeedback', 'deferred', 'optedOut')
     */
    static trackFeedbackResponse(promptType: 'first' | 'second' | 'manual', response: 'gaveFeedback' | 'deferred' | 'optedOut'): void {
        if (!reporter) return;

        try {
            reporter.sendTelemetryEvent('feedbackResponse', {
                promptType,
                response
            });
        } catch (error) {
            Logger.error('Telemetry: Error sending feedbackResponse:', error);
        }
    }

    /**
     * Track walkthrough opened
     */
    static trackWalkthroughOpened(): void {
        if (!reporter) return;

        try {
            reporter.sendTelemetryEvent('walkthroughOpened');
        } catch (error) {
            Logger.error('Telemetry: Error sending walkthroughOpened:', error);
        }
    }

    /**
     * Dispose of the telemetry reporter
     * Called automatically via context.subscriptions
     */
    static dispose(): void {
        // Reporter is disposed automatically via context.subscriptions
        reporter = undefined;
        isInitialized = false;
    }
}
