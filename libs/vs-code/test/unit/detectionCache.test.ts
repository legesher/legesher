/**
 * Unit tests for the detection memo (CORE-1776).
 *
 * Detection re-tokenized the whole document on every editor switch. The result
 * is a pure function of the document's text, and VS Code already hands us a
 * version number that changes exactly when the text does, so (uri, version) is
 * a sound cache key. These tests pin that soundness — a stale hit would pin the
 * wrong language onto an edited file, which is worse than the work saved.
 */

import * as assert from 'assert';
import { DetectionCache } from '../../src/detectionCache';
import type { DetectionResult } from '../../src/languageDetection';

const DE: DetectionResult = { language: 'de', score: 7 };
const ES: DetectionResult = { language: 'es', score: 6 };

describe('Detection cache (CORE-1776)', () => {
    it('computes on first sight of a document', () => {
        const cache = new DetectionCache();
        let calls = 0;

        const result = cache.get('file:///a.py', 1, () => { calls++; return DE; });

        assert.strictEqual(calls, 1);
        assert.deepStrictEqual(result, DE);
    });

    it('reuses the result while the version is unchanged', () => {
        // The editor-switch case: focus leaves the file and comes back, the text
        // never changed, and nothing should be re-tokenized.
        const cache = new DetectionCache();
        let calls = 0;
        const compute = () => { calls++; return DE; };

        cache.get('file:///a.py', 1, compute);
        const second = cache.get('file:///a.py', 1, compute);

        assert.strictEqual(calls, 1, 'should not recompute for the same version');
        assert.deepStrictEqual(second, DE);
    });

    it('recomputes when the document version advances', () => {
        // An edit is exactly when the cached answer stops being true.
        const cache = new DetectionCache();
        const results = [DE, ES];
        let calls = 0;
        const compute = () => results[calls++];

        assert.deepStrictEqual(cache.get('file:///a.py', 1, compute), DE);
        assert.deepStrictEqual(cache.get('file:///a.py', 2, compute), ES);
        assert.strictEqual(calls, 2);
    });

    it('caches a null result rather than retrying it', () => {
        // Declining to guess is a real answer and the expensive part already ran.
        // Storing only truthy results would leave English files — the common
        // case — recomputing on every switch.
        const cache = new DetectionCache();
        let calls = 0;
        const compute = () => { calls++; return null; };

        assert.strictEqual(cache.get('file:///a.py', 1, compute), null);
        assert.strictEqual(cache.get('file:///a.py', 1, compute), null);
        assert.strictEqual(calls, 1);
    });

    it('keeps separate entries per document', () => {
        // Alternating between two open editors is the motivating case; a
        // single-slot memo would miss on every switch and save nothing.
        const cache = new DetectionCache();
        let calls = 0;
        const de = () => { calls++; return DE; };
        const es = () => { calls++; return ES; };

        cache.get('file:///a.py', 1, de);
        cache.get('file:///b.py', 1, es);
        assert.deepStrictEqual(cache.get('file:///a.py', 1, de), DE);
        assert.deepStrictEqual(cache.get('file:///b.py', 1, es), ES);

        assert.strictEqual(calls, 2, 'both documents should stay cached');
    });

    it('forgets a document on request', () => {
        // Closing a document must evict it: VS Code restarts a reopened
        // document at version 1, so a surviving entry would be matched by a
        // revision it was never computed from — a file edited on disk while
        // closed would resolve to the language its old contents implied.
        const cache = new DetectionCache();
        const results = [DE, ES];
        let calls = 0;
        const compute = () => results[calls++];

        assert.deepStrictEqual(cache.get('file:///a.py', 1, compute), DE);
        cache.forget('file:///a.py');
        assert.deepStrictEqual(
            cache.get('file:///a.py', 1, compute),
            ES,
            'the same version must recompute after the document is forgotten'
        );
    });

    it('forgets a document that was never cached without complaint', () => {
        const cache = new DetectionCache();

        assert.doesNotThrow(() => cache.forget('file:///never-seen.py'));
    });

    it('evicts the least recently used entry past its capacity', () => {
        // Bounded so a long session browsing many files cannot grow it without
        // limit; entries hold whole detection results, not just codes.
        const cache = new DetectionCache(2);
        let calls = 0;
        const compute = () => { calls++; return DE; };

        cache.get('file:///a.py', 1, compute);   // 1
        cache.get('file:///b.py', 1, compute);   // 2
        cache.get('file:///c.py', 1, compute);   // 3, evicts a
        cache.get('file:///a.py', 1, compute);   // 4, recomputed

        assert.strictEqual(calls, 4);
    });

    it('keeps a re-read entry alive against eviction', () => {
        const cache = new DetectionCache(2);
        let calls = 0;
        const compute = () => { calls++; return DE; };

        cache.get('file:///a.py', 1, compute);   // 1
        cache.get('file:///b.py', 1, compute);   // 2
        cache.get('file:///a.py', 1, compute);   // hit, refreshes a
        cache.get('file:///c.py', 1, compute);   // 3, evicts b not a
        cache.get('file:///a.py', 1, compute);   // hit

        assert.strictEqual(calls, 3);
    });
});
