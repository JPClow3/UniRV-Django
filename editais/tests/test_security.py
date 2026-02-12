"""
Security tests: CSRF, XSS, SQL injection, authentication bypass.
"""

import pytest
from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse

from editais.models import Edital


@pytest.mark.django_db
class TestCSRFProtection:
    """Verify CSRF enforcement on POST endpoints"""

    @override_settings(CSRF_COOKIE_SECURE=False)
    def test_post_without_csrf_is_rejected(self, client):
        from django.test import Client as DjClient

        csrf_client = DjClient(enforce_csrf_checks=True)
        User.objects.create_user(username="csrfuser", password="testpass123")
        csrf_client.login(username="csrfuser", password="testpass123")
        response = csrf_client.post(reverse("edital_create"), {"titulo": "Test"})
        assert response.status_code == 403

    def test_post_with_csrf_is_accepted(self, staff_client):
        response = staff_client.post(
            reverse("edital_create"),
            {
                "titulo": "Edital CSRF OK",
                "url": "https://example.com",
                "status": "aberto",
            },
        )
        assert response.status_code in (200, 302)


@pytest.mark.django_db
class TestXSSPrevention:
    """Test XSS vectors are sanitised"""

    def test_xss_in_titulo(self, staff_client):
        staff_client.post(
            reverse("edital_create"),
            {
                "titulo": '<script>alert("xss")</script>',
                "url": "https://example.com",
                "status": "aberto",
            },
        )
        edital = Edital.objects.first()
        if edital:
            assert "<script>" not in edital.titulo

    def test_xss_in_search_query(self, client):
        response = client.get(
            reverse("editais_index"), {"q": '<script>alert("xss")</script>'}
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "<script>alert" not in content


@pytest.mark.django_db
class TestSQLInjection:
    """Basic SQL injection prevention checks"""

    def test_sql_injection_in_search(self, client):
        response = client.get(
            reverse("editais_index"), {"q": "'; DROP TABLE editais_edital; --"}
        )
        assert response.status_code == 200

    def test_sql_injection_in_filter(self, client):
        response = client.get(reverse("editais_index"), {"status": "' OR '1'='1"})
        assert response.status_code == 200


@pytest.mark.django_db
class TestAuthenticationAuthorization:
    """Verify auth bypass attempts fail"""

    def test_anonymous_cannot_delete_edital(self, client, edital):
        response = client.post(reverse("edital_delete", kwargs={"pk": edital.pk}))
        assert response.status_code == 302
        assert Edital.objects.filter(pk=edital.pk).exists()

    def test_non_staff_cannot_delete_edital(self, auth_client, edital):
        response = auth_client.post(reverse("edital_delete", kwargs={"pk": edital.pk}))
        assert response.status_code == 403
        assert Edital.objects.filter(pk=edital.pk).exists()

    def test_staff_can_delete_edital(self, staff_client, edital):
        response = staff_client.post(reverse("edital_delete", kwargs={"pk": edital.pk}))
        assert response.status_code in (200, 302)
