from flask import render_template, flash, redirect, url_for
from app.auth import auth_bp
from app.forms import LoginForm

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash("Login POST received – authentication not implemented yet.")
        return redirect(url_for("main.index"))
    return render_template("auth/login.html", form=form)
