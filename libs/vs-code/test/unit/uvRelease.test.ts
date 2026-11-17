/**
 * Unit tests for the pinned uv release table.
 *
 * The checksums themselves cannot be checked without the network; what is
 * checked is that every entry has the shape a real checksum and a real asset
 * name have, so a truncated hash or a mistyped triple fails here rather than
 * on someone's first install.
 */

import * as assert from 'assert';
import {
    UV_TARGETS,
    UV_VERSION,
    uvArchiveMember,
    uvAssetName,
    uvDownloadUrl,
    uvExecutableName,
    uvTargetFor,
    uvTargetKey,
} from '../../src/uvRelease';

describe('uvRelease', () => {
    it('pins one exact uv release', () => {
        assert.match(UV_VERSION, /^\d+\.\d+\.\d+$/);
    });

    for (const [key, target] of Object.entries(UV_TARGETS)) {
        describe(key, () => {
            it('has a full lowercase SHA-256', () => {
                assert.match(target.sha256, /^[0-9a-f]{64}$/);
            });

            it('names an asset uv publishes', () => {
                assert.match(
                    uvAssetName(target),
                    /^uv-(aarch64|x86_64)-(apple-darwin|unknown-linux-gnu|unknown-linux-musl|pc-windows-msvc)\.(tar\.gz|zip)$/
                );
                // uv ships Windows as a zip and everything else as a tarball.
                assert.strictEqual(target.archive === 'zip', target.triple.endsWith('windows-msvc'));
            });

            it('downloads over https from the pinned GitHub release', () => {
                assert.strictEqual(
                    uvDownloadUrl(target),
                    `https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/${uvAssetName(target)}`
                );
            });

            it('is keyed by the platform its triple is built for', () => {
                const [platform, arch] = key.split('-');
                const triple = target.triple;
                assert.strictEqual(triple.startsWith(arch === 'arm64' ? 'aarch64-' : 'x86_64-'), true, triple);
                const os = { darwin: 'apple-darwin', linux: 'unknown-linux', win32: 'pc-windows' }[platform];
                assert.ok(os && triple.includes(os), triple);
                assert.strictEqual(key.endsWith('-musl'), triple.endsWith('-musl'), triple);
            });
        });
    }

    it('covers macOS, glibc and musl Linux, and Windows on x64', () => {
        assert.strictEqual(uvTargetFor('darwin', 'arm64', false)?.triple, 'aarch64-apple-darwin');
        assert.strictEqual(uvTargetFor('darwin', 'x64', false)?.triple, 'x86_64-apple-darwin');
        assert.strictEqual(uvTargetFor('linux', 'x64', false)?.triple, 'x86_64-unknown-linux-gnu');
        assert.strictEqual(uvTargetFor('linux', 'arm64', false)?.triple, 'aarch64-unknown-linux-gnu');
        assert.strictEqual(uvTargetFor('linux', 'x64', true)?.triple, 'x86_64-unknown-linux-musl');
        assert.strictEqual(uvTargetFor('linux', 'arm64', true)?.triple, 'aarch64-unknown-linux-musl');
        assert.strictEqual(uvTargetFor('win32', 'x64', false)?.triple, 'x86_64-pc-windows-msvc');
    });

    it('only Linux has a musl build', () => {
        assert.strictEqual(uvTargetKey('darwin', 'arm64', true), 'darwin-arm64');
        assert.strictEqual(uvTargetKey('linux', 'arm64', true), 'linux-arm64-musl');
    });

    // lru-dict, which the server requires, has no Windows on ARM wheel, and
    // the install never compiles. Offering it there would always fail.
    it('offers no install on Windows on ARM or an unknown platform', () => {
        assert.strictEqual(uvTargetFor('win32', 'arm64', false), undefined);
        assert.strictEqual(uvTargetFor('freebsd', 'x64', false), undefined);
        assert.strictEqual(uvTargetFor('linux', 'ia32', false), undefined);
    });

    it('finds the executable where each archive keeps it', () => {
        assert.strictEqual(uvArchiveMember(UV_TARGETS['win32-x64']), 'uv.exe');
        assert.strictEqual(uvArchiveMember(UV_TARGETS['darwin-arm64']), 'uv-aarch64-apple-darwin/uv');
        assert.strictEqual(uvExecutableName('win32'), 'uv.exe');
        assert.strictEqual(uvExecutableName('linux'), 'uv');
    });
});
