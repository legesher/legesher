/**
 * Narrowing VS Code's ambiguous-character highlighting to the script a project
 * is actually written in (CORE-1978).
 *
 * VS Code flags characters that could be confused with an ASCII character —
 * the Trojan Source defence (CVE-2021-42574). Its confusable table includes
 * U+0627 ARABIC LETTER ALEF (confusable with `l`), U+1200 ETHIOPIC SYLLABLE HA
 * (`U`), U+0131 LATIN SMALL LETTER DOTLESS I (`i`) and the common Cyrillic and
 * Greek letters, so a Legesher file opens with a warning box over most of its
 * identifiers. For those files the heuristic is wrong; on the user's other
 * repositories it is load-bearing.
 *
 * ## `allowedLocales` cannot fix this — the finding that shaped this module
 *
 * The obvious instrument, `editor.unicodeHighlight.allowedLocales`, does not
 * work for the scripts Legesher ships, for two independent reasons. Both were
 * read off microsoft/vscode `src/vs/base/common/strings.ts`:
 *
 * 1. The locale table holds exactly `cs, de, es, fr, it, ja, ko, pl, pt-BR,
 *    qps-ploc, ru, tr, zh-hans, zh-hant` — VS Code's own display languages plus
 *    a pseudo-locale. There is no `ar`, no `am`, no `he`, no `hi`. Unknown keys
 *    are filtered out (`Object.hasOwn(data, l)`) and, if nothing survives, the
 *    code falls back to `_default`. `allowedLocales: {"ar": true}` is therefore
 *    byte-for-byte the same configuration as setting nothing at all.
 * 2. Even a supported locale could not reach the reported character. The
 *    per-locale maps only ever narrow `_default`; the `_common` map is merged in
 *    unconditionally (`mergeMaps(commonMap, languageSpecificMap)`), and U+0627
 *    lives in `_common`. No value of `allowedLocales` can suppress it.
 *
 * `editor.unicodeHighlight.allowedCharacters` is the instrument that does work.
 * It is a hard allowlist, and the per-character test is the part that carries
 * it: in `unicodeTextModelHighlighter.ts`, `shouldHighlightNonBasicASCII`
 * returns "no reason to highlight" for an allowed code point before any other
 * check runs. The candidate-set pass, `getCandidateCodePoints`, also subtracts
 * the allowlist — but last, after the invisible and confusable sets have been
 * unioned, and not at all when `nonBasicASCII` is on, because that branch
 * returns `'allNonBasicAscii'` before the subtraction. The allowance therefore
 * holds in every configuration, but it is the per-character check, not a
 * narrowed candidate set, that makes it hold.
 *
 * ## What this module derives
 *
 * The allowlist is the intersection of the characters the project's own
 * language pack uses with the characters VS Code would flag. That is small and
 * auditable — two characters for Arabic, one for Amharic, twelve for Russian —
 * and it leaves every other script's confusables flagged: a Cyrillic `a` pasted
 * into an Arabic file is still caught. `invisibleCharacters` is never touched,
 * so the bidi/zero-width half of the Trojan Source defence stays on.
 *
 * Deliberately has no `vscode` import: the derivation is pure over (pack,
 * document text) and is unit-testable without an editor host.
 */

/** The translated surface forms for one language, keyed by English source term. */
export interface PackTranslations {
    [englishTerm: string]: string;
}

/**
 * The code points VS Code treats as ambiguous when `allowedLocales` is left
 * alone — the union of its `_common` and `_default` maps, range-encoded.
 *
 * Transcribed from microsoft/vscode `src/vs/base/common/strings.ts`
 * (`AmbiguousCharacters.ambiguousCharacterData`), itself generated from
 * https://github.com/hediet/vscode-unicode-data. `_default` is the maximal
 * per-locale map — every locale map in that table is a subset of it — so this
 * is the largest set a default-configured editor can flag.
 *
 * A stale copy is safe in both directions, which is why vendoring it is
 * acceptable. This set is only ever *intersected* with a pack, so a code point
 * we are missing is simply not allowed and VS Code keeps flagging it, and a
 * code point VS Code has since dropped is allowed to no effect.
 */
