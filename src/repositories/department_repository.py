"""Data-access layer for the `departments` table."""

import os
import sqlite3
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repositories.database import DatabaseConnection  # noqa: E402
from models.department import Department  # noqa: E402
from exceptions.custom_exceptions import (  # noqa: E402
    DuplicateRecordException, RecordNotFoundException, EMSException,
)
from utils.logger import get_logger  # noqa: E402

logger = get_logger("repositories.department")


class DepartmentRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    def create(self, name: str, manager_employee_id: int = None) -> Department:
        if self.find_by_name(name) is not None:
            raise DuplicateRecordException("Department", "name", name)
        with self._db.transaction() as db:
            cursor = db.execute(
                "INSERT INTO departments (name, manager_employee_id) VALUES (?, ?)",
                (name, manager_employee_id),
            )
            new_id = cursor.lastrowid
        logger.info("Created department %r", name)
        return self.find_by_id(new_id)

    def find_by_id(self, department_id: int) -> Department:
        row = self._db.fetch_one("SELECT * FROM departments WHERE id = ?", (department_id,))
        if row is None:
            raise RecordNotFoundException("Department", department_id)
        return self._to_model(row)

    def find_by_name(self, name: str) -> Department | None:
        row = self._db.fetch_one("SELECT * FROM departments WHERE name = ?", (name,))
        return self._to_model(row) if row else None

    def all(self) -> list[Department]:
        rows = self._db.fetch_all("SELECT * FROM departments ORDER BY name")
        return [self._to_model(r) for r in rows]

    def delete(self, department_id: int) -> None:
        self.find_by_id(department_id)  # raises RecordNotFoundException if missing
        try:
            with self._db.transaction() as db:
                db.execute("DELETE FROM departments WHERE id = ?", (department_id,))
            logger.info("Deleted department id=%s", department_id)
        except sqlite3.IntegrityError as e:
            raise EMSException(
                "Cannot delete this department — employees or positions are still "
                "assigned to it. Reassign or remove them first."
            ) from e

    def _to_model(self, row) -> Department:
        return Department(
            department_id=row["id"],
            name=row["name"],
            manager_employee_id=row["manager_employee_id"],
        )
