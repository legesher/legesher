/**
 * Language source of truth loader
 *
 * Reads from the i18n package's languages.json - the single source of truth
 * for language metadata across the Legesher monorepo.
 */

import * as fs from 'fs';
import * as path from 'path';

interface LanguageEntry {
    name: string;
    native: string;
    iso639_2: string;
    bcp47: string;
    rtl: boolean;
    status: 'experimental' | 'available' | 'deprecated';
}

interface LanguagesJson {
    canonical_language: string;
    languages: Record<string, LanguageEntry>;
}

/**
 * Path to the i18n package's languages.json (source of truth)
 * Navigate from test/fixtures -> libs/vs-code -> libs -> i18n/legesher_i18n
 */
const LANGUAGES_JSON_PATH = path.resolve(
    __dirname,
    '../../../..', // from test/fixtures to libs/
    'libs/i18n/legesher_i18n/languages.json'
);

let cachedLanguages: LanguagesJson | null = null;

/**
 * Load language data from the i18n package's languages.json
 * This is the single source of truth for all language metadata.
 */
export function loadLanguageSourceOfTruth(): LanguagesJson {
    if (cachedLanguages) {
        return cachedLanguages;
    }

    const content = fs.readFileSync(LANGUAGES_JSON_PATH, 'utf-8');
    cachedLanguages = JSON.parse(content) as LanguagesJson;
    return cachedLanguages;
}

/**
 * Get all supported language codes from the source of truth
 */
export function getSupportedLanguageCodes(): string[] {
    const data = loadLanguageSourceOfTruth();
    return Object.keys(data.languages).sort();
}

/**
 * Get language metadata in the format expected by VS Code extension tests
 */
export function getLanguageMetadata(): Record<string, { name: string; nativeName: string; rtl?: boolean }> {
    const data = loadLanguageSourceOfTruth();
    const result: Record<string, { name: string; nativeName: string; rtl?: boolean }> = {};

    for (const [code, entry] of Object.entries(data.languages)) {
        result[code] = {
            name: entry.name,
            nativeName: entry.native,
            ...(entry.rtl ? { rtl: true } : {}),
        };
    }

    return result;
}

/**
 * Get RTL language codes from the source of truth
 */
export function getRtlLanguageCodes(): string[] {
    const data = loadLanguageSourceOfTruth();
    return Object.entries(data.languages)
        .filter(([, entry]) => entry.rtl)
        .map(([code]) => code)
        .sort();
}

/**
 * Get the expected number of supported languages
 */
export function getExpectedLanguageCount(): number {
    const data = loadLanguageSourceOfTruth();
    return Object.keys(data.languages).length;
}
