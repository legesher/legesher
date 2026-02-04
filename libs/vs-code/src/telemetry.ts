import * as vscode from 'vscode';
import { TelemetryReporter } from '@vscode/extension-telemetry';
import { isPythonKeyword, getEnglishKeyword } from './keywords';

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
// In production, this should be injected at build time
function getConnectionString(): string {
    return process.env.LEGESHER_TELEMETRY_CONNECTION_STRING || '';
}

let reporter: TelemetryReporter | undefined;
let isInitialized = false;

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

        // Check if telemetry is enabled in extension settings
        const config = vscode.workspace.getConfiguration('legesher');
        const telemetryEnabled = config.get<boolean>('telemetry.enabled', true);

        if (!telemetryEnabled) {
            console.log('[Legesher Telemetry] Disabled via extension settings');
            return;
        }

        // Get connection string at runtime (supports envFile in launch.json)
        const connectionString = getConnectionString();
        console.log('[Legesher Telemetry] Connection string present:', !!connectionString);

        // Don't initialize without a connection string
        if (!connectionString) {
            console.log('[Legesher Telemetry] No connection string configured (set LEGESHER_TELEMETRY_CONNECTION_STRING) - telemetry disabled');
            return;
        }

        try {
            reporter = new TelemetryReporter(connectionString);
            context.subscriptions.push(reporter);
            isInitialized = true;
            console.log('[Legesher Telemetry] Initialized successfully');
        } catch (error) {
            console.error('[Legesher Telemetry] Failed to initialize:', error);
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

        reporter.sendTelemetryEvent('extensionActivated', {
            targetLanguage: language,
            vscodeVersion: vscode.version,
            extensionVersion: vscode.extensions.getExtension('legesher.legesher-vscode')?.packageJSON?.version || 'unknown'
        });
    }

    /**
     * Track language change
     */
    static trackLanguageChange(fromLanguage: string, toLanguage: string): void {
        if (!reporter) return;

        reporter.sendTelemetryEvent('languageChanged', {
            fromLanguage,
            toLanguage
        });
    }

    /**
     * Track feature usage
     * @param feature - The feature used (completion, hover, diagnostic, panel, run)
     */
    static trackFeatureUsed(feature: 'completion' | 'hover' | 'diagnostic' | 'panel' | 'run' | 'semanticTokens'): void {
        if (!reporter) return;

        reporter.sendTelemetryEvent('featureUsed', {
            feature
        });
    }

    /**
     * Track command execution
     * @param command - The command executed
     */
    static trackCommand(command: string): void {
        if (!reporter) return;

        reporter.sendTelemetryEvent('commandExecuted', {
            command
        });
    }

    /**
     * Track language server connection
     * @param success - Whether connection was successful
     * @param durationMs - Connection duration in milliseconds
     */
    static trackServerConnection(success: boolean, durationMs: number): void {
        if (!reporter) return;

        reporter.sendTelemetryEvent('serverConnected', {
            success: success.toString()
        }, {
            durationMs
        });
    }

    /**
     * Track errors (non-PII)
     * @param errorType - Type of error (e.g., 'serverCrash', 'translationFailed')
     * @param context - Additional context (no PII!)
     */
    static trackError(errorType: string, context?: string): void {
        if (!reporter) return;

        reporter.sendTelemetryErrorEvent('errorOccurred', {
            errorType,
            context: context || 'none'
        });
    }

    /**
     * Track completion provided
     * @param count - Number of completion items provided
     */
    static trackCompletionProvided(count: number): void {
        if (!reporter) return;

        reporter.sendTelemetryEvent('completionProvided', {}, {
            itemCount: count
        });
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
            reporter.sendTelemetryEvent('hoverProvided', {
                keyword: englishKeyword,
                originalKeyword: keyword !== englishKeyword ? keyword : undefined
            });
        }
    }

    /**
     * Track translation panel opened
     */
    static trackPanelOpened(): void {
        if (!reporter) return;

        reporter.sendTelemetryEvent('translationPanelOpened');
    }

    /**
     * Track walkthrough step completion
     * @param stepId - The walkthrough step ID (e.g., 'intro', 'selectLanguage')
     */
    static trackWalkthroughStep(stepId: string): void {
        if (!reporter) return;

        reporter.sendTelemetryEvent('walkthroughStepCompleted', {
            stepId
        });
    }

    /**
     * Track walkthrough opened
     */
    static trackWalkthroughOpened(): void {
        if (!reporter) return;

        reporter.sendTelemetryEvent('walkthroughOpened');
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
