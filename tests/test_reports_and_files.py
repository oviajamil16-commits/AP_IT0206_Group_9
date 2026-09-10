"""Tests for HolidayService, FileImportService, and ReportController.

HolidayService's network call is mocked here (unittest.mock, stdlib —
no pytest plugin needed) because this build sandbox blocks all outbound
HTTP, including to date.nager.at. The mock verifies the parsing/error-
handling logic is correct; it does not prove the live API integration
works end-to-end. That must be confirmed on a normal networked machine —
see the Test Report.

FileImportService and ReportController need no mocking: CSV/JSON files
and pandas/matplotlib all work fully offline, so those tests are genuine,
complete, real executions.
"""

import json
import os
import sys
from unittest.mock import patch, Mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest  # noqa: E402
import requests  # noqa: E402
from repositories.database import DatabaseConnection  # noqa: E402
from repositories.user_repository import UserRepository  # noqa: E402
from repositories.employee_repository import EmployeeRepository  # noqa: E402
from repositories.department_repository import DepartmentRepository  # noqa: E402
from repositories.position_repository import PositionRepository  # noqa: E402
from repositories.payroll_repository import PayrollRepository  # noqa: E402
from repositories.attendance_repository import AttendanceRepository  # noqa: E402
from services.auth_service import AuthService  # noqa: E402
from services.file_service import FileImportService  # noqa: E402
from services.holiday_service import HolidayService  # noqa: E402
from controllers.auth_controller import AuthController  # noqa: E402
from controllers.employee_controller import EmployeeController  # noqa: E402
from controllers.report_controller import ReportController  # noqa: E402


# ---------------------------------------------------------------------------
# HolidayService — network mocked, parsing logic genuinely exercised
# ---------------------------------------------------------------------------
class TestHolidayServiceMocked:
    def test_get_holidays_parses_successful_response(self):
        fake_json = [
            {"date": "2026-01-01", "localName": "New Year's Day"},
            {"date": "2026-04-25", "localName": "Anzac Day"},
        ]
        mock_response = Mock()
        mock_response.json.return_value = fake_json
        mock_response.raise_for_status.return_value = None

        with patch("services.holiday_service.requests.get", return_value=mock_response) as mock_get:
            holidays = HolidayService("AU").get_holidays(2026)

        mock_get.assert_called_once()
        assert len(holidays) == 2
        assert holidays[0] == {"date": "2026-01-01", "name": "New Year's Day"}

    def test_get_holidays_returns_empty_list_on_network_error(self):
        with patch("services.holiday_service.requests.get",
                   side_effect=requests.ConnectionError("no network")):
            holidays = HolidayService("AU").get_holidays(2026)
        assert holidays == []

    def test_get_holidays_returns_empty_list_on_bad_status(self):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")
        with patch("services.holiday_service.requests.get", return_value=mock_response):
            holidays = HolidayService("AU").get_holidays(2026)
        assert holidays == []

    def test_is_public_holiday_matches_date(self):
        fake_json = [{"date": "2026-12-25", "localName": "Christmas Day"}]
        mock_response = Mock()
        mock_response.json.return_value = fake_json
        mock_response.raise_for_status.return_value = None
        with patch("services.holiday_service.requests.get", return_value=mock_response):
            name = HolidayService("AU").is_public_holiday("2026-12-25")
        assert name == "Christmas Day"

    def test_is_public_holiday_returns_none_for_non_holiday(self):
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        with patch("services.holiday_service.requests.get", return_value=mock_response):
            name = HolidayService("AU").is_public_holiday("2026-03-03")
        assert name is None

    def test_real_network_call_blocked_in_this_sandbox(self):
        """Documents the actual sandbox behaviour: a real call is attempted,
        blocked by the egress proxy, and fails soft to an empty list rather
        than crashing. This is not a substitute for testing on a real
        network — it confirms the failure path only."""
        holidays = HolidayService("AU").get_holidays(2026)
        assert holidays == []  # true in this sandbox; would be non-empty on a real network


# ---------------------------------------------------------------------------
# FileImportService — fully real, no mocking needed
# ---------------------------------------------------------------------------
@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    conn = DatabaseConnection(db_path)
    conn.initialise_schema(schema_path)
    yield conn
    conn.close()


@pytest.fixture
def employee_setup(db):
    user_repo = UserRepository(db)
    user_repo.create("admin", AuthService.hash_password("pw"), "ADMIN")
    auth = AuthController(AuthService(user_repo))
    auth.login("admin", "pw")
    emp_repo = EmployeeRepository(db)
    dept_repo = DepartmentRepository(db)
    pos_repo = PositionRepository(db)
    emp_ctrl = EmployeeController(auth, emp_repo, dept_repo, pos_repo)
    return FileImportService(emp_ctrl), emp_repo


