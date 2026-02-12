"""
Error handling tests: database errors, cache errors, template errors.
"""

import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import DatabaseError
from django.test import override_settings
from django.urls import reverse

from editais.models import Edital
from editais.decorators import rate_limit, get_client_ip
from editais.utils import clear_index_cache


@pytest.mark.django_db
class TestDatabaseErrorHandling:
    """Test database error handling"""

    @pytest.fixture(autouse=True)
    def _create_edital(self):
        Edital.objects.create(
            titulo="Test Edital", url="https://example.com", status="aberto"
        )

    @patch("editais.views.public.Edital.objects")
    def test_database_error_in_index_view(self, mock_objects, client):
        mock_objects.with_related.side_effect = DatabaseError(
            "Database connection failed"
        )
        response = client.get(reverse("editais_index"))
        assert response.status_code == 200

    @patch("editais.views.public.get_object_or_404")
    def test_database_error_in_detail_view(self, mock_get, client):
        mock_get.side_effect = DatabaseError("Database connection failed")
        response = client.get(reverse("edital_detail_slug", kwargs={"slug": "test"}))
        assert response.status_code == 404


@pytest.mark.django_db
class TestCacheErrorHandling:
    """Test cache error handling"""

    @pytest.fixture(autouse=True)
    def _setup_user(self, client):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", is_staff=True
        )
        client.login(username="testuser", password="testpass123")

    @patch("editais.decorators.cache")
    def test_rate_limit_with_cache_failure(self, mock_cache):
        mock_cache.add.side_effect = ConnectionError("Cache unavailable")
        from django.http import HttpResponse

        @rate_limit(key="ip", rate=5, window=60, method="POST")
        def test_view(request):
            return HttpResponse("OK")

        response = test_view(
            MagicMock(method="POST", user=MagicMock(is_authenticated=False))
        )
        assert response.status_code == 200

    @patch("editais.utils.cache")
    def test_clear_index_cache_with_cache_failure(self, mock_cache):
        mock_cache.incr.side_effect = AttributeError("Method not available")
        mock_cache.get.return_value = 1
        mock_cache.set.side_effect = ConnectionError("Cache unavailable")

        # Should not raise
        try:
            clear_index_cache()
        except Exception as exc:
            pytest.fail(
                f"clear_index_cache should handle cache errors gracefully, got: {exc}"
            )


@pytest.mark.django_db
class TestTemplateErrorHandling:
    """Test template rendering with missing context"""

    def test_template_with_missing_optional_context(self, client):
        response = client.get(reverse("home"))
        assert response.status_code == 200

    def test_template_filter_with_none_value(self):
        from editais.templatetags.editais_filters import days_until, is_deadline_soon

        assert days_until(None) is None
        assert is_deadline_soon(None) is False


@pytest.mark.django_db
class TestManagementCommandErrorHandling:
    """Test management command error handling"""

    def test_update_edital_status_with_invalid_data(self):
        from django.core.management import call_command
        from io import StringIO

        Edital.objects.create(
            titulo="Test Edital",
            url="https://example.com",
            status="aberto",
            start_date=None,
            end_date=None,
        )

        out = StringIO()
        try:
            call_command("update_edital_status", stdout=out, verbosity=0)
        except Exception as exc:
            pytest.fail(f"Command should handle edge cases gracefully, got: {exc}")


class TestIPAddressHandling:
    """Test IP address extraction and validation"""

    def test_get_client_ip_with_valid_remote_addr(self):
        request = MagicMock()
        request.META = {"REMOTE_ADDR": "192.168.1.1"}
        assert get_client_ip(request) == "192.168.1.1"

    def test_get_client_ip_with_invalid_ip(self):
        request = MagicMock()
        request.META = {"REMOTE_ADDR": "invalid-ip"}
        assert get_client_ip(request) == "unknown"

    def test_get_client_ip_with_x_forwarded_for(self):
        with override_settings(USE_X_FORWARDED_HOST=True):
            request = MagicMock()
            request.META = {
                "REMOTE_ADDR": "10.0.0.1",
                "HTTP_X_FORWARDED_FOR": "192.168.1.1, 10.0.0.1",
            }
            assert get_client_ip(request) == "192.168.1.1"
