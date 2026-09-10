-- Employee Management System — Database Schema
-- SQLite. All foreign keys enforced (PRAGMA foreign_keys = ON is set by the app).

CREATE TABLE IF NOT EXISTS departments (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    name                 TEXT NOT NULL UNIQUE,
    manager_employee_id  INTEGER,
    FOREIGN KEY (manager_employee_id) REFERENCES employees(id)
);

CREATE TABLE IF NOT EXISTS positions (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    title                TEXT NOT NULL,
    department_id        INTEGER NOT NULL,
    base_salary_grade    REAL NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS employees (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name           TEXT NOT NULL,
    last_name            TEXT NOT NULL,
    date_of_birth        TEXT,
    email                TEXT UNIQUE,
    phone                TEXT,
    hire_date            TEXT NOT NULL,
    department_id        INTEGER,
    position_id          INTEGER,
    status               TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'terminated')),
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (position_id) REFERENCES positions(id)
);

CREATE TABLE IF NOT EXISTS users (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    username             TEXT NOT NULL UNIQUE,
    password_hash        TEXT NOT NULL,
    role                 TEXT NOT NULL CHECK (role IN ('ADMIN', 'HR_STAFF')),
    employee_id          INTEGER,
    created_at           TEXT NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

CREATE TABLE IF NOT EXISTS attendance (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id          INTEGER NOT NULL,
    date                 TEXT NOT NULL,
    time_in              TEXT,
    time_out             TEXT,
    status               TEXT NOT NULL DEFAULT 'present' CHECK (status IN ('present', 'absent', 'late')),
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

CREATE TABLE IF NOT EXISTS leave_requests (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id          INTEGER NOT NULL,
    leave_type           TEXT NOT NULL,
    start_date           TEXT NOT NULL,
    end_date             TEXT NOT NULL,
    status               TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    approved_by          INTEGER,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS payroll (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id          INTEGER NOT NULL,
    period               TEXT NOT NULL,
    base_salary          REAL NOT NULL,
    allowances           REAL NOT NULL DEFAULT 0,
    deductions           REAL NOT NULL DEFAULT 0,
    net_pay              REAL NOT NULL,
    generated_date       TEXT NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
