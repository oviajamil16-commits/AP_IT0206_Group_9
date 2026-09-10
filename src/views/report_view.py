"""Console presentation layer for Reports."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exceptions.custom_exceptions import EMSException  # noqa: E402


class ReportView:
    def __init__(self, report_controller, holiday_service):
        self._reports = report_controller
        self._holidays = holiday_service

    def run(self) -> None:
        while True:
            choice = self._show_menu()
            try:
                if choice == "1":
                    self._headcount_flow()
                elif choice == "2":
                    self._payroll_summary_flow()
                elif choice == "3":
                    self._attendance_summary_flow()
                elif choice == "4":
                    self._holiday_check_flow()
                elif choice == "0":
                    return
                else:
                    print("Invalid selection.\n")
            except PermissionError as e:
                print(f"\n[Access denied] {e}\n")
            except EMSException as e:
                print(f"\n[Error] {e}\n")

    def _show_menu(self) -> str:
        print("-" * 50)
        print("  REPORTS".center(50))
        print("-" * 50)
        print("  1. Headcount by department")
        print("  2. Payroll cost summary for a period")
        print("  3. Attendance summary")
        print("  4. Check public holidays (external API)")
        print("  0. Back to main menu")
        return input("Select an option: ").strip()

    def _headcount_flow(self) -> None:
        counts, chart_path = self._reports.headcount_by_department()
        if counts.empty:
            print("\nNo employees to report on yet.\n")
            return
        print()
        for department, count in counts.items():
            print(f"  {department:<20} {count}")
        print(f"\nChart saved to: {chart_path}\n")

    def _payroll_summary_flow(self) -> None:
        period = input("Period (YYYY-MM): ").strip()
        total, average, count, chart_path = self._reports.payroll_cost_summary(period)
        if count == 0:
            print(f"\nNo payroll records found for {period}.\n")
            return
        print(f"\n{count} employee(s) paid in {period}")
        print(f"  Total net pay:   {total:.2f}")
        print(f"  Average net pay: {average:.2f}")
        print(f"\nChart saved to: {chart_path}\n")

    def _attendance_summary_flow(self) -> None:
        counts, chart_path = self._reports.attendance_summary()
        if counts.empty:
            print("\nNo attendance records to report on yet.\n")
            return
        print()
        for status, count in counts.items():
            print(f"  {status:<12} {count}")
        print(f"\nChart saved to: {chart_path}\n")

    def _holiday_check_flow(self) -> None:
        year = input("Year (e.g. 2026): ").strip()
        print("\nContacting the public holiday service (requires internet access)...")
        holidays = self._holidays.get_holidays(int(year))
        if not holidays:
            print("Couldn't retrieve public holidays right now \u2014 no internet access, "
                  "or the service is unavailable. This is non-fatal; try again later.\n")
            return
        print(f"\nPublic holidays for {year}:")
        for h in holidays:
            print(f"  {h['date']}  {h['name']}")
        print()
