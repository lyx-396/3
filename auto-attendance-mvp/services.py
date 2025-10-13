import secrets
from datetime import datetime

try:
    import pandas as pd
except ImportError:  # pragma: no cover - optional dependency fallback
    pd = None  # type: ignore

from models import db, Course, Timetable, Session, Student, Attendance
from utils import combine_utc, session_open_window


TOKEN_BYTES = 6


def generate_token():
    return secrets.token_urlsafe(TOKEN_BYTES)


def ingest_timetable(file_stream):
    if pd is None:
        raise ImportError('pandas is required for timetable ingestion')
    df = pd.read_csv(file_stream)
    required = [
        'course_name', 'teacher', 'class_name', 'weekday',
        'start_hhmm', 'end_hhmm', 'room', 'gps_lat', 'gps_lng', 'gps_radius_m'
    ]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f'Missing columns: {", ".join(missing)}')

    created_rows = 0
    for _, row in df.iterrows():
        course = Course.query.filter_by(name=row['course_name'], class_name=row['class_name']).first()
        if not course:
            course = Course(name=row['course_name'], teacher=row.get('teacher'), class_name=row.get('class_name'))
            db.session.add(course)
            db.session.flush()

        timetable = Timetable(
            course_id=course.id,
            weekday=int(row['weekday']),
            start_hhmm=str(row['start_hhmm']).zfill(4),
            end_hhmm=str(row['end_hhmm']).zfill(4),
            room=row.get('room'),
            gps_lat=float(row['gps_lat']) if pd.notna(row['gps_lat']) else None,
            gps_lng=float(row['gps_lng']) if pd.notna(row['gps_lng']) else None,
            gps_radius_m=int(row['gps_radius_m']) if pd.notna(row['gps_radius_m']) else None,
        )
        db.session.add(timetable)
        created_rows += 1

    db.session.commit()
    return created_rows


def import_students(file_stream):
    if pd is None:
        raise ImportError('pandas is required for student import')
    df = pd.read_csv(file_stream)
    required = ['student_no', 'name', 'class_name']
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f'Missing columns: {", ".join(missing)}')

    created = 0
    for _, row in df.iterrows():
        student = Student.query.filter_by(student_no=str(row['student_no'])).first()
        if not student:
            student = Student(
                student_no=str(row['student_no']),
                name=row.get('name'),
                class_name=row.get('class_name')
            )
            db.session.add(student)
            created += 1
    db.session.commit()
    return created


def create_sessions_for_day(target_date=None):
    target_date = target_date or datetime.utcnow().date()
    weekday = target_date.isoweekday()
    timetables = Timetable.query.filter_by(weekday=weekday).all()
    created = 0
    for timetable in timetables:
        start_dt = combine_utc(datetime.combine(target_date, datetime.min.time()), timetable.start_hhmm)
        end_dt = combine_utc(datetime.combine(target_date, datetime.min.time()), timetable.end_hhmm)
        existing = Session.query.filter_by(course_id=timetable.course_id, start_time=start_dt).first()
        if existing:
            continue
        session = Session(
            course_id=timetable.course_id,
            start_time=start_dt,
            end_time=end_dt,
            room=timetable.room,
            token=generate_token(),
            status='CLOSED',
            gps_lat=timetable.gps_lat,
            gps_lng=timetable.gps_lng,
            gps_radius_m=timetable.gps_radius_m,
        )
        db.session.add(session)
        created += 1
    if created:
        db.session.commit()
    return created


def rotate_tokens_for_open_sessions(now=None):
    now = now or datetime.utcnow()
    sessions = Session.query.all()
    rotated = 0
    for session in sessions:
        start, end = session_open_window(session)
        if start <= now <= end:
            if session.status != 'OPEN':
                session.status = 'OPEN'
            session.token = generate_token()
            rotated += 1
        else:
            if session.status != 'CLOSED':
                session.status = 'CLOSED'
    if sessions:
        db.session.commit()
    return rotated


def export_attendance(course_id, from_date, to_date, output_path):
    if pd is None:
        raise ImportError('pandas and openpyxl are required for exporting attendance')
    sessions = Session.query.filter(
        Session.course_id == course_id,
        Session.start_time >= datetime.combine(from_date, datetime.min.time()),
        Session.end_time <= datetime.combine(to_date, datetime.max.time())
    ).all()

    if not sessions:
        raise ValueError('No sessions found for given filters')

    session_ids = [s.id for s in sessions]
    attendances = Attendance.query.filter(Attendance.session_id.in_(session_ids)).all()

    raw_rows = []
    for record in attendances:
        raw_rows.append({
            'session_id': record.session_id,
            'student_no': record.student.student_no if record.student else None,
            'student_name': record.student.name if record.student else None,
            'timestamp_utc': record.ts.isoformat(),
            'status': record.status,
            'gps_ok': record.gps_ok,
            'device_ok': record.device_ok,
            'face_ok': record.face_ok,
        })

    raw_df = pd.DataFrame(raw_rows)
    if raw_df.empty:
        raw_df = pd.DataFrame(columns=['session_id', 'student_no', 'student_name', 'timestamp_utc', 'status', 'gps_ok', 'device_ok', 'face_ok'])

    grouped = raw_df.groupby(['student_no', 'student_name']).status.value_counts().unstack(fill_value=0) if not raw_df.empty else pd.DataFrame()
    summary_rows = []
    if not raw_df.empty:
        total_sessions = len(sessions)
        for (student_no, student_name), row in grouped.iterrows():
            on_time = row.get('on_time', 0)
            late = row.get('late', 0)
            absences = total_sessions - (on_time + late)
            summary_rows.append({
                'student_no': student_no,
                'student_name': student_name,
                'on_time': int(on_time),
                'late': int(late),
                'absent': int(absences)
            })
    summary_df = pd.DataFrame(summary_rows)
    if summary_df.empty:
        summary_df = pd.DataFrame(columns=['student_no', 'student_name', 'on_time', 'late', 'absent'])

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        summary_df.to_excel(writer, sheet_name='summary', index=False)
        raw_df.to_excel(writer, sheet_name='raw', index=False)
        for sheet in writer.sheets.values():
            sheet.freeze_panes = sheet['A2']
            for cell in sheet[1]:
                cell.font = cell.font.copy(bold=True)
    return output_path
