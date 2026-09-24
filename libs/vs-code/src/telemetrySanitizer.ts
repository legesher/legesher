/**
 * PII scrubbing for the one free-text telemetry property we send (CORE-596,
 * absorbing CORE-2031).
 *
 * Every event this extension authors is built from an enumerated vocabulary —
 * command names, language codes, scopes, outcomes — except
 * `errorOccurred.context`, which carries an error message the extension did not
 * write: a VS Code configuration failure, a translation failure, a language
 * server message. That one string is the only free text any event carries, and
 * the published claim that our events contain no file paths rests on what this
 * module removes from it (CORE-2042).
 *
 * What it removes is *shapes*, not identities. A path, a URL, an email, an IP
 * address and anything else carrying a separator are replaced; a bare word is
 * not, because nothing distinguishes `jane-macbook`, `JANE-PC`, `Jane Smith` or
 * `+1-415-555-0123` from the diagnostic prose around them. Personal data in
 * bare-word form therefore still reaches the endpoint. That is accepted, not
 * fixed: see "Known residue" at the end of this comment for the list we own.
 *
 * The scrubber this replaces was two regexes that recognised only `/`-rooted
 * paths, so `C:\Users\jane\...`, `\\server\share\...`, `192.168.1.42`,
 * `http://internal.corp.com/...` and `jane-macbook.local` all went through
 * untouched, and a path containing a space was matched only up to the space —
 * the remainder, `Smith/Documents/file.py`, was sent verbatim.
 *
 * So this works the other way round. The string is split on whitespace and
 * every token has to be *recognised as safe* to survive; a shape nobody
 * enumerated is replaced rather than forwarded.
 *
 * Splitting on whitespace is also what a path containing a space partly
 * defeats, and this is the part the first version of this comment got wrong.
 * `C:\Users\Jane Smith` arrives as two tokens. Interior segments do fall out
 * for free: each carries a separator of its own, so each is a path in its own
 * right, and adjacent identical placeholders collapse back into one. The first
 * and last segments carry no separator, though, so a leading given name and a
 * trailing surname survive. `sanitizeErrorContext` therefore runs a
 * whole-string pre-pass first that collapses a *quoted* run containing a path
 * anchor, which is the shape Node's errno messages use
 * (`scandir 'C:\Users\Jane Smith'`). Unquoted there is no marker saying where
 * the path stops and the sentence resumes, so the unquoted terminus is not
 * closed.
 *
 * What survives is deliberately narrow: words in any script (VS Code's own
 * messages are localized, and so are ours), numbers, version numbers, our own
 * `legesher.*` setting names, and `key:value` pairs whose halves are themselves
 * safe. Anything carrying a separator, a percent-escape, an `@`, a URL scheme,
 * a dot between labels, or a character outside that set is replaced.
 * Over-redaction is the failure mode we can live with; the other one ships a
 * home directory to a third-party endpoint.
 *
 * Deliberately has no `vscode` import: the rule is pure over a string, so it is
 * unit-testable without an editor host — which is the point, since the test it
 * replaced re-implemented the patterns locally and passed while the real
 * `trackError()` leaked.
 *
 * Known residue. Each of these is asserted in the unit tests against its exact
 * current output, so it changes visibly or not at all:
 *
 * - The first and last segment of an *unquoted* path containing a space:
 *   `Unable to resolve workspace folder C:\Users\Jane Smith` becomes
 *   `... <path> Smith`, and `Jane Smith\Documents\main.py failed` becomes
 *   `Jane <path> failed`. JS `\s` already covers NBSP and the other space
 *   separators, so U+00A0 behaves exactly like U+0020 here.
 * - Bare-word personal data: `jane-macbook`, `JANE-PC`, `user:jsmith`,
 *   `Jane Smith`, a Cyrillic-homoglyph spelling of `jane` (U+0430 for `a`),
 *   `+1-415-555-0123`.
 */

/**
 * What redacted content is replaced with.
 *
 * A bare dotted token deliberately has no placeholder of its own:
 * `jane-macbook.local` and `cache.v2.json` are the same shape, so naming one
 * `<host>` and the other `<path>` would mislabel half of them in the telemetry
 * table. Both become `<redacted>`, which is the true statement.
 */
const PLACEHOLDER = {
    email: '<email>',
    url: '<url>',
    path: '<path>',
    ip: '<ip>',
    unrecognized: '<redacted>',
} as const;

