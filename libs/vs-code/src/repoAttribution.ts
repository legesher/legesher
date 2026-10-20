/**
 * The opt-in repository label for calls to the hosted service.
 *
 * Opt-in usage attribution: when the user switches it on, a client attaches
 * an `X-Legesher-Repo` header so usage can be attributed to a repository.
 * Twin of `legesher_core.repo_attribution` (Python): the same literal
 * canonicalization and the same digest, so one repository gets one label
 * whichever Legesher client reports it. Both helpers are pinned to the
 * shared vectors in `libs/core/tests/fixtures/repo_attribution_vectors.json`.
 *
 * The label is the first 32 hex characters of an unkeyed SHA-256 over a
 * fixed prefix and the canonical `origin` remote. It is not secret: anyone
 * who knows a remote URL can compute its label, so the label reveals
 * whether a known remote is in use. Without a remote, the digest is over a
 * per-install salt plus the repository path instead.
 *
 * Nothing in the extension sends this label yet; the
 * `legesher.telemetry.repoAttribution` setting records the user's choice.
 * This module stays free of the `vscode` import so it can be unit tested
 * without an editor: the caller passes in the setting values and
 * `vscode.env.isTelemetryEnabled`.
 */

import { createHash } from 'crypto';

/** The request header the hosted service reads. */
export const HEADER = 'X-Legesher-Repo';

/** Domain separation for the digest; identical to the Python helper. */
export const LABEL_PREFIX = 'legesher-repo/v1:';

/** Length of the hex label (128 bits of the digest). */
export const LABEL_HEX_LENGTH = 32;

/** Environment variables that switch every kind of telemetry off. */
export const KILL_SWITCHES = ['LEGESHER_TELEMETRY_DISABLED', 'DO_NOT_TRACK'] as const;

const FALSE_WORDS = new Set(['0', 'false', 'no', 'off', '']);

// Canonicalization is literal and must match the Python twin character for
// character, so every rule is spelled out here rather than borrowed from
// `new URL` (which percent-encodes, converts to punycode and resolves dot
// segments, none of which the Python side does).
const ASCII_WHITESPACE_EDGES = /^[ \t\n\r\v\f]+|[ \t\n\r\v\f]+$/g;
const ASCII_UPPER = /[A-Z]/g;
const SCHEME = /^[A-Za-z][A-Za-z0-9+.-]*:\/\//;
const WINDOWS_DRIVE = /^[A-Za-z]:[/\\]/;
const LONE_SURROGATE = /\p{Cs}/u;
const SALT = /^[0-9a-f]{32}$/;

/**
 * ASCII whitespace trimmed and ASCII letters lowercased, as in the Python
 * twin. Not `trim()`: it strips a byte order mark that Python's `strip()`
 * keeps, and keeps the information separators Python strips.
 */
function word(value: string): string {
    return asciiLower(value.replace(ASCII_WHITESPACE_EDGES, ''));
}

function isSet(value: string | undefined): boolean {
    return value !== undefined && !FALSE_WORDS.has(word(value));
}

/** Whether a kill switch is set in the given environment. */
export function killSwitchSet(env: NodeJS.ProcessEnv = process.env): boolean {
    return KILL_SWITCHES.some((name) => isSet(env[name]));
}

/** The switches that must all be on before a label exists. */
export interface RepoAttributionGates {
    /** `legesher.telemetry.enabled`. */
    telemetryEnabled: boolean;
    /** `legesher.telemetry.repoAttribution` (default false). */
    repoAttribution: boolean;
    /** `vscode.env.isTelemetryEnabled`: VS Code's own telemetry switch. */
    vscodeTelemetryEnabled: boolean;
    env?: NodeJS.ProcessEnv;
}

/**
 * Whether attribution is allowed: every switch strictly `true` and no kill
 * switch set. A value that is not the boolean `true` (a string typed into
 * settings.json, say) never opts in.
 */
export function repoAttributionAllowed(gates: RepoAttributionGates): boolean {
    return (
        gates.telemetryEnabled === true &&
        gates.repoAttribution === true &&
        gates.vscodeTelemetryEnabled === true &&
        !killSwitchSet(gates.env ?? process.env)
    );
}

function asciiLower(text: string): string {
    return text.replace(ASCII_UPPER, (char) => String.fromCharCode(char.charCodeAt(0) + 32));
}

/** NFC, then ASCII A-Z lowercased, then NFC again (see the Python twin). */
function fold(text: string): string {
    return asciiLower(text.normalize('NFC')).normalize('NFC');
}

function firstOf(text: string, pattern: RegExp): number {
    const index = text.search(pattern);
    return index === -1 ? text.length : index;
}

/** The host of `[userinfo@]host[:port]`; an IPv6 host keeps brackets. */
function authorityHost(authority: string): string | undefined {
    const hostPort = authority.slice(authority.lastIndexOf('@') + 1);
    if (hostPort.startsWith('[')) {
        const close = hostPort.indexOf(']');
        return close === -1 ? undefined : hostPort.slice(0, close + 1);
    }
    const colon = hostPort.indexOf(':');
    return colon === -1 ? hostPort : hostPort.slice(0, colon);
}

