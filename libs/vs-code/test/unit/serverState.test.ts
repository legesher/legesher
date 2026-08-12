/**
 * Unit tests for the language-server state machine (CORE-1847).
 *
 * These are the CORE-1776 defects rewritten as invariants. Each one was
 * previously two module-level globals disagreeing, catchable only by driving a
 * real VS Code instance for two minutes; here they are properties of a single
 * object that can be asserted in milliseconds.
 *
 * The point of the consolidation is that a disagreement should be
 * unrepresentable rather than merely tested for — so what these tests pin is
 * that the object never exposes a state its own history does not support.
 */

import * as assert from 'assert';
import { LanguageServerState, type TransitionHooks } from '../../src/serverState';

/** A hooks stub that records what the state machine asked it to do. */
function hooks(overrides: Partial<TransitionHooks> = {}) {
    const calls = {
        starts: 0,
        records: [] as any[],
        failures: [] as any[],
    };
    // `start` always counts, whether or not the test supplies its own — a
    // counter that an override silently replaces reports zero attempts for the
    // tests that most need to count them.
    const start = overrides.start ?? (async () => 'started' as const);
    const base: TransitionHooks = {
        onRecord: (record, durationMs) => { calls.records.push({ ...record, durationMs }); },
        onFailure: (identity, error) => { calls.failures.push({ identity, error }); },
        now: () => 0,
        ...overrides,
        start: async () => { calls.starts++; return start(); },
    };
    return { hooks: base, calls };
}

const REQ = { trigger: 'picker' as const, source: 'user' as const };

