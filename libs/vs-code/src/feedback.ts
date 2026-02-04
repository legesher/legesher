import * as vscode from 'vscode';

/**
 * Feedback collection module for Legesher VS Code extension
 *
 * Prompts users to provide feedback after using the extension for a period of time.
 * Uses a timing-based approach to avoid being intrusive.
 */

// Get feedback URL at runtime to support envFile in launch.json during development
function getFeedbackUrl(): string {
    return process.env.LEGESHER_FEEDBACK_URL || 'https://legesher.io/go/vs-code-extension-survey';
}

// Configuration
const FEEDBACK_CONFIG = {
    // Google Form URL for feedback survey (read via getFeedbackUrl() at runtime)
    get feedbackFormUrl(): string {
        return getFeedbackUrl();
    },

    // How long to wait before first prompt (first session - immediate on second activation)
    firstPromptDelayMs: 0,

    // How long to wait before second prompt (7 days in milliseconds)
    secondPromptDelayMs: 7 * 24 * 60 * 60 * 1000,

    // How often to remind if user clicks "Not Now" (7 days in milliseconds)
    reminderDelayMs: 7 * 24 * 60 * 60 * 1000,

    // How often to check if we should prompt (1 hour in milliseconds for first session check)
    checkIntervalMs: 60 * 60 * 1000,

    // Prompt messages
    messages: {
        firstPrompt: "Welcome to Legesher! We'd love your first impressions. Would you care to share quick feedback?",
        secondPrompt: "You've been using Legesher for a week! How's your experience been coding in your native language?",
        giveFeedback: "Give Feedback",
        notNow: "Not Now",
        dontAskAgain: "Don't Ask Again"
    }
};

// Storage keys for persisting state
const STORAGE_KEYS = {
    firstActivation: 'legesher.feedback.firstActivation',
    activationCount: 'legesher.feedback.activationCount',
    firstFeedbackGiven: 'legesher.feedback.firstGiven',
    secondFeedbackGiven: 'legesher.feedback.secondGiven',
    lastPrompt: 'legesher.feedback.lastPrompt',
    dontAskAgain: 'legesher.feedback.dontAskAgain'
};

/**
 * Feedback system for collecting user input
 */
export class LegesherFeedback {
    private context: vscode.ExtensionContext;
    private checkInterval: NodeJS.Timeout | undefined;

    constructor(context: vscode.ExtensionContext) {
        this.context = context;
    }

    /**
     * Initialize the feedback system
     * Should be called during extension activation
     */
    initialize(): void {
        console.log('[Legesher Feedback] Initializing...');
        console.log('[Legesher Feedback] Feedback URL present:', !!FEEDBACK_CONFIG.feedbackFormUrl);
        console.log('[Legesher Feedback] Feedback URL:', FEEDBACK_CONFIG.feedbackFormUrl || 'undefined');

        // Record first activation time if not already set
        const firstActivation = this.context.globalState.get<number>(STORAGE_KEYS.firstActivation);
        if (!firstActivation) {
            this.context.globalState.update(STORAGE_KEYS.firstActivation, Date.now());
            this.context.globalState.update(STORAGE_KEYS.activationCount, 1);
            console.log('[Legesher Feedback] First activation recorded');
        } else {
            // Increment activation count
            const count = this.context.globalState.get<number>(STORAGE_KEYS.activationCount) || 1;
            this.context.globalState.update(STORAGE_KEYS.activationCount, count + 1);
            console.log(`[Legesher Feedback] Activation count: ${count + 1}`);
        }

        // Check if we should prompt on startup
        this.checkAndPrompt();

        // Set up periodic check
        this.checkInterval = setInterval(() => {
            this.checkAndPrompt();
        }, FEEDBACK_CONFIG.checkIntervalMs);

        console.log('[Legesher Feedback] Initialized');
    }

    /**
     * Check if we should prompt for feedback and do so if appropriate
     */
    private async checkAndPrompt(): Promise<void> {
        if (!this.shouldPrompt()) {
            return;
        }

        await this.showFeedbackPrompt();
    }

    /**
     * Determine which prompt to show (if any)
     * Returns: 'first' | 'second' | null
     */
    private getPromptType(): 'first' | 'second' | null {
        // Check if user said "Don't ask again"
        const dontAskAgain = this.context.globalState.get<boolean>(STORAGE_KEYS.dontAskAgain);
        if (dontAskAgain) {
            return null;
        }

        const activationCount = this.context.globalState.get<number>(STORAGE_KEYS.activationCount) || 1;
        const firstFeedbackGiven = this.context.globalState.get<boolean>(STORAGE_KEYS.firstFeedbackGiven);
        const secondFeedbackGiven = this.context.globalState.get<boolean>(STORAGE_KEYS.secondFeedbackGiven);

        // First prompt: Show on second activation (after first session)
        if (!firstFeedbackGiven && activationCount >= 2) {
            const lastPrompt = this.context.globalState.get<number>(STORAGE_KEYS.lastPrompt);
            if (!lastPrompt) {
                return 'first';
            }
            // Check reminder delay if they clicked "Not Now"
            const timeSinceLastPrompt = Date.now() - lastPrompt;
            if (timeSinceLastPrompt >= FEEDBACK_CONFIG.reminderDelayMs) {
                return 'first';
            }
        }

        // Second prompt: Show after 7 days
        if (firstFeedbackGiven && !secondFeedbackGiven) {
            const firstActivation = this.context.globalState.get<number>(STORAGE_KEYS.firstActivation);
            if (!firstActivation) {
                return null;
            }
            const timeSinceFirstActivation = Date.now() - firstActivation;
            if (timeSinceFirstActivation >= FEEDBACK_CONFIG.secondPromptDelayMs) {
                const lastPrompt = this.context.globalState.get<number>(STORAGE_KEYS.lastPrompt);
                if (!lastPrompt || (Date.now() - lastPrompt) >= FEEDBACK_CONFIG.reminderDelayMs) {
                    return 'second';
                }
            }
        }

        return null;
    }

