from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app.main import main_bp
from app import db
from app.models import (
    Course,
    CourseMembership,
    Task,
    TaskComment,
    Team,
    TeamMembership,
    User,
)
from app.forms import (
    TaskForm,
    TaskStatusForm,
    TaskCommentForm,
    GradeForm,
    TeamForm,
    TeamMemberForm,
)


def _ensure_sample_data():
    """Create demo courses and tasks if DB is empty.

    Combined with auth._ensure_demo_users(), this gives us:
    - Users: instructor, ta, student
    - Courses: CMPE 131, ISE 140
    - A few tasks in each course
    """
    if Course.query.first() is not None:
        return

    def user(email, role):
        record = User.query.filter_by(email=email).first()
        if record is None:
            record = User(email=email, role=role)
            db.session.add(record)
            db.session.flush()
        return record

    prof = user("prof@example.com", "instructor")
    ta = user("ta@example.com", "ta")
    student = user("student@example.com", "student")
    student2 = user("student2@example.com", "student")

    course1 = Course(code="CMPE 131", title="Software Engineering")
    course2 = Course(code="ISE 140", title="Operations Planning and Control")
    db.session.add_all([course1, course2])
    db.session.flush()

    memberships = [
        CourseMembership(user=prof, course=course1, role="instructor"),
        CourseMembership(user=ta, course=course1, role="ta"),
        CourseMembership(user=student, course=course1, role="student"),
        CourseMembership(user=student2, course=course1, role="student"),
        CourseMembership(user=prof, course=course2, role="instructor"),
        CourseMembership(user=student, course=course2, role="student"),
    ]
    db.session.add_all(memberships)
    db.session.flush()

    alpha = Team(name="Velocity", course=course1)
    beta = Team(name="Nimbus", course=course1)
    db.session.add_all([alpha, beta])
    db.session.flush()

    db.session.add_all(
        [
            TeamMembership(user=student, team=alpha),
            TeamMembership(user=ta, team=alpha),
            TeamMembership(user=student2, team=beta),
        ]
    )

    t1 = Task(
        title="Project proposal",
        description="Submit 1-page project idea.",
        course=course1,
        status="todo",
        points=50,
        team=alpha,
    )
    t2 = Task(
        title="Unit test suite",
        description="Add tests for your Flask routes.",
        course=course1,
        status="in_progress",
        points=100,
        team=beta,
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


def _build_status_columns(tasks):
    columns = []
    for value, label in Task.STATUS_CHOICES:
        columns.append(
            {
                "key": value,
                "label": label,
                "tasks": [task for task in tasks if task.status == value],
            }
        )
    return columns


@main_bp.route("/")
@login_required
def index():
    _ensure_sample_data()

    if current_user.is_authenticated and current_user.course_memberships:
        course_ids = [m.course_id for m in current_user.course_memberships]
        courses = [m.course for m in current_user.course_memberships]
        task_query = Task.query.filter(Task.course_id.in_(course_ids))
    else:
        courses = Course.query.all()
        task_query = Task.query

    upcoming_tasks = (
        task_query.order_by(Task.due_date.is_(None), Task.due_date).limit(5).all()
    )

    return render_template(
        "main/index.html",
        courses=courses,
        upcoming_tasks=upcoming_tasks,
    )


@main_bp.route("/courses")
@login_required
def courses():
    _ensure_sample_data()
    all_courses = Course.query.all()
    return render_template("main/courses.html", courses=all_courses)


@main_bp.route("/courses/<int:course_id>")
@login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)

    status_form = TaskStatusForm()
    status_form.status.choices = Task.STATUS_CHOICES
    comment_form = TaskCommentForm()

    return render_template(
        "main/course.html",
        course=course,
        status_columns=_build_status_columns(course.tasks),
        status_form=status_form,
        comment_form=comment_form,
        status_choices=Task.STATUS_CHOICES,
        teams=course.teams,
        team_form=TeamForm(),
    )


