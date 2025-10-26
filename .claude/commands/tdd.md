<!--
SOURCES:
- Anthropic Claude Code Best Practices: https://www.anthropic.com/engineering/claude-code-best-practices
- TDD workflow: Write tests → Confirm failure → Implement → Refactor
- Test-driven development with AI coding
-->

# Test-Driven Development: $ARGUMENTS

**Goal**: Implement $ARGUMENTS using test-driven development (TDD) methodology.

## TDD Workflow

This command follows strict TDD: **Tests First, Implementation Second**.

## Steps

### 1. Review Requirements

- Confirm: What behavior needs to be implemented?
- Identify: Expected inputs and outputs
- Define: Success criteria for $ARGUMENTS
- Review: Any existing tests in the area

### 2. Write Tests FIRST

**IMPORTANT**: Write tests BEFORE any implementation code.

- Create or update test file: `libs/{package}/tests/test_{module}.py`
- Write test cases that describe expected behavior
- Cover: happy path, edge cases, error conditions
- Use descriptive test names: `test_{what}_{scenario}_{expected}`
- Follow project conventions (pytest, fixtures, etc.)

Example structure:

```python
def test_{feature}_with_valid_input_returns_expected_result():
    # Arrange
    input_data = ...
    expected = ...

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected

def test_{feature}_with_invalid_input_raises_error():
    # Arrange
    invalid_input = ...

    # Act & Assert
    with pytest.raises(ExpectedError):
        function_under_test(invalid_input)
```

### 3. Run Tests and Confirm They FAIL

**Critical**: Tests must fail before implementation.

```bash
cd libs/{package} && uv run pytest tests/test_{module}.py -v
```

- Verify: Tests fail for the right reason (not syntax errors)
- Ensure: Failure messages are clear and helpful
- Confirm: No false positives (tests passing when they shouldn't)

If tests don't fail properly, revise the tests.

### 4. Commit Tests

```bash
git add tests/
git commit -m "test: add tests for $ARGUMENTS"
```

### 5. Implement Minimal Code

Now write the MINIMUM code to make tests pass.

- Don't over-engineer
- Don't add features not covered by tests
- Focus on making tests green
- Keep it simple

### 6. Run Tests Again

```bash
cd libs/{package} && uv run pytest tests/test_{module}.py -v
```

- Verify: All tests now pass
- Check: No broken tests in other modules
- Run: Full test suite to catch regressions

### 7. Refactor (Optional)

Now that tests pass, you can refactor safely:

- Improve code structure
- Remove duplication
- Improve naming
- Add documentation
- Run tests after each refactor to ensure they still pass

### 8. Commit Implementation

```bash
git add libs/{package}/
git commit -m "feat: implement $ARGUMENTS"
```

### 9. Test Coverage

Check coverage to ensure completeness:

```bash
uv run pytest --cov=legesher_{package} --cov-report=term-missing tests/
```

- Target: 90%+ coverage for new code
- Target: 100% for critical paths
- Add tests for any uncovered branches

## TDD Best Practices

### For Solo Founders

- **Tests are your safety net**: You're the only QA, tests catch regressions
- **Tests are documentation**: They show how code is meant to be used
- **Tests enable refactoring**: Change confidently knowing tests will catch breaks
- **Tests speed development**: Fix issues early when they're cheap

### For Open Source Contributors

- **Tests communicate intent**: Show contributors how code should behave
- **Tests prevent regressions**: Contributors can add features without breaking things
- **Tests guide contributions**: Contributors can write tests first, then ask for review

## When to Use TDD

**Good for TDD**:

- New features with clear input/output
- Bug fixes (write test that reproduces bug, then fix)
- Complex business logic
- Data transformations
- API endpoints
- Utilities and helpers

**Less suited for TDD**:

- Exploratory prototyping
- UI/visual design (use manual testing)
- Performance optimization (use benchmarks)
- Documentation-only changes

## Troubleshooting

**Tests won't fail**:

- Check: Are you testing the right thing?
- Ensure: You're importing the code under test
- Verify: Test assertions are actually running

**Tests are flaky**:

- Avoid: Time-dependent tests (use mocking)
- Avoid: File system dependencies (use fixtures/tmp directories)
- Avoid: Network calls (use mocks)

**Too many tests failing**:

- Start small: One test at a time
- Isolate: Test one function/class at a time
- Use: Test fixtures to reduce duplication

## Deliverable

At the end of this TDD cycle, you should have:

- [ ] Tests written first and committed
- [ ] Tests initially failed (confirmed)
- [ ] Implementation makes all tests pass
- [ ] Code coverage meets targets (90%+)
- [ ] Implementation committed with clear message
- [ ] Full test suite passes (no regressions)

Remember: Red → Green → Refactor. Tests first, always.
