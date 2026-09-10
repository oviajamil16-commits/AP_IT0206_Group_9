"""Department: a simple structural entity that Employees and Positions
belong to."""


class Department:
    def __init__(self, name: str, department_id: int = None,
                 manager_employee_id: int = None):
        self.department_id = department_id
        self.name = name
        self.manager_employee_id = manager_employee_id

    def __eq__(self, other) -> bool:
        return isinstance(other, Department) and self.department_id == other.department_id

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Department(id={self.department_id}, name={self.name!r})"
