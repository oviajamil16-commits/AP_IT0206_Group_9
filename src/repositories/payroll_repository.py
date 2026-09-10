"""Data-access layer for the `payroll` table."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repositories.database import DatabaseConnection  # noqa: E402
from models.payroll import Payroll  # noqa: E402
from exceptions.custom_exceptions import RecordNotFoundException, DuplicateRecordException  # noqa: E402
from utils.logger import get_logger  # noqa: E402

logger = get_logger("repositories.payroll")


class PayrollRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    def create(self, payroll: Payroll) -> Payroll:
        if self.find_by_employee_and_period(payroll.employee_id, payroll.period) is not None:
            raise DuplicateRecordException("Payroll", "employee/period",
                                            f"{payroll.employee_id}/{payroll.period}")
        with self._db.transaction() as db:
            cursor = db.execute(
                "INSERT INTO payroll (employee_id, period, base_salary, allowances, "
                "deductions, net_pay, generated_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (payroll.employee_id, payroll.period, payroll.base_salary, payroll.allowances,
                 payroll.deductions, payroll.net_pay, payroll.generated_date),
            )
            new_id = cursor.lastrowid
        logger.info("Generated payroll #%s for employee #%s, period %s",
                    new_id, payroll.employee_id, payroll.period)
        return self.find_by_id(new_id)

    def find_by_id(self, payroll_id: int) -> Payroll:
        row = self._db.fetch_one("SELECT * FROM payroll WHERE id = ?", (payroll_id,))
        if row is None:
            raise RecordNotFoundException("Payroll", payroll_id)
        return self._to_model(row)

    def find_by_employee_and_period(self, employee_id: int, period: str) -> Payroll | None:
        row = self._db.fetch_one(
            "SELECT * FROM payroll WHERE employee_id = ? AND period = ?", (employee_id, period)
        )
        return self._to_model(row) if row else None

    def find_by_employee(self, employee_id: int) -> list[Payroll]:
        rows = self._db.fetch_all(
            "SELECT * FROM payroll WHERE employee_id = ? ORDER BY period DESC", (employee_id,)
        )
        return [self._to_model(r) for r in rows]

    def find_by_period(self, period: str) -> list[Payroll]:
        rows = self._db.fetch_all(
            "SELECT * FROM payroll WHERE period = ? ORDER BY employee_id", (period,)
        )
        return [self._to_model(r) for r in rows]

    def all(self) -> list[Payroll]:
        rows = self._db.fetch_all("SELECT * FROM payroll ORDER BY period DESC, employee_id")
        return [self._to_model(r) for r in rows]

    def _to_model(self, row) -> Payroll:
        return Payroll(
            payroll_id=row["id"],
            employee_id=row["employee_id"],
            period=row["period"],
            base_salary=row["base_salary"],
            allowances=row["allowances"],
            deductions=row["deductions"],
            generated_date=row["generated_date"],
        )
