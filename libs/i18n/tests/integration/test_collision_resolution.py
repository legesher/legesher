"""Integration tests for collision resolution (CORE-605).

Verifies the production database has zero collisions after the
one-time migration was applied. The migration script is not retained
in this repository; these tests assert the post-migration invariant.
"""

import pytest
from pathlib import Path

from legesher_i18n.db.database import TranslationDatabase


#: The database is an untracked working copy since CORE-1794 — a fresh clone
#: does not have it until it is copied in from the private data home (see
#: libs/i18n/CLAUDE.md, "Durable home & sync ritual").
requires_real_db = pytest.mark.skipif(
    not (
        Path(__file__).resolve().parents[2] / "legesher_i18n" / "db" / "translations.db"
    ).exists(),
    reason=(
        "translations.db is an untracked working copy (CORE-1794); copy it in "
        "from the private data home — libs/i18n/CLAUDE.md, 'Durable home & "
        "sync ritual'"
    ),
)


@requires_real_db
@pytest.mark.integration
class TestCollisionResolution:
    """Integration tests against the real database."""

    def test_real_db_zero_collisions(self):
        """Verify the production translations.db has zero collisions."""
        db = TranslationDatabase()
        try:
            collisions = db.find_collisions()
            if collisions:
                details = [
                    f"  [{c['language_code']}] '{c['translation']}' "
                    f"-> {', '.join(t['term_name'] for t in c['terms'])}"
                    for c in collisions
                ]
                pytest.fail(
                    f"Found {len(collisions)} collision groups in production DB:\n"
                    + "\n".join(details)
                )
        finally:
            db.close()
