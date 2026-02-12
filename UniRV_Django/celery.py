"""
Celery application configuration for AgroHub.

Initialises the Celery app, reads Django settings prefixed with ``CELERY_``,
and auto-discovers ``tasks.py`` modules in every installed Django app.

Usage (worker)::

    celery -A UniRV_Django worker -l info

Usage (beat — periodic tasks)::

    celery -A UniRV_Django beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

Usage (flower — monitoring dashboard)::

    celery -A UniRV_Django flower --port=5555
"""

import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "UniRV_Django.settings")

app = Celery("UniRV_Django")

# Read config from Django settings; the ``CELERY_`` prefix avoids clashes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in each installed app.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self) -> None:  # type: ignore[override]
    """Echo request info — useful for verifying the broker is working."""
    print(f"Request: {self.request!r}")
