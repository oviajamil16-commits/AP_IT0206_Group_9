"""Payroll screen — calls PayrollController.run_payroll() exactly as
the console PayrollView does, including the leave-to-deduction workflow
and the invalid-period validation fix."""

import tkinter as tk
from tkinter import ttk, messagebox

from gui.styles import NAVY, WHITE, LIGHT_BG, GOLD, FONT_HEADER, FONT_BODY, FONT_BODY_BOLD
from exceptions.custom_exceptions import EMSException


class PayrollScreen(tk.Frame):
    def __init__(self, parent, controllers, user):
        super().__init__(parent, bg=LIGHT_BG)
        self.pay_ctrl = controllers["payroll"]
        self.user = user
        self.can_run = user.can("payroll.run")

        self._build_header()
        self._build_table()

    def _build_header(self):
        header = tk.Frame(self, bg=LIGHT_BG)
        header.pack(fill="x", pady=(0, 16))
        tk.Label(header, text="Payroll", font=FONT_HEADER, bg=LIGHT_BG, fg=NAVY).pack(side="left")

        form = tk.Frame(self, bg=LIGHT_BG)
        form.pack(fill="x", pady=(0, 12))
        tk.Label(form, text="Period (YYYY-MM):", font=FONT_BODY, bg=LIGHT_BG).pack(side="left")
        self.period_entry = ttk.Entry(form, width=10)
        self.period_entry.pack(side="left", padx=(6, 12))

        if self.can_run:
            tk.Button(form, text="Run Payroll", font=FONT_BODY_BOLD, bg=NAVY, fg=WHITE, relief="flat",
                      padx=12, pady=6, cursor="hand2", command=self._run_payroll).pack(side="left", padx=(0, 8))
        tk.Button(form, text="View Payslips", font=FONT_BODY, bg=WHITE, fg=NAVY, relief="solid",
                  bd=1, padx=12, pady=6, cursor="hand2", command=self._view_period).pack(side="left")

        self.status_label = tk.Label(self, text="", font=FONT_BODY, bg=LIGHT_BG, fg="#1B7A6E",
                                      wraplength=800, justify="left")
        self.status_label.pack(anchor="w", pady=(0, 8))

    def _build_table(self):
        columns = ("id", "employee_id", "period", "base_salary", "deductions", "net_pay")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=14)
        headings = {"id": "ID", "employee_id": "Emp ID", "period": "Period", "base_salary": "Base Salary",
                    "deductions": "Deductions", "net_pay": "Net Pay"}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=130, anchor="w")
        self.tree.pack(fill="both", expand=True)

    def _fill_table(self, payrolls):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for p in payrolls:
            self.tree.insert("", "end", values=(
                p.payroll_id, p.employee_id, p.period, f"${p.base_salary:,.2f}",
                f"${p.deductions:,.2f}", f"${p.net_pay:,.2f}",
            ))

    def _run_payroll(self):
        period = self.period_entry.get().strip()
        try:
            result = self.pay_ctrl.run_payroll(period)
            self.status_label.config(
                text=f"Payroll run complete: {len(result.created)} payslip(s) created, "
                     f"{len(result.skipped)} employee(s) skipped."
            )
            self._fill_table(result.created)
        except (EMSException, PermissionError) as e:
            self.status_label.config(text=str(e), fg="#A94442")

    def _view_period(self):
        period = self.period_entry.get().strip()
        try:
            payrolls = self.pay_ctrl.list_by_period(period)
            self.status_label.config(text=f"Showing {len(payrolls)} payslip(s) for {period}.", fg="#1B7A6E")
            self._fill_table(payrolls)
        except (EMSException, PermissionError) as e:
            self.status_label.config(text=str(e), fg="#A94442")
