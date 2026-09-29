/**
 * The language roles, named, and the rules that relate them (CORE-1760).
 *
 * `legesher.targetLanguage` used to mean two things at once: the language a
 * file is written in (what the server parses by) and the language the user
 * wants to read in (what hover and the UI render). Those coincide only when
 * you open your own files; the moment you open someone else's, every surface
 * built on the two-slot model gets the wrong answer. This module names the
 * roles so nothing has to conflate them again:
 *
 * - **Canonical** — the terms Python itself defines: English. The pivot every
 *   mapping routes through. Carried as `sourceLanguage`; not a user choice.
 * - **File language** — the language a given file is written in. Detected, or
 *   declared per file.
 * - **Working language** — the language the user reads and writes in right
 *   now. What hover and the UI should render into.
 * - **Known languages** — the set of languages the user reads comfortably.
 *   Orders the picker, and decides when the product should say anything at
 *   all: a Farsi file is only noteworthy to someone who does not read Farsi.
 *
 * Deliberately has no `vscode` import: every rule here is pure over values the
 * caller has already read, so it is unit-testable without an editor host —
 * the same bargain `settingsScope.ts` makes.
 */

import { type InspectedSetting, type SettingScope } from './settingsScope';

/** The role vocabulary, resolved for one document at one moment. */
export interface ResolvedLanguages {
    /** Canonical: the language the project's code is stored in. */
    sourceLanguage: string;
    /** The language this file is written in — detected, or configured. */
    fileLanguage: string;
    /** The language the user reads and writes in right now. */
    workingLanguage: string;
    /**
     * Compatibility slot for servers that predate the role split; mirrors
     * `fileLanguage`, which is what the old single slot actually carried —
     * the server used it to pick the pack it parses the file with.
     *
     * @deprecated Read `fileLanguage` and `workingLanguage` instead.
     */
    targetLanguage: string;
}

/**
 * Assemble the initialization payload from the three real roles.
 *
 * The file and working languages travel as separate slots, on purpose — the
 * whole defect this vocabulary exists to fix is the client collapsing them
 * into one value before the server ever sees them (CORE-1760). The deprecated
 * `targetLanguage` slot is filled from the file language so a server built
 * against the old protocol keeps parsing files correctly.
 */
export function buildResolvedLanguages(
    sourceLanguage: string,
    fileLanguage: string,
    workingLanguage: string
): ResolvedLanguages {
    return {
        sourceLanguage,
        fileLanguage,
        workingLanguage,
        targetLanguage: fileLanguage,
    };
}

/**
 * The languages a server is started with: the configured ones only (CORE-1976).
 *
 * A file language resolved for one document, typically by detection, is not
 * part of the session. It travels per document, in a `legesher/documentLanguage`
 * notification, so files detected in different languages no longer change what
 * the server was started with, and switching between them no longer restarts
 * it. What remains is what the server still reads only at initialize: the
 * canonical language, the working language, and the file language to assume
 * for any document the client has not named, which is the working language.
 *
 * Takes the configuration rather than a resolution on purpose: a detected
 * language has nowhere to go here.
 */
export function sessionLanguagesOf(config: {
    sourceLanguage: string;
    workingLanguage: string;
}): ResolvedLanguages {
    return buildResolvedLanguages(
        config.sourceLanguage,
        config.workingLanguage,
        config.workingLanguage
    );
}

/** The scopes a value can be explicitly set at, narrowest first. */
const SCOPE_ORDER: ReadonlyArray<[keyof InspectedSetting<string>, SettingScope]> = [
    ['workspaceFolderValue', 'folder'],
    ['workspaceValue', 'workspace'],
    ['globalValue', 'user'],
];

/**
 * Resolve the working language across both setting names, and say which scope
 * supplied it.
 *
 * Two orderings are in play and they are not interchangeable:
 *
 * - **Scope precedence comes first.** VS Code resolves folder > workspace >
 *   user > default, and a deprecated alias does not get to opt out of that. A
 *   project that pins `legesher.targetLanguage` in `.vscode/settings.json` —
 *   the exact shape CORE-1776 was about — must still beat the reader's own
 *   global preference, whichever name that preference is written under.
 * - **Key priority applies within a scope.** At the same scope,
 *   `workingLanguage` beats `targetLanguage`, so a migrated configuration is
 *   never overridden by the setting it migrated from.
 *
 * Resolving by key first inverts the first rule: a global `workingLanguage`
 * would silently outrank a workspace `targetLanguage`, so every project
 * shipping the old key would quietly resolve to the reader's own language
 * once anything had written the new key globally — which the language picker
 * does on its first use in an unpinned project.
 *
 * Reads `inspect()` rather than `get()` throughout: `get()` folds in the
 * registered default, which would shadow the alias for exactly the users the
 * alias exists for.
 */