const AMBIGUOUS_RANGES =
    'A0 B4 B8 D7 131 17F 184 18D 1A6-1A7 1B7 1BC-1BD 1C0 1C3 21C 222-223 241 251 261 263 ' +
    '269-26A 26F 28B 28F 294 2B9 2BB-2BE 2C2-2C4 2C6 2C8 2CA-2CB 2D0 2D7 2DB-2DC 2F4 2F8 ' +
    '374 37A 37E-37F 384 391-392 395-397 399-39A 39C-39D 39F 3A1 3A4-3A5 3A7 3B1 3B3 3B9 ' +
    '3BD 3BF 3C1 3C3 3C5 3D2 3DC 3E8 3F1-3F3 3F9-3FA 405-406 408 410 412 415 417 41A ' +
    '41C-41E 420-423 425 42C 430-431 433 435 43E 440-441 443 445 455-456 458 461 474-475 ' +
    '4AE-4AF 4BB 4BD 4C0 4CF 4E0 501 50C 51B-51D 54D 54F 555 55A 55D 561 563 566 570 578 ' +
    '57C-57D 581 584-585 589 5C0 5C3 5D5 5D8-5D9 5DF 5E1 5F3 60D 627 647 660-661 665 667 ' +
    '66B 66D 6BE 6C1 6D4-6D5 6F0-6F1 6F5 6F7 701-704 7C0 7CA 7F4-7F5 7FA 903 966 97D 9E6 ' +
    '9EA 9ED A66-A67 A6A A83 AE6 B03 B20 B66 B68 BE6 C02 C66 C82 CE6 D02 D20 D66 D6D D82 ' +
    'E50 ED0 101D 1040 10E7 10FF 1200 12D0 13A0-13A2 13A5 13A9-13AC 13AE 13B3 13B7 13BB ' +
    '13BD 13C0 13C2-13C3 13CE-13CF 13D2 13D4-13D5 13D9-13DA 13DE-13DF 13E2 13E6-13E7 13EE ' +
    '13F3-13F4 1400 142F 1433 1438 144A 144C 146D 146F 1472 148D 14AA 14BF 1541 157C-157D ' +
    '1587 15AF 15B4 15C5 15DE 15EA 15F0 15F7 166D-166E 1680 16B2 16B7 16C1 16CC 16D5-16D6 ' +
    '16EC-16ED 1735 1803 1809 1D04 1D0F 1D11 1D1C 1D20-1D22 1D26 1D83 1D8C 1E9D 1EFF ' +
    '1FBD-1FC0 1FEF 1FFD-1FFE 2000-200A 2010-2013 2018-201B 2024 2028-2029 202F 2032 2035 ' +
    '2039-203A 2041 2043-2044 204E 2053 205A 205F 2102 210A-210E 2110-2113 2115 2119-211D ' +
    '2124 2128 212A 212C-2131 2133-2134 2139 213D 2145-2149 2160 2164 2169 216C-2170 2174 ' +
    '2179 217C-217E 2212 2215-2217 2223 2228 222A 2236 223C 22A4 22C1 22C3 22FF 2373-2374 ' +
    '237A 23FD 2571 2573 2768-2769 276E-276F 2772-2775 2795-2796 27CB 27CD 27D9 292B-292C ' +
    '29F5 29F8-29F9 2A2F 2C85 2C8E 2C92 2C94 2C98 2C9A 2C9E-2C9F 2CA2-2CA6 2CA8 2CAC 2CBA ' +
    '2CC6 2CCA 2CCC 2CD0 2CD2 2D38-2D39 2D4F 2D51 2D54-2D55 2D5D 2E40 2F02-2F03 3007 ' +
    '3014-3015 3033 30A0 30CE 31D3-31D4 4E36 4E3F A4D0-A4D4 A4D6-A4D7 A4D9-A4DA A4DC-A4DD ' +
    'A4DF-A4E3 A4E6-A4E7 A4EA-A4EC A4EE A4F0 A4F2-A4F4 A4F8-A4F9 A4FD A4FF A60E A644 A647 ' +
    'A6DF A6EB A6EF A731 A75A A76A A76E A778 A789 A78C A798-A799 A79F A7AB A7B2-A7B4 AB32 ' +
    'AB35 AB3D AB47-AB48 AB4E AB52 AB5A AB75 AB81 AB83 AB93 ABA9-ABAA ABAF FBA6-FBAD ' +
    'FD3E-FD3F FE30 FE4D-FE4F FE58 FE68 FE8D-FE8E FEE9-FEEC FF01-FF5E FFE8 10282 ' +
    '10286-10287 1028A 10290 10292 10295-10297 1029B 102A0-102A2 102A5 102AB 102B0-102B2 ' +
    '102B4 102CF 102F5 10301-10302 10309 10311 10315 10317 1031A 1031F-10320 10322 10404 ' +
    '10415 1041B 10420 1042C 1043D 10448 104B4 104C2 104CE 104D2 104EA 104F6 10513 10516 ' +
    '10518 1051C-1051D 10525-10527 10A50 114D0 11706 1170A 1170E-1170F 118A0 118A2-118A4 ' +
    '118A6 118A9 118AC 118AE-118AF 118B2 118B5 118B8 118BB-118BC 118C0-118C4 118C6 118C8 ' +
    '118CA 118CC 118D5-118D8 118DC 118E0 118E5-118E6 118E9 118EC 118EF 118F2 16F08 16F0A ' +
    '16F16 16F28 16F35 16F3A-16F3B 16F3F-16F40 16F42-16F43 16F51-16F52 1CCD6-1CCF9 1D114 ' +
    '1D16D 1D206 1D20D 1D20F 1D212-1D213 1D216 1D22A 1D236-1D237 1D23A-1D23B 1D400-1D454 ' +
    '1D456-1D459 1D45B-1D48D 1D48F-1D49C 1D49E-1D49F 1D4A2 1D4A5-1D4A6 1D4A9-1D4AC ' +
    '1D4AE-1D4B9 1D4BB 1D4BD-1D4C1 1D4C3 1D4C5-1D4F5 1D4F7-1D505 1D507-1D50A 1D50D-1D514 ' +
    '1D516-1D51C 1D51E-1D529 1D52B-1D539 1D53B-1D53E 1D540-1D544 1D546 1D54A-1D550 ' +
    '1D552-1D55D 1D55F-1D591 1D593-1D5C5 1D5C7-1D5F9 1D5FB-1D62D 1D62F-1D661 1D663-1D695 ' +
    '1D697-1D6A4 1D6A8-1D6A9 1D6AC-1D6AE 1D6B0-1D6B1 1D6B3-1D6B4 1D6B6 1D6B8 1D6BB-1D6BC ' +
    '1D6BE 1D6C2 1D6C4 1D6CA 1D6CE 1D6D0 1D6D2 1D6D4 1D6D6 1D6E0 1D6E2-1D6E3 1D6E6-1D6E8 ' +
    '1D6EA-1D6EB 1D6ED-1D6EE 1D6F0 1D6F2 1D6F5-1D6F6 1D6F8 1D6FC 1D6FE 1D704 1D708 1D70A ' +
    '1D70C 1D70E 1D710 1D71A 1D71C-1D71D 1D720-1D722 1D724-1D725 1D727-1D728 1D72A 1D72C ' +
    '1D72F-1D730 1D732 1D736 1D738 1D73E 1D742 1D744 1D746 1D748 1D74A 1D754 1D756-1D757 ' +
    '1D75A-1D75C 1D75E-1D75F 1D761-1D762 1D764 1D766 1D769-1D76A 1D76C 1D770 1D772 1D778 ' +
    '1D77C 1D77E 1D780 1D782 1D784 1D78E 1D790-1D791 1D794-1D796 1D798-1D799 1D79B-1D79C ' +
    '1D79E 1D7A0 1D7A3-1D7A4 1D7A6 1D7AA 1D7AC 1D7B2 1D7B6 1D7B8 1D7BA 1D7BC 1D7BE 1D7C8 ' +
    '1D7CA 1D7CE-1D7FF 1E8C7 1E8CB 1EE00 1EE24 1EE64 1EE80 1EE84 1F74C 1F768 1FBF0-1FBF9';

