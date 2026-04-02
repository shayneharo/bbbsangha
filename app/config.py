import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'instance' / 'bbb_sangha_cash_tracker.db'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", "5")) * 1024 * 1024
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "storage" / "uploads"))
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf", "webp"}
    EXCEL_EXPORT_ENABLED = os.getenv("EXCEL_EXPORT_ENABLED", "true").lower() == "true"
