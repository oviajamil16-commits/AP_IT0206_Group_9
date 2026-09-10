import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest  # noqa: E402
from models.employee import Employee  # noqa: E402
from models.department import Department  # noqa: E402
from models.position import Position  # noqa: E402
from exceptions.custom_exceptions import ValidationException  # noqa: E402


class TestEmployeeModel:
    def test_full_name_property(self):
        e = Employee(first_name="Jane", last_name="Doe", hire_date="2024-01-01")
        assert e.full_name == "Jane Doe"

    def test_empty_first_name_rejected(self):
        with pytest.raises(ValidationException):
            Employee(first_name="", last_name="Doe", hire_date="2024-01-01")

    def test_default_status_is_active(self):
        e = Employee(first_name="Jane", last_name="Doe", hire_date="2024-01-01")
        assert e.status == "active"
        assert e.is_active is True

    def test_invalid_status_rejected(self):
        e = Employee(first_name="Jane", last_name="Doe", hire_date="2024-01-01")
        with pytest.raises(ValidationException):
            e.status = "on_the_moon"

    def test_status_change_updates_is_active(self):
        e = Employee(first_name="Jane", last_name="Doe", hire_date="2024-01-01")
        e.status = "terminated"
        assert e.is_active is False

    def test_equality_by_id(self):
        a = Employee(first_name="A", last_name="A", hire_date="2024-01-01", employee_id=1)
        b = Employee(first_name="B", last_name="B", hire_date="2024-01-01", employee_id=1)
        c = Employee(first_name="A", last_name="A", hire_date="2024-01-01", employee_id=2)
        assert a == b  # same id, different names -> still equal by identity
        assert a != c

    def test_role_label(self):
        e = Employee(first_name="Jane", last_name="Doe", hire_date="2024-01-01")
        assert e.role_label() == "Employee"


class TestDepartmentModel:
    def test_str_returns_name(self):
        d = Department(name="Engineering", department_id=1)
        assert str(d) == "Engineering"

    def test_equality_by_id(self):
        assert Department(name="A", department_id=1) == Department(name="B", department_id=1)
        assert Department(name="A", department_id=1) != Department(name="A", department_id=2)


class TestPositionModel:
    def test_str_returns_title(self):
        p = Position(title="Developer", department_id=1, base_salary_grade=4.0, position_id=1)
        assert str(p) == "Developer"