let ambiguousCache: Set<number> | undefined;

/** Expand the range table once, on first use. */
function ambiguousCodePoints(): Set<number> {
    if (ambiguousCache) {
        return ambiguousCache;
    }

    const codePoints = new Set<number>();
    for (const range of AMBIGUOUS_RANGES.split(' ')) {
        if (!range) {
            continue;
        }
        const [start, end] = range.split('-');
        const from = parseInt(start, 16);
        const to = end === undefined ? from : parseInt(end, 16);
        for (let cp = from; cp <= to; cp++) {
            codePoints.add(cp);
        }
    }

    ambiguousCache = codePoints;
    return codePoints;
}

/** Whether VS Code's default configuration flags this code point as confusable. */
export function isAmbiguous(codePoint: number): boolean {
    return ambiguousCodePoints().has(codePoint);
}

/**
 * The characters a language pack writes with that VS Code would flag.
 *
 * Iterated by code point (`for…of` over a string), so an astral character is
 * one entry rather than two surrogate halves — `allowedCharacters` is keyed by
 * whole characters and VS Code reads each key back with `codePointAt(0)`.
 *
 * Returned sorted by code point so the value written into a settings file is
 * stable: an unordered object would produce a spurious diff every time the
 * offer ran.
 */
export function deriveAllowedCharacters(translations: PackTranslations): string[] {
    const allowed = new Set<string>();

    for (const translated of Object.values(translations)) {
        if (typeof translated !== 'string') {
            continue;
        }
        for (const character of translated) {
            const codePoint = character.codePointAt(0);
            if (codePoint !== undefined && codePoint > 0x7f && isAmbiguous(codePoint)) {
                allowed.add(character);
            }
        }
    }

    return [...allowed].sort(
        (a, b) => (a.codePointAt(0) ?? 0) - (b.codePointAt(0) ?? 0)
    );
}

