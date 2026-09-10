"""Data-access layer for the `attendance` table."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repositories.database import DatabaseConnection  # noqa: E402
from models.attendance import Attendance  # noqa: E402
from exceptions.custom_exceptions import RecordNotFoundException  # noqa: E402
from utils.logger import get_logger  # noqa: E402

logger = get_logger("repositories.attendance")


class AttendanceRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    def create(self, attendance: Attendance) -> Attendance:
        with self._db.transaction() as db:
            cursor = db.execute(
                "INSERT INTO attendance (employee_id, date, time_in, time_out, status) "
                "VALUES (?, ?, ?, ?, ?)",
                (attendance.employee_id, attendance.date, attendance.time_in,
                 attendance.time_out, attendance.status),
            )
            new_id = cursor.lastrowid
        logger.info("Recorded attendance #%s for employee #%s on %s",
                    new_id, attendance.employee_id, attendance.date)
        return self.find_by_id(new_id)

    def find_by_id(self, attendance_id: int) -> Attendance:
        row = self._db.fetch_one("SELECT * FROM attendance WHERE id = ?", (attendance_id,))
        if row is None:
            raise RecordNotFoundException("Attendance", attendance_id)
        return self._to_model(row)

    def find_by_employee(self, employee_id: int) -> list[Attendance]:
        rows = self._db.fetch_all(
            "SELECT * FROM attendance WHERE employee_id = ? ORDER BY date DESC", (employee_id,)
        )
        return [self._to_model(r) for r in rows]

    def find_by_date(self, date: str) -> list[Attendance]:
        rows = self._db.fetch_all(
            "SELECT * FROM attendance WHERE date = ? ORDER BY employee_id", (date,)
        )
        return [self._to_model(r) for r in rows]

    def find_open_for_employee_on(self, employee_id: int, date: str) -> Attendance | None:
        """The clocked-in-but-not-out record for an employee on a given day, if any."""
        row = self._db.fetch_one(
            "SELECT * FROM attendance WHERE employee_id = ? AND date = ? AND time_out IS NULL",
            (employee_id, date),
        )
        return self._to_model(row) if row else None

    def all(self) -> list[Attendance]:
        rows = self._db.fetch_all("SELECT * FROM attendance ORDER BY date DESC, employee_id")
        return [self._to_model(r) for r in rows]

    def update(self, attendance: Attendance) -> Attendance:
        self.find_by_id(attendance.attendance_id)
        with self._db.transaction() as db:
            db.execute(
                "UPDATE attendance SET employee_id=?, date=?, time_in=?, time_out=?, status=? "
                "WHERE id=?",
                (attendance.employee_id, attendance.date, attendance.time_in,
                 attendance.time_out, attendance.status, attendance.attendance_id),
            )
        logger.info("Updated attendance #%s", attendance.attendance_id)
        return self.find_by_id(attendance.attendance_id)

    def delete(self, attendance_id: int) -> None:
        self.find_by_id(attendance_id)
        with self._db.transaction() as db:
            db.execute("DELETE FROM attendance WHERE id = ?", (attendance_id,))
        logger.info("Deleted attendance #%s", attendance_id)

    def _to_model(self, row) -> Attendance:
        return Attendance(
            attendance_id=row["id"],
            employee_id=row["employee_id"],
            date=row["date"],
            time_in=row["time_in"],
            time_out=row["time_out"],
            status=row["status"],
        )
