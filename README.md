# BBB Sangha Cash Tracker

BBB Sangha Cash Tracker is a Flask + MySQL web app for tracking cash received, cash sent, deposits, expenses, salary records, and seafood sales. It is designed to run locally or deploy on Railway with minimal setup.

## Features

- Dashboard with clickable summary cards for received, sent, deposited, balance, expenses, and sales
- Full transaction CRUD with receipt upload support
- Expense tracking with custom expense types and employee-linked salary records
- Sales tracking with editable product types such as alimango, hipon, and bangus
- Employee management for salary tracking
- Search, filters, weekly/monthly/date-range reporting
- CSV export and optional Excel export
- GCash-inspired responsive interface for desktop and mobile
- Railway-ready deployment configuration

## Project Structure

```text
BBB-Sangha-Cash-Tracker/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── models.py
│   ├── forms.py
│   ├── utils.py
│   ├── services/
│   │   ├── dashboard.py
│   │   ├── exports.py
│   │   └── reports.py
│   ├── routes/
│   │   └── web.py
│   ├── templates/
│   └── static/
├── storage/uploads/
├── schema.sql
├── requirements.txt
├── railway.json
├── Procfile
├── .env.example
├── run.py
└── README.md
```

## Environment Variables

Copy `.env.example` and set these values:

- `SECRET_KEY`: Flask secret key
- `DATABASE_URL`: SQLAlchemy-compatible MySQL connection string
- `UPLOAD_FOLDER`: folder for receipt files
- `MAX_CONTENT_LENGTH_MB`: max upload size in MB
- `EXCEL_EXPORT_ENABLED`: set to `true` or `false`

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
python run.py
```

If `DATABASE_URL` is not set, the app uses a local SQLite database for development at `instance/bbb_sangha_cash_tracker.db`.

## MySQL Setup

1. Create a MySQL database named `bbb_sangha_cash_tracker`.
2. Run the schema in [`schema.sql`](/Users/macb15/Desktop/SANGHA/schema.sql).
3. Set `DATABASE_URL` in your environment, for example:

```bash
mysql+pymysql://root:password@localhost:3306/bbb_sangha_cash_tracker
```

4. Restart the app.

The app also creates tables on boot via SQLAlchemy if they do not already exist.

## Railway Deployment

1. Create a new Railway project.
2. Add a MySQL service.
3. Set `DATABASE_URL`, `SECRET_KEY`, `UPLOAD_FOLDER`, and `EXCEL_EXPORT_ENABLED` in Railway variables.
4. Deploy the repository. Railway uses `gunicorn run:app` from `railway.json` and `Procfile`.

For persistent receipts on Railway, point `UPLOAD_FOLDER` to a mounted Railway volume path.

## Notes

- No authentication is included by design.
- No sample data is seeded.
- Uploaded files are limited by extension and file size, but production deployments should still use private storage or a mounted volume for long-term retention.
