"""Controller layer for Attendance: clock in/out, mark absent, and queries."""

import os
import sys
from datetime import datetime, date as date_cls

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from controllers.auth_controller import AuthController  # noqa: E402
from repositories.attendance_repository import AttendanceRepository  # noqa: E402
from repositories.employee_repository import EmployeeRepository  # noqa: E402
from models.attendance import Attendance  # noqa: E402
from utils.validators import Validator  # noqa: E402
from exceptions.custom_exceptions import ValidationException  # noqa: E402


class AttendanceController:
    def __init__(self, auth_controller: AuthController, attendance_repo: AttendanceRepository,
                 employee_repo: EmployeeRepository):
        self._auth = auth_controller
        self._attendance = attendance_repo
        self._employees = employee_repo

    def clock_in(self, employee_id: int, date: str = None, time_in: str = None) -> Attendance:
        self._auth.require_permission("attendance.create")
        self._employees.find_by_id(employee_id)  # validates the FK exists

        date = date or date_cls.today().isoformat()
        time_in = time_in or datetime.now().strftime("%H:%M")
        Validator.valid_date(date, "Date")

        if self._attendance.find_open_for_employee_on(employee_id, date) is not None:
            raise ValidationException("This employee is already clocked in for this date.")

        record = Attendance(employee_id=employee_id, date=date, time_in=time_in, status="present")
        return self._attendance.create(record)

    def clock_out(self, employee_id: int, date: str = None, time_out: str = None) -> Attendance:
        self._auth.require_permission("attendance.create")
        date = date or date_cls.today().isoformat()
        time_out = time_out or datetime.now().strftime("%H:%M")

        open_record = self._attendance.find_open_for_employee_on(employee_id, date)
        if open_record is None:
            raise ValidationException("No open clock-in found for this employee on this date.")

        self._validate_time_order(open_record.time_in, time_out)
        open_record.time_out = time_out
        return self._attendance.update(open_record)

    @staticmethod
    def _validate_time_order(time_in: str, time_out: str) -> None:
        """Guards against negative hours_worked (e.g. clocking out at 09:00
        after clocking in at 17:00) — found via manual testing; the model's
        hours_worked property does the subtraction with no bounds check,
        so bad data must be rejected before it's ever saved."""
        fmt = "%H:%M"
        try:
            t_in = datetime.strptime(time_in, fmt)
            t_out = datetime.strptime(time_out, fmt)
        except ValueError:
            raise ValidationException("Time must be in HH:MM format.")
        if t_out <= t_in:
            raise ValidationException(
                f"Clock-out time ({time_out}) must be after clock-in time ({time_in})."
            )

    def mark_absent(self, employee_id: int, date: str) -> Attendance:
        self._auth.require_permission("attendance.create")
        self._employees.find_by_id(employee_id)
        date = Validator.valid_date(date, "Date")
        record = Attendance(employee_id=employee_id, date=date, status="absent")
        return self._attendance.create(record)

    def get_by_employee(self, employee_id: int) -> list[Attendance]:
        self._auth.require_permission("attendance.read")
        return self._attendance.find_by_employee(employee_id)

    def get_by_date(self, date: str) -> list[Attendance]:
        self._auth.require_permission("attendance.read")
        return self._attendance.find_by_date(date)

    def list_all(self) -> list[Attendance]:
        self._auth.require_permission("attendance.read")
        return self._attendance.all()

    def get_by_id(self, attendance_id: int) -> Attendance:
        self._auth.require_permission("attendance.read")
        return self._attendance.find_by_id(attendance_id)

    def edit_attendance(self, attendance_id: int, date: str = None, time_in: str = None,
                         time_out: str = None, status: str = None,
                         clear_time_out: bool = False) -> Attendance:
        """Edit an existing record's fields. Any argument left as None keeps
        the current value. clear_time_out=True removes time_out entirely
        (e.g. correcting a record that should never have had one)."""
        self._auth.require_permission("attendance.update")
        record = self._attendance.find_by_id(attendance_id)

        if date:
            record.date = Validator.valid_date(date, "Date")
        if time_in:
            record.time_in = time_in
        if clear_time_out:
            record.time_out = None
        elif time_out:
            record.time_out = time_out
        if status:
            record.status = status  # Attendance's own setter validates against STATUSES

        if record.time_in and record.time_out:
            self._validate_time_order(record.time_in, record.time_out)

        return self._attendance.update(record)

    def delete_attendance(self, attendance_id: int) -> None:
        self._auth.require_permission("attendance.delete")
        self._attendance.delete(attendance_id)