/** `[host, path]` of a remote, or undefined for a local path. */
function splitRemote(text: string): [string, string] | undefined {
    if (WINDOWS_DRIVE.test(text)) {
        return undefined;
    }
    const scheme = SCHEME.exec(text);
    if (scheme) {
        if (asciiLower(scheme[0].slice(0, -3)) === 'file') {
            return undefined;
        }
        const rest = text.slice(scheme[0].length);
        const authorityEnd = firstOf(rest, /[/?#]/);
        const tail = rest.slice(authorityEnd);
        const host = authorityHost(rest.slice(0, authorityEnd));
        if (host === undefined) {
            return undefined;
        }
        return [host, tail.slice(0, firstOf(tail, /[?#]/))];
    }
    // scp-like [user@]host:path, recognised as git does: a colon with no
    // slash before it. Anything else is a local path.
    const colon = text.indexOf(':');
    const slash = text.indexOf('/');
    if (colon === -1 || (slash !== -1 && slash < colon)) {
        return undefined;
    }
    const start = text.slice(0, colon).lastIndexOf('@') + 1;
    if (text.startsWith('[', start)) {
        const close = text.indexOf(']', start);
        if (close === -1 || text.slice(close + 1, close + 2) !== ':') {
            return undefined;
        }
        return [text.slice(start, close + 1), text.slice(close + 2)];
    }
    return [text.slice(start, colon), text.slice(colon + 1)];
}

/**
 * The canonical form of a remote URL, or undefined for a local path.
 *
 * The same literal algorithm as `canonical_remote` in the Python helper:
 * trim ASCII whitespace and one leading BOM; a Windows drive path or a
 * `file://` URL is local; keep only the host and path of a `scheme://` URL
 * or an scp-like `[user@]host:path`; an `@` still left in either means a
 * malformed remote and no canonical form; NFC, lowercase ASCII A-Z only,
 * NFC; strip slashes and one trailing `.git`. Nothing is percent-decoded,
 * encoded or converted to punycode, and dot segments stay.
 */
export function canonicalRemote(url: string): string | undefined {
    let text = url.replace(ASCII_WHITESPACE_EDGES, '');
    if (text.startsWith('﻿')) {
        text = text.slice(1).replace(ASCII_WHITESPACE_EDGES, '');
    }
    if (!text || LONE_SURROGATE.test(text)) {
        return undefined;
    }
    const parts = splitRemote(text);
    if (parts === undefined) {
        return undefined;
    }
    const host = fold(parts[0]);
    let path = fold(parts[1]).replace(/^\/+|\/+$/g, '');
    if (path.endsWith('.git')) {
        path = path.slice(0, -'.git'.length).replace(/\/+$/, '');
    }
    // An @ left over marks a malformed remote whose password would
    // otherwise reach the hash (see the Python twin).
    if (!host || !path || host.includes('@') || path.includes('@')) {
        return undefined;
    }
    return `${host}/${path}`;
}

function digest(material: string): string {
    return createHash('sha256')
        .update(LABEL_PREFIX + material, 'utf8')
        .digest('hex')
        .slice(0, LABEL_HEX_LENGTH);
}

/** The label for a remote URL with no gates applied, or undefined. */
export function labelForRemote(url: string): string | undefined {
    const canonical = canonicalRemote(url);
    return canonical === undefined ? undefined : digest(canonical);
}

/** Everything `repoLabel` needs: the gates plus the repository facts. */
export interface RepoLabelOptions extends RepoAttributionGates {
    /** The repository's `origin` remote, undefined when it has none. */
    remoteUrl: string | undefined;
    /** The work tree's top-level path, for the per-install fallback. */
    repoRoot: string;
    /** The per-install salt (32 lowercase hex characters), if readable. */
    installSalt: string | undefined;
}

/**
 * The attribution label, or undefined when not allowed or not safe.
 *
 * Undefined unless `repoAttributionAllowed` holds. Without a usable remote,
 * the label needs a valid salt: an empty or malformed salt would make it a
 * plain hash of a guessable path, so no label is produced instead. Never
 * throws.
 */
export function repoLabel(options: RepoLabelOptions): string | undefined {
    try {
        if (!repoAttributionAllowed(options)) {
            return undefined;
        }
        const label = options.remoteUrl ? labelForRemote(options.remoteUrl) : undefined;
        if (label !== undefined) {
            return label;
        }
        if (typeof options.installSalt !== 'string' || !SALT.test(options.installSalt)) {
            return undefined;
        }
        return digest(`local:${options.installSalt}:${options.repoRoot}`);
    } catch {
        return undefined;
    }
}

/** `{ 'X-Legesher-Repo': label }` when allowed, else `{}`. */
export function repoAttributionHeaders(options: RepoLabelOptions): Record<string, string> {
    const label = repoLabel(options);
    return label ? { [HEADER]: label } : {};
}
