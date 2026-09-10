"""Regression tests for three real bugs found during manual debugging
(not caught by the original test suite):

1. Payroll deductions for leave spanning a month boundary were double-
   counted (using the leave's full duration in both affected periods),
   and leave spanning an entire middle month was silently missed by a
   flawed LIKE-based SQL query. Fixed in utils/dates.py,
   leave_repository.py, and payroll_controller.py.

2. Clocking out with a time earlier than (or equal to) the clock-in time
   produced a negative or zero hours_worked instead of being rejected.
   Fixed in AttendanceController.clock_out().

3. Payroll's period regex checked digit count only (\\d{4}-\\d{2}), so
   '2026-13' or '2026-00' passed validation and later crashed with an
   unhandled calendar.IllegalMonthError deep in period_bounds(). Fixed by
   restricting the month group to 01-12.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest  # noqa: E402
from utils.dates import period_bounds, overlap_days  # noqa: E402
from repositories.database import DatabaseConnection  # noqa: E402
from repositories.user_repository import UserRepository  # noqa: E402
from repositories.employee_repository import EmployeeRepository  # noqa: E402
from repositories.department_repository import DepartmentRepository  # noqa: E402
from repositories.position_repository import PositionRepository  # noqa: E402
from repositories.leave_repository import LeaveRepository  # noqa: E402
from repositories.payroll_repository import PayrollRepository  # noqa: E402
from repositories.attendance_repository import AttendanceRepository  # noqa: E402
from services.auth_service import AuthService  # noqa: E402
from controllers.auth_controller import AuthController  # noqa: E402
from controllers.employee_controller import EmployeeController  # noqa: E402
from controllers.leave_controller import LeaveController  # noqa: E402
from controllers.payroll_controller import PayrollController  # noqa: E402
from controllers.attendance_controller import AttendanceController  # noqa: E402
from exceptions.custom_exceptions import ValidationException  # noqa: E402


class TestPeriodBounds:
    def test_regular_month(self):
        assert period_bounds("2026-08") == ("2026-08-01", "2026-08-31")

    def test_february_leap_year(self):
        assert period_bounds("2028-02") == ("2028-02-01", "2028-02-29")

    def test_february_non_leap_year(self):
        assert period_bounds("2026-02") == ("2026-02-01", "2026-02-28")


class TestOverlapDays:
    def test_no_overlap(self):
        assert overlap_days("2026-08-01", "2026-08-05", "2026-09-01", "2026-09-30") == 0

    def test_full_containment(self):
        assert overlap_days("2026-08-10", "2026-08-15", "2026-08-01", "2026-08-31") == 6

    def test_partial_overlap_at_start(self):
        assert overlap_days("2026-07-28", "2026-08-03", "2026-08-01", "2026-08-31") == 3

    def test_partial_overlap_at_end(self):
        assert overlap_days("2026-08-29", "2026-09-02", "2026-08-01", "2026-08-31") == 3

    def test_leave_spans_entire_period(self):
        assert overlap_days("2026-07-25", "2026-09-05", "2026-08-01", "2026-08-31") == 31

    def test_single_day_leave(self):
        assert overlap_days("2026-08-15", "2026-08-15", "2026-08-01", "2026-08-31") == 1


@pytest.fixture
def payroll_leave_setup(tmp_path):
    db_path = str(tmp_path / "test.db")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    db = DatabaseConnection(db_path)
    db.initialise_schema(schema_path)
    user_repo = UserRepository(db)
    user_repo.create("admin", AuthService.hash_password("pw"), "ADMIN")
    auth = AuthController(AuthService(user_repo))
    auth.login("admin", "pw")
    dept_repo, pos_repo = DepartmentRepository(db), PositionRepository(db)
    emp_repo, leave_repo, pay_repo = EmployeeRepository(db), LeaveRepository(db), PayrollRepository(db)
    emp_ctrl = EmployeeController(auth, emp_repo, dept_repo, pos_repo)
    leave_ctrl = LeaveController(auth, leave_repo, emp_repo)
    pay_ctrl = PayrollController(auth, pay_repo, emp_repo, pos_repo, leave_repo)
    dept = dept_repo.create("Eng")
    pos = pos_repo.create("Dev", dept.department_id, 3000.0)
    emp = emp_ctrl.add_employee("A", "B", None, None, None, "2024-01-01",
                                 dept.department_id, pos.position_id)
    yield {"leave_ctrl": leave_ctrl, "pay_ctrl": pay_ctrl, "employee_id": emp.employee_id}
    db.close()


class TestPayrollMonthBoundaryRegression:
    def test_leave_crossing_month_boundary_splits_correctly(self, payroll_leave_setup):
        s = payroll_leave_setup
        leave = s["leave_ctrl"].submit_leave(s["employee_id"], "unpaid", "2026-08-29", "2026-09-02")
        s["leave_ctrl"].approve_leave(leave.leave_id)
        aug_result = s["pay_ctrl"].run_payroll("2026-08")
        sep_result = s["pay_ctrl"].run_payroll("2026-09")
        assert aug_result.created[0].deductions == round(3000 / 30 * 3, 2)
        assert sep_result.created[0].deductions == round(3000 / 30 * 2, 2)

    def test_leave_spanning_entire_middle_month_is_not_missed(self, payroll_leave_setup):
        s = payroll_leave_setup
        leave = s["leave_ctrl"].submit_leave(s["employee_id"], "unpaid", "2026-07-25", "2026-09-05")
        s["leave_ctrl"].approve_leave(leave.leave_id)
        aug_result = s["pay_ctrl"].run_payroll("2026-08")
        assert len(aug_result.created) == 1, "leave spanning the whole month must not be silently missed"
        assert aug_result.created[0].deductions == round(3000 / 30 * 31, 2)


@pytest.fixture
def attendance_setup(tmp_path):
    db_path = str(tmp_path / "test.db")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    db = DatabaseConnection(db_path)
    db.initialise_schema(schema_path)
    user_repo = UserRepository(db)
    user_repo.create("admin", AuthService.hash_password("pw"), "ADMIN")
    auth = AuthController(AuthService(user_repo))
    auth.login("admin", "pw")
    emp_ctrl = EmployeeController(auth, EmployeeRepository(db), DepartmentRepository(db), PositionRepository(db))
    emp = emp_ctrl.add_employee("A", "B", None, None, None, "2024-01-01", None, None)
    att_ctrl = AttendanceController(auth, AttendanceRepository(db), EmployeeRepository(db))
    yield {"att_ctrl": att_ctrl, "employee_id": emp.employee_id}
    db.close()


class TestAttendanceTimeOrderRegression:
    def test_clock_out_before_clock_in_rejected(self, attendance_setup):
        s = attendance_setup
        s["att_ctrl"].clock_in(s["employee_id"], "2026-08-01", "17:00")
        with pytest.raises(ValidationException):
            s["att_ctrl"].clock_out(s["employee_id"], "2026-08-01", "09:00")

    def test_clock_out_equal_to_clock_in_rejected(self, attendance_setup):
        s = attendance_setup
        s["att_ctrl"].clock_in(s["employee_id"], "2026-08-01", "09:00")
        with pytest.raises(ValidationException):
            s["att_ctrl"].clock_out(s["employee_id"], "2026-08-01", "09:00")

    def test_normal_clock_out_still_works(self, attendance_setup):
        s = attendance_setup
        s["att_ctrl"].clock_in(s["employee_id"], "2026-08-01", "09:00")
        result = s["att_ctrl"].clock_out(s["employee_id"], "2026-08-01", "17:30")
        assert result.hours_worked == 8.5


@pytest.fixture
def payroll_only_setup(tmp_path):
    db_path = str(tmp_path / "test.db")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    db = DatabaseConnection(db_path)
    db.initialise_schema(schema_path)
    user_repo = UserRepository(db)
    user_repo.create("admin", AuthService.hash_password("pw"), "ADMIN")
    auth = AuthController(AuthService(user_repo))
    auth.login("admin", "pw")
    dept_repo, pos_repo = DepartmentRepository(db), PositionRepository(db)
    emp_ctrl = EmployeeController(auth, EmployeeRepository(db), dept_repo, pos_repo)
    dept = dept_repo.create("Eng")
    pos = pos_repo.create("Dev", dept.department_id, 3000.0)
    emp_ctrl.add_employee("A", "B", None, None, None, "2024-01-01", dept.department_id, pos.position_id)
    pay_ctrl = PayrollController(auth, PayrollRepository(db), EmployeeRepository(db),
                                  pos_repo, LeaveRepository(db))
    yield pay_ctrl
    db.close()


class TestPayrollInvalidMonthRegression:
    def test_invalid_month_13_rejected_cleanly(self, payroll_only_setup):
        with pytest.raises(ValidationException):
            payroll_only_setup.run_payroll("2026-13")

    def test_invalid_month_00_rejected_cleanly(self, payroll_only_setup):
        with pytest.raises(ValidationException):
            payroll_only_setup.run_payroll("2026-00")

    def test_invalid_month_99_rejected_cleanly(self, payroll_only_setup):
        with pytest.raises(ValidationException):
            payroll_only_setup.run_payroll("2026-99")

    def test_valid_period_still_works(self, payroll_only_setup):
        result = payroll_only_setup.run_payroll("2026-08")
        assert len(result.created) == 1


@pytest.fixture
def attendance_edit_setup(tmp_path):
    db_path = str(tmp_path / "test.db")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    db = DatabaseConnection(db_path)
    db.initialise_schema(schema_path)
    user_repo = UserRepository(db)
    user_repo.create("admin", AuthService.hash_password("pw"), "ADMIN")
    user_repo.create("hr1", AuthService.hash_password("pw"), "HR_STAFF")
    admin_auth = AuthController(AuthService(user_repo))
    admin_auth.login("admin", "pw")
    emp_ctrl = EmployeeController(admin_auth, EmployeeRepository(db), DepartmentRepository(db), PositionRepository(db))
    emp = emp_ctrl.add_employee("A", "B", None, None, None, "2024-01-01", None, None)
    admin_att_ctrl = AttendanceController(admin_auth, AttendanceRepository(db), EmployeeRepository(db))
    hr_auth = AuthController(AuthService(user_repo))
    hr_auth.login("hr1", "pw")
    hr_att_ctrl = AttendanceController(hr_auth, AttendanceRepository(db), EmployeeRepository(db))
    yield {"admin_att": admin_att_ctrl, "hr_att": hr_att_ctrl, "employee_id": emp.employee_id}
    db.close()


class TestEditAttendanceFeature:
    """Tests for the edit-attendance feature that was originally left in
    orphaned, wrongly-located files (src/controllers/user.py and
    src/controllers/attendance_view.py) and never actually wired up.
    Merged into the real models/controllers/views and completed here:
    the repository call the orphaned view used (get_by_id) and the edit
    method itself (edit_attendance) didn't exist at all until now."""

    def test_edit_updates_only_provided_fields(self, attendance_edit_setup):
        s = attendance_edit_setup
        record = s["admin_att"].clock_in(s["employee_id"], "2026-08-01", "09:00")
        s["admin_att"].clock_out(s["employee_id"], "2026-08-01", "17:00")
        edited = s["admin_att"].edit_attendance(record.attendance_id, time_in="08:30")
        assert edited.time_in == "08:30"
        assert edited.time_out == "17:00"  # untouched
        assert edited.hours_worked == 8.5

    def test_edit_cannot_reintroduce_negative_hours_bug(self, attendance_edit_setup):
        s = attendance_edit_setup
        record = s["admin_att"].clock_in(s["employee_id"], "2026-08-01", "09:00")
        s["admin_att"].clock_out(s["employee_id"], "2026-08-01", "17:00")
        with pytest.raises(ValidationException):
            s["admin_att"].edit_attendance(record.attendance_id, time_in="18:00")

    def test_clear_time_out(self, attendance_edit_setup):
        s = attendance_edit_setup
        record = s["admin_att"].clock_in(s["employee_id"], "2026-08-01", "09:00")
        s["admin_att"].clock_out(s["employee_id"], "2026-08-01", "17:00")
        edited = s["admin_att"].edit_attendance(record.attendance_id, clear_time_out=True)
        assert edited.time_out is None
        assert edited.hours_worked is None

    def test_hr_staff_can_edit(self, attendance_edit_setup):
        s = attendance_edit_setup
        record = s["admin_att"].clock_in(s["employee_id"], "2026-08-01", "09:00")
        edited = s["hr_att"].edit_attendance(record.attendance_id, status="absent", clear_time_out=True)
        assert edited.status == "absent"

    def test_get_by_id_requires_read_permission(self, attendance_edit_setup):
        s = attendance_edit_setup
        record = s["admin_att"].clock_in(s["employee_id"], "2026-08-01", "09:00")
        fetched = s["admin_att"].get_by_id(record.attendance_id)
        assert fetched.attendance_id == record.attendance_id
