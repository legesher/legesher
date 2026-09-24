"""Real Python sources for the round-trip property sweep (CORE-1745).

The corpus is one set of files, shared with the engine's own per-commit
sweep (CORE-2128): ``libs/core/tests/fixtures/corpus/`` holds one file
per construct group and a ``manifest.json`` that is the single home of
each file's metadata. This module reads that directory, so the MCP sweep
and the engine sweep can never drift apart on what "the corpus" is.
Between them the files name every keyword, builtin and exception key of
the en pack (``vocabulary.py`` is generated from those keys, and the
engine sweep asserts the coverage) and the version-gated grammar:
``except*`` at 3.11, the ``type`` statement and PEP 695 type parameters
at 3.12.

Each entry declares the lowest Python grammar it parses under, so the
sweep can skip a file on a pack version that predates its syntax.

The MCP suite runs from a monorepo checkout (its conftest is not shipped
either), so a missing corpus directory is an error, not an empty sweep.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CorpusFile:
    """One source in the corpus, with the grammar it needs."""

    name: str
    source: str
    #: Lowest ``X.Y`` this parses under.
    min_version: str = "3.10"


#: Where the shared corpus lives, relative to the monorepo root.
_CORPUS_RELATIVE = Path("libs") / "core" / "tests" / "fixtures" / "corpus"

#: Engine fixtures from the monorepo, next to the corpus directory. A real
#: file nobody wrote for this test is the point; it rides along with the
#: default grammar. Keyed by basename, the same key the engine sweep uses,
#: so a ledger row is copy-pasteable between the two sweeps.
_MONOREPO_FIXTURES = ("sample_english.py",)


def _monorepo_root() -> Path | None:
    """Walk up to the checkout root, or None when running from a wheel."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "libs" / "core").is_dir() and (parent / "pyproject.toml").is_file():
            return parent
    return None


def _parts(version: str) -> tuple[int, ...]:
    return tuple(int(piece) for piece in version.split("."))


def load_corpus() -> tuple[CorpusFile, ...]:
    """Every manifest entry, read from the shared directory, in manifest order."""
    root = _monorepo_root()
    if root is None:
        raise RuntimeError(
            "the round-trip corpus lives in the monorepo checkout at "
            f"{_CORPUS_RELATIVE}; the MCP sweep cannot run outside one"
        )
    corpus_dir = root / _CORPUS_RELATIVE
    manifest = json.loads((corpus_dir / "manifest.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not manifest:
        raise ValueError(f"{corpus_dir / 'manifest.json'}: expected a non-empty object")
    return tuple(
        CorpusFile(name, (corpus_dir / name).read_text(encoding="utf-8"), min_version)
        for name, min_version in manifest.items()
    )


#: The corpus, smallest construct set first.
CORPUS: tuple[CorpusFile, ...] = load_corpus()


def in_repo_fixtures() -> tuple[CorpusFile, ...]:
    """Real engine test fixtures, when the monorepo checkout is available."""
    root = _monorepo_root()
    if root is None:
        return ()
    fixtures = root / _CORPUS_RELATIVE.parent
    return tuple(
        CorpusFile(name, (fixtures / name).read_text(encoding="utf-8"))
        for name in _MONOREPO_FIXTURES
        if (fixtures / name).is_file()
    )


def corpus_for(python_version: str) -> tuple[CorpusFile, ...]:
    """Corpus entries whose grammar the given pack version can express."""
    target = _parts(python_version)
    return tuple(
        entry for entry in CORPUS + in_repo_fixtures() if _parts(entry.min_version) <= target
    )
