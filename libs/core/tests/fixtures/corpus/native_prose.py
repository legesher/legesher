"""Prose in other scripts beside code.

The strings and comments carry the Arabic and fullwidth marks that code
position reads as ASCII; the code itself is written with ASCII marks.
"""


def greet(first, second):
    pair = [first, second]; total = len(pair)
    return "مَرْحَبًا، يَا عَالَم؛", total  # تَعْلِيق، هُنَا؛


def label(first, second):
    pair = (first, second); total = len(pair)
    if total:
        return "你好，世界：（一）"  # 注释，这里：（二）
    return "שָׁלוֹם, עוֹלָם"  # הֶעָרָה: כָּאן
