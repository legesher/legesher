/**
 * Unit tests for the language-role vocabulary (CORE-1760).
 *
 * Four behaviours are load-bearing enough to pin here:
 * - alias honouring: `legesher.targetLanguage` keeps working until
 *   `legesher.workingLanguage` is explicitly set, and never afterwards;
 * - seeding: the known set resolves to the working language rather than to
 *   nothing, so first run never starts empty;
 * - suppression: a file in a known language raises no mismatch signal;
 * - protocol carry: the file and working languages reach the server as
 *   separate slots, with the deprecated slot mirroring the file language.
 */

import * as assert from 'assert';
import {
    buildResolvedLanguages,
    identityFileLanguage,
    isUnfamiliarFileLanguage,
    partitionByKnown,
    resolveKnownLanguages,
    resolveWorkingLanguage,
    serverIdentityOf,
} from '../../src/languageProfile';
import { type InspectedSetting } from '../../src/settingsScope';

/** `inspect()` for a setting held at one scope. */
const atUser = (value: string): InspectedSetting<string> => ({ globalValue: value });
const atWorkspace = (value: string): InspectedSetting<string> => ({ workspaceValue: value });
const atFolder = (value: string): InspectedSetting<string> => ({ workspaceFolderValue: value });

describe('Working-language alias honouring (CORE-1760)', () => {
    it('uses workingLanguage when only it is set', () => {
        assert.strictEqual(resolveWorkingLanguage(atUser('pt'), undefined).language, 'pt');
    });

    it('falls back to the deprecated targetLanguage when workingLanguage is unset', () => {
        // The back-compat promise: an existing configuration keeps working
        // with no user action.
        assert.strictEqual(resolveWorkingLanguage(undefined, atUser('fa')).language, 'fa');
    });

    it('prefers workingLanguage over the alias at the same scope', () => {
        // A migrated configuration must never be overridden by the setting it
        // migrated from — but only where they compete on equal footing, which
        // is within one scope.
        assert.strictEqual(resolveWorkingLanguage(atUser('pt'), atUser('fa')).language, 'pt');
    });

    it('defaults to English when neither is set', () => {
        const resolved = resolveWorkingLanguage(undefined, undefined);
        assert.strictEqual(resolved.language, 'en');
        assert.strictEqual(resolved.scope, 'default');
    });

    it('treats an empty string as unset, falling through to the alias beside it', () => {
        // '' can leak out of a cleared settings field; it is not a language.
        assert.strictEqual(
            resolveWorkingLanguage(atUser(''), atUser('fa')).language,
            'fa'
        );
        assert.strictEqual(resolveWorkingLanguage(atUser(''), atUser('')).language, 'en');
    });

    it('ignores a registered default, which inspect() never reports', () => {
        // getLanguageConfig feeds this from inspect(), not get(): folding in
        // workingLanguage's registered 'en' default would shadow a stored
        // targetLanguage for exactly the users the alias exists for.
        assert.strictEqual(resolveWorkingLanguage(undefined, atUser('fa')).language, 'fa');
    });
});

