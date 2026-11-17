/**
 * The language server the extension installs for itself.
 *
 * Someone with no `legesher-lsp` can press Install. The extension then downloads
 * the pinned uv (`uvRelease.ts`), and uv fetches its own Python and installs the
 * server's packages from `server/requirements.lock`, every file checked against
 * the SHA-256 the lock gives it. Everything lands in one folder the extension
 * owns, in VS Code's storage for this extension: nothing goes on PATH, nothing
 * uses the machine's own Python, and `legesher.serverCommand` is never written.
 *
 * Which server runs is decided in order (`resolveServerCommand`): the user's own
 * `legesher.serverCommand`, then `legesher-lsp` on PATH, then this install. Each
 * install is named after its lock, so an extension release that ships a new lock
 * installs beside the old one, switches when the new one works, and removes the
 * old one.
 *
 * Every effect is injected (`ManagedServerDeps`), and the module is free of
 * `vscode`, so the unit tests drive it with no editor, no network and no disk.
 * `managedServerNode.ts` supplies the real effects.
 */

import * as crypto from 'crypto';
import * as path from 'path';
import { extractFromTarGz, extractFromZip } from './archive';
import { SERVER_PACKAGE, DEFAULT_SERVER_COMMAND } from './serverInstall';
import {
    UV_VERSION,
    type UvTarget,
    uvArchiveMember,
    uvAssetName,
    uvDownloadUrl,
    uvExecutableName,
} from './uvRelease';

/**
 * The Python minor version the server is installed on. uv picks the newest
 * build of it that the pinned uv release knows, and checks its checksum.
 */
export const SERVER_PYTHON = '3.12';

/** The lock, relative to the extension's root. */
export const SERVER_LOCK_PATH: readonly string[] = ['server', 'requirements.lock'];

/** The file in an install's folder that says it finished, written last. */
const MARKER_FILE = 'legesher-install.json';

/** How often the window holding the install lock says it is still working. */
export const INSTALL_HEARTBEAT_MS = 30_000;
/**
 * A lock whose holder has not said it is still working for this long was left
 * by a window that went away. Judged from the last heartbeat, not from when
 * the install started, so a slow install is never taken over.
 */
export const INSTALL_LOCK_STALE_MS = 3 * 60_000;
/** How long one window waits for another window's install before giving up. */
export const INSTALL_WAIT_MS = 20 * 60_000;
const INSTALL_POLL_MS = 2_000;

// ---------------------------------------------------------------------------
// The lock
// ---------------------------------------------------------------------------

/** What the extension needs from `server/requirements.lock`. */
export interface ServerLock {
    /**
     * Names the install folder: the first 12 hex characters of a SHA-256 over
     * the lock's requirements, so a new lock gets a new folder and an edited
     * comment does not.
     */
    readonly id: string;
    /** The `legesher-language-server` version the lock pins. */
    readonly serverVersion: string;
    /** How many packages the lock pins. */
    readonly packages: number;
}

const HASH_OPTION = /^--hash=sha256:[0-9a-f]{64}$/;
const PINNED = /^([A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]]*\])?==([^\s;]+)\s*(;.*)?$/;

/** A package name as pip compares it. */
function normalizeName(name: string): string {
    return name.toLowerCase().replace(/[-_.]+/g, '-');
}

