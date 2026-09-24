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
