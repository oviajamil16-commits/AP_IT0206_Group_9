"""Employee Management System — application entry point.

Wires up: database schema, auth/login, Employee/Department/Position CRUD,
Attendance, Leave (with approval workflow), Payroll (leave -> deduction),
Reports (pandas/matplotlib), CSV/JSON import-export, and an external
public-holiday lookup (requests) via the Reports menu.
"""

import os
import secrets
import sys

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
from services.file_service import FileImportService  # noqa: E402
from services.holiday_service import HolidayService  # noqa: E402
from controllers.auth_controller import AuthController  # noqa: E402
from controllers.employee_controller import EmployeeController  # noqa: E402
from controllers.department_controller import DepartmentController  # noqa: E402
from controllers.position_controller import PositionController  # noqa: E402
from controllers.attendance_controller import AttendanceController  # noqa: E402
from controllers.leave_controller import LeaveController  # noqa: E402
from controllers.payroll_controller import PayrollController  # noqa: E402
from controllers.report_controller import ReportController  # noqa: E402
from views.login_view import LoginView  # noqa: E402
from views.main_menu_view import MainMenuView  # noqa: E402
from views.employee_view import EmployeeView  # noqa: E402
from views.attendance_view import AttendanceView  # noqa: E402
from views.leave_view import LeaveView  # noqa: E402
from views.payroll_view import PayrollView  # noqa: E402
from views.report_view import ReportView  # noqa: E402
from exceptions.custom_exceptions import InvalidCredentialsException, EMSException  # noqa: E402
from utils.logger import get_logger  # noqa: E402

logger = get_logger("main")


def bootstrap(db: DatabaseConnection, user_repo: UserRepository) -> None:
    """First-run setup: create the schema, and seed a default admin
    account if no users exist yet."""
    db.initialise_schema()

    if user_repo.count() == 0:
        generated_password = secrets.token_urlsafe(9)  # readable, ~12 chars
        password_hash = AuthService.hash_password(generated_password)
        user_repo.create(
            username=config.DEFAULT_ADMIN_USERNAME,
            password_hash=password_hash,
            role=config.ROLE_ADMIN,
        )
        print("\nNo users found — created a default administrator account:")
        print(f"    username: {config.DEFAULT_ADMIN_USERNAME}")
        print(f"    password: {generated_password}")
        print("Change this password via user management once that module exists.\n")
        logger.info("Seeded default admin account on first run")


def run_login(login_view: LoginView, auth_controller: AuthController):
    login_view.show_banner()
    attempts_left = config.MAX_LOGIN_ATTEMPTS

    while attempts_left > 0:
        username, password = login_view.prompt_credentials()
        try:
            user = auth_controller.login(username, password)
            login_view.show_welcome(user.username, user.role)
            return user
        except InvalidCredentialsException as e:
            attempts_left -= 1
            login_view.show_error(str(e))
            login_view.show_attempts_remaining(attempts_left)

    login_view.show_lockout()
    return None


def run_main_menu(menu_view: MainMenuView, auth_controller: AuthController, views: dict) -> None:
    while True:
        choice = menu_view.show_menu(auth_controller.current_user.role)
        if choice == "0":
            auth_controller.logout()
            print("Logged out.\n")
            return
        elif choice in views:
            views[choice].run()
        else:
            print("Invalid selection — please choose a number from the menu.\n")


def main() -> None:
    db = DatabaseConnection()
    try:
        user_repo = UserRepository(db)
        bootstrap(db, user_repo)

        employee_repo = EmployeeRepository(db)
        department_repo = DepartmentRepository(db)
        position_repo = PositionRepository(db)
        attendance_repo = AttendanceRepository(db)
        leave_repo = LeaveRepository(db)
        payroll_repo = PayrollRepository(db)

        auth_service = AuthService(user_repo)
        auth_controller = AuthController(auth_service)

        employee_controller = EmployeeController(
            auth_controller, employee_repo, department_repo, position_repo
        )
        department_controller = DepartmentController(auth_controller, department_repo)
        position_controller = PositionController(auth_controller, position_repo, department_repo)
        attendance_controller = AttendanceController(auth_controller, attendance_repo, employee_repo)
        leave_controller = LeaveController(auth_controller, leave_repo, employee_repo)
        payroll_controller = PayrollController(
            auth_controller, payroll_repo, employee_repo, position_repo, leave_repo
        )
        report_controller = ReportController(
            auth_controller, employee_repo, department_repo, payroll_repo, attendance_repo,
            output_dir=config.DATA_EXPORTS_DIR,
        )

        file_import_service = FileImportService(employee_controller)
        holiday_service = HolidayService(country_code="AU")

        login_view = LoginView()
        menu_view = MainMenuView()
        employee_view = EmployeeView(
            employee_controller, department_controller, position_controller, file_import_service
        )
        attendance_view = AttendanceView(attendance_controller)
        leave_view = LeaveView(leave_controller)
        payroll_view = PayrollView(payroll_controller)
        report_view = ReportView(report_controller, holiday_service)

        views = {
            "1": employee_view,
            "2": attendance_view,
            "3": leave_view,
            "4": payroll_view,
            "5": report_view,
        }

        user = run_login(login_view, auth_controller)
        if user is not None:
            run_main_menu(menu_view, auth_controller, views)

    except EMSException as e:
        logger.exception("Unhandled application error")
        print(f"\nAn application error occurred: {e}")
    except KeyboardInterrupt:
        print("\n\nInterrupted — exiting.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