describe('Language server state (CORE-1847)', () => {
    describe('identity is never reported without something serving it', () => {
        it('reports the identity after a successful start', async () => {
            const state = new LanguageServerState();
            const { hooks: h } = hooks();

            await state.transition('en->de', REQ, h);

            assert.strictEqual(state.activeIdentity, 'en->de');
            assert.strictEqual(state.status, 'running');
        });

        it('reports no identity after a failed start', async () => {
            // CORE-1776 defect 1: the old pair survived a failed restart, so
            // switching back to it matched the cache and no-opped forever.
            const state = new LanguageServerState();
            const { hooks: h } = hooks({
                start: async () => { throw new Error('spawn failed'); },
            });

            const outcome = await state.transition('en->de', REQ, h);

            assert.strictEqual(outcome, 'failed');
            assert.strictEqual(state.activeIdentity, undefined);
            assert.strictEqual(state.status, 'failed');
        });

        it('reports no identity when the server binary is absent', async () => {
            // The identity is still remembered internally so the availability
            // check is not repeated on every editor switch — but "remembered"
            // must not read as "running", which is what repainted the status
            // bar as healthy over its own warning.
            const state = new LanguageServerState();
            const { hooks: h } = hooks({ start: async () => 'unavailable' });

            const outcome = await state.transition('en->de', REQ, h);

            assert.strictEqual(outcome, 'serverUnavailable');
            assert.strictEqual(state.activeIdentity, undefined);
            assert.strictEqual(state.status, 'unavailable');
        });

        it('does not restart for a language it already remembers, even if unavailable', async () => {
            // The no-retry behaviour the remembered identity exists to provide.
            const state = new LanguageServerState();
            const { hooks: h, calls } = hooks({ start: async () => 'unavailable' });

            await state.transition('en->de', REQ, h);
            const second = await state.transition('en->de', REQ, h);

            assert.strictEqual(second, 'unchanged');
            assert.strictEqual(calls.starts, 1, 'should not re-probe an absent server');
            assert.strictEqual(state.status, 'unavailable', 'the warning must survive the no-op');
        });
    });

    describe('failures cannot wedge the queue', () => {
        it('keeps serving later transitions after one fails', async () => {
            // CORE-1776: a rejected promise left in the chain froze every
            // subsequent language change for the rest of the session.
            const state = new LanguageServerState();
            let attempt = 0;
            const { hooks: h } = hooks({
                start: async () => {
                    attempt++;
                    if (attempt === 1) { throw new Error('boom'); }
                    return 'started';
                },
            });

            const first = await state.transition('en->de', REQ, h);
            const second = await state.transition('en->fr', REQ, h);

            assert.strictEqual(first, 'failed');
            assert.strictEqual(second, 'applied');
            assert.strictEqual(state.activeIdentity, 'en->fr');
        });

        it('serialises overlapping transitions rather than racing them', async () => {
            const state = new LanguageServerState();
            const order: string[] = [];
            let release: (() => void) | undefined;
            const { hooks: h } = hooks({
                start: async () => {
                    order.push('start');
                    if (!release) {
                        await new Promise<void>(resolve => { release = resolve; });
                    }
                    order.push('done');
                    return 'started';
                },
            });

            const a = state.transition('en->de', REQ, h);
            const b = state.transition('en->fr', REQ, h);
            await new Promise(resolve => setTimeout(resolve, 0));
            release!();
            await Promise.all([a, b]);

            assert.deepStrictEqual(
                order,
                ['start', 'done', 'start', 'done'],
                'the second transition must not begin before the first finishes'
            );
        });

        it('retries a language whose start failed rather than caching the failure', async () => {
            const state = new LanguageServerState();
            let attempt = 0;
            const { hooks: h, calls } = hooks({
                start: async () => {
                    attempt++;
                    if (attempt === 1) { throw new Error('boom'); }
                    return 'started';
                },
            });

            await state.transition('en->de', REQ, h);
            const retry = await state.transition('en->de', REQ, h);

            assert.strictEqual(retry, 'applied');
            assert.strictEqual(calls.starts, 2, 'the same language must be retryable');
        });
    });

    describe('what gets recorded', () => {
        it('records an applied transition with its trigger and source', async () => {
            const state = new LanguageServerState();
            const { hooks: h, calls } = hooks();

            await state.transition('en->de', { trigger: 'settings', source: 'workspace' }, h);

            assert.strictEqual(calls.records.length, 1);
            assert.strictEqual(calls.records[0].outcome, 'applied');
            assert.strictEqual(calls.records[0].from, 'none');
            assert.strictEqual(calls.records[0].to, 'en->de');
            assert.strictEqual(calls.records[0].trigger, 'settings');
            assert.strictEqual(calls.records[0].source, 'workspace');
        });

        it('drops a no-op that merely restates the transition just recorded', async () => {
            // A pick fires its own sync and the configuration listener, so one
            // user action yields an applied followed by an unchanged. Recording
            // the second reports every success as a no-op — and every editor
            // switch would emit one too.
            const state = new LanguageServerState();
            const { hooks: h, calls } = hooks();

            await state.transition('en->de', REQ, h);
            await state.transition('en->de', { trigger: 'settings', source: 'user' }, h);

            assert.strictEqual(calls.records.length, 1, 'the phantom no-op must not be recorded');
            assert.strictEqual(state.lastTransition!.outcome, 'applied');
            assert.strictEqual(state.lastTransition!.trigger, 'picker');
        });

        it('keeps a failed outcome visible through the no-ops that follow it', async () => {
            const state = new LanguageServerState();
            const { hooks: h } = hooks({ start: async () => 'unavailable' });

            await state.transition('en->de', REQ, h);
            await state.transition('en->de', REQ, h);

            assert.strictEqual(state.lastTransition!.outcome, 'serverUnavailable');
        });

        it('times an applied transition', async () => {
            const state = new LanguageServerState();
            let clock = 0;
            const { hooks: h, calls } = hooks({ now: () => (clock += 25) });

            await state.transition('en->de', REQ, h);

            assert.strictEqual(typeof calls.records[0].durationMs, 'number');
        });
    });

    describe('failure announcement', () => {
        it('announces a failure once, not once per trigger', async () => {
            // The configuration listener and the editor listener can drive the
            // same doomed transition; two identical modals for one problem
            // trains people to dismiss them.
            const state = new LanguageServerState();
            const { hooks: h, calls } = hooks({
                start: async () => { throw new Error('same failure'); },
            });

            await state.transition('en->de', REQ, h);
            await state.transition('en->de', REQ, h);

            assert.strictEqual(calls.failures.length, 1);
        });

        it('announces again after a success in between', async () => {
            const state = new LanguageServerState();
            let ok = false;
            const { hooks: h, calls } = hooks({
                start: async () => {
                    if (ok) { return 'started'; }
                    throw new Error('same failure');
                },
            });

            // Deliberately the *same* identity and message on both failures, so
            // this fails unless the success actually reset the suppression.
            await state.transition('en->de', REQ, h);
            ok = true;
            await state.transition('en->fr', REQ, h);
            ok = false;
            await state.transition('en->de', REQ, h);

            assert.strictEqual(calls.failures.length, 2, 'a success resets the suppression');
        });

        it('announces again for an explicit retry of the same failure', async () => {
            // Asking again about a problem you already saw must not be met with
            // silence.
            const state = new LanguageServerState();
            const { hooks: h, calls } = hooks({
                start: async () => { throw new Error('same failure'); },
            });

            await state.transition('en->de', REQ, h);
            state.invalidate();
            await state.transition('en->de', REQ, h);

            assert.strictEqual(calls.failures.length, 2);
        });
    });

    describe('explicit invalidation', () => {
        it('forces the next transition to restart even at the same language', async () => {
            const state = new LanguageServerState();
            const { hooks: h, calls } = hooks();

            await state.transition('en->de', REQ, h);
            state.invalidate();
            const outcome = await state.transition('en->de', REQ, h);

            assert.strictEqual(outcome, 'applied');
            assert.strictEqual(calls.starts, 2);
        });

        it('leaves the known status alone until the retry resolves', async () => {
            // Invalidation says "ask again", not "everything is fine now". The
            // status bar paints optimistically before each transition, so a
            // status cleared here reads as healthy and covers the (inactive)
            // warning for as long as the retry takes — briefly re-creating the
            // signal erasure CORE-1776 fixed.
            const state = new LanguageServerState();
            const { hooks: h } = hooks({ start: async () => { throw new Error('still broken'); } });

            await state.transition('en->de', REQ, h);
            assert.strictEqual(state.status, 'failed');

            state.invalidate();

            assert.strictEqual(
                state.status,
                'failed',
                'the last known status must survive an invalidation'
            );
            assert.strictEqual(
                state.activeIdentity,
                undefined,
                'but nothing may be reported as actively served'
            );
        });

        it('is not overtaken by a transition already in flight', async () => {
            // Clearing synchronously raced an entry that was already running:
            // that entry assigned the identity afterwards, and the restart
            // queued behind it collapsed into the no-op the user asked not to
            // have.
            const state = new LanguageServerState();
            let release: (() => void) | undefined;
            const { hooks: h, calls } = hooks({
                start: async () => {
                    if (!release) {
                        await new Promise<void>(resolve => { release = resolve; });
                    }
                    return 'started';
                },
            });

            const inFlight = state.transition('en->de', REQ, h);
            await new Promise(resolve => setTimeout(resolve, 0));
            state.invalidate();
            const queued = state.transition('en->de', REQ, h);
            release!();
            await inFlight;

            assert.strictEqual(await queued, 'applied', 'the explicit restart must not be swallowed');
            assert.strictEqual(calls.starts, 2);
        });
    });

    describe('shutdown', () => {
        it('reports nothing running once stopped', async () => {
            const state = new LanguageServerState();
            const { hooks: h } = hooks();

            await state.transition('en->de', REQ, h);
            state.markStopped();

            assert.strictEqual(state.activeIdentity, undefined);
            assert.strictEqual(state.status, 'none');
        });
    });
});
