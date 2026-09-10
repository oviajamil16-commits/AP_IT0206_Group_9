"""LeaveRequest: an employee's request for time off, carrying its own
approval state machine (pending -> approved/rejected)."""

import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from exceptions.custom_exceptions import ValidationException  # noqa: E402


class LeaveRequest:
    STATUSES = {"pending", "approved", "rejected"}
    LEAVE_TYPES = {"annual", "sick", "unpaid", "other"}

    def __init__(self, employee_id: int, leave_type: str, start_date: str, end_date: str,
                 leave_id: int = None, status: str = "pending", approved_by: int = None):
        self.leave_id = leave_id
        self.employee_id = employee_id
        self.leave_type = leave_type
        self.start_date = start_date
        self.end_date = end_date
        self.status = status
        self.approved_by = approved_by

    @property
    def leave_type(self) -> str:
        return self._leave_type

    @leave_type.setter
    def leave_type(self, value: str) -> None:
        if value not in self.LEAVE_TYPES:
            raise ValidationException(f"Leave type must be one of {sorted(self.LEAVE_TYPES)}.")
        self._leave_type = value

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        if value not in self.STATUSES:
            raise ValidationException(f"Leave status must be one of {sorted(self.STATUSES)}.")
        self._status = value

    @property
    def duration_days(self) -> int:
        """Inclusive day count between start_date and end_date."""
        fmt = "%Y-%m-%d"
        start = datetime.strptime(self.start_date, fmt)
        end = datetime.strptime(self.end_date, fmt)
        return (end - start).days + 1

    @property
    def is_pending(self) -> bool:
        return self.status == "pending"

    def approve(self, approver_user_id: int) -> None:
        """Domain-level state transition: only a pending request can be approved."""
        if not self.is_pending:
            raise ValidationException(
                f"Cannot approve a leave request that is already '{self.status}'."
            )
        self.status = "approved"
        self.approved_by = approver_user_id

    def reject(self, approver_user_id: int) -> None:
        if not self.is_pending:
            raise ValidationException(
                f"Cannot reject a leave request that is already '{self.status}'."
            )
        self.status = "rejected"
        self.approved_by = approver_user_id

    def __eq__(self, other) -> bool:
        return isinstance(other, LeaveRequest) and self.leave_id == other.leave_id

    def __repr__(self) -> str:
        return (f"LeaveRequest(id={self.leave_id}, employee_id={self.employee_id}, "
                f"type={self.leave_type!r}, status={self.status!r})")
