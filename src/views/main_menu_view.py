"""Main menu shell. Routes to each feature module's own view."""


class MainMenuView:
    def show_menu(self, role: str) -> str:
        print("=" * 50)
        print(f"  MAIN MENU  (role: {role})".center(50))
        print("=" * 50)
        print("  1. Employees")
        print("  2. Attendance")
        print("  3. Leave requests")
        print("  4. Payroll")
        print("  5. Reports")
        print("  0. Log out")
        return input("Select an option: ").strip()
