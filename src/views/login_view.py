"""Console presentation layer for login. No business logic or DB access here —
only prompting, input capture, and displaying results."""

import getpass


class LoginView:
    def show_banner(self) -> None:
        print("=" * 50)
        print("  EMPLOYEE MANAGEMENT SYSTEM".center(50))
        print("=" * 50)

    def prompt_credentials(self) -> tuple[str, str]:
        username = input("Username: ").strip()
        # getpass hides the password as it's typed; falls back to a plain
        # prompt automatically if the terminal doesn't support it.
        password = getpass.getpass("Password: ")
        return username, password

    def show_error(self, message: str) -> None:
        print(f"\n[!] {message}\n")

    def show_welcome(self, username: str, role: str) -> None:
        print(f"\nWelcome, {username}. Logged in as {role}.\n")

    def show_attempts_remaining(self, remaining: int) -> None:
        if remaining > 0:
            print(f"({remaining} attempt(s) remaining)")

    def show_lockout(self) -> None:
        print("\nToo many failed attempts. Exiting.\n")
