/**
 * Read one file out of a downloaded uv release archive.
 *
 * The extension needs exactly one file from the archive, the uv executable, so
 * this reads that member into memory rather than unpacking anything to disk: no
 * external `tar` or `unzip` (Windows' own `tar.exe` and the GNU `tar` that Git
 * for Windows puts first on PATH disagree about drive letters), and no member
 * path from the archive is ever joined onto a directory. The archive's SHA-256
 * is checked before it reaches this module.
 *
 * Kept free of the `vscode` module so the unit tests can load it.
 */

import * as zlib from 'zlib';

const TAR_BLOCK = 512;

/** NUL-terminated ASCII field of a tar header. */
function tarString(header: Buffer, start: number, length: number): string {
    const field = header.subarray(start, start + length);
    const end = field.indexOf(0);
    return field.subarray(0, end < 0 ? field.length : end).toString('utf8');
}

/** The size field of a tar header: octal ASCII, which every uv archive uses. */
function tarSize(header: Buffer): number {
    const field = tarString(header, 124, 12).trim();
    if (!/^[0-7]+$/.test(field)) {
        throw new Error(`unreadable tar entry size "${field}"`);
    }
    return parseInt(field, 8);
}

/** The `path` record of a pax extended header, if it has one. */
function paxPath(data: Buffer): string | undefined {
    let offset = 0;
    while (offset < data.length) {
        const space = data.indexOf(0x20, offset);
        if (space < 0) {
            break;
        }
        const length = parseInt(data.subarray(offset, space).toString('ascii'), 10);
        if (!Number.isFinite(length) || length <= 0) {
            break;
        }
        const record = data.subarray(space + 1, offset + length - 1).toString('utf8');
        const equals = record.indexOf('=');
        if (equals > 0 && record.slice(0, equals) === 'path') {
            return record.slice(equals + 1);
        }
        offset += length;
    }
    return undefined;
}

/** Member names compare without a leading `./`, as tar writers differ on it. */
function sameMember(name: string, member: string): boolean {
    return name.replace(/^\.\//, '') === member;
}

/**
 * The contents of `member` in a gzip-compressed tar archive.
 *
 * Reads ustar and GNU headers, with long names in a GNU `L` record or a pax
 * `path` record. Throws when the member is missing or is not a regular file.
 */
export function extractFromTarGz(archive: Buffer, member: string): Buffer {
    const tar = zlib.gunzipSync(archive);
    let offset = 0;
    let longName: string | undefined;

    while (offset + TAR_BLOCK <= tar.length) {
        const header = tar.subarray(offset, offset + TAR_BLOCK);
        if (header.every(byte => byte === 0)) {
            break;
        }
        const size = tarSize(header);
        const type = String.fromCharCode(header[156] || 0x30);
        const dataStart = offset + TAR_BLOCK;
        const data = tar.subarray(dataStart, dataStart + size);
        if (data.length < size) {
            throw new Error('the tar archive ends inside an entry');
        }
        offset = dataStart + Math.ceil(size / TAR_BLOCK) * TAR_BLOCK;

        if (type === 'L') {
            longName = tarString(data, 0, data.length);
            continue;
        }
        if (type === 'x') {
            longName = paxPath(data) ?? longName;
            continue;
        }

        const prefix = tarString(header, 345, 155);
        const shortName = tarString(header, 0, 100);
        const name = longName ?? (prefix ? `${prefix}/${shortName}` : shortName);
        longName = undefined;

        if (sameMember(name, member)) {
            if (type !== '0') {
                throw new Error(`"${member}" in the archive is not a regular file`);
            }
            return Buffer.from(data);
        }
    }
    throw new Error(`"${member}" is not in the archive`);
}

const ZIP_END = 0x06054b50;
const ZIP_CENTRAL = 0x02014b50;
const ZIP_LOCAL = 0x04034b50;

/**
 * The contents of `member` in a zip archive.
 *
 * Reads the central directory, then the member's local header; supports the
 * stored and deflated methods, and not zip64, which no uv archive needs.
 * Throws when the member is missing or its size disagrees with the directory.
 */
export function extractFromZip(archive: Buffer, member: string): Buffer {
    // The end-of-central-directory record sits in the last 22 bytes plus at
    // most a 65,535-byte comment.
    let end = -1;
    for (let i = archive.length - 22; i >= Math.max(0, archive.length - 22 - 0xffff); i--) {
        if (archive.readUInt32LE(i) === ZIP_END) {
            end = i;
            break;
        }
    }
    if (end < 0) {
        throw new Error('not a zip archive');
    }
    const entries = archive.readUInt16LE(end + 10);
    let offset = archive.readUInt32LE(end + 16);
    if (entries === 0xffff || offset === 0xffffffff) {
        throw new Error('zip64 archives are not supported');
    }

    for (let i = 0; i < entries; i++) {
        if (archive.readUInt32LE(offset) !== ZIP_CENTRAL) {
            throw new Error('the zip central directory is damaged');
        }
        const method = archive.readUInt16LE(offset + 10);
        const compressedSize = archive.readUInt32LE(offset + 20);
        const size = archive.readUInt32LE(offset + 24);
        const nameLength = archive.readUInt16LE(offset + 28);
        const extraLength = archive.readUInt16LE(offset + 30);
        const commentLength = archive.readUInt16LE(offset + 32);
        const localOffset = archive.readUInt32LE(offset + 42);
        const name = archive.subarray(offset + 46, offset + 46 + nameLength).toString('utf8').replace(/\\/g, '/');
        offset += 46 + nameLength + extraLength + commentLength;

        if (!sameMember(name, member)) {
            continue;
        }
        if (archive.readUInt32LE(localOffset) !== ZIP_LOCAL) {
            throw new Error(`the zip entry for "${member}" is damaged`);
        }
        const dataStart = localOffset + 30 + archive.readUInt16LE(localOffset + 26) + archive.readUInt16LE(localOffset + 28);
        const compressed = archive.subarray(dataStart, dataStart + compressedSize);
        let contents: Buffer;
        if (method === 0) {
            contents = Buffer.from(compressed);
        } else if (method === 8) {
            contents = zlib.inflateRawSync(compressed);
        } else {
            throw new Error(`"${member}" uses zip compression method ${method}, which is not supported`);
        }
        if (contents.length !== size) {
            throw new Error(`"${member}" unpacked to ${contents.length} bytes, not the ${size} the archive records`);
        }
        return contents;
    }
    throw new Error(`"${member}" is not in the archive`);
}
