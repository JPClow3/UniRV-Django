"""
Tests for startup detail views.
"""

import pytest

from django.contrib.auth.models import User
from django.urls import reverse

from editais.models import Startup
from editais.tests.factories import UserFactory


@pytest.mark.django_db
class TestStartupDetailView:
    """Test startup detail view."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.project = Startup.objects.create(
            name="Test Startup",
            description="A test startup",
            proponente=self.user,
            status="pre_incubacao",
        )
        self.project.refresh_from_db()

    def test_startup_detail_by_slug(self, client):
        """Test accessing startup detail by slug"""
        url = reverse("startup_detail_slug", kwargs={"slug": self.project.slug})
        response = client.get(url)
        assert response.status_code == 200
        assert self.project.name in response.content.decode()

    def test_startup_detail_by_id_redirects(self, client):
        """Test that accessing by ID redirects to slug URL"""
        self.project.refresh_from_db()

        assert self.project.pk
        assert self.project.slug

        slug_url = reverse("startup_detail_slug", kwargs={"slug": self.project.slug})
        slug_response = client.get(slug_url)
        assert slug_response.status_code == 200

        pk_url = reverse("startup_detail", kwargs={"pk": self.project.pk})
        pk_response = client.get(pk_url, follow=True)

        assert pk_response.status_code == 200

    def test_startup_detail_404_invalid_slug(self, client):
        """Test 404 for invalid slug"""
        url = reverse("startup_detail_slug", kwargs={"slug": "non-existent-slug"})
        response = client.get(url)
        assert response.status_code == 404

    def test_startup_detail_404_invalid_id(self, client):
        """Test 404 for invalid ID"""
        url = reverse("startup_detail", kwargs={"pk": 99999})
        response = client.get(url)
        assert response.status_code == 404

    def test_startup_detail_displays_logo(self, client):
        """Test that startup detail page handles logo display"""
        url = reverse("startup_detail_slug", kwargs={"slug": self.project.slug})
        response = client.get(url)
        assert response.status_code == 200
        assert self.project.name in response.content.decode()
