/**
 * AUTO-GENERATED FILE - DO NOT EDIT DIRECTLY
 *
 * This file is generated from translations.db (languages table, in_registry = 1)
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
    'am' |
    'ar' |
    'bn' |
    'bs' |
    'ca' |
    'cs' |
    'cy' |
    'da' |
    'de' |
    'el' |
    'en' |
    'es' |
    'fa' |
    'fi' |
    'fr' |
    'ga' |
    'gd' |
    'gl' |
    'gu' |
    'he' |
    'hi' |
    'hr' |
    'hu' |
    'id' |
    'it' |
    'ja' |
    'kn' |
    'ko' |
    'lv' |
    'mk' |
    'ml' |
    'mn' |
    'ms' |
    'my' |
    'nl' |
    'no' |
    'pl' |
    'pt' |
    'ro' |
    'ru' |
    'si' |
    'sr' |
    'su' |
    'sv' |
    'te' |
    'th' |
    'tr' |
    'ur' |
    'uz' |
    'vi' |
    'zh';

export const CANONICAL_LANGUAGE: LanguageCode = 'en';

export const LANGUAGE_METADATA: Record<LanguageCode, LanguageMetadata> = {
    'am': { name: 'Amharic', native: 'አማርኛ', iso639_2: 'amh', bcp47: 'am', rtl: false, status: 'experimental' },
    'ar': { name: 'Arabic', native: 'العربية', iso639_2: 'ara', bcp47: 'ar', rtl: true, status: 'experimental' },
    'bn': { name: 'Bengali', native: 'বাংলা', iso639_2: 'ben', bcp47: 'bn', rtl: false, status: 'experimental' },
    'bs': { name: 'Bosnian', native: 'Bosanski', iso639_2: 'bos', bcp47: 'bs', rtl: false, status: 'experimental' },
    'ca': { name: 'Catalan', native: 'Català', iso639_2: 'cat', bcp47: 'ca', rtl: false, status: 'experimental' },
    'cs': { name: 'Czech', native: 'Čeština', iso639_2: 'ces', bcp47: 'cs', rtl: false, status: 'experimental' },
    'cy': { name: 'Welsh', native: 'Cymraeg', iso639_2: 'cym', bcp47: 'cy', rtl: false, status: 'experimental' },
    'da': { name: 'Danish', native: 'Dansk', iso639_2: 'dan', bcp47: 'da', rtl: false, status: 'experimental' },
    'de': { name: 'German', native: 'Deutsch', iso639_2: 'deu', bcp47: 'de', rtl: false, status: 'experimental' },
    'el': { name: 'Greek', native: 'Ελληνικά', iso639_2: 'ell', bcp47: 'el', rtl: false, status: 'experimental' },
    'en': { name: 'English', native: 'English', iso639_2: 'eng', bcp47: 'en', rtl: false, status: 'experimental' },
    'es': { name: 'Spanish', native: 'Español', iso639_2: 'spa', bcp47: 'es', rtl: false, status: 'experimental' },
    'fa': { name: 'Persian', native: 'فارسی', iso639_2: 'fas', bcp47: 'fa', rtl: true, status: 'experimental' },
    'fi': { name: 'Finnish', native: 'Suomi', iso639_2: 'fin', bcp47: 'fi', rtl: false, status: 'experimental' },
    'fr': { name: 'French', native: 'Français', iso639_2: 'fra', bcp47: 'fr', rtl: false, status: 'experimental' },
    'ga': { name: 'Irish', native: 'Gaeilge', iso639_2: 'gle', bcp47: 'ga', rtl: false, status: 'experimental' },
    'gd': { name: 'Scottish Gaelic', native: 'Gàidhlig', iso639_2: 'gla', bcp47: 'gd', rtl: false, status: 'experimental' },
    'gl': { name: 'Galician', native: 'Galego', iso639_2: 'glg', bcp47: 'gl', rtl: false, status: 'experimental' },
    'gu': { name: 'Gujarati', native: 'ગુજરાતી', iso639_2: 'guj', bcp47: 'gu', rtl: false, status: 'experimental' },
    'he': { name: 'Hebrew', native: 'עברית', iso639_2: 'heb', bcp47: 'he', rtl: true, status: 'experimental' },
    'hi': { name: 'Hindi', native: 'हिन्दी', iso639_2: 'hin', bcp47: 'hi', rtl: false, status: 'experimental' },
    'hr': { name: 'Croatian', native: 'Hrvatski', iso639_2: 'hrv', bcp47: 'hr', rtl: false, status: 'experimental' },
    'hu': { name: 'Hungarian', native: 'Magyar', iso639_2: 'hun', bcp47: 'hu', rtl: false, status: 'experimental' },
    'id': { name: 'Indonesian', native: 'Bahasa Indonesia', iso639_2: 'ind', bcp47: 'id', rtl: false, status: 'experimental' },
    'it': { name: 'Italian', native: 'Italiano', iso639_2: 'ita', bcp47: 'it', rtl: false, status: 'experimental' },
    'ja': { name: 'Japanese', native: '日本語', iso639_2: 'jpn', bcp47: 'ja', rtl: false, status: 'experimental' },
    'kn': { name: 'Kannada', native: 'ಕನ್ನಡ', iso639_2: 'kan', bcp47: 'kn', rtl: false, status: 'experimental' },
    'ko': { name: 'Korean', native: '한국어', iso639_2: 'kor', bcp47: 'ko', rtl: false, status: 'experimental' },
    'lv': { name: 'Latvian', native: 'Latviešu', iso639_2: 'lav', bcp47: 'lv', rtl: false, status: 'experimental' },
    'mk': { name: 'Macedonian', native: 'Македонски', iso639_2: 'mkd', bcp47: 'mk', rtl: false, status: 'experimental' },
    'ml': { name: 'Malayalam', native: 'മലയാളം', iso639_2: 'mal', bcp47: 'ml', rtl: false, status: 'experimental' },
    'mn': { name: 'Mongolian', native: 'Монгол', iso639_2: 'mon', bcp47: 'mn', rtl: false, status: 'experimental' },
    'ms': { name: 'Malay', native: 'Bahasa Melayu', iso639_2: 'msa', bcp47: 'ms', rtl: false, status: 'experimental' },
    'my': { name: 'Burmese', native: 'မြန်မာ', iso639_2: 'mya', bcp47: 'my', rtl: false, status: 'experimental' },
    'nl': { name: 'Dutch', native: 'Nederlands', iso639_2: 'nld', bcp47: 'nl', rtl: false, status: 'experimental' },
    'no': { name: 'Norwegian', native: 'Norsk', iso639_2: 'nor', bcp47: 'nb', rtl: false, status: 'experimental' },
    'pl': { name: 'Polish', native: 'Polski', iso639_2: 'pol', bcp47: 'pl', rtl: false, status: 'experimental' },
    'pt': { name: 'Portuguese', native: 'Português', iso639_2: 'por', bcp47: 'pt', rtl: false, status: 'experimental' },
    'ro': { name: 'Romanian', native: 'Română', iso639_2: 'ron', bcp47: 'ro', rtl: false, status: 'experimental' },
    'ru': { name: 'Russian', native: 'Русский', iso639_2: 'rus', bcp47: 'ru', rtl: false, status: 'experimental' },
    'si': { name: 'Sinhala', native: 'සිංහල', iso639_2: 'sin', bcp47: 'si', rtl: false, status: 'experimental' },
    'sr': { name: 'Serbian', native: 'Српски', iso639_2: 'srp', bcp47: 'sr', rtl: false, status: 'experimental' },
    'su': { name: 'Sundanese', native: 'Basa Sunda', iso639_2: 'sun', bcp47: 'su', rtl: false, status: 'experimental' },
    'sv': { name: 'Swedish', native: 'Svenska', iso639_2: 'swe', bcp47: 'sv', rtl: false, status: 'experimental' },
    'te': { name: 'Telugu', native: 'తెలుగు', iso639_2: 'tel', bcp47: 'te', rtl: false, status: 'experimental' },
    'th': { name: 'Thai', native: 'ไทย', iso639_2: 'tha', bcp47: 'th', rtl: false, status: 'experimental' },
    'tr': { name: 'Turkish', native: 'Türkçe', iso639_2: 'tur', bcp47: 'tr', rtl: false, status: 'experimental' },
    'ur': { name: 'Urdu', native: 'اردو', iso639_2: 'urd', bcp47: 'ur', rtl: true, status: 'experimental' },
    'uz': { name: 'Uzbek', native: 'O\'zbek', iso639_2: 'uzb', bcp47: 'uz', rtl: false, status: 'experimental' },
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