describe('Working-language scope precedence (CORE-1760)', () => {
    // The defect this pins: resolving by key name first let a *global*
    // workingLanguage outrank a *workspace* targetLanguage, inverting VS
    // Code's own precedence. Every project shipping the old key in
    // .vscode/settings.json would then silently resolve to the reader's
    // global language — and the picker writes that global key on its first
    // use in an unpinned project, so no one had to opt in.

    it('lets a workspace alias beat a global workingLanguage', () => {
        const resolved = resolveWorkingLanguage(atUser('pt'), atWorkspace('de'));
        assert.strictEqual(resolved.language, 'de');
        assert.strictEqual(resolved.scope, 'workspace');
    });

    it('lets a folder alias beat a global workingLanguage', () => {
        const resolved = resolveWorkingLanguage(atUser('pt'), atFolder('fr'));
        assert.strictEqual(resolved.language, 'fr');
        assert.strictEqual(resolved.scope, 'folder');
    });

    it('lets a workspace workingLanguage beat a global alias', () => {
        // The mirror image: the new name does not lose its scope advantage
        // either.
        const resolved = resolveWorkingLanguage(atWorkspace('de'), atUser('pt'));
        assert.strictEqual(resolved.language, 'de');
        assert.strictEqual(resolved.scope, 'workspace');
    });

    it('applies key priority within a scope, not across scopes', () => {
        const resolved = resolveWorkingLanguage(
            { workspaceValue: 'de', globalValue: 'pt' },
            { workspaceValue: 'fa', globalValue: 'ar' }
        );
        assert.strictEqual(resolved.language, 'de', 'workspace wins, and there the new key wins');
        assert.strictEqual(resolved.scope, 'workspace');
    });

    it('walks folder then workspace then user', () => {
        const resolved = resolveWorkingLanguage(
            { globalValue: 'pt' },
            { workspaceFolderValue: 'fr', workspaceValue: 'de' }
        );
        assert.strictEqual(resolved.language, 'fr');
        assert.strictEqual(resolved.scope, 'folder');
    });

    it('reports the scope that actually supplied the value', () => {
        // The picker writes at the reported scope; a scope that does not hold
        // what was just read sends the write somewhere it will be shadowed.
        assert.strictEqual(
            resolveWorkingLanguage(undefined, atWorkspace('de')).scope,
            'workspace',
            'an alias-supplied value must report the alias\'s scope'
        );
        assert.strictEqual(resolveWorkingLanguage(atUser('pt'), undefined).scope, 'user');
    });
});

describe('Known-languages seeding (CORE-1760)', () => {
    it('seeds from the working language when nothing is configured', () => {
        assert.deepStrictEqual(resolveKnownLanguages(undefined, 'pt'), ['pt']);
    });

    it('seeds from the working language when the configured set is empty', () => {
        // Clearing every box in the manager must not produce a profile where
        // nothing is known — the user necessarily reads the language they
        // work in.
        assert.deepStrictEqual(resolveKnownLanguages([], 'pt'), ['pt']);
    });

    it('returns the configured set when one exists', () => {
        assert.deepStrictEqual(resolveKnownLanguages(['pt', 'en'], 'pt'), ['pt', 'en']);
    });

    it('does not force the working language into a configured set', () => {
        // A deliberate set is respected as written; the seed is a fallback,
        // not an invariant member.
        assert.deepStrictEqual(resolveKnownLanguages(['en'], 'pt'), ['en']);
    });

    it('drops duplicates and non-string junk from a hand-edited setting', () => {
        assert.deepStrictEqual(
            resolveKnownLanguages(['pt', 'pt', '', 'en'], 'pt'),
            ['pt', 'en']
        );
    });

    describe('a wrongly-typed setting must not throw', () => {
        // VS Code neither validates a hand-edited value against the declared
        // schema on write nor coerces it on read, so any of these can arrive
        // here verbatim. Assuming an array threw a TypeError on the
        // activation path, and the measured blast radius was total: language
        // changes stopped happening at all, with no error and the previous
        // transition still reporting `applied` — a silent no-op wearing a
        // success badge, which is the failure class this subsystem keeps
        // producing.
        const malformed: Array<[string, unknown]> = [
            ['a bare string', 'pt'],
            ['a number', 42],
            ['a boolean', true],
            ['an object', { pt: true }],
            ['null', null],
        ];

        for (const [description, value] of malformed) {
            it(`falls back to the seed for ${description}`, () => {
                assert.deepStrictEqual(resolveKnownLanguages(value, 'pt'), ['pt']);
            });
        }

        it('keeps the usable codes out of a mixed array', () => {
            assert.deepStrictEqual(
                resolveKnownLanguages(['pt', 7, null, 'en', {}], 'pt'),
                ['pt', 'en']
            );
        });
    });
});

describe('Mismatch suppression by known languages (CORE-1760)', () => {
    it('signals a file language the user does not know', () => {
        // The motivating case: Portuguese working language, Farsi file.
        assert.strictEqual(isUnfamiliarFileLanguage('fa', 'pt', ['pt', 'en']), true);
    });

    it('suppresses the signal when the file language is known', () => {
        // An English file for a Portuguese speaker who reads English: it just
        // works — no signal, no offer.
        assert.strictEqual(isUnfamiliarFileLanguage('en', 'pt', ['pt', 'en']), false);
    });

    it('never signals the working language itself', () => {
        // Even with a hand-edited known set that omits it.
        assert.strictEqual(isUnfamiliarFileLanguage('pt', 'pt', ['en']), false);
    });

    it('signals nothing on a seeded first run for own-language files', () => {
        const known = resolveKnownLanguages(undefined, 'pt');
        assert.strictEqual(isUnfamiliarFileLanguage('pt', 'pt', known), false);
    });
});

