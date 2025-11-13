from flask import render_template
from app.main import main_bp

@main_bp.route("/")
def index():
    courses = [
        {"code": "CMPE 131", "title": "Software Engineering"},
        {"code": "CMPE 180", "title": "Special Topics"},
    ]
    return render_template("main/index.html", courses=courses)

@main_bp.route("/feature")
def feature():
    return render_template("main/feature.html")
