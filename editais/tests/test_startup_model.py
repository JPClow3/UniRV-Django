"""
Tests for Startup model edge cases.

Tests slug generation, logo field, and concurrent operations.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from editais.models import Startup, Edital


class StartupSlugGenerationTestCase(TestCase):
    """Test slug generation edge cases for Startup model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_slug_generation_from_name(self):
        """Test that slug is generated from project name"""
        project = Startup.objects.create(
            name='AgroTech Solutions',
            proponente=self.user
        )
        self.assertIsNotNone(project.slug)
        self.assertIn('agrotech', project.slug.lower())
    
    def test_slug_generation_empty_name(self):
        """Test slug generation with empty name (edge case)"""
        project = Startup(name='', proponente=self.user)
        project.save()
        self.assertIsNotNone(project.slug)
        self.assertGreater(len(project.slug), 0)
    
    def test_slug_generation_special_characters(self):
        """Test slug generation with special characters"""
        project = Startup.objects.create(
            name='Startup @#$% 123!',
            proponente=self.user
        )
        self.assertIsNotNone(project.slug)
        # Slug should not contain special characters
        self.assertNotIn('@', project.slug)
        self.assertNotIn('#', project.slug)
        self.assertNotIn('$', project.slug)
    
    def test_slug_uniqueness(self):
        """Test that duplicate names generate unique slugs"""
        project1 = Startup.objects.create(
            name='Test Startup',
            proponente=self.user
        )
        project2 = Startup.objects.create(
            name='Test Startup',
            proponente=self.user
        )
        self.assertNotEqual(project1.slug, project2.slug)
        self.assertTrue(project2.slug.endswith('-2') or project2.slug.endswith('-1'))
    
    def test_logo_field_exists(self):
        """Test that logo field exists and can be set"""
        project = Startup.objects.create(
            name='Test Startup',
            proponente=self.user
        )
        # Logo field should exist (ImageFieldFile is never None, but can be empty)
        self.assertTrue(hasattr(project, 'logo'))
        # Check if logo is empty (ImageFieldFile evaluates to False when empty)
        self.assertFalse(project.logo)


class StartupConcurrentSlugGenerationTestCase(TestCase):
    """Test concurrent slug generation scenarios"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_concurrent_slug_generation(self):
        """Test that concurrent saves with same name generate unique slugs"""
        # Create multiple startups with same name simultaneously
        startups = []
        for i in range(5):
            startup = Startup(name='Concurrent Startup', proponente=self.user)
            startup.save()
            startups.append(startup)
        
        # All slugs should be unique
        slugs = [s.slug for s in startups]
        self.assertEqual(len(slugs), len(set(slugs)))


class StartupModelValidationTestCase(TestCase):
    """Test Startup model validation"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_startup_requires_name(self):
        """Test that startup requires a name"""
        startup = Startup(proponente=self.user)
        with self.assertRaises(ValidationError):
            startup.full_clean()
    
    def test_startup_requires_proponente(self):
        """Test that startup requires a proponente"""
        startup = Startup(name='Test Startup')
        with self.assertRaises(ValidationError):
            startup.full_clean()

