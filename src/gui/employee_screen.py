"""Employee list/CRUD screen. Every action below calls the exact same
EmployeeController/DepartmentController/PositionController methods the
console EmployeeView uses — this file only handles layout and dialogs."""

import tkinter as tk
from tkinter import ttk, messagebox

from gui.styles import NAVY, WHITE, GOLD, LIGHT_BG, DARK_TEXT, MUTED_TEXT, FONT_HEADER, FONT_BODY, FONT_BODY_BOLD
from exceptions.custom_exceptions import EMSException


class EmployeeScreen(tk.Frame):
    def __init__(self, parent, controllers, user):
        super().__init__(parent, bg=LIGHT_BG)
        self.emp_ctrl = controllers["employee"]
        self.dept_ctrl = controllers["department"]
        self.pos_ctrl = controllers["position"]
        self.user = user
        self.can_delete = user.can("employee.delete")
        self.can_manage_org = user.can("department.create")

        self._build_header()
        self._build_table()
        self.refresh()

    # ------------------------------------------------------------------
    def _build_header(self):
        header = tk.Frame(self, bg=LIGHT_BG)
        header.pack(fill="x", pady=(0, 16))

        tk.Label(header, text="Employees", font=FONT_HEADER, bg=LIGHT_BG, fg=NAVY).pack(side="left")

        btn_frame = tk.Frame(header, bg=LIGHT_BG)
        btn_frame.pack(side="right")

        if self.can_manage_org:
            tk.Button(btn_frame, text="Manage Departments", font=FONT_BODY, bg=WHITE, fg=NAVY,
                      relief="solid", bd=1, padx=12, pady=6, cursor="hand2",
                      command=self._open_department_manager).pack(side="left", padx=(0, 8))
            tk.Button(btn_frame, text="Manage Positions", font=FONT_BODY, bg=WHITE, fg=NAVY,
                      relief="solid", bd=1, padx=12, pady=6, cursor="hand2",
                      command=self._open_position_manager).pack(side="left", padx=(0, 8))

        tk.Button(btn_frame, text="+ Add Employee", font=FONT_BODY_BOLD, bg=NAVY, fg=WHITE,
                  relief="flat", padx=14, pady=6, cursor="hand2",
                  command=self._open_add_dialog).pack(side="left")

        search_frame = tk.Frame(self, bg=LIGHT_BG)
        search_frame.pack(fill="x", pady=(0, 12))
        tk.Label(search_frame, text="Search:", font=FONT_BODY, bg=LIGHT_BG, fg=DARK_TEXT).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=(8, 0))

    def _build_table(self):
        columns = ("id", "name", "email", "status", "department", "position", "hire_date")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=16)
        headings = {"id": "ID", "name": "Name", "email": "Email", "status": "Status",
                    "department": "Department", "position": "Position", "hire_date": "Hire Date"}
        widths = {"id": 45, "name": 160, "email": 190, "status": 90, "department": 130,
                  "position": 130, "hire_date": 100}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")
        self.tree.pack(fill="both", expand=True)

        action_bar = tk.Frame(self, bg=LIGHT_BG)
        action_bar.pack(fill="x", pady=(12, 0))
        tk.Button(action_bar, text="Edit Selected", font=FONT_BODY, bg=WHITE, fg=NAVY,
                  relief="solid", bd=1, padx=12, pady=6, cursor="hand2",
                  command=self._open_edit_dialog).pack(side="left")
        if self.can_delete:
            tk.Button(action_bar, text="Delete Selected", font=FONT_BODY, bg=WHITE, fg="#A94442",
                      relief="solid", bd=1, padx=12, pady=6, cursor="hand2",
                      command=self._delete_selected).pack(side="left", padx=(8, 0))

    # ------------------------------------------------------------------
    def _dept_lookup(self):
        return {d.department_id: d.name for d in self.dept_ctrl.list_departments()}

    def _pos_lookup(self):
        return {p.position_id: p.title for p in self.pos_ctrl.list_positions()}

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        depts = self._dept_lookup()
        positions = self._pos_lookup()
        query = self.search_var.get().strip()
        employees = self.emp_ctrl.search_employees(name_contains=query) if query else self.emp_ctrl.list_employees()
        for e in employees:
            self.tree.insert("", "end", iid=str(e.employee_id), values=(
                e.employee_id, e.full_name, e.email or "-", e.status,
                depts.get(e.department_id, "-"), positions.get(e.position_id, "-"), e.hire_date,
            ))

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Select an employee first.")
            return None
        return int(sel[0])

    # ------------------------------------------------------------------
    def _open_add_dialog(self):
        EmployeeFormDialog(self, mode="add", emp_ctrl=self.emp_ctrl, dept_ctrl=self.dept_ctrl,
                            pos_ctrl=self.pos_ctrl, on_saved=self.refresh)

    def _open_edit_dialog(self):
        emp_id = self._selected_id()
        if emp_id is None:
            return
        employee = self.emp_ctrl.get_employee(emp_id)
        EmployeeFormDialog(self, mode="edit", emp_ctrl=self.emp_ctrl, dept_ctrl=self.dept_ctrl,
                            pos_ctrl=self.pos_ctrl, on_saved=self.refresh, employee=employee)

    def _delete_selected(self):
        emp_id = self._selected_id()
        if emp_id is None:
            return
        employee = self.emp_ctrl.get_employee(emp_id)
        if not messagebox.askyesno("Confirm delete", f"Delete {employee.full_name}? This cannot be undone."):
            return
        try:
            self.emp_ctrl.delete_employee(emp_id)
            self.refresh()
        except (EMSException, PermissionError) as e:
            messagebox.showerror("Error", str(e))

    def _open_department_manager(self):
        OrgManagerDialog(self, title="Manage Departments", kind="department",
                          dept_ctrl=self.dept_ctrl, pos_ctrl=self.pos_ctrl, on_change=self.refresh)

    def _open_position_manager(self):
        OrgManagerDialog(self, title="Manage Positions", kind="position",
                          dept_ctrl=self.dept_ctrl, pos_ctrl=self.pos_ctrl, on_change=self.refresh)


