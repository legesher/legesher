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
    /** Which configuration scope supplied targetLanguage. */
    scope: 'folder' | 'workspace' | 'user' | 'default';
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
 * Get the current language configuration from VS Code settings.
 *
 * Resolution follows VS Code's own precedence (folder > workspace > user >
 * default) via `get()`. The previous implementation read `inspect().globalValue`
 * directly, which silently ignored workspace and folder settings — a
 * `legesher.targetLanguage` committed in a project's `.vscode/settings.json`
 * had no effect at all (CORE-455).
 *
 * `inspect()` is still used, but only to report *which* scope won, for the
 * status bar indicator. It returns each scope's value separately; it is `get()`
 * that resolves the effective one.
 *
 * @param resource Optional document URI. Supply it so folder-level settings in
 * a multi-root workspace resolve against the right folder.
 */
export function getLanguageConfig(resource?: vscode.Uri): LanguageConfig {
    const config = vscode.workspace.getConfiguration('legesher', resource);

    const targetLanguage = config.get<string>('targetLanguage') || 'en';
    const sourceLanguage = config.get<string>('sourceLanguage') || 'en';

    const inspected = config.inspect<string>('targetLanguage');
    let scope: LanguageConfig['scope'] = 'default';
    if (inspected?.workspaceFolderValue !== undefined) {
        scope = 'folder';
    } else if (inspected?.workspaceValue !== undefined) {
        scope = 'workspace';
    } else if (inspected?.globalValue !== undefined) {
        scope = 'user';
    }

    return {
        targetLanguage,
        sourceLanguage,
        scope
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
