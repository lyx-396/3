from datetime import datetime, timedelta
from types import SimpleNamespace

from utils import haversine_distance_m, session_open_window, is_session_open


def test_haversine_distance():
    lat1, lon1 = 40.7128, -74.0060
    lat2, lon2 = 40.7138, -74.0065
    distance = haversine_distance_m(lat1, lon1, lat2, lon2)
    assert 0 < distance < 200


def test_session_open_window():
    start = datetime.utcnow()
    session = SimpleNamespace(start_time=start, end_time=start + timedelta(hours=1))
    window_start, window_end = session_open_window(session)
    assert window_start == session.start_time - timedelta(minutes=10)
    assert window_end == session.end_time + timedelta(minutes=5)


def test_is_session_open():
    start = datetime.utcnow()
    session = SimpleNamespace(start_time=start, end_time=start + timedelta(minutes=5))
    assert is_session_open(session, now=start)
    assert not is_session_open(session, now=start - timedelta(minutes=15))
