import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest  # noqa: E402
from repositories.database import DatabaseConnection  # noqa: E402
from repositories.user_repository import UserRepository  # noqa: E402
from repositories.employee_repository import EmployeeRepository  # noqa: E402
from repositories.department_repository import DepartmentRepository  # noqa: E402
from repositories.position_repository import PositionRepository  # noqa: E402
from repositories.attendance_repository import AttendanceRepository  # noqa: E402
from repositories.leave_repository import LeaveRepository  # noqa: E402
from repositories.payroll_repository import PayrollRepository  # noqa: E402
from services.auth_service import AuthService  # noqa: E402
from controllers.auth_controller import AuthController  # noqa: E402
from controllers.employee_controller import EmployeeController  # noqa: E402
from controllers.department_controller import DepartmentController  # noqa: E402
from controllers.position_controller import PositionController  # noqa: E402
from controllers.attendance_controller import AttendanceController  # noqa: E402
from controllers.leave_controller import LeaveController  # noqa: E402
from controllers.payroll_controller import PayrollController  # noqa: E402
from models.leave_request import LeaveRequest  # noqa: E402
from models.attendance import Attendance  # noqa: E402
from exceptions.custom_exceptions import ValidationException, DuplicateRecordException  # noqa: E402


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    conn = DatabaseConnection(db_path)
    conn.initialise_schema(schema_path)
    yield conn
    conn.close()


@pytest.fixture
def setup(db):
    """A logged-in admin with a department, position, and one employee ready to use."""
    user_repo = UserRepository(db)
    user_repo.create("admin", AuthService.hash_password("pw"), "ADMIN")
    user_repo.create("hr1", AuthService.hash_password("pw"), "HR_STAFF")

    emp_repo = EmployeeRepository(db)
    dept_repo = DepartmentRepository(db)
    pos_repo = PositionRepository(db)
    att_repo = AttendanceRepository(db)
    leave_repo = LeaveRepository(db)
    pay_repo = PayrollRepository(db)

    auth = AuthController(AuthService(user_repo))
    auth.login("admin", "pw")

    emp_ctrl = EmployeeController(auth, emp_repo, dept_repo, pos_repo)
    dept_ctrl = DepartmentController(auth, dept_repo)
    pos_ctrl = PositionController(auth, pos_repo, dept_repo)
    att_ctrl = AttendanceController(auth, att_repo, emp_repo)
    leave_ctrl = LeaveController(auth, leave_repo, emp_repo)
    pay_ctrl = PayrollController(auth, pay_repo, emp_repo, pos_repo, leave_repo)

    dept = dept_ctrl.add_department("Engineering")
    pos = pos_ctrl.add_position("Developer", dept.department_id, "3000")
    employee = emp_ctrl.add_employee(
        "Alex", "Kim", None, "alex@example.com", None, "2023-06-01",
        dept.department_id, pos.position_id,
    )

    return {
        "auth": auth, "employee": employee, "department": dept, "position": pos,
        "att_ctrl": att_ctrl, "leave_ctrl": leave_ctrl, "pay_ctrl": pay_ctrl,
        "leave_repo": leave_repo,
    }


class TestAttendanceModel:
    def test_hours_worked_computed(self):
        a = Attendance(employee_id=1, date="2026-08-01", time_in="09:00", time_out="17:30")
        assert a.hours_worked == 8.5

    def test_hours_worked_none_without_clock_out(self):
        a = Attendance(employee_id=1, date="2026-08-01", time_in="09:00")
        assert a.hours_worked is None

    def test_invalid_status_rejected(self):
        a = Attendance(employee_id=1, date="2026-08-01")
        with pytest.raises(ValidationException):
            a.status = "on_vacation"


class TestAttendanceWorkflow:
    def test_clock_in_and_out(self, setup):
        record = setup["att_ctrl"].clock_in(setup["employee"].employee_id, "2026-08-03", "09:00")
        assert record.status == "present"
        updated = setup["att_ctrl"].clock_out(setup["employee"].employee_id, "2026-08-03", "17:00")
        assert updated.hours_worked == 8.0

    def test_double_clock_in_blocked(self, setup):
        setup["att_ctrl"].clock_in(setup["employee"].employee_id, "2026-08-03", "09:00")
        with pytest.raises(ValidationException):
            setup["att_ctrl"].clock_in(setup["employee"].employee_id, "2026-08-03", "09:05")

    def test_mark_absent(self, setup):
        record = setup["att_ctrl"].mark_absent(setup["employee"].employee_id, "2026-08-04")
        assert record.status == "absent"


