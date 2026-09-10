"""Data-access layer for the `positions` table."""

import os
import sqlite3
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repositories.database import DatabaseConnection  # noqa: E402
from models.position import Position  # noqa: E402
from exceptions.custom_exceptions import RecordNotFoundException, EMSException  # noqa: E402
from utils.logger import get_logger  # noqa: E402

logger = get_logger("repositories.position")


class PositionRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    def create(self, title: str, department_id: int, base_salary_grade: float) -> Position:
        with self._db.transaction() as db:
            cursor = db.execute(
                "INSERT INTO positions (title, department_id, base_salary_grade) VALUES (?, ?, ?)",
                (title, department_id, base_salary_grade),
            )
            new_id = cursor.lastrowid
        logger.info("Created position %r in department id=%s", title, department_id)
        return self.find_by_id(new_id)

    def find_by_id(self, position_id: int) -> Position:
        row = self._db.fetch_one("SELECT * FROM positions WHERE id = ?", (position_id,))
        if row is None:
            raise RecordNotFoundException("Position", position_id)
        return self._to_model(row)

    def all(self) -> list[Position]:
        rows = self._db.fetch_all("SELECT * FROM positions ORDER BY title")
        return [self._to_model(r) for r in rows]

    def find_by_department(self, department_id: int) -> list[Position]:
        rows = self._db.fetch_all(
            "SELECT * FROM positions WHERE department_id = ? ORDER BY title", (department_id,)
        )
        return [self._to_model(r) for r in rows]

    def delete(self, position_id: int) -> None:
        self.find_by_id(position_id)
        try:
            with self._db.transaction() as db:
                db.execute("DELETE FROM positions WHERE id = ?", (position_id,))
            logger.info("Deleted position id=%s", position_id)
        except sqlite3.IntegrityError as e:
            raise EMSException(
                "Cannot delete this position — employees are still assigned to it."
            ) from e

    def _to_model(self, row) -> Position:
        return Position(
            position_id=row["id"],
            title=row["title"],
            department_id=row["department_id"],
            base_salary_grade=row["base_salary_grade"],
        )