/**
 * Which of `derived` actually occur in this document.
 *
 * The offer is gated on this rather than on the file's language alone. A user
 * whose working language is Arabic still opens ordinary English files, and
 * prompting there would be an offer to fix a problem that is not on screen.
 *
 * Stops as soon as every derived character has been seen. A translated file
 * hits that within the first few lines, which is the case where the scan would
 * otherwise cost the most: the derived sets are tiny (two characters for
 * Arabic, one for Amharic) and the documents are not. The English case still
 * reads the whole text — there is no way to know a character is absent without
 * looking — so the caller memoizes.
 */
export function charactersPresentIn(text: string, derived: readonly string[]): string[] {
    const wanted = new Set(derived);
    const present = new Set<string>();

    for (const character of text) {
        if (wanted.has(character)) {
            present.add(character);
            if (present.size === wanted.size) {
                break;
            }
        }
    }

    return derived.filter(character => present.has(character));
}

/** Whether `allowedCharacters` already permits every character in `derived`. */
export function alreadyAllows(
    allowedCharacters: Readonly<Record<string, unknown>> | undefined,
    derived: readonly string[]
): boolean {
    return derived.every(character => allowedCharacters?.[character] === true);
}

/**
 * The value to write into the workspace settings file.
 *
 * ## Why this is not a merge of the effective value
 *
 * An earlier version of this function merged what `get()` resolves, on the
 * belief that VS Code picks an object-valued setting by precedence and that a
 * workspace value therefore replaces the user's. That is the opposite of what
 * VS Code does. The bundled `@types/vscode` says so directly — "Only `object`
 * value types are merged and all other value types are overridden" — and gives
 * the worked example: a default of `{a: 1, b: 2}` under a user value of
 * `{b: 3, c: 4}` resolves to `{a: 1, b: 3, c: 4}`. The implementation is
 * `ConfigurationModel.mergeContents`, a recursive structural merge down the
 * default → application → user → workspace → folder chain.
 *
 * The user's own allowances therefore survive a workspace write with no help
 * from us, and merging the *effective* value was not merely redundant, it
 * leaked: VS Code's one-click "Exclude {char} from being highlighted" hover
 * action writes to **user** scope, so every character a contributor had ever
 * excluded anywhere was copied into the project's `.vscode/settings.json` and
 * committed to everyone who pulls it. Reading with a resource made it worse in
 * a multi-root workspace, where one folder's private allowances would be
 * promoted to the whole workspace file.
 *
 * ## Why the workspace value is still read
 *
 * Only for idempotence, and only that one scope. A workspace holding an Arabic
 * file and a Russian file offers twice — the session guard is per language —
 * and a bare write would drop the first language's characters and then re-offer
 * for it on every editor switch for the rest of the session. Existing entries
 * are carried through unchanged, including any set to `false`: at workspace
 * scope that is not a no-op but a deliberate revocation of a user-scope
 * allowance, and it is not ours to discard.
 *
 * VS Code makes the same distinction in the same file: `unicodeHighlighter.ts`
 * reads the effective value in `excludeCharFromBeingHighlighted`, which writes
 * to `ConfigurationTarget.USER` where that is harmless, and switches to
 * `inspect(...).user?.value` in `excludeLocaleFromBeingHighlighted` right below
 * it. Read the scope you are about to write.
 */
