from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    # initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # import models so that user_loader is registered
    from app import models  # noqa: F401

    # register blueprints
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app
