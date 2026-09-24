import * as vscode from 'vscode';
import { Logger } from './logger';
import { getLanguageName } from './config';
import { getTranslationsForLanguage } from './languagePackLoader';
import {
    alreadyAllows,
    charactersPresentIn,
    deriveAllowedCharacters,
    describeLanguageOrigin,
    formatCodePoints,
    shouldOfferAllowedCharacters,
    workspaceAllowance,
    type LanguageOrigin,
} from './unicodeHighlight';

/**
 * The workspace-scoped offer to stop VS Code flagging a project's own script
 * as confusable (CORE-1978).
 *
 * Deliberately an offer and deliberately workspace-scoped. The extension could
 * ship `contributes.configurationDefaults` and turn the check off for every
 * Python file every user of this extension ever opens — which would remove a
 * real Trojan Source protection from repositories that have nothing to do with
 * Legesher. The distinction the editor cannot make and we can is that *this*
 * project is written in a script whose letters are not impersonations, and the
 * place to record that is this project's settings.
 *
 * What is written is `editor.unicodeHighlight.allowedCharacters`, carrying only
 * the characters the resolved language's pack uses that VS Code would otherwise
 * flag. Nothing the user has allowed for themselves is copied into the project
 * file: VS Code merges object-valued settings across scopes, so a user-scope
 * allowance survives a workspace write on its own (see `workspaceAllowance`).
 * `ambiguousCharacters` is never turned off, so every *other* script's
 * confusables keep their warning; `invisibleCharacters` is never touched at
 * all, so the zero-width and bidi half of the defence is untouched.
 *
 * The offer never appears in an untrusted workspace. That is both the honest
 * behaviour — we do not relax a security default in a repository the user has
 * declined to trust — and the only working one, since VS Code registers the
 * setting `restricted: true` and discards a workspace value for it until trust
 * is granted.
 *
 * The derivation itself lives in `unicodeHighlight.ts`, with the evidence for
 * why `allowedLocales` is not the instrument it looks like.
 */

const DISMISSED_KEY = 'legesher.unicodeHighlight.dontAskAgain';

const ACTIONS = {
    allow: 'Allow Them',
    notNow: 'Not Now',
    dontAskAgain: "Don't Ask Again",
} as const;

/**
 * Languages already offered in this window.
 *
 * Without it, declining would re-prompt on the next editor switch — the offer
 * runs on the same sync that repaints the status bar, which fires constantly.
 * Module-level rather than persisted on purpose: "Not Now" should mean this
 * session, and only "Don't Ask Again" should outlive the window.
 */
const offeredThisSession = new Set<string>();

/** Derivations already computed, keyed by language. */
const derivedByLanguage = new Map<string, readonly string[]>();

/** How many documents the presence memo remembers. Mirrors `DetectionCache`. */
const MAX_PRESENCE_ENTRIES = 50;

interface PresenceEntry {
    version: number;
    language: string;
    present: readonly string[];
}

/**
 * Which derived characters each document contains, memoized on (uri, version).
 *
 * The scan is a pure function of the text, and VS Code advances `version`
 * exactly when the text changes, so a hit can only be returned for the bytes
 * that produced it — the same bargain `DetectionCache` makes for detection
 * (CORE-1776). The language is part of the key too: the derived set it is
 * scanned against is a property of the pack, so the same bytes give different
 * answers for different working languages.
 *
 * Without this, an English file re-scanned forever. A file with no derived
 * characters present is never added to `offeredThisSession` — correctly, there
 * was nothing to offer — so nothing marked it as checked, and every editor
 * switch back to it read the whole document again.
 */
const presenceByDocument = new Map<string, PresenceEntry>();

/**
 * Forget one document's presence entry.
 *
 * Required when a document closes, for the reason `DetectionCache.forget`
 * exists: VS Code restarts a reopened document's version at 1, so an entry left
 * behind can be matched by a *different* revision of the same file — one edited
 * on disk while it was closed — and answer for text that is no longer there.
 */
export function forgetUnicodeHighlightPresence(uri: string): void {
    presenceByDocument.delete(uri);
}

/** Configuration handle for the one section this module reads and writes. */
function highlightConfig(resource?: vscode.Uri): vscode.WorkspaceConfiguration {
    return vscode.workspace.getConfiguration('editor.unicodeHighlight', resource);
}

