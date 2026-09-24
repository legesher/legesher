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
