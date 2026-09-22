import * as vscode from 'vscode';
import { TelemetryReporter } from '@vscode/extension-telemetry';
import { isPythonKeyword, getEnglishKeyword } from './keywords';
import { Logger } from './logger';
import type { SettingScope } from './settingsScope';
import type {
    LanguageTrigger,
    ResolutionSource,
    TransitionOutcome,
} from './serverState';

/**
 * Telemetry module for Legesher VS Code extension
 *
 * Collects usage data to help improve the extension.
 * Respects VS Code's telemetry settings and user preferences.
 *
 * The events we author contain no code content, no file paths, and no
 * identifiers; the bundled @vscode/extension-telemetry library adds a
 * pseudonymous machine id and session id to each event.
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
type TrackedCommand = 'restartServer' | 'selectLanguage' | 'manageMyLanguages' | 'showTranslationPanel' | 'tryTranslationPanel' | 'giveFeedback';

/** Known error types for type-safe error tracking */
type TrackedErrorType = 'serverError' | 'serverConnectionClosed' | 'serverNotInstalled' | 'serverStartFailed' | 'translationFailed'
    | 'languageWriteFailed' | 'languageWriteShadowed';

/**
 * The transition vocabulary is owned by the state machine, not by the analytics
 * layer, and re-exported here only for convenience at existing call sites.
 *
 * The dependency runs this way deliberately: telemetry describes what the system
 * did, so the system defines the words. Two hand-maintained copies of the same
 * enumeration is the shape of the bug class this instrumentation exists to catch
 * (CORE-1776, CORE-1847).
 */
export type { LanguageTrigger, TransitionOutcome, ResolutionSource };

/** Whether a settings write landed where it would actually take effect. */
export type WriteOutcome = 'applied' | 'shadowed' | 'failed';

/**
 * Legesher Telemetry - tracks usage to improve the extension
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
        const telemetryEnabled = config.get<boolean>('telemetry.enabled', false);

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
     * Track a requested language change and what actually became of it
     * (CORE-1776).
     *
     * `languageChanged` above records only picker *intent*, and it is sent
     * before the write it describes — so a pick that silently did nothing still
     * reported success, and the majority of transitions (settings edits,
     * detection, activation) were never counted at all. This records the whole
     * transition instead: what asked for it, where the language came from, the
     * pair the server actually ended on, and whether anything happened.
     *
     * Language codes and scope names are not PII; no paths or content are sent.
     *
     * @param params.from - Server identity before, or 'none'
     * @param params.to - Server identity requested, as `source->target`
     * @param params.trigger - What asked for the change
     * @param params.source - Which scope or mechanism supplied the language
     * @param params.outcome - What actually happened
     * @param params.durationMs - Time to apply, when one was applied
     */
    static trackLanguageTransition(params: {
        from: string;
        to: string;
        trigger: LanguageTrigger;
        source: ResolutionSource;
        outcome: TransitionOutcome;
        durationMs?: number;
    }): void {
        if (!reporter) return;

        try {
            reporter.sendTelemetryEvent('languageTransition', {
                from: params.from,
                to: params.to,
                trigger: params.trigger,
                source: params.source,
                outcome: params.outcome,
            }, params.durationMs === undefined ? undefined : { durationMs: params.durationMs });
        } catch (error) {
            Logger.error('Telemetry: Error sending languageTransition:', error);
        }
    }

    /**
     * Track a language settings write and whether it can take effect
     * (CORE-1776).
     *
     * The scope is the point: a write to user settings that a workspace value
     * outranks is indistinguishable from a successful one unless the scope is
     * recorded alongside the outcome.
     */
    static trackLanguageSettingWrite(
        setting: 'workingLanguage' | 'languageDetection' | 'knownLanguages',
        // A configuration scope, not a resolution source: a *write* can land in
        // folder/workspace/user settings, but never in 'detected', which is not
        // somewhere anything can be written.
        scope: SettingScope,
        outcome: WriteOutcome
    ): void {
        if (!reporter) return;

        try {
            reporter.sendTelemetryEvent('languageSettingWritten', {
                setting,
                scope,
                outcome,
            });
        } catch (error) {
            Logger.error('Telemetry: Error sending languageSettingWritten:', error);
        }
    }

    /**
     * Track a content-detection decision (CORE-1776).
     *
     * Detection's thresholds were tuned against fixtures and have never been
     * measured against real files. Declines are recorded as well as hits: a
     * detector that never fires and one that fires constantly are different
     * problems, and only the scores tell them apart.
     *
     * Emitted per document *version*, not per editor switch — the memo absorbs
     * the repeats.
     */
    static trackLanguageDetection(
        outcome: 'detected' | 'declined',
        detail: { language?: string; score?: number; runnerUpScore?: number } = {}
    ): void {
        if (!reporter) return;

        try {
            reporter.sendTelemetryEvent('languageDetected', {
                outcome,
                language: detail.language ?? 'none',
            }, {
                score: detail.score ?? 0,
                runnerUpScore: detail.runnerUpScore ?? 0,
            });
        } catch (error) {
            Logger.error('Telemetry: Error sending languageDetected:', error);
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
