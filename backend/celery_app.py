from celery import Celery
from celery.schedules import crontab

def make_celery(app=None):
    celery = Celery(
        'medsync',
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/1',
        include=[
            'celery_tasks.email_tasks',
            'celery_tasks.export_tasks'
        ]
    )

    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Asia/Kolkata',
        enable_utc=True,

        # Beat scheduler for periodic tasks
        beat_schedule={
            # Daily reminder at 8 AM IST every day
            'daily-appointment-reminders': {
                'task': 'celery_tasks.email_tasks.send_daily_reminders',
                'schedule': crontab(hour=8, minute=0),
            },
            # Monthly report on the 1st of each month at 9 AM IST
            'monthly-doctor-reports': {
                'task': 'celery_tasks.email_tasks.send_monthly_reports',
                'schedule': crontab(day_of_month=1, hour=9, minute=0),
            },
        }
    )

    return celery

celery = make_celery()
