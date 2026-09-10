"""Console presentation layer for Attendance."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exceptions.custom_exceptions import EMSException  # noqa: E402
from models.attendance import Attendance  # noqa: E402


class AttendanceView:
    def __init__(self, attendance_controller):
        self._attendance = attendance_controller

    def run(self) -> None:
        while True:
            choice = self._show_menu()
            try:
                if choice == "1":
                    self._clock_in_flow()
                elif choice == "2":
                    self._clock_out_flow()
                elif choice == "3":
                    self._mark_absent_flow()
                elif choice == "4":
                    self._view_by_employee_flow()
                elif choice == "5":
                    self._view_by_date_flow()
                elif choice == "6":
                    self._edit_record_flow()
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
        print("  ATTENDANCE".center(50))
        print("-" * 50)
        print("  1. Clock in")
        print("  2. Clock out")
        print("  3. Mark absent")
        print("  4. View attendance for an employee")
        print("  5. View attendance for a date")
        print("  6. Edit an attendance record")
        print("  0. Back to main menu")
        return input("Select an option: ").strip()

    def _clock_in_flow(self) -> None:
        employee_id = int(input("Employee id: ").strip())
        date = input("Date (YYYY-MM-DD, blank for today): ").strip() or None
        time_in = input("Time in (HH:MM, blank for now): ").strip() or None
        record = self._attendance.clock_in(employee_id, date, time_in)
        print(f"\nClocked in: employee #{record.employee_id} on {record.date} at {record.time_in}\n")

    def _clock_out_flow(self) -> None:
        employee_id = int(input("Employee id: ").strip())
        date = input("Date (YYYY-MM-DD, blank for today): ").strip() or None
        time_out = input("Time out (HH:MM, blank for now): ").strip() or None
        record = self._attendance.clock_out(employee_id, date, time_out)
        hours = record.hours_worked
        print(f"\nClocked out: {record.time_in} \u2192 {record.time_out}"
              f"{f' ({hours} hours)' if hours is not None else ''}\n")

    def _mark_absent_flow(self) -> None:
        employee_id = int(input("Employee id: ").strip())
        date = input("Date (YYYY-MM-DD): ").strip()
        self._attendance.mark_absent(employee_id, date)
        print(f"\nMarked employee #{employee_id} absent on {date}\n")

    def _view_by_employee_flow(self) -> None:
        employee_id = int(input("Employee id: ").strip())
        records = self._attendance.get_by_employee(employee_id)
        self._print_table(records)

    def _view_by_date_flow(self) -> None:
        date = input("Date (YYYY-MM-DD): ").strip()
        records = self._attendance.get_by_date(date)
        self._print_table(records)

    def _print_table(self, records) -> None:
        if not records:
            print("\nNo attendance records found.\n")
            return
        print(f"\n{'ID':<5}{'Employee':<10}{'Date':<12}{'In':<8}{'Out':<8}{'Hours':<8}{'Status':<10}")
        print("-" * 61)
        for r in records:
            hours = r.hours_worked
            print(f"{r.attendance_id:<5}{r.employee_id:<10}{r.date:<12}"
                  f"{(r.time_in or '-'):<8}{(r.time_out or '-'):<8}"
                  f"{(str(hours) if hours is not None else '-'):<8}{r.status:<10}")
        print()
    def _edit_record_flow(self) -> None:
        attendance_id = int(input("Attendance record id to edit: ").strip())
        current = self._attendance.get_by_id(attendance_id)
        print(f"\nCurrent record: date={current.date}  in={current.time_in or '-'}  "
              f"out={current.time_out or '-'}  status={current.status}")
        print("Press Enter on any field to leave it unchanged.\n")

        date = input(f"New date [{current.date}]: ").strip() or None
        time_in = input(f"New time in [{current.time_in or '-'}]: ").strip() or None
        time_out_raw = input(f"New time out [{current.time_out or '-'}] "
                              f"(type 'clear' to remove it): ").strip()
        clear_time_out = time_out_raw.lower() == "clear"
        time_out = None if clear_time_out or not time_out_raw else time_out_raw
        status = input(f"New status {sorted(Attendance.STATUSES)} "
                       f"[{current.status}]: ").strip() or None

        updated = self._attendance.edit_attendance(
            attendance_id, date=date, time_in=time_in, time_out=time_out,
            status=status, clear_time_out=clear_time_out,
        )
        print(f"\nUpdated: date={updated.date}  in={updated.time_in or '-'}  "
              f"out={updated.time_out or '-'}  status={updated.status}\n")
