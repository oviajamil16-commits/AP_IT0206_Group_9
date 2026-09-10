"""Employee Management System — GRAPHICAL entry point.

Wires up the exact same database, repositories, services, and
controllers as main.py (the console version). The ONLY difference is
the presentation layer: this launches the Tkinter App (src/gui/) instead
of the console login/menu loop. Every business rule, validation, and
permission check is identical because it's the same Controller code
either way — that's the point of keeping Views separate from everything
else.
"""

import os
import secrets
import sys
import tkinter as tk
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config  # noqa: E402
from repositories.database import DatabaseConnection  # noqa: E402
from repositories.user_repository import UserRepository  # noqa: E402
from repositories.employee_repository import EmployeeRepository  # noqa: E402
from repositories.department_repository import DepartmentRepository  # noqa: E402
from repositories.position_repository import PositionRepository  # noqa: E402
from repositories.attendance_repository import AttendanceRepository  # noqa: E402
from repositories.leave_repository import LeaveRepository  # noqa: E402
from repositories.payroll_repository import PayrollRepository  # noqa: E402
from services.auth_service import AuthService  # noqa: E402
from controllers.auth_controller import AuthController  # noqa: E402
from controllers.employee_controller import EmployeeController  # noqa: E402
from controllers.department_controller import DepartmentController  # noqa: E402
from controllers.position_controller import PositionController  # noqa: E402
from controllers.attendance_controller import AttendanceController  # noqa: E402
from controllers.leave_controller import LeaveController  # noqa: E402
from controllers.payroll_controller import PayrollController  # noqa: E402
from controllers.report_controller import ReportController  # noqa: E402
from gui.app import App  # noqa: E402
from utils.logger import get_logger  # noqa: E402

logger = get_logger("gui_main")


def bootstrap(db: DatabaseConnection, user_repo: UserRepository) -> None:
    """Identical to main.py's bootstrap: create schema, seed a default
    admin on first run. Uses a messagebox instead of print() since
    there's no console to print to once the GUI is running."""
    db.initialise_schema()

    if user_repo.count() == 0:
        generated_password = secrets.token_urlsafe(9)
        password_hash = AuthService.hash_password(generated_password)
        user_repo.create(
            username=config.DEFAULT_ADMIN_USERNAME,
            password_hash=password_hash,
            role=config.ROLE_ADMIN,
        )
        logger.info("Seeded default admin account on first run")
        messagebox.showinfo(
            "First-run setup",
            "No users found — created a default administrator account:\n\n"
            f"Username: {config.DEFAULT_ADMIN_USERNAME}\n"
            f"Password: {generated_password}\n\n"
            "Write this down — it will not be shown again.",
        )


def main() -> None:
    db = DatabaseConnection()
    try:
        user_repo = UserRepository(db)

        # bootstrap() needs a Tk root to show the messagebox, so create
        # a hidden root first, run bootstrap, then hand it to App.
        root_holder = tk.Tk()
        root_holder.withdraw()
        bootstrap(db, user_repo)
        root_holder.destroy()

        employee_repo = EmployeeRepository(db)
        department_repo = DepartmentRepository(db)
        position_repo = PositionRepository(db)
        attendance_repo = AttendanceRepository(db)
        leave_repo = LeaveRepository(db)
        payroll_repo = PayrollRepository(db)

        auth_service = AuthService(user_repo)
        auth_controller = AuthController(auth_service)

        controllers = {
            "auth": auth_controller,
            "employee": EmployeeController(auth_controller, employee_repo, department_repo, position_repo),
            "department": DepartmentController(auth_controller, department_repo),
            "position": PositionController(auth_controller, position_repo, department_repo),
            "attendance": AttendanceController(auth_controller, attendance_repo, employee_repo),
            "leave": LeaveController(auth_controller, leave_repo, employee_repo),
            "payroll": PayrollController(auth_controller, payroll_repo, employee_repo, position_repo, leave_repo),
            "report": ReportController(auth_controller, employee_repo, department_repo, payroll_repo,
                                        attendance_repo, output_dir=config.DATA_EXPORTS_DIR),
        }

        app = App(controllers)
        app.mainloop()

    except Exception:
        logger.exception("Unhandled application error")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
