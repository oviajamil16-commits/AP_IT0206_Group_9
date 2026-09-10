"""Date helpers shared by LeaveRepository (finding leave overlapping a
payroll period) and PayrollController (calculating exactly how many of
those days fall inside that period). Split out as its own module because
both needed the same period-boundary and interval-overlap logic, and a
previous version had each compute it differently -- which was the root
cause of a month-boundary deduction bug."""

import calendar
from datetime import date


def period_bounds(period: str) -> tuple[str, str]:
    """Given 'YYYY-MM', return (first_day, last_day) as 'YYYY-MM-DD' strings."""
    year, month = (int(p) for p in period.split("-"))
    last_day = calendar.monthrange(year, month)[1]
    start = date(year, month, 1).isoformat()
    end = date(year, month, last_day).isoformat()
    return start, end


def overlap_days(a_start: str, a_end: str, b_start: str, b_end: str) -> int:
    """Number of days (inclusive) where date range [a_start, a_end] overlaps
    [b_start, b_end]. All dates are 'YYYY-MM-DD' strings. Returns 0 if the
    ranges don't overlap at all."""
    latest_start = max(a_start, b_start)
    earliest_end = min(a_end, b_end)
    if latest_start > earliest_end:
        return 0
    d1 = date.fromisoformat(latest_start)
    d2 = date.fromisoformat(earliest_end)
    return (d2 - d1).days + 1
