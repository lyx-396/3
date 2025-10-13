from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Student(db.Model, TimestampMixin):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    student_no = db.Column(db.String(32), unique=True, nullable=False, index=True)
    name = db.Column(db.String(128))
    class_name = db.Column(db.String(64))
    phone_hash = db.Column(db.String(128))
    device_fingerprint = db.Column(db.String(256))


class Course(db.Model, TimestampMixin):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    teacher = db.Column(db.String(128))
    class_name = db.Column(db.String(64))
    timetables = db.relationship('Timetable', backref='course', lazy=True)
    sessions = db.relationship('Session', backref='course', lazy=True)


class Timetable(db.Model, TimestampMixin):
    __tablename__ = 'timetables'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)
    weekday = db.Column(db.Integer, nullable=False)
    start_hhmm = db.Column(db.String(4), nullable=False)
    end_hhmm = db.Column(db.String(4), nullable=False)
    room = db.Column(db.String(64))
    gps_lat = db.Column(db.Float)
    gps_lng = db.Column(db.Float)
    gps_radius_m = db.Column(db.Integer)


class Session(db.Model, TimestampMixin):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False, index=True)
    start_time = db.Column(db.DateTime, nullable=False, index=True)
    end_time = db.Column(db.DateTime, nullable=False, index=True)
    room = db.Column(db.String(64))
    token = db.Column(db.String(64), nullable=False, index=True)
    status = db.Column(db.String(16), nullable=False, default='CLOSED')
    gps_lat = db.Column(db.Float)
    gps_lng = db.Column(db.Float)
    gps_radius_m = db.Column(db.Integer)

    attendances = db.relationship('Attendance', backref='session', lazy=True)


class Attendance(db.Model, TimestampMixin):
    __tablename__ = 'attendances'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    ts = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(16), nullable=False)
    gps_ok = db.Column(db.Boolean, default=True)
    face_ok = db.Column(db.Boolean, default=True)
    device_ok = db.Column(db.Boolean, default=True)

    student = db.relationship('Student')


class AdminUser(db.Model, TimestampMixin):
    __tablename__ = 'admin_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    pwd_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(64), default='admin')
