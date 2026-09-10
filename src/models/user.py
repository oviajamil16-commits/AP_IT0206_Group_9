"""User domain models.

User is an abstract base class; Administrator and HRStaff are concrete
roles. Putting permission logic on the subclasses (rather than an
if/else on a role string scattered through the controllers) is a
deliberate OOP choice: calling code just does

    if current_user.can(action):
        ...

and polymorphism picks the right answer for whichever role is logged in.
"""

from abc import ABC, abstractmethod
from datetime import datetime


class User(ABC):
    """Abstract base for any authenticated EMS user."""

    def __init__(self, user_id: int, username: str, password_hash: str,
                 employee_id: int = None, created_at: str = None):
        self._user_id = user_id
        self._username = username
        self._password_hash = password_hash
        self._employee_id = employee_id
        self._created_at = created_at or datetime.now().isoformat(timespec="seconds")

    # -- read-only properties: identity fields should not be mutated
    #    after construction by ordinary application code -------------
    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @property
    def employee_id(self):
        return self._employee_id

    @property
    def created_at(self) -> str:
        return self._created_at

    @property
    @abstractmethod
    def role(self) -> str:
        """Role code stored in the database ('ADMIN' / 'HR_STAFF')."""

    @abstractmethod
    def can(self, action: str) -> bool:
        """Return True if this user's role is permitted to perform `action`.

        `action` is one of the short permission codes used across the
        controllers, e.g. 'employee.delete', 'payroll.run', 'leave.approve'.
        """

    def __eq__(self, other) -> bool:
        return isinstance(other, User) and self.user_id == other.user_id

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.user_id}, username={self.username!r})"


class Administrator(User):
    """Full-access role: can manage every entity, including payroll and users."""

    _PERMISSIONS = {
        "employee.create", "employee.read", "employee.update", "employee.delete",
        "department.create", "department.read", "department.update", "department.delete",
        "position.create", "position.read", "position.update", "position.delete",
        "attendance.create", "attendance.read", "attendance.update",
        "leave.create", "leave.read", "leave.approve",
        "payroll.run", "payroll.read",
        "report.read",
        "user.manage",
    }

    @property
    def role(self) -> str:
        return "ADMIN"

    def can(self, action: str) -> bool:
        return action in self._PERMISSIONS


class HRStaff(User):
    """Restricted role: day-to-day HR operations, no deletes, no payroll changes."""

    _PERMISSIONS = {
        "employee.create", "employee.read", "employee.update",
        "department.read",
        "position.read",
        "attendance.create", "attendance.read", "attendance.update",
        "leave.create", "leave.read",
        "payroll.read",
        "report.read",
    }

    @property
    def role(self) -> str:
        return "HR_STAFF"

    def can(self, action: str) -> bool:
        return action in self._PERMISSIONS


def build_user(row) -> User:
    """Factory: turn a `users` table row into the correct User subclass.

    Row is expected to be a sqlite3.Row (or dict-like) with columns
    id, username, password_hash, role, employee_id, created_at.
    """
    role = row["role"]
    kwargs = dict(
        user_id=row["id"],
        username=row["username"],
        password_hash=row["password_hash"],
        employee_id=row["employee_id"],
        created_at=row["created_at"],
    )
    if role == "ADMIN":
        return Administrator(**kwargs)
    elif role == "HR_STAFF":
        return HRStaff(**kwargs)
    raise ValueError(f"Unknown user role in database: {role!r}")
