/**
 * Unit tests for settings-scope precedence (CORE-1776).
 *
 * The picker used to write `ConfigurationTarget.Global` unconditionally while
 * resolution honoured folder/workspace precedence, so a workspace-level
 * `legesher.targetLanguage` silently swallowed every pick. These tests pin the
 * precedence rule that both the reader and the writer now share.
 */

import * as assert from 'assert';
import { scopeOf } from '../../src/settingsScope';

describe('Settings scope precedence (CORE-1776)', () => {
    it('reports default when the setting is unset everywhere', () => {
        assert.strictEqual(scopeOf({}), 'default');
    });

    it('reports default when inspect() itself returns undefined', () => {
        // A mocked or unregistered setting can inspect to undefined; that must
        // not throw, and "nothing set" is the honest answer.
        assert.strictEqual(scopeOf(undefined), 'default');
    });

    it('reports user for a global value', () => {
        assert.strictEqual(scopeOf({ globalValue: 'es' }), 'user');
    });

    it('reports workspace for a workspace value', () => {
        assert.strictEqual(scopeOf({ workspaceValue: 'de' }), 'workspace');
    });

    it('reports folder for a workspace-folder value', () => {
        assert.strictEqual(scopeOf({ workspaceFolderValue: 'fr' }), 'folder');
    });

    it('prefers workspace over user', () => {
        assert.strictEqual(
            scopeOf({ globalValue: 'es', workspaceValue: 'de' }),
            'workspace'
        );
    });

    it('prefers folder over workspace and user', () => {
        // The demo-repo shape: a committed workspace setting plus the user's own
        // global preference plus a per-folder override.
        assert.strictEqual(
            scopeOf({ globalValue: 'es', workspaceValue: 'de', workspaceFolderValue: 'fr' }),
            'folder'
        );
    });

    it('treats an explicitly set falsy value as set', () => {
        // `''` and `false` are legitimate stored values. Testing truthiness
        // rather than `!== undefined` would report the wrong scope and send the
        // write to a scope that loses to the one actually in effect.
        assert.strictEqual(scopeOf({ workspaceValue: '' }), 'workspace');
        assert.strictEqual(scopeOf<boolean>({ globalValue: false }), 'user');
    });
});
