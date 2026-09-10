"""Employee: the central domain entity of the system. Extends Person,
adding employment-specific fields."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.person import Person  # noqa: E402
from exceptions.custom_exceptions import ValidationException  # noqa: E402


class Employee(Person):
    STATUSES = {"active", "inactive", "terminated"}

    def __init__(self, first_name: str, last_name: str, hire_date: str,
                 employee_id: int = None, date_of_birth: str = None,
                 email: str = None, phone: str = None,
                 department_id: int = None, position_id: int = None,
                 status: str = "active"):
        super().__init__(first_name, last_name, date_of_birth, email, phone)
        self.employee_id = employee_id
        self.hire_date = hire_date
        self.department_id = department_id
        self.position_id = position_id
        self.status = status

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        if value not in self.STATUSES:
            raise ValidationException(f"Status must be one of {sorted(self.STATUSES)}.")
        self._status = value

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    def role_label(self) -> str:
        return "Employee"

    def __eq__(self, other) -> bool:
        return isinstance(other, Employee) and self.employee_id == other.employee_id

    def __repr__(self) -> str:
        return f"Employee(id={self.employee_id}, name={self.full_name!r}, status={self.status!r})"
