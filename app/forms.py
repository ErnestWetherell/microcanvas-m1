from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    TextAreaField,
    IntegerField,
    SelectField,
)
from wtforms.fields import DateField
from wtforms.validators import DataRequired, Optional, NumberRange


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password")  # not enforced in this prototype
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Log In")


class TaskForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    description = TextAreaField("Description")
    due_date = DateField("Due date", format="%Y-%m-%d", validators=[Optional()])
    points = IntegerField("Points", validators=[Optional(), NumberRange(min=1, max=1000)])
    team_id = SelectField("Team", coerce=int, choices=[(0, "Whole course")])
    submit = SubmitField("Save Task")


class TaskStatusForm(FlaskForm):
    status = SelectField("Status", choices=[], validators=[DataRequired()])
    submit = SubmitField("Update")


class TaskCommentForm(FlaskForm):
    body = TextAreaField("Comment", validators=[DataRequired()])
    submit = SubmitField("Post feedback")


class GradeForm(FlaskForm):
    score = IntegerField("Score", validators=[Optional(), NumberRange(min=0, max=1000)])
    submit = SubmitField("Save Grade")


class TeamForm(FlaskForm):
    name = StringField("Team name", validators=[DataRequired()])
    submit = SubmitField("Create team")


class TeamMemberForm(FlaskForm):
    user_id = SelectField("Add member", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Add to team")
