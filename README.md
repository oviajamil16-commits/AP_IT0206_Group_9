# Employee Management System 

IT0206 Advanced Computer Programming 2 — Team Project (Assessment 2)

## What's built so far

**All six planned modules are now complete and verified end-to-end**, on top of the foundation (database, auth, login):

**Foundation:**
- SQLite schema with 7 related tables (`database/schema.sql`)
- `DatabaseConnection` with parameterised queries and commit/rollback transactions
- `User` domain model (abstract base) with `Administrator` and `HRStaff` subclasses demonstrating inheritance and polymorphism
- `UserRepository`, `AuthService` (PBKDF2-HMAC hashing — see note below), `AuthController`
- `LoginView` / `MainMenuView`, app-wide logging, custom exception hierarchy, first-run bootstrap

**Employee CRUD** (Menu 1): `Person`→`Employee`, `Department`, `Position` — full CRUD, search/filter, FK-violation protection.

**Attendance** (Menu 2): clock in/out with double-clock-in prevention, mark absent, a computed `hours_worked` property, view by employee or by date.

**Leave requests** (Menu 3): submit → approve/reject workflow with the state machine enforced *on the domain model itself* (`LeaveRequest.approve()`/`.reject()` refuse to fire on a non-pending request, not just at the controller layer). HR Staff can submit; only Administrators can approve/reject.

**Payroll** (Menu 4) — the SRS's core transactional workflow: `PayrollController.run_payroll(period)` pulls each active employee's position grade as base salary, looks up their **approved, unpaid** leave requests overlapping that period, and converts unpaid days into a real deduction (`daily_rate × days`). Re-running a period skips employees already paid. Verified: 3 days unpaid leave on a 3000 base salary correctly deducts 300.

**Reports** (Menu 5): pandas-aggregated headcount-by-department, payroll cost summary, and attendance summary, each rendered as a real matplotlib bar chart saved to `data/exports/`. Menu option 4 is a genuine external HTTP call (`requests`) to the free Nager.Date public holiday API — opt-in only, so the app stays fully usable offline; a blocked/failed request degrades to an empty result with a logged warning rather than crashing.

**CSV/JSON import/export** (Employee menu, options 8–9): bulk-import employees from CSV or JSON with per-row error collection (one bad row doesn't abort the batch), and export the current employee list to either format. Sample files are in `data/imports/`.

**Import/export note:** every imported row goes through `EmployeeController.add_employee()` — the exact same validation and permission checks as typing it in by hand.

## Running it

```bash
cd src
python main.py
```

First run prints a generated admin password — save it, you'll need it to log in.

## Testing it

Real pytest could not be installed in the sandbox this was built in (the
egress proxy blocks pypi.org despite it being a nominally allowed
domain). `run_tests_shim.py` is a small, fully-disclosed compatibility
shim implementing just the pytest features the suite actually uses
(`@pytest.fixture`, `pytest.raises`, `tmp_path`) and runs the real,
unmodified test files:

```bash
python run_tests_shim.py
```

Currently: **71/71 tests pass** (real execution, real temporary SQLite
databases, plus a fully-real pandas/matplotlib chart-generation test and
a mocked-network test suite for the holiday API — see the Test Report
for full output). Still run genuine pytest on a normal machine before
treating this as final evidence:

```bash
pip install pytest pytest-cov
pytest tests/ -v --cov=src
```

- `tests/test_services.py` — password hashing, user repository CRUD, login, permissions (13 tests)
- `tests/test_models.py` — Employee/Department/Position model validation (10 tests)
- `tests/test_repositories.py` — Employee/Department/Position CRUD, search, FK protection, controller validation (15 tests)
- `tests/test_attendance_leave_payroll.py` — clock in/out, leave state machine, payroll deduction math (19 tests)

## A note on password hashing

`AuthService.hash_password()` uses Python's built-in `hashlib.pbkdf2_hmac`
with a random per-user salt (200,000 iterations) rather than `bcrypt`,
because this environment doesn't have network access to install
third-party packages while building the scaffold. It's a genuinely secure
approach, but if you want `bcrypt` for the "additional libraries" rubric
credit (Section 6.2.7), it's an easy swap — only `hash_password()` and
`verify_password()` in `services/auth_service.py` need to change; nothing
else in the codebase touches password hashes directly.

## Next steps for the team

1. Split Attendance, Leave, and Payroll across the team — each is a
   self-contained vertical slice following the exact pattern already
   proven in Employee: `models/<entity>.py` →
   `repositories/<entity>_repository.py` →
   `controllers/<entity>_controller.py` → `views/<entity>_view.py`.
2. Leave submission/approval should update `leave_requests.status` and,
   per the SRS's core transactional workflow, feed into a payroll
   deduction — that's the natural link between the Leave and Payroll
   modules.
3. Wire each new controller/view into `main.py`, replacing the matching
   `show_not_implemented()` branch in `main_menu_view.py`.
4. Add `pandas`/`matplotlib` for the Reports module and `requests` for
   at least one external HTTP interaction — both still unused, and both
   required by Section 6.2.7 of the brief.
5. Disclose this AI-assisted code in your Technical Documentation per
   the assessment's AI Usage Policy (Section 16) — note what was
   AI-generated as scaffold versus what your team built and understood.

## Team

<!-- List team members and roles here per Section 13.2 of the brief -->
