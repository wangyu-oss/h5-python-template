import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

app = Celery('h5', broker=os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0'))
app.conf.beat_schedule = {
    'cleanup-every-minute': {'task': 'jobs.celery_app.cleanup', 'schedule': 60.0},
}


@app.task(name='jobs.celery_app.cleanup')
def cleanup():
    import django
    django.setup()
    from jobs.tasks import run_due
    run_due()
