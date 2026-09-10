"""File-handling service: CSV and JSON import/export for Employee records.

Kept separate from EmployeeController so file-parsing concerns (encoding,
row-by-row error collection) don't leak into business-logic validation —
this service calls EmployeeController.add_employee() for each row, so
every imported record goes through the exact same validation and
permission checks as a manually entered one.
"""

import csv
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exceptions.custom_exceptions import EMSException  # noqa: E402
from utils.logger import get_logger  # noqa: E402

logger = get_logger("services.file_import")

REQUIRED_FIELDS = ["first_name", "last_name", "hire_date"]
OPTIONAL_FIELDS = ["date_of_birth", "email", "phone", "department_id", "position_id"]


class ImportResult:
    def __init__(self):
        self.created = []          # list of Employee
        self.errors = []           # list of (row_number, message)

    @property
    def success_count(self) -> int:
        return len(self.created)

    @property
    def error_count(self) -> int:
        return len(self.errors)


class FileImportService:
    def __init__(self, employee_controller):
        self._employees = employee_controller

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------
    def import_employees_csv(self, path: str) -> ImportResult:
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return self._import_rows(reader)

    def import_employees_json(self, path: str) -> ImportResult:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise EMSException("JSON import file must contain a list of employee objects.")
        return self._import_rows(data)

    def _import_rows(self, rows) -> ImportResult:
        result = ImportResult()
        for i, row in enumerate(rows, start=1):
            try:
                missing = [f for f in REQUIRED_FIELDS if not row.get(f)]
                if missing:
                    raise EMSException(f"missing required field(s): {', '.join(missing)}")

                department_id = row.get("department_id") or None
                position_id = row.get("position_id") or None
                employee = self._employees.add_employee(
                    first_name=row.get("first_name"),
                    last_name=row.get("last_name"),
                    date_of_birth=row.get("date_of_birth") or None,
                    email=row.get("email") or None,
                    phone=row.get("phone") or None,
                    hire_date=row.get("hire_date"),
                    department_id=int(department_id) if department_id else None,
                    position_id=int(position_id) if position_id else None,
                )
                result.created.append(employee)
            except Exception as e:  # noqa: BLE001 — a bad row must not abort the whole import
                logger.warning("Import row %d failed: %s", i, e)
                result.errors.append((i, str(e)))

        logger.info("Import finished: %d created, %d errors",
                    result.success_count, result.error_count)
        return result

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def export_employees_csv(self, path: str, employees) -> int:
        fieldnames = ["id", "first_name", "last_name", "date_of_birth", "email", "phone",
                      "hire_date", "department_id", "position_id", "status"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for e in employees:
                writer.writerow({
                    "id": e.employee_id, "first_name": e.first_name, "last_name": e.last_name,
                    "date_of_birth": e.date_of_birth or "", "email": e.email or "",
                    "phone": e.phone or "", "hire_date": e.hire_date,
                    "department_id": e.department_id or "", "position_id": e.position_id or "",
                    "status": e.status,
                })
        logger.info("Exported %d employees to %s", len(employees), path)
        return len(employees)

    def export_employees_json(self, path: str, employees) -> int:
        data = [{
            "id": e.employee_id, "first_name": e.first_name, "last_name": e.last_name,
            "date_of_birth": e.date_of_birth, "email": e.email, "phone": e.phone,
            "hire_date": e.hire_date, "department_id": e.department_id,
            "position_id": e.position_id, "status": e.status,
        } for e in employees]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info("Exported %d employees to %s", len(employees), path)
        return len(employees)
