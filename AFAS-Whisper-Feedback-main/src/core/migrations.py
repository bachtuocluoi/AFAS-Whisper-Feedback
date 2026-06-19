"""
Lightweight schema migration runner.

Add new entries to MIGRATIONS (in order). Each migration runs exactly once —
tracked in the `schema_migrations` table. Safe to re-run on startup: applied
migrations are skipped, and ADD COLUMN statements that already exist are
silently marked as applied (handles fresh DBs where create_all already built
the column).
"""

import logging
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

MIGRATIONS = [
    {
        "id": "001_add_grammar_id_to_feedback",
        "sql": "ALTER TABLE feedback ADD COLUMN grammar_id INTEGER",
    },
    {
        "id": "002_add_grammar_score_to_scores",
        "sql": "ALTER TABLE scores ADD COLUMN grammar_score REAL",
    },
]


def run_migrations(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(id TEXT PRIMARY KEY, applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        ))

        for migration in MIGRATIONS:
            mid = migration["id"]

            already = conn.execute(
                text("SELECT 1 FROM schema_migrations WHERE id = :id"), {"id": mid}
            ).fetchone()
            if already:
                continue

            try:
                conn.execute(text(migration["sql"]))
            except Exception as exc:
                err = str(exc).lower()
                # Fresh DB: create_all already added the column — just record it.
                if "duplicate column" in err or "already exists" in err:
                    logger.debug("Migration %s: already applied outside runner, recording.", mid)
                else:
                    raise

            conn.execute(
                text("INSERT OR IGNORE INTO schema_migrations (id) VALUES (:id)"),
                {"id": mid},
            )
            logger.info("Migration applied: %s", mid)
