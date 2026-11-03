"""Names spelled like builtins where they cannot be the builtin (CORE-2237).

An attribute, a keyword argument and a name after a dot are never the
builtin they are spelled like, so every pack leaves each one exactly as
written. Nothing in this file binds such a name itself, which is the
condition for that rule.
"""

import argparse
import os.path
import types


class Record:
    def __init__(self, size):
        self.id = size
        self.input = None
        self.type = "plain"
        self.range = range(size)


record = Record(3)
record.format = "{}-{}".format(record.id, record.type)
options = types.SimpleNamespace(id=1, type=str, input=None, len=2, open=False)
parser = argparse.ArgumentParser()
parser.add_argument("--count", type=int, default=0)
print(options.id, options.type.__name__, len(record.range), sep=",", end="\n")
print(os.path.join("a", "b"), record.format, getattr(record, "input"))
