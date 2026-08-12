"""Real Python sources for the round-trip property sweep (CORE-1745).

Held as strings rather than files so the corpus travels with the test suite
and no lint/type run treats it as project code. Between them these cover
the construct space a pack actually has to map: every keyword class,
builtins, exceptions, and the version-gated grammar.

Each entry declares the lowest Python grammar it parses under, so the sweep
can skip a file on a pack version that predates its syntax.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CorpusFile:
    """One source in the corpus, with the grammar it needs."""

    name: str
    source: str
    #: Lowest ``X.Y`` this parses under.
    min_version: str = "3.10"


CONTROL_FLOW = '''\
"""Branching, loops, and the operators that spell them."""


def classify(value):
    if value is None:
        return "none"
    elif value is True or value is False:
        return "bool"
    elif not isinstance(value, int) and value in (1, 2):
        return "member"
    else:
        return "other"


def walk(items):
    total = 0
    for index, item in enumerate(items):
        if item is None:
            continue
        while total < 100:
            total += index
            break
        else:
            pass
    return total
'''

FUNCTIONS_AND_CLASSES = '''\
"""Definitions, decorators, inheritance, and scoping keywords."""

COUNTER = 0


def memoize(function):
    cache = {}

    def wrapper(*args, **kwargs):
        global COUNTER
        COUNTER += 1
        key = str(args) + str(sorted(kwargs.items()))
        if key not in cache:
            cache[key] = function(*args, **kwargs)
        return cache[key]

    return wrapper


class Shape:
    """A base class with a class attribute and a property."""

    sides = 0

    def __init__(self, name: str) -> None:
        self.name = name

    @property
    def label(self) -> str:
        return f"{self.name}({self.sides})"

    @staticmethod
    def describe() -> str:
        return "a shape"


class Square(Shape):
    sides = 4

    def scale(self, factor):
        def inner(value):
            nonlocal factor
            factor = factor * 2
            return value * factor

        return inner


@memoize
def area(side):
    return side * side
'''

EXCEPTIONS = '''\
"""Every exception keyword plus the builtin exception names."""


def parse_number(raw):
    try:
        return int(raw)
    except ValueError:
        raise TypeError("not a number") from None
    except (KeyError, IndexError) as exc:
        print(exc)
        return None
    else:
        return 0
    finally:
        pass


def guard(value):
    assert value is not None, "value required"
    if not isinstance(value, (int, float)):
        raise ValueError("bad value")
    try:
        result = 1 / value
    except ZeroDivisionError:
        result = float("inf")
    except ArithmeticError:
        raise
    return result


def lookup(mapping, key):
    try:
        return mapping[key]
    except KeyError:
        raise LookupError(key)
    except AttributeError:
        raise RuntimeError("not a mapping")
'''

BUILTINS_AND_COMPREHENSIONS = '''\
"""Builtins, comprehensions, lambdas, and the walrus operator."""

NAMES = ["ada", "grace", "katherine"]

lengths = [len(name) for name in NAMES if name]
by_length = {name: len(name) for name in NAMES}
unique = {len(name) for name in NAMES}
pairs = list(zip(NAMES, map(str.upper, NAMES)))

longest = max(NAMES, key=lambda name: len(name))
shortest = min(NAMES, key=len)
joined = ", ".join(sorted(NAMES, reverse=True))
counted = sum(1 for name in NAMES if name.startswith("a"))
flags = [bool(name) for name in NAMES]
numbers = list(range(10))
as_tuple = tuple(numbers)
as_dict = dict(enumerate(NAMES))


def summarize(values):
    if (total := sum(values)) > 10:
        return round(float(total), 2)
    return abs(int(total))


def show(values):
    for index, value in enumerate(values):
        print(f"{index}: {value!r}", end="\\n")
    return str(len(values))
'''

CONTEXT_AND_ASYNC = '''\
"""Context managers, generators, and the async keywords."""

import contextlib


def counter(limit):
    current = 0
    while current < limit:
        received = yield current
        if received is not None:
            current = received
        else:
            current += 1


def chained(values):
    yield from values


@contextlib.contextmanager
def opened(resource):
    try:
        yield resource
    finally:
        del resource


async def fetch(source):
    async with source as handle:
        async for chunk in handle:
            await handle.flush()
            if chunk is None:
                break
    return True


async def gather(sources):
    results = [await fetch(source) for source in sources]
    return results


def use(path):
    with open(path) as handle, contextlib.suppress(OSError):
        data = handle.read()
    return data


def cleanup(mapping):
    with contextlib.suppress(KeyError):
        del mapping["stale"]
'''

PATTERN_MATCHING = '''\
"""Structural pattern matching (3.10+)."""


def route(command):
    match command:
        case {"action": "go", "direction": direction}:
            return direction
        case ["move", x, y]:
            return (x, y)
        case str() as text if text:
            return text
        case [first, *rest]:
            return first, rest
        case None:
            return None
        case _:
            return "unknown"


def describe(point):
    match point:
        case (0, 0):
            return "origin"
        case (x, 0) | (0, x):
            return f"axis at {x}"
        case _:
            return "elsewhere"
'''

EXCEPTION_GROUPS = '''\
"""Exception groups and except* (3.11+)."""


def run(tasks):
    try:
        raise ExceptionGroup("failures", [ValueError("a"), TypeError("b")])
    except* ValueError as group:
        print(group)
    except* TypeError:
        pass
    finally:
        del tasks
    return True
'''

#: The corpus, smallest construct set first.
CORPUS: tuple[CorpusFile, ...] = (
    CorpusFile("control_flow.py", CONTROL_FLOW),
    CorpusFile("functions_and_classes.py", FUNCTIONS_AND_CLASSES),
    CorpusFile("exceptions.py", EXCEPTIONS),
    CorpusFile("builtins_and_comprehensions.py", BUILTINS_AND_COMPREHENSIONS),
    CorpusFile("context_and_async.py", CONTEXT_AND_ASYNC),
    CorpusFile("pattern_matching.py", PATTERN_MATCHING, min_version="3.10"),
    CorpusFile("exception_groups.py", EXCEPTION_GROUPS, min_version="3.11"),
)

#: Engine fixtures from the monorepo, when the sweep runs inside a checkout.
#: A real file nobody wrote for this test is the point; absent from a wheel
#: install, so it is additive rather than required.
_MONOREPO_FIXTURES = ("libs/core/tests/fixtures/sample_english.py",)


def _monorepo_root() -> Path | None:
    """Walk up to the checkout root, or None when running from a wheel."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "libs" / "core").is_dir() and (parent / "pyproject.toml").is_file():
            return parent
    return None


def in_repo_fixtures() -> tuple[CorpusFile, ...]:
    """Real engine test fixtures, when the monorepo checkout is available."""
    root = _monorepo_root()
    if root is None:
        return ()
    found = []
    for relative in _MONOREPO_FIXTURES:
        path = root / relative
        if path.is_file():
            found.append(CorpusFile(relative, path.read_text(encoding="utf-8")))
    return tuple(found)


def corpus_for(python_version: str) -> tuple[CorpusFile, ...]:
    """Corpus entries whose grammar the given pack version can express."""

    def parts(version: str) -> tuple[int, ...]:
        return tuple(int(piece) for piece in version.split("."))

    target = parts(python_version)
    return tuple(
        entry for entry in CORPUS + in_repo_fixtures() if parts(entry.min_version) <= target
    )
