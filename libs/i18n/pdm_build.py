"""PDM build hook to bundle language packs into the legesher-i18n wheel.

This hook copies the language-packs/ YAML files into legesher_i18n/bundled_packs/
before the wheel is built, so they are included in the installed package.
The copy is cleaned up after the build completes.
"""

import shutil
from pathlib import Path


_BUNDLED_DIR = Path(__file__).parent / "legesher_i18n" / "bundled_packs"
_SOURCE_DIR = Path(__file__).parent / "language-packs"


def pdm_build_initialize(context):
    """Copy language-packs into legesher_i18n/bundled_packs/ before build."""
    if _SOURCE_DIR.exists() and not _BUNDLED_DIR.exists():
        shutil.copytree(
            _SOURCE_DIR,
            _BUNDLED_DIR,
            ignore=shutil.ignore_patterns(
                "__pycache__",
                "*.pyc",
                "*.egg-info",
                "CHANGELOG.md",
                "README.md",
            ),
        )


def pdm_build_finalize(context, artifact):
    """Clean up the copied bundled_packs directory after build."""
    if _BUNDLED_DIR.exists() and _BUNDLED_DIR.is_dir():
        shutil.rmtree(_BUNDLED_DIR)