export function resolveWorkingLanguage(
    working: InspectedSetting<string> | undefined,
    deprecated: InspectedSetting<string> | undefined
): { language: string; scope: SettingScope } {
    for (const [key, scope] of SCOPE_ORDER) {
        // Within one scope the new name wins, then the alias. An empty string
        // is not a language: a cleared settings field must fall through to the
        // alias beside it, and then to the next scope, rather than resolving
        // to `''` and taking every later lookup with it.
        const value = [working?.[key], deprecated?.[key]].find(
            candidate => candidate !== undefined && candidate !== ''
        );
        if (value !== undefined) {
            return { language: value, scope };
        }
    }
    return { language: 'en', scope: 'default' };
}

/**
 * Resolve the known-language set, seeding it when nothing usable is configured.
 *
 * An unset or empty set resolves to the working language rather than to
 * nothing: someone necessarily reads the language they work in, and a set
 * that could resolve empty would make "is this file's language known?" answer
 * no for everything — turning every file into a mismatch on first run, before
 * the user has configured anything (CORE-1760).
 *
 * The parameter is typed `unknown` because that is what a settings file can
 * actually contain. VS Code neither validates a hand-edited value against the
 * declared schema on write nor coerces it on read, so `"knownLanguages": "pt"`
 * arrives here as a string. Assuming an array made that a `TypeError` on the
 * activation path, which froze every later language change into a silent
 * no-op — the exact silent-success failure this subsystem keeps producing.
 * Anything that is not an array of usable codes falls back to the seed.
 */
export function resolveKnownLanguages(
    configured: unknown,
    workingLanguage: string
): string[] {
    const cleaned = (Array.isArray(configured) ? configured : []).filter(
        (code): code is string => typeof code === 'string' && code.length > 0
    );
    return cleaned.length > 0 ? Array.from(new Set(cleaned)) : [workingLanguage];
}

/**
 * Whether a file's language warrants saying anything at all.
 *
 * The known set is what makes mismatch signalling mean something: without it,
 * a file in a language the user reads and a file in one they do not look
 * identical, and the product either nags about both or stays silent about
 * both. A file already in a known language just works — no signal, no offer.
 */
export function isUnfamiliarFileLanguage(
    fileLanguage: string,
    workingLanguage: string,
    knownLanguages: string[]
): boolean {
    return fileLanguage !== workingLanguage && !knownLanguages.includes(fileLanguage);
}

/**
 * Split a language list into known languages and the rest, both in the input
 * list's order.
 *
 * The picker shows the known partition first, under a separator: on a
 * 51-language list that is the difference between a picker you scan and one
 * you search.
 */
export function partitionByKnown<T extends { code: string }>(
    languages: T[],
    knownLanguages: string[]
): { known: T[]; others: T[] } {
    const knownSet = new Set(knownLanguages);
    return {
        known: languages.filter(lang => knownSet.has(lang.code)),
        others: languages.filter(lang => !knownSet.has(lang.code)),
    };
}

/**
 * The identity a running server is keyed by: everything it read at initialize.
 *
 * The server reads its languages once, in `on_initialize`, so a change to
 * *any* of them requires a restart — keying on fewer slots than the server
 * consumes is how a change silently did nothing (CORE-1754). The working
 * language appears only when it differs from the file language, which keeps
 * the identity `source->file` for the common own-files case. The extension
 * keys the running server on `sessionLanguagesOf`, where the two are the same,
 * because a document's own language is sent per document (CORE-1976).
 */
export function serverIdentityOf(languages: ResolvedLanguages): string {
    const base = `${languages.sourceLanguage}->${languages.fileLanguage}`;
    return languages.workingLanguage === languages.fileLanguage
        ? base
        : `${base}+${languages.workingLanguage}`;
}

/**
 * The file language named by a server identity, for messages that name what
 * the user is not getting.
 */
export function identityFileLanguage(identity: string): string {
    return identity.split('->')[1]?.split('+')[0] ?? identity;
}
