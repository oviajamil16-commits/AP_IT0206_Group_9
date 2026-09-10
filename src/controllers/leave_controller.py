"""Controller layer for Leave requests, including the submit -> approve/reject
workflow that Payroll later reads from (approved unpaid leave -> deduction)."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from controllers.auth_controller import AuthController  # noqa: E402
from repositories.leave_repository import LeaveRepository  # noqa: E402
from repositories.employee_repository import EmployeeRepository  # noqa: E402
from models.leave_request import LeaveRequest  # noqa: E402
from utils.validators import Validator  # noqa: E402
from exceptions.custom_exceptions import ValidationException  # noqa: E402


class LeaveController:
    def __init__(self, auth_controller: AuthController, leave_repo: LeaveRepository,
                 employee_repo: EmployeeRepository):
        self._auth = auth_controller
        self._leave = leave_repo
        self._employees = employee_repo

    def submit_leave(self, employee_id: int, leave_type: str, start_date: str,
                      end_date: str) -> LeaveRequest:
        self._auth.require_permission("leave.create")
        self._employees.find_by_id(employee_id)  # validates the FK exists

        start_date = Validator.valid_date(start_date, "Start date")
        end_date = Validator.valid_date(end_date, "End date")
        if end_date < start_date:
            raise ValidationException("End date cannot be before start date.")

        leave = LeaveRequest(
            employee_id=employee_id, leave_type=leave_type,
            start_date=start_date, end_date=end_date,
        )
        return self._leave.create(leave)

    def get_leave(self, leave_id: int) -> LeaveRequest:
        self._auth.require_permission("leave.read")
        return self._leave.find_by_id(leave_id)

    def list_by_status(self, status: str = None) -> list[LeaveRequest]:
        self._auth.require_permission("leave.read")
        if status:
            return self._leave.find_by_status(status)
        return self._leave.all()

    def list_by_employee(self, employee_id: int) -> list[LeaveRequest]:
        self._auth.require_permission("leave.read")
        return self._leave.find_by_employee(employee_id)

    def approve_leave(self, leave_id: int) -> LeaveRequest:
        self._auth.require_permission("leave.approve")
        leave = self._leave.find_by_id(leave_id)
        approver = self._auth.current_user
        leave.approve(approver.user_id)  # domain-level state-machine check
        return self._leave.update(leave)

    def reject_leave(self, leave_id: int) -> LeaveRequest:
        self._auth.require_permission("leave.approve")
        leave = self._leave.find_by_id(leave_id)
        approver = self._auth.current_user
        leave.reject(approver.user_id)
        return self._leave.update(leave)
