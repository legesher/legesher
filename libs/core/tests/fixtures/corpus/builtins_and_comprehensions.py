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
        print(f"{index}: {value!r}", end="\n")
    return str(len(values))
