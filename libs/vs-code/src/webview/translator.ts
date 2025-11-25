import * as vscode from 'vscode';
import { getTranslations } from '../keywords';

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
        // TODO: Integrate with LSP server for actual translation
        // For now, return a simulated translation for demo purposes
        const translated = await simulateTranslation(originalCode, targetLanguage);
        return translated;
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        throw new Error(`Translation failed: ${errorMessage}`);
    }
}

/**
 * Simulate translation for demo purposes.
 * This will be replaced with actual LSP server integration.
 *
 * @param code The original Python code
 * @param targetLanguage The target language code
 * @returns Simulated translated code
 */
async function simulateTranslation(code: string, targetLanguage: string): Promise<string> {
    // Get translations for the target language from language packs
    const translations = getTranslations(targetLanguage);

    if (!translations) {
        // Default: return original code (English or unsupported language)
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
