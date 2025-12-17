from app import db
from app.models import Course, Task, TaskComment, User
from app.main.routes import _ensure_sample_data


def seed_demo(app):
    """Create sample data without requiring a logged-in request."""
    with app.app_context():
        _ensure_sample_data()


def login(client, email):
    return client.post(
        "/auth/login",
        data={"email": email},
        follow_redirects=True,
    )


def test_login_creates_new_user(client, app):
    response = login(client, "newstudent@example.com")
    assert response.status_code == 200
    assert b"Logged in as newstudent@example.com" in response.data

    with app.app_context():
        assert User.query.filter_by(email="newstudent@example.com").first() is not None


def test_dashboard_requires_auth(client):
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]


def test_dashboard_lists_courses(client, app):
    seed_demo(app)
    login(client, "student@example.com")
    resp = client.get("/", follow_redirects=True)
    assert b"CMPE 131" in resp.data


def test_instructor_can_create_task(client, app):
    seed_demo(app)
    login(client, "prof@example.com")
    with app.app_context():
        course = Course.query.filter_by(code="CMPE 131").first()
        tasks_before = len(course.tasks)

    resp = client.post(
        f"/courses/{course.id}/tasks/new",
        data={
            "title": "Prototype review",
            "description": "Discuss MVP status",
            "points": 75,
            "team_id": 0,
        },
        follow_redirects=True,
    )
    assert b"Task created" in resp.data

    with app.app_context():
        refreshed = db.session.get(Course, course.id)
        assert len(refreshed.tasks) == tasks_before + 1


def test_course_board_renders_columns(client, app):
    seed_demo(app)
    login(client, "student@example.com")
    with app.app_context():
        course = Course.query.filter_by(code="CMPE 131").first()

    resp = client.get(f"/courses/{course.id}", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Task board" in resp.data
    assert b"In progress" in resp.data
    assert b"Team" in resp.data


def test_courses_requires_auth(client):
    resp = client.get("/courses")
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]


def test_student_updates_task_status(client, app):
    seed_demo(app)
    login(client, "student@example.com")
    with app.app_context():
        task = Task.query.first()
        assert task is not None

    resp = client.post(
        f"/tasks/{task.id}/status",
        data={"status": Task.STATUS_DONE},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Task status updated" in resp.data

    with app.app_context():
        updated = db.session.get(Task, task.id)
        assert updated.status == Task.STATUS_DONE


def test_instructor_can_move_task_between_columns(client, app):
    seed_demo(app)
    login(client, "prof@example.com")
    with app.app_context():
        task = Task.query.filter_by(status=Task.STATUS_IN_PROGRESS).first()
        assert task is not None

    resp = client.post(
        f"/tasks/{task.id}/status",
        data={"status": Task.STATUS_TODO},
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        refreshed = db.session.get(Task, task.id)
        assert refreshed.status == Task.STATUS_TODO


def test_ta_can_leave_feedback_comment(client, app):
    seed_demo(app)
    login(client, "ta@example.com")
    with app.app_context():
        task = Task.query.first()
        assert TaskComment.query.count() == 0

    resp = client.post(
        f"/tasks/{task.id}/comments",
        data={"body": "Reviewed!"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Feedback posted" in resp.data

    with app.app_context():
        comments = TaskComment.query.filter_by(task_id=task.id).all()
        assert len(comments) == 1
        assert comments[0].author.role == "ta"


def test_student_cannot_leave_feedback(client, app):
    seed_demo(app)
    login(client, "student@example.com")
    with app.app_context():
        task = Task.query.first()

    resp = client.post(
        f"/tasks/{task.id}/comments",
        data={"body": "I should not do this"},
    )
    assert resp.status_code == 403
    assert b"Access denied" in resp.data

    with app.app_context():
        assert TaskComment.query.count() == 0


def test_team_page_renders_members_and_tasks(client, app):
    seed_demo(app)
    login(client, "student@example.com")
    with app.app_context():
        team = Task.query.filter(Task.team_id.isnot(None)).first().team

    resp = client.get(f"/teams/{team.id}", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Members" in resp.data
    assert b"Team tasks" in resp.data


def test_student_cannot_access_instructor_task_page(client, app):
    seed_demo(app)
    login(client, "student@example.com")
    with app.app_context():
        course = Course.query.filter_by(code="CMPE 131").first()

    resp = client.get(f"/courses/{course.id}/tasks/new")
    assert resp.status_code == 403
    assert b"Access denied" in resp.data


def test_instructor_can_view_analytics(client, app):
    seed_demo(app)
    login(client, "prof@example.com")

    resp = client.get("/analytics")
    assert resp.status_code == 200
    assert b"Course analytics" in resp.data
    assert b"CMPE 131" in resp.data


def test_student_cannot_view_analytics(client, app):
    seed_demo(app)
    login(client, "student@example.com")

    resp = client.get("/analytics")
    assert resp.status_code == 403


def test_missing_page_shows_custom_404(client, app):
    seed_demo(app)
    login(client, "student@example.com")
    resp = client.get("/totally-missing")
    assert resp.status_code == 404
    assert b"Page not found" in resp.data


def test_bad_status_input_returns_400_page(client, app):
    seed_demo(app)
    login(client, "student@example.com")
    with app.app_context():
        task = Task.query.first()
    resp = client.post(
        f"/tasks/{task.id}/status",
        data={"status": "not-valid"},
    )
    assert resp.status_code == 400
    assert b"We couldn't process that" in resp.data
