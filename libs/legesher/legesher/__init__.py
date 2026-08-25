"""Legesher — write and run Python in your own language.

Installing this package gives you the ``legesher`` command. It translates
Python between natural languages, keeping the code runnable: keywords and
builtins move deterministically through a reviewed language pack, and
identifiers, comments and strings move through a model when you ask for a
full translation.

Start here::

    legesher --help                              # every command
    legesher init                                # set up a project
    legesher translate app.py --to es            # translate a file
    legesher run app.py                          # run localized code

Most of the library surface lives in separate distributions: ``legesher_core``
(the translation engine), ``legesher_i18n`` (language packs), and
``legesher_runtime`` (exception hooks that render tracebacks in the language
pack's words).

This package is mainly the command-line front end over them. The one part of
it meant to be imported is :mod:`legesher.runtime`, which holds the import
hook that lets ``import mi_modulo`` load a localized source file, along with
the source mapper and traceback handler that ``legesher run`` installs::

    from legesher.runtime import install_import_hook
    install_import_hook("es")

Note the two are different things despite the similar names:
``legesher.runtime`` is the import machinery in this package, while
``legesher_runtime`` is a separate distribution that translates exception
type names and messages.
"""

__version__ = "0.23.0"
