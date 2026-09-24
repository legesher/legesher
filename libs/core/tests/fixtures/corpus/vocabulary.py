"""Every builtin and exception name the en pack maps, as plain expressions.

Generated from the en 3.13 pack keys (CORE-2128), one name per line, so
every pack's rendering of every builtin and exception goes through the
round trip, the NFC check and the invisible-character check, and on
CPython 3.10/3.11 the tokenizer-fragmentation pin. The other corpus files
use the names a real program would; this one exists so no rendering is
left unexercised.

``test_every_pack.py`` asserts the NAME tokens here cover every builtin
and exception key of the running version's en pack, so a new pack term
fails the suite until this file is regenerated.

Builtins are spelled as the pack keys spell them: the token translator
matches keys exactly, so ``ellipsis`` and ``notimplemented`` carry the
pack's lowercase spelling (``Ellipsis`` and ``NotImplemented`` are in no
pack). Exceptions are spelled with the canonical builtin name the engine
maps each lowercase key to (``legesher_core.utils.merge_exception_translations``).
"""

# builtins (73)
__import__
abs
aiter
all
anext
any
ascii
bin
bool
breakpoint
bytearray
bytes
callable
chr
classmethod
compile
complex
delattr
dict
dir
divmod
ellipsis
enumerate
eval
exec
filter
float
format
frozenset
getattr
globals
hasattr
hash
help
hex
id
input
int
isinstance
issubclass
iter
len
list
locals
map
max
memoryview
min
next
notimplemented
object
oct
open
ord
pow
print
property
range
repr
reversed
round
set
setattr
slice
sorted
staticmethod
str
sum
super
tuple
type
vars
zip

# exceptions (70)
ArithmeticError
AssertionError
AttributeError
BaseException
BaseExceptionGroup
BlockingIOError
BrokenPipeError
BufferError
BytesWarning
ChildProcessError
ConnectionAbortedError
ConnectionError
ConnectionRefusedError
ConnectionResetError
DeprecationWarning
EOFError
EncodingWarning
EnvironmentError
Exception
ExceptionGroup
FileExistsError
FileNotFoundError
FloatingPointError
FutureWarning
GeneratorExit
IOError
ImportError
ImportWarning
IndentationError
IndexError
InterruptedError
IsADirectoryError
KeyError
KeyboardInterrupt
LookupError
MemoryError
ModuleNotFoundError
NameError
NotADirectoryError
NotImplementedError
OSError
OverflowError
PendingDeprecationWarning
PermissionError
ProcessLookupError
PythonFinalizationError
RecursionError
ReferenceError
ResourceWarning
RuntimeError
RuntimeWarning
StopAsyncIteration
StopIteration
SyntaxError
SyntaxWarning
SystemError
SystemExit
TabError
TimeoutError
TypeError
UnboundLocalError
UnicodeDecodeError
UnicodeEncodeError
UnicodeError
UnicodeTranslateError
UnicodeWarning
UserWarning
ValueError
Warning
ZeroDivisionError
