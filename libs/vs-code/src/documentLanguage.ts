/**
 * Telling the language server which language each document is written in
 * (CORE-1976).
 *
 * The server used to read one language at initialize and answer every request
 * with it. Switching to a file detected in another language meant restarting
 * the server, and a file the restart had not caught up with came back with no
 * highlighting and no hover, as if it were broken. Now the client names each
 * document's language in a `legesher/documentLanguage` notification, and the
 * server answers each request in the language of the document it is about.
 * Detection, its cache and the precedence rules stay on this side; the server
 * does no detection of its own.
 *
 * Deliberately free of `vscode`: what to send, and when a send is redundant,
 * is unit-testable without an editor host, the same bargain `serverState.ts`
 * makes. The editor side (which documents, and when) lives in `client.ts`.
 */

/** The notification's wire name, namespaced like the server's `legesher/status`. */
export const DOCUMENT_LANGUAGE_NOTIFICATION = 'legesher/documentLanguage';

/** One document, and the language it is written in. */
export interface DocumentLanguageParams {
    uri: string;
    language: string;
}

/**
 * What one server has been told, so a report it already has costs nothing.
 *
 * Create one per language client. A restarted server starts with an empty map,
 * so a record that outlived it would suppress exactly the reports the new
 * server needs.
 */
export class DocumentLanguageSync {
    private readonly sent = new Map<string, string>();

    constructor(private readonly send: (params: DocumentLanguageParams) => Promise<void>) {}

    /**
     * Name `uri`'s language to the server, unless it was last told exactly this.
     *
     * `force` sends regardless, for a document being opened: the server forgot
     * it when it closed, whatever this record says. A send that fails is not
     * recorded, so the next report tries again instead of trusting a message
     * that never left; the record keeps whatever the server last received.
     *
     * Resolves to whether a notification was sent; rejects if sending failed.
     */
    async report(
        uri: string,
        language: string,
        options: { force?: boolean } = {}
    ): Promise<boolean> {
        if (!options.force && this.sent.get(uri) === language) {
            return false;
        }
        await this.send({ uri, language });
        this.sent.set(uri, language);
        return true;
    }

    /** Drop a closed document, so reopening it names it afresh. */
    forget(uri: string): void {
        this.sent.delete(uri);
    }

    /** The language last sent for `uri`, if any. */
    sentFor(uri: string): string | undefined {
        return this.sent.get(uri);
    }
}
