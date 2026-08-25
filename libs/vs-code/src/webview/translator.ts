import * as vscode from 'vscode';
import { getTranslations } from '../keywords';

// Track which languages we've already warned about to avoid log spam
const _warnedLanguages = new Set<string>();

/**
 * Translate a Python document to the target language.
 *
 * For MVP, this is a placeholder that returns a simulated translation.
 * In production, this will integrate with the LSP server to perform actual translation.
 *
 * @param document The document to translate
 * @param targetLanguage The target language code (e.g., 'es', 'ar', 'zh')
 * @returns The translated code as a string
 */
export async function translateDocument(
    document: vscode.TextDocument,
    targetLanguage: string
): Promise<string> {
    // Validate document is Python
    if (document.languageId !== 'python') {
        throw new Error('Translation only supports Python files');
    }

    const originalCode = document.getText();

    // Check if document is empty
    if (!originalCode.trim()) {
        return originalCode;
    }

    try {
        // Preview-quality translation, computed in the extension from the
        // bundled language packs rather than by the engine. See
        // `simulateTranslation` for what that does and does not cover.
        const translated = await simulateTranslation(originalCode, targetLanguage);
        return translated;
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        throw Object.assign(new Error(`Translation failed: ${errorMessage}`), { cause: error });
    }
}

/**
 * Translate keywords by word-boundary substitution against the bundled packs.
 *
 * This is the panel's preview path, not the engine. It rewrites every
 * word-boundary match, so unlike `legesher translate` it has no lexical
 * awareness: a keyword spelled inside a string literal or a comment is
 * rewritten too, and an identifier that happens to match a keyword is not
 * protected. Good enough to show what a file looks like translated; not the
 * path to use for output that has to run.
 *
 * Returns the code unchanged when no pack is bundled for the language.
 *
 * @param code The original Python code
 * @param targetLanguage The target language code
 * @returns Code with pack keywords substituted
 */
async function simulateTranslation(code: string, targetLanguage: string): Promise<string> {
    // Get translations for the target language from language packs
    const translations = getTranslations(targetLanguage);

    if (!translations) {
        if (!_warnedLanguages.has(targetLanguage)) {
            _warnedLanguages.add(targetLanguage);
            console.warn(
                `[Legesher] No translations found for language "${targetLanguage}". ` +
                'Language packs may not be bundled with the extension. ' +
                'Rebuild the extension to copy language packs.'
            );
        }
        return code;
    }

    // Apply translations using word boundary regex to avoid partial matches
    let translatedCode = code;
    for (const [keyword, translation] of Object.entries(translations)) {
        const regex = new RegExp(`\\b${keyword}\\b`, 'g');
        translatedCode = translatedCode.replace(regex, translation);
    }

    return translatedCode;
}

/**
 * Format a translation error for display.
 *
 * @param error The error that occurred
 * @returns A user-friendly error message
 */
export function formatTranslationError(error: unknown): string {
    if (error instanceof Error) {
        return error.message;
    }
    return 'An unknown error occurred during translation';
}
