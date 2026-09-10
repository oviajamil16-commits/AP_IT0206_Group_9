"""Controller layer for Payroll. run_payroll() is the SRS's core
transactional workflow: approved unpaid leave for the period is read back
and converted into a payroll deduction for the affected employee."""

import os
import re
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from controllers.auth_controller import AuthController  # noqa: E402
from repositories.payroll_repository import PayrollRepository  # noqa: E402
from repositories.employee_repository import EmployeeRepository  # noqa: E402
from repositories.position_repository import PositionRepository  # noqa: E402
from repositories.leave_repository import LeaveRepository  # noqa: E402
from models.payroll import Payroll  # noqa: E402
from exceptions.custom_exceptions import ValidationException, DuplicateRecordException, RecordNotFoundException  # noqa: E402
from utils.logger import get_logger  # noqa: E402
from utils.dates import period_bounds, overlap_days  # noqa: E402

logger = get_logger("controllers.payroll")

_PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")  # month restricted to 01-12
DAYS_PER_PERIOD = 30  # simplifying assumption, documented in the technical docs


class PayrollRunResult:
    """Small value object summarising one payroll run."""

    def __init__(self):
        self.created: list[Payroll] = []
        self.skipped: list[tuple[int, str]] = []  # (employee_id, reason)


class PayrollController:
    def __init__(self, auth_controller: AuthController, payroll_repo: PayrollRepository,
                 employee_repo: EmployeeRepository, position_repo: PositionRepository,
                 leave_repo: LeaveRepository):
        self._auth = auth_controller
        self._payroll = payroll_repo
        self._employees = employee_repo
        self._positions = position_repo
        self._leaves = leave_repo

    def run_payroll(self, period: str) -> PayrollRunResult:
        """Core transactional workflow: for every active employee with a
        position, compute base salary from their position's grade, deduct
        for any approved unpaid leave overlapping this period, and record
        the result. Employees already paid for this period are skipped."""
        self._auth.require_permission("payroll.run")
        if not _PERIOD_RE.match(period):
            raise ValidationException("Period must be in YYYY-MM format, e.g. 2026-08.")

        result = PayrollRunResult()
        for employee in self._employees.all():
            if not employee.is_active:
                result.skipped.append((employee.employee_id, "employee is not active"))
                continue
            if employee.position_id is None:
                result.skipped.append((employee.employee_id, "no position assigned"))
                continue

            try:
                position = self._positions.find_by_id(employee.position_id)
            except RecordNotFoundException:
                result.skipped.append((employee.employee_id, "position no longer exists"))
                continue

            base_salary = position.base_salary_grade
            deduction = self._calculate_leave_deduction(employee.employee_id, period, base_salary)

            payroll = Payroll(
                employee_id=employee.employee_id, period=period,
                base_salary=base_salary, allowances=0.0, deductions=deduction,
            )
            try:
                created = self._payroll.create(payroll)
                result.created.append(created)
            except DuplicateRecordException:
                result.skipped.append((employee.employee_id, f"already paid for {period}"))

        logger.info("Payroll run for %s: %d created, %d skipped",
                    period, len(result.created), len(result.skipped))
        return result

    def _calculate_leave_deduction(self, employee_id: int, period: str, base_salary: float) -> float:
        """Deduct for approved unpaid leave, counting only the days that
        actually fall inside this period -- not the leave's full length.
        A leave spanning Aug 29 - Sep 2 must deduct 3 days from August's
        payroll and 2 days from September's, not 5 days from each."""
        unpaid_leaves = self._leaves.find_approved_unpaid_overlapping_period(employee_id, period)
        if not unpaid_leaves:
            return 0.0
        period_start, period_end = period_bounds(period)
        total_unpaid_days = sum(
            overlap_days(leave.start_date, leave.end_date, period_start, period_end)
            for leave in unpaid_leaves
        )
        daily_rate = base_salary / DAYS_PER_PERIOD
        return round(daily_rate * total_unpaid_days, 2)

    def get_payslip(self, employee_id: int, period: str) -> Payroll:
        self._auth.require_permission("payroll.read")
        payroll = self._payroll.find_by_employee_and_period(employee_id, period)
        if payroll is None:
            raise RecordNotFoundException("Payroll", f"employee {employee_id}, period {period}")
        return payroll

    def list_by_period(self, period: str) -> list[Payroll]:
        self._auth.require_permission("payroll.read")
        return self._payroll.find_by_period(period)

    def list_by_employee(self, employee_id: int) -> list[Payroll]:
        self._auth.require_permission("payroll.read")
        return self._payroll.find_by_employee(employee_id)