@main_bp.route("/courses/<int:course_id>/tasks/new", methods=["GET", "POST"])
@login_required
def new_task(course_id):
    course = Course.query.get_or_404(course_id)

    if not current_user.is_instructor:
        abort(403)

    form = TaskForm()
    form.team_id.choices = [(0, "Whole course")] + [
        (team.id, team.name) for team in course.teams
    ]

    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            points=form.points.data or 100,
            course=course,
        )
        if form.team_id.data:
            task.team = Team.query.get(form.team_id.data) if form.team_id.data else None
        db.session.add(task)
        db.session.commit()
        flash("Task created.")
        return redirect(url_for("main.course_detail", course_id=course.id))

    # set default points
    if form.points.data is None:
        form.points.data = 100

    return render_template("main/task_form.html", form=form, course=course)


@main_bp.route("/tasks/<int:task_id>/status", methods=["POST"])
@login_required
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    form = TaskStatusForm()
    form.status.choices = Task.STATUS_CHOICES

    if not form.validate_on_submit():
        abort(400)

    task.status = form.status.data
    db.session.commit()
    flash("Task status updated.")
    return redirect(request.referrer or url_for("main.course_detail", course_id=task.course_id))


@main_bp.route("/tasks/<int:task_id>/comments", methods=["POST"])
@login_required
def add_task_comment(task_id):
    task = Task.query.get_or_404(task_id)
    if not current_user.can_review_tasks:
        abort(403)

    form = TaskCommentForm()
    if form.validate_on_submit():
        body = form.body.data.strip()
        if not body:
            flash("Comment cannot be empty.")
            return redirect(request.referrer or url_for("main.course_detail", course_id=task.course_id))
        comment = TaskComment(body=body, task=task, author=current_user)
        db.session.add(comment)
        db.session.commit()
        flash("Feedback posted.")
    else:
        flash("Comment cannot be empty.")
    return redirect(request.referrer or url_for("main.course_detail", course_id=task.course_id))


@main_bp.route("/tasks/<int:task_id>/grade", methods=["GET", "POST"])
@login_required
def grade_task(task_id):
    """Prototype-grade: instructor sets a single score for the task."""
    if not current_user.is_instructor:
        abort(403)

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


@main_bp.route("/courses/<int:course_id>/teams", methods=["POST"])
@login_required
def create_team(course_id):
    course = Course.query.get_or_404(course_id)
    if not current_user.is_instructor:
        abort(403)

    form = TeamForm()
    if form.validate_on_submit():
        team = Team(name=form.name.data.strip(), course=course)
        db.session.add(team)
        db.session.commit()
        flash("Team created.")
    else:
        flash("Team name required.")
    return redirect(url_for("main.course_detail", course_id=course.id))


@main_bp.route("/teams/<int:team_id>")
@login_required
def team_detail(team_id):
    team = Team.query.get_or_404(team_id)

    member_form = TeamMemberForm()
    course_member_ids = {m.user_id for m in team.course.memberships if m.role == "student"}
    existing_ids = {m.user_id for m in team.memberships}
    available_students = course_member_ids - existing_ids
    member_choices = [
        (m.user.id, m.user.email)
        for m in team.course.memberships
        if m.user_id in available_students
    ]
    if not member_choices:
        member_choices = []
    member_form.user_id.choices = member_choices

    status_form = TaskStatusForm()
    status_form.status.choices = Task.STATUS_CHOICES
    comment_form = TaskCommentForm()

    return render_template(
        "main/team.html",
        team=team,
        status_columns=_build_status_columns(team.tasks),
        member_form=member_form,
        status_form=status_form,
        comment_form=comment_form,
        status_choices=Task.STATUS_CHOICES,
    )


@main_bp.route("/teams/<int:team_id>/members", methods=["POST"])
@login_required
def add_team_member(team_id):
    team = Team.query.get_or_404(team_id)
    if not current_user.is_instructor:
        abort(403)

    form = TeamMemberForm()
    available = [
        (m.user.id, m.user.email)
        for m in team.course.memberships
        if m.role == "student"
        and m.user_id not in {member.user_id for member in team.memberships}
    ]
    form.user_id.choices = available

    if not available:
        flash("All students are already on a team.")
        return redirect(url_for("main.team_detail", team_id=team.id))

    if form.validate_on_submit():
        db.session.add(TeamMembership(user_id=form.user_id.data, team=team))
        db.session.commit()
        flash("Member added.")
    else:
        flash("Please pick a student.")
    return redirect(url_for("main.team_detail", team_id=team.id))


@main_bp.route("/feature")
def feature():
    # still just a stub; can describe future ideas here
    return render_template("main/feature.html")
