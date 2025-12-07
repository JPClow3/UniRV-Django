"""
Tests for startup detail views.

Tests startup detail view with slug and ID, 404 handling.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from editais.models import Project


class StartupDetailViewTestCase(TestCase):
    """Test startup detail view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.project = Project.objects.create(
            name='Test Startup',
            description='A test startup',
            proponente=self.user
        )
    
    def test_startup_detail_by_slug(self):
        """Test accessing startup detail by slug"""
        url = reverse('startup_detail_slug', kwargs={'slug': self.project.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.project.name)
    
    def test_startup_detail_by_id_redirects(self):
        """Test that accessing by ID redirects to slug URL"""
        # Ensure project has a slug (should be generated on save)
        self.project.refresh_from_db()
        url = reverse('startup_detail', kwargs={'pk': self.project.pk})
        response = self.client.get(url, follow=False)
        
        if self.project.slug:
            # Should redirect to slug URL if slug exists
            self.assertIn(response.status_code, [301, 302], 
                         f"Expected redirect (301/302), got {response.status_code}")
            if response.status_code in [301, 302]:
                self.assertIn(self.project.slug, response.url)
        else:
            # If no slug, should call detail view directly (200)
            self.assertEqual(response.status_code, 200,
                           f"Expected 200 when no slug, got {response.status_code}")
    
    def test_startup_detail_404_invalid_slug(self):
        """Test 404 for invalid slug"""
        url = reverse('startup_detail_slug', kwargs={'slug': 'non-existent-slug'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
    
    def test_startup_detail_404_invalid_id(self):
        """Test 404 for invalid ID"""
        url = reverse('startup_detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
    
    def test_startup_detail_displays_logo(self):
        """Test that startup detail page handles logo display"""
        url = reverse('startup_detail_slug', kwargs={'slug': self.project.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Page should render even without logo
        self.assertContains(response, self.project.name)

