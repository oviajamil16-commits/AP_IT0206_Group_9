"""Reports screen — calls ReportController exactly as the console
ReportView does, then displays the PNG it actually wrote to disk
(the same file used by the console version) rather than re-plotting."""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from gui.styles import NAVY, WHITE, LIGHT_BG, GOLD, MUTED_TEXT, FONT_HEADER, FONT_BODY, FONT_BODY_BOLD
from exceptions.custom_exceptions import EMSException


class ReportsScreen(tk.Frame):
    def __init__(self, parent, controllers, user):
        super().__init__(parent, bg=LIGHT_BG)
        self.report_ctrl = controllers["report"]
        self._current_image = None  # keep a reference so it isn't garbage-collected

        self._build_header()
        self._build_body()

    def _build_header(self):
        header = tk.Frame(self, bg=LIGHT_BG)
        header.pack(fill="x", pady=(0, 16))
        tk.Label(header, text="Reports", font=FONT_HEADER, bg=LIGHT_BG, fg=NAVY).pack(side="left")

        btns = tk.Frame(self, bg=LIGHT_BG)
        btns.pack(fill="x", pady=(0, 8))
        tk.Button(btns, text="Headcount by Department", font=FONT_BODY_BOLD, bg=NAVY, fg=WHITE,
                  relief="flat", padx=12, pady=6, cursor="hand2",
                  command=self._show_headcount).pack(side="left", padx=(0, 8))

        tk.Label(btns, text="Payroll period:", font=FONT_BODY, bg=LIGHT_BG).pack(side="left", padx=(12, 4))
        self.period_entry = ttk.Entry(btns, width=10)
        self.period_entry.pack(side="left")
        tk.Button(btns, text="Payroll Cost Summary", font=FONT_BODY_BOLD, bg=NAVY, fg=WHITE,
                  relief="flat", padx=12, pady=6, cursor="hand2",
                  command=self._show_payroll_summary).pack(side="left", padx=(8, 8))

        tk.Button(btns, text="Attendance Summary", font=FONT_BODY_BOLD, bg=NAVY, fg=WHITE,
                  relief="flat", padx=12, pady=6, cursor="hand2",
                  command=self._show_attendance_summary).pack(side="left")

        self.status_label = tk.Label(self, text="", font=FONT_BODY, bg=LIGHT_BG, fg="#A94442")
        self.status_label.pack(anchor="w", pady=(0, 8))

    def _build_body(self):
        self.chart_label = tk.Label(self, bg=WHITE, text="Choose a report above to generate it.",
                                     font=FONT_BODY, fg=MUTED_TEXT)
        self.chart_label.pack(fill="both", expand=True)

    def _display_chart(self, path, caption):
        if path is None:
            self.chart_label.config(image="", text=caption or "No data available for this report.")
            return
        img = Image.open(path)
        img.thumbnail((760, 460))
        self._current_image = ImageTk.PhotoImage(img)
        self.chart_label.config(image=self._current_image, text="")

    def _show_headcount(self):
        try:
            counts, chart_path = self.report_ctrl.headcount_by_department()
            self.status_label.config(text="")
            self._display_chart(chart_path, "No employees to report on yet.")
        except (EMSException, PermissionError) as e:
            self.status_label.config(text=str(e))

    def _show_payroll_summary(self):
        period = self.period_entry.get().strip()
        try:
            total, average, count, chart_path = self.report_ctrl.payroll_cost_summary(period)
            self.status_label.config(
                text=f"Total: ${total:,.2f}   Average: ${average:,.2f}   Payslips: {count}", fg="#1B7A6E"
            )
            self._display_chart(chart_path, f"No payroll records for {period} yet.")
        except (EMSException, PermissionError) as e:
            self.status_label.config(text=str(e), fg="#A94442")

    def _show_attendance_summary(self):
        try:
            counts, chart_path = self.report_ctrl.attendance_summary()
            self.status_label.config(text="")
            self._display_chart(chart_path, "No attendance records yet.")
        except (EMSException, PermissionError) as e:
            self.status_label.config(text=str(e))
