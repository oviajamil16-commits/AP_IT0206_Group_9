import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest  # noqa: E402
from repositories.database import DatabaseConnection  # noqa: E402
from repositories.user_repository import UserRepository  # noqa: E402
from repositories.employee_repository import EmployeeRepository  # noqa: E402
from repositories.department_repository import DepartmentRepository  # noqa: E402
from repositories.position_repository import PositionRepository  # noqa: E402
from services.auth_service import AuthService  # noqa: E402
from controllers.auth_controller import AuthController  # noqa: E402
from controllers.employee_controller import EmployeeController  # noqa: E402
from controllers.department_controller import DepartmentController  # noqa: E402
from controllers.position_controller import PositionController  # noqa: E402
from models.employee import Employee  # noqa: E402
from exceptions.custom_exceptions import (  # noqa: E402
    DuplicateRecordException, RecordNotFoundException, ValidationException, EMSException,
)


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    conn = DatabaseConnection(db_path)
    conn.initialise_schema(schema_path)
    yield conn
    conn.close()


@pytest.fixture
def repos(db):
    return {
        "user": UserRepository(db),
        "employee": EmployeeRepository(db),
        "department": DepartmentRepository(db),
        "position": PositionRepository(db),
    }


@pytest.fixture
def admin_controllers(repos):
    """Controllers with a logged-in Administrator session."""
    repos["user"].create("admin", AuthService.hash_password("pw"), "ADMIN")
    auth = AuthController(AuthService(repos["user"]))
    auth.login("admin", "pw")
    return {
        "auth": auth,
        "employee": EmployeeController(auth, repos["employee"], repos["department"], repos["position"]),
        "department": DepartmentController(auth, repos["department"]),
        "position": PositionController(auth, repos["position"], repos["department"]),
    }


@pytest.fixture
def hr_controllers(repos, admin_controllers):
    """Same repos, but a second session logged in as HR Staff."""
    repos["user"].create("hr1", AuthService.hash_password("pw"), "HR_STAFF")
    auth = AuthController(AuthService(repos["user"]))
    auth.login("hr1", "pw")
    return {
        "auth": auth,
        "employee": EmployeeController(auth, repos["employee"], repos["department"], repos["position"]),
        "department": DepartmentController(auth, repos["department"]),
    }


class TestDepartmentRepository:
    def test_create_and_find(self, repos):
        dept = repos["department"].create("Engineering")
        assert repos["department"].find_by_id(dept.department_id).name == "Engineering"

    def test_duplicate_name_raises(self, repos):
        repos["department"].create("Engineering")
        with pytest.raises(DuplicateRecordException):
            repos["department"].create("Engineering")

    def test_find_missing_raises(self, repos):
        with pytest.raises(RecordNotFoundException):
            repos["department"].find_by_id(999)

    def test_delete_blocked_by_dependent_position(self, repos):
        dept = repos["department"].create("Engineering")
        repos["position"].create("Developer", dept.department_id, 4.0)
        with pytest.raises(EMSException):
            repos["department"].delete(dept.department_id)


class TestEmployeeRepositoryCRUD:
    def test_create_read_update_delete(self, repos):
        dept = repos["department"].create("Engineering")
        pos = repos["position"].create("Developer", dept.department_id, 4.0)

        employee = Employee(
            first_name="Jane", last_name="Doe", hire_date="2024-01-01",
            email="jane@example.com", department_id=dept.department_id, position_id=pos.position_id,
        )
        created = repos["employee"].create(employee)
        assert created.employee_id is not None

        found = repos["employee"].find_by_id(created.employee_id)
        assert found.full_name == "Jane Doe"

        found.status = "inactive"
        updated = repos["employee"].update(found)
        assert updated.status == "inactive"

        repos["employee"].delete(created.employee_id)
        with pytest.raises(RecordNotFoundException):
            repos["employee"].find_by_id(created.employee_id)

    def test_duplicate_email_raises(self, repos):
        e1 = Employee(first_name="A", last_name="A", hire_date="2024-01-01", email="dup@example.com")
        repos["employee"].create(e1)
        e2 = Employee(first_name="B", last_name="B", hire_date="2024-01-01", email="dup@example.com")
        with pytest.raises(DuplicateRecordException):
            repos["employee"].create(e2)

    def test_search_by_name(self, repos):
        repos["employee"].create(Employee(first_name="Jane", last_name="Doe", hire_date="2024-01-01"))
        repos["employee"].create(Employee(first_name="John", last_name="Smith", hire_date="2024-01-01"))
        results = repos["employee"].search(name_contains="Jane")
        assert len(results) == 1
        assert results[0].first_name == "Jane"

    def test_search_by_status(self, repos):
        e = repos["employee"].create(Employee(first_name="Jane", last_name="Doe", hire_date="2024-01-01"))
        repos["employee"].create(Employee(first_name="John", last_name="Smith", hire_date="2024-01-01"))
        e.status = "inactive"
        repos["employee"].update(e)
        results = repos["employee"].search(status="inactive")
        assert len(results) == 1
        assert results[0].last_name == "Doe"


class TestEmployeeControllerValidation:
    def test_add_employee_success(self, admin_controllers):
        emp = admin_controllers["employee"].add_employee(
            "Jane", "Doe", None, "jane@example.com", None, "2024-01-01", None, None
        )
        assert emp.employee_id is not None

    def test_invalid_hire_date_raises(self, admin_controllers):
        with pytest.raises(ValidationException):
            admin_controllers["employee"].add_employee(
                "Jane", "Doe", None, None, None, "01/01/2024", None, None
            )

    def test_invalid_email_raises(self, admin_controllers):
        with pytest.raises(ValidationException):
            admin_controllers["employee"].add_employee(
                "Jane", "Doe", None, "not-an-email", None, "2024-01-01", None, None
            )

    def test_unknown_department_id_raises(self, admin_controllers):
        with pytest.raises(RecordNotFoundException):
            admin_controllers["employee"].add_employee(
                "Jane", "Doe", None, None, None, "2024-01-01", 999, None
            )


class TestEmployeeControllerPermissions:
    def test_hr_staff_can_create_but_not_delete(self, admin_controllers, hr_controllers):
        emp = hr_controllers["employee"].add_employee(
            "Jane", "Doe", None, None, None, "2024-01-01", None, None
        )
        with pytest.raises(PermissionError):
            hr_controllers["employee"].delete_employee(emp.employee_id)

    def test_hr_staff_cannot_create_department(self, hr_controllers):
        with pytest.raises(PermissionError):
            hr_controllers["department"].add_department("Marketing")

    def test_admin_can_delete_employee(self, admin_controllers):
        emp = admin_controllers["employee"].add_employee(
            "Jane", "Doe", None, None, None, "2024-01-01", None, None
        )
        admin_controllers["employee"].delete_employee(emp.employee_id)
        with pytest.raises(RecordNotFoundException):
            admin_controllers["employee"].get_employee(emp.employee_id)