export function workspaceAllowance(
    workspaceValue: Readonly<Record<string, unknown>> | undefined,
    derived: readonly string[]
): Record<string, unknown> {
    const value: Record<string, unknown> = { ...(workspaceValue ?? {}) };

    for (const character of derived) {
        value[character] = true;
    }

    return value;
}

/** Where a resolved language came from, for a message that has to say so. */
export type LanguageOrigin = 'folder' | 'workspace' | 'detected' | 'user' | 'default';

/**
 * How to describe where the language came from, in a sentence.
 *
 * The offer relaxes a security default in a repository, so it has to say whose
 * language it is acting on. "This project's language pack" was wrong: the pack
 * is chosen by the *reader*, and in an unfamiliar repository the honest
 * sentence is that the file is being read as Arabic because that is the
 * reader's own setting — not because the project said so. Matches the status
 * bar's vocabulary (`origins` in extension.ts) so one concept has one wording.
 */
export function describeLanguageOrigin(origin: LanguageOrigin): string {
    switch (origin) {
        case 'folder':
        case 'workspace':
            return "this project's own setting";
        case 'detected':
            return 'detected from the file contents';
        case 'user':
            return 'your working-language setting';
        case 'default':
            return 'the default working language';
    }
}

/** Everything the offer needs to decide, with no editor in the picture. */
export interface OfferConditions {
    /** Pack characters VS Code would flag; empty means nothing to fix. */
    derived: readonly string[];
    /** Of those, the ones actually in the document on screen. */
    present: readonly string[];
    /** `editor.unicodeHighlight.ambiguousCharacters` as currently resolved. */
    ambiguousCharactersEnabled: boolean;
    /** `editor.unicodeHighlight.allowedCharacters` as currently resolved. */
    allowedCharacters: Readonly<Record<string, unknown>> | undefined;
    /** The user chose "Don't ask again". */
    dismissed: boolean;
    /** Already offered for this language in this session. */
    offeredThisSession: boolean;
    /** There is a folder to write workspace settings into. */
    hasWorkspace: boolean;
    /** The user has granted this workspace trust (`vscode.workspace.isTrusted`). */
    isTrusted: boolean;
}

/**
 * Whether to put the offer on screen.
 *
 * Every clause is a reason *not* to ask, and each one is its own bug if it is
 * missing: asking with nothing to fix, asking about a file that shows no
 * warnings, asking a user who already turned the check off, asking again after
 * being told not to, or asking when the only place we could write is the user's
 * own settings — which would weaken the check on their other repositories, the
 * one outcome this ticket rules out.
 *
 * `isTrusted` is the newest clause and the one with teeth. The manifest
 * declares `untrustedWorkspaces.supported: "limited"`, so this extension
 * activates in Restricted Mode, and VS Code registers
 * `editor.unicodeHighlight.allowedCharacters` with `restricted: true`: a
 * workspace value for it is *ignored* until the user grants trust. Without this
 * clause the offer appears, the write appears to succeed, VS Code discards it,
 * the read-back fails and the user is told a narrower setting is shadowing
 * theirs — sending them to look at folder settings for a problem that is not
 * there. The stronger reason is the plain one: a repository the user has
 * explicitly declined to trust is not a repository we write a relaxed security
 * default into.
 */
export function shouldOfferAllowedCharacters(conditions: OfferConditions): boolean {
    return (
        conditions.derived.length > 0 &&
        conditions.present.length > 0 &&
        conditions.ambiguousCharactersEnabled &&
        !alreadyAllows(conditions.allowedCharacters, conditions.derived) &&
        !conditions.dismissed &&
        !conditions.offeredThisSession &&
        conditions.hasWorkspace &&
        conditions.isTrusted
    );
}

/** `U+0627`-style rendering, for a message that must survive an RTL screenshot. */
export function formatCodePoints(characters: readonly string[]): string {
    return characters
        .map(character => `U+${(character.codePointAt(0) ?? 0).toString(16).toUpperCase().padStart(4, '0')}`)
        .join(', ');
}
