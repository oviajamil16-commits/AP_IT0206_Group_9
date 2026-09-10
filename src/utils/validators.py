"""Reusable input-validation helpers shared across controllers.

Centralising validation here (rather than scattering isinstance/regex
checks through each controller) keeps the business-rule wording
consistent and makes it trivial to test in isolation.
"""

import os
import re
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exceptions.custom_exceptions import ValidationException  # noqa: E402

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Validator:
    @staticmethod
    def require_non_empty(value: str, field_name: str) -> str:
        if value is None or not str(value).strip():
            raise ValidationException(f"{field_name} cannot be empty.")
        return str(value).strip()

    @staticmethod
    def valid_date(value: str, field_name: str) -> str:
        value = str(value).strip()
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValidationException(f"{field_name} must be in YYYY-MM-DD format.")
        return value

    @staticmethod
    def valid_email(value: str) -> str:
        value = str(value).strip()
        if value and not _EMAIL_RE.match(value):
            raise ValidationException("Email address is not valid.")
        return value

    @staticmethod
    def valid_choice(value, choices, field_name: str):
        if value not in choices:
            raise ValidationException(f"{field_name} must be one of {sorted(choices)}.")
        return value

    @staticmethod
    def valid_positive_number(value, field_name: str) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ValidationException(f"{field_name} must be a number.")
        if number < 0:
            raise ValidationException(f"{field_name} cannot be negative.")
        return number

    @staticmethod
    def valid_int(value, field_name: str) -> int:
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            raise ValidationException(f"{field_name} must be a whole number.")
