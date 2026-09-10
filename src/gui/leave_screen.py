"""Leave requests screen — submit, list, and approve/reject, calling
LeaveController exactly as the console LeaveView does. The approve/
reject buttons are only shown to users who can perform them; the
Controller (and the LeaveRequest model itself) still enforce this
regardless, so hiding the button is UX, not the actual security
boundary."""

import tkinter as tk
from tkinter import ttk, messagebox

from gui.styles import NAVY, WHITE, LIGHT_BG, GOLD, FONT_HEADER, FONT_BODY, FONT_BODY_BOLD
from exceptions.custom_exceptions import EMSException


class LeaveScreen(tk.Frame):
    def __init__(self, parent, controllers, user):
        super().__init__(parent, bg=LIGHT_BG)
        self.leave_ctrl = controllers["leave"]
        self.user = user
        self.can_approve = user.can("leave.approve")

        self._build_header()
        self._build_table()
        self.refresh()

    def _build_header(self):
        header = tk.Frame(self, bg=LIGHT_BG)
        header.pack(fill="x", pady=(0, 16))
        tk.Label(header, text="Leave Requests", font=FONT_HEADER, bg=LIGHT_BG, fg=NAVY).pack(side="left")
        tk.Button(header, text="+ Submit Leave Request", font=FONT_BODY_BOLD, bg=NAVY, fg=WHITE,
                  relief="flat", padx=14, pady=6, cursor="hand2",
                  command=self._open_submit_dialog).pack(side="right")

        filter_frame = tk.Frame(self, bg=LIGHT_BG)
        filter_frame.pack(fill="x", pady=(0, 12))
        tk.Label(filter_frame, text="Filter by status:", font=FONT_BODY, bg=LIGHT_BG).pack(side="left")
        self.status_var = tk.StringVar(value="all")
        for val in ["all", "pending", "approved", "rejected"]:
            tk.Radiobutton(filter_frame, text=val.capitalize(), variable=self.status_var, value=val,
                           bg=LIGHT_BG, command=self.refresh).pack(side="left", padx=(6, 0))

    def _build_table(self):
        columns = ("id", "employee_id", "type", "start", "end", "days", "status", "approved_by")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=14)
        headings = {"id": "ID", "employee_id": "Emp ID", "type": "Type", "start": "Start",
                    "end": "End", "days": "Days", "status": "Status", "approved_by": "Approved By"}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=100, anchor="w")
        self.tree.pack(fill="both", expand=True)

        if self.can_approve:
            action_bar = tk.Frame(self, bg=LIGHT_BG)
            action_bar.pack(fill="x", pady=(12, 0))
            tk.Button(action_bar, text="Approve Selected", font=FONT_BODY_BOLD, bg="#1B7A6E", fg=WHITE,
                      relief="flat", padx=12, pady=6, cursor="hand2",
                      command=self._approve_selected).pack(side="left")
            tk.Button(action_bar, text="Reject Selected", font=FONT_BODY, bg=WHITE, fg="#A94442",
                      relief="solid", bd=1, padx=12, pady=6, cursor="hand2",
                      command=self._reject_selected).pack(side="left", padx=(8, 0))

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        status = None if self.status_var.get() == "all" else self.status_var.get()
        for r in self.leave_ctrl.list_by_status(status):
            self.tree.insert("", "end", iid=str(r.leave_id), values=(
                r.leave_id, r.employee_id, r.leave_type, r.start_date, r.end_date,
                r.duration_days, r.status, r.approved_by or "-",
            ))

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Select a leave request first.")
            return None
        return int(sel[0])

    def _approve_selected(self):
        leave_id = self._selected_id()
        if leave_id is None:
            return
        try:
            self.leave_ctrl.approve_leave(leave_id)
            self.refresh()
        except (EMSException, PermissionError) as e:
            messagebox.showerror("Error", str(e))

    def _reject_selected(self):
        leave_id = self._selected_id()
        if leave_id is None:
            return
        try:
            self.leave_ctrl.reject_leave(leave_id)
            self.refresh()
        except (EMSException, PermissionError) as e:
            messagebox.showerror("Error", str(e))

    def _open_submit_dialog(self):
        SubmitLeaveDialog(self, leave_ctrl=self.leave_ctrl, on_saved=self.refresh)


class SubmitLeaveDialog(tk.Toplevel):
    def __init__(self, parent, leave_ctrl, on_saved):
        super().__init__(parent)
        self.leave_ctrl = leave_ctrl
        self.on_saved = on_saved

        self.title("Submit Leave Request")
        self.geometry("360x420")
        self.configure(bg=WHITE)
        self.transient(parent)
        self.grab_set()

        tk.Label(self, text="Submit Leave Request", font=FONT_HEADER, bg=WHITE, fg=NAVY).pack(
            anchor="w", padx=20, pady=(16, 12))

        self.emp_id = self._labeled_entry("Employee ID")
        tk.Label(self, text="Leave type", font=FONT_BODY, bg=WHITE).pack(anchor="w", padx=20, pady=(10, 0))
        self.leave_type = ttk.Combobox(self, values=["annual", "sick", "unpaid", "other"], state="readonly")
        self.leave_type.pack(padx=20, fill="x")
        self.start_date = self._labeled_entry("Start date (YYYY-MM-DD)")
        self.end_date = self._labeled_entry("End date (YYYY-MM-DD)")

        self.error_label = tk.Label(self, text="", font=FONT_BODY, bg=WHITE, fg="#A94442", wraplength=320)
        self.error_label.pack(anchor="w", padx=20, pady=(12, 0))

        tk.Button(self, text="Submit", font=FONT_BODY_BOLD, bg=NAVY, fg=WHITE, relief="flat",
                  padx=20, pady=8, cursor="hand2", command=self._submit).pack(padx=20, pady=16, fill="x")

    def _labeled_entry(self, label):
        tk.Label(self, text=label, font=FONT_BODY, bg=WHITE).pack(anchor="w", padx=20, pady=(10, 0))
        entry = ttk.Entry(self, width=30)
        entry.pack(padx=20, fill="x")
        return entry

    def _submit(self):
        try:
            emp_id = int(self.emp_id.get().strip())
        except ValueError:
            self.error_label.config(text="Employee ID must be a number.")
            return
        try:
            self.leave_ctrl.submit_leave(
                emp_id, self.leave_type.get(), self.start_date.get().strip(), self.end_date.get().strip()
            )
            self.on_saved()
            self.destroy()
        except (EMSException, PermissionError) as e:
            self.error_label.config(text=str(e))
