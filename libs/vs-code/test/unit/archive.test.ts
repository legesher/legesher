/**
 * Unit tests for reading the uv executable out of a release archive.
 *
 * The archives are built here in the formats' own terms (see
 * support/archives.ts). The real uv archives were also read with this module
 * by hand when it was written; the PR records that run.
 */

import * as assert from 'assert';
import { extractFromTarGz, extractFromZip } from '../../src/archive';
import { makeTarGz, makeZip, paxPathRecord } from './support/archives';

/** Bytes that are not text, so a decode-and-re-encode would change them. */
const BINARY = Buffer.from([0x7f, 0x45, 0x4c, 0x46, 0x00, 0xff, 0xfe, 0x80, 0x0a, 0x0d, 0x00]);

describe('archive', () => {
    describe('extractFromTarGz', () => {
        it('returns the member byte for byte from the folder uv packs it in', () => {
            const archive = makeTarGz([
                { name: 'uv-x86_64-unknown-linux-gnu/', type: '5' },
                { name: 'uv-x86_64-unknown-linux-gnu/uvx', data: Buffer.from('not this one') },
                { name: 'uv-x86_64-unknown-linux-gnu/uv', data: BINARY },
            ]);
            assert.deepStrictEqual(extractFromTarGz(archive, 'uv-x86_64-unknown-linux-gnu/uv'), BINARY);
        });

        it('spans entries larger than one block', () => {
            const big = Buffer.alloc(512 * 3 + 7, 0xab);
            const archive = makeTarGz([
                { name: 'a/filler', data: Buffer.alloc(1000, 1) },
                { name: 'a/uv', data: big },
            ]);
            assert.deepStrictEqual(extractFromTarGz(archive, 'a/uv'), big);
        });

        it('matches a member written with a leading ./', () => {
            const archive = makeTarGz([{ name: './a/uv', data: BINARY }]);
            assert.deepStrictEqual(extractFromTarGz(archive, 'a/uv'), BINARY);
        });

        it('reads a GNU long name', () => {
            const long = `${'d'.repeat(120)}/uv`;
            const archive = makeTarGz([
                { name: '././@LongLink', type: 'L', data: Buffer.from(`${long}\0`) },
                { name: long.slice(0, 100), data: BINARY },
            ]);
            assert.deepStrictEqual(extractFromTarGz(archive, long), BINARY);
        });

        it('reads a pax path, in a script with combining marks, byte for byte', () => {
            // Devanagari with a virama, and Sinhala with a ZWJ conjunct.
            const name = 'देवनागरी-ශ්‍රී/uv';
            const archive = makeTarGz([
                { name: 'PaxHeader', type: 'x', data: paxPathRecord(name) },
                { name: 'placeholder', data: BINARY },
            ]);
            assert.deepStrictEqual(extractFromTarGz(archive, name), BINARY);
        });

        it('names the member when it is missing', () => {
            const archive = makeTarGz([{ name: 'a/uvx', data: BINARY }]);
            assert.throws(() => extractFromTarGz(archive, 'a/uv'), /"a\/uv" is not in the archive/);
        });

        it('refuses a member that is not a regular file', () => {
            const archive = makeTarGz([{ name: 'a/uv', type: '5' }]);
            assert.throws(() => extractFromTarGz(archive, 'a/uv'), /not a regular file/);
        });

        it('refuses an archive cut short inside the member', () => {
            const whole = makeTarGz([{ name: 'a/uv', data: Buffer.alloc(4096, 1) }]);
            const tar = require('zlib').gunzipSync(whole) as Buffer;
            const cut = require('zlib').gzipSync(tar.subarray(0, 512 + 100)) as Buffer;
            assert.throws(() => extractFromTarGz(cut, 'a/uv'), /ends inside an entry/);
        });
    });

    describe('extractFromZip', () => {
        it('returns a deflated member byte for byte from the archive root', () => {
            const archive = makeZip([
                { name: 'uvx.exe', data: Buffer.from('not this one') },
                { name: 'uv.exe', data: BINARY },
            ]);
            assert.deepStrictEqual(extractFromZip(archive, 'uv.exe'), BINARY);
        });

        it('returns a stored member', () => {
            const archive = makeZip([{ name: 'uv.exe', data: BINARY, method: 0 }]);
            assert.deepStrictEqual(extractFromZip(archive, 'uv.exe'), BINARY);
        });

        it('names the member when it is missing', () => {
            const archive = makeZip([{ name: 'uvw.exe', data: BINARY }]);
            assert.throws(() => extractFromZip(archive, 'uv.exe'), /"uv.exe" is not in the archive/);
        });

        it('refuses a member whose size disagrees with the directory', () => {
            const archive = makeZip([{ name: 'uv.exe', data: BINARY, recordedSize: BINARY.length + 1 }]);
            assert.throws(() => extractFromZip(archive, 'uv.exe'), /unpacked to 11 bytes, not the 12/);
        });

        it('refuses something that is not a zip', () => {
            assert.throws(() => extractFromZip(Buffer.alloc(64, 7), 'uv.exe'), /not a zip archive/);
        });
    });
});
