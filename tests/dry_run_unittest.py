"""Equivalent of tests/test_services.py, test_models.py, test_repositories.py,
written against the stdlib unittest framework instead of pytest.

WHY THIS FILE EXISTS: pytest cannot be installed in this build sandbox
(no network access to PyPI). unittest ships with Python, so this file lets
the exact same test logic actually run and produce real pass/fail output
here, as genuine evidence the code works — not a substitute for running
the real pytest suite in tests/test_*.py, which remains the required
deliverable per the assessment brief and should still be run with
`pytest tests/ -v` on a normal networked machine.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from repositories.database import DatabaseConnection
from repositories.user_repository import UserRepository
from repositories.employee_repository import EmployeeRepository
from repositories.department_repository import DepartmentRepository
from repositories.position_repository import PositionRepository
from services.auth_service import AuthService
from controllers.auth_controller import AuthController
from controllers.employee_controller import EmployeeController
from controllers.department_controller import DepartmentController
from controllers.position_controller import PositionController
from models.employee import Employee
from models.department import Department
from models.position import Position
from exceptions.custom_exceptions import (
    DuplicateRecordException, RecordNotFoundException, ValidationException, EMSException,
)

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")


def fresh_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)  # DatabaseConnection creates it
    conn = DatabaseConnection(path)
    conn.initialise_schema(SCHEMA_PATH)
    return conn, path


class DbTestCase(unittest.TestCase):
    """Base class: fresh temp SQLite DB per test, cleaned up after."""

    def setUp(self):
        self.db, self.db_path = fresh_db()
        self.user_repo = UserRepository(self.db)
        self.employee_repo = EmployeeRepository(self.db)
        self.department_repo = DepartmentRepository(self.db)
        self.position_repo = PositionRepository(self.db)

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def login_as(self, username, password, role):
        self.user_repo.create(username, AuthService.hash_password(password), role)
        auth = AuthController(AuthService(self.user_repo))
        auth.login(username, password)
        return auth


# ---------------------------------------------------------------------------
# Password hashing (mirrors test_services.py :: TestPasswordHashing)
# ---------------------------------------------------------------------------
class TestPasswordHashing(unittest.TestCase):
    def test_hash_is_not_plaintext(self):
        hashed = AuthService.hash_password("correct horse battery staple")
        self.assertNotIn("correct horse battery staple", hashed)

    def test_verify_correct_password(self):
        hashed = AuthService.hash_password("mypassword123")
        self.assertTrue(AuthService.verify_password("mypassword123", hashed))

    def test_verify_wrong_password(self):
        hashed = AuthService.hash_password("mypassword123")
        self.assertFalse(AuthService.verify_password("wrongpassword", hashed))

    def test_two_hashes_of_same_password_differ(self):
        h1 = AuthService.hash_password("samepassword")
        h2 = AuthService.hash_password("samepassword")
        self.assertNotEqual(h1, h2)


# ---------------------------------------------------------------------------
# User repository + login (mirrors test_services.py :: TestUserRepository / TestAuthServiceLogin)
# ---------------------------------------------------------------------------
class TestUserRepositoryAndLogin(DbTestCase):
    def test_create_and_find_by_username(self):
        self.user_repo.create("jdoe", AuthService.hash_password("pw"), "HR_STAFF")
        found = self.user_repo.find_by_username("jdoe")
        self.assertIsNotNone(found)
        self.assertEqual(found.username, "jdoe")
        self.assertEqual(found.role, "HR_STAFF")

    def test_duplicate_username_raises(self):
        self.user_repo.create("jdoe", AuthService.hash_password("pw"), "HR_STAFF")
        with self.assertRaises(DuplicateRecordException):
            self.user_repo.create("jdoe", AuthService.hash_password("pw2"), "ADMIN")

    def test_find_unknown_username_returns_none(self):
        self.assertIsNone(self.user_repo.find_by_username("nobody"))

    def test_login_success(self):
        self.user_repo.create("admin1", AuthService.hash_password("secret"), "ADMIN")
        user = AuthService(self.user_repo).login("admin1", "secret")
        self.assertEqual(user.username, "admin1")
        self.assertEqual(user.role, "ADMIN")

    def test_login_wrong_password_raises(self):
        from exceptions.custom_exceptions import InvalidCredentialsException
        self.user_repo.create("admin1", AuthService.hash_password("secret"), "ADMIN")
        with self.assertRaises(InvalidCredentialsException):
            AuthService(self.user_repo).login("admin1", "wrong")

    def test_admin_can_delete_employee_permission(self):
        self.user_repo.create("admin1", AuthService.hash_password("pw"), "ADMIN")
        admin = self.user_repo.find_by_username("admin1")
        self.assertTrue(admin.can("employee.delete"))

    def test_hr_staff_cannot_delete_employee_permission(self):
        self.user_repo.create("hr1", AuthService.hash_password("pw"), "HR_STAFF")
        hr = self.user_repo.find_by_username("hr1")
        self.assertFalse(hr.can("employee.delete"))


# ---------------------------------------------------------------------------
# Domain models (mirrors test_models.py)
# ---------------------------------------------------------------------------
class TestEmployeeModel(unittest.TestCase):
    def test_full_name_property(self):
        e = Employee(first_name="Jane", last_name="Doe", hire_date="2024-01-01")
        self.assertEqual(e.full_name, "Jane Doe")

    def test_empty_first_name_rejected(self):
        with self.assertRaises(ValidationException):
            Employee(first_name="", last_name="Doe", hire_date="2024-01-01")

    def test_default_status_is_active(self):
        e = Employee(first_name="Jane", last_name="Doe", hire_date="2024-01-01")
        self.assertEqual(e.status, "active")
        self.assertTrue(e.is_active)

    def test_invalid_status_rejected(self):
        e = Employee(first_name="Jane", last_name="Doe", hire_date="2024-01-01")
        with self.assertRaises(ValidationException):
            e.status = "on_the_moon"

    def test_equality_by_id(self):
        a = Employee(first_name="A", last_name="A", hire_date="2024-01-01", employee_id=1)
        b = Employee(first_name="B", last_name="B", hire_date="2024-01-01", employee_id=1)
        c = Employee(first_name="A", last_name="A", hire_date="2024-01-01", employee_id=2)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)


class TestDepartmentAndPositionModels(unittest.TestCase):
    def test_department_str(self):
        self.assertEqual(str(Department(name="Engineering", department_id=1)), "Engineering")

    def test_position_str(self):
        p = Position(title="Developer", department_id=1, base_salary_grade=4.0, position_id=1)
        self.assertEqual(str(p), "Developer")


# ---------------------------------------------------------------------------
# Repository CRUD (mirrors test_repositories.py)
# ---------------------------------------------------------------------------
class TestDepartmentRepository(DbTestCase):
    def test_create_and_find(self):
        dept = self.department_repo.create("Engineering")
        self.assertEqual(self.department_repo.find_by_id(dept.department_id).name, "Engineering")

    def test_duplicate_name_raises(self):
        self.department_repo.create("Engineering")
        with self.assertRaises(DuplicateRecordException):
            self.department_repo.create("Engineering")

    def test_delete_blocked_by_dependent_position(self):
        dept = self.department_repo.create("Engineering")
        self.position_repo.create("Developer", dept.department_id, 4.0)
        with self.assertRaises(EMSException):
            self.department_repo.delete(dept.department_id)


class TestEmployeeRepositoryCRUD(DbTestCase):
    def test_create_read_update_delete(self):
        dept = self.department_repo.create("Engineering")
        pos = self.position_repo.create("Developer", dept.department_id, 4.0)
        employee = Employee(first_name="Jane", last_name="Doe", hire_date="2024-01-01",
                             email="jane@example.com", department_id=dept.department_id,
                             position_id=pos.position_id)
        created = self.employee_repo.create(employee)
        self.assertIsNotNone(created.employee_id)

        found = self.employee_repo.find_by_id(created.employee_id)
        self.assertEqual(found.full_name, "Jane Doe")

        found.status = "inactive"
        updated = self.employee_repo.update(found)
        self.assertEqual(updated.status, "inactive")

        self.employee_repo.delete(created.employee_id)
        with self.assertRaises(RecordNotFoundException):
            self.employee_repo.find_by_id(created.employee_id)

    def test_duplicate_email_raises(self):
        self.employee_repo.create(Employee(first_name="A", last_name="A", hire_date="2024-01-01", email="dup@example.com"))
        with self.assertRaises(DuplicateRecordException):
            self.employee_repo.create(Employee(first_name="B", last_name="B", hire_date="2024-01-01", email="dup@example.com"))

    def test_search_by_name(self):
        self.employee_repo.create(Employee(first_name="Jane", last_name="Doe", hire_date="2024-01-01"))
        self.employee_repo.create(Employee(first_name="John", last_name="Smith", hire_date="2024-01-01"))
        results = self.employee_repo.search(name_contains="Jane")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].first_name, "Jane")


class TestEmployeeControllerValidationAndPermissions(DbTestCase):
    def test_add_employee_success(self):
        auth = self.login_as("admin1", "pw", "ADMIN")
        ctrl = EmployeeController(auth, self.employee_repo, self.department_repo, self.position_repo)
        emp = ctrl.add_employee("Jane", "Doe", None, "jane@example.com", None, "2024-01-01", None, None)
        self.assertIsNotNone(emp.employee_id)

    def test_invalid_hire_date_raises(self):
        auth = self.login_as("admin1", "pw", "ADMIN")
        ctrl = EmployeeController(auth, self.employee_repo, self.department_repo, self.position_repo)
        with self.assertRaises(ValidationException):
            ctrl.add_employee("Jane", "Doe", None, None, None, "01/01/2024", None, None)

    def test_unknown_department_id_raises(self):
        auth = self.login_as("admin1", "pw", "ADMIN")
        ctrl = EmployeeController(auth, self.employee_repo, self.department_repo, self.position_repo)
        with self.assertRaises(RecordNotFoundException):
            ctrl.add_employee("Jane", "Doe", None, None, None, "2024-01-01", 999, None)

    def test_hr_staff_can_create_but_not_delete(self):
        auth = self.login_as("hr1", "pw", "HR_STAFF")
        ctrl = EmployeeController(auth, self.employee_repo, self.department_repo, self.position_repo)
        emp = ctrl.add_employee("Jane", "Doe", None, None, None, "2024-01-01", None, None)
        with self.assertRaises(PermissionError):
            ctrl.delete_employee(emp.employee_id)

    def test_hr_staff_cannot_create_department(self):
        auth = self.login_as("hr1", "pw", "HR_STAFF")
        dept_ctrl = DepartmentController(auth, self.department_repo)
        with self.assertRaises(PermissionError):
            dept_ctrl.add_department("Marketing")

    def test_admin_can_delete_employee(self):
        auth = self.login_as("admin1", "pw", "ADMIN")
        ctrl = EmployeeController(auth, self.employee_repo, self.department_repo, self.position_repo)
        emp = ctrl.add_employee("Jane", "Doe", None, None, None, "2024-01-01", None, None)
        ctrl.delete_employee(emp.employee_id)
        with self.assertRaises(RecordNotFoundException):
            ctrl.get_employee(emp.employee_id)


if __name__ == "__main__":
    unittest.main(verbosity=2)
