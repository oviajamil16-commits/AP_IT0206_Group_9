"""
Standalone utility: reset a user's password directly in the database.

This app does not currently have a "change password" feature built into
its menus/GUI, so this script exists as a maintenance tool -- it uses the
exact same password-hashing function as the real app (AuthService.hash_password,
PBKDF2-HMAC, 200,000 iterations, random per-user salt), so the resulting
hash is 100% compatible with normal login.

Place this file in the PROJECT ROOT (the same folder that contains
src/, database/, etc.) and run it from there:

    python reset_password.py

You'll be shown the existing usernames, asked which one to reset, and
asked to type the new password twice (hidden input) to confirm it matches.
"""

import getpass
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
sys.path.insert(0, SRC_DIR)

import config  # noqa: E402
from repositories.database import DatabaseConnection  # noqa: E402
from repositories.user_repository import UserRepository  # noqa: E402
from services.auth_service import AuthService  # noqa: E402
from exceptions.custom_exceptions import RecordNotFoundException  # noqa: E402


def main():
    print(f"Using database: {config.DATABASE_PATH}")
    if not os.path.exists(config.DATABASE_PATH):
        print("ERROR: database/app.db not found. Run `python src/main.py` "
              "at least once first so the database is bootstrapped.")
        sys.exit(1)

    db = DatabaseConnection(config.DATABASE_PATH)
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)

    users = user_repo.all()
    if not users:
        print("No users found in the database.")
        sys.exit(1)

    print("\nExisting accounts:")
    for u in users:
        print(f"  - {u.username} ({u.role})")

    username = input("\nUsername to reset: ").strip()
    try:
        user = user_repo.find_by_username(username)
    except RecordNotFoundException:
        user = None
    if user is None:
        print(f"No user found with username '{username}'.")
        sys.exit(1)

    new_password = getpass.getpass("New password: ")
    confirm_password = getpass.getpass("Confirm new password: ")
    if new_password != confirm_password:
        print("Passwords do not match. Nothing was changed.")
        sys.exit(1)
    if len(new_password) < 8:
        print("Password should be at least 8 characters. Nothing was changed.")
        sys.exit(1)

    new_hash = auth_service.hash_password(new_password)
    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user.user_id))
    db.commit()

    print(f"\nPassword for '{username}' has been reset. "
          f"You can now log in with the new password.")


if __name__ == "__main__":
    main()
