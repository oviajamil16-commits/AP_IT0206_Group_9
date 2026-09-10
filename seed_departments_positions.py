"""
Seed script: adds Departments and Positions to the real application
database (database/app.db) using the app's own controllers, repositories
and validation -- exactly the same path the GUI/CLI menus use, so
anything created here is fully valid and payroll-ready.

Place this file in the PROJECT ROOT (the same folder that contains
src/, database/, etc.) and run it from there:

    python seed_departments_positions.py

You will be prompted to log in with an existing Administrator account
(department.create / position.create both require admin permissions).
That's the admin username/password that was printed to the console the
first time you ever ran `python main.py`.

Edit the DEPARTMENTS / POSITIONS lists below to match what you actually
need before running -- what's here is just a starting example.
"""

import getpass
import os
import sys

# Make src/ importable regardless of where this script is invoked from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
sys.path.insert(0, SRC_DIR)

import config  # noqa: E402
from repositories.database import DatabaseConnection  # noqa: E402
from repositories.department_repository import DepartmentRepository  # noqa: E402
from repositories.position_repository import PositionRepository  # noqa: E402
from repositories.user_repository import UserRepository  # noqa: E402
from services.auth_service import AuthService  # noqa: E402
from controllers.auth_controller import AuthController  # noqa: E402
from controllers.department_controller import DepartmentController  # noqa: E402
from controllers.position_controller import PositionController  # noqa: E402
from exceptions.custom_exceptions import EMSException, DuplicateRecordException  # noqa: E402

# ---------------------------------------------------------------------
# EDIT THESE to match the departments/positions you actually want.
# Each position must reference one of the department names listed below.
# base_salary_grade is a monthly base salary used directly by payroll.
# ---------------------------------------------------------------------
DEPARTMENTS = [
    "Engineering",
    "Human Resources",
    "Finance",
    "Sales",
]

POSITIONS = [
    # (title, department_name, base_salary_grade)
    ("Software Engineer", "Engineering", 3000.0),
    ("Senior Software Engineer", "Engineering", 4500.0),
    ("HR Officer", "Human Resources", 2500.0),
    ("Accountant", "Finance", 2800.0),
    ("Sales Executive", "Sales", 2200.0),
]
# ---------------------------------------------------------------------


def main():
    print(f"Using database: {config.DATABASE_PATH}")
    if not os.path.exists(config.DATABASE_PATH):
        print("ERROR: database/app.db not found. Run `python src/main.py` "
              "at least once first so the database is bootstrapped.")
        sys.exit(1)

    db = DatabaseConnection(config.DATABASE_PATH)
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)
    auth_controller = AuthController(auth_service)

    print("\nLog in with an Administrator account to seed data.")
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")
    try:
        auth_controller.login(username, password)
    except Exception as e:
        print(f"Login failed: {e}")
        sys.exit(1)
    print(f"Logged in as {auth_controller.current_user.username} "
          f"({auth_controller.current_user.role}).\n")

    dept_repo = DepartmentRepository(db)
    pos_repo = PositionRepository(db)
    dept_ctrl = DepartmentController(auth_controller, dept_repo)
    pos_ctrl = PositionController(auth_controller, pos_repo, dept_repo)

    # --- Departments -----------------------------------------------
    dept_ids = {}
    existing = {d.name: d.department_id for d in dept_ctrl.list_departments()}
    for name in DEPARTMENTS:
        if name in existing:
            print(f"[skip] Department already exists: {name} (id={existing[name]})")
            dept_ids[name] = existing[name]
            continue
        try:
            dept = dept_ctrl.add_department(name)
            dept_ids[name] = dept.department_id
            print(f"[created] Department: {name} (id={dept.department_id})")
        except (EMSException, DuplicateRecordException) as e:
            print(f"[error] Department '{name}': {e}")

    # --- Positions ---------------------------------------------------
    existing_positions = {(p.title, p.department_id) for p in pos_ctrl.list_positions()}
    for title, dept_name, salary in POSITIONS:
        dept_id = dept_ids.get(dept_name)
        if dept_id is None:
            print(f"[error] Position '{title}': department '{dept_name}' "
                  f"was not created, skipping.")
            continue
        if (title, dept_id) in existing_positions:
            print(f"[skip] Position already exists: {title} ({dept_name})")
            continue
        try:
            pos = pos_ctrl.add_position(title, dept_id, salary)
            print(f"[created] Position: {title} ({dept_name}), "
                  f"base salary {pos.base_salary_grade} (id={pos.position_id})")
        except (EMSException, DuplicateRecordException) as e:
            print(f"[error] Position '{title}': {e}")

    print("\nDone. You can now assign these positions to employees "
          "(Employee menu -> add/edit) and payroll will pick up the "
          "base salary automatically.")


if __name__ == "__main__":
    main()