const PLACEHOLDER_VALUES: ReadonlySet<string> = new Set(Object.values(PLACEHOLDER));

/** Returned when there is nothing to report, preserving the previous contract. */
const NO_CONTEXT = 'none';

/**
 * How deep a `key:value` nest is worth taking apart.
 *
 * The kv rule recurses once per colon, so a token of a few thousand colons
 * exhausts the stack. Our own call sites send one colon; a VS Code message
 * carrying a Windows path and an errno sends a handful. Anything past this is
 * not a shape worth classifying.
 */
const MAX_COLON_DEPTH = 64;

/** Colons in `token`, without allocating the split. */
function colonCount(token: string): number {
    let count = 0;
    for (let i = 0; i < token.length; i++) {
        if (token[i] === ':') {
            count++;
            if (count > MAX_COLON_DEPTH) {
                return count;
            }
        }
    }
    return count;
}

// Brackets and sentence punctuation wrap a value without being part of it:
// `('C:\Users\jane')` is a path in brackets, not an unrecognised token. A
// trailing colon is not stripped — `ENOENT:` keeps it through the `key:value`
// rule below.
const LEADING_PUNCTUATION = /^[('"`[{<]+/;
const TRAILING_PUNCTUATION = /[)'"`\]}>,;.!?]+$/;

/**
 * A quoted run whose contents look like a path, matched over the whole string
 * before it is split into tokens.
 *
 * This is the one place a path containing a space can be redacted whole,
 * because the closing quote says where it ends, which is exactly the shape
 * Node's errno messages use (`ENOENT: ..., open '/Users/Jane Smith/main.py'`).
 * The quotes go with it, so the result reads `open <path>` rather than
 * `open '<path>'`.
 *
 * The path anchor is asserted in a lookahead rather than checked afterwards so
 * that a quoted run *without* one is not consumed: in `don't open 'C:\x\Jane
 * Smith'` a plain quoted-run pattern would pair the apostrophe in `don't` with
 * the opening quote of the path and leave the path unmatched. The anchor is a
 * literal separator anywhere in the run, or a drive marker or `~` at its very
 * start. `[A-Za-z]:` is not accepted mid-run, because `'ENOENT: no such file'`
 * would otherwise be collapsed into `<path>`.
 */
const QUOTED_PATH_RUN = /(['"`])(?=~|[A-Za-z]:\S|[^'"`]*[\\/])[^'"`]*\1/g;

const EMAIL = /^[^\s@]+@[^\s@]+$/;
const URL_SCHEME = /^[A-Za-z][A-Za-z0-9+.-]*:\/\//;
/** `\\server\share\...` */
const UNC_PATH = /^\\\\/;
/**
 * `C:\...`, `C:/...`, a bare `C:`, or the drive-relative `C:jane`.
 *
 * No separator is required after the colon. `C:jane` is a valid Windows path:
 * it names `jane` relative to the current directory on drive C, and requiring
 * one let the whole thing through as an unremarkable word. The cost is that a
 * single letter followed by a colon is always read as a drive marker, so a
 * one-letter `key:value` label becomes `<path>`; nothing we send has one.
 */
const WINDOWS_DRIVE_PATH = /^[A-Za-z]:/;
/** `~/...`, `~\...`, or a bare `~`. */
const HOME_PATH = /^~(?:[\\/]|$)/;
const IPV4 = /^\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?$/;
const IPV6 = /^(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}$/;
/**
 * A percent-escape. `%` is a safe word character, since `100%` and
 * `%USERPROFILE%` are both ordinary content, but `%2F` and `%5C` are
 * separators in disguise,
 * and `C%3A%5CUsers%5Cjane` carries no literal separator at all, so without
 * this it reached the endpoint as a word.
 */
const PERCENT_ENCODED = /%[0-9A-Fa-f]{2}/;
/** Our own configuration namespace: enumerable, and the most useful token in these messages. */
const OUR_SETTING = /^legesher\.[A-Za-z0-9_.]+$/;
const VERSION = /^v?\d+(?:\.\d+)+$/;
/**
 * A word in any script, plus the punctuation that appears inside one. Letters
 * are matched by Unicode property so a localized message survives; format
 * characters (bidi marks among them) are not letters, so a token carrying one
 * is redacted rather than forwarded.
 */
const SAFE_WORD = /^[\p{L}\p{N}_'+%#\u2013\u2014\u2019-]+$/u;

/**
 * The placeholder a token must be replaced with, or `undefined` when it is
 * recognised as safe and survives exactly as written.
 */
function classify(token: string): string | undefined {
    if (token === '') {
        return undefined;
    }

    if (EMAIL.test(token)) {
        return PLACEHOLDER.email;
    }
    if (URL_SCHEME.test(token)) {
        return PLACEHOLDER.url;
    }
    // Before the drive check, not after: `a::1` is an abbreviated IPv6 address
    // and also starts with a letter and a colon, so the drive rule would
    // relabel it `<path>`. Both are redactions; this one is the true one.
    if (IPV4.test(token) || IPV6.test(token)) {
        return PLACEHOLDER.ip;
    }
    if (UNC_PATH.test(token) || WINDOWS_DRIVE_PATH.test(token) || HOME_PATH.test(token)) {
        return PLACEHOLDER.path;
    }

    // `key:value` is the shape our own call sites send (`workingLanguage:workspace`,
    // `workingLanguage:<a VS Code error>`), so each half is judged on its own
    // rather than the pair being thrown away for containing a colon.
    //
    // The split is on the FIRST colon only. Splitting on every colon takes
    // `cwd:C:jsmith` apart into three pieces, and the drive marker, the thing
    // that makes `C:jsmith` a path, is destroyed before anything can classify
    // it, so all three pieces read as safe words. A value half may itself hold
    // colons, so this recurs once per colon; each call is on a strictly shorter
    // string, so it terminates.
    //
    // It terminates, but the stack runs out before the string does: a token of
    // several thousand colons overflows, and because trackError() scrubs
    // outside its own try block the error escapes into a caller that is itself
    // an error handler. Nothing we send is a key:value nest of any depth, so a
    // token past this bound is degenerate and gets replaced whole.
    if (colonCount(token) > MAX_COLON_DEPTH) {
        return PLACEHOLDER.unrecognized;
    }
    const separator = token.indexOf(':');
    if (separator !== -1) {
        const key = scrubToken(token.slice(0, separator));
        const value = scrubToken(token.slice(separator + 1));
        const rejoined = `${key}:${value}`;
        return rejoined === token ? undefined : rejoined;
    }

    // A literal separator is checked before the percent-escape so that a path
    // carrying one encoded space is still labelled `<path>` rather than the
    // vaguer `<redacted>`. Either way it is replaced.
    if (token.includes('/') || token.includes('\\')) {
        return PLACEHOLDER.path;
    }
    if (PERCENT_ENCODED.test(token)) {
        return PLACEHOLDER.unrecognized;
    }
    if (token.includes('.')) {
        return OUR_SETTING.test(token) || VERSION.test(token) ? undefined : PLACEHOLDER.unrecognized;
    }

    return SAFE_WORD.test(token) ? undefined : PLACEHOLDER.unrecognized;
}

/** A single whitespace-delimited token, redacted or returned untouched. */
function scrubToken(token: string): string {
    const core = token.replace(LEADING_PUNCTUATION, '').replace(TRAILING_PUNCTUATION, '');
    return classify(core) ?? token;
}

/**
 * Strip personal data out of a free-text error context before it is sent.
 *
 * @param context - The raw message, or `undefined` when a call site has none
 * @returns The redacted message, or `'none'` when there was nothing to send
 */
export function sanitizeErrorContext(context?: string): string {
    // Quoted paths are collapsed whole before tokenizing, because the closing
    // quote is the only reliable end marker a path containing a space has.
    const anchored = context ? context.replace(QUOTED_PATH_RUN, PLACEHOLDER.path) : '';
    const tokens = anchored.split(/\s+/).filter(token => token !== '');
    if (tokens.length === 0) {
        return NO_CONTEXT;
    }

    const scrubbed: string[] = [];
    for (const token of tokens) {
        const piece = scrubToken(token);
        // The interior of a path containing spaces arrives as a run of tokens,
        // each a path on its own; one `<path>` says everything the run said.
        if (PLACEHOLDER_VALUES.has(piece) && scrubbed[scrubbed.length - 1] === piece) {
            continue;
        }
        scrubbed.push(piece);
    }

    return scrubbed.join(' ');
}
