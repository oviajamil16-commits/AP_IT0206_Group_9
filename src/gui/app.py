"""Main Tkinter application: owns the window and swaps between the
Login screen and the Dashboard shell. This file and everything else in
src/gui/ is a new PRESENTATION layer only — it calls the exact same
Controllers as the console version (views/*.py) and does not modify a
single Model, Repository, or Service. That separation is only possible
because the MVC architecture was enforced from the start.
"""

import tkinter as tk
from tkinter import messagebox

from gui.styles import NAVY, WHITE
from gui.login_screen import LoginScreen
from gui.dashboard import Dashboard
from exceptions.custom_exceptions import InvalidCredentialsException


class App(tk.Tk):
    def __init__(self, controllers: dict):
        super().__init__()
        self.controllers = controllers
        self.auth_controller = controllers["auth"]

        self.title("Employee Management System")
        self.geometry("1180x720")
        self.minsize(1000, 640)
        self.configure(bg=WHITE)

        self._container = tk.Frame(self, bg=WHITE)
        self._container.pack(fill="both", expand=True)

        self.max_login_attempts = 3
        self._login_attempts_left = self.max_login_attempts

        self._show_login()

    # ------------------------------------------------------------------
    def _clear(self):
        for widget in self._container.winfo_children():
            widget.destroy()

    def _show_login(self):
        self._clear()
        self._login_attempts_left = self.max_login_attempts
        LoginScreen(self._container, on_login=self._handle_login).pack(fill="both", expand=True)

    def _handle_login(self, username: str, password: str, on_error):
        try:
            user = self.auth_controller.login(username, password)
            self._show_dashboard(user)
        except InvalidCredentialsException as e:
            self._login_attempts_left -= 1
            if self._login_attempts_left <= 0:
                messagebox.showerror("Locked out", "Too many failed attempts. The application will close.")
                self.destroy()
            else:
                on_error(f"{e} ({self._login_attempts_left} attempt(s) remaining)")

    def _show_dashboard(self, user):
        self._clear()
        Dashboard(self._container, controllers=self.controllers, user=user,
                  on_logout=self._handle_logout).pack(fill="both", expand=True)

    def _handle_logout(self):
        self.auth_controller.logout()
        self._show_login()
