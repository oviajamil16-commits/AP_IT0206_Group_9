"""Person: abstract base for anyone the system tracks by name and
contact details. Employee is the only concrete subclass today, but the
shape exists so a future subclass (e.g. Applicant) could reuse it."""

import os
import sys
from abc import ABC, abstractmethod

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exceptions.custom_exceptions import ValidationException  # noqa: E402


class Person(ABC):
    def __init__(self, first_name: str, last_name: str, date_of_birth: str = None,
                 email: str = None, phone: str = None):
        self.first_name = first_name
        self.last_name = last_name
        self.date_of_birth = date_of_birth
        self.email = email
        self.phone = phone

    # -- encapsulated fields with validating setters ---------------------
    @property
    def first_name(self) -> str:
        return self._first_name

    @first_name.setter
    def first_name(self, value: str) -> None:
        if not value or not str(value).strip():
            raise ValidationException("First name cannot be empty.")
        self._first_name = str(value).strip()

    @property
    def last_name(self) -> str:
        return self._last_name

    @last_name.setter
    def last_name(self, value: str) -> None:
        if not value or not str(value).strip():
            raise ValidationException("Last name cannot be empty.")
        self._last_name = str(value).strip()

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def date_of_birth(self):
        return self._date_of_birth

    @date_of_birth.setter
    def date_of_birth(self, value) -> None:
        self._date_of_birth = value

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value) -> None:
        self._email = str(value).strip() if value else None

    @property
    def phone(self):
        return self._phone

    @phone.setter
    def phone(self, value) -> None:
        self._phone = value

    @abstractmethod
    def role_label(self) -> str:
        """Human-readable label for what kind of Person this is."""

    def __str__(self) -> str:
        return self.full_name
