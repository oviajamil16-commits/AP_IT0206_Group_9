"""Controller layer for Department management. Thin — Department has no
complex business rules beyond permission checks and name validation."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from controllers.auth_controller import AuthController  # noqa: E402
from repositories.department_repository import DepartmentRepository  # noqa: E402
from models.department import Department  # noqa: E402
from utils.validators import Validator  # noqa: E402


class DepartmentController:
    def __init__(self, auth_controller: AuthController, department_repo: DepartmentRepository):
        self._auth = auth_controller
        self._departments = department_repo

    def add_department(self, name: str) -> Department:
        self._auth.require_permission("department.create")
        name = Validator.require_non_empty(name, "Department name")
        return self._departments.create(name)

    def list_departments(self) -> list[Department]:
        self._auth.require_permission("department.read")
        return self._departments.all()

    def get_department(self, department_id: int) -> Department:
        self._auth.require_permission("department.read")
        return self._departments.find_by_id(department_id)

    def delete_department(self, department_id: int) -> None:
        self._auth.require_permission("department.delete")
        self._departments.delete(department_id)
