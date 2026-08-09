/**
 * Unit tests for content-based language detection (CORE-1729)
 *
 * Detection infers which Legesher language a file is written in by matching
 * its tokens against the installed language packs. It must be conservative:
 * when the signal is weak or ambiguous it returns null so the caller can fall
 * back to the configured language rather than guessing wrong.
 */

import * as assert from 'assert';
import {
    buildSourceVocabulary,
    buildVocabularies,
    buildVocabulary,
    detectLanguage,
} from '../../src/languageDetection';

// Minimal slices of real pack data. Keys are the English source terms,
// values are the translated surface forms that appear in translated code.
const DE_TRANSLATIONS = {
    def: 'definit',
    for: 'für',
    in: 'enthält',
    if: 'wenn',
    return: 'zurückgeben',
    print: 'drucken',
    len: 'dieLänge',
    None: 'Nichts',
    True: 'wahr',
    False: 'Falsch',
};

const ES_TRANSLATIONS = {
    def: 'definir',
    for: 'para',
    in: 'en',
    if: 'si',
    return: 'retornar',
    print: 'imprimir',
    len: 'longitud',
    None: 'Nada',
    True: 'verdadero',
    False: 'falso',
};

const GERMAN_SOURCE = `
definit greet(name):
    message = f"Hallo, {name}!"
    drucken(message)
    zurückgeben message

definit main():
    für i enthält Bereich(1, 5):
        drucken(i)
`;

const ENGLISH_SOURCE = `
def greet(name):
    message = f"Hello, {name}!"
    print(message)
    return message

def main():
    for i in range(1, 5):
        print(i)
`;

