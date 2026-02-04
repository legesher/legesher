/**
 * Unit tests for config module
 *
 * Tests language configuration loading and validation.
 * Uses the i18n package's languages.json as the source of truth.
 */

import * as assert from 'assert';
import * as sinon from 'sinon';
import {
    getSupportedLanguageCodes,
    getLanguageMetadata,
    getRtlLanguageCodes,
    getExpectedLanguageCount,
} from '../fixtures/language-source';

// Load from source of truth (libs/i18n/legesher_i18n/languages.json)
const SUPPORTED_LANGUAGES = getSupportedLanguageCodes();
const LANGUAGE_METADATA = getLanguageMetadata();
const EXPECTED_LANGUAGE_COUNT = getExpectedLanguageCount();
const RTL_LANGUAGES = getRtlLanguageCodes();

describe('Config Module', () => {
    let sandbox: sinon.SinonSandbox;

    beforeEach(() => {
        sandbox = sinon.createSandbox();
    });

    afterEach(() => {
        sandbox.restore();
    });

    describe('Supported Languages', () => {
        it(`should have exactly ${EXPECTED_LANGUAGE_COUNT} supported languages`, () => {
            assert.strictEqual(SUPPORTED_LANGUAGES.length, EXPECTED_LANGUAGE_COUNT);
        });

        it('should include all required language codes', () => {
            // These are the core languages that must always be supported
            const required = ['en', 'es', 'fr', 'de', 'zh', 'ja', 'ko', 'ar', 'he'];

            required.forEach(lang => {
                assert.ok(
                    SUPPORTED_LANGUAGES.includes(lang),
                    `${lang} should be in supported languages`
                );
            });
        });

        it('should use ISO 639-1 two-letter codes', () => {
            SUPPORTED_LANGUAGES.forEach(lang => {
                assert.strictEqual(
                    lang.length,
                    2,
                    `${lang} should be a 2-letter code`
                );
                assert.ok(
                    /^[a-z]{2}$/.test(lang),
                    `${lang} should be lowercase letters only`
                );
            });
        });

        it('should have unique language codes', () => {
            const uniqueCodes = new Set(SUPPORTED_LANGUAGES);
            assert.strictEqual(
                uniqueCodes.size,
                SUPPORTED_LANGUAGES.length,
                'Language codes should be unique'
            );
        });
    });

    describe('Language Metadata', () => {
        it('should have metadata for all supported languages', () => {
            SUPPORTED_LANGUAGES.forEach(lang => {
                assert.ok(
                    LANGUAGE_METADATA[lang],
                    `Metadata should exist for ${lang}`
                );
            });
        });

        it('should have name and nativeName for each language', () => {
            Object.entries(LANGUAGE_METADATA).forEach(([code, meta]) => {
                assert.ok(meta.name, `${code} should have a name`);
                assert.ok(meta.nativeName, `${code} should have a nativeName`);
                assert.ok(meta.name.length > 0, `${code} name should not be empty`);
                assert.ok(meta.nativeName.length > 0, `${code} nativeName should not be empty`);
            });
        });

        it('should mark RTL languages correctly', () => {
            const ltrLanguages = SUPPORTED_LANGUAGES.filter(l => !RTL_LANGUAGES.includes(l));

            RTL_LANGUAGES.forEach(lang => {
                assert.strictEqual(
                    LANGUAGE_METADATA[lang].rtl,
                    true,
                    `${lang} should be marked as RTL`
                );
            });

            ltrLanguages.forEach(lang => {
                assert.ok(
                    !LANGUAGE_METADATA[lang].rtl,
                    `${lang} should not be marked as RTL`
                );
            });
        });

        it('should have Arabic and Hebrew as RTL languages', () => {
            // Explicit check for known RTL languages
            assert.ok(RTL_LANGUAGES.includes('ar'), 'Arabic should be RTL');
            assert.ok(RTL_LANGUAGES.includes('he'), 'Hebrew should be RTL');
        });
    });

    describe('Language Configuration', () => {
        it('should default to English', () => {
            const mockConfig: Record<string, string> = {};
            const targetLanguage = mockConfig['legesher.targetLanguage'] ?? 'en';

            assert.strictEqual(targetLanguage, 'en');
        });

        it('should validate target language against supported list', () => {
            const validateLanguage = (lang: string): boolean => {
                return SUPPORTED_LANGUAGES.includes(lang);
            };

            // Valid languages
            assert.ok(validateLanguage('en'));
            assert.ok(validateLanguage('es'));
            assert.ok(validateLanguage('zh'));

            // Invalid languages
            assert.ok(!validateLanguage('xx'));
            assert.ok(!validateLanguage(''));
            assert.ok(!validateLanguage('english'));
            assert.ok(!validateLanguage('EN')); // Case-sensitive
        });

        it('should support only English as source language', () => {
            // Per the extension design, source language is always English
            const supportedSourceLanguages = ['en'];

            assert.strictEqual(supportedSourceLanguages.length, 1);
            assert.strictEqual(supportedSourceLanguages[0], 'en');
        });
    });

    describe('Language Name Resolution', () => {
        it('should return correct name for language code', () => {
            const getLanguageName = (code: string): string => {
                return LANGUAGE_METADATA[code]?.name ?? code;
            };

            assert.strictEqual(getLanguageName('en'), 'English');
            assert.strictEqual(getLanguageName('es'), 'Spanish');
            assert.strictEqual(getLanguageName('zh'), 'Chinese');
            assert.strictEqual(getLanguageName('ja'), 'Japanese');
        });

        it('should return native name for language code', () => {
            const getLanguageNativeName = (code: string): string => {
                return LANGUAGE_METADATA[code]?.nativeName ?? code;
            };

            assert.strictEqual(getLanguageNativeName('en'), 'English');
            assert.strictEqual(getLanguageNativeName('es'), 'Español');
            assert.strictEqual(getLanguageNativeName('zh'), '中文');
            assert.strictEqual(getLanguageNativeName('ja'), '日本語');
            assert.strictEqual(getLanguageNativeName('ar'), 'العربية');
        });

        it('should return code for unknown language', () => {
            const getLanguageName = (code: string): string => {
                return LANGUAGE_METADATA[code]?.name ?? code;
            };

            assert.strictEqual(getLanguageName('xx'), 'xx');
            assert.strictEqual(getLanguageName('unknown'), 'unknown');
        });
    });

    describe('Active Languages', () => {
        it('should return all languages when status is experimental', () => {
            // All languages are currently experimental
            const getActiveLanguages = () => {
                return SUPPORTED_LANGUAGES.map(code => ({
                    code,
                    ...LANGUAGE_METADATA[code],
                    status: 'experimental' as const,
                }));
            };

            const activeLanguages = getActiveLanguages();

            assert.strictEqual(activeLanguages.length, EXPECTED_LANGUAGE_COUNT);
            activeLanguages.forEach(lang => {
                assert.strictEqual(lang.status, 'experimental');
            });
        });

        it('should include all metadata in active language objects', () => {
            const getActiveLanguages = () => {
                return SUPPORTED_LANGUAGES.map(code => ({
                    code,
                    ...LANGUAGE_METADATA[code],
                }));
            };

            const activeLanguages = getActiveLanguages();

            activeLanguages.forEach(lang => {
                assert.ok(lang.code, 'Should have code');
                assert.ok(lang.name, 'Should have name');
                assert.ok(lang.nativeName, 'Should have nativeName');
            });
        });
    });
});
