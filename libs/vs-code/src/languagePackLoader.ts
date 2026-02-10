/**
 * Language Pack Loader for Legesher VS Code extension
 *
 * Loads Python keyword translations from YAML language pack files.
 * Language packs are located in the i18n package at:
 * libs/i18n/language-packs/python/{lang}/legesher_i18n_python_{lang}/packs/3.10.yml
 */

import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';
import { getActiveLanguageCodes } from './config';

/**
 * Structure of a language pack YAML file
 */
interface LanguagePack {
    language: string;
    target: string;
    version: string;
    keywords: { [english: string]: string };
    builtins?: { [english: string]: string };
    exceptions?: { [english: string]: string };
    metadata?: {
        python_version_min: string;
        python_version_max: string;
        last_updated: string;
        author: string;
    };
}

/**
 * Keyword translations indexed by language code
 */
export interface KeywordTranslations {
    [lang: string]: { [english: string]: string };
}

// Cache for loaded language packs
let _translationsCache: KeywordTranslations | null = null;
let _allKeywordsCache: Set<string> | null = null;
let _englishKeywordsCache: string[] | null = null;
// Separate caches for keywords vs builtins (for syntax highlighting)
let _pythonKeywordsCache: Set<string> | null = null;
let _pythonBuiltinsCache: Set<string> | null = null;
let _pathErrorLogged = false;

/**
 * Get the path to the language packs directory
 * Supports both development (monorepo) and packaged extension contexts
 */
function getLanguagePacksPath(extensionPath: string): string | null {
    // In development: extensionPath is libs/vs-code
    // Language packs are at ../../libs/i18n/language-packs/python
    const devPath = path.join(extensionPath, '..', '..', 'libs', 'i18n', 'language-packs', 'python');
    if (fs.existsSync(devPath)) {
        return devPath;
    }

    // In packaged extension: language packs should be bundled at ./language-packs
    const bundledPath = path.join(extensionPath, 'language-packs');
    if (fs.existsSync(bundledPath)) {
        return bundledPath;
    }

    // Fallback: monorepo root (when extensionPath is the repo root, not libs/vs-code)
    const fallbackPath = path.join(extensionPath, 'libs', 'i18n', 'language-packs', 'python');
    if (fs.existsSync(fallbackPath)) {
        return fallbackPath;
    }

    if (!_pathErrorLogged) {
        _pathErrorLogged = true;
        console.error(
            `[Legesher] Language packs not found. Searched:\n` +
            `  - ${devPath}\n` +
            `  - ${bundledPath}\n` +
            `  - ${fallbackPath}\n` +
            `Rebuild the extension with 'npm run compile' to bundle language packs.`
        );
    }
    return null;
}

/**
 * Load a single language pack from YAML file
 */
function loadLanguagePack(packPath: string): LanguagePack | null {
    try {
        if (!fs.existsSync(packPath)) {
            console.log(`[Legesher] Language pack not found: ${packPath}`);
            return null;
        }

        const content = fs.readFileSync(packPath, 'utf8');
        const pack = yaml.load(content) as LanguagePack;

        if (!pack || !pack.keywords) {
            console.warn(`[Legesher] Invalid language pack format: ${packPath}`);
            return null;
        }

        return pack;
    } catch (error) {
        console.error(`[Legesher] Error loading language pack ${packPath}:`, error);
        return null;
    }
}

/**
 * Load all language pack translations
 * @param extensionPath - The extension's installation path
 * @returns Keyword translations for all available languages
 */
export function loadAllTranslations(extensionPath: string): KeywordTranslations {
    if (_translationsCache) {
        return _translationsCache;
    }

    const translations: KeywordTranslations = {};
    const languagePacksPath = getLanguagePacksPath(extensionPath);

    if (!languagePacksPath) {
        _translationsCache = translations;
        return translations;
    }

    // Supported languages from centralized language registry (single source of truth)
    // Uses getActiveLanguageCodes() to include both 'available' and 'experimental' status
    const supportedLanguages = getActiveLanguageCodes();

    for (const lang of supportedLanguages) {
        // Path structure: {lang}/legesher_i18n_python_{lang}/packs/3.10.yml
        const packPath = path.join(
            languagePacksPath,
            lang,
            `legesher_i18n_python_${lang}`,
            'packs',
            '3.10.yml'
        );

        const pack = loadLanguagePack(packPath);
        if (pack && pack.keywords) {
            // Merge keywords and builtins into a single translation map
            translations[lang] = {
                ...pack.keywords,
                ...(pack.builtins || {}),
                ...(pack.exceptions || {})
            };
            console.log(`[Legesher] Loaded language pack: ${lang} (${Object.keys(translations[lang]).length} terms)`);
        }
    }

    // If no packs loaded, log a warning
    if (Object.keys(translations).length === 0) {
        console.warn(`[Legesher] No language packs loaded from ${languagePacksPath}`);
    }

    _translationsCache = translations;
    return translations;
}

/**
 * Get all English Python keywords from loaded language packs
 * Falls back to English pack or hardcoded list if packs unavailable
 */