class EmployeeFormDialog(tk.Toplevel):
    """Add/Edit employee modal. Field validation is NOT duplicated here —
    it's left entirely to EmployeeController, so the exact same rules
    (date format, email format, FK existence) apply as in the console."""

    def __init__(self, parent, mode, emp_ctrl, dept_ctrl, pos_ctrl, on_saved, employee=None):
        super().__init__(parent)
        self.emp_ctrl = emp_ctrl
        self.on_saved = on_saved
        self.mode = mode
        self.employee = employee

        self.title("Add Employee" if mode == "add" else "Edit Employee")
        # Edit mode has an extra "Status" field that Add mode doesn't, so it
        # needs more vertical room or the Save button gets cut off below
        # the visible window.
        self.geometry("420x520" if mode == "add" else "420x600")
        self.resizable(False, True)
        self.configure(bg=WHITE)
        self.transient(parent)
        self.grab_set()

        depts = dept_ctrl.list_departments()
        positions = pos_ctrl.list_positions()
        self._dept_by_name = {d.name: d.department_id for d in depts}
        self._pos_by_name = {p.title: p.position_id for p in positions}

        pad = {"padx": 20, "pady": (10, 0)}
        tk.Label(self, text=self.title(), font=FONT_HEADER, bg=WHITE, fg=NAVY).pack(anchor="w", **pad)

        self.first_name = self._labeled_entry("First name", employee.first_name if employee else "")
        self.last_name = self._labeled_entry("Last name", employee.last_name if employee else "")
        self.email = self._labeled_entry("Email (optional)", employee.email if employee else "")
        self.phone = self._labeled_entry("Phone (optional)", employee.phone if employee else "")
        self.hire_date = self._labeled_entry("Hire date (YYYY-MM-DD)", employee.hire_date if employee else "")

        tk.Label(self, text="Department", font=FONT_BODY, bg=WHITE, fg=DARK_TEXT).pack(anchor="w", padx=20, pady=(10, 0))
        self.dept_var = tk.StringVar()
        dept_names = ["(none)"] + list(self._dept_by_name.keys())
        current_dept = next((n for n, i in self._dept_by_name.items() if employee and i == employee.department_id), "(none)")
        self.dept_var.set(current_dept)
        ttk.Combobox(self, textvariable=self.dept_var, values=dept_names, state="readonly", width=35).pack(padx=20, fill="x")

        tk.Label(self, text="Position", font=FONT_BODY, bg=WHITE, fg=DARK_TEXT).pack(anchor="w", padx=20, pady=(10, 0))
        self.pos_var = tk.StringVar()
        pos_names = ["(none)"] + list(self._pos_by_name.keys())
        current_pos = next((n for n, i in self._pos_by_name.items() if employee and i == employee.position_id), "(none)")
        self.pos_var.set(current_pos)
        ttk.Combobox(self, textvariable=self.pos_var, values=pos_names, state="readonly", width=35).pack(padx=20, fill="x")

        if mode == "edit":
            tk.Label(self, text="Status", font=FONT_BODY, bg=WHITE, fg=DARK_TEXT).pack(anchor="w", padx=20, pady=(10, 0))
            self.status_var = tk.StringVar(value=employee.status)
            ttk.Combobox(self, textvariable=self.status_var, values=["active", "inactive", "terminated"],
                         state="readonly", width=35).pack(padx=20, fill="x")

        self.error_label = tk.Label(self, text="", font=FONT_BODY, bg=WHITE, fg="#A94442",
                                     wraplength=380, justify="left")
        self.error_label.pack(anchor="w", padx=20, pady=(12, 0))

        tk.Button(self, text="Save", font=FONT_BODY_BOLD, bg=NAVY, fg=WHITE, relief="flat",
                  padx=20, pady=8, cursor="hand2", command=self._save).pack(padx=20, pady=16, fill="x")

    def _labeled_entry(self, label, initial=""):
        tk.Label(self, text=label, font=FONT_BODY, bg=WHITE, fg=DARK_TEXT).pack(anchor="w", padx=20, pady=(10, 0))
        entry = ttk.Entry(self, width=38)
        entry.insert(0, initial or "")
        entry.pack(padx=20, fill="x")
        return entry

    def _save(self):
        dept_id = self._dept_by_name.get(self.dept_var.get())
        pos_id = self._pos_by_name.get(self.pos_var.get())
        try:
            if self.mode == "add":
                self.emp_ctrl.add_employee(
                    self.first_name.get(), self.last_name.get(), None,
                    self.email.get() or None, self.phone.get() or None,
                    self.hire_date.get(), dept_id, pos_id,
                )
            else:
                self.emp_ctrl.update_employee(
                    self.employee.employee_id,
                    first_name=self.first_name.get(), last_name=self.last_name.get(),
                    email=self.email.get() or None, phone=self.phone.get() or None,
                    status=self.status_var.get(), department_id=dept_id, position_id=pos_id,
                )
            self.on_saved()
            self.destroy()
        except (EMSException, PermissionError) as e:
            self.error_label.config(text=str(e))


