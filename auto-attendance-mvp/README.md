# Auto Attendance MVP

Fully automated university attendance system built with Flask, SQLAlchemy, and APScheduler. The application imports course timetables, auto-creates daily sessions, rotates QR tokens to combat screenshot abuse, validates GPS/device fingerprints, and exports rich Excel attendance reports.

![Admin dashboard placeholder](static/sample_screenshot.png)

## Features

- 📅 **Timetable ingestion** via CSV upload for rapid onboarding
- ⏰ **Daily session generation** at 00:10 UTC driven by APScheduler
- 🔁 **Rotating QR tokens** every 30 seconds for active sessions
- 🛰️ **GPS geofence validation** with configurable radius per timetable entry
- 💻 **Device fingerprint binding** on first check-in per student
- 📱 **Mobile-friendly H5 check-in page** with live token polling
- 📦 **Excel exports** containing raw events and per-student summaries
- 🔒 **Basic admin guard** using HTTP Basic Auth sourced from environment variables
- 🧪 **pytest test suite** covering utilities and critical API flows
- 🧠 **Face verification stub** ready for future biometric integration

## Architecture Overview

```
+---------------------+
|  CSV Timetable/     |
|  Student Imports    |
+----------+----------+
           |
           v
+---------------------+       APScheduler         +---------------------+
|  SQLite / MySQL     |<------------------------->|  Daily Jobs         |
|  SQLAlchemy Models  |   (00:10 create sessions) |  (token rotation)   |
+----------+----------+                           +----------+----------+
           |                                                   |
           v                                                   v
+---------------------+       QR Token         +-------------------------+
|  Flask Admin Pages  |<---------------------->|  Check-in H5 Frontend   |
|  (/admin/*)         |     (/admin/qrcode)    |  (/checkin)             |
+----------+----------+                        +-------------------------+
           |                                                    |
           v                                                    v
+---------------------+                              +-------------------+
|  Attendance Records |----------------------------->|  Excel Exports    |
|  (on_time/late)     |   pandas + openpyxl          |  (/admin/export)  |
+---------------------+                              +-------------------+
```

## Quick Start

### Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.template .env  # adjust ADMIN_* and DATABASE_URL as needed
FLASK_APP=app.py flask run --host=0.0.0.0 --port=5000
```

### Using Makefile

```bash
make install
make run
```

### Docker

```bash
docker-compose up --build
```

The application listens on `http://localhost:8080` in Docker mode and `http://localhost:5000` when run locally.

## Environment Variables

| Variable      | Default              | Description |
| ------------- | -------------------- | ----------- |
| `SECRET_KEY`  | `dev-secret`         | Flask session key |
| `DATABASE_URL`| `sqlite:///auto.db`  | SQLAlchemy database URI (supports SQLite/MySQL) |
| `ADMIN_USER`  | `admin`              | Admin username for HTTP Basic Auth |
| `ADMIN_PASS`  | `changeme`           | Admin password for HTTP Basic Auth |
| `FLASK_ENV`   | `development`        | Flask environment |

> ℹ️ Always run behind HTTPS and rotate the admin credentials in production.

## Sample Data

Import demo fixtures to explore the UI quickly:

```bash
# Admin endpoints require HTTP basic auth (default admin/changeme)
curl -u admin:changeme -F "file=@data/sample_students.csv" http://localhost:5000/admin/students/import
curl -u admin:changeme -F "file=@data/sample_timetable.csv" http://localhost:5000/admin/upload_timetable
```

## API Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| `POST` | `/admin/upload_timetable` | Upload timetable CSV (admin auth) |
| `POST` | `/admin/students/import`  | Upload student roster CSV (admin auth) |
| `GET`  | `/admin/sessions/today`   | HTML overview of today's sessions |
| `GET`  | `/admin/sessions/<id>/qrcode` | Dynamic QR code PNG for projector display |
| `GET`  | `/checkin?sid=<session_id>` | Student H5 check-in page |
| `GET`  | `/api/session_token?sid=<session_id>` | Poll current session token & window |
| `POST` | `/api/checkin` | Submit student attendance event |
| `GET`  | `/admin/export?course=<id>&from=YYYY-MM-DD&to=YYYY-MM-DD` | Download Excel export |
| `POST` | `/api/face_check` | Placeholder face verification endpoint |

### Sample Check-in Flow

```bash
# Fetch rotating token
curl "http://localhost:5000/api/session_token?sid=1"

# Submit a check-in
curl -X POST http://localhost:5000/api/checkin \
  -F sid=1 \
  -F student_no=2024001 \
  -F token=<token-from-previous-call> \
  -F lat=40.7128 \
  -F lng=-74.0060 \
  -F device="curl-demo"
```

## Anti-Cheat Strategies

- **QR token rotation** invalidates screenshots within seconds.
- **Geofencing** ensures students are physically within the classroom radius.
- **Device fingerprint binding** locks the first successful check-in to a user-agent string.
- **Face verification stub** ready to integrate with live biometric services (returns success by default today).

## Excel Exports

Exports contain two worksheets:

1. `summary` – per student counts of `on_time`, `late`, and derived `absent` values.
2. `raw` – every check-in event with timestamps and validation flags.

Sheets include bold headers and frozen panes for improved readability.

## Production Hardening Tips

- Terminate TLS at a reverse proxy (nginx/Traefik) and forward `X-Forwarded-*` headers.
- Swap SQLite with MySQL/PostgreSQL via `DATABASE_URL` for concurrency.
- Rotate admin credentials frequently and integrate with SSO if possible.
- Schedule regular database backups and export archives.
- Enforce HTTPS, secure cookies, and CSRF tokens for admin forms in a hardened deployment.

## Roadmap

- 🤳 Integrate live face recognition provider and persist verification evidence.
- 🔐 Campus SSO (OAuth/SAML) for admin & student authentication.
- 📡 Wi-Fi/BLE fingerprinting for additional location validation.
- 📲 Native mobile companion app with push reminders.

## Testing

```bash
pytest
```

Happy automating! 🎓
