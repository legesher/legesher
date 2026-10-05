"""Python's own spelling of the builtin names a language pack keys in lowercase.

Packs key their ``builtins`` and ``exceptions`` sections in lowercase
(``valueerror``, ``notimplemented``), but Python spells several of those names
with capitals (``ValueError``, ``NotImplemented``). Every reader that turns a
pack key back into a Python name needs the same lookup.
"""

import builtins

# Lowercase -> the name as Python spells it, for every name in `builtins`.
BUILTIN_CASE_MAP: dict[str, str] = {name.lower(): name for name in dir(builtins)}
