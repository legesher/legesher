"""Semicolons, one-line bodies, and the marks that group and separate."""


def tally(items):
    item_count = 0; running_total = 0
    for item in items:
        item_count += 1; running_total += item
    if item_count: return running_total / item_count
    return 0


def window(items, low_mark, high_mark):
    inner_part = items[low_mark:high_mark]; every_other = items[::2]
    by_mark = {low_mark: inner_part, high_mark: every_other}
    return (
        inner_part,
        every_other,
        by_mark,
    )


def describe(items):
    if (item_count := len(items)) > 3: return item_count
    pair_up = lambda left_side, right_side: (left_side, right_side)
    return pair_up(item_count, items)
