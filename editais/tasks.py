"""
Background/async tasks for the editais app.

Welcome email is sent via a fire-and-forget thread to avoid blocking the
request cycle. For production with Celery, replace send_welcome_email_async
with a Celery task (e.g. send_welcome_email.delay(user_id)).
"""

import logging
import threading

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _send_welcome_email_sync(email: str, first_name: str) -> None:
    """Send welcome email (sync). Used by thread or Celery task."""
    if not getattr(settings, 'EMAIL_HOST', None):
        return
    try:
        send_mail(
            subject='Bem-vindo ao AgroHub!',
            message=(
                f'Olá {first_name},\n\n'
                'Bem-vindo ao sistema de gestão de editais do AgroHub UniRV!\n\n'
                'Sua conta foi criada com sucesso.'
            ),
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@agrohub.unirv.edu.br'),
            recipient_list=[email],
            fail_silently=True,
        )
    except (ConnectionError, OSError, ValueError) as e:
        logger.warning("Failed to send welcome email to %s: %s", email, e)


def send_welcome_email_async(email: str, first_name: str) -> None:
    """
    Send welcome email in a background thread so the request returns immediately.

    Uses fire-and-forget; no retries or visibility. Prefer Celery in production.
    """
    thread = threading.Thread(
        target=_send_welcome_email_sync,
        args=(email, first_name or ''),
        daemon=True,
    )
    thread.start()
