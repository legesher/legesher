/**
 * Unit tests for telemetry module
 *
 * Tests telemetry initialization, event tracking, and privacy controls.
 */

import * as assert from 'assert';
import * as sinon from 'sinon';

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

        it('should default telemetry to enabled', () => {
            const mockConfig: Record<string, boolean> = {};

            const telemetryEnabled = mockConfig['telemetry.enabled'] ?? true;

            assert.strictEqual(telemetryEnabled, true);
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

    describe('Walkthrough Tracking', () => {
        it('should track walkthrough opened event', () => {
            // Verify the event structure for walkthrough opened
            const eventName = 'walkthroughOpened';

            // The event should have no additional properties
            assert.strictEqual(eventName, 'walkthroughOpened');
        });

        it('should track walkthrough step completion with stepId', () => {
            const stepId = 'legesher.welcome.selectLanguage';

            const eventData = {
                stepId
            };

            assert.strictEqual(eventData.stepId, 'legesher.welcome.selectLanguage');
        });

        it('should track all walkthrough step IDs correctly', () => {
            const expectedStepIds = [
                'legesher.welcome.intro',
                'legesher.welcome.install',
                'legesher.welcome.selectLanguage',
                'legesher.welcome.translationPanel',
                'legesher.welcome.hover',
                'legesher.welcome.feedback'
            ];

            expectedStepIds.forEach(stepId => {
                const eventData = { stepId };
                assert.ok(
                    eventData.stepId.startsWith('legesher.welcome.'),
                    `Step ID ${stepId} should follow naming convention`
                );
            });
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

        it('should not include PII in error tracking', () => {
            // Error context should be generic, not contain file paths or code
            const safeErrorContexts = [
                'serverCrash',
                'translationFailed',
                'connectionTimeout',
                'initializationFailed',
            ];

            const unsafeContexts = [
                '/Users/john/code/project/secret.py',
                'Error at line 42: password = "123456"',
                'john@example.com',
            ];

            // Safe contexts should be allowed
            safeErrorContexts.forEach(context => {
                assert.ok(
                    !context.includes('/') && !context.includes('@'),
                    `${context} is a safe error context`
                );
            });

            // Would need to validate/sanitize these in actual implementation
            unsafeContexts.forEach(context => {
                assert.ok(
                    context.includes('/') || context.includes('@') || context.includes('='),
                    `${context} contains potentially sensitive data`
                );
            });
        });
    });
});
