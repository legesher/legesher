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
