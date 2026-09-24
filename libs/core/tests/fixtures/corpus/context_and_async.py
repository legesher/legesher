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
