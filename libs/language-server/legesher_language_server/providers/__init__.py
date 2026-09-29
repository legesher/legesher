"""LSP feature providers for Legesher Language Server.

Each module answers one LSP request against the user's language pack:

- ``hover``: hover tooltips with translated keyword and builtin documentation
- ``completion``: completion items for localized keywords, Python's builtins
  under their English names, and symbols declared in the current file
- ``diagnostic``: parse-time errors (SyntaxError and its kin) rendered from
  translated message templates
- ``semantic_tokens``: token classification so translated keywords highlight
  like their English counterparts

Each provider answers in the language of the document it is asked about, which
the client names per document; a document it has not named is read in the
configured file language (CORE-1976). In ``hover`` and ``semantic_tokens``,
which word a keyword or builtin maps to comes from that language's pack, so
that part follows all shipped packs;
``completion`` reads the pack for keywords only and offers builtins under
their English names. The prose attached to a word — the documentation
``hover`` shows and the message text ``diagnostic`` renders — is written out
in this package and currently covers English, Spanish, and Arabic only; other
languages get the localized word without the explanation.

The server calls these directly; they are the baseline that works with no
external tooling installed. When an external type-aware server is configured,
``enhanced_intelligence`` enriches the hover and diagnostic answers on top.
"""

from .completion import provide_completion
from .diagnostic import provide_diagnostics
from .hover import provide_hover
from .semantic_tokens import provide_semantic_tokens

__all__ = [
    "provide_hover",
    "provide_completion",
    "provide_diagnostics",
    "provide_semantic_tokens",
]
