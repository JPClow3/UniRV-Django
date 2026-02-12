"""
Permission tests: staff vs non-staff access to dashboard views.
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestEditalPermissions:
    """Permission checks for dashboard views"""

    def test_staff_can_access_dashboard(self, staff_client):
        response = staff_client.get(reverse("admin_dashboard"))
        assert response.status_code == 200

    def test_non_staff_cannot_access_dashboard(self, auth_client):
        response = auth_client.get(reverse("admin_dashboard"))
        assert response.status_code == 403

    def test_anonymous_redirected_to_login(self, client):
        response = client.get(reverse("admin_dashboard"))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_staff_can_access_create(self, staff_client):
        response = staff_client.get(reverse("edital_create"))
        assert response.status_code == 200

    def test_non_staff_cannot_access_create(self, auth_client):
        response = auth_client.get(reverse("edital_create"))
        assert response.status_code == 403

    def test_anonymous_cannot_access_create(self, client):
        response = client.get(reverse("edital_create"))
        assert response.status_code == 302

    def test_staff_can_access_edit(self, staff_client, edital):
        response = staff_client.get(reverse("edital_update", kwargs={"pk": edital.pk}))
        assert response.status_code == 200

    def test_non_staff_cannot_access_edit(self, auth_client, edital):
        response = auth_client.get(reverse("edital_update", kwargs={"pk": edital.pk}))
        assert response.status_code == 403
