import * as vscode from 'vscode';

// Import from generated language definitions (single source of truth)
import {
    LANGUAGE_METADATA,
    getLanguageName as generatedGetLanguageName,
    getLanguageNativeName as generatedGetLanguageNativeName,
    getActiveLanguageCodes,
    getAvailableLanguageCodes,
    getRtlLanguageCodes,
    isSupportedLanguage,
    isRtlLanguage,
    type LanguageCode,
    type LanguageMetadata as GeneratedLanguageMetadata
} from './generated/languages';

/**
 * Language configuration returned by getLanguageConfig()
 */
export interface LanguageConfig {
    targetLanguage: string;
    sourceLanguage: string;
}

/**
 * Language pack information for display
 */
export interface LanguageInfo {
    code: string;
    name: string;
    nativeName: string;
}

/**
 * Get the current language configuration from VS Code settings
 */
export function getLanguageConfig(): LanguageConfig {
    const config = vscode.workspace.getConfiguration('legesher');

    // During extension development, inspect() returns the actual effective value
    // across all configuration scopes (global, workspace, folder)
    const targetLangInspect = config.inspect<string>('targetLanguage');
    const sourceLangInspect = config.inspect<string>('sourceLanguage');

    // Priority: globalValue > defaultValue
    const targetLanguage = targetLangInspect?.globalValue ||
                          targetLangInspect?.defaultValue ||
                          'en';
    const sourceLanguage = sourceLangInspect?.globalValue ||
                          sourceLangInspect?.defaultValue ||
                          'en';

    return {
        targetLanguage,
        sourceLanguage
    };
}

/**
 * Get available languages from the generated language registry.
 * This is the single source of truth loaded from languages.json.
 */
export function getAvailableLanguages(): LanguageInfo[] {
    return getAvailableLanguageCodes().map(code => ({
        code,
        name: generatedGetLanguageName(code),
        nativeName: generatedGetLanguageNativeName(code)
    }));
}

/**
 * Get active (non-deprecated) languages from the generated language registry.
 * Includes both 'available' and 'experimental' status languages.
 */
export function getActiveLanguages(): LanguageInfo[] {
    return getActiveLanguageCodes().map(code => ({
        code,
        name: generatedGetLanguageName(code),
        nativeName: generatedGetLanguageNativeName(code)
    }));
}

/**
 * Get the display name for a language code
 */
export function getLanguageName(code: string): string {
    return generatedGetLanguageName(code);
}

/**
 * Get the native name for a language code
 */
export function getLanguageNativeName(code: string): string {
    return generatedGetLanguageNativeName(code);
}

// Re-export for convenience
export {
    LANGUAGE_METADATA,
    getActiveLanguageCodes,
    getAvailableLanguageCodes,
    getRtlLanguageCodes,
    isSupportedLanguage,
    isRtlLanguage,
    type LanguageCode,
    type GeneratedLanguageMetadata
};
