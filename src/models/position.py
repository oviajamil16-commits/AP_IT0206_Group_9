"""Position: a job title within a Department, carrying a base salary grade
that Payroll will read from later."""


class Position:
    def __init__(self, title: str, department_id: int, base_salary_grade: float,
                 position_id: int = None):
        self.position_id = position_id
        self.title = title
        self.department_id = department_id
        self.base_salary_grade = base_salary_grade

    def __eq__(self, other) -> bool:
        return isinstance(other, Position) and self.position_id == other.position_id

    def __str__(self) -> str:
        return self.title

    def __repr__(self) -> str:
        return f"Position(id={self.position_id}, title={self.title!r})"
