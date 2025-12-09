from app.models import Course, Task, User


def seed_demo(client):
    """Hit the dashboard once so sample data is created."""
    client.get("/")


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


def test_dashboard_lists_courses(client):
    seed_demo(client)
    login(client, "student@example.com")
    resp = client.get("/", follow_redirects=True)
    assert b"CMPE 131" in resp.data


def test_instructor_can_create_task(client, app):
    seed_demo(client)
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
        refreshed = Course.query.get(course.id)
        assert len(refreshed.tasks) == tasks_before + 1


def test_student_toggle_task(client, app):
    seed_demo(client)
    login(client, "student@example.com")
    with app.app_context():
        task = Task.query.first()
        original = task.status

    resp = client.get(f"/tasks/{task.id}/toggle", follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        updated = Task.query.get(task.id)
        assert updated.status != original
