/**
 * Builders for the tar.gz and zip archives the unit tests feed the extractor.
 *
 * Written out by hand from the formats rather than produced by `tar` or `zip`,
 * so the tests need no external tool and can build the shapes a real archive
 * may have (GNU long names, pax headers, stored and deflated zip entries).
 */

import * as zlib from 'zlib';

export interface TarEntry {
    name: string;
    data?: Buffer;
    /** The tar type flag: '0' file (the default), '5' directory, 'L' GNU long name, 'x' pax header. */
    type?: string;
}

function octal(value: number, width: number): string {
    return value.toString(8).padStart(width - 1, '0') + '\0';
}

function tarHeader(name: string, size: number, type: string): Buffer {
    const header = Buffer.alloc(512);
    header.write(name.slice(0, 100), 0, 'utf8');
    header.write(octal(0o755, 8), 100, 'ascii');
    header.write(octal(0, 8), 108, 'ascii');
    header.write(octal(0, 8), 116, 'ascii');
    header.write(octal(size, 12), 124, 'ascii');
    header.write(octal(0, 12), 136, 'ascii');
    header.write(type, 156, 'ascii');
    header.write('ustar\0', 257, 'ascii');
    header.write('00', 263, 'ascii');
    header.fill(0x20, 148, 156);
    let sum = 0;
    for (const byte of header) {
        sum += byte;
    }
    header.write(octal(sum, 7) + ' ', 148, 'ascii');
    return header;
}

/** A gzip-compressed tar archive holding `entries`, in order. */
export function makeTarGz(entries: TarEntry[]): Buffer {
    const blocks: Buffer[] = [];
    for (const entry of entries) {
        const data = entry.data ?? Buffer.alloc(0);
        blocks.push(tarHeader(entry.name, data.length, entry.type ?? '0'));
        blocks.push(data);
        const pad = (512 - (data.length % 512)) % 512;
        blocks.push(Buffer.alloc(pad));
    }
    blocks.push(Buffer.alloc(1024));
    return zlib.gzipSync(Buffer.concat(blocks));
}

/** A pax extended header body setting `path`. */
export function paxPathRecord(value: string): Buffer {
    const body = ` path=${value}\n`;
    // The length prefix counts itself, so settle it by iterating.
    let length = Buffer.byteLength(body) + 1;
    while (String(length).length + Buffer.byteLength(body) !== length) {
        length = String(length).length + Buffer.byteLength(body);
    }
    return Buffer.from(`${length}${body}`, 'utf8');
}

export interface ZipEntry {
    name: string;
    data: Buffer;
    /** Deflate (8, the default) or store (0). */
    method?: 0 | 8;
    /** Overrides the uncompressed size the directory records, to fake damage. */
    recordedSize?: number;
}

/** A zip archive holding `entries`. */
export function makeZip(entries: ZipEntry[]): Buffer {
    const locals: Buffer[] = [];
    const centrals: Buffer[] = [];
    let offset = 0;
    for (const entry of entries) {
        const method = entry.method ?? 8;
        const name = Buffer.from(entry.name, 'utf8');
        const body = method === 8 ? zlib.deflateRawSync(entry.data) : entry.data;
        const size = entry.recordedSize ?? entry.data.length;

        const local = Buffer.alloc(30);
        local.writeUInt32LE(0x04034b50, 0);
        local.writeUInt16LE(20, 4);
        local.writeUInt16LE(0x0800, 6);
        local.writeUInt16LE(method, 8);
        local.writeUInt32LE(body.length, 18);
        local.writeUInt32LE(size, 22);
        local.writeUInt16LE(name.length, 26);
        locals.push(local, name, body);

        const central = Buffer.alloc(46);
        central.writeUInt32LE(0x02014b50, 0);
        central.writeUInt16LE(20, 4);
        central.writeUInt16LE(20, 6);
        central.writeUInt16LE(0x0800, 8);
        central.writeUInt16LE(method, 10);
        central.writeUInt32LE(body.length, 20);
        central.writeUInt32LE(size, 24);
        central.writeUInt16LE(name.length, 28);
        central.writeUInt32LE(offset, 42);
        centrals.push(central, name);

        offset += local.length + name.length + body.length;
    }
    const directory = Buffer.concat(centrals);
    const end = Buffer.alloc(22);
    end.writeUInt32LE(0x06054b50, 0);
    end.writeUInt16LE(entries.length, 8);
    end.writeUInt16LE(entries.length, 10);
    end.writeUInt32LE(directory.length, 12);
    end.writeUInt32LE(offset, 16);
    return Buffer.concat([...locals, directory, end]);
}
