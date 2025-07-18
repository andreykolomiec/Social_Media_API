import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "social_media_platform.settings")

app = Celery("social_media_platform")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")


# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


"""Test task to check scheduling"""


@app.task(bind=True)
def test_scheduled_task(self, message):
    """Test task for checking scheduling"""
    from datetime import datetime

    print(f"Test task completed at {datetime.now()}")
    print(f"Message: {message}")
    return f"Task executed at {datetime.now()}"
