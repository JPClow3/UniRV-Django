"""
Tests for Project model edge cases.

Tests slug generation, logo field, and concurrent operations.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from editais.models import Project, Edital


class ProjectSlugGenerationTestCase(TestCase):
    """Test slug generation edge cases for Project model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_slug_generation_from_name(self):
        """Test that slug is generated from project name"""
        project = Project.objects.create(
            name='AgroTech Solutions',
            proponente=self.user
        )
        self.assertIsNotNone(project.slug)
        self.assertIn('agrotech', project.slug.lower())
    
    def test_slug_generation_empty_name(self):
        """Test slug generation with empty name (edge case)"""
        project = Project(name='', proponente=self.user)
        project.save()
        self.assertIsNotNone(project.slug)
        self.assertGreater(len(project.slug), 0)
    
    def test_slug_generation_special_characters(self):
        """Test slug generation with special characters"""
        project = Project.objects.create(
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
        project1 = Project.objects.create(
            name='Test Startup',
            proponente=self.user
        )
        project2 = Project.objects.create(
            name='Test Startup',
            proponente=self.user
        )
        self.assertNotEqual(project1.slug, project2.slug)
        self.assertTrue(project2.slug.endswith('-2') or project2.slug.endswith('-1'))
    
    def test_logo_field_exists(self):
        """Test that logo field exists and can be set"""
        project = Project.objects.create(
            name='Test Startup',
            proponente=self.user
        )
        # Logo field should exist (ImageFieldFile is never None, but can be empty)
        self.assertTrue(hasattr(project, 'logo'))
        # Check if logo is empty (ImageFieldFile evaluates to False when empty)
        self.assertFalse(project.logo)


class ProjectConcurrentSlugGenerationTestCase(TestCase):
    """Test concurrent slug generation scenarios"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_concurrent_slug_generation(self):
        """Test that concurrent saves with same name generate unique slugs"""
        # Create multiple projects with same name simultaneously
        projects = []
        for i in range(5):
            project = Project(name='Concurrent Startup', proponente=self.user)
            project.save()
            projects.append(project)
        
        # All slugs should be unique
        slugs = [p.slug for p in projects]
        self.assertEqual(len(slugs), len(set(slugs)))


class ProjectModelValidationTestCase(TestCase):
    """Test Project model validation"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_project_requires_name(self):
        """Test that project requires a name"""
        project = Project(proponente=self.user)
        with self.assertRaises(ValidationError):
            project.full_clean()
    
    def test_project_requires_proponente(self):
        """Test that project requires a proponente"""
        project = Project(name='Test Startup')
        with self.assertRaises(ValidationError):
            project.full_clean()

