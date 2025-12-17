# MicroCanvas Protype

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
- Dashboard showing enrolled courses and upcoming tasks (authentication required).
- Course board grouped by task status with inline dropdowns to move cards plus instructor-only task creation and grading forms.
- Students and instructors can move tasks across the To Do / In Progress / Done columns using the new status-update form.
- Team management: instructors create teams, assign members, and view team-specific task boards.
- Teaching assistants can review task cards and leave quick feedback comments without the full instructor toolset.
- Simple analytics dashboard for instructors/TAs summarizing per-course completion rates and late-task counts.
- Edge cases: custom 404/400/403 pages handle missing content, bad inputs, and unauthorized instructor pages gracefully.
- Responsive navigation (Home, Courses, Feature, Login/Logout) and simple CSS styling.
- SQLite-backed models for `User`, `Course`, `Task`, `CourseMembership`, `Team`, and `TeamMembership`.

## Tests

Run the automated suite with:

```bash
pytest
```

### Testing plan

- **Routes & flows:** `tests/test_app.py` hits login, dashboard, instructor task creation, both student/instructor task status updates, TA feedback comments, the analytics page, and full course/team pages via `client.get()` to verify WTForms, template rendering, and redirects (covering `/courses/<id>`, `/teams/<id>`, `/analytics`, and `/tasks/<id>/status`/`/tasks/<id>/comments`).
- **Models:** The same tests assert SQLAlchemy persistence by checking that `User`, `Course`, and `Task` records are created/updated appropriately.
- **Structure:** Shared fixtures live in `tests/conftest.py`, which spins up an in-memory SQLite database for each run.
- **Integration coverage:** Dedicated `client.get()` requests confirm that course and team templates render the correct sections and that redirects behave as expected.
- **Framework:** Pytest 9.x drives the suite (listed in `requirements.txt`).
- **Edge cases:** Additional tests hit nonexistent routes, tampered status updates, and unauthorized instructor-only pages to ensure the custom 404/400/403 pages respond correctly.