class TestLeaveRequestModel:
    def test_duration_days_inclusive(self):
        leave = LeaveRequest(1, "annual", "2026-08-10", "2026-08-12")
        assert leave.duration_days == 3

    def test_approve_transitions_state(self):
        leave = LeaveRequest(1, "annual", "2026-08-10", "2026-08-12")
        leave.approve(approver_user_id=99)
        assert leave.status == "approved"
        assert leave.approved_by == 99

    def test_cannot_approve_twice(self):
        leave = LeaveRequest(1, "annual", "2026-08-10", "2026-08-12")
        leave.approve(approver_user_id=99)
        with pytest.raises(ValidationException):
            leave.approve(approver_user_id=99)

    def test_cannot_reject_after_approve(self):
        leave = LeaveRequest(1, "annual", "2026-08-10", "2026-08-12")
        leave.approve(approver_user_id=99)
        with pytest.raises(ValidationException):
            leave.reject(approver_user_id=99)


class TestLeaveWorkflow:
    def test_submit_and_approve(self, setup):
        leave = setup["leave_ctrl"].submit_leave(
            setup["employee"].employee_id, "unpaid", "2026-08-10", "2026-08-12"
        )
        assert leave.status == "pending"
        approved = setup["leave_ctrl"].approve_leave(leave.leave_id)
        assert approved.status == "approved"

    def test_end_before_start_rejected(self, setup):
        with pytest.raises(ValidationException):
            setup["leave_ctrl"].submit_leave(
                setup["employee"].employee_id, "annual", "2026-08-12", "2026-08-10"
            )

    def test_hr_staff_can_submit_but_not_approve(self, db, setup):
        auth2 = AuthController(AuthService(UserRepository(db)))
        auth2.login("hr1", "pw")
        leave_ctrl2 = LeaveController(auth2, setup["leave_repo"], EmployeeRepository(db))
        leave = leave_ctrl2.submit_leave(
            setup["employee"].employee_id, "sick", "2026-08-20", "2026-08-20"
        )
        with pytest.raises(PermissionError):
            leave_ctrl2.approve_leave(leave.leave_id)


class TestPayrollWorkflow:
    def test_run_payroll_no_leave(self, setup):
        result = setup["pay_ctrl"].run_payroll("2026-08")
        assert len(result.created) == 1
        assert result.created[0].base_salary == 3000.0
        assert result.created[0].deductions == 0.0
        assert result.created[0].net_pay == 3000.0

    def test_run_payroll_with_approved_unpaid_leave_deducts(self, setup):
        leave = setup["leave_ctrl"].submit_leave(
            setup["employee"].employee_id, "unpaid", "2026-08-10", "2026-08-12"
        )
        setup["leave_ctrl"].approve_leave(leave.leave_id)

        result = setup["pay_ctrl"].run_payroll("2026-08")
        payroll = result.created[0]
        # 3 days unpaid out of a 30-day period on a 3000 base salary
        assert payroll.deductions == round(3000 / 30 * 3, 2)
        assert payroll.net_pay == round(3000 - payroll.deductions, 2)

    def test_pending_leave_does_not_deduct(self, setup):
        # Not approved yet -> should not affect payroll
        setup["leave_ctrl"].submit_leave(
            setup["employee"].employee_id, "unpaid", "2026-08-10", "2026-08-12"
        )
        result = setup["pay_ctrl"].run_payroll("2026-08")
        assert result.created[0].deductions == 0.0

    def test_rerun_same_period_skips(self, setup):
        setup["pay_ctrl"].run_payroll("2026-08")
        result2 = setup["pay_ctrl"].run_payroll("2026-08")
        assert len(result2.created) == 0
        assert len(result2.skipped) == 1

    def test_invalid_period_format_rejected(self, setup):
        with pytest.raises(ValidationException):
            setup["pay_ctrl"].run_payroll("August 2026")

    def test_employee_without_position_skipped(self, setup, db):
        emp_repo = EmployeeRepository(db)
        dept_repo = DepartmentRepository(db)
        pos_repo = PositionRepository(db)
        emp_ctrl = EmployeeController(setup["auth"], emp_repo, dept_repo, pos_repo)
        emp_ctrl.add_employee("No", "Position", None, None, None, "2024-01-01", None, None)

        result = setup["pay_ctrl"].run_payroll("2026-08")
        assert any("no position" in reason for _, reason in result.skipped)
