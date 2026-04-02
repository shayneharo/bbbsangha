from pathlib import Path

from flask import Flask

from .config import Config
from .extensions import db
from .routes.web import web


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    app.register_blueprint(web)

    with app.app_context():
        from . import models  # noqa: F401

        db.create_all()

    return app
