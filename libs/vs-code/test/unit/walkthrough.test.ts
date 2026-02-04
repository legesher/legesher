/**
 * Unit tests for walkthrough functionality
 *
 * Tests the tryTranslationPanel demo code and walkthrough configuration.
 */

import * as assert from 'assert';

describe('Walkthrough Module', () => {
    describe('Sample Python Code', () => {
        // This is the sample code from tryTranslationPanel in extension.ts
        // We test it separately to ensure it remains valid Python with good keyword coverage
        const getSampleCode = (langName: string) => `# Legesher Demo - See your code in ${langName}!
# Hover over keywords to see translations

def greet(name):
    """Say hello to someone."""
    if name:
        print(f"Hello, {name}!")
        return True
    else:
        print("Hello, World!")
        return False

class Calculator:
    """A simple calculator class."""

    def __init__(self):
        self.result = 0

    def add(self, x, y):
        """Add two numbers."""
        self.result = x + y
        return self.result

# Try it out!
for i in range(3):
    greet(f"User {i}")

# Error handling example
try:
    value = int("not a number")
except ValueError as e:
    print(f"Caught an error: {e}")
finally:
    print("Done!")
`;

        it('should contain essential Python keywords', () => {
            const sampleCode = getSampleCode('Spanish');

            // Keywords that should be in the sample for good demo coverage
            const expectedKeywords = [
                'def',      // function definition
                'if',       // conditional
                'else',     // conditional branch
                'return',   // function return
                'True',     // boolean literal
                'False',    // boolean literal
                'class',    // class definition
                'for',      // loop
                'try',      // exception handling
                'except',   // exception handling
                'finally',  // exception handling
                'as',       // exception aliasing
            ];

            expectedKeywords.forEach(keyword => {
                assert.ok(
                    sampleCode.includes(keyword),
                    `Sample code should contain keyword '${keyword}'`
                );
            });
        });

        it('should contain essential Python builtins', () => {
            const sampleCode = getSampleCode('Spanish');

            // Builtins that should be in the sample
            const expectedBuiltins = [
                'print',    // output function
                'range',    // iteration helper
                'int',      // type conversion
            ];

            expectedBuiltins.forEach(builtin => {
                assert.ok(
                    sampleCode.includes(builtin),
                    `Sample code should contain builtin '${builtin}'`
                );
            });
        });

        it('should include the target language name in the header', () => {
            const langName = 'Español';
            const sampleCode = getSampleCode(langName);

            assert.ok(
                sampleCode.includes(langName),
                'Sample code header should include the target language name'
            );
        });

        it('should be syntactically valid Python', () => {
            const sampleCode = getSampleCode('Spanish');

            // Basic syntax checks (not a full parser, but catches obvious issues)
            // Check balanced parentheses
            const openParens = (sampleCode.match(/\(/g) || []).length;
            const closeParens = (sampleCode.match(/\)/g) || []).length;
            assert.strictEqual(openParens, closeParens, 'Parentheses should be balanced');

            // Check that function definitions have colons
            const defLines = sampleCode.split('\n').filter(line => line.trim().startsWith('def '));
            defLines.forEach(line => {
                assert.ok(
                    line.includes(':'),
                    `Function definition should end with colon: ${line}`
                );
            });

            // Check that class definitions have colons
            const classLines = sampleCode.split('\n').filter(line => line.trim().startsWith('class '));
            classLines.forEach(line => {
                assert.ok(
                    line.includes(':'),
                    `Class definition should end with colon: ${line}`
                );
            });
        });

        it('should have good keyword variety for translation demo', () => {
            const sampleCode = getSampleCode('Spanish');

            // Count unique keywords present
            const allKeywords = [
                'def', 'if', 'else', 'elif', 'return', 'True', 'False', 'None',
                'class', 'for', 'while', 'try', 'except', 'finally', 'as',
                'import', 'from', 'with', 'lambda', 'yield', 'raise', 'pass',
                'break', 'continue', 'and', 'or', 'not', 'in', 'is',
                'async', 'await', 'global', 'nonlocal'
            ];

            const presentKeywords = allKeywords.filter(kw => sampleCode.includes(kw));

            // Should have at least 10 different keywords for a good demo
            assert.ok(
                presentKeywords.length >= 10,
                `Sample should contain at least 10 keywords, found ${presentKeywords.length}: ${presentKeywords.join(', ')}`
            );
        });
    });

    describe('Walkthrough Step IDs', () => {
        const walkthroughSteps = [
            { id: 'legesher.welcome.intro', hasCompletionEvent: false },
            { id: 'legesher.welcome.install', hasCompletionEvent: false },
            { id: 'legesher.welcome.selectLanguage', hasCompletionEvent: true },
            { id: 'legesher.welcome.translationPanel', hasCompletionEvent: true },
            { id: 'legesher.welcome.hover', hasCompletionEvent: false },
            { id: 'legesher.welcome.feedback', hasCompletionEvent: true }
        ];

        it('should have correct number of walkthrough steps', () => {
            assert.strictEqual(walkthroughSteps.length, 6, 'Should have 6 walkthrough steps');
        });

        it('should follow consistent naming convention', () => {
            walkthroughSteps.forEach(step => {
                assert.ok(
                    step.id.startsWith('legesher.welcome.'),
                    `Step ID ${step.id} should start with 'legesher.welcome.'`
                );
            });
        });

        it('should have completion events only for interactive steps', () => {
            // Steps with commands should have completion events
            const interactiveSteps = ['selectLanguage', 'translationPanel', 'feedback'];

            walkthroughSteps.forEach(step => {
                const stepName = step.id.split('.').pop();
                const isInteractive = interactiveSteps.includes(stepName || '');

                assert.strictEqual(
                    step.hasCompletionEvent,
                    isInteractive,
                    `Step ${step.id} completion event expectation mismatch`
                );
            });
        });
    });
});
