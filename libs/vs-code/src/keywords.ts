/**
 * Python keywords and translations for Legesher VS Code extension
 *
 * This module provides access to Python keywords and their translations
 * across all supported languages. Data is loaded from the i18n language packs
 * to ensure translations stay in sync.
 *
 * For translation and hover functionality, use the language pack loader directly.
 * This module provides convenience re-exports and the extension path management.
 */

import {
    loadAllTranslations,
    getAllKeywords,
    isPythonKeyword as _isPythonKeyword,
    getEnglishKeyword as _getEnglishKeyword,
    getEnglishKeywords,
    getTranslationsForLanguage,
    KeywordTranslations
} from './languagePackLoader';

// Store the extension path for use by exported functions
let _extensionPath: string = '';

/**
 * Initialize the keywords module with the extension path
 * Must be called during extension activation
 */
export function initializeKeywords(extensionPath: string): void {
    _extensionPath = extensionPath;
    // Pre-load translations
    loadAllTranslations(extensionPath);
    console.log('[Legesher Keywords] Initialized with path:', extensionPath);
}

/**
 * Get the extension path (for internal use)
 */
function getExtensionPath(): string {
    if (!_extensionPath) {
        console.warn('[Legesher Keywords] Extension path not initialized, using current directory');
        return process.cwd();
    }
    return _extensionPath;
}

/**
 * Get all keyword translations indexed by language
 * Loaded from language pack YAML files
 */
export function getKeywordTranslations(): KeywordTranslations {
    return loadAllTranslations(getExtensionPath());
}

/**
 * Check if a word is a Python keyword in any supported language
 * This is used by telemetry to determine if a hover should be tracked
 *
 * @param word The word to check
 * @returns true if the word is a Python keyword in any language
 */
export function isPythonKeyword(word: string): boolean {
    return _isPythonKeyword(word, getExtensionPath());
}

/**
 * Get the English keyword for a translated keyword
 * Returns the original word if it's already English or not found
 *
 * @param word The translated keyword
 * @returns The English keyword, or the original word if not found
 */
export function getEnglishKeyword(word: string): string {
    return _getEnglishKeyword(word, getExtensionPath());
}

/**
 * Get all English Python keywords
 */
export function getPythonKeywords(): string[] {
    return getEnglishKeywords(getExtensionPath());
}

/**
 * Get a set of all valid keywords (English + all translations) for efficient lookup
 */
export function getAllKeywordsSet(): Set<string> {
    return getAllKeywords(getExtensionPath());
}

/**
 * Get translations for a specific target language
 * @param lang Language code (e.g., 'es', 'ar', 'zh', 'fr')
 * @returns Translation map or null if language not found
 */
export function getTranslations(lang: string): { [english: string]: string } | null {
    return getTranslationsForLanguage(lang, getExtensionPath());
}

// Re-export types
export type { KeywordTranslations };
