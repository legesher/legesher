/**
 * What the language client does when its connection to the server errors or
 * closes (CORE-2316).
 *
 * Only the extension starts servers, through its state machine
 * (`serverState.ts`), which knows which languages were asked for and tells the
 * user when a start fails. So a closed connection stays closed: a restart from
 * inside the client runs behind the state machine's back, with whatever
 * languages that client was created with. The extension decides when to start
 * it again: on `Legesher: Restart Language Server`, a change to the configured
 * languages, or, after a start that failed, the next sync.
 * Staying closed has one more consequence: a server that exits during the
 * handshake can leave the client's start() resolved rather than rejected, so
 * `startServer` checks that the client is running before it counts a start.
 *
 * The answers are vscode-languageclient's enum members, by name. The number
 * this replaced, `{ action: 2 }`, was commented as "do not restart" and is
 * `CloseAction.Restart`: every unexpected close restarted the server (the
 * library does not ask during the extension's own stops), and a binary that
 * died on the handshake was relaunched in a loop for the life of the window.
 *
 * Kept apart from `client.ts`, with no `vscode` import of its own, so a unit
 * test can check the answers against the library's enums.
 */

import { CloseAction, ErrorAction, type ErrorHandler } from 'vscode-languageclient/node';

/** Where the handler reports what happened: the log and telemetry, injected. */
export interface ConnectionEvents {
    error(...args: Parameters<ErrorHandler['error']>): void;
    closed(): void;
}

export function connectionErrorHandler(events: ConnectionEvents): ErrorHandler {
    return {
        error: (error, message, count) => {
            events.error(error, message, count);
            // One bad message is no reason to give up on a server that is
            // otherwise answering.
            return { action: ErrorAction.Continue };
        },
        closed: () => {
            events.closed();
            return { action: CloseAction.DoNotRestart };
        },
    };
}
