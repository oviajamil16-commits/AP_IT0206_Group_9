"""Dashboard shell: sidebar navigation + a content area that swaps
between module screens. Which sidebar items are shown depends on the
logged-in user's role via user.can(action) — exactly the same
permission model the console version uses, just reflected in the UI
instead of raising PermissionError after the fact (though the
Controllers still enforce it either way — this is UX, not security)."""

import tkinter as tk

from gui.styles import NAVY, BLUE, ICE, WHITE, GOLD, LIGHT_BG, DARK_TEXT, MUTED_TEXT, FONT_BODY, FONT_BODY_BOLD
from gui.employee_screen import EmployeeScreen
from gui.attendance_screen import AttendanceScreen
from gui.leave_screen import LeaveScreen
from gui.payroll_screen import PayrollScreen
from gui.reports_screen import ReportsScreen


class Dashboard(tk.Frame):
    def __init__(self, parent, controllers: dict, user, on_logout):
        super().__init__(parent, bg=WHITE)
        self.controllers = controllers
        self.user = user
        self.on_logout = on_logout

        self._nav_buttons = {}
        self._content = None

        self._build_sidebar()
        self._build_content_area()
        self.show_screen("employees")

    # ------------------------------------------------------------------
    def _build_sidebar(self):
        sidebar = tk.Frame(self, bg=NAVY, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="EMS", font=("Segoe UI", 18, "bold"), bg=NAVY, fg=WHITE).pack(
            anchor="w", padx=20, pady=(24, 2))
        tk.Label(sidebar, text=f"{self.user.username} · {self.user.role}", font=("Segoe UI", 9),
                 bg=NAVY, fg=ICE).pack(anchor="w", padx=20, pady=(0, 24))

        nav_items = [
            ("employees", "Employees"),
            ("attendance", "Attendance"),
            ("leave", "Leave Requests"),
            ("payroll", "Payroll"),
            ("reports", "Reports"),
        ]
        for key, label in nav_items:
            btn = tk.Button(
                sidebar, text=label, font=FONT_BODY, bg=NAVY, fg=WHITE, bd=0,
                activebackground=BLUE, activeforeground=WHITE, anchor="w",
                padx=20, pady=10, relief="flat", cursor="hand2",
                command=lambda k=key: self.show_screen(k),
            )
            btn.pack(fill="x")
            self._nav_buttons[key] = btn

        tk.Frame(sidebar, bg=NAVY).pack(fill="both", expand=True)  # spacer

        logout_btn = tk.Button(
            sidebar, text="Log out", font=FONT_BODY_BOLD, bg=GOLD, fg=WHITE, bd=0,
            activebackground="#96690A", activeforeground=WHITE, relief="flat",
            padx=20, pady=10, cursor="hand2", command=self.on_logout,
        )
        logout_btn.pack(fill="x", side="bottom")

    def _build_content_area(self):
        self._content_area = tk.Frame(self, bg=LIGHT_BG)
        self._content_area.pack(side="left", fill="both", expand=True)

    def _highlight_nav(self, active_key):
        for key, btn in self._nav_buttons.items():
            btn.config(bg=BLUE if key == active_key else NAVY)

    # ------------------------------------------------------------------
    def show_screen(self, key: str):
        self._highlight_nav(key)
        if self._content is not None:
            self._content.destroy()

        screen_classes = {
            "employees": EmployeeScreen,
            "attendance": AttendanceScreen,
            "leave": LeaveScreen,
            "payroll": PayrollScreen,
            "reports": ReportsScreen,
        }
        screen_cls = screen_classes[key]
        self._content = screen_cls(self._content_area, controllers=self.controllers, user=self.user)
        self._content.pack(fill="both", expand=True, padx=24, pady=24)
