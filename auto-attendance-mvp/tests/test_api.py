from datetime import datetime, timedelta

import pytest

flask = pytest.importorskip('flask')

from app import create_app
from models import db, Course, Session, Student


@pytest.fixture()
def client():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    })

    with app.app_context():
        db.create_all()
        course = Course(name='Testing 101', teacher='Prof. Test', class_name='QA')
        db.session.add(course)
        db.session.flush()

        session = Session(
            course_id=course.id,
            start_time=datetime.utcnow() - timedelta(minutes=1),
            end_time=datetime.utcnow() + timedelta(minutes=30),
            room='Lab',
            token='initial',
            status='OPEN'
        )
        db.session.add(session)

        student = Student(student_no='12345', name='Test Student', class_name='QA')
        db.session.add(student)
        db.session.commit()

    with app.test_client() as client:
        yield client


def test_session_token_and_checkin(client):
    token_resp = client.get('/api/session_token', query_string={'sid': 1})
    assert token_resp.status_code == 200
    token_data = token_resp.get_json()
    assert token_data['status'] in {'OPEN', 'CLOSED'}
    token = token_data['token']

    payload = {
        'sid': 1,
        'student_no': '12345',
        'token': token,
        'lat': '40.7128',
        'lng': '-74.0060',
        'device': 'pytest-device'
    }
    checkin_resp = client.post('/api/checkin', data=payload)
    assert checkin_resp.status_code == 200
    body = checkin_resp.get_json()
    assert body['status'] in {'on_time', 'late'}


def test_invalid_token_rejected(client):
    resp = client.post('/api/checkin', data={
        'sid': 1,
        'student_no': '12345',
        'token': 'bogus'
    })
    assert resp.status_code == 400
    assert 'Invalid' in resp.get_json()['message']
