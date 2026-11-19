/**
 * What to tell someone whose language server cannot be found (CORE-2203).
 *
 * The extension does not bundle the server. `legesher.serverCommand` defaults
 * to `legesher-lsp`, the console script of the `legesher-language-server`
 * Python package, and hover, completion, diagnostics and keyword highlighting
 * all come from it. When it is missing, what helps is the package name, the
 * setting, and the extension's own Install command (`managedServer.ts`), so
 * that is what the message gives. For a terminal install it points at the
 * extension README rather than giving a command: the README is the page that
 * changes when the install steps do, with no extension release needed.
 *
 * Kept free of the `vscode` module so the unit tests can load it.
 */

/** The Python distribution that provides the default server command. */
export const SERVER_PACKAGE = 'legesher-language-server';

/** The console script that package installs: the `legesher.serverCommand` default. */
export const DEFAULT_SERVER_COMMAND = 'legesher-lsp';

/** The command palette title of `legesher.installLanguageServer`, as package.json declares it. */
export const INSTALL_COMMAND_TITLE = 'Legesher: Install Language Server';

/** The README section with the manual install steps. */
export const MANUAL_STEPS_URL =
    'https://github.com/legesher/legesher/blob/main/libs/vs-code/README.md#the-language-server';

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
        ? `Run "${INSTALL_COMMAND_TITLE}" to install it with no terminal. ` +
          `It is ${DEFAULT_SERVER_COMMAND}, from the ${SERVER_PACKAGE} Python package: ${where}. ` +
          `Or set legesher.serverCommand to the server's full path.`
        : `Check that legesher.serverCommand ("${command}") points to the server. ` +
          `The default, ${DEFAULT_SERVER_COMMAND}, comes from the ${SERVER_PACKAGE} Python package: ${where}.`;
    return `Language server not found. ${SERVER_FEATURES} need it. ${fix}`;
}
