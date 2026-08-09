/**
 * Content-based language detection (CORE-1729).
 *
 * Infers which Legesher language a file is written in by matching its tokens
 * against the installed language packs, so a translated file works without the
 * user first pointing a setting at the right language.
 *
 * Deliberately has no `vscode` import: detection is pure over (text, packs) and
 * is unit-testable without an editor host.
 *
 * Detection is conservative by design. A wrong guess silently swaps the user's
 * language, which is worse than not guessing, so weak or ambiguous evidence
 * returns null and the caller falls back to the configured language.
 */

/** The translated surface forms for one language, keyed by English source term. */
export interface PackTranslations {
    [englishTerm: string]: string;
}

/** The set of tokens that count as evidence for one language. */
export interface PackVocabulary {
    language: string;
    terms: Set<string>;
}

export interface DetectionResult {
    language: string;
    /** Number of distinct vocabulary terms found in the document. */
    score: number;
    runnerUp?: { language: string; score: number };
}

export interface DetectOptions {
    /** Minimum distinct term hits before a language is considered at all. */
    minHits?: number;
    /** How far the winner must outscore the runner-up to be trusted. */
    minMargin?: number;
}

const DEFAULT_MIN_HITS = 2;

/**
 * How far the winner must outscore the runner-up.
 *
 * Measured against all 50 translated fixtures: the tightest genuine margin is 4
 * (id, ms, pt), so 3 leaves a full point of headroom while refusing the cases
 * that actually go wrong. Related-language families overlap heavily — a Spanish
 * file scores 4 for Catalan and 3 for Spanish, and a margin of 1 confidently
 * returns Catalan. Families at risk include ca/es, no/da/sv and bs/hr/sr.
 */
const DEFAULT_MIN_MARGIN = 3;

/** The language packs are keyed by; never itself a detection result. */
export const SOURCE_LANGUAGE = 'en';

/**
 * Unicode-aware token pattern.
 *
 * Packs cover non-Latin scripts, so \w is not sufficient. Underscore is treated
 * as part of a token so `vordrucken_y` does not read as the term `drucken`.
 *
 * Combining marks (\p{M}) are part of a token, not separators. Brahmic and
 * SE-Asian scripts write vowels as marks, so without this `সংজ্ঞা` shatters into
 * ["স", "জ", "ঞ"] and those languages never match. Zero-width joiner and
 * non-joiner are included for the same reason: Sinhala conjuncts are written
 * with ZWJ, which would otherwise split a term mid-word.
 *
 * This mirrors Python's own identifier rules (XID_Start / XID_Continue), which
 * likewise treat marks as continuation characters.
 */
const TOKEN_PATTERN = /[\p{L}\p{N}\p{M}_‌‍]+/gu;

/**
 * Build the evidence vocabulary for one language from its pack translations.
 *
 * Entries a pack leaves untranslated (value identical to the English term) are
 * dropped. Packs are incomplete, and keeping those would make every English
 * file match every language. This also means the English pack, whose values all
 * equal their keys, correctly yields an empty vocabulary.
 */
export function buildVocabulary(
    language: string,
    translations: PackTranslations
): PackVocabulary {
    const terms = new Set<string>();

    for (const [englishTerm, translatedTerm] of Object.entries(translations)) {
        if (!translatedTerm || translatedTerm === englishTerm) {
            continue;
        }
        terms.add(translatedTerm);
    }

    return { language, terms };
}

/**
 * Build the vocabulary for the source language itself, from the English terms
 * the packs are keyed by.
 *
 * Detection cannot simply exclude English. Packs translate some keywords to
 * single letters or common short words — `cs` maps `and`→`a` and `with`→`s`,
 * `ca` maps `is`→`es`, `nl` maps `or`→`of` — all of which occur constantly in
 * ordinary English code. Scoring only translated terms, a plain English file
 * accumulates hits for those languages and is confidently misidentified.
 *
 * Making English a candidate turns it into the null hypothesis: English code
 * scores heavily for English (`def`, `return`, `for`, `print`), so no
 * translated language can clear the margin, and detection correctly declines.
 */
export function buildSourceVocabulary(translations: PackTranslations): PackVocabulary {
    return { language: SOURCE_LANGUAGE, terms: new Set(Object.keys(translations)) };
}

/**
 * Build detection vocabularies for every language in a pack translation map,
 * plus the source language as the null hypothesis (see buildSourceVocabulary).
 *
 * Languages whose vocabulary ends up empty are dropped: they contribute no
 * evidence and would otherwise sit in the results as permanent zero-scorers.
 * That is what removes the English *pack*, which maps every term to itself —
 * the English candidate is rebuilt from the keys instead.
 */
