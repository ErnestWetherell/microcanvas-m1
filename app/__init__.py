from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_object="app.config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # import models so metadata is registered
    from app import models  # noqa: F401

    # create tables on startup (dev only, fine for this class)
    with app.app_context():
        db.create_all()

    from app.auth.routes import auth_bp
    from app.main.routes import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    @app.errorhandler(404)
    def not_found(error):
        return (
            render_template("errors/404.html", error=error),
            404,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return (
            render_template("errors/400.html", error=error),
            400,
        )

    @app.errorhandler(403)
    def forbidden(error):
        return (
            render_template("errors/403.html", error=error),
            403,
        )

    return app
