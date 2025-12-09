# MicroCanvas Prototype

MicroCanvas is a CMPE 131 mini-LMS focused on sprint-style task tracking for software project courses. It provides a lightweight dashboard for students plus instructor tooling to post tasks, organize teams, and monitor progress.

## Quick start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask --app run.py run   # or python run.py
```

On the first launch the database seeds demo data automatically. Ready-made accounts:

| Role       | Email                 | Password |
| ---------- | --------------------- | -------- |
| Instructor | prof@example.com      | (none)   |
| TA         | ta@example.com        | (none)   |
| Student    | student@example.com   | (none)   |

Enter any other email on the login form to auto-create a new student profile.

## Implemented MVP features

- Login/logout via Flask-Login, with flash notifications for key actions.
- Dashboard showing enrolled courses and upcoming tasks.
- Course board grouped by task status with instructor-only task creation and grading forms.
- Ability for students to toggle tasks between "to-do" and "done".
- Team management: instructors create teams, assign members, and view team-specific task boards.
- Responsive navigation (Home, Courses, Feature, Login/Logout) and simple CSS styling.
- SQLite-backed models for `User`, `Course`, `Task`, `CourseMembership`, `Team`, and `TeamMembership`.

## Tests

Run the automated suite with:

```bash
pytest
```

### Testing plan

- **Routes & flows:** `tests/test_app.py` hits login, dashboard, instructor task creation, and student task toggling to verify WTForms and role rules.
- **Models:** The same tests assert SQLAlchemy persistence by checking that `User`, `Course`, and `Task` records are created/updated appropriately.
- **Structure:** Shared fixtures live in `tests/conftest.py`, which spins up an in-memory SQLite database for each run.
- **Framework:** Pytest 9.x drives the suite (listed in `requirements.txt`).
