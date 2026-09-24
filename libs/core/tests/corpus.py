"""The round-trip corpus: real Python sources covering the construct space.

One corpus, two consumers (CORE-2128). The files live under
``tests/fixtures/corpus/``, next to the engine they exercise. The MCP
suite (``libs/mcp/tests/corpus.py``) reads the same directory through the
same manifest, so the engine sweep and the MCP sweep can never disagree
about what "the corpus" is. Between them the files name every keyword,
builtin and exception key of the en pack (``vocabulary.py`` is generated
from those keys, and ``test_every_pack.py`` asserts the coverage) and the
version-gated grammar: ``except*`` at 3.11, the ``type`` statement and
PEP 695 type parameters at 3.12.

``manifest.json`` is the one place a file's metadata lives: the lowest
Python grammar it parses under (so a sweep can skip it on a pack version
that predates its syntax) and the order entries are yielded in, smallest
construct set first. A ``.py`` in the directory but absent from the
manifest is a test failure (``test_every_pack.py``), never a silent
omission.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

#: Where the construct files and their manifest live.
CORPUS_DIR: Path = Path(__file__).resolve().parent / "fixtures" / "corpus"
MANIFEST: Path = CORPUS_DIR / "manifest.json"


@dataclass(frozen=True)
class CorpusFile:
    """One source in the corpus, with the grammar it needs."""

    name: str
    source: str
    #: Lowest ``X.Y`` this parses under.
    min_version: str = "3.10"


def _parts(version: str) -> tuple[int, ...]:
    return tuple(int(piece) for piece in version.split("."))


def load_manifest() -> dict[str, str]:
    """``{file name: min_version}`` in manifest order, validated."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not manifest:
        raise ValueError(f"{MANIFEST}: expected a non-empty object")
    for name, min_version in manifest.items():
        if not name.endswith(".py"):
            raise ValueError(f"{MANIFEST}: {name!r} is not a .py file")
        # A malformed version must fail here, not inside a comparison.
        _parts(min_version)
    return manifest


def load_corpus() -> tuple[CorpusFile, ...]:
    """Every manifest entry, read from disk, in manifest order."""
    return tuple(
        CorpusFile(
            name,
            (CORPUS_DIR / name).read_text(encoding="utf-8"),
            min_version,
        )
        for name, min_version in load_manifest().items()
    )


#: The corpus, smallest construct set first.
CORPUS: tuple[CorpusFile, ...] = load_corpus()

#: Engine fixtures that predate the corpus. A real file nobody wrote for
#: this sweep is the point, so they ride along with the default grammar.
_SIBLING_FIXTURES = ("sample_english.py",)


def in_repo_fixtures() -> tuple[CorpusFile, ...]:
    """The pre-existing engine fixtures, additive to the corpus."""
    fixtures = CORPUS_DIR.parent
    return tuple(
        CorpusFile(name, (fixtures / name).read_text(encoding="utf-8"))
        for name in _SIBLING_FIXTURES
        if (fixtures / name).is_file()
    )


def corpus_for(python_version: str) -> tuple[CorpusFile, ...]:
    """Corpus entries whose grammar the given version can express."""
    target = _parts(python_version)
    return tuple(
        entry
        for entry in CORPUS + in_repo_fixtures()
        if _parts(entry.min_version) <= target
    )
