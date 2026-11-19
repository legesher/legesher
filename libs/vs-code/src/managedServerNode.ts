/**
 * The real effects behind `managedServer.ts`: https downloads, processes and the
 * filesystem, through Node only.
 *
 * Kept free of the `vscode` module so the unit tests can load it, and so a
 * script can run a real install outside an editor.
 */

import { execFile } from 'child_process';
import { existsSync, promises as fsp } from 'fs';
import * as https from 'https';
import type { IncomingMessage } from 'http';
import type { ManagedFs, ManagedServerDeps, RunResult } from './managedServer';

/** The most redirects a download follows; GitHub's release links take one. */
const MAX_REDIRECTS = 5;
/** The largest download accepted; the biggest uv archive is under 20 MB. */
const MAX_DOWNLOAD_BYTES = 64 * 1024 * 1024;
/** A download with no data for this long is abandoned. */
const DOWNLOAD_IDLE_MS = 60_000;
/** A uv step that takes longer than this is abandoned. */
const RUN_TIMEOUT_MS = 15 * 60_000;

/**
 * Where a redirect leads, or an error when it leaves https.
 *
 * Every hop must be https: the archive's checksum is checked anyway, but a
 * download that would cross to plain http is refused before it starts.
 */
export function redirectTarget(from: string, location: string | undefined): string {
    if (!location) {
        throw new Error(`a redirect from ${from} named no location`);
    }
    const next = new URL(location, from);
    if (next.protocol !== 'https:') {
        throw new Error(`refusing to follow a redirect from ${from} to a ${next.protocol} address`);
    }
    return next.toString();
}

/** The bytes at an https URL. */
export function download(url: string, redirects = 0): Promise<Buffer> {
    return new Promise((resolve, reject) => {
        if (new URL(url).protocol !== 'https:') {
            reject(new Error(`refusing to download ${url}: not https`));
            return;
        }
        const request = https.get(url, { headers: { 'User-Agent': 'legesher-vscode' } }, (response: IncomingMessage) => {
            const status = response.statusCode ?? 0;
            if (status >= 300 && status < 400) {
                response.resume();
                if (redirects >= MAX_REDIRECTS) {
                    reject(new Error(`too many redirects downloading ${url}`));
                    return;
                }
                try {
                    resolve(download(redirectTarget(url, response.headers.location), redirects + 1));
                } catch (error) {
                    reject(error);
                }
                return;
            }
            if (status !== 200) {
                response.resume();
                reject(new Error(`downloading ${url} answered HTTP ${status}`));
                return;
            }
            const chunks: Buffer[] = [];
            let received = 0;
            response.on('data', (chunk: Buffer) => {
                received += chunk.length;
                if (received > MAX_DOWNLOAD_BYTES) {
                    request.destroy(new Error(`${url} is larger than ${MAX_DOWNLOAD_BYTES} bytes`));
                    return;
                }
                chunks.push(chunk);
            });
            response.on('end', () => resolve(Buffer.concat(chunks)));
            response.on('error', reject);
        });
        request.setTimeout(DOWNLOAD_IDLE_MS, () => request.destroy(new Error(`downloading ${url} stalled`)));
        request.on('error', reject);
    });
}

/** Run a process with separate arguments and no shell. */
export function run(
    command: string,
    args: readonly string[],
    options: { env: NodeJS.ProcessEnv; cwd: string }
): Promise<RunResult> {
    return new Promise((resolve, reject) => {
        execFile(
            command,
            [...args],
            {
                env: options.env,
                cwd: options.cwd,
                windowsHide: true,
                maxBuffer: 16 * 1024 * 1024,
                timeout: RUN_TIMEOUT_MS,
                encoding: 'utf8',
            },
            (error, stdout, stderr) => {
                if (error) {
                    const detail = [stderr, stdout].map(text => String(text).trim()).filter(Boolean).join('\n');
                    reject(new Error(detail || error.message));
                } else {
                    resolve({ stdout: String(stdout), stderr: String(stderr) });
                }
            }
        );
    });
}

/** The filesystem, through `fs.promises`. */
export const nodeFs: ManagedFs = {
    readFile: file => fsp.readFile(file, 'utf8'),
    writeFile: (file, data, mode) => fsp.writeFile(file, data, mode === undefined ? undefined : { mode }),
    mkdir: async (dir, recursive) => {
        await fsp.mkdir(dir, { recursive });
    },
    rm: target => fsp.rm(target, { recursive: true, force: true, maxRetries: 3 }),
    rename: (from, to) => fsp.rename(from, to),
    readdir: async dir => {
        try {
            return await fsp.readdir(dir);
        } catch (error) {
            if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
                return [];
            }
            throw error;
        }
    },
    exists: async target => {
        try {
            await fsp.access(target);
            return true;
        } catch {
            return false;
        }
    },
};

/**
 * Whether this Linux machine's C library is musl (Alpine and other small
 * container images), by the dynamic loader musl installs.
 */
export function isMusl(platform: string, exists: (file: string) => boolean = existsSync): boolean {
    return platform === 'linux' && (exists('/lib/ld-musl-x86_64.so.1') || exists('/lib/ld-musl-aarch64.so.1'));
}

/**
 * Whether a process with this id is running. Signal 0 checks without
 * signalling, on Windows too; EPERM means it runs as another user.
 */
export function isAlive(pid: number): boolean {
    try {
        process.kill(pid, 0);
        return true;
    } catch (error) {
        return (error as NodeJS.ErrnoException).code === 'EPERM';
    }
}

/** The real effects, logging through `log`. */
export function nodeManagedServerDeps(options: { log(message: string): void; proxy?: string }): ManagedServerDeps {
    return {
        platform: process.platform,
        env: process.env,
        proxy: options.proxy,
        download: url => download(url),
        run,
        fs: nodeFs,
        now: () => Date.now(),
        sleep: ms => new Promise(resolve => setTimeout(resolve, ms)),
        every: (ms, tick) => {
            const timer = setInterval(tick, ms);
            timer.unref?.();
            return () => clearInterval(timer);
        },
        pid: process.pid,
        isAlive,
        log: options.log,
    };
}
