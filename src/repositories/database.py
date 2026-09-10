"""Database connection management and transaction handling.

This is the only module in the application that opens a raw sqlite3
connection. Every other repository goes through DatabaseConnection so
that connection setup (foreign keys, row factory) and transaction
behaviour (commit/rollback) are defined in exactly one place.
"""

import os
import sqlite3
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402
from utils.logger import get_logger  # noqa: E402

logger = get_logger("repositories.database")


class DatabaseConnection:
    """Wraps a single sqlite3 connection and exposes transaction helpers."""

    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._connection = sqlite3.connect(self.db_path)
        self._connection.row_factory = sqlite3.Row
        # Enforce FK constraints — SQLite ignores them by default.
        self._connection.execute("PRAGMA foreign_keys = ON;")
        logger.debug("Opened database connection at %s", self.db_path)

    # ------------------------------------------------------------------
    # Schema setup
    # ------------------------------------------------------------------
    def initialise_schema(self, schema_path: str = config.SCHEMA_PATH) -> None:
        """Create all tables if they don't already exist."""
        with open(schema_path, "r", encoding="utf-8") as f:
            script = f.read()
        try:
            self._connection.executescript(script)
            self._connection.commit()
            logger.info("Database schema initialised from %s", schema_path)
        except sqlite3.Error:
            logger.exception("Failed to initialise schema")
            raise

    # ------------------------------------------------------------------
    # Query execution
    # ------------------------------------------------------------------
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Run a single parameterised statement (no implicit commit)."""
        try:
            return self._connection.execute(query, params)
        except sqlite3.Error:
            logger.exception("Query failed: %s | params=%s", query, params)
            raise

    def fetch_one(self, query: str, params: tuple = ()):
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetch_all(self, query: str, params: tuple = ()):
        cursor = self.execute(query, params)
        return cursor.fetchall()

    # ------------------------------------------------------------------
    # Transaction control
    # ------------------------------------------------------------------
    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        self._connection.rollback()
        logger.warning("Transaction rolled back")

    def transaction(self):
        """Context manager: commits on success, rolls back on any exception.

        Usage:
            with db.transaction():
                db.execute("INSERT INTO ...", (...))
                db.execute("UPDATE ...", (...))
        """
        return _Transaction(self)

    def close(self) -> None:
        self._connection.close()
        logger.debug("Closed database connection")


class _Transaction:
    """Small context-manager helper backing DatabaseConnection.transaction()."""

    def __init__(self, db: DatabaseConnection):
        self._db = db

    def __enter__(self):
        return self._db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self._db.commit()
        else:
            self._db.rollback()
        return False  # never swallow the exception