class OrgManagerDialog(tk.Toplevel):
    """Shared Add/List/Delete dialog for Departments and Positions."""

    def __init__(self, parent, title, kind, dept_ctrl, pos_ctrl, on_change):
        super().__init__(parent)
        self.kind = kind
        self.dept_ctrl = dept_ctrl
        self.pos_ctrl = pos_ctrl
        self.on_change = on_change

        self.title(title)
        self.geometry("420x460" if kind == "department" else "560x460")
        self.configure(bg=WHITE)
        self.transient(parent)
        self.grab_set()

        tk.Label(self, text=title, font=FONT_HEADER, bg=WHITE, fg=NAVY).pack(anchor="w", padx=20, pady=(16, 8))

        form = tk.Frame(self, bg=WHITE)
        form.pack(fill="x", padx=20)
        if kind == "department":
            self.name_entry = ttk.Entry(form, width=24)
            self.name_entry.pack(side="left")
            tk.Button(form, text="Add", bg=NAVY, fg=WHITE, relief="flat", padx=12,
                      command=self._add_department).pack(side="left", padx=(8, 0))
        else:
            tk.Label(form, text="Title", font=FONT_BODY, bg=WHITE, fg=MUTED_TEXT).grid(row=0, column=0, sticky="w")
            tk.Label(form, text="Department", font=FONT_BODY, bg=WHITE, fg=MUTED_TEXT).grid(row=0, column=1, sticky="w", padx=(4, 0))
            tk.Label(form, text="Base salary", font=FONT_BODY, bg=WHITE, fg=MUTED_TEXT).grid(row=0, column=2, sticky="w", padx=(4, 0))

            self.title_entry = ttk.Entry(form, width=16)
            self.title_entry.grid(row=1, column=0)
            self.dept_var = tk.StringVar()
            depts = dept_ctrl.list_departments()
            self._dept_by_name = {d.name: d.department_id for d in depts}
            ttk.Combobox(form, textvariable=self.dept_var, values=list(self._dept_by_name.keys()),
                         state="readonly", width=14).grid(row=1, column=1, padx=(4, 0))
            self.grade_entry = ttk.Entry(form, width=10)
            self.grade_entry.grid(row=1, column=2, padx=(4, 0))
            tk.Button(form, text="Add", bg=NAVY, fg=WHITE, relief="flat", padx=8,
                      command=self._add_position).grid(row=1, column=3, padx=(4, 0))

        self.error_label = tk.Label(self, text="", font=FONT_BODY, bg=WHITE, fg="#A94442", wraplength=380)
        self.error_label.pack(anchor="w", padx=20, pady=(6, 0))

        self.listbox = tk.Listbox(self, font=FONT_BODY)
        self.listbox.pack(fill="both", expand=True, padx=20, pady=12)

        button_row = tk.Frame(self, bg=WHITE)
        button_row.pack(padx=20, pady=(0, 16), fill="x")
        tk.Button(button_row, text="Refresh", bg=WHITE, fg=NAVY, relief="solid", bd=1,
                  command=self._refresh_list).pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Button(button_row, text="Delete Selected", bg=WHITE, fg="#A94442", relief="solid", bd=1,
                  command=self._delete_selected).pack(side="left", fill="x", expand=True)

        self._refresh_list()

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        if self.kind == "department":
            self._items = self.dept_ctrl.list_departments()
            for d in self._items:
                self.listbox.insert(tk.END, f"{d.department_id}. {d.name}")
        else:
            self._items = self.pos_ctrl.list_positions()
            dept_names = {d.department_id: d.name for d in self.dept_ctrl.list_departments()}
            for p in self._items:
                dept_name = dept_names.get(p.department_id, "Unknown dept")
                self.listbox.insert(
                    tk.END,
                    f"{p.position_id}. {p.title} — {dept_name} — base salary {p.base_salary_grade:,.2f}",
                )

    def _add_department(self):
        try:
            self.dept_ctrl.add_department(self.name_entry.get())
            self.name_entry.delete(0, tk.END)
            self.error_label.config(text="")
            self._refresh_list()
            self.on_change()
        except (EMSException, PermissionError) as e:
            self.error_label.config(text=str(e))

    def _add_position(self):
        dept_id = self._dept_by_name.get(self.dept_var.get())
        if dept_id is None:
            self.error_label.config(text="Choose a department first.")
            return
        try:
            self.pos_ctrl.add_position(self.title_entry.get(), dept_id, self.grade_entry.get())
            self.title_entry.delete(0, tk.END)
            self.grade_entry.delete(0, tk.END)
            self.error_label.config(text="")
            self._refresh_list()
            self.on_change()
        except (EMSException, PermissionError) as e:
            self.error_label.config(text=str(e))

    def _delete_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        item = self._items[sel[0]]
        try:
            if self.kind == "department":
                self.dept_ctrl.delete_department(item.department_id)
            else:
                self.pos_ctrl.delete_position(item.position_id)
            self._refresh_list()
            self.on_change()
        except (EMSException, PermissionError) as e:
            self.error_label.config(text=str(e))
