"""Controller layer for Employee management — the reference vertical
slice. Validates input, enforces role permissions, checks foreign-key
references exist, then delegates persistence to EmployeeRepository."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from controllers.auth_controller import AuthController  # noqa: E402
from repositories.employee_repository import EmployeeRepository  # noqa: E402
from repositories.department_repository import DepartmentRepository  # noqa: E402
from repositories.position_repository import PositionRepository  # noqa: E402
from models.employee import Employee  # noqa: E402
from utils.validators import Validator  # noqa: E402
from utils.logger import get_logger  # noqa: E402

logger = get_logger("controllers.employee")


class EmployeeController:
    def __init__(self, auth_controller: AuthController, employee_repo: EmployeeRepository,
                 department_repo: DepartmentRepository, position_repo: PositionRepository):
        self._auth = auth_controller
        self._employees = employee_repo
        self._departments = department_repo
        self._positions = position_repo

    def add_employee(self, first_name: str, last_name: str, date_of_birth: str,
                      email: str, phone: str, hire_date: str,
                      department_id: int, position_id: int) -> Employee:
        self._auth.require_permission("employee.create")

        first_name = Validator.require_non_empty(first_name, "First name")
        last_name = Validator.require_non_empty(last_name, "Last name")
        hire_date = Validator.valid_date(
            Validator.require_non_empty(hire_date, "Hire date"), "Hire date"
        )
        if date_of_birth:
            date_of_birth = Validator.valid_date(date_of_birth, "Date of birth")
        if email:
            email = Validator.valid_email(email)

        # Referential integrity: fail fast with a clear message rather
        # than letting a bad id reach the database as an orphaned FK.
        if department_id is not None:
            self._departments.find_by_id(department_id)
        if position_id is not None:
            self._positions.find_by_id(position_id)

        employee = Employee(
            first_name=first_name, last_name=last_name, hire_date=hire_date,
            date_of_birth=date_of_birth, email=email or None, phone=phone or None,
            department_id=department_id, position_id=position_id,
        )
        return self._employees.create(employee)

    def get_employee(self, employee_id: int) -> Employee:
        self._auth.require_permission("employee.read")
        return self._employees.find_by_id(employee_id)

    def list_employees(self) -> list[Employee]:
        self._auth.require_permission("employee.read")
        return self._employees.all()

    def search_employees(self, name_contains: str = None, department_id: int = None,
                          status: str = None) -> list[Employee]:
        self._auth.require_permission("employee.read")
        if status:
            status = Validator.valid_choice(status, Employee.STATUSES, "Status")
        return self._employees.search(name_contains, department_id, status)

    def update_employee(self, employee_id: int, first_name: str = None, last_name: str = None,
                         email: str = None, phone: str = None, status: str = None,
                         department_id: int = None, position_id: int = None) -> Employee:
        self._auth.require_permission("employee.update")
        employee = self._employees.find_by_id(employee_id)

        if first_name:
            employee.first_name = Validator.require_non_empty(first_name, "First name")
        if last_name:
            employee.last_name = Validator.require_non_empty(last_name, "Last name")
        if email:
            employee.email = Validator.valid_email(email)
        if phone:
            employee.phone = phone
        if status:
            employee.status = status  # Employee's own setter validates against STATUSES
        if department_id is not None:
            self._departments.find_by_id(department_id)
            employee.department_id = department_id
        if position_id is not None:
            self._positions.find_by_id(position_id)
            employee.position_id = position_id

        return self._employees.update(employee)

    def delete_employee(self, employee_id: int) -> None:
        self._auth.require_permission("employee.delete")
        self._employees.delete(employee_id)