describe('Language Detection (CORE-1729)', () => {
    describe('buildVocabulary', () => {
        it('collects the translated surface forms for a language', () => {
            const vocab = buildVocabulary('de', DE_TRANSLATIONS);

            assert.strictEqual(vocab.language, 'de');
            assert.ok(vocab.terms.has('drucken'), 'should contain translated builtin');
            assert.ok(vocab.terms.has('definit'), 'should contain translated keyword');
        });

        it('drops terms a pack leaves untranslated', () => {
            // Packs are incomplete: some entries are identical to English.
            // Those must not count as evidence, or every English file matches.
            const partial = { def: 'definir', print: 'print', return: 'return' };

            const vocab = buildVocabulary('es', partial);

            assert.ok(vocab.terms.has('definir'), 'translated term is kept');
            assert.ok(!vocab.terms.has('print'), 'untranslated term is dropped');
            assert.ok(!vocab.terms.has('return'), 'untranslated term is dropped');
        });
    });

    describe('buildVocabularies', () => {
        it('builds one vocabulary per language plus English as the null hypothesis', () => {
            // The English pack maps every term to itself and yields no evidence
            // terms, so it is dropped as a pack — but English is re-added as a
            // candidate built from the keys, so plain English code has something
            // to score for and cannot be misread as a translated language.
            const vocabs = buildVocabularies({
                de: DE_TRANSLATIONS,
                es: ES_TRANSLATIONS,
                en: { def: 'def', print: 'print' },
            });

            const languages = vocabs.map(v => v.language).sort();
            assert.deepStrictEqual(languages, ['de', 'en', 'es']);

            const english = vocabs.find(v => v.language === 'en')!;
            assert.ok(english.terms.has('def'), 'English candidate holds source terms');
            assert.ok(english.terms.has('return'), 'terms are unioned across packs');
            assert.strictEqual(
                vocabs.filter(v => v.language === 'en').length,
                1,
                'English must not be duplicated by the identity pack'
            );
        });
    });

    describe('detectLanguage', () => {
        const vocabs = [
            buildVocabulary('de', DE_TRANSLATIONS),
            buildVocabulary('es', ES_TRANSLATIONS),
        ];

        it('identifies the language a file is written in', () => {
            const result = detectLanguage(GERMAN_SOURCE, vocabs);

            assert.ok(result, 'should detect a language');
            assert.strictEqual(result!.language, 'de');
        });

        it('returns null for plain English Python', () => {
            // English is the source language, never a detection target.
            const result = detectLanguage(ENGLISH_SOURCE, vocabs);

            assert.strictEqual(result, null);
        });

        it('returns null for English code that collides with short pack terms', () => {
            // Real packs translate keywords to single letters and common short
            // words (cs: and->a, with->s; nl: or->of; ca: is->es), which occur
            // constantly in ordinary English code. Counting only translated
            // terms, such a file scores for those languages and detects wrongly.
            // English has to compete as a candidate, not be excluded.
            const czech = buildVocabulary('cs', {
                and: 'a',
                with: 's',
                def: 'def_cs',
                print: 'tisk',
            });
            const english = buildSourceVocabulary({
                and: 'a', with: 's', def: 'def_cs', print: 'tisk',
                return: 'x', for: 'y',
            });

            const englishCode = 'def add(a, b):\n    s = a + b\n    return s\n';

            const result = detectLanguage(englishCode, [czech, english]);

            assert.strictEqual(result, null);
        });

        it('returns null when two related languages are within the margin', () => {
            // Romance packs share most surface forms: a Spanish file scores 4 for
            // Catalan and 3 for Spanish, so a one-point lead picks the wrong one.
            // Related-language families (ca/es, no/da/sv, bs/hr/sr) need a real
            // gap, not a single term, before detection commits.
            const catalan = buildVocabulary('ca', {
                def: 'definir', if: 'si', return: 'retornar',
                print: 'imprimir', len: 'longitud',
            });
            const spanish = buildVocabulary('es', {
                def: 'definir', if: 'si', return: 'retornar',
                print: 'imprimir', len: 'largo',
            });

            // Four shared terms plus one Catalan-only term: ca 5, es 4. A single
            // extra hit must not decide between two plausible languages.
            const spanishCode =
                'definir saludar(nombre):\n    retornar f"Hola"\n\nsi x:\n' +
                '    imprimir(longitud(x))\n';

            const result = detectLanguage(spanishCode, [catalan, spanish]);

            assert.strictEqual(result, null);
        });

        it('ignores prose in comments', () => {
            // A Legesher user writes comments in their own language, so prose is
            // ordinary input. Counting it as keyword evidence lets a comment
            // block outvote the code it describes: English code with heavy
            // Spanish comments scored es=14 against the real packs.
            const spanishProse = [
                '# definir la funcion para imprimir el resultado',
                '# si el valor es nada, retornar falso',
                '# para cada elemento en la lista, continuar',
                'def f(x):',
                '    return x',
                ''
            ].join('\n');

            const result = detectLanguage(spanishProse, vocabs);

            assert.strictEqual(result, null);
        });

        it('ignores prose in string literals and docstrings', () => {
            const withDocstring = [
                'definit greet(name):',
                '    """This function prints a greeting and returns it."""',
                '    drucken(name)',
                '    zurückgeben name',
                ''
            ].join('\n');

            // The German code must still win; the English docstring must not
            // count against it.
            const result = detectLanguage(withDocstring, vocabs);

            assert.ok(result, 'should still detect the code language');
            assert.strictEqual(result!.language, 'de');
        });

        it('returns null when there is too little evidence', () => {
            // A single hit is not enough to switch a user's language.
            const result = detectLanguage('drucken(1)\n', vocabs);

            assert.strictEqual(result, null);
        });

        it('returns null when two languages tie', () => {
            // Ambiguous input must fall back rather than pick arbitrarily.
            const ambiguous = 'definit x\ndefinir y\ndrucken(1)\nimprimir(2)\n';

            const result = detectLanguage(ambiguous, vocabs);

            assert.strictEqual(result, null);
        });

        it('matches whole tokens only', () => {
            // 'drucken' inside a longer identifier is not evidence of German.
            const embedded = 'ausdruckenX = 1\nvordrucken_y = 2\nabdrucken_z = 3\n';

            const result = detectLanguage(embedded, vocabs);

            assert.strictEqual(result, null);
        });

        it('counts each distinct term once, not per occurrence', () => {
            // One keyword repeated many times is still one piece of evidence.
            const repeated = 'drucken(1)\ndrucken(2)\ndrucken(3)\ndrucken(4)\n';

            const result = detectLanguage(repeated, vocabs);

            assert.strictEqual(result, null);
        });

        it('tokenizes scripts written with combining marks', () => {
            // Brahmic and SE-Asian scripts write vowels as combining marks
            // (Unicode category M). A token pattern of letters and digits alone
            // shatters সংজ্ঞা into fragments and detects nothing.
            const bengali = buildVocabulary('bn', {
                def: 'সংজ্ঞা',
                for: 'জন্য',
                if: 'যদি',
                return: 'ফেরত',
                print: 'মুদ্রণ',
            });

            const bengaliSource = 'সংজ্ঞা greet(নাম):\n    মুদ্রণ(নাম)\n    ফেরত নাম\n';

            const result = detectLanguage(bengaliSource, [bengali, ...vocabs]);

            assert.ok(result, 'should detect a mark-using script');
            assert.strictEqual(result!.language, 'bn');
        });

        it('reports the winning score and the runner-up', () => {
            const result = detectLanguage(GERMAN_SOURCE, vocabs);

            assert.ok(result, 'should detect a language');
            assert.ok(result!.score >= 2, 'winner should have real evidence');
            assert.ok(
                result!.runnerUp === undefined || result!.score > result!.runnerUp.score,
                'winner must outscore the runner-up'
            );
        });
    });
});
