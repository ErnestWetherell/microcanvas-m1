from flask import (
    render_template,
    redirect,
    url_for,
    flash,
)
from flask_login import current_user, login_required
from app.main import main_bp
from app import db
from app.models import Course, Task, User
from app.forms import TaskForm, GradeForm


def _ensure_sample_data():
    """Create demo courses and tasks if DB is empty.

    Combined with auth._ensure_demo_users(), this gives us:
    - Users: instructor, ta, student
    - Courses: CMPE 131, ISE 140
    - A few tasks in each course
    """
    if Course.query.first() is not None:
        return

    course1 = Course(code="CMPE 131", title="Software Engineering")
    course2 = Course(code="ISE 140", title="Production & Ops Mgmt")

    db.session.add_all([course1, course2])
    db.session.commit()

    t1 = Task(
        title="Project proposal",
        description="Submit 1-page project idea.",
        course=course1,
        status="todo",
        points=50,
    )
    t2 = Task(
        title="Unit test suite",
        description="Add tests for your Flask routes.",
        course=course1,
        status="in_progress",
        points=100,
    )
    t3 = Task(
        title="HW 3 – Forecasting",
        description="Solve forecasting problems 1–5.",
        course=course2,
        status="todo",
        points=75,
    )

    db.session.add_all([t1, t2, t3])
    db.session.commit()


@main_bp.route("/")
def index():
    _ensure_sample_data()

    courses = Course.query.all()

    upcoming_tasks = Task.query.order_by(Task.due_date.is_(True)).limit(5).all()

    return render_template(
        "main/index.html",
        courses=courses,
        upcoming_tasks=upcoming_tasks,
    )


@main_bp.route("/courses/<int:course_id>")
@login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)

    tasks_todo = [t for t in course.tasks if t.status == "todo"]
    tasks_in_progress = [t for t in course.tasks if t.status == "in_progress"]
    tasks_done = [t for t in course.tasks if t.status == "done"]

    return render_template(
        "main/course.html",
        course=course,
        tasks_todo=tasks_todo,
        tasks_in_progress=tasks_in_progress,
        tasks_done=tasks_done,
    )


@main_bp.route("/courses/<int:course_id>/tasks/new", methods=["GET", "POST"])
@login_required
def new_task(course_id):
    course = Course.query.get_or_404(course_id)

    if not current_user.is_instructor:
        flash("Only instructors can create tasks.")
        return redirect(url_for("main.course_detail", course_id=course.id))

    form = TaskForm()

    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            points=form.points.data or 100,
            course=course,
        )
        db.session.add(task)
        db.session.commit()
        flash("Task created.")
        return redirect(url_for("main.course_detail", course_id=course.id))

    # set default points
    if form.points.data is None:
        form.points.data = 100

    return render_template("main/task_form.html", form=form, course=course)


@main_bp.route("/tasks/<int:task_id>/toggle")
@login_required
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)

    # simple toggle between todo and done
    if task.status == "done":
        task.status = "todo"
    else:
        task.status = "done"

    db.session.commit()
    flash("Task status updated.")
    return redirect(url_for("main.course_detail", course_id=task.course_id))


@main_bp.route("/tasks/<int:task_id>/grade", methods=["GET", "POST"])
@login_required
def grade_task(task_id):
    """Prototype-grade: instructor sets a single score for the task."""
    if not current_user.is_instructor:
        flash("Only instructors can enter grades.")
        return redirect(url_for("main.index"))

    task = Task.query.get_or_404(task_id)
    form = GradeForm()

    if form.validate_on_submit():
        task.score = form.score.data
        db.session.commit()
        flash("Grade saved.")
        return redirect(url_for("main.course_detail", course_id=task.course_id))

    # preload existing score
    if task.score is not None and form.score.data is None:
        form.score.data = task.score

    return render_template("main/grade_form.html", form=form, task=task)


@main_bp.route("/feature")
def feature():
    # still just a stub; can describe future ideas here
    return render_template("main/feature.html")
