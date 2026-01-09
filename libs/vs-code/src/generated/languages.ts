/**
 * AUTO-GENERATED FILE - DO NOT EDIT DIRECTLY
 *
 * This file is generated from libs/i18n/legesher_i18n/languages.json
 * Run: uv run python libs/i18n/legesher_i18n/scripts/generate_languages.py
 */

export type LanguageStatus = 'available' | 'experimental' | 'deprecated';

export interface LanguageMetadata {
    name: string;
    native: string;
    iso639_2: string;
    bcp47: string;
    rtl: boolean;
    status: LanguageStatus;
}

export type LanguageCode =
    'ar' |
    'da' |
    'de' |
    'el' |
    'en' |
    'es' |
    'fi' |
    'fr' |
    'he' |
    'hi' |
    'hu' |
    'id' |
    'it' |
    'ja' |
    'ko' |
    'ms' |
    'nl' |
    'no' |
    'pl' |
    'pt' |
    'ru' |
    'sv' |
    'th' |
    'tr' |
    'vi' |
    'zh';

export const CANONICAL_LANGUAGE: LanguageCode = 'en';

export const LANGUAGE_METADATA: Record<LanguageCode, LanguageMetadata> = {
    'ar': { name: 'Arabic', native: 'العربية', iso639_2: 'ara', bcp47: 'ar', rtl: true, status: 'experimental' },
    'da': { name: 'Danish', native: 'Dansk', iso639_2: 'dan', bcp47: 'da', rtl: false, status: 'experimental' },
    'de': { name: 'German', native: 'Deutsch', iso639_2: 'deu', bcp47: 'de', rtl: false, status: 'experimental' },
    'el': { name: 'Greek', native: 'Ελληνικά', iso639_2: 'ell', bcp47: 'el', rtl: false, status: 'experimental' },
    'en': { name: 'English', native: 'English', iso639_2: 'eng', bcp47: 'en', rtl: false, status: 'experimental' },
    'es': { name: 'Spanish', native: 'Español', iso639_2: 'spa', bcp47: 'es', rtl: false, status: 'experimental' },
    'fi': { name: 'Finnish', native: 'Suomi', iso639_2: 'fin', bcp47: 'fi', rtl: false, status: 'experimental' },
    'fr': { name: 'French', native: 'Français', iso639_2: 'fra', bcp47: 'fr', rtl: false, status: 'experimental' },
    'he': { name: 'Hebrew', native: 'עברית', iso639_2: 'heb', bcp47: 'he', rtl: true, status: 'experimental' },
    'hi': { name: 'Hindi', native: 'हिन्दी', iso639_2: 'hin', bcp47: 'hi', rtl: false, status: 'experimental' },
    'hu': { name: 'Hungarian', native: 'Magyar', iso639_2: 'hun', bcp47: 'hu', rtl: false, status: 'experimental' },
    'id': { name: 'Indonesian', native: 'Bahasa Indonesia', iso639_2: 'ind', bcp47: 'id', rtl: false, status: 'experimental' },
    'it': { name: 'Italian', native: 'Italiano', iso639_2: 'ita', bcp47: 'it', rtl: false, status: 'experimental' },
    'ja': { name: 'Japanese', native: '日本語', iso639_2: 'jpn', bcp47: 'ja', rtl: false, status: 'experimental' },
    'ko': { name: 'Korean', native: '한국어', iso639_2: 'kor', bcp47: 'ko', rtl: false, status: 'experimental' },
    'ms': { name: 'Malay', native: 'Bahasa Melayu', iso639_2: 'msa', bcp47: 'ms', rtl: false, status: 'experimental' },
    'nl': { name: 'Dutch', native: 'Nederlands', iso639_2: 'nld', bcp47: 'nl', rtl: false, status: 'experimental' },
    'no': { name: 'Norwegian', native: 'Norsk', iso639_2: 'nor', bcp47: 'nb', rtl: false, status: 'experimental' },
    'pl': { name: 'Polish', native: 'Polski', iso639_2: 'pol', bcp47: 'pl', rtl: false, status: 'experimental' },
    'pt': { name: 'Portuguese', native: 'Português', iso639_2: 'por', bcp47: 'pt', rtl: false, status: 'experimental' },
    'ru': { name: 'Russian', native: 'Русский', iso639_2: 'rus', bcp47: 'ru', rtl: false, status: 'experimental' },
    'sv': { name: 'Swedish', native: 'Svenska', iso639_2: 'swe', bcp47: 'sv', rtl: false, status: 'experimental' },
    'th': { name: 'Thai', native: 'ไทย', iso639_2: 'tha', bcp47: 'th', rtl: false, status: 'experimental' },
    'tr': { name: 'Turkish', native: 'Türkçe', iso639_2: 'tur', bcp47: 'tr', rtl: false, status: 'experimental' },
    'vi': { name: 'Vietnamese', native: 'Tiếng Việt', iso639_2: 'vie', bcp47: 'vi', rtl: false, status: 'experimental' },
    'zh': { name: 'Chinese', native: '中文', iso639_2: 'zho', bcp47: 'zh-Hans', rtl: false, status: 'experimental' },
};

/**
 * Get all available language codes.
 */
export function getAvailableLanguageCodes(): LanguageCode[] {
    return Object.keys(LANGUAGE_METADATA)
        .filter(code => LANGUAGE_METADATA[code as LanguageCode].status === 'available') as LanguageCode[];
}

/**
 * Get all active (non-deprecated) language codes.
 * Returns both 'available' and 'experimental' status languages.
 */
export function getActiveLanguageCodes(): LanguageCode[] {
    return Object.keys(LANGUAGE_METADATA)
        .filter(code => {
            const status = LANGUAGE_METADATA[code as LanguageCode].status;
            return status === 'available' || status === 'experimental';
        }) as LanguageCode[];
}

/**
 * Get all RTL (right-to-left) language codes.
 */
export function getRtlLanguageCodes(): LanguageCode[] {
    return Object.keys(LANGUAGE_METADATA)
        .filter(code => LANGUAGE_METADATA[code as LanguageCode].rtl) as LanguageCode[];
}

/**
 * Get the English name for a language code.
 */
export function getLanguageName(code: string): string {
    return LANGUAGE_METADATA[code as LanguageCode]?.name ?? code.toUpperCase();
}

/**
 * Get the native name for a language code.
 */
export function getLanguageNativeName(code: string): string {
    return LANGUAGE_METADATA[code as LanguageCode]?.native ?? code.toUpperCase();
}

/**
 * Check if a language code uses RTL script.
 */
export function isRtlLanguage(code: string): boolean {
    return LANGUAGE_METADATA[code as LanguageCode]?.rtl ?? false;
}

/**
 * Check if a language code is supported.
 */
export function isSupportedLanguage(code: string): boolean {
    return code in LANGUAGE_METADATA;
}