/**
 * The pack characters VS Code would flag, computed once per language.
 *
 * Memoized because the caller runs on every editor switch and the answer is a
 * property of the pack, which does not change while the window is open. Thirty-
 * four of the fifty-one packs derive an empty set, and that emptiness is the
 * cheapest early exit there is.
 */
function derivedFor(extensionPath: string, language: string): readonly string[] {
    const cached = derivedByLanguage.get(language);
    if (cached) {
        return cached;
    }

    const translations = getTranslationsForLanguage(language, extensionPath);
    const derived = translations ? deriveAllowedCharacters(translations) : [];
    derivedByLanguage.set(language, derived);
    return derived;
}

/** `charactersPresentIn` for a document, computed once per (uri, version, language). */
function presentIn(
    document: vscode.TextDocument,
    language: string,
    derived: readonly string[]
): readonly string[] {
    const key = document.uri.toString();
    const cached = presenceByDocument.get(key);
    if (cached && cached.version === document.version && cached.language === language) {
        // Reinsert so recency, not first sight, decides what gets evicted.
        presenceByDocument.delete(key);
        presenceByDocument.set(key, cached);
        return cached.present;
    }

    const present = charactersPresentIn(document.getText(), derived);
    presenceByDocument.delete(key);
    presenceByDocument.set(key, { version: document.version, language, present });

    while (presenceByDocument.size > MAX_PRESENCE_ENTRIES) {
        const oldest = presenceByDocument.keys().next().value;
        if (oldest === undefined) {
            break;
        }
        presenceByDocument.delete(oldest);
    }

    return present;
}

/**
 * Offer to allow this file's own script, if the offer is warranted.
 *
 * Never throws and never blocks: it rides the language sync, and a failure here
 * must not take a language change down with it.
 */
export async function maybeOfferUnicodeHighlightAllowance(
    context: vscode.ExtensionContext,
    document: vscode.TextDocument,
    language: string,
    origin: LanguageOrigin
): Promise<void> {
    try {
        // A cheap prefilter, not the decision. Everything here is also a clause
        // of shouldOfferAllowedCharacters below, which stays the authority; the
        // point is to avoid reading the pack and scanning the document on every
        // editor switch for the overwhelmingly common case of nothing to do.
        const dismissed = context.globalState.get<boolean>(DISMISSED_KEY, false);
        const hasWorkspace = (vscode.workspace.workspaceFolders?.length ?? 0) > 0;
        const isTrusted = vscode.workspace.isTrusted;
        if (dismissed || !hasWorkspace || !isTrusted || offeredThisSession.has(language)) {
            return;
        }

        const derived = derivedFor(context.extensionPath, language);
        if (derived.length === 0) {
            return;
        }

        const config = highlightConfig(document.uri);
        const present = presentIn(document, language, derived);

        const shouldOffer = shouldOfferAllowedCharacters({
            derived,
            present,
            ambiguousCharactersEnabled: config.get<boolean>('ambiguousCharacters', true),
            allowedCharacters: config.get<Record<string, unknown>>('allowedCharacters'),
            dismissed,
            offeredThisSession: offeredThisSession.has(language),
            hasWorkspace,
            isTrusted,
        });

        if (!shouldOffer) {
            return;
        }

        offeredThisSession.add(language);
        await prompt(context, document.uri, language, origin, derived, present);
    } catch (error) {
        // Logged, not surfaced. Nothing here is load-bearing for the editor:
        // the worst outcome of failing silently is the warnings staying on,
        // which is the state the user is already in.
        Logger.warn('Could not evaluate the Unicode highlighting offer', error);
    }
}

