"""Data-access layer for the `employees` table. Full CRUD plus
search/filter, all via parameterised queries."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from repositories.database import DatabaseConnection  # noqa: E402
from models.employee import Employee  # noqa: E402
from exceptions.custom_exceptions import DuplicateRecordException, RecordNotFoundException  # noqa: E402
from utils.logger import get_logger  # noqa: E402

logger = get_logger("repositories.employee")


class EmployeeRepository:
    def __init__(self, db: DatabaseConnection):
        self._db = db

    def create(self, employee: Employee) -> Employee:
        if employee.email and self.find_by_email(employee.email) is not None:
            raise DuplicateRecordException("Employee", "email", employee.email)

        with self._db.transaction() as db:
            cursor = db.execute(
                "INSERT INTO employees (first_name, last_name, date_of_birth, email, phone, "
                "hire_date, department_id, position_id, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (employee.first_name, employee.last_name, employee.date_of_birth,
                 employee.email, employee.phone, employee.hire_date,
                 employee.department_id, employee.position_id, employee.status),
            )
            new_id = cursor.lastrowid
        logger.info("Created employee #%s: %s", new_id, employee.full_name)
        return self.find_by_id(new_id)

    def find_by_id(self, employee_id: int) -> Employee:
        row = self._db.fetch_one("SELECT * FROM employees WHERE id = ?", (employee_id,))
        if row is None:
            raise RecordNotFoundException("Employee", employee_id)
        return self._to_model(row)

    def find_by_email(self, email: str) -> Employee | None:
        row = self._db.fetch_one("SELECT * FROM employees WHERE email = ?", (email,))
        return self._to_model(row) if row else None

    def all(self) -> list[Employee]:
        rows = self._db.fetch_all("SELECT * FROM employees ORDER BY last_name, first_name")
        return [self._to_model(r) for r in rows]

    def search(self, name_contains: str = None, department_id: int = None,
               status: str = None) -> list[Employee]:
        query = "SELECT * FROM employees WHERE 1=1"
        params: list = []

        if name_contains:
            query += " AND (first_name LIKE ? OR last_name LIKE ?)"
            like = f"%{name_contains}%"
            params += [like, like]
        if department_id is not None:
            query += " AND department_id = ?"
            params.append(department_id)
        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY last_name, first_name"
        rows = self._db.fetch_all(query, tuple(params))
        return [self._to_model(r) for r in rows]

    def update(self, employee: Employee) -> Employee:
        self.find_by_id(employee.employee_id)  # raises if missing
        with self._db.transaction() as db:
            db.execute(
                "UPDATE employees SET first_name=?, last_name=?, date_of_birth=?, email=?, "
                "phone=?, hire_date=?, department_id=?, position_id=?, status=? WHERE id=?",
                (employee.first_name, employee.last_name, employee.date_of_birth,
                 employee.email, employee.phone, employee.hire_date,
                 employee.department_id, employee.position_id, employee.status,
                 employee.employee_id),
            )
        logger.info("Updated employee #%s", employee.employee_id)
        return self.find_by_id(employee.employee_id)

    def delete(self, employee_id: int) -> None:
        self.find_by_id(employee_id)
        with self._db.transaction() as db:
            db.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
        logger.info("Deleted employee #%s", employee_id)

    def _to_model(self, row) -> Employee:
        return Employee(
            employee_id=row["id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            date_of_birth=row["date_of_birth"],
            email=row["email"],
            phone=row["phone"],
            hire_date=row["hire_date"],
            department_id=row["department_id"],
            position_id=row["position_id"],
            status=row["status"],
        )
