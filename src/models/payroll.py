"""Payroll: one pay-period record for one employee. net_pay is always
computed from the other three figures rather than stored independently,
so it can never drift out of sync with them."""

import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exceptions.custom_exceptions import ValidationException  # noqa: E402


class Payroll:
    def __init__(self, employee_id: int, period: str, base_salary: float,
                 payroll_id: int = None, allowances: float = 0.0, deductions: float = 0.0,
                 generated_date: str = None):
        self.payroll_id = payroll_id
        self.employee_id = employee_id
        self.period = period
        self.base_salary = base_salary
        self.allowances = allowances
        self.deductions = deductions
        self.generated_date = generated_date or datetime.now().isoformat(timespec="seconds")

    @property
    def base_salary(self) -> float:
        return self._base_salary

    @base_salary.setter
    def base_salary(self, value: float) -> None:
        self._base_salary = self._non_negative(value, "Base salary")

    @property
    def allowances(self) -> float:
        return self._allowances

    @allowances.setter
    def allowances(self, value: float) -> None:
        self._allowances = self._non_negative(value, "Allowances")

    @property
    def deductions(self) -> float:
        return self._deductions

    @deductions.setter
    def deductions(self, value: float) -> None:
        self._deductions = self._non_negative(value, "Deductions")

    @staticmethod
    def _non_negative(value, field_name: str) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ValidationException(f"{field_name} must be a number.")
        if number < 0:
            raise ValidationException(f"{field_name} cannot be negative.")
        return number

    @property
    def net_pay(self) -> float:
        """Always derived, never stored independently of its inputs."""
        return round(self.base_salary + self.allowances - self.deductions, 2)

    def __eq__(self, other) -> bool:
        return isinstance(other, Payroll) and self.payroll_id == other.payroll_id

    def __repr__(self) -> str:
        return (f"Payroll(id={self.payroll_id}, employee_id={self.employee_id}, "
                f"period={self.period!r}, net_pay={self.net_pay})")
