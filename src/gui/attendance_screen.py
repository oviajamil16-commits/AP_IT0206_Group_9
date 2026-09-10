"""Attendance screen — calls AttendanceController exactly as the
console AttendanceView does."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from gui.styles import NAVY, WHITE, LIGHT_BG, DARK_TEXT, FONT_HEADER, FONT_BODY, FONT_BODY_BOLD, GOLD
from exceptions.custom_exceptions import EMSException


class AttendanceScreen(tk.Frame):
    def __init__(self, parent, controllers, user):
        super().__init__(parent, bg=LIGHT_BG)
        self.att_ctrl = controllers["attendance"]
        self.emp_ctrl = controllers["employee"]

        self._build_header()
        self._build_table()
        self.refresh()

    def _build_header(self):
        header = tk.Frame(self, bg=LIGHT_BG)
        header.pack(fill="x", pady=(0, 16))
        tk.Label(header, text="Attendance", font=FONT_HEADER, bg=LIGHT_BG, fg=NAVY).pack(side="left")

        form = tk.Frame(self, bg=LIGHT_BG)
        form.pack(fill="x", pady=(0, 12))

        tk.Label(form, text="Employee ID:", font=FONT_BODY, bg=LIGHT_BG).pack(side="left")
        self.emp_id_entry = ttk.Entry(form, width=6)
        self.emp_id_entry.pack(side="left", padx=(4, 12))

        tk.Label(form, text="Date:", font=FONT_BODY, bg=LIGHT_BG).pack(side="left")
        self.date_entry = ttk.Entry(form, width=12)
        self.date_entry.insert(0, date.today().isoformat())
        self.date_entry.pack(side="left", padx=(4, 12))

        tk.Label(form, text="Time (HH:MM):", font=FONT_BODY, bg=LIGHT_BG).pack(side="left")
        self.time_entry = ttk.Entry(form, width=8)
        self.time_entry.pack(side="left", padx=(4, 12))

        tk.Button(form, text="Clock In", font=FONT_BODY_BOLD, bg=NAVY, fg=WHITE, relief="flat",
                  padx=10, pady=4, cursor="hand2", command=self._clock_in).pack(side="left", padx=(0, 6))
        tk.Button(form, text="Clock Out", font=FONT_BODY_BOLD, bg=NAVY, fg=WHITE, relief="flat",
                  padx=10, pady=4, cursor="hand2", command=self._clock_out).pack(side="left", padx=(0, 6))
        tk.Button(form, text="Mark Absent", font=FONT_BODY, bg=WHITE, fg="#A94442", relief="solid",
                  bd=1, padx=10, pady=4, cursor="hand2", command=self._mark_absent).pack(side="left")

        # A second row: filter the table below by the Employee ID or Date
        # fields above, using AttendanceController.get_by_employee() /
        # get_by_date() -- both already existed but nothing in the GUI
        # called them, so the table only ever showed every record.
        filter_row = tk.Frame(self, bg=LIGHT_BG)
        filter_row.pack(fill="x", pady=(0, 12))
        tk.Button(filter_row, text="View by Employee", font=FONT_BODY, bg=WHITE, fg=NAVY,
                  relief="solid", bd=1, padx=10, pady=4, cursor="hand2",
                  command=self._filter_by_employee).pack(side="left", padx=(0, 6))
        tk.Button(filter_row, text="View by Date", font=FONT_BODY, bg=WHITE, fg=NAVY,
                  relief="solid", bd=1, padx=10, pady=4, cursor="hand2",
                  command=self._filter_by_date).pack(side="left", padx=(0, 6))
        tk.Button(filter_row, text="Show All", font=FONT_BODY, bg=WHITE, fg=NAVY,
                  relief="solid", bd=1, padx=10, pady=4, cursor="hand2",
                  command=self._show_all).pack(side="left", padx=(0, 6))
        tk.Button(filter_row, text="Refresh", font=FONT_BODY, bg=WHITE, fg=NAVY,
                  relief="solid", bd=1, padx=10, pady=4, cursor="hand2",
                  command=self.refresh).pack(side="left", padx=(0, 6))
        tk.Button(filter_row, text="Delete Selected", font=FONT_BODY, bg=WHITE, fg="#A94442",
                  relief="solid", bd=1, padx=10, pady=4, cursor="hand2",
                  command=self._delete_selected).pack(side="left")

        self.error_label = tk.Label(self, text="", font=FONT_BODY, bg=LIGHT_BG, fg="#A94442")
        self.error_label.pack(anchor="w", pady=(0, 8))

    def _build_table(self):
        columns = ("id", "employee_id", "date", "time_in", "time_out", "status", "hours")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=16)
        headings = {"id": "ID", "employee_id": "Emp ID", "date": "Date", "time_in": "Time In",
                    "time_out": "Time Out", "status": "Status", "hours": "Hours Worked"}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=110, anchor="w")
        self.tree.pack(fill="both", expand=True)

        # Row highlighting by status: light tint background + the shared
        # SUCCESS/DANGER colour for the text, so present/absent stand out
        # at a glance without hurting readability.
        self.tree.tag_configure("present", background="#C8E6C9", foreground=DARK_TEXT)
        self.tree.tag_configure("absent", background="#F8D7DA", foreground=DARK_TEXT)
        self.tree.tag_configure("late", background="#FCF3DC", foreground=GOLD)

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        records = self._current_records()
        for r in records:
            status = (r.status or "").lower()
            tag = status if status in ("present", "absent", "late") else ""
            self.tree.insert("", "end", values=(
                r.attendance_id, r.employee_id, r.date, r.time_in or "-", r.time_out or "-",
                r.status, r.hours_worked if r.hours_worked is not None else "-",
            ), tags=(tag,) if tag else ())

    def _current_records(self):
        """Returns the record set for whichever filter is currently active
        ("all" by default, or "employee" / "date" after a filter button is
        clicked). Re-run automatically after every clock action so the
        filter stays applied instead of resetting to show everything."""
        mode, value = getattr(self, "_filter", ("all", None))
        if mode == "employee":
            return self.att_ctrl.get_by_employee(value)
        if mode == "date":
            return self.att_ctrl.get_by_date(value)
        return self.att_ctrl.list_all()

    def _filter_by_employee(self):
        try:
            emp_id = int(self.emp_id_entry.get().strip())
        except ValueError:
            self.error_label.config(text="Enter a numeric Employee ID to filter by employee.")
            return
        self._filter = ("employee", emp_id)
        self.error_label.config(text="")
        self.refresh()

    def _filter_by_date(self):
        d = self.date_entry.get().strip()
        if not d:
            self.error_label.config(text="Enter a date (YYYY-MM-DD) to filter by date.")
            return
        self._filter = ("date", d)
        self.error_label.config(text="")
        self.refresh()

    def _show_all(self):
        self._filter = ("all", None)
        self.error_label.config(text="")
        self.refresh()

    def _get_common_fields(self):
        try:
            emp_id = int(self.emp_id_entry.get().strip())
        except ValueError:
            self.error_label.config(text="Employee ID must be a number.")
            return None, None
        return emp_id, self.date_entry.get().strip()

    def _clock_in(self):
        emp_id, d = self._get_common_fields()
        if emp_id is None:
            return
        try:
            self.att_ctrl.clock_in(emp_id, d, self.time_entry.get().strip() or None)
            self.error_label.config(text="")
            self.refresh()
        except (EMSException, PermissionError) as e:
            self.error_label.config(text=str(e))

    def _clock_out(self):
        emp_id, d = self._get_common_fields()
        if emp_id is None:
            return
        try:
            self.att_ctrl.clock_out(emp_id, d, self.time_entry.get().strip() or None)
            self.error_label.config(text="")
            self.refresh()
        except (EMSException, PermissionError) as e:
            self.error_label.config(text=str(e))

    def _mark_absent(self):
        emp_id, d = self._get_common_fields()
        if emp_id is None:
            return
        try:
            self.att_ctrl.mark_absent(emp_id, d)
            self.error_label.config(text="")
            self.refresh()
        except (EMSException, PermissionError) as e:
            self.error_label.config(text=str(e))

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Select an attendance record first.")
            return None
        return int(self.tree.item(sel[0], "values")[0])

    def _delete_selected(self):
        attendance_id = self._selected_id()
        if attendance_id is None:
            return
        if not messagebox.askyesno("Confirm delete",
                                    f"Delete attendance record #{attendance_id}? "
                                    f"This cannot be undone."):
            return
        try:
            self.att_ctrl.delete_attendance(attendance_id)
            self.error_label.config(text="")
            self.refresh()
        except (EMSException, PermissionError) as e:
            self.error_label.config(text=str(e))
