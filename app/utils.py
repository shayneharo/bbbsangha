import csv
import io
import os
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from flask import abort, current_app, send_from_directory
from werkzeug.utils import secure_filename


def parse_date(value):
    if not value:
        raise ValueError("Date is required.")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("Date must use YYYY-MM-DD format.") from exc


def default_date():
    return date.today().isoformat()


def allowed_file(filename):
    if "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in current_app.config["ALLOWED_EXTENSIONS"]


def save_uploaded_file(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        raise ValueError("Unsupported receipt file type.")

    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = secure_filename(file_storage.filename)
    extension = filename.rsplit(".", 1)[1].lower()
    final_name = f"{uuid.uuid4().hex}.{extension}"
    file_storage.save(upload_dir / final_name)
    return final_name


def delete_uploaded_file(filename):
    if not filename:
        return
    path = Path(current_app.config["UPLOAD_FOLDER"]) / filename
    if path.exists():
        path.unlink()


def serve_uploaded_file(filename):
    if not filename:
        abort(404)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, as_attachment=False)


def money(value):
    amount = Decimal(value or 0)
    return f"{amount:,.2f}"


def build_csv(rows, headers):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return output.getvalue().encode("utf-8")


def get_period_dates(period, start_str=None, end_str=None):
    today = date.today()
    if period == "weekly":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
    elif period == "monthly":
        start = today.replace(day=1)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1) - timedelta(days=1)
        else:
            end = start.replace(month=start.month + 1) - timedelta(days=1)
    elif period == "range":
        start = parse_date(start_str)
        end = parse_date(end_str)
        if end < start:
            raise ValueError("End date must be on or after start date.")
    else:
        start = today.replace(day=1)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1) - timedelta(days=1)
        else:
            end = start.replace(month=start.month + 1) - timedelta(days=1)
    return start, end
