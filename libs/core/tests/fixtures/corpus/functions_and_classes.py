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
