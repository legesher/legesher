"""The type alias statement and PEP 695 type parameters (3.12+)."""

type Pair[T] = tuple[T, T]


def first[T](items: list[T]) -> T:
    return items[0]


class Box[T]:
    def __init__(self, item: T):
        self.item = item

    def get(self) -> T:
        return self.item
