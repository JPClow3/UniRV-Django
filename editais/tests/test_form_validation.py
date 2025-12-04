"""
Form validation tests with edge values.
"""

from datetime import date, timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from ..forms import EditalForm, UserRegistrationForm
from ..models import Project


class EditalFormValidationTest(TestCase):
    """Test EditalForm validation with edge cases"""
    
    def test_required_fields(self):
        """Test that required fields are validated"""
        form = EditalForm({})
        self.assertFalse(form.is_valid())
        self.assertIn('titulo', form.errors)
        self.assertIn('url', form.errors)
    
    def test_url_validation(self):
        """Test URL field validation"""
        # Valid URL
        form = EditalForm({
            'titulo': 'Test Edital',
            'url': 'https://example.com',
            'status': 'aberto'
        })
        self.assertTrue(form.is_valid())
        
        # Invalid URL format
        form = EditalForm({
            'titulo': 'Test Edital',
            'url': 'not-a-url',
            'status': 'aberto'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('url', form.errors)
    
    def test_date_validation_end_before_start(self):
        """Test that end_date before start_date is invalid"""
        form = EditalForm({
            'titulo': 'Test Edital',
            'url': 'https://example.com',
            'status': 'aberto',
            'start_date': date.today() + timedelta(days=30),
            'end_date': date.today(),
        })
        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)
    
    def test_date_validation_same_dates(self):
        """Test that same start and end date is valid"""
        same_date = date.today()
        form = EditalForm({
            'titulo': 'Test Edital',
            'url': 'https://example.com',
            'status': 'aberto',
            'start_date': same_date,
            'end_date': same_date,
        })
        self.assertTrue(form.is_valid())
    
    def test_max_length_validation(self):
        """Test max length validation on fields"""
        # Title max length is 500
        long_title = 'a' * 501
        form = EditalForm({
            'titulo': long_title,
            'url': 'https://example.com',
            'status': 'aberto'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('titulo', form.errors)
    
    def test_status_choices_validation(self):
        """Test that invalid status values are rejected"""
        form = EditalForm({
            'titulo': 'Test Edital',
            'url': 'https://example.com',
            'status': 'invalid_status'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)


class UserRegistrationFormValidationTest(TestCase):
    """Test UserRegistrationForm validation"""
    
    def test_required_fields(self):
        """Test that required fields are validated"""
        form = UserRegistrationForm({})
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('first_name', form.errors)
        self.assertIn('password1', form.errors)
        self.assertIn('password2', form.errors)
    
    def test_email_uniqueness(self):
        """Test that duplicate emails are rejected"""
        User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='testpass123'
        )
        
        form = UserRegistrationForm({
            'username': 'newuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_password_mismatch(self):
        """Test that mismatched passwords are rejected"""
        form = UserRegistrationForm({
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'ComplexPass123!',
            'password2': 'DifferentPass123!',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
    
    def test_password_validation(self):
        """Test Django's password validators"""
        # Too short password
        form = UserRegistrationForm({
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'short',
            'password2': 'short',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
    
    def test_email_format_validation(self):
        """Test email format validation"""
        form = UserRegistrationForm({
            'username': 'testuser',
            'email': 'not-an-email',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class ProjectModelValidationTest(TestCase):
    """Test Project model validation, especially image upload"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_image_file_size_validation(self):
        """Test that large image files are rejected"""
        # Create a file larger than 5MB
        large_file = SimpleUploadedFile(
            "large.jpg",
            b"x" * (6 * 1024 * 1024),  # 6MB
            content_type="image/jpeg"
        )
        
        project = Project(
            name='Test Project',
            proponente=self.user,
            status='pre_incubacao',
            logo=large_file
        )
        
        with self.assertRaises(ValidationError):
            project.clean()
    
    def test_image_file_extension_validation(self):
        """Test that non-image file extensions are rejected"""
        invalid_file = SimpleUploadedFile(
            "document.pdf",
            b"fake pdf content",
            content_type="application/pdf"
        )
        
        project = Project(
            name='Test Project',
            proponente=self.user,
            status='pre_incubacao',
            logo=invalid_file
        )
        
        with self.assertRaises(ValidationError):
            project.clean()
    
    def test_valid_image_upload(self):
        """Test that valid image uploads are accepted"""
        valid_file = SimpleUploadedFile(
            "logo.jpg",
            b"fake jpeg content",
            content_type="image/jpeg"
        )
        
        project = Project(
            name='Test Project',
            proponente=self.user,
            status='pre_incubacao',
            logo=valid_file
        )
        
        # Should not raise validation error
        try:
            project.clean()
        except ValidationError:
            self.fail("Valid image should not raise ValidationError")
    
    def test_project_without_logo(self):
        """Test that project without logo is valid"""
        project = Project(
            name='Test Project',
            proponente=self.user,
            status='pre_incubacao'
        )
        
        # Should not raise validation error
        try:
            project.clean()
        except ValidationError:
            self.fail("Project without logo should be valid")