    /**
     * Determine if we should show the feedback prompt
     */
    private shouldPrompt(): boolean {
        return this.getPromptType() !== null;
    }

    /**
     * Show the feedback prompt to the user
     */
    private async showFeedbackPrompt(): Promise<void> {
        // Don't show prompts if feedback URL is not configured
        if (!FEEDBACK_CONFIG.feedbackFormUrl) {
            return;
        }

        const promptType = this.getPromptType();
        if (!promptType) {
            return;
        }

        // Record that we showed the prompt
        this.context.globalState.update(STORAGE_KEYS.lastPrompt, Date.now());

        // Select the appropriate message
        const message = promptType === 'first'
            ? FEEDBACK_CONFIG.messages.firstPrompt
            : FEEDBACK_CONFIG.messages.secondPrompt;

        const result = await vscode.window.showInformationMessage(
            message,
            FEEDBACK_CONFIG.messages.giveFeedback,
            FEEDBACK_CONFIG.messages.notNow,
            FEEDBACK_CONFIG.messages.dontAskAgain
        );

        switch (result) {
            case FEEDBACK_CONFIG.messages.giveFeedback:
                // Open feedback form in browser
                await vscode.env.openExternal(vscode.Uri.parse(FEEDBACK_CONFIG.feedbackFormUrl));
                // Mark the appropriate feedback as given
                if (promptType === 'first') {
                    this.context.globalState.update(STORAGE_KEYS.firstFeedbackGiven, true);
                } else {
                    this.context.globalState.update(STORAGE_KEYS.secondFeedbackGiven, true);
                }
                // Show thank you message
                vscode.window.showInformationMessage(
                    "Thank you for helping improve Legesher! Your feedback is invaluable."
                );
                console.log(`[Legesher Feedback] User opened feedback form (${promptType} prompt)`);
                break;

            case FEEDBACK_CONFIG.messages.dontAskAgain:
                this.context.globalState.update(STORAGE_KEYS.dontAskAgain, true);
                console.log('[Legesher Feedback] User opted out of feedback prompts');
                break;

            case FEEDBACK_CONFIG.messages.notNow:
            default:
                console.log(`[Legesher Feedback] User deferred feedback (${promptType} prompt)`);
                break;
        }
    }

    /**
     * Manually trigger feedback prompt (e.g., from command palette)
     */
    async promptNow(): Promise<void> {
        // Check if feedback URL is configured
        if (!FEEDBACK_CONFIG.feedbackFormUrl) {
            vscode.window.showWarningMessage(
                'Feedback form not configured (set LEGESHER_FEEDBACK_URL). Please check extension settings.'
            );
            return;
        }

        const result = await vscode.window.showInformationMessage(
            "Would you like to share feedback about Legesher?",
            "Open Feedback Form",
            "Cancel"
        );

        if (result === "Open Feedback Form") {
            await vscode.env.openExternal(vscode.Uri.parse(FEEDBACK_CONFIG.feedbackFormUrl));
            // Only mark first feedback as given - don't skip the 7-day prompt
            this.context.globalState.update(STORAGE_KEYS.firstFeedbackGiven, true);
            vscode.window.showInformationMessage(
                "Thank you for your feedback!"
            );
        }
    }

    /**
     * Reset feedback state (for testing purposes)
     */
    async resetState(): Promise<void> {
        await this.context.globalState.update(STORAGE_KEYS.firstActivation, undefined);
        await this.context.globalState.update(STORAGE_KEYS.activationCount, undefined);
        await this.context.globalState.update(STORAGE_KEYS.firstFeedbackGiven, undefined);
        await this.context.globalState.update(STORAGE_KEYS.secondFeedbackGiven, undefined);
        await this.context.globalState.update(STORAGE_KEYS.lastPrompt, undefined);
        await this.context.globalState.update(STORAGE_KEYS.dontAskAgain, undefined);
        console.log('[Legesher Feedback] State reset');
    }

    /**
     * Dispose of the feedback system
     */
    dispose(): void {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = undefined;
        }
    }
}

// Singleton instance
let feedbackInstance: LegesherFeedback | undefined;

/**
 * Initialize the feedback system
 * @param context Extension context
 */
export function initializeFeedback(context: vscode.ExtensionContext): LegesherFeedback {
    if (!feedbackInstance) {
        feedbackInstance = new LegesherFeedback(context);
        feedbackInstance.initialize();
        context.subscriptions.push({
            dispose: () => feedbackInstance?.dispose()
        });
    }
    return feedbackInstance;
}

/**
 * Get the feedback instance
 */
export function getFeedbackInstance(): LegesherFeedback | undefined {
    return feedbackInstance;
}
