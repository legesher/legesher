"""Integration tests for collision resolution (CORE-605).

Verifies the production database has zero collisions after the
one-time migration was applied. The migration script itself is
archived in private-working-memory (scripts/resolve_collisions_core605.py).
"""

import pytest

from legesher_i18n.db.database import TranslationDatabase


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
