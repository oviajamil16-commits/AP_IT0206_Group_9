"""Data-access layer for the `users` table."""

import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repositories.database import DatabaseConnection  # noqa: E402
from models.user import build_user, User  # noqa: E402
from exceptions.custom_exceptions import DuplicateRecordException, RecordNotFoundException  # noqa: E402
from utils.logger import get_logger  # noqa: E402

logger = get_logger("repositories.user")


class UserRepository:
    """Object-oriented data access for User accounts. No raw SQL leaves this class."""

    def __init__(self, db: DatabaseConnection):
        self._db = db

    def find_by_username(self, username: str) -> User | None:
        row = self._db.fetch_one(
            "SELECT id, username, password_hash, role, employee_id, created_at "
            "FROM users WHERE username = ?",
            (username,),
        )
        return build_user(row) if row else None

    def find_by_id(self, user_id: int) -> User:
        row = self._db.fetch_one(
            "SELECT id, username, password_hash, role, employee_id, created_at "
            "FROM users WHERE id = ?",
            (user_id,),
        )
        if row is None:
            raise RecordNotFoundException("User", user_id)
        return build_user(row)

    def all(self) -> list[User]:
        rows = self._db.fetch_all(
            "SELECT id, username, password_hash, role, employee_id, created_at "
            "FROM users ORDER BY username"
        )
        return [build_user(r) for r in rows]

    def create(self, username: str, password_hash: str, role: str,
               employee_id: int = None) -> User:
        if self.find_by_username(username) is not None:
            raise DuplicateRecordException("User", "username", username)

        created_at = datetime.now().isoformat(timespec="seconds")
        with self._db.transaction() as db:
            cursor = db.execute(
                "INSERT INTO users (username, password_hash, role, employee_id, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (username, password_hash, role, employee_id, created_at),
            )
            new_id = cursor.lastrowid
        logger.info("Created user %r with role %s", username, role)
        return self.find_by_id(new_id)

    def count(self) -> int:
        row = self._db.fetch_one("SELECT COUNT(*) AS n FROM users")
        return row["n"]
