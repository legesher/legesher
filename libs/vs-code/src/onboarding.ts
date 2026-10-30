import * as vscode from 'vscode';
import { LegesherTelemetry } from './telemetry';

/**
 * Onboarding Manager for Legesher VS Code Extension
 *
 * Handles first-time user experience including:
 * - Welcome message
 * - Language selection
 * - ML training data consent
 */

export class OnboardingManager {
    private static readonly STORAGE_KEY = 'legesher.onboarding.completed';
    private static readonly ML_CONSENT_KEY = 'legesher.onboarding.mlConsentAsked';

    /**
     * Check if this is the user's first time activating the extension
     */
    static isFirstTimeUser(context: vscode.ExtensionContext): boolean {
        return !context.globalState.get<boolean>(this.STORAGE_KEY, false);
    }

    /**
     * Show onboarding experience for first-time users
     * Called during extension activation
     */
    static async showOnboarding(context: vscode.ExtensionContext): Promise<void> {
        const isFirstTime = this.isFirstTimeUser(context);

        if (!isFirstTime) {
            return; // Already onboarded
        }

        // Open the interactive walkthrough for a rich onboarding experience
        await vscode.commands.executeCommand(
            'workbench.action.openWalkthrough',
            'legesher.legesher-vscode#legesher.welcome',
            false // don't open in side bar
        );

        // Track walkthrough opened
        LegesherTelemetry.trackWalkthroughOpened();

        // Mark onboarding as complete (user can always re-access via Help > Get Started)
        await context.globalState.update(this.STORAGE_KEY, true);

        // Show ML training consent after a brief delay (don't overwhelm on first open)
        const ML_CONSENT_DELAY_MS = 5000;
        setTimeout(() => {
            this.showMLTrainingConsent(context);
        }, ML_CONSENT_DELAY_MS);
    }

    /**
     * Show ML training data collection consent dialog
     * This is a separate step from the welcome message
     */
    static async showMLTrainingConsent(context: vscode.ExtensionContext): Promise<void> {
        // Check if we've already asked for ML consent
        const alreadyAsked = context.globalState.get<boolean>(this.ML_CONSENT_KEY, false);
        if (alreadyAsked) {
            return;
        }

        const result = await vscode.window.showInformationMessage(
            '🤝 Help improve Legesher translations? Share feedback when you correct suggestions. No code or personal info collected; events carry a pseudonymous machine id.',
            'Learn More',
            'Yes, Help Improve',
            'No Thanks'
        );

        // Mark as asked (even if they clicked Learn More, don't spam them)
        await context.globalState.update(this.ML_CONSENT_KEY, true);

        if (result === 'Learn More') {
            // Open privacy policy
            await vscode.env.openExternal(
                vscode.Uri.parse('https://docs.legesher.io/privacy/#ml-training-data-opt-in-only')
            );

            // Show a follow-up dialog with just Yes/No (they've read the policy)
            const followUpResult = await vscode.window.showInformationMessage(
                'Would you like to contribute usage data to Legesher so we can improve translations?',
                'Yes, Help Improve',
                'No Thanks'
            );

            const optedIn = followUpResult === 'Yes, Help Improve';
            await this.saveMLConsent(optedIn);
        } else {
            const optedIn = result === 'Yes, Help Improve';
            await this.saveMLConsent(optedIn);
        }
    }

    /**
     * Save ML training consent to settings
     */
    private static async saveMLConsent(optedIn: boolean): Promise<void> {
        await vscode.workspace
            .getConfiguration('legesher')
            .update(
                'telemetry.contributeToMLTraining',
                optedIn,
                vscode.ConfigurationTarget.Global
            );
    }

    /**
     * Prompt for ML consent when user makes their first translation correction
     * (Alternative to showing during onboarding - shows in context)
     *
     * Call this when user makes first correction if consent not yet given
     */
    static async promptMLConsentOnFirstCorrection(context: vscode.ExtensionContext): Promise<boolean> {
        const alreadyAsked = context.globalState.get<boolean>(this.ML_CONSENT_KEY, false);

        if (alreadyAsked) {
            // Return current setting
            return vscode.workspace
                .getConfiguration('legesher')
                .get<boolean>('telemetry.contributeToMLTraining', false);
        }

        // Show consent dialog
        await this.showMLTrainingConsent(context);

        // Return user's choice
        return vscode.workspace
            .getConfiguration('legesher')
            .get<boolean>('telemetry.contributeToMLTraining', false);
    }

    /**
     * Reset onboarding (useful for testing)
     * Adds a command: legesher.resetOnboarding
     */
    static registerResetCommand(context: vscode.ExtensionContext): void {
        const disposable = vscode.commands.registerCommand('legesher.resetOnboarding', async () => {
            await context.globalState.update(this.STORAGE_KEY, false);
            await context.globalState.update(this.ML_CONSENT_KEY, false);
            await vscode.workspace
                .getConfiguration('legesher')
                .update('telemetry.contributeToMLTraining', undefined, vscode.ConfigurationTarget.Global);

            vscode.window.showInformationMessage(
                'Onboarding reset! Reload window to see it again.',
                'Reload Window'
            ).then(result => {
                if (result === 'Reload Window') {
                    vscode.commands.executeCommand('workbench.action.reloadWindow');
                }
            });
        });

        context.subscriptions.push(disposable);
    }
}
