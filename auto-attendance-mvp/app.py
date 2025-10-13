import io
import os
from datetime import datetime

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency fallback
    def load_dotenv():  # type: ignore
        return False
from flask import (Flask, Response, jsonify, redirect, render_template,
                   request, send_file, url_for)
try:
    import qrcode
    from qrcode.image.pil import PilImage
except ImportError:  # pragma: no cover - optional dependency fallback
    qrcode = None
    PilImage = None

from models import db, Session, Attendance, Student
from services import (
    ingest_timetable,
    import_students,
    create_sessions_for_day,
    rotate_tokens_for_open_sessions,
    export_attendance,
)
from tasks import init_scheduler
from utils import session_open_window, classify_status, haversine_distance_m


load_dotenv()


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///auto.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
    app.config['EXPORT_FOLDER'] = os.path.join(app.root_path, 'exports')
    app.config['ADMIN_USER'] = os.getenv('ADMIN_USER', 'admin')
    app.config['ADMIN_PASS'] = os.getenv('ADMIN_PASS', 'changeme')

    if config:
        app.config.update(config)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    init_scheduler(app)

    register_routes(app)
    return app


def check_auth(app, auth):
    return auth and auth.username == app.config['ADMIN_USER'] and auth.password == app.config['ADMIN_PASS']


