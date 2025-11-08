import * as vscode from 'vscode';

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
    return {
        targetLanguage: config.get<string>('targetLanguage', 'en'),
        sourceLanguage: config.get<string>('sourceLanguage', 'en')
    };
}

/**
 * Get available languages (MVP: hardcoded list)
 * Future: Auto-discover from installed i18n packages
 */
export function getAvailableLanguages(): LanguageInfo[] {
    return [
        { code: 'en', name: 'English', nativeName: 'English' },
        { code: 'es', name: 'Spanish', nativeName: 'Español' },
        { code: 'ar', name: 'Arabic', nativeName: 'العربية' },
        { code: 'zh', name: 'Chinese', nativeName: '中文' }
    ];
}

/**
 * Get the display name for a language code
 */
export function getLanguageName(code: string): string {
    const languages = getAvailableLanguages();
    const lang = languages.find(l => l.code === code);
    return lang ? lang.name : code.toUpperCase();
}

/**
 * Get the native name for a language code
 */
export function getLanguageNativeName(code: string): string {
    const languages = getAvailableLanguages();
    const lang = languages.find(l => l.code === code);
    return lang ? lang.nativeName : code.toUpperCase();
}
