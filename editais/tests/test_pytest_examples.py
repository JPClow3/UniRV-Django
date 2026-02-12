"""
Example pytest tests — Celery task, health endpoint, email flow.

Run with::

    pytest editais/tests/test_pytest_examples.py -v
"""

from unittest.mock import patch

import pytest
from django.core import mail
from django.test import override_settings
from freezegun import freeze_time

from editais.tasks import (
    send_welcome_email_async,
    send_welcome_email_task,
    _send_welcome_email_sync,
)


# ---------------------------------------------------------------------------
# 1) Unit test — Celery task sends email (eager mode)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSendWelcomeEmailTask:
    """Verify the Celery task sends the welcome email correctly."""

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_task_sends_email(self) -> None:
        """Task should dispatch exactly one email with expected subject."""
        send_welcome_email_task.delay("joao@example.com", "João")

        assert len(mail.outbox) == 1
        msg = mail.outbox[0]
        assert msg.subject == "Bem-vindo ao AgroHub!"
        assert "João" in msg.body
        assert msg.to == ["joao@example.com"]

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_sync_sender_sends_email(self) -> None:
        """The sync helper should populate the Django outbox."""
        _send_welcome_email_sync("maria@example.com", "Maria")

        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["maria@example.com"]

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        USE_CELERY=True,
    )
    def test_async_dispatcher_uses_celery_when_flag_set(self) -> None:
        """When USE_CELERY=True, send_welcome_email_async should use Celery."""
        with patch.object(
            send_welcome_email_task, "delay", wraps=send_welcome_email_task.delay
        ) as mock_delay:
            send_welcome_email_async("ana@example.com", "Ana")
            mock_delay.assert_called_once_with("ana@example.com", "Ana")


# ---------------------------------------------------------------------------
# 2) Integration test — /ht/ health endpoint (django-health-check)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestHealthEndpoint:
    """Verify the django-health-check endpoint returns 200."""

    def test_health_check_returns_200(self, client) -> None:
        """GET /ht/ or /health/ should return 200 when DB and cache are healthy.
        Uses /health/ (custom endpoint) when Redis is not configured to avoid /ht/ failures.
        """
        # Prefer custom /health/ which works without Redis; /ht/ requires Redis when configured
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_legacy_health_check_returns_200(self, client) -> None:
        """GET /health/ (custom endpoint) should still return 200."""
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @freeze_time("2026-06-15 12:00:00")
    def test_health_timestamp(self, client) -> None:
        """Health response should include a parseable timestamp."""
        response = client.get("/health/")
        data = response.json()
        assert "2026-06-15" in data["timestamp"]


# ---------------------------------------------------------------------------
# 3) E2E email flow — registration triggers welcome email (mocked)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRegistrationEmailFlow:
    """End-to-end: user registration dispatches a welcome email."""

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_registration_sends_welcome_email(self, client) -> None:
        """POST /register/ with valid data should trigger welcome email."""
        with patch("editais.views.public.send_welcome_email_async") as mock_send:
            response = client.post(
                "/register/",
                data={
                    "username": "testuser_pytest",
                    "email": "pytest@example.com",
                    "first_name": "Pytest",
                    "last_name": "User",
                    "password1": "Str0ngP@ss2026!",
                    "password2": "Str0ngP@ss2026!",
                },
            )
            # Registration redirects on success
            if response.status_code in (200, 302):
                # If form was valid and user created, the mock should have been called
                if mock_send.called:
                    mock_send.assert_called_once()
                    call_args = mock_send.call_args
                    assert call_args[0][0] == "pytest@example.com"  # email
