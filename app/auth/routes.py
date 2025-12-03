from flask import render_template, flash, redirect, url_for
from flask_login import login_user, logout_user, current_user, login_required
from app.auth import auth_bp
from app.forms import LoginForm
from app.models import User
from app import db


def _ensure_demo_users():
    """Create a couple of demo users if DB is empty.

    - prof@example.com  (instructor)
    - ta@example.com    (ta)
    - student@example.com (student)
    """
    if User.query.first() is not None:
        return

    prof = User(email="prof@example.com", role="instructor")
    ta = User(email="ta@example.com", role="ta")
    student = User(email="student@example.com", role="student")
    db.session.add_all([prof, ta, student])
    db.session.commit()


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    _ensure_demo_users()

    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        # if user doesn't exist, auto-create as student
        if user is None:
            user = User(email=email, role="student")
            db.session.add(user)
            db.session.commit()

        login_user(user, remember=form.remember_me.data)
        flash(f"Logged in as {user.email} ({user.role}).")
        return redirect(url_for("main.index"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for("main.index"))
