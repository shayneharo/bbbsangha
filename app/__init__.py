from pathlib import Path

from flask import Flask
from sqlalchemy import inspect, text

from .config import Config
from .extensions import db
from .routes.web import web


def _ensure_schema_updates():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    if "expenses" not in tables:
        return

    expense_columns = {column["name"] for column in inspector.get_columns("expenses")}
    if "include_in_balance" not in expense_columns:
        db.session.execute(
            text(
                "ALTER TABLE expenses "
                "ADD COLUMN include_in_balance BOOLEAN NOT NULL DEFAULT 1"
            )
        )
        db.session.commit()


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
        _ensure_schema_updates()

    return app
