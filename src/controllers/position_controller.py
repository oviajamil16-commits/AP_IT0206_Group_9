"""Controller layer for Position management."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from controllers.auth_controller import AuthController  # noqa: E402
from repositories.position_repository import PositionRepository  # noqa: E402
from repositories.department_repository import DepartmentRepository  # noqa: E402
from models.position import Position  # noqa: E402
from utils.validators import Validator  # noqa: E402


class PositionController:
    def __init__(self, auth_controller: AuthController, position_repo: PositionRepository,
                 department_repo: DepartmentRepository):
        self._auth = auth_controller
        self._positions = position_repo
        self._departments = department_repo

    def add_position(self, title: str, department_id: int, base_salary_grade_raw) -> Position:
        self._auth.require_permission("position.create")
        title = Validator.require_non_empty(title, "Position title")
        self._departments.find_by_id(department_id)  # validates the FK exists
        grade = Validator.valid_positive_number(base_salary_grade_raw, "Base salary grade")
        return self._positions.create(title, department_id, grade)

    def list_positions(self) -> list[Position]:
        self._auth.require_permission("position.read")
        return self._positions.all()

    def list_positions_for_department(self, department_id: int) -> list[Position]:
        self._auth.require_permission("position.read")
        return self._positions.find_by_department(department_id)

    def delete_position(self, position_id: int) -> None:
        self._auth.require_permission("position.delete")
        self._positions.delete(position_id)
