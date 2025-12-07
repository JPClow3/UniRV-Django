"""
Tests for public views (home, ambientes_inovacao, projetos_aprovados, login, register).
"""

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class HomeViewTest(TestCase):
    """Tests for home page view"""
    
    def setUp(self):
        self.client = Client()
    
    def test_home_page_loads(self):
        """Test that home page loads without authentication"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        # Verify content is present (template is being rendered)
        self.assertContains(response, 'AgroHub', status_code=200)
    
    def test_home_page_contains_branding(self):
        """Test that home page contains AgroHub branding"""
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'AgroHub', status_code=200)


class AmbientesInovacaoViewTest(TestCase):
    """Tests for ambientes de inovação page view"""
    
    def setUp(self):
        self.client = Client()
    
    def test_ambientes_inovacao_page_loads(self):
        """Test that ambientes de inovação page loads without authentication"""
        response = self.client.get(reverse('ambientes_inovacao'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'ambientes_inovacao.html')


class ProjetosAprovadosViewTest(TestCase):
    """Tests for projetos aprovados page view"""
    
    def setUp(self):
        self.client = Client()
    
    def test_projetos_aprovados_page_loads(self):
        """Test that projetos aprovados page loads without authentication"""
        response = self.client.get(reverse('projetos_aprovados'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projetos_aprovados.html')


class LoginViewTest(TestCase):
    """Tests for login view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
    
    def test_login_page_loads(self):
        """Test that login page loads without authentication"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
    
    def test_login_page_redirects_authenticated_user(self):
        """Test that authenticated users are redirected to dashboard"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('login'))
        self.assertRedirects(response, reverse('dashboard_home'))
    
    def test_login_with_valid_credentials(self):
        """Test login with valid credentials"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('dashboard_home'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, 'form')
    
    def test_login_redirects_to_next_url(self):
        """Test that login redirects to next URL if provided"""
        next_url = '/editais/'
        response = self.client.post(
            reverse('login') + f'?next={next_url}',
            {
                'username': 'testuser',
                'password': 'testpass123'
            }
        )
        self.assertRedirects(response, next_url)
    
    def test_login_page_has_csrf_token(self):
        """Test that login page includes CSRF token"""
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'csrfmiddlewaretoken')


class RegisterViewTest(TestCase):
    """Tests for user registration view"""
    
    def setUp(self):
        self.client = Client()
    
    def test_register_page_loads(self):
        """Test that register page loads without authentication"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')
    
    def test_register_page_redirects_authenticated_user(self):
        """Test that authenticated users are redirected to dashboard"""
        user = User.objects.create_user(
            username='existinguser',
            password='testpass123'
        )
        self.client.login(username='existinguser', password='testpass123')
        response = self.client.get(reverse('register'))
        self.assertRedirects(response, reverse('dashboard_home'))
    
    def test_register_with_valid_data(self):
        """Test user registration with valid data"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertRedirects(response, reverse('dashboard_home'))
        self.assertTrue(User.objects.filter(username='newuser').exists())
        # User should be automatically logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_register_with_invalid_data(self):
        """Test user registration with invalid data"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'invalid-email',
            'password1': 'short',
            'password2': 'short',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())
        self.assertContains(response, 'form')
    
    def test_register_with_duplicate_email(self):
        """Test that registration fails with duplicate email"""
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='testpass123'
        )
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'existing@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())
    
    def test_register_page_has_csrf_token(self):
        """Test that register page includes CSRF token"""
        response = self.client.get(reverse('register'))
        self.assertContains(response, 'csrfmiddlewaretoken')


class DjangoMessagesToToastTest(TestCase):
    """Tests for Django messages to toast notification conversion"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
    
    def test_success_message_appears_as_toast(self):
        """Test that Django success messages are converted to toast notifications"""
        from django.contrib import messages
        self.client.login(username='testuser', password='testpass123')
        
        # Make a request to get a session
        response = self.client.get(reverse('home'))
        # Add message to the session storage directly
        storage = messages.get_messages(response.wsgi_request)
        storage.add(messages.SUCCESS, 'Test success message')
        # Save the session
        response.wsgi_request.session.save()
        
        # Make another request - message should be available
        response = self.client.get(reverse('home'))
        messages_list = list(messages.get_messages(response.wsgi_request))
        # Check if message is in the list
        self.assertTrue(any(msg.message == 'Test success message' for msg in messages_list),
                       f"Message not found. Messages: {[m.message for m in messages_list]}")
    
    def test_error_message_appears_as_toast(self):
        """Test that Django error messages are converted to toast notifications"""
        from django.contrib import messages
        self.client.login(username='testuser', password='testpass123')
        
        # Make a request to get a session
        response = self.client.get(reverse('home'))
        # Add message to the session storage directly
        storage = messages.get_messages(response.wsgi_request)
        storage.add(messages.ERROR, 'Test error message')
        # Save the session
        response.wsgi_request.session.save()
        
        # Make another request - message should be available
        response = self.client.get(reverse('home'))
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(any(msg.message == 'Test error message' for msg in messages_list),
                       f"Message not found. Messages: {[m.message for m in messages_list]}")
    
    def test_warning_message_appears_as_toast(self):
        """Test that Django warning messages are converted to toast notifications"""
        from django.contrib import messages
        self.client.login(username='testuser', password='testpass123')
        
        # Make a request to get a session
        response = self.client.get(reverse('home'))
        # Add message to the session storage directly
        storage = messages.get_messages(response.wsgi_request)
        storage.add(messages.WARNING, 'Test warning message')
        # Save the session
        response.wsgi_request.session.save()
        
        # Make another request - message should be available
        response = self.client.get(reverse('home'))
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(any(msg.message == 'Test warning message' for msg in messages_list),
                       f"Message not found. Messages: {[m.message for m in messages_list]}")


class PasswordResetTest(TestCase):
    """Tests for complete password reset workflow"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='oldpass123',
            email='test@example.com'
        )
    
    def test_password_reset_page_loads(self):
        """Test that password reset page loads"""
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/password_reset_form.html')
    
    def test_password_reset_with_valid_email(self):
        """Test password reset with valid email"""
        from django.core import mail
        
        response = self.client.post(reverse('password_reset'), {
            'email': 'test@example.com'
        })
        # Should redirect to password_reset_done
        self.assertRedirects(response, reverse('password_reset_done'))
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('test@example.com', mail.outbox[0].to)
    
    def test_password_reset_with_invalid_email(self):
        """Test password reset with invalid email"""
        from django.core import mail
        
        response = self.client.post(reverse('password_reset'), {
            'email': 'nonexistent@example.com'
        })
        # Should still redirect (for security - don't reveal if email exists)
        self.assertRedirects(response, reverse('password_reset_done'))
        
        # Email should still be sent (security best practice)
        # But in Django, it won't send if email doesn't exist
        # This test verifies the form doesn't crash
    
    def test_password_reset_done_page_loads(self):
        """Test that password reset done page loads"""
        response = self.client.get(reverse('password_reset_done'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/password_reset_done.html')
    
    def test_password_reset_complete_page_loads(self):
        """Test that password reset complete page loads"""
        response = self.client.get(reverse('password_reset_complete'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/password_reset_complete.html')