/** The lock's requirement lines, continuations joined and comments dropped. */
function logicalLines(text: string): string[] {
    const joined = text.replace(/\r\n/g, '\n').replace(/\\\n/g, ' ');
    return joined
        .split('\n')
        .map(line => line.replace(/(^|\s)#.*$/, '').trim())
        .filter(line => line.length > 0);
}

/**
 * Everything wrong with a lock, as sentences; empty when it is usable.
 *
 * The rules are what make `--require-hashes` mean something: every line is one
 * package pinned with `==` and at least one `--hash=sha256:`, and there are no
 * option lines, so a lock cannot point the install at another index, a URL or a
 * local folder. It must pin the language server itself.
 */
export function lockProblems(text: string): string[] {
    const problems: string[] = [];
    let server = 0;
    const lines = logicalLines(text);
    for (const line of lines) {
        if (line.startsWith('-')) {
            problems.push(`option line "${line.split(/\s+/)[0]}" is not allowed; the lock lists pinned, hashed packages only`);
            continue;
        }
        const hashAt = line.search(/\s--/);
        const spec = (hashAt < 0 ? line : line.slice(0, hashAt)).trim();
        const options = hashAt < 0 ? [] : line.slice(hashAt).trim().split(/\s+/);
        const pinned = PINNED.exec(spec);
        if (!pinned) {
            problems.push(`"${spec}" is not pinned with ==`);
            continue;
        }
        // An option hidden in a marker (`; x -i https://...`) is still an option.
        const hidden = spec.split(/\s+/).filter(token => token.startsWith('-'));
        if (hidden.length > 0) {
            problems.push(`"${pinned[1]}" carries ${hidden.join(' ')}; only --hash=sha256 is allowed`);
        }
        const stray = options.filter(option => !HASH_OPTION.test(option));
        if (stray.length > 0) {
            problems.push(`"${pinned[1]}" carries ${stray.join(' ')}; only --hash=sha256 is allowed`);
        }
        if (options.length - stray.length === 0) {
            problems.push(`"${pinned[1]}" has no --hash=sha256`);
        }
        if (normalizeName(pinned[1]) === SERVER_PACKAGE) {
            server++;
        }
    }
    if (lines.length === 0) {
        problems.push('the lock lists no packages');
    } else if (server !== 1) {
        problems.push(`the lock must pin ${SERVER_PACKAGE} exactly once, and pins it ${server} times`);
    }
    return problems;
}

/** Read a lock, or throw naming everything wrong with it. */
export function parseServerLock(text: string): ServerLock {
    const problems = lockProblems(text);
    if (problems.length > 0) {
        throw new Error(`the language server lock is not usable: ${problems.join('; ')}`);
    }
    const lines = logicalLines(text);
    let serverVersion = '';
    for (const line of lines) {
        const pinned = PINNED.exec(line.split(/\s--/)[0].trim());
        if (pinned && normalizeName(pinned[1]) === SERVER_PACKAGE) {
            serverVersion = pinned[3];
        }
    }
    const id = crypto.createHash('sha256').update([...lines].sort().join('\n')).digest('hex').slice(0, 12);
    return { id, serverVersion, packages: lines.length };
}

// ---------------------------------------------------------------------------
// Where things go
// ---------------------------------------------------------------------------

/** The folders and files of the extension's own server install. */
export interface ServerLayout {
    readonly root: string;
    /** Holds the pinned uv, in a folder named after its version. */
    readonly uvDir: string;
    readonly uvPath: string;
    /** uv's Python builds (`UV_PYTHON_INSTALL_DIR`). */
    readonly pythonDir: string;
    /** uv's download cache during an install, deleted after it. */
    readonly cacheDir: string;
    /** Python executables uv would link (`UV_PYTHON_BIN_DIR`); kept inside the root. */
    readonly binDir: string;
    /** One folder per lock id. */
    readonly envsDir: string;
    /** Held by the window that is installing. */
    readonly lockDir: string;
    /** One folder per install, holding a file per process that runs its server. */
    readonly leasesDir: string;
    envDir(id: string): string;
    envPython(id: string): string;
    serverPath(id: string): string;
    markerPath(id: string): string;
}

/**
 * The layout under `root` on `platform`.
 *
 * Paths are joined with the platform's own separator, so a test can check the
 * Windows layout on any machine.
 */
export function serverLayout(root: string, platform: string): ServerLayout {
    const p = platform === 'win32' ? path.win32 : path.posix;
    const windows = platform === 'win32';
    const uvDir = p.join(root, 'uv', UV_VERSION);
    const envsDir = p.join(root, 'envs');
    const envDir = (id: string): string => p.join(envsDir, id);
    return {
        root,
        uvDir,
        uvPath: p.join(uvDir, uvExecutableName(platform)),
        pythonDir: p.join(root, 'python'),
        cacheDir: p.join(root, 'cache'),
        binDir: p.join(root, 'bin'),
        envsDir,
        lockDir: p.join(root, 'install.lock'),
        leasesDir: p.join(root, 'leases'),
        envDir,
        envPython: id => windows ? p.join(envDir(id), 'Scripts', 'python.exe') : p.join(envDir(id), 'bin', 'python'),
        serverPath: id => windows
            ? p.join(envDir(id), 'Scripts', `${DEFAULT_SERVER_COMMAND}.exe`)
            : p.join(envDir(id), 'bin', DEFAULT_SERVER_COMMAND),
        markerPath: id => p.join(envDir(id), MARKER_FILE),
    };
}

// ---------------------------------------------------------------------------
// The environment uv and the server run in
// ---------------------------------------------------------------------------

/**
 * The user's uv settings that still apply to an install.
 *
 * Each one only says where to fetch from or how to trust TLS, and none can
 * change what is installed: every file is still checked against a checksum
 * that ships in the extension. They are kept so a machine that can only reach
 * a mirror can still install. Every other `UV_*` variable is dropped, among
 * them `UV_PYTHON_DOWNLOADS_JSON_URL`, which would replace the Python
 * checksums uv checks against.
 */
export const UV_ENV_PASSTHROUGH: readonly string[] = [
    'UV_DEFAULT_INDEX',
    'UV_INDEX',
    'UV_INDEX_URL',
    'UV_PYTHON_INSTALL_MIRROR',
    'UV_NATIVE_TLS',
    'UV_SYSTEM_CERTS',
];

/** Python variables that would make the installed server load other code. */
const PYTHON_ISOLATION = ['PYTHONHOME', 'PYTHONPATH', 'VIRTUAL_ENV'];

/** `env` without `names`, compared case-insensitively as Windows does. */
function without(env: NodeJS.ProcessEnv, drop: (upperName: string) => boolean): NodeJS.ProcessEnv {
    const result: NodeJS.ProcessEnv = {};
    for (const [name, value] of Object.entries(env)) {
        if (!drop(name.toUpperCase())) {
            result[name] = value;
        }
    }
    return result;
}

/**
 * The environment for the extension's own server process: the user's, without
 * the variables that would point its Python at other packages.
 */
export function isolatedPythonEnv(env: NodeJS.ProcessEnv): NodeJS.ProcessEnv {
    return without(env, name => PYTHON_ISOLATION.includes(name));
}

/**
 * The environment uv runs in.
 *
 * Starts from `isolatedPythonEnv(base)`, drops every `UV_*` variable outside
 * `UV_ENV_PASSTHROUGH`, then sets the ones that keep the install inside
 * `layout.root`: uv's Python builds, its cache and any Python links it makes
 * stay there, uv reads no `uv.toml` or `pyproject.toml`, uses only Python
 * builds it manages, and registers nothing in the Windows registry.
 *
 * @param proxy VS Code's `http.proxy`, passed on when the environment names no
 *   proxy of its own: VS Code applies it to the extension's own downloads, but
 *   uv only reads the environment.
 */
export function uvEnvironment(base: NodeJS.ProcessEnv, layout: ServerLayout, proxy?: string): NodeJS.ProcessEnv {
    const env = without(
        isolatedPythonEnv(base),
        name => name.startsWith('UV_') && !UV_ENV_PASSTHROUGH.includes(name)
    );
    const hasProxy = Object.keys(env).some(name => ['HTTPS_PROXY', 'HTTP_PROXY', 'ALL_PROXY'].includes(name.toUpperCase()));
    if (proxy && !hasProxy) {
        env.HTTPS_PROXY = proxy;
        env.HTTP_PROXY = proxy;
    }
    return {
        ...env,
        UV_PYTHON_INSTALL_DIR: layout.pythonDir,
        UV_CACHE_DIR: layout.cacheDir,
        UV_PYTHON_BIN_DIR: layout.binDir,
        UV_PYTHON_INSTALL_BIN: '0',
        UV_PYTHON_INSTALL_REGISTRY: '0',
        UV_PYTHON_PREFERENCE: 'only-managed',
        UV_PYTHON_DOWNLOADS: 'automatic',
        UV_NO_CONFIG: '1',
        // Copied, not linked, so deleting the cache afterwards cannot touch
        // the installed files.
        UV_LINK_MODE: 'copy',
        UV_NO_PROGRESS: '1',
        NO_COLOR: '1',
    };
}

// ---------------------------------------------------------------------------
// Effects
// ---------------------------------------------------------------------------

/** The filesystem operations an install needs. */
export interface ManagedFs {
    readFile(file: string): Promise<string>;
    /** Writes `data`, creating the file with `mode` when given. */
    writeFile(file: string, data: string | Buffer, mode?: number): Promise<void>;
    /** With `recursive` false, rejects with code `EEXIST` when `dir` exists. */
    mkdir(dir: string, recursive: boolean): Promise<void>;
    /** Removes a file or folder and everything in it; no error when missing. */
    rm(target: string): Promise<void>;
    rename(from: string, to: string): Promise<void>;
    /** The names in `dir`; empty when it does not exist. */
    readdir(dir: string): Promise<string[]>;
    exists(target: string): Promise<boolean>;
}

/** What a finished process wrote. */
export interface RunResult {
    readonly stdout: string;
    readonly stderr: string;
}

/** Everything an install does to the outside world. */
export interface ManagedServerDeps {
    readonly platform: string;
    /** The environment the extension runs in, before it is cleaned for uv. */
    readonly env: NodeJS.ProcessEnv;
    /** VS Code's `http.proxy`, if set. */
    readonly proxy?: string;
    /** The bytes at an https URL, following redirects. */
    download(url: string): Promise<Buffer>;
    /**
     * Run `command` with `args` as separate arguments, never through a shell,
     * so a path with spaces or any script in it reaches the process intact.
     * Rejects when the process fails, with its stderr in the message.
     */
    run(command: string, args: readonly string[], options: { env: NodeJS.ProcessEnv; cwd: string }): Promise<RunResult>;
    readonly fs: ManagedFs;
    now(): number;
    sleep(ms: number): Promise<void>;
    /** Call `tick` every `ms` until the returned function is called. */
    every(ms: number, tick: () => void): () => void;
    /** This process's id, for the install lock and for leases. */
    readonly pid: number;
    /** Whether a process with this id is running. */
    isAlive(pid: number): boolean;
    log(message: string): void;
}

// ---------------------------------------------------------------------------
// Finding installs
// ---------------------------------------------------------------------------

/** A finished install of the server. */
export interface InstalledServer {
    readonly id: string;
    readonly serverPath: string;
    readonly serverVersion: string;
    readonly installedAt: number;
}

interface Marker {
    lockId: string;
    serverVersion: string;
    uvVersion: string;
    python: string;
    installedAt: number;
}

async function readMarker(layout: ServerLayout, id: string, deps: ManagedServerDeps): Promise<InstalledServer | undefined> {
    try {
        const marker = JSON.parse(await deps.fs.readFile(layout.markerPath(id))) as Partial<Marker>;
        if (marker.lockId !== id || typeof marker.serverVersion !== 'string') {
            return undefined;
        }
        return {
            id,
            serverPath: layout.serverPath(id),
            serverVersion: marker.serverVersion,
            installedAt: typeof marker.installedAt === 'number' ? marker.installedAt : 0,
        };
    } catch {
        return undefined;
    }
}

/** The extension's finished installs: the one for this lock, and the newest other. */
export interface ManagedState {
    readonly current?: InstalledServer;
    readonly stale?: InstalledServer;
}

/**
 * The finished installs under `layout`. A folder with no marker is an install
 * that never finished, and is ignored.
 */
export async function managedServerState(
    layout: ServerLayout,
    lock: ServerLock,
    deps: ManagedServerDeps
): Promise<ManagedState> {
    let current: InstalledServer | undefined;
    let stale: InstalledServer | undefined;
    for (const name of await deps.fs.readdir(layout.envsDir)) {
        if (name.startsWith('.')) {
            continue;
        }
        const installed = await readMarker(layout, name, deps);
        if (!installed) {
            continue;
        }
        if (name === lock.id) {
            current = installed;
        } else if (!stale || installed.installedAt > stale.installedAt) {
            stale = installed;
        }
    }
    return { current, stale };
}

// ---------------------------------------------------------------------------
// Which server runs
// ---------------------------------------------------------------------------

/** Where the command the extension starts came from. */
export type ServerSource = 'setting' | 'path' | 'managed' | 'managed-stale';

/** A server command that answered `--version`, and where it came from. */
export interface ResolvedServerCommand {
    readonly command: string;
    readonly source: ServerSource;
    /** The extension's own install, when that is what runs. */
    readonly installed?: InstalledServer;
}

/**
 * The server to start, or undefined when nothing that answers is available.
 *
 * In order: a `legesher.serverCommand` other than the default, which is the
 * user's choice and is never second-guessed, even when it does not answer;
 * then `legesher-lsp` on PATH, which someone installed on purpose; then the
 * extension's own install for this lock; then its install for an older lock,
 * which keeps working while the new one installs.
 */
export async function resolveServerCommand(
    configured: string,
    managed: ManagedState,
    isAvailable: (command: string, isolated: boolean) => Promise<boolean>
): Promise<ResolvedServerCommand | undefined> {
    // `isolated` is true for the extension's own install, which is checked in
    // the environment it runs in (`isolatedPythonEnv`): a PYTHONHOME that
    // breaks it for the check would not break it for the real start.
    if (configured !== DEFAULT_SERVER_COMMAND) {
        return await isAvailable(configured, false) ? { command: configured, source: 'setting' } : undefined;
    }
    if (await isAvailable(DEFAULT_SERVER_COMMAND, false)) {
        return { command: DEFAULT_SERVER_COMMAND, source: 'path' };
    }
    if (managed.current && await isAvailable(managed.current.serverPath, true)) {
        return { command: managed.current.serverPath, source: 'managed', installed: managed.current };
    }
    if (managed.stale && await isAvailable(managed.stale.serverPath, true)) {
        return { command: managed.stale.serverPath, source: 'managed-stale', installed: managed.stale };
    }
    return undefined;
}

// ---------------------------------------------------------------------------
// Installing
// ---------------------------------------------------------------------------

/** The stage an install is at, for progress and for errors. */
export type InstallStep = 'uv' | 'server' | 'check';

/** Why an install did not finish. */
export class ServerInstallError extends Error {
    constructor(readonly step: InstallStep | 'unsupported' | 'busy', message: string) {
        super(message);
        this.name = 'ServerInstallError';
    }
}

/**
 * Refuse `data` unless its SHA-256 is `expected`.
 *
 * @param what Names the download in the error.
 */
export function verifySha256(data: Buffer, expected: string, what: string): void {
    const actual = crypto.createHash('sha256').update(data).digest('hex');
    if (actual !== expected) {
        throw new ServerInstallError(
            'uv',
            `${what} did not match its pinned checksum (expected sha256 ${expected}, got ${actual}); nothing was installed`
        );
    }
}

function errorCode(error: unknown): string | undefined {
    return typeof error === 'object' && error !== null && 'code' in error
        ? String((error as { code: unknown }).code)
        : undefined;
}

interface LockOwner {
    token: string;
    pid: number;
    heartbeatAt: number;
}

function ownerFile(dir: string, platform: string): string {
    return platform === 'win32' ? path.win32.join(dir, 'owner.json') : path.posix.join(dir, 'owner.json');
}

async function readOwner(file: string, deps: ManagedServerDeps): Promise<LockOwner | undefined> {
    try {
        const owner = JSON.parse(await deps.fs.readFile(file)) as Partial<LockOwner>;
        return typeof owner.token === 'string' && typeof owner.heartbeatAt === 'number'
            ? { token: owner.token, pid: Number(owner.pid), heartbeatAt: owner.heartbeatAt }
            : undefined;
    } catch {
        return undefined;
    }
}

/**
 * Take the install lock, waiting while another window holds it.
 *
 * The holder rewrites `owner.json` every `INSTALL_HEARTBEAT_MS` for as long as
 * it holds the lock. A lock with no heartbeat for `INSTALL_LOCK_STALE_MS` was
 * left by a window that went away, and is taken over: moved aside under a name
 * only this window uses, then checked, so that two windows judging the same
 * lock stale cannot both end up holding it. Releasing removes the lock only
 * while it still carries this window's token.
 *
 * Resolves to the function that releases it.
 */
async function acquireInstallLock(layout: ServerLayout, deps: ManagedServerDeps): Promise<() => Promise<void>> {
    const waitingSince = deps.now();
    const owner = ownerFile(layout.lockDir, deps.platform);
    const token = crypto.randomBytes(12).toString('hex');
    const sign = () => deps.fs.writeFile(owner, JSON.stringify({ token, pid: deps.pid, heartbeatAt: deps.now() }));
    for (;;) {
        try {
            await deps.fs.mkdir(layout.lockDir, false);
            await sign();
            const stop = deps.every(INSTALL_HEARTBEAT_MS, () => {
                void readOwner(owner, deps).then(current => current?.token === token ? sign() : undefined)
                    .catch(error => deps.log(`Could not refresh the install lock: ${String(error)}`));
            });
            return async () => {
                stop();
                if ((await readOwner(owner, deps))?.token === token) {
                    await deps.fs.rm(layout.lockDir);
                } else {
                    deps.log('The install lock was taken over by another window; leaving it');
                }
            };
        } catch (error) {
            if (errorCode(error) !== 'EEXIST') {
                throw error;
            }
        }
        const recorded = await readOwner(owner, deps);
        // Unreadable: taken but not yet written, or written by a window that
        // died between the two. Judged from when this window started waiting.
        const lastSign = recorded?.heartbeatAt ?? waitingSince;
        if (deps.now() - lastSign > INSTALL_LOCK_STALE_MS) {
            const aside = `${layout.lockDir}.stale-${token}`;
            try {
                await deps.fs.rename(layout.lockDir, aside);
            } catch {
                continue; // Another window moved it first.
            }
            const moved = await readOwner(ownerFile(aside, deps.platform), deps);
            if (moved && moved.token !== recorded?.token) {
                // Another window took the stale lock over between the read
                // and the move, and this moved its fresh lock. Give it back.
                await deps.fs.rename(aside, layout.lockDir).catch(() => undefined);
                continue;
            }
            deps.log(`Taking over an install lock with no heartbeat since ${new Date(lastSign).toISOString()}`);
            await deps.fs.rm(aside);
            continue;
        }
        if (deps.now() - waitingSince > INSTALL_WAIT_MS) {
            throw new ServerInstallError('busy', 'another VS Code window is still installing the language server');
        }
        await deps.sleep(INSTALL_POLL_MS);
    }
}

/** Whether the server in an install answers with the version its marker records. */
async function answers(installed: InstalledServer, layout: ServerLayout, deps: ManagedServerDeps): Promise<boolean> {
    try {
        const { stdout } = await deps.run(installed.serverPath, ['--version'], { env: isolatedPythonEnv(deps.env), cwd: layout.root });
        return stdout.trim().split(/\s+/).includes(installed.serverVersion);
    } catch {
        return false;
    }
}

/** The pinned uv, downloaded and checked unless an earlier install left it. */
async function ensureUv(layout: ServerLayout, target: UvTarget, env: NodeJS.ProcessEnv, deps: ManagedServerDeps): Promise<string> {
    if (await deps.fs.exists(layout.uvPath)) {
        try {
            const { stdout } = await deps.run(layout.uvPath, ['--version'], { env, cwd: layout.root });
            if (stdout.trim().startsWith(`uv ${UV_VERSION}`)) {
                return layout.uvPath;
            }
        } catch {
            // Damaged or partial: fetched again below.
        }
    }
    const url = uvDownloadUrl(target);
    deps.log(`Downloading ${url}`);
    const archive = await deps.download(url);
    verifySha256(archive, target.sha256, uvAssetName(target));
    const member = uvArchiveMember(target);
    const binary = target.archive === 'zip' ? extractFromZip(archive, member) : extractFromTarGz(archive, member);
    await deps.fs.mkdir(layout.uvDir, true);
    const partial = `${layout.uvPath}.partial`;
    await deps.fs.writeFile(partial, binary, 0o755);
    await deps.fs.rm(layout.uvPath);
    await deps.fs.rename(partial, layout.uvPath);
    return layout.uvPath;
}

/** The last lines of a failed process's output, for an error message. */
function tail(error: unknown): string {
    const text = error instanceof Error ? error.message : String(error);
    const lines = text.trim().split(/\r?\n/).filter(line => line.trim().length > 0);
    return lines.slice(-6).join('\n');
}

/** The arguments of each uv call, in order; exported for the tests. */
export function uvInstallCommands(layout: ServerLayout, lock: ServerLock, lockPath: string): string[][] {
    return [
        ['venv', '--python', SERVER_PYTHON, '--no-project', layout.envDir(lock.id)],
        [
            'pip', 'install',
            '--python', layout.envPython(lock.id),
            '--require-hashes',
            '--no-build',
            '-r', lockPath,
        ],
    ];
}

/** What an install needs to know. */
export interface InstallRequest {
    readonly layout: ServerLayout;
    readonly lock: ServerLock;
    /** The lock file's path inside the installed extension. */
    readonly lockPath: string;
    /** The uv build for this platform; undefined where the install is not available. */
    readonly target: UvTarget | undefined;
    /** Shown to the user as `platform-arch` when there is no target. */
    readonly platformKey: string;
    onStep?(step: InstallStep): void;
}

/**
 * Install the server for `lock`, or return the install that already exists.
 *
 * Only one window installs at a time; a window that waited returns what the
 * other window installed. The marker that makes an install visible is written
 * last, after the installed server has answered `--version` with the locked
 * version, so a half-finished install is never used: it is removed on failure,
 * and the next attempt starts its folder again.
 */
export async function installManagedServer(request: InstallRequest, deps: ManagedServerDeps): Promise<InstalledServer> {
    const { layout, lock, lockPath, target } = request;
    if (!target) {
        throw new ServerInstallError(
            'unsupported',
            `the extension cannot install its language server on this platform (${request.platformKey})`
        );
    }
    await deps.fs.mkdir(layout.envsDir, true);
    const release = await acquireInstallLock(layout, deps);
    try {
        // An install that finished but no longer answers (a quarantined
        // executable, a removed Python) is installed again, not returned.
        const existing = await readMarker(layout, lock.id, deps);
        if (existing) {
            if (await answers(existing, layout, deps)) {
                return existing;
            }
            deps.log(`The installed server in ${layout.envDir(lock.id)} does not answer; installing it again`);
        }

        const env = uvEnvironment(deps.env, layout, deps.proxy);
        request.onStep?.('uv');
        const uv = await ensureUv(layout, target, env, deps);

        const envDir = layout.envDir(lock.id);
        await deps.fs.rm(envDir);
        try {
            request.onStep?.('server');
            for (const args of uvInstallCommands(layout, lock, lockPath)) {
                deps.log(`Running uv ${args.join(' ')}`);
                try {
                    await deps.run(uv, args, { env, cwd: layout.root });
                } catch (error) {
                    throw new ServerInstallError('server', `uv ${args[0] === 'venv' ? 'could not set up Python' : 'could not install the server'}: ${tail(error)}`);
                }
            }

            request.onStep?.('check');
            const serverPath = layout.serverPath(lock.id);
            let reported: string;
            try {
                reported = (await deps.run(serverPath, ['--version'], { env: isolatedPythonEnv(deps.env), cwd: layout.root })).stdout.trim();
            } catch (error) {
                throw new ServerInstallError('check', `the installed server did not start: ${tail(error)}`);
            }
            if (!reported.split(/\s+/).includes(lock.serverVersion)) {
                throw new ServerInstallError('check', `the installed server reports "${reported}", not version ${lock.serverVersion}`);
            }

            const marker: Marker = {
                lockId: lock.id,
                serverVersion: lock.serverVersion,
                uvVersion: UV_VERSION,
                python: SERVER_PYTHON,
                installedAt: deps.now(),
            };
            const markerPath = layout.markerPath(lock.id);
            await deps.fs.writeFile(`${markerPath}.partial`, JSON.stringify(marker, null, 2));
            await deps.fs.rename(`${markerPath}.partial`, markerPath);
            deps.log(`Installed ${SERVER_PACKAGE} ${lock.serverVersion} at ${envDir}`);
            return { id: lock.id, serverPath, serverVersion: lock.serverVersion, installedAt: marker.installedAt };
        } catch (error) {
            await deps.fs.rm(envDir).catch(cleanup => deps.log(`Could not remove the unfinished install: ${String(cleanup)}`));
            throw error;
        } finally {
            await deps.fs.rm(layout.cacheDir).catch(cleanup => deps.log(`Could not remove uv's cache: ${String(cleanup)}`));
        }
    } finally {
        await release();
    }
}

/**
 * Record that this process runs the server in install `id`, and drop the
 * records it left on any other install.
 *
 * `removeOtherInstalls` keeps an install while a running process holds a
 * lease on it: after an extension update, a window that has not been reloaded
 * still runs the older extension and its older server.
 */
export async function takeLease(layout: ServerLayout, id: string, deps: ManagedServerDeps): Promise<void> {
    const p = deps.platform === 'win32' ? path.win32 : path.posix;
    for (const name of await deps.fs.readdir(layout.leasesDir)) {
        if (name !== id) {
            await deps.fs.rm(p.join(layout.leasesDir, name, String(deps.pid)));
        }
    }
    await deps.fs.mkdir(p.join(layout.leasesDir, id), true);
    await deps.fs.writeFile(p.join(layout.leasesDir, id, String(deps.pid)), String(deps.now()));
}

/** Whether a running process holds a lease on install `id`. */
async function leased(layout: ServerLayout, id: string, deps: ManagedServerDeps): Promise<boolean> {
    const p = deps.platform === 'win32' ? path.win32 : path.posix;
    for (const name of await deps.fs.readdir(p.join(layout.leasesDir, id))) {
        const pid = Number(name);
        if (Number.isInteger(pid) && pid > 0 && deps.isAlive(pid)) {
            return true;
        }
    }
    return false;
}

/**
 * Remove every install other than `keepId` that no running process uses, and
 * every uv but the pinned one.
 *
 * Resolves to the installs removed, or undefined when another window holds the
 * install lock and nothing was looked at. Each folder is renamed aside before
 * it is deleted, so a folder that cannot be deleted whole (on Windows, a file
 * still open) is never left looking like a usable install. Failures are logged;
 * the next window to start the server tries again.
 */
export async function removeOtherInstalls(
    layout: ServerLayout,
    keepId: string,
    deps: ManagedServerDeps
): Promise<string[] | undefined> {
    try {
        await deps.fs.mkdir(layout.lockDir, false);
    } catch {
        return undefined;
    }
    const removed: string[] = [];
    const p = deps.platform === 'win32' ? path.win32 : path.posix;
    try {
        for (const name of await deps.fs.readdir(layout.envsDir)) {
            if (name === keepId) {
                continue;
            }
            const target = p.join(layout.envsDir, name);
            try {
                let doomed = target;
                if (!name.startsWith('.')) {
                    if (await leased(layout, name, deps)) {
                        deps.log(`Keeping the language server install ${name}: another window still runs it`);
                        continue;
                    }
                    doomed = p.join(layout.envsDir, `.removing-${name}-${deps.now()}`);
                    await deps.fs.rename(target, doomed);
                    removed.push(name);
                    await deps.fs.rm(p.join(layout.leasesDir, name));
                }
                await deps.fs.rm(doomed);
            } catch (error) {
                deps.log(`Could not remove the old language server install ${name}: ${String(error)}`);
            }
        }
        for (const version of await deps.fs.readdir(p.join(layout.root, 'uv'))) {
            if (version !== UV_VERSION) {
                await deps.fs.rm(p.join(layout.root, 'uv', version)).catch(error => deps.log(`Could not remove uv ${version}: ${String(error)}`));
            }
        }
    } finally {
        await deps.fs.rm(layout.lockDir);
    }
    return removed;
}