describe('Picker ordering by known languages (CORE-1760)', () => {
    const languages = [
        { code: 'ar', nativeName: 'العربية' },
        { code: 'en', nativeName: 'English' },
        { code: 'fa', nativeName: 'فارسی' },
        { code: 'pt', nativeName: 'Português' },
    ];

    it('puts known languages in the first partition, list order preserved', () => {
        const { known, others } = partitionByKnown(languages, ['pt', 'en']);
        assert.deepStrictEqual(known.map(l => l.code), ['en', 'pt']);
        assert.deepStrictEqual(others.map(l => l.code), ['ar', 'fa']);
    });

    it('keeps every language exactly once across the two partitions', () => {
        const { known, others } = partitionByKnown(languages, ['en']);
        assert.deepStrictEqual(
            [...known, ...others].map(l => l.code).sort(),
            languages.map(l => l.code).sort()
        );
    });

    it('ignores known codes that are not in the offered list', () => {
        const { known, others } = partitionByKnown(languages, ['xx', 'pt']);
        assert.deepStrictEqual(known.map(l => l.code), ['pt']);
        assert.strictEqual(others.length, 3);
    });
});

describe('Protocol carry: separate file and working slots (CORE-1760)', () => {
    it('carries file and working languages as distinct slots', () => {
        const languages = buildResolvedLanguages('en', 'fa', 'pt');
        assert.strictEqual(languages.fileLanguage, 'fa');
        assert.strictEqual(languages.workingLanguage, 'pt');
        // Collapsing them client-side is the defect this vocabulary exists to
        // prevent: the server cannot un-collapse a single slot.
        assert.notStrictEqual(languages.fileLanguage, languages.workingLanguage);
    });

    it('mirrors the file language into the deprecated targetLanguage slot', () => {
        // A server that predates the role split parsed files by
        // targetLanguage; the compat slot must therefore carry the file
        // language, never the working language.
        const languages = buildResolvedLanguages('en', 'fa', 'pt');
        assert.strictEqual(languages.targetLanguage, 'fa');
    });

    it('carries the canonical language unchanged', () => {
        assert.strictEqual(buildResolvedLanguages('en', 'fa', 'pt').sourceLanguage, 'en');
    });

    it('survives a JSON round-trip with all slots intact', () => {
        // initializationOptions travel as JSON; nothing may rely on class
        // instances or undefined-dropping.
        const sent = buildResolvedLanguages('en', 'fa', 'pt');
        const received = JSON.parse(JSON.stringify(sent));
        assert.deepStrictEqual(received, {
            sourceLanguage: 'en',
            fileLanguage: 'fa',
            workingLanguage: 'pt',
            targetLanguage: 'fa',
        });
    });
});

describe('Server identity across the role split (CORE-1760)', () => {
    it('keeps the source->file shape when file and working agree', () => {
        // The own-files case, and the shape every existing assertion and log
        // line knows.
        assert.strictEqual(
            serverIdentityOf(buildResolvedLanguages('en', 'de', 'de')),
            'en->de'
        );
    });

    it('includes the working language when it differs from the file language', () => {
        // The server reads the working language at initialize, so a change to
        // it must produce a different identity — identical identities
        // collapse to a no-op restart.
        assert.strictEqual(
            serverIdentityOf(buildResolvedLanguages('en', 'fa', 'pt')),
            'en->fa+pt'
        );
        assert.notStrictEqual(
            serverIdentityOf(buildResolvedLanguages('en', 'fa', 'pt')),
            serverIdentityOf(buildResolvedLanguages('en', 'fa', 'en'))
        );
    });

    it('names the file language from either identity shape', () => {
        assert.strictEqual(identityFileLanguage('en->de'), 'de');
        assert.strictEqual(identityFileLanguage('en->fa+pt'), 'fa');
    });
});
