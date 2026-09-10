"""Custom exception hierarchy for the Employee Management System.

All application-specific exceptions derive from EMSException so calling
code can catch broadly (``except EMSException``) or narrowly
(``except RecordNotFoundException``) depending on what it needs to do.
"""


class EMSException(Exception):
    """Base class for all EMS application-specific exceptions."""


class InvalidCredentialsException(EMSException):
    """Raised when a login attempt fails (unknown user or wrong password)."""

    def __init__(self, message: str = "Invalid username or password."):
        super().__init__(message)


class RecordNotFoundException(EMSException):
    """Raised when a lookup by id/key finds no matching record."""

    def __init__(self, entity: str, identifier):
        message = f"{entity} with identifier '{identifier}' was not found."
        super().__init__(message)
        self.entity = entity
        self.identifier = identifier


class DuplicateRecordException(EMSException):
    """Raised when an insert would violate a uniqueness constraint."""

    def __init__(self, entity: str, field: str, value):
        message = f"{entity} with {field} '{value}' already exists."
        super().__init__(message)
        self.entity = entity
        self.field = field
        self.value = value


class ValidationException(EMSException):
    """Raised when user-supplied input fails validation rules."""
