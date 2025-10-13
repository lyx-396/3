import math
from datetime import datetime, time, timedelta


def haversine_distance_m(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance between two points in meters."""
    radius = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def hhmm_to_time(value: str) -> time:
    if not value or len(value) != 4:
        raise ValueError('HHMM string expected, got %s' % value)
    hour = int(value[:2])
    minute = int(value[2:])
    return time(hour=hour, minute=minute)


def combine_utc(dt: datetime, hhmm: str) -> datetime:
    base = datetime(dt.year, dt.month, dt.day)
    tm = hhmm_to_time(hhmm)
    return datetime.combine(base.date(), tm)


def session_open_window(session):
    start = session.start_time - timedelta(minutes=10)
    end = session.end_time + timedelta(minutes=5)
    return start, end


def is_session_open(session, now=None):
    now = now or datetime.utcnow()
    start, end = session_open_window(session)
    return start <= now <= end


def classify_status(session, ts):
    threshold = session.start_time + timedelta(minutes=10)
    if ts <= threshold:
        return 'on_time'
    return 'late'
