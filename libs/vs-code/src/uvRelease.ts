/**
 * The uv release the extension downloads to install its own language server.
 *
 * uv is pinned to one release, and each archive the extension may download is
 * pinned to its SHA-256. The checksums were read from the release's
 * `sha256.sum` and from GitHub's own digest of each asset, which agreed. A
 * download whose bytes do not hash to the value here is refused before
 * anything is extracted from it. The pinned uv in turn checks the Python it
 * downloads against the checksums built into that uv release, and the server's
 * packages against `server/requirements.lock`, so every byte the install
 * fetches is checked against a value that ships inside the extension.
 *
 * To move to a newer uv: change `UV_VERSION`, and replace every checksum below
 * with the matching line of that release's `sha256.sum`.
 *
 * Kept free of the `vscode` module so the unit tests can load it.
 */

/** The pinned uv release. */
export const UV_VERSION = '0.13.7';

/** How a uv release archive is packed. */
export type UvArchive = 'tar.gz' | 'zip';

/** One platform's uv release archive. */
export interface UvTarget {
    /** The Rust target triple uv names its release assets by. */
    readonly triple: string;
    readonly archive: UvArchive;
    /** SHA-256 of the archive, lowercase hex. */
    readonly sha256: string;
}

/**
 * The platforms the extension can install its server on, keyed by
 * `uvTargetKey`.
 *
 * Windows on ARM is absent on purpose: `lru-dict`, which the server requires,
 * publishes no wheel for it, and the install never compiles anything. Such a
 * machine is told the install is not available there and pointed at the manual
 * steps.
 */
export const UV_TARGETS: Readonly<Record<string, UvTarget>> = {
    'darwin-arm64': {
        triple: 'aarch64-apple-darwin',
        archive: 'tar.gz',
        sha256: '81b811b57e4624df7ed3aac148e0359100d9962f3d9dce00aec533dc2e086731',
    },
    'darwin-x64': {
        triple: 'x86_64-apple-darwin',
        archive: 'tar.gz',
        sha256: '20c47e4c1f630b8abaff8c291fa9b9aa300fef92c4fbff95adf198b55287cda7',
    },
    'linux-arm64': {
        triple: 'aarch64-unknown-linux-gnu',
        archive: 'tar.gz',
        sha256: '71279f8d3c67241e807b9d8db872d1bf541579fb9f08b7d1eb1682196d1e57dc',
    },
    'linux-x64': {
        triple: 'x86_64-unknown-linux-gnu',
        archive: 'tar.gz',
        sha256: 'c5221ff41b7892bfc223543883600125f6a47fe845093e0f5bdff4f359196d83',
    },
    'linux-arm64-musl': {
        triple: 'aarch64-unknown-linux-musl',
        archive: 'tar.gz',
        sha256: '2d3ec076a0c4c0e8250bb6418c44080828b544f1a3be0b6e46adf9fb6923de45',
    },
    'linux-x64-musl': {
        triple: 'x86_64-unknown-linux-musl',
        archive: 'tar.gz',
        sha256: '287491da03f2a785c70fa75b13e1f849918c2f2b5415fe84876b8214eeb792f9',
    },
    'win32-x64': {
        triple: 'x86_64-pc-windows-msvc',
        archive: 'zip',
        sha256: '0cdc5b38fe5a8168ed6a25814f5ba43c21d313dd3187314fccb37b7cec46e021',
    },
};

/**
 * The key a platform is looked up by in `UV_TARGETS`.
 *
 * @param platform `process.platform`.
 * @param arch `process.arch`.
 * @param musl Whether a Linux machine's C library is musl (Alpine and other
 *   small container images), which needs uv's separate musl build.
 */
export function uvTargetKey(platform: string, arch: string, musl: boolean): string {
    return platform === 'linux' && musl ? `${platform}-${arch}-musl` : `${platform}-${arch}`;
}

/** The uv archive for this platform, or undefined where the install is not available. */
export function uvTargetFor(platform: string, arch: string, musl: boolean): UvTarget | undefined {
    return UV_TARGETS[uvTargetKey(platform, arch, musl)];
}

/** The release asset's file name, as uv publishes it. */
export function uvAssetName(target: UvTarget): string {
    return `uv-${target.triple}.${target.archive}`;
}

/** Where the pinned release asset is downloaded from. */
export function uvDownloadUrl(target: UvTarget): string {
    return `https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/${uvAssetName(target)}`;
}

/** The uv executable's name on this platform. */
export function uvExecutableName(platform: string): string {
    return platform === 'win32' ? 'uv.exe' : 'uv';
}

/**
 * The path of the uv executable inside the archive: the tarballs keep it in a
 * folder named after the target, the Windows zip at its root.
 */
export function uvArchiveMember(target: UvTarget): string {
    return target.archive === 'zip' ? 'uv.exe' : `uv-${target.triple}/uv`;
}
