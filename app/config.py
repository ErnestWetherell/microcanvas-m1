import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "development-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "microcanvas.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
