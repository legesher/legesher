/**
 * Memo for content-based language detection (CORE-1776).
 *
 * Detection tokenizes the whole document and scores it against every installed
 * vocabulary. That ran again on every editor switch, for text that had not
 * changed — alternating between two files re-tokenized both, repeatedly, on a
 * path that runs during interactive editing.
 *
 * The result is a pure function of the document's text, and VS Code hands us a
 * version number that advances exactly when the text does, so `(uri, version)`
 * is a sound key: a hit can only be returned for the same bytes that produced
 * it. Getting that wrong would be worse than the work saved — a stale hit pins
 * the wrong language onto an edited file — so the version is compared, never
 * assumed.
 *
 * Deliberately has no `vscode` import, matching languageDetection.ts: the cache
 * is pure over (key, version) and is unit-testable without an editor host.
 */

import type { DetectionResult } from './languageDetection';

/**
 * How many documents to remember.
 *
 * One entry per document, so this bounds a long session spent browsing many
 * files rather than a single hot document. Entries hold a whole detection
 * result, not just a code, and the working set of open editors is far smaller
 * than this.
 */
const DEFAULT_MAX_ENTRIES = 50;

interface CacheEntry {
    version: number;
    result: DetectionResult | null;
}

export class DetectionCache {
    // Map preserves insertion order, which is what makes least-recently-used
    // eviction a delete-and-reinsert rather than a bookkeeping structure.
    private readonly entries = new Map<string, CacheEntry>();

    constructor(private readonly maxEntries: number = DEFAULT_MAX_ENTRIES) {}

    /**
     * Return the detection result for this document version, computing it only
     * on a miss.
     *
     * `null` — detection declining to guess — is cached like any other result.
     * It is the common case for ordinary English source, and the expensive part
     * has already run by the time we know it.
     */
    get(uri: string, version: number, compute: () => DetectionResult | null): DetectionResult | null {
        const cached = this.entries.get(uri);
        if (cached && cached.version === version) {
            // Reinsert so recency, not first sight, decides what gets evicted.
            this.entries.delete(uri);
            this.entries.set(uri, cached);
            return cached.result;
        }

        const result = compute();
        this.entries.delete(uri);
        this.entries.set(uri, { version, result });

        while (this.entries.size > this.maxEntries) {
            const oldest = this.entries.keys().next().value;
            if (oldest === undefined) {
                break;
            }
            this.entries.delete(oldest);
        }

        return result;
    }

    /**
     * Forget one document.
     *
     * Required when a document closes: VS Code restarts a reopened document's
     * version at 1, so an entry left behind can be matched by a *different*
     * revision of the same file — one edited on disk while it was closed — and
     * pin a language the text no longer supports.
     */
    forget(uri: string): void {
        this.entries.delete(uri);
    }

    /** Drop everything, for when the vocabularies themselves change. */
    clear(): void {
        this.entries.clear();
    }
}
