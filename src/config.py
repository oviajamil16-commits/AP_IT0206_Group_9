"""Application configuration and constants."""

import os

# Project root = two levels up from this file (src/config.py -> project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASE_DIR = os.path.join(BASE_DIR, "database")
DATABASE_PATH = os.path.join(DATABASE_DIR, "app.db")
SCHEMA_PATH = os.path.join(DATABASE_DIR, "schema.sql")

LOGS_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE_PATH = os.path.join(LOGS_DIR, "app.log")

DATA_IMPORTS_DIR = os.path.join(BASE_DIR, "data", "imports")
DATA_EXPORTS_DIR = os.path.join(BASE_DIR, "data", "exports")

# Roles
ROLE_ADMIN = "ADMIN"
ROLE_HR_STAFF = "HR_STAFF"

# First-run default administrator account.
# The password is intentionally NOT hardcoded here — main.py prints a
# freshly generated one to the console the first time the app runs,
# so nobody can grep a real password out of source control.
DEFAULT_ADMIN_USERNAME = "admin"

MAX_LOGIN_ATTEMPTS = 3
