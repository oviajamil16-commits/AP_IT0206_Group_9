"""Console presentation layer for Payroll."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exceptions.custom_exceptions import EMSException  # noqa: E402


class PayrollView:
    def __init__(self, payroll_controller):
        self._payroll = payroll_controller

    def run(self) -> None:
        while True:
            choice = self._show_menu()
            try:
                if choice == "1":
                    self._run_payroll_flow()
                elif choice == "2":
                    self._view_payslip_flow()
                elif choice == "3":
                    self._list_by_period_flow()
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

    def _show_menu(self) -> str:
        print("-" * 50)
        print("  PAYROLL".center(50))
        print("-" * 50)
        print("  1. Run payroll for a period")
        print("  2. View a payslip")
        print("  3. List payroll for a period")
        print("  0. Back to main menu")
        return input("Select an option: ").strip()

    def _run_payroll_flow(self) -> None:
        period = input("Period (YYYY-MM): ").strip()
        result = self._payroll.run_payroll(period)
        print(f"\nPayroll run complete for {period}: "
              f"{len(result.created)} payslip(s) created, {len(result.skipped)} skipped.")
        for p in result.created:
            print(f"  Employee #{p.employee_id}: base={p.base_salary:.2f}, "
                  f"deductions={p.deductions:.2f}, net_pay={p.net_pay:.2f}")
        for employee_id, reason in result.skipped:
            print(f"  Employee #{employee_id}: skipped ({reason})")
        print()

    def _view_payslip_flow(self) -> None:
        employee_id = int(input("Employee id: ").strip())
        period = input("Period (YYYY-MM): ").strip()
        payslip = self._payroll.get_payslip(employee_id, period)
        print(f"\n--- Payslip: employee #{payslip.employee_id}, {payslip.period} ---")
        print(f"  Base salary:  {payslip.base_salary:>10.2f}")
        print(f"  Allowances:   {payslip.allowances:>10.2f}")
        print(f"  Deductions:   {payslip.deductions:>10.2f}")
        print(f"  Net pay:      {payslip.net_pay:>10.2f}")
        print(f"  Generated:    {payslip.generated_date}\n")

    def _list_by_period_flow(self) -> None:
        period = input("Period (YYYY-MM): ").strip()
        records = self._payroll.list_by_period(period)
        if not records:
            print("\nNo payroll records found for this period.\n")
            return
        print(f"\n{'Employee':<10}{'Base':<10}{'Allow.':<10}{'Deduct.':<10}{'Net pay':<10}")
        print("-" * 50)
        total = 0.0
        for p in records:
            print(f"{p.employee_id:<10}{p.base_salary:<10.2f}{p.allowances:<10.2f}"
                  f"{p.deductions:<10.2f}{p.net_pay:<10.2f}")
            total += p.net_pay
        print("-" * 50)
        print(f"{'Total net pay:':<40}{total:.2f}\n")
