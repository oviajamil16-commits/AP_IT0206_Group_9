"""Console presentation layer for Leave requests."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exceptions.custom_exceptions import EMSException  # noqa: E402


class LeaveView:
    def __init__(self, leave_controller):
        self._leave = leave_controller

    def run(self) -> None:
        while True:
            choice = self._show_menu()
            try:
                if choice == "1":
                    self._submit_flow()
                elif choice == "2":
                    self._list_flow()
                elif choice == "3":
                    self._approve_flow()
                elif choice == "4":
                    self._reject_flow()
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
        print("  LEAVE REQUESTS".center(50))
        print("-" * 50)
        print("  1. Submit leave request")
        print("  2. List leave requests")
        print("  3. Approve leave request")
        print("  4. Reject leave request")
        print("  0. Back to main menu")
        return input("Select an option: ").strip()

    def _submit_flow(self) -> None:
        employee_id = int(input("Employee id: ").strip())
        print("Leave type [annual/sick/unpaid/other]:")
        leave_type = input("> ").strip()
        start_date = input("Start date (YYYY-MM-DD): ").strip()
        end_date = input("End date (YYYY-MM-DD): ").strip()
        leave = self._leave.submit_leave(employee_id, leave_type, start_date, end_date)
        print(f"\nSubmitted leave request #{leave.leave_id} "
              f"({leave.duration_days} day(s), status: {leave.status})\n")

    def _list_flow(self) -> None:
        status = input("Filter by status [pending/approved/rejected] (blank for all): ").strip() or None
        leaves = self._leave.list_by_status(status)
        self._print_table(leaves)

    def _approve_flow(self) -> None:
        leave_id = int(input("Leave request id to approve: ").strip())
        leave = self._leave.approve_leave(leave_id)
        print(f"\nApproved leave request #{leave.leave_id}\n")

    def _reject_flow(self) -> None:
        leave_id = int(input("Leave request id to reject: ").strip())
        leave = self._leave.reject_leave(leave_id)
        print(f"\nRejected leave request #{leave.leave_id}\n")

    def _print_table(self, leaves) -> None:
        if not leaves:
            print("\nNo leave requests found.\n")
            return
        print(f"\n{'ID':<5}{'Employee':<10}{'Type':<10}{'Start':<12}{'End':<12}{'Days':<6}{'Status':<10}")
        print("-" * 65)
        for l in leaves:
            print(f"{l.leave_id:<5}{l.employee_id:<10}{l.leave_type:<10}{l.start_date:<12}"
                  f"{l.end_date:<12}{l.duration_days:<6}{l.status:<10}")
        print()