export function getEnglishKeywords(extensionPath: string): string[] {
    if (_englishKeywordsCache) {
        return _englishKeywordsCache;
    }

    const translations = loadAllTranslations(extensionPath);

    // English pack has keywords mapping to themselves
    if (translations.en) {
        _englishKeywordsCache = Object.keys(translations.en);
        return _englishKeywordsCache;
    }

    // Fall back to any loaded pack's keys (they're all English)
    for (const lang of Object.keys(translations)) {
        if (translations[lang]) {
            _englishKeywordsCache = Object.keys(translations[lang]);
            return _englishKeywordsCache;
        }
    }

    // Ultimate fallback: hardcoded Python 3.10+ keywords
    _englishKeywordsCache = [
        'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
        'break', 'case', 'class', 'continue', 'def', 'del', 'elif', 'else',
        'except', 'finally', 'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'match', 'nonlocal', 'not', 'or', 'pass', 'raise',
        'return', 'try', 'while', 'with', 'yield'
    ];
    return _englishKeywordsCache;
}

/**
 * Get a set of all valid keywords (English + all translations) for efficient lookup
 */
export function getAllKeywords(extensionPath: string): Set<string> {
    if (_allKeywordsCache) {
        return _allKeywordsCache;
    }

    const translations = loadAllTranslations(extensionPath);
    const keywords = new Set<string>();

    // Add all English keywords and all translated keywords
    for (const langTranslations of Object.values(translations)) {
        // Add English keys
        for (const english of Object.keys(langTranslations)) {
            keywords.add(english);
        }
        // Add translated values
        for (const translated of Object.values(langTranslations)) {
            if (typeof translated === 'string') {
                keywords.add(translated);
            }
        }
    }

    _allKeywordsCache = keywords;
    return keywords;
}

/**
 * Check if a word is a Python keyword in any supported language
 */
export function isPythonKeyword(word: string, extensionPath: string): boolean {
    return getAllKeywords(extensionPath).has(word);
}

/**
 * Get the English keyword for a translated keyword
 * Returns the original word if it's already English or not found
 */
export function getEnglishKeyword(word: string, extensionPath: string): string {
    const englishKeywords = getEnglishKeywords(extensionPath);

    // Check if it's already an English keyword
    if (englishKeywords.includes(word)) {
        return word;
    }

    // Search through all translations
    const translations = loadAllTranslations(extensionPath);
    for (const langTranslations of Object.values(translations)) {
        for (const [english, translated] of Object.entries(langTranslations)) {
            if (translated === word) {
                return english;
            }
        }
    }

    return word;
}

/**
 * Get translations for a specific language
 */
export function getTranslationsForLanguage(lang: string, extensionPath: string): { [english: string]: string } | null {
    const translations = loadAllTranslations(extensionPath);
    return translations[lang] || null;
}

/**
 * Get a set of English Python keywords only (not builtins or exceptions)
 * Used for syntax highlighting to distinguish keywords from builtins
 */
export function getEnglishKeywordsSet(extensionPath: string): Set<string> {
    if (_pythonKeywordsCache) {
        return _pythonKeywordsCache;
    }

    const languagePacksPath = getLanguagePacksPath(extensionPath);
    if (languagePacksPath) {
        const packPath = path.join(
            languagePacksPath,
            'en',
            'legesher_i18n_python_en',
            'packs',
            '3.10.yml'
        );

        const pack = loadLanguagePack(packPath);
        if (pack && pack.keywords) {
            _pythonKeywordsCache = new Set(Object.keys(pack.keywords));
            return _pythonKeywordsCache;
        }
    }

    // Fallback: hardcoded Python 3.10+ keywords
    _pythonKeywordsCache = new Set([
        'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
        'break', 'case', 'class', 'continue', 'def', 'del', 'elif', 'else',
        'except', 'finally', 'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'match', 'nonlocal', 'not', 'or', 'pass', 'raise',
        'return', 'try', 'while', 'with', 'yield'
    ]);

    return _pythonKeywordsCache;
}

/**
 * Get a set of English Python builtins only (not keywords or exceptions)
 * Used for syntax highlighting to distinguish builtins from keywords
 */
export function getEnglishBuiltinsSet(extensionPath: string): Set<string> {
    if (_pythonBuiltinsCache) {
        return _pythonBuiltinsCache;
    }

    const languagePacksPath = getLanguagePacksPath(extensionPath);
    if (languagePacksPath) {
        const packPath = path.join(
            languagePacksPath,
            'en',
            'legesher_i18n_python_en',
            'packs',
            '3.10.yml'
        );

        const pack = loadLanguagePack(packPath);
        if (pack && pack.builtins) {
            _pythonBuiltinsCache = new Set(Object.keys(pack.builtins));
            return _pythonBuiltinsCache;
        }
    }

    // Fallback: hardcoded Python builtins
    _pythonBuiltinsCache = new Set([
        'abs', 'aiter', 'all', 'any', 'anext', 'ascii', 'bin', 'bool',
        'breakpoint', 'bytearray', 'bytes', 'callable', 'chr', 'classmethod',
        'compile', 'complex', 'delattr', 'dict', 'dir', 'divmod', 'enumerate',
        'eval', 'exec', 'filter', 'float', 'format', 'frozenset', 'getattr',
        'globals', 'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int',
        'isinstance', 'issubclass', 'iter', 'len', 'list', 'locals', 'map',
        'max', 'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord',
        'pow', 'print', 'property', 'range', 'repr', 'reversed', 'round',
        'set', 'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum',
        'super', 'tuple', 'type', 'vars', 'zip'
    ]);

    return _pythonBuiltinsCache;
}

/**
 * Clear the cache (useful for testing or when language packs are updated)
 */
export function clearCache(): void {
    _translationsCache = null;
    _allKeywordsCache = null;
    _englishKeywordsCache = null;
    _pythonKeywordsCache = null;
    _pythonBuiltinsCache = null;
    _pathErrorLogged = false;
}
