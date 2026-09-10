"""Attendance: a single day's clock-in/clock-out record for an employee."""

import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exceptions.custom_exceptions import ValidationException  # noqa: E402


class Attendance:
    STATUSES = {"present", "absent", "late"}

    def __init__(self, employee_id: int, date: str, attendance_id: int = None,
                 time_in: str = None, time_out: str = None, status: str = "present"):
        self.attendance_id = attendance_id
        self.employee_id = employee_id
        self.date = date
        self.time_in = time_in
        self.time_out = time_out
        self.status = status

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        if value not in self.STATUSES:
            raise ValidationException(f"Attendance status must be one of {sorted(self.STATUSES)}.")
        self._status = value

    @property
    def hours_worked(self):
        """Computed property: hours between time_in and time_out, or None
        if either is missing (e.g. still clocked in, or marked absent)."""
        if not self.time_in or not self.time_out:
            return None
        fmt = "%H:%M"
        try:
            t_in = datetime.strptime(self.time_in, fmt)
            t_out = datetime.strptime(self.time_out, fmt)
        except ValueError:
            return None
        delta = t_out - t_in
        return round(delta.total_seconds() / 3600, 2)

    def __eq__(self, other) -> bool:
        return isinstance(other, Attendance) and self.attendance_id == other.attendance_id

    def __repr__(self) -> str:
        return f"Attendance(id={self.attendance_id}, employee_id={self.employee_id}, date={self.date!r}, status={self.status!r})"