def register_routes(app: Flask):
    @app.route('/')
    def index():
        return redirect(url_for('admin_sessions_today'))

    def require_admin_auth():
        auth = request.authorization
        if not check_auth(app, auth):
            return Response('Authentication required', 401, {'WWW-Authenticate': 'Basic realm="Admin Area"'})
        return None

    @app.route('/admin/upload_timetable', methods=['POST'])
    def admin_upload_timetable():
        auth_resp = require_admin_auth()
        if auth_resp:
            return auth_resp
        file = request.files.get('file')
        if not file:
            return jsonify({'message': 'CSV file is required'}), 400
        try:
            created = ingest_timetable(file)
            return jsonify({'message': f'Imported {created} timetable rows'})
        except Exception as exc:  # pylint: disable=broad-except
            return jsonify({'message': str(exc)}), 400

    @app.route('/admin/students/import', methods=['POST'])
    def admin_import_students():
        auth_resp = require_admin_auth()
        if auth_resp:
            return auth_resp
        file = request.files.get('file')
        if not file:
            return jsonify({'message': 'CSV file is required'}), 400
        try:
            created = import_students(file)
            return jsonify({'message': f'Imported {created} students'})
        except Exception as exc:  # pylint: disable=broad-except
            return jsonify({'message': str(exc)}), 400

    @app.route('/admin/sessions/today')
    def admin_sessions_today():
        auth_resp = require_admin_auth()
        if auth_resp:
            return auth_resp
        today = datetime.utcnow().date()
        start = datetime.combine(today, datetime.min.time())
        end = datetime.combine(today, datetime.max.time())
        sessions = Session.query.filter(Session.start_time >= start, Session.end_time <= end).order_by(Session.start_time).all()
        for session in sessions:
            counts = (
                db.session.query(Attendance.status, db.func.count(Attendance.id))
                .filter(Attendance.session_id == session.id)
                .group_by(Attendance.status)
                .all()
            )
            session.count_on_time = next((cnt for status, cnt in counts if status == 'on_time'), 0)
            session.count_late = next((cnt for status, cnt in counts if status == 'late'), 0)
        return render_template('admin_sessions_today.html', sessions=sessions, year=today.year)

    @app.route('/admin/sessions/<int:sid>/qrcode')
    def admin_session_qrcode(sid):
        auth_resp = require_admin_auth()
        if auth_resp:
            return auth_resp
        if qrcode is None or PilImage is None:
            return jsonify({'message': 'QR code generation requires qrcode and pillow packages'}), 503
        session = Session.query.get_or_404(sid)
        checkin_url = url_for('checkin_page', sid=session.id, _external=True)
        img = qrcode.make(checkin_url, image_factory=PilImage)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return send_file(buf, mimetype='image/png')

    @app.route('/checkin')
    def checkin_page():
        sid = request.args.get('sid')
        session = Session.query.get_or_404(sid)
        return render_template('checkin.html', sid=session.id, year=datetime.utcnow().year)

    @app.route('/api/session_token')
    def api_session_token():
        sid = request.args.get('sid')
        if not sid:
            return jsonify({'message': 'sid required'}), 400
        session = Session.query.get_or_404(sid)
        start, end = session_open_window(session)
        rotate_tokens_for_open_sessions()
        db.session.refresh(session)
        return jsonify({
            'token': session.token,
            'status': session.status,
            'window': {
                'start': start.isoformat(),
                'end': end.isoformat(),
            },
        })

    @app.route('/api/checkin', methods=['POST'])
    def api_checkin():
        sid = request.form.get('sid')
        student_no = request.form.get('student_no')
        token = request.form.get('token')
        lat = request.form.get('lat')
        lng = request.form.get('lng')
        device = request.form.get('device')

        if not all([sid, student_no, token]):
            return jsonify({'message': 'sid, student_no, and token are required'}), 400

        session = Session.query.get(sid)
        if not session:
            return jsonify({'message': 'Session not found'}), 404

        now = datetime.utcnow()
        start, end = session_open_window(session)
        if not (start <= now <= end):
            session.status = 'CLOSED'
            db.session.commit()
            return jsonify({'message': 'Session is closed'}), 400

        if token != session.token:
            return jsonify({'message': 'Invalid or expired token'}), 400

        student = Student.query.filter_by(student_no=str(student_no)).first()
        if not student:
            return jsonify({'message': 'Student not found. Please import student roster first.'}), 404

        attendance = Attendance.query.filter_by(session_id=session.id, student_id=student.id).first()
        if attendance:
            return jsonify({'message': 'Already checked in', 'status': attendance.status})

        gps_ok = True
        if session.gps_lat is not None and session.gps_lng is not None and session.gps_radius_m:
            if lat is None or lng is None or lat == '' or lng == '':
                gps_ok = False
            else:
                try:
                    distance = haversine_distance_m(float(lat), float(lng), session.gps_lat, session.gps_lng)
                    gps_ok = distance <= session.gps_radius_m
                except ValueError:
                    gps_ok = False

        device_ok = True
        if device:
            if student.device_fingerprint and student.device_fingerprint != device:
                device_ok = False
            elif not student.device_fingerprint:
                student.device_fingerprint = device

        status_value = classify_status(session, now)
        attendance = Attendance(
            session_id=session.id,
            student_id=student.id,
            ts=now,
            status=status_value,
            gps_ok=gps_ok,
            device_ok=device_ok,
            face_ok=True,
        )
        db.session.add(attendance)
        db.session.commit()

        message = 'Check-in recorded'
        if not gps_ok:
            message += ' (GPS mismatch)'
        if not device_ok:
            message += ' (Device mismatch)'

        return jsonify({'message': message, 'status': status_value, 'gps_ok': gps_ok, 'device_ok': device_ok})

    @app.route('/admin/export')
    def admin_export():
        auth_resp = require_admin_auth()
        if auth_resp:
            return auth_resp
        course_id = request.args.get('course', type=int)
        date_from = request.args.get('from')
        date_to = request.args.get('to')
        if not (course_id and date_from and date_to):
            return jsonify({'message': 'course, from, to parameters required'}), 400
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD'}), 400

        filename = f"export_{course_id}_{from_date}_{to_date}.xlsx"
        path = os.path.join(app.config['EXPORT_FOLDER'], filename)
        try:
            export_attendance(course_id, from_date, to_date, path)
        except Exception as exc:  # pylint: disable=broad-except
            return jsonify({'message': str(exc)}), 400
        return send_file(path, as_attachment=True, download_name=filename)

    @app.route('/api/face_check', methods=['POST'])
    def api_face_check():
        # TODO: integrate with actual face recognition provider
        return jsonify({'ok': True, 'face_ok': True, 'message': 'Face check stub. Integrate provider here.'})

    @app.route('/trigger/create_sessions')
    def trigger_create_sessions():
        auth_resp = require_admin_auth()
        if auth_resp:
            return auth_resp
        created = create_sessions_for_day()
        return jsonify({'created': created})

    @app.route('/trigger/rotate_tokens')
    def trigger_rotate_tokens():
        auth_resp = require_admin_auth()
        if auth_resp:
            return auth_resp
        rotated = rotate_tokens_for_open_sessions()
        return jsonify({'rotated': rotated})


app = create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
