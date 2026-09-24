/**
 * Unit tests for the Unicode-highlighting allowance (CORE-1978).
 *
 * The behaviour under test is the narrowing: allow the characters this
 * project's language pack actually writes with, and nothing else. A test that
 * passed by allowing too much would defeat the point of the ticket, so the
 * assertions are as much about what stays flagged as about what stops.
 *
 * Characters are built from code points rather than written literally. Arabic
 * and Hebrew letters in a source file reorder the surrounding ASCII on screen,
 * which makes a failing assertion very hard to read — and code points are what
 * the implementation actually keys on.
 */

import * as assert from 'assert';
import {
    alreadyAllows,
    charactersPresentIn,
    deriveAllowedCharacters,
    describeLanguageOrigin,
    formatCodePoints,
    isAmbiguous,
    shouldOfferAllowedCharacters,
    workspaceAllowance,
    type OfferConditions,
} from '../../src/unicodeHighlight';

// The ticket's own example: Alef is reported as confusable with Latin `l`.
const ARABIC_ALEF = 0x0627;
const ARABIC_HEH = 0x0647;
// Ordinary Arabic letters VS Code does not flag.
const ARABIC_BEH = 0x0628;
const ARABIC_MEEM = 0x0645;
// Ethiopic: exactly two syllables in the whole block are flagged.
const ETHIOPIC_HA = 0x1200;
const ETHIOPIC_HU = 0x1201;
// Latin-script languages are not exempt: Turkish dotless i is confusable with `i`.
const TURKISH_DOTLESS_I = 0x0131;
// Another script's confusable, used to prove it stays flagged.
const CYRILLIC_SMALL_A = 0x0430;
// Astral plane, to pin surrogate-pair handling.
const ARABIC_MATHEMATICAL_ALEF = 0x1ee00;

const ch = (codePoint: number): string => String.fromCodePoint(codePoint);

