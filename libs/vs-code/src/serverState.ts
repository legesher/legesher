/**
 * The language server's state, and the only thing allowed to change it
 * (CORE-1847).
 *
 * This subsystem produced the same class of bug three times — CORE-1728,
 * CORE-1754, CORE-1776 — and every instance was the same shape: two pieces of
 * module-level state that were supposed to describe one situation, disagreeing.
 * The identity said a language was running while nothing was; the status bar
 * showed a language the server had failed to load; a cached pair outlived the
 * process it described.
 *
 * They are one object here, with one method that changes them, so a
 * disagreement is unrepresentable rather than merely tested for. In particular
 * two questions that were previously answered by the same variable are now
 * separate and cannot drift:
 *
 *   - *which language do we remember asking for* — kept even when no server
 *     runs, so a missing binary is not re-probed on every editor switch
 *   - *which language is actually being served* — `activeIdentity`, which is
 *     undefined unless something is really running
 *
 * Deliberately free of `vscode` and `vscode-languageclient`: starting a server
 * is injected as a hook, so the state machine is unit-testable without an
 * editor host. The CORE-1776 regressions are unit tests here rather than
 * two-minute integration runs.
 */

import type { SettingScope } from './settingsScope';

/** Whether anything is actually serving the language we last asked for. */
export type ServerStatus = 'none' | 'running' | 'unavailable' | 'failed';

/** Whether a start produced a running server. Absence is not an error. */
export type StartResult = 'started' | 'unavailable';

/** What asked for a language change, so intent can be told from side effects. */
export type LanguageTrigger = 'activation' | 'picker' | 'settings' | 'editor' | 'restart';

/**
 * Where the resolved language came from.
 *
 * Derived from `SettingScope` rather than restated, so the vocabulary the
 * resolver uses and the one the analytics record cannot drift apart.
 */
export type ResolutionSource = SettingScope | 'detected';

/**
 * How a requested language change ended.
 *
 * `unchanged` is the one that matters most: it is the shape every silent
 * failure in this subsystem took — a change was requested, nothing happened,
 * and every surface reported success.
 */
export type TransitionOutcome = 'applied' | 'unchanged' | 'failed' | 'serverUnavailable';

/** A completed language change, whatever became of it. */
export interface TransitionRecord {
    from: string;
    to: string;
    trigger: LanguageTrigger;
    source: ResolutionSource;
    outcome: TransitionOutcome;
}

/** What the caller wants recorded about why this transition happened. */
export interface TransitionRequest {
    trigger: LanguageTrigger;
    source: ResolutionSource;
}

/**
 * The effects a transition needs from the outside world.
 *
 * Injected rather than imported so this module stays free of the editor host.
 */
export interface TransitionHooks {
    /**
     * Stop whatever is running and start the requested language.
     *
     * Returns `unavailable` when there is no server binary to start — a
     * supported state, not an error — and throws when a start was attempted and
     * failed.
     */
    start(): Promise<StartResult>;
    /** Record a transition that actually meant something. */
    onRecord(record: TransitionRecord, durationMs?: number): void;
    /** Tell the user a language change did not take. */
    onFailure(identity: string, error: unknown): void;
    /** Injected so duration is measurable without a real clock. */
    now(): number;
}

export class LanguageServerState {
    /**
     * Serialises changes so overlapping triggers cannot race (CORE-1728).
     *
     * Owned by the same object that owns the state it protects — the two were
     * previously separate module variables, which is how an explicit restart
     * could be overtaken by an in-flight transition that assigned the identity
     * after the restart had cleared it.
     */
    private queue: Promise<void> = Promise.resolve();

    /** The language we last asked for, remembered even if nothing serves it. */
    private requested: string | undefined;
    private state: ServerStatus = 'none';
    private record: TransitionRecord | undefined;
    /** Signature of the last announced failure, to suppress duplicates. */
    private announced: string | undefined;

    /** Whether anything is serving the language we asked for. */
    get status(): ServerStatus {
        return this.state;
    }

    /**
     * The identity actually being served, or undefined.
     *
     * Gated on a running server, not on the remembered request. A missing
     * binary still records a request — so the availability check is not repeated
     * on every editor switch — and reporting that as running is what let the
     * status bar repaint itself healthy over its own warning.
     */
    get activeIdentity(): string | undefined {
        return this.state === 'running' ? this.requested : undefined;
    }

