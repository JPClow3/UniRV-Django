"""AgroHub Django project package.

Ensures the Celery app is loaded when Django starts so that
``@shared_task`` decorators use it and ``autodiscover_tasks()`` can find
task modules across all installed apps.
"""

from .celery import app as celery_app

__all__ = ("celery_app",)
