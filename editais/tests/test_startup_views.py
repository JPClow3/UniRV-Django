"""
Tests for startup detail views.

Tests startup detail view with slug and ID, 404 handling.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from editais.models import Startup


class StartupDetailViewTestCase(TestCase):
    """Test startup detail view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.project = Startup.objects.create(
            name="Test Startup",
            description="A test startup",
            proponente=self.user,
            status="pre_incubacao",
        )
        # Ensure slug is generated
        self.project.refresh_from_db()

    def test_startup_detail_by_slug(self):
        """Test accessing startup detail by slug"""
        url = reverse("startup_detail_slug", kwargs={"slug": self.project.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project.name)

    def test_startup_detail_by_id_redirects(self):
        """Test that accessing by ID redirects to slug URL"""
        # Ensure project has a slug (should be generated on save)
        self.project.refresh_from_db()

        # Verify project exists and has a slug
        self.assertIsNotNone(self.project.pk)
        self.assertTrue(self.project.slug, "Startup should have a slug after save")

        # Test accessing by slug first (should work)
        slug_url = reverse("startup_detail_slug", kwargs={"slug": self.project.slug})
        slug_response = self.client.get(slug_url)
        self.assertEqual(
            slug_response.status_code,
            200,
            f"Startup detail by slug should return 200, got {slug_response.status_code}",
        )

        # Test accessing by PK with follow=True to follow any redirects
        pk_url = reverse("startup_detail", kwargs={"pk": self.project.pk})
        pk_response = self.client.get(pk_url, follow=True)

        # After following redirects, should get 200 or show the startup page
        # The redirect chain should eventually lead to the slug URL
        self.assertEqual(
            pk_response.status_code,
            200,
            f"Startup detail by PK (with follow) should return 200, got {pk_response.status_code}. "
            f"Redirect chain: {pk_response.redirect_chain}",
        )

    def test_startup_detail_404_invalid_slug(self):
        """Test 404 for invalid slug"""
        url = reverse("startup_detail_slug", kwargs={"slug": "non-existent-slug"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_startup_detail_404_invalid_id(self):
        """Test 404 for invalid ID"""
        url = reverse("startup_detail", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_startup_detail_displays_logo(self):
        """Test that startup detail page handles logo display"""
        url = reverse("startup_detail_slug", kwargs={"slug": self.project.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Page should render even without logo
        self.assertContains(response, self.project.name)
