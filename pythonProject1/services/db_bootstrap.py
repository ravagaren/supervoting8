"""Bootstrap helpers for the application runtime."""
from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "user_profiles.sqlite3"


def _connect(db_path: str | os.PathLike[str]) -> sqlite3.Connection:
    """Create a SQLite connection and set row_factory."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def bootstrap_user_profiles_db(db_path: str | os.PathLike[str] | None = None) -> str:
    """Create/prepare the SQLite database for user profiles.

    This runs at app startup and ensures the data directory and schema exist.
    """
    target = str(db_path or os.getenv("USER_PROFILES_DB_PATH", DEFAULT_DB_PATH))
    target_path = Path(target)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Initializing user profiles SQLite database at %s", target_path)

    with _connect(target_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                migration_name TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()

        migration_dir = BASE_DIR / "migrations"
        migration_dir.mkdir(exist_ok=True)

        for migration_file in sorted(migration_dir.glob("*.sql")):
            migration_name = migration_file.name
            already_applied = conn.execute(
                "SELECT 1 FROM schema_migrations WHERE migration_name = ?",
                (migration_name,),
            ).fetchone()

            if already_applied:
                continue

            logger.info("Applying migration %s", migration_name)
            conn.executescript(migration_file.read_text(encoding="utf-8"))
            conn.execute(
                "INSERT INTO schema_migrations (migration_name) VALUES (?)",
                (migration_name,),
            )
            conn.commit()

    logger.info("User profiles SQLite database ready at %s", target_path)
    return str(target_path)


def bootstrap_application_data() -> None:
    """Prepare persistent application stores before the bot starts polling."""
    bootstrap_user_profiles_db()
