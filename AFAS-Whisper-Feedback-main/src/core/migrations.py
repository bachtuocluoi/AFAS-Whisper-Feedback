"""
Lightweight schema migration runner.

Add new entries to MIGRATIONS (in order). Each migration runs exactly once —
tracked in the `schema_migrations` table. Safe to re-run on startup: applied
migrations are skipped, and errors listed in a migration's `safe_errors` are
silently recorded (handles fresh DBs where create_all already built the column,
or RENAME operations where the column is already in its target state).
"""

import logging
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Default errors that mean "already done" for ADD COLUMN statements.
_DEFAULT_SAFE = ["duplicate column", "already exists"]

MIGRATIONS = [
    {
        "id": "001_add_grammar_id_to_feedback",
        "sql": "ALTER TABLE feedback ADD COLUMN grammar_id INTEGER",
    },
    {
        "id": "002_add_grammar_score_to_scores",
        "sql": "ALTER TABLE scores ADD COLUMN grammar_score REAL",
    },
    {
        "id": "003_add_shap_values_to_scores",
        "sql": "ALTER TABLE scores ADD COLUMN shap_values TEXT",
    },
    # Add future migrations below, e.g.:
    # {
    #     "id": "004_add_foo_to_bar",
    #     "sql": "ALTER TABLE bar ADD COLUMN foo TEXT",
    # },
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

            safe_errors = migration.get("safe_errors", _DEFAULT_SAFE)
            try:
                conn.execute(text(migration["sql"]))
            except Exception as exc:
                err = str(exc).lower()
                if any(s in err for s in safe_errors):
                    logger.debug("Migration %s: already applied, recording.", mid)
                else:
                    raise

            conn.execute(
                text("INSERT OR IGNORE INTO schema_migrations (id) VALUES (:id)"),
                {"id": mid},
            )
            logger.info("Migration applied: %s", mid)
