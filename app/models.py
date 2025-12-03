from app import db, login_manager
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # global role for now: "student", "instructor", "ta"
    role = db.Column(db.String(20), default="student", nullable=False)

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


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(120), nullable=False)

    # one-to-many relationship with tasks (assignments)
    tasks = db.relationship(
        "Task",
        back_populates="course",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Course {self.code}>"


class Task(db.Model):
    """Task doubles as an assignment in this prototype.

    It has points and an optional score, so we can talk about grades.
    In a full version we would have a separate per-student grade table.
    """

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(20), nullable=False, default="todo")  # todo/in_progress/done

    # simple grading fields (global per task in this prototype)
    points = db.Column(db.Integer, nullable=False, default=100)
    score = db.Column(db.Integer)  # None = not graded yet

    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    course = db.relationship("Course", back_populates="tasks")

    def __repr__(self) -> str:
        return f"<Task {self.title} ({self.status})>"