export function buildVocabularies(
    translationsByLanguage: { [language: string]: PackTranslations }
): PackVocabulary[] {
    const vocabularies = Object.entries(translationsByLanguage)
        .filter(([language]) => language !== SOURCE_LANGUAGE)
        .map(([language, translations]) => buildVocabulary(language, translations))
        .filter(vocab => vocab.terms.size > 0);

    // Union of every pack's keys: packs may cover slightly different terms.
    const sourceTerms: PackTranslations = {};
    for (const translations of Object.values(translationsByLanguage)) {
        for (const englishTerm of Object.keys(translations)) {
            sourceTerms[englishTerm] = englishTerm;
        }
    }
    if (Object.keys(sourceTerms).length > 0) {
        vocabularies.push(buildSourceVocabulary(sourceTerms));
    }

    return vocabularies;
}

/**
 * Remove comments and string literals, leaving the code positions.
 *
 * Keyword evidence must come from code, not prose. A Legesher user writes
 * comments in their own language, so prose is ordinary input rather than an
 * edge case — and left in, it outvotes the code it describes: English source
 * with heavy Spanish comments scores `es` 14 against the real packs and the
 * language server is switched to Spanish for a file that has no Spanish code in
 * it (CORE-1765).
 *
 * A single scan rather than regexes, so a `#` inside a string is not mistaken
 * for a comment and a quote inside a comment does not open a string. It is not
 * a Python parser and does not need to be: the scorer only needs the code-ish
 * remainder, and detection already declines when evidence is thin.
 */
export function stripProse(text: string): string {
    const IDENTIFIER_PREFIX = /[A-Za-z]$/;
    let out = '';
    let i = 0;

    while (i < text.length) {
        const char = text[i];

        // Comment: skip to end of line, leaving the newline in place.
        if (char === '#') {
            while (i < text.length && text[i] !== '\n') {
                i++;
            }
            continue;
        }

        if (char === '"' || char === "'") {
            // Drop any string prefix already emitted (f, r, b, rb, …) so it is
            // not left behind as a stray one-character token — packs do contain
            // single-letter translations.
            while (IDENTIFIER_PREFIX.test(out)) {
                out = out.slice(0, -1);
            }

            const triple = char.repeat(3);
            if (text.startsWith(triple, i)) {
                const end = text.indexOf(triple, i + 3);
                i = end === -1 ? text.length : end + 3;
            } else {
                i++;
                while (i < text.length) {
                    if (text[i] === '\\') {
                        i += 2;
                        continue;
                    }
                    if (text[i] === char || text[i] === '\n') {
                        i++;
                        break;
                    }
                    i++;
                }
            }
            // Stand in for the removed literal so neighbouring tokens stay apart.
            out += ' ';
            continue;
        }

        out += char;
        i++;
    }

    return out;
}

/**
 * Detect which language `text` is written in.
 *
 * Returns null when no language clears `minHits`, or when the leader fails to
 * beat the runner-up by `minMargin`.
 */
export function detectLanguage(
    text: string,
    vocabularies: PackVocabulary[],
    options: DetectOptions = {}
): DetectionResult | null {
    const minHits = options.minHits ?? DEFAULT_MIN_HITS;
    const minMargin = options.minMargin ?? DEFAULT_MIN_MARGIN;

    const tokens = new Set(stripProse(text).match(TOKEN_PATTERN) ?? []);
    if (tokens.size === 0) {
        return null;
    }

    // Score each language by how many distinct vocabulary terms appear. Distinct
    // rather than total occurrences, so one keyword in a loop is not mistaken
    // for broad evidence.
    const scores = vocabularies
        .map(vocab => {
            let score = 0;
            for (const term of vocab.terms) {
                if (tokens.has(term)) {
                    score++;
                }
            }
            return { language: vocab.language, score };
        })
        .sort((a, b) => b.score - a.score);

    const winner = scores[0];
    if (!winner || winner.score < minHits) {
        return null;
    }

    const runnerUp = scores[1];
    if (runnerUp && winner.score - runnerUp.score < minMargin) {
        return null;
    }

    // The source language winning means the file is ordinary English Python.
    // That is a successful decision, not a detection: report nothing and let the
    // caller keep the configured language.
    if (winner.language === SOURCE_LANGUAGE) {
        return null;
    }

    return {
        language: winner.language,
        score: winner.score,
        runnerUp: runnerUp ? { language: runnerUp.language, score: runnerUp.score } : undefined,
    };
}
