"""Data-access layer for the `leave_requests` table."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repositories.database import DatabaseConnection  # noqa: E402
from models.leave_request import LeaveRequest  # noqa: E402
from exceptions.custom_exceptions import RecordNotFoundException  # noqa: E402
from utils.logger import get_logger  # noqa: E402
from utils.dates import period_bounds  # noqa: E402

logger = get_logger("repositories.leave")


class LeaveRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    def create(self, leave: LeaveRequest) -> LeaveRequest:
        with self._db.transaction() as db:
            cursor = db.execute(
                "INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, "
                "status, approved_by) VALUES (?, ?, ?, ?, ?, ?)",
                (leave.employee_id, leave.leave_type, leave.start_date, leave.end_date,
                 leave.status, leave.approved_by),
            )
            new_id = cursor.lastrowid
        logger.info("Created leave request #%s for employee #%s", new_id, leave.employee_id)
        return self.find_by_id(new_id)

    def find_by_id(self, leave_id: int) -> LeaveRequest:
        row = self._db.fetch_one("SELECT * FROM leave_requests WHERE id = ?", (leave_id,))
        if row is None:
            raise RecordNotFoundException("LeaveRequest", leave_id)
        return self._to_model(row)

    def find_by_employee(self, employee_id: int) -> list[LeaveRequest]:
        rows = self._db.fetch_all(
            "SELECT * FROM leave_requests WHERE employee_id = ? ORDER BY start_date DESC",
            (employee_id,),
        )
        return [self._to_model(r) for r in rows]

    def find_by_status(self, status: str) -> list[LeaveRequest]:
        rows = self._db.fetch_all(
            "SELECT * FROM leave_requests WHERE status = ? ORDER BY start_date", (status,)
        )
        return [self._to_model(r) for r in rows]

    def find_approved_unpaid_overlapping_period(self, employee_id: int, period: str) -> list[LeaveRequest]:
        """Approved, unpaid leave requests overlapping a 'YYYY-MM' period —
        the exact lookup Payroll needs to compute a leave deduction.

        Uses a true interval-overlap test (start <= period_end AND
        end >= period_start) rather than checking whether either endpoint
        falls inside the period — the earlier LIKE-based version missed
        any leave that spans an entire period in the middle of a longer
        date range (e.g. leave from July 25 to September 5 has neither
        endpoint in August, but still covers all of it)."""
        period_start, period_end = period_bounds(period)
        rows = self._db.fetch_all(
            "SELECT * FROM leave_requests WHERE employee_id = ? AND status = 'approved' "
            "AND leave_type = 'unpaid' AND start_date <= ? AND end_date >= ?",
            (employee_id, period_end, period_start),
        )
        return [self._to_model(r) for r in rows]

    def all(self) -> list[LeaveRequest]:
        rows = self._db.fetch_all("SELECT * FROM leave_requests ORDER BY start_date DESC")
        return [self._to_model(r) for r in rows]

    def update(self, leave: LeaveRequest) -> LeaveRequest:
        self.find_by_id(leave.leave_id)
        with self._db.transaction() as db:
            db.execute(
                "UPDATE leave_requests SET employee_id=?, leave_type=?, start_date=?, "
                "end_date=?, status=?, approved_by=? WHERE id=?",
                (leave.employee_id, leave.leave_type, leave.start_date, leave.end_date,
                 leave.status, leave.approved_by, leave.leave_id),
            )
        logger.info("Updated leave request #%s (status=%s)", leave.leave_id, leave.status)
        return self.find_by_id(leave.leave_id)

    def _to_model(self, row) -> LeaveRequest:
        return LeaveRequest(
            leave_id=row["id"],
            employee_id=row["employee_id"],
            leave_type=row["leave_type"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            status=row["status"],
            approved_by=row["approved_by"],
        )
