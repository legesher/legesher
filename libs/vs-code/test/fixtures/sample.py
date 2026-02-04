# Sample Python file for VS Code extension integration tests
# This file contains various Python constructs that Legesher translates


def greet(name):
    """Say hello to someone."""
    if name:
        print(f"Hello, {name}!")
    else:
        print("Hello, World!")
    return True


class Calculator:
    """A simple calculator class."""

    def __init__(self):
        self.result = 0

    def add(self, value):
        self.result += value
        return self

    def subtract(self, value):
        self.result -= value
        return self


# Keywords that Legesher translates
for i in range(10):
    while i > 0:
        break

try:
    x = 1 / 0
except ZeroDivisionError:
    # Intentionally ignore ZeroDivisionError in this test fixture
    pass
finally:
    print("Done")


# Async support
async def fetch_data():
    await async_operation()  # noqa: F821
    yield "data"


# Boolean and None literals
is_valid = True
is_empty = False
nothing = None

# Import statements


# Lambda and comprehensions
def double(x):
    return x * 2


squares = [x**2 for x in range(5)]

# With statement
with open("file.txt") as f:
    content = f.read()

# Assert and raise
assert True, "This should pass"
# raise ValueError("Example error")
