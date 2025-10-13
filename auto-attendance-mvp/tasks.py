from datetime import datetime

from flask import current_app
from flask_apscheduler import APScheduler

from services import create_sessions_for_day, rotate_tokens_for_open_sessions


scheduler = APScheduler()


def init_scheduler(app):
    if app.config.get('TESTING'):
        return

    scheduler.init_app(app)
    scheduler.start()

    if not scheduler.get_job('daily_session_creation'):
        scheduler.add_job(
            id='daily_session_creation',
            func=lambda: create_sessions_for_day(datetime.utcnow().date()),
            trigger='cron',
            hour=0,
            minute=10,
        )

    if not scheduler.get_job('rotate_tokens'):
        scheduler.add_job(
            id='rotate_tokens',
            func=rotate_tokens_for_open_sessions,
            trigger='interval',
            seconds=30,
        )
