/**
 * Unit tests for the real effects behind the extension's server install.
 *
 * `run` is exercised for real, against Node itself, because the property that
 * matters (arguments reach the process exactly, with no shell between) is one
 * only a real process can show. Nothing here touches the network.
 */

import * as assert from 'assert';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import { download, isAlive, isMusl, nodeFs, redirectTarget, run } from '../../src/managedServerNode';

describe('managedServerNode', () => {
    describe('redirectTarget', () => {
        it('resolves a relative location against the https address it came from', () => {
            assert.strictEqual(
                redirectTarget('https://github.com/astral-sh/uv/releases/download/0.13.7/uv.zip', '/objects/1'),
                'https://github.com/objects/1'
            );
        });

        it('follows an https location on another host', () => {
            assert.strictEqual(
                redirectTarget('https://github.com/a', 'https://release-assets.githubusercontent.com/b?x=1'),
                'https://release-assets.githubusercontent.com/b?x=1'
            );
        });

        it('refuses a redirect to plain http, or to nowhere', () => {
            assert.throws(() => redirectTarget('https://github.com/a', 'http://example.invalid/uv.zip'), /http: address/);
            assert.throws(() => redirectTarget('https://github.com/a', undefined), /named no location/);
        });
    });

    it('download refuses a plain http address before connecting', async () => {
        await assert.rejects(download('http://example.invalid/uv.tar.gz'), /not https/);
    });

    it('isMusl looks for the musl loader, on Linux only', () => {
        const present = (file: string) => file === '/lib/ld-musl-x86_64.so.1';
        assert.strictEqual(isMusl('linux', present), true);
        assert.strictEqual(isMusl('linux', () => false), false);
        assert.strictEqual(isMusl('darwin', present), false);
    });

    it('isAlive sees this process, and not one that has exited', async () => {
        assert.strictEqual(isAlive(process.pid), true);
        const child = require('child_process').spawn(process.execPath, ['-e', '0']);
        const pid: number = child.pid;
        await new Promise(resolve => child.on('exit', resolve));
        assert.strictEqual(isAlive(pid), false);
    });

    describe('run', () => {
        // Characters a shell would expand, split or stop at, and scripts with
        // combining marks.
        const args = [
            'two words',
            '$HOME; echo injected',
            '"quoted" \'single\' `tick`',
            'देवनागरी ශ්‍රී שָׁלוֹם عَرَبِيّ ภาษาไทย 漢字',
            '',
        ];

        it('hands each argument to the process exactly as given', async () => {
            const { stdout } = await run(
                process.execPath,
                ['-e', 'process.stdout.write(JSON.stringify(process.argv.slice(1)))', ...args],
                { env: process.env, cwd: os.tmpdir() }
            );
            assert.deepStrictEqual(JSON.parse(stdout), args);
        });

        it('rejects with what the process wrote to stderr', async () => {
            await assert.rejects(
                run(process.execPath, ['-e', 'process.stderr.write("Hash mismatch for `pygls`"); process.exit(2)'],
                    { env: process.env, cwd: os.tmpdir() }),
                /Hash mismatch for `pygls`/
            );
        });
    });

    describe('nodeFs', () => {
        let dir: string;
        beforeEach(() => {
            dir = fs.mkdtempSync(path.join(os.tmpdir(), 'legesher देवनागरी '));
        });
        afterEach(() => fs.rmSync(dir, { recursive: true, force: true }));

        it('lists a missing folder as empty', async () => {
            assert.deepStrictEqual(await nodeFs.readdir(path.join(dir, 'missing')), []);
        });

        it('reports EEXIST for a lock folder that is already taken', async () => {
            const lock = path.join(dir, 'install.lock');
            await nodeFs.mkdir(lock, false);
            await assert.rejects(nodeFs.mkdir(lock, false), (error: NodeJS.ErrnoException) => error.code === 'EEXIST');
        });

        it('writes an executable mode and removes folders whole', async () => {
            const file = path.join(dir, 'ශ්‍රී', 'uv');
            await nodeFs.mkdir(path.dirname(file), true);
            await nodeFs.writeFile(file, Buffer.from('x'), 0o755);
            if (process.platform !== 'win32') {
                assert.strictEqual(fs.statSync(file).mode & 0o777, 0o755);
            }
            await nodeFs.rm(path.dirname(file));
            assert.strictEqual(await nodeFs.exists(file), false);
            await nodeFs.rm(path.join(dir, 'never-there'));
        });
    });
});
