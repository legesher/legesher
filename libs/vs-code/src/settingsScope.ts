/**
 * Which configuration scope supplies a setting's value (CORE-1776).
 *
 * VS Code resolves a setting by precedence — folder > workspace > user >
 * default — and `get()` hands back the winner without saying who won. Both the
 * reader and the writer need to know: the status bar reports where the language
 * came from, and the language picker has to write at the scope that is actually
 * in effect. Writing `Global` while a workspace value wins is a silent no-op
 * dressed up as success, which is the bug this module exists to prevent.
 *
 * Deliberately has no `vscode` import: the precedence rule is pure over an
 * inspect() result, so it is unit-testable without an editor host.
 */

/** The configuration scope a value came from, narrowest first. */
export type SettingScope = 'folder' | 'workspace' | 'user' | 'default';

/**
 * The subset of `WorkspaceConfiguration.inspect()` that decides precedence.
 *
 * Structural rather than imported so this module stays free of `vscode`; a real
 * inspect() result satisfies it.
 */
export interface InspectedSetting<T> {
    workspaceFolderValue?: T;
    workspaceValue?: T;
    globalValue?: T;
}

/**
 * Report which scope currently supplies the value.
 *
 * Tests each scope for *being set* (`!== undefined`) rather than for
 * truthiness. `''` and `false` are legitimate stored values, and treating them
 * as unset would report a wider scope than the one in effect — sending a write
 * to a scope that the real one shadows, which is the whole failure mode.
 *
 * Returns 'default' when nothing is set anywhere, including when `inspect()`
 * itself returns undefined for an unregistered setting.
 */
export function scopeOf<T>(inspected: InspectedSetting<T> | undefined): SettingScope {
    if (inspected?.workspaceFolderValue !== undefined) {
        return 'folder';
    }
    if (inspected?.workspaceValue !== undefined) {
        return 'workspace';
    }
    if (inspected?.globalValue !== undefined) {
        return 'user';
    }
    return 'default';
}
