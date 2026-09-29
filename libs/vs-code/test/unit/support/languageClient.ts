/**
 * Loading modules that need vscode-languageclient, outside an editor
 * (CORE-2316).
 *
 * The library requires `vscode` as it loads, and that module exists only
 * inside the editor's extension host. `withoutEditor` answers that one require
 * with an inert stand-in while `load` runs, then takes the stand-in away and
 * drops every module loaded meanwhile from Node's cache. Nothing else in the
 * run can reach the stand-in: another test that imports the library, or
 * `vscode` itself, still fails outside the editor, whatever order the files run
 * in. The stand-in only has to survive the library's load, which subclasses a
 * few `vscode` classes; nothing calls into it.
 */

import Module = require('module');

type Load = (request: string, parent: unknown, isMain: boolean) => unknown;

const loader = Module as unknown as { _load: Load };

const standIn: object = new Proxy(function () {}, {
    get: () => standIn,
    apply: () => standIn,
    construct: () => standIn,
});

export function withoutEditor<T>(load: () => T): T {
    const alreadyLoaded = new Set(Object.keys(require.cache));
    const original = loader._load;
    loader._load = function (request, parent, isMain) {
        return request === 'vscode' ? standIn : original.call(this, request, parent, isMain);
    };
    try {
        return load();
    } finally {
        loader._load = original;
        for (const file of Object.keys(require.cache)) {
            if (!alreadyLoaded.has(file)) {
                delete require.cache[file];
            }
        }
    }
}
