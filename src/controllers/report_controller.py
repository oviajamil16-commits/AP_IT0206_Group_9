"""Controller layer for Reports. Uses pandas to aggregate data already
fetched through the normal repository layer (no raw SQL here — pandas
operates on plain Python objects handed to it, keeping the MVC boundary
intact), and matplotlib to render a chart to a PNG file."""

import os
import sys

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless-safe backend — no display required
import matplotlib.pyplot as plt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from controllers.auth_controller import AuthController  # noqa: E402
from repositories.employee_repository import EmployeeRepository  # noqa: E402
from repositories.department_repository import DepartmentRepository  # noqa: E402
from repositories.payroll_repository import PayrollRepository  # noqa: E402
from repositories.attendance_repository import AttendanceRepository  # noqa: E402
from utils.logger import get_logger  # noqa: E402

logger = get_logger("controllers.report")


class ReportController:
    def __init__(self, auth_controller: AuthController, employee_repo: EmployeeRepository,
                 department_repo: DepartmentRepository, payroll_repo: PayrollRepository,
                 attendance_repo: AttendanceRepository, output_dir: str):
        self._auth = auth_controller
        self._employees = employee_repo
        self._departments = department_repo
        self._payroll = payroll_repo
        self._attendance = attendance_repo
        self._output_dir = output_dir
        os.makedirs(self._output_dir, exist_ok=True)

    def headcount_by_department(self):
        """Returns a pandas DataFrame: department name -> employee count,
        and the chart file path."""
        self._auth.require_permission("report.read")
        employees = self._employees.all()
        departments = {d.department_id: d.name for d in self._departments.all()}

        df = pd.DataFrame([{"department_id": e.department_id} for e in employees])
        if df.empty:
            counts = pd.Series(dtype=int)
        else:
            df["department"] = df["department_id"].map(departments).fillna("Unassigned")
            counts = df.groupby("department").size().sort_values(ascending=False)

        chart_path = os.path.join(self._output_dir, "headcount_by_department.png")
        self._bar_chart(counts, "Headcount by Department", "Department", "Employees", chart_path)
        return counts, chart_path

    def payroll_cost_summary(self, period: str):
        """Returns (total, average, count, chart_path) for a given period."""
        self._auth.require_permission("report.read")
        records = self._payroll.find_by_period(period)
        if not records:
            return 0.0, 0.0, 0, None

        df = pd.DataFrame([{"employee_id": p.employee_id, "net_pay": p.net_pay} for p in records])
        total = round(df["net_pay"].sum(), 2)
        average = round(df["net_pay"].mean(), 2)

        chart_path = os.path.join(self._output_dir, f"payroll_{period}.png")
        series = df.set_index("employee_id")["net_pay"]
        self._bar_chart(series, f"Net Pay by Employee \u2014 {period}", "Employee ID", "Net pay", chart_path)
        return total, average, len(records), chart_path

    def attendance_summary(self):
        """Returns a pandas Series: status -> count, across all records."""
        self._auth.require_permission("report.read")
        records = self._attendance.all()
        if not records:
            return pd.Series(dtype=int), None

        df = pd.DataFrame([{"status": r.status} for r in records])
        counts = df.groupby("status").size()

        chart_path = os.path.join(self._output_dir, "attendance_summary.png")
        self._bar_chart(counts, "Attendance Summary", "Status", "Count", chart_path)
        return counts, chart_path

    def _bar_chart(self, series, title, xlabel, ylabel, path) -> None:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        if len(series) > 0:
            series.plot(kind="bar", ax=ax, color="#1F3864")
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        plt.tight_layout()
        fig.savefig(path, dpi=140)
        plt.close(fig)
        logger.info("Saved chart to %s", path)