class TestFileImportServiceCSV:
    def test_import_valid_csv(self, employee_setup, tmp_path):
        service, emp_repo = employee_setup
        csv_path = tmp_path / "employees.csv"
        csv_path.write_text(
            "first_name,last_name,hire_date,email\n"
            "Jane,Doe,2024-01-01,jane@example.com\n"
            "John,Smith,2024-02-01,\n"
        )
        result = service.import_employees_csv(str(csv_path))
        assert result.success_count == 2
        assert result.error_count == 0
        assert len(emp_repo.all()) == 2

    def test_import_csv_missing_required_field_collected_as_error(self, employee_setup, tmp_path):
        service, emp_repo = employee_setup
        csv_path = tmp_path / "bad.csv"
        csv_path.write_text("first_name,last_name,hire_date\nNoHireDate,Person,\n")
        result = service.import_employees_csv(str(csv_path))
        assert result.success_count == 0
        assert result.error_count == 1
        assert "hire_date" in result.errors[0][1]

    def test_one_bad_row_does_not_abort_whole_import(self, employee_setup, tmp_path):
        service, emp_repo = employee_setup
        csv_path = tmp_path / "mixed.csv"
        csv_path.write_text(
            "first_name,last_name,hire_date\n"
            "Good,Row,2024-01-01\n"
            "Bad,Row,\n"
            "Also Good,Row,2024-01-02\n"
        )
        result = service.import_employees_csv(str(csv_path))
        assert result.success_count == 2
        assert result.error_count == 1


class TestFileImportServiceJSON:
    def test_import_valid_json(self, employee_setup, tmp_path):
        service, emp_repo = employee_setup
        json_path = tmp_path / "employees.json"
        json_path.write_text(json.dumps([
            {"first_name": "Jane", "last_name": "Doe", "hire_date": "2024-01-01"},
        ]))
        result = service.import_employees_json(str(json_path))
        assert result.success_count == 1
        assert len(emp_repo.all()) == 1

    def test_import_json_not_a_list_raises(self, employee_setup, tmp_path):
        from exceptions.custom_exceptions import EMSException
        service, _ = employee_setup
        json_path = tmp_path / "bad.json"
        json_path.write_text(json.dumps({"not": "a list"}))
        with pytest.raises(EMSException):
            service.import_employees_json(str(json_path))


class TestFileExport:
    def test_export_csv_then_reimport_round_trips(self, employee_setup, tmp_path):
        service, emp_repo = employee_setup
        service.import_employees_json(str(_write_json(tmp_path, [
            {"first_name": "Jane", "last_name": "Doe", "hire_date": "2024-01-01"},
        ])))
        employees = emp_repo.all()
        csv_path = tmp_path / "export.csv"
        count = service.export_employees_csv(str(csv_path), employees)
        assert count == 1
        assert csv_path.exists()
        content = csv_path.read_text()
        assert "Jane" in content and "Doe" in content


def _write_json(tmp_path, data):
    path = tmp_path / "seed.json"
    path.write_text(json.dumps(data))
    return path


# ---------------------------------------------------------------------------
# ReportController — fully real, pandas + matplotlib, no mocking needed
# ---------------------------------------------------------------------------
@pytest.fixture
def report_setup(db, tmp_path):
    user_repo = UserRepository(db)
    user_repo.create("admin", AuthService.hash_password("pw"), "ADMIN")
    auth = AuthController(AuthService(user_repo))
    auth.login("admin", "pw")

    emp_repo = EmployeeRepository(db)
    dept_repo = DepartmentRepository(db)
    pos_repo = PositionRepository(db)
    pay_repo = PayrollRepository(db)
    att_repo = AttendanceRepository(db)
    emp_ctrl = EmployeeController(auth, emp_repo, dept_repo, pos_repo)

    dept = dept_repo.create("Engineering")
    pos = pos_repo.create("Developer", dept.department_id, 3000.0)
    emp_ctrl.add_employee("Jane", "Doe", None, None, None, "2024-01-01", dept.department_id, pos.position_id)
    emp_ctrl.add_employee("John", "Smith", None, None, None, "2024-01-01", dept.department_id, pos.position_id)

    report_ctrl = ReportController(auth, emp_repo, dept_repo, pay_repo, att_repo,
                                    output_dir=str(tmp_path / "exports"))
    return report_ctrl


class TestReportController:
    def test_headcount_by_department_real_pandas_and_chart(self, report_setup):
        counts, chart_path = report_setup.headcount_by_department()
        assert counts["Engineering"] == 2
        assert os.path.exists(chart_path)
        assert os.path.getsize(chart_path) > 0  # a real PNG was actually written

    def test_headcount_with_no_employees_does_not_crash(self, db, tmp_path):
        user_repo = UserRepository(db)
        user_repo.create("admin", AuthService.hash_password("pw"), "ADMIN")
        auth = AuthController(AuthService(user_repo))
        auth.login("admin", "pw")
        report_ctrl = ReportController(
            auth, EmployeeRepository(db), DepartmentRepository(db),
            PayrollRepository(db), AttendanceRepository(db),
            output_dir=str(tmp_path / "exports"),
        )
        counts, chart_path = report_ctrl.headcount_by_department()
        assert len(counts) == 0
        assert os.path.exists(chart_path)
