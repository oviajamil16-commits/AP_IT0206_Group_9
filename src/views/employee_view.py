"""Console presentation layer for Employee management. No business logic
or database access — only prompts, input capture, and formatted output.
Errors raised by the controller layer are caught and displayed here."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exceptions.custom_exceptions import EMSException  # noqa: E402


class EmployeeView:
    def __init__(self, employee_controller, department_controller, position_controller,
                 file_import_service=None):
        self._employees = employee_controller
        self._departments = department_controller
        self._positions = position_controller
        self._files = file_import_service

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        while True:
            choice = self._show_menu()
            try:
                if choice == "1":
                    self._add_employee_flow()
                elif choice == "2":
                    self._list_employees_flow()
                elif choice == "3":
                    self._search_employees_flow()
                elif choice == "4":
                    self._update_employee_flow()
                elif choice == "5":
                    self._delete_employee_flow()
                elif choice == "6":
                    self._manage_departments_flow()
                elif choice == "7":
                    self._manage_positions_flow()
                elif choice == "8":
                    self._import_flow()
                elif choice == "9":
                    self._export_flow()
                elif choice == "0":
                    return
                else:
                    print("Invalid selection.\n")
            except PermissionError as e:
                print(f"\n[Access denied] {e}\n")
            except EMSException as e:
                print(f"\n[Error] {e}\n")
            except ValueError:
                print("\n[Error] Please enter a valid number where an id is expected.\n")
            except (FileNotFoundError, OSError) as e:
                print(f"\n[Error] Could not access that file: {e}\n")

    def _show_menu(self) -> str:
        print("-" * 50)
        print("  EMPLOYEE MANAGEMENT".center(50))
        print("-" * 50)
        print("  1. Add employee")
        print("  2. List all employees")
        print("  3. Search employees")
        print("  4. Update employee")
        print("  5. Delete employee")
        print("  6. Manage departments")
        print("  7. Manage positions")
        print("  8. Import employees from file (CSV/JSON)")
        print("  9. Export employees to file (CSV/JSON)")
        print("  0. Back to main menu")
        return input("Select an option: ").strip()

    # ------------------------------------------------------------------
    # Add
    # ------------------------------------------------------------------
    def _add_employee_flow(self) -> None:
        print("\n-- Add employee --")
        first_name = input("First name: ")
        last_name = input("Last name: ")
        dob = input("Date of birth (YYYY-MM-DD, optional): ").strip() or None
        email = input("Email (optional): ").strip() or None
        phone = input("Phone (optional): ").strip() or None
        hire_date = input("Hire date (YYYY-MM-DD): ").strip()
        department_id = self._choose_department()
        position_id = self._choose_position(department_id)

        employee = self._employees.add_employee(
            first_name, last_name, dob, email, phone, hire_date, department_id, position_id
        )
        print(f"\nCreated employee #{employee.employee_id}: {employee.full_name}\n")

    def _choose_department(self):
        departments = self._departments.list_departments()
        if not departments:
            print("(No departments exist yet — use 'Manage departments' to add one first.)")
            return None
        print("\nAvailable departments:")
        for d in departments:
            print(f"  {d.department_id}. {d.name}")
        raw = input("Department id (blank to skip): ").strip()
        return int(raw) if raw else None

    def _choose_position(self, department_id):
        positions = self._positions.list_positions()
        if department_id is not None:
            positions = [p for p in positions if p.department_id == department_id]
        if not positions:
            print("(No matching positions exist yet — use 'Manage positions' to add one first.)")
            return None
        print("\nAvailable positions:")
        for p in positions:
            print(f"  {p.position_id}. {p.title}")
        raw = input("Position id (blank to skip): ").strip()
        return int(raw) if raw else None

    # ------------------------------------------------------------------
    # List / search
    # ------------------------------------------------------------------
    def _list_employees_flow(self) -> None:
        employees = self._employees.list_employees()
        self._print_employee_table(employees)

    def _search_employees_flow(self) -> None:
        print("\n-- Search employees (leave any field blank to skip it) --")
        name = input("Name contains: ").strip() or None
        status = input("Status [active/inactive/terminated]: ").strip() or None
        department_id = self._choose_department()
        results = self._employees.search_employees(
            name_contains=name, department_id=department_id, status=status
        )
        self._print_employee_table(results)

    def _print_employee_table(self, employees) -> None:
        if not employees:
            print("\nNo employees found.\n")
            return
        print(f"\n{'ID':<5}{'Name':<25}{'Status':<12}{'Hire date':<12}{'Dept':<6}{'Pos':<6}")
        print("-" * 66)
        for e in employees:
            print(
                f"{e.employee_id:<5}{e.full_name:<25}{e.status:<12}{e.hire_date:<12}"
                f"{str(e.department_id or '-'):<6}{str(e.position_id or '-'):<6}"
            )
        print()

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def _update_employee_flow(self) -> None:
        employee_id = int(input("Employee id to update: ").strip())
        current = self._employees.get_employee(employee_id)
        print(f"Updating {current.full_name} — leave a field blank to keep its current value.")
        first_name = input(f"First name [{current.first_name}]: ").strip() or None
        last_name = input(f"Last name [{current.last_name}]: ").strip() or None
        email = input(f"Email [{current.email or '-'}]: ").strip() or None
        phone = input(f"Phone [{current.phone or '-'}]: ").strip() or None
        status = input(f"Status [{current.status}]: ").strip() or None

        updated = self._employees.update_employee(
            employee_id, first_name=first_name, last_name=last_name,
            email=email, phone=phone, status=status,
        )
        print(f"\nUpdated employee #{updated.employee_id}: {updated.full_name}\n")

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------
    def _delete_employee_flow(self) -> None:
        employee_id = int(input("Employee id to delete: ").strip())
        employee = self._employees.get_employee(employee_id)
        confirm = input(f"Type 'yes' to confirm deleting {employee.full_name}: ").strip().lower()
        if confirm == "yes":
            self._employees.delete_employee(employee_id)
            print("Employee deleted.\n")
        else:
            print("Cancelled.\n")

    # ------------------------------------------------------------------
    # Department / position sub-management
    # ------------------------------------------------------------------
    def _manage_departments_flow(self) -> None:
        while True:
            print("\n-- Departments --")
            print("  1. Add department")
            print("  2. List departments")
            print("  3. Delete department")
            print("  0. Back")
            choice = input("Select an option: ").strip()
            try:
                if choice == "1":
                    name = input("Department name: ").strip()
                    dept = self._departments.add_department(name)
                    print(f"Created department #{dept.department_id}: {dept.name}")
                elif choice == "2":
                    for d in self._departments.list_departments():
                        print(f"  {d.department_id}. {d.name}")
                elif choice == "3":
                    dept_id = int(input("Department id to delete: ").strip())
                    self._departments.delete_department(dept_id)
                    print("Department deleted.")
                elif choice == "0":
                    return
                else:
                    print("Invalid selection.")
            except PermissionError as e:
                print(f"[Access denied] {e}")
            except EMSException as e:
                print(f"[Error] {e}")

    def _manage_positions_flow(self) -> None:
        while True:
            print("\n-- Positions --")
            print("  1. Add position")
            print("  2. List positions")
            print("  3. Delete position")
            print("  0. Back")
            choice = input("Select an option: ").strip()
            try:
                if choice == "1":
                    title = input("Position title: ").strip()
                    department_id = self._choose_department()
                    if department_id is None:
                        print("A position must belong to a department — add one first.")
                        continue
                    grade_raw = input("Base salary grade (number): ").strip()
                    position = self._positions.add_position(title, department_id, grade_raw)
                    print(f"Created position #{position.position_id}: {position.title}")
                elif choice == "2":
                    for p in self._positions.list_positions():
                        print(f"  {p.position_id}. {p.title} (dept {p.department_id})")
                elif choice == "3":
                    pos_id = int(input("Position id to delete: ").strip())
                    self._positions.delete_position(pos_id)
                    print("Position deleted.")
                elif choice == "0":
                    return
                else:
                    print("Invalid selection.")
            except PermissionError as e:
                print(f"[Access denied] {e}")
            except EMSException as e:
                print(f"[Error] {e}")

    # ------------------------------------------------------------------
    # Import / export
    # ------------------------------------------------------------------
    def _import_flow(self) -> None:
        if self._files is None:
            print("\nImport/export is not available in this session.\n")
            return
        path = input("Path to CSV or JSON file: ").strip()
        if path.lower().endswith(".json"):
            result = self._files.import_employees_json(path)
        else:
            result = self._files.import_employees_csv(path)

        print(f"\nImport finished: {result.success_count} created, {result.error_count} error(s).")
        for row_num, message in result.errors:
            print(f"  row {row_num}: {message}")
        print()

    def _export_flow(self) -> None:
        if self._files is None:
            print("\nImport/export is not available in this session.\n")
            return
        path = input("Path to write (.csv or .json): ").strip()
        employees = self._employees.list_employees()
        if path.lower().endswith(".json"):
            count = self._files.export_employees_json(path, employees)
        else:
            count = self._files.export_employees_csv(path, employees)
        print(f"\nExported {count} employee(s) to {path}\n")
