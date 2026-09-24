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
