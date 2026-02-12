"""
Background/async tasks for the editais app.

Welcome email is sent via Celery ``@shared_task`` when ``USE_CELERY=True``.
Otherwise falls back to a fire-and-forget daemon thread so the request
returns immediately (no broker required for local development).

Retry policy: 3 retries with exponential back-off (60 s, 120 s, 180 s).
"""

import logging
import threading
from typing import Optional

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Celery task — used when USE_CELERY=True
# ---------------------------------------------------------------------------


@shared_task(
    bind=True,
    name="editais.tasks.send_welcome_email_task",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(ConnectionError, OSError),
    retry_backoff=True,
    retry_jitter=True,
    ignore_result=True,
)
def send_welcome_email_task(self, email: str, first_name: str) -> None:  # type: ignore[override]
    """Send welcome email via Celery with automatic retries.

    Args:
        email: Recipient email address.
        first_name: Recipient first name (used in greeting).
    """
    _send_welcome_email_sync(email, first_name)


# ---------------------------------------------------------------------------
# Shared synchronous sender
# ---------------------------------------------------------------------------


def _send_welcome_email_sync(email: str, first_name: str) -> None:
    """Send welcome email (sync). Used by Celery task or thread fallback."""
    if not getattr(settings, "EMAIL_HOST", None) and "console" not in getattr(
        settings, "EMAIL_BACKEND", ""
    ):
        return
    try:
        send_mail(
            subject="Bem-vindo ao AgroHub!",
            message=(
                f"Olá {first_name},\n\n"
                "Bem-vindo ao sistema de gestão de editais do AgroHub UniRV!\n\n"
                "Sua conta foi criada com sucesso."
            ),
            from_email=getattr(
                settings, "DEFAULT_FROM_EMAIL", "noreply@agrohub.unirv.edu.br"
            ),
            recipient_list=[email],
            fail_silently=True,
        )
        logger.info("Welcome email sent to %s", email)
    except (ConnectionError, OSError, ValueError) as e:
        logger.warning("Failed to send welcome email to %s: %s", email, e)
        raise  # Let Celery retry if running as task


# ---------------------------------------------------------------------------
# Thread fallback — used when USE_CELERY=False
# ---------------------------------------------------------------------------


def _send_welcome_email_thread(email: str, first_name: str) -> None:
    """Fire-and-forget thread wrapper (no retries, no visibility)."""
    thread = threading.Thread(
        target=_send_welcome_email_sync,
        args=(email, first_name or ""),
        daemon=True,
    )
    thread.start()


# ---------------------------------------------------------------------------
# Public API — views should call this function
# ---------------------------------------------------------------------------


def send_welcome_email_async(email: str, first_name: Optional[str] = None) -> None:
    """Dispatch welcome email via Celery (preferred) or thread (fallback).

    Reads ``settings.USE_CELERY`` to decide the dispatch mechanism.
    This keeps callers (views) decoupled from the transport.

    Args:
        email: Recipient email address.
        first_name: Recipient first name.
    """
    name = first_name or ""
    if getattr(settings, "USE_CELERY", False):
        send_welcome_email_task.delay(email, name)
    else:
        _send_welcome_email_thread(email, name)
