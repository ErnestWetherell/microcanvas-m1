from datetime import datetime

from app import db, login_manager
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # global role for now: "student", "instructor", "ta"
    role = db.Column(db.String(20), default="student", nullable=False)

    course_memberships = db.relationship(
        "CourseMembership",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    team_memberships = db.relationship(
        "TeamMembership",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    task_comments = db.relationship(
        "TaskComment",
        back_populates="author",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"

    @property
    def is_instructor(self) -> bool:
        return self.role == "instructor"

    @property
    def is_student(self) -> bool:
        return self.role == "student"

    @property
    def is_ta(self) -> bool:
        return self.role == "ta"

    @property
    def can_review_tasks(self) -> bool:
        return self.role in ("instructor", "ta")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(120), nullable=False)

    # one-to-many relationship with tasks (assignments)
    tasks = db.relationship(
        "Task", back_populates="course", cascade="all, delete-orphan"
    )
    memberships = db.relationship(
        "CourseMembership",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    teams = db.relationship(
        "Team", back_populates="course", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Course {self.code}>"


class CourseMembership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    role = db.Column(db.String(20), default="student", nullable=False)

    user = db.relationship("User", back_populates="course_memberships")
    course = db.relationship("Course", back_populates="memberships")

    __table_args__ = (
        db.UniqueConstraint("user_id", "course_id", name="uq_user_course"),
    )

    def __repr__(self) -> str:
        return f"<CourseMembership {self.user.email} -> {self.course.code}>"


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)

    course = db.relationship("Course", back_populates="teams")
    memberships = db.relationship(
        "TeamMembership",
        back_populates="team",
        cascade="all, delete-orphan",
    )
    tasks = db.relationship("Task", back_populates="team")

    def member_names(self):
        return ", ".join(m.user.email for m in self.memberships) or "No members yet"

    def __repr__(self) -> str:
        return f"<Team {self.name}>"


class TeamMembership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False)

    user = db.relationship("User", back_populates="team_memberships")
    team = db.relationship("Team", back_populates="memberships")

    __table_args__ = (db.UniqueConstraint("user_id", "team_id", name="uq_user_team"),)

    def __repr__(self) -> str:
        return f"<TeamMembership {self.user.email} -> {self.team.name}>"


class Task(db.Model):
    """Task doubles as an assignment in this prototype.

    It has points and an optional score, so we can talk about grades.
    In a full version we would have a separate per-student grade table.
    """

    STATUS_TODO = "todo"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_DONE = "done"
    STATUS_CHOICES = [
        (STATUS_TODO, "To do"),
        (STATUS_IN_PROGRESS, "In progress"),
        (STATUS_DONE, "Done"),
    ]

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date)
    status = db.Column(
        db.String(20),
        nullable=False,
        default=STATUS_TODO,
    )

    # simple grading fields (global per task in this prototype)
    points = db.Column(db.Integer, nullable=False, default=100)
    score = db.Column(db.Integer)  # None = not graded yet

    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"))
    course = db.relationship("Course", back_populates="tasks")
    team = db.relationship("Team", back_populates="tasks")
    comments = db.relationship(
        "TaskComment",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskComment.created_at.desc()",
    )

    def __repr__(self) -> str:
        return f"<Task {self.title} ({self.status})>"

    @property
    def status_label(self) -> str:
        """Human readable label for templates."""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)


class TaskComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    task = db.relationship("Task", back_populates="comments")
    author = db.relationship("User", back_populates="task_comments")

    def __repr__(self) -> str:
        return f"<TaskComment {self.author.email} on {self.task.title}>"
