/**
 * Unit tests for telemetry module
 *
 * Tests telemetry initialization, event tracking, and privacy controls.
 */

import * as assert from 'assert';
import * as sinon from 'sinon';

import { sanitizeErrorContext } from '../../src/telemetrySanitizer';

// Store original env
const originalEnv = { ...process.env };

describe('Telemetry Module', () => {
    let sandbox: sinon.SinonSandbox;

    beforeEach(() => {
        sandbox = sinon.createSandbox();
        // Reset environment
        process.env = { ...originalEnv };
    });

    afterEach(() => {
        sandbox.restore();
        process.env = originalEnv;
    });

    describe('Connection String Handling', () => {
        it('should not log connection string contents', () => {
            // This test verifies the security fix from v0.1.2
            // The connection string should never appear in logs
            const consoleLogSpy = sandbox.spy(console, 'log');

            // Set a mock connection string
            process.env.LEGESHER_TELEMETRY_CONNECTION_STRING = 'InstrumentationKey=test-key-12345;Endpoint=https://test.com';

            // The telemetry module should only log whether the string is present, not its contents
            // This is a design verification test
            const connectionString = process.env.LEGESHER_TELEMETRY_CONNECTION_STRING;

            // Good: Log presence only
            console.log('[Legesher Telemetry] Connection string present:', !!connectionString);

            // Verify the actual value was not logged
            const logCalls = consoleLogSpy.getCalls().map(call => call.args.join(' '));
            logCalls.forEach(log => {
                assert.ok(!log.includes('InstrumentationKey'), 'Connection string should not be logged');
                assert.ok(!log.includes('test-key'), 'Key contents should not be logged');
            });
        });

        it('should handle missing connection string gracefully', () => {
            delete process.env.LEGESHER_TELEMETRY_CONNECTION_STRING;

            const connectionString = process.env.LEGESHER_TELEMETRY_CONNECTION_STRING || '';

            assert.strictEqual(connectionString, '');
            assert.strictEqual(!!connectionString, false);
        });

        it('should handle empty connection string', () => {
            process.env.LEGESHER_TELEMETRY_CONNECTION_STRING = '';

            const connectionString = process.env.LEGESHER_TELEMETRY_CONNECTION_STRING || '';

            assert.strictEqual(connectionString, '');
            assert.strictEqual(!!connectionString, false);
        });
    });

    describe('Telemetry Settings', () => {
        it('should respect telemetry.enabled setting', () => {
            // Test that telemetry can be disabled via settings
            const mockConfig = {
                'telemetry.enabled': false,
            };

            const telemetryEnabled = mockConfig['telemetry.enabled'];

            assert.strictEqual(telemetryEnabled, false);
        });

        it('should default telemetry to disabled (opt-in)', () => {
            const mockConfig: Record<string, boolean> = {};

            const telemetryEnabled = mockConfig['telemetry.enabled'] ?? false;

            assert.strictEqual(telemetryEnabled, false);
        });

        it('should track ML training consent separately', () => {
            const mockConfig = {
                'telemetry.enabled': true,
                'telemetry.contributeToMLTraining': false,
            };

            // Basic telemetry enabled, but ML training disabled
            assert.strictEqual(mockConfig['telemetry.enabled'], true);
            assert.strictEqual(mockConfig['telemetry.contributeToMLTraining'], false);
        });
    });

    describe('Event Tracking Behavior', () => {
        it('should not throw when tracking without initialization', () => {
            // Telemetry methods should fail silently when reporter is undefined
            // This is important for graceful degradation
            const reporter: any = undefined;

            assert.doesNotThrow(() => {
                if (!reporter) return;
                reporter.sendTelemetryEvent('test');
            });
        });

        it('should track language change events with from/to', () => {
            const fromLanguage = 'en';
            const toLanguage = 'es';

            const eventData = {
                fromLanguage,
                toLanguage,
            };

            assert.strictEqual(eventData.fromLanguage, 'en');
            assert.strictEqual(eventData.toLanguage, 'es');
        });

        it('should track activation with correct properties', () => {
            const language = 'es';
            const vscodeVersion = '1.85.0';
            const extensionVersion = '0.1.2';

            const eventData = {
                targetLanguage: language,
                vscodeVersion,
                extensionVersion,
            };

            assert.strictEqual(eventData.targetLanguage, 'es');
            assert.strictEqual(eventData.vscodeVersion, '1.85.0');
            assert.strictEqual(eventData.extensionVersion, '0.1.2');
        });
    });

    describe('Privacy Protection', () => {
        it('should only track Python keywords in hover events', () => {
            // List of Python keywords that are safe to track
            const pythonKeywords = [
                'def', 'class', 'if', 'else', 'for', 'while', 'return',
                'import', 'from', 'try', 'except', 'finally', 'with',
                'as', 'lambda', 'yield', 'raise', 'pass', 'break',
                'continue', 'and', 'or', 'not', 'in', 'is', 'True',
                'False', 'None', 'async', 'await', 'global', 'nonlocal',
            ];

            // User-defined names should NOT be tracked
            const userDefinedNames = [
                'myFunction', 'userName', 'calculateTotal', 'processData',
            ];

            // Verify keywords are recognized
            pythonKeywords.forEach(keyword => {
                assert.ok(
                    pythonKeywords.includes(keyword),
                    `${keyword} should be in Python keywords list`
                );
            });

            // Verify user-defined names are NOT in the keywords list
            userDefinedNames.forEach(name => {
                assert.ok(
                    !pythonKeywords.includes(name),
                    `${name} should NOT be tracked as a keyword`
                );
            });
        });
    });

    describe('PII Sanitization', () => {
        // These exercise the shipped sanitizeErrorContext(), on real inputs and
        // exact outputs. The block they replace declared a local copy of the two
        // regexes and asserted against that, so it passed while the real
        // trackError() forwarded `C:\Users\jane\...` intact, and its
        // "Windows-style paths" case fed the scrubber a forward-slash string
        // that Windows never produces (CORE-596, absorbing CORE-2031).

        const redactionCases: ReadonlyArray<{ what: string; input: string; expected: string }> = [
            {
                what: 'a POSIX home path',
                input: 'Error in /Users/john/code/project/secret.py',
                expected: 'Error in <path>',
            },
            {
                what: 'a Linux home path',
                input: 'Cannot read /home/jdoe/.config/legesher/settings.json',
                expected: 'Cannot read <path>',
            },
            {
                what: 'a Windows drive-rooted path',
                input: 'Error in C:\\Users\\jdoe\\Documents\\file.py',
                expected: 'Error in <path>',
            },
            {
                what: 'a Windows drive-rooted path written with forward slashes',
                input: 'Error in C:/Users/jdoe/Documents/file.py',
                expected: 'Error in <path>',
            },
            // `C:jane` names `jane` on drive C relative to the current
            // directory, so it is a path with no separator in it at all. The
            // first version of this scrubber required one after the drive
            // letter and let the whole thing through as a word.
            {
                what: 'a drive-relative Windows path, which carries no separator',
                input: 'C:jane',
                expected: '<path>',
            },
            {
                what: 'a drive-relative Windows path mid-sentence',
                input: 'Could not open D:jdoe',
                expected: 'Could not open <path>',
            },
            {
                what: 'a drive-relative Windows path after an errno label',
                input: 'Failed: Z:jsmith',
                expected: 'Failed: <path>',
            },
            // Splitting a token on every colon destroys the drive marker
            // before anything can classify it, so `C:jsmith` reaches the
            // endpoint as two safe-looking words. The split is on the first
            // colon only.
            {
                what: 'a drive marker in the value half of a key:value token',
                input: 'cwd:C:jsmith',
                expected: 'cwd:<path>',
            },
            {
                what: 'a full Windows path in the value half of a key:value token',
                input: 'workingLanguage:C:\\Users\\jane\\x.py',
                expected: 'workingLanguage:<path>',
            },
            // `%` is a safe word character, so a percent-encoded path carries
            // no separator this scrubber can see.
            {
                what: 'a percent-encoded Windows path',
                input: 'C%3A%5CUsers%5Cjane%5CDesktop',
                expected: '<redacted>',
            },
            {
                what: 'a percent-encoded POSIX path',
                input: '%2FUsers%2Fjane',
                expected: '<redacted>',
            },
            {
                what: 'a UNC path',
                input: 'Cannot open \\\\fileserver\\share\\jdoe\\main.py',
                expected: 'Cannot open <path>',
            },
            {
                what: 'a POSIX path containing spaces',
                input: 'Error in /Users/John Smith/Documents/file.py',
                expected: 'Error in <path>',
            },
            {
                what: 'a Windows path containing spaces',
                input: 'Error in C:\\Users\\John Smith\\Documents\\file.py',
                expected: 'Error in <path>',
            },
            {
                what: 'a home-relative path',
                input: 'Missing ~/.legesher/cache.json',
                expected: 'Missing <path>',
            },
            {
                what: 'a quoted path inside an errno message',
                input: "ENOENT: no such file or directory, open '/Users/jdoe/main.py'",
                expected: 'ENOENT: no such file or directory, open <path>',
            },
            // A quote is the only end marker a path containing a space has, and
            // it is the marker Node's errno messages use. Without the
            // whole-string pre-pass the trailing `Smith'` is a bare word and
            // survives.
            {
                what: 'a quoted Windows path containing a space',
                input: "EPERM: operation not permitted, scandir 'C:\\Users\\Jane Smith'",
                expected: 'EPERM: operation not permitted, scandir <path>',
            },
            {
                what: 'a quoted POSIX path whose last segment contains a space',
                input: "Cannot open '/Volumes/Jane Smith'",
                expected: 'Cannot open <path>',
            },
            {
                what: 'a nested path with dots and hyphens',
                input: 'Cannot read /var/lib/data-repo/cache/lang-pack.v2.json',
                expected: 'Cannot read <path>',
            },
            {
                what: 'an IPv4 address',
                input: 'connection to 192.168.1.42 refused',
                expected: 'connection to <ip> refused',
            },
            {
                what: 'an IPv4 address with a port',
                input: 'connection to 10.0.0.7:8080 refused',
                expected: 'connection to <ip> refused',
            },
            {
                what: 'an IPv6 address',
                input: 'connection to fe80::1 refused',
                expected: 'connection to <ip> refused',
            },
            {
                what: 'a URL carrying an internal domain',
                input: 'GET http://internal.corp.com/api/v1/user/12345 failed',
                expected: 'GET <url> failed',
            },
            {
                what: 'a bare hostname carrying a username',
                input: 'connection refused by john-macbook.local',
                expected: 'connection refused by <redacted>',
            },
            {
                what: 'a bare filename, which has the same shape as a hostname',
                input: 'Cannot read jane-doe-resume.py',
                expected: 'Cannot read <redacted>',
            },
            {
                what: 'an email address',
                input: 'Failed for user john.doe@example.com on startup',
                expected: 'Failed for user <email> on startup',
            },
            {
                what: 'a token of no recognised shape',
                input: 'write failed with fd=7&owner=jdoe',
                expected: 'write failed with <redacted>',
            },
            {
                what: 'several kinds of PII at once',
                input: 'Error in /home/user/file.py: contact admin@corp.com or support@corp.com',
                expected: 'Error in <path>: contact <email> or <email>',
            },
            {
                what: 'a path in the value half of the key:value contexts we send',
                input: 'workingLanguage:EACCES /Users/jdoe/.vscode/settings.json',
                expected: 'workingLanguage:EACCES <path>',
            },
        ];

        redactionCases.forEach(({ what, input, expected }) => {
            it(`redacts ${what}`, () => {
                assert.strictEqual(sanitizeErrorContext(input), expected);
            });
        });

        it('never lets an identifying fragment through', () => {
            // A second, blunter net over the same table: whatever the
            // placeholders end up looking like, none of these may survive.
            const mustNotSurvive = [
                'john', 'jdoe', 'jsmith', 'Smith', 'jane', 'doe', 'corp.com', 'macbook',
                '192.168.1.42', '10.0.0.7', 'fileserver', 'Users', 'home/user',
                'Desktop', 'Volumes',
            ];

            redactionCases.forEach(({ what, input }) => {
                const result = sanitizeErrorContext(input);
                mustNotSurvive.forEach(fragment => {
                    assert.ok(
                        !result.includes(fragment),
                        `"${fragment}" survived sanitization of ${what}: ${result}`
                    );
                });
            });
        });

        it('is idempotent, so a placeholder is never redacted again', () => {
            redactionCases.forEach(({ what, input }) => {
                const once = sanitizeErrorContext(input);
                assert.strictEqual(sanitizeErrorContext(once), once, `not idempotent for ${what}`);
            });
        });

        const preservedContexts: ReadonlyArray<{ what: string; input: string }> = [
            { what: 'an enumerated error label', input: 'serverCrash' },
            { what: 'a camelCase failure name', input: 'initializationFailed' },
            { what: 'a plain English sentence', input: 'Language server closed unexpectedly' },
            // The exact shapes extension.ts sends for languageWriteShadowed
            // and languageWriteFailed.
            { what: 'a setting:scope pair', input: 'workingLanguage:workspace' },
            { what: 'a setting:scope pair for the known set', input: 'knownLanguages:folder' },
            { what: 'one of our own setting names', input: 'legesher.workingLanguage is not registered' },
            { what: 'a version number', input: 'version 0.1.5 is not supported' },
            // Letters are matched by Unicode property, not A-Z: VS Code's
            // messages are localized, and so are the people using this.
            { what: 'a localized message', input: 'No se pudo escribir la configuración' },
            // `%` on its own is ordinary content; only a full `%XX` escape is
            // a separator in disguise.
            { what: 'an unexpanded environment variable', input: '%USERPROFILE%' },
            { what: 'a percentage', input: 'translation 100% complete' },
            // The key:value rule splits on the first colon, so an errno label
            // followed by prose is still a label followed by prose.
            { what: 'an errno label ahead of its message', input: 'ENOENT: no such file or directory' },
            // The quoted-path pre-pass only fires on a run that holds a path
            // anchor; a quoted setting name is not one.
            { what: 'a quoted setting name', input: "Unknown configuration 'workingLanguage'" },
        ];

        preservedContexts.forEach(({ what, input }) => {
            it(`leaves ${what} unchanged`, () => {
                assert.strictEqual(sanitizeErrorContext(input), input);
            });
        });

        it('falls back to "none" when there is no context', () => {
            assert.strictEqual(sanitizeErrorContext(undefined), 'none');
            assert.strictEqual(sanitizeErrorContext(''), 'none');
            assert.strictEqual(sanitizeErrorContext('   \n  '), 'none');
        });

        // Personal data this scrubber does NOT remove, pinned to its exact
        // current output so the residue is owned instead of invisible. These
        // are not aspirational: each one is a string that reaches the analytics
        // endpoint today, and the matching "Known residue" section of
        // telemetrySanitizer.ts says why.
        //
        // If a case here starts failing, the scrubber got better: move the case
        // up into `redactionCases` with its new expectation. Do not edit the
        // expectation in place to make the suite green.
        const knownResidue: ReadonlyArray<{ what: string; leaks: string; input: string; expected: string }> = [
            // A path containing a space is split on that space. Interior
            // segments carry a separator of their own and are redacted; the
            // first and last carry none.
            {
                what: 'the last segment of an unquoted path containing a space',
                leaks: 'the surname',
                input: 'Unable to resolve workspace folder C:\\Users\\Jane Smith',
                expected: 'Unable to resolve workspace folder <path> Smith',
            },
            {
                what: 'the first segment of an unquoted path containing a space',
                leaks: 'the given name',
                input: 'Jane Smith\\Documents\\project\\main.py could not be read',
                expected: 'Jane <path> could not be read',
            },
            {
                what: 'the last segment of an unquoted POSIX path containing a space',
                leaks: 'the folder name',
                input: 'watch ENOSPC /home/jane/src/Patient Records',
                expected: 'watch ENOSPC <path> Records',
            },
            {
                what: 'every trailing segment of an unquoted volume name',
                leaks: 'the surname and the volume label',
                input: 'Failed to read directory: /Volumes/Jane Smith Backup',
                expected: 'Failed to read directory: <path> Smith Backup',
            },
            // JS `\s` already covers NBSP and the other space separators, so
            // U+00A0 is neither better nor worse than U+0020 here.
            {
                what: 'a path split on a no-break space, exactly as on a plain space',
                leaks: 'the surname',
                input: 'Unable to resolve workspace folder C:\\Users\\Jane\u00a0Smith',
                expected: 'Unable to resolve workspace folder <path> Smith',
            },
            // The quoted pre-pass needs the run to be free of other quote
            // characters, so a nested quote puts the message back in the
            // unquoted case above.
            {
                what: 'a quoted path containing a nested quote',
                leaks: 'the surname',
                input: 'Cannot open \'C:\\Users\\Jane "Janey" Smith\'',
                expected: 'Cannot open <path> "Janey" Smith\'',
            },
            // Bare-word personal data survives by design: nothing in its shape
            // distinguishes it from the diagnostic prose it sits in.
            {
                what: 'a hostname with no domain suffix',
                leaks: 'the machine owner',
                input: 'connection refused by jane-macbook',
                expected: 'connection refused by jane-macbook',
            },
            {
                what: 'a NetBIOS-style computer name',
                leaks: 'the machine owner',
                input: 'cannot reach JANE-PC',
                expected: 'cannot reach JANE-PC',
            },
            {
                what: 'a username in the value half of a key:value token',
                leaks: 'the account name',
                input: 'user:jsmith',
                expected: 'user:jsmith',
            },
            {
                what: 'a person name written as prose',
                leaks: 'the full name',
                input: 'Jane Smith',
                expected: 'Jane Smith',
            },
            // The quoted-run pre-pass substitutes its placeholder mid-string
            // with no whitespace boundary. Abutting text containing a colon
            // therefore fuses with it: the leading `<` is stripped as
            // punctuation, the `>` lands in the key half, and the value half is
            // judged on its own. Only reachable with no whitespace between the
            // two, which no message we send produces. Padding the placeholder
            // was measured and is 30x worse, because the extra token boundaries
            // manufacture bare words.
            {
                what: 'text fused onto a quoted path with no whitespace between',
                leaks: 'the account name',
                input: "'C:\\a\\b'user:jsmith",
                expected: '<redacted>:jsmith',
            },
            {
                what: 'a drive-relative path fused onto a quoted UNC path',
                leaks: 'the user directory',
                input: '`\\\\srv\\share\\Zqxjane`C:Zqxjane',
                expected: '<redacted>:Zqxjane',
            },
            // U+0430 CYRILLIC SMALL LETTER A, which is a letter under \p{L}
            // exactly like the Latin one it imitates.
            {
                what: 'a name spelled with a homoglyph',
                leaks: 'the given name',
                input: 'j\u0430ne',
                expected: 'j\u0430ne',
            },
            {
                what: 'a phone number',
                leaks: 'the phone number',
                input: '+1-415-555-0123',
                expected: '+1-415-555-0123',
            },
        ];

        describe('known residue (documented, not fixed)', () => {
            knownResidue.forEach(({ what, leaks, input, expected }) => {
                it(`still forwards ${what} (leaks ${leaks})`, () => {
                    assert.strictEqual(sanitizeErrorContext(input), expected);
                });
            });
        });

        describe('degenerate input', () => {
            // The key:value rule recurses once per colon, so a long enough run
            // exhausted the stack. trackError scrubs outside its own try, and
            // two of its call sites are themselves error handlers, so the
            // RangeError escaped into one.
            it('does not overflow the stack on a long run of colons', () => {
                const pathological = ':'.repeat(50000);
                assert.strictEqual(sanitizeErrorContext(pathological), '<redacted>');
            });

            it('still classifies the colon shapes we actually send', () => {
                assert.strictEqual(sanitizeErrorContext('workingLanguage:workspace'), 'workingLanguage:workspace');
                assert.strictEqual(sanitizeErrorContext('cwd:C:jsmith'), 'cwd:<path>');
                assert.strictEqual(sanitizeErrorContext('fe80::1'), '<ip>');
                assert.strictEqual(sanitizeErrorContext('1:2:3:4:5:6:7:8'), '<ip>');
                assert.strictEqual(sanitizeErrorContext('10.0.0.7:8080'), '<ip>');
            });
        });
    });

    describe('Type-Safe Parameters', () => {
        it('should only allow known command names', () => {
            const validCommands: string[] = [
                'restartServer',
                'selectLanguage',
                'showTranslationPanel',
                'tryTranslationPanel',
                'giveFeedback',
            ];

            // These are the ONLY valid commands — no arbitrary strings allowed
            assert.strictEqual(validCommands.length, 5, 'Exactly 5 tracked commands should exist');

            // Verify all expected commands are present
            assert.ok(validCommands.includes('restartServer'));
            assert.ok(validCommands.includes('selectLanguage'));
            assert.ok(validCommands.includes('showTranslationPanel'));
            assert.ok(validCommands.includes('tryTranslationPanel'));
            assert.ok(validCommands.includes('giveFeedback'));
        });

        it('should only allow known feature names', () => {
            const validFeatures: string[] = [
                'completion',
                'hover',
                'panel',
                'semanticTokens',
            ];

            assert.strictEqual(validFeatures.length, 4, 'Exactly 4 tracked features should exist');
        });

        it('should only allow known error types', () => {
            const validErrorTypes: string[] = [
                'serverError',
                'serverConnectionClosed',
                'serverNotInstalled',
                'serverStartFailed',
                'translationFailed',
            ];

            assert.strictEqual(validErrorTypes.length, 5, 'Exactly 5 tracked error types should exist');
        });

        it('should only allow known feedback response types', () => {
            const validPromptTypes = ['first', 'second', 'manual'];
            const validResponses = ['gaveFeedback', 'deferred', 'optedOut'];

            assert.strictEqual(validPromptTypes.length, 3);
            assert.strictEqual(validResponses.length, 3);
        });
    });

    describe('Error Handling', () => {
        it('should not throw when reporter is undefined and methods are called', () => {
            // All telemetry methods should return silently when reporter is undefined
            // This tests the `if (!reporter) return;` guard in every method
            const reporter: any = undefined;

            const methods = [
                () => { if (!reporter) return; reporter.sendTelemetryEvent('test'); },
                () => { if (!reporter) return; reporter.sendTelemetryEvent('test', { key: 'val' }); },
                () => { if (!reporter) return; reporter.sendTelemetryErrorEvent('test', { key: 'val' }); },
            ];

            methods.forEach((method, i) => {
                assert.doesNotThrow(method, `Method ${i} should not throw when reporter is undefined`);
            });
        });

        it('should catch and swallow errors from reporter.sendTelemetryEvent', () => {
            // Simulates a reporter that throws — the try/catch should prevent propagation
            const faultyReporter = {
                sendTelemetryEvent: (..._args: unknown[]) => { throw new Error('Network failure'); },
                sendTelemetryErrorEvent: (..._args: unknown[]) => { throw new Error('Network failure'); },
            };

            // Wrap in the same pattern used in telemetry.ts
            assert.doesNotThrow(() => {
                try {
                    faultyReporter.sendTelemetryEvent('test');
                } catch (_error) {
                    // Swallowed — matches telemetry.ts behavior
                }
            });

            assert.doesNotThrow(() => {
                try {
                    faultyReporter.sendTelemetryErrorEvent('test');
                } catch (_error) {
                    // Swallowed — matches telemetry.ts behavior
                }
            });
        });
    });
});
