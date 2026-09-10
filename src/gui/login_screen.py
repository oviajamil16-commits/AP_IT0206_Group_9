"""Login screen. No business logic here — credentials are handed to
App, which calls AuthController.login() exactly as the console version
does. This widget only knows how to collect input and display errors."""

import tkinter as tk
from tkinter import ttk

from gui.styles import NAVY, ICE, WHITE, GOLD, DARK_TEXT, MUTED_TEXT, FONT_TITLE, FONT_BODY


class LoginScreen(tk.Frame):
    def __init__(self, parent, on_login):
        super().__init__(parent, bg=WHITE)
        self._on_login = on_login

        # Left navy panel
        left = tk.Frame(self, bg=NAVY, width=460)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="👥", font=("Segoe UI", 40), bg=GOLD, fg=WHITE,
                 width=2, height=1).place(x=48, y=64)
        tk.Label(left, text="Employee\nManagement\nSystem", font=("Segoe UI", 26, "bold"),
                 bg=NAVY, fg=WHITE, justify="left", anchor="w").place(x=48, y=170)
        tk.Label(left, text="IT0206 · Advanced Computer Programming 2",
                 font=("Segoe UI", 10, "italic"), bg=NAVY, fg=ICE).place(x=48, y=330)

        # Right login panel
        right = tk.Frame(self, bg=WHITE)
        right.pack(side="left", fill="both", expand=True)

        form = tk.Frame(right, bg=WHITE)
        form.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(form, text="Sign in", font=FONT_TITLE, bg=WHITE, fg=NAVY).grid(
            row=0, column=0, sticky="w", pady=(0, 4))
        tk.Label(form, text="Enter your administrator or HR staff credentials",
                 font=FONT_BODY, bg=WHITE, fg=MUTED_TEXT).grid(row=1, column=0, sticky="w", pady=(0, 24))

        tk.Label(form, text="Username", font=FONT_BODY, bg=WHITE, fg=DARK_TEXT).grid(
            row=2, column=0, sticky="w")
        self.username_entry = ttk.Entry(form, width=34, font=FONT_BODY)
        self.username_entry.grid(row=3, column=0, pady=(2, 16), ipady=4)
        self.username_entry.focus_set()

        tk.Label(form, text="Password", font=FONT_BODY, bg=WHITE, fg=DARK_TEXT).grid(
            row=4, column=0, sticky="w")
        self.password_entry = ttk.Entry(form, width=34, font=FONT_BODY, show="•")
        self.password_entry.grid(row=5, column=0, pady=(2, 8), ipady=4)
        self.password_entry.bind("<Return>", lambda e: self._submit())

        self.error_label = tk.Label(form, text="", font=FONT_BODY, bg=WHITE, fg="#A94442",
                                     wraplength=340, justify="left")
        self.error_label.grid(row=6, column=0, sticky="w", pady=(4, 12))

        login_btn = tk.Button(form, text="Log in", font=("Segoe UI", 11, "bold"), bg=NAVY, fg=WHITE,
                               activebackground=GOLD, activeforeground=WHITE, relief="flat",
                               padx=20, pady=8, command=self._submit, cursor="hand2")
        login_btn.grid(row=7, column=0, sticky="ew")

    def _submit(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        self.error_label.config(text="")
        if not username or not password:
            self.error_label.config(text="Enter both a username and a password.")
            return
        self._on_login(username, password, self._show_error)

    def _show_error(self, message: str):
        self.error_label.config(text=message)
        self.password_entry.delete(0, tk.END)
