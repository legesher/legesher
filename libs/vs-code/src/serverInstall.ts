/**
 * What to tell someone whose language server cannot be found (CORE-2203).
 *
 * The extension does not bundle the server. `legesher.serverCommand` defaults
 * to `legesher-lsp`, the console script of the `legesher-language-server`
 * Python package, and hover, completion, diagnostics and keyword highlighting
 * all come from it. When it is missing, what helps is the package name and the
 * setting, so that is what the message gives. For how to get the package it
 * points at the extension README rather than giving an install command: until
 * the package is on PyPI there is no command that works, and the README is the
 * page that changes when it is published, with no extension release needed.
 *
 * Kept free of the `vscode` module so the unit tests can load it.
 */

/** The Python distribution that provides the default server command. */
export const SERVER_PACKAGE = 'legesher-language-server';

/** The console script that package installs: the `legesher.serverCommand` default. */
export const DEFAULT_SERVER_COMMAND = 'legesher-lsp';

/** The features that stop working without the server, in the words the docs use. */
const SERVER_FEATURES = 'Hover, completion, diagnostics and keyword highlighting';

/**
 * The message for a server command that could not be run.
 *
 * @param command The configured `legesher.serverCommand`.
 */
export function serverNotFoundMessage(command: string): string {
    const where = `see "The language server" in the extension README`;
    const fix = command === DEFAULT_SERVER_COMMAND
        ? `It is ${DEFAULT_SERVER_COMMAND}, from the ${SERVER_PACKAGE} Python package: ${where}. ` +
          `Or set legesher.serverCommand to the server's full path.`
        : `Check that legesher.serverCommand ("${command}") points to the server. ` +
          `The default, ${DEFAULT_SERVER_COMMAND}, comes from the ${SERVER_PACKAGE} Python package: ${where}.`;
    return `Language server not found. ${SERVER_FEATURES} need it. ${fix}`;
}