async function prompt(
    context: vscode.ExtensionContext,
    resource: vscode.Uri,
    language: string,
    origin: LanguageOrigin,
    derived: readonly string[],
    present: readonly string[]
): Promise<void> {
    const languageName = getLanguageName(language);

    // Names the language and where it came from. The earlier wording, "this
    // project's language pack", was wrong in the case that matters: the pack is
    // the *reader's* working language, so in an unfamiliar repository the
    // message claimed the project's authority for the reader's own setting —
    // exactly backwards for someone deciding whether to relax a security
    // default in code they have not read.
    //
    // Code points rather than the characters themselves: the message is read in
    // a notification that does not isolate bidi runs, and an Arabic letter
    // dropped into an English sentence reorders the rest of it on screen.
    const action = await vscode.window.showInformationMessage(
        `Legesher: VS Code flags ${formatCodePoints(present)} in this file as confusable ` +
        `with Latin letters. The file is being read as ${languageName} ` +
        `(${describeLanguageOrigin(origin)}). Allow the ${derived.length} ` +
        `${languageName} character${derived.length === 1 ? '' : 's'} the ${languageName} ` +
        "language pack uses, in this workspace's settings? Invisible-character and " +
        'bidi detection stays on.',
        ACTIONS.allow,
        ACTIONS.notNow,
        ACTIONS.dontAskAgain
    );

    if (action === ACTIONS.dontAskAgain) {
        await context.globalState.update(DISMISSED_KEY, true);
        Logger.info('Unicode highlighting: user opted out of the allowance offer');
        return;
    }

    if (action !== ACTIONS.allow) {
        Logger.info(`Unicode highlighting: offer deferred for ${language}`);
        return;
    }

    await applyAllowance(resource, language, languageName, derived);
}

/**
 * Write the allowance at workspace scope and confirm it actually took.
 *
 * What is written is the derived set and the workspace file's own previous
 * contents — never the effective value. `workspaceAllowance` carries the
 * evidence; the short version is that VS Code merges object-valued settings
 * across scopes, so writing the effective value would have copied the user's
 * private allowances into a file that gets committed.
 *
 * `inspect()` rather than `get()` for the read, and `workspaceValue` rather
 * than `workspaceFolderValue`: the write target is the workspace file, which is
 * one file however many roots the workspace has, so the value it is built from
 * has to be resource-independent too.
 *
 * Read back rather than trusting `update()` to resolve, for the reason
 * `applySetting` in extension.ts does: a write can land at the scope asked for
 * and still be shadowed by a narrower one, and reporting that as success is how
 * a setting appears not to work while a notification says it did (CORE-1776).
 * The read-back still uses `get()` — the merged view is exactly the question
 * being asked, which is whether the characters are allowed for this file now.
 */
async function applyAllowance(
    resource: vscode.Uri,
    language: string,
    languageName: string,
    derived: readonly string[]
): Promise<void> {
    const existing = highlightConfig(resource)
        .inspect<Record<string, unknown>>('allowedCharacters')?.workspaceValue;

    try {
        await highlightConfig(resource).update(
            'allowedCharacters',
            workspaceAllowance(existing, derived),
            vscode.ConfigurationTarget.Workspace
        );
    } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        Logger.error('Failed to write editor.unicodeHighlight.allowedCharacters', message);
        void vscode.window.showErrorMessage(
            `Legesher could not save the ${languageName} character allowance: ${message}`
        );
        return;
    }

    const effective = highlightConfig(resource).get<Record<string, unknown>>('allowedCharacters');
    if (!alreadyAllows(effective, derived)) {
        Logger.error(
            'editor.unicodeHighlight.allowedCharacters was written but does not resolve ' +
            'to the allowance — a narrower configuration scope is overriding it'
        );
        void vscode.window.showWarningMessage(
            'Legesher saved the character allowance, but a more specific setting is ' +
            'overriding it, so the warnings will remain. Check your folder settings.'
        );
        return;
    }

    Logger.info(
        `Unicode highlighting: allowed ${derived.length} ${language} characters ` +
        `(${formatCodePoints(derived)}) at workspace scope`
    );

    // Says only what is true. An earlier draft listed Legesher's engine guards
    // in a way that read as a replacement for the check just relaxed; they are
    // not one. Nothing at the Legesher layer looks for confusables, so the
    // honest sentence names what still runs and stops there.
    void vscode.window.showInformationMessage(
        `Legesher allowed ${derived.length} ${languageName} character` +
        `${derived.length === 1 ? '' : 's'} in this workspace. VS Code still flags ` +
        "invisible and bidi characters, and every other script's confusables. Legesher's " +
        'git clean filter still rejects bidi controls, invisible characters and ' +
        'unsupported-script identifiers on commit. Nothing re-checks the allowed ' +
        'characters themselves — see the extension README.'
    );
}
