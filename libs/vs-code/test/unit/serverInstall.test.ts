/**
 * Unit tests for the server-not-found message (CORE-2203).
 *
 * The message makes a claim about two other files: that `legesher-lsp` is the
 * setting's default, and that the `legesher-language-server` package is what
 * installs it. Both are read from those files here, so renaming the package or
 * the console script fails this test instead of sending users after a name
 * that does not exist.
 */

import * as assert from 'assert';
import * as fs from 'fs';
import * as path from 'path';
import {
    DEFAULT_SERVER_COMMAND,
    SERVER_PACKAGE,
    serverNotFoundMessage,
} from '../../src/serverInstall';

const EXTENSION_ROOT = path.resolve(__dirname, '..', '..');
const SERVER_PYPROJECT = path.resolve(EXTENSION_ROOT, '..', 'language-server', 'pyproject.toml');

/** The body of one `[table]` in a TOML file, up to the next table header. */
function tomlTable(text: string, table: string): string {
    const start = text.indexOf(`[${table}]\n`);
    assert.ok(start >= 0, `no [${table}] in ${SERVER_PYPROJECT}`);
    const body = text.slice(start + table.length + 3);
    const end = body.search(/^\[/m);
    return end < 0 ? body : body.slice(0, end);
}

describe('serverInstall', () => {
    it('uses the default that package.json declares for legesher.serverCommand', () => {
        const manifest = JSON.parse(fs.readFileSync(path.join(EXTENSION_ROOT, 'package.json'), 'utf8'));
        const setting = manifest.contributes.configuration.properties['legesher.serverCommand'];
        assert.strictEqual(setting.default, DEFAULT_SERVER_COMMAND);
    });

    it('names the Python package that actually installs that command', () => {
        const pyproject = fs.readFileSync(SERVER_PYPROJECT, 'utf8');
        assert.match(tomlTable(pyproject, 'project'), new RegExp(`^name = "${SERVER_PACKAGE}"$`, 'm'));
        assert.match(
            tomlTable(pyproject, 'project.scripts'),
            new RegExp(`^${DEFAULT_SERVER_COMMAND} = "`, 'm'),
        );
    });

    it('tells someone on the default what to install, and why', () => {
        const message = serverNotFoundMessage(DEFAULT_SERVER_COMMAND);
        assert.ok(message.includes(SERVER_PACKAGE), message);
        assert.ok(message.includes(DEFAULT_SERVER_COMMAND), message);
        assert.ok(message.includes('legesher.serverCommand'), message);
        assert.ok(message.includes('Hover, completion, diagnostics and keyword highlighting'), message);
        assert.ok(message.includes('extension README'), message);
    });

    it('points someone with a custom command back at their setting', () => {
        const message = serverNotFoundMessage('/opt/tools/legesher-lsp-dev');
        assert.ok(message.includes('"/opt/tools/legesher-lsp-dev"'), message);
        assert.ok(message.includes('legesher.serverCommand'), message);
        assert.ok(message.includes(SERVER_PACKAGE), message);
        assert.ok(message.includes('extension README'), message);
    });

    // The message ships inside the extension, so an install command in it
    // could only be corrected by an extension release. Until the package is
    // on PyPI no such command works; the README carries it instead (CORE-2203).
    it('gives no install command', () => {
        for (const command of [DEFAULT_SERVER_COMMAND, '/opt/tools/legesher-lsp-dev']) {
            const message = serverNotFoundMessage(command);
            assert.doesNotMatch(message, /\b(pip|pipx|uv)\s+(install|tool)\b|\bpip install\b/, message);
        }
    });
});
