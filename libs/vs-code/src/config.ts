import * as vscode from 'vscode';
import { scopeOf, type SettingScope } from './settingsScope';
import {
    resolveKnownLanguages,
    resolveWorkingLanguage,
    type ResolvedLanguages,
} from './languageProfile';

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

// The languages a server instance is started with. Defined with the rest of
// the role vocabulary in languageProfile.ts; re-exported here because this
// module is where every consumer already looks for it. The server reads all of
// it once, in on_initialize, so its identity is the whole set — passing it as
// one value keeps the languages that were resolved and the languages the
// server is actually running from drifting apart (CORE-1776).
export { type ResolvedLanguages };

/**
 * Language configuration returned by getLanguageConfig()
 *
 * The user's side of the language profile (CORE-1760): the roles that come
 * from settings rather than from the file on screen. The file language is
 * resolved per document, by detection, and never lives here.
 */
export interface LanguageConfig {
    /** Canonical: the language the project's code is stored in. */
    sourceLanguage: string;
    /** The language the user reads and writes in right now. */
    workingLanguage: string;
    /** The languages the user reads comfortably; never empty (seeded). */
    knownLanguages: string[];
    /** Which configuration scope supplied the working language (or its deprecated alias). */
    scope: SettingScope;
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
 * The working language honours `legesher.targetLanguage` as a deprecated
 * alias, without letting the alias escape VS Code's precedence: scope decides
 * first (folder > workspace > user > default), and only within one scope does
 * `workingLanguage` outrank `targetLanguage`. So an existing configuration
 * keeps working, a migrated one is never overridden by the setting it migrated
 * from, and a project that pins the old key still beats the reader's own
 * global preference (CORE-1760). See `resolveWorkingLanguage` for why
 * resolving by key first is the wrong shape.
 *
 * @param resource Optional document URI. Supply it so folder-level settings in
 * a multi-root workspace resolve against the right folder.
 */
export function getLanguageConfig(resource?: vscode.Uri): LanguageConfig {
    const config = vscode.workspace.getConfiguration('legesher', resource);

    // Resolved together rather than as two independent lookups: the scope that
    // supplies the value and the value itself have to come from the same pass,
    // or the picker writes to a scope that does not hold what it just read.
    const { language: workingLanguage, scope } = resolveWorkingLanguage(
        config.inspect<string>('workingLanguage'),
        config.inspect<string>('targetLanguage')
    );
    const sourceLanguage = config.get<string>('sourceLanguage') || 'en';
    // Deliberately untyped: `get<string[]>` is a claim, not a check, and a
    // hand-edited settings file can hold anything.
    const knownLanguages = resolveKnownLanguages(
        config.get('knownLanguages'),
        workingLanguage
    );

    return {
        sourceLanguage,
        workingLanguage,
        knownLanguages,
        scope
    };
}

/**
 * Report which scope currently supplies `key`, for a write that has to land
 * where it will actually take effect (CORE-1776).
 *
 * Pass a `config` obtained with the document's URI so folder-level settings
 * resolve against the right folder in a multi-root workspace.
 */
export function getSettingScope(
    config: vscode.WorkspaceConfiguration,
    key: string
): SettingScope {
    return scopeOf(config.inspect(key));
}

export { type SettingScope };

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