describe('Unicode highlighting allowance (CORE-1978)', () => {
    describe('the vendored confusable table', () => {
        it('flags the character the ticket reports', () => {
            // If this fails, the range literal stopped parsing and every
            // derivation below silently returns nothing.
            assert.ok(isAmbiguous(ARABIC_ALEF), 'U+0627 must be flagged');
            assert.ok(isAmbiguous(ETHIOPIC_HA), 'U+1200 must be flagged');
            assert.ok(isAmbiguous(TURKISH_DOTLESS_I), 'U+0131 must be flagged');
        });

        it('leaves ordinary letters of those scripts alone', () => {
            assert.ok(!isAmbiguous(ARABIC_BEH));
            assert.ok(!isAmbiguous(ARABIC_MEEM));
            assert.ok(!isAmbiguous(ETHIOPIC_HU));
        });

        it('parses both singletons and ranges', () => {
            // 'A0' is the first singleton in the literal; '2000-200A' a range.
            assert.ok(isAmbiguous(0xa0));
            assert.ok(isAmbiguous(0x2000));
            assert.ok(isAmbiguous(0x2005));
            assert.ok(isAmbiguous(0x200a));
            assert.ok(!isAmbiguous(0x200b), 'U+200B is invisible, not ambiguous');
        });
    });

    describe('deriveAllowedCharacters', () => {
        it('keeps only the pack characters VS Code would flag', () => {
            const pack = {
                if: ch(ARABIC_ALEF) + ch(ARABIC_BEH),
                print: ch(ARABIC_MEEM) + ch(ARABIC_HEH),
            };

            assert.deepStrictEqual(
                deriveAllowedCharacters(pack),
                [ch(ARABIC_ALEF), ch(ARABIC_HEH)]
            );
        });

        it('returns nothing for a pack with no flagged characters', () => {
            // A Spanish pack: non-ASCII, but none of it confusable.
            assert.deepStrictEqual(
                deriveAllowedCharacters({ if: 'si', print: 'imprimir', pass: 'pasar' }),
                []
            );
        });

        it('covers Latin-script languages too', () => {
            assert.deepStrictEqual(
                deriveAllowedCharacters({ for: 'i' + ch(TURKISH_DOTLESS_I) + 'in' }),
                [ch(TURKISH_DOTLESS_I)]
            );
        });

        it('ignores ASCII entirely', () => {
            assert.deepStrictEqual(deriveAllowedCharacters({ if: 'if', def: 'def' }), []);
        });

        it('sorts by code point, so a rewritten settings file does not churn', () => {
            const pack = {
                a: ch(ETHIOPIC_HA),
                b: ch(ARABIC_ALEF),
                c: ch(CYRILLIC_SMALL_A),
            };

            assert.deepStrictEqual(
                deriveAllowedCharacters(pack),
                [ch(CYRILLIC_SMALL_A), ch(ARABIC_ALEF), ch(ETHIOPIC_HA)]
            );
        });

        it('treats an astral character as one entry, not two surrogates', () => {
            const derived = deriveAllowedCharacters({ x: ch(ARABIC_MATHEMATICAL_ALEF) });

            assert.strictEqual(derived.length, 1);
            assert.strictEqual(derived[0].codePointAt(0), ARABIC_MATHEMATICAL_ALEF);
        });

        it('survives a pack whose values are not all strings', () => {
            // Packs are data on disk and the loader's shape check can be
            // bypassed by a hand-edited file; this must not throw.
            const pack = { if: ch(ARABIC_ALEF), bad: undefined as unknown as string };

            assert.deepStrictEqual(deriveAllowedCharacters(pack), [ch(ARABIC_ALEF)]);
        });
    });

    describe('charactersPresentIn', () => {
        const derived = [ch(ARABIC_ALEF), ch(ARABIC_HEH)];

        it('reports only what the document actually contains', () => {
            const text = `def f():\n    x = ${ch(ARABIC_ALEF)}${ch(ARABIC_BEH)}\n`;

            assert.deepStrictEqual(charactersPresentIn(text, derived), [ch(ARABIC_ALEF)]);
        });

        it('is empty for an ordinary English file', () => {
            assert.deepStrictEqual(charactersPresentIn('def f():\n    pass\n', derived), []);
        });

        it('preserves the derived order rather than order of appearance', () => {
            const text = ch(ARABIC_HEH) + ch(ARABIC_ALEF);

            assert.deepStrictEqual(charactersPresentIn(text, derived), derived);
        });

        it('stops once every derived character has been found', () => {
            // The early exit must not change the answer. Both characters appear
            // in the first few bytes and then a megabyte of text follows; the
            // result is the same as without the megabyte.
            const head = ch(ARABIC_ALEF) + ch(ARABIC_HEH);
            const tail = 'x'.repeat(1_000_000) + ch(ARABIC_BEH);

            assert.deepStrictEqual(charactersPresentIn(head + tail, derived), derived);
        });

        it('still reports a character that only appears late', () => {
            // The exit is on completeness, not on a byte budget: a file whose
            // only flagged character is on the last line must still be caught.
            const text = 'x'.repeat(50_000) + ch(ARABIC_HEH);

            assert.deepStrictEqual(charactersPresentIn(text, derived), [ch(ARABIC_HEH)]);
        });

        it('returns nothing for an empty derived set', () => {
            assert.deepStrictEqual(charactersPresentIn(ch(ARABIC_ALEF), []), []);
        });
    });

    describe('alreadyAllows', () => {
        it('is true only when every derived character is allowed', () => {
            const derived = [ch(ARABIC_ALEF), ch(ARABIC_HEH)];

            assert.ok(alreadyAllows({ [ch(ARABIC_ALEF)]: true, [ch(ARABIC_HEH)]: true }, derived));
            assert.ok(!alreadyAllows({ [ch(ARABIC_ALEF)]: true }, derived));
            assert.ok(!alreadyAllows(undefined, derived));
        });

        it('requires the value to be exactly true', () => {
            // A hand-edited settings file can hold anything, and VS Code's own
            // schema is `boolean`; a truthy string is not an allowance.
            assert.ok(!alreadyAllows({ [ch(ARABIC_ALEF)]: 'yes' }, [ch(ARABIC_ALEF)]));
            assert.ok(!alreadyAllows({ [ch(ARABIC_ALEF)]: false }, [ch(ARABIC_ALEF)]));
        });

        it('is vacuously true for an empty derived set', () => {
            assert.ok(alreadyAllows(undefined, []));
        });
    });

    describe('workspaceAllowance', () => {
        it('writes the derived set and nothing else', () => {
            assert.deepStrictEqual(
                workspaceAllowance(undefined, [ch(ARABIC_ALEF)]),
                { [ch(ARABIC_ALEF)]: true }
            );
        });

        it('adds nothing of its own to an empty workspace file', () => {
            // The blocker this function exists to fix. VS Code merges
            // object-valued settings across scopes — @types/vscode: "Only
            // `object` value types are merged and all other value types are
            // overridden" — so a user's own allowances survive a workspace
            // write untouched and never needed copying. Building the write from
            // the *effective* value instead pulled every character the
            // contributor had ever excluded, including via VS Code's own
            // user-scope hover action, into `.vscode/settings.json`, where it
            // gets committed and imposed on everyone who pulls.
            //
            // The defence in depth is the shape of this function: it can only
            // emit the derived set plus whatever the caller hands it, and the
            // caller hands it `inspect().workspaceValue` — the file it is about
            // to rewrite — not `get()`.
            const written = workspaceAllowance(undefined, [ch(ARABIC_ALEF), ch(ARABIC_HEH)]);

            assert.deepStrictEqual(Object.keys(written), [ch(ARABIC_ALEF), ch(ARABIC_HEH)]);
        });

        it('keeps a second language, so one workspace can hold both', () => {
            // The session guard is per language, so an Arabic file and a
            // Russian file in one workspace offer twice. A bare write would
            // drop the first language and then re-offer for it forever.
            const first = workspaceAllowance(undefined, [ch(ARABIC_ALEF)]);
            const second = workspaceAllowance(first, [ch(CYRILLIC_SMALL_A)]);

            assert.deepStrictEqual(second, {
                [ch(ARABIC_ALEF)]: true,
                [ch(CYRILLIC_SMALL_A)]: true,
            });
        });

        it('is idempotent for the same language', () => {
            const once = workspaceAllowance(undefined, [ch(ARABIC_ALEF), ch(ARABIC_HEH)]);

            assert.deepStrictEqual(
                workspaceAllowance(once, [ch(ARABIC_ALEF), ch(ARABIC_HEH)]),
                once
            );
        });

        it('preserves a workspace-scope false rather than dropping it', () => {
            // At workspace scope `false` is not a no-op: because scopes merge,
            // it revokes a user-scope allowance inside this project. Dropping
            // it would silently re-grant the allowance the project refused.
            assert.deepStrictEqual(
                workspaceAllowance({ [ch(CYRILLIC_SMALL_A)]: false }, [ch(ARABIC_ALEF)]),
                { [ch(CYRILLIC_SMALL_A)]: false, [ch(ARABIC_ALEF)]: true }
            );
        });

        it('turns a workspace-scope false into true when that is what was asked for', () => {
            assert.deepStrictEqual(
                workspaceAllowance({ [ch(ARABIC_ALEF)]: false }, [ch(ARABIC_ALEF)]),
                { [ch(ARABIC_ALEF)]: true }
            );
        });

        it('does not mutate the value it was given', () => {
            const existing = { [ch(CYRILLIC_SMALL_A)]: true };
            workspaceAllowance(existing, [ch(ARABIC_ALEF)]);

            assert.deepStrictEqual(existing, { [ch(CYRILLIC_SMALL_A)]: true });
        });
    });

    describe('describeLanguageOrigin', () => {
        it('distinguishes the project\'s claim from the reader\'s setting', () => {
            // The whole point of naming the source: in an unfamiliar repository
            // the pack is the reader's, not the project's, and the message must
            // not borrow the project's authority for it.
            assert.strictEqual(describeLanguageOrigin('workspace'), "this project's own setting");
            assert.strictEqual(describeLanguageOrigin('folder'), "this project's own setting");
            assert.strictEqual(describeLanguageOrigin('user'), 'your working-language setting');
            assert.strictEqual(
                describeLanguageOrigin('detected'),
                'detected from the file contents'
            );
            assert.strictEqual(
                describeLanguageOrigin('default'),
                'the default working language'
            );
        });
    });

    describe('shouldOfferAllowedCharacters', () => {
        const offerable = (): OfferConditions => ({
            derived: [ch(ARABIC_ALEF), ch(ARABIC_HEH)],
            present: [ch(ARABIC_ALEF)],
            ambiguousCharactersEnabled: true,
            allowedCharacters: undefined,
            dismissed: false,
            offeredThisSession: false,
            hasWorkspace: true,
            isTrusted: true,
        });

        it('offers when a translated file is on screen and nothing is configured', () => {
            assert.ok(shouldOfferAllowedCharacters(offerable()));
        });

        it('stays quiet when the pack has nothing VS Code would flag', () => {
            assert.ok(!shouldOfferAllowedCharacters({ ...offerable(), derived: [], present: [] }));
        });

        it('stays quiet when the file on screen shows no warnings', () => {
            // The user's working language can be Arabic while the open file is
            // ordinary English; there is nothing to fix there.
            assert.ok(!shouldOfferAllowedCharacters({ ...offerable(), present: [] }));
        });

        it('stays quiet when the user has already turned the check off', () => {
            assert.ok(!shouldOfferAllowedCharacters({
                ...offerable(),
                ambiguousCharactersEnabled: false,
            }));
        });

        it('stays quiet when every derived character is already allowed', () => {
            assert.ok(!shouldOfferAllowedCharacters({
                ...offerable(),
                allowedCharacters: { [ch(ARABIC_ALEF)]: true, [ch(ARABIC_HEH)]: true },
            }));
        });

        it('still offers when only some derived characters are allowed', () => {
            assert.ok(shouldOfferAllowedCharacters({
                ...offerable(),
                allowedCharacters: { [ch(ARABIC_ALEF)]: true },
            }));
        });

        it('honours "Don\'t Ask Again"', () => {
            assert.ok(!shouldOfferAllowedCharacters({ ...offerable(), dismissed: true }));
        });

        it('asks once per language per session', () => {
            assert.ok(!shouldOfferAllowedCharacters({ ...offerable(), offeredThisSession: true }));
        });

        it('stays quiet with no workspace to write to', () => {
            // The only remaining target would be the user's own settings, which
            // would weaken the check on every other repository they open — the
            // outcome this ticket rules out.
            assert.ok(!shouldOfferAllowedCharacters({ ...offerable(), hasWorkspace: false }));
        });

        it('stays quiet in an untrusted workspace', () => {
            // The manifest declares untrustedWorkspaces.supported "limited", so
            // the extension runs in Restricted Mode. VS Code registers
            // editor.unicodeHighlight.allowedCharacters with `restricted: true`
            // and discards a workspace value for it until trust is granted, so
            // the offer would prompt, appear to write, silently fail the
            // read-back and send the user to look at folder settings. Beyond
            // that: we do not relax a security default in a repository the user
            // has explicitly declined to trust.
            assert.ok(!shouldOfferAllowedCharacters({ ...offerable(), isTrusted: false }));
        });

        it('requires trust even when everything else is satisfied', () => {
            // Pinned separately from the clause above so that reordering the
            // conjunction cannot make trust vacuously true.
            const trusted = { ...offerable(), isTrusted: true };
            assert.ok(shouldOfferAllowedCharacters(trusted));
            assert.ok(!shouldOfferAllowedCharacters({ ...trusted, isTrusted: false }));
        });
    });

    describe('formatCodePoints', () => {
        it('renders U+XXXX, padded, uppercase', () => {
            assert.strictEqual(
                formatCodePoints([ch(ARABIC_ALEF), ch(TURKISH_DOTLESS_I)]),
                'U+0627, U+0131'
            );
        });

        it('renders an astral code point without truncating it', () => {
            assert.strictEqual(formatCodePoints([ch(ARABIC_MATHEMATICAL_ALEF)]), 'U+1EE00');
        });
    });
});