    /** How the last meaningful language change ended. */
    get lastTransition(): TransitionRecord | undefined {
        return this.record;
    }

    /**
     * Bring the server to `identity`, queued behind any change already running.
     *
     * Idempotent: a request for the language already remembered is a no-op, so
     * whichever of several triggers arrives first does the work and the rest
     * collapse. Never rejects — a failure is an outcome, and a rejected promise
     * left in the queue would wedge every later change behind it.
     */
    transition(
        identity: string,
        request: TransitionRequest,
        hooks: TransitionHooks
    ): Promise<TransitionOutcome> {
        const applied = this.queue.then<TransitionOutcome>(async () => {
            const from = this.requested ?? 'none';

            if (this.requested === identity) {
                return this.finish(from, identity, request, 'unchanged', hooks);
            }

            const startedAt = hooks.now();
            try {
                // Cleared before the step that can fail, not after it. Leaving
                // the old request in place through a failed start meant
                // switching back to it matched the cache and collapsed into a
                // no-op that never retried (CORE-1776).
                this.requested = undefined;

                const result = await hooks.start();

                this.requested = identity;
                this.state = result === 'started' ? 'running' : 'unavailable';
                // A change that worked clears the suppression, so the next
                // failure is announced even if it repeats an earlier one.
                this.announced = undefined;

                return this.finish(
                    from,
                    identity,
                    request,
                    result === 'started' ? 'applied' : 'serverUnavailable',
                    hooks,
                    hooks.now() - startedAt
                );
            } catch (error) {
                // No request is remembered after a failure, so the same language
                // can be asked for again rather than matching a cached success.
                this.requested = undefined;
                this.state = 'failed';
                this.announce(identity, error, hooks);
                return this.finish(from, identity, request, 'failed', hooks, hooks.now() - startedAt);
            }
        });

        // The queue must survive a failure. The outcome still reaches the caller
        // through `applied`, which is a separate promise.
        this.queue = applied.then(() => undefined, () => undefined);
        return applied;
    }

    /**
     * Forget what is running, so the next transition restarts even at the same
     * language.
     *
     * Queued rather than applied immediately: clearing synchronously races a
     * transition already in flight, which assigns its identity on success —
     * after the clear — leaving the explicit restart queued behind it to match
     * and collapse into the no-op the user asked not to have (CORE-1776).
     */
    invalidate(): void {
        this.queue = this.queue.then(() => {
            this.requested = undefined;
            // `state` is deliberately left alone. Invalidating says "ask again",
            // not "everything is fine now", and the status bar paints
            // optimistically before each transition — so clearing the status
            // here reads as healthy and covers an `(inactive)` warning for as
            // long as the retry takes. `activeIdentity` is already undefined
            // once the request is forgotten, which is the part that matters.
            //
            // An explicit retry always deserves an answer, even about a failure
            // the user has already been shown.
            this.announced = undefined;
        });
    }

    /** Nothing is running any more — for shutdown. */
    markStopped(): void {
        this.requested = undefined;
        this.state = 'none';
    }

    /**
     * Record the outcome, unless it is a no-op restating the last one.
     *
     * Two things produce those, both by design and neither user-meaningful: a
     * pick fires its own sync *and* the configuration listener, so one action
     * yields an applied followed by an unchanged; and every editor switch
     * re-resolves to the language already running. Keeping them would overwrite
     * real outcomes with phantoms and make most of the telemetry noise.
     */
    private finish(
        from: string,
        to: string,
        request: TransitionRequest,
        outcome: TransitionOutcome,
        hooks: TransitionHooks,
        durationMs?: number
    ): TransitionOutcome {
        if (outcome === 'unchanged' && this.record?.to === to) {
            return outcome;
        }

        this.record = { from, to, trigger: request.trigger, source: request.source, outcome };
        hooks.onRecord(this.record, durationMs);
        return outcome;
    }

    /** Announce a failure once per distinct problem. */
    private announce(identity: string, error: unknown, hooks: TransitionHooks): void {
        const message = error instanceof Error ? error.message : String(error);
        const signature = `${identity}:${message}`;
        if (this.announced === signature) {
            return;
        }
        this.announced = signature;
        hooks.onFailure(identity, error);
    }
}
